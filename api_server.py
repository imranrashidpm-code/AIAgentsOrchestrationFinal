"""
HTTP API for the Reporting agent (and SDLC+Reporting chain) for use from web apps,
mobile clients, or AI chat / bot frontends.

Run locally:
  uvicorn api_server:app --host 0.0.0.0 --port 8080

OpenAPI: http://localhost:8080/docs

Set ORCHESTRATOR_API_KEY in production and send Authorization: Bearer <token> on POST routes.
"""

from __future__ import annotations

import asyncio
import io
import os
import time
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path as FsPath
from typing import Any, Callable

from agent_capabilities.brain import reset_request_llm_model, set_request_llm_model
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Path, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

APP_DIR = FsPath(__file__).resolve().parent

# Load .env before importing crews (so OPENAI_API_KEY, DB URL, etc. are set)
load_dotenv()

from agent_run_output import (
    merge_extra,
    output_dir_for,
    save_pack_agent_output,
    save_sdlc_crew_report,
    save_sdlc_then_report_pair,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    # shutdown hooks if needed later


app = FastAPI(
    title="AI Agents Orchestrator API",
    description="Reporting, SDLC, **Automation**, **GTM**, **Design**, **Project Management**, **DevOps & platform**, **QA & test strategy**, **Data & analytics**, **HR & talent**, **orchestrated (auto plan + multi-agent run)**, **codegen (app source tree from spec MD)**, plus **greenfield** packs: "
    "mobile architecture, API/contract, security & privacy, integration/BFF, observability, release & distribution, localization. "
    "Use the `content` field in responses as the assistant/bot message body. Successful runs are also saved under each pack’s "
    "``Output/{agent_id}/latest.md`` and ``Output/{agent_id}/history/`` (see `meta.output_*` keys; disable with ``ORCHESTRATOR_SAVE_OUTPUT=0``). "
    "CLIs may still use ``--out-dir`` for additional layout.",
    version="1.0.0",
    lifespan=lifespan,
)

_cors = os.environ.get("ORCHESTRATOR_CORS_ORIGINS", "*").strip()
_origins = [o.strip() for o in _cors.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins if _origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _require_api_key(authorization: str | None = Header(None, alias="Authorization")) -> None:
    key = os.environ.get("ORCHESTRATOR_API_KEY", "").strip()
    if not key:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header (Bearer token required).")
    token = authorization[len("Bearer ") :].strip()
    if token != key:
        raise HTTPException(status_code=401, detail="Invalid API token.")


def _wrap_response(
    content: str,
    *,
    pipeline: str,
    started: float,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ms = int((time.perf_counter() - started) * 1000)
    out: dict[str, Any] = {
        "ok": True,
        "content": content,
        "pipeline": pipeline,
        "duration_ms": ms,
    }
    if extra:
        out["meta"] = extra
    return out


def _run_exception_as_http(e: Exception) -> HTTPException:
    """
    Map common local setup failures (e.g. missing ``crewai`` when using the wrong Python) to
    503 and a clearer message than a raw ``ModuleNotFoundError`` string.
    """
    if isinstance(e, ModuleNotFoundError):
        name = getattr(e, "name", None) or ""
        if name == "crewai" or "crewai" in str(e).lower():
            return HTTPException(
                status_code=503,
                detail=(
                    "CrewAI is not installed or the process is using a Python that cannot load it. "
                    "Use Python 3.10–3.13, install deps (e.g. pip install -r requirements.txt), and start the API with "
                    "the project venv: .venv\\Scripts\\python -m uvicorn api_server:app --host 127.0.0.1 --port 8080 — "
                    "or run .\\run_api.ps1 on Windows."
                ),
            )
        if name:
            return HTTPException(
                status_code=503,
                detail=f"Missing Python module: {name!r}. Run: pip install -r requirements.txt (use Python 3.10–3.13).",
            )
    return HTTPException(status_code=500, detail=str(e))


async def _to_thread_with_optional_llm(llm_model: str | None, fn: Callable[[], Any]) -> Any:
    """Run ``fn`` in a worker thread; ``llm_model`` (if set) overrides env for that run via :class:`contextvars`."""
    tok = set_request_llm_model(llm_model)
    try:
        return await asyncio.to_thread(fn)
    finally:
        reset_request_llm_model(tok)


# --- Schemas (stable for any client / bot) ---


class ReportRequest(BaseModel):
    """Run only the Reporting agent. Send either `prompt` or `user_message` (chat-bot alias)."""

    model_config = {"populate_by_name": True}

    prompt: str = Field(
        ...,
        min_length=1,
        description="User question (natural language).",
        validation_alias=AliasChoices("prompt", "user_message", "message"),
    )
    context: str = Field(
        default="None specified.",
        description="Optional business rules, units, or extra instructions.",
    )
    llm_model: str | None = Field(
        default=None,
        description="Override model for this run only. Server .env still supplies OPENAI_API_KEY.",
    )


class SdlcThenReportRequest(BaseModel):
    """Run full SDLC, then Reporting with SDLC text as context."""

    project_brief: str = Field(..., min_length=1)
    constraints: str = "None specified."
    module_scope: str = "Full product"
    sprint_context: str = "Full pipeline"
    report_prompt: str = Field(
        ...,
        min_length=1,
        description="Instructions for the Reporting step after SDLC.",
    )
    report_context: str = Field(
        default="None specified.",
        description="Extra text passed only to the Reporting step.",
    )
    llm_model: str | None = Field(
        default=None,
        description="Override model for this run only. Server .env still supplies OPENAI_API_KEY.",
    )


class ErrorBody(BaseModel):
    ok: bool = False
    error: str
    content: str = ""


class AutomationRequest(BaseModel):
    """Body for a single automation agent (ERP workflow). Use `content` in the response in UIs."""

    model_config = {"populate_by_name": True}

    user_prompt: str = Field(
        ...,
        min_length=1,
        description="What you want the agent to do.",
        validation_alias=AliasChoices("user_prompt", "prompt", "user_message", "message"),
    )
    constraints: str = Field(default="None specified.", description="Policy or rule constraints.")
    business_context: str = Field(
        default="None specified.",
        description="Paste ERP data, log excerpts, or free-text context.",
    )
    llm_model: str | None = Field(
        default=None,
        description="Override model for this run only. Server .env still supplies OPENAI_API_KEY.",
    )


class SalesMarketingRequest(AutomationRequest):
    """Same JSON shape as automation agents; **examples** are tuned for GTM `sm_*` agents in OpenAPI /docs."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "user_prompt": (
                        "Plan an integrated Q2 marketing campaign for mid-market buyers in the US and UK, "
                        "with objectives, channel mix, and weekly milestones."
                    ),
                    "constraints": "B2B SaaS; 3-person marketing team; $20–50K ACV; no direct mail.",
                    "business_context": (
                        "Product: workflow automation for operations teams; ICP: VP Operations in 500–2000 FTE companies."
                    ),
                },
            ],
        },
    )


class DesignRequest(AutomationRequest):
    """``dg_*`` Design Agents — use `content` in UIs, or the **design_run.py** CLI with ``--out-dir`` to save files."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "user_prompt": "Redesign the checkout flow for web: fewer steps, guest checkout, and clearer errors.",
                    "constraints": "Existing brand; WCAG 2.2 AA; no new payment providers this quarter.",
                    "business_context": "B2C retail; 40% mobile; Stripe already integrated.",
                },
            ],
        },
    )


