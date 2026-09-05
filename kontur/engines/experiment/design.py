"""Experiment design: arms, units, guardrails, pre-registration.

An experiment is declared *before* it runs: metric, minimum sample, horizon and
guardrails. Assignment is a deterministic hash of (experiment id, unit id), so
re-running the analysis never reshuffles the arms (rule EXP-004).
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any

from kontur.core.claims import HYPOTHESES
from kontur.core.errors import ConfigurationError


class ExperimentUnit(StrEnum):
    """What gets randomised."""

    URL = "url"
    QUERY = "query"
    SECTION = "section"
    TEMPLATE = "template"


class GuardrailDirection(StrEnum):
    NOT_BELOW = "not_below"
    NOT_ABOVE = "not_above"


@dataclass(frozen=True, slots=True)
class Arm:
    name: str
    is_control: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ConfigurationError("arm name is required")
        object.__setattr__(self, "name", self.name.strip().lower())


@dataclass(frozen=True, slots=True)
class Guardrail:
    """A metric that must not degrade, whatever the primary metric does."""

    metric: str
    direction: GuardrailDirection
    threshold: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "direction", GuardrailDirection(self.direction))

    def breached_by(self, value: float) -> bool:
        if self.direction is GuardrailDirection.NOT_BELOW:
            return value < self.threshold
        return value > self.threshold

    def to_dict(self) -> dict[str, Any]:
        return {"metric": self.metric, "direction": self.direction.value, "threshold": self.threshold}


@dataclass(frozen=True, slots=True)
class Experiment:
    """A pre-registered experiment."""

    id: str
    hypothesis_id: str
    unit: ExperimentUnit
    primary_metric: str
    arms: tuple[Arm, ...]
    min_sample_per_arm: int
    starts_on: date
    ends_on: date
    guardrails: tuple[Guardrail, ...] = ()
    confidence: float = 0.95
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ConfigurationError("experiment id is required")
        object.__setattr__(self, "unit", ExperimentUnit(self.unit))
        if self.hypothesis_id not in HYPOTHESES:
            raise ConfigurationError(
                f"experiment {self.id} references unknown hypothesis {self.hypothesis_id!r}"
            )
        if len(self.arms) < 2:
            raise ConfigurationError("an experiment needs at least a control and one variant")
        controls = [a for a in self.arms if a.is_control]
        if len(controls) != 1:
            raise ConfigurationError("exactly one arm must be marked as the control")
        if len({a.name for a in self.arms}) != len(self.arms):
            raise ConfigurationError("arm names must be unique")
        if self.min_sample_per_arm < 1:
            raise ConfigurationError("min_sample_per_arm must be >= 1")
        for value in (self.starts_on, self.ends_on):
            if isinstance(value, datetime):
                raise ConfigurationError("use dates, not datetimes, for the experiment horizon")
        if self.ends_on <= self.starts_on:
            raise ConfigurationError("ends_on must be after starts_on")

    @property
    def control(self) -> Arm:
        return next(a for a in self.arms if a.is_control)

    @property
    def variants(self) -> tuple[Arm, ...]:
        return tuple(a for a in self.arms if not a.is_control)

    @property
    def arm_names(self) -> tuple[str, ...]:
        return tuple(a.name for a in self.arms)

    def is_running(self, on: date) -> bool:
        return self.starts_on <= on <= self.ends_on

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "hypothesis_id": self.hypothesis_id,
            "unit": self.unit.value,
            "primary_metric": self.primary_metric,
            "arms": [{"name": a.name, "is_control": a.is_control, "description": a.description} for a in self.arms],
            "min_sample_per_arm": self.min_sample_per_arm,
            "starts_on": self.starts_on.isoformat(),
            "ends_on": self.ends_on.isoformat(),
            "guardrails": [g.to_dict() for g in self.guardrails],
            "confidence": self.confidence,
            "notes": self.notes,
        }


def assign_arm(experiment: Experiment, unit_id: str) -> str:
    """Deterministically map a unit to an arm (rule EXP-004)."""
    if not unit_id or not unit_id.strip():
        raise ConfigurationError("unit_id is required for assignment")
    digest = hashlib.sha256(f"{experiment.id}:{unit_id.strip().lower()}".encode()).digest()
    bucket = int.from_bytes(digest[:8], "big") % len(experiment.arms)
    return experiment.arms[bucket].name


def assign_all(experiment: Experiment, unit_ids: Iterable[str]) -> dict[str, str]:
    return {unit_id: assign_arm(experiment, unit_id) for unit_id in unit_ids}


def assignment_balance(assignments: dict[str, str], arms: Sequence[str]) -> dict[str, float]:
    """Share of units per arm — used to catch a broken split before analysing."""
    total = len(assignments) or 1
    counts = {arm: 0 for arm in arms}
    for arm in assignments.values():
        counts[arm] = counts.get(arm, 0) + 1
    return {arm: count / total for arm, count in counts.items()}


@dataclass
class ExperimentRegistry:
    """All declared experiments, keyed by id."""

    experiments: dict[str, Experiment] = field(default_factory=dict)

    def register(self, experiment: Experiment) -> ExperimentRegistry:
        if experiment.id in self.experiments:
            raise ConfigurationError(f"experiment {experiment.id} is already registered")
        self.experiments[experiment.id] = experiment
        return self

    def get(self, experiment_id: str) -> Experiment:
        try:
            return self.experiments[experiment_id]
        except KeyError as exc:
            raise ConfigurationError(f"unknown experiment {experiment_id!r}") from exc

    def for_hypothesis(self, hypothesis_id: str) -> list[Experiment]:
        return [e for e in self.experiments.values() if e.hypothesis_id == hypothesis_id]
