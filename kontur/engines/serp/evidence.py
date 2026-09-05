"""OUR PAGE -> COMPETITOR MATRIX -> CONTENT / ENTITY / QUESTION GAP -> INFORMATION GAIN."""

from __future__ import annotations

import statistics
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

from kontur.core.errors import ConfigurationError, InsufficientDataError
from kontur.core.provenance import EvidenceSet
from kontur.engines.serp.models import (
    CompetitorResult,
    PageProfile,
    SerpEvidenceSummary,
    SerpSnapshot,
)

#: Share of the analysed competitors that must contain a heading/entity/question
#: before it counts as SERP consensus rather than one site's idea.
CONSENSUS_SHARE = 0.5

DedicatedMatcher = Callable[[CompetitorResult], bool]


def token_matcher(*tokens: str) -> DedicatedMatcher:
    """A competitor page counts as dedicated when the facet token is in its URL or H1."""
    needles = tuple(t.strip().lower() for t in tokens if t.strip())
    if not needles:
        raise ConfigurationError("token_matcher() needs at least one token")

    def matcher(result: CompetitorResult) -> bool:
        haystack = f"{result.profile.url} {result.profile.h1} {result.profile.title}".lower()
        return any(needle in haystack for needle in needles)

    return matcher


def _consensus(
    values: Sequence[frozenset[str]], *, share: float = CONSENSUS_SHARE
) -> frozenset[str]:
    if not values:
        return frozenset()
    threshold = max(1, round(len(values) * share))
    counts: dict[str, int] = {}
    for value_set in values:
        for item in value_set:
            counts[item] = counts.get(item, 0) + 1
    return frozenset(item for item, count in counts.items() if count >= threshold)


def summarise_serp(
    snapshot: SerpSnapshot,
    *,
    top_n: int = 10,
    dedicated: DedicatedMatcher | None = None,
    consensus_share: float = CONSENSUS_SHARE,
) -> SerpEvidenceSummary:
    """Collapse a SERP capture into the consensus shape of the pages that rank."""
    results = snapshot.top(top_n)
    if not results:
        return SerpEvidenceSummary(
            query=snapshot.query,
            competitors_analysed=0,
            dedicated_pages=0,
            median_word_count=0,
            evidence=EvidenceSet.of(snapshot.provenance),
        )

    profiles = [r.profile for r in results]
    return SerpEvidenceSummary(
        query=snapshot.query,
        competitors_analysed=len(results),
        dedicated_pages=sum(1 for r in results if dedicated(r)) if dedicated else 0,
        median_word_count=int(statistics.median(p.word_count for p in profiles)),
        common_headings=_consensus([p.heading_set for p in profiles], share=consensus_share),
        common_entities=_consensus([p.entities for p in profiles], share=consensus_share),
        common_questions=_consensus([p.question_set for p in profiles], share=consensus_share),
        table_share=sum(1 for p in profiles if p.has_table) / len(profiles),
        schema_share=sum(1 for p in profiles if p.schema_types) / len(profiles),
        evidence=EvidenceSet.of(snapshot.provenance),
    )


@dataclass(frozen=True, slots=True)
class ContentGap:
    """What the SERP consensus has and our page does not."""

    query: str
    missing_headings: tuple[str, ...] = ()
    missing_entities: tuple[str, ...] = ()
    missing_questions: tuple[str, ...] = ()
    word_count_delta: int = 0
    missing_table: bool = False
    missing_schema: bool = False
    extra_entities: tuple[str, ...] = ()
    extra_questions: tuple[str, ...] = ()
    evidence: EvidenceSet = field(default_factory=EvidenceSet)

    @property
    def is_empty(self) -> bool:
        return not (
            self.missing_headings
            or self.missing_entities
            or self.missing_questions
            or self.missing_table
            or self.missing_schema
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "missing_headings": list(self.missing_headings),
            "missing_entities": list(self.missing_entities),
            "missing_questions": list(self.missing_questions),
            "word_count_delta": self.word_count_delta,
            "missing_table": self.missing_table,
            "missing_schema": self.missing_schema,
            "extra_entities": list(self.extra_entities),
            "extra_questions": list(self.extra_questions),
            "evidence": self.evidence.to_list(),
        }