class ProjectManagementRequest(AutomationRequest):
    """``pm_*`` Project Management Agents — PMBOK phases plus ERD, architecture, and sprint roadmaps. Prefer **pm_run.py** with ``--out-dir`` to save phase/artifact folders on disk; the API only returns the markdown body in ``content``."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "user_prompt": "Greenfield: customer self-service portal with auth, case management, and KB search.",
                    "constraints": "2-week sprints; 2 backend, 2 frontend, 1 QA; launch in 4 months (target).",
                    "business_context": "Java + React; PostgreSQL; AWS; SSO via Okta planned.",
                },
            ],
        },
    )


class DevOpsPlatformRequest(AutomationRequest):
    """``dvp_*`` DevOps & platform — runbooks, postmortems, SLO/SLA, CI/CD, K8s (high level)."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "user_prompt": "Runbook: blue/green deploy for the payments service on EKS with rollback if error rate > 1%.",
                    "constraints": "Maintenance window 02:00–04:00 UTC; on-call in EU and US; PCI zone.",
                    "business_context": "Argo CD; Datadog; payments-api v3.2.1.",
                },
            ],
        },
    )


class QaTestStrategyRequest(AutomationRequest):
    """``qts_*`` QA & test strategy — test plan, RBT, E2E scope, regression strategy."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "user_prompt": "E2E scope for a new saved-payment-methods feature on web and iOS webview.",
                    "constraints": "2 week sprint; 1 automation engineer; staging only; no full prod test data.",
                    "business_context": "Stripe; React SPA; Okta; feature flag FF_PAY_V2.",
                },
            ],
        },
    )


class DataAnalyticsRequest(AutomationRequest):
    """``dta_*`` Data & analytics — metrics, dashboards, events, warehouse/dbt (conceptual). Complements the Reporting SQL agent."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "user_prompt": "Define North Star, activation, and retention metrics for a B2B PLG analytics product.",
                    "constraints": "Snowflake; dbt; no PII in self-serve exports; RLS in BI.",
                    "business_context": "ACME-tenant SaaS; accounts + users; trial-to-paid journey.",
                },
            ],
        },
    )


class HrTalentRequest(AutomationRequest):
    """``hrt_*`` HR & talent — drafts and checklists only; not legal advice. Review with HR and counsel where needed."""

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "user_prompt": "Senior Software Engineer, backend, remote EU, fintech, Java/Spring, AWS.",
                    "constraints": "EEO; no salary in JD public version; 4 interview rounds max.",
                    "business_context": "50-person product eng; SRE on-call rotation shared.",
                },
            ],
        },
    )


