from app.api.schemas.common import Metric, Score, ScoreDriver
from app.core.enums import ConfidenceGrade
from app.core.score_config import (
    CONFIDENCE_PENALTY,
    DEFAULT_METRIC_BASELINES,
    SCORE_CONFIG,
)


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
