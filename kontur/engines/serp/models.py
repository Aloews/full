"""SERP evidence: what the pages that already rank actually contain."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from kontur.core.errors import ConfigurationError
from kontur.core.provenance import EvidenceSet, Provenance


def _norm_set(values: Iterable[str]) -> frozenset[str]:
    return frozenset(v.strip().lower() for v in values if v and v.strip())


@dataclass(frozen=True, slots=True)
class PageProfile:
    """The extractable shape of a page — ours or a competitor's."""

    url: str
    title: str = ""
    h1: str = ""
    word_count: int = 0
    headings: tuple[str, ...] = ()
    questions: tuple[str, ...] = ()
    entities: frozenset[str] = frozenset()
    tables: int = 0
    internal_links: int = 0
    schema_types: frozenset[str] = frozenset()
    last_modified: datetime | None = None

    def __post_init__(self) -> None:
        if self.word_count < 0 or self.tables < 0 or self.internal_links < 0:
            raise ConfigurationError("page profile counters must be >= 0")
        object.__setattr__(self, "entities", _norm_set(self.entities))
        object.__setattr__(self, "schema_types", _norm_set(self.schema_types))
        object.__setattr__(self, "headings", tuple(h.strip() for h in self.headings if h.strip()))
        object.__setattr__(self, "questions", tuple(q.strip() for q in self.questions if q.strip()))

    @property
    def heading_set(self) -> frozenset[str]:
        return _norm_set(self.headings)

    @property
    def question_set(self) -> frozenset[str]:
        return _norm_set(self.questions)

    @property
    def has_table(self) -> bool:
        return self.tables > 0

    def freshness_days(self, now: datetime | None = None) -> float | None:
        if self.last_modified is None:
            return None
        now = now or datetime.now(UTC)
        last = self.last_modified
        if last.tzinfo is None:
            last = last.replace(tzinfo=UTC)
        return (now - last).total_seconds() / 86400.0


@dataclass(frozen=True, slots=True)
class CompetitorResult:
    """One organic result plus the profile we extracted from it."""

    domain: str
    position: int
    profile: PageProfile

    def __post_init__(self) -> None:
        if self.position < 1:
            raise ConfigurationError("SERP position starts at 1")
        object.__setattr__(self, "domain", self.domain.strip().lower())


@dataclass(frozen=True, slots=True)
class SerpSnapshot:
    """One capture of a SERP. Never treated as permanent."""

    query: str
    captured_at: datetime
    results: tuple[CompetitorResult, ...]
    provenance: Provenance
    region: str = "ru"
    device: str = "desktop"

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ConfigurationError("SERP snapshot needs a query")
        if not isinstance(self.provenance, Provenance):
            raise ConfigurationError("SERP snapshot needs provenance")
        object.__setattr__(self, "query", self.query.strip().lower())
        object.__setattr__(
            self, "results", tuple(sorted(self.results, key=lambda r: r.position))
        )

    def top(self, n: int = 10) -> tuple[CompetitorResult, ...]:
        return self.results[:n]

    @property
    def domains(self) -> tuple[str, ...]:
        return tuple(r.domain for r in self.results)


@dataclass(frozen=True, slots=True)
class SerpEvidenceSummary:
    """What the top of the SERP agrees on for one query."""

    query: str
    competitors_analysed: int
    dedicated_pages: int
    median_word_count: int
    common_headings: frozenset[str] = frozenset()
    common_entities: frozenset[str] = frozenset()
    common_questions: frozenset[str] = frozenset()
    table_share: float = 0.0
    schema_share: float = 0.0
    evidence: EvidenceSet = field(default_factory=EvidenceSet)

    def __post_init__(self) -> None:
        if self.competitors_analysed < 0 or self.dedicated_pages < 0:
            raise ConfigurationError("counters must be >= 0")
        if self.dedicated_pages > self.competitors_analysed:
            raise ConfigurationError("dedicated_pages cannot exceed competitors_analysed")
        for name in ("table_share", "schema_share"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ConfigurationError(f"{name} must be within [0, 1]")

    @property
    def has_dedicated_pages(self) -> bool:
        """True when a meaningful part of the top results is a page for this exact intent."""
        if self.competitors_analysed == 0:
            return False
        return self.dedicated_pages >= 2 or (self.dedicated_pages / self.competitors_analysed) >= 0.3

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "competitors_analysed": self.competitors_analysed,
            "dedicated_pages": self.dedicated_pages,
            "has_dedicated_pages": self.has_dedicated_pages,
            "median_word_count": self.median_word_count,
            "common_headings": sorted(self.common_headings),
            "common_entities": sorted(self.common_entities),
            "common_questions": sorted(self.common_questions),
            "table_share": self.table_share,
            "schema_share": self.schema_share,
            "evidence": self.evidence.to_list(),
        }
