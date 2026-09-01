"""Data model for the Yandex GET parameter controller.

Yandex Webmaster exposes a dedicated "GET parameters" setting where a site owner
declares which parameters are taken into account during indexing and which are
ignored, in order to cut duplicates, reduce crawl load and speed up indexing.
Kontur models that decision explicitly, per parameter, with reasons and with the
crawl evidence that produced it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Iterable

from kontur.core.errors import ConfigurationError
from kontur.core.provenance import Confidence, EvidenceSet, Provenance, Sourced


class ParamDecision(StrEnum):
    """What the controller declares for a single GET parameter."""

    #: Do not crawl URLs carrying it at all (crawl trap / unbounded space).
    BLOCK = "BLOCK"
    #: Ignore it when indexing: the URL without it is the document.
    EXCLUDE = "EXCLUDE"
    #: Meaning depends on the value (page=1 vs page=7) — decided per URL.
    CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"
    #: Not decided yet. Safe-by-default hold: never indexable while pending.
    ANALYZE = "ANALYZE"
    #: A real SEO facet: values of this parameter deserve indexable hubs.
    SEO_HUB = "SEO_HUB"


#: Higher number = more prohibitive. Conflicting rules resolve upwards, which is
#: how Yandex behaves when directives disagree.
PARAM_RESTRICTIVENESS: dict[ParamDecision, int] = {
    ParamDecision.SEO_HUB: 0,
    ParamDecision.ANALYZE: 1,
    ParamDecision.CONTEXT_DEPENDENT: 2,
    ParamDecision.EXCLUDE: 3,
    ParamDecision.BLOCK: 4,
}


def most_restrictive_param_decision(decisions: Iterable[ParamDecision]) -> ParamDecision:
    items = [ParamDecision(d) for d in decisions]
    if not items:
        raise ConfigurationError("most_restrictive_param_decision() needs at least one decision")
    return max(items, key=lambda d: PARAM_RESTRICTIVENESS[d])


class ParamReason(StrEnum):
    """Why a parameter received its decision (shown in the dashboard)."""

    TRACKING = "tracking"
    DUPLICATE_INTENT = "duplicate_intent"
    PAGINATION = "pagination"
    SESSION_IDENTIFIER = "session_identifier"
    UNBOUNDED_VALUE_SPACE = "unbounded_value_space"
    POSSIBLE_SEO_FACET = "possible_seo_facet"
    SEARCH_DEMAND = "search_demand"
    COMMERCIAL_INTENT = "commercial_intent"
    NO_SEARCH_DEMAND = "no_search_demand"
    DEMAND_DATA_MISSING = "demand_data_missing"
    UNKNOWN_PARAMETER = "unknown_parameter"
    MANUAL_OVERRIDE = "manual_override"
    LOW_URL_VOLUME = "low_url_volume"


@dataclass(frozen=True, slots=True)
class ParamObservation:
    """What the crawl/log ingest actually saw for one parameter."""

    name: str
    detected_urls: int
    distinct_values: int
    provenance: Provenance
    sample_values: tuple[str, ...] = ()
    pages_with_param: int = 0
    indexable_pages_with_param: int = 0

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ConfigurationError("parameter name is required")
        object.__setattr__(self, "name", self.name.strip().lower())
        if self.detected_urls < 0 or self.distinct_values < 0:
            raise ConfigurationError("counts must be non-negative")
        if not isinstance(self.provenance, Provenance):
            raise ConfigurationError("ParamObservation requires a Provenance")

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "detected_urls": self.detected_urls,
            "distinct_values": self.distinct_values,
            "sample_values": list(self.sample_values),
            "pages_with_param": self.pages_with_param,
            "indexable_pages_with_param": self.indexable_pages_with_param,
            "provenance": self.provenance.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class ParamDemand:
    """Measured demand for the values of one parameter.

    ``total_monthly_demand`` is whatever the demand export reports (Wordstat or
    an equivalent); Kontur never estimates it.
    """

    parameter: str
    values_with_demand: int
    total_monthly_demand: float
    top_values: tuple[tuple[str, float], ...] = ()

    def __post_init__(self) -> None:
        if self.values_with_demand < 0 or self.total_monthly_demand < 0:
            raise ConfigurationError("demand figures must be non-negative")


@dataclass(frozen=True, slots=True)
class ParamRuling:
    """The controller's explainable verdict for one parameter."""

    name: str
    decision: ParamDecision
    reasons: tuple[ParamReason, ...]
    rule_ids: tuple[str, ...] = ()
    detected_urls: int = 0
    distinct_values: int = 0
    evidence: EvidenceSet = field(default_factory=EvidenceSet)
    demand: Sourced | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision", ParamDecision(self.decision))
        object.__setattr__(self, "reasons", tuple(ParamReason(r) for r in self.reasons))
        if not self.reasons:
            raise ConfigurationError(
                f"parameter {self.name} received {self.decision} with no reason; "
                "unexplained parameter decisions are not allowed"
            )

    @property
    def confidence(self) -> Confidence:
        return self.evidence.confidence

    @property
    def is_sample(self) -> bool:
        return self.evidence.is_sample

    @property
    def is_indexable(self) -> bool:
        return self.decision is ParamDecision.SEO_HUB

    def to_dict(self) -> dict[str, Any]:
        return {
            "parameter": self.name,
            "detected_urls": self.detected_urls,
            "distinct_values": self.distinct_values,
            "decision": self.decision.value,
            "reason": [r.value for r in self.reasons],
            "rules": list(self.rule_ids),
            "confidence": self.confidence.value,
            "is_sample": self.is_sample,
            "note": self.note,
            "evidence": self.evidence.to_list(),
        }

    def dashboard_row(self) -> dict[str, Any]:
        """The row rendered under Indexation -> GET Parameters."""
        return {
            "parameter": self.name,
            "detected_urls": self.detected_urls,
            "decision": "SEO HUB" if self.decision is ParamDecision.SEO_HUB else self.decision.value,
            "reason": ", ".join(r.value.replace("_", " ") for r in self.reasons),
            "confidence": self.confidence.value,
            "is_sample": self.is_sample,
        }


