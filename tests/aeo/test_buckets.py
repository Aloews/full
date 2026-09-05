"""Answer-length buckets are experiment arms, not a target."""

from __future__ import annotations

import pytest

from kontur.core.claims import HYPOTHESES, HypothesisStatus
from kontur.core.errors import ConfigurationError
from kontur.engines.aeo.buckets import (
    BUCKET_HYPOTHESIS_ID,
    AnswerLengthBucket,
    bucket_for,
    experiment_arms,
    target_words,
)

pytestmark = pytest.mark.aeo


@pytest.mark.rule("AEO-002")
@pytest.mark.positive
@pytest.mark.boundary
@pytest.mark.parametrize(
    ("words", "expected"),
    [
        (0, AnswerLengthBucket.BELOW_RANGE),
        (19, AnswerLengthBucket.BELOW_RANGE),
        (20, AnswerLengthBucket.SHORT),
        (40, AnswerLengthBucket.SHORT),
        (41, AnswerLengthBucket.MEDIUM),
        (60, AnswerLengthBucket.MEDIUM),
        (61, AnswerLengthBucket.LONG),
        (100, AnswerLengthBucket.LONG),
        (101, AnswerLengthBucket.ABOVE_RANGE),
    ],
)
def test_bucket_edges(words: int, expected: AnswerLengthBucket) -> None:
    assert bucket_for(words) is expected


@pytest.mark.rule("AEO-002")
@pytest.mark.negative
def test_buckets_are_arms_of_an_open_hypothesis() -> None:
    hypothesis = HYPOTHESES[BUCKET_HYPOTHESIS_ID]
    assert hypothesis.status is HypothesisStatus.PROPOSED
    assert "no established optimum" in (hypothesis.note or "")
    assert len(experiment_arms()) == 3, "three arms to compare, not one rule to follow"


@pytest.mark.rule("AEO-002")
@pytest.mark.negative
def test_no_bucket_is_marked_as_preferred() -> None:
    ranges = {bucket: target_words(bucket) for bucket in experiment_arms()}
    assert len({r for r in ranges.values()}) == 3
    for bucket in experiment_arms():
        assert not str(bucket.value).endswith("optimal")


@pytest.mark.rule("AEO-002")
@pytest.mark.negative
def test_invalid_input_is_refused() -> None:
    with pytest.raises(ConfigurationError):
        bucket_for(-1)
    with pytest.raises(ConfigurationError):
        target_words(AnswerLengthBucket.ABOVE_RANGE)


def test_ranges_do_not_overlap() -> None:
    seen: set[int] = set()
    for bucket in experiment_arms():
        low, high = target_words(bucket)
        span = set(range(low, high + 1))
        assert not span & seen, f"{bucket} overlaps another arm"
        seen |= span
