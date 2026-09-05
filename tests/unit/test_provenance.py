"""Provenance is the boundary where fabricated data is stopped."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from kontur.core.errors import (
    InvalidProvenanceError,
    MissingProvenanceError,
    SampleDataError,
)
from kontur.core.provenance import (
    Confidence,
    EvidenceSet,
    Provenance,
    Sourced,
    reject_sample_data,
    require_provenance,
)

pytestmark = pytest.mark.unit


@pytest.mark.rule("DATA-001")
@pytest.mark.positive
def test_sourced_value_keeps_its_provenance(crawl_provenance: Provenance) -> None:
    sourced = Sourced(48210, crawl_provenance)
    assert require_provenance(sourced) is sourced
    assert sourced.provenance.source == "crawl:site_audit"
    assert sourced.confidence is Confidence.HIGH


@pytest.mark.rule("DATA-001")
@pytest.mark.negative
def test_bare_value_is_refused_at_the_boundary() -> None:
    with pytest.raises(MissingProvenanceError, match="source \\+ retrieved_at \\+ confidence"):
        require_provenance(48210, what="detected_urls")


@pytest.mark.rule("DATA-001")
@pytest.mark.negative
@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"source": ""}, MissingProvenanceError),
        ({"source": "  "}, MissingProvenanceError),
        ({"source": "Bad Source!"}, InvalidProvenanceError),
        ({"retrieved_at": datetime.now(UTC) + timedelta(days=2)}, InvalidProvenanceError),
        ({"confidence": "probably"}, InvalidProvenanceError),
    ],
)
def test_incomplete_provenance_is_rejected(kwargs: dict, expected: type[Exception]) -> None:
    base = {
        "source": "crawl:site_audit",
        "retrieved_at": datetime.now(UTC),
        "confidence": Confidence.HIGH,
    }
    with pytest.raises(expected):
        Provenance(**{**base, **kwargs})


@pytest.mark.rule("DATA-002")
@pytest.mark.positive
def test_sample_mark_propagates_through_evidence(sample_provenance, crawl_provenance) -> None:
    evidence = EvidenceSet.of(crawl_provenance, sample_provenance)
    assert evidence.is_sample is True
    assert evidence.confidence is Confidence.LOW, "a set is only as strong as its weakest fact"


@pytest.mark.rule("DATA-002")
@pytest.mark.negative
def test_real_evidence_is_not_marked_as_sample(crawl_provenance, alice_provenance) -> None:
    evidence = EvidenceSet.of(crawl_provenance, alice_provenance)
    assert evidence.is_sample is False
    reject_sample_data(evidence, what="AI visibility report")


@pytest.mark.rule("DATA-002")
@pytest.mark.negative
def test_sample_data_is_refused_where_measurements_are_required(sample_provenance) -> None:
    with pytest.raises(SampleDataError, match="sample:crawl"):
        reject_sample_data(EvidenceSet.of(sample_provenance), what="AI visibility report")


def test_evidence_merge_deduplicates(crawl_provenance) -> None:
    merged = EvidenceSet.of(crawl_provenance).merge(EvidenceSet.of(crawl_provenance))
    assert len(merged) == 1


def test_provenance_age_is_measured_in_days(crawl_provenance) -> None:
    assert 1.5 < crawl_provenance.age_days() < 2.5


def test_confidence_ordering_is_total() -> None:
    assert Confidence.weakest([Confidence.HIGH, Confidence.LOW, Confidence.MEDIUM]) is Confidence.LOW
    assert Confidence.weakest([]) is Confidence.LOW


# ------------------------------------------------------------ time handling
def test_confidence_ranks_are_fixed() -> None:
    """The ranks are compared numerically all over the platform."""
    assert Confidence.LOW.rank == 1
    assert Confidence.MEDIUM.rank == 2
    assert Confidence.HIGH.rank == 3


def test_a_naive_timestamp_is_read_as_utc() -> None:

    provenance = Provenance("crawl:site_audit", datetime(2026, 8, 1, 12, 0), Confidence.HIGH)
    assert provenance.retrieved_at == datetime(2026, 8, 1, 12, 0, tzinfo=UTC)


def test_an_offset_timestamp_is_converted_not_relabelled() -> None:
    moscow = timezone(timedelta(hours=3))
    provenance = Provenance(
        "crawl:site_audit", datetime(2026, 8, 1, 12, 0, tzinfo=moscow), Confidence.HIGH
    )
    assert provenance.retrieved_at == datetime(2026, 8, 1, 9, 0, tzinfo=UTC)


def test_an_iso_string_is_accepted() -> None:
    provenance = Provenance("crawl:site_audit", "2026-08-01T12:00:00+00:00", Confidence.HIGH)
    assert provenance.retrieved_at.isoformat() == "2026-08-01T12:00:00+00:00"


def test_a_malformed_timestamp_is_rejected() -> None:
    with pytest.raises(InvalidProvenanceError, match="ISO-8601"):
        Provenance("crawl:site_audit", "the first of August", Confidence.HIGH)
    with pytest.raises(InvalidProvenanceError, match="date/datetime"):
        Provenance("crawl:site_audit", 1754049600, Confidence.HIGH)


def test_a_plain_date_is_accepted() -> None:
    from datetime import date

    provenance = Provenance("crawl:site_audit", date(2026, 8, 1), Confidence.HIGH)
    assert provenance.retrieved_at == datetime(2026, 8, 1, tzinfo=UTC)


def test_age_is_measured_in_exact_days() -> None:
    provenance = Provenance(
        "crawl:site_audit", datetime(2026, 8, 1, tzinfo=UTC), Confidence.HIGH
    )
    age = provenance.age_days(now=datetime(2026, 8, 3, tzinfo=UTC))
    assert age == pytest.approx(2.0, abs=1e-9)


def test_age_accepts_a_naive_reference_time() -> None:
    provenance = Provenance(
        "crawl:site_audit", datetime(2026, 8, 1, tzinfo=UTC), Confidence.HIGH
    )
    assert provenance.age_days(now=datetime(2026, 8, 3)) == pytest.approx(2.0, abs=1e-9)


def test_evidence_of_nothing_is_empty(crawl_provenance) -> None:
    assert len(EvidenceSet.of(None, None)) == 0
    assert len(EvidenceSet.of(crawl_provenance, None)) == 1
    with pytest.raises(MissingProvenanceError):
        EvidenceSet.of("not provenance")
