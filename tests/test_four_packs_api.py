"""Smoke tests for DevOps, QA, Data, HR API routes (no LLM)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api_server import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_devops_catalog(client: TestClient) -> None:
    r = client.get("/v1/devops-platform/agents")
    assert r.status_code == 200
    ids = {x["id"] for x in r.json()}
    assert "dvp_kubernetes_platform" in ids
    assert len(ids) == 5


def test_qa_catalog(client: TestClient) -> None:
    r = client.get("/v1/qa-test-strategy/agents")
    assert r.status_code == 200
    ids = {x["id"] for x in r.json()}
    assert "qts_e2e_feature_scope" in ids
    assert len(ids) == 4


def test_data_catalog(client: TestClient) -> None:
    r = client.get("/v1/data-analytics/agents")
    assert r.status_code == 200
    ids = {x["id"] for x in r.json()}
    assert "dta_warehouse_dbt_conceptual" in ids
    assert len(ids) == 4


def test_hr_catalog(client: TestClient) -> None:
    r = client.get("/v1/hr-talent/agents")
    assert r.status_code == 200
    ids = {x["id"] for x in r.json()}
    assert "hrt_performance_review_structure" in ids
    assert len(ids) == 5


@patch("devops_platform_agents.run_devops_platform_agent", autospec=True)
def test_post_devops(mock_run, client: TestClient) -> None:
    class R:
        raw = "ok\n"

    mock_run.return_value = R()
    b = client.post(
        "/v1/devops-platform/dvp_ops_runbook",
        json={"user_prompt": "x", "constraints": "n", "business_context": "n"},
    )
    assert b.status_code == 200
    assert b.json()["meta"]["suggested_file_path"].endswith("dvp_ops_runbook.md")
    mock_run.assert_called_once()


@patch("qa_test_strategy_agents.run_qa_test_strategy_agent", autospec=True)
def test_post_qa(mock_run, client: TestClient) -> None:
    class R:
        raw = "ok\n"

    mock_run.return_value = R()
    b = client.post(
        "/v1/qa-test-strategy/qts_test_plan",
        json={"user_prompt": "x", "constraints": "n", "business_context": "n"},
    )
    assert b.status_code == 200
    mock_run.assert_called_once()


@patch("data_analytics_agents.run_data_analytics_agent", autospec=True)
def test_post_data(mock_run, client: TestClient) -> None:
    class R:
        raw = "ok\n"

    mock_run.return_value = R()
    b = client.post(
        "/v1/data-analytics/dta_dashboard_spec",
        json={"user_prompt": "x", "constraints": "n", "business_context": "n"},
    )
    assert b.status_code == 200
    mock_run.assert_called_once()


@patch("hr_talent_agents.run_hr_talent_agent", autospec=True)
def test_post_hr(mock_run, client: TestClient) -> None:
    class R:
        raw = "ok\n"

    mock_run.return_value = R()
    b = client.post(
        "/v1/hr-talent/hrt_role_description",
        json={"user_prompt": "x", "constraints": "n", "business_context": "n"},
    )
    assert b.status_code == 200
    mock_run.assert_called_once()
