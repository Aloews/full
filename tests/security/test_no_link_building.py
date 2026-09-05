"""The backlink module classifies risk; it must never grow builder features."""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from kontur.engines.backlinks import risk as risk_module
from kontur.engines.backlinks.risk import RiskLevel, analyse_backlinks

pytestmark = pytest.mark.security

#: Verbs that would turn analysis into automation.
FORBIDDEN_VERBS = (
    "build_network", "create_network", "register_domain", "buy_link", "purchase_link",
    "place_link", "generate_pbn", "spin_content", "submit_link", "post_comment",
    "blast", "outreach_send", "auto_publish",
)


@pytest.mark.rule("LINK-001")
@pytest.mark.positive
def test_the_module_only_classifies(crawl_provenance) -> None:
    from datetime import date

    from kontur.engines.backlinks.risk import AnchorType, Backlink

    links = [
        Backlink(f"blog{i}.example", "/slots/", "подробнее", AnchorType.GENERIC, date(2026, 3, 1 + i % 27))
        for i in range(20)
    ]
    report = analyse_backlinks("https://casino.example/slots/", links, provenance=crawl_provenance)
    assert isinstance(report.level, RiskLevel)
    assert "does not build, buy or recommend" in report.to_dict()["scope"]


@pytest.mark.rule("LINK-001")
@pytest.mark.negative
def test_no_builder_shaped_function_exists() -> None:
    source = Path(inspect.getfile(risk_module)).read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    for name in names:
        lowered = name.lower()
        for verb in FORBIDDEN_VERBS:
            assert verb not in lowered, f"{name} looks like link automation, not analysis"


@pytest.mark.rule("LINK-001")
@pytest.mark.negative
def test_the_module_performs_no_network_io() -> None:
    source = Path(inspect.getfile(risk_module)).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {"requests", "httpx", "urllib", "socket", "smtplib", "ftplib", "selenium"}


@pytest.mark.rule("LINK-002")
@pytest.mark.positive
def test_commercial_anchor_concentration_raises_risk(crawl_provenance) -> None:
    from datetime import date

    from kontur.engines.backlinks.risk import AnchorType, Backlink

    def profile(anchor_type: AnchorType) -> float:
        links = [
            Backlink(
                f"site{i}.example",
                "/slots/",
                "казино онлайн" if anchor_type is AnchorType.COMMERCIAL else f"источник {i}",
                anchor_type,
                date(2026, 3, 1 + i % 27),
                ip_c_class=f"10.{i}.0",
            )
            for i in range(20)
        ]
        return analyse_backlinks("/slots/", links, provenance=crawl_provenance).score

    assert profile(AnchorType.COMMERCIAL) > profile(AnchorType.BRAND)


@pytest.mark.rule("LINK-003")
@pytest.mark.positive
def test_a_velocity_spike_raises_risk(crawl_provenance) -> None:
    from datetime import date, timedelta

    from kontur.engines.backlinks.risk import AnchorType, Backlink, velocity_factor

    steady = [
        Backlink(f"s{i}.example", "/x/", "a", AnchorType.BRAND, date(2026, 1, 1) + timedelta(days=i * 10))
        for i in range(18)
    ]
    spiky = [
        Backlink(f"b{i}.example", "/x/", "a", AnchorType.BRAND, date(2026, 1, 1))
        for i in range(40)
    ] + [
        Backlink(f"c{i}.example", "/x/", "a", AnchorType.BRAND, date(2026, 1, 1) + timedelta(days=40 + i * 30))
        for i in range(3)
    ]
    assert velocity_factor(spiky).value > velocity_factor(steady).value


def test_an_empty_profile_is_refused(crawl_provenance) -> None:
    from kontur.core.errors import InsufficientDataError

    with pytest.raises(InsufficientDataError):
        analyse_backlinks("/slots/", [], provenance=crawl_provenance)


def test_analysis_requires_provenance() -> None:
    from datetime import date

    from kontur.core.errors import ConfigurationError
    from kontur.engines.backlinks.risk import AnchorType, Backlink

    with pytest.raises(ConfigurationError, match="provenance"):
        analyse_backlinks(
            "/slots/",
            [Backlink("a.example", "/x/", "a", AnchorType.BRAND, date(2026, 1, 1))],
            provenance=None,
        )
