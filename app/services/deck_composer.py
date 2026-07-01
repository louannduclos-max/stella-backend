"""
DeckComposer — Sprint 14b : le deck se COMPOSE, il n'est plus figé.

PRINCIPE (demande produit Louann, 02/07) :
  Les catégories de KPI (theme_id du KPI_CATALOG) sont le contrat entre
  l'intention client (wizard : kpi_focus) et la composition du deck.
  Se bloquer sur une liste fixe de slides = débordements et slides pauvres
  quand les données ou l'intention ne s'y prêtent pas.

100 % DÉTERMINISTE — aucun LLM. Le composeur décide :
  1. Les sections CORE (toujours présentes — squelette de l'étude).
  2. Les sections THÉMATIQUES : incluses si (le client les demande via
     kpi_focus OU pas de focus exprimé) ET (des données réelles existent).
  3. Les sections d'ENRICHISSEMENT : ajoutées quand leur thème est demandé
     et que les données le permettent.
  4. Un hint de qualité par section : "solid" (données réelles) ou
     "baseline_only" (tout est fallback national → la slide dira "estimation").

Le composeur ne SUPPRIME jamais une section core : une étude reste une étude.
"""
from __future__ import annotations

from app.core.kpi_catalog import KPI_CATALOG

# ─────────────────────────────────────────────────────────────────────────────
# Contrats de composition
# ─────────────────────────────────────────────────────────────────────────────

# Sections toujours présentes, dans l'ordre du deck.
CORE_SECTIONS: list[str] = [
    "cover",
    "executive_summary",
    "market_scorecard",
]

CORE_CLOSING: list[str] = [
    "swot",
    "verdict",
    "action_plan",
    "methodology_sources",
]

# theme_id (catégorie KPI) → sections thématiques pilotées par cette catégorie.
# L'ordre de ce dict est l'ordre d'apparition dans le deck.
THEME_SECTIONS: dict[str, list[str]] = {
    "demography":       ["demographics"],
    "target_segments":  ["target_segments"],
    "employment":       ["employment_talent"],
    "income_housing":   ["income_housing"],
    "real_estate":      ["real_estate"],
    "microzones":       ["microzones"],
    "operations":       ["geo_analysis"],
    "competition":      ["competition_mapping"],
    "regulation":       ["regulation_feasibility"],
    "business_case":    ["funding_feasibility", "market_overview"],
    "pricing":          [],   # KPI portés par regulation_feasibility (tarifs) — variant futur
    "tourism":          [],   # KPI portés par income_housing (rés. secondaires) — variant futur
}

# Sections d'enrichissement transverses (hors thème unique).
ENRICHMENT_SECTIONS: dict[str, list[str]] = {
    # benchmark national pertinent dès qu'on parle démographie/revenus
    "benchmark_comparison": ["demography", "income_housing"],
}

# Index metric_id → theme_id depuis le catalogue (source de vérité).
_METRIC_THEME: dict[str, str] = {
    item["metric_id"]: item["theme_id"] for item in KPI_CATALOG
}


# ─────────────────────────────────────────────────────────────────────────────
# Disponibilité des données par thème
# ─────────────────────────────────────────────────────────────────────────────

def _theme_data_status(manifest: dict) -> dict[str, str]:
    """
    Pour chaque thème : "solid" (≥1 métrique réelle non-fallback),
    "baseline_only" (uniquement des fallbacks nationaux) ou "missing".
    """
    status: dict[str, str] = {}
    metrics_obj = manifest.get("metrics") or {}
    items = metrics_obj.get("items", []) if isinstance(metrics_obj, dict) else metrics_obj

    for m in items:
        theme = _METRIC_THEME.get(m.get("metric_id"))
        if not theme:
            continue
        if not m.get("fallback_used"):
            status[theme] = "solid"
        else:
            status.setdefault(theme, "baseline_only")

    # Cas particuliers portés par d'autres clés du manifest
    if (manifest.get("competitors_total_count") or 0) > 0:
        status["competition"] = "solid"
    mz = manifest.get("microzones") or {}
    if isinstance(mz, dict) and mz.get("neighborhoods"):
        status.setdefault("microzones", "baseline_only")
    if manifest.get("funding_scale") or manifest.get("market_sizing"):
        status.setdefault("business_case", "solid")

    return status


# ─────────────────────────────────────────────────────────────────────────────
# Composition
# ─────────────────────────────────────────────────────────────────────────────

