"""
Sales & Marketing (GTM) agent IDs — go-to-market, brand, and revenue narrative work.

Note: For **ERP / order-to-cash** sales (quotes, credit, rebates), use `automation_agents` `sales_*` ids; this pack focuses on ICP, campaigns, content, and commercial strategy.
"""

from __future__ import annotations

# (id, short label, category)
SALES_MARKETING_AGENTS: tuple[tuple[str, str, str], ...] = (
    # Sales motion & revenue
    ("sm_lead_research_icp", "ICP, lead research & TAM scoping", "sales_revenue"),
    ("sm_pipeline_forecast", "Pipeline review, hygiene & forecast narrative", "sales_revenue"),
    ("sm_deal_coaching", "Deal strategy & next-step coaching (MEDDIC-style)", "sales_revenue"),
    ("sm_pricing_packaging", "SaaS/product pricing & packaging", "sales_revenue"),
    ("sm_account_growth", "Key account, expansion & NRR/GRR plans", "sales_revenue"),
    # Marketing — demand & channels
    ("sm_campaign_planner", "Integrated marketing campaign (objectives, channels, KPIs)", "marketing_demand"),
    ("sm_content_engine", "Content strategy, pillars & creative briefs", "marketing_demand"),
    ("sm_social_community", "Social, creator & community playbooks", "marketing_demand"),
    ("sm_paid_media", "Paid search, social & program recommendations", "marketing_demand"),
    ("sm_seo_content_clusters", "SEO, clusters & content calendar outline", "marketing_demand"),
    ("sm_email_lifecycle", "Email nurture, lifecycle & newsletters", "marketing_demand"),
    # Brand, field, competitive, PMM
    ("sm_brand_messaging", "Positioning, narrative & value props", "brand_pmm"),
    ("sm_events_webinars", "Events, webinars & field marketing plans", "brand_pmm"),
    ("sm_competitive_intel", "Competitive battlecards & market intel", "brand_pmm"),
    ("sm_product_launch_gtm", "Product / feature launch GTM (PMM)", "brand_pmm"),
)

SALES_MARKETING_AGENT_IDS: frozenset[str] = frozenset(a[0] for a in SALES_MARKETING_AGENTS)


def list_sales_marketing_by_category() -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {}
    for aid, label, cat in SALES_MARKETING_AGENTS:
        out.setdefault(cat, []).append((aid, label))
    return out
