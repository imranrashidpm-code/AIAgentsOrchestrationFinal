# AIAgentsOrchestrator

Professional **CrewAI** orchestration: **(1) SDLC** product documentation, **(2) Reporting** (optional read-only SQL), **(3) Automation Agents** (ERP / operations), **(4) Sales & Marketing (GTM)**, **(5) Design Agents**, **(6) Project Management Agents**, **(7) DevOps & platform**, **(8) QA & test strategy**, **(9) Data & analytics**, **(10) HR & talent**, and the **(11) HTTP API** for clients and chat apps.

## Requirements

- **Python 3.10–3.13** (CrewAI does not support 3.14 yet)
- **Standalone LLM access (not Cursor / not your IDE chat):** set `OPENAI_API_KEY` in `.env`. Every agent receives an explicit `llm` model id (default `gpt-4o-mini` unless you set `ORCHESTRATOR_AGENT_LLM`, `OPENAI_MODEL_NAME`, or `ORCHESTRATOR_DEFAULT_LLM`). Execution is **autonomous** in the sense that each run calls your provider’s API from **Python/uvicorn** — no Claude-in-Cursor session is used.
- Optional: tune **autonomy** with `ORCHESTRATOR_AGENT_REASONING=1` (planning pass, default on), `ORCHESTRATOR_AGENT_MAX_ITER` (default 25), and `allow_delegation=false` from the shared brain layer.

