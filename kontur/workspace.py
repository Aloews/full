"""A workspace wires the engines together for one site.

It is the object the API, the dashboard and the CLI all talk to, so the four
loops (SEO / AEO / GEO / experiments) share one set of inputs and one set of
provenance marks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from kontur.core.errors import InsufficientDataError
from kontur.core.provenance import Sourced
from kontur.engines.experiment.design import Experiment, ExperimentRegistry
from kontur.engines.faceted.models import (
    DEFAULT_FACET_CONFIG,
    IGAMING_SLOTS_CATALOG,
    FacetCatalog,
    FacetConfig,
)
from kontur.engines.faceted.pipeline import FacetedIndexationEngine, decision_summary
from kontur.engines.faceted.providers import MappingProvider
from kontur.engines.geo.metrics import AiVisibilityReport, build_report
from kontur.engines.geo.models import AliceSnapshot, QuerySet
from kontur.engines.geo.snapshots import SnapshotStore
from kontur.engines.getparams.controller import GetParameterController
from kontur.engines.getparams.export import build_export, robots_block
from kontur.engines.getparams.models import ParamObservation
from kontur.graph.query_graph import QueryAnswerGraph, build_graph
from kontur.ingest import samples


@dataclass
class Workspace:
    """Everything Kontur knows about one site."""

    site: str
    catalog: FacetCatalog = IGAMING_SLOTS_CATALOG
    config: FacetConfig = DEFAULT_FACET_CONFIG
    parameters: GetParameterController = field(default_factory=GetParameterController)
    snapshots: SnapshotStore = field(default_factory=SnapshotStore)
    experiments: ExperimentRegistry = field(default_factory=ExperimentRegistry)
    filter_states: dict[str, dict[str, Any]] = field(default_factory=dict)
    serp_positions: dict[str, int] = field(default_factory=dict)
    tracked_queries: QuerySet | None = None

    # ------------------------------------------------------------------ setup
    def load_parameters(
        self, observations: Sequence[ParamObservation], demand: Mapping[str, Sourced] | None = None
    ) -> "Workspace":
        self.parameters.observe(observations)
        for name, value in (demand or {}).items():
            self.parameters.set_demand(name, value)
        return self

    def load_alice(self, snapshots: Sequence[AliceSnapshot]) -> "Workspace":
        for snapshot in snapshots:
            self.snapshots.add(snapshot)
        return self

    def register_experiment(self, experiment: Experiment) -> "Workspace":
        self.experiments.register(experiment)
        return self

    # ------------------------------------------------------------- indexation
    @property
    def engine(self) -> FacetedIndexationEngine:
        return FacetedIndexationEngine(
            catalog=self.catalog,
            parameters=self.parameters,
            config=self.config,
            demand=MappingProvider({k: v["demand"] for k, v in self.filter_states.items() if "demand" in v}),
            intent=MappingProvider({k: v["intent"] for k, v in self.filter_states.items() if "intent" in v}),
            inventory=MappingProvider(
                {k: v["inventory"] for k, v in self.filter_states.items() if "inventory" in v}
            ),
            business=MappingProvider(
                {k: v["business"] for k, v in self.filter_states.items() if "business" in v}
            ),
            serp=MappingProvider({k: v["serp"] for k, v in self.filter_states.items() if "serp" in v}),
        )

    def decide(self, urls: Sequence[str]) -> list[dict[str, Any]]:
        return [record.to_dict() for record in self.engine.decide_many(urls)]

    def indexation_summary(self, urls: Sequence[str]) -> dict[str, Any]:
        return decision_summary(self.engine.decide_many(urls))

    def parameter_rows(self) -> list[dict[str, Any]]:
        return self.parameters.dashboard_rows()

    def parameter_export(self) -> dict[str, Any]:
        return build_export(self.parameters.rulings()).to_dict()

    def robots_txt(self) -> str:
        return robots_block(self.parameters.rulings())

    # --------------------------------------------------------------- ai visibility
    def ai_visibility(self, *, require_real_data: bool = False) -> AiVisibilityReport:
        snapshots = self.snapshots.for_site(self.site)
        if not snapshots:
            raise InsufficientDataError(f"no Alice AI snapshots loaded for {self.site}")
        return build_report(
            snapshots, query_set=self.tracked_queries, require_real_data=require_real_data
        )

    def graph(self) -> QueryAnswerGraph:
        return build_graph(
            self.site, self.snapshots.for_site(self.site), serp_positions=self.serp_positions
        )

    def volatility(self, *, threshold: float = 0.5) -> list[dict[str, Any]]:
        return self.snapshots.volatile_queries(self.site, threshold=threshold)

    # -------------------------------------------------------------------- meta
    @property
    def contains_sample_data(self) -> bool:
        rulings_sample = any(r.is_sample for r in self.parameters.rulings())
        snapshots_sample = any(s.is_sample for s in self.snapshots.for_site(self.site))
        return rulings_sample or snapshots_sample

    def overview(self) -> dict[str, Any]:
        return {
            "site": self.site,
            "parameters": self.parameters.summary(),
            "alice_weeks": len(self.snapshots.for_site(self.site)),
            "filter_states": len(self.filter_states),
            "experiments": len(self.experiments.experiments),
            "contains_sample_data": self.contains_sample_data,
        }


def demo_workspace() -> Workspace:
    """A workspace filled with clearly-marked sample data."""
    workspace = Workspace(site=samples.SAMPLE_SITE)
    workspace.load_parameters(samples.sample_param_observations(), samples.sample_param_demand())
    workspace.load_alice(samples.sample_alice_snapshots())
    workspace.filter_states = samples.sample_filter_states()
    workspace.serp_positions = samples.sample_serp_positions()
    workspace.tracked_queries = QuerySet(
        "core",
        frozenset(
            {
                "что такое megaways",
                "слоты pragmatic play",
                "что такое rtp в слотах",
                "слоты с покупкой бонуса",
                "как работает волатильность слотов",
                "кластерные слоты",
            }
        ),
    )
    return workspace
