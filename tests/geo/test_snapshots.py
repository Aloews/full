"""Repeated measurement is what turns an observation into a finding."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from kontur.core.errors import ConfigurationError, InsufficientDataError
from kontur.engines.geo.models import AliceObservation, AliceSnapshot
from kontur.engines.geo.snapshots import (
    MIN_OBSERVATIONS_FOR_TREND,
    QueryTimeline,
    SnapshotStore,
    answer_volatility,
    assess_trend,
)

pytestmark = pytest.mark.geo

QUERY = "что такое megaways"


def _timeline(store: SnapshotStore) -> QueryTimeline:
    return store.timeline("casino.example", QUERY)


@pytest.mark.rule("GEO-003")
@pytest.mark.positive
def test_a_change_over_enough_weeks_is_reportable(snapshot_store: SnapshotStore) -> None:
    verdict = assess_trend(_timeline(snapshot_store))
    assert verdict.observations == 4
    assert verdict.reportable is True
    assert verdict.direction == "gained"
    assert "weekly observations" in verdict.explanation


@pytest.mark.rule("GEO-003")
@pytest.mark.negative
def test_a_single_snapshot_is_not_a_finding(alice_provenance) -> None:
    week = date(2026, 7, 6)
    store = SnapshotStore()
    store.add(
        AliceSnapshot(
            site="casino.example",
            week_start=week,
            observations=(AliceObservation(QUERY, week, alice_provenance, our_domain_mentioned=True),),
            provenance=alice_provenance,
        )
    )
    verdict = assess_trend(_timeline(store))
    assert verdict.reportable is False
    assert verdict.direction == "unknown"
    assert "Alice varies its answers" in verdict.explanation


@pytest.mark.rule("GEO-003")
@pytest.mark.negative
def test_a_volatile_source_set_blocks_attribution(alice_provenance) -> None:
    store = SnapshotStore()
    for index in range(4):
        week = date(2026, 7, 6) + (date(2026, 7, 13) - date(2026, 7, 6)) * index
        store.add(
            AliceSnapshot(
                site="casino.example",
                week_start=week,
                observations=(
                    AliceObservation(
                        QUERY,
                        week,
                        alice_provenance,
                        our_domain_mentioned=index >= 2,
                        competitor_domains=(f"rival-{index}.example", f"other-{index}.example"),
                    ),
                ),
                provenance=alice_provenance,
            )
        )
    verdict = assess_trend(_timeline(store))
    assert verdict.volatility is not None and verdict.volatility >= 0.8
    assert verdict.reportable is False
    assert "too volatile" in verdict.explanation


@pytest.mark.rule("GEO-003")
@pytest.mark.negative
def test_the_minimum_must_be_at_least_two(snapshot_store: SnapshotStore) -> None:
    with pytest.raises(ConfigurationError, match="min_observations"):
        assess_trend(_timeline(snapshot_store), min_observations=1)


def test_volatility_reflects_source_churn() -> None:
    assert answer_volatility([{"a", "b"}, {"a", "b"}, {"a", "b"}]) == 0.0
    assert answer_volatility([{"a"}, {"b"}, {"c"}]) == 1.0


def test_the_store_replaces_a_re_imported_week(snapshot_store: SnapshotStore, alice_provenance) -> None:
    before = len(snapshot_store.for_site("casino.example"))
    week = snapshot_store.for_site("casino.example")[0].week_start
    snapshot_store.add(
        AliceSnapshot(
            site="casino.example",
            week_start=week,
            observations=(AliceObservation(QUERY, week, alice_provenance),),
            provenance=alice_provenance,
        )
    )
    assert len(snapshot_store.for_site("casino.example")) == before
    assert len(snapshot_store.timeline("casino.example", QUERY)) == before


def test_the_window_keeps_the_most_recent_weeks(snapshot_store: SnapshotStore) -> None:
    window = snapshot_store.window("casino.example", weeks=2)
    assert len(window) == 2
    assert window[-1].week_start == max(s.week_start for s in snapshot_store.for_site("casino.example"))
    with pytest.raises(ConfigurationError):
        snapshot_store.window("casino.example", weeks=0)


def test_an_unknown_query_has_no_timeline(snapshot_store: SnapshotStore) -> None:
    with pytest.raises(InsufficientDataError, match="no observations"):
        snapshot_store.timeline("casino.example", "не отслеживаемый запрос")


def test_the_store_lists_its_sites_and_queries(snapshot_store: SnapshotStore) -> None:
    assert snapshot_store.sites() == ("casino.example",)
    assert QUERY in snapshot_store.queries("casino.example")


def test_only_objects_of_the_right_type_are_stored() -> None:
    with pytest.raises(ConfigurationError):
        SnapshotStore().add("not a snapshot")


def test_min_observations_default_is_documented() -> None:
    assert MIN_OBSERVATIONS_FOR_TREND >= 3


def test_volatility_of_an_empty_and_a_populated_snapshot_is_total() -> None:
    """Losing every source is a complete turnover, not a quiet zero."""
    assert answer_volatility([set(), {"a.example"}]) == 1.0
    assert answer_volatility([{"a.example"}, set()]) == 1.0
    assert answer_volatility([set(), set(), set()]) == 0.0


def test_an_unchanged_mention_rate_reads_as_flat(alice_provenance) -> None:
    store = SnapshotStore()
    for index in range(4):
        week = date(2026, 7, 6) + timedelta(weeks=index)
        store.add(
            AliceSnapshot(
                site="casino.example",
                week_start=week,
                observations=(
                    AliceObservation(
                        QUERY, week, alice_provenance,
                        our_domain_mentioned=True,
                        our_url_cited="https://casino.example/x/",
                        competitor_domains=("rival-one.example",),
                    ),
                ),
                provenance=alice_provenance,
            )
        )
    verdict = assess_trend(_timeline(store))
    assert verdict.direction == "flat"
    assert verdict.reportable is False


def test_the_window_defaults_to_twelve_weeks(alice_provenance) -> None:
    store = SnapshotStore()
    for index in range(14):
        week = date(2026, 5, 4) + timedelta(weeks=index)
        store.add(
            AliceSnapshot(
                site="casino.example",
                week_start=week,
                observations=(AliceObservation(QUERY, week, alice_provenance),),
                provenance=alice_provenance,
            )
        )
    assert len(store.window("casino.example")) == 12
    assert len(store.window("casino.example", weeks=1)) == 1


def test_volatile_queries_use_the_default_threshold(alice_provenance) -> None:
    """A query whose source set half turns over each week is reported by default."""
    store = SnapshotStore()
    sources = [("a.example", "b.example"), ("a.example", "c.example"), ("d.example", "e.example")]
    for index, competitors in enumerate(sources):
        week = date(2026, 7, 6) + timedelta(weeks=index)
        store.add(
            AliceSnapshot(
                site="casino.example",
                week_start=week,
                observations=(
                    AliceObservation(QUERY, week, alice_provenance, competitor_domains=competitors),
                ),
                provenance=alice_provenance,
            )
        )
    rows = store.volatile_queries("casino.example")
    assert [row["query"] for row in rows] == [QUERY]
    assert rows[0]["volatility"] >= 0.5
    assert store.volatile_queries("casino.example", threshold=0.99) == []


def test_single_observation_queries_are_skipped_not_crashed(snapshot_store, alice_provenance) -> None:
    week = date(2026, 8, 3)
    snapshot_store.add(
        AliceSnapshot(
            site="casino.example",
            week_start=week,
            observations=(AliceObservation("одноразовый запрос", week, alice_provenance),),
            provenance=alice_provenance,
        )
    )
    rows = snapshot_store.volatile_queries("casino.example", threshold=0.0)
    assert "одноразовый запрос" not in {row["query"] for row in rows}


def test_two_observations_are_enough_to_report_volatility(alice_provenance) -> None:
    store = SnapshotStore()
    for index, competitors in enumerate((("a.example", "b.example"), ("c.example", "d.example"))):
        week = date(2026, 7, 6) + timedelta(weeks=index)
        store.add(
            AliceSnapshot(
                site="casino.example",
                week_start=week,
                observations=(
                    AliceObservation(QUERY, week, alice_provenance, competitor_domains=competitors),
                ),
                provenance=alice_provenance,
            )
        )
    rows = store.volatile_queries("casino.example")
    assert [row["observations"] for row in rows] == [2]
    assert rows[0]["volatility"] == 1.0


def test_a_query_exactly_at_the_threshold_is_reported(alice_provenance) -> None:
    """The threshold is inclusive: at 0.50 the query is volatile enough to flag."""
    store = SnapshotStore()
    for index, competitors in enumerate((("a.example", "b.example"), ("a.example",))):
        week = date(2026, 7, 6) + timedelta(weeks=index)
        store.add(
            AliceSnapshot(
                site="casino.example",
                week_start=week,
                observations=(
                    AliceObservation(QUERY, week, alice_provenance, competitor_domains=competitors),
                ),
                provenance=alice_provenance,
            )
        )
    assert store.timeline("casino.example", QUERY).volatility() == pytest.approx(0.5)
    assert [row["query"] for row in store.volatile_queries("casino.example", threshold=0.5)] == [QUERY]


def test_blank_sources_are_filtered_not_crashed_on() -> None:
    """Exports contain blanks; a source list must survive them."""
    assert answer_volatility([{"a.example", "", None}, {"a.example"}]) == 0.0
    assert answer_volatility([{"  ", "a.example"}, {"b.example"}]) == 1.0


def test_two_observations_are_an_acceptable_minimum(snapshot_store) -> None:
    verdict = assess_trend(_timeline(snapshot_store), min_observations=2)
    assert verdict.observations == 4
    assert verdict.reportable is True