## Setup

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
# Edit .env and set OPENAI_API_KEY
```

## Agent run memory (all agent runners)

Each **agent id** (e.g. `procurement_requisition_po`, `dg_visual_ui`, `pm_phase_planning`) can **persist prior runs** on disk: after every successful kickoff, a short **append-only** log stores your prompt, constraints, user business context, and a **truncated output**. On the next run, that history is **prepended into the context the model sees** (usually `business_context`; for SDLC, `project_brief`; for Reporting, `reporting_context`) so responses stay consistent. This is **not** weight fine-tuning—it is **retrieval of your own past I/O** from `.agent_memory/<agent_id>.jsonl` (or `AGENT_MEMORY_DIR`).

- **Turn off:** set `AGENT_MEMORY=0` in `.env`.
- **Override location:** `AGENT_MEMORY_DIR` (default `.agent_memory/`). The path is in `.gitignore` by default.
- **Pipelines:** `sdlc_full_pipeline` and `reporting_agent` are the memory ids for the multi-step SDLC crew and the Reporting agent.

## Six capability layers (every agent / crew)

All runnable agents share the same **stack** (pack-specific where noted):

1. **Brain (reasoning model)** — **every** `Agent` config gets an explicit `llm` (default `gpt-4o-mini` if unset); override with `ORCHESTRATOR_AGENT_LLM`, `OPENAI_MODEL_NAME`, or `ORCHESTRATOR_DEFAULT_LLM`. This runs **your** API/CLI process, not Cursor/IDE chat.
2. **Memory (context & state)** — `agent_memory` (JSONL per `agent_id`; see above).
3. **Tools (action & interaction)** — `orchestrator_stack_status` (when enabled) on every **single-agent** run; **SDLC** agents share `get_pack_tools("sdlc")`; **Reporting** also attaches read-only **SQL** tools when `REPORTING_DATABASE_URL` is set, plus the stack tool. Disable the meta-tool with `ORCHESTRATOR_CAPABILITY_TOOL=0` if the model over-calls it.
4. **Perception (input handling)** — normalizes and caps string inputs before kickoff (`ORCHESTRATOR_PERCEPTION=1` by default).
5. **Planning & goal-oriented behavior** — a fixed “plan then deliver” block is prepended to context when `ORCHESTRATOR_PLANNING=1` and `ORCHESTRATOR_CAPABILITIES=1` (default).
6. **Governance & guardrails (safety)** — policy text (no harmful / privacy / professional-advice scope) is prepended when `ORCHESTRATOR_GOVERNANCE=1` and `ORCHESTRATOR_CAPABILITIES=1` (default).

**Disable the extra layers (keep memory as configured):** `ORCHESTRATOR_CAPABILITIES=0` turns off governance + planning + perception notes in the **prefix** (memory and brain still apply unless you set those off separately). See `.env.example` for all toggles.

## Usage

```powershell
.\.venv\Scripts\python.exe main.py "Your product brief..." --constraints "Your standards..." --module-scope "Inventory" --sprint "Sprint 1" --out docs\output.md
```

Parallel jobs (output order matches the JSON file):

```powershell
.\.venv\Scripts\python.exe main.py "Vision brief..." --parallel examples\parallel_modules.example.json --out docs\parallel.md
```

## Automation Agents (ERP workflow)

The **`automation_agents/`** package defines **one CrewAI agent per id** (single-agent, single-task), so you can invoke **only** the automation you need (procurement, inventory, finance, etc.). Agent definitions live in `automation_agents/config/automation_agents_*.yaml`; tasks in `automation_tasks_*.yaml`. The canonical list is in `automation_agents/registry.py`.

**List all agent ids:**

```powershell
.\.venv\Scripts\python.exe automation_run.py --list-agents
```

**Run one agent (example):**

```powershell
.\.venv\Scripts\python.exe automation_run.py procurement_requisition_po --prompt "Draft a PO plan for next month for class A items" --constraints "Max 3 day lead time" --context "Paste SKU list or policy text here"
```

**From Python:** `from automation_agents import run_automation_agent`  
**From HTTP:** `GET /v1/automation/agents` and `POST /v1/automation/{agent_id}` (see API section). Response uses the same `content` field as other bot endpoints.

Outputs are **draft / decision-support** narratives unless you later wire ERP APIs or tools—humans stay in the loop for real postings.

## Sales & Marketing (GTM) agents

The **`sales_marketing_agents/`** package defines **one CrewAI agent per `sm_*` id** (single-agent, single-task): ICP and pipeline narrative, campaign planning, content, paid/organic, email lifecycle, brand/positioning, events, competitive intel, and product launch GTM. Configs live in `sales_marketing_agents/config/sales_marketing_agents_*.yaml` and `sales_marketing_tasks_*.yaml`. The catalog is in `sales_marketing_agents/registry.py`.

**Not the same as ERP “sales” in Automation:** `automation_agents` includes order-to-cash style agents (quotes, credit, rebates). Use **`sm_*`** for go-to-market and demand generation; use **`automation` `sales_*`** for operational ERP narratives.

**List all GTM agent ids:**

```powershell
.\.venv\Scripts\python.exe sales_marketing_run.py --list-agents
```

**Run one agent (example):**

```powershell
.\.venv\Scripts\python.exe sales_marketing_run.py sm_campaign_planner --prompt "Q2 launch campaign for mid-market" --constraints "B2B SaaS; $20–50K ACV" --context "3-person marketing team; US + UK"
```

**From Python:** `from sales_marketing_agents import run_sales_marketing_agent`  
**From HTTP:** `GET /v1/sales-marketing/agents` and `POST /v1/sales-marketing/{agent_id}`

## Design Agents

**Display name:** **Design Agents** (ids `dg_*`). The **`design_agents/`** package turns a prompt into structured **design deliverables** (brief, research plan, IA, wireframe spec, visual/UI direction, design system, accessibility, dev handoff). Configs: `design_agents/config/design_agents_*.yaml` and `design_tasks_*.yaml`. Catalog: `design_agents/registry.py`.

**List and run (optional—save to a folder tree with `--out-dir`):**

```powershell
.\.venv\Scripts\python.exe design_run.py --list-agents
.\.venv\Scripts\python.exe design_run.py dg_visual_ui --prompt "Redesign the settings page for mobile-first" --constraints "Use existing design tokens" --context "React + MUI" --out-dir project_documentation
```

**From Python:** `from design_agents import run_design_agent`  
**From HTTP:** `GET /v1/design/agents`, `POST /v1/design/{agent_id}`. The API returns markdown in `content`; use `meta.suggested_file_path` as a relative path, or the CLI to write files for you.

## Project Management Agents

**Display name:** **Project Management Agents** (ids `pm_*`). Use them for a **new project**, a **new feature in an existing product**, a **major fix**, or a **substantial upgrade**: requirements, **ERD (Mermaid)**, **backend and frontend architecture**, and a **multi-sprint plan with parallel tracks** (e.g. backend / frontend / data / DevOps), aligned to **Initiation, Planning, Execution, Monitoring/Controlling, and Closure** as separate invokable agents.

**Saving documentation to disk:** pass **`--out-dir <folder>`** (recommended). Each run writes one `.md` file under a stable subfolder, for example `phases/02_planning/`, `artifacts/data_model/`, `artifacts/sprints/`. Call agents in whatever order your process needs, reusing the same folder so documentation accumulates in one project directory.

**Examples:**

```powershell
.\.venv\Scripts\python.exe pm_run.py --list-agents
cd "D:\imran rashid\Orchestration"
.\.venv\Scripts\python.exe pm_run.py pm_phase_initiation --prompt "New customer portal with Okta SSO and case management" --out-dir my_project_docs
.\.venv\Scripts\python.exe pm_run.py pm_erd_data_model --prompt "Same portal as above; include accounts, cases, attachments" --out-dir my_project_docs
.\.venv\Scripts\python.exe pm_run.py pm_sprint_parallel_roadmap --prompt "2-week sprints; 2 BE / 2 FE / 1 QA; 4 months to GA" --out-dir my_project_docs
```

**From Python:** `from project_management_agents import run_project_management_agent`  
**From HTTP:** `GET /v1/project-management/agents`, `POST /v1/project-management/{agent_id}`. The server does not write to your disk; the CLI does when you pass `--out-dir`.

## DevOps & platform

**Display name:** **DevOps & platform** (ids `dvp_*`). Runbooks, incident postmortems, SLO/SLA framing, high-level **CI/CD** design, and **Kubernetes** platform sketches. Package: `devops_platform_agents/`, CLI: `devops_platform_run.py` (optional `--out-dir` for `devops/...` paths).

**Example:**

```powershell
.\.venv\Scripts\python.exe devops_platform_run.py dvp_incident_postmortem --prompt "Table-top: DB failover took 45m; partial checkout outage" --out-dir my_runbooks
```

**From Python:** `from devops_platform_agents import run_devops_platform_agent`  
**From HTTP:** `GET /v1/devops-platform/agents`, `POST /v1/devops-platform/{agent_id}`

## QA & test strategy

**Display name:** **QA & test strategy** (ids `qts_*`). Test plan, **risk-based** testing, **E2E** scope for a feature, and regression strategy. Package: `qa_test_strategy_agents/`, CLI: `qa_test_strategy_run.py`.

**From HTTP:** `GET /v1/qa-test-strategy/agents`, `POST /v1/qa-test-strategy/{agent_id}`

## Data & analytics

**Display name:** **Data & analytics** (ids `dta_*`). Metric definitions, dashboard spec, event-schema narrative, and **warehouse + dbt conceptual** model. Complements the **Reporting** agent (ad-hoc SQL) with *design-time* analytics docs. Package: `data_analytics_agents/`, CLI: `data_analytics_run.py`.

**From HTTP:** `GET /v1/data-analytics/agents`, `POST /v1/data-analytics/{agent_id}`

## HR & talent

**Display name:** **HR & talent** (ids `hrt_*`). Job descriptions, comp band *narrative*, interview plans, L&D program outlines, and performance process structure. Outputs are **drafts + checklists** — **not legal advice**; review with HR and counsel. Package: `hr_talent_agents/`, CLI: `hr_talent_run.py`.

**From HTTP:** `GET /v1/hr-talent/agents`, `POST /v1/hr-talent/{agent_id}`

## More business areas to cover with future agent packs

Useful next packs (each could mirror `automation_agents` / `sales_marketing_agents` patterns):

| Area | Example focus |
|------|----------------|
| **HR & talent** | Job architecture, comp bands, L&D, performance reviews, hiring pipelines |
| **Legal & compliance** | Policy drafting support, RFP/contract checklists, privacy/security program outlines |
| **Customer success & support** | Playbooks, health scoring narratives, deflection/FAQ, renewals/escalation |
| **Strategy & operations** | OKRs, business planning, process mapping, vendor/outsourcing RFPs |
| **R&D / product** | Discovery synthesis, technical specs, research backlog prioritization |
| **Finance (FP&A, treasury)** | Budget narrative, board packs, **distinct from** ERP GL automation agents |
| **ESG & sustainability** | Reporting frameworks, supplier questionnaires, target-setting storylines |
| **Partners & channels** | Partner programs, MDF, co-sell, distributor enablement |

## Reporting Agent (external database + prompts)

The **Reporting Agent** answers business questions in plain language. It can call **read-only** SQL on an external database when `REPORTING_DATABASE_URL` is set (see `.env.example`). Use it for prompts such as:

- *“Profit and loss summary for 01-Jul-2016 to 30-Jun-2017”*
- *“Executive summary and recommendations on over-purchasing and expired inventory”*

```powershell
.\.venv\Scripts\python.exe report.py "Give me P&L summary for period 01-Jul-2016 to 30-Jun-2017"
.\.venv\Scripts\python.exe report.py "Executive summary and recommendations re: over-purchase and expired stock" --context "Wholesale distribution; USD" --out docs\report.md
```

Security: use a **read-only** DB user in production; queries are restricted to a single `SELECT` (no DML/DDL). For PostgreSQL, install a driver (e.g. `psycopg2-binary`) if you use a `postgresql+...` URL.

### Full pipeline: SDLC then Reporting

Run the **10-step SDLC crew**, then automatically run the **Reporting Agent** with the SDLC output (truncated; see `REPORTING_SDLC_CONTEXT_MAX` in `.env.example`) as background context. **Cannot** be combined with `--parallel`.

```powershell
.\.venv\Scripts\python.exe main.py "Your product brief..." --constraints "..." `
  --module-scope "Full product" --sprint "Full pipeline" `
  --with-report --report-prompt "Executive summary and KPI-style recommendations using DB if available." `
  --out docs\full_run.md --report-out docs\report_only.md
```

