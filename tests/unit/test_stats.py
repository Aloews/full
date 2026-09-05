"""The statistics behind experiment verdicts, checked against known values."""

from __future__ import annotations

import pytest

from kontur.core.errors import ConfigurationError, InsufficientDataError
from kontur.engines.experiment.stats import (
    bootstrap_ci,
    holm_bonferroni,
    normal_cdf,
    regularized_incomplete_beta,
    required_sample_size_proportions,
    student_t_sf,
    two_proportion_z_test,
    welch_t_test,
    z_quantile,
)

pytestmark = pytest.mark.unit


def test_normal_cdf_matches_reference_values() -> None:
    assert normal_cdf(0.0) == pytest.approx(0.5)
    assert normal_cdf(1.959963984540054) == pytest.approx(0.975, abs=1e-6)
    assert normal_cdf(-1.959963984540054) == pytest.approx(0.025, abs=1e-6)


def test_student_t_matches_reference_values() -> None:
    # Two-sided p for t=2.0 with 10 df is 0.073388 in any statistics table.
    assert 2 * student_t_sf(2.0, 10) == pytest.approx(0.073388, abs=1e-6)
    # The 95% two-sided critical value for 10 df is 2.228.
    assert 2 * student_t_sf(2.228, 10) == pytest.approx(0.05, abs=1e-3)
    assert student_t_sf(0.0, 10) == pytest.approx(0.5)


def test_incomplete_beta_edges() -> None:
    assert regularized_incomplete_beta(2, 3, 0.0) == 0.0
    assert regularized_incomplete_beta(2, 3, 1.0) == 1.0
    assert regularized_incomplete_beta(1, 1, 0.25) == pytest.approx(0.25)
    with pytest.raises(ConfigurationError):
        regularized_incomplete_beta(2, 3, 1.5)
    with pytest.raises(ConfigurationError):
        regularized_incomplete_beta(0, 3, 0.5)


def test_two_proportion_test_agrees_with_a_hand_calculation() -> None:
    result = two_proportion_z_test(
        control_successes=100, control_trials=1000, variant_successes=140, variant_trials=1000
    )
    assert result.estimate == pytest.approx(0.04)
    assert result.statistic == pytest.approx(2.7524, abs=1e-3)
    assert result.p_value == pytest.approx(0.00592, abs=1e-4)
    assert result.ci_low == pytest.approx(0.01157, abs=1e-4)
    assert result.ci_high == pytest.approx(0.06843, abs=1e-4)
    assert result.crosses_zero is False


def test_no_difference_gives_a_p_value_of_one() -> None:
    result = two_proportion_z_test(
        control_successes=100, control_trials=1000, variant_successes=100, variant_trials=1000
    )
    assert result.estimate == 0.0
    assert result.p_value == pytest.approx(1.0)
    assert result.crosses_zero is True


@pytest.mark.parametrize(
    "kwargs",
    [
        {"control_trials": 0},
        {"variant_trials": 0},
    ],
)
def test_empty_arms_are_refused(kwargs: dict) -> None:
    base = dict(
        control_successes=0, control_trials=10, variant_successes=0, variant_trials=10
    )
    with pytest.raises(InsufficientDataError):
        two_proportion_z_test(**{**base, **kwargs})


def test_successes_cannot_exceed_trials() -> None:
    with pytest.raises(ConfigurationError):
        two_proportion_z_test(
            control_successes=11, control_trials=10, variant_successes=1, variant_trials=10
        )


def test_welch_handles_unequal_variance() -> None:
    result = welch_t_test([1, 2, 3, 4, 5, 6], [3, 4, 5, 6, 7, 8])
    assert result.estimate == pytest.approx(2.0)
    assert result.p_value == pytest.approx(0.0938, abs=1e-3)
    with pytest.raises(InsufficientDataError):
        welch_t_test([1.0], [2.0, 3.0])


def test_identical_samples_produce_no_effect() -> None:
    result = welch_t_test([5, 5, 5, 5], [5, 5, 5, 5])
    assert result.estimate == 0.0
    assert result.p_value == 1.0


def test_bootstrap_is_deterministic() -> None:
    first = bootstrap_ci([1, 2, 3, 4, 5], [3, 4, 5, 6, 7], iterations=500)
    second = bootstrap_ci([1, 2, 3, 4, 5], [3, 4, 5, 6, 7], iterations=500)
    assert first == second, "a re-run of the same analysis must produce the same interval"
    assert first[0] <= first[1]
    with pytest.raises(ConfigurationError):
        bootstrap_ci([1, 2], [3, 4], iterations=10)
    with pytest.raises(InsufficientDataError):
        bootstrap_ci([], [1, 2])


@pytest.mark.rule("EXP-003")
@pytest.mark.positive
def test_holm_correction_raises_the_bar_for_multiple_metrics() -> None:
    adjusted = holm_bonferroni([0.01, 0.04, 0.03, 0.2])
    assert adjusted[0] == (pytest.approx(0.04), True)
    assert adjusted[1][1] is False, "0.04 is no longer significant among four comparisons"
    assert all(a[0] >= b for a, b in zip(adjusted, [0.01, 0.04, 0.03, 0.2], strict=True))


@pytest.mark.rule("EXP-003")
@pytest.mark.negative
def test_a_single_comparison_is_unchanged_by_correction() -> None:
    assert holm_bonferroni([0.01]) == [(pytest.approx(0.01), True)]
    assert holm_bonferroni([]) == []


@pytest.mark.rule("EXP-003")
@pytest.mark.negative
def test_invalid_p_values_are_refused() -> None:
    with pytest.raises(ConfigurationError):
        holm_bonferroni([1.5])
    with pytest.raises(ConfigurationError):
        holm_bonferroni([0.5], alpha=1.5)


def test_sample_size_matches_the_standard_formula() -> None:
    assert required_sample_size_proportions(baseline_rate=0.10, minimum_detectable_effect=0.02) == 3841
    bigger_effect = required_sample_size_proportions(baseline_rate=0.10, minimum_detectable_effect=0.05)
    assert bigger_effect < 3841, "a larger effect needs fewer units"
    with pytest.raises(ConfigurationError):
        required_sample_size_proportions(baseline_rate=1.0, minimum_detectable_effect=0.02)
    with pytest.raises(ConfigurationError):
        required_sample_size_proportions(baseline_rate=0.1, minimum_detectable_effect=0.0)
    with pytest.raises(ConfigurationError):
        required_sample_size_proportions(baseline_rate=0.1, minimum_detectable_effect=0.02, power=0.5)


def test_unsupported_confidence_is_refused() -> None:
    with pytest.raises(ConfigurationError):
        z_quantile(0.42)
