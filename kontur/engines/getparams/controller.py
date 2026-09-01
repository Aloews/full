"""The Yandex GET Parameter Controller.

Holds the crawl observations, the demand exports, the human overrides and any
policy imported from an existing configuration (robots.txt, a previous Webmaster
setting), and resolves them into one ruling per parameter.

Conflicts between co-equal policy sources resolve to the more prohibitive
variant (rule GETP-002).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from kontur.core.errors import ConfigurationError
from kontur.core.provenance import EvidenceSet, Provenance, Sourced
from kontur.core.registry import rule_ids
from kontur.engines.getparams.catalog import FacetCandidate
from kontur.engines.getparams.classifier import DEFAULT_CONFIG, ClassifierConfig, classify_parameter
from kontur.engines.getparams.models import (
    ParamDecision,
    ParamObservation,
    ParamReason,
    ParamRuling,
    merge_rulings,
)


@dataclass(frozen=True, slots=True)
class ParamPolicy:
    """A declared policy for a parameter, from a human or an imported config."""

    name: str
    decision: ParamDecision
    note: str
    provenance: Provenance
    reasons: tuple[ParamReason, ...] = (ParamReason.MANUAL_OVERRIDE,)
    replaces_automatic: bool = False

    def __post_init__(self) -> None:
        if not self.note or not self.note.strip():
            raise ConfigurationError(
                f"policy for {self.name!r} needs a note: an unexplained override is not auditable"
            )
        object.__setattr__(self, "name", self.name.strip().lower())
        object.__setattr__(self, "decision", ParamDecision(self.decision))

    def as_ruling(self, observation: ParamObservation | None) -> ParamRuling:
        return ParamRuling(
            name=self.name,
            decision=self.decision,
            reasons=self.reasons,
            rule_ids=rule_ids("GETP-002"),
            detected_urls=observation.detected_urls if observation else 0,
            distinct_values=observation.distinct_values if observation else 0,
            evidence=EvidenceSet.of(self.provenance),
            note=self.note,
        )


@dataclass
class GetParameterController:
    """Aggregates evidence and emits one ruling per parameter."""

    config: ClassifierConfig = DEFAULT_CONFIG
    facet_candidates: dict[str, FacetCandidate] | None = None
    _observations: dict[str, ParamObservation] = field(default_factory=dict, init=False)
    _demand: dict[str, Sourced] = field(default_factory=dict, init=False)
    _overrides: dict[str, ParamPolicy] = field(default_factory=dict, init=False)
    _policies: dict[str, list[ParamPolicy]] = field(default_factory=dict, init=False)

    # ------------------------------------------------------------------ inputs
    def observe(self, observations: Iterable[ParamObservation]) -> "GetParameterController":
        for observation in observations:
            existing = self._observations.get(observation.name)
            if existing is None or observation.detected_urls >= existing.detected_urls:
                self._observations[observation.name] = observation
        return self

    def set_demand(self, parameter: str, demand: Sourced) -> "GetParameterController":
        if not isinstance(demand, Sourced):
            raise ConfigurationError(
                f"demand for {parameter!r} must be Sourced(...) with source + retrieved_at + confidence"
            )
        self._demand[parameter.strip().lower()] = demand
        return self

    def override(self, policy: ParamPolicy) -> "GetParameterController":
        """Replace the automatic classification for a parameter (audited)."""
        self._overrides[policy.name] = ParamPolicy(
            name=policy.name,
            decision=policy.decision,
            note=policy.note,
            provenance=policy.provenance,
            reasons=policy.reasons,
            replaces_automatic=True,
        )
        return self

    def add_policy(self, policy: ParamPolicy) -> "GetParameterController":
        """Add a co-equal policy (e.g. imported robots.txt / previous settings).

        Co-equal policies never loosen a decision: the most restrictive of all
        co-equal sources wins.
        """
        self._policies.setdefault(policy.name, []).append(policy)
        return self

    # ------------------------------------------------------------------ outputs
    @property
    def known_parameters(self) -> tuple[str, ...]:
        names = set(self._observations) | set(self._overrides) | set(self._policies)
        return tuple(sorted(names))

    def automatic_ruling(self, parameter: str) -> ParamRuling | None:
        observation = self._observations.get(parameter)
        if observation is None:
            return None
        return classify_parameter(
            observation,
            demand=self._demand.get(parameter),
            config=self.config,
            facet_candidates=self.facet_candidates,
        )

    def ruling(self, parameter: str) -> ParamRuling:
        """The effective ruling for one parameter, with every reason preserved."""
        name = parameter.strip().lower()
        observation = self._observations.get(name)
        contributions: list[ParamRuling] = []

        override = self._overrides.get(name)
        if override is not None:
            contributions.append(override.as_ruling(observation))
        else:
            automatic = self.automatic_ruling(name)
            if automatic is not None:
                contributions.append(automatic)

        for policy in self._policies.get(name, []):
            contributions.append(policy.as_ruling(observation))

        if not contributions:
            # An unknown parameter is held, never quietly indexed (rule GETP-003).
            return ParamRuling(
                name=name,
                decision=ParamDecision.ANALYZE,
                reasons=(ParamReason.UNKNOWN_PARAMETER,),
                rule_ids=rule_ids("GETP-003"),
                note="No observation, demand or policy for this parameter.",
            )
        if len(contributions) == 1:
            return contributions[0]
        return merge_rulings(contributions)

    def rulings(self) -> list[ParamRuling]:
        """All rulings, ordered by crawl impact (most detected URLs first)."""
        return sorted(
            (self.ruling(name) for name in self.known_parameters),
            key=lambda r: (-r.detected_urls, r.name),
        )

    def decision(self, parameter: str) -> ParamDecision:
        return self.ruling(parameter).decision

    def _names_with(self, *decisions: ParamDecision) -> tuple[str, ...]:
        wanted = set(decisions)
        return tuple(sorted(r.name for r in self.rulings() if r.decision in wanted))

    def excluded_parameters(self) -> tuple[str, ...]:
        """Parameters Yandex should ignore when indexing (EXCLUDE and BLOCK)."""
        return self._names_with(ParamDecision.EXCLUDE, ParamDecision.BLOCK)

    def blocked_parameters(self) -> tuple[str, ...]:
        return self._names_with(ParamDecision.BLOCK)

    def indexable_parameters(self) -> tuple[str, ...]:
        return self._names_with(ParamDecision.SEO_HUB)

    def context_dependent_parameters(self) -> tuple[str, ...]:
        return self._names_with(ParamDecision.CONTEXT_DEPENDENT)

    def pending_parameters(self) -> tuple[str, ...]:
        return self._names_with(ParamDecision.ANALYZE)

    def dashboard_rows(self) -> list[dict[str, Any]]:
        return [r.dashboard_row() for r in self.rulings()]

    def summary(self) -> dict[str, Any]:
        rulings = self.rulings()
        by_decision: dict[str, int] = {}
        for ruling in rulings:
            by_decision[ruling.decision.value] = by_decision.get(ruling.decision.value, 0) + 1
        return {
            "parameters": len(rulings),
            "detected_urls": sum(r.detected_urls for r in rulings),
            "by_decision": by_decision,
            "pending_review": list(self.pending_parameters()),
            "contains_sample_data": any(r.is_sample for r in rulings),
        }
