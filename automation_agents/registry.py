"""Registered automation agent IDs (ERP / operations). Each ID maps to `automation_agents_*.yaml` + `automation_tasks_*.yaml`."""

from __future__ import annotations

# (id, short label, category)
AUTOMATION_AGENTS: tuple[tuple[str, str, str], ...] = (
    # Procurement & supply
    ("procurement_requisition_po", "Requisition & draft PO", "procurement"),
    ("procurement_three_way_match", "Three-way match (PO / receipt / invoice)", "procurement"),
    ("procurement_supplier_performance", "Supplier performance & scorecard", "procurement"),
    # Inventory & warehouse
    ("inventory_stock_policy", "Stock policy (reorder, safety stock, ABC)", "inventory"),
    ("inventory_allocation_promising", "Allocation & order promising", "inventory"),
    ("inventory_count_variance", "Cycle count & variance analysis", "inventory"),
    ("inventory_expiry_slow_mover", "Expiry & slow-mover actions", "inventory"),
    # Sales & revenue
    ("sales_quote_config", "Quote & configuration", "sales"),
    ("sales_credit_release", "Credit hold / release triage", "sales"),
    ("sales_rebate_contract", "Rebate & contract compliance", "sales"),
    # Manufacturing
    ("manufacturing_planner_mrp", "Planning & MRP-style suggestions", "manufacturing"),
    ("manufacturing_routing_work_order", "Routings & work order guidance", "manufacturing"),
    ("manufacturing_quality_ncr", "Quality & NCR triage", "manufacturing"),
    # Finance
    ("finance_period_close", "Period close checklist & narrative", "finance"),
    ("finance_reconciliation", "Reconciliation explanations", "finance"),
    ("finance_ap_automation", "AP classification & routing", "finance"),
    ("finance_tax_compliance_helper", "Tax & compliance decision support", "finance"),
    # Analytics
    ("analytics_kpi_variance_narrator", "KPI & variance narrator", "analytics"),
    ("analytics_scenario_what_if", "Scenario what-if (documentation style)", "analytics"),
    # Data & IT
    ("data_master_data_steward", "Master data duplicate & quality", "data"),
    ("data_integration_health", "Integration / sync health triage", "data"),
    ("data_user_access_sod", "Access & SoD review support", "data"),
    # Cross-cutting workflow
    ("workflow_case_triage", "Case / ticket routing", "workflow"),
    ("workflow_sop_training", "SOP & training draft from process", "workflow"),
    ("workflow_approval_workflow", "Approval packet preparation", "workflow"),
)

AUTOMATION_AGENT_IDS: frozenset[str] = frozenset(a[0] for a in AUTOMATION_AGENTS)


def list_agents_by_category() -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {}
    for aid, label, cat in AUTOMATION_AGENTS:
        out.setdefault(cat, []).append((aid, label))
    return out
