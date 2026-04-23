"""
DevOps & platform — runbooks, incident postmortems, SLO/SLA wording, K8s & CI/CD high-level design.

Display name: **DevOps & platform** (ids ``dvp_*``).
"""

from __future__ import annotations

DEVOPS_PLATFORM_AGENTS: tuple[tuple[str, str, str, str], ...] = (
    ("dvp_ops_runbook", "Operational runbook (procedure, checks, rollback)", "operations", "devops/runbooks"),
    ("dvp_incident_postmortem", "Incident postmortem (timeline, root cause, actions)", "incidents", "devops/incidents"),
    (
        "dvp_slo_sla_framing",
        "SLO/SLA wording, error budget, and alerting policy outline",
        "reliability",
        "devops/reliability",
    ),
    (
        "dvp_cicd_pipeline_design",
        "CI/CD high-level design (stages, gates, env promotion, secrets at outline level)",
        "delivery",
        "devops/cicd",
    ),
    (
        "dvp_kubernetes_platform",
        "Kubernetes platform sketch (workloads, networking, HPA, GitOps; high level)",
        "platform",
        "devops/kubernetes",
    ),
)

DEVOPS_PLATFORM_AGENT_IDS: frozenset[str] = frozenset(a[0] for a in DEVOPS_PLATFORM_AGENTS)
AGENT_OUTPUT_SUBDIR: dict[str, str] = {a[0]: a[3] for a in DEVOPS_PLATFORM_AGENTS}
DISPLAY_NAME = "DevOps & platform"


def list_by_category() -> dict[str, list[tuple[str, str]]]:
    out: dict[str, list[tuple[str, str]]] = {}
    for aid, label, cat, _ in DEVOPS_PLATFORM_AGENTS:
        out.setdefault(cat, []).append((aid, label))
    return out
