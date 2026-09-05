"""Data providers for the faceted pipeline.

The engine never fetches anything itself: it asks providers, and every provider
returns data wrapped in :class:`~kontur.core.provenance.Sourced` (or ``None``
when it has nothing). That is what makes "we have no demand data for this
filter state" a first-class outcome instead of a silent zero.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from kontur.core.provenance import Sourced
from kontur.engines.faceted.models import FilterState
from kontur.engines.faceted.signals import IntentAssessment
from kontur.engines.serp.models import SerpEvidenceSummary


def state_key(state: FilterState) -> str:
    """Stable dictionary key for a filter state."""
    return state.to_url()


@runtime_checkable
class QueryResolver(Protocol):
    def query_for(self, state: FilterState) -> str | None: ...


@runtime_checkable
class DemandProvider(Protocol):
    def demand_for(self, state: FilterState) -> Sourced | None: ...


@runtime_checkable
class IntentProvider(Protocol):
    def intent_for(self, state: FilterState) -> IntentAssessment | None: ...


@runtime_checkable
class SerpProvider(Protocol):
    def evidence_for(self, state: FilterState) -> SerpEvidenceSummary | None: ...


@runtime_checkable
class InventoryProvider(Protocol):
    def inventory_for(self, state: FilterState) -> Sourced | None: ...


@runtime_checkable
class BusinessValueProvider(Protocol):
    def value_for(self, state: FilterState) -> Sourced | None: ...


@dataclass(frozen=True, slots=True)
class LabelQueryResolver:
    """Builds the target query from the facet values, e.g. 'megaways слоты'."""

    suffix: str = ""

    def query_for(self, state: FilterState) -> str | None:
        parts = [value for _, value in state.selections]
        if not parts:
            return None
        query = " ".join(parts)
        return f"{query} {self.suffix}".strip() if self.suffix else query


@dataclass
class MappingProvider:
    """Serves pre-loaded values keyed by filter-state URL."""

    values: Mapping[str, object] = field(default_factory=dict)

    def _get(self, state: FilterState):
        return self.values.get(state_key(state))

    def demand_for(self, state: FilterState) -> Sourced | None:
        return self._get(state)

    def intent_for(self, state: FilterState) -> IntentAssessment | None:
        return self._get(state)

    def evidence_for(self, state: FilterState) -> SerpEvidenceSummary | None:
        return self._get(state)

    def inventory_for(self, state: FilterState) -> Sourced | None:
        return self._get(state)

    def value_for(self, state: FilterState) -> Sourced | None:
        return self._get(state)
