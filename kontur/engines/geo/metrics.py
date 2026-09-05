"""AI visibility metrics computed from the Alice export.

    AI Visibility
    |- SoV
    |- Mention rate
    |- Cited URLs
    |- Query coverage
    |- Competitor overlap
    |- Winning queries
    `- Lost queries

There is no invented "GEO score" here. Every figure is a ratio over rows that
exist in an export, and every report states the window it was computed over.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from kontur.core.errors import ConfigurationError, InsufficientDataError, SampleDataError
from kontur.core.provenance import EvidenceSet
from kontur.engines.geo.models import AliceObservation, AliceSnapshot, QuerySet


def _check_rows(observations: Sequence[AliceObservation], *, what: str) -> None:
    if not observations:
        raise InsufficientDataError(f"{what} needs at least one observation")
    for observation in observations:
        if not isinstance(observation, AliceObservation):
            raise ConfigurationError(f"{what} expects AliceObservation rows")


def share_of_voice(observations: Sequence[AliceObservation]) -> float:
    """Our share of all source citations in the answers covered by the export.

    Computed strictly over the supplied rows (rule GEO-004): a query that is not
    in the export contributes nothing, in either direction.
    """
    _check_rows(observations, what="share_of_voice")
    our_citations = 0
    total_citations = 0
    for observation in observations:
        if not observation.ai_answer_present:
            continue
        # A mention counts as one citation for us whether or not the export
        # captured which of our URLs was used.
        ours = 1 if observation.our_domain_mentioned else 0
        our_citations += ours
        total_citations += len(observation.competitor_domains) + ours
    if total_citations == 0:
        return 0.0
    # our_citations counts at most one source per row and is included in the
    # denominator, so the ratio cannot leave [0, 1] and needs no clamp.
    return our_citations / total_citations


def mention_rate(observations: Sequence[AliceObservation]) -> float:
    """Share of answered queries where our domain appears at all."""
    _check_rows(observations, what="mention_rate")
    answered = [o for o in observations if o.ai_answer_present]
    if not answered:
        return 0.0
    return sum(1 for o in answered if o.our_domain_mentioned) / len(answered)


def cited_urls(observations: Sequence[AliceObservation]) -> list[tuple[str, int]]:
    """Our URLs that Alice cited, most cited first."""
    _check_rows(observations, what="cited_urls")
    counter = Counter(o.our_url_cited for o in observations if o.our_url_cited)
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))


def query_coverage(observations: Sequence[AliceObservation], query_set: QuerySet) -> float:
    """Share of the tracked query set where we are mentioned."""
    _check_rows(observations, what="query_coverage")
    if len(query_set) == 0:
        raise InsufficientDataError("query_coverage needs a non-empty query set")
    mentioned = {o.query for o in observations if o.our_domain_mentioned} & query_set.queries
    return len(mentioned) / len(query_set)


def competitor_overlap(observations: Sequence[AliceObservation]) -> list[dict[str, Any]]:
    """Per competitor: how often they are cited, and how often alongside us."""
    _check_rows(observations, what="competitor_overlap")
    answered = [o for o in observations if o.ai_answer_present]
    total = len(answered) or 1
    appearances: Counter[str] = Counter()
    together: Counter[str] = Counter()
    for observation in answered:
        for domain in observation.competitor_domains:
            appearances[domain] += 1
            if observation.our_domain_mentioned:
                together[domain] += 1
    rows = [
        {
            "domain": domain,
            "queries": count,
            "share": count / total,
            "co_cited_with_us": together.get(domain, 0),
            # ``count`` came from this very Counter, so it is at least 1.
            "overlap": together.get(domain, 0) / count,
        }
        for domain, count in appearances.items()
    ]
    return sorted(rows, key=lambda r: (-r["queries"], r["domain"]))


def _mentions_by_query(snapshot: AliceSnapshot) -> dict[str, bool]:
    return {o.query: o.our_domain_mentioned for o in snapshot.observations}


def winning_queries(before: AliceSnapshot, after: AliceSnapshot) -> list[str]:
    """Queries where we were absent before and are cited now (rule GEO-005)."""
    _assert_comparable(before, after)
    old, new = _mentions_by_query(before), _mentions_by_query(after)
    return sorted(q for q, mentioned in new.items() if mentioned and not old.get(q, False))


def lost_queries(before: AliceSnapshot, after: AliceSnapshot) -> list[str]:
    """Queries where we were cited before and are absent now (rule GEO-005)."""
    _assert_comparable(before, after)
    old, new = _mentions_by_query(before), _mentions_by_query(after)
    return sorted(q for q, mentioned in old.items() if mentioned and not new.get(q, False))


def _assert_comparable(before: AliceSnapshot, after: AliceSnapshot) -> None:
    if not isinstance(before, AliceSnapshot) or not isinstance(after, AliceSnapshot):
        raise ConfigurationError("winning/lost queries need two AliceSnapshot objects")
    if before.site != after.site:
        raise ConfigurationError(
            f"cannot compare snapshots of different sites: {before.site} vs {after.site}"
        )
    if before.week_start >= after.week_start:
        raise ConfigurationError(
            f"'before' snapshot ({before.week_start}) must precede 'after' ({after.week_start})"
        )
    shared = set(before.queries) & set(after.queries)
    if not shared:
        raise InsufficientDataError(
            "the two snapshots share no queries; a delta over disjoint query sets is meaningless"
        )


@dataclass(frozen=True, slots=True)
class AiVisibilityReport:
    """Everything the AI visibility panel shows, with its window and provenance."""

    site: str
    window_start: date
    window_end: date
    queries_analysed: int
    share_of_voice: float
    reported_share_of_voice: float | None
    mention_rate: float
    cited_urls: tuple[tuple[str, int], ...]
    query_coverage: float | None
    competitors: tuple[dict[str, Any], ...]
    winning_queries: tuple[str, ...] = ()
    lost_queries: tuple[str, ...] = ()
    evidence: EvidenceSet = field(default_factory=EvidenceSet)

    @property
    def is_sample(self) -> bool:
        return self.evidence.is_sample

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "site": self.site,
            "window": {"start": self.window_start.isoformat(), "end": self.window_end.isoformat()},
            "queries_analysed": self.queries_analysed,
            "share_of_voice": round(self.share_of_voice, 4),
            "reported_share_of_voice": self.reported_share_of_voice,
            "mention_rate": round(self.mention_rate, 4),
            "cited_urls": [{"url": u, "citations": c} for u, c in self.cited_urls],
            "query_coverage": None if self.query_coverage is None else round(self.query_coverage, 4),
            "competitors": list(self.competitors),
            "winning_queries": list(self.winning_queries),
            "lost_queries": list(self.lost_queries),
            "confidence": self.evidence.confidence.value,
            "is_sample": self.is_sample,
            "evidence": self.evidence.to_list(),
        }
        if self.is_sample:
            payload["warning"] = (
                "SAMPLE DATA — generated fixtures, not a Yandex Webmaster export. "
                "These figures must not be reported as measured AI visibility."
            )
        return payload


def build_report(
    snapshots: Sequence[AliceSnapshot],
    *,
    query_set: QuerySet | None = None,
    require_real_data: bool = False,
) -> AiVisibilityReport:
    """Aggregate weekly snapshots into one AI visibility report."""
    if not snapshots:
        raise InsufficientDataError("build_report() needs at least one snapshot")
    sites = {s.site for s in snapshots}
    if len(sites) != 1:
        raise ConfigurationError(f"snapshots belong to different sites: {sorted(sites)}")

    ordered = sorted(snapshots, key=lambda s: s.week_start)
    observations = [o for snapshot in ordered for o in snapshot.observations]
    if not observations:
        raise InsufficientDataError("snapshots contain no observations")

    evidence = EvidenceSet()
    for snapshot in ordered:
        evidence = evidence.merge(snapshot.evidence)

    if require_real_data and evidence.is_sample:
        raise SampleDataError(
            "AI visibility report was asked for real measurements but the snapshots are sample data"
        )

    latest = ordered[-1]
    winning: list[str] = []
    lost: list[str] = []
    if len(ordered) >= 2:
        try:
            winning = winning_queries(ordered[-2], latest)
            lost = lost_queries(ordered[-2], latest)
        except InsufficientDataError:
            winning, lost = [], []

    return AiVisibilityReport(
        site=latest.site,
        window_start=ordered[0].week_start,
        window_end=latest.week_start,
        queries_analysed=len({o.query for o in observations}),
        share_of_voice=share_of_voice(observations),
        reported_share_of_voice=latest.reported_share_of_voice,
        mention_rate=mention_rate(observations),
        cited_urls=tuple(cited_urls(observations)),
        query_coverage=query_coverage(observations, query_set) if query_set else None,
        competitors=tuple(competitor_overlap(observations)),
        winning_queries=tuple(winning),
        lost_queries=tuple(lost),
        evidence=evidence,
    )


def iter_observations(snapshots: Iterable[AliceSnapshot]) -> list[AliceObservation]:
    return [o for snapshot in snapshots for o in snapshot.observations]
