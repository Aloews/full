"""The indexation rules for faceted navigation.

Each rule is a small pure function over :class:`FacetContext` returning a
:class:`~kontur.core.decisions.DecisionRecord` when it fires and ``None`` when
it does not. :data:`RULE_CHAIN` is the evaluation order: the first rule that
fires decides, which is what keeps the outcome explainable — the audit trail
shows exactly which rule stopped the URL and why.
"""

from __future__ import annotations

from collections.abc import Callable

from kontur.core.decisions import Decision, DecisionRecord, ReasonCode
from kontur.core.registry import rule_ids
from kontur.core.urls import strip_params
from kontur.engines.faceted.context import FacetContext
from kontur.engines.faceted.models import FacetStatus
from kontur.engines.faceted.signals import content_uniqueness_score
from kontur.engines.getparams.models import ParamDecision

Rule = Callable[[FacetContext], DecisionRecord | None]


def _record(ctx: FacetContext, decision: Decision, reasons, rule_id: str, **kwargs) -> DecisionRecord:
    return DecisionRecord(
        url=ctx.url,
        decision=decision,
        reasons=tuple(reasons),
        rule_ids=rule_ids(rule_id),
        evidence=ctx.evidence,
        trace=tuple(ctx.trace),
        **kwargs,
    )


def rule_blocked_parameter(ctx: FacetContext) -> DecisionRecord | None:
    """FACET-011 — a parameter marked BLOCK turns the URL into a crawl trap."""
    blocked = [n for n in ctx.url_param_names if ctx.param_decisions.get(n) is ParamDecision.BLOCK]
    if not blocked:
        return None
    ctx.record("indexation_decision", f"blocked parameters present: {blocked}", parameters=blocked)
    return _record(ctx, Decision.BLOCK, (ReasonCode.BLOCKED_PARAMETER,), "FACET-011")


def rule_excluded_parameters(ctx: FacetContext) -> DecisionRecord | None:
    """FACET-001 — tracking/excluded parameters canonicalise to the clean URL."""
    excluded = [
        n for n in ctx.url_param_names if ctx.param_decisions.get(n) is ParamDecision.EXCLUDE
    ]
    if not excluded:
        return None
    target = strip_params(ctx.url, excluded)
    reasons = [ReasonCode.EXCLUDED_PARAMETER]
    if any(n.startswith("utm_") or n in {"yclid", "ysclid", "gclid", "fbclid"} for n in excluded):
        reasons.insert(0, ReasonCode.TRACKING_PARAMETER)
    ctx.record("indexation_decision", f"excluded parameters present: {excluded}", parameters=excluded)
    return _record(
        ctx, Decision.CANONICAL, reasons, "FACET-001", canonical_target=target
    )


def rule_deprecated_facet(ctx: FacetContext) -> DecisionRecord | None:
    """FACET-009 — a renamed facet keeps its equity through a redirect."""
    for name, value in ctx.state.selections:
        if not ctx.catalog.has(name):
            continue
        facet = ctx.catalog.get(name)
        if facet.status is FacetStatus.DEPRECATED and facet.replacement:
            replaced = ctx.state.without(name)
            selections = tuple(sorted((*replaced.selections, (facet.replacement, value))))
            target = type(ctx.state)(ctx.state.path, selections).to_url()
            ctx.record("indexation_decision", f"facet {name} is deprecated", replacement=facet.replacement)
            return _record(
                ctx, Decision.REDIRECT, (ReasonCode.DEPRECATED_FACET,), "FACET-009",
                redirect_target=target,
            )
    return None


def rule_pagination(ctx: FacetContext) -> DecisionRecord | None:
    """FACET-010 — page=1 duplicates the base URL; deeper pages may stand alone."""
    if ctx.pagination is None:
        return None
    if ctx.pagination.is_first_page:
        target = strip_params(ctx.url, [ctx.pagination.parameter])
        ctx.record("indexation_decision", "first page duplicates the base URL")
        return _record(
            ctx, Decision.CANONICAL, (ReasonCode.PAGINATION_FIRST_PAGE,), "FACET-010",
            canonical_target=target,
        )

    inventory = ctx.inventory_value
    pages = inventory.pages if inventory else 1
    if pages >= ctx.config.min_pages_for_deep_pagination:
        ctx.record("indexation_decision", f"page {ctx.pagination.page} of {pages}", pages=pages)
        return _record(
            ctx, Decision.INDEX,
            (ReasonCode.PAGINATION_DEEP_SET, ReasonCode.SUFFICIENT_INVENTORY),
            "FACET-010",
        )

    target = strip_params(ctx.url, [ctx.pagination.parameter])
    ctx.record("indexation_decision", "paginated URL without a deep result set", pages=pages)
    return _record(
        ctx, Decision.CANONICAL, (ReasonCode.PAGINATION_FIRST_PAGE,), "FACET-010",
        canonical_target=target,
    )


