"""
LLM → validated source files on disk, under ``codegen_agents/Output/{run_id}/``.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_capabilities.brain import resolve_llm
from agent_run_output import REPO_ROOT

from .path_validate import is_allowed_artifact_path, normalize_rel_path

MAX_SPEC_CHARS = 100_000
MAX_TOTAL_FILE_CHARS = 500_000
MAX_FILES = 40
MAX_FILE_CHARS = 100_000


def _read_orchestrated_latest() -> str:
    p = REPO_ROOT / "orchestrated_agents" / "Output" / "orchestrated_run" / "latest.md"
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def _build_messages(
    *,
    user_prompt: str,
    spec: str,
    constraints: str,
    stack: str,
) -> list[dict[str, str]]:
    sys = f"""You are a senior software engineer. You receive a product/architecture spec (Markdown) and must output
a **JSON object** (no markdown fences) with exactly these keys:
- "summary": string — short description of what you generated and how to run or open the project.
- "files": array of objects, each {{"path": "<relative/posix/path>", "content": "<utf-8 text file body>"}}.

Rules:
1. **stack hint:** "{stack}" — if `android` or `kotlin` appears (case-insensitive), generate a **minimal** Android
   Studio–compatible project layout: `settings.gradle` or `settings.gradle.kts`, project + app `build.gradle` or
   `.kts`, `AndroidManifest.xml`, at least one `Activity` in Kotlin, `res/layout/*.xml` as needed, `values/strings.xml`.
   If `web` or `react` appears, use a small Vite/React or plain HTML+JS tree. If `node` or `express`, a tiny Express
   `package.json` + `src/index.js` or `ts`. If `auto`, pick the most plausible from the spec.
2. All **path** values must be relative (no `..`, no drive letters). Use forward slashes in JSON.
3. Every file must be **plain text** source or config. No base64, no binary.
4. Prefer **at most {MAX_FILES}** files, each under ~{MAX_FILE_CHARS} characters. Keep the sample **runnable** or
   buildable in principle (Gradle/ npm scripts where applicable).
5. Include a **README.md** at project root with setup steps.
6. If the spec is vague, make reasonable defaults (package name, app name) and state them in README.

Return only valid JSON."""

    user = f"""## Codegen request
{user_prompt}

## Stack / constraints
{constraints}

## Specification (markdown)
{spec}
"""
    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": user},
    ]


def run_codegen_from_spec(
    *,
    user_prompt: str,
    spec_markdown: str,
    constraints: str = "None specified.",
    stack: str = "auto",
    load_orchestrated_latest: bool = False,
    llm_model: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Writes ``codegen_agents/Output/{{run_id}}/**`` and returns ``(summary_markdown, meta)``.
    """
    from openai import OpenAI

    if load_orchestrated_latest:
        from_disk = _read_orchestrated_latest()
        spec = (from_disk or spec_markdown or "").strip() or (spec_markdown or "")
    else:
        spec = (spec_markdown or "").strip()

    if len(spec) < 20:
        if load_orchestrated_latest:
            raise ValueError(
                "No specification text: either paste spec_markdown (20+ chars) or run Auto first and save "
                "orchestrated_agents/Output/orchestrated_run/latest.md on the server (ORCHESTRATOR_SAVE_OUTPUT=1).",
            )
        raise ValueError("spec_markdown is too short (need at least 20 characters) or use load_orchestrated_latest with a saved Auto run.")

    spec = spec[:MAX_SPEC_CHARS]
    model = (llm_model or "").strip() or resolve_llm()
    run_id = f"codegen_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    out_base = REPO_ROOT / "codegen_agents" / "Output" / run_id
    out_base.mkdir(parents=True, exist_ok=True)

    client = OpenAI()
    raw = client.chat.completions.create(
        model=model,
        temperature=0.15,
        response_format={"type": "json_object"},
        messages=_build_messages(
            user_prompt=user_prompt,
            spec=spec,
            constraints=constraints or "None specified.",
            stack=stack or "auto",
        ),
    )
    text = (raw.choices[0].message.content or "").strip()
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Model returned non-object JSON")

    summary = str(data.get("summary") or "Generated project.")
    files_raw = data.get("files")
    if not isinstance(files_raw, list) or not files_raw:
        raise ValueError("Model JSON missing non-empty 'files' array")

    total_chars = 0
    written: list[str] = []
    errors: list[str] = []
    n = 0
    for item in files_raw[:MAX_FILES]:
        if not isinstance(item, dict):
            continue
        rel = str(item.get("path") or "").strip()
        content = str(item.get("content") or "")
        if not rel or not is_allowed_artifact_path(rel):
            errors.append(f"skip bad path: {rel!r}")
            continue
        rel_n = normalize_rel_path(rel)
        if len(content) > MAX_FILE_CHARS:
            content = content[:MAX_FILE_CHARS] + "\n\n[truncated by codegen pipeline]\n"
        total_chars += len(content)
        if total_chars > MAX_TOTAL_FILE_CHARS:
            errors.append("stopped: MAX_TOTAL_FILE_CHARS")
            break
        dest = out_base / rel_n.replace("/", os.sep)
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            errors.append(f"mkdir {dest}: {e}")
            continue
        try:
            dest.write_text(content, encoding="utf-8", errors="strict")
        except OSError as e:
            errors.append(f"write {rel_n}: {e}")
            continue
        written.append(rel_n)
        n += 1

    if not written:
        raise ValueError("No valid files were written. " + " ".join(errors[:5]))

    # Record meta on disk
    meta_disk = {
        "run_id": run_id,
        "stack": stack,
        "files": written,
        "errors": errors,
        "model": model,
    }
    (out_base / "codegen_meta.json").write_text(json.dumps(meta_disk, indent=2, ensure_ascii=False), encoding="utf-8")

    rel_root = out_base.relative_to(REPO_ROOT)
    summary_md = "\n\n".join(
        [
            "# Codegen result",
            "",
            f"**Run id:** `{run_id}`",
            f"**Files written:** {len(written)}",
            "",
            "## Model summary",
            summary,
            "",
            "## Files",
            "\n".join(f"- `{f}`" for f in written[:50]),
            "",
            f"**Output directory (repo):** `{rel_root.as_posix()}/`",
            f"**ZIP:** `GET` `/v1/artifact/output-zip?pack=codegen_agents&agent_id={run_id}` (Bearer) or use **Export → ZIP** in the UI with this run.",
        ]
    )
    if errors:
        summary_md += "\n\n## Notes\n" + "\n".join(f"- {e}" for e in errors[:20])

    meta: dict[str, Any] = {
        "codegen": True,
        "codegen_run_id": run_id,
        "codegen_file_count": len(written),
        "codegen_files": written[:200],
    }
    return summary_md, meta
