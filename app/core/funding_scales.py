"""
Barèmes de financement de la dépendance par pays.

France : APA (Allocation Personnalisée d'Autonomie)
  Source officielle : CNSA — Tarifs APA à domicile au 1er janvier {année}
  URL : https://www.cnsa.fr → Publications → Tarifs APA
  ⚠️ Revalorisé chaque année au 1er janvier — revérifier à la source AVANT de coder.
  Les montants ci-dessous ont été vérifiés pour 2026 sur la circulaire DGCS.

Espagne : SAAD (Sistema para la Autonomía y Atención a la Dependencia)
  → À implémenter avant tout déploiement Interdomicilio ES réel.
  → Ne PAS retourner le barème FR pour une étude ES.

RÈGLE : si aucun barème n'est disponible pour le pays de l'étude,
retourner None → pas de slide financement → pas d'invention.
"""

FUNDING_SCALE_YEAR_FR = 2026

# Plafonds mensuels du plan d'aide APA à domicile par GIR, France 2026.
# Source : CNSA / DGCS — arrondis officiels.
APA_SCALE_FR = [
    {
        "gir": "GIR 1",
        "label": "Dépendance totale",
        "apa_ceiling_eur_month": 2080.33,
        "coverage_note": "Plafond le plus élevé, maintien à domicile lourd",
    },
    {
        "gir": "GIR 2",
        "label": "Dépendance sévère",
        "apa_ceiling_eur_month": 1682.30,
        "coverage_note": "Forte prise en charge publique",
    },
    {
        "gir": "GIR 3",
        "label": "Dépendance modérée",
        "apa_ceiling_eur_month": 1215.99,
        "coverage_note": "Prise en charge intermédiaire",
    },
    {
        "gir": "GIR 4",
        "label": "Dépendance légère",
        "apa_ceiling_eur_month": 811.52,
        "coverage_note": "Plafond le plus bas — marché privé complémentaire important",
    },
]

# Participation progressive du bénéficiaire selon revenus mensuels, France 2026.
# Source : CNSA — Tableau 4 (participation à domicile).
APA_PARTICIPATION_FR = {
    "no_participation_below_eur": 933.89,    # revenus ≤ seuil → 0 % de participation
    "max_participation_above_eur": 3439.31,  # revenus > seuil → 90 % de participation
    "note": (
        "Participation progressive de 0 % à 90 % selon les revenus mensuels "
        "du bénéficiaire. Les ménages modestes bénéficient d'une couverture quasi-totale."
    ),
}


def get_funding_scale(country: str = "FR") -> dict | None:
    """
    Retourne le barème de financement pour un pays donné.
    Retourne None si le pays n'est pas encore couvert (pas d'invention).
    """
    if country.upper() == "FR":
        return {
            "type": "APA (Allocation Personnalisée d'Autonomie)",
            "source": f"CNSA — Tarifs APA à domicile au 1er janvier {FUNDING_SCALE_YEAR_FR}",
            "year": FUNDING_SCALE_YEAR_FR,
            "scale": APA_SCALE_FR,
            "participation": APA_PARTICIPATION_FR,
        }
    # ES = SAAD — à implémenter (Ley 39/2006 de Dependencia)
    # IT, DE, BE — à implémenter si nécessaire
    return None
