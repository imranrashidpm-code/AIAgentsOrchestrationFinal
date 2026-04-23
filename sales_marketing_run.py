"""CLI for Sales & Marketing (GTM) agents."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from sales_marketing_agents import (
    SALES_MARKETING_AGENT_IDS,
    list_sales_marketing_by_category,
    run_sales_marketing_agent,
)


def _print_catalog() -> None:
    order = ["sales_revenue", "marketing_demand", "brand_pmm"]
    for cat in order:
        items = list_sales_marketing_by_category().get(cat, [])
        if not items:
            continue
        print(f"\n[{cat.upper().replace('_', ' ')}]")
        for aid, label in items:
            print(f"  {aid}")
            print(f"      {label}")


def main() -> int:
    if sys.version_info[:2] < (3, 10) or sys.version_info[:2] > (3, 13):
        print("Use Python 3.10–3.13 for CrewAI.", file=sys.stderr)
        return 2
    load_dotenv()

    p = argparse.ArgumentParser(
        description="Run one Sales & Marketing (GTM) agent. Use --list-agents to see all ids.",
    )
    p.add_argument("agent_id", nargs="?", help="e.g. sm_campaign_planner")
    p.add_argument(
        "--list-agents",
        action="store_true",
        help="Print all GTM agent ids and exit.",
    )
    p.add_argument("--prompt", default=os.environ.get("SM_USER_PROMPT", ""))
    p.add_argument("--constraints", default=os.environ.get("SM_CONSTRAINTS", "None specified."))
    p.add_argument(
        "--context",
        dest="business_context",
        default=os.environ.get("SM_BUSINESS_CONTEXT", "None specified."),
    )
    p.add_argument("--out", metavar="FILE")
    args = p.parse_args()

    if args.list_agents:
        _print_catalog()
        return 0
    if not args.agent_id:
        p.print_help()
        print()
        _print_catalog()
        return 0
    if args.agent_id not in SALES_MARKETING_AGENT_IDS:
        print("Unknown agent_id. Run: python sales_marketing_run.py --list-agents", file=sys.stderr)
        return 2
    if not (args.prompt or "").strip():
        print("Provide --prompt (or SM_USER_PROMPT).", file=sys.stderr)
        return 2
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY is not set.", file=sys.stderr)

    r = run_sales_marketing_agent(
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
