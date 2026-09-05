"""The faceted indexation rule chain."""

from __future__ import annotations

import pytest

from kontur.core.decisions import Decision, ReasonCode
from kontur.core.provenance import Sourced
from kontur.engines.faceted import rules
from kontur.engines.faceted.models import (
    FacetCatalog,
    FacetConfig,
    FacetDefinition,
    FacetStatus,
    FilterInventory,
)
from kontur.engines.faceted.pipeline import FacetedIndexationEngine
from kontur.engines.faceted.signals import (
    BusinessValue,
    IntentAssessment,
    IntentLabel,
    SearchDemand,
)

pytestmark = pytest.mark.seo

MEGAWAYS = "/slots/?mechanic=megaways"


# ---------------------------------------------------------------- FACET-001
@pytest.mark.rule("FACET-001")
@pytest.mark.positive
def test_tracking_parameters_canonicalise_to_the_clean_url(facet_engine) -> None:
    decision = facet_engine().decide(f"{MEGAWAYS}&utm_source=vk")
    assert decision.decision is Decision.CANONICAL
    assert decision.canonical_target == MEGAWAYS
    assert ReasonCode.TRACKING_PARAMETER in decision.reasons
    assert decision.rule_ids == ("FACET-001",)


@pytest.mark.rule("FACET-001")
@pytest.mark.positive
def test_sort_parameter_canonicalises_away(facet_engine) -> None:
    decision = facet_engine().decide(f"{MEGAWAYS}&sort=popular")
    assert decision.decision is Decision.CANONICAL
    assert decision.canonical_target == MEGAWAYS
    assert ReasonCode.EXCLUDED_PARAMETER in decision.reasons


@pytest.mark.rule("FACET-001")
@pytest.mark.negative
def test_clean_url_is_not_canonicalised_for_parameters(facet_engine) -> None:
    context = facet_engine().build_context(MEGAWAYS)
    assert rules.rule_excluded_parameters(context) is None


# ---------------------------------------------------------------- FACET-002
@pytest.mark.rule("FACET-002")
@pytest.mark.positive
def test_facet_depth_over_the_budget_is_noindexed(facet_engine) -> None:
    decision = facet_engine().decide("/slots/?mechanic=megaways&provider=pragmatic&theme=egypt")
    assert decision.decision is Decision.NOINDEX
    assert ReasonCode.FACET_DEPTH_EXCEEDED in decision.reasons


@pytest.mark.rule("FACET-002")
@pytest.mark.negative
def test_depth_at_the_limit_still_passes(facet_engine) -> None:
    context = facet_engine().build_context("/slots/?mechanic=megaways&provider=pragmatic")
    assert context.state.depth == 2
    assert rules.rule_facet_depth(context) is None


# ---------------------------------------------------------------- FACET-003
@pytest.mark.rule("FACET-003")
@pytest.mark.positive
def test_empty_filter_state_is_noindexed(facet_engine, crawl_provenance) -> None:
    engine = facet_engine({"inventory": Sourced(FilterInventory(0, 0, 0), crawl_provenance)})
    decision = engine.decide(MEGAWAYS)
    assert decision.decision is Decision.NOINDEX
    assert ReasonCode.EMPTY_RESULT_SET in decision.reasons


@pytest.mark.rule("FACET-003")
@pytest.mark.positive
def test_thin_filter_state_is_noindexed(facet_engine, crawl_provenance) -> None:
    engine = facet_engine({"inventory": Sourced(FilterInventory(2, 2, 0), crawl_provenance)})
    decision = engine.decide(MEGAWAYS)
    assert decision.decision is Decision.NOINDEX
    assert ReasonCode.THIN_CONTENT in decision.reasons


@pytest.mark.rule("FACET-003")
@pytest.mark.negative
def test_healthy_inventory_does_not_trigger_the_thin_rule(facet_engine) -> None:
    context = facet_engine().build_context(MEGAWAYS)
    assert rules.rule_empty_inventory(context) is None


@pytest.mark.rule("FACET-003")
@pytest.mark.negative
def test_missing_inventory_does_not_pretend_the_page_is_empty(facet_engine) -> None:
    engine = facet_engine({"inventory": None})
    context = engine.build_context(MEGAWAYS)
    assert context.inventory is None
    assert rules.rule_empty_inventory(context) is None


