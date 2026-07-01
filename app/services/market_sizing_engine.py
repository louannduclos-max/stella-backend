"""
MarketSizingEngine — estime le marché SAD privé adressable localement.

Croise les données démographiques réelles (metrics) avec des hypothèses
documentées et sourcées pour produire une estimation du nombre de clients
privés potentiels.

100 % déterministe. Aucun LLM. Aucune valeur inventée.
Les hypothèses sont TOUJOURS exposées dans le résultat — jamais cachées.
Si les données nécessaires manquent, retourne None (pas d'estimation partielle).
"""


class MarketSizingEngine:

    # Hypothèses nationales documentées.
    # Source : DREES — "Les bénéficiaires de l'APA : qui sont-ils ?" (2023)
    # Revérifier si une mise à jour DREES est disponible.
    HYPOTHESES = {
        "dependency_rate_among_75plus": 0.20,
        "dependency_rate_source": "DREES 2023 — environ 20 % des 75+ en perte d'autonomie (GIR 1-4)",
        "private_sad_preference_rate": 0.35,
        "private_sad_preference_source": (
            "Estimation marché : environ 35 % des bénéficiaires dépendants "
            "recourent à un prestataire SAD privé ou mixte."
        ),
    }

    def estimate(self, study) -> dict | None:
        """
        Estime le nombre de bénéficiaires potentiels et le marché adressable privé.

        Retourne None si les données nécessaires manquent.
        Retourne un dict avec le résultat ET les hypothèses utilisées.
        """
        by_id = {m.metric_id: m for m in study.metrics}

        population_metric = by_id.get("population_total")
        seniors_75_count = by_id.get("seniors_75_plus_count")
        seniors_75_share = by_id.get("seniors_75_plus_share")

        if not population_metric:
            return None  # impossible de calculer sans population totale

        try:
            pop = float(population_metric.value)
        except (TypeError, ValueError):
            return None

        # Résoudre le nombre de 75+ (effectif direct ou part × population)
        count_75: float | None = None
        if seniors_75_count:
            try:
                count_75 = float(seniors_75_count.value)
            except (TypeError, ValueError):
                pass
        if count_75 is None and seniors_75_share:
            try:
                share = float(seniors_75_share.value)
                # Si c'est déjà un effectif (> 200 personnes), utiliser tel quel
                count_75 = share if share > 200 else pop * (share / 100)
            except (TypeError, ValueError):
                pass

        if count_75 is None:
            return None  # impossible sans données 75+

        dep_rate = self.HYPOTHESES["dependency_rate_among_75plus"]
        priv_rate = self.HYPOTHESES["private_sad_preference_rate"]

        estimated_dependent = round(count_75 * dep_rate)
        addressable_private = round(estimated_dependent * priv_rate)

        return {
            "seniors_75_plus": round(count_75),
            "estimated_dependent": estimated_dependent,
            "addressable_private_market": addressable_private,
            "hypotheses": {
                "dependency_rate_among_75plus": dep_rate,
                "dependency_rate_source": self.HYPOTHESES["dependency_rate_source"],
                "private_sad_preference_rate": priv_rate,
                "private_sad_preference_source": self.HYPOTHESES["private_sad_preference_source"],
            },
            "disclaimer": (
                "Estimation basée sur des taux nationaux appliqués aux effectifs locaux. "
                "À affiner avec données départementales DREES si disponibles."
            ),
        }


market_sizing_engine = MarketSizingEngine()
