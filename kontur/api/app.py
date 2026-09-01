"""The Kontur HTTP surface.

HTML routes render the dashboard; ``/api/*`` routes return the same data as
JSON. Both go through the workspace, so a figure can never appear on a page
without the provenance and sample marks that travel with it.
"""

from __future__ import annotations

from typing import Any, Sequence

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field

from kontur.core.claims import HYPOTHESES
from kontur.core.errors import (
    ConfigurationError,
    InsufficientDataError,
    KonturError,
    MissingProvenanceError,
    SampleDataError,
)
from kontur.core.provenance import Confidence, Provenance
from kontur.core.redaction import redact
from kontur.core.registry import RULES, SCORING_FUNCTIONS
from kontur.dashboard import render
from kontur.engines.aeo.answer import assess_answer_first
from kontur.engines.aeo.content import parse_html
from kontur.engines.aeo.extraction import extraction_report
from kontur.engines.backlinks.risk import AnchorType, Backlink, analyse_backlinks
from kontur.ingest.validation import parse_date
from kontur.workspace import Workspace, demo_workspace

MAX_URLS_PER_REQUEST = 200
MAX_LINKS_PER_REQUEST = 5000
MAX_HTML_BYTES = 2_000_000


class DecideRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=MAX_URLS_PER_REQUEST)


class AeoRequest(BaseModel):
    url: str = Field(..., max_length=2048)
    html: str = Field(..., max_length=MAX_HTML_BYTES)
    query: str | None = Field(default=None, max_length=400)


class BacklinkIn(BaseModel):
    source_domain: str = Field(..., max_length=253)
    anchor: str = Field(default="", max_length=400)
    anchor_type: str = Field(default="generic")
    first_seen: str
    ip_c_class: str | None = None
    registrar: str | None = None
    analytics_id: str | None = None
    template_hash: str | None = None
    topical_relevance: float = Field(default=1.0, ge=0.0, le=1.0)
    content_similarity: float = Field(default=0.0, ge=0.0, le=1.0)


class BacklinkRequest(BaseModel):
    target: str = Field(..., max_length=2048)
    source: str = Field(..., max_length=120)
    retrieved_at: str
    confidence: str = Field(default="medium")
    links: list[BacklinkIn] = Field(..., min_length=1, max_length=MAX_LINKS_PER_REQUEST)


def _fail(exc: KonturError) -> HTTPException:
    status = {
        MissingProvenanceError: 422,
        SampleDataError: 409,
        InsufficientDataError: 422,
        ConfigurationError: 400,
    }.get(type(exc), 400)
    return HTTPException(status_code=status, detail=str(exc))


def default_urls(workspace: Workspace) -> list[str]:
    """A representative URL set for the dashboard's decision table."""
    urls = list(workspace.filter_states)
    urls.extend(["/slots/", "/slots/?mechanic=megaways&utm_source=vk", "/slots/?mechanic=megaways&page=2"])
    return urls


