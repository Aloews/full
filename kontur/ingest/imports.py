"""Importers.

Every importer takes an explicit :class:`~kontur.core.provenance.Provenance`.
There is no default, no "unknown source" fallback and no way to load a row
without saying where it came from and when it was retrieved (rule DATA-001).
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from kontur.core.errors import ConfigurationError, MissingProvenanceError
from kontur.core.provenance import Confidence, Provenance, Sourced
from kontur.engines.geo.models import AliceObservation, AliceSnapshot, AnswerType
from kontur.engines.getparams.models import ParamDemand, ParamObservation
from kontur.ingest.validation import (
    clean_identifier,
    clean_query,
    parse_bool,
    parse_date,
    parse_datetime,
    parse_float,
    parse_int,
    require_columns,
    split_list,
)


def provenance_from_manifest(manifest: Mapping[str, Any]) -> Provenance:
    """Build provenance from an export manifest, refusing incomplete ones."""
    missing = [key for key in ("source", "retrieved_at", "confidence") if not manifest.get(key)]
    if missing:
        raise MissingProvenanceError(
            f"export manifest is missing {', '.join(missing)}; "
            "an import without source + retrieval date + confidence is refused"
        )
    return Provenance(
        source=str(manifest["source"]),
        retrieved_at=parse_datetime(manifest["retrieved_at"], field="retrieved_at"),
        confidence=Confidence(str(manifest["confidence"]).lower()),
        source_url=manifest.get("source_url"),
        note=manifest.get("note"),
    )


def load_manifest(path: str | Path) -> Provenance:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return provenance_from_manifest(payload)


def read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _rows(source: Iterable[Mapping[str, Any]] | str | Path) -> Iterator[Mapping[str, Any]]:
    if isinstance(source, (str, Path)):
        yield from read_csv(source)
    else:
        yield from source


# --------------------------------------------------------------------- crawl
def import_param_observations(
    source: Iterable[Mapping[str, Any]] | str | Path, *, provenance: Provenance
) -> list[ParamObservation]:
    """Load per-parameter crawl statistics.

    Columns: ``parameter``, ``detected_urls``, ``distinct_values`` and the
    optional ``sample_values``, ``pages_with_param``, ``indexable_pages``.
    """
    if not isinstance(provenance, Provenance):
        raise MissingProvenanceError("import_param_observations() requires provenance")

    observations: list[ParamObservation] = []
    for index, row in enumerate(_rows(source), start=1):
        where = f"parameter row {index}"
        require_columns(row, ("parameter", "detected_urls", "distinct_values"), where=where)
        observations.append(
            ParamObservation(
                name=clean_identifier(row["parameter"], field=f"{where}.parameter", max_length=64),
                detected_urls=parse_int(row["detected_urls"], field=f"{where}.detected_urls"),
                distinct_values=parse_int(row["distinct_values"], field=f"{where}.distinct_values"),
                provenance=provenance,
                sample_values=split_list(row.get("sample_values"), field=f"{where}.sample_values"),
                pages_with_param=parse_int(row.get("pages_with_param") or 0, field=f"{where}.pages_with_param"),
                indexable_pages_with_param=parse_int(
                    row.get("indexable_pages") or 0, field=f"{where}.indexable_pages"
                ),
            )
        )
    return observations


# -------------------------------------------------------------------- demand
def import_param_demand(
    source: Iterable[Mapping[str, Any]] | str | Path, *, provenance: Provenance
) -> dict[str, Sourced]:
    """Load measured demand per parameter value and aggregate it per parameter.

    Columns: ``parameter``, ``value``, ``monthly_demand``.
    """
    if not isinstance(provenance, Provenance):
        raise MissingProvenanceError("import_param_demand() requires provenance")

    per_param: dict[str, list[tuple[str, float]]] = {}
    for index, row in enumerate(_rows(source), start=1):
        where = f"demand row {index}"
        require_columns(row, ("parameter", "value", "monthly_demand"), where=where)
        name = clean_identifier(row["parameter"], field=f"{where}.parameter", max_length=64).lower()
        value = clean_identifier(row["value"], field=f"{where}.value")
        volume = parse_float(row["monthly_demand"], field=f"{where}.monthly_demand", minimum=0.0)
        per_param.setdefault(name, []).append((value, volume))

    result: dict[str, Sourced] = {}
    for name, pairs in per_param.items():
        with_demand = [(v, d) for v, d in pairs if d > 0]
        result[name] = Sourced(
            ParamDemand(
                parameter=name,
                values_with_demand=len(with_demand),
                total_monthly_demand=sum(d for _, d in pairs),
                top_values=tuple(sorted(with_demand, key=lambda kv: -kv[1])[:10]),
            ),
            provenance,
        )
    return result


# ------------------------------------------------------- Alice AI visibility
@dataclass(frozen=True, slots=True)
class AliceImportResult:
    site: str
    snapshots: tuple[AliceSnapshot, ...]
    rows: int

    def weeks(self) -> tuple[date, ...]:
        return tuple(s.week_start for s in self.snapshots)


def import_alice_visibility(
    source: Iterable[Mapping[str, Any]] | str | Path,
    *,
    site: str,
    provenance: Provenance,
    reported_share_of_voice: Mapping[str, float] | None = None,
) -> AliceImportResult:
    """Load the Yandex Webmaster "visibility in Alice AI" export.

    Columns: ``query``, ``week``, plus the optional ``ai_answer``,
    ``our_domain_mentioned``, ``our_url``, ``competitors``, ``answer_type``,
    ``serp_position``, ``impressions``.
    """
    if not isinstance(provenance, Provenance):
        raise MissingProvenanceError(
            "import_alice_visibility() requires provenance: AI visibility figures "
            "without a source and retrieval date are not admissible"
        )

    by_week: dict[date, list[AliceObservation]] = {}
    total = 0
    for index, row in enumerate(_rows(source), start=1):
        where = f"alice row {index}"
        require_columns(row, ("query", "week"), where=where)
        week = parse_date(row["week"], field=f"{where}.week")
        url = row.get("our_url") or None
        observation = AliceObservation(
            query=clean_query(row["query"], field=f"{where}.query"),
            week_start=week,
            provenance=provenance,
            ai_answer_present=parse_bool(row.get("ai_answer"), field=f"{where}.ai_answer", default=True),
            our_domain_mentioned=parse_bool(
                row.get("our_domain_mentioned"), field=f"{where}.our_domain_mentioned", default=False
            ),
            our_url_cited=clean_identifier(url, field=f"{where}.our_url", max_length=512) if url else None,
            competitor_domains=split_list(row.get("competitors"), field=f"{where}.competitors"),
            answer_type=AnswerType(str(row.get("answer_type") or "unknown").strip().lower()),
            serp_position=(
                parse_int(row["serp_position"], field=f"{where}.serp_position", minimum=1)
                if row.get("serp_position")
                else None
            ),
            impressions=parse_int(row.get("impressions") or 0, field=f"{where}.impressions"),
        )
        by_week.setdefault(week, []).append(observation)
        total += 1

    if not by_week:
        raise ConfigurationError("the Alice export contains no rows")

    reported = {str(k): float(v) for k, v in (reported_share_of_voice or {}).items()}
    snapshots = tuple(
        AliceSnapshot(
            site=site,
            week_start=week,
            observations=tuple(observations),
            provenance=provenance,
            reported_share_of_voice=reported.get(week.isoformat()),
        )
        for week, observations in sorted(by_week.items())
    )
    return AliceImportResult(site=site, snapshots=snapshots, rows=total)


def import_serp_positions(
    source: Iterable[Mapping[str, Any]] | str | Path, *, provenance: Provenance
) -> dict[str, int]:
    """Load our organic position per query. Columns: ``query``, ``position``."""
    if not isinstance(provenance, Provenance):
        raise MissingProvenanceError("import_serp_positions() requires provenance")
    positions: dict[str, int] = {}
    for index, row in enumerate(_rows(source), start=1):
        where = f"serp row {index}"
        require_columns(row, ("query", "position"), where=where)
        positions[clean_query(row["query"], field=f"{where}.query")] = parse_int(
            row["position"], field=f"{where}.position", minimum=1
        )
    return positions


def write_csv(path: str | Path, rows: Sequence[Mapping[str, Any]], *, columns: Sequence[str]) -> None:
    with Path(path).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})
