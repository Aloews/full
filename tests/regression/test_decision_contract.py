"""The decision envelope is a published contract; drift here breaks consumers."""

from __future__ import annotations

import json

import pytest

from kontur.core.decisions import Decision, DecisionRecord, ReasonCode

pytestmark = [pytest.mark.regression, pytest.mark.seo]

#: The exact shape documented in the README and consumed by the dashboard.
GOLDEN = {
    "url": "/slots/megaways/",
    "decision": "INDEX",
    "reason": ["search_demand", "unique_intent", "unique_content", "commercial_value"],
}


@pytest.mark.rule("FACET-007")
@pytest.mark.regression
def test_the_published_envelope_is_stable() -> None:
    record = DecisionRecord(
        url="/slots/megaways/",
        decision=Decision.INDEX,
        reasons=(
            ReasonCode.SEARCH_DEMAND,
            ReasonCode.UNIQUE_INTENT,
            ReasonCode.UNIQUE_CONTENT,
            ReasonCode.COMMERCIAL_VALUE,
        ),
    )
    payload = record.to_dict()
    assert {key: payload[key] for key in GOLDEN} == GOLDEN
    assert json.loads(json.dumps(payload))["reason"] == GOLDEN["reason"]


@pytest.mark.rule("FACET-007")
@pytest.mark.regression
def test_the_envelope_keeps_its_additive_fields() -> None:
    record = DecisionRecord(
        url="/slots/megaways/",
        decision=Decision.INDEX,
        reasons=(ReasonCode.SEARCH_DEMAND,),
        rule_ids=("FACET-007",),
    )
    payload = record.to_dict()
    for key in ("rules", "confidence", "is_sample", "evidence", "trace"):
        assert key in payload, f"{key} disappeared from the decision envelope"


@pytest.mark.rule("FACET-001")
@pytest.mark.regression
def test_tracking_parameters_stay_a_canonical_not_a_noindex(facet_engine) -> None:
    """A canonical keeps the signals; a noindex throws them away."""
    record = facet_engine().decide("/slots/?mechanic=megaways&utm_source=vk")
    assert record.decision is Decision.CANONICAL
    assert record.canonical_target == "/slots/?mechanic=megaways"


@pytest.mark.rule("FACET-002")
@pytest.mark.regression
def test_depth_limit_stays_at_two_by_default(facet_engine) -> None:
    engine = facet_engine()
    assert engine.config.max_depth == 2
    assert engine.decide("/slots/?mechanic=megaways&provider=pragmatic&theme=egypt").decision is Decision.NOINDEX


@pytest.mark.rule("FACET-003")
@pytest.mark.regression
def test_the_thin_content_floor_stays_at_three_items(facet_engine, crawl_provenance) -> None:
    from kontur.core.provenance import Sourced
    from kontur.engines.faceted.models import FilterInventory

    engine = facet_engine()
    assert engine.config.min_items == 3
    at_floor = facet_engine({"inventory": Sourced(FilterInventory(3, 3, 1), crawl_provenance)})
    assert at_floor.decide("/slots/?mechanic=megaways").decision is not Decision.NOINDEX


@pytest.mark.rule("FACET-004")
@pytest.mark.regression
def test_the_demand_floor_stays_at_thirty(facet_engine) -> None:
    assert facet_engine().config.min_monthly_demand == 30.0


@pytest.mark.rule("FACET-005")
@pytest.mark.regression
def test_absent_demand_never_produces_index(facet_engine) -> None:
    record = facet_engine({"demand": None}).decide("/slots/?mechanic=megaways")
    assert record.decision is not Decision.INDEX
    assert ReasonCode.DEMAND_DATA_MISSING in record.reasons


@pytest.mark.rule("FACET-006")
@pytest.mark.regression
def test_the_uniqueness_floor_stays_at_035(facet_engine) -> None:
    assert facet_engine().config.min_uniqueness == 0.35


@pytest.mark.rule("FACET-010")
@pytest.mark.regression
def test_first_page_always_canonicalises_to_the_base(facet_engine) -> None:
    record = facet_engine().decide("/slots/?mechanic=megaways&page=1")
    assert record.decision is Decision.CANONICAL
    assert record.canonical_target == "/slots/?mechanic=megaways"


@pytest.mark.rule("FACET-012")
@pytest.mark.regression
def test_an_analyze_parameter_never_yields_index(facet_engine) -> None:
    record = facet_engine().decide("/slots/?rtp=96plus")
    assert record.decision is not Decision.INDEX
    assert ReasonCode.AWAITING_ANALYSIS in record.reasons


@pytest.mark.rule("FACET-007")
@pytest.mark.regression
def test_the_rule_chain_order_is_fixed() -> None:
    from kontur.engines.faceted.rules import RULE_CHAIN

    assert [rule.__name__ for rule in RULE_CHAIN] == [
        "rule_blocked_parameter",
        "rule_excluded_parameters",
        "rule_deprecated_facet",
        "rule_pagination",
        "rule_facet_depth",
        "rule_empty_inventory",
        "rule_pending_analysis",
        "rule_missing_demand_data",
        "rule_no_demand",
        "rule_duplicate_of_parent",
        "rule_low_business_value",
        "rule_index_when_all_signals_present",
    ]
