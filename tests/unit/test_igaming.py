"""The iGaming page-type taxonomy."""

from __future__ import annotations

import pytest

from kontur.core.errors import ConfigurationError
from kontur.engines.igaming.taxonomy import (
    PAGE_TYPES,
    Intent,
    PageType,
    check_completeness,
    classify_url,
    spec_for,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("/slots/", PageType.CATEGORY),
        ("/slots/megaways/", PageType.MECHANIC),
        ("/mechanics/cluster-pays/", PageType.MECHANIC),
        ("/slots/pragmatic/gates-of-olympus/", PageType.GAME),
        ("/providers/pragmatic/", PageType.PROVIDER),
        ("/bonuses/welcome/", PageType.BONUS),
        ("/rtp/", PageType.RTP),
        ("/volatility/", PageType.VOLATILITY),
        ("/jackpots/mega/", PageType.JACKPOT),
        ("/reviews/casino-x/", PageType.REVIEW),
        ("/compare/pragmatic-vs-novomatic/", PageType.COMPARISON),
        ("/blog/kak-rabotaet-rtp/", PageType.INFORMATIONAL),
        ("/register/", PageType.COMMERCIAL),
        ("/nothing/like/this/at/all/", PageType.UNKNOWN),
    ],
)
def test_url_classification(url: str, expected: PageType) -> None:
    assert classify_url(url) is expected


def test_query_strings_do_not_change_the_page_type() -> None:
    assert classify_url("/slots/megaways/?utm_source=vk") is PageType.MECHANIC


def test_a_path_without_a_leading_slash_still_classifies() -> None:
    assert classify_url("slots/") is PageType.CATEGORY


def test_every_specification_declares_its_intent_and_requirements() -> None:
    for page_type, spec in PAGE_TYPES.items():
        assert spec.page_type is page_type
        assert isinstance(spec.intent, Intent)
        assert spec.url_patterns, f"{page_type} matches nothing"
        assert spec.to_dict()["page_type"] == page_type.value


def test_conversion_surfaces_are_not_indexable_by_default() -> None:
    assert spec_for(PageType.COMMERCIAL).indexable_by_default is False
    assert spec_for(PageType.MECHANIC).indexable_by_default is True


def test_an_unknown_page_type_is_refused() -> None:
    with pytest.raises(ConfigurationError):
        spec_for(PageType.UNKNOWN)


def test_completeness_lists_what_a_page_is_missing() -> None:
    report = check_completeness(
        "/slots/megaways/", present_blocks=["definition", "game_grid"], schema_types=["itemlist"]
    )
    assert report.page_type is PageType.MECHANIC
    assert report.is_complete is False
    assert set(report.missing_blocks) == {"how_it_works", "comparison_table", "faq"}
    assert report.missing_schema == ("faqpage",)
    assert report.findings


def test_a_complete_page_reports_no_gaps() -> None:
    report = check_completeness(
        "/slots/megaways/",
        present_blocks=["definition", "how_it_works", "game_grid", "comparison_table", "faq"],
        schema_types=["faqpage", "itemlist"],
    )
    assert report.is_complete is True
    assert report.to_dict()["complete"] is True


def test_an_unclassifiable_url_says_so() -> None:
    report = check_completeness("/no/such/section/here/", present_blocks=[], schema_types=[])
    assert report.page_type is PageType.UNKNOWN
    assert "does not match any known" in report.findings[0]


def test_the_page_type_can_be_forced() -> None:
    report = check_completeness(
        "/custom/landing/", present_blocks=["verdict"], schema_types=[], page_type=PageType.REVIEW
    )
    assert report.page_type is PageType.REVIEW
    assert "methodology" in report.missing_blocks


def test_a_review_must_name_its_author_and_method() -> None:
    required = set(spec_for(PageType.REVIEW).required_blocks)
    assert {"author", "methodology"} <= required


def test_an_rtp_page_must_show_its_methodology() -> None:
    assert "methodology" in spec_for(PageType.RTP).required_blocks
