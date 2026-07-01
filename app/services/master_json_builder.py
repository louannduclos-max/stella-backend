from datetime import UTC, datetime

from app.api.schemas.common import Study
from app.services.benchmark_engine import benchmark_engine
from app.services.lovable_config import build_lovable_config
from app.services.slide_precompute import precompute_slide_values


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

        # Market sizing (Chantier 3, fix Sprint 13) — champ Pydantic déclaré.
        # L'ancien attribut dynamique `_market_sizing` levait ValueError sur Pydantic v2
        # (Study n'autorise pas les attributs non déclarés) → toujours null en prod.
        # Filet : recalcul direct si le champ est vide (couvre les études legacy
        # rechargées depuis Supabase sans repasser par le pipeline).
        market_sizing = getattr(study, "market_sizing", None) or getattr(study, "_market_sizing", None)
        if market_sizing is None:
            try:
                from app.services.market_sizing_engine import market_sizing_engine
                market_sizing = market_sizing_engine.estimate(study)
            except Exception:
                market_sizing = None  # jamais bloquant, jamais d'estimation partielle

        manifest = {
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

        # Sprint 10 — Pré-calcul des valeurs dérivées pour les slides HTML
        # L'agent LLM recopie ces valeurs, il ne calcule jamais.
        # benchmark_rows (gap_display), demographics_pie, scores_radar, competition_avg_rating

        # Enrichissement benchmark national — idempotent (safe même si déjà fait dans le pipeline).
        # Couvre les études sauvegardées avant le branchement de benchmark_engine dans run_study.py.
        try:
            benchmark_engine.enrich_metrics(study.metrics, study.country)
        except Exception:
            pass  # jamais bloquant

        manifest = precompute_slide_values(study, manifest)

        return manifest


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