def merge_rulings(rulings: list[ParamRuling]) -> ParamRuling:
    """Resolve conflicting rulings for the same parameter (rule GETP-002).

    The most restrictive decision wins and every contributing reason is kept, so
    the dashboard can show *why* a parameter ended up excluded even though one
    source wanted it indexable.
    """
    if not rulings:
        raise ConfigurationError("merge_rulings() needs at least one ruling")
    names = {r.name for r in rulings}
    if len(names) != 1:
        raise ConfigurationError(f"cannot merge rulings for different parameters: {sorted(names)}")

    winner = most_restrictive_param_decision(r.decision for r in rulings)
    reasons: list[ParamReason] = []
    rule_ids: list[str] = ["GETP-002"] if len({r.decision for r in rulings}) > 1 else []
    evidence = EvidenceSet()
    demand: Sourced | None = None
    notes: list[str] = []

    for ruling in rulings:
        for reason in ruling.reasons:
            if reason not in reasons:
                reasons.append(reason)
        for rid in ruling.rule_ids:
            if rid not in rule_ids:
                rule_ids.append(rid)
        evidence = evidence.merge(ruling.evidence)
        demand = demand or ruling.demand
        if ruling.note:
            notes.append(ruling.note)

    return ParamRuling(
        name=next(iter(names)),
        decision=winner,
        reasons=tuple(reasons),
        rule_ids=tuple(rule_ids),
        detected_urls=max(r.detected_urls for r in rulings),
        distinct_values=max(r.distinct_values for r in rulings),
        evidence=evidence,
        demand=demand,
        note="; ".join(notes) or None,
    )
