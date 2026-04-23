from __future__ import annotations

import json

import pytest


def test_memory_merge_and_persist(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_MEMORY", "1")
    monkeypatch.setenv("AGENT_MEMORY_DIR", str(tmp_path))
    from agent_memory.store import _format_prior_block, merge_inputs_with_memory, record_run

    class R:
        raw = "# Output A\n"

    # First run: no prior file yet — context is unchanged
    m0, eff0 = merge_inputs_with_memory(
        "test_agent_x",
        user_prompt="hello",
        constraints="c",
        business_context="ctx",
    )
    assert m0["business_context"] == "ctx"
    record_run("test_agent_x", eff0, R())

    p = tmp_path / "test_agent_x.jsonl"
    assert p.is_file()
    line = p.read_text(encoding="utf-8").strip()
    o = json.loads(line)
    assert o["user_prompt"] == "hello"
    assert "# Output A" in o["output_excerpt"]

    # Second run: prior run is injected
    m2, _ = merge_inputs_with_memory(
        "test_agent_x",
        user_prompt="second",
        constraints="c",
        business_context="ctx2",
    )
    assert "Prior work memory" in m2["business_context"]
    assert "hello" in m2["business_context"] or "Output A" in m2["business_context"]


def test_memory_off_no_prefix(monkeypatch):
    monkeypatch.setenv("AGENT_MEMORY", "0")
    from agent_memory.store import merge_inputs_with_memory

    merged, eff = merge_inputs_with_memory(
        "any",
        user_prompt="a",
        constraints="b",
        business_context="c",
    )
    assert merged == eff
    assert "Prior work" not in merged["business_context"]
