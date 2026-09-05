"""SQLite persistence.

Provenance columns are part of every table: a row cannot be stored, and cannot
come back, without the source, the retrieval date and the confidence it was
imported with.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Sequence
from contextlib import closing
from datetime import date, datetime
from pathlib import Path
from typing import Any

from kontur.core.decisions import DecisionRecord
from kontur.core.errors import ConfigurationError
from kontur.core.provenance import Confidence, Provenance
from kontur.engines.geo.models import AliceObservation, AliceSnapshot, AnswerType
from kontur.engines.getparams.models import ParamObservation

SCHEMA = """
CREATE TABLE IF NOT EXISTS param_observations (
    name TEXT NOT NULL,
    detected_urls INTEGER NOT NULL,
    distinct_values INTEGER NOT NULL,
    sample_values TEXT NOT NULL DEFAULT '[]',
    source TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    confidence TEXT NOT NULL,
    PRIMARY KEY (name, source, retrieved_at)
);
CREATE TABLE IF NOT EXISTS decisions (
    url TEXT NOT NULL,
    decision TEXT NOT NULL,
    reasons TEXT NOT NULL,
    rules TEXT NOT NULL,
    canonical_target TEXT,
    redirect_target TEXT,
    confidence TEXT NOT NULL,
    is_sample INTEGER NOT NULL,
    decided_at TEXT NOT NULL,
    PRIMARY KEY (url, decided_at)
);
CREATE TABLE IF NOT EXISTS alice_observations (
    site TEXT NOT NULL,
    week_start TEXT NOT NULL,
    query TEXT NOT NULL,
    ai_answer_present INTEGER NOT NULL,
    our_domain_mentioned INTEGER NOT NULL,
    our_url_cited TEXT,
    competitor_domains TEXT NOT NULL,
    answer_type TEXT NOT NULL,
    serp_position INTEGER,
    impressions INTEGER NOT NULL,
    reported_sov REAL,
    source TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    confidence TEXT NOT NULL,
    PRIMARY KEY (site, week_start, query)
);
"""


def _provenance_of(row: sqlite3.Row) -> Provenance:
    return Provenance(
        source=row["source"],
        retrieved_at=datetime.fromisoformat(row["retrieved_at"]),
        confidence=Confidence(row["confidence"]),
    )


class KonturStore:
    """A thin, explicit SQLite store — no ORM, no hidden migrations."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self._connection = sqlite3.connect(self.path)
        self._connection.row_factory = sqlite3.Row
        with closing(self._connection.cursor()) as cursor:
            cursor.executescript(SCHEMA)
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> KonturStore:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    # ------------------------------------------------------------ parameters
    def save_param_observations(self, observations: Iterable[ParamObservation]) -> int:
        rows = [
            (
                o.name,
                o.detected_urls,
                o.distinct_values,
                json.dumps(list(o.sample_values), ensure_ascii=False),
                o.provenance.source,
                o.provenance.retrieved_at.isoformat(),
                o.provenance.confidence.value,
            )
            for o in observations
        ]
        with closing(self._connection.cursor()) as cursor:
            cursor.executemany(
                "INSERT OR REPLACE INTO param_observations "
                "(name, detected_urls, distinct_values, sample_values, source, retrieved_at, confidence) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
        self._connection.commit()
        return len(rows)

    def load_param_observations(self) -> list[ParamObservation]:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute("SELECT * FROM param_observations ORDER BY detected_urls DESC, name")
            return [
                ParamObservation(
                    name=row["name"],
                    detected_urls=row["detected_urls"],
                    distinct_values=row["distinct_values"],
                    provenance=_provenance_of(row),
                    sample_values=tuple(json.loads(row["sample_values"])),
                )
                for row in cursor.fetchall()
            ]

    # ------------------------------------------------------------- decisions
    def save_decisions(self, records: Sequence[DecisionRecord], *, decided_at: datetime | None = None) -> int:
        stamp = (decided_at or datetime.now()).isoformat(timespec="seconds")
        rows = [
            (
                r.url,
                r.decision.value,
                json.dumps([x.value for x in r.reasons]),
                json.dumps(list(r.rule_ids)),
                r.canonical_target,
                r.redirect_target,
                r.confidence.value,
                int(r.is_sample),
                stamp,
            )
            for r in records
        ]
        with closing(self._connection.cursor()) as cursor:
            cursor.executemany(
                "INSERT OR REPLACE INTO decisions (url, decision, reasons, rules, canonical_target, "
                "redirect_target, confidence, is_sample, decided_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
        self._connection.commit()
        return len(rows)

    def load_decisions(self, *, url: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM decisions"
        params: tuple[Any, ...] = ()
        if url:
            query += " WHERE url = ?"
            params = (url,)
        query += " ORDER BY decided_at DESC, url"
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(query, params)
            return [
                {
                    "url": row["url"],
                    "decision": row["decision"],
                    "reason": json.loads(row["reasons"]),
                    "rules": json.loads(row["rules"]),
                    "canonical_target": row["canonical_target"],
                    "redirect_target": row["redirect_target"],
                    "confidence": row["confidence"],
                    "is_sample": bool(row["is_sample"]),
                    "decided_at": row["decided_at"],
                }
                for row in cursor.fetchall()
            ]

    # ------------------------------------------------------ alice snapshots
    def save_alice_snapshot(self, snapshot: AliceSnapshot) -> int:
        rows = [
            (
                snapshot.site,
                snapshot.week_start.isoformat(),
                o.query,
                int(o.ai_answer_present),
                int(o.our_domain_mentioned),
                o.our_url_cited,
                json.dumps(list(o.competitor_domains), ensure_ascii=False),
                o.answer_type.value,
                o.serp_position,
                o.impressions,
                snapshot.reported_share_of_voice,
                o.provenance.source,
                o.provenance.retrieved_at.isoformat(),
                o.provenance.confidence.value,
            )
            for o in snapshot.observations
        ]
        with closing(self._connection.cursor()) as cursor:
            cursor.executemany(
                "INSERT OR REPLACE INTO alice_observations (site, week_start, query, ai_answer_present, "
                "our_domain_mentioned, our_url_cited, competitor_domains, answer_type, serp_position, "
                "impressions, reported_sov, source, retrieved_at, confidence) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
        self._connection.commit()
        return len(rows)

    def load_alice_snapshots(self, site: str) -> list[AliceSnapshot]:
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(
                "SELECT * FROM alice_observations WHERE site = ? ORDER BY week_start, query", (site,)
            )
            rows = cursor.fetchall()
        if not rows:
            return []

        by_week: dict[str, list[sqlite3.Row]] = {}
        for row in rows:
            by_week.setdefault(row["week_start"], []).append(row)

        snapshots: list[AliceSnapshot] = []
        for week, week_rows in sorted(by_week.items()):
            provenance = _provenance_of(week_rows[0])
            observations = tuple(
                AliceObservation(
                    query=row["query"],
                    week_start=date.fromisoformat(row["week_start"]),
                    provenance=_provenance_of(row),
                    ai_answer_present=bool(row["ai_answer_present"]),
                    our_domain_mentioned=bool(row["our_domain_mentioned"]),
                    our_url_cited=row["our_url_cited"],
                    competitor_domains=tuple(json.loads(row["competitor_domains"])),
                    answer_type=AnswerType(row["answer_type"]),
                    serp_position=row["serp_position"],
                    impressions=row["impressions"],
                )
                for row in week_rows
            )
            snapshots.append(
                AliceSnapshot(
                    site=site,
                    week_start=date.fromisoformat(week),
                    observations=observations,
                    provenance=provenance,
                    reported_share_of_voice=week_rows[0]["reported_sov"],
                )
            )
        return snapshots

    def counts(self) -> dict[str, int]:
        result: dict[str, int] = {}
        with closing(self._connection.cursor()) as cursor:
            for table in ("param_observations", "decisions", "alice_observations"):
                cursor.execute(f"SELECT COUNT(*) AS n FROM {table}")  # noqa: S608 - fixed table names
                result[table] = cursor.fetchone()["n"]
        return result


def open_store(path: str | Path = ":memory:") -> KonturStore:
    if isinstance(path, Path) and path.parent and not path.parent.exists():
        raise ConfigurationError(f"directory does not exist: {path.parent}")
    return KonturStore(path)
