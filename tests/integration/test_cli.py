"""The command line interface."""

from __future__ import annotations

import json

import pytest

from kontur.cli import main

pytestmark = pytest.mark.integration


def _run(capsys, *args: str) -> tuple[int, str]:
    code = main(list(args))
    return code, capsys.readouterr().out


def test_overview_reports_the_workspace(capsys) -> None:
    code, out = _run(capsys, "overview")
    assert code == 0
    payload = json.loads(out)
    assert payload["site"] == "casino.example"
    assert payload["contains_sample_data"] is True


def test_params_prints_the_dashboard_rows(capsys) -> None:
    code, out = _run(capsys, "params")
    assert code == 0
    rows = {row["parameter"]: row for row in json.loads(out)}
    assert rows["utm_source"]["decision"] == "EXCLUDE"
    assert rows["mechanic"]["decision"] == "SEO HUB"


def test_export_produces_the_webmaster_payload(capsys) -> None:
    code, out = _run(capsys, "export")
    payload = json.loads(out)
    assert code == 0
    assert payload["tool"] == "yandex_webmaster.get_parameters"
    assert payload["contains_sample_data"] is True


def test_robots_prints_directives(capsys) -> None:
    code, out = _run(capsys, "robots")
    assert code == 0
    assert "Clean-param:" in out


def test_decide_explains_every_url(capsys) -> None:
    code, out = _run(capsys, "decide", "/slots/?mechanic=megaways", "/slots/?phpsessid=x")
    assert code == 0
    decisions = json.loads(out)
    assert [d["decision"] for d in decisions] == ["INDEX", "BLOCK"]
    assert all(d["reason"] for d in decisions)


def test_ai_visibility_is_marked_as_sample(capsys) -> None:
    code, out = _run(capsys, "ai-visibility")
    payload = json.loads(out)
    assert code == 0
    assert payload["is_sample"] is True
    assert "SAMPLE DATA" in payload["warning"]


def test_rules_lists_the_registry(capsys) -> None:
    code, out = _run(capsys, "rules")
    assert code == 0
    ids = {rule["id"] for rule in json.loads(out)}
    assert {"GETP-002", "FACET-007", "GEO-003"} <= ids


def test_an_unknown_command_is_rejected() -> None:
    with pytest.raises(SystemExit):
        main(["not-a-command"])


def test_a_kontur_error_becomes_exit_code_two(capsys, monkeypatch) -> None:
    from kontur.core.errors import InsufficientDataError

    def explode(self, **kwargs):
        raise InsufficientDataError("no snapshots loaded")

    monkeypatch.setattr("kontur.workspace.Workspace.ai_visibility", explode)
    code = main(["ai-visibility"])
    assert code == 2
    assert "no snapshots loaded" in capsys.readouterr().err
