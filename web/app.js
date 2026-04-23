/**
 * Orchestrator browser UI: same-origin API (uvicorn) or set API base to call another host.
 * LLM and OPENAI_API_KEY are read on the server from .env; this page only sends optional llm_model per request.
 */

const STORAGE_KEY = "orchestrator_bearer";
/** Default when the field is left empty — server root, never `/app`. */
const DEFAULT_API_BASE = "http://127.0.0.1:8080";
const DEFAULT_MODELS = ["", "gpt-4o-mini", "gpt-4o", "gpt-4-turbo"];

/** @type {{ content: string, meta: object, pipeline: string } | null} */
let lastRun = null;

const PACKS = [
  {
    key: "orchestrated",
    label: "Auto — AI picks agents (full catalog)",
    kind: "orchestrated",
    post: "/v1/orchestrated/run",
  },
  {
    key: "codegen",
    label: "Codegen — app source from spec (ZIP)",
    kind: "codegen",
    post: "/v1/codegen/generate",
  },
  { key: "report", label: "Reporting (business / SQL report)", kind: "report", post: "/v1/report" },
  {
    key: "automation",
    label: "Automation (ERP workflow)",
    kind: "agent",
    list: "/v1/automation/agents",
    post: (id) => `/v1/automation/${encodeURIComponent(id)}`,
  },
  {
    key: "sales_marketing",
    label: "Sales & Marketing (GTM)",
    kind: "agent",
    list: "/v1/sales-marketing/agents",
    post: (id) => `/v1/sales-marketing/${encodeURIComponent(id)}`,
  },
  {
    key: "design",
    label: "Design",
    kind: "agent",
    list: "/v1/design/agents",
    post: (id) => `/v1/design/${encodeURIComponent(id)}`,
  },
  {
    key: "project_management",
    label: "Project management",
    kind: "agent",
    list: "/v1/project-management/agents",
    post: (id) => `/v1/project-management/${encodeURIComponent(id)}`,
  },
  {
    key: "devops",
    label: "DevOps & platform",
    kind: "agent",
    list: "/v1/devops-platform/agents",
    post: (id) => `/v1/devops-platform/${encodeURIComponent(id)}`,
  },
  {
    key: "qa",
    label: "QA & test strategy",
    kind: "agent",
    list: "/v1/qa-test-strategy/agents",
    post: (id) => `/v1/qa-test-strategy/${encodeURIComponent(id)}`,
  },
  {
    key: "data",
    label: "Data & analytics",
    kind: "agent",
    list: "/v1/data-analytics/agents",
    post: (id) => `/v1/data-analytics/${encodeURIComponent(id)}`,
  },
  {
    key: "hr",
    label: "HR & talent (drafts)",
    kind: "agent",
    list: "/v1/hr-talent/agents",
    post: (id) => `/v1/hr-talent/${encodeURIComponent(id)}`,
  },
  {
    key: "mobile_arch",
    label: "Mobile architecture",
    kind: "agent",
    list: "/v1/mobile-architecture/agents",
    post: (id) => `/v1/mobile-architecture/${encodeURIComponent(id)}`,
  },
  {
    key: "api_contract",
    label: "API & contract",
    kind: "agent",
    list: "/v1/api-contract/agents",
    post: (id) => `/v1/api-contract/${encodeURIComponent(id)}`,
  },
  {
    key: "sec_privacy",
    label: "Security & privacy (advisory)",
    kind: "agent",
    list: "/v1/security-privacy/agents",
    post: (id) => `/v1/security-privacy/${encodeURIComponent(id)}`,
  },
  {
    key: "int_bff",
    label: "Integration & BFF",
    kind: "agent",
    list: "/v1/integration-bff/agents",
    post: (id) => `/v1/integration-bff/${encodeURIComponent(id)}`,
  },
  {
    key: "observability",
    label: "Observability",
    kind: "agent",
    list: "/v1/observability/agents",
    post: (id) => `/v1/observability/${encodeURIComponent(id)}`,
  },
  {
    key: "release_dist",
    label: "Release & distribution",
    kind: "agent",
    list: "/v1/release-distribution/agents",
    post: (id) => `/v1/release-distribution/${encodeURIComponent(id)}`,
  },
  {
    key: "localization",
    label: "Localization (i18n/l10n)",
    kind: "agent",
    list: "/v1/localization/agents",
    post: (id) => `/v1/localization/${encodeURIComponent(id)}`,
  },
];

function el(id) {
  return document.getElementById(id);
}

