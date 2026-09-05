"""From a pre-registered experiment to a verdict."""

from __future__ import annotations

from datetime import date

import pytest

from kontur.core.errors import ConfigurationError
from kontur.engines.experiment.decision import (
    ArmResult,
    ExperimentAnalysis,
    Verdict,
    evaluate,
)
from kontur.engines.experiment.design import (
    Arm,
    Experiment,
    ExperimentRegistry,
    ExperimentUnit,
    Guardrail,
    GuardrailDirection,
    assign_all,
    assign_arm,
    assignment_balance,
)

pytestmark = pytest.mark.integration


@pytest.fixture
def experiment() -> Experiment:
    return Experiment(
        id="EXP-12",
        hypothesis_id="H-001",
        unit=ExperimentUnit.URL,
        primary_metric="cited_url_rate",
        arms=(Arm("control", is_control=True), Arm("answer_first")),
        min_sample_per_arm=300,
        starts_on=date(2026, 6, 1),
        ends_on=date(2026, 7, 15),
        guardrails=(Guardrail("indexed_share", GuardrailDirection.NOT_BELOW, 0.95),),
    )


@pytest.mark.rule("EXP-001")
@pytest.mark.positive
def test_a_powered_experiment_produces_a_verdict(experiment: Experiment) -> None:
    verdict = evaluate(
        ExperimentAnalysis(
            experiment,
            [ArmResult("control", 90, 900), ArmResult("answer_first", 140, 910)],
            {"indexed_share": 0.99},
        )
    )
    assert verdict.verdict is Verdict.ADOPT
    assert verdict.claim is not None
    assert verdict.claim.experiment_id == "EXP-12"
    assert "95% CI" in verdict.claim.statement()


@pytest.mark.rule("EXP-001")
@pytest.mark.negative
def test_an_underpowered_experiment_is_inconclusive_not_a_win(experiment: Experiment) -> None:
    verdict = evaluate(
        ExperimentAnalysis(
            experiment,
            [ArmResult("control", 9, 90), ArmResult("answer_first", 30, 91)],
            {"indexed_share": 0.99},
        )
    )
    assert verdict.verdict is Verdict.INCONCLUSIVE
    assert verdict.claim is None
    assert "below the pre-registered minimum" in verdict.reasons[0]


@pytest.mark.rule("EXP-002")
@pytest.mark.positive
def test_a_breached_guardrail_rejects_a_winning_variant(experiment: Experiment) -> None:
    verdict = evaluate(
        ExperimentAnalysis(
            experiment,
            [ArmResult("control", 90, 900), ArmResult("answer_first", 140, 910)],
            {"indexed_share": 0.80},
        )
    )
    assert verdict.verdict is Verdict.REJECT
    assert verdict.guardrail_breaches
    assert verdict.claim is None


@pytest.mark.rule("EXP-002")
@pytest.mark.negative
def test_an_unmeasured_guardrail_cannot_be_cleared(experiment: Experiment) -> None:
    verdict = evaluate(
        ExperimentAnalysis(
            experiment, [ArmResult("control", 90, 900), ArmResult("answer_first", 140, 910)], {}
        )
    )
    assert verdict.verdict is Verdict.REJECT
    assert "not measured" in verdict.guardrail_breaches[0]


@pytest.mark.rule("EXP-004")
@pytest.mark.positive
def test_assignment_is_deterministic_and_balanced(experiment: Experiment) -> None:
    units = [f"/slots/page-{index}/" for index in range(1000)]
    first = assign_all(experiment, units)
    second = assign_all(experiment, units)
    assert first == second, "a re-run must not reshuffle the arms"
    balance = assignment_balance(first, experiment.arm_names)
    assert all(0.45 <= share <= 0.55 for share in balance.values())


@pytest.mark.rule("EXP-004")
@pytest.mark.negative
def test_assignment_refuses_an_empty_unit(experiment: Experiment) -> None:
    with pytest.raises(ConfigurationError):
        assign_arm(experiment, "")


@pytest.mark.rule("EXP-004")
@pytest.mark.negative
def test_two_experiments_do_not_share_an_assignment(experiment: Experiment) -> None:
    other = Experiment(
        id="EXP-13",
        hypothesis_id="H-001",
        unit=ExperimentUnit.URL,
        primary_metric="cited_url_rate",
        arms=experiment.arms,
        min_sample_per_arm=300,
        starts_on=experiment.starts_on,
        ends_on=experiment.ends_on,
    )
    units = [f"/slots/page-{index}/" for index in range(200)]
    differing = sum(1 for unit in units if assign_arm(experiment, unit) != assign_arm(other, unit))
    assert differing > 50, "different experiments must randomise independently"


def test_a_worse_variant_is_rejected(experiment: Experiment) -> None:
    verdict = evaluate(
        ExperimentAnalysis(
            experiment,
            [ArmResult("control", 200, 900), ArmResult("answer_first", 90, 910)],
            {"indexed_share": 0.99},
        )
    )
    assert verdict.verdict is Verdict.REJECT
    assert "significantly worse" in " ".join(verdict.reasons)


