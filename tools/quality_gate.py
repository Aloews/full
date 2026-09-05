"""The final quality gate.

Merging is blocked unless every one of these holds:

    critical tests   PASS
    meta tests       PASS
    security tests   PASS
    mutation score   >= the per-module thresholds
    core coverage    >= the configured floor
    suite integrity  T-META-001 detected its controlled break

The gate consumes the artefacts the CI stages produce, so a failure points at
the stage that produced it instead of re-running everything.

    python -m tools.quality_gate --reports reports
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: Statement coverage floor for the decision-making core.
CORE_COVERAGE_THRESHOLD = 0.90
#: Statement coverage floor for the project as a whole.
TOTAL_COVERAGE_THRESHOLD = 0.80
#: Path prefixes that count as "core".
CORE_PREFIXES = ("kontur/core/", "kontur/engines/")

#: Stages whose status files must exist and read PASS.
REQUIRED_STAGES = (
    "lint",
    "typecheck",
    "unit",
    "integration",
    "seo",
    "aeo",
    "geo",
    "security",
    "regression",
    "api",
    "e2e",
    "meta",
)


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    passed: bool
    detail: str

    @property
    def symbol(self) -> str:
        return "PASS" if self.passed else "BLOCK"


def _read_status(reports: Path, stage: str) -> Check:
    path = reports / f"{stage}.status"
    if not path.exists():
        return Check(f"{stage} tests", False, f"no status file at {path}")
    value = path.read_text(encoding="utf-8").strip().upper()
    return Check(f"{stage} tests", value == "PASS", value or "empty status file")


def _check_mutation(reports: Path) -> list[Check]:
    path = reports / "mutation.json"
    if not path.exists():
        return [Check("mutation score", False, f"no mutation report at {path}")]
    report = json.loads(path.read_text(encoding="utf-8"))
    checks = [
        Check(
            "mutation score",
            bool(report.get("passed")),
            f"{report.get('overall_score', 0):.1%} overall across {report.get('mutants', 0)} mutants",
        )
    ]
    for module in report.get("modules", []):
        if not module.get("passed"):
            checks.append(
                Check(
                    f"mutation: {module['module']}",
                    False,
                    f"{module['score']:.1%} < {module['threshold']:.0%} ({module['survived']} survived)",
                )
            )
    return checks


def _check_sentinel(reports: Path) -> Check:
    path = reports / "sentinel.json"
    if not path.exists():
        return Check("suite integrity (T-META-001)", False, f"no sentinel report at {path}")
    report = json.loads(path.read_text(encoding="utf-8"))
    detail = (
        "the suite detected the controlled break"
        if report.get("trustworthy")
        else report.get("detail", "the suite did not detect the controlled break")
    )
    return Check("suite integrity (T-META-001)", bool(report.get("trustworthy")), detail)


def _coverage_ratio(files: dict[str, Any], prefixes: Sequence[str] | None = None) -> tuple[float, int]:
    covered = 0
    total = 0
    for name, data in files.items():
        normalised = name.replace("\\", "/")
        if prefixes and not normalised.startswith(tuple(prefixes)):
            continue
        summary = data.get("summary", {})
        covered += summary.get("covered_lines", 0)
        total += summary.get("num_statements", 0)
    return (covered / total if total else 0.0), total


def _check_coverage(reports: Path) -> list[Check]:
    path = reports / "coverage.json"
    if not path.exists():
        return [Check("core coverage", False, f"no coverage report at {path}")]
    report = json.loads(path.read_text(encoding="utf-8"))
    files = report.get("files", {})

    core_ratio, core_statements = _coverage_ratio(files, CORE_PREFIXES)
    total_ratio, total_statements = _coverage_ratio(files)
    return [
        Check(
            "core coverage",
            core_ratio >= CORE_COVERAGE_THRESHOLD,
            f"{core_ratio:.1%} of {core_statements} statements (floor {CORE_COVERAGE_THRESHOLD:.0%})",
        ),
        Check(
            "total coverage",
            total_ratio >= TOTAL_COVERAGE_THRESHOLD,
            f"{total_ratio:.1%} of {total_statements} statements (floor {TOTAL_COVERAGE_THRESHOLD:.0%})",
        ),
    ]


def collect_checks(reports: Path, *, stages: Sequence[str] = REQUIRED_STAGES) -> list[Check]:
    checks = [_read_status(reports, stage) for stage in stages]
    checks.extend(_check_mutation(reports))
    checks.append(_check_sentinel(reports))
    checks.extend(_check_coverage(reports))
    return checks


def render(checks: Sequence[Check]) -> str:
    width = max(len(check.name) for check in checks) + 2
    lines = ["", "FINAL QUALITY GATE", "=" * (width + 60)]
    for check in checks:
        lines.append(f"  {check.symbol:<6} {check.name:<{width}} {check.detail}")
    lines.append("=" * (width + 60))
    blocked = [c for c in checks if not c.passed]
    if blocked:
        lines.append(f"BLOCK — {len(blocked)} of {len(checks)} checks failed:")
        lines.extend(f"    - {c.name}: {c.detail}" for c in blocked)
    else:
        lines.append(f"PASS — all {len(checks)} checks cleared")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Kontur final quality gate")
    parser.add_argument("--reports", type=Path, default=Path("reports"))
    parser.add_argument("--stage", action="append", dest="stages", help="override the required stages")
    parser.add_argument("--json", type=Path, help="write the gate result as JSON")
    args = parser.parse_args(argv)

    checks = collect_checks(args.reports, stages=args.stages or REQUIRED_STAGES)
    print(render(checks))

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {
                    "passed": all(c.passed for c in checks),
                    "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail} for c in checks],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    return 0 if all(check.passed for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
