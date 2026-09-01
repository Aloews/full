"""Answer-first assessment (rule AEO-001).

An assistant lifts a self-contained answer or it lifts nothing. This module
checks whether one exists and is extractable. It deliberately says nothing
about what that does to visibility — that is what the experiment engine is for.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from kontur.core.claims import GuidelineRecommendation
from kontur.engines.aeo.buckets import AnswerLengthBucket, bucket_for
from kontur.engines.aeo.content import BlockKind, PageContent, word_count

#: Minimum words for a paragraph to count as a self-contained answer rather
#: than a lead-in sentence.
MIN_ANSWER_WORDS = 20

#: How far into the page the answer may sit before it stops being answer-first.
MAX_BLOCKS_BEFORE_ANSWER = 2

_FILLER_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^\s*в\s+(?:современном\s+мире|наши\s+дни|последнее\s+время)", re.IGNORECASE),
    re.compile(r"^\s*(?:сегодня|сейчас)\s+(?:трудно|сложно)\s+представить", re.IGNORECASE),
    re.compile(r"^\s*как\s+известно", re.IGNORECASE),
    re.compile(r"^\s*многие\s+(?:игроки|пользователи|люди)\s+задаются", re.IGNORECASE),
    re.compile(r"^\s*in\s+today'?s\s+world", re.IGNORECASE),
    re.compile(r"^\s*it\s+is\s+no\s+secret", re.IGNORECASE),
)

_TOKEN_RE = re.compile(r"[\w’'-]+", re.UNICODE)

#: Function words carry no topical signal, so they are excluded from the
#: query-coverage check: "что такое megaways" is about ``megaways``.
STOPWORDS: frozenset[str] = frozenset({
    "что", "как", "это", "такое", "для", "или", "все", "его", "они", "она",
    "при", "под", "над", "без", "про", "чем", "где", "тот", "эта", "эти",
    "the", "what", "why", "how", "are", "and", "for", "with", "that", "this",
    "does", "can", "you", "your", "its", "into", "from", "about",
})


def _tokens(text: str, *, drop_stopwords: bool = False) -> set[str]:
    tokens = {t.lower() for t in _TOKEN_RE.findall(text or "") if len(t) > 2}
    return tokens - STOPWORDS if drop_stopwords else tokens


def starts_with_filler(text: str) -> bool:
    return any(pattern.search(text or "") for pattern in _FILLER_PATTERNS)


@dataclass(frozen=True, slots=True)
class AnswerAssessment:
    """Whether the page opens with an extractable answer, and what shape it has."""

    url: str
    has_answer_first: bool
    word_count: int
    bucket: AnswerLengthBucket
    blocks_before_answer: int
    query_term_coverage: float
    filler_opening: bool
    findings: tuple[str, ...] = ()
    excerpt: str = ""
    recommendations: tuple[GuidelineRecommendation, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "has_answer_first": self.has_answer_first,
            "word_count": self.word_count,
            "bucket": self.bucket.value,
            "blocks_before_answer": self.blocks_before_answer,
            "query_term_coverage": round(self.query_term_coverage, 3),
            "filler_opening": self.filler_opening,
            "findings": list(self.findings),
            "excerpt": self.excerpt,
            "recommendations": [r.to_dict() for r in self.recommendations],
        }


def assess_answer_first(page: PageContent, *, query: str | None = None) -> AnswerAssessment:
    """Check the opening of ``page`` against the answer-first guideline."""
    target = query or page.target_query
    paragraph = page.first_paragraph()
    position = page.blocks_before_first_paragraph()
    findings: list[str] = []

    if paragraph is None:
        return AnswerAssessment(
            url=page.url,
            has_answer_first=False,
            word_count=0,
            bucket=bucket_for(0),
            blocks_before_answer=position,
            query_term_coverage=0.0,
            filler_opening=False,
            findings=("no paragraph found: there is nothing for an assistant to lift",),
            recommendations=(
                GuidelineRecommendation("H-001", "Open the page with a self-contained answer paragraph."),
            ),
        )

    words = word_count(paragraph.text)
    filler = starts_with_filler(paragraph.text)

    coverage = 1.0
    if target:
        query_tokens = _tokens(target, drop_stopwords=True)
        if query_tokens:
            present = query_tokens & _tokens(paragraph.text)
            coverage = len(present) / len(query_tokens)

    if position > MAX_BLOCKS_BEFORE_ANSWER:
        findings.append(
            f"answer paragraph is block #{position + 1}: {position} blocks come before it"
        )
    if words < MIN_ANSWER_WORDS:
        findings.append(f"opening paragraph has {words} words, under the {MIN_ANSWER_WORDS}-word floor")
    if filler:
        findings.append("opening sentence is filler, not an answer")
    if target and coverage < 0.5:
        findings.append(
            f"opening covers {coverage:.0%} of the query terms: it may not read as an answer to {target!r}"
        )

    has_answer = not findings
    recommendations: list[GuidelineRecommendation] = []
    if not has_answer:
        recommendations.append(
            GuidelineRecommendation("H-001", "Rewrite the opening as a direct answer to the target query.")
        )
    recommendations.append(
        GuidelineRecommendation(
            "H-002",
            f"Current answer length falls in bucket {bucket_for(words).value}; "
            "compare buckets in an experiment before standardising one.",
        )
    )

    return AnswerAssessment(
        url=page.url,
        has_answer_first=has_answer,
        word_count=words,
        bucket=bucket_for(words),
        blocks_before_answer=position,
        query_term_coverage=coverage,
        filler_opening=filler,
        findings=tuple(findings),
        excerpt=paragraph.text[:280],
        recommendations=tuple(recommendations),
    )


def answer_blocks(page: PageContent) -> tuple[str, ...]:
    """Every block an assistant could quote verbatim, in document order."""
    quotable: list[str] = []
    for block in page.blocks:
        if block.kind is BlockKind.PARAGRAPH and word_count(block.text) >= MIN_ANSWER_WORDS:
            quotable.append(block.text)
        elif block.kind in (BlockKind.LIST, BlockKind.TABLE, BlockKind.FAQ):
            quotable.append(block.text or " / ".join(block.items))
    return tuple(quotable)
