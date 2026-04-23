"""Smoke tests for Design and Project Management API routes (no LLM)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api_server import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_list_design_agents(client: TestClient) -> None:
    r = client.get("/v1/design/agents")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 8
    ids = {x["id"] for x in data}
    assert "dg_visual_ui" in ids


def test_list_project_management_agents(client: TestClient) -> None:
    r = client.get("/v1/project-management/agents")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 10
    ids = {x["id"] for x in data}
    assert "pm_sprint_parallel_roadmap" in ids
    assert "pm_phase_initiation" in ids


@patch("design_agents.run_design_agent", autospec=True)
def test_post_design(mock_run, client: TestClient) -> None:
    class _R:
        raw = "# Design spec\n"

    mock_run.return_value = _R()
    r = client.post(
        "/v1/design/dg_visual_ui",
        json={"user_prompt": "Settings page", "constraints": "None", "business_context": "None"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["suggested_file_path"].endswith("dg_visual_ui.md")
    mock_run.assert_called_once()


@patch("project_management_agents.run_project_management_agent", autospec=True)
def test_post_pm(mock_run, client: TestClient) -> None:
    class _R:
        raw = "# Sprint plan\n"

    mock_run.return_value = _R()
    r = client.post(
        "/v1/project-management/pm_erd_data_model",
        json={"user_prompt": "Portal ERD", "constraints": "None", "business_context": "None"},
    )
    assert r.status_code == 200
    assert "artifacts/data_model/" in (r.json().get("meta") or {}).get("suggested_file_path", "")
    mock_run.assert_called_once()