/**
 * API root: **server origin only** (e.g. `http://127.0.0.1:8080`), not the `/app` page URL.
 * If you paste `http://host:port/app`, we strip `/app` so `/v1/...` works (otherwise requests hit `/app/v1/...` → 404).
 */
function baseUrl() {
  let raw = (el("apiBase").value || "").trim().replace(/\/+$/, "");
  if (raw) {
    raw = raw.replace(/\/app$/i, "").replace(/\/+$/, "");
    return raw;
  }
  if (typeof location !== "undefined" && location.protocol && location.protocol !== "file:") {
    return location.origin;
  }
  return "";
}

/** GET requests: no Content-Type (avoids unnecessary CORS preflight on some browsers). */
function authHeadersGet() {
  const h = {};
  const t = (el("apiKey").value || sessionStorage.getItem(STORAGE_KEY) || "").trim();
  if (t) h.Authorization = `Bearer ${t}`;
  return h;
}

function authHeaders() {
  const h = { "Content-Type": "application/json", ...authHeadersGet() };
  return h;
}

function selectedPack() {
  const v = el("pack").value;
  return PACKS.find((p) => p.key === v) || PACKS[0];
}

function updateFormForPack() {
  const pack = selectedPack();
  const isReport = pack.kind === "report";
  const isOrch = pack.kind === "orchestrated";
  const isCodegen = pack.kind === "codegen";
  const cw = el("codegenWrap");
  if (cw) cw.hidden = !isCodegen;
  el("promptLabel").textContent = isReport
    ? "Report prompt"
    : isOrch
      ? "Goal (describe what to build or deliver — AI will plan agents)"
      : isCodegen
        ? "Codegen instructions (what to implement)"
        : "User prompt / task";
  const cons = el("constraints");
  const consLabel = cons?.previousElementSibling;
  if (consLabel && consLabel.tagName === "LABEL") consLabel.style.display = isReport ? "none" : "block";
  if (cons) cons.style.display = isReport ? "none" : "block";
  const bc = el("businessContext");
  const bcLabel = bc?.previousElementSibling;
  if (bcLabel && bcLabel.tagName === "LABEL") {
    bcLabel.textContent = isCodegen ? "Specification (markdown)" : "Business context";
  }
  bc.placeholder = isReport
    ? "Optional context, units, or rules for the reporting step…"
    : isOrch
      ? "Stack, teams, regions, compliance, or anything the planner should know…"
      : isCodegen
        ? "Paste the full Auto-orchestrated (or any) spec markdown here, unless using the server file checkbox only."
        : "Paste ERP data, project context, or free text…";
}

function llmModel() {
  const s = el("llmModel").value.trim();
  const c = (el("llmCustom").value || "").trim();
  if (c) return c;
  return s || null;
}

function safeFileBase() {
  if (!lastRun) return "orchestrator_output";
  const id = lastRun.meta && lastRun.meta.agent_id;
  if (id) return String(id).replace(/[^\w.]+/g, "_").slice(0, 100);
  return String(lastRun.pipeline || "run").replace(/[^\w.]+/g, "_").slice(0, 100);
}

function updateDownloadUi() {
  const pan = el("downloadPanel");
  if (!pan) return;
  const has = !!(lastRun && lastRun.content != null && String(lastRun.content).length > 0);
  pan.hidden = !has;
  const m = (lastRun && lastRun.meta) || {};
  const canZip = !!(m.output_pack && m.output_agent_id != null && String(m.output_agent_id) !== "");
  ["dlMd", "dlTxt", "dlPng", "dlJpeg"].forEach((id) => {
    const b = el(id);
    if (b) b.disabled = !has;
  });
  const z = el("dlZip");
  if (z) z.disabled = !canZip;
}

function downloadBlob(blob, filename) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

/** Fetch a server-generated artifact (e.g. Matplotlib wireframe PNG). */
async function downloadArtifactFile(pack, agentId, filename, saveAs) {
  const root = baseUrl();
  if (!root) {
    alert("Set API base.");
    return;
  }
  const u = `${root}/v1/artifact/file?pack=${encodeURIComponent(pack)}&agent_id=${encodeURIComponent(agentId)}&file=${encodeURIComponent(filename)}`;
  const res = await fetch(u, { headers: authHeadersGet(), cache: "no-store" });
  if (!res.ok) {
    const t = await res.text();
    let detail = t;
    try {
      const j = JSON.parse(t);
      detail = (j && j.detail) || t;
    } catch {
      /* raw */
    }
    throw new Error(detail);
  }
  const blob = await res.blob();
  downloadBlob(blob, saveAs || filename);
}

