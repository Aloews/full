"""Export the controller's rulings into artefacts a webmaster can apply.

Two artefacts:

* a JSON payload for the Yandex Webmaster "GET parameters" setting, split into
  the parameters to ignore, the parameters to take into account, and the ones
  still under review;
* ``Clean-param`` / ``Disallow`` directives for robots.txt, for the sites that
  keep their parameter policy there.

Both are deterministic: the same rulings always produce byte-identical output
(rule GETP-008), because a directive file that changes between runs cannot be
reviewed in a pull request.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Sequence

from kontur.core.errors import ConfigurationError
from kontur.engines.getparams.models import ParamDecision, ParamRuling

#: Yandex documents a length limit for a single Clean-param directive.
CLEAN_PARAM_MAX_LENGTH = 500


@dataclass(frozen=True, slots=True)
class YandexGetParametersExport:
    """The payload mirroring Webmaster's GET-parameter setting."""

    exclude: tuple[str, ...]
    consider: tuple[str, ...]
    review: tuple[str, ...]
    blocked: tuple[str, ...]
    generated_at: datetime
    contains_sample_data: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": "yandex_webmaster.get_parameters",
            "generated_at": self.generated_at.astimezone(timezone.utc).isoformat(),
            "exclude": list(self.exclude),
            "consider": list(self.consider),
            "review": list(self.review),
            "blocked_from_crawling": list(self.blocked),
            "contains_sample_data": self.contains_sample_data,
            "note": (
                "exclude = ignore during indexing; consider = take into account; "
                "review = undecided, keep out of the indexable set until analysed."
            ),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)


def build_export(
    rulings: Iterable[ParamRuling], *, generated_at: datetime | None = None
) -> YandexGetParametersExport:
    rulings = list(rulings)
    generated_at = generated_at or datetime.now(timezone.utc)

    def names(*decisions: ParamDecision) -> tuple[str, ...]:
        wanted = set(decisions)
        return tuple(sorted({r.name for r in rulings if r.decision in wanted}))

    return YandexGetParametersExport(
        exclude=names(ParamDecision.EXCLUDE, ParamDecision.BLOCK),
        consider=names(ParamDecision.SEO_HUB, ParamDecision.CONTEXT_DEPENDENT),
        review=names(ParamDecision.ANALYZE),
        blocked=names(ParamDecision.BLOCK),
        generated_at=generated_at,
        contains_sample_data=any(r.is_sample for r in rulings),
    )


def clean_param_directives(parameters: Sequence[str], path: str = "/") -> list[str]:
    """Build ``Clean-param`` lines, chunked to stay under the length limit."""
    if not path.startswith("/"):
        raise ConfigurationError("Clean-param path must start with '/'")
    names = sorted({p.strip().lower() for p in parameters if p and p.strip()})
    if not names:
        return []

    lines: list[str] = []
    chunk: list[str] = []

    def render(items: Sequence[str]) -> str:
        return f"Clean-param: {'&'.join(items)} {path}"

    for name in names:
        candidate = [*chunk, name]
        if chunk and len(render(candidate)) > CLEAN_PARAM_MAX_LENGTH:
            lines.append(render(chunk))
            chunk = [name]
        else:
            chunk = candidate
    if chunk:
        lines.append(render(chunk))
    return lines


def parse_clean_param_directives(lines: Iterable[str]) -> dict[str, set[str]]:
    """Inverse of :func:`clean_param_directives`, used to verify round-trips."""
    out: dict[str, set[str]] = {}
    for raw in lines:
        line = raw.strip()
        if not line.lower().startswith("clean-param:"):
            continue
        body = line.split(":", 1)[1].strip()
        parts = body.split(None, 1)
        params = parts[0]
        path = parts[1].strip() if len(parts) > 1 else "/"
        out.setdefault(path, set()).update(p for p in params.split("&") if p)
    return out


def robots_disallow_directives(blocked: Sequence[str]) -> list[str]:
    """Disallow patterns for parameters that must not be crawled at all."""
    lines: list[str] = []
    for name in sorted({p.strip().lower() for p in blocked if p and p.strip()}):
        lines.append(f"Disallow: /*?*{name}=")
        lines.append(f"Disallow: /*&{name}=")
    return lines


def robots_block(rulings: Iterable[ParamRuling], *, path: str = "/", user_agent: str = "Yandex") -> str:
    """A ready-to-paste robots.txt block for the given rulings."""
    rulings = list(rulings)
    excluded = [r.name for r in rulings if r.decision is ParamDecision.EXCLUDE]
    blocked = [r.name for r in rulings if r.decision is ParamDecision.BLOCK]
    lines = [f"User-agent: {user_agent}"]
    lines.extend(robots_disallow_directives(blocked))
    lines.extend(clean_param_directives([*excluded, *blocked], path))
    return "\n".join(lines) + "\n"
