"""Keep credentials out of exports, reports and logs (rule SEC-002)."""

from __future__ import annotations

import re
from typing import Any

REDACTED = "[REDACTED]"

_SECRET_KEY_RE = re.compile(
    r"(?:^|[_.-])(?:password|passwd|secret|token|api[_-]?key|apikey|oauth|authorization|"
    r"access[_-]?key|private[_-]?key|session[_-]?id|cookie)(?:$|[_.-])",
    re.IGNORECASE,
)

_SECRET_VALUE_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),                     # AWS access key id
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),                    # GitHub tokens
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),                  # Slack tokens
    re.compile(r"\bey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),  # JWT
    re.compile(r"(?i)\b(?:oauth|bearer)\s+[A-Za-z0-9._~+/=-]{16,}"),  # bearer headers
)


def is_secret_key(key: str) -> bool:
    return bool(_SECRET_KEY_RE.search(key or ""))


def redact_text(text: str) -> str:
    """Replace secret-looking values inside a free-form string."""
    if not text:
        return text
    out = text
    for pattern in _SECRET_VALUE_RES:
        out = pattern.sub(REDACTED, out)
    # key=value pairs in query strings / config dumps
    out = re.sub(
        r"(?i)\b([a-z0-9_.-]*(?:password|secret|token|api[_-]?key|session[_-]?id)[a-z0-9_.-]*)"
        r"\s*[=:]\s*([^\s&;\"']+)",
        lambda m: f"{m.group(1)}={REDACTED}",
        out,
    )
    return out


def redact(value: Any) -> Any:
    """Recursively redact secrets from dicts/lists/strings before they leave the process."""
    if isinstance(value, dict):
        return {
            k: (REDACTED if is_secret_key(str(k)) else redact(v))
            for k, v in value.items()
        }
    if isinstance(value, (list, tuple)):
        rebuilt = [redact(v) for v in value]
        return type(value)(rebuilt) if isinstance(value, tuple) else rebuilt
    if isinstance(value, str):
        return redact_text(value)
    return value
