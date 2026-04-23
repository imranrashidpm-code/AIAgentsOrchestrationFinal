"""CLI to run a single automation agent by id (ERP workflow automation)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from automation_agents import (
    AUTOMATION_AGENT_IDS,
    list_agents_by_category,
    run_automation_agent,
)


def _print_agent_catalog() -> None:
    by_cat = list_agents_by_category()
    order = [
        "procurement",
        "inventory",
        "sales",
        "manufacturing",
        "finance",
        "analytics",
        "data",
        "workflow",
    ]
    for cat in order:
        items = by_cat.get(cat, [])
        if not items:
            continue
        print(f"\n[{cat.upper()}]")
        for aid, label in items:
            print(f"  {aid}")
            print(f"      {label}")


def main() -> int:
    vi = sys.version_info[:2]
    if vi < (3, 10) or vi > (3, 13):
        print("Use Python 3.10–3.13 for CrewAI.", file=sys.stderr)
        return 2

    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Run one Automation Agent by id. Use --list-agents to see all ids.",
    )
    parser.add_argument(
        "agent_id",
        nargs="?",
        help="Agent id, e.g. procurement_requisition_po",
    )
    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="Print all agent ids and exit.",
    )
    parser.add_argument(
        "--prompt",
        default=os.environ.get("AUTOMATION_USER_PROMPT", ""),
        help="Main user request (natural language).",
    )
    parser.add_argument(
        "--constraints",
        default=os.environ.get("AUTOMATION_CONSTRAINTS", "None specified."),
    )
    parser.add_argument(
        "--context",
        dest="business_context",
        default=os.environ.get("AUTOMATION_BUSINESS_CONTEXT", "None specified."),
        help="Business / ERP context: paste data, policies, or tables as text.",
    )
    parser.add_argument("--out", metavar="FILE", help="Write result to file (UTF-8).")
    args = parser.parse_args()

    if args.list_agents:
        _print_agent_catalog()
        return 0

    if not args.agent_id:
        parser.print_help()
        print()
        _print_agent_catalog()
        return 0

    if args.agent_id not in AUTOMATION_AGENT_IDS:
        print(f"Unknown agent_id: {args.agent_id!r}", file=sys.stderr)
        print("Run: python automation_run.py --list-agents", file=sys.stderr)
        return 2

    if not args.prompt.strip():
        print("Error: provide --prompt or set AUTOMATION_USER_PROMPT.", file=sys.stderr)
        return 2

    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY is not set.", file=sys.stderr)

    result = run_automation_agent(
        args.agent_id,
        {
            "user_prompt": args.prompt,
            "constraints": args.constraints,
            "business_context": args.business_context,
        },
    )
    text = getattr(result, "raw", None) or ""
    out = text if str(text).endswith("\n") else str(text) + "\n"
    sys.stdout.write(out)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
