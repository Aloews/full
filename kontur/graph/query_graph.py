"""The QUERY -> SERP -> ALICE AI ANSWER -> SOURCES -> OUR URL graph.

    QUERY
      |-> YANDEX SERP        (our organic position at that moment)
      |-> ALICE AI ANSWER    (present? what shape?)
            |-> MENTIONS         (is our domain in the answer at all)
            |-> COMPETITOR SOURCES
            `-> OUR URL          (which page was cited)

Every edge is stamped with the date it was observed. Nothing in this graph is a
standing fact: the same query re-observed a week later is a *new* snapshot, and
the graph keeps both.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Iterable, Mapping

from kontur.core.errors import ConfigurationError, InsufficientDataError, MissingProvenanceError
from kontur.core.provenance import EvidenceSet, Provenance
from kontur.engines.geo.models import AliceObservation, AliceSnapshot, AnswerType, _norm_domain


@dataclass(frozen=True, slots=True)
class GraphObservation:
    """One dated observation of a query's answer surface."""

    query: str
    observed_on: date
    provenance: Provenance
    serp_position: int | None = None
    ai_answer_present: bool = False
    our_domain_mentioned: bool = False
    our_url_cited: str | None = None
    competitor_domains: tuple[str, ...] = ()
    answer_type: AnswerType = AnswerType.UNKNOWN

    def __post_init__(self) -> None:
        if not self.query or not self.query.strip():
            raise ConfigurationError("graph observation needs a query")
        if not isinstance(self.provenance, Provenance):
            raise MissingProvenanceError(
                f"graph observation for {self.query!r} has no provenance"
            )
        object.__setattr__(self, "query", " ".join(self.query.split()).lower())
        object.__setattr__(self, "answer_type", AnswerType(self.answer_type))
        object.__setattr__(
            self,
            "competitor_domains",
            tuple(dict.fromkeys(_norm_domain(d) for d in self.competitor_domains if d and d.strip())),
        )
        if isinstance(self.observed_on, datetime):
            object.__setattr__(self, "observed_on", self.observed_on.date())
        if not isinstance(self.observed_on, date):
            raise ConfigurationError("observed_on must be a date")
        if self.serp_position is not None and self.serp_position < 1:
            raise ConfigurationError("serp_position starts at 1")

    @classmethod
    def from_alice(
        cls,
        observation: AliceObservation,
        *,
        serp_position: int | None = None,
    ) -> "GraphObservation":
        return cls(
            query=observation.query,
            observed_on=observation.week_start,
            provenance=observation.provenance,
            serp_position=serp_position if serp_position is not None else observation.serp_position,
            ai_answer_present=observation.ai_answer_present,
            our_domain_mentioned=observation.our_domain_mentioned,
            our_url_cited=observation.our_url_cited,
            competitor_domains=observation.competitor_domains,
            answer_type=observation.answer_type,
        )

    @property
    def sources(self) -> tuple[str, ...]:
        domains = list(self.competitor_domains)
        if self.our_url_cited:
            domains.insert(0, _norm_domain(self.our_url_cited))
        return tuple(dict.fromkeys(domains))

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "date": self.observed_on.isoformat(),
            "serp_position": self.serp_position,
            "ai_answer_present": self.ai_answer_present,
            "our_domain_mentioned": self.our_domain_mentioned,
            "our_url_cited": self.our_url_cited,
            "competitor_domains": list(self.competitor_domains),
            "answer_type": self.answer_type.value,
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class GraphEdge:
    source: str
    target: str
    kind: str
    observed_on: date
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "kind": self.kind,
            "date": self.observed_on.isoformat(),
            "weight": self.weight,
        }


