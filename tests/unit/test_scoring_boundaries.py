"""Boundary behaviour of every registered scoring function.

Each function is bounded to [0, 1]; these tests pin both ends, the shape in
between, and the refusal of impossible inputs.
"""

from __future__ import annotations

from datetime import date

import pytest

from kontur.core.errors import ConfigurationError, InsufficientDataError
from kontur.core.provenance import Provenance
from kontur.core.registry import SCORING_FUNCTIONS
from kontur.engines.aeo.extraction import ExtractionSignals, extraction_readiness_score
from kontur.engines.backlinks.risk import (
    AnchorType,
    Backlink,
    RiskFactor,
    backlink_risk_score,
    classify_risk,
)
from kontur.engines.faceted.signals import (
    business_value_score,
    content_uniqueness_score,
    demand_score,
)
from kontur.engines.geo.metrics import share_of_voice
from kontur.engines.geo.models import AliceObservation
from kontur.engines.geo.snapshots import answer_volatility
from kontur.engines.serp.evidence import information_gain_score
from kontur.engines.serp.models import PageProfile, SerpEvidenceSummary

pytestmark = pytest.mark.unit


# ------------------------------------------------------------- demand_score
@pytest.mark.boundary
@pytest.mark.scoring("demand_score")
def test_demand_score_boundaries() -> None:
    assert demand_score(0) == 0.0
    assert demand_score(1000) == 1.0
    assert demand_score(50_000) == 1.0
    assert 0.0 < demand_score(1) < demand_score(100) < demand_score(999) < 1.0
    with pytest.raises(ConfigurationError):
        demand_score(-1)
    with pytest.raises(ConfigurationError):
        demand_score(100, reference=0)


# --------------------------------------------------- content_uniqueness_score
@pytest.mark.boundary
@pytest.mark.scoring("content_uniqueness_score")
def test_content_uniqueness_score_boundaries() -> None:
    assert content_uniqueness_score(unique_items=0, total_items=0) == 0.0
    assert content_uniqueness_score(unique_items=0, total_items=100) == 0.0
    assert content_uniqueness_score(unique_items=100, total_items=100, editorial_blocks=3) == 1.0
    assert content_uniqueness_score(unique_items=100, total_items=100, editorial_blocks=99) == 1.0
    assert 0.0 < content_uniqueness_score(unique_items=50, total_items=100) < 1.0
    with pytest.raises(ConfigurationError):
        content_uniqueness_score(unique_items=101, total_items=100)
    with pytest.raises(ConfigurationError):
        content_uniqueness_score(unique_items=1, total_items=1, editorial_target=0)


# ------------------------------------------------------- business_value_score
@pytest.mark.boundary
@pytest.mark.scoring("business_value_score")
def test_business_value_score_boundaries() -> None:
    assert business_value_score(commercial_items=0, total_items=0) == 0.0
    assert business_value_score(commercial_items=0, total_items=50, revenue_index=0.0) == 0.0
    assert business_value_score(commercial_items=50, total_items=50, revenue_index=1.0) == 1.0
    assert business_value_score(commercial_items=50, total_items=50) == pytest.approx(0.6)
    with pytest.raises(ConfigurationError):
        business_value_score(commercial_items=51, total_items=50)
    with pytest.raises(ConfigurationError):
        business_value_score(commercial_items=1, total_items=1, revenue_index=1.5)


# ----------------------------------------------------- information_gain_score
def _summary(**kwargs) -> SerpEvidenceSummary:
    defaults = {
        "query": "megaways",
        "competitors_analysed": 10,
        "dedicated_pages": 4,
        "median_word_count": 900,
        "common_entities": frozenset({"rtp", "волатильность"}),
        "common_questions": frozenset({"что такое megaways?"}),
        "table_share": 0.8,
        "schema_share": 0.7,
    }
    return SerpEvidenceSummary(**{**defaults, **kwargs})


@pytest.mark.boundary
@pytest.mark.scoring("information_gain_score")
def test_information_gain_score_boundaries() -> None:
    nothing_new = PageProfile(url="/a/", entities=frozenset({"rtp"}), questions=("что такое megaways?",))
    assert information_gain_score(nothing_new, _summary()) == 0.0

    everything_new = PageProfile(
        url="/b/",
        entities=frozenset({"e1", "e2", "e3", "e4", "e5"}),
        questions=("q1?", "q2?", "q3?"),
        tables=1,
        schema_types=frozenset({"faqpage"}),
    )
    assert information_gain_score(everything_new, _summary(table_share=0.0, schema_share=0.0)) == 1.0
    assert 0.0 < information_gain_score(everything_new, _summary()) < 1.0

    with pytest.raises(ConfigurationError):
        information_gain_score(nothing_new, _summary(), entity_target=0)
    with pytest.raises(InsufficientDataError):
        information_gain_score(nothing_new, _summary(competitors_analysed=0, dedicated_pages=0))


# -------------------------------------------------- extraction_readiness_score
@pytest.mark.boundary
@pytest.mark.scoring("extraction_readiness_score")
def test_extraction_readiness_score_boundaries() -> None:
    assert extraction_readiness_score(ExtractionSignals()) == 0.0
    full = ExtractionSignals(
        has_direct_answer=True,
        question_headings=3,
        lists=2,
        tables=1,
        answer_schema_types=1,
        numeric_facts=3,
    )
    assert extraction_readiness_score(full) == pytest.approx(1.0)
    over = ExtractionSignals(
        has_direct_answer=True,
        question_headings=30,
        lists=20,
        tables=10,
        answer_schema_types=6,
        numeric_facts=99,
    )
    assert extraction_readiness_score(over) == pytest.approx(1.0), "extra structure cannot exceed 1"
    assert 0.0 < extraction_readiness_score(ExtractionSignals(has_direct_answer=True)) < 1.0
    with pytest.raises(ConfigurationError):
        ExtractionSignals(lists=-1)
    with pytest.raises(ConfigurationError):
        extraction_readiness_score("not signals")


