"""Level 2 — tests about the tests.

A green suite means nothing if the suite cannot fail. These meta-tests check the
properties that make the rest of the suite trustworthy: that every test is
discovered, that every critical rule is covered from both sides, that every test
asserts something, that nothing is skipped without a reason, and that the
fixtures, endpoints and scoring functions the suite claims to cover really exist.

    MT-001  every test is discovered by pytest
    MT-002  every critical rule has at least one positive test
    MT-003  every critical rule has at least one negative test
    MT-004  every test contains an assertion
    MT-005  no test passes regardless of the result
    MT-006  no unexplained skipped tests
    MT-007  every requested fixture exists
    MT-008  every API endpoint has an integration test
    MT-009  every critical SEO rule has a regression test
    MT-010  every scoring function has boundary tests
"""

from __future__ import annotations

import re
import subprocess
import sys

import pytest

from kontur.api.app import create_app, endpoint_paths
from kontur.core.registry import (
    RULES,
    SCORING_FUNCTIONS,
    critical_rules,
    rules_requiring_regression,
)
from kontur.testing.inventory import TestInventory, build_inventory, find_repo_root

pytestmark = pytest.mark.meta

REPO = find_repo_root()


@pytest.fixture(scope="module")
def inventory() -> TestInventory:
    return build_inventory(REPO / "tests")


# ------------------------------------------------------------------- MT-001
def test_mt_001_every_test_is_discovered_by_pytest(inventory: TestInventory) -> None:
    """A test file pytest cannot collect is a test that never runs."""
    assert inventory.collection_errors == (), f"unparseable test modules: {inventory.collection_errors}"
    assert len(inventory) > 0, "the inventory found no tests at all"

    result = subprocess.run(  # noqa: S603 - fixed argv, no shell
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests"],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, f"pytest could not collect the suite:\n{result.stdout[-2000:]}"

    collected_files: set[str] = set()
    collected_names: set[str] = set()
    for line in result.stdout.splitlines():
        match = re.match(r"^(tests/[\w/]+\.py)::([\w]+)", line.strip())
        if match:
            collected_files.add(match.group(1))
            collected_names.add(f"{match.group(1)}::{match.group(2)}")

    missing_files = {module.path for module in inventory.modules if module.tests} - collected_files
    assert not missing_files, f"test modules pytest did not collect: {sorted(missing_files)}"

    missing_tests = {test.node_id for test in inventory.tests} - collected_names
    assert not missing_tests, f"tests pytest did not collect: {sorted(missing_tests)[:10]}"


# ------------------------------------------------------------ MT-002 / 003
def test_mt_002_every_critical_rule_has_a_positive_test(inventory: TestInventory) -> None:
    uncovered = [rule.id for rule in critical_rules() if not inventory.positive_tests_for(rule.id)]
    assert not uncovered, f"critical rules without a positive test: {uncovered}"


def test_mt_003_every_critical_rule_has_a_negative_test(inventory: TestInventory) -> None:
    uncovered = [rule.id for rule in critical_rules() if not inventory.negative_tests_for(rule.id)]
    assert not uncovered, f"critical rules without a negative test: {uncovered}"


# ------------------------------------------------------------------- MT-004
def test_mt_004_every_test_contains_an_assertion(inventory: TestInventory) -> None:
    offenders = [test.node_id for test in inventory.without_assertions()]
    assert not offenders, f"tests that assert nothing: {offenders}"


# ------------------------------------------------------------------- MT-005
def test_mt_005_no_test_passes_regardless_of_the_result(inventory: TestInventory) -> None:
    """Tautological assertions (`assert True`, `assert x == x`) prove nothing.

    The stronger form of this check — that the suite actually fails when the
    implementation breaks — is T-META-001 in test_suite_integrity.py.
    """
    offenders = [test.node_id for test in inventory.tautological()]
    assert not offenders, f"tests whose only assertions are tautologies: {offenders}"


# ------------------------------------------------------------------- MT-006
def test_mt_006_no_unexplained_skipped_tests(inventory: TestInventory) -> None:
    offenders = {test.node_id: test.unexplained_skips for test in inventory.unexplained_skips()}
    assert not offenders, f"skipped tests without a reason: {offenders}"
    for test in inventory.tests:
        for marker, reason in test.skip_markers:
            assert len(reason.strip()) >= 10, (
                f"{test.node_id} is {marker}ped with a reason too short to review: {reason!r}"
            )


# ------------------------------------------------------------------- MT-007
def test_mt_007_every_requested_fixture_exists(inventory: TestInventory) -> None:
    missing = inventory.missing_fixtures()
    assert not missing, f"tests requesting fixtures nothing defines: {missing}"


# ------------------------------------------------------------------- MT-008
def test_mt_008_every_api_endpoint_has_an_integration_test(inventory: TestInventory) -> None:
    paths = endpoint_paths(create_app())
    assert paths, "the app exposes no routes"
    uncovered = [path for path in paths if not inventory.tests_for_endpoint(path)]
    assert not uncovered, f"API routes without a test: {uncovered}"


# ------------------------------------------------------------------- MT-009
def test_mt_009_every_critical_seo_rule_has_a_regression_test(inventory: TestInventory) -> None:
    uncovered = [
        rule.id for rule in rules_requiring_regression() if not inventory.regression_tests_for(rule.id)
    ]
    assert not uncovered, f"critical SEO rules without a regression test: {uncovered}"


# ------------------------------------------------------------------- MT-010
def test_mt_010_every_scoring_function_has_boundary_tests(inventory: TestInventory) -> None:
    uncovered = [name for name in SCORING_FUNCTIONS if not inventory.boundary_tests_for(name)]
    assert not uncovered, f"scoring functions without a boundary test: {uncovered}"


# --------------------------------------------------------- supporting checks
def test_every_rule_id_used_by_a_test_exists_in_the_registry(inventory: TestInventory) -> None:
    """A typo in a rule marker would otherwise satisfy nothing, silently."""
    unknown = sorted(inventory.covered_rules() - set(RULES))
    assert not unknown, f"tests reference rule ids that do not exist: {unknown}"


def test_every_registered_rule_is_referenced_by_at_least_one_test(inventory: TestInventory) -> None:
    uncovered = sorted(set(RULES) - inventory.covered_rules())
    assert not uncovered, f"rules no test refers to: {uncovered}"


def test_positive_and_negative_markers_are_used_deliberately(inventory: TestInventory) -> None:
    for test in inventory.tests:
        if test.is_positive or test.is_negative:
            assert test.rule_ids, f"{test.node_id} is marked positive/negative but names no rule"
        assert not (test.is_positive and test.is_negative), (
            f"{test.node_id} claims to be both a positive and a negative test"
        )


def test_the_suite_covers_every_level(inventory: TestInventory) -> None:
    for marker in ("unit", "integration", "api", "e2e", "security", "seo", "aeo", "geo", "regression"):
        assert inventory.with_marker(marker) or any(
            marker in module.path for module in inventory.modules
        ), f"no tests at the {marker} level"
