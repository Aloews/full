"""From measurements to a verdict: ADOPT / REJECT / INCONCLUSIVE.

The rules are deliberately unexciting:

* an underpowered result is INCONCLUSIVE, never a win (rule EXP-001);
* a breached guardrail is REJECT, whatever the primary metric did (EXP-002);
* several metrics are corrected with Holm before anything is called significant
  (EXP-003).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from kontur.core.claims import EffectClaim
from kontur.core.errors import ConfigurationError
from kontur.core.registry import rule_ids
from kontur.engines.experiment.design import Experiment, Guardrail
from kontur.engines.experiment.stats import TestResult, holm_bonferroni, two_proportion_z_test


class Verdict(StrEnum):
    ADOPT = "ADOPT"
    REJECT = "REJECT"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True, slots=True)
class ArmResult:
    """Observed counts for one arm."""

    arm: str
    successes: int
    trials: int

    def __post_init__(self) -> None:
        if self.trials < 0 or self.successes < 0:
            raise ConfigurationError("counts must be >= 0")
        if self.successes > self.trials:
            raise ConfigurationError(f"arm {self.arm}: successes exceed trials")

    @property
    def rate(self) -> float:
        return self.successes / self.trials if self.trials else 0.0


@dataclass(frozen=True, slots=True)
class ExperimentVerdict:
    """The decision, the evidence behind it, and why it went that way."""

    experiment_id: str
    verdict: Verdict
    reasons: tuple[str, ...]
    primary: TestResult | None = None
    secondary: tuple[TestResult, ...] = ()
    guardrail_breaches: tuple[str, ...] = ()
    claim: EffectClaim | None = None
    rule_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "verdict", Verdict(self.verdict))
        if not self.reasons:
            raise ConfigurationError("an experiment verdict must state its reasons")

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "verdict": self.verdict.value,
            "reasons": list(self.reasons),
            "primary": self.primary.to_dict() if self.primary else None,
            "secondary": [t.to_dict() for t in self.secondary],
            "guardrail_breaches": list(self.guardrail_breaches),
            "claim": self.claim.to_dict() if self.claim else None,
            "rules": list(self.rule_ids),
        }


@dataclass
class ExperimentAnalysis:
    """Inputs for one analysis run."""

    experiment: Experiment
    results: Sequence[ArmResult]
    guardrail_values: Mapping[str, float] = field(default_factory=dict)
    secondary_results: Sequence[tuple[str, ArmResult, ArmResult]] = ()
    alpha: float = 0.05

    def arm(self, name: str) -> ArmResult:
        for result in self.results:
            if result.arm == name:
                return result
        raise ConfigurationError(f"no result for arm {name!r}")


def _guardrail_breaches(guardrails: Sequence[Guardrail], values: Mapping[str, float]) -> list[str]:
    breaches: list[str] = []
    for guardrail in guardrails:
        if guardrail.metric not in values:
            breaches.append(f"{guardrail.metric}: not measured, guardrail cannot be cleared")
            continue
        value = values[guardrail.metric]
        if guardrail.breached_by(value):
            breaches.append(
                f"{guardrail.metric}={value:g} breaches {guardrail.direction.value} {guardrail.threshold:g}"
            )
    return breaches


def evaluate(analysis: ExperimentAnalysis) -> ExperimentVerdict:
    """Turn measurements into a verdict."""
    experiment = analysis.experiment
    control = analysis.arm(experiment.control.name)
    variants = [analysis.arm(a.name) for a in experiment.variants]

    reasons: list[str] = []
    rules: list[str] = []

    # EXP-002 — guardrails are checked first: a breach ends the analysis.
    breaches = _guardrail_breaches(experiment.guardrails, analysis.guardrail_values)
    if breaches:
        rules.extend(rule_ids("EXP-002"))
        reasons.append("guardrail breached")
        return ExperimentVerdict(
            experiment_id=experiment.id,
            verdict=Verdict.REJECT,
            reasons=tuple(reasons),
            guardrail_breaches=tuple(breaches),
            rule_ids=tuple(rules),
        )

    # EXP-001 — power before significance.
    underpowered = [
        r.arm for r in (control, *variants) if r.trials < experiment.min_sample_per_arm
    ]
    if underpowered:
        rules.extend(rule_ids("EXP-001"))
        return ExperimentVerdict(
            experiment_id=experiment.id,
            verdict=Verdict.INCONCLUSIVE,
            reasons=(
                f"arms below the pre-registered minimum of {experiment.min_sample_per_arm}: "
                + ", ".join(underpowered),
            ),
            rule_ids=tuple(rules),
        )

    primary = two_proportion_z_test(
        control_successes=control.successes,
        control_trials=control.trials,
        variant_successes=variants[0].successes,
        variant_trials=variants[0].trials,
        name=experiment.primary_metric,
        confidence=experiment.confidence,
    )

    secondary: list[TestResult] = []
    for name, secondary_control, secondary_variant in analysis.secondary_results:
        secondary.append(
            two_proportion_z_test(
                control_successes=secondary_control.successes,
                control_trials=secondary_control.trials,
                variant_successes=secondary_variant.successes,
                variant_trials=secondary_variant.trials,
                name=name,
                confidence=experiment.confidence,
            )
        )

    # EXP-003 — correct across every comparison that was actually run.
    all_tests = [primary, *secondary]
    corrected = holm_bonferroni([t.p_value for t in all_tests], alpha=analysis.alpha)
    primary_adjusted_p, primary_significant = corrected[0]
    if len(all_tests) > 1:
        rules.extend(rule_ids("EXP-003"))

    reasons.append(
        f"{experiment.primary_metric}: {primary.estimate:+.4g} "
        f"(95% CI [{primary.ci_low:+.4g}, {primary.ci_high:+.4g}], "
        f"p={primary.p_value:.4g}, Holm-adjusted p={primary_adjusted_p:.4g})"
    )

    if primary_significant and primary.estimate > 0:
        verdict = Verdict.ADOPT
        claim = EffectClaim(
            hypothesis_id=experiment.hypothesis_id,
            experiment_id=experiment.id,
            metric=experiment.primary_metric,
            point_estimate=primary.estimate,
            ci_low=primary.ci_low,
            ci_high=primary.ci_high,
            n_control=control.trials,
            n_variant=variants[0].trials,
        )
    elif primary_significant and primary.estimate < 0:
        verdict = Verdict.REJECT
        reasons.append("variant is significantly worse than control")
        claim = None
    else:
        verdict = Verdict.INCONCLUSIVE
        reasons.append("the interval includes no effect after correction")
        claim = None

    return ExperimentVerdict(
        experiment_id=experiment.id,
        verdict=verdict,
        reasons=tuple(reasons),
        primary=primary,
        secondary=tuple(secondary),
        claim=claim,
        rule_ids=tuple(rules),
    )
