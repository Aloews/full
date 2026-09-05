"""Mutation testing: break the implementation on purpose, expect a red suite.

The engine copies the project into a temporary directory, applies one mutation
at a time to a target module, runs that module's tests, and records whether the
suite noticed. A surviving mutant is a hole in the tests, not a bug in the code.

    python -m tools.mutation.runner --json reports/mutation.json
    python -m tools.mutation.runner --module kontur/engines/faceted/rules.py -n 5
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from tools.mutation.config import TARGETS, CampaignSettings, MutationTarget, is_equivalent
from tools.mutation.operators import Mutation, generate_mutations

#: Directories copied into the sandbox. Everything else is irrelevant to a run.
COPIED = ("kontur", "tests", "tools", "pyproject.toml")
IGNORED = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".git", "reports")


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "pyproject.toml").exists():
            return candidate
    raise RuntimeError("could not locate the repository root")


@dataclass(frozen=True, slots=True)
class MutantResult:
    module: str
    operator: str
    lineno: int
    description: str
    killed: bool
    duration: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ModuleReport:
    module: str
    label: str
    threshold: float
    results: list[MutantResult] = field(default_factory=list)
    excluded: list[dict[str, str]] = field(default_factory=list)
    baseline_ok: bool = True

    @property
    def killed(self) -> int:
        return sum(1 for r in self.results if r.killed)

    @property
    def survived(self) -> int:
        return sum(1 for r in self.results if not r.killed)

    @property
    def score(self) -> float:
        total = len(self.results)
        return self.killed / total if total else 1.0

    @property
    def passed(self) -> bool:
        return self.baseline_ok and self.score >= self.threshold

    def survivors(self) -> list[MutantResult]:
        return [r for r in self.results if not r.killed]

    def to_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "label": self.label,
            "threshold": self.threshold,
            "mutants": len(self.results),
            "killed": self.killed,
            "survived": self.survived,
            "score": round(self.score, 4),
            "passed": self.passed,
            "baseline_ok": self.baseline_ok,
            "survivors": [r.to_dict() for r in self.survivors()],
            "excluded_as_equivalent": list(self.excluded),
        }


@dataclass
class CampaignReport:
    modules: list[ModuleReport] = field(default_factory=list)
    duration: float = 0.0

    @property
    def total_mutants(self) -> int:
        return sum(len(m.results) for m in self.modules)

    @property
    def total_killed(self) -> int:
        return sum(m.killed for m in self.modules)

    @property
    def overall_score(self) -> float:
        return self.total_killed / self.total_mutants if self.total_mutants else 1.0

    @property
    def passed(self) -> bool:
        return bool(self.modules) and all(m.passed for m in self.modules)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mutants": self.total_mutants,
            "killed": self.total_killed,
            "survived": self.total_mutants - self.total_killed,
            "overall_score": round(self.overall_score, 4),
            "passed": self.passed,
            "duration_seconds": round(self.duration, 1),
            "modules": [m.to_dict() for m in self.modules],
        }

    def render(self) -> str:
        lines = [
            f"{'module':<48} {'label':<16} {'kill':>6} {'score':>7} {'bar':>6}  result",
            "-" * 96,
        ]
        for module in self.modules:
            verdict = "PASS" if module.passed else "FAIL"
            lines.append(
                f"{module.module:<48} {module.label:<16} "
                f"{module.killed:>3}/{len(module.results):<2} {module.score:>7.1%} "
                f"{module.threshold:>6.0%}  {verdict}"
            )
            for survivor in module.survivors():
                lines.append(f"    SURVIVED  line {survivor.lineno:>4}  {survivor.description}")
            for entry in module.excluded:
                lines.append(
                    f"    excluded (equivalent) line {entry['line']:>4}  {entry['justification']}"
                )
        lines.append("-" * 96)
        lines.append(
            f"overall {self.total_killed}/{self.total_mutants} = {self.overall_score:.1%} "
            f"in {self.duration:.0f}s — {'PASS' if self.passed else 'FAIL'}"
        )
        return "\n".join(lines)


class Sandbox:
    """A throwaway copy of the project that mutants are applied to."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.directory = Path(tempfile.mkdtemp(prefix="kontur-mutation-"))
        for name in COPIED:
            source = root / name
            if not source.exists():
                continue
            destination = self.directory / name
            if source.is_dir():
                shutil.copytree(source, destination, ignore=IGNORED)
            else:
                shutil.copy2(source, destination)

    def cleanup(self) -> None:
        shutil.rmtree(self.directory, ignore_errors=True)

    def __enter__(self) -> Sandbox:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.cleanup()

    def run_tests(self, tests: Sequence[str], *, timeout: int) -> tuple[int, str]:
        # Bytecode caching must stay off: consecutive mutants of the same size
        # written within the same second share an mtime, and CPython would then
        # reuse the previous mutant's .pyc — silently scoring the wrong code.
        environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        result = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [
                sys.executable, "-B", "-m", "pytest", *tests,
                "-x", "-q", "--no-header", "-p", "no:cacheprovider",
            ],
            cwd=self.directory,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=environment,
        )
        return result.returncode, result.stdout[-1500:]

    def write(self, relative: str, source: str) -> None:
        (self.directory / relative).write_text(source, encoding="utf-8")

    def read(self, relative: str) -> str:
        return (self.directory / relative).read_text(encoding="utf-8")


