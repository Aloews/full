"""Ingest -> engines -> decisions -> report -> storage, in one pass."""

from __future__ import annotations

from datetime import date

import pytest

from kontur.core.provenance import Sourced
from kontur.engines.faceted.models import FilterInventory
from kontur.engines.faceted.signals import (
    BusinessValue,
    IntentAssessment,
    IntentLabel,
    SearchDemand,
)
from kontur.engines.geo.models import QuerySet
from kontur.graph.query_graph import build_graph
from kontur.ingest.imports import (
    import_alice_visibility,
    import_param_demand,
    import_param_observations,
    import_serp_positions,
)
from kontur.storage.sqlite import KonturStore
from kontur.workspace import Workspace

pytestmark = pytest.mark.e2e

CRAWL_ROWS = [
    {"parameter": "utm_source", "detected_urls": "48210", "distinct_values": "137"},
    {"parameter": "sort", "detected_urls": "12440", "distinct_values": "6"},
    {"parameter": "page", "detected_urls": "9100", "distinct_values": "64"},
    {"parameter": "provider", "detected_urls": "4812", "distinct_values": "48"},
    {"parameter": "mechanic", "detected_urls": "1290", "distinct_values": "22"},
    {"parameter": "rtp", "detected_urls": "840", "distinct_values": "9"},
    {"parameter": "phpsessid", "detected_urls": "380", "distinct_values": "380"},
]

DEMAND_ROWS = [
    {"parameter": "mechanic", "value": "megaways", "monthly_demand": "3200"},
    {"parameter": "mechanic", "value": "cluster", "monthly_demand": "1100"},
    {"parameter": "mechanic", "value": "hold-and-win", "monthly_demand": "900"},
    {"parameter": "provider", "value": "pragmatic", "monthly_demand": "12000"},
    {"parameter": "provider", "value": "novomatic", "monthly_demand": "4400"},
    {"parameter": "provider", "value": "playson", "monthly_demand": "1800"},
    {"parameter": "rtp", "value": "96plus", "monthly_demand": "40"},
]

ALICE_ROWS = [
    {
        "query": "что такое megaways",
        "week": week,
        "ai_answer": "yes",
        "our_domain_mentioned": mentioned,
        "our_url": "https://casino.example/slots/?mechanic=megaways" if mentioned == "yes" else "",
        "competitors": "rival-one.example|rival-two.example",
        "answer_type": "generated",
    }
    for week, mentioned in (
        ("2026-07-06", "no"),
        ("2026-07-13", "no"),
        ("2026-07-20", "yes"),
        ("2026-07-27", "yes"),
    )
]


def test_a_full_pass_from_exports_to_a_persisted_report(
    crawl_provenance, demand_provenance, alice_provenance, tmp_path
) -> None:
    # ---- ingest ---------------------------------------------------------
    observations = import_param_observations(CRAWL_ROWS, provenance=crawl_provenance)
    demand = import_param_demand(DEMAND_ROWS, provenance=demand_provenance)
    alice = import_alice_visibility(ALICE_ROWS, site="casino.example", provenance=alice_provenance)
    positions = import_serp_positions(
        [{"query": "что такое megaways", "position": "4"}], provenance=crawl_provenance
    )

    # ---- workspace ------------------------------------------------------
    workspace = Workspace(site="casino.example")
    workspace.load_parameters(observations, demand)
    workspace.load_alice(alice.snapshots)
    workspace.serp_positions = positions
    workspace.tracked_queries = QuerySet("core", frozenset({"что такое megaways", "rtp слотов"}))
    workspace.filter_states = {
        "/slots/?mechanic=megaways": {
            "demand": Sourced(SearchDemand(3200.0, 46, "megaways слоты"), demand_provenance),
            "intent": IntentAssessment(IntentLabel.COMMERCIAL, 0.22, 0.71),
            "inventory": Sourced(FilterInventory(84, 71, 3, pages=4), crawl_provenance),
            "business": Sourced(BusinessValue(70, 84, 0.62), crawl_provenance),
        }
    }

    # ---- indexation -----------------------------------------------------
    urls = [
        "/slots/?mechanic=megaways",
        "/slots/?mechanic=megaways&utm_source=vk",
        "/slots/?mechanic=megaways&sort=popular",
        "/slots/?mechanic=megaways&page=1",
        "/slots/?rtp=96plus",
        "/slots/?phpsessid=abc",
    ]
    decisions = {d["url"]: d for d in workspace.decide(urls)}
    assert decisions["/slots/?mechanic=megaways"]["decision"] == "INDEX"
    assert decisions["/slots/?mechanic=megaways&utm_source=vk"]["decision"] == "CANONICAL"
    assert decisions["/slots/?mechanic=megaways&sort=popular"]["decision"] == "CANONICAL"
    assert decisions["/slots/?mechanic=megaways&page=1"]["decision"] == "CANONICAL"
    assert decisions["/slots/?rtp=96plus"]["decision"] == "CANONICAL"
    assert decisions["/slots/?phpsessid=abc"]["decision"] == "BLOCK"
    assert all(d["reason"] for d in decisions.values())
    assert all(d["is_sample"] is False for d in decisions.values())

    # ---- parameter export ----------------------------------------------
    export = workspace.parameter_export()
    assert "utm_source" in export["exclude"]
    assert "mechanic" in export["consider"]
    assert "provider" in export["consider"]
    assert "rtp" in export["review"]
    assert export["contains_sample_data"] is False

    # ---- AI visibility --------------------------------------------------
    report = workspace.ai_visibility(require_real_data=True)
    assert report.window_start == date(2026, 7, 6)
    assert report.window_end == date(2026, 7, 27)
    assert report.mention_rate == pytest.approx(0.5)
    assert report.cited_urls[0][0] == "https://casino.example/slots/?mechanic=megaways"
    assert report.winning_queries == ()

    # ---- graph ----------------------------------------------------------
    graph = build_graph("casino.example", alice.snapshots, serp_positions=positions)
    path = graph.citation_path("что такое megaways")
    assert [step["mentioned"] for step in path] == [False, False, True, True]
    assert path[-1]["serp_position"] == 4

    # ---- persistence ----------------------------------------------------
    with KonturStore(tmp_path / "kontur.sqlite") as store:
        store.save_param_observations(observations)
        store.save_decisions(workspace.engine.decide_many(urls))
        for snapshot in alice.snapshots:
            store.save_alice_snapshot(snapshot)
        counts = store.counts()

    assert counts == {"param_observations": 7, "decisions": 6, "alice_observations": 4}


def test_the_indexable_set_is_small_and_justified(workspace) -> None:
    urls = [
        "/slots/?mechanic=megaways",
        "/slots/?mechanic=megaways&utm_source=vk",
        "/slots/?rtp=96plus",
        "/slots/?mechanic=megaways&provider=pragmatic&theme=egypt",
    ]
    summary = workspace.indexation_summary(urls)
    assert summary["by_decision"]["INDEX"] == 1
    assert summary["total"] == 4
    for record in workspace.engine.decide_many(urls):
        assert record.rule_ids, f"{record.url} was decided without naming a rule"
