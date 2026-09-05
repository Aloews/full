"""URL parsing, normalisation and input bounds."""

from __future__ import annotations

import pytest

from kontur.core.errors import ConfigurationError
from kontur.core.urls import (
    MAX_URL_LENGTH,
    build_url,
    is_same_document,
    normalise_url,
    param_names,
    params_as_dict,
    parent_path,
    parse_url,
    strip_params,
    validate_url,
)

pytestmark = pytest.mark.unit

URL = "https://Casino.Example/slots/?utm_source=vk&provider=pragmatic&sort=popular#anchor"


def test_parsing_lowercases_the_host_and_drops_the_fragment() -> None:
    parsed = parse_url(URL)
    assert parsed.host == "casino.example"
    assert parsed.path == "/slots/"
    assert parsed.fragment == ""
    assert param_names(URL) == ("utm_source", "provider", "sort")


def test_stripping_parameters_preserves_the_rest() -> None:
    assert strip_params(URL, ["utm_source", "sort"]) == "https://casino.example/slots/?provider=pragmatic"


def test_normalisation_orders_parameters() -> None:
    a = "/slots/?b=2&a=1"
    b = "/slots/?a=1&b=2"
    assert normalise_url(a) == normalise_url(b)
    assert is_same_document(a, b)


def test_normalisation_drops_empty_values() -> None:
    assert normalise_url("/slots/?a=&b=1") == "/slots/?b=1"


def test_repeated_parameters_are_preserved() -> None:
    assert params_as_dict("/slots/?tag=a&tag=b") == {"tag": ["a", "b"]}


@pytest.mark.parametrize(
    ("path", "expected"),
    [("/slots/megaways/", "/slots/"), ("/slots/", "/"), ("/", "/"), ("/a/b/c/", "/a/b/")],
)
def test_parent_path(path: str, expected: str) -> None:
    assert parent_path(path) == expected


def test_build_url_round_trips() -> None:
    assert build_url("/slots/", {"provider": "pragmatic"}) == "/slots/?provider=pragmatic"
    assert build_url("/slots/", None) == "/slots/"


@pytest.mark.rule("SEC-003")
@pytest.mark.positive
def test_ordinary_urls_pass_validation() -> None:
    assert validate_url("/slots/?provider=pragmatic") == "/slots/?provider=pragmatic"


@pytest.mark.rule("SEC-003")
@pytest.mark.negative
@pytest.mark.parametrize(
    "url",
    [
        "",
        "   ",
        "/slots/\x00evil",
        "/slots/\nSet-Cookie: x",
    ],
)
def test_malformed_urls_are_rejected(url: str) -> None:
    with pytest.raises(ConfigurationError):
        validate_url(url)


@pytest.mark.rule("SEC-003")
@pytest.mark.negative
def test_oversized_urls_are_rejected() -> None:
    with pytest.raises(ConfigurationError, match="exceeds"):
        validate_url("/slots/?x=" + "a" * MAX_URL_LENGTH)


@pytest.mark.rule("SEC-003")
@pytest.mark.negative
def test_oversized_parameter_values_are_rejected() -> None:
    with pytest.raises(ConfigurationError, match="exceeds"):
        parse_url("/slots/?provider=" + "a" * 300)


@pytest.mark.rule("SEC-003")
@pytest.mark.negative
def test_non_string_urls_are_rejected() -> None:
    with pytest.raises(ConfigurationError):
        validate_url(None)
