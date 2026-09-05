"""Shared fixtures.

Real-looking provenance is used wherever a test needs data that must be
accepted as a measurement; ``sample:`` provenance is used wherever a test needs
to prove that fixtures cannot be passed off as measurements.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from kontur.core.provenance import Confidence, Provenance, Sourced
from kontur.engines.faceted.models import (
    IGAMING_SLOTS_CATALOG,
    FacetConfig,
    FilterInventory,
)
from kontur.engines.faceted.pipeline import FacetedIndexationEngine
from kontur.engines.faceted.providers import MappingProvider
from kontur.engines.faceted.signals import (
    BusinessValue,
    IntentAssessment,
    IntentLabel,
    SearchDemand,
)
from kontur.engines.geo.models import AliceObservation, AliceSnapshot
from kontur.engines.geo.snapshots import SnapshotStore
from kontur.engines.getparams.controller import GetParameterController
from kontur.engines.getparams.models import ParamDemand, ParamObservation
from kontur.workspace import Workspace

MEGAWAYS = "/slots/?mechanic=megaways"


@pytest.fixture
def crawl_provenance() -> Provenance:
    return Provenance(
        source="crawl:site_audit",
        retrieved_at=datetime.now(UTC) - timedelta(days=2),
        confidence=Confidence.HIGH,
    )


@pytest.fixture
def demand_provenance() -> Provenance:
    return Provenance(
        source="wordstat:export",
        retrieved_at=datetime.now(UTC) - timedelta(days=5),
        confidence=Confidence.MEDIUM,
    )


@pytest.fixture
def alice_provenance() -> Provenance:
    return Provenance(
        source="yandex_webmaster:alice_visibility",
        retrieved_at=datetime.now(UTC) - timedelta(days=1),
        confidence=Confidence.HIGH,
    )


@pytest.fixture
def sample_provenance() -> Provenance:
    return Provenance(
        source="sample:crawl",
        retrieved_at=datetime.now(UTC) - timedelta(days=1),
        confidence=Confidence.LOW,
    )


@pytest.fixture
def observation(crawl_provenance: Provenance):
    def build(name: str, detected_urls: int = 100, distinct_values: int = 10) -> ParamObservation:
        return ParamObservation(
            name=name,
            detected_urls=detected_urls,
            distinct_values=distinct_values,
            provenance=crawl_provenance,
        )

    return build


@pytest.fixture
def demand(demand_provenance: Provenance):
    def build(parameter: str, values: int = 5, total: float = 1000.0) -> Sourced:
        return Sourced(ParamDemand(parameter, values, total), demand_provenance)

    return build


@pytest.fixture
def controller(observation, demand) -> GetParameterController:
    ctrl = GetParameterController()
    ctrl.observe(
        [
            observation("utm_source", 48210, 137),
            observation("sort", 12440, 6),
            observation("page", 9100, 64),
            observation("mechanic", 1290, 22),
            observation("rtp", 840, 9),
            observation("phpsessid", 380, 380),
            observation("promo_widget", 210, 5),
        ]
    )
    ctrl.set_demand("mechanic", demand("mechanic", 7, 5400.0))
    ctrl.set_demand("rtp", demand("rtp", 1, 40.0))
    return ctrl


@pytest.fixture
def indexable_state(crawl_provenance: Provenance, demand_provenance: Provenance) -> dict:
    """A filter state that satisfies every INDEX signal."""
    return {
        "demand": Sourced(SearchDemand(3200.0, 46, "megaways слоты"), demand_provenance),
        "intent": IntentAssessment(IntentLabel.COMMERCIAL, 0.22, 0.71),
        "inventory": Sourced(FilterInventory(84, 71, 3, pages=4), crawl_provenance),
        "business": Sourced(BusinessValue(70, 84, 0.62), crawl_provenance),
    }


@pytest.fixture
def facet_engine(controller: GetParameterController, indexable_state: dict):
    """Engine factory: pass overrides to model a different filter state."""

    def build(state: dict | None = None, *, url: str = MEGAWAYS, config: FacetConfig | None = None):
        merged = {**indexable_state, **(state or {})}
        return FacetedIndexationEngine(
            catalog=IGAMING_SLOTS_CATALOG,
            parameters=controller,
            config=config or FacetConfig(),
            demand=MappingProvider({url: merged.get("demand")} if merged.get("demand") else {}),
            intent=MappingProvider({url: merged.get("intent")} if merged.get("intent") else {}),
            inventory=MappingProvider({url: merged.get("inventory")} if merged.get("inventory") else {}),
            business=MappingProvider({url: merged.get("business")} if merged.get("business") else {}),
            serp=MappingProvider({url: merged.get("serp")} if merged.get("serp") else {}),
        )

    return build


@pytest.fixture
def alice_snapshots(alice_provenance: Provenance) -> list[AliceSnapshot]:
    """Four weeks where our domain gains a citation for one query."""
    weeks = [date(2026, 7, 6) + timedelta(weeks=i) for i in range(4)]
    snapshots: list[AliceSnapshot] = []
    for index, week in enumerate(weeks):
        observations = (
            AliceObservation(
                query="что такое megaways",
                week_start=week,
                provenance=alice_provenance,
                our_domain_mentioned=index >= 2,
                our_url_cited="https://casino.example/slots/megaways/" if index >= 2 else None,
                competitor_domains=("rival-one.example", "rival-two.example"),
                serp_position=4,
            ),
            AliceObservation(
                query="слоты с покупкой бонуса",
                week_start=week,
                provenance=alice_provenance,
                our_domain_mentioned=False,
                competitor_domains=("rival-one.example", "rival-three.example"),
            ),
        )
        snapshots.append(
            AliceSnapshot(
                site="casino.example",
                week_start=week,
                observations=observations,
                provenance=alice_provenance,
                reported_share_of_voice=0.10 + 0.01 * index,
            )
        )
    return snapshots


@pytest.fixture
def snapshot_store(alice_snapshots: list[AliceSnapshot]) -> SnapshotStore:
    store = SnapshotStore()
    for snapshot in alice_snapshots:
        store.add(snapshot)
    return store


@pytest.fixture
def workspace(controller: GetParameterController, alice_snapshots, indexable_state) -> Workspace:
    ws = Workspace(site="casino.example", parameters=controller)
    ws.load_alice(alice_snapshots)
    ws.filter_states = {MEGAWAYS: indexable_state}
    return ws


@pytest.fixture
def api_client(workspace: Workspace):
    from fastapi.testclient import TestClient

    from kontur.api.app import create_app

    return TestClient(create_app(workspace))