function downloadMd() {
  if (!lastRun || lastRun.content == null) return;
  const blob = new Blob([String(lastRun.content)], { type: "text/markdown;charset=utf-8" });
  downloadBlob(blob, `${safeFileBase()}.md`);
}

function downloadTxt() {
  if (!lastRun || lastRun.content == null) return;
  const blob = new Blob([String(lastRun.content)], { type: "text/plain;charset=utf-8" });
  downloadBlob(blob, `${safeFileBase()}.txt`);
}

async function downloadPng() {
  if (!lastRun) return;
  const m = lastRun.meta || {};
  if (m.output_wireframe_png && m.output_pack && m.output_agent_id) {
    try {
      await downloadArtifactFile(
        m.output_pack,
        m.output_agent_id,
        "latest_wireframe.png",
        `${safeFileBase()}_wireframe.png`
      );
    } catch (e) {
      alert((e && e.message) || String(e));
    }
    return;
  }
  const node = el("out");
  if (typeof html2canvas !== "function") {
    alert("Screenshot library (html2canvas) did not load. Check your network and refresh the page.");
    return;
  }
  try {
    const canvas = await html2canvas(node, { backgroundColor: "#f6f6f3", scale: 2, logging: false, useCORS: true });
    await new Promise((resolve, reject) => {
      canvas.toBlob(
        (blob) => {
          if (blob) {
            downloadBlob(blob, `${safeFileBase()}.png`);
            resolve();
          } else reject(new Error("empty blob"));
        },
        "image/png"
      );
    });
  } catch (e) {
    alert(`PNG export failed: ${(e && e.message) || e}. Very long output may exceed browser limits—try .md or .txt.`);
  }
}

async function downloadJpeg() {
  if (!lastRun) return;
  const m = lastRun.meta || {};
  if (m.output_wireframe_jpeg && m.output_pack && m.output_agent_id) {
    try {
      await downloadArtifactFile(
        m.output_pack,
        m.output_agent_id,
        "latest_wireframe.jpg",
        `${safeFileBase()}_wireframe.jpg`
      );
    } catch (e) {
      alert((e && e.message) || String(e));
    }
    return;
  }
  const node = el("out");
  if (typeof html2canvas !== "function") {
    alert("Screenshot library (html2canvas) did not load. Check your network and refresh the page.");
    return;
  }
  try {
    const canvas = await html2canvas(node, { backgroundColor: "#f6f6f3", scale: 2, logging: false, useCORS: true });
    await new Promise((resolve, reject) => {
      canvas.toBlob(
        (blob) => {
          if (blob) {
            downloadBlob(blob, `${safeFileBase()}.jpg`);
            resolve();
          } else reject(new Error("empty blob"));
        },
        "image/jpeg",
        0.92
      );
    });
  } catch (e) {
    alert(`JPEG export failed: ${(e && e.message) || e}. Very long output may exceed browser limits—try .md or .txt.`);
  }
}

async function downloadZip() {
  const m = lastRun && lastRun.meta;
  if (!m || !m.output_pack || m.output_agent_id == null || String(m.output_agent_id) === "") {
    alert("No server output path. Set ORCHESTRATOR_SAVE_OUTPUT=1 in .env, restart the API, and run the agent again.");
    return;
  }
  const root = baseUrl();
  if (!root) {
    alert("Set API base.");
    return;
  }
  const u = `${root}/v1/artifact/output-zip?pack=${encodeURIComponent(m.output_pack)}&agent_id=${encodeURIComponent(m.output_agent_id)}`;
  try {
    const res = await fetch(u, { headers: authHeadersGet(), cache: "no-store" });
    if (!res.ok) {
      const t = await res.text();
      let detail = t;
      try {
        const j = JSON.parse(t);
        detail = (j && j.detail) || t;
      } catch {
        /* raw */
      }
      throw new Error(detail);
    }
    const blob = await res.blob();
    downloadBlob(blob, `${m.output_pack}_${m.output_agent_id}_output.zip`);
  } catch (e) {
    alert((e && e.message) || String(e));
  }
}

