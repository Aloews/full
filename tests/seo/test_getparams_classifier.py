"""Classification of GET parameters from crawl evidence."""

from __future__ import annotations

import pytest

from kontur.core.errors import MissingProvenanceError
from kontur.engines.getparams.classifier import ClassifierConfig, classify_parameter
from kontur.engines.getparams.models import ParamDecision, ParamDemand, ParamReason

pytestmark = pytest.mark.seo


@pytest.mark.rule("GETP-001")
@pytest.mark.positive
@pytest.mark.parametrize("name", ["utm_source", "utm_medium", "utm_whatever", "yclid", "gclid", "fbclid"])
def test_tracking_parameters_are_excluded(observation, name: str) -> None:
    ruling = classify_parameter(observation(name, 48210, 137))
    assert ruling.decision is ParamDecision.EXCLUDE
    assert ParamReason.TRACKING in ruling.reasons
    assert "GETP-001" in ruling.rule_ids


@pytest.mark.rule("GETP-001")
@pytest.mark.negative
@pytest.mark.parametrize("name", ["mechanic", "provider", "page", "volatility"])
def test_content_parameters_are_not_treated_as_tracking(observation, name: str) -> None:
    ruling = classify_parameter(observation(name, 500, 12))
    assert ParamReason.TRACKING not in ruling.reasons


@pytest.mark.rule("GETP-003")
@pytest.mark.positive
def test_unknown_parameter_is_held_for_analysis(observation) -> None:
    ruling = classify_parameter(observation("promo_widget", 210, 5))
    assert ruling.decision is ParamDecision.ANALYZE
    assert ParamReason.UNKNOWN_PARAMETER in ruling.reasons
    assert ruling.is_indexable is False


@pytest.mark.rule("GETP-003")
@pytest.mark.negative
def test_unknown_parameter_never_becomes_indexable_on_its_own(observation) -> None:
    ruling = classify_parameter(observation("mystery_param", 99999, 3))
    assert ruling.decision is not ParamDecision.SEO_HUB
    assert ruling.decision is not ParamDecision.CONTEXT_DEPENDENT


@pytest.mark.rule("GETP-004")
@pytest.mark.positive
@pytest.mark.parametrize("name", ["sort", "order", "orderby", "view", "per_page"])
def test_sort_and_display_parameters_are_excluded(observation, name: str) -> None:
    ruling = classify_parameter(observation(name, 12440, 6))
    assert ruling.decision is ParamDecision.EXCLUDE
    assert ParamReason.DUPLICATE_INTENT in ruling.reasons


@pytest.mark.rule("GETP-005")
@pytest.mark.positive
def test_pagination_is_context_dependent(observation) -> None:
    ruling = classify_parameter(observation("page", 9100, 64))
    assert ruling.decision is ParamDecision.CONTEXT_DEPENDENT
    assert ParamReason.PAGINATION in ruling.reasons


@pytest.mark.rule("GETP-007")
@pytest.mark.positive
@pytest.mark.parametrize("name", ["phpsessid", "sessionid", "jsessionid", "sid", "user_token"])
def test_session_identifiers_are_blocked(observation, name: str) -> None:
    ruling = classify_parameter(observation(name, 380, 380))
    assert ruling.decision is ParamDecision.BLOCK
    assert ParamReason.SESSION_IDENTIFIER in ruling.reasons


@pytest.mark.rule("GETP-006")
@pytest.mark.positive
def test_facet_with_measured_demand_becomes_a_hub(observation, demand) -> None:
    ruling = classify_parameter(observation("mechanic", 1290, 22), demand=demand("mechanic", 7, 5400.0))
    assert ruling.decision is ParamDecision.SEO_HUB
    assert ParamReason.SEARCH_DEMAND in ruling.reasons
    assert ruling.demand is not None, "the demand export must stay attached to the ruling"
    assert ruling.evidence.is_sample is False


@pytest.mark.rule("GETP-006")
@pytest.mark.negative
def test_facet_without_demand_data_is_held_not_promoted(observation) -> None:
    ruling = classify_parameter(observation("mechanic", 1290, 22))
    assert ruling.decision is ParamDecision.ANALYZE
    assert ParamReason.DEMAND_DATA_MISSING in ruling.reasons


