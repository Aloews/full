"""A minimal, dependency-free content model for AEO analysis."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from html.parser import HTMLParser
from typing import Any

from kontur.core.errors import ConfigurationError

_WORD_RE = re.compile(r"[\w’'-]+", re.UNICODE)
_QUESTION_RE = re.compile(r"[?？]\s*$")
_RU_QUESTION_WORDS = (
    "что", "как", "почему", "зачем", "когда", "где", "какой", "какая", "какие",
    "сколько", "чем", "кто", "можно ли", "стоит ли",
)
_EN_QUESTION_WORDS = ("what", "how", "why", "when", "where", "which", "who", "can", "is", "are", "do")


def word_count(text: str) -> int:
    return len(_WORD_RE.findall(text or ""))


def looks_like_question(text: str) -> bool:
    value = (text or "").strip().lower()
    if not value:
        return False
    if _QUESTION_RE.search(value):
        return True
    first_two = " ".join(value.split()[:2])
    return any(value.startswith(w) for w in _RU_QUESTION_WORDS) or any(
        first_two.startswith(w + " ") for w in _EN_QUESTION_WORDS
    )


class BlockKind(StrEnum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    FAQ = "faq"


@dataclass(frozen=True, slots=True)
class ContentBlock:
    kind: BlockKind
    text: str
    level: int = 0
    items: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", BlockKind(self.kind))
        object.__setattr__(self, "text", (self.text or "").strip())

    @property
    def word_count(self) -> int:
        return word_count(self.text) + sum(word_count(i) for i in self.items)

    @property
    def is_question(self) -> bool:
        return looks_like_question(self.text)


@dataclass(frozen=True, slots=True)
class PageContent:
    """The structural shape of one page."""

    url: str
    title: str = ""
    h1: str = ""
    blocks: tuple[ContentBlock, ...] = ()
    schema_types: frozenset[str] = frozenset()
    target_query: str | None = None
    entities: frozenset[str] = field(default=frozenset())

    def __post_init__(self) -> None:
        if not self.url:
            raise ConfigurationError("PageContent.url is required")
        object.__setattr__(self, "schema_types", frozenset(s.strip().lower() for s in self.schema_types if s.strip()))
        object.__setattr__(self, "entities", frozenset(e.strip().lower() for e in self.entities if e.strip()))

    def of_kind(self, kind: BlockKind) -> tuple[ContentBlock, ...]:
        return tuple(b for b in self.blocks if b.kind is kind)

    @property
    def headings(self) -> tuple[str, ...]:
        return tuple(b.text for b in self.of_kind(BlockKind.HEADING))

    @property
    def questions(self) -> tuple[str, ...]:
        found = [b.text for b in self.blocks if b.kind in (BlockKind.HEADING, BlockKind.FAQ) and b.is_question]
        return tuple(dict.fromkeys(found))

    @property
    def total_words(self) -> int:
        return sum(b.word_count for b in self.blocks)

    @property
    def tables(self) -> int:
        return len(self.of_kind(BlockKind.TABLE))

    def first_paragraph(self) -> ContentBlock | None:
        for block in self.blocks:
            if block.kind is BlockKind.PARAGRAPH and block.text:
                return block
        return None

    def blocks_before_first_paragraph(self) -> int:
        for index, block in enumerate(self.blocks):
            if block.kind is BlockKind.PARAGRAPH and block.text:
                return index
        return len(self.blocks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "h1": self.h1,
            "blocks": len(self.blocks),
            "total_words": self.total_words,
            "schema_types": sorted(self.schema_types),
            "questions": list(self.questions),
        }


class _ContentHTMLParser(HTMLParser):
    """Pulls headings, paragraphs, lists, tables and JSON-LD types out of HTML."""

    _HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[ContentBlock] = []
        self.schema_types: set[str] = set()
        self.title = ""
        self.h1 = ""
        self._stack: list[str] = []
        self._buffer: list[str] = []
        self._list_items: list[str] = []
        self._script_type: str | None = None

    # -- helpers
    def _flush(self, kind: BlockKind, level: int = 0) -> None:
        text = " ".join(" ".join(self._buffer).split())
        self._buffer = []
        if not text and kind is not BlockKind.LIST:
            return
        if kind is BlockKind.HEADING:
            if level == 1 and not self.h1:
                self.h1 = text
            self.blocks.append(ContentBlock(BlockKind.HEADING, text, level=level))
        else:
            self.blocks.append(ContentBlock(kind, text))

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k.lower(): (v or "") for k, v in attrs}
        if tag == "script":
            self._script_type = attrs_dict.get("type", "").lower()
        if tag in ("ul", "ol"):
            self._list_items = []
        if tag == "table":
            self._buffer = []
        self._stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        text = " ".join(" ".join(self._buffer).split())
        if tag in self._HEADINGS:
            self._flush(BlockKind.HEADING, level=int(tag[1]))
        elif tag == "p":
            self._flush(BlockKind.PARAGRAPH)
        elif tag == "li":
            if text:
                self._list_items.append(text)
            self._buffer = []
        elif tag in ("ul", "ol"):
            if self._list_items:
                self.blocks.append(
                    ContentBlock(BlockKind.LIST, "", items=tuple(self._list_items))
                )
            self._list_items = []
            self._buffer = []
        elif tag == "table":
            self.blocks.append(ContentBlock(BlockKind.TABLE, text))
            self._buffer = []
        elif tag == "title":
            self.title = text
            self._buffer = []
        elif tag == "script":
            self._script_type = None
            self._buffer = []
        while self._stack and self._stack.pop() != tag:
            continue

    def handle_data(self, data: str) -> None:
        if self._script_type == "application/ld+json":
            self._collect_schema(data)
            return
        if self._stack and self._stack[-1] in ("script", "style"):
            return
        self._buffer.append(data)

    def _collect_schema(self, raw: str) -> None:
        try:
            payload = json.loads(raw)
        except (ValueError, TypeError):
            return
        for node in _iter_json_nodes(payload):
            if isinstance(node, dict) and "@type" in node:
                value = node["@type"]
                if isinstance(value, str):
                    self.schema_types.add(value.lower())
                elif isinstance(value, list):
                    self.schema_types.update(str(v).lower() for v in value)


def _iter_json_nodes(node: Any) -> Iterable[Any]:
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _iter_json_nodes(value)
    elif isinstance(node, list):
        for value in node:
            yield from _iter_json_nodes(value)


def parse_html(html: str, *, url: str, target_query: str | None = None) -> PageContent:
    """Parse a page into the AEO content model (stdlib only)."""
    parser = _ContentHTMLParser()
    parser.feed(html or "")
    parser.close()
    blocks = list(parser.blocks)
    if "faqpage" in parser.schema_types:
        blocks = [
            ContentBlock(BlockKind.FAQ, b.text, level=b.level, items=b.items)
            if b.kind is BlockKind.HEADING and b.is_question
            else b
            for b in blocks
        ]
    return PageContent(
        url=url,
        title=parser.title,
        h1=parser.h1,
        blocks=tuple(blocks),
        schema_types=frozenset(parser.schema_types),
        target_query=target_query,
    )
