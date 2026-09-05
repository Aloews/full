"""Data model for Yandex Webmaster's "site visibility in Alice AI" export.

The report Yandex publishes is weekly, covers the last three months, and shows
Share of Voice, the queries, the pages and the competing sources. Kontur stores
it as *observations with a retrieval date*, never as a standing truth: Alice can
return a different answer and a different set of sources for the same query at
different moments, so a single row is evidence about one moment only.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any

from kontur.core.errors import ConfigurationError, MissingProvenanceError
from kontur.core.provenance import EvidenceSet, Provenance


class AnswerType(StrEnum):
    """Shape of the assistant answer, as far as the export tells us."""

    GENERATED = "generated"
    SUMMARY = "summary"
    LIST = "list"
    LINKS_ONLY = "links_only"
    NO_ANSWER = "no_answer"
    UNKNOWN = "unknown"


def _norm_domain(value: str) -> str:
    domain = (value or "").strip().lower()
    if domain.startswith("http://") or domain.startswith("https://"):
        domain = domain.split("//", 1)[1]
    return domain.split("/", 1)[0].removeprefix("www.")


@dataclass(frozen=True, slots=True)
class AliceObservation:
    """One (query, week) row of the Alice AI visibility export."""

    query: str
    week_start: date
    provenance: Provenance
    ai_answer_present: bool = True
    our_domain_mentioned: bool = False
    our_url_cited: str | None = None
    competitor_domains: tuple[str, ...] = ()
    answer_type: AnswerType = AnswerType.UNKNOWN
    serp_position: int | None = None
    impressions: int = 0

    def __post_init__(self) -> None:
        if not self.query or not self.query.strip():
            raise ConfigurationError("observation needs a query")
        if not isinstance(self.provenance, Provenance):
            raise MissingProvenanceError(
                f"Alice observation for {self.query!r} has no provenance; "
                "AI visibility rows must carry source + retrieval date + confidence"
            )
        object.__setattr__(self, "query", " ".join(self.query.split()).lower())
        object.__setattr__(self, "answer_type", AnswerType(self.answer_type))
        object.__setattr__(
            self,
            "competitor_domains",
            tuple(dict.fromkeys(_norm_domain(d) for d in self.competitor_domains if d and d.strip())),
        )
        if isinstance(self.week_start, datetime):
            object.__setattr__(self, "week_start", self.week_start.date())
        if not isinstance(self.week_start, date):
            raise ConfigurationError("week_start must be a date")
        if self.serp_position is not None and self.serp_position < 1:
            raise ConfigurationError("serp_position starts at 1")
        if self.impressions < 0:
            raise ConfigurationError("impressions must be >= 0")
        if self.our_url_cited and not self.our_domain_mentioned:
            object.__setattr__(self, "our_domain_mentioned", True)

    @property
    def is_sample(self) -> bool:
        return self.provenance.is_sample

    @property
    def sources(self) -> tuple[str, ...]:
        """Every domain cited in this answer, ours included."""
        domains = list(self.competitor_domains)
        if self.our_url_cited:
            domains.insert(0, _norm_domain(self.our_url_cited))
        return tuple(dict.fromkeys(domains))

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "week_start": self.week_start.isoformat(),
            "ai_answer_present": self.ai_answer_present,
            "our_domain_mentioned": self.our_domain_mentioned,
            "our_url_cited": self.our_url_cited,
            "competitor_domains": list(self.competitor_domains),
            "answer_type": self.answer_type.value,
            "serp_position": self.serp_position,
            "impressions": self.impressions,
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class AliceSnapshot:
    """One weekly capture of the export for one site."""

    site: str
    week_start: date
    observations: tuple[AliceObservation, ...]
    provenance: Provenance
    reported_share_of_voice: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.provenance, Provenance):
            raise MissingProvenanceError("AliceSnapshot requires provenance")
        object.__setattr__(self, "site", _norm_domain(self.site))
        if isinstance(self.week_start, datetime):
            object.__setattr__(self, "week_start", self.week_start.date())
        if self.reported_share_of_voice is not None and not 0.0 <= self.reported_share_of_voice <= 1.0:
            raise ConfigurationError("reported_share_of_voice must be within [0, 1]")
        mismatched = [o.query for o in self.observations if o.week_start != self.week_start]
        if mismatched:
            raise ConfigurationError(
                f"observations from other weeks in the {self.week_start} snapshot: {mismatched[:3]}"
            )

    @property
    def queries(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(o.query for o in self.observations))

    @property
    def evidence(self) -> EvidenceSet:
        return EvidenceSet.of(self.provenance, *(o.provenance for o in self.observations))

    @property
    def is_sample(self) -> bool:
        return self.evidence.is_sample

    def observation_for(self, query: str) -> AliceObservation | None:
        needle = " ".join(query.split()).lower()
        for observation in self.observations:
            if observation.query == needle:
                return observation
        return None

    def age_days(self, now: datetime | None = None) -> float:
        now = now or datetime.now(UTC)
        return (now.date() - self.week_start).days


def group_by_week(observations: Iterable[AliceObservation]) -> dict[date, list[AliceObservation]]:
    grouped: dict[date, list[AliceObservation]] = {}
    for observation in observations:
        grouped.setdefault(observation.week_start, []).append(observation)
    return dict(sorted(grouped.items()))


@dataclass(frozen=True, slots=True)
class QuerySet:
    """The tracked query universe, used for coverage (never extrapolated beyond it)."""

    name: str
    queries: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "queries", frozenset(" ".join(q.split()).lower() for q in self.queries if q.strip())
        )

    def __len__(self) -> int:
        return len(self.queries)
