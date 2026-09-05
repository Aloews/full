"""AI visibility metrics from the Alice export."""

from __future__ import annotations

from datetime import date

import pytest

from kontur.core.errors import (
    ConfigurationError,
    InsufficientDataError,
    MissingProvenanceError,
    SampleDataError,
)
from kontur.engines.geo.metrics import (
    build_report,
    cited_urls,
    competitor_overlap,
    lost_queries,
    mention_rate,
    query_coverage,
    share_of_voice,
    winning_queries,
)
from kontur.engines.geo.models import AliceObservation, AliceSnapshot, QuerySet

pytestmark = pytest.mark.geo


@pytest.mark.rule("GEO-001")
@pytest.mark.positive
def test_a_sourced_export_produces_a_report(alice_snapshots) -> None:
    report = build_report(alice_snapshots)
    assert report.site == "casino.example"
    assert report.queries_analysed == 2
    assert 0.0 <= report.share_of_voice <= 1.0
    assert report.evidence.is_sample is False
    assert report.to_dict()["confidence"] == "high"


@pytest.mark.rule("GEO-001")
@pytest.mark.negative
def test_an_observation_without_provenance_is_refused() -> None:
    with pytest.raises(MissingProvenanceError, match="source \\+ retrieval date \\+ confidence"):
        AliceObservation(query="что такое megaways", week_start=date(2026, 7, 6), provenance=None)


@pytest.mark.rule("GEO-001")
@pytest.mark.negative
def test_a_snapshot_without_provenance_is_refused() -> None:
    with pytest.raises(MissingProvenanceError):
        AliceSnapshot(site="casino.example", week_start=date(2026, 7, 6), observations=(), provenance=None)


@pytest.mark.rule("GEO-002")
@pytest.mark.positive
def test_sample_backed_reports_carry_a_warning(sample_provenance) -> None:
    week = date(2026, 7, 6)
    snapshot = AliceSnapshot(
        site="casino.example",
        week_start=week,
        observations=(
            AliceObservation("что такое megaways", week, sample_provenance, our_domain_mentioned=True),
        ),
        provenance=sample_provenance,
    )
    payload = build_report([snapshot]).to_dict()
    assert payload["is_sample"] is True
    assert "SAMPLE DATA" in payload["warning"]


@pytest.mark.rule("GEO-002")
@pytest.mark.negative
def test_sample_data_cannot_be_requested_as_a_measurement(sample_provenance) -> None:
    week = date(2026, 7, 6)
    snapshot = AliceSnapshot(
        site="casino.example",
        week_start=week,
        observations=(AliceObservation("q", week, sample_provenance),),
        provenance=sample_provenance,
    )
    with pytest.raises(SampleDataError, match="real measurements"):
        build_report([snapshot], require_real_data=True)


@pytest.mark.rule("GEO-002")
@pytest.mark.negative
def test_real_data_passes_the_measurement_gate(alice_snapshots) -> None:
    report = build_report(alice_snapshots, require_real_data=True)
    assert report.is_sample is False
    assert "warning" not in report.to_dict()


@pytest.mark.rule("GEO-004")
@pytest.mark.positive
def test_coverage_is_measured_against_the_declared_query_set(alice_snapshots) -> None:
    tracked = QuerySet("core", frozenset({"что такое megaways", "слоты с покупкой бонуса", "rtp слотов"}))
    report = build_report(alice_snapshots, query_set=tracked)
    assert report.query_coverage == pytest.approx(1 / 3)


@pytest.mark.rule("GEO-004")
@pytest.mark.negative
def test_queries_outside_the_export_contribute_nothing(alice_provenance) -> None:
    week = date(2026, 7, 6)
    observations = [
        AliceObservation("a", week, alice_provenance, our_domain_mentioned=True, competitor_domains=("x.ru",))
    ]
    assert share_of_voice(observations) == pytest.approx(0.5)
    with pytest.raises(InsufficientDataError):
        share_of_voice([])
    with pytest.raises(InsufficientDataError):
        query_coverage(observations, QuerySet("empty", frozenset()))


