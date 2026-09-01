"""Answer-length buckets.

The buckets are experiment arms, not a target. There is no established optimal
answer length; "keep it under 60 words" is an editorial convention worth
testing, and hypothesis H-002 is where that test lives. ``bucket_for`` labels a
piece of copy so an experiment can compare arms — it does not score it.
"""

from __future__ import annotations

from enum import StrEnum

from kontur.core.errors import ConfigurationError

#: The hypothesis these buckets belong to.
BUCKET_HYPOTHESIS_ID = "H-002"


class AnswerLengthBucket(StrEnum):
    SHORT = "20-40"
    MEDIUM = "40-60"
    LONG = "60-100"
    BELOW_RANGE = "below-20"
    ABOVE_RANGE = "above-100"


#: Inclusive upper bounds; the ranges partition [20, 100] without overlap.
BUCKET_RANGES: dict[AnswerLengthBucket, tuple[int, int]] = {
    AnswerLengthBucket.SHORT: (20, 40),
    AnswerLengthBucket.MEDIUM: (41, 60),
    AnswerLengthBucket.LONG: (61, 100),
}


def bucket_for(words: int) -> AnswerLengthBucket:
    """Label a word count with its bucket."""
    if words < 0:
        raise ConfigurationError("word count must be >= 0")
    for bucket, (low, high) in BUCKET_RANGES.items():
        if low <= words <= high:
            return bucket
    return AnswerLengthBucket.BELOW_RANGE if words < 20 else AnswerLengthBucket.ABOVE_RANGE


def experiment_arms() -> tuple[AnswerLengthBucket, ...]:
    """The arms an answer-length experiment randomises over."""
    return tuple(BUCKET_RANGES)


def target_words(bucket: AnswerLengthBucket) -> tuple[int, int]:
    try:
        return BUCKET_RANGES[AnswerLengthBucket(bucket)]
    except KeyError as exc:
        raise ConfigurationError(f"{bucket} is not an experiment arm") from exc
