"""The workspace wires the four loops onto one set of inputs."""

from __future__ import annotations

import pytest

from kontur.core.errors import InsufficientDataError
from kontur.engines.getparams.models import ParamDecision
from kontur.workspace import Workspace, demo_workspace

pytestmark = pytest.mark.integration


def test_the_overview_covers_every_loop(workspace: Workspace) -> None:
    overview = workspace.overview()
    assert overview["site"] == "casino.example"
    assert overview["parameters"]["parameters"] > 0
    assert overview["alice_weeks"] == 4
    assert overview["filter_states"] == 1


def test_parameter_policy_reaches_the_indexation_decision(workspace: Workspace) -> None:
    assert workspace.parameters.decision("utm_source") is ParamDecision.EXCLUDE
    decision = workspace.decide(["/slots/?mechanic=megaways&utm_source=vk"])[0]
    assert decision["decision"] == "CANONICAL"
    assert decision["canonical_target"] == "/slots/?mechanic=megaways"


def test_the_summary_lists_the_indexable_set(workspace: Workspace) -> None:
    summary = workspace.indexation_summary(
        ["/slots/?mechanic=megaways", "/slots/?rtp=96plus", "/slots/?phpsessid=x"]
    )
    assert summary["indexable"] == ["/slots/?mechanic=megaways"]
    assert summary["by_decision"]["BLOCK"] == 1


def test_the_robots_block_matches_the_parameter_rulings(workspace: Workspace) -> None:
    robots = workspace.robots_txt()
    for parameter in workspace.parameters.excluded_parameters():
        assert parameter in robots


def test_ai_visibility_and_graph_share_the_same_snapshots(workspace: Workspace) -> None:
    report = workspace.ai_visibility()
    graph = workspace.graph()
    assert report.queries_analysed == graph.to_dict()["queries"]


def test_a_workspace_without_snapshots_says_so() -> None:
    with pytest.raises(InsufficientDataError, match="no Alice AI snapshots"):
        Workspace(site="empty.example").ai_visibility()


def test_real_data_is_not_marked_as_sample(workspace: Workspace) -> None:
    assert workspace.contains_sample_data is False
    assert workspace.ai_visibility(require_real_data=True).is_sample is False


def test_the_demo_workspace_is_marked_as_sample_everywhere() -> None:
    demo = demo_workspace()
    assert demo.contains_sample_data is True
    assert demo.ai_visibility().is_sample is True
    assert "SAMPLE DATA" in demo.ai_visibility().to_dict()["warning"]
    assert demo.parameter_export()["contains_sample_data"] is True
    assert all(row["is_sample"] for row in demo.parameter_rows())


def test_the_demo_workspace_reproduces_the_documented_parameter_table() -> None:
    rows = {row["parameter"]: row for row in demo_workspace().parameter_rows()}
    assert rows["utm_source"]["decision"] == "EXCLUDE"
    assert rows["sort"]["decision"] == "EXCLUDE"
    assert rows["page"]["decision"] == "CONTEXT_DEPENDENT"
    assert rows["mechanic"]["decision"] == "SEO HUB"
    assert rows["phpsessid"]["decision"] == "BLOCK"
