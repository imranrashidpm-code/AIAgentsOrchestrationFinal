"""CLI for release & distribution agent (`rel_app_distribution`)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from output_paths import sanitize_filename, write_agent_markdown
from release_distribution_agent import (
    AGENT_OUTPUT_SUBDIR,
    DISPLAY_NAME,
    RELEASE_DISTRIBUTION_AGENT_IDS,
    run_release_distribution_agent,
)


def main() -> int:
    if sys.version_info[:2] < (3, 10) or sys.version_info[:2] > (3, 13):
        print("Use Python 3.10–3.13 for CrewAI.", file=sys.stderr)
        return 2
    load_dotenv()
    p = argparse.ArgumentParser(description=f"Run {DISPLAY_NAME} agent.")
    p.add_argument("agent_id", nargs="?", default="rel_app_distribution")
    p.add_argument("--list-agents", action="store_true")
    p.add_argument("--prompt", default=os.environ.get("REL_USER_PROMPT", ""))
    p.add_argument("--constraints", default=os.environ.get("REL_CONSTRAINTS", "None specified."))
    p.add_argument("--context", dest="business_context", default=os.environ.get("REL_BUSINESS_CONTEXT", "None specified."))
    p.add_argument("--out-dir", metavar="DIR")
    p.add_argument("--out", metavar="FILE")
    args = p.parse_args()
    if args.list_agents:
        for aid in sorted(RELEASE_DISTRIBUTION_AGENT_IDS):
            print(aid)
        return 0
    if not (args.prompt or "").strip():
        print("Provide --prompt.", file=sys.stderr)
        return 2
    if args.agent_id not in RELEASE_DISTRIBUTION_AGENT_IDS:
        return 2
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY is not set.", file=sys.stderr)
    r = run_release_distribution_agent(
        args.agent_id,
        {"user_prompt": args.prompt, "constraints": args.constraints, "business_context": args.business_context},
    )
    text = getattr(r, "raw", None) or ""
    out = text if str(text).endswith("\n") else str(text) + "\n"
    sys.stdout.write(out)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
    if args.out_dir:
        sub = AGENT_OUTPUT_SUBDIR.get(args.agent_id, "platform/release")
        parts = tuple(Path(sub.replace("\\", "/")).parts)
        fn = f"{sanitize_filename(args.agent_id)}.md"
        saved = write_agent_markdown(Path(args.out_dir), *parts, filename=fn, body=out)
        print(f"\n[Saved] {saved.resolve()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
