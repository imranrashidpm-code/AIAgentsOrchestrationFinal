"""
Sales & Marketing (GTM) agents — ICP, pipeline, campaigns, content, brand, launch. One agent per id.

Not the same as ERP `automation_agents` sales_* (quotes/credit). Use this pack for
go-to-market and demand generation narratives.

CLI: ``python sales_marketing_run.py <agent_id> --prompt "..."`` (``--list-agents`` for the catalog)
API: ``GET /v1/sales-marketing/agents`` · ``POST /v1/sales-marketing/{agent_id}``
"""

from .registry import (
    SALES_MARKETING_AGENT_IDS,
    SALES_MARKETING_AGENTS,
    list_sales_marketing_by_category,
)

__all__ = [
    "SALES_MARKETING_AGENT_IDS",
    "SALES_MARKETING_AGENTS",
    "list_sales_marketing_by_category",
    "run_sales_marketing_agent",
]


def __getattr__(name: str):
    if name == "run_sales_marketing_agent":
        from .factory import run_sales_marketing_agent

        return run_sales_marketing_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
