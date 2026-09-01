"""The faceted indexation pipeline.

    QUERY -> FILTER STATE -> SEARCH DEMAND -> INTENT -> SERP/COMPETITOR EVIDENCE
          -> CONTENT UNIQUENESS -> BUSINESS VALUE -> INDEXATION DECISION

Each stage writes into the context and appends to the audit trail; the decision
stage runs the rule chain. The result is a single explainable verdict per URL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from kontur.core.decisions import Decision, DecisionRecord
from kontur.core.errors import ConfigurationError
from kontur.core.urls import parse_url
from kontur.engines.faceted.context import FacetContext
from kontur.engines.faceted.models import (
    DEFAULT_FACET_CONFIG,
    FacetCatalog,
    FacetConfig,
    FilterState,
    detect_pagination,
)
from kontur.engines.faceted.providers import (
    BusinessValueProvider,
    DemandProvider,
    InventoryProvider,
    IntentProvider,
    LabelQueryResolver,
    QueryResolver,
    SerpProvider,
)
from kontur.engines.faceted.rules import RULE_CHAIN
from kontur.engines.faceted.signals import content_uniqueness_score
from kontur.engines.getparams.catalog import PAGINATION_PARAMS
from kontur.engines.getparams.controller import GetParameterController
from kontur.engines.getparams.models import ParamDecision

STAGES: tuple[str, ...] = (
    "query",
    "filter_state",
    "search_demand",
    "intent",
    "serp_evidence",
    "content_uniqueness",
    "business_value",
    "indexation_decision",
)


@dataclass
class FacetedIndexationEngine:
    """Decides what happens to every faceted URL, and says why."""

    catalog: FacetCatalog
    parameters: GetParameterController | None = None
    config: FacetConfig = DEFAULT_FACET_CONFIG
    query_resolver: QueryResolver = field(default_factory=LabelQueryResolver)
    demand: DemandProvider | None = None
    intent: IntentProvider | None = None
    serp: SerpProvider | None = None
    inventory: InventoryProvider | None = None
    business: BusinessValueProvider | None = None
    pagination_params: frozenset[str] = PAGINATION_PARAMS

    def __post_init__(self) -> None:
        if not isinstance(self.catalog, FacetCatalog):
            raise ConfigurationError("FacetedIndexationEngine needs a FacetCatalog")

    # ---------------------------------------------------------------- stages
    def _param_decisions(self, names: Iterable[str]) -> dict[str, ParamDecision]:
        if self.parameters is None:
            return {}
        return {name: self.parameters.decision(name) for name in names}

    def build_context(self, url: str) -> FacetContext:
        parsed = parse_url(url)
        state, others = FilterState.from_url(url, self.catalog)
        pagination = detect_pagination(parsed.params, self.pagination_params)
        if pagination is not None:
            others = tuple((k, v) for k, v in others if k != pagination.parameter)

        ctx = FacetContext(
            url=url,
            state=state,
            catalog=self.catalog,
            config=self.config,
            other_params=others,
            pagination=pagination,
        )

        # Stage 1 — QUERY
        query = self.query_resolver.query_for(state)
        ctx.record("query", f"target query: {query!r}" if query else "no facet-derived query", query=query)

        # Stage 2 — FILTER STATE
        ctx.param_decisions = self._param_decisions(ctx.url_param_names)
        ctx.record(
            "filter_state",
            f"depth {state.depth}: {state.selections}",
            state=state.to_dict(),
            other_parameters=[list(p) for p in others],
            parameter_decisions={k: v.value for k, v in ctx.param_decisions.items()},
        )

        # Stage 3 — SEARCH DEMAND
        demand = self.demand.demand_for(state) if self.demand else None
        ctx.demand = demand
        ctx.add_evidence(demand)
        ctx.record(
            "search_demand",
            (
                f"{demand.value.monthly_volume:.0f}/month from {demand.provenance.source}"
                if demand
                else "no demand data"
            ),
            monthly_volume=demand.value.monthly_volume if demand else None,
        )

        # Stage 4 — INTENT
        ctx.intent = self.intent.intent_for(state) if self.intent else None
        ctx.record(
            "intent",
            (
                f"{ctx.intent.label} intent, overlap {ctx.intent.overlap_with_parent:.2f}"
                if ctx.intent
                else "no intent assessment"
            ),
            intent=ctx.intent.to_dict() if ctx.intent else None,
        )

        # Stage 5 — SERP / COMPETITOR EVIDENCE
        ctx.serp = self.serp.evidence_for(state) if self.serp else None
        if ctx.serp is not None:
            ctx.evidence = ctx.evidence.merge(ctx.serp.evidence)
        ctx.record(
            "serp_evidence",
            (
                f"{ctx.serp.dedicated_pages}/{ctx.serp.competitors_analysed} dedicated competitor pages"
                if ctx.serp
                else "no SERP capture"
            ),
            serp=ctx.serp.to_dict() if ctx.serp else None,
        )

        # Stage 6 — CONTENT UNIQUENESS
        inventory = self.inventory.inventory_for(state) if self.inventory else None
        ctx.inventory = inventory
        ctx.add_evidence(inventory)
        if inventory is not None:
            value = inventory.value
            uniqueness = content_uniqueness_score(
                unique_items=value.unique_items_vs_parent,
                total_items=value.total_items,
                editorial_blocks=value.editorial_blocks,
            )
            ctx.record(
                "content_uniqueness",
                f"{value.total_items} items, uniqueness {uniqueness:.2f}",
                items=value.total_items,
                uniqueness=uniqueness,
                pages=value.pages,
            )
        else:
            ctx.record("content_uniqueness", "no inventory data")

        # Stage 7 — BUSINESS VALUE
        business = self.business.value_for(state) if self.business else None
        ctx.business = business
        ctx.add_evidence(business)
        ctx.record(
            "business_value",
            f"score {business.value.score:.2f}" if business else "no business data",
            business_value=business.value.score if business else None,
        )
        return ctx

    # -------------------------------------------------------------- decision
    def decide(self, url: str) -> DecisionRecord:
        ctx = self.build_context(url)
        for rule in RULE_CHAIN:
            verdict = rule(ctx)
            if verdict is not None:
                return verdict
        raise ConfigurationError(  # pragma: no cover - the chain ends with a total rule
            f"no rule produced a decision for {url}; the rule chain must be total"
        )

    def decide_many(self, urls: Sequence[str]) -> list[DecisionRecord]:
        return [self.decide(url) for url in urls]


def decision_summary(records: Iterable[DecisionRecord]) -> dict[str, Any]:
    """Counts per verdict plus the indexable set, for the dashboard."""
    records = list(records)
    counts: dict[str, int] = {d.value: 0 for d in Decision}
    for record in records:
        counts[record.decision.value] += 1
    return {
        "total": len(records),
        "by_decision": counts,
        "indexable": sorted(r.url for r in records if r.decision is Decision.INDEX),
        "contains_sample_data": any(r.is_sample for r in records),
    }
