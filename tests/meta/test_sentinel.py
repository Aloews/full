"""The Test Sentinel — floors the suite is never allowed to fall below.

Meta-tests check the *shape* of the suite; the sentinel checks its *size and
strength*. A refactor that quietly deletes half the negative tests, or a merge
that drops the meta layer, fails here rather than being discovered months later
when a bad indexation decision ships.

The floors are deliberately below the current counts: they are a ratchet
against erosion, not a target to game. Raise them when the suite grows.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kontur.core.registry import RULES, SCORING_FUNCTIONS, critical_rules
from kontur.testing.inventory import build_inventory, find_repo_root
from tools.mutation.config import CRITICAL_THRESHOLD
from tools.mutation.sentinel import run_sentinel

pytestmark = pytest.mark.meta

REPO = find_repo_root()

EXPECTED_MINIMUM = 380
EXPECTED_CRITICAL = 110
EXPECTED_NEGATIVE = 75
EXPECTED_POSITIVE = 55
EXPECTED_META = 14
EXPECTED_REGRESSION = 17
EXPECTED_BOUNDARY = 8
EXPECTED_SECURITY = 25
MUTATION_THRESHOLD = CRITICAL_THRESHOLD


@pytest.fixture(scope="module")
def inventory():
    return build_inventory(REPO / "tests")


def test_test_count_floor(inventory) -> None:
    assert len(inventory) >= EXPECTED_MINIMUM, (
        f"the suite shrank to {len(inventory)} tests, below the {EXPECTED_MINIMUM} floor"
    )


def test_critical_rule_coverage_floor(inventory) -> None:
    critical = {rule.id for rule in critical_rules()}
    covering = [t for t in inventory.tests if set(t.rule_ids) & critical]
    assert len(covering) >= EXPECTED_CRITICAL, (
        f"only {len(covering)} tests cover critical rules, below the {EXPECTED_CRITICAL} floor"
    )


def test_negative_test_floor(inventory) -> None:
    count = len(inventory.with_marker("negative"))
    assert count >= EXPECTED_NEGATIVE, f"{count} negative tests is below the {EXPECTED_NEGATIVE} floor"


def test_positive_test_floor(inventory) -> None:
    count = len(inventory.with_marker("positive"))
    assert count >= EXPECTED_POSITIVE, f"{count} positive tests is below the {EXPECTED_POSITIVE} floor"


def test_meta_test_floor(inventory) -> None:
    count = len(inventory.with_marker("meta"))
    assert count >= EXPECTED_META, f"{count} meta-tests is below the {EXPECTED_META} floor"


def test_regression_and_boundary_floors(inventory) -> None:
    assert len(inventory.with_marker("regression")) >= EXPECTED_REGRESSION
    assert len(inventory.with_marker("boundary")) >= EXPECTED_BOUNDARY
    assert len(inventory.with_marker("security")) >= EXPECTED_SECURITY


def test_every_rule_and_scoring_function_stays_covered(inventory) -> None:
    assert inventory.covered_rules() >= set(RULES), "a rule lost its tests"
    covered_scoring = {name for name in SCORING_FUNCTIONS if inventory.boundary_tests_for(name)}
    assert covered_scoring == set(SCORING_FUNCTIONS), "a scoring function lost its boundary tests"


@pytest.mark.slow
def test_intentionally_broken_fixture_is_detected() -> None:
    """The suite must go red when a real module is deliberately broken."""
    result = run_sentinel()
    assert result.trustworthy, result.detail


@pytest.mark.slow
def test_mutation_score_meets_the_threshold() -> None:
    """Read the campaign report when CI produced one, otherwise measure a module.

    The full campaign is a CI stage; running it inside every local test run would
    make the suite unusable, so the fast path measures one core-SEO module.
    """
    report_path = Path(REPO / "reports" / "mutation.json")
    if report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["overall_score"] >= MUTATION_THRESHOLD, (
            f"mutation score {report['overall_score']:.1%} is below {MUTATION_THRESHOLD:.0%}"
        )
        assert report["passed"], "at least one module is below its own mutation threshold"
        return

    from tools.mutation.config import CampaignSettings
    from tools.mutation.runner import run_campaign

    campaign = run_campaign(
        CampaignSettings(max_mutants_per_module=6),
        modules=["kontur/engines/faceted/rules.py"],
    )
    assert campaign.overall_score >= MUTATION_THRESHOLD, campaign.render()