async function loadCatalog() {
  const pack = selectedPack();
  const agentSelect = el("agent");
  const agentWrap = el("agentWrap");
  if (pack.kind === "report" || pack.kind === "orchestrated" || pack.kind === "codegen") {
    agentWrap.hidden = true;
    agentSelect.innerHTML = "";
    if (pack.kind === "orchestrated") {
      const o = document.createElement("option");
      o.value = "";
      o.textContent = "Planner selects agents from the full catalog (no manual pick)";
      agentSelect.appendChild(o);
    } else if (pack.kind === "codegen") {
      const o = document.createElement("option");
      o.value = "";
      o.textContent = "No agent pick — spec + stack are used for codegen";
      agentSelect.appendChild(o);
    }
    updateFormForPack();
    return;
  }
  updateFormForPack();
  agentWrap.hidden = false;
  const root = baseUrl();
  if (!root) {
    agentSelect.innerHTML = "";
    const o = document.createElement("option");
    o.value = "";
    o.textContent =
      "Set API base (e.g. http://127.0.0.1:8080) — file:// pages cannot call the API without it";
    agentSelect.appendChild(o);
    return;
  }
  const url = `${root}${pack.list}`;
  try {
    const res = await fetch(url, { headers: authHeadersGet(), cache: "no-store" });
    if (!res.ok) {
      const t = await res.text();
      throw new Error(`${res.status} ${res.statusText}${t ? `: ${t.slice(0, 200)}` : ""}`);
    }
    const data = await res.json();
    agentSelect.innerHTML = "";
    for (const row of data) {
      const o = document.createElement("option");
      o.value = row.id;
      o.textContent = `${row.id} — ${row.label || ""}`.trim();
      o.title = row.category || "";
      agentSelect.appendChild(o);
    }
  } catch (e) {
    const msg = e && e.message ? String(e.message) : String(e);
    agentSelect.innerHTML = "";
    const o = document.createElement("option");
    o.value = "";
    o.textContent = `Catalog failed: ${msg.slice(0, 120)}`;
    o.title = msg;
    agentSelect.appendChild(o);
  }
}

async function runAgent() {
  const pack = selectedPack();
  const out = el("out");
  const meta = el("meta");
  out.textContent = "";
  out.classList.remove("err");
  meta.textContent = "";
  const prompt = (el("userPrompt").value || "").trim();
  if (!prompt) {
    out.classList.add("err");
    out.innerHTML = '<span class="err">Enter a prompt / request.</span>';
    return;
  }
  const constraints = (el("constraints").value || "None specified.").trim() || "None specified.";
  const business =
    pack.kind === "codegen"
      ? (el("businessContext").value || "").trim()
      : (el("businessContext").value || "None specified.").trim() || "None specified.";
  const llm = llmModel();

  const keyVal = (el("apiKey").value || "").trim();
  if (keyVal) sessionStorage.setItem(STORAGE_KEY, keyVal);

  const root = baseUrl();
  if (!root) {
    out.classList.add("err");
    out.innerHTML = '<span class="err">Set API base to your server URL (e.g. http://127.0.0.1:8080). Open /app/ from the API host or paste the base here.</span>';
    return;
  }

  let path;
  let body;
  if (pack.kind === "orchestrated") {
    path = root + pack.post;
    body = JSON.stringify({
      user_prompt: prompt,
      constraints,
      business_context: business,
      llm_model: llm,
    });
  } else if (pack.kind === "report") {
    path = root + pack.post;
    body = JSON.stringify({
      prompt,
      context: business,
      llm_model: llm,
    });
  } else if (pack.kind === "codegen") {
    const loadO = !!(el("loadOrchestrated") && el("loadOrchestrated").checked);
    if (!loadO && business.length < 20) {
      out.classList.add("err");
      out.innerHTML =
        '<span class="err">Enter at least 20 characters of specification (markdown), or check “Load latest Auto spec from server” (requires saved server file).</span>';
      return;
    }
    const stack = (el("codegenStack") && el("codegenStack").value) || "auto";
    path = root + pack.post;
    body = JSON.stringify({
      user_prompt: prompt,
      spec_markdown: business,
      constraints,
      stack,
      load_orchestrated_latest: loadO,
      llm_model: llm,
    });
  } else {
    const agentId = (el("agent").value || "").trim();
    if (!agentId) {
      out.classList.add("err");
      out.innerHTML = '<span class="err">Select an agent (load the catalog for this pack).</span>';
      return;
    }
    path = root + pack.post(agentId);
    body = JSON.stringify({
      user_prompt: prompt,
      constraints,
      business_context: business,
      llm_model: llm,
    });
  }

  el("runBtn").disabled = true;
  out.textContent = "Running…";
  try {
    const res = await fetch(path, { method: "POST", headers: authHeaders(), body });
    const text = await res.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      out.textContent = text;
      meta.textContent = `HTTP ${res.status}`;
      if (!res.ok) {
        out.classList.add("err");
        if (res.status === 404) {
          out.textContent =
            `${text}\n\n` +
            "404 usually means the API base is wrong or the server is an old build.\n" +
            "• Set API base to the server root only, e.g. http://127.0.0.1:8080 (not …/app).\n" +
            "• Restart uvicorn after pulling code so POST /v1/orchestrated/run is registered.";
        }
      }
      return;
    }
    if (!res.ok) {
      out.classList.add("err");
      const detail = (data && (data.detail || data.error)) || text;
      let extra = "";
      if (res.status === 404) {
        extra =
          "<br/><br/><small>404: use API base <code>http://127.0.0.1:8080</code> (no <code>/app</code>). Restart the API server if <code>/v1/orchestrated/run</code> was recently added.</small>";
      }
      out.innerHTML = `<span class="err">${res.status} ${detail}</span>${extra}`;
      return;
    }
    out.classList.remove("err");
    out.textContent = data.content != null ? String(data.content) : text;
    const m = data.meta || {};
    lastRun = {
      content: data.content != null ? String(data.content) : String(text),
      meta: m,
      pipeline: data.pipeline != null ? String(data.pipeline) : "",
    };
    updateDownloadUi();
    const bits = [];
    if (m.output_wireframe_png) bits.push(`wireframe image (server): ${m.output_wireframe_png}`);
    if (m.wireframe_raster_error) bits.push(`wireframe image error: ${m.wireframe_raster_error}`);
    if (m.output_latest) bits.push(`saved (latest): ${m.output_latest}`);
    if (m.output_latest_report) bits.push(`saved report: ${m.output_latest_report}`);
    if (m.output_latest_sdlc) bits.push(`saved sdlc: ${m.output_latest_sdlc}`);
    if (m.output_dir && !m.output_latest) bits.push(`output dir: ${m.output_dir}`);
    bits.push(`duration_ms: ${data.duration_ms ?? "—"}`, `pipeline: ${data.pipeline ?? "—"}`);
    if (Object.keys(m).length) {
      bits.push(`meta: ${JSON.stringify(m)}`);
    }
    meta.textContent = bits.join(" · ");
  } catch (e) {
    out.classList.add("err");
    out.innerHTML = `<span class="err">${(e && e.message) || e}</span>`;
  } finally {
    el("runBtn").disabled = false;
  }
}

