"""The codebase itself must not promise effects it has not measured."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from kontur.core.claims import find_unproven_claims
from kontur.testing.inventory import find_repo_root

pytestmark = [pytest.mark.regression, pytest.mark.geo]

REPO = find_repo_root()

#: The claim scanner and the tests that exercise it necessarily contain the
#: forbidden phrasings as data.
EXEMPT = {
    "kontur/core/claims.py",
    "tests/unit/test_claims.py",
    "tests/regression/test_no_unproven_claims_in_repo.py",
}

#: Metric names that would mean the platform invented its own AI-visibility score
#: instead of reporting what Yandex measures.
FORBIDDEN_METRIC_NAMES = {"geo_score", "aeo_score", "ai_visibility_score", "visibility_index"}


def _scannable_files() -> list[Path]:
    files: list[Path] = []
    for pattern in ("kontur/**/*.py", "docs/**/*.md", "README.md"):
        for path in REPO.glob(pattern):
            if "__pycache__" in path.parts:
                continue
            if str(path.relative_to(REPO)).replace("\\", "/") in EXEMPT:
                continue
            files.append(path)
    return files


@pytest.mark.rule("AEO-004")
@pytest.mark.regression
def test_no_module_or_document_promises_an_effect() -> None:
    offenders: dict[str, list[str]] = {}
    for path in _scannable_files():
        hits = find_unproven_claims(path.read_text(encoding="utf-8"))
        if hits:
            offenders[str(path.relative_to(REPO))] = hits
    assert not offenders, f"unproven effect claims found: {offenders}"


@pytest.mark.rule("GEO-002")
@pytest.mark.regression
def test_no_invented_ai_visibility_metric_exists() -> None:
    offenders: dict[str, list[str]] = {}
    for path in REPO.glob("kontur/**/*.py"):
        if "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.append(node.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                names.append(node.id)
            elif isinstance(node, ast.arg):
                names.append(node.arg)
        hits = [name for name in names if name.lower() in FORBIDDEN_METRIC_NAMES]
        if hits:
            offenders[str(path.relative_to(REPO))] = hits
    assert not offenders, (
        "AI visibility must come from the Yandex export, not from an invented score: " f"{offenders}"
    )


@pytest.mark.rule("GEO-002")
@pytest.mark.regression
def test_every_ai_visibility_payload_states_its_provenance(workspace) -> None:
    payload = workspace.ai_visibility().to_dict()
    assert payload["evidence"], "the report must name its sources"
    assert all(item["source"] and item["retrieved_at"] and item["confidence"] for item in payload["evidence"])
    assert "is_sample" in payload