def rule_facet_depth(ctx: FacetContext) -> DecisionRecord | None:
    """FACET-002 — combinations deeper than the budget are not indexable."""
    limit = min(ctx.config.max_depth, ctx.catalog.max_depth)
    if ctx.state.depth <= limit:
        return None
    ctx.record(
        "indexation_decision",
        f"facet depth {ctx.state.depth} exceeds limit {limit}",
        depth=ctx.state.depth,
        limit=limit,
    )
    return _record(ctx, Decision.NOINDEX, (ReasonCode.FACET_DEPTH_EXCEEDED,), "FACET-002")


def rule_empty_inventory(ctx: FacetContext) -> DecisionRecord | None:
    """FACET-003 — an empty or thin filter state answers no query."""
    inventory = ctx.inventory_value
    if inventory is None:
        return None
    if inventory.total_items == 0:
        ctx.record("indexation_decision", "filter state returns no items")
        return _record(ctx, Decision.NOINDEX, (ReasonCode.EMPTY_RESULT_SET,), "FACET-003")
    if inventory.total_items < ctx.config.min_items:
        ctx.record(
            "indexation_decision",
            f"only {inventory.total_items} items (minimum {ctx.config.min_items})",
            items=inventory.total_items,
        )
        return _record(ctx, Decision.NOINDEX, (ReasonCode.THIN_CONTENT,), "FACET-003")
    return None


def rule_pending_analysis(ctx: FacetContext) -> DecisionRecord | None:
    """FACET-012 — a facet still under review is held, never indexed."""
    pending = [
        n for n in ctx.url_param_names if ctx.param_decisions.get(n) is ParamDecision.ANALYZE
    ]
    if not pending:
        return None
    ctx.record("indexation_decision", f"parameters awaiting analysis: {pending}", parameters=pending)
    return _record(
        ctx, Decision.CANONICAL, (ReasonCode.AWAITING_ANALYSIS,), "FACET-012",
        canonical_target=strip_params(ctx.url, pending),
    )


def rule_missing_demand_data(ctx: FacetContext) -> DecisionRecord | None:
    """FACET-005 — absence of demand data is not evidence of demand."""
    if ctx.demand is not None:
        return None
    ctx.record("indexation_decision", "no demand export covers this filter state")
    return _record(
        ctx, Decision.CANONICAL, (ReasonCode.DEMAND_DATA_MISSING,), "FACET-005",
        canonical_target=ctx.state.parent().to_url(),
    )


def rule_no_demand(ctx: FacetContext) -> DecisionRecord | None:
    """FACET-004 — measured demand below the threshold means no separate document."""
    demand = ctx.demand_value
    if demand is None:
        return None
    if demand.monthly_volume >= ctx.config.min_monthly_demand:
        return None
    ctx.record(
        "indexation_decision",
        f"demand {demand.monthly_volume:.0f}/month below {ctx.config.min_monthly_demand:.0f}",
        monthly_volume=demand.monthly_volume,
    )
    return _record(
        ctx, Decision.CANONICAL, (ReasonCode.NO_SEARCH_DEMAND,), "FACET-004",
        canonical_target=ctx.state.parent().to_url(),
    )


def rule_duplicate_of_parent(ctx: FacetContext) -> DecisionRecord | None:
    """FACET-006 — a near-copy of the parent competes with it instead of adding to it."""
    inventory = ctx.inventory_value
    reasons: list[ReasonCode] = []

    if ctx.intent is not None and not ctx.intent.is_distinct:
        reasons.append(ReasonCode.DUPLICATE_INTENT)

    if inventory is not None:
        uniqueness = content_uniqueness_score(
            unique_items=inventory.unique_items_vs_parent,
            total_items=inventory.total_items,
            editorial_blocks=inventory.editorial_blocks,
        )
        if uniqueness < ctx.config.min_uniqueness:
            reasons.append(ReasonCode.DUPLICATE_CONTENT)
            ctx.record(
                "content_uniqueness",
                f"uniqueness {uniqueness:.2f} below {ctx.config.min_uniqueness:.2f}",
                uniqueness=uniqueness,
            )

    if not reasons:
        return None
    return _record(
        ctx, Decision.CANONICAL, reasons, "FACET-006",
        canonical_target=ctx.state.parent().to_url(),
    )


