"""Everything the decision rules are allowed to look at.

The context is filled in stage by stage by the pipeline; a rule reads it and
returns a verdict. Rules never fetch data themselves, which is what makes them
cheap to test and safe to mutate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from kontur.core.decisions import StageOutcome
from kontur.core.provenance import EvidenceSet, Sourced
from kontur.engines.faceted.models import (
    DEFAULT_FACET_CONFIG,
    FacetCatalog,
    FacetConfig,
    FilterInventory,
    FilterState,
    PaginationState,
)
from kontur.engines.faceted.signals import BusinessValue, IntentAssessment, SearchDemand
from kontur.engines.getparams.models import ParamDecision
from kontur.engines.serp.models import SerpEvidenceSummary


@dataclass
class FacetContext:
    """Working state for one URL going through the pipeline."""

    url: str
    state: FilterState
    catalog: FacetCatalog
    config: FacetConfig = DEFAULT_FACET_CONFIG
    other_params: tuple[tuple[str, str], ...] = ()
    param_decisions: dict[str, ParamDecision] = field(default_factory=dict)
    pagination: PaginationState | None = None
    demand: Sourced | None = None
    intent: IntentAssessment | None = None
    serp: SerpEvidenceSummary | None = None
    inventory: Sourced | None = None
    business: Sourced | None = None
    evidence: EvidenceSet = field(default_factory=EvidenceSet)
    trace: list[StageOutcome] = field(default_factory=list)

    # ---------------------------------------------------------------- helpers
    def record(self, stage: str, summary: str, **data: Any) -> None:
        self.trace.append(StageOutcome(stage=stage, summary=summary, data=data))

    def add_evidence(self, *sources: Sourced | None) -> None:
        for source in sources:
            if source is not None:
                self.evidence = self.evidence.merge(EvidenceSet.of(source))

    @property
    def demand_value(self) -> SearchDemand | None:
        return self.demand.value if self.demand is not None else None

    @property
    def inventory_value(self) -> FilterInventory | None:
        return self.inventory.value if self.inventory is not None else None

    @property
    def business_value(self) -> BusinessValue | None:
        return self.business.value if self.business is not None else None

    def params_with(self, decision: ParamDecision) -> tuple[str, ...]:
        return tuple(sorted(name for name, d in self.param_decisions.items() if d is decision))

    @property
    def url_param_names(self) -> tuple[str, ...]:
        names = [name for name, _ in self.other_params]
        names.extend(self.state.facet_names)
        if self.pagination is not None:
            names.append(self.pagination.parameter)
        seen: list[str] = []
        for name in names:
            if name not in seen:
                seen.append(name)
        return tuple(seen)
