"""Indexation decisions and the reason codes that explain them.

Every decision Kontur emits is a :class:`DecisionRecord`: a verdict plus the
ordered reason codes, the rule ids that fired, and the provenance of every fact
that was consulted. A decision without reasons is a bug, not a shortcut.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Iterable, Sequence

from kontur.core.errors import ConfigurationError
from kontur.core.provenance import Confidence, EvidenceSet


class Decision(StrEnum):
    """What the crawler/indexer should do with a URL."""

    INDEX = "INDEX"
    CANONICAL = "CANONICAL"
    NOINDEX = "NOINDEX"
    BLOCK = "BLOCK"
    REDIRECT = "REDIRECT"


#: Higher number = removes more of the URL's ability to rank on its own.
#: Used when two rules disagree: the more restrictive verdict wins.
DECISION_RESTRICTIVENESS: dict[Decision, int] = {
    Decision.INDEX: 0,
    Decision.CANONICAL: 1,
    Decision.REDIRECT: 2,
    Decision.NOINDEX: 3,
    Decision.BLOCK: 4,
}


def most_restrictive(decisions: Iterable[Decision]) -> Decision:
    """Resolve conflicting verdicts by taking the most restrictive one.

    Yandex applies the more prohibitive variant when directives conflict, so
    Kontur models the same lattice rather than letting rule order decide.
    """
    items = list(decisions)
    if not items:
        raise ConfigurationError("most_restrictive() needs at least one decision")
    return max(items, key=lambda d: DECISION_RESTRICTIVENESS[Decision(d)])


class ReasonCode(StrEnum):
    """Machine-readable explanation fragments attached to a decision."""

    # --- reasons to index -------------------------------------------------
    SEARCH_DEMAND = "search_demand"
    UNIQUE_INTENT = "unique_intent"
    UNIQUE_CONTENT = "unique_content"
    COMMERCIAL_VALUE = "commercial_value"
    COMPETITOR_EVIDENCE = "competitor_evidence"
    SUFFICIENT_INVENTORY = "sufficient_inventory"
    PAGINATION_DEEP_SET = "pagination_deep_set"

    # --- reasons to hold back ---------------------------------------------
    NO_SEARCH_DEMAND = "no_search_demand"
    DEMAND_DATA_MISSING = "demand_data_missing"
    DUPLICATE_INTENT = "duplicate_intent"
    DUPLICATE_CONTENT = "duplicate_content"
    THIN_CONTENT = "thin_content"
    EMPTY_RESULT_SET = "empty_result_set"
    FACET_DEPTH_EXCEEDED = "facet_depth_exceeded"
    TRACKING_PARAMETER = "tracking_parameter"
    EXCLUDED_PARAMETER = "excluded_parameter"
    BLOCKED_PARAMETER = "blocked_parameter"
    SORT_STATE = "sort_state"
    PAGINATION_FIRST_PAGE = "pagination_first_page"
    LOW_BUSINESS_VALUE = "low_business_value"
    NO_COMPETITOR_EVIDENCE = "no_competitor_evidence"
    DEPRECATED_FACET = "deprecated_facet"
    UNKNOWN_PARAMETER = "unknown_parameter"
    AWAITING_ANALYSIS = "awaiting_analysis"
    SAMPLE_DATA_ONLY = "sample_data_only"


@dataclass(frozen=True, slots=True)
class StageOutcome:
    """One step of the faceted pipeline, kept for the audit trail."""

    stage: str
    summary: str
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"stage": self.stage, "summary": self.summary, "data": dict(self.data)}


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    """An explainable indexation verdict for one URL."""

    url: str
    decision: Decision
    reasons: tuple[ReasonCode, ...]
    rule_ids: tuple[str, ...] = ()
    evidence: EvidenceSet = field(default_factory=EvidenceSet)
    canonical_target: str | None = None
    redirect_target: str | None = None
    trace: tuple[StageOutcome, ...] = ()

    def __post_init__(self) -> None:
        if not self.url:
            raise ConfigurationError("DecisionRecord.url is required")
        object.__setattr__(self, "decision", Decision(self.decision))
        object.__setattr__(self, "reasons", tuple(ReasonCode(r) for r in self.reasons))
        if not self.reasons:
            raise ConfigurationError(
                f"decision {self.decision} for {self.url} has no reason codes; "
                "unexplained decisions are not allowed"
            )
        if self.decision is Decision.CANONICAL and not self.canonical_target:
            raise ConfigurationError(f"CANONICAL decision for {self.url} needs a canonical_target")
        if self.decision is Decision.REDIRECT and not self.redirect_target:
            raise ConfigurationError(f"REDIRECT decision for {self.url} needs a redirect_target")

    @property
    def confidence(self) -> Confidence:
        return self.evidence.confidence

    @property
    def is_sample(self) -> bool:
        return self.evidence.is_sample

    def to_dict(self) -> dict[str, Any]:
        """Serialise to the documented decision envelope.

        The ``url`` / ``decision`` / ``reason`` triple is the stable public
        contract (see tests/regression/test_decision_contract.py); everything
        else is additive.
        """
        payload: dict[str, Any] = {
            "url": self.url,
            "decision": self.decision.value,
            "reason": [r.value for r in self.reasons],
            "rules": list(self.rule_ids),
            "confidence": self.confidence.value,
            "is_sample": self.is_sample,
            "evidence": self.evidence.to_list(),
            "trace": [s.to_dict() for s in self.trace],
        }
        if self.canonical_target:
            payload["canonical_target"] = self.canonical_target
        if self.redirect_target:
            payload["redirect_target"] = self.redirect_target
        return payload


def merge_decisions(records: Sequence[DecisionRecord]) -> DecisionRecord:
    """Combine verdicts for the same URL, keeping the most restrictive one.

    Reasons and evidence from every contributing record are preserved so the
    merged verdict stays explainable.
    """
    if not records:
        raise ConfigurationError("merge_decisions() needs at least one record")
    urls = {r.url for r in records}
    if len(urls) != 1:
        raise ConfigurationError(f"cannot merge decisions for different URLs: {sorted(urls)}")

    winner_decision = most_restrictive(r.decision for r in records)
    winners = [r for r in records if r.decision is winner_decision]
    primary = winners[0]

    reasons: list[ReasonCode] = []
    rule_ids: list[str] = []
    evidence = EvidenceSet()
    trace: list[StageOutcome] = []
    for record in records:
        for reason in record.reasons:
            if reason not in reasons:
                reasons.append(reason)
        for rid in record.rule_ids:
            if rid not in rule_ids:
                rule_ids.append(rid)
        evidence = evidence.merge(record.evidence)
        trace.extend(record.trace)

    return DecisionRecord(
        url=primary.url,
        decision=winner_decision,
        reasons=tuple(reasons),
        rule_ids=tuple(rule_ids),
        evidence=evidence,
        canonical_target=primary.canonical_target,
        redirect_target=primary.redirect_target,
        trace=tuple(trace),
    )