Programmatic: `from sdlc_crew import run_sdlc_then_reporting`.

## HTTP API (any app, chat UI, or AI bot)

Start the service (after `pip install -r requirements.txt` and a configured `.env`):

```powershell
.\.venv\Scripts\python.exe -m uvicorn api_server:app --host 0.0.0.0 --port 8080
```

- **OpenAPI / try-it:** [http://localhost:8080/docs](http://localhost:8080/docs) (Sales & Marketing `POST` includes **example** request bodies and responses on the GTM routes.)
- **Health:** `GET /health`

**API smoke tests** (mocks the LLM; `ORCHESTRATOR_API_KEY` not required for these). Run from the **repository root** (the folder that contains `tests/`), not from your home directory:

```powershell
cd "D:\imran rashid\Orchestration"
py -3.13 -m pytest tests/ -q
```

If you prefer a one-liner from anywhere: `py -3.13 -m pytest "D:\imran rashid\Orchestration\tests" -q`

### Endpoints (JSON)

| Method | Path | Use |
|--------|------|-----|
| `GET` | `/v1/automation/agents` | **Catalog** of automation agent `id` / `label` / `category` |
| `POST` | `/v1/automation/{agent_id}` | Run **one** ERP **Automation Agent** (e.g. `procurement_requisition_po`) |
| `GET` | `/v1/sales-marketing/agents` | **Catalog** of GTM agent `id` / `label` / `category` |
| `POST` | `/v1/sales-marketing/{agent_id}` | Run **one** **Sales & Marketing (GTM)** agent (e.g. `sm_campaign_planner`) |
| `GET` | `/v1/design/agents` | **Catalog** of **Design Agents** (`dg_*`) |
| `POST` | `/v1/design/{agent_id}` | Run **one** design agent (e.g. `dg_visual_ui`); `meta.suggested_file_path` is a relative save path |
| `GET` | `/v1/project-management/agents` | **Catalog** of **Project Management Agents** (`pm_*`) |
| `POST` | `/v1/project-management/{agent_id}` | Run **one** PM agent (e.g. `pm_sprint_parallel_roadmap`); save `content` or use **pm_run.py** `--out-dir` |
| `GET` | `/v1/devops-platform/agents` | Catalog: **DevOps & platform** (`dvp_*`) |
| `POST` | `/v1/devops-platform/{agent_id}` | e.g. `dvp_cicd_pipeline_design`, `dvp_slo_sla_framing` |
| `GET` | `/v1/qa-test-strategy/agents` | Catalog: **QA & test strategy** (`qts_*`) |
| `POST` | `/v1/qa-test-strategy/{agent_id}` | e.g. `qts_risk_based_testing` |
| `GET` | `/v1/data-analytics/agents` | Catalog: **Data & analytics** (`dta_*`) |
| `POST` | `/v1/data-analytics/{agent_id}` | e.g. `dta_metric_definitions` |
| `GET` | `/v1/hr-talent/agents` | Catalog: **HR & talent** (`hrt_*`) |
| `POST` | `/v1/hr-talent/{agent_id}` | Drafts only; e.g. `hrt_interview_plan` |
| `POST` | `/v1/report` | Natural-language **reporting** (same engine as `report.py`) |
| `POST` | `/v1/chat/complete` | Same as `/v1/report` (handy for chat frontends) |
| `POST` | `/v1/sdlc-then-report` | Full **SDLC** then **Reporting** (see OpenAPI for body fields) |

**Response shape** (all POST JSON responses): use the **`content` string as the bot / assistant message** to show the user. Example:

```json
{ "ok": true, "content": "# Report\\n...", "pipeline": "report", "duration_ms": 12345 }
```

**Request body (automation, GTM, design, PM):** `user_prompt` (or `prompt` / `user_message` / `message`), optional `constraints`, optional `business_context`.

**Request body (reporting):** at least one of `prompt`, `user_message`, or `message` (all mean the same user question), plus optional `context`.

**Security (production):** set `ORCHESTRATOR_API_KEY` in `.env` and send `Authorization: Bearer <your_key>` on POST requests. Tighten `ORCHESTRATOR_CORS_ORIGINS` to your web app’s origin(s). Run behind HTTPS (reverse proxy).

**Example (curl):**

```powershell
curl -s -X POST http://localhost:8080/v1/report -H "Content-Type: application/json" -d "{\"prompt\":\"P&L summary for last month\",\"context\":\"USD; wholesale\"}"
```

## Publish to GitHub

Canonical remote: `https://github.com/developer-digitalsofts/AIAgentsOrchestrator.git`.

If the repository **does not exist yet** or push fails, use a [Personal Access Token](https://github.com/settings/tokens) (classic, **repo** scope):

```powershell
cd "D:\imran rashid\Orchestration"
$env:GITHUB_TOKEN = "ghp_your_token_here"
.\scripts\publish-github.ps1
```

Or create an **empty** repository (no README) on GitHub with that name, then:

```powershell
git push -u origin main
```

## License

Specify your license in this repository as needed.
