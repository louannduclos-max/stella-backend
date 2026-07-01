from app.api.schemas.common import Metric, Score, ScoreDriver
from app.core.enums import ConfidenceGrade
from app.core.score_config import (
    CONFIDENCE_PENALTY,
    DEFAULT_METRIC_BASELINES,
    SCORE_CONFIG,
)

# ─────────────────────────────────────────────────────────────────────────────
# Sprint 13f — interprétations déterministes par seuils (aucun LLM).
# Le moteur normalise tous les scores en "haut = favorable" : pour les
# dimensions "inversées" (pression concurrentielle, complexité réglementaire,
# risque d'exécution), un score BAS signifie que le phénomène est FORT.
# Les formulations le traduisent — ne jamais écrire "faible pression" pour
# un score bas de pression concurrentielle.
# Seuils : ≥ 60 favorable / 40-59 intermédiaire / < 40 défavorable.
# ─────────────────────────────────────────────────────────────────────────────

_INTERPRETATIONS: dict[str, tuple[str, str, str]] = {
    # score_name: (texte si ≥60, texte 40-59, texte <40)
    "market_attractiveness": (
        "Marché local attractif : la demande potentielle soutient une implantation.",
        "Attractivité de marché intermédiaire : un potentiel réel mais sans marge de confort.",
        "Attractivité de marché limitée : la demande locale ne porte pas le projet à elle seule.",
    ),
    "rh_feasibility": (
        "Vivier RH favorable : le recrutement d'intervenants est réaliste sur la zone.",
        "Faisabilité RH intermédiaire : recrutement possible mais sous tension.",
        "Vivier RH insuffisant : le recrutement d'intervenants sera le premier obstacle.",
    ),
    "competitive_pressure": (
        "Pression concurrentielle contenue : de l'espace reste à prendre.",
        "Pression concurrentielle sensible : une différenciation claire est nécessaire.",
        "Pression concurrentielle forte : marché dense, la part de marché se prendra sur les acteurs en place.",
    ),
    "regulatory_complexity": (
        "Cadre réglementaire praticable : pas de barrière administrative majeure.",
        "Complexité réglementaire modérée : anticiper les délais d'autorisation.",
        "Cadre réglementaire exigeant : la conformité (autorisation SAAD) est un chantier à part entière.",
    ),
    "premium_potential": (
        "Potentiel premium élevé : une clientèle solvable pour des prestations à valeur ajoutée.",
        "Potentiel premium moyen : le positionnement haut de gamme demande un ciblage fin.",
        "Potentiel premium restreint : privilégier une offre cœur de marché.",
    ),
    "recurring_revenue_potential": (
        "Fort potentiel de revenus récurrents : la dépendance installée alimente des contrats durables.",
        "Potentiel récurrent correct : une base de contrats réguliers est constructible.",
        "Potentiel récurrent limité : les revenus réguliers seront longs à construire.",
    ),
    "execution_risk": (
        "Risque d'exécution maîtrisé : les conditions opérationnelles sont réunies.",
        "Risque d'exécution modéré : un pilotage serré du lancement s'impose.",
        "Risque d'exécution élevé : cumul de facteurs défavorables sur la mise en œuvre.",
    ),
}


def _interpret(score_name: str, value: float) -> str | None:
    """Retourne la phrase d'interprétation par seuils, None si dimension inconnue."""
    tiers = _INTERPRETATIONS.get(score_name)
    if not tiers:
        return None
    if value >= 60:
        return tiers[0]
    if value >= 40:
        return tiers[1]
    return tiers[2]


class ScoringEngine:
    def bootstrap_scores(self) -> list[Score]:
        scores: list[Score] = []
        for score_name, config in SCORE_CONFIG.items():
            drivers = [
                ScoreDriver(metric_name=item["metric_id"], normalized_value=50, weight=item["weight"])
                for item in config["metrics"]
            ]
            scores.append(
                Score(
                    score_id=f"scr_{score_name}",
                    name=score_name,
                    label=config["label"],
                    weight=config["weight"],
                    value=50,
                    confidence_grade=ConfidenceGrade.C,
                    drivers=drivers,
                    missing_inputs_count=len(config["metrics"]),
                    status="provisional",
                )
            )
        return scores

    def compute_scores(self, metrics: list[Metric]) -> list[Score]:
        metric_by_id = {m.metric_id: m for m in metrics}
        scores: list[Score] = []

        for score_name, config in SCORE_CONFIG.items():
            drivers: list[ScoreDriver] = []
            missing = 0
            confidences: list[ConfidenceGrade] = []

            for item in config["metrics"]:
                metric = metric_by_id.get(item["metric_id"])
                if metric is None:
                    missing += 1
                    drivers.append(ScoreDriver(metric_name=item["metric_id"], normalized_value=50, weight=item["weight"]))
                    continue
                normalized = self._normalize(metric.metric_id, metric.value, config["higher_is_better"])
                drivers.append(ScoreDriver(metric_name=metric.metric_id, normalized_value=normalized, weight=item["weight"]))
                confidences.append(metric.confidence_grade)

            base = sum(d.normalized_value * d.weight for d in drivers)
            confidence = self._aggregate_confidence(confidences)
            penalty = CONFIDENCE_PENALTY[confidence]
            value = max(0, min(100, round(base - penalty)))

            scores.append(
                Score(
                    score_id=f"scr_{score_name}",
                    name=score_name,
                    label=config["label"],
                    weight=config["weight"],
                    value=value,
                    confidence_grade=confidence,
                    drivers=drivers,
                    missing_inputs_count=missing,
                    status="final" if missing == 0 else "partial",
                    interpretation=_interpret(score_name, value),
                )
            )
        return scores

    def _normalize(self, metric_id: str, value, higher_is_better: bool) -> float:
        try:
            v = float(value)
        except (TypeError, ValueError):
            return 50.0
        baseline = float(DEFAULT_METRIC_BASELINES.get(metric_id, v if v else 1))
        if baseline == 0:
            ratio = 1.0
        else:
            ratio = v / baseline
        score = 50 * ratio if higher_is_better else 50 / max(ratio, 0.01)
        return max(0.0, min(100.0, score))

    def _aggregate_confidence(self, confidences: list[ConfidenceGrade]) -> ConfidenceGrade:
        if not confidences:
            return ConfidenceGrade.E
        order = {ConfidenceGrade.A: 0, ConfidenceGrade.B: 1, ConfidenceGrade.C: 2, ConfidenceGrade.D: 3, ConfidenceGrade.E: 4}
        worst = max(confidences, key=lambda c: order[c])
        return worst


scoring_engine = ScoringEngine()
