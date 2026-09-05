"""SERP evidence: competitor matrix, gaps, information gain."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from kontur.core.errors import InsufficientDataError
from kontur.engines.serp.evidence import (
    competitor_matrix,
    content_gap,
    information_gain_score,
    opportunities,
    summarise_serp,
    token_matcher,
)
from kontur.engines.serp.models import CompetitorResult, PageProfile, SerpSnapshot

pytestmark = pytest.mark.seo


@pytest.fixture
def snapshot(crawl_provenance) -> SerpSnapshot:
    results = []
    for position in range(1, 7):
        results.append(
            CompetitorResult(
                domain=f"rival{position}.example",
                position=position,
                profile=PageProfile(
                    url=f"https://rival{position}.example/slots/megaways/",
                    title="Megaways слоты",
                    h1="Megaways",
                    word_count=800 + position * 20,
                    headings=("Что такое Megaways", "Список игр"),
                    questions=("Что такое megaways?",),
                    entities=frozenset({"rtp", "волатильность", "big time gaming"}),
                    tables=1 if position <= 4 else 0,
                    internal_links=30,
                    schema_types=frozenset({"itemlist"}) if position <= 4 else frozenset(),
                    last_modified=datetime(2026, 6, 1, tzinfo=UTC),
                ),
            )
        )
    return SerpSnapshot(
        query="megaways слоты",
        captured_at=datetime(2026, 8, 1, tzinfo=UTC),
        results=tuple(results),
        provenance=crawl_provenance,
    )


def test_the_summary_captures_the_serp_consensus(snapshot: SerpSnapshot) -> None:
    summary = summarise_serp(snapshot, dedicated=token_matcher("megaways"))
    assert summary.competitors_analysed == 6
    assert summary.dedicated_pages == 6
    assert summary.has_dedicated_pages is True
    assert "rtp" in summary.common_entities
    assert summary.table_share == pytest.approx(4 / 6)


def test_an_empty_serp_yields_an_empty_summary(crawl_provenance) -> None:
    empty = SerpSnapshot(
        query="никто не ранжируется",
        captured_at=datetime(2026, 8, 1, tzinfo=UTC),
        results=(),
        provenance=crawl_provenance,
    )
    summary = summarise_serp(empty)
    assert summary.competitors_analysed == 0
    assert summary.has_dedicated_pages is False


def test_the_gap_lists_what_the_serp_has_and_we_do_not(snapshot: SerpSnapshot) -> None:
    summary = summarise_serp(snapshot)
    ours = PageProfile(url="/slots/megaways/", word_count=400, entities=frozenset({"rtp"}))
    gap = content_gap(ours, summary)
    assert "волатильность" in gap.missing_entities
    assert "что такое megaways?" in gap.missing_questions
    assert gap.missing_table is True
    assert gap.missing_schema is True
    assert gap.word_count_delta < 0
    assert gap.is_empty is False


def test_a_complete_page_has_no_gap(snapshot: SerpSnapshot) -> None:
    summary = summarise_serp(snapshot)
    ours = PageProfile(
        url="/slots/megaways/",
        word_count=1000,
        headings=("Что такое Megaways", "Список игр"),
        questions=("Что такое megaways?",),
        entities=frozenset({"rtp", "волатильность", "big time gaming"}),
        tables=1,
        schema_types=frozenset({"itemlist"}),
    )
    assert content_gap(ours, summary).is_empty is True


def test_information_gain_rewards_what_the_serp_lacks(snapshot: SerpSnapshot) -> None:
    summary = summarise_serp(snapshot)
    plain = PageProfile(url="/a/", entities=frozenset({"rtp"}))
    richer = PageProfile(
        url="/b/",
        entities=frozenset({"rtp", "hit frequency", "max win", "bonus buy", "ways to win", "provider"}),
        questions=("Сколько стоит бонусная покупка?", "Какой максимальный выигрыш?", "Что такое hit rate?"),
    )
    assert information_gain_score(richer, summary) > information_gain_score(plain, summary)


def test_a_gap_needs_competitors(crawl_provenance) -> None:
    empty = SerpSnapshot(
        query="q",
        captured_at=datetime(2026, 8, 1, tzinfo=UTC),
        results=(),
        provenance=crawl_provenance,
    )
    summary = summarise_serp(empty)
    with pytest.raises(InsufficientDataError):
        content_gap(PageProfile(url="/a/"), summary)


def test_the_matrix_has_one_row_per_competitor(snapshot: SerpSnapshot) -> None:
    matrix = competitor_matrix(snapshot, dedicated=token_matcher("megaways"))
    assert len(matrix.rows) == 6
    assert matrix.rows[0]["position"] == 1
    assert matrix.rows[0]["dedicated"] is True
    assert matrix.rows[0]["freshness_days"] is not None


def test_opportunities_are_actions_not_promises(snapshot: SerpSnapshot) -> None:
    summary = summarise_serp(snapshot)
    ours = PageProfile(url="/slots/megaways/", word_count=400, entities=frozenset())
    actions = opportunities(content_gap(ours, summary))
    assert actions
    assert all("%" not in action for action in actions)
    assert any("comparison table" in action for action in actions)


def test_results_are_sorted_by_position(snapshot: SerpSnapshot) -> None:
    assert [r.position for r in snapshot.results] == sorted(r.position for r in snapshot.results)
    assert snapshot.top(3)[-1].position == 3


def test_a_token_matcher_needs_tokens() -> None:
    from kontur.core.errors import ConfigurationError

    with pytest.raises(ConfigurationError):
        token_matcher("  ")
