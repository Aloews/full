"""T-META-001 — the suite must fail when the implementation is broken.

This is the check the whole test-governance layer rests on. Everything else
measures the *shape* of the suite; this measures whether it can actually detect
a controlled implementation failure.
"""

from __future__ import annotations

import pytest

from tools.mutation.config import SENTINEL_MARKER, SENTINEL_MODULE
from tools.mutation.sentinel import UNTRUSTWORTHY, run_sentinel

pytestmark = [pytest.mark.meta, pytest.mark.slow]


@pytest.fixture(scope="module")
def sentinel():
    return run_sentinel()


def test_t_meta_001_the_suite_detects_a_controlled_break(sentinel) -> None:
    assert sentinel.baseline_passed, f"the suite was already red: {sentinel.detail}"
    assert sentinel.break_applied, sentinel.detail
    assert sentinel.break_detected, f"{UNTRUSTWORTHY}\n{sentinel.detail}"
    assert sentinel.trustworthy


def test_the_sentinel_breaks_something_real() -> None:
    """The anchor must still exist, or the sentinel is breaking nothing."""
    from tools.mutation.runner import repo_root

    source = (repo_root() / SENTINEL_MODULE).read_text(encoding="utf-8")
    assert SENTINEL_MARKER in source, (
        f"the sentinel anchor disappeared from {SENTINEL_MODULE}; "
        "point it at the current implementation instead of deleting the check"
    )


def test_the_sentinel_reports_an_untrustworthy_suite_clearly(sentinel) -> None:
    payload = sentinel.to_dict()
    assert payload["check"] == "T-META-001"
    assert payload["module"] == SENTINEL_MODULE
    assert payload["break"], "the controlled break must be described in the report"
    assert "PASS" in sentinel.render()
