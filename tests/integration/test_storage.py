"""Persistence keeps provenance attached."""

from __future__ import annotations

import pytest

from kontur.core.decisions import Decision
from kontur.storage.sqlite import KonturStore, open_store

pytestmark = pytest.mark.integration


@pytest.fixture
def store() -> KonturStore:
    with KonturStore() as instance:
        yield instance


def test_param_observations_round_trip(store: KonturStore, controller, observation) -> None:
    observations = [observation("utm_source", 48210, 137), observation("sort", 12440, 6)]
    assert store.save_param_observations(observations) == 2
    loaded = store.load_param_observations()
    assert [o.name for o in loaded] == ["utm_source", "sort"]
    assert loaded[0].provenance.source == "crawl:site_audit"
    assert loaded[0].provenance.confidence.value == "high"


def test_re_importing_the_same_export_does_not_duplicate(store: KonturStore, observation) -> None:
    store.save_param_observations([observation("sort", 12440, 6)])
    store.save_param_observations([observation("sort", 12440, 6)])
    assert store.counts()["param_observations"] == 1


def test_decisions_round_trip(store: KonturStore, facet_engine) -> None:
    records = facet_engine().decide_many(["/slots/?mechanic=megaways", "/slots/?rtp=96plus"])
    assert store.save_decisions(records) == 2
    loaded = store.load_decisions()
    by_url = {row["url"]: row for row in loaded}
    assert by_url["/slots/?mechanic=megaways"]["decision"] == Decision.INDEX.value
    assert by_url["/slots/?rtp=96plus"]["canonical_target"] == "/slots/"
    assert by_url["/slots/?mechanic=megaways"]["reason"]


def test_decisions_can_be_filtered_by_url(store: KonturStore, facet_engine) -> None:
    store.save_decisions(facet_engine().decide_many(["/slots/?mechanic=megaways", "/slots/?rtp=96plus"]))
    assert len(store.load_decisions(url="/slots/?rtp=96plus")) == 1


def test_alice_snapshots_round_trip(store: KonturStore, alice_snapshots) -> None:
    for snapshot in alice_snapshots:
        store.save_alice_snapshot(snapshot)
    loaded = store.load_alice_snapshots("casino.example")
    assert len(loaded) == len(alice_snapshots)
    assert loaded[0].week_start == alice_snapshots[0].week_start
    assert loaded[-1].observations[0].provenance.source == "yandex_webmaster:alice_visibility"
    assert loaded[0].reported_share_of_voice == pytest.approx(0.10)


def test_reloaded_snapshots_still_produce_a_report(store: KonturStore, alice_snapshots) -> None:
    from kontur.engines.geo.metrics import build_report

    for snapshot in alice_snapshots:
        store.save_alice_snapshot(snapshot)
    report = build_report(store.load_alice_snapshots("casino.example"), require_real_data=True)
    assert report.queries_analysed == 2
    assert report.is_sample is False


def test_an_unknown_site_returns_nothing(store: KonturStore) -> None:
    assert store.load_alice_snapshots("unknown.example") == []


def test_counts_report_every_table(store: KonturStore) -> None:
    assert set(store.counts()) == {"param_observations", "decisions", "alice_observations"}


def test_a_file_backed_store_persists(tmp_path, observation) -> None:
    path = tmp_path / "kontur.sqlite"
    with open_store(path) as first:
        first.save_param_observations([observation("sort", 12440, 6)])
    with open_store(path) as second:
        assert [o.name for o in second.load_param_observations()] == ["sort"]