class CodegenRequest(BaseModel):
    """Generate a source tree on disk from specification markdown. Download ZIP with ``GET /v1/artifact/output-zip?pack=codegen_agents&agent_id=<run_id>`` (``run_id`` is in response ``meta``)."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",
    )
    user_prompt: str = Field(
        ...,
        min_length=1,
        description="What to build (e.g. Android login + welcome screen) and any codegen hints.",
        validation_alias=AliasChoices("user_prompt", "prompt", "user_message", "message"),
    )
    spec_markdown: str = Field(
        default="",
        description="Full product/spec markdown. Paste Auto-orchestrated output here, or leave empty when `load_orchestrated_latest` is true and that file exists.",
    )
    constraints: str = Field(default="None specified.", description="Stack hints, min SDK, no third-party, etc.")
    stack: str = Field(
        default="auto",
        description="`auto`, `android_kotlin`, `web_react`, `node_express`, or similar to steer the model.",
    )
    load_orchestrated_latest: bool = Field(
        default=False,
        description="If true, spec text is read from `orchestrated_agents/Output/orchestrated_run/latest.md` (when present), "
        "with `spec_markdown` as fallback when file is empty.",
    )
    llm_model: str | None = Field(
        default=None,
        description="Override model for this run; server .env still supplies OPENAI_API_KEY.",
    )


# --- Routes ---


def _truthy_env(name: str) -> bool:
    v = (os.environ.get(name) or "").strip().lower()
    return v in ("1", "true", "yes", "on")


@app.get("/v1/sandbox/ui-bearer", include_in_schema=False)
def sandbox_ui_bearer(request: Request) -> dict[str, Any]:
    """
    **Local dev only** (set ``ORCHESTRATOR_UI_SANDBOX=1`` in ``.env``): returns the current
    ``ORCHESTRATOR_API_KEY`` so the static ``/app/`` page can pre-fill the Bearer field.
    Responds 404 if sandbox is off or the client is not loopback. Do not enable in production.
    """
    if not _truthy_env("ORCHESTRATOR_UI_SANDBOX"):
        raise HTTPException(status_code=404, detail="Not found")
    if not request.client:
        raise HTTPException(status_code=404, detail="Not found")
    host = (request.client.host or "").lower()
    if host not in ("127.0.0.1", "localhost", "::1", "::ffff:127.0.0.1"):
        raise HTTPException(status_code=404, detail="Not found")
    k = os.environ.get("ORCHESTRATOR_API_KEY", "").strip()
    return {"bearer": k or None}


_ALLOWED_ZIP_PACKS = frozenset(
    {
        "design_agents",
        "automation_agents",
        "sales_marketing_agents",
        "project_management_agents",
        "devops_platform_agents",
        "qa_test_strategy_agents",
        "data_analytics_agents",
        "hr_talent_agents",
        "orchestrated_agents",
        "codegen_agents",
        "mobile_architecture_agent",
        "api_contract_agent",
        "security_privacy_agent",
        "integration_bff_agent",
        "observability_agent",
        "release_distribution_agent",
        "localization_agent",
        "sdlc_crew",
    },
)


@app.get(
    "/v1/artifact/output-zip",
    dependencies=[Depends(_require_api_key)],
    summary="Download the saved Output/{agent} folder as a .zip (same paths as meta.output_pack / output_agent_id).",
)
def download_output_zip(
    pack: str = Query(..., description="Pack directory, e.g. design_agents"),
    agent_id: str = Query(..., description="Agent id under Output/"),
) -> StreamingResponse:
    if pack not in _ALLOWED_ZIP_PACKS:
        raise HTTPException(status_code=400, detail="Invalid pack parameter.")
    base = output_dir_for(pack, agent_id)
    if not base.is_dir():
        raise HTTPException(
            status_code=404,
            detail="No saved output folder. Run the agent with ORCHESTRATOR_SAVE_OUTPUT=1, then try again.",
        )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in base.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(base).as_posix())
    buf.seek(0)
    fname = f"{pack}_{base.name}_output.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


_ALLOWED_ARTIFACT_FILES = frozenset(
    {
        "latest_wireframe.png",
        "latest_wireframe.jpg",
    }
)


@app.get(
    "/v1/artifact/file",
    dependencies=[Depends(_require_api_key)],
    summary="Download a single file from a pack Output folder (e.g. wireframe PNG/JPEG).",
)
def download_artifact_file(
    pack: str = Query(..., description="Pack directory, e.g. design_agents"),
    agent_id: str = Query(..., description="Agent id under Output/"),
    file: str = Query(..., description="e.g. latest_wireframe.png"),
) -> FileResponse:
    if pack not in _ALLOWED_ZIP_PACKS:
        raise HTTPException(status_code=400, detail="Invalid pack parameter.")
    if file not in _ALLOWED_ARTIFACT_FILES:
        raise HTTPException(status_code=400, detail="Invalid file name.")
    path = output_dir_for(pack, agent_id) / file
    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="File not found. For wireframe images, use agent dg_wireframe_spec and run again after installing matplotlib.",
        )
    media = "image/png" if file.endswith(".png") else "image/jpeg"
    return FileResponse(path, media_type=media, filename=file)


@app.get("/health")
def health() -> dict[str, str]:
    return {"ok": "true", "service": "ai-agents-orchestrator"}


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "AI Agents Orchestrator API",
        "docs": "/docs",
        "health": "/health",
        "browser_ui": "/app/",
        "reporting": "POST /v1/report",
        "orchestrated_info": "GET /v1/orchestrated/info",
        "orchestrated_run": "POST /v1/orchestrated/run",
        "codegen_generate": "POST /v1/codegen/generate",
        "sdlc_then_report": "POST /v1/sdlc-then-report",
        "automation_agents": "GET /v1/automation/agents",
        "automation_run": "POST /v1/automation/{agent_id}",
        "sales_marketing_agents": "GET /v1/sales-marketing/agents",
        "sales_marketing_run": "POST /v1/sales-marketing/{agent_id}",
        "design_agents": "GET /v1/design/agents",
        "design_run": "POST /v1/design/{agent_id}",
        "project_management_agents": "GET /v1/project-management/agents",
        "project_management_run": "POST /v1/project-management/{agent_id}",
        "devops_platform_agents": "GET /v1/devops-platform/agents",
        "devops_platform_run": "POST /v1/devops-platform/{agent_id}",
        "qa_test_strategy_agents": "GET /v1/qa-test-strategy/agents",
        "qa_test_strategy_run": "POST /v1/qa-test-strategy/{agent_id}",
        "data_analytics_agents": "GET /v1/data-analytics/agents",
        "data_analytics_run": "POST /v1/data-analytics/{agent_id}",
        "hr_talent_agents": "GET /v1/hr-talent/agents",
        "hr_talent_run": "POST /v1/hr-talent/{agent_id}",
        "mobile_architecture": "GET /v1/mobile-architecture/agents",
        "mobile_architecture_run": "POST /v1/mobile-architecture/{agent_id}",
        "api_contract": "GET /v1/api-contract/agents",
        "api_contract_run": "POST /v1/api-contract/{agent_id}",
        "security_privacy": "GET /v1/security-privacy/agents",
        "security_privacy_run": "POST /v1/security-privacy/{agent_id}",
        "integration_bff": "GET /v1/integration-bff/agents",
        "integration_bff_run": "POST /v1/integration-bff/{agent_id}",
        "observability": "GET /v1/observability/agents",
        "observability_run": "POST /v1/observability/{agent_id}",
        "release_distribution": "GET /v1/release-distribution/agents",
        "release_distribution_run": "POST /v1/release-distribution/{agent_id}",
        "localization": "GET /v1/localization/agents",
        "localization_run": "POST /v1/localization/{agent_id}",
        "output_zip": "GET /v1/artifact/output-zip?pack=…&agent_id=… (Bearer; zips saved Output folder)",
    }


@app.post("/v1/report", dependencies=[Depends(_require_api_key)])
async def post_report(req: ReportRequest) -> dict[str, Any]:
    """
    Generate a business report from a natural-language prompt. Suitable for direct use as the
    **assistant** message in a chat UI: read `content` and display to the user.
    """
    started = time.perf_counter()

    def _run() -> Any:
        from sdlc_crew import run_reporting_pipeline

        return run_reporting_pipeline(
            {
                "user_report_prompt": req.prompt,
                "reporting_context": req.context,
            }
        )

    try:
        result = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    text = getattr(result, "raw", None) or ""
    saved = save_sdlc_crew_report(text, "report")
    return _wrap_response(
        text,
        pipeline="report",
        started=started,
        extra=merge_extra(None, saved),
    )


@app.get("/v1/orchestrated/info")
def get_orchestrated_info() -> dict[str, Any]:
    """Describe **orchestrated** mode (LLM picks agents from the full catalog)."""
    from orchestrated_agents import orchestrated_info

    return orchestrated_info()


@app.post(
    "/v1/orchestrated/run",
    dependencies=[Depends(_require_api_key)],
    summary="Auto-orchestrate: plan which agents to run, then run them in sequence",
)
async def post_orchestrated_run(req: AutomationRequest) -> dict[str, Any]:
    """
    One prompt: an OpenAI JSON planner selects **3+** steps from the full agent catalog (design, PM, QA,
    mobile architecture, SDLC pipeline, etc.), then each step runs in order. Response `content` is combined
    markdown; `meta.plan` holds the chosen steps and rationale.
    """
    started = time.perf_counter()

    def _run() -> Any:
        from orchestrated_agents import run_orchestrated

        return run_orchestrated(
            user_prompt=req.user_prompt,
            constraints=req.constraints or "None specified.",
            business_context=req.business_context or "None specified.",
            llm_model=req.llm_model,
        )

    try:
        text, meta_extra = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    saved = save_pack_agent_output(
        pack_folder="orchestrated_agents",
        agent_id="orchestrated_run",
        content=text,
        pipeline="orchestrated:multi",
    )
    return _wrap_response(
        text,
        pipeline="orchestrated:multi",
        started=started,
        extra=merge_extra(
            merge_extra(
                {
                    "agent_id": "orchestrated_run",
                    "suggested_file_path": "orchestrated/orchestrated_run.md",
                    "orchestrated": True,
                },
                saved,
            ),
            meta_extra,
        ),
    )


@app.post(
    "/v1/codegen/generate",
    dependencies=[Depends(_require_api_key)],
    summary="Codegen: create source files from spec markdown, ZIP from codegen_agents/Output",
)
async def post_codegen_generate(req: CodegenRequest) -> dict[str, Any]:
    """
    Runs the **codegen** pipeline: model emits a JSON list of (path, content) text files, written under
    ``codegen_agents/Output/{codegen_run_id}/``. Response ``content`` is a short markdown summary; ``meta.codegen_run_id``
    is the folder name to use with ``GET /v1/artifact/output-zip?pack=codegen_agents&agent_id=...``.
    """
    started = time.perf_counter()

    def _run() -> Any:
        from codegen_agents.pipeline import run_codegen_from_spec

        return run_codegen_from_spec(
            user_prompt=req.user_prompt,
            spec_markdown=req.spec_markdown,
            constraints=req.constraints or "None specified.",
            stack=req.stack or "auto",
            load_orchestrated_latest=req.load_orchestrated_latest,
            llm_model=req.llm_model,
        )

    try:
        text, meta_ex = await _to_thread_with_optional_llm(req.llm_model, _run)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise _run_exception_as_http(e) from e

    rid = (meta_ex or {}).get("codegen_run_id")
    if not rid:
        raise HTTPException(status_code=500, detail="Codegen run did not return codegen_run_id.")
    from codegen_agents.registry import AGENT_OUTPUT_SUBDIR

    sub = AGENT_OUTPUT_SUBDIR.get("codegen_from_spec", "codegen/exports")
    saved = save_pack_agent_output(
        pack_folder="codegen_agents",
        agent_id=rid,
        content=text,
        pipeline="codegen:generate",
    ) or {}
    return _wrap_response(
        text,
        pipeline="codegen:generate",
        started=started,
        extra=merge_extra(
            merge_extra(
                {
                    "agent_id": rid,
                    "suggested_file_path": f"{sub}/ (full tree in Output/{rid}/)",
                    "codegen": True,
                },
                saved,
            ),
            meta_ex,
        ),
    )


@app.post("/v1/sdlc-then-report", dependencies=[Depends(_require_api_key)])
async def post_sdlc_then_report(req: SdlcThenReportRequest) -> dict[str, Any]:
    """
    Run the full SDLC documentation pipeline, then the Reporting agent. The response `content`
    is the **reporting** section (SDLC+report is long); use for bot follow-up or fetch SDLC from logs if needed.
    For full SDLC+report in one string, we return both in meta for convenience.
    """
    started = time.perf_counter()
    sdlc_inputs = {
        "project_brief": req.project_brief,
        "constraints": req.constraints,
        "module_scope": req.module_scope,
        "sprint_context": req.sprint_context,
    }

    def _run() -> tuple[Any, Any]:
        from sdlc_crew import run_sdlc_then_reporting

        return run_sdlc_then_reporting(
            sdlc_inputs,
            user_report_prompt=req.report_prompt,
            reporting_extra=req.report_context,
        )

    try:
        sdlc_r, rep_r = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    sdlc_text = getattr(sdlc_r, "raw", None) or ""
    report_text = getattr(rep_r, "raw", None) or ""
    saved = save_sdlc_then_report_pair(
        sdlc_text=sdlc_text,
        report_text=report_text,
        pipeline="sdlc_then_report",
    )
    return _wrap_response(
        report_text,
        pipeline="sdlc_then_report",
        started=started,
        extra=merge_extra(
            {
                "sdlc_content": sdlc_text,
                "report_content": report_text,
                "note": "For chat bots, you may show `content` (report) first; `meta.sdlc_content` is the full SDLC output.",
            },
            saved,
        ),
    )


@app.post(
    "/v1/chat/complete",
    dependencies=[Depends(_require_api_key)],
    summary="Same as /v1/report (chat UIs that expect /chat/complete)",
)
async def post_chat_complete(req: ReportRequest) -> dict[str, Any]:
    """Same body and response as `POST /v1/report` — for frameworks that use a /chat/complete path."""
    return await post_report(req)


@app.get("/v1/automation/agents")
def list_automation_agents() -> list[dict[str, str]]:
    """Catalog of automation agent ids, labels, and categories (GET before POST /v1/automation/{agent_id})."""
    from automation_agents.registry import AUTOMATION_AGENTS

    return [{"id": a[0], "label": a[1], "category": a[2]} for a in AUTOMATION_AGENTS]


@app.post(
    "/v1/automation/{agent_id}",
    dependencies=[Depends(_require_api_key)],
    summary="Run one ERP automation agent by id",
)
async def post_automation(
    agent_id: str,
    req: AutomationRequest,
) -> dict[str, Any]:
    """Invoke a **single** automation agent. ``content`` in the response is the agent output (markdown)."""
    from automation_agents import run_automation_agent
    from automation_agents.registry import AUTOMATION_AGENT_IDS

    if agent_id not in AUTOMATION_AGENT_IDS:
        raise HTTPException(
            status_code=404,
            detail="Unknown agent_id. Use GET /v1/automation/agents for the catalog.",
        )
    started = time.perf_counter()

    def _run() -> Any:
        return run_automation_agent(
            agent_id,
            {
                "user_prompt": req.user_prompt,
                "constraints": req.constraints,
                "business_context": req.business_context,
            },
        )

    try:
        result = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    text = getattr(result, "raw", None) or ""
    saved = save_pack_agent_output(
        pack_folder="automation_agents",
        agent_id=agent_id,
        content=text,
        pipeline=f"automation:{agent_id}",
    )
    return _wrap_response(
        text,
        pipeline=f"automation:{agent_id}",
        started=started,
        extra=merge_extra({"agent_id": agent_id}, saved),
    )


_SALES_MKT_CATALOG_EXAMPLE: list[dict[str, str]] = [
    {
        "id": "sm_campaign_planner",
        "label": "Integrated marketing campaign (objectives, channels, KPIs)",
        "category": "marketing_demand",
    },
    {
        "id": "sm_lead_research_icp",
        "label": "ICP, lead research & TAM scoping",
        "category": "sales_revenue",
    },
]

_SALES_MKT_OK_EXAMPLE: dict[str, Any] = {
    "ok": True,
    "content": "# Campaign plan\n\n## Objectives\n- ...\n",
    "pipeline": "sales_marketing:sm_campaign_planner",
    "duration_ms": 12000,
    "meta": {"agent_id": "sm_campaign_planner"},
}


@app.get(
    "/v1/sales-marketing/agents",
    response_model=list[dict[str, str]],
    summary="List Sales & Marketing (GTM) agent ids",
    responses={
        200: {
            "description": "Array of {id, label, category}; use `id` in POST /v1/sales-marketing/{agent_id}.",
            "content": {
                "application/json": {
                    "example": _SALES_MKT_CATALOG_EXAMPLE,
                },
            },
        },
    },
)
def list_sales_marketing_agents() -> list[dict[str, str]]:
    """Catalog of GTM / sales & marketing agent ids (GET before POST /v1/sales-marketing/{agent_id})."""
    from sales_marketing_agents.registry import SALES_MARKETING_AGENTS

    return [{"id": a[0], "label": a[1], "category": a[2]} for a in SALES_MARKETING_AGENTS]


@app.post(
    "/v1/sales-marketing/{agent_id}",
    dependencies=[Depends(_require_api_key)],
    summary="Run one Sales & Marketing (GTM) agent by id",
    responses={
        200: {
            "description": "Success; `content` is the agent markdown. Show `content` as the bot/assistant message.",
            "content": {"application/json": {"example": _SALES_MKT_OK_EXAMPLE}},
        },
    },
)
async def post_sales_marketing(
    req: SalesMarketingRequest,
    agent_id: str = Path(
        ...,
        description="GTM agent id from `GET /v1/sales-marketing/agents` (e.g. `sm_campaign_planner`, `sm_lead_research_icp`).",
        examples=["sm_campaign_planner", "sm_content_engine", "sm_brand_messaging"],
    ),
) -> dict[str, Any]:
    """Invoke a **single** GTM agent (ICP, campaigns, content, launch). ``content`` is the agent output (markdown)."""
    from sales_marketing_agents import run_sales_marketing_agent
    from sales_marketing_agents.registry import SALES_MARKETING_AGENT_IDS

    if agent_id not in SALES_MARKETING_AGENT_IDS:
        raise HTTPException(
            status_code=404,
            detail="Unknown agent_id. Use GET /v1/sales-marketing/agents for the catalog.",
        )
    started = time.perf_counter()

    def _run() -> Any:
        return run_sales_marketing_agent(
            agent_id,
            {
                "user_prompt": req.user_prompt,
                "constraints": req.constraints,
                "business_context": req.business_context,
            },
        )

    try:
        result = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    text = getattr(result, "raw", None) or ""
    saved = save_pack_agent_output(
        pack_folder="sales_marketing_agents",
        agent_id=agent_id,
        content=text,
        pipeline=f"sales_marketing:{agent_id}",
    )
    return _wrap_response(
        text,
        pipeline=f"sales_marketing:{agent_id}",
        started=started,
        extra=merge_extra({"agent_id": agent_id}, saved),
    )


@app.get("/v1/design/agents")
def list_design_agents() -> list[dict[str, str]]:
    """Catalog of Design Agent ids (``dg_*``)."""
    from design_agents.registry import DESIGN_AGENTS

    return [{"id": a[0], "label": a[1], "category": a[2]} for a in DESIGN_AGENTS]


@app.post(
    "/v1/design/{agent_id}",
    dependencies=[Depends(_require_api_key)],
    summary="Run one Design Agent by id",
)
async def post_design(
    req: DesignRequest,
    agent_id: str = Path(
        ...,
        description="Design agent id from `GET /v1/design/agents` (e.g. `dg_visual_ui`, `dg_wireframe_spec`).",
        examples=["dg_visual_ui", "dg_design_brief", "dg_dev_handoff"],
    ),
) -> dict[str, Any]:
    """``content`` is markdown. The API also writes ``design_agents/Output/{agent_id}/latest.md`` (+ history); see ``meta.output_*``."""
    from design_agents import run_design_agent
    from design_agents.registry import AGENT_OUTPUT_SUBDIR, DESIGN_AGENT_IDS

    if agent_id not in DESIGN_AGENT_IDS:
        raise HTTPException(
            status_code=404,
            detail="Unknown agent_id. Use GET /v1/design/agents for the catalog.",
        )
    started = time.perf_counter()

    def _run() -> Any:
        return run_design_agent(
            agent_id,
            {
                "user_prompt": req.user_prompt,
                "constraints": req.constraints,
                "business_context": req.business_context,
            },
        )

    try:
        result = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    text = getattr(result, "raw", None) or ""
    sub = AGENT_OUTPUT_SUBDIR.get(agent_id, "design")
    saved = save_pack_agent_output(
        pack_folder="design_agents",
        agent_id=agent_id,
        content=text,
        pipeline=f"design:{agent_id}",
    )
    from design_agents.wireframe_raster import save_wireframe_dashboard_images

    wire_meta = save_wireframe_dashboard_images(
        agent_id=agent_id,
        user_prompt=req.user_prompt,
        constraints=req.constraints,
        business_context=req.business_context,
        markdown_output=text,
    )
    return _wrap_response(
        text,
        pipeline=f"design:{agent_id}",
        started=started,
        extra=merge_extra(
            merge_extra(
                {"agent_id": agent_id, "suggested_file_path": f"{sub}/{agent_id}.md"},
                saved,
            ),
            wire_meta,
        ),
    )


@app.get("/v1/project-management/agents")
def list_project_management_agents() -> list[dict[str, str]]:
    """Catalog of Project Management Agent ids (``pm_*``)."""
    from project_management_agents.registry import PROJECT_MANAGEMENT_AGENTS

    return [{"id": a[0], "label": a[1], "category": a[2]} for a in PROJECT_MANAGEMENT_AGENTS]


@app.post(
    "/v1/project-management/{agent_id}",
    dependencies=[Depends(_require_api_key)],
    summary="Run one Project Management Agent by id",
)
async def post_project_management(
    req: ProjectManagementRequest,
    agent_id: str = Path(
        ...,
        description="PM agent id from `GET /v1/project-management/agents` (e.g. `pm_sprint_parallel_roadmap`, `pm_erd_data_model`).",
        examples=["pm_phase_planning", "pm_sprint_parallel_roadmap", "pm_backend_architecture"],
    ),
) -> dict[str, Any]:
    """``content`` is markdown (ERD, architecture, sprints, etc.). Use the **pm_run.py** CLI with ``--out-dir`` to write files; API returns the body and `meta.suggested_file_path` as a template path."""
    from project_management_agents import run_project_management_agent
    from project_management_agents.registry import AGENT_OUTPUT_SUBDIR, PROJECT_MANAGEMENT_AGENT_IDS

    if agent_id not in PROJECT_MANAGEMENT_AGENT_IDS:
        raise HTTPException(
            status_code=404,
            detail="Unknown agent_id. Use GET /v1/project-management/agents for the catalog.",
        )
    started = time.perf_counter()

    def _run() -> Any:
        return run_project_management_agent(
            agent_id,
            {
                "user_prompt": req.user_prompt,
                "constraints": req.constraints,
                "business_context": req.business_context,
            },
        )

    try:
        result = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    text = getattr(result, "raw", None) or ""
    sub = AGENT_OUTPUT_SUBDIR.get(agent_id, "artifacts")
    saved = save_pack_agent_output(
        pack_folder="project_management_agents",
        agent_id=agent_id,
        content=text,
        pipeline=f"project_management:{agent_id}",
    )
    return _wrap_response(
        text,
        pipeline=f"project_management:{agent_id}",
        started=started,
        extra=merge_extra({"agent_id": agent_id, "suggested_file_path": f"{sub}/{agent_id}.md"}, saved),
    )


@app.get("/v1/devops-platform/agents")
def list_devops_platform_agents() -> list[dict[str, str]]:
    from devops_platform_agents.registry import DEVOPS_PLATFORM_AGENTS

    return [{"id": a[0], "label": a[1], "category": a[2]} for a in DEVOPS_PLATFORM_AGENTS]


@app.post(
    "/v1/devops-platform/{agent_id}",
    dependencies=[Depends(_require_api_key)],
    summary="Run one DevOps & platform agent by id",
)
async def post_devops_platform(
    req: DevOpsPlatformRequest,
    agent_id: str = Path(
        ...,
        examples=["dvp_ops_runbook", "dvp_kubernetes_platform", "dvp_slo_sla_framing"],
    ),
) -> dict[str, Any]:
    from devops_platform_agents import run_devops_platform_agent
    from devops_platform_agents.registry import AGENT_OUTPUT_SUBDIR, DEVOPS_PLATFORM_AGENT_IDS

    if agent_id not in DEVOPS_PLATFORM_AGENT_IDS:
        raise HTTPException(status_code=404, detail="Unknown agent_id. Use GET /v1/devops-platform/agents.")
    started = time.perf_counter()

    def _run() -> Any:
        return run_devops_platform_agent(
            agent_id,
            {
                "user_prompt": req.user_prompt,
                "constraints": req.constraints,
                "business_context": req.business_context,
            },
        )

    try:
        result = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    text = getattr(result, "raw", None) or ""
    sub = AGENT_OUTPUT_SUBDIR.get(agent_id, "devops")
    saved = save_pack_agent_output(
        pack_folder="devops_platform_agents",
        agent_id=agent_id,
        content=text,
        pipeline=f"devops_platform:{agent_id}",
    )
    return _wrap_response(
        text,
        pipeline=f"devops_platform:{agent_id}",
        started=started,
        extra=merge_extra({"agent_id": agent_id, "suggested_file_path": f"{sub}/{agent_id}.md"}, saved),
    )


@app.get("/v1/qa-test-strategy/agents")
def list_qa_test_strategy_agents() -> list[dict[str, str]]:
    from qa_test_strategy_agents.registry import QA_TEST_STRATEGY_AGENTS

    return [{"id": a[0], "label": a[1], "category": a[2]} for a in QA_TEST_STRATEGY_AGENTS]


@app.post(
    "/v1/qa-test-strategy/{agent_id}",
    dependencies=[Depends(_require_api_key)],
    summary="Run one QA & test strategy agent by id",
)
async def post_qa_test_strategy(
    req: QaTestStrategyRequest,
    agent_id: str = Path(..., examples=["qts_test_plan", "qts_e2e_feature_scope", "qts_risk_based_testing"]),
) -> dict[str, Any]:
    from qa_test_strategy_agents import run_qa_test_strategy_agent
    from qa_test_strategy_agents.registry import AGENT_OUTPUT_SUBDIR, QA_TEST_STRATEGY_AGENT_IDS

    if agent_id not in QA_TEST_STRATEGY_AGENT_IDS:
        raise HTTPException(status_code=404, detail="Unknown agent_id. Use GET /v1/qa-test-strategy/agents.")
    started = time.perf_counter()

    def _run() -> Any:
        return run_qa_test_strategy_agent(
            agent_id,
            {
                "user_prompt": req.user_prompt,
                "constraints": req.constraints,
                "business_context": req.business_context,
            },
        )

    try:
        result = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    text = getattr(result, "raw", None) or ""
    sub = AGENT_OUTPUT_SUBDIR.get(agent_id, "qa")
    saved = save_pack_agent_output(
        pack_folder="qa_test_strategy_agents",
        agent_id=agent_id,
        content=text,
        pipeline=f"qa_test_strategy:{agent_id}",
    )
    return _wrap_response(
        text,
        pipeline=f"qa_test_strategy:{agent_id}",
        started=started,
        extra=merge_extra({"agent_id": agent_id, "suggested_file_path": f"{sub}/{agent_id}.md"}, saved),
    )


@app.get("/v1/data-analytics/agents")
def list_data_analytics_agents() -> list[dict[str, str]]:
    from data_analytics_agents.registry import DATA_ANALYTICS_AGENTS

    return [{"id": a[0], "label": a[1], "category": a[2]} for a in DATA_ANALYTICS_AGENTS]


@app.post(
    "/v1/data-analytics/{agent_id}",
    dependencies=[Depends(_require_api_key)],
    summary="Run one Data & analytics agent by id",
)
async def post_data_analytics(
    req: DataAnalyticsRequest,
    agent_id: str = Path(..., examples=["dta_metric_definitions", "dta_warehouse_dbt_conceptual", "dta_event_schema_narrative"]),
) -> dict[str, Any]:
    from data_analytics_agents import run_data_analytics_agent
    from data_analytics_agents.registry import AGENT_OUTPUT_SUBDIR, DATA_ANALYTICS_AGENT_IDS

    if agent_id not in DATA_ANALYTICS_AGENT_IDS:
        raise HTTPException(status_code=404, detail="Unknown agent_id. Use GET /v1/data-analytics/agents.")
    started = time.perf_counter()

    def _run() -> Any:
        return run_data_analytics_agent(
            agent_id,
            {
                "user_prompt": req.user_prompt,
                "constraints": req.constraints,
                "business_context": req.business_context,
            },
        )

    try:
        result = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    text = getattr(result, "raw", None) or ""
    sub = AGENT_OUTPUT_SUBDIR.get(agent_id, "data")
    saved = save_pack_agent_output(
        pack_folder="data_analytics_agents",
        agent_id=agent_id,
        content=text,
        pipeline=f"data_analytics:{agent_id}",
    )
    return _wrap_response(
        text,
        pipeline=f"data_analytics:{agent_id}",
        started=started,
        extra=merge_extra({"agent_id": agent_id, "suggested_file_path": f"{sub}/{agent_id}.md"}, saved),
    )


@app.get("/v1/hr-talent/agents")
def list_hr_talent_agents() -> list[dict[str, str]]:
    from hr_talent_agents.registry import HR_TALENT_AGENTS

    return [{"id": a[0], "label": a[1], "category": a[2]} for a in HR_TALENT_AGENTS]


@app.post(
    "/v1/hr-talent/{agent_id}",
    dependencies=[Depends(_require_api_key)],
    summary="Run one HR & talent agent by id (drafts; not legal advice)",
)
async def post_hr_talent(
    req: HrTalentRequest,
    agent_id: str = Path(..., examples=["hrt_role_description", "hrt_interview_plan", "hrt_compensation_bands"]),
) -> dict[str, Any]:
    from hr_talent_agents import run_hr_talent_agent
    from hr_talent_agents.registry import AGENT_OUTPUT_SUBDIR, HR_TALENT_AGENT_IDS

    if agent_id not in HR_TALENT_AGENT_IDS:
        raise HTTPException(status_code=404, detail="Unknown agent_id. Use GET /v1/hr-talent/agents.")
    started = time.perf_counter()

    def _run() -> Any:
        return run_hr_talent_agent(
            agent_id,
            {
                "user_prompt": req.user_prompt,
                "constraints": req.constraints,
                "business_context": req.business_context,
            },
        )

    try:
        result = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    text = getattr(result, "raw", None) or ""
    sub = AGENT_OUTPUT_SUBDIR.get(agent_id, "hr")
    saved = save_pack_agent_output(
        pack_folder="hr_talent_agents",
        agent_id=agent_id,
        content=text,
        pipeline=f"hr_talent:{agent_id}",
    )
    return _wrap_response(
        text,
        pipeline=f"hr_talent:{agent_id}",
        started=started,
        extra=merge_extra({"agent_id": agent_id, "suggested_file_path": f"{sub}/{agent_id}.md"}, saved),
    )


@app.get("/v1/mobile-architecture/agents")
def list_mobile_architecture_agents() -> list[dict[str, str]]:
    from mobile_architecture_agent.registry import MOBILE_ARCHITECTURE_AGENTS

    return [{"id": a[0], "label": a[1], "category": a[2]} for a in MOBILE_ARCHITECTURE_AGENTS]


@app.post(
    "/v1/mobile-architecture/{agent_id}",
    dependencies=[Depends(_require_api_key)],
    summary="Run mobile architecture agent (mob_stack_architecture)",
)
async def post_mobile_architecture(req: AutomationRequest, agent_id: str = Path(..., examples=["mob_stack_architecture"])) -> dict[str, Any]:
    from mobile_architecture_agent import run_mobile_architecture_agent
    from mobile_architecture_agent.registry import AGENT_OUTPUT_SUBDIR, MOBILE_ARCHITECTURE_AGENT_IDS

    if agent_id not in MOBILE_ARCHITECTURE_AGENT_IDS:
        raise HTTPException(status_code=404, detail="Unknown agent_id. Use GET /v1/mobile-architecture/agents.")
    started = time.perf_counter()

    def _run() -> Any:
        return run_mobile_architecture_agent(
            agent_id,
            {
                "user_prompt": req.user_prompt,
                "constraints": req.constraints,
                "business_context": req.business_context,
            },
        )

    try:
        result = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    text = getattr(result, "raw", None) or ""
    sub = AGENT_OUTPUT_SUBDIR.get(agent_id, "platform/mobile")
    saved = save_pack_agent_output(
        pack_folder="mobile_architecture_agent",
        agent_id=agent_id,
        content=text,
        pipeline=f"mobile_architecture:{agent_id}",
    )
    return _wrap_response(
        text,
        pipeline=f"mobile_architecture:{agent_id}",
        started=started,
        extra=merge_extra({"agent_id": agent_id, "suggested_file_path": f"{sub}/{agent_id}.md"}, saved),
    )


@app.get("/v1/api-contract/agents")
def list_api_contract_agents() -> list[dict[str, str]]:
    from api_contract_agent.registry import API_CONTRACT_AGENTS

    return [{"id": a[0], "label": a[1], "category": a[2]} for a in API_CONTRACT_AGENTS]


@app.post(
    "/v1/api-contract/{agent_id}",
    dependencies=[Depends(_require_api_key)],
    summary="Run API & contract agent (api_openapi_contract)",
)
async def post_api_contract(req: AutomationRequest, agent_id: str = Path(..., examples=["api_openapi_contract"])) -> dict[str, Any]:
    from api_contract_agent import run_api_contract_agent
    from api_contract_agent.registry import AGENT_OUTPUT_SUBDIR, API_CONTRACT_AGENT_IDS

    if agent_id not in API_CONTRACT_AGENT_IDS:
        raise HTTPException(status_code=404, detail="Unknown agent_id. Use GET /v1/api-contract/agents.")
    started = time.perf_counter()

    def _run() -> Any:
        return run_api_contract_agent(
            agent_id,
            {
                "user_prompt": req.user_prompt,
                "constraints": req.constraints,
                "business_context": req.business_context,
            },
        )

    try:
        result = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    text = getattr(result, "raw", None) or ""
    sub = AGENT_OUTPUT_SUBDIR.get(agent_id, "contracts/api")
    saved = save_pack_agent_output(
        pack_folder="api_contract_agent",
        agent_id=agent_id,
        content=text,
        pipeline=f"api_contract:{agent_id}",
    )
    return _wrap_response(
        text,
        pipeline=f"api_contract:{agent_id}",
        started=started,
        extra=merge_extra({"agent_id": agent_id, "suggested_file_path": f"{sub}/{agent_id}.md"}, saved),
    )


@app.get("/v1/security-privacy/agents")
def list_security_privacy_agents() -> list[dict[str, str]]:
    from security_privacy_agent.registry import SECURITY_PRIVACY_AGENTS

    return [{"id": a[0], "label": a[1], "category": a[2]} for a in SECURITY_PRIVACY_AGENTS]


@app.post(
    "/v1/security-privacy/{agent_id}",
    dependencies=[Depends(_require_api_key)],
    summary="Run security & privacy agent (advisory; sec_privacy_threat_pii)",
)
async def post_security_privacy(req: AutomationRequest, agent_id: str = Path(..., examples=["sec_privacy_threat_pii"])) -> dict[str, Any]:
    from security_privacy_agent import run_security_privacy_agent
    from security_privacy_agent.registry import AGENT_OUTPUT_SUBDIR, SECURITY_PRIVACY_AGENT_IDS

    if agent_id not in SECURITY_PRIVACY_AGENT_IDS:
        raise HTTPException(status_code=404, detail="Unknown agent_id. Use GET /v1/security-privacy/agents.")
    started = time.perf_counter()

    def _run() -> Any:
        return run_security_privacy_agent(
            agent_id,
            {
                "user_prompt": req.user_prompt,
                "constraints": req.constraints,
                "business_context": req.business_context,
            },
        )

    try:
        result = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    text = getattr(result, "raw", None) or ""
    sub = AGENT_OUTPUT_SUBDIR.get(agent_id, "security/privacy")
    saved = save_pack_agent_output(
        pack_folder="security_privacy_agent",
        agent_id=agent_id,
        content=text,
        pipeline=f"security_privacy:{agent_id}",
    )
    return _wrap_response(
        text,
        pipeline=f"security_privacy:{agent_id}",
        started=started,
        extra=merge_extra({"agent_id": agent_id, "suggested_file_path": f"{sub}/{agent_id}.md"}, saved),
    )


@app.get("/v1/integration-bff/agents")
def list_integration_bff_agents() -> list[dict[str, str]]:
    from integration_bff_agent.registry import INTEGRATION_BFF_AGENTS

    return [{"id": a[0], "label": a[1], "category": a[2]} for a in INTEGRATION_BFF_AGENTS]


@app.post(
    "/v1/integration-bff/{agent_id}",
    dependencies=[Depends(_require_api_key)],
    summary="Run integration & BFF agent (int_bff_patterns)",
)
async def post_integration_bff(req: AutomationRequest, agent_id: str = Path(..., examples=["int_bff_patterns"])) -> dict[str, Any]:
    from integration_bff_agent import run_integration_bff_agent
    from integration_bff_agent.registry import AGENT_OUTPUT_SUBDIR, INTEGRATION_BFF_AGENT_IDS

    if agent_id not in INTEGRATION_BFF_AGENT_IDS:
        raise HTTPException(status_code=404, detail="Unknown agent_id. Use GET /v1/integration-bff/agents.")
    started = time.perf_counter()

    def _run() -> Any:
        return run_integration_bff_agent(
            agent_id,
            {
                "user_prompt": req.user_prompt,
                "constraints": req.constraints,
                "business_context": req.business_context,
            },
        )

    try:
        result = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    text = getattr(result, "raw", None) or ""
    sub = AGENT_OUTPUT_SUBDIR.get(agent_id, "platform/integration")
    saved = save_pack_agent_output(
        pack_folder="integration_bff_agent",
        agent_id=agent_id,
        content=text,
        pipeline=f"integration_bff:{agent_id}",
    )
    return _wrap_response(
        text,
        pipeline=f"integration_bff:{agent_id}",
        started=started,
        extra=merge_extra({"agent_id": agent_id, "suggested_file_path": f"{sub}/{agent_id}.md"}, saved),
    )


@app.get("/v1/observability/agents")
def list_observability_agents() -> list[dict[str, str]]:
    from observability_agent.registry import OBSERVABILITY_AGENTS

    return [{"id": a[0], "label": a[1], "category": a[2]} for a in OBSERVABILITY_AGENTS]


@app.post(
    "/v1/observability/{agent_id}",
    dependencies=[Depends(_require_api_key)],
    summary="Run observability agent (obs_product_platform)",
)
async def post_observability(req: AutomationRequest, agent_id: str = Path(..., examples=["obs_product_platform"])) -> dict[str, Any]:
    from observability_agent import run_observability_agent
    from observability_agent.registry import AGENT_OUTPUT_SUBDIR, OBSERVABILITY_AGENT_IDS

    if agent_id not in OBSERVABILITY_AGENT_IDS:
        raise HTTPException(status_code=404, detail="Unknown agent_id. Use GET /v1/observability/agents.")
    started = time.perf_counter()

    def _run() -> Any:
        return run_observability_agent(
            agent_id,
            {
                "user_prompt": req.user_prompt,
                "constraints": req.constraints,
                "business_context": req.business_context,
            },
        )

    try:
        result = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    text = getattr(result, "raw", None) or ""
    sub = AGENT_OUTPUT_SUBDIR.get(agent_id, "platform/observability")
    saved = save_pack_agent_output(
        pack_folder="observability_agent",
        agent_id=agent_id,
        content=text,
        pipeline=f"observability:{agent_id}",
    )
    return _wrap_response(
        text,
        pipeline=f"observability:{agent_id}",
        started=started,
        extra=merge_extra({"agent_id": agent_id, "suggested_file_path": f"{sub}/{agent_id}.md"}, saved),
    )


@app.get("/v1/release-distribution/agents")
def list_release_distribution_agents() -> list[dict[str, str]]:
    from release_distribution_agent.registry import RELEASE_DISTRIBUTION_AGENTS

    return [{"id": a[0], "label": a[1], "category": a[2]} for a in RELEASE_DISTRIBUTION_AGENTS]


@app.post(
    "/v1/release-distribution/{agent_id}",
    dependencies=[Depends(_require_api_key)],
    summary="Run release & distribution agent (rel_app_distribution)",
)
async def post_release_distribution(req: AutomationRequest, agent_id: str = Path(..., examples=["rel_app_distribution"])) -> dict[str, Any]:
    from release_distribution_agent import run_release_distribution_agent
    from release_distribution_agent.registry import AGENT_OUTPUT_SUBDIR, RELEASE_DISTRIBUTION_AGENT_IDS

    if agent_id not in RELEASE_DISTRIBUTION_AGENT_IDS:
        raise HTTPException(status_code=404, detail="Unknown agent_id. Use GET /v1/release-distribution/agents.")
    started = time.perf_counter()

    def _run() -> Any:
        return run_release_distribution_agent(
            agent_id,
            {
                "user_prompt": req.user_prompt,
                "constraints": req.constraints,
                "business_context": req.business_context,
            },
        )

    try:
        result = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    text = getattr(result, "raw", None) or ""
    sub = AGENT_OUTPUT_SUBDIR.get(agent_id, "platform/release")
    saved = save_pack_agent_output(
        pack_folder="release_distribution_agent",
        agent_id=agent_id,
        content=text,
        pipeline=f"release_distribution:{agent_id}",
    )
    return _wrap_response(
        text,
        pipeline=f"release_distribution:{agent_id}",
        started=started,
        extra=merge_extra({"agent_id": agent_id, "suggested_file_path": f"{sub}/{agent_id}.md"}, saved),
    )


@app.get("/v1/localization/agents")
def list_localization_agents() -> list[dict[str, str]]:
    from localization_agent.registry import LOCALIZATION_AGENTS

    return [{"id": a[0], "label": a[1], "category": a[2]} for a in LOCALIZATION_AGENTS]


@app.post(
    "/v1/localization/{agent_id}",
    dependencies=[Depends(_require_api_key)],
    summary="Run localization (i18n/l10n) agent (i18n_l10n_spec)",
)
async def post_localization(req: AutomationRequest, agent_id: str = Path(..., examples=["i18n_l10n_spec"])) -> dict[str, Any]:
    from localization_agent import run_localization_agent
    from localization_agent.registry import AGENT_OUTPUT_SUBDIR, LOCALIZATION_AGENT_IDS

    if agent_id not in LOCALIZATION_AGENT_IDS:
        raise HTTPException(status_code=404, detail="Unknown agent_id. Use GET /v1/localization/agents.")
    started = time.perf_counter()

    def _run() -> Any:
        return run_localization_agent(
            agent_id,
            {
                "user_prompt": req.user_prompt,
                "constraints": req.constraints,
                "business_context": req.business_context,
            },
        )

    try:
        result = await _to_thread_with_optional_llm(req.llm_model, _run)
    except Exception as e:
        raise _run_exception_as_http(e) from e

    text = getattr(result, "raw", None) or ""
    sub = AGENT_OUTPUT_SUBDIR.get(agent_id, "product/localization")
    saved = save_pack_agent_output(
        pack_folder="localization_agent",
        agent_id=agent_id,
        content=text,
        pipeline=f"localization:{agent_id}",
    )
    return _wrap_response(
        text,
        pipeline=f"localization:{agent_id}",
        started=started,
        extra=merge_extra({"agent_id": agent_id, "suggested_file_path": f"{sub}/{agent_id}.md"}, saved),
    )


app.mount(
    "/app",
    StaticFiles(directory=str(APP_DIR / "web"), html=True),
    name="web_ui",
)