def _select(mutations: list[Mutation], limit: int, seed: int) -> list[Mutation]:
    if len(mutations) <= limit:
        return mutations
    rng = random.Random(seed)
    return sorted(rng.sample(mutations, limit), key=lambda m: (m.lineno, m.operator))


def run_target(
    sandbox: Sandbox, target: MutationTarget, settings: CampaignSettings, *, verbose: bool = False
) -> ModuleReport:
    report = ModuleReport(module=target.module, label=target.label, threshold=target.threshold)
    original = sandbox.read(target.module)

    code, output = sandbox.run_tests(target.tests, timeout=settings.timeout_seconds)
    if code != 0:
        report.baseline_ok = False
        if verbose:
            print(f"  baseline FAILED for {target.module}:\n{output}")
        return report

    candidates = []
    for mutation in generate_mutations(original):
        entry = is_equivalent(target.module, mutation.operator, mutation.description)
        if entry is not None:
            report.excluded.append(
                {"operator": mutation.operator, "line": str(mutation.lineno),
                 "justification": entry.justification}
            )
            continue
        candidates.append(mutation)

    mutations = _select(candidates, settings.max_mutants_per_module, settings.seed)
    for mutation in mutations:
        started = time.monotonic()
        sandbox.write(target.module, mutation.source)
        try:
            code, _ = sandbox.run_tests(target.tests, timeout=settings.timeout_seconds)
            killed = code != 0
        except subprocess.TimeoutExpired:
            killed = True  # a hang is a detected change, not a silent pass
        finally:
            sandbox.write(target.module, original)

        report.results.append(
            MutantResult(
                module=target.module,
                operator=mutation.operator,
                lineno=mutation.lineno,
                description=mutation.description,
                killed=killed,
                duration=time.monotonic() - started,
            )
        )
        if verbose:
            print(f"  {'killed ' if killed else 'SURVIVED'} {mutation.description}")
    return report


def run_campaign(
    settings: CampaignSettings | None = None,
    *,
    modules: Sequence[str] | None = None,
    verbose: bool = False,
) -> CampaignReport:
    settings = settings or CampaignSettings()
    targets = [t for t in settings.targets if not modules or t.module in modules]
    if not targets:
        raise SystemExit(f"no mutation targets match {modules}")

    started = time.monotonic()
    report = CampaignReport()
    with Sandbox(repo_root()) as sandbox:
        for target in targets:
            if verbose:
                print(f"mutating {target.module}")
            report.modules.append(run_target(sandbox, target, settings, verbose=verbose))
    report.duration = time.monotonic() - started
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Kontur mutation engine")
    parser.add_argument("--module", action="append", dest="modules", help="limit to these modules")
    parser.add_argument("-n", "--max-mutants", type=int, default=12, help="mutants per module")
    parser.add_argument("--seed", type=int, default=20260401)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--json", type=Path, help="write the report as JSON")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    settings = CampaignSettings(
        max_mutants_per_module=args.max_mutants,
        seed=args.seed,
        timeout_seconds=args.timeout,
        targets=TARGETS,
    )
    report = run_campaign(settings, modules=args.modules, verbose=args.verbose)
    print(report.render())

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        print(f"\nreport written to {args.json}")

    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
