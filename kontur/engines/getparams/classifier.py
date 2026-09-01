"""Turn crawl observations into an explainable decision per GET parameter."""

from __future__ import annotations

from dataclasses import dataclass

from kontur.core.errors import ConfigurationError
from kontur.core.provenance import EvidenceSet, Sourced, require_provenance
from kontur.core.registry import rule_ids
from kontur.engines.getparams.catalog import (
    IGAMING_FACET_CANDIDATES,
    FacetCandidate,
    ParamFamily,
    family_of,
)
from kontur.engines.getparams.models import (
    ParamDecision,
    ParamDemand,
    ParamObservation,
    ParamReason,
    ParamRuling,
)


@dataclass(frozen=True, slots=True)
class ClassifierConfig:
    """Thresholds for promoting a parameter to an indexable facet.

    These are operational settings, not claims about the search engine. Changing
    them changes how much indexable space the site opens up, which is exactly
    the kind of change that belongs in an experiment.
    """

    min_demand_for_hub: float = 100.0
    min_values_with_demand: int = 3
    max_distinct_values_for_hub: int = 200

    def __post_init__(self) -> None:
        if self.min_demand_for_hub < 0:
            raise ConfigurationError("min_demand_for_hub must be >= 0")
        if self.min_values_with_demand < 1:
            raise ConfigurationError("min_values_with_demand must be >= 1")
        if self.max_distinct_values_for_hub < 1:
            raise ConfigurationError("max_distinct_values_for_hub must be >= 1")


DEFAULT_CONFIG = ClassifierConfig()


def classify_parameter(
    observation: ParamObservation,
    *,
    demand: Sourced | None = None,
    config: ClassifierConfig = DEFAULT_CONFIG,
    facet_candidates: dict[str, FacetCandidate] | None = None,
) -> ParamRuling:
    """Classify one parameter.

    ``demand`` must be a :class:`~kontur.core.provenance.Sourced` wrapping a
    :class:`ParamDemand`; a bare value is refused, because a facet is promoted on
    measured demand or not at all (rules GETP-006, DATA-001).
    """
    if not isinstance(observation, ParamObservation):
        raise ConfigurationError("classify_parameter() needs a ParamObservation")

    family = family_of(observation.name, facet_candidates=facet_candidates)
    evidence = EvidenceSet.of(observation.provenance)
    common = {
        "name": observation.name,
        "detected_urls": observation.detected_urls,
        "distinct_values": observation.distinct_values,
    }

    if family is ParamFamily.SESSION:
        return ParamRuling(
            **common,
            decision=ParamDecision.BLOCK,
            reasons=(ParamReason.SESSION_IDENTIFIER, ParamReason.UNBOUNDED_VALUE_SPACE),
            rule_ids=rule_ids("GETP-007"),
            evidence=evidence,
            note="Per-visitor identifier: one document per session is a crawl trap.",
        )

    if family is ParamFamily.TRACKING:
        return ParamRuling(
            **common,
            decision=ParamDecision.EXCLUDE,
            reasons=(ParamReason.TRACKING,),
            rule_ids=rule_ids("GETP-001"),
            evidence=evidence,
            note="Campaign/click identifier: does not change the document.",
        )

    if family in (ParamFamily.SORT, ParamFamily.DISPLAY):
        return ParamRuling(
            **common,
            decision=ParamDecision.EXCLUDE,
            reasons=(ParamReason.DUPLICATE_INTENT,),
            rule_ids=rule_ids("GETP-004"),
            evidence=evidence,
            note="Re-orders or re-renders the same inventory.",
        )

    if family is ParamFamily.PAGINATION:
        return ParamRuling(
            **common,
            decision=ParamDecision.CONTEXT_DEPENDENT,
            reasons=(ParamReason.PAGINATION,),
            rule_ids=rule_ids("GETP-005"),
            evidence=evidence,
            note="page=1 duplicates the base URL; deeper pages are decided per URL.",
        )

    if family is ParamFamily.FACET_CANDIDATE:
        return _classify_facet_candidate(observation, demand, config, evidence, common)

    return ParamRuling(
        **common,
        decision=ParamDecision.ANALYZE,
        reasons=(ParamReason.UNKNOWN_PARAMETER,),
        rule_ids=rule_ids("GETP-003"),
        evidence=evidence,
        note="Not in the catalogue: held for review, never indexable by default.",
    )


def _classify_facet_candidate(
    observation: ParamObservation,
    demand: Sourced | None,
    config: ClassifierConfig,
    evidence: EvidenceSet,
    common: dict,
) -> ParamRuling:
    if observation.distinct_values > config.max_distinct_values_for_hub:
        return ParamRuling(
            **common,
            decision=ParamDecision.ANALYZE,
            reasons=(ParamReason.POSSIBLE_SEO_FACET, ParamReason.UNBOUNDED_VALUE_SPACE),
            rule_ids=rule_ids("GETP-006"),
            evidence=evidence,
            note=(
                f"{observation.distinct_values} distinct values exceeds the "
                f"{config.max_distinct_values_for_hub} allowed for a hub."
            ),
        )

    if demand is None:
        return ParamRuling(
            **common,
            decision=ParamDecision.ANALYZE,
            reasons=(ParamReason.POSSIBLE_SEO_FACET, ParamReason.DEMAND_DATA_MISSING),
            rule_ids=rule_ids("GETP-006"),
            evidence=evidence,
            note="Looks like an SEO facet, but no demand export covers it yet.",
        )

    sourced = require_provenance(demand, what=f"demand for parameter {observation.name!r}")
    stats = sourced.value
    if not isinstance(stats, ParamDemand):
        raise ConfigurationError("demand must wrap a ParamDemand")
    evidence = evidence.merge(EvidenceSet.of(sourced.provenance))

    if stats.total_monthly_demand <= 0 or stats.values_with_demand <= 0:
        return ParamRuling(
            **common,
            decision=ParamDecision.EXCLUDE,
            reasons=(ParamReason.NO_SEARCH_DEMAND, ParamReason.DUPLICATE_INTENT),
            rule_ids=rule_ids("GETP-006"),
            evidence=evidence,
            demand=sourced,
            note="Measured demand for every value is zero.",
        )

    meets_volume = stats.total_monthly_demand >= config.min_demand_for_hub
    meets_breadth = stats.values_with_demand >= config.min_values_with_demand
    if meets_volume and meets_breadth:
        return ParamRuling(
            **common,
            decision=ParamDecision.SEO_HUB,
            reasons=(
                ParamReason.POSSIBLE_SEO_FACET,
                ParamReason.SEARCH_DEMAND,
                ParamReason.COMMERCIAL_INTENT,
            ),
            rule_ids=rule_ids("GETP-006"),
            evidence=evidence,
            demand=sourced,
            note=(
                f"{stats.values_with_demand} values carry measured demand "
                f"({stats.total_monthly_demand:.0f}/month)."
            ),
        )

    return ParamRuling(
        **common,
        decision=ParamDecision.ANALYZE,
        reasons=(ParamReason.POSSIBLE_SEO_FACET, ParamReason.LOW_URL_VOLUME),
        rule_ids=rule_ids("GETP-006"),
        evidence=evidence,
        demand=sourced,
        note=(
            f"Demand exists but is below the hub thresholds "
            f"({stats.total_monthly_demand:.0f} < {config.min_demand_for_hub} or "
            f"{stats.values_with_demand} < {config.min_values_with_demand} values)."
        ),
    )


__all__ = [
    "ClassifierConfig",
    "DEFAULT_CONFIG",
    "IGAMING_FACET_CANDIDATES",
    "classify_parameter",
]
