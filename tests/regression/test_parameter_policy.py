"""The parameter policy must not drift silently."""

from __future__ import annotations

import pytest

from kontur.engines.getparams.classifier import classify_parameter
from kontur.engines.getparams.controller import ParamPolicy
from kontur.engines.getparams.models import ParamDecision

pytestmark = [pytest.mark.regression, pytest.mark.seo]


@pytest.mark.rule("GETP-001")
@pytest.mark.regression
@pytest.mark.parametrize(
    "parameter",
    ["utm_source", "utm_medium", "utm_campaign", "yclid", "ysclid", "gclid", "fbclid", "_openstat"],
)
def test_the_tracking_catalogue_stays_excluded(observation, parameter: str) -> None:
    assert classify_parameter(observation(parameter)).decision is ParamDecision.EXCLUDE


@pytest.mark.rule("GETP-002")
@pytest.mark.regression
def test_conflicts_still_resolve_upwards(controller, crawl_provenance) -> None:
    controller.add_policy(
        ParamPolicy("mechanic", ParamDecision.CONTEXT_DEPENDENT, "imported legacy policy", crawl_provenance)
    )
    assert controller.decision("mechanic") is ParamDecision.CONTEXT_DEPENDENT


@pytest.mark.rule("GETP-003")
@pytest.mark.regression
def test_unknown_parameters_still_default_to_analyze(observation) -> None:
    assert classify_parameter(observation("brand_new_param")).decision is ParamDecision.ANALYZE


@pytest.mark.rule("GETP-006")
@pytest.mark.regression
def test_hub_promotion_thresholds_are_stable(observation, demand) -> None:
    from kontur.engines.getparams.classifier import DEFAULT_CONFIG

    assert DEFAULT_CONFIG.min_demand_for_hub == 100.0
    assert DEFAULT_CONFIG.min_values_with_demand == 3
    assert DEFAULT_CONFIG.max_distinct_values_for_hub == 200

    just_enough = classify_parameter(observation("mechanic"), demand=demand("mechanic", 3, 100.0))
    assert just_enough.decision is ParamDecision.SEO_HUB

    one_short = classify_parameter(observation("mechanic"), demand=demand("mechanic", 2, 100.0))
    assert one_short.decision is ParamDecision.ANALYZE


@pytest.mark.rule("GETP-006")
@pytest.mark.regression
def test_the_documented_dashboard_table_is_reproduced(observation, demand) -> None:
    """The table from the product brief, rebuilt from the engine."""
    cases = [
        ("utm_source", 48210, 137, None, "EXCLUDE", "tracking"),
        ("sort", 12440, 6, None, "EXCLUDE", "duplicate intent"),
        ("provider", 4812, 48, None, "ANALYZE", "possible seo facet"),
        ("mechanic", 1290, 22, ("mechanic", 7, 5400.0), "SEO HUB", "search demand"),
        ("rtp", 840, 9, ("rtp", 1, 40.0), "ANALYZE", "possible seo facet"),
    ]
    for name, urls, values, demand_args, expected_decision, expected_reason in cases:
        ruling = classify_parameter(
            observation(name, urls, values),
            demand=demand(*demand_args) if demand_args else None,
        )
        row = ruling.dashboard_row()
        assert row["decision"] == expected_decision, name
        assert expected_reason in row["reason"], name
        assert row["detected_urls"] == urls
