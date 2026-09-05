"""Secrets never reach an export, a report or a log."""

from __future__ import annotations

import pytest

from kontur.core.redaction import REDACTED, is_secret_key, redact, redact_text

pytestmark = [pytest.mark.unit, pytest.mark.security]


@pytest.mark.rule("SEC-002")
@pytest.mark.positive
@pytest.mark.parametrize("key", ["password", "api_key", "API-KEY", "session_id", "access_key", "authorization"])
def test_secret_keys_are_recognised(key: str) -> None:
    assert is_secret_key(key) is True


@pytest.mark.rule("SEC-002")
@pytest.mark.negative
@pytest.mark.parametrize("key", ["parameter", "detected_urls", "provider", "keyword", "tokenizer_note"])
def test_ordinary_keys_are_left_alone(key: str) -> None:
    assert is_secret_key(key) is False


@pytest.mark.rule("SEC-002")
@pytest.mark.positive
def test_nested_secrets_are_redacted() -> None:
    payload = {
        "site": "casino.example",
        "auth": {"api_key": "abcd1234", "note": "keep"},
        "links": [{"url": "https://x/?token=supersecretvalue1234"}],
    }
    cleaned = redact(payload)
    assert cleaned["auth"]["api_key"] == REDACTED
    assert cleaned["auth"]["note"] == "keep"
    assert "supersecretvalue1234" not in cleaned["links"][0]["url"]


@pytest.mark.rule("SEC-002")
@pytest.mark.positive
@pytest.mark.parametrize(
    "text",
    [
        "AKIAIOSFODNN7EXAMPLE",
        "ghp_0123456789abcdefghijABCDEFGHIJ",
        "xoxb-1234567890-abcdefghij",
        "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abcdefghijklmno",
    ],
)
def test_credential_shapes_are_scrubbed(text: str) -> None:
    assert REDACTED in redact_text(text)


@pytest.mark.rule("SEC-002")
@pytest.mark.negative
def test_ordinary_report_text_survives_untouched() -> None:
    text = "utm_source detected on 48210 URLs; decision EXCLUDE (tracking)"
    assert redact_text(text) == text


def test_redaction_preserves_container_types() -> None:
    assert isinstance(redact(("a", "b")), tuple)
    assert redact(42) == 42
    assert redact(None) is None
