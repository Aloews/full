"""Provenance: every external fact carries source + retrieval date + confidence.

This module is the spine of the "no fake data" requirement. A value that came
from outside the system (Yandex Webmaster, a crawl, a SERP capture, Wordstat)
can only enter an engine wrapped in :class:`Sourced`, and :class:`Provenance`
refuses to be constructed without the three mandatory attributes.

Sample data is allowed to exist (development, fixtures, the demo dashboard) but
it is *marked* — :attr:`Provenance.is_sample` — and every report built from it
inherits the mark, so it can never be presented as a real measurement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Any, Generic, Iterable, TypeVar

from kontur.core.errors import (
    InvalidProvenanceError,
    MissingProvenanceError,
    SampleDataError,
)

T = TypeVar("T")

#: Source prefixes that mark data as non-authoritative (fixtures, demos, generators).
SAMPLE_SOURCE_PREFIXES: tuple[str, ...] = ("sample:", "fixture:", "synthetic:", "demo:")

_SOURCE_RE = re.compile(r"^[a-z0-9][a-z0-9_.:+-]{2,120}$")


class Confidence(StrEnum):
    """How much weight a fact may carry in a decision."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def rank(self) -> int:
        return {"low": 1, "medium": 2, "high": 3}[self.value]

    @classmethod
    def weakest(cls, values: Iterable["Confidence"]) -> "Confidence":
        items = list(values)
        if not items:
            return cls.LOW
        return min(items, key=lambda c: c.rank)


def _coerce_retrieved_at(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime(value.year, value.month, value.day)
    elif isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
        except ValueError as exc:  # pragma: no cover - message only
            raise InvalidProvenanceError(f"retrieved_at is not ISO-8601: {value!r}") from exc
    else:
        raise InvalidProvenanceError(f"retrieved_at must be a date/datetime/ISO string, got {type(value).__name__}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class Provenance:
    """Where a fact came from, when it was retrieved and how much we trust it."""

    source: str
    retrieved_at: datetime
    confidence: Confidence
    source_url: str | None = None
    note: str | None = None

    def __post_init__(self) -> None:
        if not self.source or not self.source.strip():
            raise MissingProvenanceError("provenance.source is required")
        source = self.source.strip().lower()
        if not _SOURCE_RE.match(source):
            raise InvalidProvenanceError(
                f"provenance.source {self.source!r} must match {_SOURCE_RE.pattern}"
            )
        object.__setattr__(self, "source", source)

        if self.retrieved_at is None:
            raise MissingProvenanceError("provenance.retrieved_at is required")
        retrieved = _coerce_retrieved_at(self.retrieved_at)
        if retrieved > datetime.now(timezone.utc):
            raise InvalidProvenanceError("provenance.retrieved_at is in the future")
        object.__setattr__(self, "retrieved_at", retrieved)

        if self.confidence is None:
            raise MissingProvenanceError("provenance.confidence is required")
        try:
            object.__setattr__(self, "confidence", Confidence(self.confidence))
        except ValueError as exc:
            raise InvalidProvenanceError(f"unknown confidence {self.confidence!r}") from exc

    @property
    def is_sample(self) -> bool:
        """True when the fact comes from fixtures/demo generators, not a real export."""
        return self.source.startswith(SAMPLE_SOURCE_PREFIXES)

    def age_days(self, now: datetime | None = None) -> float:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return (now - self.retrieved_at).total_seconds() / 86400.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "retrieved_at": self.retrieved_at.isoformat(),
            "confidence": self.confidence.value,
            "source_url": self.source_url,
            "note": self.note,
            "is_sample": self.is_sample,
        }


@dataclass(frozen=True, slots=True)
class Sourced(Generic[T]):
    """A value that cannot be separated from its provenance."""

    value: T
    provenance: Provenance

    def __post_init__(self) -> None:
        if not isinstance(self.provenance, Provenance):
            raise MissingProvenanceError(
                f"value {self.value!r} was passed without a Provenance instance"
            )

    @property
    def is_sample(self) -> bool:
        return self.provenance.is_sample

    @property
    def confidence(self) -> Confidence:
        return self.provenance.confidence

    def map(self, fn) -> "Sourced":
        return Sourced(fn(self.value), self.provenance)

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.value, "provenance": self.provenance.to_dict()}


@dataclass(frozen=True, slots=True)
class EvidenceSet:
    """The provenance of every fact that fed a single decision or metric."""

    items: tuple[Provenance, ...] = field(default_factory=tuple)

    @classmethod
    def of(cls, *sources: Provenance | Sourced | None) -> "EvidenceSet":
        collected: list[Provenance] = []
        for item in sources:
            if item is None:
                continue
            if isinstance(item, Sourced):
                collected.append(item.provenance)
            elif isinstance(item, Provenance):
                collected.append(item)
            else:
                raise MissingProvenanceError(f"cannot build evidence from {type(item).__name__}")
        return cls(tuple(collected))

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    @property
    def is_sample(self) -> bool:
        return any(p.is_sample for p in self.items)

    @property
    def confidence(self) -> Confidence:
        """A decision is never more confident than its weakest supporting fact."""
        return Confidence.weakest(p.confidence for p in self.items)

    def merge(self, other: "EvidenceSet") -> "EvidenceSet":
        seen: dict[tuple[str, str], Provenance] = {}
        for p in (*self.items, *other.items):
            seen[(p.source, p.retrieved_at.isoformat())] = p
        return EvidenceSet(tuple(seen.values()))

    def to_list(self) -> list[dict[str, Any]]:
        return [p.to_dict() for p in self.items]


def require_provenance(value: Any, *, what: str = "value") -> Sourced:
    """Return ``value`` if it is :class:`Sourced`, otherwise refuse it."""
    if isinstance(value, Sourced):
        return value
    raise MissingProvenanceError(
        f"{what} must be a Sourced(...) carrying source + retrieved_at + confidence, "
        f"got a bare {type(value).__name__}"
    )


def reject_sample_data(evidence: EvidenceSet | Sourced | Provenance, *, what: str) -> None:
    """Refuse sample data where only a real measurement is acceptable."""
    if isinstance(evidence, Sourced):
        evidence = EvidenceSet.of(evidence)
    elif isinstance(evidence, Provenance):
        evidence = EvidenceSet.of(evidence)
    if evidence.is_sample:
        samples = sorted({p.source for p in evidence if p.is_sample})
        raise SampleDataError(f"{what} refuses sample data: {', '.join(samples)}")
