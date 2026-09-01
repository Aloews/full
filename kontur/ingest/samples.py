"""Deterministic sample data for development and the demo dashboard.

Every provenance produced here starts with ``sample:``, which makes
:attr:`Provenance.is_sample` true and propagates through every derived report.
The dashboard renders a warning banner for sample-backed panels and
:func:`kontur.engines.geo.metrics.build_report` refuses to produce a
"real measurement" report from it. There is no code path that turns sample data
into a reported Yandex figure.
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone
from typing import Any

from kontur.core.provenance import Confidence, Provenance, Sourced
from kontur.engines.faceted.models import FilterInventory
from kontur.engines.faceted.signals import BusinessValue, IntentAssessment, IntentLabel, SearchDemand
from kontur.engines.geo.models import AliceObservation, AliceSnapshot, AnswerType
from kontur.engines.getparams.models import ParamDemand, ParamObservation

SAMPLE_SITE = "casino.example"
_SEED = 20260401


def sample_provenance(kind: str, *, days_ago: int = 3, confidence: Confidence = Confidence.LOW) -> Provenance:
    return Provenance(
        source=f"sample:{kind}",
        retrieved_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
        confidence=confidence,
        note="Generated fixture. Not a measurement.",
    )


def sample_param_observations() -> list[ParamObservation]:
    provenance = sample_provenance("crawl")
    rows = [
        ("utm_source", 48210, 137),
        ("utm_medium", 47980, 12),
        ("gclid", 21300, 21300),
        ("sort", 12440, 6),
        ("page", 9100, 64),
        ("provider", 4812, 48),
        ("mechanic", 1290, 22),
        ("rtp", 840, 9),
        ("volatility", 610, 3),
        ("bonus-buy", 430, 2),
        ("phpsessid", 380, 380),
        ("promo_widget", 210, 5),
    ]
    return [
        ParamObservation(name=name, detected_urls=urls, distinct_values=values, provenance=provenance)
        for name, urls, values in rows
    ]


def sample_param_demand() -> dict[str, Sourced]:
    provenance = sample_provenance("demand", confidence=Confidence.LOW)
    demand = {
        "mechanic": ParamDemand("mechanic", 7, 5400.0, (("megaways", 3200.0), ("cluster", 1100.0))),
        "provider": ParamDemand("provider", 22, 31000.0, (("pragmatic", 12000.0), ("novomatic", 4400.0))),
        "rtp": ParamDemand("rtp", 1, 40.0, (("96plus", 40.0),)),
        "volatility": ParamDemand("volatility", 3, 890.0, (("high", 520.0), ("low", 220.0))),
        "bonus-buy": ParamDemand("bonus-buy", 2, 260.0, (("yes", 240.0),)),
        "promo_widget": ParamDemand("promo_widget", 0, 0.0, ()),
    }
    return {name: Sourced(value, provenance) for name, value in demand.items()}


def sample_filter_states() -> dict[str, dict[str, Any]]:
    """Per filter-state demand / intent / inventory / business value."""
    provenance = sample_provenance("analytics")
    demand_provenance = sample_provenance("demand")
    return {
        "/slots/?mechanic=megaways": {
            "demand": Sourced(SearchDemand(3200.0, 46, "megaways слоты"), demand_provenance),
            "intent": IntentAssessment(IntentLabel.COMMERCIAL, 0.22, 0.71),
            "inventory": Sourced(FilterInventory(84, 71, 3, pages=4), provenance),
            "business": Sourced(BusinessValue(70, 84, 0.62), provenance),
        },
        "/slots/?provider=pragmatic": {
            "demand": Sourced(SearchDemand(12000.0, 120, "pragmatic play слоты"), demand_provenance),
            "intent": IntentAssessment(IntentLabel.COMMERCIAL, 0.31, 0.66),
            "inventory": Sourced(FilterInventory(210, 198, 4, pages=9), provenance),
            "business": Sourced(BusinessValue(180, 210, 0.71), provenance),
        },
        "/slots/?rtp=96plus": {
            "demand": Sourced(SearchDemand(40.0, 3, "слоты с rtp 96"), demand_provenance),
            "intent": IntentAssessment(IntentLabel.MIXED, 0.86, 0.12),
            "inventory": Sourced(FilterInventory(160, 22, 0, pages=7), provenance),
            "business": Sourced(BusinessValue(40, 160, 0.10), provenance),
        },
        "/slots/?volatility=high": {
            "demand": Sourced(SearchDemand(520.0, 18, "слоты с высокой волатильностью"), demand_provenance),
            "intent": IntentAssessment(IntentLabel.COMMERCIAL, 0.44, 0.51),
            "inventory": Sourced(FilterInventory(96, 63, 2, pages=4), provenance),
            "business": Sourced(BusinessValue(72, 96, 0.44), provenance),
        },
        "/slots/?bonus-buy=yes": {
            "demand": Sourced(SearchDemand(240.0, 11, "слоты с покупкой бонуса"), demand_provenance),
            "intent": IntentAssessment(IntentLabel.COMMERCIAL, 0.38, 0.58),
            "inventory": Sourced(FilterInventory(48, 41, 2, pages=2), provenance),
            "business": Sourced(BusinessValue(39, 48, 0.51), provenance),
        },
        "/slots/?mechanic=cluster": {
            "demand": Sourced(SearchDemand(1100.0, 22, "кластерные слоты"), demand_provenance),
            "intent": IntentAssessment(IntentLabel.COMMERCIAL, 0.29, 0.63),
            "inventory": Sourced(FilterInventory(37, 30, 2, pages=2), provenance),
            "business": Sourced(BusinessValue(28, 37, 0.40), provenance),
        },
    }


def sample_alice_snapshots(*, weeks: int = 8) -> list[AliceSnapshot]:
    """Weekly Alice AI visibility fixtures for the last ``weeks`` weeks."""
    provenance = sample_provenance("alice_visibility")
    rng = random.Random(_SEED)
    queries = [
        ("что такое megaways", "https://casino.example/slots/megaways/", AnswerType.GENERATED),
        ("слоты pragmatic play", "https://casino.example/slots/?provider=pragmatic", AnswerType.LIST),
        ("что такое rtp в слотах", None, AnswerType.SUMMARY),
        ("слоты с покупкой бонуса", "https://casino.example/slots/?bonus-buy=yes", AnswerType.LIST),
        ("как работает волатильность слотов", None, AnswerType.GENERATED),
    ]
    competitors = ["rival-one.example", "rival-two.example", "wiki.example", "forum.example"]

    monday = date.today() - timedelta(days=date.today().weekday())
    snapshots: list[AliceSnapshot] = []
    for index in range(weeks):
        week_start = monday - timedelta(weeks=weeks - 1 - index)
        observations: list[AliceObservation] = []
        for query, our_url, answer_type in queries:
            mentioned = our_url is not None and rng.random() < 0.35 + 0.05 * index
            sources = rng.sample(competitors, k=rng.randint(1, 3))
            observations.append(
                AliceObservation(
                    query=query,
                    week_start=week_start,
                    provenance=provenance,
                    ai_answer_present=rng.random() < 0.92,
                    our_domain_mentioned=mentioned,
                    our_url_cited=our_url if mentioned else None,
                    competitor_domains=tuple(sources),
                    answer_type=answer_type,
                    serp_position=rng.randint(1, 12),
                    impressions=rng.randint(50, 900),
                )
            )
        snapshots.append(
            AliceSnapshot(
                site=SAMPLE_SITE,
                week_start=week_start,
                observations=tuple(observations),
                provenance=provenance,
                reported_share_of_voice=round(0.07 + 0.004 * index, 4),
            )
        )
    return snapshots


def sample_serp_positions() -> dict[str, int]:
    return {
        "что такое megaways": 3,
        "слоты pragmatic play": 6,
        "что такое rtp в слотах": 11,
        "слоты с покупкой бонуса": 8,
        "как работает волатильность слотов": 14,
    }
