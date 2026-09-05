"""T-META-001 — is this test suite capable of failing?

A green suite proves nothing unless it goes red when the implementation breaks.
The sentinel introduces one controlled, documented break into a real module and
requires the corresponding tests to fail:

    BROKEN IMPLEMENTATION
            |
            v
    EXPECTED TEST FAILURE          -> the suite is trustworthy

    BROKEN IMPLEMENTATION
            |
            v
    ALL TESTS PASS                 -> FAILED: TEST SUITE IS NOT TRUSTWORTHY

The break inverts rule GETP-002: conflicting GET-parameter policies would
resolve to the *least* restrictive variant. Any suite that cannot see that is
not protecting the indexation graph.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.mutation.config import (
    SENTINEL_DESCRIPTION,
    SENTINEL_MARKER,
    SENTINEL_MODULE,
    SENTINEL_REPLACEMENT,
    SENTINEL_TESTS,
)
from tools.mutation.runner import Sandbox, repo_root

UNTRUSTWORTHY = "FAILED — TEST SUITE IS NOT TRUSTWORTHY"


@dataclass(frozen=True, slots=True)
class SentinelResult:
    baseline_passed: bool
    break_applied: bool
    break_detected: bool
    module: str
    tests: tuple[str, ...]
    description: str
    detail: str = ""

    @property
    def trustworthy(self) -> bool:
        return self.baseline_passed and self.break_applied and self.break_detected

    def to_dict(self) -> dict[str, Any]:
        return {
            "check": "T-META-001",
            "module": self.module,
            "tests": list(self.tests),
            "break": self.description,
            "baseline_passed": self.baseline_passed,
            "break_applied": self.break_applied,
            "break_detected": self.break_detected,
            "trustworthy": self.trustworthy,
            "detail": self.detail,
        }

    def render(self) -> str:
        if self.trustworthy:
            return (
                f"T-META-001 PASS — the suite detected the controlled break\n"
                f"  module: {self.module}\n  break:  {self.description}"
            )
        return f"T-META-001 {UNTRUSTWORTHY}\n  {self.detail}"


def run_sentinel(*, timeout: int = 180, root: Path | None = None) -> SentinelResult:
    """Break one rule on purpose and require the suite to notice."""
    with Sandbox(root or repo_root()) as sandbox:
        original = sandbox.read(SENTINEL_MODULE)

        if SENTINEL_MARKER not in original:
            return SentinelResult(
                baseline_passed=False,
                break_applied=False,
                break_detected=False,
                module=SENTINEL_MODULE,
                tests=SENTINEL_TESTS,
                description=SENTINEL_DESCRIPTION,
                detail=(
                    f"the sentinel anchor is gone from {SENTINEL_MODULE}: "
                    f"{SENTINEL_MARKER!r} no longer appears. Update the sentinel so it keeps "
                    "breaking something real."
                ),
            )

        code, output = sandbox.run_tests(SENTINEL_TESTS, timeout=timeout)
        if code != 0:
            return SentinelResult(
                baseline_passed=False,
                break_applied=False,
                break_detected=False,
                module=SENTINEL_MODULE,
                tests=SENTINEL_TESTS,
                description=SENTINEL_DESCRIPTION,
                detail=f"the suite is already red before the break was applied:\n{output}",
            )

        broken = original.replace(SENTINEL_MARKER, SENTINEL_REPLACEMENT, 1)
        sandbox.write(SENTINEL_MODULE, broken)
        try:
            code, output = sandbox.run_tests(SENTINEL_TESTS, timeout=timeout)
        finally:
            sandbox.write(SENTINEL_MODULE, original)

        detected = code != 0
        return SentinelResult(
            baseline_passed=True,
            break_applied=True,
            break_detected=detected,
            module=SENTINEL_MODULE,
            tests=SENTINEL_TESTS,
            description=SENTINEL_DESCRIPTION,
            detail=(
                ""
                if detected
                else (
                    f"{SENTINEL_MODULE} was broken ({SENTINEL_DESCRIPTION}) and "
                    f"{', '.join(SENTINEL_TESTS)} still passed. A suite that cannot see this "
                    "cannot be trusted to protect anything else."
                )
            ),
        )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the test-suite integrity check (T-META-001)")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args(argv)

    result = run_sentinel(timeout=args.timeout)
    print(result.render())
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    return 0 if result.trustworthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
