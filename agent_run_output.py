"""
Save successful agent / report API runs to disk: ``{pack}/Output/{agent_id}/latest.md`` plus
``history/{timestamp}_{agent_id}.md``. Disabled when ``ORCHESTRATOR_SAVE_OUTPUT=0`` in the environment.
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent


def output_dir_for(pack_folder: str, agent_id: str) -> Path:
    """Resolved ``…/{pack}/Output/{agent_id}/`` (may not exist)."""
    return REPO_ROOT / pack_folder / "Output" / _safe_segment(agent_id)


def _enabled() -> bool:
    v = (os.environ.get("ORCHESTRATOR_SAVE_OUTPUT", "1") or "1").strip().lower()
    return v in ("1", "true", "yes", "on")


def _safe_segment(s: str) -> str:
    s = (s or "").strip() or "unknown"
    return re.sub(r"[^\w.\-]+", "_", s)[:200]


def _header(pipeline: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"<!-- saved_by=api pipeline={pipeline!r} utc={ts} -->\n\n"


def save_pack_agent_output(
    *,
    pack_folder: str,
    agent_id: str,
    content: str,
    pipeline: str,
) -> dict[str, Any]:
    """
    ``pack_folder`` is the top-level package directory name, e.g. ``design_agents``.
    """
    if not _enabled() or not content:
        return {}
    try:
        aid = _safe_segment(agent_id)
        base = REPO_ROOT / pack_folder / "Output" / aid
        hist = base / "history"
        hist.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        body = _header(pipeline) + content
        hpath = hist / f"{ts}_{aid}.md"
        hpath.write_text(body, encoding="utf-8")
        lpath = base / "latest.md"
        lpath.write_text(body, encoding="utf-8")
        rel = lambda p: str(p.relative_to(REPO_ROOT)).replace("\\", "/")
        return {
            "output_pack": pack_folder,
            "output_agent_id": aid,
            "output_dir": rel(base),
            "output_latest": rel(lpath),
            "output_history": rel(hpath),
        }
    except OSError as e:
        return {"output_save_error": str(e)}


def save_sdlc_crew_report(
    content: str,
    pipeline: str,
) -> dict[str, Any]:
    """``POST /v1/report`` — under ``sdlc_crew/Output/reporting/``."""
    return save_pack_agent_output(
        pack_folder="sdlc_crew",
        agent_id="reporting",
        content=content,
        pipeline=pipeline,
    )


def save_sdlc_then_report_pair(
    *,
    sdlc_text: str,
    report_text: str,
    pipeline: str,
) -> dict[str, Any]:
    """``POST /v1/sdlc-then-report`` — under ``sdlc_crew/Output/sdlc_then_report/``."""
    if not _enabled():
        return {}
    out: dict[str, Any] = {}
    try:
        base = REPO_ROOT / "sdlc_crew" / "Output" / "sdlc_then_report"
        sub = base / "history" / datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        sub.mkdir(parents=True, exist_ok=True)
        h_sdlc = _header(pipeline) + sdlc_text
        h_rep = _header(pipeline) + report_text
        (sub / "sdlc.md").write_text(h_sdlc, encoding="utf-8")
        (sub / "report.md").write_text(h_rep, encoding="utf-8")
        (base / "latest_sdlc.md").write_text(h_sdlc, encoding="utf-8")
        (base / "latest_report.md").write_text(h_rep, encoding="utf-8")
        rel = lambda p: str(p.relative_to(REPO_ROOT)).replace("\\", "/")
        out["output_pack"] = "sdlc_crew"
        out["output_agent_id"] = "sdlc_then_report"
        out["output_dir"] = rel(base)
        out["output_history_run"] = rel(sub)
        out["output_latest_sdlc"] = rel(base / "latest_sdlc.md")
        out["output_latest_report"] = rel(base / "latest_report.md")
    except OSError as e:
        out["output_save_error"] = str(e)
    return out


def merge_extra(
    base_extra: dict[str, Any] | None,
    saved: dict[str, Any],
) -> dict[str, Any] | None:
    m: dict[str, Any] = {**(base_extra or {}), **(saved or {})}
    m = {k: v for k, v in m.items() if v is not None and v != ""}
    return m or None


def safe_output_segment(s: str) -> str:
    """Public alias for the safe output folder segment (agent id, step folder names)."""
    return _safe_segment(s)


def save_orchestrated_step_artifact(
    *,
    step_index: int,
    pack_folder: str,
    agent_id: str,
    step_content: str,
    pipeline: str,
    bundle_folder: str = "orchestrated_agents",
    bundle_agent_id: str = "orchestrated_run",
) -> dict[str, Any]:
    """
    1) Saves to the same path as a normal API run: ``{pack}/Output/{agent_id}/latest.md`` (+ history).
    2) Writes a copy under ``{bundle}/Output/{bundle_agent}/steps/{nnn_agentId}/content.md`` for the ZIP bundle.

    Returns rel paths and merge-friendly keys. Empty if ``ORCHESTRATOR_SAVE_OUTPUT`` is off.
    """
    out: dict[str, Any] = {}
    if not _enabled() or not (step_content and str(step_content).strip()):
        return out
    out.update(
        save_pack_agent_output(
            pack_folder=pack_folder,
            agent_id=agent_id,
            content=step_content,
            pipeline=pipeline,
        )
    )
    try:
        step_name = f"{int(step_index):03d}_{_safe_segment(agent_id)}"
        bundle_base = REPO_ROOT / bundle_folder / "Output" / _safe_segment(bundle_agent_id) / "steps" / step_name
        bundle_base.mkdir(parents=True, exist_ok=True)
        body = _header(pipeline) + step_content
        cpath = bundle_base / "content.md"
        cpath.write_text(body, encoding="utf-8")
        rel = lambda p: str(p.relative_to(REPO_ROOT)).replace("\\", "/")
        out["orchestrated_step_dir"] = rel(bundle_base)
        out["orchestrated_step_content"] = rel(cpath)
    except OSError as e:
        out["orchestrated_step_save_error"] = str(e)
    return out


def write_orchestrated_run_manifest(
    *,
    user_prompt: str,
    plan: dict[str, Any],
    step_index_dirs: list[dict[str, Any]],
    bundle_folder: str = "orchestrated_agents",
    bundle_agent_id: str = "orchestrated_run",
) -> dict[str, Any]:
    """
    Writes ``orchestrated_manifest.json`` and ``PROJECT_INDEX.md`` under the bundle output folder.
    """
    out: dict[str, Any] = {}
    if not _enabled():
        return out
    try:
        import json

        base = REPO_ROOT / bundle_folder / "Output" / _safe_segment(bundle_agent_id)
        base.mkdir(parents=True, exist_ok=True)
        manifest = {
            "bundle_agent_id": bundle_agent_id,
            "user_prompt_summary": (user_prompt or "")[:2000],
            "rationale": (plan or {}).get("rationale"),
            "steps": step_index_dirs,
        }
        mpath = base / "orchestrated_manifest.json"
        mpath.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        # Human-readable table of contents for the ZIP
        lines: list[str] = [
            "# Orchestrated run — project bundle",
            "",
            "This folder is produced by **Auto — AI picks agents**. Each subfolder under `steps/` is one agent step; "
            "the combined report is in `latest.md` (also returned as API `content`).",
            "",
            "These outputs are **specifications and documentation** (Markdown). They are not a full source-code repo "
            "unless a step explicitly included generated text you can copy into a project.",
            "",
            "## Step outputs (under `steps/`)",
            "",
        ]
        for row in step_index_dirs:
            idx = row.get("index", "?")
            p = row.get("pack", "")
            a = row.get("agent_id", "")
            rel_d = row.get("step_dir_rel", "")
            lines.append(f"- **Step {idx}** — `{p}` / `{a}` → `{rel_d}`")
        lines.append("")
        lines.append("## Manifest")
        lines.append(f"- `orchestrated_manifest.json` — machine-readable list of steps and paths")
        lines.append("")
        ipath = base / "PROJECT_INDEX.md"
        ipath.write_text("\n".join(lines), encoding="utf-8")
        rel = lambda p: str(p.relative_to(REPO_ROOT)).replace("\\", "/")
        out["orchestrated_manifest"] = rel(mpath)
        out["orchestrated_project_index"] = rel(ipath)
    except OSError as e:
        out["orchestrated_manifest_error"] = str(e)
    return out


def copy_file_into_orchestrated_step(
    source_repo_relative: str,
    *,
    step_index: int,
    agent_id: str,
    dest_name: str,
    bundle_folder: str = "orchestrated_agents",
    bundle_agent_id: str = "orchestrated_run",
) -> str | None:
    """
    Copy a file (e.g. wireframe png) from another pack output into the orchestrated step folder ``artifacts/``.
    Returns relative path to the copy, or None.
    """
    if not _enabled() or not source_repo_relative:
        return None
    try:
        import shutil

        src = (REPO_ROOT / source_repo_relative).resolve()
        if not src.is_file():
            return None
        step_name = f"{int(step_index):03d}_{_safe_segment(agent_id)}"
        dest_dir = (
            REPO_ROOT / bundle_folder / "Output" / _safe_segment(bundle_agent_id) / "steps" / step_name / "artifacts"
        )
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / dest_name
        shutil.copy2(src, dest)
        return str(dest.relative_to(REPO_ROOT)).replace("\\", "/")
    except OSError:
        return None
