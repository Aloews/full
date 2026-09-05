"""Ingest bounds: oversized and malformed input fails at the door."""

from __future__ import annotations

import pytest

from kontur.core.errors import ConfigurationError
from kontur.ingest.validation import (
    MAX_IDENTIFIER_LENGTH,
    MAX_QUERY_LENGTH,
    clean_identifier,
    clean_query,
    clean_text,
    parse_bool,
    parse_date,
    parse_float,
    parse_int,
    require_columns,
    split_list,
)

pytestmark = pytest.mark.security


@pytest.mark.rule("SEC-003")
@pytest.mark.positive
def test_ordinary_identifiers_pass() -> None:
    assert clean_identifier(" utm_source ", field="parameter") == "utm_source"
    assert clean_query("  Что   такое   MEGAWAYS ") == "что такое megaways"


@pytest.mark.rule("SEC-003")
@pytest.mark.negative
@pytest.mark.parametrize("value", ["", "   ", None, "with\x00null", "with\nnewline"])
def test_malformed_identifiers_are_rejected(value) -> None:
    with pytest.raises(ConfigurationError):
        clean_identifier(value, field="parameter")


@pytest.mark.rule("SEC-003")
@pytest.mark.negative
def test_oversized_identifiers_are_rejected() -> None:
    with pytest.raises(ConfigurationError, match="exceeds"):
        clean_identifier("a" * (MAX_IDENTIFIER_LENGTH + 1), field="parameter")
    with pytest.raises(ConfigurationError, match="exceeds"):
        clean_query("q" * (MAX_QUERY_LENGTH + 1))
    with pytest.raises(ConfigurationError, match="exceeds"):
        clean_text("x" * 10, field="note", max_length=5)


@pytest.mark.rule("SEC-003")
@pytest.mark.negative
def test_oversized_lists_are_rejected() -> None:
    with pytest.raises(ConfigurationError, match="more than"):
        split_list("|".join(f"d{i}.example" for i in range(60)), field="competitors")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("42", 42), (" 1 000 ", 1000), (7, 7)],
)
def test_integers_parse(raw, expected: int) -> None:
    assert parse_int(raw, field="n") == expected


@pytest.mark.parametrize("raw", ["", None, "abc", "1.5"])
def test_bad_integers_are_rejected(raw) -> None:
    with pytest.raises(ConfigurationError):
        parse_int(raw, field="n")


def test_negative_values_are_rejected_by_default() -> None:
    with pytest.raises(ConfigurationError, match=">="):
        parse_int("-5", field="n")
    assert parse_int("-5", field="n", minimum=None) == -5


def test_floats_accept_the_comma_decimal_separator() -> None:
    assert parse_float("3,5", field="x") == 3.5
    with pytest.raises(ConfigurationError):
        parse_float("2", field="x", maximum=1.0)


@pytest.mark.parametrize(("raw", "expected"), [("да", True), ("no", False), ("1", True), ("-", False)])
def test_booleans_parse(raw: str, expected: bool) -> None:
    assert parse_bool(raw, field="flag") is expected


def test_unknown_booleans_are_rejected() -> None:
    with pytest.raises(ConfigurationError):
        parse_bool("maybe", field="flag")
    assert parse_bool("", field="flag", default=True) is True


@pytest.mark.parametrize("raw", ["2026-07-06", "06.07.2026", "2026/07/06"])
def test_supported_date_formats(raw: str) -> None:
    assert parse_date(raw, field="week").isoformat() == "2026-07-06"


def test_unsupported_dates_are_rejected() -> None:
    with pytest.raises(ConfigurationError, match="not a supported date"):
        parse_date("July 6th", field="week")


def test_missing_columns_are_named() -> None:
    with pytest.raises(ConfigurationError, match="detected_urls"):
        require_columns({"parameter": "sort"}, ("parameter", "detected_urls"), where="row 1")
