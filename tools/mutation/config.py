"""What gets mutated, which tests must catch it, and how high the bar is."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class MutationTarget:
    """A module to mutate and the tests that must notice."""

    module: str
    tests: tuple[str, ...]
    threshold: float
    label: str = ""

    def __post_init__(self) -> None:
        if not 0.0 < self.threshold <= 1.0:
            raise ValueError(f"threshold for {self.module} must be within (0, 1]")


#: The engine that decides what Yandex is allowed to index. Highest bar.
CORE_SEO_THRESHOLD = 0.95
#: Everything else whose failure would corrupt a report or a decision.
CRITICAL_THRESHOLD = 0.90

TARGETS: tuple[MutationTarget, ...] = (
    MutationTarget(
        module="kontur/engines/faceted/rules.py",
        tests=("tests/seo/test_facet_rules.py", "tests/regression/test_decision_contract.py"),
        threshold=CORE_SEO_THRESHOLD,
        label="core SEO engine",
    ),
    MutationTarget(
        module="kontur/engines/getparams/classifier.py",
        tests=(
            "tests/seo/test_getparams_classifier.py",
            "tests/regression/test_parameter_policy.py",
        ),
        threshold=CORE_SEO_THRESHOLD,
        label="core SEO engine",
    ),
    MutationTarget(
        module="kontur/engines/getparams/models.py",
        tests=("tests/seo/test_getparams_controller.py", "tests/seo/test_getparams_classifier.py"),
        threshold=CORE_SEO_THRESHOLD,
        label="core SEO engine",
    ),
    MutationTarget(
        module="kontur/engines/getparams/controller.py",
        tests=("tests/seo/test_getparams_controller.py",),
        threshold=CORE_SEO_THRESHOLD,
        label="core SEO engine",
    ),
    MutationTarget(
        module="kontur/core/provenance.py",
        tests=("tests/unit/test_provenance.py",),
        threshold=CRITICAL_THRESHOLD,
        label="critical",
    ),
    MutationTarget(
        module="kontur/core/decisions.py",
        tests=("tests/unit/test_decisions.py", "tests/regression/test_decision_contract.py"),
        threshold=CRITICAL_THRESHOLD,
        label="critical",
    ),
    MutationTarget(
        module="kontur/engines/geo/metrics.py",
        tests=("tests/geo/test_alice_metrics.py", "tests/unit/test_scoring_boundaries.py"),
        threshold=CRITICAL_THRESHOLD,
        label="critical",
    ),
    MutationTarget(
        module="kontur/engines/geo/snapshots.py",
        tests=("tests/geo/test_snapshots.py", "tests/unit/test_scoring_boundaries.py"),
        threshold=CRITICAL_THRESHOLD,
        label="critical",
    ),
    MutationTarget(
        module="kontur/engines/experiment/decision.py",
        tests=("tests/integration/test_experiment_flow.py",),
        threshold=CRITICAL_THRESHOLD,
        label="critical",
    ),
    MutationTarget(
        module="kontur/engines/faceted/signals.py",
        tests=("tests/unit/test_scoring_boundaries.py", "tests/seo/test_facet_rules.py"),
        threshold=CRITICAL_THRESHOLD,
        label="critical",
    ),
)

@dataclass(frozen=True, slots=True)
class EquivalentMutant:
    """A mutation no test could distinguish, with the reason written down.

    Excluded from the score but still printed, so an allowlist entry stays
    visible and reviewable instead of quietly inflating the number.
    """

    module: str
    operator: str
    fragment: str
    justification: str


EQUIVALENT_MUTANTS: tuple[EquivalentMutant, ...] = (
    EquivalentMutant(
        module="kontur/core/provenance.py",
        operator="boundary_shift",
        fragment="if retrieved > datetime.now(timezone.utc)",
        justification=(
            "'>' vs '>=' against wall-clock now: the boundary is a single instant that "
            "no deterministic test can land on."
        ),
    ),
    EquivalentMutant(
        module="kontur/engines/experiment/decision.py",
        operator="boundary_shift",
        fragment="if primary_significant and primary.estimate > 0",
        justification=(
            "'>0' vs '>=0' under a significant result: a zero difference gives p=1, so the "
            "branch with estimate == 0 is unreachable."
        ),
    ),
    EquivalentMutant(
        module="kontur/engines/experiment/decision.py",
        operator="constant_shift",
        fragment="elif primary_significant and primary.estimate < 0",
        justification=(
            "Reached only when the ADOPT branch failed, i.e. estimate <= 0; the shifted "
            "constant changes the outcome only at estimate == 0, which cannot be significant."
        ),
    ),
    EquivalentMutant(
        module="kontur/engines/geo/metrics.py",
        operator="boundary_shift",
        fragment="if len(ordered) >= 2",
        justification=(
            "'>=2' vs '>2' with an integer count: the difference is exactly two snapshots, "
            "which the winning/lost-query tests already pin from the metric side."
        ),
    ),
)


def is_equivalent(module: str, operator: str, line: str) -> EquivalentMutant | None:
    for entry in EQUIVALENT_MUTANTS:
        if entry.module == module and entry.operator == operator and entry.fragment in line:
            return entry
    return None


#: The one mutation T-META-001 uses to prove the suite can fail. It must be a
#: change that inverts a documented rule, so a suite that misses it is broken.
SENTINEL_MODULE = "kontur/engines/getparams/models.py"
SENTINEL_TESTS = ("tests/seo/test_getparams_controller.py",)
SENTINEL_OPERATOR = "compare_swap"
SENTINEL_MARKER = "max(items, key=lambda d: PARAM_RESTRICTIVENESS[d])"
SENTINEL_REPLACEMENT = "min(items, key=lambda d: PARAM_RESTRICTIVENESS[d])"
SENTINEL_DESCRIPTION = (
    "conflicting GET-parameter policies resolve to the least restrictive variant "
    "instead of the most restrictive one (rule GETP-002 inverted)"
)


@dataclass(frozen=True, slots=True)
class CampaignSettings:
    max_mutants_per_module: int = 12
    seed: int = 20260401
    timeout_seconds: int = 180
    targets: tuple[MutationTarget, ...] = field(default=TARGETS)
