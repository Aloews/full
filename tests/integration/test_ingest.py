"""Importers refuse data that cannot say where it came from."""

from __future__ import annotations

import json
from datetime import date

import pytest

from kontur.core.errors import ConfigurationError, MissingProvenanceError
from kontur.core.provenance import Confidence
from kontur.ingest.imports import (
    import_alice_visibility,
    import_param_demand,
    import_param_observations,
    import_serp_positions,
    load_manifest,
    provenance_from_manifest,
    read_csv,
    write_csv,
)

pytestmark = pytest.mark.integration

MANIFEST = {
    "source": "yandex_webmaster:alice_visibility",
    "retrieved_at": "2026-08-24",
    "confidence": "high",
    "source_url": "https://webmaster.yandex.ru/",
}


@pytest.mark.rule("DATA-001")
@pytest.mark.positive
def test_a_complete_manifest_produces_provenance() -> None:
    provenance = provenance_from_manifest(MANIFEST)
    assert provenance.source == "yandex_webmaster:alice_visibility"
    assert provenance.confidence is Confidence.HIGH
    assert provenance.is_sample is False


@pytest.mark.rule("DATA-001")
@pytest.mark.negative
@pytest.mark.parametrize("missing", ["source", "retrieved_at", "confidence"])
def test_an_incomplete_manifest_is_refused(missing: str) -> None:
    manifest = {k: v for k, v in MANIFEST.items() if k != missing}
    with pytest.raises(MissingProvenanceError, match=missing):
        provenance_from_manifest(manifest)


@pytest.mark.rule("DATA-001")
@pytest.mark.negative
@pytest.mark.parametrize(
    "importer",
    [import_param_observations, import_param_demand, import_serp_positions],
)
def test_importers_refuse_to_run_without_provenance(importer) -> None:
    with pytest.raises(MissingProvenanceError):
        importer([], provenance=None)


@pytest.mark.rule("DATA-001")
@pytest.mark.negative
def test_the_alice_importer_refuses_to_run_without_provenance() -> None:
    with pytest.raises(MissingProvenanceError, match="not admissible"):
        import_alice_visibility([], site="casino.example", provenance=None)


def test_param_observations_import_from_rows(crawl_provenance) -> None:
    rows = [
        {"parameter": "utm_source", "detected_urls": "48210", "distinct_values": "137"},
        {"parameter": "sort", "detected_urls": "12 440", "distinct_values": "6", "sample_values": "asc|desc"},
    ]
    observations = import_param_observations(rows, provenance=crawl_provenance)
    assert [o.name for o in observations] == ["utm_source", "sort"]
    assert observations[1].detected_urls == 12440
    assert observations[1].sample_values == ("asc", "desc")
    assert observations[0].provenance is crawl_provenance


def test_a_missing_column_names_the_row(crawl_provenance) -> None:
    with pytest.raises(ConfigurationError, match="parameter row 1"):
        import_param_observations([{"parameter": "sort"}], provenance=crawl_provenance)


def test_demand_is_aggregated_per_parameter(demand_provenance) -> None:
    rows = [
        {"parameter": "mechanic", "value": "megaways", "monthly_demand": "3200"},
        {"parameter": "mechanic", "value": "cluster", "monthly_demand": "1100"},
        {"parameter": "mechanic", "value": "hold", "monthly_demand": "0"},
    ]
    demand = import_param_demand(rows, provenance=demand_provenance)
    stats = demand["mechanic"].value
    assert stats.total_monthly_demand == 4300.0
    assert stats.values_with_demand == 2
    assert stats.top_values[0] == ("megaways", 3200.0)


def test_alice_import_groups_rows_into_weekly_snapshots(alice_provenance) -> None:
    rows = [
        {
            "query": "что такое megaways",
            "week": "2026-07-06",
            "ai_answer": "yes",
            "our_domain_mentioned": "no",
            "competitors": "rival-one.example|rival-two.example",
            "answer_type": "generated",
            "serp_position": "4",
            "impressions": "120",
        },
        {
            "query": "что такое megaways",
            "week": "2026-07-13",
            "our_domain_mentioned": "yes",
            "our_url": "https://casino.example/slots/megaways/",
            "competitors": "rival-one.example",
        },
    ]
    result = import_alice_visibility(rows, site="casino.example", provenance=alice_provenance)
    assert result.rows == 2
    assert result.weeks() == (date(2026, 7, 6), date(2026, 7, 13))
    assert result.snapshots[1].observations[0].our_domain_mentioned is True


def test_alice_import_attaches_the_reported_share_of_voice(alice_provenance) -> None:
    rows = [{"query": "q", "week": "2026-07-06"}]
    result = import_alice_visibility(
        rows,
        site="casino.example",
        provenance=alice_provenance,
        reported_share_of_voice={"2026-07-06": 0.12},
    )
    assert result.snapshots[0].reported_share_of_voice == 0.12


def test_an_empty_alice_export_is_refused(alice_provenance) -> None:
    with pytest.raises(ConfigurationError, match="no rows"):
        import_alice_visibility([], site="casino.example", provenance=alice_provenance)


def test_csv_round_trip(tmp_path, crawl_provenance) -> None:
    path = tmp_path / "params.csv"
    write_csv(
        path,
        [{"parameter": "utm_source", "detected_urls": 48210, "distinct_values": 137}],
        columns=["parameter", "detected_urls", "distinct_values"],
    )
    observations = import_param_observations(read_csv(path), provenance=crawl_provenance)
    assert observations[0].detected_urls == 48210


def test_manifest_is_loaded_from_disk(tmp_path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(MANIFEST), encoding="utf-8")
    assert load_manifest(path).source == "yandex_webmaster:alice_visibility"


def test_serp_positions_import(crawl_provenance) -> None:
    positions = import_serp_positions(
        [{"query": "Что Такое Megaways", "position": "4"}], provenance=crawl_provenance
    )
    assert positions == {"что такое megaways": 4}
