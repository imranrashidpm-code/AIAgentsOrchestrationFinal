"""
Server-side **raster wireframe** for ``dg_wireframe_spec``.

The figure is **derived from the LLM markdown output** (headings, bullets, keywords, numbers, period tokens)
so labels and structure align with the written spec. Chart values are illustrative; if the text embeds
enough numbers they are used, otherwise a deterministic series seeded from the markdown hash varies per run.
"""

from __future__ import annotations

import hashlib
import io
import re
from datetime import datetime, timezone
from textwrap import fill
from typing import Any

import numpy as np

from agent_run_output import REPO_ROOT, output_dir_for

WIREFRAME_RASTER_AGENT_IDS: frozenset[str] = frozenset({"dg_wireframe_spec"})

_KW_RE = re.compile(
    r"kpi|metric|dashboard|graph|chart|plot|revenue|sales|purchase|margin|"
    r"delta|period|compare|comparison|yoy|qoq|trend|inventory|fulfillment",
    re.I,
)


def _strip_inline_md(s: str) -> str:
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    return s.strip()


def _extract_period_labels(md: str) -> list[str]:
    q = re.findall(r"\b(Q[1-4])\b", md, re.I)
    if len(q) >= 3:
        return list(dict.fromkeys(q))[:5]
    moy = re.findall(
        r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\b",
        md,
        re.I,
    )
    if len(moy) >= 3:
        return [x[:3] for x in moy[:5]]
    t = re.findall(r"\bT\d+\b", md, re.I)
    if len(t) >= 3:
        return t[:5]
    wk = re.findall(r"\b(?:Week|Wk)\s*(\d+)\b", md, re.I)
    if len(wk) >= 3:
        return [f"W{x}" for x in wk[:5]]
    return []


