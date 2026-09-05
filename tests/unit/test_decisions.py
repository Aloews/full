"""The decision envelope and conflict resolution."""

from __future__ import annotations

import pytest

from kontur.core.decisions import (
    Decision,
    DecisionRecord,
    ReasonCode,
    merge_decisions,
    most_restrictive,
)
from kontur.core.errors import ConfigurationError
from kontur.core.provenance import EvidenceSet

pytestmark = pytest.mark.unit


def record(decision: Decision, *reasons: ReasonCode, **kwargs) -> DecisionRecord:
    return DecisionRecord(url="/slots/megaways/", decision=decision, reasons=reasons, **kwargs)


def test_decision_without_a_reason_is_refused() -> None:
    with pytest.raises(ConfigurationError, match="no reason codes"):
        DecisionRecord(url="/slots/", decision=Decision.NOINDEX, reasons=())


def test_canonical_needs_a_target() -> None:
    with pytest.raises(ConfigurationError, match="canonical_target"):
        record(Decision.CANONICAL, ReasonCode.DUPLICATE_CONTENT)


def test_redirect_needs_a_target() -> None:
    with pytest.raises(ConfigurationError, match="redirect_target"):
        record(Decision.REDIRECT, ReasonCode.DEPRECATED_FACET)


def test_url_is_required() -> None:
    with pytest.raises(ConfigurationError):
        DecisionRecord(url="", decision=Decision.INDEX, reasons=(ReasonCode.SEARCH_DEMAND,))


@pytest.mark.parametrize(
    ("decisions", "expected"),
    [
        ([Decision.INDEX, Decision.CANONICAL], Decision.CANONICAL),
        ([Decision.CANONICAL, Decision.REDIRECT], Decision.REDIRECT),
        ([Decision.REDIRECT, Decision.NOINDEX], Decision.NOINDEX),
        ([Decision.NOINDEX, Decision.BLOCK], Decision.BLOCK),
        ([Decision.INDEX], Decision.INDEX),
    ],
)
def test_restrictiveness_lattice(decisions, expected) -> None:
    assert most_restrictive(decisions) is expected


def test_most_restrictive_needs_input() -> None:
    with pytest.raises(ConfigurationError):
        most_restrictive([])


def test_merging_keeps_every_reason_and_the_strictest_verdict() -> None:
    merged = merge_decisions(
        [
            record(Decision.INDEX, ReasonCode.SEARCH_DEMAND),
            record(Decision.NOINDEX, ReasonCode.THIN_CONTENT),
        ]
    )
    assert merged.decision is Decision.NOINDEX
    assert set(merged.reasons) == {ReasonCode.SEARCH_DEMAND, ReasonCode.THIN_CONTENT}


def test_merging_across_urls_is_refused() -> None:
    with pytest.raises(ConfigurationError, match="different URLs"):
        merge_decisions(
            [
                record(Decision.INDEX, ReasonCode.SEARCH_DEMAND),
                DecisionRecord(url="/other/", decision=Decision.INDEX, reasons=(ReasonCode.SEARCH_DEMAND,)),
            ]
        )


def test_merging_nothing_is_refused() -> None:
    with pytest.raises(ConfigurationError):
        merge_decisions([])


def test_confidence_comes_from_the_evidence(crawl_provenance, sample_provenance) -> None:
    strong = record(Decision.INDEX, ReasonCode.SEARCH_DEMAND, evidence=EvidenceSet.of(crawl_provenance))
    weak = record(Decision.INDEX, ReasonCode.SEARCH_DEMAND, evidence=EvidenceSet.of(sample_provenance))
    assert strong.confidence.rank > weak.confidence.rank
    assert weak.is_sample is True


def test_the_restrictiveness_table_is_exact() -> None:
    """Consumers compare these numbers; the values themselves are the contract."""
    from kontur.core.decisions import DECISION_RESTRICTIVENESS

    assert DECISION_RESTRICTIVENESS == {
        Decision.INDEX: 0,
        Decision.CANONICAL: 1,
        Decision.REDIRECT: 2,
        Decision.NOINDEX: 3,
        Decision.BLOCK: 4,
    }


def test_the_merged_record_takes_its_target_from_the_winning_verdict() -> None:
    merged = merge_decisions(
        [
            record(Decision.INDEX, ReasonCode.SEARCH_DEMAND),
            record(Decision.CANONICAL, ReasonCode.DUPLICATE_CONTENT, canonical_target="/slots/"),
        ]
    )
    assert merged.decision is Decision.CANONICAL
    assert merged.canonical_target == "/slots/", "the target came from a losing record"


def test_merging_collects_every_rule_id_exactly_once() -> None:
    merged = merge_decisions(
        [
            record(Decision.INDEX, ReasonCode.SEARCH_DEMAND, rule_ids=("FACET-007",)),
            record(Decision.NOINDEX, ReasonCode.THIN_CONTENT, rule_ids=("FACET-003", "FACET-007")),
        ]
    )
    assert merged.rule_ids == ("FACET-007", "FACET-003")


def test_merging_collects_every_reason_exactly_once() -> None:
    merged = merge_decisions(
        [
            record(Decision.NOINDEX, ReasonCode.THIN_CONTENT),
            record(Decision.NOINDEX, ReasonCode.THIN_CONTENT, ReasonCode.EMPTY_RESULT_SET),
        ]
    )
    assert merged.reasons == (ReasonCode.THIN_CONTENT, ReasonCode.EMPTY_RESULT_SET)
