"""Behavioural analysis stays correlational."""

from __future__ import annotations

import random
from datetime import date

import pytest

from kontur.core.errors import ConfigurationError, InsufficientDataError
from kontur.engines.behavior.correlation import (
    CAUSAL_CAVEAT,
    MIN_SAMPLE_FOR_CORRELATION,
    correlate,
    pearson,
    spearman,
)
from kontur.engines.behavior.funnel import FunnelObservation, build_funnel

pytestmark = pytest.mark.unit


def _series(n: int = 40) -> tuple[list[float], list[float]]:
    rng = random.Random(11)
    a = [rng.random() for _ in range(n)]
    b = [value * 0.7 + rng.random() * 0.3 for value in a]
    return a, b


@pytest.mark.rule("BEH-001")
@pytest.mark.positive
def test_correlation_output_is_labelled_non_causal() -> None:
    a, b = _series()
    result = correlate("engaged_rate", a, "conversion_rate", b)
    assert result.causal is False
    assert result.to_dict()["causal"] is False
    assert CAUSAL_CAVEAT in result.describe()
    assert CAUSAL_CAVEAT in result.to_dict()["caveat"]


@pytest.mark.rule("BEH-001")
@pytest.mark.negative
def test_a_strong_correlation_still_refuses_to_claim_causation() -> None:
    values = [float(i) for i in range(40)]
    result = correlate("dwell_time", values, "position", values)
    assert result.coefficient == pytest.approx(1.0)
    assert result.causal is False, "a perfect correlation is still not a cause"


@pytest.mark.rule("BEH-002")
@pytest.mark.positive
def test_a_sufficient_sample_is_reported() -> None:
    a, b = _series(MIN_SAMPLE_FOR_CORRELATION)
    assert correlate("a", a, "b", b).n == MIN_SAMPLE_FOR_CORRELATION


@pytest.mark.rule("BEH-002")
@pytest.mark.negative
def test_a_small_sample_is_refused() -> None:
    a, b = _series(MIN_SAMPLE_FOR_CORRELATION - 1)
    with pytest.raises(InsufficientDataError, match="below the"):
        correlate("a", a, "b", b)


def test_unpaired_samples_are_refused() -> None:
    with pytest.raises(ConfigurationError):
        correlate("a", [1.0, 2.0], "b", [1.0])
    with pytest.raises(ConfigurationError):
        spearman([1.0, 2.0], [1.0])


def test_correlation_coefficients_are_bounded() -> None:
    assert pearson([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)
    assert pearson([1, 1, 1], [1, 2, 3]) == 0.0
    assert spearman([1, 2, 3], [10, 20, 30]) == pytest.approx(1.0)
    with pytest.raises(InsufficientDataError):
        pearson([1.0], [1.0])


def test_spearman_is_robust_to_a_monotone_outlier() -> None:
    a = [1, 2, 3, 4, 5]
    b = [1, 2, 3, 4, 1000]
    assert spearman(a, b) == pytest.approx(1.0)
    assert pearson(a, b) < 0.95


def test_the_funnel_cannot_widen(crawl_provenance) -> None:
    with pytest.raises(ConfigurationError, match="cannot widen"):
        FunnelObservation("/slots/", date(2026, 7, 1), crawl_provenance, impressions=10, clicks=20)


def test_funnel_reports_the_biggest_drop(crawl_provenance) -> None:
    observations = [
        FunnelObservation("/slots/", date(2026, 7, 1), crawl_provenance, 10_000, 700, 520, 300, 180, 42)
    ]
    report = build_funnel(observations)
    assert report.counts["serp_impression"] == 10_000
    assert report.biggest_drop == "serp_impression->serp_click"
    assert "not ranking inputs" in report.to_dict()["caveat"]


def test_funnel_needs_a_single_url(crawl_provenance) -> None:
    with pytest.raises(ConfigurationError, match="several URLs"):
        build_funnel(
            [
                FunnelObservation("/a/", date(2026, 7, 1), crawl_provenance, 10, 1),
                FunnelObservation("/b/", date(2026, 7, 1), crawl_provenance, 10, 1),
            ]
        )
    with pytest.raises(InsufficientDataError):
        build_funnel([])