@dataclass
class QueryAnswerGraph:
    """Temporal graph of queries, answers and the URLs behind them."""

    site: str
    observations: list[GraphObservation] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.site = _norm_domain(self.site)
        if not self.site:
            raise ConfigurationError("QueryAnswerGraph needs a site")

    # ------------------------------------------------------------------ ingest
    def add(self, observation: GraphObservation) -> "QueryAnswerGraph":
        if not isinstance(observation, GraphObservation):
            raise ConfigurationError("QueryAnswerGraph stores GraphObservation objects")
        self.observations = [
            o for o in self.observations
            if not (o.query == observation.query and o.observed_on == observation.observed_on)
        ]
        self.observations.append(observation)
        self.observations.sort(key=lambda o: (o.query, o.observed_on))
        return self

    def ingest_snapshot(
        self, snapshot: AliceSnapshot, *, serp_positions: Mapping[str, int] | None = None
    ) -> "QueryAnswerGraph":
        positions = {k.lower(): v for k, v in (serp_positions or {}).items()}
        for observation in snapshot.observations:
            self.add(
                GraphObservation.from_alice(
                    observation, serp_position=positions.get(observation.query)
                )
            )
        return self

    # ------------------------------------------------------------------ reads
    @property
    def queries(self) -> tuple[str, ...]:
        return tuple(sorted({o.query for o in self.observations}))

    @property
    def evidence(self) -> EvidenceSet:
        return EvidenceSet.of(*(o.provenance for o in self.observations))

    @property
    def is_sample(self) -> bool:
        return self.evidence.is_sample

    def timeline(self, query: str) -> tuple[GraphObservation, ...]:
        needle = " ".join(query.split()).lower()
        found = tuple(
            sorted((o for o in self.observations if o.query == needle), key=lambda o: o.observed_on)
        )
        if not found:
            raise InsufficientDataError(f"no observations of {query!r}")
        return found

    def sources_for(self, query: str) -> list[tuple[str, int]]:
        """Domains cited for this query, most frequent first."""
        counter: Counter[str] = Counter()
        for observation in self.timeline(query):
            counter.update(observation.sources)
        return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))

    def our_urls_for(self, query: str) -> list[tuple[str, int]]:
        counter = Counter(o.our_url_cited for o in self.timeline(query) if o.our_url_cited)
        return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))

    def competitors(self, *, limit: int = 20) -> list[tuple[str, int]]:
        counter: Counter[str] = Counter()
        for observation in self.observations:
            counter.update(observation.competitor_domains)
        return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]

    def citation_path(self, query: str) -> list[dict[str, Any]]:
        """The QUERY -> ANSWER -> URL chain for each observation of a query."""
        path: list[dict[str, Any]] = []
        for observation in self.timeline(query):
            path.append(
                {
                    "date": observation.observed_on.isoformat(),
                    "serp_position": observation.serp_position,
                    "ai_answer": observation.answer_type.value if observation.ai_answer_present else None,
                    "mentioned": observation.our_domain_mentioned,
                    "cited_url": observation.our_url_cited,
                    "competitors": list(observation.competitor_domains),
                }
            )
        return path

    # ------------------------------------------------------------------ export
    def nodes(self) -> list[dict[str, Any]]:
        nodes: dict[str, dict[str, Any]] = {}

        def put(node_id: str, kind: str, **attrs: Any) -> None:
            nodes.setdefault(node_id, {"id": node_id, "kind": kind, **attrs})

        for observation in self.observations:
            put(f"query:{observation.query}", "query", label=observation.query)
            answer_id = f"answer:{observation.query}@{observation.observed_on.isoformat()}"
            put(
                answer_id,
                "ai_answer",
                date=observation.observed_on.isoformat(),
                present=observation.ai_answer_present,
                answer_type=observation.answer_type.value,
            )
            if observation.our_url_cited:
                put(f"url:{observation.our_url_cited}", "our_url", label=observation.our_url_cited)
            for domain in observation.competitor_domains:
                put(f"domain:{domain}", "competitor", label=domain)
        return sorted(nodes.values(), key=lambda n: n["id"])

    def edges(self) -> list[GraphEdge]:
        edges: list[GraphEdge] = []
        for observation in self.observations:
            query_id = f"query:{observation.query}"
            answer_id = f"answer:{observation.query}@{observation.observed_on.isoformat()}"
            edges.append(GraphEdge(query_id, answer_id, "answered_by", observation.observed_on))
            if observation.our_url_cited:
                edges.append(
                    GraphEdge(answer_id, f"url:{observation.our_url_cited}", "cites", observation.observed_on)
                )
            for domain in observation.competitor_domains:
                edges.append(
                    GraphEdge(answer_id, f"domain:{domain}", "cites_competitor", observation.observed_on)
                )
            if observation.serp_position is not None:
                edges.append(
                    GraphEdge(
                        query_id,
                        f"url:{observation.our_url_cited}" if observation.our_url_cited else f"site:{self.site}",
                        "ranks",
                        observation.observed_on,
                        weight=float(observation.serp_position),
                    )
                )
        return edges

    def to_dict(self) -> dict[str, Any]:
        return {
            "site": self.site,
            "queries": len(self.queries),
            "observations": len(self.observations),
            "nodes": self.nodes(),
            "edges": [e.to_dict() for e in self.edges()],
            "is_sample": self.is_sample,
            "caveat": (
                "Each edge is one dated observation. Alice AI answers and their source "
                "sets vary over time; compare snapshots, never single captures."
            ),
        }


def build_graph(
    site: str,
    snapshots: Iterable[AliceSnapshot],
    *,
    serp_positions: Mapping[str, int] | None = None,
) -> QueryAnswerGraph:
    graph = QueryAnswerGraph(site=site)
    for snapshot in snapshots:
        graph.ingest_snapshot(snapshot, serp_positions=serp_positions)
    return graph