def compose_deck(manifest: dict, kpi_focus: list[str] | None = None) -> list[dict]:
    """
    Compose le deck : liste ordonnée de
      {section_id, status, theme, data}
    - status : "core" | "included" | "excluded_focus" | "excluded_no_data"
    - data   : "solid" | "baseline_only" | "missing" (hint qualité pour la slide)

    kpi_focus : catégories demandées par le client (wizard). None ou vide =
    pas de préférence = tout ce qui a des données.
    """
    focus = {f.strip().lower() for f in (kpi_focus or []) if f and f.strip()}
    data_status = _theme_data_status(manifest)

    deck: list[dict] = []

    for sid in CORE_SECTIONS:
        deck.append({"section_id": sid, "status": "core", "theme": None, "data": "solid"})

    for theme, sections in THEME_SECTIONS.items():
        theme_data = data_status.get(theme, "missing")
        for sid in sections:
            if focus and theme not in focus:
                deck.append({"section_id": sid, "status": "excluded_focus",
                             "theme": theme, "data": theme_data})
            elif theme_data == "missing":
                deck.append({"section_id": sid, "status": "excluded_no_data",
                             "theme": theme, "data": theme_data})
            else:
                deck.append({"section_id": sid, "status": "included",
                             "theme": theme, "data": theme_data})

    for sid, themes in ENRICHMENT_SECTIONS.items():
        relevant = (not focus) or any(t in focus for t in themes)
        has_data = any(data_status.get(t) == "solid" for t in themes)
        if relevant and has_data and (manifest.get("benchmark_rows") or sid != "benchmark_comparison"):
            deck.append({"section_id": sid, "status": "included",
                         "theme": "+".join(themes), "data": "solid"})
        else:
            deck.append({"section_id": sid, "status": "excluded_focus" if not relevant else "excluded_no_data",
                         "theme": "+".join(themes), "data": "solid" if has_data else "missing"})

    for sid in CORE_CLOSING:
        deck.append({"section_id": sid, "status": "core", "theme": None, "data": "solid"})

    return deck


def active_sections(manifest: dict, kpi_focus: list[str] | None = None) -> list[str]:
    """Liste ordonnée des section_id retenues (core + included)."""
    return [
        d["section_id"]
        for d in compose_deck(manifest, kpi_focus)
        if d["status"] in ("core", "included")
    ]


# ─────────────────────────────────────────────────────────────────────────────
# Pont avec le wizard front (Sprint 14b)
# Le wizard classe les KPI en 5 axes (tables *_master côté CF Pages) :
# market / hr / transport / competition / synthesis. Mapping vers les thèmes
# du KPI_CATALOG backend. synthesis = sections core, toujours présentes.
# ─────────────────────────────────────────────────────────────────────────────

# ATTENTION : les clés = les clés RÉELLES de analysis_axes envoyées par le front
# (wizard-submit.server.ts : demography = market_kpis, hr = hr_kpis, ...).
# Bug corrigé Sprint 14c : la clé front est "demography", PAS "market" —
# l'axe démographie/marché coché était perdu (constaté sur l'étude Lyon).
FRONT_AXES_TO_THEMES: dict[str, list[str]] = {
    "demography":  ["demography", "target_segments", "income_housing",
                    "real_estate", "business_case"],
    "market":      ["demography", "target_segments", "income_housing",
                    "real_estate", "business_case"],  # alias défensif
    "hr":          ["employment"],
    "transport":   ["operations", "microzones"],
    "competition": ["competition"],
    "synthesis":   [],  # core sections — jamais exclues
}


def kpi_focus_from_wizard(wizard_selections: dict | None) -> list[str] | None:
    """
    Traduit les axes d'analyse cochés au wizard (analysis_axes) en kpi_focus
    (thèmes backend). Retourne None si le client n'a rien restreint
    (aucun axe, ou tous les axes) → deck complet.
    """
    if not wizard_selections:
        return None
    axes = wizard_selections.get("analysis_axes") or {}
    if not isinstance(axes, dict):
        return None
    # Comparer sur les clés RÉELLEMENT envoyées par le front (pas sur notre
    # mapping, qui contient des alias) — Sprint 14c.
    active = [a for a, on in axes.items() if on]
    inactive = [a for a, on in axes.items() if not on and a != "synthesis"]
    if not active or not inactive:
        return None  # rien coché ou tout coché = pas de restriction
    themes: list[str] = []
    for axis in active:
        themes.extend(FRONT_AXES_TO_THEMES.get(axis, []))
    return themes or None


KNOWN_THEMES: list[str] = list(THEME_SECTIONS.keys())
