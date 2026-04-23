"""CLI for QA & test strategy agents."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from output_paths import sanitize_filename, write_agent_markdown
from qa_test_strategy_agents import (
    AGENT_OUTPUT_SUBDIR,
    DISPLAY_NAME,
    QA_TEST_STRATEGY_AGENT_IDS,
    list_by_category,
    run_qa_test_strategy_agent,
)


def _print_catalog() -> None:
    print(f"{DISPLAY_NAME} (prefix qts_)")
    order = ["planning", "risk", "e2e", "regression"]
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
    p.add_argument("agent_id", nargs="?", help="e.g. qts_test_plan")
    p.add_argument("--list-agents", action="store_true", help="Print all qts_ ids")
    p.add_argument("--prompt", default=os.environ.get("QTS_USER_PROMPT", ""))
    p.add_argument("--constraints", default=os.environ.get("QTS_CONSTRAINTS", "None specified."))
    p.add_argument(
        "--context", dest="business_context", default=os.environ.get("QTS_BUSINESS_CONTEXT", "None specified.")
    )
    p.add_argument("--out-dir", metavar="DIR", help="Save under qa/... subfolders")
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
    if args.agent_id not in QA_TEST_STRATEGY_AGENT_IDS:
        print("Unknown agent_id. Run: py qa_test_strategy_run.py --list-agents", file=sys.stderr)
        return 2
    if not (args.prompt or "").strip():
        print("Provide --prompt (or QTS_USER_PROMPT).", file=sys.stderr)
        return 2
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY is not set.", file=sys.stderr)

    r = run_qa_test_strategy_agent(
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
        sub = AGENT_OUTPUT_SUBDIR.get(args.agent_id, "qa")
        parts = tuple(Path(sub.replace("\\", "/")).parts)
        fn = f"{sanitize_filename(args.agent_id)}.md"
        saved = write_agent_markdown(base, *parts, filename=fn, body=out)
        print(f"\n[Saved] {saved.resolve()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
