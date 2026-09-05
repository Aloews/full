"""The artefacts a webmaster actually applies."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from kontur.core.errors import ConfigurationError
from kontur.engines.getparams.export import (
    CLEAN_PARAM_MAX_LENGTH,
    build_export,
    clean_param_directives,
    parse_clean_param_directives,
    robots_block,
    robots_disallow_directives,
)

pytestmark = pytest.mark.seo


@pytest.mark.rule("GETP-008")
@pytest.mark.positive
def test_the_export_is_deterministic(controller) -> None:
    stamp = datetime(2026, 8, 20, tzinfo=UTC)
    first = build_export(controller.rulings(), generated_at=stamp).to_json()
    second = build_export(controller.rulings(), generated_at=stamp).to_json()
    assert first == second, "the same rulings must produce byte-identical output"


@pytest.mark.rule("GETP-008")
@pytest.mark.positive
def test_clean_param_directives_round_trip() -> None:
    params = ["utm_source", "utm_medium", "sort", "gclid"]
    lines = clean_param_directives(params, "/slots/")
    parsed = parse_clean_param_directives(lines)
    assert parsed["/slots/"] == set(params)


@pytest.mark.rule("GETP-008")
@pytest.mark.positive
def test_long_parameter_lists_are_chunked() -> None:
    params = [f"param_number_{index:03d}" for index in range(80)]
    lines = clean_param_directives(params)
    assert len(lines) > 1
    assert all(len(line) <= CLEAN_PARAM_MAX_LENGTH for line in lines)
    assert parse_clean_param_directives(lines)["/"] == set(params)


@pytest.mark.rule("GETP-008")
@pytest.mark.negative
def test_an_empty_parameter_list_produces_no_directives() -> None:
    assert clean_param_directives([]) == []
    assert clean_param_directives(["", "  "]) == []
    assert robots_disallow_directives([]) == []


@pytest.mark.rule("GETP-008")
@pytest.mark.negative
def test_a_relative_path_is_refused() -> None:
    with pytest.raises(ConfigurationError, match="must start with"):
        clean_param_directives(["sort"], "slots/")


def test_the_export_splits_parameters_by_intent(controller) -> None:
    payload = build_export(controller.rulings()).to_dict()
    assert "utm_source" in payload["exclude"]
    assert "phpsessid" in payload["exclude"]
    assert "phpsessid" in payload["blocked_from_crawling"]
    assert "mechanic" in payload["consider"]
    assert "page" in payload["consider"]
    assert "rtp" in payload["review"]
    assert payload["tool"] == "yandex_webmaster.get_parameters"


def test_pending_parameters_are_never_in_the_consider_list(controller) -> None:
    payload = build_export(controller.rulings()).to_dict()
    assert set(payload["review"]).isdisjoint(payload["consider"])


def test_robots_block_covers_blocked_and_excluded_parameters(controller) -> None:
    block = robots_block(controller.rulings())
    assert "User-agent: Yandex" in block
    assert "Disallow: /*?*phpsessid=" in block
    assert "Clean-param:" in block
    assert "utm_source" in block


def test_sample_data_is_flagged_in_the_export(sample_provenance) -> None:
    from kontur.engines.getparams.classifier import classify_parameter
    from kontur.engines.getparams.models import ParamObservation

    ruling = classify_parameter(ParamObservation("utm_source", 10, 2, sample_provenance))
    assert build_export([ruling]).to_dict()["contains_sample_data"] is True
