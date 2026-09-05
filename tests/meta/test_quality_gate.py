"""The gate itself must block, not just report."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.quality_gate import (
    CORE_COVERAGE_THRESHOLD,
    REQUIRED_STAGES,
    collect_checks,
    main,
    render,
)

pytestmark = pytest.mark.meta


def _write_reports(directory: Path, *, stages_pass: bool = True, mutation: float = 1.0,
                   trustworthy: bool = True, core_covered: int = 95) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for stage in REQUIRED_STAGES:
        (directory / f"{stage}.status").write_text("PASS" if stages_pass else "FAIL", encoding="utf-8")
    (directory / "mutation.json").write_text(
        json.dumps(
            {
                "overall_score": mutation,
                "passed": mutation >= 0.95,
                "mutants": 100,
                "modules": [
                    {
                        "module": "kontur/engines/faceted/rules.py",
                        "score": mutation,
                        "threshold": 0.95,
                        "survived": int(100 * (1 - mutation)),
                        "passed": mutation >= 0.95,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (directory / "sentinel.json").write_text(
        json.dumps({"trustworthy": trustworthy, "detail": "" if trustworthy else "break went unnoticed"}),
        encoding="utf-8",
    )
    (directory / "coverage.json").write_text(
        json.dumps(
            {
                "files": {
                    "kontur/core/decisions.py": {
                        "summary": {"covered_lines": core_covered, "num_statements": 100}
                    },
                    "kontur/api/app.py": {"summary": {"covered_lines": 90, "num_statements": 100}},
                }
            }
        ),
        encoding="utf-8",
    )


def test_a_clean_run_passes(tmp_path: Path) -> None:
    _write_reports(tmp_path)
    checks = collect_checks(tmp_path)
    assert all(check.passed for check in checks)
    assert "PASS — all" in render(checks)
    assert main(["--reports", str(tmp_path)]) == 0


def test_a_failing_stage_blocks(tmp_path: Path) -> None:
    _write_reports(tmp_path, stages_pass=False)
    assert main(["--reports", str(tmp_path)]) == 1


def test_a_low_mutation_score_blocks(tmp_path: Path) -> None:
    _write_reports(tmp_path, mutation=0.60)
    checks = {check.name: check for check in collect_checks(tmp_path)}
    assert checks["mutation score"].passed is False
    assert main(["--reports", str(tmp_path)]) == 1


def test_an_untrustworthy_suite_blocks(tmp_path: Path) -> None:
    _write_reports(tmp_path, trustworthy=False)
    checks = {check.name: check for check in collect_checks(tmp_path)}
    assert checks["suite integrity (T-META-001)"].passed is False
    assert "break went unnoticed" in checks["suite integrity (T-META-001)"].detail
    assert main(["--reports", str(tmp_path)]) == 1


def test_low_core_coverage_blocks(tmp_path: Path) -> None:
    _write_reports(tmp_path, core_covered=int(CORE_COVERAGE_THRESHOLD * 100) - 5)
    checks = {check.name: check for check in collect_checks(tmp_path)}
    assert checks["core coverage"].passed is False
    assert main(["--reports", str(tmp_path)]) == 1


def test_missing_artefacts_block_rather_than_pass(tmp_path: Path) -> None:
    """An absent report is a failure, never a silent success."""
    checks = collect_checks(tmp_path)
    assert not any(check.passed for check in checks)
    assert main(["--reports", str(tmp_path)]) == 1


def test_the_gate_writes_a_machine_readable_result(tmp_path: Path) -> None:
    _write_reports(tmp_path)
    output = tmp_path / "gate.json"
    assert main(["--reports", str(tmp_path), "--json", str(output)]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["passed"] is True
    assert len(payload["checks"]) == len(REQUIRED_STAGES) + 4


def test_every_pipeline_stage_is_required() -> None:
    for stage in ("unit", "integration", "seo", "aeo", "geo", "security", "regression", "meta"):
        assert stage in REQUIRED_STAGES
