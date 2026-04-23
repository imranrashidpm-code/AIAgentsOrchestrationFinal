"""Run the Reporting Agent: natural-language business reports with optional external DB."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from sdlc_crew import run_reporting_pipeline


def _default_prompt() -> str:
    return (
        "Give an executive summary of the business current state and recommend actions "
        "to improve operations (e.g. over-purchasing, slow-moving or expired inventory assumptions)."
    )


def main() -> int:
    vi = sys.version_info[:2]
    if vi < (3, 10) or vi > (3, 13):
        print(
            "This project needs Python 3.10–3.13. "
            f"Current interpreter: {sys.version.split()[0]}.",
            file=sys.stderr,
        )
        return 2

    load_dotenv()

    parser = argparse.ArgumentParser(
        description=(
            "Reporting Agent: answer prompts using read-only SQL on REPORTING_DATABASE_URL "
            "when configured (MySQL via pymysql, or other SQLAlchemy URLs)."
        ),
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        default=_default_prompt(),
        help="Natural-language report request (e.g. P&L for a date range).",
    )
    parser.add_argument(
        "--context",
        default=os.environ.get("REPORTING_CONTEXT", "None specified."),
        help="Extra business rules, company context, or units.",
    )
    parser.add_argument(
        "--out",
        metavar="FILE",
        help="Write the report to this file (UTF-8).",
    )
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print(
            "Warning: OPENAI_API_KEY is not set.",
            file=sys.stderr,
        )

    inputs = {
        "user_report_prompt": args.prompt,
        "reporting_context": args.context,
    }
    result = run_reporting_pipeline(inputs)
    text = result.raw
    sys.stdout.write(text if text.endswith("\n") else text + "\n")

    if args.out:
        Path(args.out).write_text(text + ("" if text.endswith("\n") else "\n"), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