@pytest.mark.rule("GETP-006")
@pytest.mark.negative
def test_bare_demand_without_provenance_is_refused(observation) -> None:
    with pytest.raises(MissingProvenanceError):
        classify_parameter(observation("mechanic", 1290, 22), demand=ParamDemand("mechanic", 7, 5400.0))


@pytest.mark.rule("GETP-006")
@pytest.mark.negative
def test_facet_with_zero_measured_demand_is_excluded(observation, demand) -> None:
    ruling = classify_parameter(observation("theme", 400, 12), demand=demand("theme", 0, 0.0))
    assert ruling.decision is ParamDecision.EXCLUDE
    assert ParamReason.NO_SEARCH_DEMAND in ruling.reasons


@pytest.mark.rule("GETP-006")
@pytest.mark.negative
def test_facet_below_the_thresholds_stays_under_analysis(observation, demand) -> None:
    ruling = classify_parameter(observation("rtp", 840, 9), demand=demand("rtp", 1, 40.0))
    assert ruling.decision is ParamDecision.ANALYZE
    assert ParamReason.LOW_URL_VOLUME in ruling.reasons


@pytest.mark.rule("GETP-006")
@pytest.mark.negative
def test_unbounded_value_space_blocks_promotion(observation, demand) -> None:
    ruling = classify_parameter(
        observation("provider", 5000, 5000),
        demand=demand("provider", 40, 90000.0),
        config=ClassifierConfig(max_distinct_values_for_hub=200),
    )
    assert ruling.decision is ParamDecision.ANALYZE
    assert ParamReason.UNBOUNDED_VALUE_SPACE in ruling.reasons


def test_every_ruling_explains_itself(observation, demand) -> None:
    for name in ("utm_source", "sort", "page", "mechanic", "phpsessid", "unknown_x"):
        ruling = classify_parameter(observation(name), demand=demand(name) if name == "mechanic" else None)
        assert ruling.reasons, f"{name} was decided without a reason"
        assert ruling.dashboard_row()["reason"]


def test_sample_provenance_marks_the_ruling(sample_provenance) -> None:
    from kontur.engines.getparams.models import ParamObservation

    ruling = classify_parameter(ParamObservation("utm_source", 10, 2, sample_provenance))
    assert ruling.is_sample is True
    assert ruling.dashboard_row()["is_sample"] is True


# ------------------------------------------------------- input validation
@pytest.mark.parametrize(
    ("detected_urls", "distinct_values"),
    [(-1, 5), (5, -1), (-1, -1)],
)
def test_negative_counts_are_refused(crawl_provenance, detected_urls: int, distinct_values: int) -> None:
    from kontur.core.errors import ConfigurationError
    from kontur.engines.getparams.models import ParamObservation

    with pytest.raises(ConfigurationError, match="non-negative"):
        ParamObservation("sort", detected_urls, distinct_values, crawl_provenance)


def test_zero_counts_are_a_valid_observation(crawl_provenance) -> None:
    """A parameter can be declared before the crawl has seen it."""
    from kontur.engines.getparams.models import ParamObservation

    observation = ParamObservation("sort", 0, 0, crawl_provenance)
    assert observation.detected_urls == 0
    assert observation.distinct_values == 0
    assert classify_parameter(observation).decision is ParamDecision.EXCLUDE


def test_an_observation_needs_a_name_and_provenance(crawl_provenance) -> None:
    from kontur.core.errors import ConfigurationError
    from kontur.engines.getparams.models import ParamObservation

    with pytest.raises(ConfigurationError, match="name is required"):
        ParamObservation("  ", 10, 2, crawl_provenance)
    with pytest.raises(ConfigurationError, match="Provenance"):
        ParamObservation("sort", 10, 2, provenance=None)


def test_observation_names_are_normalised(crawl_provenance) -> None:
    from kontur.engines.getparams.models import ParamObservation

    assert ParamObservation("  UTM_Source ", 1, 1, crawl_provenance).name == "utm_source"


@pytest.mark.parametrize(
    ("values_with_demand", "total"),
    [(-1, 100.0), (1, -5.0), (-1, -5.0)],
)
def test_negative_demand_figures_are_refused(values_with_demand: int, total: float) -> None:
    from kontur.core.errors import ConfigurationError
    from kontur.engines.getparams.models import ParamDemand

    with pytest.raises(ConfigurationError, match="non-negative"):
        ParamDemand("mechanic", values_with_demand, total)


