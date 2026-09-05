"""Correlation between behavioural metrics and outcomes.

Every result produced here is explicitly correlational (rule BEH-001). "Users
who stayed three minutes" is an observation about users, not a documented
ranking input, and this module refuses to phrase it as one. If you want a causal
statement, run an experiment: :mod:`kontur.engines.experiment`.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from kontur.core.errors import ConfigurationError, InsufficientDataError
from kontur.engines.experiment.stats import student_t_sf

#: Below this many paired observations a correlation is not reported at all.
MIN_SAMPLE_FOR_CORRELATION = 30

CAUSAL_CAVEAT = (
    "Correlational only. This does not show that changing the behavioural metric "
    "changes the outcome; run a controlled experiment to test that."
)


def _ranks(values: Sequence[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    index = 0
    while index < len(order):
        end = index
        while end + 1 < len(order) and values[order[end + 1]] == values[order[index]]:
            end += 1
        average_rank = (index + end) / 2.0 + 1.0
        for position in range(index, end + 1):
            ranks[order[position]] = average_rank
        index = end + 1
    return ranks


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) != len(y):
        raise ConfigurationError("pearson() needs paired samples of equal length")
    n = len(x)
    if n < 2:
        raise InsufficientDataError("pearson() needs at least two pairs")
    mean_x, mean_y = sum(x) / n, sum(y) / n
    numerator = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y, strict=True))
    denominator = math.sqrt(sum((a - mean_x) ** 2 for a in x) * sum((b - mean_y) ** 2 for b in y))
    if denominator == 0:
        return 0.0
    return max(-1.0, min(1.0, numerator / denominator))


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    """Rank correlation — robust to the skew typical of session metrics."""
    if len(x) != len(y):
        raise ConfigurationError("spearman() needs paired samples of equal length")
    if len(x) < 2:
        raise InsufficientDataError("spearman() needs at least two pairs")
    return pearson(_ranks(x), _ranks(y))


@dataclass(frozen=True, slots=True)
class CorrelationResult:
    """A correlation, its sample size, and the caveat it always travels with."""

    metric_a: str
    metric_b: str
    coefficient: float
    n: int
    p_value: float
    method: str = "spearman"

    #: Present so that no consumer can serialise this as a causal finding.
    causal: bool = False

    @property
    def is_significant(self) -> bool:
        return self.p_value < 0.05

    def describe(self) -> str:
        direction = "positive" if self.coefficient > 0 else "negative" if self.coefficient < 0 else "no"
        return (
            f"{direction} rank correlation of {self.coefficient:+.2f} between {self.metric_a} "
            f"and {self.metric_b} over n={self.n} (p={self.p_value:.3g}). {CAUSAL_CAVEAT}"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_a": self.metric_a,
            "metric_b": self.metric_b,
            "coefficient": round(self.coefficient, 4),
            "n": self.n,
            "p_value": self.p_value,
            "method": self.method,
            "significant": self.is_significant,
            "causal": self.causal,
            "caveat": CAUSAL_CAVEAT,
        }


def correlate(
    metric_a: str,
    values_a: Sequence[float],
    metric_b: str,
    values_b: Sequence[float],
    *,
    min_sample: int = MIN_SAMPLE_FOR_CORRELATION,
) -> CorrelationResult:
    """Rank-correlate two behavioural series (rule BEH-002 enforces the sample floor)."""
    if len(values_a) != len(values_b):
        raise ConfigurationError("correlate() needs paired samples of equal length")
    if len(values_a) < min_sample:
        raise InsufficientDataError(
            f"{len(values_a)} pairs is below the {min_sample}-pair floor; "
            "a correlation from this few observations is noise"
        )

    coefficient = spearman(values_a, values_b)
    n = len(values_a)
    if abs(coefficient) >= 1.0:
        p_value = 0.0
    else:
        t_statistic = coefficient * math.sqrt((n - 2) / (1 - coefficient**2))
        p_value = 2.0 * student_t_sf(abs(t_statistic), n - 2)
    return CorrelationResult(
        metric_a=metric_a,
        metric_b=metric_b,
        coefficient=coefficient,
        n=n,
        p_value=min(1.0, p_value),
    )
