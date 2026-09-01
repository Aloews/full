"""The behavioural funnel.

    SERP CTR -> Landing engagement -> Filter interaction -> Game interaction -> Conversion

This is an analytics layer, not a target list. Kontur reports where users drop
out; it does not assert that any dwell time or engagement rate causes a ranking
change (see :mod:`kontur.engines.behavior.correlation`).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Any, Sequence

from kontur.core.errors import ConfigurationError, InsufficientDataError
from kontur.core.provenance import EvidenceSet, Provenance


class FunnelStage(StrEnum):
    IMPRESSION = "serp_impression"
    CLICK = "serp_click"
    ENGAGED = "landing_engagement"
    FILTER = "filter_interaction"
    GAME = "game_interaction"
    CONVERSION = "conversion"


ORDERED_STAGES: tuple[FunnelStage, ...] = (
    FunnelStage.IMPRESSION,
    FunnelStage.CLICK,
    FunnelStage.ENGAGED,
    FunnelStage.FILTER,
    FunnelStage.GAME,
    FunnelStage.CONVERSION,
)


@dataclass(frozen=True, slots=True)
class FunnelObservation:
    """Counts for one URL over one period."""

    url: str
    period: date
    provenance: Provenance
    impressions: int = 0
    clicks: int = 0
    engaged_sessions: int = 0
    filter_interactions: int = 0
    game_interactions: int = 0
    conversions: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.provenance, Provenance):
            raise ConfigurationError("funnel observations require provenance")
        counts = self.as_counts()
        for name, value in counts.items():
            if value < 0:
                raise ConfigurationError(f"{name} must be >= 0")
        ordered = [counts[stage.value] for stage in ORDERED_STAGES]
        for index in range(1, len(ordered)):
            if ordered[index] > ordered[index - 1]:
                raise ConfigurationError(
                    f"{ORDERED_STAGES[index].value}={ordered[index]} exceeds the preceding "
                    f"{ORDERED_STAGES[index - 1].value}={ordered[index - 1]}: the funnel cannot widen"
                )

    def as_counts(self) -> dict[str, int]:
        return {
            FunnelStage.IMPRESSION.value: self.impressions,
            FunnelStage.CLICK.value: self.clicks,
            FunnelStage.ENGAGED.value: self.engaged_sessions,
            FunnelStage.FILTER.value: self.filter_interactions,
            FunnelStage.GAME.value: self.game_interactions,
            FunnelStage.CONVERSION.value: self.conversions,
        }


@dataclass(frozen=True, slots=True)
class FunnelReport:
    url: str
    periods: int
    counts: dict[str, int]
    step_rates: dict[str, float]
    biggest_drop: str
    evidence: EvidenceSet

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "periods": self.periods,
            "counts": self.counts,
            "step_rates": {k: round(v, 4) for k, v in self.step_rates.items()},
            "biggest_drop": self.biggest_drop,
            "evidence": self.evidence.to_list(),
            "caveat": (
                "Descriptive funnel. Stage rates are outcomes to investigate, not "
                "targets to hit, and not ranking inputs."
            ),
        }


def build_funnel(observations: Sequence[FunnelObservation]) -> FunnelReport:
    """Aggregate observations for one URL into stage counts and step rates."""
    if not observations:
        raise InsufficientDataError("build_funnel() needs at least one observation")
    urls = {o.url for o in observations}
    if len(urls) != 1:
        raise ConfigurationError(f"observations span several URLs: {sorted(urls)}")

    totals: dict[str, int] = {stage.value: 0 for stage in ORDERED_STAGES}
    for observation in observations:
        for key, value in observation.as_counts().items():
            totals[key] += value

    step_rates: dict[str, float] = {}
    for index in range(1, len(ORDERED_STAGES)):
        previous, current = ORDERED_STAGES[index - 1], ORDERED_STAGES[index]
        denominator = totals[previous.value]
        step_rates[f"{previous.value}->{current.value}"] = (
            totals[current.value] / denominator if denominator else 0.0
        )

    biggest_drop = min(step_rates, key=lambda k: step_rates[k]) if step_rates else ""
    return FunnelReport(
        url=next(iter(urls)),
        periods=len(observations),
        counts=totals,
        step_rates=step_rates,
        biggest_drop=biggest_drop,
        evidence=EvidenceSet.of(*(o.provenance for o in observations)),
    )