def test_zero_demand_is_a_valid_measurement() -> None:
    from kontur.engines.getparams.models import ParamDemand

    stats = ParamDemand("mechanic", 0, 0.0)
    assert stats.values_with_demand == 0
    assert stats.total_monthly_demand == 0.0


def test_rulings_are_immutable(observation) -> None:
    import dataclasses

    ruling = classify_parameter(observation("sort", 100, 4))
    with pytest.raises(dataclasses.FrozenInstanceError):
        ruling.decision = ParamDecision.SEO_HUB


def test_a_ruling_needs_at_least_one_reason(observation) -> None:
    from kontur.core.errors import ConfigurationError
    from kontur.engines.getparams.models import ParamRuling

    with pytest.raises(ConfigurationError, match="no reason"):
        ParamRuling(name="sort", decision=ParamDecision.EXCLUDE, reasons=())


def test_the_restrictiveness_table_is_exact() -> None:
    from kontur.engines.getparams.models import PARAM_RESTRICTIVENESS

    assert PARAM_RESTRICTIVENESS == {
        ParamDecision.SEO_HUB: 0,
        ParamDecision.ANALYZE: 1,
        ParamDecision.CONTEXT_DEPENDENT: 2,
        ParamDecision.EXCLUDE: 3,
        ParamDecision.BLOCK: 4,
    }


def test_optional_observation_counters_default_to_zero(crawl_provenance) -> None:
    from kontur.engines.getparams.models import ParamObservation

    observation = ParamObservation("sort", 10, 2, crawl_provenance)
    assert observation.pages_with_param == 0
    assert observation.indexable_pages_with_param == 0
    assert observation.sample_values == ()


def test_the_dashboard_renames_only_the_hub_decision(observation, demand) -> None:
    hub = classify_parameter(observation("mechanic"), demand=demand("mechanic", 7, 5400.0))
    tracking = classify_parameter(observation("utm_source"))
    assert hub.dashboard_row()["decision"] == "SEO HUB"
    assert tracking.dashboard_row()["decision"] == "EXCLUDE"
    assert classify_parameter(observation("page")).dashboard_row()["decision"] == "CONTEXT_DEPENDENT"


def test_a_single_value_facet_can_be_configured() -> None:
    """One value with demand is a legitimate policy for a small catalogue."""
    config = ClassifierConfig(min_values_with_demand=1)
    assert config.min_values_with_demand == 1


@pytest.mark.parametrize(
    "kwargs",
    [{"min_values_with_demand": 0}, {"min_demand_for_hub": -1.0}, {"max_distinct_values_for_hub": 0}],
)
def test_impossible_classifier_configs_are_refused(kwargs: dict) -> None:
    from kontur.core.errors import ConfigurationError

    with pytest.raises(ConfigurationError):
        ClassifierConfig(**kwargs)


@pytest.mark.rule("GETP-006")
@pytest.mark.positive
def test_a_facet_exactly_at_the_cardinality_ceiling_is_still_promotable(observation, demand) -> None:
    """The ceiling is inclusive: 200 values is within budget, 201 is not."""
    config = ClassifierConfig(max_distinct_values_for_hub=200)
    at_ceiling = classify_parameter(
        observation("provider", 5000, 200), demand=demand("provider", 40, 90000.0), config=config
    )
    assert at_ceiling.decision is ParamDecision.SEO_HUB

    over_ceiling = classify_parameter(
        observation("provider", 5000, 201), demand=demand("provider", 40, 90000.0), config=config
    )
    assert over_ceiling.decision is ParamDecision.ANALYZE


@pytest.mark.rule("GETP-006")
@pytest.mark.negative
def test_demand_volume_without_any_value_behind_it_is_excluded(observation, demand) -> None:
    """Volume attributed to no individual value is not usable demand."""
    ruling = classify_parameter(observation("theme", 400, 12), demand=demand("theme", 0, 500.0))
    assert ruling.decision is ParamDecision.EXCLUDE
    assert ParamReason.NO_SEARCH_DEMAND in ruling.reasons
