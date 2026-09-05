"""Hypotheses, effect claims and the ban on unproven promises."""

from __future__ import annotations

import pytest

from kontur.core.claims import (
    HYPOTHESES,
    EffectClaim,
    GuidelineRecommendation,
    Hypothesis,
    HypothesisStatus,
    assert_no_unproven_claims,
    find_unproven_claims,
    guideline,
)
from kontur.core.errors import ConfigurationError, UnprovenClaimError

pytestmark = pytest.mark.unit


@pytest.mark.rule("AEO-004")
@pytest.mark.positive
def test_an_effect_claim_requires_an_experiment() -> None:
    claim = EffectClaim("H-001", "EXP-12", "cited_url_rate", 0.041, 0.012, 0.070, 900, 910)
    assert "EXP-12" in claim.statement()
    assert claim.crosses_zero is False
    assert claim.to_dict()["experiment_id"] == "EXP-12"


@pytest.mark.rule("AEO-004")
@pytest.mark.negative
def test_an_effect_claim_without_an_experiment_is_refused() -> None:
    with pytest.raises(UnprovenClaimError, match="no experiment_id"):
        EffectClaim("H-001", "", "cited_url_rate", 0.041, 0.012, 0.070, 900, 910)


@pytest.mark.rule("AEO-004")
@pytest.mark.negative
def test_an_effect_claim_without_a_sample_is_refused() -> None:
    with pytest.raises(UnprovenClaimError, match="non-empty control"):
        EffectClaim("H-001", "EXP-12", "cited_url_rate", 0.041, 0.012, 0.070, 0, 910)


@pytest.mark.rule("AEO-004")
@pytest.mark.negative
@pytest.mark.parametrize(
    "text",
    [
        "This block gives +120% to AI visibility",
        "Гарантирует рост в топ",
        "answer-first is a ranking factor",
        "поведенческие факторы ранжирования",
        "will boost your rankings within a month",
    ],
)
def test_promissory_language_is_detected(text: str) -> None:
    assert find_unproven_claims(text), f"{text!r} should have been flagged"
    with pytest.raises(UnprovenClaimError):
        assert_no_unproven_claims(text, where="test copy")


@pytest.mark.rule("AEO-004")
@pytest.mark.positive
@pytest.mark.parametrize(
    "text",
    [
        "In EXP-12 the variant's cited-url rate was 4.1pp higher, 95% CI [1.2, 7.0].",
        "Hypothesis H-002 compares answer-length buckets; no effect is asserted.",
        "The interval includes zero, so the result is inconclusive.",
    ],
)
def test_measured_language_passes(text: str) -> None:
    assert find_unproven_claims(text) == []
    assert_no_unproven_claims(text, where="test copy")


def test_shipped_hypotheses_start_unproven() -> None:
    assert HYPOTHESES, "the platform ships with a hypothesis backlog"
    for hypothesis in HYPOTHESES.values():
        assert hypothesis.status is HypothesisStatus.PROPOSED
        assert hypothesis.experiment_ids == ()


def test_supported_status_requires_an_experiment() -> None:
    with pytest.raises(ConfigurationError, match="without any experiment"):
        Hypothesis("H-999", "x", "metric", HypothesisStatus.SUPPORTED)


def test_unknown_hypothesis_is_refused() -> None:
    with pytest.raises(ConfigurationError, match="unknown hypothesis"):
        guideline("H-404")


def test_guideline_status_filter() -> None:
    with pytest.raises(UnprovenClaimError, match="is proposed"):
        guideline("H-001", statuses=[HypothesisStatus.SUPPORTED])


def test_recommendations_carry_their_caveat() -> None:
    payload = GuidelineRecommendation("H-002", "Try the 20-40 bucket").to_dict()
    assert payload["status"] == "proposed"
    assert "No causal effect" in payload["caveat"]
