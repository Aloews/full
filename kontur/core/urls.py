"""URL and query-string handling shared by the indexation engines."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from kontur.core.errors import ConfigurationError

MAX_URL_LENGTH = 2048
MAX_PARAM_NAME_LENGTH = 64
MAX_PARAM_VALUE_LENGTH = 256

_CONTROL_CHARS = {chr(c) for c in range(0x20)} | {"\x7f"}


@dataclass(frozen=True, slots=True)
class ParsedUrl:
    scheme: str
    host: str
    path: str
    params: tuple[tuple[str, str], ...]
    fragment: str = ""

    @property
    def param_names(self) -> tuple[str, ...]:
        seen: list[str] = []
        for name, _ in self.params:
            if name not in seen:
                seen.append(name)
        return tuple(seen)

    def values_of(self, name: str) -> tuple[str, ...]:
        return tuple(v for k, v in self.params if k == name)

    def with_params(self, params: Iterable[tuple[str, str]]) -> ParsedUrl:
        return ParsedUrl(self.scheme, self.host, self.path, tuple(params), self.fragment)

    def to_url(self) -> str:
        query = urlencode(self.params, doseq=False)
        netloc = self.host
        return urlunsplit((self.scheme, netloc, self.path, query, self.fragment))


def validate_url(url: str) -> str:
    """Reject unbounded or control-character input at the boundary (rule SEC-003)."""
    if url is None:
        raise ConfigurationError("url is required")
    if not isinstance(url, str):
        raise ConfigurationError(f"url must be a string, got {type(url).__name__}")
    if not url.strip():
        raise ConfigurationError("url must not be empty")
    if len(url) > MAX_URL_LENGTH:
        raise ConfigurationError(f"url exceeds {MAX_URL_LENGTH} characters ({len(url)})")
    bad = _CONTROL_CHARS.intersection(url)
    if bad:
        raise ConfigurationError("url contains control characters")
    return url.strip()


def parse_url(url: str) -> ParsedUrl:
    """Split a URL (absolute or path-only) into its indexation-relevant parts."""
    cleaned = validate_url(url)
    split = urlsplit(cleaned)
    params = tuple(parse_qsl(split.query, keep_blank_values=True))
    for name, value in params:
        if len(name) > MAX_PARAM_NAME_LENGTH:
            raise ConfigurationError(
                f"parameter name exceeds {MAX_PARAM_NAME_LENGTH} characters: {name[:32]}..."
            )
        if len(value) > MAX_PARAM_VALUE_LENGTH:
            raise ConfigurationError(
                f"value of parameter {name!r} exceeds {MAX_PARAM_VALUE_LENGTH} characters"
            )
    return ParsedUrl(
        scheme=split.scheme,
        host=split.netloc.lower(),
        path=split.path or "/",
        params=params,
        fragment="",
    )


def param_names(url: str) -> tuple[str, ...]:
    return parse_url(url).param_names


def params_as_dict(url: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for name, value in parse_url(url).params:
        out.setdefault(name, []).append(value)
    return out


def strip_params(url: str, names: Iterable[str]) -> str:
    """Remove the named parameters, keeping the order of the rest."""
    drop = {n.lower() for n in names}
    parsed = parse_url(url)
    kept = tuple((k, v) for k, v in parsed.params if k.lower() not in drop)
    return parsed.with_params(kept).to_url()


def keep_only_params(url: str, names: Iterable[str]) -> str:
    keep = {n.lower() for n in names}
    parsed = parse_url(url)
    kept = tuple((k, v) for k, v in parsed.params if k.lower() in keep)
    return parsed.with_params(kept).to_url()


def normalise_url(url: str, *, sort_params: bool = True, drop_empty: bool = True) -> str:
    """Canonical string form: lowercase host, no fragment, ordered parameters.

    Two URLs that address the same document must normalise to the same string,
    otherwise the duplicate detector counts them twice.
    """
    parsed = parse_url(url)
    params: Sequence[tuple[str, str]] = parsed.params
    if drop_empty:
        params = [(k, v) for k, v in params if v != ""]
    if sort_params:
        params = sorted(params, key=lambda kv: (kv[0], kv[1]))
    return ParsedUrl(parsed.scheme, parsed.host, parsed.path, tuple(params), "").to_url()


def build_url(path: str, params: Mapping[str, str] | Iterable[tuple[str, str]] | None = None) -> str:
    items = list(params.items()) if isinstance(params, Mapping) else list(params or [])
    query = urlencode(items, doseq=False)
    return f"{path}?{query}" if query else path


def is_same_document(a: str, b: str) -> bool:
    return normalise_url(a) == normalise_url(b)


def parent_path(path: str) -> str:
    """The directory one level up, keeping the trailing slash convention."""
    cleaned = parse_url(path).path
    trimmed = cleaned.rstrip("/")
    if not trimmed:
        return "/"
    head, _, _ = trimmed.rpartition("/")
    return f"{head}/" if head else "/"
