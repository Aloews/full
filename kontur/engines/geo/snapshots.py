"""Temporal snapshots of Alice AI answers.

Alice can produce a different answer, and a different set of sources, for the
same query at different moments. Kontur therefore stores snapshots and treats a
single observation as an anecdote: a change is only reportable when it is
visible across repeated measurements (rule GEO-003).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from kontur.core.errors import ConfigurationError, InsufficientDataError
from kontur.engines.geo.models import AliceObservation, AliceSnapshot

#: How many weekly observations of a query are required before a change in its
#: AI visibility is reported as a change rather than as noise.
MIN_OBSERVATIONS_FOR_TREND = 3


def _jaccard_distance(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    return 1.0 - len(a & b) / len(union)


def answer_volatility(source_sets: Sequence[Iterable[str]]) -> float:
    """How much the cited-source set moves between consecutive snapshots.

    0.0 = the same sources every week, 1.0 = complete turnover every week.
    High volatility means single-snapshot comparisons for this query are
    meaningless, not that anything improved or degraded.
    """
    sets = [frozenset(s.strip().lower() for s in item if s and s.strip()) for item in source_sets]
    if len(sets) < 2:
        raise InsufficientDataError(
            "answer_volatility needs at least two snapshots; one capture has no variance"
        )
    # Each Jaccard distance is within [0, 1], so their mean is too.
    distances = [_jaccard_distance(sets[i], sets[i + 1]) for i in range(len(sets) - 1)]
    return sum(distances) / len(distances)


@dataclass(frozen=True, slots=True)
class QueryTimeline:
    """Every observation of one query, in chronological order."""

    site: str
    query: str
    observations: tuple[AliceObservation, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "observations", tuple(sorted(self.observations, key=lambda o: o.week_start))
        )

    def __len__(self) -> int:
        return len(self.observations)

    @property
    def weeks(self) -> tuple[date, ...]:
        return tuple(o.week_start for o in self.observations)

    @property
    def mention_history(self) -> tuple[bool, ...]:
        return tuple(o.our_domain_mentioned for o in self.observations)

    @property
    def source_sets(self) -> tuple[frozenset[str], ...]:
        return tuple(frozenset(o.sources) for o in self.observations)

    def volatility(self) -> float:
        return answer_volatility([set(s) for s in self.source_sets])

    def to_dict(self) -> dict[str, Any]:
        return {
            "site": self.site,
            "query": self.query,
            "observations": len(self.observations),
            "weeks": [w.isoformat() for w in self.weeks],
            "mention_history": list(self.mention_history),
            "sources_per_week": [sorted(s) for s in self.source_sets],
        }


@dataclass(frozen=True, slots=True)
class TrendVerdict:
    """Whether a visibility change survives repeated measurement."""

    query: str
    observations: int
    reportable: bool
    direction: str
    volatility: float | None
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "observations": self.observations,
            "reportable": self.reportable,
            "direction": self.direction,
            "volatility": None if self.volatility is None else round(self.volatility, 3),
            "explanation": self.explanation,
        }


def assess_trend(
    timeline: QueryTimeline, *, min_observations: int = MIN_OBSERVATIONS_FOR_TREND
) -> TrendVerdict:
    """Decide whether this query's history supports reporting a change."""
    if min_observations < 2:
        raise ConfigurationError("min_observations must be >= 2")

    count = len(timeline)
    if count < min_observations:
        return TrendVerdict(
            query=timeline.query,
            observations=count,
            reportable=False,
            direction="unknown",
            volatility=None,
            explanation=(
                f"{count} observation(s) < {min_observations} required: Alice varies its answers, "
                "so this is not yet a measurable change"
            ),
        )

    history = timeline.mention_history
    first_half = history[: count // 2]
    second_half = history[count // 2 :]
    before = sum(first_half) / len(first_half)
    after = sum(second_half) / len(second_half)
    volatility = timeline.volatility()

    if after > before:
        direction = "gained"
    elif after < before:
        direction = "lost"
    else:
        direction = "flat"

    reportable = direction != "flat" and volatility < 0.8
    explanation = (
        f"mention rate {before:.0%} -> {after:.0%} over {count} weekly observations, "
        f"source volatility {volatility:.2f}"
    )
    if not reportable and direction != "flat":
        explanation += "; source set is too volatile to attribute the change"
    return TrendVerdict(
        query=timeline.query,
        observations=count,
        reportable=reportable,
        direction=direction,
        volatility=volatility,
        explanation=explanation,
    )


@dataclass
class SnapshotStore:
    """Weekly snapshots per site, with query timelines built on demand."""

    snapshots: list[AliceSnapshot] = field(default_factory=list)

    def add(self, snapshot: AliceSnapshot) -> SnapshotStore:
        if not isinstance(snapshot, AliceSnapshot):
            raise ConfigurationError("SnapshotStore stores AliceSnapshot objects")
        replaced = [
            s for s in self.snapshots
            if not (s.site == snapshot.site and s.week_start == snapshot.week_start)
        ]
        replaced.append(snapshot)
        self.snapshots = sorted(replaced, key=lambda s: (s.site, s.week_start))
        return self

    def sites(self) -> tuple[str, ...]:
        return tuple(sorted({s.site for s in self.snapshots}))

    def for_site(self, site: str) -> list[AliceSnapshot]:
        needle = site.strip().lower().removeprefix("www.")
        return [s for s in self.snapshots if s.site == needle]

    def window(self, site: str, *, weeks: int = 12) -> list[AliceSnapshot]:
        """The most recent ``weeks`` snapshots — the export covers three months."""
        if weeks < 1:
            raise ConfigurationError("weeks must be >= 1")
        return self.for_site(site)[-weeks:]

    def timeline(self, site: str, query: str) -> QueryTimeline:
        needle = " ".join(query.split()).lower()
        observations = [
            observation
            for snapshot in self.for_site(site)
            for observation in snapshot.observations
            if observation.query == needle
        ]
        if not observations:
            raise InsufficientDataError(f"no observations of {query!r} for {site}")
        return QueryTimeline(site=site.strip().lower(), query=needle, observations=tuple(observations))

    def queries(self, site: str) -> tuple[str, ...]:
        return tuple(sorted({o.query for s in self.for_site(site) for o in s.observations}))

    def volatile_queries(self, site: str, *, threshold: float = 0.5) -> list[dict[str, Any]]:
        """Queries whose source set churns enough to invalidate one-off checks."""
        rows: list[dict[str, Any]] = []
        for query in self.queries(site):
            timeline = self.timeline(site, query)
            if len(timeline) < 2:
                continue
            volatility = timeline.volatility()
            if volatility >= threshold:
                rows.append(
                    {"query": query, "observations": len(timeline), "volatility": round(volatility, 3)}
                )
        return sorted(rows, key=lambda r: -r["volatility"])
