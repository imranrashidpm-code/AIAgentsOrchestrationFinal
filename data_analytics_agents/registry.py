"""
Data & analytics — metrics, dashboards, event schemas, warehouse/dbt conceptual models.

Complements the **Reporting** SQL agent with design-time analytics documentation.
Display name: **Data & analytics** (ids ``dta_*``).
"""

from __future__ import annotations

DATA_ANALYTICS_AGENTS: tuple[tuple[str, str, str, str], ...] = (
    ("dta_metric_definitions", "Metric & KPI definitions (conformed names, owners, refresh)", "metrics", "data/metrics"),
    ("dta_dashboard_spec", "Dashboard / reporting product spec (audience, charts, actions)", "product", "data/product"),
    ("dta_event_schema_narrative", "Event & analytics schema narrative (naming, PII, validation)", "events", "data/events"),
    (
        "dta_warehouse_dbt_conceptual",
        "Warehouse & dbt conceptual model (marts, layers, lineage; not executable SQL by default)",
        "warehouse",
        "data/warehouse",
    ),
)

DATA_ANALYTICS_AGENT_IDS: frozenset[str] = frozenset(a[0] for a in DATA_ANALYTICS_AGENTS)
AGENT_OUTPUT_SUBDIR: dict[str, str] = {a[0]: a[3] for a in DATA_ANALYTICS_AGENTS}
DISPLAY_NAME = "Data & analytics"


def list_by_category() -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {}
    for aid, label, cat, _ in DATA_ANALYTICS_AGENTS:
        out.setdefault(cat, []).append((aid, label))
    return out
