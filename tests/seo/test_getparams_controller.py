"""Conflict resolution and the effective parameter policy."""

from __future__ import annotations

import pytest

from kontur.core.errors import ConfigurationError
from kontur.engines.getparams.controller import GetParameterController, ParamPolicy
from kontur.engines.getparams.models import (
    ParamDecision,
    ParamReason,
    merge_rulings,
    most_restrictive_param_decision,
)

pytestmark = pytest.mark.seo


@pytest.mark.rule("GETP-002")
@pytest.mark.positive
def test_conflicting_policies_resolve_to_the_more_prohibitive_one(
    controller: GetParameterController, crawl_provenance
) -> None:
    assert controller.decision("mechanic") is ParamDecision.SEO_HUB

    controller.add_policy(
        ParamPolicy("mechanic", ParamDecision.EXCLUDE, "legacy robots.txt Clean-param", crawl_provenance)
    )
    ruling = controller.ruling("mechanic")

    assert ruling.decision is ParamDecision.EXCLUDE
    assert "GETP-002" in ruling.rule_ids
    assert ParamReason.SEARCH_DEMAND in ruling.reasons, "the losing rationale must stay visible"
    assert ParamReason.MANUAL_OVERRIDE in ruling.reasons


@pytest.mark.rule("GETP-002")
@pytest.mark.negative
def test_a_permissive_policy_cannot_loosen_a_restrictive_classification(
    controller: GetParameterController, crawl_provenance
) -> None:
    controller.add_policy(
        ParamPolicy("utm_source", ParamDecision.SEO_HUB, "someone wanted utm landing pages", crawl_provenance)
    )
    assert controller.decision("utm_source") is ParamDecision.EXCLUDE


@pytest.mark.rule("GETP-002")
@pytest.mark.negative
def test_merging_rulings_of_different_parameters_is_refused(controller: GetParameterController) -> None:
    with pytest.raises(ConfigurationError, match="different parameters"):
        merge_rulings([controller.ruling("sort"), controller.ruling("page")])


@pytest.mark.rule("GETP-002")
@pytest.mark.positive
@pytest.mark.parametrize(
    ("decisions", "expected"),
    [
        ([ParamDecision.SEO_HUB, ParamDecision.ANALYZE], ParamDecision.ANALYZE),
        ([ParamDecision.ANALYZE, ParamDecision.CONTEXT_DEPENDENT], ParamDecision.CONTEXT_DEPENDENT),
        ([ParamDecision.CONTEXT_DEPENDENT, ParamDecision.EXCLUDE], ParamDecision.EXCLUDE),
        ([ParamDecision.EXCLUDE, ParamDecision.BLOCK], ParamDecision.BLOCK),
        ([ParamDecision.SEO_HUB, ParamDecision.SEO_HUB], ParamDecision.SEO_HUB),
    ],
)
def test_restrictiveness_lattice(decisions, expected) -> None:
    assert most_restrictive_param_decision(decisions) is expected


@pytest.mark.rule("GETP-002")
@pytest.mark.negative
def test_resolving_an_empty_conflict_is_an_error() -> None:
    with pytest.raises(ConfigurationError):
        most_restrictive_param_decision([])


def test_an_override_replaces_the_automatic_classification(
    controller: GetParameterController, crawl_provenance
) -> None:
    controller.override(
        ParamPolicy(
            "promo_widget",
            ParamDecision.EXCLUDE,
            "widget state, confirmed with the front-end team",
            crawl_provenance,
        )
    )
    ruling = controller.ruling("promo_widget")
    assert ruling.decision is ParamDecision.EXCLUDE
    assert ruling.note and "front-end" in ruling.note


def test_a_policy_without_a_note_is_refused(crawl_provenance) -> None:
    with pytest.raises(ConfigurationError, match="needs a note"):
        ParamPolicy("sort", ParamDecision.EXCLUDE, "  ", crawl_provenance)


def test_unseen_parameters_default_to_analysis() -> None:
    controller = GetParameterController()
    assert controller.decision("never_crawled") is ParamDecision.ANALYZE


def test_rows_are_ordered_by_crawl_impact(controller: GetParameterController) -> None:
    rows = controller.dashboard_rows()
    counts = [row["detected_urls"] for row in rows]
    assert counts == sorted(counts, reverse=True)


def test_summary_groups_parameters_by_decision(controller: GetParameterController) -> None:
    summary = controller.summary()
    assert summary["parameters"] == len(controller.known_parameters)
    assert summary["by_decision"][ParamDecision.EXCLUDE.value] >= 2
    assert "rtp" in summary["pending_review"]