def parse_wireframe_from_markdown(
    md: str,
    *,
    user_prompt: str = "",
    constraints: str = "",
    business_context: str = "",
) -> dict[str, Any]:
    """
    Map markdown spec + user fields into layout dict for Matplotlib.
    """
    md = (md or "").strip()
    if not md:
        md = f"## {user_prompt or 'Wireframe'}\n{constraints}\n{business_context}"

    h1 = re.findall(r"^#\s+(.+)$", md, re.MULTILINE)
    h2 = re.findall(r"^##\s+(.+)$", md, re.MULTILINE)
    h3 = re.findall(r"^###\s+(.+)$", md, re.MULTILINE)
    if h1:
        title = _strip_inline_md(h1[0])[:100]
    elif h2:
        title = _strip_inline_md(h2[0])[:100]
    else:
        title = (user_prompt or "Wireframe spec").strip()[:100]

    bullets: list[str] = []
    for m in re.finditer(r"^\s*[-*+]\s+(.+)$", md, re.MULTILINE):
        b = _strip_inline_md(m.group(1))
        if b and b not in bullets:
            bullets.append(b)

    kpi_work: list[str] = []
    for b in bullets:
        if _KW_RE.search(b) and len(b) < 70:
            kpi_work.append(b[:32])
    for b in bullets:
        if b not in kpi_work and len(b) < 55 and len(kpi_work) < 4:
            kpi_work.append(b[:32])
    while len(kpi_work) < 4:
        kpi_work.append(f"KPI {len(kpi_work) + 1}")
    kpi_labels = kpi_work[:4]

    panel_src: list[str] = [_strip_inline_md(x)[:55] for x in h2 + h3 if _strip_inline_md(x)]
    seen: set[str] = set()
    panel_titles: list[str] = []
    for p in panel_src:
        if p and p not in seen:
            seen.add(p)
            panel_titles.append(p)
        if len(panel_titles) >= 4:
            break
    i = 0
    while len(panel_titles) < 4:
        panel_titles.append(f"Chart / flow {i + 1}")
        i += 1
    panel_titles = panel_titles[:4]

    # First narrative paragraph as subtitle
    lines = md.splitlines()
    para: list[str] = []
    for line in lines:
        t = line.strip()
        if not t or t.startswith("#") or t.startswith("---"):
            if para:
                break
            continue
        if re.match(r"^[-*+]\s", t) or re.match(r"^\d+\.\s", t):
            if para:
                break
            continue
        para.append(t)
    summary = _strip_inline_md(" ".join(para))[:320] if para else ""
    if not summary:
        summary = _strip_inline_md(
            f"{(constraints or '')[:160]}  {(business_context or '')[:180]}".strip(" ·")
        )[:320]

    period_labels = _extract_period_labels(md)
    if not period_labels or len(period_labels) < 3:
        period_labels = [f"P{i + 1}" for i in range(5)]
    else:
        while len(period_labels) < 5:
            period_labels.append(f"P{len(period_labels) + 1}")
        period_labels = period_labels[:5]

    # Numbers in text (optional series)
    num_strs = re.findall(r"\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\b", md)
    nums: list[float] = []
    for ns in num_strs:
        try:
            nums.append(float(ns.replace(",", "")))
        except ValueError:
            pass
    n = len(period_labels)
    h = hashlib.sha256(md.encode("utf-8", errors="replace")).hexdigest()
    seed = int(h[:8], 16) % (2**32)
    rng = np.random.default_rng(seed)
    if len(nums) >= n * 2:
        cur = np.array(nums[:n], dtype=float)
        prev = np.array(nums[n : n * 2], dtype=float)
    elif len(nums) >= n:
        cur = np.array(nums[:n], dtype=float)
        prev = cur * rng.uniform(0.75, 0.95, size=n)
    else:
        cur = rng.uniform(25, 95, size=n)
        prev = cur * rng.uniform(0.7, 0.95, size=n)

    # Legend wording from spec
    lc, lp = "Current", "Previous"
    low = md.lower()
    if re.search(r"\byear over year\b|\byoy\b", low):
        lc, lp = "Current (YoY base)", "Prior period"
    if re.search(r"\bqoq\b|quarter over quarter", low):
        lc, lp = "Current Q", "Prior Q"
    if re.search(r"same period last year|splsy", low):
        lp = "Same period (prior year)"

    return {
        "title": title,
        "summary": summary,
        "kpi_labels": kpi_labels,
        "panel_titles": panel_titles,
        "period_labels": period_labels,
        "series_current": cur,
        "series_previous": prev,
        "legend_current": lc,
        "legend_prev": lp,
    }


