"""Statistics for SEO/AEO/GEO experiments, implemented without SciPy.

Nothing here is exotic: a two-proportion z-test, Welch's t-test, a deterministic
bootstrap and Holm's step-down correction. They are written out so the whole
inference path is auditable and testable, and so an experiment verdict never
depends on a black box.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Callable, Sequence

from kontur.core.errors import ConfigurationError, InsufficientDataError

#: Two-sided z quantiles for the confidence levels the platform uses.
_Z_QUANTILES: dict[float, float] = {0.90: 1.6448536269514722, 0.95: 1.959963984540054, 0.99: 2.5758293035489004}


def normal_cdf(z: float) -> float:
    """Standard normal CDF via the error function."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def normal_sf(z: float) -> float:
    return 1.0 - normal_cdf(z)


def z_quantile(confidence: float) -> float:
    try:
        return _Z_QUANTILES[round(confidence, 2)]
    except KeyError as exc:
        raise ConfigurationError(
            f"confidence {confidence} is not supported; use one of {sorted(_Z_QUANTILES)}"
        ) from exc


def _betacf(a: float, b: float, x: float, *, max_iterations: int = 200, epsilon: float = 3e-14) -> float:
    """Continued fraction for the incomplete beta function (Lentz's method)."""
    tiny = 1e-30
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, max_iterations + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < epsilon:
            break
    return h


def regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    """I_x(a, b), the regularized incomplete beta function."""
    if not 0.0 <= x <= 1.0:
        raise ConfigurationError(f"x must be within [0, 1], got {x}")
    if a <= 0 or b <= 0:
        raise ConfigurationError("a and b must be > 0")
    if x in (0.0, 1.0):
        return x
    front = math.exp(
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1.0 - x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def student_t_sf(t: float, df: float) -> float:
    """P(T > t) for Student's t with ``df`` degrees of freedom."""
    if df <= 0:
        raise ConfigurationError("degrees of freedom must be > 0")
    x = df / (df + t * t)
    tail = 0.5 * regularized_incomplete_beta(df / 2.0, 0.5, x)
    return tail if t > 0 else 1.0 - tail


@dataclass(frozen=True, slots=True)
class TestResult:
    """A single comparison: effect, interval, and the p-value behind it."""

    name: str
    estimate: float
    ci_low: float
    ci_high: float
    p_value: float
    statistic: float
    n_control: int
    n_variant: int
    confidence: float = 0.95

    @property
    def crosses_zero(self) -> bool:
        return self.ci_low <= 0.0 <= self.ci_high

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "estimate": self.estimate,
            "ci": [self.ci_low, self.ci_high],
            "p_value": self.p_value,
            "statistic": self.statistic,
            "n_control": self.n_control,
            "n_variant": self.n_variant,
            "confidence": self.confidence,
            "crosses_zero": self.crosses_zero,
        }


def two_proportion_z_test(
    *,
    control_successes: int,
    control_trials: int,
    variant_successes: int,
    variant_trials: int,
    name: str = "conversion",
    confidence: float = 0.95,
) -> TestResult:
    """Compare two rates. Effect is variant minus control, in percentage points."""
    for label, successes, trials in (
        ("control", control_successes, control_trials),
        ("variant", variant_successes, variant_trials),
    ):
        if trials <= 0:
            raise InsufficientDataError(f"{label} arm has no trials")
        if not 0 <= successes <= trials:
            raise ConfigurationError(f"{label} successes must be within [0, trials]")

    p_control = control_successes / control_trials
    p_variant = variant_successes / variant_trials
    estimate = p_variant - p_control

    pooled = (control_successes + variant_successes) / (control_trials + variant_trials)
    se_pooled = math.sqrt(pooled * (1 - pooled) * (1 / control_trials + 1 / variant_trials))
    statistic = 0.0 if se_pooled == 0 else estimate / se_pooled
    p_value = 2.0 * normal_sf(abs(statistic))

    se_unpooled = math.sqrt(
        p_control * (1 - p_control) / control_trials + p_variant * (1 - p_variant) / variant_trials
    )
    margin = z_quantile(confidence) * se_unpooled
    return TestResult(
        name=name,
        estimate=estimate,
        ci_low=estimate - margin,
        ci_high=estimate + margin,
        p_value=min(1.0, p_value),
        statistic=statistic,
        n_control=control_trials,
        n_variant=variant_trials,
        confidence=confidence,
    )