def create_app(workspace: Workspace | None = None) -> FastAPI:
    workspace = workspace or demo_workspace()
    app = FastAPI(
        title="Kontur",
        version="0.1.0",
        description="Yandex-first SEO / AEO / GEO platform with a test-governance layer.",
    )
    app.state.workspace = workspace

    # ------------------------------------------------------------- HTML pages
    @app.get("/", response_class=HTMLResponse)
    def overview_page() -> str:
        ws: Workspace = app.state.workspace
        return render.render_overview(ws.overview(), sample=ws.contains_sample_data)

    @app.get("/indexation/parameters", response_class=HTMLResponse)
    def parameters_page() -> str:
        ws: Workspace = app.state.workspace
        return render.render_parameters(ws.parameter_rows(), sample=ws.contains_sample_data)

    @app.get("/indexation/decisions", response_class=HTMLResponse)
    def decisions_page() -> str:
        ws: Workspace = app.state.workspace
        return render.render_decisions(ws.decide(default_urls(ws)), sample=ws.contains_sample_data)

    @app.get("/ai-visibility", response_class=HTMLResponse)
    def ai_visibility_page() -> str:
        ws: Workspace = app.state.workspace
        try:
            report = ws.ai_visibility().to_dict()
        except KonturError as exc:
            raise _fail(exc) from exc
        return render.render_ai_visibility(report, ws.volatility())

    # -------------------------------------------------------------- JSON API
    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "service": "kontur"}

    @app.get("/api/overview")
    def api_overview() -> dict[str, Any]:
        return app.state.workspace.overview()

    @app.get("/api/indexation/parameters")
    def api_parameters() -> dict[str, Any]:
        ws: Workspace = app.state.workspace
        return {
            "rows": [r.to_dict() for r in ws.parameters.rulings()],
            "summary": ws.parameters.summary(),
        }

    @app.get("/api/indexation/parameters/export")
    def api_parameter_export() -> dict[str, Any]:
        return app.state.workspace.parameter_export()

    @app.get("/api/indexation/robots", response_class=PlainTextResponse)
    def api_robots() -> str:
        return app.state.workspace.robots_txt()

    @app.post("/api/indexation/decide")
    def api_decide(request: DecideRequest) -> dict[str, Any]:
        ws: Workspace = app.state.workspace
        try:
            decisions = ws.decide(request.urls)
        except KonturError as exc:
            raise _fail(exc) from exc
        return {"decisions": decisions, "summary": ws.indexation_summary(request.urls)}

    @app.get("/api/ai-visibility")
    def api_ai_visibility(require_real_data: bool = Query(default=False)) -> dict[str, Any]:
        try:
            return app.state.workspace.ai_visibility(require_real_data=require_real_data).to_dict()
        except KonturError as exc:
            raise _fail(exc) from exc

    @app.get("/api/ai-visibility/graph")
    def api_graph() -> dict[str, Any]:
        try:
            return app.state.workspace.graph().to_dict()
        except KonturError as exc:
            raise _fail(exc) from exc

    @app.get("/api/ai-visibility/volatility")
    def api_volatility(threshold: float = Query(default=0.5, ge=0.0, le=1.0)) -> dict[str, Any]:
        return {"queries": app.state.workspace.volatility(threshold=threshold)}

    @app.post("/api/aeo/assess")
    def api_aeo(request: AeoRequest) -> dict[str, Any]:
        try:
            page = parse_html(request.html, url=request.url, target_query=request.query)
            return {
                "answer": assess_answer_first(page, query=request.query).to_dict(),
                "extraction": extraction_report(page, query=request.query).to_dict(),
                "content": page.to_dict(),
            }
        except KonturError as exc:
            raise _fail(exc) from exc

    @app.post("/api/backlinks/risk")
    def api_backlinks(request: BacklinkRequest) -> dict[str, Any]:
        try:
            provenance = Provenance(
                source=request.source,
                retrieved_at=parse_date(request.retrieved_at, field="retrieved_at"),
                confidence=Confidence(request.confidence.lower()),
            )
            links = [
                Backlink(
                    source_domain=item.source_domain,
                    target_url=request.target,
                    anchor=item.anchor,
                    anchor_type=AnchorType(item.anchor_type.lower()),
                    first_seen=parse_date(item.first_seen, field="first_seen"),
                    ip_c_class=item.ip_c_class,
                    registrar=item.registrar,
                    analytics_id=item.analytics_id,
                    template_hash=item.template_hash,
                    topical_relevance=item.topical_relevance,
                    content_similarity=item.content_similarity,
                )
                for item in request.links
            ]
            return redact(analyse_backlinks(request.target, links, provenance=provenance).to_dict())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except KonturError as exc:
            raise _fail(exc) from exc

    @app.get("/api/rules")
    def api_rules() -> dict[str, Any]:
        return {
            "rules": [
                {
                    "id": rule.id,
                    "title": rule.title,
                    "kind": rule.kind.value,
                    "criticality": rule.criticality.value,
                    "module": rule.module,
                    "rationale": rule.rationale,
                    "requires_regression_test": rule.requires_regression_test,
                }
                for rule in RULES.values()
            ],
            "scoring_functions": [
                {"name": fn.name, "path": fn.dotted_path, "bounds": [fn.lower, fn.upper]}
                for fn in SCORING_FUNCTIONS.values()
            ],
        }

    @app.get("/api/hypotheses")
    def api_hypotheses() -> dict[str, Any]:
        return {
            "hypotheses": [h.to_dict() for h in HYPOTHESES.values()],
            "note": (
                "Guidelines are hypotheses under test. Kontur reports measured differences "
                "with intervals; it does not assert effects on rankings or AI visibility."
            ),
        }

    return app


def endpoint_paths(app: FastAPI) -> Sequence[str]:
    """Every route path the app serves (used by meta-test MT-008)."""
    return sorted(
        {
            route.path
            for route in app.routes
            if getattr(route, "path", "").startswith(("/api", "/health", "/indexation", "/ai-visibility"))
            or getattr(route, "path", "") == "/"
        }
    )


app = create_app()
