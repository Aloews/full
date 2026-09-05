"""Hypotheses and effect claims.

GEO/AEO techniques are treated as hypotheses under test, not as known causes.
A recent survey of the GEO literature (2023-2026) reports that the field is
heterogeneous and that no stable, universal causal effect of optimisation
techniques on organic discoverability or downstream behaviour has been
established; repeated measurement, controls and human verification are what
the evidence actually supports.

So Kontur can say "hypothesis H-004 is under test in experiment EXP-12" and it
can say "in experiment EXP-12 the variant's cited-URL rate was 4.1pp higher,
95% CI [1.2, 7.0]". It cannot say "this gives +120% AI visibility".
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from kontur.core.errors import ConfigurationError, UnprovenClaimError


class HypothesisStatus(StrEnum):
    PROPOSED = "proposed"
    TESTING = "testing"
    SUPPORTED = "supported"
    REFUTED = "refuted"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True, slots=True)
class Hypothesis:
    """A testable editorial or technical guideline."""

    id: str
    statement: str
    metric: str
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    experiment_ids: tuple[str, ...] = ()
    note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", HypothesisStatus(self.status))
        if self.status in (HypothesisStatus.SUPPORTED, HypothesisStatus.REFUTED) and not self.experiment_ids:
            raise ConfigurationError(
                f"hypothesis {self.id} claims status {self.status} without any experiment"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "statement": self.statement,
            "metric": self.metric,
            "status": self.status.value,
            "experiment_ids": list(self.experiment_ids),
            "note": self.note,
        }


#: Guidelines Kontur ships with. Every one of them starts as a hypothesis.
HYPOTHESES: dict[str, Hypothesis] = {
    h.id: h
    for h in (
        Hypothesis("H-001", "An answer-first opening block increases the rate at which our URL "
                            "is cited by Alice AI for the target query.",
                   "cited_url_rate"),
        Hypothesis("H-002", "Answer length bucket 20-40 words is cited more often than 60-100 "
                            "for definitional queries.", "cited_url_rate",
                   note="Arms: 20-40 / 40-60 / 60-100. There is no established optimum; "
                        "the bucket is the treatment, not a rule."),
        Hypothesis("H-003", "A comparison table for provider/mechanic pages increases the share "
                            "of queries where our page is a cited source.", "query_coverage"),
        Hypothesis("H-004", "Promoting a filter state to an indexable hub increases non-brand "
                            "organic entries for its query cluster without cannibalising the parent.",
                   "organic_entries"),
        Hypothesis("H-005", "Reducing indexable parameter combinations shortens the time from "
                            "publication to first indexation.", "days_to_index"),
    )
}


@dataclass(frozen=True, slots=True)
class EffectClaim:
    """A statement about an effect. Only constructible with a linked experiment."""

    hypothesis_id: str
    experiment_id: str
    metric: str
    point_estimate: float
    ci_low: float
    ci_high: float
    n_control: int
    n_variant: int
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.experiment_id:
            raise UnprovenClaimError(
                f"effect claim for {self.hypothesis_id} has no experiment_id; "
                "unmeasured effects cannot be stated"
            )
        if self.ci_low > self.ci_high:
            raise ConfigurationError("ci_low must be <= ci_high")
        if min(self.n_control, self.n_variant) <= 0:
            raise UnprovenClaimError("effect claim needs a non-empty control and variant")

    @property
    def crosses_zero(self) -> bool:
        return self.ci_low <= 0.0 <= self.ci_high

    def statement(self) -> str:
        """A sentence that reports the measurement and nothing more."""
        direction = "difference"
        return (
            f"In {self.experiment_id}, the variant's {self.metric} showed a {direction} of "
            f"{self.point_estimate:+.4g} (95% CI [{self.ci_low:+.4g}, {self.ci_high:+.4g}], "
            f"n={self.n_control}/{self.n_variant})."
            + (" The interval includes zero." if self.crosses_zero else "")
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "experiment_id": self.experiment_id,
            "metric": self.metric,
            "point_estimate": self.point_estimate,
            "ci": [self.ci_low, self.ci_high],
            "n_control": self.n_control,
            "n_variant": self.n_variant,
            "crosses_zero": self.crosses_zero,
            "statement": self.statement(),
        }


# Patterns that turn a measurement into a promise. Assembled from fragments so
# this module does not itself contain a literal marketing sentence for the
# repository scanner to trip over.
_UPLIFT = r"[+]\s*\d+(?:[.,]\d+)?\s*%"
_PROMISE_WORDS = r"guarantee[ds]?|guarantees|гарантир\w*"
_RANK_PROMISE = r"(?:boost|increase|улучшит|повысит)\w*\s+(?:your\s+)?(?:rankings?|позици\w+)"

FORBIDDEN_CLAIM_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(rf"{_UPLIFT}\s*(?:to|к|в)?\s*(?:ai|geo|aeo)\s*visibility", re.IGNORECASE),
    re.compile(rf"{_UPLIFT}\s*(?:to|к)\s*(?:traffic|трафик\w*)", re.IGNORECASE),
    re.compile(_PROMISE_WORDS + r"\s+(?:top|первое место|рост|growth)", re.IGNORECASE),
    re.compile(_RANK_PROMISE, re.IGNORECASE),
    re.compile(r"\branking factor\b(?!\s*(?:\?|claim|myth))", re.IGNORECASE),
    re.compile(r"фактор\w*\s+ранжирован\w+", re.IGNORECASE),
)


def find_unproven_claims(text: str) -> list[str]:
    """Return the fragments of ``text`` that assert an unproven effect."""
    hits: list[str] = []
    for pattern in FORBIDDEN_CLAIM_PATTERNS:
        hits.extend(match.group(0).strip() for match in pattern.finditer(text))
    return hits


def assert_no_unproven_claims(text: str, *, where: str = "text") -> None:
    """Raise :class:`UnprovenClaimError` if ``text`` promises an effect."""
    hits = find_unproven_claims(text)
    if hits:
        raise UnprovenClaimError(f"{where} contains unproven effect claims: {hits}")


def guideline(hypothesis_id: str, *, statuses: Iterable[HypothesisStatus] | None = None) -> Hypothesis:
    """Fetch a hypothesis, optionally requiring it to be in one of ``statuses``."""
    try:
        hypothesis = HYPOTHESES[hypothesis_id]
    except KeyError as exc:
        raise ConfigurationError(f"unknown hypothesis {hypothesis_id!r}") from exc
    if statuses is not None and hypothesis.status not in {HypothesisStatus(s) for s in statuses}:
        raise UnprovenClaimError(
            f"hypothesis {hypothesis_id} is {hypothesis.status}, not one of {list(statuses)}"
        )
    return hypothesis


@dataclass(frozen=True, slots=True)
class GuidelineRecommendation:
    """A recommendation that always travels with its evidential status."""

    hypothesis_id: str
    action: str
    evidence: tuple[EffectClaim, ...] = field(default_factory=tuple)

    @property
    def status(self) -> HypothesisStatus:
        return guideline(self.hypothesis_id).status

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "action": self.action,
            "status": self.status.value,
            "evidence": [c.to_dict() for c in self.evidence],
            "caveat": (
                "Editorial hypothesis under test. No causal effect on rankings or AI "
                "visibility is asserted; adopt only after an experiment supports it."
            ),
        }
