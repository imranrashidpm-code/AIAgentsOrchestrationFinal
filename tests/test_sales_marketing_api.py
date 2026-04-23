"""Smoke tests for Sales & Marketing API routes (no LLM calls)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api_server import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_list_sales_marketing_agents(client: TestClient) -> None:
    r = client.get("/v1/sales-marketing/agents")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 15
    for row in data:
        assert set(row.keys()) == {"id", "label", "category"}
    ids = {x["id"] for x in data}
    assert "sm_campaign_planner" in ids
    assert "sm_lead_research_icp" in ids


def test_post_sales_marketing_unknown_agent_404(client: TestClient) -> None:
    r = client.post(
        "/v1/sales-marketing/not_a_valid_sm_id",
        json={
            "user_prompt": "hello",
            "constraints": "None specified.",
            "business_context": "None specified.",
        },
    )
    assert r.status_code == 404


@patch("sales_marketing_agents.run_sales_marketing_agent", autospec=True)
def test_post_sales_marketing_smoke(mock_run, client: TestClient) -> None:
    class _Result:
        raw = "# Mock GTM output\n"

    mock_run.return_value = _Result()

    r = client.post(
        "/v1/sales-marketing/sm_campaign_planner",
        json={
            "user_prompt": "Plan Q2 campaign",
            "constraints": "B2B SaaS",
            "business_context": "Small marketing team",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert body.get("content") == "# Mock GTM output\n"
    assert body.get("meta", {}).get("agent_id") == "sm_campaign_planner"
    assert "sales_marketing:sm_campaign_planner" in (body.get("pipeline") or "")
    mock_run.assert_called_once()


def test_openapi_includes_sales_marketing_paths() -> None:
    spec = app.openapi()
    paths = spec.get("paths", {})
    assert "/v1/sales-marketing/agents" in paths
    assert "/v1/sales-marketing/{agent_id}" in paths
    post = paths["/v1/sales-marketing/{agent_id}"]["post"]
    assert "Sales & Marketing" in (post.get("summary") or "")
    # Examples live on the $ref target (components.schemas.SalesMarketingRequest)
    smr = spec.get("components", {}).get("schemas", {}).get("SalesMarketingRequest", {})
    ex = smr.get("examples") or []
    assert ex, "expected json_schema_extra examples on SalesMarketingRequest"
    assert "user_prompt" in ex[0] and "Q2" in (ex[0].get("user_prompt") or "")
