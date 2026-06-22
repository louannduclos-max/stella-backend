from app.api.schemas.common import Score
from app.core.score_config import VERDICT_MAPPING, VERDICT_RULES


class VerdictEngine:
    def derive(self, scores: list[Score]):
        if not scores:
            return VERDICT_MAPPING["go_conditional"]

        weighted = sum((score.value * score.weight) for score in scores) / 100
        min_confidence = min((score.confidence_grade for score in scores), default=None)

        if weighted >= VERDICT_RULES["go"]["min_score"] and min_confidence in {"A", "B"}:
            return VERDICT_MAPPING["go"]
        if weighted >= VERDICT_RULES["go_conditional"]["min_score"]:
            return VERDICT_MAPPING["go_conditional"]
        return VERDICT_MAPPING["no_go"]


verdict_engine = VerdictEngine()
