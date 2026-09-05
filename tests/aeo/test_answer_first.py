"""Answer-first assessment."""

from __future__ import annotations

import pytest

from kontur.engines.aeo.answer import (
    MIN_ANSWER_WORDS,
    answer_blocks,
    assess_answer_first,
    starts_with_filler,
)
from kontur.engines.aeo.content import parse_html

pytestmark = pytest.mark.aeo

GOOD = """<html><body><h1>Что такое Megaways</h1>
<p>Megaways — это механика игровых автоматов, при которой число символов на каждом барабане
меняется в каждом спине, из-за чего количество способов выигрыша достигает 117 649, а RTP
большинства релизов держится около 96%.</p>
<h2>Как работает механика?</h2><ul><li>Барабаны меняют высоту</li><li>Каскады</li></ul>
</body></html>"""

FILLER = """<html><body><h1>Megaways</h1>
<p>В современном мире слоты стали невероятно популярны, и это совершенно неудивительно,
ведь их выбор поистине огромен и продолжает расти каждый день без остановки.</p>
<p>Megaways — это механика с переменным числом символов на барабанах.</p></body></html>"""

BURIED = """<html><body><h1>Megaways</h1>
<h2>Оглавление</h2><ul><li>Что это</li></ul>
<h2>История</h2><ul><li>2016</li></ul><h2>Наконец</h2>
<p>Megaways — это механика игровых автоматов, при которой число символов на каждом барабане
меняется в каждом спине, что даёт до 117 649 способов выигрыша за один спин игры.</p>
</body></html>"""


@pytest.mark.rule("AEO-001")
@pytest.mark.positive
def test_a_direct_opening_answer_is_recognised() -> None:
    page = parse_html(GOOD, url="/slots/megaways/", target_query="что такое megaways")
    assessment = assess_answer_first(page)
    assert assessment.has_answer_first is True
    assert assessment.findings == ()
    assert assessment.word_count >= MIN_ANSWER_WORDS
    assert assessment.query_term_coverage == pytest.approx(1.0)


@pytest.mark.rule("AEO-001")
@pytest.mark.negative
def test_filler_opening_is_rejected() -> None:
    page = parse_html(FILLER, url="/slots/megaways/", target_query="megaways")
    assessment = assess_answer_first(page)
    assert assessment.has_answer_first is False
    assert assessment.filler_opening is True
    assert any("filler" in finding for finding in assessment.findings)


@pytest.mark.rule("AEO-001")
@pytest.mark.negative
def test_a_buried_answer_is_not_answer_first() -> None:
    page = parse_html(BURIED, url="/slots/megaways/", target_query="megaways")
    assessment = assess_answer_first(page)
    assert assessment.has_answer_first is False
    assert assessment.blocks_before_answer > 2
    assert any("block #" in finding for finding in assessment.findings)


@pytest.mark.rule("AEO-001")
@pytest.mark.negative
def test_a_page_without_paragraphs_has_nothing_to_lift() -> None:
    page = parse_html("<html><body><h1>Megaways</h1><ul><li>x</li></ul></body></html>", url="/x/")
    assessment = assess_answer_first(page)
    assert assessment.has_answer_first is False
    assert assessment.word_count == 0
    assert "nothing for an assistant to lift" in assessment.findings[0]


@pytest.mark.rule("AEO-001")
@pytest.mark.negative
def test_an_answer_that_ignores_the_query_is_flagged() -> None:
    page = parse_html(GOOD, url="/slots/megaways/", target_query="бонус за регистрацию промокод")
    assessment = assess_answer_first(page)
    assert assessment.has_answer_first is False
    assert assessment.query_term_coverage < 0.5


@pytest.mark.rule("AEO-001")
@pytest.mark.negative
def test_a_too_short_opening_is_flagged() -> None:
    page = parse_html("<html><body><h1>x</h1><p>Megaways — механика.</p></body></html>", url="/x/")
    assert assess_answer_first(page).has_answer_first is False


def test_stopwords_do_not_count_against_query_coverage() -> None:
    page = parse_html(GOOD, url="/slots/megaways/")
    assert assess_answer_first(page, query="что такое megaways").query_term_coverage == 1.0


@pytest.mark.parametrize(
    "text",
    ["В современном мире слоты...", "Как известно, RTP...", "In today's world, slots..."],
)
def test_filler_openings_are_detected(text: str) -> None:
    assert starts_with_filler(text) is True


def test_a_direct_definition_is_not_filler() -> None:
    assert starts_with_filler("Megaways — это механика игровых автоматов.") is False


def test_quotable_blocks_are_collected() -> None:
    page = parse_html(GOOD, url="/slots/megaways/")
    blocks = answer_blocks(page)
    assert len(blocks) >= 2
    assert any("Megaways" in block for block in blocks)


def test_recommendations_reference_a_hypothesis() -> None:
    page = parse_html(GOOD, url="/slots/megaways/", target_query="что такое megaways")
    ids = {r.hypothesis_id for r in assess_answer_first(page).recommendations}
    assert "H-002" in ids
