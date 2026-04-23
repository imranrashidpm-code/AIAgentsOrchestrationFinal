"""
Brain (reasoning & model): every agent gets an **explicit** ``llm`` id so runs work anywhere
you set ``OPENAI_API_KEY`` (or your provider’s env) — **no IDE / Cursor / Claude session** is involved.

Autonomy-oriented defaults (iterations, reasoning pass, no delegation) are applied unless YAML/env overrides.
"""

from __future__ import annotations

import os
from contextvars import ContextVar
from typing import Any

# Default when no model env is set — OpenAI-style id (CrewAI ``create_llm``); override freely.
_DEFAULT_MODEL = "gpt-4o-mini"

# Per-request model (set from API body ``llm_model`` / CLI inputs) — overrides env for that run only.
_llm_request_override: ContextVar[str | None] = ContextVar("_llm_request_override", default=None)


def _truthy(name: str, default: str = "1") -> bool:
    v = (os.environ.get(name, default) or default).strip().lower()
    return v in ("1", "true", "yes", "on")


def set_request_llm_model(model: str | None) -> object | None:
    """
    If ``model`` is a non-empty string, set a **per-request** override for :func:`resolve_llm` in the current
    (async) context. Returns a token to pass to :func:`reset_request_llm_model` after the run, or ``None`` if
    there was no override to apply.
    """
    if not model or not (s := model.strip()):
        return None
    return _llm_request_override.set(s)


def reset_request_llm_model(token: object | None) -> None:
    if token is not None:
        _llm_request_override.reset(token)


def resolve_llm() -> str:
    """
    Resolved model id **always** returned (never None).

    Priority: per-request override (set via :func:`set_request_llm_model` / HTTP ``llm_model``) →
    ``ORCHESTRATOR_AGENT_LLM`` → ``OPENAI_MODEL_NAME`` → ``ORCHESTRATOR_DEFAULT_LLM`` → built-in default.
    """
    o = _llm_request_override.get()
    if o:
        return o
    for key in ("ORCHESTRATOR_AGENT_LLM", "OPENAI_MODEL_NAME", "ORCHESTRATOR_DEFAULT_LLM"):
        v = (os.environ.get(key) or "").strip()
        if v:
            return v
    return _DEFAULT_MODEL


def reasoning_model_from_env() -> str | None:
    """Backward-compatible: explicit model if any env was set, else ``None`` (prefer :func:`resolve_llm`)."""
    for key in ("ORCHESTRATOR_AGENT_LLM", "OPENAI_MODEL_NAME", "ORCHESTRATOR_DEFAULT_LLM"):
        v = (os.environ.get(key) or "").strip()
        if v:
            return v
    return None


def _max_iter() -> int:
    try:
        return max(1, min(100, int(os.environ.get("ORCHESTRATOR_AGENT_MAX_ITER", "25"))))
    except ValueError:
        return 25


def enrich_agent_config(cfg: dict[str, Any]) -> dict[str, Any]:
    """
    Merge **standalone LLM + autonomy defaults** into YAML-derived agent config.

    - ``llm``: always set (API calls go to your configured provider via CrewAI, not the IDE).
    - ``allow_delegation``: ``False`` unless already present in ``cfg`` (single-agent crews stay self-contained).
    - ``max_iter``: from ``ORCHESTRATOR_AGENT_MAX_ITER`` or 25 if not in ``cfg``.
    - ``reasoning``: plan/reflection step when ``ORCHESTRATOR_AGENT_REASONING`` is on (default on).
    """
    out = dict(cfg)
    out["llm"] = resolve_llm()
    if "allow_delegation" not in out:
        out["allow_delegation"] = False
    if "max_iter" not in out:
        out["max_iter"] = _max_iter()
    if "reasoning" not in out:
        out["reasoning"] = _truthy("ORCHESTRATOR_AGENT_REASONING", "1")
    return out
