"""
Security & privacy (threat modeling, PII, controls) — **draft checklist only, not legal advice.**
"""

from __future__ import annotations

SECURITY_PRIVACY_AGENTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "sec_privacy_threat_pii",
        "Security + privacy: threat model, PII inventory, controls & DPIA-style outline",
        "security",
        "security/privacy",
    ),
)

SECURITY_PRIVACY_AGENT_IDS: frozenset[str] = frozenset(a[0] for a in SECURITY_PRIVACY_AGENTS)
AGENT_OUTPUT_SUBDIR: dict[str, str] = {a[0]: a[3] for a in SECURITY_PRIVACY_AGENTS}
DISPLAY_NAME = "Security & privacy"
