"""Backlink risk analysis.

This module *analyses* a link profile and reports how much manipulation
footprint it carries. It does not build, buy, register or recommend networks,
and it never emits a target share of links from any source type. Kontur is an
analysis platform; producing link schemes is out of scope by design (rule
LINK-001), and the security suite asserts that no builder-shaped function is
ever added here.

Factors, each normalised to [0, 1]:

    footprint            shared hosting / registrar / analytics / template
    anchor_concentration how concentrated the anchor text distribution is
    commercial_anchors   share of money anchors
    velocity             burstiness of link acquisition
    content_similarity   how alike the donor pages are
    topical_distance     how far the donors are from our topic
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any

from kontur.core.errors import ConfigurationError, InsufficientDataError
from kontur.core.provenance import EvidenceSet, Provenance
from kontur.core.registry import rule_ids


class RiskLevel(StrEnum):
    LOW = "LOW RISK"
    MEDIUM = "MEDIUM RISK"
    HIGH = "HIGH RISK"


class AnchorType(StrEnum):
    BRAND = "brand"
    URL = "url"
    GENERIC = "generic"
    COMMERCIAL = "commercial"
    IMAGE = "image"


@dataclass(frozen=True, slots=True)
class Backlink:
    """One inbound link and the ownership signals visible around it."""

    source_domain: str
    target_url: str
    anchor: str
    anchor_type: AnchorType
    first_seen: date
    dofollow: bool = True
    ip_c_class: str | None = None
    registrar: str | None = None
    analytics_id: str | None = None
    template_hash: str | None = None
    topical_relevance: float = 1.0
    content_similarity: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_domain", self.source_domain.strip().lower().removeprefix("www."))
        object.__setattr__(self, "anchor_type", AnchorType(self.anchor_type))
        for name in ("topical_relevance", "content_similarity"):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ConfigurationError(f"{name} must be within [0, 1], got {value}")


@dataclass(frozen=True, slots=True)
class RiskFactor:
    name: str
    value: float
    weight: float
    explanation: str

    def __post_init__(self) -> None:
        if not 0.0 <= self.value <= 1.0:
            raise ConfigurationError(f"risk factor {self.name} must be within [0, 1]")
        if self.weight <= 0:
            raise ConfigurationError(f"risk factor {self.name} needs a positive weight")

    def to_dict(self) -> dict[str, Any]:
        return {
            "factor": self.name,
            "value": round(self.value, 4),
            "weight": self.weight,
            "explanation": self.explanation,
        }


FACTOR_WEIGHTS: dict[str, float] = {
    "footprint": 0.30,
    "anchor_concentration": 0.20,
    "commercial_anchors": 0.20,
    "velocity": 0.15,
    "content_similarity": 0.10,
    "topical_distance": 0.05,
}


def _herfindahl(counts: Iterable[int]) -> float:
    values = [c for c in counts if c > 0]
    total = sum(values)
    if total == 0:
        return 0.0
    shares = [c / total for c in values]
    hhi = sum(s * s for s in shares)
    n = len(values)
    if n == 1:
        return 1.0
    # Rescale so a perfectly even distribution is 0 and a single anchor is 1.
    return max(0.0, min(1.0, (hhi - 1.0 / n) / (1.0 - 1.0 / n)))


def _cluster_share(values: Sequence[str | None]) -> float:
    present = [v for v in values if v]
    if not present:
        return 0.0
    counts = Counter(present)
    return max(counts.values()) / len(values)


def footprint_factor(links: Sequence[Backlink]) -> RiskFactor:
    """Shared hosting, registrar, analytics id or page template across donors."""
    signals = {
        "IP C-class": _cluster_share([link.ip_c_class for link in links]),
        "registrar": _cluster_share([link.registrar for link in links]),
        "analytics id": _cluster_share([link.analytics_id for link in links]),
        "template": _cluster_share([link.template_hash for link in links]),
    }
    strongest_name, strongest = max(signals.items(), key=lambda kv: kv[1])
    return RiskFactor(
        name="footprint",
        value=strongest,
        weight=FACTOR_WEIGHTS["footprint"],
        explanation=(
            f"{strongest:.0%} of donors share the same {strongest_name}"
            if strongest > 0
            else "no shared ownership signal detected across donors"
        ),
    )


def anchor_concentration_factor(links: Sequence[Backlink]) -> RiskFactor:
    counts = Counter(link.anchor.strip().lower() for link in links if link.anchor.strip())
    value = _herfindahl(counts.values())
    top = counts.most_common(1)[0] if counts else ("", 0)
    return RiskFactor(
        name="anchor_concentration",
        value=value,
        weight=FACTOR_WEIGHTS["anchor_concentration"],
        explanation=(
            f"most frequent anchor {top[0]!r} used by {top[1]} of {len(links)} links"
            if counts
            else "no anchor text captured"
        ),
    )


def commercial_anchor_factor(links: Sequence[Backlink]) -> RiskFactor:
    commercial = sum(1 for link in links if link.anchor_type is AnchorType.COMMERCIAL)
    share = commercial / len(links) if links else 0.0
    return RiskFactor(
        name="commercial_anchors",
        value=share,
        weight=FACTOR_WEIGHTS["commercial_anchors"],
        explanation=f"{share:.0%} of anchors are commercial ({commercial}/{len(links)})",
    )


def velocity_factor(links: Sequence[Backlink], *, window_days: int = 30) -> RiskFactor:
    """Burstiness: how much the biggest acquisition month exceeds the typical one."""
    if window_days < 1:
        raise ConfigurationError("window_days must be >= 1")
    if not links:
        return RiskFactor("velocity", 0.0, FACTOR_WEIGHTS["velocity"], "no links to profile")

    buckets: Counter[int] = Counter()
    earliest = min(link.first_seen for link in links)
    for link in links:
        buckets[(link.first_seen - earliest).days // window_days] += 1

    counts = sorted(buckets.values())
    peak = counts[-1]
    typical = counts[len(counts) // 2] if counts else 0
    if typical == 0:
        value = 1.0 if peak >= 5 and len(counts) > 1 else 0.0
    else:
        value = max(0.0, min(1.0, (peak / typical - 1.0) / 4.0))
    return RiskFactor(
        name="velocity",
        value=value,
        weight=FACTOR_WEIGHTS["velocity"],
        explanation=f"peak {peak} links per {window_days}d vs typical {typical}",
    )


def content_similarity_factor(links: Sequence[Backlink]) -> RiskFactor:
    values = [link.content_similarity for link in links]
    mean = sum(values) / len(values) if values else 0.0
    return RiskFactor(
        name="content_similarity",
        value=mean,
        weight=FACTOR_WEIGHTS["content_similarity"],
        explanation=f"average donor-page similarity {mean:.2f}",
    )


def topical_distance_factor(links: Sequence[Backlink]) -> RiskFactor:
    values = [1.0 - link.topical_relevance for link in links]
    mean = sum(values) / len(values) if values else 0.0
    return RiskFactor(
        name="topical_distance",
        value=mean,
        weight=FACTOR_WEIGHTS["topical_distance"],
        explanation=f"average topical distance from our subject {mean:.2f}",
    )


def backlink_risk_score(factors: Sequence[RiskFactor]) -> float:
    """Weighted mean of the risk factors, bounded to [0, 1]."""
    if not factors:
        raise InsufficientDataError("backlink_risk_score needs at least one factor")
    total_weight = sum(f.weight for f in factors)
    if total_weight <= 0:
        raise ConfigurationError("factor weights must sum to a positive number")
    score = sum(f.value * f.weight for f in factors) / total_weight
    return min(1.0, max(0.0, score))


def classify_risk(score: float) -> RiskLevel:
    if not 0.0 <= score <= 1.0:
        raise ConfigurationError(f"score must be within [0, 1], got {score}")
    if score < 0.34:
        return RiskLevel.LOW
    if score < 0.67:
        return RiskLevel.MEDIUM
    return RiskLevel.HIGH


@dataclass(frozen=True, slots=True)
class BacklinkRiskReport:
    target: str
    links_analysed: int
    donors: int
    score: float
    level: RiskLevel
    factors: tuple[RiskFactor, ...]
    evidence: EvidenceSet = field(default_factory=EvidenceSet)
    rule_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "links_analysed": self.links_analysed,
            "donors": self.donors,
            "risk_score": round(self.score, 4),
            "risk_level": self.level.value,
            "factors": [f.to_dict() for f in self.factors],
            "rules": list(self.rule_ids),
            "evidence": self.evidence.to_list(),
            "scope": (
                "Risk classification only. This module does not build, buy or "
                "recommend link networks."
            ),
        }


def analyse_backlinks(
    target: str,
    links: Sequence[Backlink],
    *,
    provenance: Provenance,
    window_days: int = 30,
) -> BacklinkRiskReport:
    """Classify the manipulation footprint of a link profile."""
    if not links:
        raise InsufficientDataError("a link profile needs at least one backlink")
    if not isinstance(provenance, Provenance):
        raise ConfigurationError("backlink analysis requires provenance for the link export")

    factors = (
        footprint_factor(links),
        anchor_concentration_factor(links),
        commercial_anchor_factor(links),
        velocity_factor(links, window_days=window_days),
        content_similarity_factor(links),
        topical_distance_factor(links),
    )
    score = backlink_risk_score(factors)
    return BacklinkRiskReport(
        target=target,
        links_analysed=len(links),
        donors=len({link.source_domain for link in links}),
        score=score,
        level=classify_risk(score),
        factors=factors,
        evidence=EvidenceSet.of(provenance),
        rule_ids=rule_ids("LINK-001", "LINK-002", "LINK-003"),
    )


__all__ = [
    "AnchorType",
    "Backlink",
    "BacklinkRiskReport",
    "RiskFactor",
    "RiskLevel",
    "analyse_backlinks",
    "anchor_concentration_factor",
    "backlink_risk_score",
    "classify_risk",
    "commercial_anchor_factor",
    "content_similarity_factor",
    "footprint_factor",
    "topical_distance_factor",
    "velocity_factor",
]