def welch_t_test(
    control: Sequence[float],
    variant: Sequence[float],
    *,
    name: str = "metric",
    confidence: float = 0.95,
) -> TestResult:
    """Compare two means without assuming equal variances."""
    if len(control) < 2 or len(variant) < 2:
        raise InsufficientDataError("Welch's t-test needs at least two observations per arm")

    mean_c, mean_v = sum(control) / len(control), sum(variant) / len(variant)
    var_c = sum((x - mean_c) ** 2 for x in control) / (len(control) - 1)
    var_v = sum((x - mean_v) ** 2 for x in variant) / (len(variant) - 1)
    se = math.sqrt(var_c / len(control) + var_v / len(variant))
    estimate = mean_v - mean_c

    if se == 0:
        statistic, p_value, df = 0.0, 1.0, float(len(control) + len(variant) - 2)
    else:
        statistic = estimate / se
        numerator = (var_c / len(control) + var_v / len(variant)) ** 2
        denominator = (var_c / len(control)) ** 2 / (len(control) - 1) + (var_v / len(variant)) ** 2 / (
            len(variant) - 1
        )
        df = numerator / denominator if denominator else float(len(control) + len(variant) - 2)
        p_value = 2.0 * student_t_sf(abs(statistic), df)

    margin = z_quantile(confidence) * se
    return TestResult(
        name=name,
        estimate=estimate,
        ci_low=estimate - margin,
        ci_high=estimate + margin,
        p_value=min(1.0, p_value),
        statistic=statistic,
        n_control=len(control),
        n_variant=len(variant),
        confidence=confidence,
    )


def bootstrap_ci(
    control: Sequence[float],
    variant: Sequence[float],
    *,
    statistic: Callable[[Sequence[float]], float] | None = None,
    iterations: int = 2000,
    confidence: float = 0.95,
    seed: int = 20260401,
) -> tuple[float, float]:
    """Percentile bootstrap CI for the difference of a statistic.

    Seeded, so a re-run of the same analysis produces the same interval.
    """
    if not control or not variant:
        raise InsufficientDataError("bootstrap needs non-empty samples")
    if iterations < 100:
        raise ConfigurationError("iterations must be >= 100 for a usable interval")
    stat = statistic or (lambda values: sum(values) / len(values))
    rng = random.Random(seed)
    diffs: list[float] = []
    for _ in range(iterations):
        sample_c = [control[rng.randrange(len(control))] for _ in range(len(control))]
        sample_v = [variant[rng.randrange(len(variant))] for _ in range(len(variant))]
        diffs.append(stat(sample_v) - stat(sample_c))
    diffs.sort()
    alpha = 1.0 - confidence
    low_index = max(0, int(math.floor(alpha / 2 * iterations)))
    high_index = min(iterations - 1, int(math.ceil((1 - alpha / 2) * iterations)) - 1)
    return diffs[low_index], diffs[high_index]


def holm_bonferroni(p_values: Sequence[float], *, alpha: float = 0.05) -> list[tuple[float, bool]]:
    """Holm's step-down correction. Returns (adjusted p, significant) in input order."""
    if not p_values:
        return []
    if not 0 < alpha < 1:
        raise ConfigurationError("alpha must be within (0, 1)")
    for p in p_values:
        if not 0.0 <= p <= 1.0:
            raise ConfigurationError(f"p-value out of range: {p}")

    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    total = len(p_values)
    adjusted: list[float] = [0.0] * total
    running = 0.0
    for rank, (index, p) in enumerate(indexed):
        value = min(1.0, (total - rank) * p)
        running = max(running, value)
        adjusted[index] = running
    return [(adjusted[i], adjusted[i] <= alpha) for i in range(total)]


def required_sample_size_proportions(
    *, baseline_rate: float, minimum_detectable_effect: float, alpha: float = 0.05, power: float = 0.8
) -> int:
    """Per-arm sample size for a two-proportion test (normal approximation)."""
    if not 0.0 < baseline_rate < 1.0:
        raise ConfigurationError("baseline_rate must be within (0, 1)")
    if minimum_detectable_effect <= 0:
        raise ConfigurationError("minimum_detectable_effect must be > 0")
    target = baseline_rate + minimum_detectable_effect
    if not 0.0 < target < 1.0:
        raise ConfigurationError("baseline_rate + MDE must stay within (0, 1)")

    z_alpha = z_quantile(1 - alpha)
    z_beta = {0.8: 0.8416212335729143, 0.9: 1.2815515655446004}.get(round(power, 2))
    if z_beta is None:
        raise ConfigurationError("power must be 0.8 or 0.9")
    pooled = (baseline_rate + target) / 2
    numerator = (
        z_alpha * math.sqrt(2 * pooled * (1 - pooled))
        + z_beta * math.sqrt(baseline_rate * (1 - baseline_rate) + target * (1 - target))
    ) ** 2
    return math.ceil(numerator / (minimum_detectable_effect**2))
