"""Read-only database tools for the Reporting Agent (external SQL source)."""

from __future__ import annotations

import os
import re
from typing import Any

from crewai.tools.base_tool import BaseTool, tool

_engine: Any = None


def _get_engine():
    global _engine
    if _engine is not None:
        return _engine
    url = os.environ.get("REPORTING_DATABASE_URL", "").strip()
    if not url:
        return None
    from sqlalchemy import create_engine

    _engine = create_engine(url, pool_pre_ping=True, future=True)
    return _engine


def _is_safe_readonly_sql(sql: str) -> tuple[bool, str]:
    s = sql.strip()
    if not s:
        return False, "Empty query."
    if ";" in s.rstrip(";"):
        return False, "Multiple statements are not allowed."
    s_one = s.rstrip().rstrip(";")
    if not re.match(r"(?is)^\s*select\s+", s_one):
        return False, "Only a single SELECT statement is allowed."
    upper = s_one.upper()
    forbidden = (
        " INSERT ",
        " UPDATE ",
        " DELETE ",
        " DROP ",
        " TRUNCATE ",
        " ALTER ",
        " CREATE ",
        " GRANT ",
        " REVOKE ",
        " INTO OUTFILE",
        " LOAD_FILE",
        " BENCHMARK(",
    )
    padded = f" {upper} "
    for bad in forbidden:
        if bad in padded:
            return False, f"Forbidden pattern: {bad.strip()}"
    if len(s_one) > 200_000:
        return False, "Query exceeds maximum length."
    return True, ""


def _list_tables() -> str:
    engine = _get_engine()
    if engine is None:
        return "No REPORTING_DATABASE_URL; cannot list tables."
    from sqlalchemy import inspect

    try:
        insp = inspect(engine)
        names = insp.get_table_names()
        if not names:
            return "No tables found (or no permission to list them)."
        return "Tables:\n" + "\n".join(f"- {n}" for n in sorted(names))
    except Exception as e:
        return f"Error listing tables: {e!s}"


@tool("list_database_tables")
def list_database_tables(placeholder: str = "") -> str:
    """
    List all table names in the external reporting database.
    Call this before writing SQL when the schema is unknown. Pass an empty string if unused.
    """
    _ = placeholder
    return _list_tables()


@tool("run_readonly_sql")
def run_readonly_sql(sql: str) -> str:
    """
    Execute exactly ONE read-only SQL SELECT. Returns a tab-separated text block (header + rows).
    Use only for analytics — never INSERT, UPDATE, DELETE, or DDL. Requires valid table/column names.
    """
    engine = _get_engine()
    if engine is None:
        return (
            "DATABASE NOT CONFIGURED: set REPORTING_DATABASE_URL (e.g. "
            "mysql+pymysql://user:pass@host:3306/dbname). "
            "Without a live connection, state clearly in your report that figures are illustrative only."
        )
    ok, err = _is_safe_readonly_sql(sql)
    if not ok:
        return f"Query rejected: {err}"
    max_rows = int(os.environ.get("REPORTING_SQL_MAX_ROWS", "5000"))
    from sqlalchemy import text

    with engine.connect() as conn:
        r = conn.execute(text(sql))
        cols = list(r.keys())
        rows = r.fetchmany(max_rows + 1)
    if len(rows) > max_rows:
        rows = rows[:max_rows]
        tail = f"\n... truncated to {max_rows} rows; refine the SELECT with filters or LIMIT."
    else:
        tail = ""
    if not rows:
        return f"0 rows. Columns: {cols}{tail}"
    out = ["\t".join(str(c) for c in cols)]
    for row in rows:
        out.append("\t".join("" if v is None else str(v) for v in row))
    return "\n".join(out) + tail


def build_reporting_tools() -> list[BaseTool]:
    """Tools attached to the Reporting Agent (must be instantiated tool objects)."""
    return [list_database_tables, run_readonly_sql]
