from __future__ import annotations

import os

import pytest


def test_resolve_llm_always_string(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ORCHESTRATOR_AGENT_LLM", raising=False)
    monkeypatch.delenv("OPENAI_MODEL_NAME", raising=False)
    monkeypatch.delenv("ORCHESTRATOR_DEFAULT_LLM", raising=False)
    from agent_capabilities.brain import enrich_agent_config, resolve_llm

    assert resolve_llm() == "gpt-4o-mini"
    d = enrich_agent_config({"role": "r", "goal": "g", "backstory": "b"})
    assert d["llm"] == "gpt-4o-mini"
    assert d["allow_delegation"] is False
    assert d["max_iter"] == 25
    assert d["reasoning"] is True


def test_resolve_llm_openai_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL_NAME", "gpt-4o")
    from agent_capabilities.brain import enrich_agent_config, resolve_llm

    assert resolve_llm() == "gpt-4o"
    d = enrich_agent_config({"role": "r", "goal": "g", "backstory": "b"})
    assert d["llm"] == "gpt-4o"


def test_resolve_llm_request_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL_NAME", "gpt-4o")
    from agent_capabilities.brain import (
        enrich_agent_config,
        reset_request_llm_model,
        resolve_llm,
        set_request_llm_model,
    )

    tok = set_request_llm_model("gpt-4o-mini")
    try:
        assert resolve_llm() == "gpt-4o-mini"
        d = enrich_agent_config({"role": "r", "goal": "g", "backstory": "b"})
        assert d["llm"] == "gpt-4o-mini"
    finally:
        reset_request_llm_model(tok)
    assert resolve_llm() == "gpt-4o"