/**
 * If the server was started with ORCHESTRATOR_UI_SANDBOX=1 and a matching ORCHESTRATOR_API_KEY
 * in .env, the API exposes this (loopback only) so the browser can fill the Bearer field.
 */
async function prefillApiKeyIfSandbox() {
  const existing = (el("apiKey").value || sessionStorage.getItem(STORAGE_KEY) || "").trim();
  if (existing) return;
  const root = baseUrl();
  if (!root) return;
  try {
    const res = await fetch(`${root}/v1/sandbox/ui-bearer`, { cache: "no-store" });
    if (!res.ok) return;
    const data = await res.json();
    if (data && typeof data.bearer === "string" && data.bearer) {
      el("apiKey").value = data.bearer;
      sessionStorage.setItem(STORAGE_KEY, data.bearer);
    }
  } catch {
    // sandbox off, non-loopback, or not same origin
  }
}

function init() {
  const baseEl = el("apiBase");
  if (baseEl && !(baseEl.value || "").trim()) {
    baseEl.value = DEFAULT_API_BASE;
  }
  const llmSelect = el("llmModel");
  DEFAULT_MODELS.forEach((m) => {
    const o = document.createElement("option");
    o.value = m;
    o.textContent = m === "" ? "Server default (.env)" : m;
    llmSelect.appendChild(o);
  });
  const packSelect = el("pack");
  PACKS.forEach((p) => {
    const o = document.createElement("option");
    o.value = p.key;
    o.textContent = p.label;
    packSelect.appendChild(o);
  });
  packSelect.addEventListener("change", () => {
    updateFormForPack();
    loadCatalog();
  });
  el("apiBase").addEventListener("change", () => {
    loadCatalog();
  });
  el("apiKey").addEventListener("change", () => {
    const t = (el("apiKey").value || "").trim();
    if (t) sessionStorage.setItem(STORAGE_KEY, t);
  });
  const saved = sessionStorage.getItem(STORAGE_KEY);
  if (saved) el("apiKey").value = saved;
  el("runBtn").addEventListener("click", runAgent);
  const dl = ["dlMd", "dlTxt", "dlPng", "dlJpeg", "dlZip"];
  const handlers = [downloadMd, downloadTxt, downloadPng, downloadJpeg, downloadZip];
  dl.forEach((id, i) => {
    const b = el(id);
    if (b) b.addEventListener("click", handlers[i]);
  });
  updateFormForPack();
  updateDownloadUi();
  (async () => {
    await prefillApiKeyIfSandbox();
    loadCatalog();
  })();
}

document.addEventListener("DOMContentLoaded", init);
