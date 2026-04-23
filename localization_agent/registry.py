"""Internationalization (i18n) & localization (l10n) — locale, RTL, content workflow."""

from __future__ import annotations

LOCALIZATION_AGENTS: tuple[tuple[str, str, str, str], ...] = (
    (
        "i18n_l10n_spec",
        "i18n & l10n: locales, string workflow, formatting, RTL, testing",
        "l10n",
        "product/localization",
    ),
)

LOCALIZATION_AGENT_IDS: frozenset[str] = frozenset(a[0] for a in LOCALIZATION_AGENTS)
AGENT_OUTPUT_SUBDIR: dict[str, str] = {a[0]: a[3] for a in LOCALIZATION_AGENTS}
DISPLAY_NAME = "Localization (i18n/l10n)"