# ----------------------------------------------------------- share_of_voice
def _observation(mentioned: bool, competitors: tuple[str, ...], provenance: Provenance) -> AliceObservation:
    return AliceObservation(
        query="что такое megaways",
        week_start=date(2026, 7, 6),
        provenance=provenance,
        our_domain_mentioned=mentioned,
        our_url_cited="https://casino.example/x/" if mentioned else None,
        competitor_domains=competitors,
    )


@pytest.mark.boundary
@pytest.mark.scoring("share_of_voice")
def test_share_of_voice_boundaries(alice_provenance: Provenance) -> None:
    absent = [_observation(False, ("a.example", "b.example"), alice_provenance)]
    assert share_of_voice(absent) == 0.0

    alone = [_observation(True, (), alice_provenance)]
    assert share_of_voice(alone) == 1.0

    shared = [_observation(True, ("a.example",), alice_provenance)]
    assert share_of_voice(shared) == pytest.approx(0.5)

    with pytest.raises(InsufficientDataError):
        share_of_voice([])


# -------------------------------------------------------- answer_volatility
@pytest.mark.boundary
@pytest.mark.scoring("answer_volatility")
def test_answer_volatility_boundaries() -> None:
    assert answer_volatility([{"a", "b"}, {"a", "b"}]) == 0.0
    assert answer_volatility([{"a"}, {"b"}]) == 1.0
    assert 0.0 < answer_volatility([{"a", "b"}, {"a", "c"}]) < 1.0
    assert answer_volatility([set(), set()]) == 0.0
    with pytest.raises(InsufficientDataError):
        answer_volatility([{"a"}])


# ------------------------------------------------------- backlink_risk_score
@pytest.mark.boundary
@pytest.mark.scoring("backlink_risk_score")
def test_backlink_risk_score_boundaries() -> None:
    zero = [RiskFactor("footprint", 0.0, 1.0, "clean")]
    one = [RiskFactor("footprint", 1.0, 1.0, "identical donors")]
    assert backlink_risk_score(zero) == 0.0
    assert backlink_risk_score(one) == 1.0
    mixed = [RiskFactor("a", 0.0, 1.0, ""), RiskFactor("b", 1.0, 1.0, "")]
    assert backlink_risk_score(mixed) == pytest.approx(0.5)
    with pytest.raises(InsufficientDataError):
        backlink_risk_score([])
    with pytest.raises(ConfigurationError):
        RiskFactor("bad", 1.5, 1.0, "")
    with pytest.raises(ConfigurationError):
        RiskFactor("bad", 0.5, 0.0, "")


@pytest.mark.boundary
@pytest.mark.scoring("backlink_risk_score")
def test_risk_level_thresholds() -> None:
    assert classify_risk(0.0).value == "LOW RISK"
    assert classify_risk(0.339).value == "LOW RISK"
    assert classify_risk(0.34).value == "MEDIUM RISK"
    assert classify_risk(0.669).value == "MEDIUM RISK"
    assert classify_risk(0.67).value == "HIGH RISK"
    assert classify_risk(1.0).value == "HIGH RISK"
    with pytest.raises(ConfigurationError):
        classify_risk(1.2)


def test_every_registered_scoring_function_is_importable() -> None:
    import importlib

    for scoring in SCORING_FUNCTIONS.values():
        module_name, _, attribute = scoring.dotted_path.rpartition(".")
        module = importlib.import_module(module_name)
        assert callable(getattr(module, attribute)), f"{scoring.dotted_path} is not callable"


def test_backlink_link_validation() -> None:
    with pytest.raises(ConfigurationError):
        Backlink("x.ru", "/a/", "anchor", AnchorType.BRAND, date(2026, 1, 1), topical_relevance=2.0)


def test_zero_demand_and_zero_queries_are_valid_measurements() -> None:
    from kontur.engines.faceted.signals import IntentAssessment, IntentLabel, SearchDemand

    demand = SearchDemand(0.0, 0)
    assert demand.monthly_volume == 0.0
    assert demand.query_count == 0
    with pytest.raises(ConfigurationError):
        SearchDemand(-1.0)
    with pytest.raises(ConfigurationError):
        SearchDemand(10.0, -1)

    intent = IntentAssessment(IntentLabel.COMMERCIAL, 0.2)
    assert intent.distinct_query_share == 0.0, "the default must not invent distinct demand"
    with pytest.raises(ConfigurationError):
        IntentAssessment(IntentLabel.COMMERCIAL, 1.5)
    with pytest.raises(ConfigurationError):
        IntentAssessment(IntentLabel.COMMERCIAL, 0.2, distinct_query_share=-0.1)


def test_intent_distinctness_boundary() -> None:
    from kontur.engines.faceted.signals import IntentAssessment, IntentLabel

    assert IntentAssessment(IntentLabel.COMMERCIAL, 0.79).is_distinct is True
    assert IntentAssessment(IntentLabel.COMMERCIAL, 0.80).is_distinct is False
