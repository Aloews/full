"""Input validation at the ingest boundary (rule SEC-003).

Everything entering Kontur comes from a crawler, an export or an API payload —
all attacker-influenced to some degree. Identifiers are length-bounded,
control characters are rejected and numbers are parsed strictly, so a malformed
export fails loudly at the door instead of corrupting a report.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Iterable, Mapping

from kontur.core.errors import ConfigurationError

MAX_IDENTIFIER_LENGTH = 128
MAX_QUERY_LENGTH = 400
MAX_TEXT_LENGTH = 4096

_CONTROL_CHARS = {chr(c) for c in range(0x20)} | {"\x7f"}


def clean_identifier(value: Any, *, field: str, max_length: int = MAX_IDENTIFIER_LENGTH) -> str:
    if value is None:
        raise ConfigurationError(f"{field} is required")
    text = str(value).strip()
    if not text:
        raise ConfigurationError(f"{field} must not be empty")
    if len(text) > max_length:
        raise ConfigurationError(f"{field} exceeds {max_length} characters ({len(text)})")
    if _CONTROL_CHARS.intersection(text):
        raise ConfigurationError(f"{field} contains control characters")
    return text


def clean_query(value: Any, *, field: str = "query") -> str:
    text = clean_identifier(value, field=field, max_length=MAX_QUERY_LENGTH)
    return " ".join(text.split()).lower()


def clean_text(value: Any, *, field: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    if value is None:
        return ""
    text = str(value)
    if len(text) > max_length:
        raise ConfigurationError(f"{field} exceeds {max_length} characters ({len(text)})")
    if _CONTROL_CHARS.intersection(text) - {"\n", "\t"}:
        raise ConfigurationError(f"{field} contains control characters")
    return text.strip()


def parse_int(value: Any, *, field: str, minimum: int | None = 0) -> int:
    if value is None or value == "":
        raise ConfigurationError(f"{field} is required")
    try:
        parsed = int(str(value).strip().replace(" ", "").replace(" ", ""))
    except ValueError as exc:
        raise ConfigurationError(f"{field} is not an integer: {value!r}") from exc
    if minimum is not None and parsed < minimum:
        raise ConfigurationError(f"{field} must be >= {minimum}, got {parsed}")
    return parsed


def parse_float(value: Any, *, field: str, minimum: float | None = None, maximum: float | None = None) -> float:
    if value is None or value == "":
        raise ConfigurationError(f"{field} is required")
    try:
        parsed = float(str(value).strip().replace(" ", "").replace(" ", "").replace(",", "."))
    except ValueError as exc:
        raise ConfigurationError(f"{field} is not a number: {value!r}") from exc
    if minimum is not None and parsed < minimum:
        raise ConfigurationError(f"{field} must be >= {minimum}, got {parsed}")
    if maximum is not None and parsed > maximum:
        raise ConfigurationError(f"{field} must be <= {maximum}, got {parsed}")
    return parsed


def parse_bool(value: Any, *, field: str, default: bool | None = None) -> bool:
    if value is None or value == "":
        if default is None:
            raise ConfigurationError(f"{field} is required")
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "да", "+"}:
        return True
    if text in {"0", "false", "no", "n", "нет", "-"}:
        return False
    raise ConfigurationError(f"{field} is not a boolean: {value!r}")


def parse_date(value: Any, *, field: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = clean_identifier(value, field=field, max_length=32)
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ConfigurationError(f"{field} is not a supported date: {value!r}")


def parse_datetime(value: Any, *, field: str) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    parsed = parse_date(value, field=field)
    return datetime(parsed.year, parsed.month, parsed.day, tzinfo=timezone.utc)


def require_columns(row: Mapping[str, Any], columns: Iterable[str], *, where: str) -> None:
    missing = [c for c in columns if c not in row]
    if missing:
        raise ConfigurationError(f"{where} is missing required column(s): {', '.join(missing)}")


def split_list(value: Any, *, field: str, separator: str = "|", max_items: int = 50) -> tuple[str, ...]:
    if value is None or value == "":
        return ()
    text = clean_text(value, field=field)
    items = [part.strip() for part in text.split(separator) if part.strip()]
    if len(items) > max_items:
        raise ConfigurationError(f"{field} has {len(items)} items, more than the {max_items} allowed")
    return tuple(items)
