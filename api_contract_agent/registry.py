"""API & contract design — OpenAPI/GraphQL, versioning, errors, idempotency (spec-level)."""

from __future__ import annotations

API_CONTRACT_AGENTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "api_openapi_contract",
        "API contract: OpenAPI/GraphQL, versioning, errors, pagination, idempotency",
        "api",
        "contracts/api",
    ),
)

API_CONTRACT_AGENT_IDS: frozenset[str] = frozenset(a[0] for a in API_CONTRACT_AGENTS)
AGENT_OUTPUT_SUBDIR: dict[str, str] = {a[0]: a[3] for a in API_CONTRACT_AGENTS}
DISPLAY_NAME = "API & contract"
