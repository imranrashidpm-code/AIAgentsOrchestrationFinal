"""
End-to-end orchestrated run: plan → execute steps → merge markdown.
"""

from __future__ import annotations

import traceback
from typing import Any

from agent_capabilities.brain import reset_request_llm_model, set_request_llm_model
from agent_run_output import (
    copy_file_into_orchestrated_step,
    save_orchestrated_step_artifact,
    write_orchestrated_run_manifest,
)

from .dispatch import execute_step, result_to_text
from .fallback import build_fallback_plan
from .planner import plan_workflow


def run_orchestrated(
    *,
    user_prompt: str,
    constraints: str,
    business_context: str,
    llm_model: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Returns ``(markdown_content, meta_dict)`` where ``meta`` includes plan and per-step info.
    """
    tok = set_request_llm_model(llm_model)
    try:
        try:
            plan = plan_workflow(
                user_prompt=user_prompt,
                constraints=constraints,
                business_context=business_context,
                llm_model=llm_model,
            )
        except Exception:
            plan = build_fallback_plan(user_prompt, constraints, business_context)
        steps_in = plan.get("steps") or []
        if not steps_in:
            plan = build_fallback_plan(user_prompt, constraints, business_context)
            steps_in = plan.get("steps") or []
        sections: list[str] = [
            "# Orchestrated run\n",
            f"**Planner rationale:** {plan.get('rationale', '—')}\n",
            f"**Steps:** {len(steps_in)}\n",
            "\n---\n",
        ]
        step_meta: list[dict[str, Any]] = []
        extra_wire: dict[str, Any] = {}
        manifest_rows: list[dict[str, Any]] = []

        for i, st in enumerate(steps_in, start=1):
            pack = st["pack"]
            agent_id = st["agent_id"]
            header = f"\n## Step {i}: `{pack}` / `{agent_id}`\n\n"
            sections.append(header)
            one: dict[str, Any] = {
                "index": i,
                "pack": pack,
                "agent_id": agent_id,
            }
            try:
                result = execute_step(
                    pack,
                    agent_id,
                    {
                        "user_prompt": st["user_prompt"],
                        "constraints": st["constraints"],
                        "business_context": st["business_context"],
                    },
                )
                full_text = result_to_text(result)
                display_text = full_text
                if len(display_text) > 80000:
                    display_text = display_text[:80000] + (
                        "\n\n[… truncated in combined view only; full text is under each pack Output/ and in steps/ …]\n"
                    )
                sections.append(display_text + "\n")
                one["ok"] = True
                one["length"] = len(full_text)

                pipe = f"orchestrated:step{i}:{pack}:{agent_id}"
                saved_step = save_orchestrated_step_artifact(
                    step_index=i,
                    pack_folder=pack,
                    agent_id=agent_id,
                    step_content=full_text,
                    pipeline=pipe,
                )
                for k, v in saved_step.items():
                    if k.startswith("output_") or k.startswith("orchestrated_"):
                        one[k] = v
                if saved_step.get("orchestrated_step_dir"):
                    one["step_dir_rel"] = saved_step.get("orchestrated_step_dir")
                    one["output_latest"] = saved_step.get("output_latest")

                w = getattr(result, "_orchestrated_wireframe_meta", None)
                if w:
                    extra_wire.update(w)
                    one["wireframe_meta"] = w
                    for fname in ("output_wireframe_png", "output_wireframe_jpeg"):
                        rel_p = w.get(fname)
                        if rel_p:
                            ext = "wireframe.png" if "png" in fname else "wireframe.jpg"
                            cpy = copy_file_into_orchestrated_step(
                                rel_p,
                                step_index=i,
                                agent_id=agent_id,
                                dest_name=ext,
                            )
                            if cpy:
                                one["artifact_copy_" + ext.split(".")[-1]] = cpy
                we = getattr(result, "_orchestrated_wireframe_error", None)
                if we:
                    one["wireframe_error"] = we
            except Exception as e:
                tb = traceback.format_exc()
                sections.append(f"**Error in this step:** {e}\n\n```\n{tb[:4000]}\n```\n")
                one["ok"] = False
                one["error"] = str(e)[:2000]
            step_meta.append(one)
            manifest_rows.append(
                {
                    "index": i,
                    "pack": one.get("pack"),
                    "agent_id": one.get("agent_id"),
                    "ok": one.get("ok", False),
                    "step_dir_rel": one.get("step_dir_rel"),
                    "pack_output_latest": one.get("output_latest") or one.get("pack_output_latest"),
                }
            )

        man = write_orchestrated_run_manifest(
            user_prompt=user_prompt,
            plan=plan if isinstance(plan, dict) else {},
            step_index_dirs=manifest_rows,
        )
        combined = "\n".join(sections)
        meta: dict[str, Any] = {
            "orchestrated": True,
            "orchestrated_bundle_agent_id": "orchestrated_run",
            "orchestrated_steps_written": len([r for r in manifest_rows if r.get("ok")]),
            "plan": {
                "rationale": plan.get("rationale"),
                "steps": [
                    {k: st[k] for k in ("pack", "agent_id", "user_prompt", "constraints", "business_context") if k in st}
                    for st in steps_in
                ],
            },
            "step_results": step_meta,
        }
        meta.update(man)
        if extra_wire:
            meta.update(extra_wire)
        return combined, meta
    finally:
        reset_request_llm_model(tok)