# ---------------------------------------------------------- FACET-004 / 005
@pytest.mark.rule("FACET-004")
@pytest.mark.positive
def test_demand_below_the_threshold_canonicalises_to_the_parent(facet_engine, demand_provenance) -> None:
    engine = facet_engine({"demand": Sourced(SearchDemand(4.0, 1), demand_provenance)})
    decision = engine.decide(MEGAWAYS)
    assert decision.decision is Decision.CANONICAL
    assert ReasonCode.NO_SEARCH_DEMAND in decision.reasons
    assert decision.canonical_target == "/slots/"


@pytest.mark.rule("FACET-004")
@pytest.mark.negative
def test_measured_demand_above_the_threshold_passes(facet_engine) -> None:
    context = facet_engine().build_context(MEGAWAYS)
    assert rules.rule_no_demand(context) is None


@pytest.mark.rule("FACET-005")
@pytest.mark.positive
def test_missing_demand_data_is_not_read_as_demand(facet_engine) -> None:
    engine = facet_engine({"demand": None})
    decision = engine.decide(MEGAWAYS)
    assert decision.decision is Decision.CANONICAL
    assert ReasonCode.DEMAND_DATA_MISSING in decision.reasons
    assert decision.decision is not Decision.INDEX


@pytest.mark.rule("FACET-005")
@pytest.mark.negative
def test_present_demand_data_skips_the_missing_data_rule(facet_engine) -> None:
    context = facet_engine().build_context(MEGAWAYS)
    assert rules.rule_missing_demand_data(context) is None


# ---------------------------------------------------------------- FACET-006
@pytest.mark.rule("FACET-006")
@pytest.mark.positive
def test_content_duplicating_the_parent_canonicalises(facet_engine, crawl_provenance) -> None:
    engine = facet_engine({"inventory": Sourced(FilterInventory(80, 4, 0), crawl_provenance)})
    decision = engine.decide(MEGAWAYS)
    assert decision.decision is Decision.CANONICAL
    assert ReasonCode.DUPLICATE_CONTENT in decision.reasons
    assert decision.rule_ids == ("FACET-006",), "the duplicate-content rule must be the one that fired"


@pytest.mark.rule("FACET-006")
@pytest.mark.positive
def test_intent_duplicating_the_parent_canonicalises(facet_engine) -> None:
    engine = facet_engine({"intent": IntentAssessment(IntentLabel.COMMERCIAL, 0.95, 0.02)})
    decision = engine.decide(MEGAWAYS)
    assert decision.decision is Decision.CANONICAL
    assert ReasonCode.DUPLICATE_INTENT in decision.reasons
    assert decision.rule_ids == ("FACET-006",), "the duplicate-intent rule must be the one that fired"


@pytest.mark.rule("FACET-006")
@pytest.mark.negative
def test_distinct_intent_and_content_pass(facet_engine) -> None:
    context = facet_engine().build_context(MEGAWAYS)
    assert rules.rule_duplicate_of_parent(context) is None


# ---------------------------------------------------------------- FACET-007
@pytest.mark.rule("FACET-007")
@pytest.mark.positive
def test_all_four_signals_produce_index(facet_engine) -> None:
    decision = facet_engine().decide(MEGAWAYS)
    assert decision.decision is Decision.INDEX
    assert set(decision.reasons) == {
        ReasonCode.SEARCH_DEMAND,
        ReasonCode.UNIQUE_INTENT,
        ReasonCode.UNIQUE_CONTENT,
        ReasonCode.COMMERCIAL_VALUE,
    }


@pytest.mark.rule("FACET-007")
@pytest.mark.negative
def test_missing_business_value_prevents_index_and_names_the_gap(facet_engine, crawl_provenance) -> None:
    engine = facet_engine({"business": Sourced(BusinessValue(2, 84, 0.0), crawl_provenance)})
    decision = engine.decide(MEGAWAYS)
    assert decision.decision is not Decision.INDEX
    assert ReasonCode.LOW_BUSINESS_VALUE in decision.reasons


@pytest.mark.rule("FACET-007")
@pytest.mark.negative
def test_serp_evidence_is_required_when_configured(facet_engine) -> None:
    engine = facet_engine(config=FacetConfig(require_serp_evidence=True))
    decision = engine.decide(MEGAWAYS)
    assert decision.decision is Decision.CANONICAL
    assert ReasonCode.NO_COMPETITOR_EVIDENCE in decision.reasons


# ---------------------------------------------------------------- FACET-008
@pytest.mark.rule("FACET-008")
@pytest.mark.positive
def test_no_business_value_with_weak_demand_is_noindexed(
    facet_engine, crawl_provenance, demand_provenance
) -> None:
    engine = facet_engine(
        {
            "demand": Sourced(SearchDemand(90.0, 4), demand_provenance),
            "business": Sourced(BusinessValue(0, 84, 0.0), crawl_provenance),
        }
    )
    decision = engine.decide(MEGAWAYS)
    assert decision.decision is Decision.NOINDEX
    assert ReasonCode.LOW_BUSINESS_VALUE in decision.reasons