def content_gap(our_page: PageProfile, summary: SerpEvidenceSummary) -> ContentGap:
    """Diff our page against the SERP consensus, in both directions."""
    if summary.competitors_analysed == 0:
        raise InsufficientDataError(
            f"no competitors analysed for {summary.query!r}; cannot compute a gap"
        )
    return ContentGap(
        query=summary.query,
        missing_headings=tuple(sorted(summary.common_headings - our_page.heading_set)),
        missing_entities=tuple(sorted(summary.common_entities - our_page.entities)),
        missing_questions=tuple(sorted(summary.common_questions - our_page.question_set)),
        word_count_delta=our_page.word_count - summary.median_word_count,
        missing_table=summary.table_share >= 0.5 and not our_page.has_table,
        missing_schema=summary.schema_share >= 0.5 and not our_page.schema_types,
        extra_entities=tuple(sorted(our_page.entities - summary.common_entities)),
        extra_questions=tuple(sorted(our_page.question_set - summary.common_questions)),
        evidence=summary.evidence,
    )


def information_gain_score(
    our_page: PageProfile,
    summary: SerpEvidenceSummary,
    *,
    entity_target: int = 5,
    question_target: int = 3,
) -> float:
    """How much this page adds beyond what the ranking set already says.

    This measures *difference from the consensus*, nothing more. It is an input
    to editorial prioritisation, not a prediction of ranking movement.
    """
    if entity_target < 1 or question_target < 1:
        raise ConfigurationError("targets must be >= 1")
    if summary.competitors_analysed == 0:
        raise InsufficientDataError(
            f"no competitors analysed for {summary.query!r}; information gain is undefined"
        )

    extra_entities = len(our_page.entities - summary.common_entities)
    extra_questions = len(our_page.question_set - summary.common_questions)
    entity_part = min(extra_entities / entity_target, 1.0)
    question_part = min(extra_questions / question_target, 1.0)

    structural = 0.0
    if our_page.has_table and summary.table_share < 0.5:
        structural += 0.5
    if our_page.schema_types and summary.schema_share < 0.5:
        structural += 0.5

    score = 0.5 * entity_part + 0.3 * question_part + 0.2 * min(structural, 1.0)
    return min(1.0, max(0.0, score))


@dataclass(frozen=True, slots=True)
class CompetitorMatrix:
    """Row-per-competitor view used by the SEO hub report."""

    query: str
    rows: tuple[dict[str, Any], ...]
    summary: SerpEvidenceSummary

    def to_dict(self) -> dict[str, Any]:
        return {"query": self.query, "rows": list(self.rows), "summary": self.summary.to_dict()}


def competitor_matrix(
    snapshot: SerpSnapshot,
    *,
    top_n: int = 10,
    dedicated: DedicatedMatcher | None = None,
) -> CompetitorMatrix:
    summary = summarise_serp(snapshot, top_n=top_n, dedicated=dedicated)
    rows: list[dict[str, Any]] = []
    for result in snapshot.top(top_n):
        profile = result.profile
        rows.append(
            {
                "position": result.position,
                "domain": result.domain,
                "url": profile.url,
                "title": profile.title,
                "h1": profile.h1,
                "word_count": profile.word_count,
                "headings": len(profile.headings),
                "questions": len(profile.questions),
                "tables": profile.tables,
                "entities": len(profile.entities),
                "internal_links": profile.internal_links,
                "schema": sorted(profile.schema_types),
                "freshness_days": profile.freshness_days(),
                "dedicated": bool(dedicated(result)) if dedicated else None,
            }
        )
    return CompetitorMatrix(query=snapshot.query, rows=tuple(rows), summary=summary)


def opportunities(gap: ContentGap, *, limit: int = 10) -> list[str]:
    """Human-readable, non-promissory next actions derived from the gap."""
    actions: list[str] = []
    for question in gap.missing_questions[:limit]:
        actions.append(f"Answer the question competitors cover: {question!r}")
    for entity in gap.missing_entities[:limit]:
        actions.append(f"Cover the entity present across the SERP: {entity!r}")
    for heading in gap.missing_headings[:limit]:
        actions.append(f"Add a section for: {heading!r}")
    if gap.missing_table:
        actions.append("Add a comparison table: most ranking pages have one")
    if gap.missing_schema:
        actions.append("Add structured data: most ranking pages expose it")
    if gap.word_count_delta < 0:
        actions.append(
            f"Page is {abs(gap.word_count_delta)} words below the SERP median "
            "— check for uncovered subtopics, not for padding"
        )
    return actions[:limit]


def _iter_profiles(results: Iterable[CompetitorResult]) -> list[PageProfile]:
    return [r.profile for r in results]
