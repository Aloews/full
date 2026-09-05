"""Extraction readiness (rule AEO-003).

Measures how much of a page is in a shape an assistant can lift: a direct
answer, question headings, lists, tables, FAQ markup and concrete numbers.
It is a structural measurement of our own page — no external claim is involved.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from kontur.core.errors import ConfigurationError
from kontur.engines.aeo.answer import assess_answer_first
from kontur.engines.aeo.content import BlockKind, PageContent

_NUMERIC_FACT_RE = re.compile(r"\d+(?:[.,]\d+)?\s*(?:%|₽|руб|rub|x|х|раз|ways|мс|сек)", re.IGNORECASE)

#: Structured-data types that mark a page as machine-readable for Q&A.
ANSWER_SCHEMA_TYPES: frozenset[str] = frozenset(
    {"faqpage", "qapage", "question", "howto", "article", "itemlist", "table"}
)

WEIGHTS: dict[str, float] = {
    "direct_answer": 0.35,
    "question_headings": 0.15,
    "lists": 0.10,
    "tables": 0.15,
    "schema": 0.15,
    "numeric_facts": 0.10,
}


@dataclass(frozen=True, slots=True)
class ExtractionSignals:
    """Counted structural features of a page."""

    has_direct_answer: bool = False
    question_headings: int = 0
    lists: int = 0
    tables: int = 0
    answer_schema_types: int = 0
    numeric_facts: int = 0

    def __post_init__(self) -> None:
        for name in ("question_headings", "lists", "tables", "answer_schema_types", "numeric_facts"):
            if getattr(self, name) < 0:
                raise ConfigurationError(f"{name} must be >= 0")

    def to_dict(self) -> dict[str, Any]:
        return {
            "has_direct_answer": self.has_direct_answer,
            "question_headings": self.question_headings,
            "lists": self.lists,
            "tables": self.tables,
            "answer_schema_types": self.answer_schema_types,
            "numeric_facts": self.numeric_facts,
        }


def extraction_signals(page: PageContent, *, query: str | None = None) -> ExtractionSignals:
    answer = assess_answer_first(page, query=query)
    numeric = sum(len(_NUMERIC_FACT_RE.findall(b.text)) for b in page.blocks)
    numeric += sum(len(_NUMERIC_FACT_RE.findall(i)) for b in page.blocks for i in b.items)
    return ExtractionSignals(
        has_direct_answer=answer.has_answer_first,
        question_headings=len(page.questions),
        lists=len(page.of_kind(BlockKind.LIST)),
        tables=len(page.of_kind(BlockKind.TABLE)),
        answer_schema_types=len(page.schema_types & ANSWER_SCHEMA_TYPES),
        numeric_facts=numeric,
    )


def extraction_readiness_score(signals: ExtractionSignals) -> float:
    """Weighted share of the extractable-shape checklist that the page satisfies.

    Bounded to [0, 1]: 0 when nothing on the page is liftable, 1 when a direct
    answer, question headings, a list, a table, answer schema and concrete
    numbers are all present.
    """
    if not isinstance(signals, ExtractionSignals):
        raise ConfigurationError("extraction_readiness_score() needs ExtractionSignals")

    parts = {
        "direct_answer": 1.0 if signals.has_direct_answer else 0.0,
        "question_headings": min(signals.question_headings / 3.0, 1.0),
        "lists": min(signals.lists / 2.0, 1.0),
        "tables": min(signals.tables / 1.0, 1.0),
        "schema": min(signals.answer_schema_types / 1.0, 1.0),
        "numeric_facts": min(signals.numeric_facts / 3.0, 1.0),
    }
    score = sum(WEIGHTS[key] * value for key, value in parts.items())
    return min(1.0, max(0.0, score))


@dataclass(frozen=True, slots=True)
class ExtractionReport:
    url: str
    signals: ExtractionSignals
    score: float
    gaps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "signals": self.signals.to_dict(),
            "extraction_readiness": round(self.score, 3),
            "gaps": list(self.gaps),
            "caveat": (
                "Structural readiness of our own page. It does not predict whether an "
                "assistant will cite it."
            ),
        }


def extraction_report(page: PageContent, *, query: str | None = None) -> ExtractionReport:
    signals = extraction_signals(page, query=query)
    gaps: list[str] = []
    if not signals.has_direct_answer:
        gaps.append("no answer-first paragraph")
    if signals.question_headings == 0:
        gaps.append("no question-shaped headings")
    if signals.tables == 0:
        gaps.append("no comparison table")
    if signals.answer_schema_types == 0:
        gaps.append("no FAQ/QA structured data")
    if signals.numeric_facts == 0:
        gaps.append("no concrete numbers (RTP, limits, counts)")
    return ExtractionReport(
        url=page.url,
        signals=signals,
        score=extraction_readiness_score(signals),
        gaps=tuple(gaps),
    )
