"""Run the professional SDLC crew (requires LLM API credentials in environment)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import TextIO

from dotenv import load_dotenv

from sdlc_crew import (
    load_parallel_jobs_from_json,
    run_parallel_pipelines,
    run_sdlc_then_reporting,
    run_single_pipeline,
)


def _default_brief() -> str:
    return (
        "Build a small internal web app for tracking employee training completions. "
        "Managers assign courses; employees mark lessons complete; HR exports CSV monthly."
    )


def _default_report_prompt() -> str:
    return (
        "Using the SDLC documentation as background, produce: (1) a short executive summary, "
        "(2) key operational and financial reporting insights if an external database is available "
        "via your tools, otherwise qualitative recommendations, and "
        "(3) numbered recommendations to improve the business (e.g. purchase discipline, stock aging, expiry risk)."
    )


def _write_output(stream: TextIO, text: str) -> None:
    stream.write(text)
    if not text.endswith("\n"):
        stream.write("\n")


def main() -> int:
    vi = sys.version_info[:2]
    if vi < (3, 10) or vi > (3, 13):
        print(
            "This project needs Python 3.10–3.13 (CrewAI has no wheels for Python 3.14 yet). "
            f"Current interpreter: {sys.version.split()[0]}. "
            'Create a venv with e.g. `py -3.13 -m venv .venv`.',
            file=sys.stderr,
        )
        return 2

    load_dotenv()

    parser = argparse.ArgumentParser(
        description=(
            "Run the professional SDLC crew: gathering -> analysis -> architecture -> "
            "database -> web -> Android -> iOS -> desktop -> QA -> DevOps. "
            "Use --parallel for concurrent module/sprint runs (output order matches JSON). "
            "Use --with-report to chain the Reporting Agent after SDLC (single run only)."
        ),
    )
    parser.add_argument(
        "brief",
        nargs="?",
        default=_default_brief(),
        help="Project / product description (positional).",
    )
    parser.add_argument(
        "--constraints",
        default=os.environ.get("SDLC_CONSTRAINTS", "None specified."),
        help="Global constraints, standards, or context for all agents.",
    )
    parser.add_argument(
        "--module-scope",
        default=os.environ.get("SDLC_MODULE_SCOPE", "Full product"),
        help="Module or feature area this run focuses on (e.g. Inventory, Billing).",
    )
    parser.add_argument(
        "--sprint",
        default=os.environ.get("SDLC_SPRINT_CONTEXT", "Full pipeline"),
        help="Sprint or delivery slice (goals, timeline, dependencies).",
    )
    parser.add_argument(
        "--parallel",
        metavar="JOBS.json",
        help=(
            "JSON file: array of objects with optional keys project_brief, constraints, "
            "module_scope, sprint_context. Runs one pipeline per object in parallel."
        ),
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Max concurrent pipelines when using --parallel (default: 4).",
    )
    parser.add_argument(
        "--out",
        metavar="FILE",
        help="Write combined output to this file (UTF-8) instead of only stdout.",
    )
    parser.add_argument(
        "--with-report",
        action="store_true",
        help=(
            "After the SDLC crew finishes, run the Reporting Agent with the SDLC text as context "
            "(not compatible with --parallel)."
        ),
    )
    parser.add_argument(
        "--report-prompt",
        default=os.environ.get("REPORTING_AFTER_SDLC_PROMPT", _default_report_prompt()),
        help="Question/instructions for the Reporting Agent when using --with-report.",
    )
    parser.add_argument(
        "--report-context",
        default=os.environ.get("REPORTING_AFTER_SDLC_EXTRA", "None specified."),
        help="Extra free-text context passed only to the Reporting step (e.g. currency, entity name).",
    )
    parser.add_argument(
        "--report-out",
        metavar="FILE",
        help="Write only the Reporting section to this file (UTF-8). Implies --with-report.",
    )
    args = parser.parse_args()

    if args.report_out and not args.with_report:
        args.with_report = True

    if args.parallel and args.with_report:
        print(
            "Error: --with-report cannot be used with --parallel. Run SDLC only, or use a single job.",
            file=sys.stderr,
        )
        return 2

    if not os.environ.get("OPENAI_API_KEY"):
        print(
            "Warning: OPENAI_API_KEY is not set. Set it or configure another LLM per CrewAI docs.",
            file=sys.stderr,
        )

    out_lines: list[str] = []

    def emit(chunk: str) -> None:
        out_lines.append(chunk)

    if args.parallel:
        jobs = load_parallel_jobs_from_json(args.parallel)
        pairs = run_parallel_pipelines(
            jobs,
            args.brief,
            args.constraints,
            max_workers=max(1, args.max_workers),
        )
        for merged, result in pairs:
            header = (
                f"\n{'=' * 72}\n"
                f"MODULE: {merged['module_scope']}\n"
                f"SPRINT: {merged['sprint_context']}\n"
                f"{'=' * 72}\n\n"
            )
            emit(header)
            emit(result.raw)
    else:
        inputs = {
            "project_brief": args.brief,
            "constraints": args.constraints,
            "module_scope": args.module_scope,
            "sprint_context": args.sprint,
        }
        if args.with_report:
            sdlc_res, report_res = run_sdlc_then_reporting(
                inputs,
                user_report_prompt=str(args.report_prompt),
                reporting_extra=str(args.report_context),
            )
            sdlc_text = getattr(sdlc_res, "raw", None) or ""
            report_text = getattr(report_res, "raw", None) or ""
            emit(sdlc_text)
            border = f"\n\n{'=' * 72}\nREPORTING AGENT (after SDLC)\n{'=' * 72}\n\n"
            emit(border)
            emit(report_text)
            if args.report_out:
                Path(args.report_out).write_text(
                    report_text + ("" if str(report_text).endswith("\n") else "\n"),
                    encoding="utf-8",
                )
        else:
            result = run_single_pipeline(inputs)
            emit(result.raw)

    combined = "".join(out_lines)

    _write_output(sys.stdout, combined)

    if args.out:
        Path(args.out).write_text(combined + ("" if combined.endswith("\n") else "\n"), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
