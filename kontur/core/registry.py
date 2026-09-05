"""The single source of truth for rules and scoring functions.

Meta-tests read this registry to answer questions like "does every critical
rule have a negative test?". Engines reference rule ids from here so a rule can
never fire under an id that nobody is allowed to test.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from kontur.core.errors import ConfigurationError, UnknownRuleError


class Criticality(StrEnum):
    CRITICAL = "critical"
    STANDARD = "standard"


class RuleKind(StrEnum):
    INDEXATION = "indexation"
    SEO = "seo"
    AEO = "aeo"
    GEO = "geo"
    EXPERIMENT = "experiment"
    LINKS = "links"
    BEHAVIOR = "behavior"
    DATA_INTEGRITY = "data_integrity"
    SECURITY = "security"


#: Rule kinds that count as "SEO rules" for the regression-test requirement.
SEO_RULE_KINDS: frozenset[RuleKind] = frozenset({RuleKind.SEO, RuleKind.INDEXATION})


@dataclass(frozen=True, slots=True)
class Rule:
    id: str
    title: str
    kind: RuleKind
    criticality: Criticality
    module: str
    rationale: str

    @property
    def is_critical(self) -> bool:
        return self.criticality is Criticality.CRITICAL

    @property
    def requires_regression_test(self) -> bool:
        return self.is_critical and self.kind in SEO_RULE_KINDS


def _rules(*rules: Rule) -> dict[str, Rule]:
    out: dict[str, Rule] = {}
    for rule in rules:
        if rule.id in out:
            raise ConfigurationError(f"duplicate rule id {rule.id}")
        out[rule.id] = rule
    return out


C = Criticality.CRITICAL
S = Criticality.STANDARD

RULES: dict[str, Rule] = _rules(
    # ------------------------------------------------------------------ GET parameters
    Rule("GETP-001", "Tracking parameters are always excluded from indexing",
         RuleKind.INDEXATION, C, "kontur.engines.getparams.classifier",
         "utm_*, gclid, yclid and friends create duplicates and burn crawl budget."),
    Rule("GETP-002", "Conflicting parameter policies resolve to the most restrictive one",
         RuleKind.INDEXATION, C, "kontur.engines.getparams.controller",
         "Yandex applies the more prohibitive variant when directives conflict."),
    Rule("GETP-003", "An unknown parameter defaults to ANALYZE, never to indexable",
         RuleKind.INDEXATION, C, "kontur.engines.getparams.classifier",
         "Unclassified parameters must not silently open new indexable space."),
    Rule("GETP-004", "Sort-style parameters are excluded as duplicate intent",
         RuleKind.INDEXATION, S, "kontur.engines.getparams.classifier",
         "Re-ordering the same inventory does not create a new document."),
    Rule("GETP-005", "Pagination parameters are context dependent",
         RuleKind.INDEXATION, S, "kontur.engines.getparams.classifier",
         "page=1 duplicates the base URL; deeper pages may deserve indexing."),
    Rule("GETP-006", "Promotion to SEO_HUB requires sourced search demand",
         RuleKind.INDEXATION, C, "kontur.engines.getparams.classifier",
         "A facet becomes a landing page because of measured demand, not taste."),
    Rule("GETP-007", "Session/identifier parameters are blocked from crawling",
         RuleKind.INDEXATION, S, "kontur.engines.getparams.classifier",
         "Unbounded identifier space is a crawl trap."),
    Rule("GETP-008", "Parameter export is deterministic and round-trips",
         RuleKind.INDEXATION, S, "kontur.engines.getparams.export",
         "A directive file that changes between runs cannot be reviewed."),
    # ------------------------------------------------------------------ Faceted navigation
    Rule("FACET-001", "URLs carrying excluded parameters canonicalise to the clean URL",
         RuleKind.SEO, C, "kontur.engines.faceted.rules",
         "Tracking state must never fragment a document's signals."),
    Rule("FACET-002", "Facet combinations deeper than the configured limit are noindexed",
         RuleKind.SEO, C, "kontur.engines.faceted.rules",
         "Combinatorial explosion starves the crawler of useful URLs."),
    Rule("FACET-003", "Empty or thin filter states are noindexed",
         RuleKind.SEO, C, "kontur.engines.faceted.rules",
         "A page with no inventory answers no query."),
    Rule("FACET-004", "Filter states without measured demand canonicalise to the parent",
         RuleKind.SEO, C, "kontur.engines.faceted.rules",
         "Demand is the entry ticket to the indexable graph."),
    Rule("FACET-005", "Missing demand data yields the conservative verdict, not INDEX",
         RuleKind.SEO, C, "kontur.engines.faceted.rules",
         "Absence of data is not evidence of demand."),
    Rule("FACET-006", "Filter states whose content duplicates the parent canonicalise",
         RuleKind.SEO, C, "kontur.engines.faceted.rules",
         "Near-identical documents compete with each other."),
    Rule("FACET-007", "INDEX requires demand + unique intent + unique content + business value",
         RuleKind.SEO, C, "kontur.engines.faceted.rules",
         "All four signals together are what makes a hub worth crawling."),
    Rule("FACET-008", "Filter states without business value and with weak demand are noindexed",
         RuleKind.SEO, S, "kontur.engines.faceted.rules",
         "Indexable space costs crawl budget; it must earn it."),
    Rule("FACET-009", "Deprecated facets redirect to their replacement",
         RuleKind.SEO, S, "kontur.engines.faceted.rules",
         "Renamed taxonomy keeps its equity through 301s."),
    Rule("FACET-010", "page=1 canonicalises to the base URL; deeper pages may self-canonicalise",
         RuleKind.SEO, C, "kontur.engines.faceted.rules",
         "Pagination is context dependent, not uniformly excluded."),
    Rule("FACET-011", "Blocked parameters produce a BLOCK verdict",
         RuleKind.SEO, S, "kontur.engines.faceted.rules",
         "Crawl traps are cut off before they are indexed."),
    Rule("FACET-012", "Facets still awaiting analysis never receive INDEX",
         RuleKind.SEO, C, "kontur.engines.faceted.rules",
         "ANALYZE is a hold, and a hold must be safe by default."),
    # ------------------------------------------------------------------ AEO
    Rule("AEO-001", "An answer-first block must exist and be extractable",
         RuleKind.AEO, C, "kontur.engines.aeo.answer",
         "Assistants lift a direct answer or they lift nothing."),
    Rule("AEO-002", "Answer length buckets are editorial hypotheses, not ranking factors",
         RuleKind.AEO, C, "kontur.engines.aeo.buckets",
         "20-40 / 40-60 / 60-100 are arms of an experiment, not a law."),
    Rule("AEO-003", "Extraction readiness requires structured evidence",
         RuleKind.AEO, S, "kontur.engines.aeo.extraction",
         "Lists, tables, FAQ blocks and definitions are what gets quoted."),
    Rule("AEO-004", "No effect claim without a linked experiment result",
         RuleKind.AEO, C, "kontur.core.claims",
         "A percentage uplift with no experiment behind it is a sales sentence, "
         "not a measurement."),
    # ------------------------------------------------------------------ GEO / Alice AI
    Rule("GEO-001", "AI visibility metrics require provenance on every input row",
         RuleKind.GEO, C, "kontur.engines.geo.metrics",
         "Source + retrieval date + confidence or the number does not exist."),
    Rule("GEO-002", "Sample data can never be presented as measured AI visibility",
         RuleKind.GEO, C, "kontur.engines.geo.metrics",
         "Demo fixtures must be visibly marked end to end."),
    Rule("GEO-003", "A single snapshot is not evidence of an AI visibility change",
         RuleKind.GEO, C, "kontur.engines.geo.snapshots",
         "Alice can return a different answer and source set for the same query."),
    Rule("GEO-004", "Share of Voice is computed only over queries present in the export",
         RuleKind.GEO, S, "kontur.engines.geo.metrics",
         "Extrapolating beyond the export invents visibility."),
    Rule("GEO-005", "Winning/lost queries need two comparable snapshots",
         RuleKind.GEO, S, "kontur.engines.geo.metrics",
         "A delta needs a before and an after over the same window."),
    # ------------------------------------------------------------------ Experiments
    Rule("EXP-001", "A decision requires the pre-registered minimum sample",
         RuleKind.EXPERIMENT, C, "kontur.engines.experiment.decision",
         "Peeking at an underpowered test manufactures effects."),
    Rule("EXP-002", "A breached guardrail forces REJECT regardless of the primary metric",
         RuleKind.EXPERIMENT, C, "kontur.engines.experiment.decision",
         "A win that breaks indexation or revenue is not a win."),
    Rule("EXP-003", "Multiple comparisons are corrected before a verdict",
         RuleKind.EXPERIMENT, S, "kontur.engines.experiment.stats",
         "Twenty metrics produce one 'significant' result by luck."),
    Rule("EXP-004", "Arm assignment is deterministic and reproducible",
         RuleKind.EXPERIMENT, C, "kontur.engines.experiment.design",
         "A re-run that reshuffles arms destroys the comparison."),
    # ------------------------------------------------------------------ Links
    Rule("LINK-001", "The backlink module classifies risk and never builds networks",
         RuleKind.LINKS, C, "kontur.engines.backlinks.risk",
         "This is an analysis platform, not a spam automation tool."),
    Rule("LINK-002", "Commercial anchor concentration raises risk",
         RuleKind.LINKS, S, "kontur.engines.backlinks.risk",
         "A money-anchor spike is the classic manipulation footprint."),
    Rule("LINK-003", "Link velocity spikes raise risk",
         RuleKind.LINKS, S, "kontur.engines.backlinks.risk",
         "Unnatural acquisition curves are detectable and penalised."),
    # ------------------------------------------------------------------ Behaviour
    Rule("BEH-001", "Behavioural output is labelled correlational, never causal",
         RuleKind.BEHAVIOR, C, "kontur.engines.behavior.correlation",
         "Time on page is an observation about users, not a documented input to "
         "how any search engine ranks."),
    Rule("BEH-002", "Correlation requires a minimum sample before it is reported",
         RuleKind.BEHAVIOR, S, "kontur.engines.behavior.correlation",
         "Five sessions produce a beautiful, meaningless r."),
    # ------------------------------------------------------------------ Data integrity
    Rule("DATA-001", "An external fact without provenance is rejected at the boundary",
         RuleKind.DATA_INTEGRITY, C, "kontur.core.provenance",
         "The ingest layer is where fabrication is stopped."),
    Rule("DATA-002", "Sample provenance propagates to every derived report",
         RuleKind.DATA_INTEGRITY, C, "kontur.core.provenance",
         "Marks must survive aggregation, or they are decoration."),
    # ------------------------------------------------------------------ Security
    Rule("SEC-001", "Untrusted strings are escaped before they reach the dashboard",
         RuleKind.SECURITY, C, "kontur.dashboard.render",
         "Crawled URLs and query text are attacker-controlled input."),
    Rule("SEC-002", "Credentials never appear in exports, reports or logs",
         RuleKind.SECURITY, C, "kontur.core.redaction",
         "Exports get pasted into tickets and chats."),
    Rule("SEC-003", "Ingested identifiers are length-bounded and normalised",
         RuleKind.SECURITY, S, "kontur.ingest.validation",
         "Unbounded input is a denial-of-service and a storage bug."),
)


@dataclass(frozen=True, slots=True)
class ScoringFunction:
    """A bounded numeric function that must be tested at its edges (MT-010)."""

    name: str
    dotted_path: str
    lower: float
    upper: float
    description: str


SCORING_FUNCTIONS: dict[str, ScoringFunction] = {
    fn.name: fn
    for fn in (
        ScoringFunction("demand_score", "kontur.engines.faceted.signals.demand_score",
                        0.0, 1.0, "Normalised search demand for a filter state."),
        ScoringFunction("content_uniqueness_score",
                        "kontur.engines.faceted.signals.content_uniqueness_score",
                        0.0, 1.0, "How different a filter state is from its parent."),
        ScoringFunction("business_value_score",
                        "kontur.engines.faceted.signals.business_value_score",
                        0.0, 1.0, "Commercial worth of a filter state."),
        ScoringFunction("information_gain_score",
                        "kontur.engines.serp.evidence.information_gain_score",
                        0.0, 1.0, "What our page adds over the SERP consensus."),
        ScoringFunction("extraction_readiness_score",
                        "kontur.engines.aeo.extraction.extraction_readiness_score",
                        0.0, 1.0, "How liftable a page is for an assistant answer."),
        ScoringFunction("share_of_voice", "kontur.engines.geo.metrics.share_of_voice",
                        0.0, 1.0, "Our share of Alice AI citations in a query set."),
        ScoringFunction("answer_volatility", "kontur.engines.geo.snapshots.answer_volatility",
                        0.0, 1.0, "How much Alice's source set moves between snapshots."),
        ScoringFunction("backlink_risk_score", "kontur.engines.backlinks.risk.backlink_risk_score",
                        0.0, 1.0, "Aggregated manipulation-footprint risk."),
    )
}


def get_rule(rule_id: str) -> Rule:
    try:
        return RULES[rule_id]
    except KeyError as exc:
        raise UnknownRuleError(f"unknown rule id {rule_id!r}") from exc


def rule_ids(*ids: str) -> tuple[str, ...]:
    """Validate rule ids at call sites so typos fail fast."""
    for rid in ids:
        get_rule(rid)
    return tuple(ids)


def critical_rules() -> list[Rule]:
    return [r for r in RULES.values() if r.is_critical]


def rules_of_kind(kinds: Iterable[RuleKind]) -> list[Rule]:
    wanted = {RuleKind(k) for k in kinds}
    return [r for r in RULES.values() if r.kind in wanted]


def rules_requiring_regression() -> list[Rule]:
    return [r for r in RULES.values() if r.requires_regression_test]