@pytest.mark.rule("FACET-008")
@pytest.mark.negative
def test_strong_demand_protects_a_low_value_facet_from_noindex(
    facet_engine, crawl_provenance
) -> None:
    """3200/month is far above 5x the 30/month floor, so FACET-008 stands down."""
    engine = facet_engine({"business": Sourced(BusinessValue(0, 84, 0.0), crawl_provenance)})
    context = engine.build_context(MEGAWAYS)
    assert rules.rule_low_business_value(context) is None


# ---------------------------------------------------------------- FACET-009
@pytest.mark.rule("FACET-009")
@pytest.mark.positive
def test_deprecated_facet_redirects_to_its_replacement(controller, crawl_provenance) -> None:
    catalog = FacetCatalog.of(
        [
            FacetDefinition("mechanic", "Mechanic"),
            FacetDefinition("mechanics", "Old mechanic", status=FacetStatus.DEPRECATED, replacement="mechanic"),
        ]
    )
    engine = FacetedIndexationEngine(catalog=catalog, parameters=controller)
    decision = engine.decide("/slots/?mechanics=megaways")
    assert decision.decision is Decision.REDIRECT
    assert decision.redirect_target == "/slots/?mechanic=megaways"
    assert ReasonCode.DEPRECATED_FACET in decision.reasons


@pytest.mark.rule("FACET-009")
@pytest.mark.negative
def test_deprecated_facet_must_declare_a_replacement() -> None:
    from kontur.core.errors import ConfigurationError

    with pytest.raises(ConfigurationError, match="replacement"):
        FacetDefinition("mechanics", "Old", status=FacetStatus.DEPRECATED)


# ---------------------------------------------------------------- FACET-010
@pytest.mark.rule("FACET-010")
@pytest.mark.positive
def test_first_page_canonicalises_to_the_base_url(facet_engine) -> None:
    decision = facet_engine().decide(f"{MEGAWAYS}&page=1")
    assert decision.decision is Decision.CANONICAL
    assert decision.canonical_target == MEGAWAYS
    assert ReasonCode.PAGINATION_FIRST_PAGE in decision.reasons


@pytest.mark.rule("FACET-010")
@pytest.mark.positive
def test_deep_page_of_a_large_set_is_indexable(facet_engine) -> None:
    decision = facet_engine().decide(f"{MEGAWAYS}&page=3")
    assert decision.decision is Decision.INDEX
    assert ReasonCode.PAGINATION_DEEP_SET in decision.reasons


@pytest.mark.rule("FACET-010")
@pytest.mark.negative
def test_deep_page_of_a_shallow_set_canonicalises(facet_engine, crawl_provenance) -> None:
    engine = facet_engine({"inventory": Sourced(FilterInventory(20, 18, 2, pages=1), crawl_provenance)})
    decision = engine.decide(f"{MEGAWAYS}&page=4")
    assert decision.decision is Decision.CANONICAL
    assert decision.canonical_target == MEGAWAYS


@pytest.mark.rule("FACET-010")
@pytest.mark.negative
def test_url_without_pagination_skips_the_pagination_rule(facet_engine) -> None:
    context = facet_engine().build_context(MEGAWAYS)
    assert context.pagination is None
    assert rules.rule_pagination(context) is None


# ---------------------------------------------------------------- FACET-011
@pytest.mark.rule("FACET-011")
@pytest.mark.positive
def test_blocked_parameter_produces_block(facet_engine) -> None:
    decision = facet_engine().decide(f"{MEGAWAYS}&phpsessid=abc123")
    assert decision.decision is Decision.BLOCK
    assert ReasonCode.BLOCKED_PARAMETER in decision.reasons


@pytest.mark.rule("FACET-011")
@pytest.mark.negative
def test_ordinary_url_is_not_blocked(facet_engine) -> None:
    context = facet_engine().build_context(MEGAWAYS)
    assert rules.rule_blocked_parameter(context) is None


# ---------------------------------------------------------------- FACET-012
@pytest.mark.rule("FACET-012")
@pytest.mark.positive
def test_parameter_awaiting_analysis_is_never_indexed(facet_engine) -> None:
    decision = facet_engine().decide("/slots/?rtp=96plus")
    assert decision.decision is Decision.CANONICAL
    assert ReasonCode.AWAITING_ANALYSIS in decision.reasons
    assert decision.canonical_target == "/slots/"


