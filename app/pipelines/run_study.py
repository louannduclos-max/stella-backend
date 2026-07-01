from datetime import UTC, datetime

from app.api.schemas.common import FundingScale, Section, Study
from app.core.enums import StudyStatus
from app.core.national_benchmarks import benchmarks_are_stale
from app.repositories.studies_repo import studies_repo
from app.services.benchmark_engine import benchmark_engine
from app.services.consolidation_engine import consolidation_engine
from app.services.microzones_engine import microzones_engine
from app.services.qa_engine import qa_engine
from app.services.scoring_engine import scoring_engine
from app.services.section_registry import SECTION_REGISTRY
from app.services.verdict_engine import verdict_engine


# Phases visibles dans StudyGenerationStage côté front
# Doit correspondre aux DEFAULT_PHASE_LABELS dans study-generation-stage.tsx :
#   1 → Préparation du brief
#   2 → Analyse des paramètres & collecte des données
#   3 → Rédaction de l'étude
#   4 → Mise en page & visuels
#   5 → Finalisation
_PHASE_LABELS = {
    1: "Préparation du brief",
    2: "Collecte des données terrain",
    3: "Consolidation & KPIs",
    4: "Scoring & Verdict",
    5: "Génération des slides",
}


def _emit(study_id: str, phase: int, progress: int, eta: int | None = None) -> None:
    """
    Envoie un callback de progression vers le frontend (best-effort, jamais bloquant).
    study_id est l'UUID Supabase (= external_study_id passé depuis le webhook).
    """
    try:
        from app.services.progress_notifier import notify_front
        notify_front(
            study_id=study_id,
            status="processing",
            progress=progress,
            phase=phase,
            phase_total=5,
            phase_label=_PHASE_LABELS.get(phase),
            eta_seconds=eta,
        )
    except Exception:
        pass  # ne jamais bloquer le pipeline sur une erreur de callback


class StudyPipeline:
    def run(self, study_id: str) -> Study:
        study = studies_repo.get(study_id)
        if not study:
            raise ValueError("study not found")

        # Phase 1 — Préparation (progress 5 %)
        study.status = StudyStatus.QUEUED
        studies_repo.save(study)
        _emit(study_id, phase=1, progress=5, eta=240)

        # Phase 2 — Collecte (progress 20 %)
        study.status = StudyStatus.COLLECTING
        study.updated_at = datetime.now(UTC)
        _emit(study_id, phase=2, progress=20, eta=180)
        metrics, sources = consolidation_engine.collect_all(study)
        study.metrics = metrics
        study.sources = sources
        study.microzones = microzones_engine.build_snapshot(study)

        # Phase 3 — Consolidation (progress 50 %)
        study.status = StudyStatus.CONSOLIDATING
        # Enrichissement benchmark national (déterministe, jamais bloquant)
        try:
            study.metrics = benchmark_engine.enrich_metrics(study.metrics, study.country)
            if benchmarks_are_stale(datetime.now(UTC).year):
                import logging
                logging.getLogger(__name__).warning(
                    "[benchmark] Références nationales périmées (BENCHMARKS_YEAR < %d-1) — à revérifier",
                    datetime.now(UTC).year,
                )
        except Exception:
            pass  # ne jamais bloquer le pipeline sur un enrichissement
        # Barème de financement + market sizing
        try:
            from app.core.funding_scales import get_funding_scale
            from app.services.market_sizing_engine import market_sizing_engine
            scale_data = get_funding_scale(study.country)
            if scale_data:
                study.funding_scale = FundingScale(
                    country=study.country,
                    type=scale_data["type"],
                    source=scale_data["source"],
                    year=scale_data["year"],
                    scale_rows=scale_data["scale"],
                    participation=scale_data["participation"],
                )
            # market_sizing est exposé dans le manifest via master_json_builder
            study._market_sizing = market_sizing_engine.estimate(study)  # type: ignore[attr-defined]
        except Exception:
            pass  # pays sans barème défini → pas de slide financement, pas d'invention
        study.sections = [self._build_section_shell(item, metrics) for item in SECTION_REGISTRY]
        _emit(study_id, phase=3, progress=50, eta=90)

        # Phase 4 — Scoring + narratifs LLM (progress 75 %)
        study.status = StudyStatus.SCORING
        study.scores = scoring_engine.compute_scores(metrics)
        study.verdict = verdict_engine.derive(study.scores)
        # Sprint 4 Lot C : narratifs analytiques (Gemini si GEMINI_API_KEY, sinon template)
        try:
            from app.services.gemini_analyst import generate_narratives
            study.narratives = generate_narratives(study)
        except Exception:
            pass  # ne jamais bloquer le pipeline sur une erreur de narrative
        _emit(study_id, phase=4, progress=75, eta=45)

        # Phase 5 — Génération des slides (progress 90 %)
        study.status = StudyStatus.GENERATING
        study.qa_results = qa_engine.run(study)
        _emit(study_id, phase=5, progress=90, eta=15)

        has_blocking = any(
            item.severity == "blocking" and item.status == "fail"
            for item in study.qa_results
        )
        study.status = StudyStatus.QA_FAILED if has_blocking else StudyStatus.READY
        study.updated_at = datetime.now(UTC)
        studies_repo.save(study)
        return study

    def _build_section_shell(self, item: dict, metrics) -> Section:
        attached = [m.metric_id for m in metrics if m.metric_id in item["expected_kpis"]]
        slots = {key: None for key in item["slot_contract"].keys()}
        slots["_attached_metrics"] = attached
        return Section(
            section_id=item["section_id"],
            display_name=item["display_name"],
            priority=item["priority"],
            required=item["required"],
            component_main=item["component_main"],
            component_fallback=item["component_fallback"],
            render_types=item["render_types"],
            slot_contract=item["slot_contract"],
            expected_kpis=item["expected_kpis"],
            slots=slots,
            citations=[],
            qa_status="pending",
        )


study_pipeline = StudyPipeline()