@pytest.mark.rule("GEO-005")
@pytest.mark.positive
def test_winning_and_lost_queries_need_two_snapshots(alice_snapshots) -> None:
    won = winning_queries(alice_snapshots[1], alice_snapshots[2])
    assert won == ["что такое megaways"]
    assert lost_queries(alice_snapshots[2], alice_snapshots[3]) == []


@pytest.mark.rule("GEO-005")
@pytest.mark.negative
def test_a_delta_needs_ordered_comparable_snapshots(alice_snapshots) -> None:
    with pytest.raises(ConfigurationError, match="must precede"):
        winning_queries(alice_snapshots[2], alice_snapshots[1])
    with pytest.raises(ConfigurationError, match="different sites"):
        other = AliceSnapshot(
            site="other.example",
            week_start=alice_snapshots[3].week_start,
            observations=alice_snapshots[3].observations,
            provenance=alice_snapshots[3].provenance,
        )
        winning_queries(alice_snapshots[0], other)


def test_answered_queries_drive_the_mention_rate(alice_snapshots) -> None:
    observations = [o for s in alice_snapshots for o in s.observations]
    assert mention_rate(observations) == pytest.approx(2 / 8)


def test_cited_urls_are_ranked(alice_snapshots) -> None:
    observations = [o for s in alice_snapshots for o in s.observations]
    urls = cited_urls(observations)
    assert urls == [("https://casino.example/slots/megaways/", 2)]


def test_competitor_overlap_reports_co_citation(alice_snapshots) -> None:
    observations = [o for s in alice_snapshots for o in s.observations]
    rows = competitor_overlap(observations)
    by_domain = {row["domain"]: row for row in rows}
    assert by_domain["rival-one.example"]["queries"] == 8
    assert by_domain["rival-one.example"]["co_cited_with_us"] == 2


def test_reports_of_different_sites_cannot_be_merged(alice_snapshots) -> None:
    other = AliceSnapshot(
        site="other.example",
        week_start=alice_snapshots[0].week_start,
        observations=alice_snapshots[0].observations,
        provenance=alice_snapshots[0].provenance,
    )
    with pytest.raises(ConfigurationError, match="different sites"):
        build_report([alice_snapshots[0], other])


def test_empty_input_is_refused() -> None:
    with pytest.raises(InsufficientDataError):
        build_report([])


def test_snapshot_rejects_observations_from_another_week(alice_provenance) -> None:
    with pytest.raises(ConfigurationError, match="other weeks"):
        AliceSnapshot(
            site="casino.example",
            week_start=date(2026, 7, 6),
            observations=(AliceObservation("q", date(2026, 7, 13), alice_provenance),),
            provenance=alice_provenance,
        )


def test_a_cited_url_implies_a_mention(alice_provenance) -> None:
    observation = AliceObservation(
        "q", date(2026, 7, 6), alice_provenance, our_url_cited="https://casino.example/x/"
    )
    assert observation.our_domain_mentioned is True
    assert observation.sources[0] == "casino.example"


def test_share_of_voice_is_zero_when_no_answer_was_shown(alice_provenance) -> None:
    week = date(2026, 7, 6)
    silent = [
        AliceObservation("q1", week, alice_provenance, ai_answer_present=False,
                         competitor_domains=("a.example",)),
        AliceObservation("q2", week, alice_provenance, ai_answer_present=False,
                         our_domain_mentioned=True),
    ]
    assert share_of_voice(silent) == 0.0
    assert mention_rate(silent) == 0.0


def test_a_competitor_never_seen_with_us_reports_zero_overlap(alice_provenance) -> None:
    week = date(2026, 7, 6)
    observations = [
        AliceObservation("q1", week, alice_provenance, our_domain_mentioned=False,
                         competitor_domains=("solo.example",)),
    ]
    row = competitor_overlap(observations)[0]
    assert row["domain"] == "solo.example"
    assert row["co_cited_with_us"] == 0
    assert row["overlap"] == 0.0