def save_wireframe_dashboard_images(
    *,
    agent_id: str,
    user_prompt: str,
    constraints: str,
    business_context: str,
    markdown_output: str = "",
) -> dict[str, Any]:
    if agent_id not in WIREFRAME_RASTER_AGENT_IDS:
        return {}
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as e:
        return {
            "wireframe_raster_error": (
                f"Matplotlib is required for wireframe images: {e}. "
                f"Run: pip install matplotlib"
            ),
        }

    layout = parse_wireframe_from_markdown(
        markdown_output,
        user_prompt=user_prompt,
        constraints=constraints,
        business_context=business_context,
    )

    base = output_dir_for("design_agents", agent_id)
    try:
        base.mkdir(parents=True, exist_ok=True)
        hist = base / "history"
        hist.mkdir(exist_ok=True)
    except OSError as e:
        return {"wireframe_raster_error": str(e)}

    title = layout["title"]
    summary = layout["summary"]
    kpi_labels = layout["kpi_labels"]
    panel_titles = layout["panel_titles"]
    period_labels = layout["period_labels"]
    cur_base = np.asarray(layout["series_current"], dtype=float)
    prev_base = np.asarray(layout["series_previous"], dtype=float)
    lc, lp = layout["legend_current"], layout["legend_prev"]

    fig = plt.figure(figsize=(15, 10), facecolor="#eceff1")
    fig.patch.set_facecolor("#eceff1")
    st = fill(f"Wireframe (from spec) — {title}", width=90)
    fig.suptitle(st, fontsize=14, fontweight="semibold", color="#1a237e", y=0.98)
    if summary:
        sub = fill(summary, width=110)
        fig.text(0.5, 0.91, sub, ha="center", fontsize=8.5, color="#37474f", wrap=True)
    if (constraints or business_context) and not summary:
        cap = f"{(constraints or '')[:120]}  ·  {(business_context or '')[:160]}".strip(" ·")
        if cap:
            fig.text(0.5, 0.91, cap, ha="center", fontsize=8, color="#607d8b", style="italic", wrap=True)

    gs = fig.add_gridspec(3, 4, left=0.04, right=0.99, top=0.86, bottom=0.05, hspace=0.5, wspace=0.32)
    colors = ("#1565c0", "#2e7d32", "#ef6c00", "#6a1b9a")
    for i, name in enumerate(kpi_labels):
        ax = fig.add_subplot(gs[0, i])
        ax.set_facecolor("#ffffff")
        ax.set_title(name, fontsize=8.5, color="#263238", pad=3)
        h = 55 + (i * 7 + (hash(name) % 20))
        h = min(h, 120)
        ax.barh([0], [float(h)], color=colors[i % 4], height=0.45, alpha=0.88, edgecolor="white", linewidth=0.5)
        ax.set_xlim(0, 130)
        ax.set_yticks([])
        ax.tick_params(axis="x", labelsize=7)
        for spine in ax.spines.values():
            spine.set_edgecolor("#cfd8dc")

    x = np.arange(len(period_labels))
    w = 0.34
    # Scale series per panel from same base (slightly different mix so panels differ)
    factors = (1.0, 0.62, 0.88, 1.12)
    for idx, cslice, ft in zip(
        range(4),
        (slice(0, 2), slice(2, 4), slice(0, 2), slice(2, 4)),
        factors,
    ):
        r = 1 if idx < 2 else 2
        a1 = cur_base * (ft * (0.9 + 0.02 * idx))
        a2 = prev_base * (ft * 0.92)
        a1 = np.clip(a1, 0.5, None)
        a2 = np.clip(a2, 0.5, None)
        ax = fig.add_subplot(gs[r, cslice])
        ax.set_facecolor("#fafafa")
        ax.bar(x - w / 2, a1, w, label=lc, color="#1976d2", edgecolor="white", linewidth=0.4)
        ax.bar(x + w / 2, a2, w, label=lp, color="#90a4ae", edgecolor="white", linewidth=0.4)
        ptitle = fill(panel_titles[idx], width=50)
        ax.set_title(ptitle, fontsize=9, color="#212121", pad=4)
        ax.set_xticks(x)
        ax.set_xticklabels(period_labels, fontsize=7, rotation=0)
        ax.legend(fontsize=6.5, loc="upper right", framealpha=0.9)
        ax.grid(True, axis="y", alpha=0.28)
        ax.set_ylabel("scale (illustrative)", fontsize=7)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    fig.subplots_adjust(top=0.88)

    buf_png = io.BytesIO()
    fig.savefig(
        buf_png,
        format="png",
        dpi=150,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    buf_png.seek(0)
    buf_jpg = io.BytesIO()
    fig.savefig(
        buf_jpg,
        format="jpeg",
        dpi=150,
        bbox_inches="tight",
        facecolor=fig.get_facecolor(),
        pil_kwargs={"quality": 90},
    )
    buf_jpg.seek(0)
    plt.close(fig)

    png_b, jpg_b = buf_png.getvalue(), buf_jpg.getvalue()
    lpng = base / "latest_wireframe.png"
    ljpg = base / "latest_wireframe.jpg"
    try:
        lpng.write_bytes(png_b)
        ljpg.write_bytes(jpg_b)
        (hist / f"{ts}_wireframe.png").write_bytes(png_b)
        (hist / f"{ts}_wireframe.jpg").write_bytes(jpg_b)
    except OSError as e:
        return {"wireframe_raster_error": str(e)}

    rel = lambda p: str(p.relative_to(REPO_ROOT)).replace("\\", "/")
    return {
        "output_wireframe_png": rel(lpng),
        "output_wireframe_jpeg": rel(ljpg),
        "wireframe_raster": "erp_dashboard_from_markdown_v2",
    }
