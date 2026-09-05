"""Known parameter families.

The catalogue is deliberately explicit rather than clever: a maintainer must be
able to read it and say "yes, ``ysclid`` is a Yandex click id and must never
create a document".
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class ParamFamily(StrEnum):
    TRACKING = "tracking"
    SESSION = "session"
    SORT = "sort"
    DISPLAY = "display"
    PAGINATION = "pagination"
    FACET_CANDIDATE = "facet_candidate"
    UNKNOWN = "unknown"


#: Analytics / advertising click identifiers. They never change the document.
TRACKING_PARAMS: frozenset[str] = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "utm_id",
    "utm_source_platform", "utm_creative_format", "utm_marketing_tactic",
    "yclid", "ysclid", "gclid", "gclsrc", "dclid", "wbraid", "gbraid", "fbclid", "ttclid",
    "msclkid", "twclid", "igshid", "vkclid", "_openstat", "roistat", "roistat_visit",
    "erid", "from", "frm", "referrer", "ref", "source", "campaign_id", "adgroup",
    "click_id", "clickid", "cid", "aff_id", "affiliate", "aff_sub", "subid", "sub_id",
    "banner_id", "promo_source", "partner", "pid",
})

#: Session and user identifiers: unbounded space, one document per visitor.
SESSION_PARAM_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^(?:php)?sess(?:ion)?_?id$"),
    re.compile(r"^jsessionid$"),
    re.compile(r"^sid$"),
    re.compile(r"^s_id$"),
    re.compile(r"^visitor_?id$"),
    re.compile(r"^user_?(?:id|hash|token)$"),
    re.compile(r"^_?token$"),
    re.compile(r"^csrf.*$"),
    re.compile(r"^auth.*$"),
)

#: Re-ordering the same inventory does not create a new document.
SORT_PARAMS: frozenset[str] = frozenset({
    "sort", "sorting", "sort_by", "sortby", "order", "orderby", "order_by", "direction",
    "dir", "asc", "desc", "sort_order",
})

#: Presentation state (grid/list, page size, currency switcher, ...).
DISPLAY_PARAMS: frozenset[str] = frozenset({
    "view", "display", "layout", "mode", "per_page", "perpage", "limit", "count",
    "columns", "ui_theme", "skin", "currency", "lang_switcher", "compact",
})

#: Position inside a result set. Meaning depends on the value.
PAGINATION_PARAMS: frozenset[str] = frozenset({"page", "p", "pg", "offset", "start", "from_page"})


@dataclass(frozen=True, slots=True)
class FacetCandidate:
    """A parameter that plausibly encodes a real content facet."""

    name: str
    label: str
    vertical: str = "generic"


#: iGaming facet vocabulary. These are *candidates*: promotion to an indexable
#: hub still requires measured demand (rule GETP-006).
IGAMING_FACET_CANDIDATES: dict[str, FacetCandidate] = {
    c.name: c
    for c in (
        FacetCandidate("provider", "Game provider", "igaming"),
        FacetCandidate("mechanic", "Game mechanic", "igaming"),
        FacetCandidate("feature", "Game feature", "igaming"),
        FacetCandidate("theme", "Game theme", "igaming"),
        FacetCandidate("volatility", "Volatility", "igaming"),
        FacetCandidate("rtp", "RTP band", "igaming"),
        FacetCandidate("bonus-buy", "Bonus buy", "igaming"),
        FacetCandidate("bonus_buy", "Bonus buy", "igaming"),
        FacetCandidate("jackpot", "Jackpot type", "igaming"),
        FacetCandidate("reels", "Reel layout", "igaming"),
        FacetCandidate("lines", "Paylines", "igaming"),
        FacetCandidate("min-bet", "Minimum bet", "igaming"),
        FacetCandidate("category", "Category", "igaming"),
    )
}


def _matches_session(name: str) -> bool:
    return any(pattern.match(name) for pattern in SESSION_PARAM_PATTERNS)


def family_of(name: str, *, facet_candidates: dict[str, FacetCandidate] | None = None) -> ParamFamily:
    """Classify a parameter name into a family (pure name-based lookup)."""
    key = (name or "").strip().lower()
    if not key:
        return ParamFamily.UNKNOWN
    candidates = IGAMING_FACET_CANDIDATES if facet_candidates is None else facet_candidates
    if key in TRACKING_PARAMS or key.startswith("utm_"):
        return ParamFamily.TRACKING
    if _matches_session(key):
        return ParamFamily.SESSION
    if key in SORT_PARAMS:
        return ParamFamily.SORT
    if key in PAGINATION_PARAMS:
        return ParamFamily.PAGINATION
    # A facet declared for this vertical wins over the generic display list:
    # `theme` is a UI switcher on a shop and a content facet on a slots catalogue.
    if key in candidates:
        return ParamFamily.FACET_CANDIDATE
    if key in DISPLAY_PARAMS:
        return ParamFamily.DISPLAY
    return ParamFamily.UNKNOWN
