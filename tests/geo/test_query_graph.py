"""QUERY -> SERP -> ALICE AI ANSWER -> SOURCES -> OUR URL."""

from __future__ import annotations

from datetime import date

import pytest

from kontur.core.errors import ConfigurationError, InsufficientDataError, MissingProvenanceError
from kontur.graph.query_graph import GraphObservation, QueryAnswerGraph, build_graph

pytestmark = pytest.mark.geo

QUERY = "что такое megaways"


@pytest.fixture
def graph(alice_snapshots) -> QueryAnswerGraph:
    return build_graph("casino.example", alice_snapshots, serp_positions={QUERY: 4})


def test_the_graph_records_every_field_of_the_contract(graph: QueryAnswerGraph) -> None:
    row = graph.timeline(QUERY)[0].to_dict()
    for field in (
        "query", "date", "serp_position", "ai_answer_present", "our_domain_mentioned",
        "our_url_cited", "competitor_domains", "answer_type", "provenance",
    ):
        assert field in row, f"{field} missing from the observation contract"


def test_snapshots_are_kept_separately_not_collapsed(graph: QueryAnswerGraph) -> None:
    timeline = graph.timeline(QUERY)
    assert len(timeline) == 4
    assert [o.our_domain_mentioned for o in timeline] == [False, False, True, True]


def test_the_citation_path_shows_the_moment_we_appear(graph: QueryAnswerGraph) -> None:
    path = graph.citation_path(QUERY)
    assert path[0]["cited_url"] is None
    assert path[-1]["cited_url"] == "https://casino.example/slots/megaways/"
    assert path[-1]["serp_position"] == 4


def test_sources_and_competitors_are_aggregated(graph: QueryAnswerGraph) -> None:
    assert dict(graph.sources_for(QUERY))["rival-one.example"] == 4
    assert dict(graph.our_urls_for(QUERY))["https://casino.example/slots/megaways/"] == 2
    assert graph.competitors()[0][1] >= 4


def test_the_export_carries_the_variability_caveat(graph: QueryAnswerGraph) -> None:
    payload = graph.to_dict()
    assert payload["queries"] == 2
    assert payload["nodes"] and payload["edges"]
    assert "vary over time" in payload["caveat"]


def test_edges_are_typed(graph: QueryAnswerGraph) -> None:
    kinds = {edge.kind for edge in graph.edges()}
    assert {"answered_by", "cites", "cites_competitor", "ranks"} <= kinds


def test_re_ingesting_a_week_replaces_it(graph: QueryAnswerGraph, alice_provenance) -> None:
    before = len(graph.timeline(QUERY))
    graph.add(
        GraphObservation(
            query=QUERY,
            observed_on=graph.timeline(QUERY)[0].observed_on,
            provenance=alice_provenance,
            our_domain_mentioned=True,
        )
    )
    assert len(graph.timeline(QUERY)) == before


def test_observations_require_provenance() -> None:
    with pytest.raises(MissingProvenanceError):
        GraphObservation(query=QUERY, observed_on=date(2026, 7, 6), provenance=None)


def test_invalid_input_is_refused(alice_provenance) -> None:
    with pytest.raises(ConfigurationError):
        GraphObservation(query="  ", observed_on=date(2026, 7, 6), provenance=alice_provenance)
    with pytest.raises(ConfigurationError):
        GraphObservation(
            query=QUERY, observed_on=date(2026, 7, 6), provenance=alice_provenance, serp_position=0
        )
    with pytest.raises(ConfigurationError):
        QueryAnswerGraph(site="")
    with pytest.raises(ConfigurationError):
        QueryAnswerGraph(site="casino.example").add("nope")


def test_an_unseen_query_has_no_timeline(graph: QueryAnswerGraph) -> None:
    with pytest.raises(InsufficientDataError):
        graph.timeline("незнакомый запрос")
