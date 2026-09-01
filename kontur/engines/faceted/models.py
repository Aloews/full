"""Filter states and the facet catalogue they are validated against."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Iterable, Mapping

from kontur.core.errors import ConfigurationError
from kontur.core.urls import build_url, parse_url


class FacetStatus(StrEnum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"


@dataclass(frozen=True, slots=True)
class FacetDefinition:
    """One filterable dimension of a listing."""

    name: str
    label: str
    status: FacetStatus = FacetStatus.ACTIVE
    allowed_values: frozenset[str] | None = None
    replacement: str | None = None
    hub_candidate: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", self.name.strip().lower())
        object.__setattr__(self, "status", FacetStatus(self.status))
        if self.status is FacetStatus.DEPRECATED and not self.replacement:
            raise ConfigurationError(
                f"deprecated facet {self.name!r} must name its replacement so URLs can be redirected"
            )

    def accepts(self, value: str) -> bool:
        return self.allowed_values is None or value in self.allowed_values


@dataclass(frozen=True, slots=True)
class FacetCatalog:
    """The facets a section supports, plus the depth budget for combinations."""

    facets: Mapping[str, FacetDefinition]
    max_depth: int = 2

    def __post_init__(self) -> None:
        if self.max_depth < 1:
            raise ConfigurationError("max_depth must be >= 1")
        object.__setattr__(self, "facets", dict(self.facets))

    @classmethod
    def of(cls, definitions: Iterable[FacetDefinition], max_depth: int = 2) -> "FacetCatalog":
        return cls({d.name: d for d in definitions}, max_depth=max_depth)

    def has(self, name: str) -> bool:
        return name.strip().lower() in self.facets

    def get(self, name: str) -> FacetDefinition:
        try:
            return self.facets[name.strip().lower()]
        except KeyError as exc:
            raise ConfigurationError(f"unknown facet {name!r}") from exc

    def deprecated(self) -> tuple[FacetDefinition, ...]:
        return tuple(f for f in self.facets.values() if f.status is FacetStatus.DEPRECATED)


@dataclass(frozen=True, slots=True)
class FilterState:
    """A concrete combination of facet selections on one listing path."""

    path: str
    selections: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.path.startswith("/"):
            raise ConfigurationError(f"filter state path must start with '/': {self.path!r}")
        normalised = tuple(sorted((k.strip().lower(), v) for k, v in self.selections))
        object.__setattr__(self, "selections", normalised)

    @property
    def depth(self) -> int:
        return len(self.selections)

    @property
    def facet_names(self) -> tuple[str, ...]:
        return tuple(k for k, _ in self.selections)

    def value_of(self, facet: str) -> str | None:
        for name, value in self.selections:
            if name == facet:
                return value
        return None

    def without(self, facet: str) -> "FilterState":
        return FilterState(self.path, tuple(s for s in self.selections if s[0] != facet))

    def parent(self) -> "FilterState":
        """Drop the last selection; the bare listing is its own parent."""
        if not self.selections:
            return self
        return FilterState(self.path, self.selections[:-1])

    def to_url(self) -> str:
        return build_url(self.path, self.selections)

    @classmethod
    def from_url(cls, url: str, catalog: FacetCatalog) -> tuple["FilterState", tuple[tuple[str, str], ...]]:
        """Split a URL into (facet selections, everything else)."""
        parsed = parse_url(url)
        selections: list[tuple[str, str]] = []
        others: list[tuple[str, str]] = []
        for name, value in parsed.params:
            key = name.strip().lower()
            if catalog.has(key):
                selections.append((key, value))
            else:
                others.append((key, value))
        return cls(parsed.path, tuple(selections)), tuple(others)

    def to_dict(self) -> dict[str, Any]:
        return {"path": self.path, "selections": [list(s) for s in self.selections], "depth": self.depth}


@dataclass(frozen=True, slots=True)
class FilterInventory:
    """What the filter state actually returns."""

    total_items: int
    unique_items_vs_parent: int = 0
    editorial_blocks: int = 0
    pages: int = 1
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.total_items < 0:
            raise ConfigurationError("total_items must be >= 0")
        if self.unique_items_vs_parent < 0:
            raise ConfigurationError("unique_items_vs_parent must be >= 0")
        if self.unique_items_vs_parent > self.total_items:
            raise ConfigurationError("unique_items_vs_parent cannot exceed total_items")
        if self.pages < 1:
            raise ConfigurationError("pages must be >= 1")


@dataclass(frozen=True, slots=True)
class FacetConfig:
    """Operational thresholds for the indexation decision."""

    max_depth: int = 2
    min_items: int = 3
    min_monthly_demand: float = 30.0
    min_uniqueness: float = 0.35
    min_business_value: float = 0.20
    min_pages_for_deep_pagination: int = 2
    require_serp_evidence: bool = False

    def __post_init__(self) -> None:
        for name in ("min_uniqueness", "min_business_value"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ConfigurationError(f"{name} must be within [0, 1], got {value}")
        if self.max_depth < 1:
            raise ConfigurationError("max_depth must be >= 1")
        if self.min_items < 0:
            raise ConfigurationError("min_items must be >= 0")
        if self.min_monthly_demand < 0:
            raise ConfigurationError("min_monthly_demand must be >= 0")


DEFAULT_FACET_CONFIG = FacetConfig()


@dataclass(frozen=True, slots=True)
class PaginationState:
    """Where a URL sits inside a paginated set."""

    parameter: str
    page: int

    @property
    def is_first_page(self) -> bool:
        return self.page <= 1


def detect_pagination(params: Iterable[tuple[str, str]], pagination_params: frozenset[str]) -> PaginationState | None:
    for name, value in params:
        if name in pagination_params:
            try:
                page = int(value)
            except (TypeError, ValueError):
                page = 1
            return PaginationState(name, max(page, 1))
    return None


IGAMING_SLOTS_CATALOG = FacetCatalog.of(
    [
        FacetDefinition("provider", "Game provider"),
        FacetDefinition("mechanic", "Game mechanic"),
        FacetDefinition("feature", "Game feature"),
        FacetDefinition("theme", "Theme"),
        FacetDefinition("volatility", "Volatility", allowed_values=frozenset({"low", "medium", "high"})),
        FacetDefinition("rtp", "RTP band", allowed_values=frozenset({"96plus", "97plus", "98plus"})),
        FacetDefinition("bonus-buy", "Bonus buy", allowed_values=frozenset({"yes", "no"})),
        FacetDefinition("jackpot", "Jackpot"),
        FacetDefinition("min-bet", "Minimum bet", hub_candidate=False),
    ],
    max_depth=2,
)