def test_excluded_set_includes_blocked_parameters(controller: GetParameterController) -> None:
    assert "phpsessid" in controller.excluded_parameters()
    assert "phpsessid" in controller.blocked_parameters()
    assert "mechanic" in controller.indexable_parameters()
    assert "page" in controller.context_dependent_parameters()


def test_the_merged_ruling_keeps_the_demand_export(controller, crawl_provenance) -> None:
    """Merging must not drop the evidence that justified the promotion."""
    automatic = controller.automatic_ruling("mechanic")
    assert automatic is not None and automatic.demand is not None

    controller.add_policy(
        ParamPolicy("mechanic", ParamDecision.EXCLUDE, "legacy policy", crawl_provenance)
    )
    merged = controller.ruling("mechanic")
    assert merged.demand is not None, "the demand export disappeared during the merge"
    assert merged.demand.value.total_monthly_demand == automatic.demand.value.total_monthly_demand


def test_merging_keeps_the_largest_observed_counts(controller, crawl_provenance) -> None:
    controller.add_policy(ParamPolicy("sort", ParamDecision.BLOCK, "manual block", crawl_provenance))
    merged = controller.ruling("sort")
    assert merged.detected_urls == 12440
    assert merged.distinct_values == 6


def test_merging_a_single_ruling_is_a_no_op(controller) -> None:
    single = controller.ruling("sort")
    assert merge_rulings([single]).decision is single.decision
    assert merge_rulings([single]).reasons == single.reasons


def test_observations_keep_the_largest_crawl(controller, observation) -> None:
    controller.observe([observation("sort", 5, 2)])
    assert controller.ruling("sort").detected_urls == 12440
    controller.observe([observation("sort", 99999, 2)])
    assert controller.ruling("sort").detected_urls == 99999


def test_demand_must_be_sourced(controller) -> None:
    from kontur.core.errors import ConfigurationError
    from kontur.engines.getparams.models import ParamDemand

    with pytest.raises(ConfigurationError, match="Sourced"):
        controller.set_demand("mechanic", ParamDemand("mechanic", 7, 5400.0))


@pytest.mark.rule("GETP-002")
@pytest.mark.positive
def test_the_conflict_rule_is_recorded_only_when_sources_disagree(
    controller, crawl_provenance
) -> None:
    """GETP-002 marks a resolved conflict; agreement is not a conflict."""
    agreeing = ParamPolicy("sort", ParamDecision.EXCLUDE, "same verdict as the classifier", crawl_provenance)
    controller.add_policy(agreeing)
    assert "GETP-002" not in merge_rulings(
        [controller.automatic_ruling("sort"), agreeing.as_ruling(None)]
    ).rule_ids

    disagreeing = ParamPolicy("page", ParamDecision.BLOCK, "manual crawl block", crawl_provenance)
    assert "GETP-002" in merge_rulings(
        [controller.automatic_ruling("page"), disagreeing.as_ruling(None)]
    ).rule_ids


def test_a_re_crawl_with_the_same_counts_wins(controller, observation, alice_provenance) -> None:
    """The newest export replaces an equal-sized older one, provenance and all."""
    from kontur.engines.getparams.models import ParamObservation

    fresh = ParamObservation("sort", 12440, 6, alice_provenance)
    controller.observe([fresh])
    assert controller.ruling("sort").evidence.items[0].source == "yandex_webmaster:alice_visibility"


def test_the_summary_counts_each_parameter_once(controller) -> None:
    summary = controller.summary()
    assert sum(summary["by_decision"].values()) == summary["parameters"] == 7
    assert summary["by_decision"]["EXCLUDE"] == 2
    assert summary["by_decision"]["BLOCK"] == 1
    assert summary["by_decision"]["SEO_HUB"] == 1
    assert summary["detected_urls"] == 48210 + 12440 + 9100 + 1290 + 840 + 380 + 210


def test_a_ruling_without_a_crawl_reports_no_urls(crawl_provenance) -> None:
    controller = GetParameterController()
    controller.add_policy(
        ParamPolicy("never_crawled", ParamDecision.EXCLUDE, "declared by the SEO team", crawl_provenance)
    )
    ruling = controller.ruling("never_crawled")
    assert ruling.detected_urls == 0
    assert ruling.distinct_values == 0


def test_the_fallback_ruling_reports_no_counts() -> None:
    ruling = GetParameterController().ruling("unseen")
    assert ruling.detected_urls == 0
    assert ruling.decision is ParamDecision.ANALYZE
