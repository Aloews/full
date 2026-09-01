"""iGaming SEO operations: the page types the vertical actually needs.

    Categories | Games | Providers | Mechanics | Features | Bonuses | RTP
    Volatility | Jackpots | Reviews | Comparisons | Commercial | Informational

Each type declares what a complete page of that type contains. The requirements
are editorial and technical completeness checks — they say nothing about what
any search engine or assistant will do with the page.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Iterable

from kontur.core.errors import ConfigurationError


class PageType(StrEnum):
    CATEGORY = "category"
    GAME = "game"
    PROVIDER = "provider"
    MECHANIC = "mechanic"
    FEATURE = "feature"
    BONUS = "bonus"
    RTP = "rtp"
    VOLATILITY = "volatility"
    JACKPOT = "jackpot"
    REVIEW = "review"
    COMPARISON = "comparison"
    INFORMATIONAL = "informational"
    COMMERCIAL = "commercial"
    UNKNOWN = "unknown"


class Intent(StrEnum):
    COMMERCIAL = "commercial"
    INFORMATIONAL = "informational"
    TRANSACTIONAL = "transactional"
    MIXED = "mixed"


@dataclass(frozen=True, slots=True)
class PageTypeSpec:
    """What a complete page of this type contains."""

    page_type: PageType
    intent: Intent
    url_patterns: tuple[str, ...]
    required_blocks: tuple[str, ...] = ()
    required_schema: frozenset[str] = frozenset()
    indexable_by_default: bool = True
    notes: str = ""

    def matches(self, url: str) -> bool:
        return any(re.search(pattern, url) for pattern in self.url_patterns)

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_type": self.page_type.value,
            "intent": self.intent.value,
            "url_patterns": list(self.url_patterns),
            "required_blocks": list(self.required_blocks),
            "required_schema": sorted(self.required_schema),
            "indexable_by_default": self.indexable_by_default,
            "notes": self.notes,
        }


PAGE_TYPES: dict[PageType, PageTypeSpec] = {
    spec.page_type: spec
    for spec in (
        PageTypeSpec(PageType.CATEGORY, Intent.COMMERCIAL, (r"^/slots/?$", r"^/games/[^/]+/?$"),
                     ("intro", "game_grid", "filters", "faq"), frozenset({"itemlist"})),
        PageTypeSpec(PageType.GAME, Intent.TRANSACTIONAL, (r"^/slots/[^/]+/[^/]+/?$", r"^/game/[^/]+/?$"),
                     ("demo", "rtp", "volatility", "provider", "how_to_play"),
                     frozenset({"videogame", "breadcrumblist"})),
        PageTypeSpec(PageType.PROVIDER, Intent.COMMERCIAL, (r"^/providers?/[^/]+/?$",),
                     ("provider_intro", "game_grid", "licence", "faq"),
                     frozenset({"organization", "itemlist"})),
        PageTypeSpec(PageType.MECHANIC, Intent.MIXED, (r"^/slots/(?:megaways|cluster|hold-and-win)/?$",
                                                       r"^/mechanics?/[^/]+/?$"),
                     ("definition", "how_it_works", "game_grid", "comparison_table", "faq"),
                     frozenset({"faqpage", "itemlist"}),
                     notes="Definitional head plus an inventory tail: the classic answer-first page."),
        PageTypeSpec(PageType.FEATURE, Intent.MIXED, (r"^/features?/[^/]+/?$",),
                     ("definition", "game_grid", "faq"), frozenset({"itemlist"})),
        PageTypeSpec(PageType.BONUS, Intent.COMMERCIAL, (r"^/bonus(?:es)?/[^/]*/?$",),
                     ("offer_terms", "wagering", "comparison_table", "faq"),
                     frozenset({"faqpage"}),
                     notes="Terms and wagering must be on the page itself, not only in a PDF."),
        PageTypeSpec(PageType.RTP, Intent.INFORMATIONAL, (r"^/rtp/?$", r"^/slots/rtp-[^/]+/?$"),
                     ("definition", "rtp_table", "methodology", "faq"),
                     frozenset({"faqpage", "table"}),
                     notes="An RTP page without a methodology block is an unverifiable claim."),
        PageTypeSpec(PageType.VOLATILITY, Intent.INFORMATIONAL, (r"^/volatility/?$", r"^/slots/volatility-[^/]+/?$"),
                     ("definition", "bands", "game_grid", "faq"), frozenset({"faqpage"})),
        PageTypeSpec(PageType.JACKPOT, Intent.COMMERCIAL, (r"^/jackpots?/[^/]*/?$",),
                     ("current_pools", "game_grid", "rules", "faq"), frozenset({"itemlist"})),
        PageTypeSpec(PageType.REVIEW, Intent.MIXED, (r"^/reviews?/[^/]+/?$",),
                     ("verdict", "pros_cons", "methodology", "author", "faq"),
                     frozenset({"review", "person"}),
                     notes="A review without a named author and a methodology block is not a review."),
        PageTypeSpec(PageType.COMPARISON, Intent.COMMERCIAL, (r"^/compare/[^/]+/?$", r"^/[^/]+-vs-[^/]+/?$"),
                     ("comparison_table", "criteria", "verdict", "faq"),
                     frozenset({"table", "faqpage"})),
        PageTypeSpec(PageType.INFORMATIONAL, Intent.INFORMATIONAL, (r"^/blog/[^/]+/?$", r"^/guides?/[^/]+/?$"),
                     ("answer_first", "body", "faq", "author"), frozenset({"article"})),
        PageTypeSpec(PageType.COMMERCIAL, Intent.TRANSACTIONAL, (r"^/promo/[^/]+/?$", r"^/register/?$"),
                     ("offer", "terms"), frozenset(), indexable_by_default=False,
                     notes="Conversion surfaces: usually not the place to chase organic entries."),
    )
}


def classify_url(url: str) -> PageType:
    """Best-effort page-type detection from the path alone."""
    path = (url or "").split("?", 1)[0]
    if not path.startswith("/"):
        path = "/" + path
    for spec in PAGE_TYPES.values():
        if spec.matches(path):
            return spec.page_type
    return PageType.UNKNOWN


def spec_for(page_type: PageType) -> PageTypeSpec:
    try:
        return PAGE_TYPES[PageType(page_type)]
    except KeyError as exc:
        raise ConfigurationError(f"no specification for page type {page_type!r}") from exc


@dataclass(frozen=True, slots=True)
class CompletenessReport:
    url: str
    page_type: PageType
    missing_blocks: tuple[str, ...] = ()
    missing_schema: tuple[str, ...] = ()
    findings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_complete(self) -> bool:
        return not (self.missing_blocks or self.missing_schema)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "page_type": self.page_type.value,
            "complete": self.is_complete,
            "missing_blocks": list(self.missing_blocks),
            "missing_schema": list(self.missing_schema),
            "findings": list(self.findings),
        }


def check_completeness(
    url: str,
    *,
    present_blocks: Iterable[str],
    schema_types: Iterable[str],
    page_type: PageType | None = None,
) -> CompletenessReport:
    """Compare a page against the specification for its type."""
    detected = PageType(page_type) if page_type else classify_url(url)
    if detected is PageType.UNKNOWN:
        return CompletenessReport(
            url=url,
            page_type=detected,
            findings=("URL does not match any known iGaming page type",),
        )

    spec = spec_for(detected)
    present = {b.strip().lower() for b in present_blocks if b and b.strip()}
    schemas = {s.strip().lower() for s in schema_types if s and s.strip()}
    return CompletenessReport(
        url=url,
        page_type=detected,
        missing_blocks=tuple(sorted(set(spec.required_blocks) - present)),
        missing_schema=tuple(sorted(spec.required_schema - schemas)),
        findings=(spec.notes,) if spec.notes else (),
    )
