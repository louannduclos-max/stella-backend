"""
Pré-calcule toutes les valeurs dérivées dont les slides HTML ont besoin.
100% déterministe. L'agent LLM ne calcule JAMAIS — il recopie ces valeurs.

Sprint 10 v2 — corrige la faille majeure v1 :
  v1 : l'agent calculait ecarts, complements, moyennes -> hallucination + rejet QA
  v2 : tout est pre-calcule ici et injecte dans le manifest AVANT l'appel a l'agent.

Chaque valeur derivee devient une entree du manifest, donc tracable par le QA
(le QA verifie que tout nombre affiche existe dans le manifest).

Regles :
  - Aucune valeur inventee : si la donnee est manquante, le champ reste None.
  - Les champs derives ont des noms distincts des champs sources (pas d'ecrasement).
  - L'agent recoit benchmark_rows avec gap_display deja ecrit — il recopie.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def precompute_slide_values(study, manifest: dict) -> dict:
    """
    Enrichit le manifest avec les valeurs derivees pres a afficher.
    Appele par master_json_builder.build() en derniere etape.

    Valeurs ajoutees :
      benchmark_rows        : liste des ecarts au benchmark national (gap_display pre-calcule)
      demographics_pie      : labels + values (complement 100-s pre-calcule)
      scores_radar          : labels + values arrondies pour spider chart
      competition_avg_rating: moyenne des notes (pas a recalculer par l'agent)
      competition_table     : directs/indirects + étoiles pré-calculées (Sprint 12)
    """
    manifest = _compute_benchmark_rows(study, manifest)
    manifest = _compute_demographics_pie(study, manifest)
    manifest = _compute_scores_radar(study, manifest)
    manifest = _compute_competition_avg_rating(study, manifest)
    manifest = _compute_competition_table(study, manifest)
    return manifest


# -----------------------------------------------------------------------------
# Benchmark national (section benchmark_comparison)
# -----------------------------------------------------------------------------

def _compute_benchmark_rows(study, manifest: dict) -> dict:
    """
    Ecarts au benchmark national avec signe et direction.

    Chaque row contient :
      gap_display : ex "+52.6%" ou "-8.3%" — recopier tel quel, NE PAS recalculer
      direction   : "up" | "down" | "neutral" — pour le badge couleur
      gap_pct     : float brut si besoin de tri cote agent
    """
    rows = []
    for m in study.metrics:
        if m.national_benchmark is None:
            continue
        try:
            local = float(m.value)
            nat = float(m.national_benchmark)
        except (TypeError, ValueError):
            continue

        if nat != 0:
            gap_pct = round((local - nat) / nat * 100, 1)
            sign = "+" if gap_pct > 0 else ""
            gap_display = f"{sign}{gap_pct}%"
            direction = "up" if gap_pct > 0 else "down"
        else:
            gap_pct = None
            gap_display = "n.d."
            direction = "neutral"

        rows.append({
            "label":          m.label,
            "local":          m.value,
            "national":       m.national_benchmark,
            "unit":           m.unit or "",
            "gap_pct":        gap_pct,          # float brut
            "gap_display":    gap_display,       # affichage pret : "+52.6%"
            "direction":      direction,         # "up" | "down" | "neutral"
            "interpretation": m.benchmark_interpretation or "",
        })

    manifest["benchmark_rows"] = rows
    logger.debug("[precompute] benchmark_rows : %d lignes", len(rows))
    return manifest


# -----------------------------------------------------------------------------
# Demographie (section demographics)
# -----------------------------------------------------------------------------

def _compute_demographics_pie(study, manifest: dict) -> dict:
    """
    Repartition demographique pour camembert.
    Le complement (100 - seniors_share) est pre-calcule ici, pas par l'agent.
    L'agent recopie demographics_pie.values tels quels.
    """
    by_id = {m.metric_id: m for m in study.metrics}
    seniors = by_id.get("seniors_60_plus_share")

    if seniors is not None:
        try:
            s = round(float(seniors.value), 1)
            manifest["demographics_pie"] = {
                "labels": ["60 ans et +", "Moins de 60 ans"],
                "values": [s, round(100.0 - s, 1)],  # complement pre-calcule
            }
        except (TypeError, ValueError):
            manifest["demographics_pie"] = None
    else:
        manifest["demographics_pie"] = None

    return manifest


# -----------------------------------------------------------------------------
# Scores radar (section verdict)
# -----------------------------------------------------------------------------

def _compute_scores_radar(study, manifest: dict) -> dict:
    """
    Donnees radar pour spider chart du verdict.
    Valeurs arrondies et labellisees — l'agent recopie scores_radar.values.
    """
    if study.scores:
        manifest["scores_radar"] = {
            "labels": [s.label for s in study.scores],
            "values": [round(float(s.value)) for s in study.scores],
        }
    else:
        manifest["scores_radar"] = None
    return manifest


# -----------------------------------------------------------------------------
# Concurrence — note moyenne (section competition_mapping)
# -----------------------------------------------------------------------------

def _compute_competition_avg_rating(study, manifest: dict) -> dict:
    """
    Note moyenne du marche concurrentiel.
    Pre-calculee ici — l'agent ne divise pas, il recopie competition_avg_rating.
    """
    rated = [
        c.rating for c in (study.competitors or [])
        if c.rating is not None
    ]
    manifest["competition_avg_rating"] = (
        round(sum(rated) / len(rated), 1) if rated else None
    )
    return manifest


# -----------------------------------------------------------------------------
# Concurrence — tableau structuré directs/indirects + étoiles (Sprint 12)
# -----------------------------------------------------------------------------

def _stars(rating: float | None) -> str | None:
    """
    Convertit une note en chaîne d'étoiles pré-calculée.
    Ex : 4.5 → "★★★★☆"
    L'agent HTML recopie — il ne calcule PAS les étoiles.
    """
    if rating is None:
        return None
    full = int(round(rating))
    full = max(0, min(5, full))
    return "★" * full + "☆" * (5 - full)


def _compute_competition_table(study, manifest: dict) -> dict:
    """
    Tableau concurrentiel structuré pour la slide competition_mapping.

    Produit :
      competition_table.directs   : jusqu'à 8 concurrents directs (domain + étoiles)
      competition_table.indirects : jusqu'à 6 concurrents indirects
      competition_table.count_direct  : total directs (pas seulement top 8)
      competition_table.count_total   : total tous acteurs collectés
      competition_table.avg_rating    : note moyenne (repris de competition_avg_rating)

    L'agent HTML recopie ces valeurs — il ne filtre ni ne calcule.
    """
    comps = study.competitors or []

    def _to_row(c) -> dict:
        return {
            "name":     c.name,
            "domain":   getattr(c, "domain", None) or "n.d.",
            "rating":   c.rating,
            "stars":    _stars(c.rating),
            "reviews":  c.reviews_count,
            "source_id": c.source_id,
        }

    directs   = [c for c in comps if c.is_direct_competitor]
    indirects = [c for c in comps if not c.is_direct_competitor]

    manifest["competition_table"] = {
        "directs":      [_to_row(c) for c in directs[:8]],
        "indirects":    [_to_row(c) for c in indirects[:6]],
        "count_direct": len(directs),
        "count_total":  len(comps),
        "avg_rating":   manifest.get("competition_avg_rating"),
    }
    logger.debug(
        "[precompute] competition_table : %d directs / %d indirects / %d total",
        len(directs), len(indirects), len(comps),
    )
    return manifest