def test_two_snapshots_of_the_same_week_cannot_be_compared(alice_snapshots) -> None:
    same_week = AliceSnapshot(
        site=alice_snapshots[0].site,
        week_start=alice_snapshots[0].week_start,
        observations=alice_snapshots[0].observations,
        provenance=alice_snapshots[0].provenance,
    )
    with pytest.raises(ConfigurationError, match="must precede"):
        winning_queries(alice_snapshots[0], same_week)


def test_a_delta_needs_at_least_one_shared_query(alice_provenance) -> None:
    first = AliceSnapshot(
        site="casino.example",
        week_start=date(2026, 7, 6),
        observations=(AliceObservation("query one", date(2026, 7, 6), alice_provenance),),
        provenance=alice_provenance,
    )
    second = AliceSnapshot(
        site="casino.example",
        week_start=date(2026, 7, 13),
        observations=(AliceObservation("query two", date(2026, 7, 13), alice_provenance),),
        provenance=alice_provenance,
    )
    with pytest.raises(InsufficientDataError, match="share no queries"):
        winning_queries(first, second)


def test_a_query_new_to_the_export_can_be_won(alice_provenance) -> None:
    """A query absent from the earlier snapshot was not previously ours."""
    before = AliceSnapshot(
        site="casino.example",
        week_start=date(2026, 7, 6),
        observations=(
            AliceObservation("shared query", date(2026, 7, 6), alice_provenance, our_domain_mentioned=True),
        ),
        provenance=alice_provenance,
    )
    after = AliceSnapshot(
        site="casino.example",
        week_start=date(2026, 7, 13),
        observations=(
            AliceObservation("shared query", date(2026, 7, 13), alice_provenance, our_domain_mentioned=True),
            AliceObservation("brand new query", date(2026, 7, 13), alice_provenance, our_domain_mentioned=True),
        ),
        provenance=alice_provenance,
    )
    assert winning_queries(before, after) == ["brand new query"]


def test_the_payload_rounds_share_of_voice_to_four_decimals(alice_provenance) -> None:
    week = date(2026, 7, 6)
    observations = tuple(
        AliceObservation(
            f"q{index}", week, alice_provenance,
            our_domain_mentioned=index == 0,
            competitor_domains=("a.example", "b.example"),
        )
        for index in range(3)
    )
    snapshot = AliceSnapshot("casino.example", week, observations, alice_provenance)
    report = build_report([snapshot])
    assert report.share_of_voice == pytest.approx(1 / 7)
    assert report.to_dict()["share_of_voice"] == round(1 / 7, 4)


def test_the_report_compares_the_two_most_recent_snapshots(alice_provenance) -> None:
    def snapshot(week: date, mentioned: bool) -> AliceSnapshot:
        return AliceSnapshot(
            site="casino.example",
            week_start=week,
            observations=(
                AliceObservation("что такое megaways", week, alice_provenance, our_domain_mentioned=mentioned),
            ),
            provenance=alice_provenance,
        )

    # absent, present, absent -> the latest transition is a loss, not a win.
    report = build_report(
        [
            snapshot(date(2026, 7, 6), False),
            snapshot(date(2026, 7, 13), True),
            snapshot(date(2026, 7, 20), False),
        ]
    )
    assert report.lost_queries == ("что такое megaways",)
    assert report.winning_queries == ()


def test_two_snapshots_are_enough_for_a_delta(alice_provenance) -> None:
    def snapshot(week: date, mentioned: bool) -> AliceSnapshot:
        return AliceSnapshot(
            site="casino.example",
            week_start=week,
            observations=(AliceObservation("q", week, alice_provenance, our_domain_mentioned=mentioned),),
            provenance=alice_provenance,
        )

    report = build_report([snapshot(date(2026, 7, 6), False), snapshot(date(2026, 7, 13), True)])
    assert report.winning_queries == ("q",)
