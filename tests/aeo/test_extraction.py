"""Extraction readiness and the content model."""

from __future__ import annotations

import pytest

from kontur.engines.aeo.content import BlockKind, looks_like_question, parse_html, word_count
from kontur.engines.aeo.extraction import extraction_report, extraction_signals

pytestmark = pytest.mark.aeo

RICH = """<html><head><title>Megaways</title>
<script type="application/ld+json">{"@type":"FAQPage","mainEntity":[{"@type":"Question"}]}</script>
</head><body><h1>Что такое Megaways</h1>
<p>Megaways — это механика игровых автоматов с переменным числом символов на барабанах,
дающая до 117 649 способов выигрыша за спин при RTP около 96%.</p>
<h2>Как считается RTP?</h2><ul><li>96.5% в базовой игре</li><li>Бонусные покупки меняют RTP</li></ul>
<h2>Чем отличается от кластеров?</h2><ol><li>Барабаны</li></ol>
<table><tr><td>RTP</td><td>96.5%</td></tr></table></body></html>"""

BARE = "<html><body><h1>Megaways</h1><p>Коротко о механике.</p></body></html>"


@pytest.mark.rule("AEO-003")
@pytest.mark.positive
def test_structured_page_scores_high() -> None:
    page = parse_html(RICH, url="/slots/megaways/", target_query="что такое megaways")
    report = extraction_report(page, query="что такое megaways")
    assert report.score > 0.8
    assert report.gaps == ()
    assert report.signals.tables == 1
    assert report.signals.answer_schema_types >= 1


@pytest.mark.rule("AEO-003")
@pytest.mark.negative
def test_bare_page_scores_low_and_lists_its_gaps() -> None:
    page = parse_html(BARE, url="/slots/megaways/")
    report = extraction_report(page)
    assert report.score < 0.2
    assert "no comparison table" in report.gaps
    assert "no FAQ/QA structured data" in report.gaps


@pytest.mark.rule("AEO-003")
@pytest.mark.negative
def test_the_report_refuses_to_predict_citations() -> None:
    page = parse_html(RICH, url="/slots/megaways/")
    assert "does not predict" in extraction_report(page).to_dict()["caveat"]


def test_html_parsing_extracts_structure() -> None:
    page = parse_html(RICH, url="/slots/megaways/")
    assert page.title == "Megaways"
    assert page.h1 == "Что такое Megaways"
    assert page.tables == 1
    assert len(page.of_kind(BlockKind.LIST)) == 2
    assert "faqpage" in page.schema_types
    assert page.total_words > 30


def test_faq_schema_promotes_question_headings() -> None:
    page = parse_html(RICH, url="/slots/megaways/")
    assert len(page.of_kind(BlockKind.FAQ)) >= 2


def test_numeric_facts_are_counted() -> None:
    page = parse_html(RICH, url="/slots/megaways/")
    assert extraction_signals(page).numeric_facts >= 2


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Как работает механика?", True),
        ("что такое megaways", True),
        ("What is RTP", True),
        ("История механики", False),
        ("", False),
    ],
)
def test_question_detection(text: str, expected: bool) -> None:
    assert looks_like_question(text) is expected


def test_word_count_handles_cyrillic_and_punctuation() -> None:
    # Megaways/это/механика/дающая/117/649/способов — the dash is not a word and the
    # space-separated thousands group counts as two tokens.
    assert word_count("Megaways — это механика, дающая 117 649 способов.") == 7
    assert word_count("") == 0


def test_broken_json_ld_does_not_break_parsing() -> None:
    html = '<html><head><script type="application/ld+json">{oops</script></head><body><p>x</p></body></html>'
    assert parse_html(html, url="/x/").schema_types == frozenset()
