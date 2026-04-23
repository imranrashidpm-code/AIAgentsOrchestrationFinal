"""CLI for security & privacy agent (`sec_privacy_threat_pii`) — advisory; not legal advice."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from output_paths import sanitize_filename, write_agent_markdown
from security_privacy_agent import AGENT_OUTPUT_SUBDIR, DISPLAY_NAME, SECURITY_PRIVACY_AGENT_IDS, run_security_privacy_agent


def main() -> int:
    if sys.version_info[:2] < (3, 10) or sys.version_info[:2] > (3, 13):
        print("Use Python 3.10–3.13 for CrewAI.", file=sys.stderr)
        return 2
    load_dotenv()
    p = argparse.ArgumentParser(description=f"Run {DISPLAY_NAME} agent.")
    p.add_argument("agent_id", nargs="?", default="sec_privacy_threat_pii")
    p.add_argument("--list-agents", action="store_true")
    p.add_argument("--prompt", default=os.environ.get("SEC_USER_PROMPT", ""))
    p.add_argument("--constraints", default=os.environ.get("SEC_CONSTRAINTS", "None specified."))
    p.add_argument("--context", dest="business_context", default=os.environ.get("SEC_BUSINESS_CONTEXT", "None specified."))
    p.add_argument("--out-dir", metavar="DIR")
    p.add_argument("--out", metavar="FILE")
    args = p.parse_args()
    if args.list_agents:
        for aid in sorted(SECURITY_PRIVACY_AGENT_IDS):
            print(aid)
        return 0
    if not (args.prompt or "").strip():
        print("Provide --prompt.", file=sys.stderr)
        return 2
    if args.agent_id not in SECURITY_PRIVACY_AGENT_IDS:
        return 2
    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY is not set.", file=sys.stderr)
    r = run_security_privacy_agent(
        args.agent_id,
        {"user_prompt": args.prompt, "constraints": args.constraints, "business_context": args.business_context},
    )
    text = getattr(r, "raw", None) or ""
    out = text if str(text).endswith("\n") else str(text) + "\n"
    sys.stdout.write(out)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
    if args.out_dir:
        sub = AGENT_OUTPUT_SUBDIR.get(args.agent_id, "security/privacy")
        parts = tuple(Path(sub.replace("\\", "/")).parts)
        fn = f"{sanitize_filename(args.agent_id)}.md"
        saved = write_agent_markdown(Path(args.out_dir), *parts, filename=fn, body=out)
        print(f"\n[Saved] {saved.resolve()}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
