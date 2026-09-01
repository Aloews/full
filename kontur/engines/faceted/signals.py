"""The measurable signals a filter state is judged on.

Every score is bounded to [0, 1], raises on impossible input, and is documented
by what it *measures* rather than by what it supposedly does to rankings.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from kontur.core.errors import ConfigurationError

#: Volume at which demand is considered fully satisfied for scoring purposes.
DEMAND_REFERENCE_VOLUME = 1000.0


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))


@dataclass(frozen=True, slots=True)
class SearchDemand:
    """Measured demand for the query cluster a filter state targets."""

    monthly_volume: float
    query_count: int = 0
    top_query: str | None = None

    def __post_init__(self) -> None:
        if self.monthly_volume < 0:
            raise ConfigurationError("monthly_volume must be >= 0")
        if self.query_count < 0:
            raise ConfigurationError("query_count must be >= 0")


class IntentLabel(StrEnum):
    COMMERCIAL = "commercial"
    INFORMATIONAL = "informational"
    NAVIGATIONAL = "navigational"
    MIXED = "mixed"


@dataclass(frozen=True, slots=True)
class IntentAssessment:
    """Does this filter state answer a different question than its parent?"""

    label: IntentLabel
    overlap_with_parent: float
    distinct_query_share: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "label", IntentLabel(self.label))
        for name in ("overlap_with_parent", "distinct_query_share"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ConfigurationError(f"{name} must be within [0, 1], got {value}")

    @property
    def is_distinct(self) -> bool:
        """Distinct when most of its query cluster is not the parent's cluster."""
        return self.overlap_with_parent < 0.8

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label.value,
            "overlap_with_parent": self.overlap_with_parent,
            "distinct_query_share": self.distinct_query_share,
            "is_distinct": self.is_distinct,
        }


def demand_score(monthly_volume: float, *, reference: float = DEMAND_REFERENCE_VOLUME) -> float:
    """Normalise raw monthly demand onto [0, 1] with a log scale.

    0 volume -> 0.0, ``reference`` or more -> 1.0. Log scaling keeps a
    500/month cluster from looking negligible next to a 50 000/month head term.
    """
    if monthly_volume < 0:
        raise ConfigurationError("monthly_volume must be >= 0")
    if reference <= 0:
        raise ConfigurationError("reference must be > 0")
    if monthly_volume == 0:
        return 0.0
    if monthly_volume >= reference:
        return 1.0
    return _clamp01(math.log1p(monthly_volume) / math.log1p(reference))


def content_uniqueness_score(
    *,
    unique_items: int,
    total_items: int,
    editorial_blocks: int = 0,
    editorial_target: int = 3,
) -> float:
    """How much of this page is not already on the parent.

    Inventory difference carries most of the weight; original editorial blocks
    (intro, comparison table, FAQ) carry the rest.
    """
    if total_items < 0 or unique_items < 0 or editorial_blocks < 0:
        raise ConfigurationError("counts must be >= 0")
    if unique_items > total_items:
        raise ConfigurationError("unique_items cannot exceed total_items")
    if editorial_target < 1:
        raise ConfigurationError("editorial_target must be >= 1")
    inventory = (unique_items / total_items) if total_items else 0.0
    editorial = min(editorial_blocks / editorial_target, 1.0)
    return _clamp01(0.7 * inventory + 0.3 * editorial)


def business_value_score(
    *,
    commercial_items: int,
    total_items: int,
    revenue_index: float = 0.0,
) -> float:
    """Commercial worth of the filter state.

    ``revenue_index`` is a site-supplied [0, 1] figure (share of revenue, margin
    index, whatever the business tracks); Kontur does not invent it.
    """
    if commercial_items < 0 or total_items < 0:
        raise ConfigurationError("counts must be >= 0")
    if commercial_items > total_items:
        raise ConfigurationError("commercial_items cannot exceed total_items")
    if not 0.0 <= revenue_index <= 1.0:
        raise ConfigurationError(f"revenue_index must be within [0, 1], got {revenue_index}")
    coverage = (commercial_items / total_items) if total_items else 0.0
    return _clamp01(0.6 * coverage + 0.4 * revenue_index)


@dataclass(frozen=True, slots=True)
class BusinessValue:
    """Raw business inputs, kept alongside the score for auditability."""

    commercial_items: int
    total_items: int
    revenue_index: float = 0.0

    @property
    def score(self) -> float:
        return business_value_score(
            commercial_items=self.commercial_items,
            total_items=self.total_items,
            revenue_index=self.revenue_index,
        )
