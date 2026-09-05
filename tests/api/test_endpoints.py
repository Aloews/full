"""Every route the app serves has a test that exercises it."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.api


@pytest.mark.endpoint("/health")
def test_health(api_client) -> None:
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.endpoint("/")
def test_overview_page(api_client) -> None:
    response = api_client.get("/")
    assert response.status_code == 200
    assert "KONTUR" in response.text
    assert "GET Parameters" in response.text


@pytest.mark.endpoint("/indexation/parameters")
def test_parameters_page(api_client) -> None:
    response = api_client.get("/indexation/parameters")
    assert response.status_code == 200
    assert "Detected URLs" in response.text
    assert "utm_source" in response.text


@pytest.mark.endpoint("/indexation/decisions")
def test_decisions_page(api_client) -> None:
    response = api_client.get("/indexation/decisions")
    assert response.status_code == 200
    assert "INDEXATION DECISION" in response.text


@pytest.mark.endpoint("/ai-visibility")
def test_ai_visibility_page(api_client) -> None:
    response = api_client.get("/ai-visibility")
    assert response.status_code == 200
    assert "Share of Voice" in response.text
    assert "Answer volatility" in response.text


@pytest.mark.endpoint("/api/overview")
def test_api_overview(api_client) -> None:
    payload = api_client.get("/api/overview").json()
    assert payload["site"] == "casino.example"
    assert payload["parameters"]["parameters"] > 0


@pytest.mark.endpoint("/api/indexation/parameters")
def test_api_parameters(api_client) -> None:
    payload = api_client.get("/api/indexation/parameters").json()
    names = {row["parameter"] for row in payload["rows"]}
    assert {"utm_source", "mechanic", "phpsessid"} <= names
    assert all(row["reason"] for row in payload["rows"]), "every row explains itself"


@pytest.mark.endpoint("/api/indexation/parameters/export")
def test_api_parameter_export(api_client) -> None:
    payload = api_client.get("/api/indexation/parameters/export").json()
    assert payload["tool"] == "yandex_webmaster.get_parameters"
    assert "utm_source" in payload["exclude"]


@pytest.mark.endpoint("/api/indexation/robots")
def test_api_robots(api_client) -> None:
    response = api_client.get("/api/indexation/robots")
    assert response.status_code == 200
    assert "Clean-param:" in response.text


@pytest.mark.endpoint("/api/indexation/decide")
def test_api_decide(api_client) -> None:
    response = api_client.post(
        "/api/indexation/decide",
        json={"urls": ["/slots/?mechanic=megaways", "/slots/?mechanic=megaways&utm_source=vk"]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert [d["decision"] for d in payload["decisions"]] == ["INDEX", "CANONICAL"]
    assert payload["summary"]["total"] == 2


@pytest.mark.endpoint("/api/indexation/decide")
def test_api_decide_rejects_oversized_batches(api_client) -> None:
    response = api_client.post("/api/indexation/decide", json={"urls": ["/x/"] * 500})
    assert response.status_code == 422


@pytest.mark.endpoint("/api/ai-visibility")
def test_api_ai_visibility(api_client) -> None:
    payload = api_client.get("/api/ai-visibility").json()
    assert 0.0 <= payload["share_of_voice"] <= 1.0
    assert payload["window"]["start"] <= payload["window"]["end"]
    assert payload["evidence"], "the report names its sources"


@pytest.mark.endpoint("/api/ai-visibility/graph")
def test_api_graph(api_client) -> None:
    payload = api_client.get("/api/ai-visibility/graph").json()
    assert payload["queries"] >= 1
    assert payload["nodes"] and payload["edges"]


@pytest.mark.endpoint("/api/ai-visibility/volatility")
def test_api_volatility(api_client) -> None:
    response = api_client.get("/api/ai-visibility/volatility?threshold=0.0")
    assert response.status_code == 200
    assert isinstance(response.json()["queries"], list)


@pytest.mark.endpoint("/api/aeo/assess")
def test_api_aeo(api_client) -> None:
    html = (
        "<html><body><h1>Что такое Megaways</h1>"
        "<p>Megaways — это механика игровых автоматов, при которой число символов на барабанах "
        "меняется в каждом спине, что даёт до 117 649 способов выигрыша за спин.</p></body></html>"
    )
    payload = api_client.post(
        "/api/aeo/assess", json={"url": "/slots/megaways/", "html": html, "query": "что такое megaways"}
    ).json()
    assert payload["answer"]["has_answer_first"] is True
    assert 0.0 <= payload["extraction"]["extraction_readiness"] <= 1.0


@pytest.mark.endpoint("/api/backlinks/risk")
def test_api_backlinks(api_client) -> None:
    links = [
        {
            "source_domain": f"pbn{index}.example",
            "anchor": "казино онлайн играть",
            "anchor_type": "commercial",
            "first_seen": "2026-03-01",
            "ip_c_class": "10.1.0",
            "registrar": "regX",
            "analytics_id": "UA-1",
            "topical_relevance": 0.2,
            "content_similarity": 0.9,
        }
        for index in range(12)
    ]
    payload = api_client.post(
        "/api/backlinks/risk",
        json={
            "target": "https://casino.example/slots/",
            "source": "backlink_export:vendor",
            "retrieved_at": "2026-08-20",
            "confidence": "medium",
            "links": links,
        },
    ).json()
    assert payload["risk_level"] == "HIGH RISK"
    assert "does not build" in payload["scope"]


@pytest.mark.endpoint("/api/backlinks/risk")
def test_api_backlinks_rejects_a_bad_date(api_client) -> None:
    response = api_client.post(
        "/api/backlinks/risk",
        json={
            "target": "/slots/",
            "source": "backlink_export:vendor",
            "retrieved_at": "not-a-date",
            "links": [{"source_domain": "x.example", "first_seen": "2026-03-01"}],
        },
    )
    assert response.status_code == 400


@pytest.mark.endpoint("/api/rules")
def test_api_rules(api_client) -> None:
    payload = api_client.get("/api/rules").json()
    ids = {rule["id"] for rule in payload["rules"]}
    assert {"GETP-001", "FACET-007", "GEO-003", "EXP-002"} <= ids
    assert len(payload["scoring_functions"]) >= 8


@pytest.mark.endpoint("/api/hypotheses")
def test_api_hypotheses(api_client) -> None:
    payload = api_client.get("/api/hypotheses").json()
    assert all(h["status"] == "proposed" for h in payload["hypotheses"])
    assert "does not assert effects" in payload["note"]


def test_unknown_routes_are_404(api_client) -> None:
    assert api_client.get("/does-not-exist").status_code == 404
