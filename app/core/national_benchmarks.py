"""
Benchmarks nationaux de référence — France (extensible par pays).

CHAQUE valeur porte sa source ET son année de validité.
⚠️ Revérifier annuellement à la source officielle avant de coder.
Sources : INSEE (démographie/revenus), DREES (dépendance), France Travail (emploi), DVF (immobilier).

Ce fichier est la SEULE source de vérité pour les benchmarks codés en dur.
Ne jamais copier ces valeurs dans un autre fichier sans pointer ici.
"""

BENCHMARKS_YEAR = 2024  # année de validité de la majorité des valeurs

NATIONAL_BENCHMARKS_FR: dict[str, dict] = {
    # ─── Démographie ──────────────────────────────────────────────────────────
    "seniors_60_plus_share": {
        "value": 27.0,
        "source": "INSEE — Bilan démographique 2023",
        "year": 2023,
        "unit": "%",
    },
    "seniors_75_plus_share": {
        "value": 9.5,
        "source": "INSEE — Bilan démographique 2023",
        "year": 2023,
        "unit": "%",
    },
    "aging_index": {
        "value": 133.0,
        "source": "INSEE — Bilan démographique 2023",
        "year": 2023,
        "unit": "indice",
    },
    "dependency_ratio": {
        "value": 55.0,
        "source": "INSEE — Indicateurs démographiques 2023",
        "year": 2023,
        "unit": "indice",
    },
    # ─── Revenus ──────────────────────────────────────────────────────────────
    "median_income": {
        "value": 22_040,
        "source": "INSEE — Filosofi 2021 (revenus disponibles par UC)",
        "year": 2021,
        "unit": "EUR/an",
    },
    # ─── Emploi ───────────────────────────────────────────────────────────────
    "unemployment_rate": {
        "value": 7.3,
        "source": "France Travail — Taux de chômage BIT T4 2024",
        "year": 2024,
        "unit": "%",
    },
    # ─── Population ───────────────────────────────────────────────────────────
    "foreign_residents_share": {
        "value": 10.3,
        "source": "INSEE — RP 2020 exploitation principale",
        "year": 2023,
        "unit": "%",
    },
    # ─── Immobilier ───────────────────────────────────────────────────────────
    "real_estate_price_house_m2": {
        "value": 2_650,
        "source": "DVF (Demandes de Valeurs Foncières) — médiane nationale 2024",
        "year": 2024,
        "unit": "EUR/m²",
    },
    # ─── À compléter au besoin ────────────────────────────────────────────────
    # "population_growth_5y", "taxable_households_share", ...
    # Ajouter ici avec source + year avant tout usage.
}


def get_national_benchmark(metric_id: str, country: str = "FR") -> dict | None:
    """
    Retourne le benchmark national pour un metric_id et un pays.
    Retourne None si pas de benchmark disponible (pas d'invention).
    """
    if country.upper() != "FR":
        # Étendre ici pour ES (INE, SEPE) quand filiales Espagne disponibles
        return None
    return NATIONAL_BENCHMARKS_FR.get(metric_id)


def benchmarks_are_stale(current_year: int) -> bool:
    """
    Signale si les benchmarks ont plus d'un an par rapport à BENCHMARKS_YEAR.
    À appeler au démarrage pour déclencher un avertissement de maintenance.
    """
    return current_year - BENCHMARKS_YEAR > 1
