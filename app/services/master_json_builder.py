from datetime import UTC, datetime

from app.api.schemas.common import Study
from app.services.lovable_config import build_lovable_config


class MasterJsonBuilder:
    def build(self, study: Study) -> dict:
        metrics = [metric.model_dump(mode="json") for metric in study.metrics]
        scores = [score.model_dump(mode="json") for score in study.scores]
        sections = [section.model_dump(mode="json") for section in study.sections]
        sources = [source.model_dump(mode="json") for source in study.sources]
        qa_results = [qa.model_dump(mode="json") for qa in study.qa_results]

        metrics_by_id = {item["metric_id"]: item for item in metrics}
        scores_by_id = {item["score_id"]: item for item in scores}

        # Concurrents nommés — top 10 + total (Chantier 2)
        competitors_all = [c.model_dump(mode="json") for c in (study.competitors or [])]
        competitors_top = competitors_all[:10]
        competitors_total = len(competitors_all)

        # Barème financement (Chantier 3)
        funding_scale = (
            study.funding_scale.model_dump(mode="json") if study.funding_scale else None
        )

        # Market sizing (Chantier 3) — stocké en attribut temporaire par le pipeline
        market_sizing = getattr(study, "_market_sizing", None)

        return {
            "export_name": "stella_master_json",
            "generated_at": datetime.now(UTC).isoformat(),
            "study": {
                "study_id": study.study_id,
                "version": study.version,
                "status": study.status,
                "country": study.country,
                "language": study.language,
                "study_type": study.study_type,
                "study_date": study.study_date,
                "verdict": study.verdict,
                "created_at": study.created_at,
                "updated_at": study.updated_at,
                "geo_scope": study.geo_scope.model_dump(mode="json"),
                "business_context": study.business_context.model_dump(mode="json"),
            },
            "metrics": {
                "count": len(metrics),
                "items": metrics,
                "by_id": metrics_by_id,
            },
            "scores": {
                "count": len(scores),
                "items": scores,
                "by_id": scores_by_id,
            },
            "sections": {
                "count": len(sections),
                "items": sections,
            },
            "microzones": study.microzones.model_dump(mode="json") if study.microzones else None,
            "sources": {
                "count": len(sources),
                "items": sources,
            },
            "qa": {
                "count": len(qa_results),
                "items": qa_results,
                "has_blocking": any(item["severity"] == "blocking" and item["status"] == "fail" for item in qa_results),
            },
            "lovable": build_lovable_config(
                business_model=study.business_context.business_model,
                study_id=study.study_id,
            ),
            # Narratifs LLM (Gemini ou template) — utilisés par le Slide Builder Agent
            "narratives": study.narratives or {},
            # Score composite pondéré
            "score_composite": self._compute_composite(study),
            # ─── Data-Depth sprint ────────────────────────────────────────────
            # Concurrents nommés Google Places (Chantier 2)
            "competitors_top": competitors_top,          # jusqu'à 10 acteurs nommés
            "competitors_total_count": competitors_total,  # nb total identifiés
            # Barème de financement (Chantier 3) — None si pays non couvert
            "funding_scale": funding_scale,
            # Marché adressable estimé (Chantier 3) — None si données insuffisantes
            "market_sizing": market_sizing,
        }


    def _compute_composite(self, study) -> float | None:
        """Calcule le score composite pondéré depuis les scores de l'étude."""
        if not study.scores:
            return None
        total_weight = sum(s.weight for s in study.scores)
        if total_weight == 0:
            return None
        weighted = sum(s.value * s.weight for s in study.scores)
        return round(weighted / total_weight, 1)


master_json_builder = MasterJsonBuilder()