def test_multiple_metrics_are_corrected(experiment: Experiment) -> None:
    analysis = ExperimentAnalysis(
        experiment,
        [ArmResult("control", 90, 900), ArmResult("answer_first", 112, 910)],
        {"indexed_share": 0.99},
        secondary_results=[
            ("mention_rate", ArmResult("control", 40, 900), ArmResult("answer_first", 48, 910)),
            ("query_coverage", ArmResult("control", 20, 900), ArmResult("answer_first", 24, 910)),
        ],
    )
    verdict = evaluate(analysis)
    assert "EXP-003" in verdict.rule_ids
    assert "Holm-adjusted" in verdict.reasons[0]
    assert len(verdict.secondary) == 2


def test_experiment_declaration_is_validated() -> None:
    base = dict(
        id="EXP-99",
        hypothesis_id="H-001",
        unit=ExperimentUnit.URL,
        primary_metric="m",
        min_sample_per_arm=10,
        starts_on=date(2026, 6, 1),
        ends_on=date(2026, 7, 1),
    )
    with pytest.raises(ConfigurationError, match="at least a control"):
        Experiment(**base, arms=(Arm("only", is_control=True),))
    with pytest.raises(ConfigurationError, match="exactly one arm"):
        Experiment(**base, arms=(Arm("a"), Arm("b")))
    with pytest.raises(ConfigurationError, match="unknown hypothesis"):
        Experiment(**{**base, "hypothesis_id": "H-404"}, arms=(Arm("a", is_control=True), Arm("b")))
    with pytest.raises(ConfigurationError, match="ends_on"):
        Experiment(
            **{**base, "ends_on": date(2026, 5, 1)}, arms=(Arm("a", is_control=True), Arm("b"))
        )


def test_the_registry_rejects_duplicates(experiment: Experiment) -> None:
    registry = ExperimentRegistry().register(experiment)
    assert registry.get("EXP-12") is experiment
    assert registry.for_hypothesis("H-001") == [experiment]
    with pytest.raises(ConfigurationError, match="already registered"):
        registry.register(experiment)
    with pytest.raises(ConfigurationError, match="unknown experiment"):
        registry.get("EXP-404")


def test_arm_results_are_validated() -> None:
    with pytest.raises(ConfigurationError):
        ArmResult("control", 10, 5)
    with pytest.raises(ConfigurationError):
        ArmResult("control", -1, 5)


def test_an_arm_with_no_trials_yet_is_valid() -> None:
    """A freshly started arm has zero of everything; that is not a data error."""
    empty = ArmResult("control", 0, 0)
    assert empty.rate == 0.0


def test_every_trial_converting_is_valid() -> None:
    perfect = ArmResult("variant", 50, 50)
    assert perfect.rate == 1.0


@pytest.mark.rule("EXP-002")
@pytest.mark.negative
def test_a_worse_but_insignificant_variant_is_inconclusive(experiment: Experiment) -> None:
    verdict = evaluate(
        ExperimentAnalysis(
            experiment,
            [ArmResult("control", 100, 900), ArmResult("answer_first", 95, 910)],
            {"indexed_share": 0.99},
        )
    )
    assert verdict.verdict is Verdict.INCONCLUSIVE
    assert verdict.primary is not None and verdict.primary.estimate < 0
    assert verdict.claim is None


def test_two_comparisons_already_trigger_the_correction(experiment: Experiment) -> None:
    analysis = ExperimentAnalysis(
        experiment,
        [ArmResult("control", 90, 900), ArmResult("answer_first", 140, 910)],
        {"indexed_share": 0.99},
        secondary_results=[
            ("mention_rate", ArmResult("control", 40, 900), ArmResult("answer_first", 48, 910)),
        ],
    )
    assert "EXP-003" in evaluate(analysis).rule_ids


def test_a_single_comparison_records_no_correction(experiment: Experiment) -> None:
    analysis = ExperimentAnalysis(
        experiment,
        [ArmResult("control", 90, 900), ArmResult("answer_first", 140, 910)],
        {"indexed_share": 0.99},
    )
    assert "EXP-003" not in evaluate(analysis).rule_ids


@pytest.mark.rule("EXP-001")
@pytest.mark.positive
def test_arms_exactly_at_the_minimum_are_powered_enough(experiment: Experiment) -> None:
    """The pre-registered minimum is inclusive: 300 units is 300 units."""
    verdict = evaluate(
        ExperimentAnalysis(
            experiment,
            [ArmResult("control", 30, 300), ArmResult("answer_first", 33, 300)],
            {"indexed_share": 0.99},
        )
    )
    assert verdict.verdict is not Verdict.INCONCLUSIVE or "minimum" not in verdict.reasons[0]
    assert verdict.primary is not None, "an arm at the minimum must be analysed, not skipped"
