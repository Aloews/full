"""Crawled strings are attacker-controlled input, not trusted content."""

from __future__ import annotations

import pytest

from kontur.dashboard.render import render_ai_visibility, render_decisions, render_parameters

pytestmark = pytest.mark.security

PAYLOAD = "<script>alert('xss')</script>"
ATTRIBUTE_PAYLOAD = '"><img src=x onerror=alert(1)>'


@pytest.mark.rule("SEC-001")
@pytest.mark.positive
def test_parameter_names_are_escaped() -> None:
    html = render_parameters(
        [
            {
                "parameter": PAYLOAD,
                "detected_urls": 1,
                "decision": "EXCLUDE",
                "reason": ATTRIBUTE_PAYLOAD,
                "confidence": "low",
            }
        ]
    )
    assert PAYLOAD not in html
    assert "&lt;script&gt;" in html
    # The payload survives as inert text; what matters is that no tag is opened.
    assert "<img" not in html
    assert "&lt;img" in html


@pytest.mark.rule("SEC-001")
@pytest.mark.positive
def test_urls_and_reasons_in_the_decision_table_are_escaped() -> None:
    html = render_decisions(
        [
            {
                "url": f"/slots/?q={PAYLOAD}",
                "decision": "CANONICAL",
                "reason": [PAYLOAD],
                "rules": ["FACET-001"],
                "canonical_target": ATTRIBUTE_PAYLOAD,
                "confidence": "high",
            }
        ]
    )
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


@pytest.mark.rule("SEC-001")
@pytest.mark.positive
def test_query_text_from_the_alice_export_is_escaped() -> None:
    report = {
        "site": "casino.example",
        "window": {"start": "2026-07-06", "end": "2026-07-27"},
        "share_of_voice": 0.1,
        "mention_rate": 0.2,
        "queries_analysed": 1,
        "cited_urls": [{"url": f"https://x/{PAYLOAD}", "citations": 1}],
        "competitors": [{"domain": PAYLOAD, "queries": 1, "share": 1.0, "co_cited_with_us": 0, "overlap": 0.0}],
        "winning_queries": [PAYLOAD],
        "lost_queries": [],
        "confidence": "high",
        "is_sample": False,
    }
    html = render_ai_visibility(report, [{"query": PAYLOAD, "observations": 3, "volatility": 0.9}])
    assert "<script>" not in html
    assert html.count("&lt;script&gt;") >= 4


@pytest.mark.rule("SEC-001")
@pytest.mark.negative
def test_ordinary_text_is_not_mangled() -> None:
    html = render_parameters(
        [
            {
                "parameter": "utm_source",
                "detected_urls": 48210,
                "decision": "EXCLUDE",
                "reason": "tracking",
                "confidence": "high",
            }
        ]
    )
    assert "utm_source" in html
    assert "tracking" in html
    assert "48 210" in html, "large numbers stay readable"


@pytest.mark.rule("SEC-001")
@pytest.mark.negative
def test_a_decision_tag_cannot_inject_a_class_break() -> None:
    html = render_parameters(
        [
            {
                "parameter": "x",
                "detected_urls": 1,
                "decision": '"><script>alert(1)</script>',
                "reason": "y",
                "confidence": "low",
            }
        ]
    )
    assert "<script>" not in html


def test_the_sample_banner_is_rendered_only_when_asked() -> None:
    rows = [{"parameter": "x", "detected_urls": 1, "decision": "EXCLUDE", "reason": "y", "confidence": "low"}]
    assert "SAMPLE DATA" in render_parameters(rows, sample=True)
    assert "SAMPLE DATA" not in render_parameters(rows, sample=False)


def test_empty_tables_render_without_crashing() -> None:
    assert "no data" in render_parameters([])
