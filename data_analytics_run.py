"""CLI for Data & analytics agents."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from data_analytics_agents import (
    AGENT_OUTPUT_SUBDIR,
    DATA_ANALYTICS_AGENT_IDS,
    DISPLAY_NAME,
    list_by_category,
    run_data_analytics_agent,
)
from output_paths import sanitize_filename, write_agent_markdown


def _print_catalog() -> None:
    print(f"{DISPLAY_NAME} (prefix dta_)")
    order = ["metrics", "product", "events", "warehouse"]
    for cat in order:
        items = list_by_category().get(cat, [])
        if not items:
            continue
        print(f"\n[{cat.upper()}]")
        for aid, label in items:
            print(f"  {aid}")
            print(f"      {label}")


def main() -> int:
    if sys.version_info[:2] < (3, 10) or sys.version_info[:2] > (3, 13):
        print("Use Python 3.10–3.13 for CrewAI.", file=sys.stderr)
        return 2
    load_dotenv()
    p = argparse.ArgumentParser(description=f"Run one {DISPLAY_NAME} agent. Use --list-agents for ids.")
    p.add_argument("agent_id", nargs="?", help="e.g. dta_metric_definitions")
    p.add_argument("--list-agents", action="store_true", help="Print all dta_ ids")
    p.add_argument("--prompt", default=os.environ.get("DTA_USER_PROMPT", ""))
    p.add_argument("--constraints", default=os.environ.get("DTA_CONSTRAINTS", "None specified."))
    p.add_argument(
        "--context", dest="business_context", default=os.environ.get("DTA_BUSINESS_CONTEXT", "None specified.")
    )
    p.add_argument("--out-dir", metavar="DIR", help="Save under data/... subfolders")
    p.add_argument("--out", metavar="FILE", help="Also write to a single file")
    args = p.parse_args()

    if args.list_agents:
        _print_catalog()
        return 0
    if not args.agent_id:
        p.print_help()
        print()
        _print_catalog()
        return 0
    if args.agent_id not in DATA_ANALYTICS_AGENT_IDS:
        print("Unknown agent_id. Run: py data_analytics_run.py --list-agents", file=sys.stderr)
        return 2
    if not (args.prompt or "").strip():
        print("Provide --prompt (or DTA_USER_PROMPT).", file=sys.stderr)
        return 2
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY is not set.", file=sys.stderr)

    r = run_data_analytics_agent(
        args.agent_id,
        {
            "user_prompt": args.prompt,
            "constraints": args.constraints,
            "business_context": args.business_context,
        },
    )
    text = getattr(r, "raw", None) or ""
    out = text if str(text).endswith("\n") else str(text) + "\n"
    sys.stdout.write(out)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
    if args.out_dir:
        base = Path(args.out_dir)
        sub = AGENT_OUTPUT_SUBDIR.get(args.agent_id, "data")
        parts = tuple(Path(sub.replace("\\", "/")).parts)
        fn = f"{sanitize_filename(args.agent_id)}.md"
        saved = write_agent_markdown(base, *parts, filename=fn, body=out)
        print(f"\n[Saved] {saved.resolve()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