def rule_low_business_value(ctx: FacetContext) -> DecisionRecord | None:
    """FACET-008 — weak demand plus no commercial worth does not earn crawl budget."""
    business = ctx.business_value
    demand = ctx.demand_value
    if business is None or demand is None:
        return None
    value = business.score
    if value >= ctx.config.min_business_value:
        return None
    strong_demand = ctx.config.min_monthly_demand * ctx.config.weak_demand_multiplier
    if demand.monthly_volume >= strong_demand:
        return None
    ctx.record(
        "business_value",
        f"business value {value:.2f} below {ctx.config.min_business_value:.2f} with demand "
        f"{demand.monthly_volume:.0f}/month under the {strong_demand:.0f} strong-demand mark",
        business_value=value,
        strong_demand_threshold=strong_demand,
    )
    return _record(ctx, Decision.NOINDEX, (ReasonCode.LOW_BUSINESS_VALUE,), "FACET-008")


def rule_index_when_all_signals_present(ctx: FacetContext) -> DecisionRecord | None:
    """FACET-007 — INDEX needs demand + unique intent + unique content + business value.

    When a signal is missing the URL canonicalises to its parent and the missing
    signal is named in the reasons, so nothing is ever rejected silently.
    """
    reasons: list[ReasonCode] = []
    missing: list[ReasonCode] = []

    demand = ctx.demand_value
    if demand is not None and demand.monthly_volume >= ctx.config.min_monthly_demand:
        reasons.append(ReasonCode.SEARCH_DEMAND)
    else:
        missing.append(ReasonCode.NO_SEARCH_DEMAND)

    if ctx.intent is not None and ctx.intent.is_distinct:
        reasons.append(ReasonCode.UNIQUE_INTENT)
    else:
        missing.append(ReasonCode.DUPLICATE_INTENT)

    inventory = ctx.inventory_value
    if inventory is not None:
        uniqueness = content_uniqueness_score(
            unique_items=inventory.unique_items_vs_parent,
            total_items=inventory.total_items,
            editorial_blocks=inventory.editorial_blocks,
        )
        if uniqueness >= ctx.config.min_uniqueness:
            reasons.append(ReasonCode.UNIQUE_CONTENT)
        else:
            missing.append(ReasonCode.DUPLICATE_CONTENT)
    else:
        missing.append(ReasonCode.DUPLICATE_CONTENT)

    business = ctx.business_value
    if business is not None and business.score >= ctx.config.min_business_value:
        reasons.append(ReasonCode.COMMERCIAL_VALUE)
    else:
        missing.append(ReasonCode.LOW_BUSINESS_VALUE)

    if ctx.config.require_serp_evidence:
        if ctx.serp is not None and ctx.serp.has_dedicated_pages:
            reasons.append(ReasonCode.COMPETITOR_EVIDENCE)
        else:
            missing.append(ReasonCode.NO_COMPETITOR_EVIDENCE)
    elif ctx.serp is not None and ctx.serp.has_dedicated_pages:
        reasons.append(ReasonCode.COMPETITOR_EVIDENCE)

    if missing:
        ctx.record("indexation_decision", "not every INDEX signal is present", missing=[m.value for m in missing])
        return _record(
            ctx, Decision.CANONICAL, missing, "FACET-007",
            canonical_target=ctx.state.parent().to_url(),
        )

    ctx.record("indexation_decision", "all INDEX signals present", signals=[r.value for r in reasons])
    return _record(ctx, Decision.INDEX, reasons, "FACET-007")


#: Evaluation order. Hard technical facts first, then demand, then quality.
RULE_CHAIN: tuple[Rule, ...] = (
    rule_blocked_parameter,
    rule_excluded_parameters,
    rule_deprecated_facet,
    rule_pagination,
    rule_facet_depth,
    rule_empty_inventory,
    rule_pending_analysis,
    rule_missing_demand_data,
    rule_no_demand,
    rule_duplicate_of_parent,
    rule_low_business_value,
    rule_index_when_all_signals_present,
)