@pytest.mark.rule("FACET-012")
@pytest.mark.negative
def test_decided_parameters_do_not_trigger_the_hold(facet_engine) -> None:
    context = facet_engine().build_context(MEGAWAYS)
    assert rules.rule_pending_analysis(context) is None


# ------------------------------------------------------------------ pipeline
def test_every_decision_carries_the_eight_stage_trace(facet_engine) -> None:
    decision = facet_engine().decide(MEGAWAYS)
    stages = [step.stage for step in decision.trace]
    for stage in ("query", "filter_state", "search_demand", "intent", "serp_evidence",
                  "content_uniqueness", "business_value", "indexation_decision"):
        assert stage in stages, f"stage {stage} missing from the audit trail"


def test_rule_chain_is_total(facet_engine) -> None:
    engine = facet_engine()
    for url in (MEGAWAYS, "/slots/", "/slots/?rtp=96plus", f"{MEGAWAYS}&page=2", "/slots/?phpsessid=x"):
        assert engine.decide(url).reasons, f"{url} produced a decision with no reason"


# ------------------------------------------------- missing-signal robustness
@pytest.mark.rule("FACET-006")
@pytest.mark.negative
def test_a_missing_intent_assessment_does_not_crash_the_chain(facet_engine) -> None:
    decision = facet_engine({"intent": None}).decide(MEGAWAYS)
    assert decision.decision is Decision.CANONICAL
    assert ReasonCode.DUPLICATE_INTENT in decision.reasons
    assert decision.rule_ids == ("FACET-007",)


@pytest.mark.rule("FACET-006")
@pytest.mark.negative
def test_missing_inventory_falls_through_to_the_signal_check(facet_engine) -> None:
    decision = facet_engine({"inventory": None}).decide(MEGAWAYS)
    assert decision.decision is Decision.CANONICAL
    assert ReasonCode.DUPLICATE_CONTENT in decision.reasons
    assert decision.rule_ids == ("FACET-007",)


@pytest.mark.rule("FACET-008")
@pytest.mark.negative
def test_the_business_rule_needs_both_inputs(facet_engine) -> None:
    """With only one of the two signals present the rule stands down instead of guessing."""
    engine = facet_engine({"business": None})
    context = engine.build_context(MEGAWAYS)
    assert rules.rule_low_business_value(context) is None

    engine = facet_engine({"demand": None})
    context = engine.build_context(MEGAWAYS)
    assert rules.rule_low_business_value(context) is None


@pytest.mark.rule("FACET-008")
@pytest.mark.negative
def test_demand_exactly_at_the_strong_mark_protects_the_facet(
    facet_engine, crawl_provenance, demand_provenance
) -> None:
    """The strong-demand mark is inclusive: 5x the floor is strong."""
    from kontur.engines.faceted.models import FacetConfig

    config = FacetConfig()
    strong = config.min_monthly_demand * config.weak_demand_multiplier
    engine = facet_engine(
        {
            "demand": Sourced(SearchDemand(strong, 5), demand_provenance),
            "business": Sourced(BusinessValue(0, 84, 0.0), crawl_provenance),
        },
        config=config,
    )
    assert rules.rule_low_business_value(engine.build_context(MEGAWAYS)) is None


@pytest.mark.rule("FACET-010")
@pytest.mark.positive
def test_a_two_page_set_is_deep_enough(facet_engine, crawl_provenance) -> None:
    """min_pages_for_deep_pagination is inclusive."""
    engine = facet_engine({"inventory": Sourced(FilterInventory(40, 33, 2, pages=2), crawl_provenance)})
    decision = engine.decide(f"{MEGAWAYS}&page=2")
    assert decision.decision is Decision.INDEX
    assert ReasonCode.PAGINATION_DEEP_SET in decision.reasons


@pytest.mark.rule("FACET-009")
@pytest.mark.negative
def test_an_active_facet_with_a_successor_is_not_redirected(controller) -> None:
    """A replacement is only acted on once the facet is actually deprecated."""
    catalog = FacetCatalog.of(
        [
            FacetDefinition("mechanic", "Mechanic"),
            FacetDefinition("mechanics", "Newer name planned", replacement="mechanic"),
        ]
    )
    engine = FacetedIndexationEngine(catalog=catalog, parameters=controller)
    decision = engine.decide("/slots/?mechanics=megaways")
    assert decision.decision is not Decision.REDIRECT
