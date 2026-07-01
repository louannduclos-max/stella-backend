from datetime import datetime
from uuid import uuid4

from app.api.schemas.common import QAResult, Study
from app.core.enums import ConfidenceGrade, QASeverity


CRITICAL_KPIS = [
    "population_total",
    "seniors_60_plus_share",
    "median_income",
    "unemployment_rate",
    "competitor_count_15min",
    "real_estate_price_house_m2",
    "regulatory_barrier_level",
]


KPI_RANGES = {
    "population_total": (50, 20_000_000),
    "population_growth_5y": (-30, 50),
    "density_population": (0, 50_000),
    "seniors_60_plus_share": (5, 70),
    "seniors_75_plus_share": (2, 40),
    "households_with_children_share": (5, 70),
    "unemployment_rate": (0, 40),
    "median_income": (8_000, 80_000),
    "taxable_households_share": (10, 95),
    "home_ownership_share": (10, 95),
    "tenants_share": (5, 90),
    "real_estate_price_house_m2": (300, 30_000),
    "real_estate_price_apartment_m2": (300, 30_000),
    "rental_price_m2": (3, 80),
    "real_estate_price_growth_5y": (-30, 100),
    "competitor_count_15min": (0, 500),
    "competitor_count_30min": (0, 1_500),
    "franchise_brand_count": (0, 50),
    "apa_hourly_rate": (10, 40),
    "regulated_saad_rate": (10, 40),
    "avg_hourly_price_cleaning": (10, 60),
    "avg_hourly_price_care": (15, 80),
}


class QAEngine:
    def run(self, study: Study) -> list[QAResult]:
        results: list[QAResult] = []

        if not study.geo_scope.city:
            results.append(self._fail("DATA_001", "Ville absente dans geo_scope",
                "Renseigner une ville valide avant exécution."))

        if not study.sections:
            results.append(self._fail("SEC_001", "Aucune section générée",
                "Construire le shell canonique des sections avant rendu."))

        for section in study.sections:
            if section.required and not section.slot_contract:
                results.append(self._fail("SEC_002",
                    f"Contrat de slots absent pour {section.section_id}",
                    "Définir un slot_contract complet dans le registry.",
                    section_id=section.section_id))
            if (section.required and not section.expected_kpis
                    and section.section_id not in {"methodology_sources", "market_scorecard", "verdict", "action_plan"}):
                results.append(self._warn("SEC_003",
                    f"Aucun KPI attendu défini pour {section.section_id}",
                    "Rattacher les KPI canoniques à la section.",
                    section_id=section.section_id))

        if not study.scores or len(study.scores) != 7:
            results.append(self._fail("SCR_001",
                "Le scorecard Stella doit contenir 7 sous-scores.",
                "Initialiser les 7 sous-scores canoniques avant verdict."))

        metrics_by_id = {m.metric_id: m for m in study.metrics}

        for metric_id in CRITICAL_KPIS:
            metric = metrics_by_id.get(metric_id)
            if metric is None:
                results.append(self._fail("KPI_001",
                    f"KPI critique manquant: {metric_id}",
                    "Vérifier le collector responsable de ce KPI."))
                continue
            if metric.fallback_used and metric.confidence_grade in {ConfidenceGrade.D, ConfidenceGrade.E}:
                results.append(self._warn("KPI_002",
                    f"KPI critique {metric_id} en fallback (confiance {metric.confidence_grade.value}).",
                    "Brancher la source réelle correspondante."))

        for metric in study.metrics:
            bounds = KPI_RANGES.get(metric.metric_id)
            if not bounds:
                continue
            try:
                value = float(metric.value)
            except (TypeError, ValueError):
                continue
            lo, hi = bounds
            if value < lo or value > hi:
                results.append(self._fail("KPI_003",
                    f"Valeur hors plage pour {metric.metric_id}: {value} (attendu {lo}-{hi}).",
                    "Vérifier la source ou la formule du collector."))

        for score in study.scores:
            if score.value < 0 or score.value > 100:
                results.append(self._fail("SCR_002",
                    f"Score {score.score_id} hors borne 0-100 ({score.value}).",
                    "Recalibrer le scoring_engine."))

        if study.verdict is None:
            results.append(self._fail("VRD_001",
                "Verdict non calculé",
                "Exécuter verdict_engine après scoring."))

        # ─── QA Data-Depth : cohérence des nouvelles données enrichies ────────
        for metric in study.metrics:
            if metric.national_benchmark is not None and not metric.benchmark_source_id:
                results.append(self._warn("BENCH_001",
                    f"Métrique {metric.metric_id} : benchmark sans source_id.",
                    "Vérifier national_benchmarks.py — chaque valeur doit porter sa source."))

        if study.funding_scale and study.funding_scale.country != study.country:
            results.append(self._fail("FUND_001",
                f"Barème de financement ({study.funding_scale.country}) différent du pays de l'étude ({study.country}).",
                "Ne jamais afficher un barème d'un pays différent de l'étude."))

        if not results:
            results.append(self._build_result(
                test_id="QA_OK",
                severity=QASeverity.WARNING,
                status="pass",
                message="QA métier OK - contrats, KPI critiques, ranges, scores, verdict validés.",
                remediation="Aucune action immédiate.",
            ))

        return results

    def _fail(self, test_id: str, message: str, remediation: str, section_id: str | None = None) -> QAResult:
        return self._build_result(test_id, QASeverity.BLOCKING, "fail", message, remediation, section_id)

    def _warn(self, test_id: str, message: str, remediation: str, section_id: str | None = None) -> QAResult:
        return self._build_result(test_id, QASeverity.WARNING, "warning", message, remediation, section_id)

    def _build_result(
        self,
        test_id: str,
        severity: QASeverity,
        status: str,
        message: str,
        remediation: str,
        section_id: str | None = None,
    ) -> QAResult:
        return QAResult(
            qa_id=f"qa_{uuid4().hex[:8]}",
            test_id=test_id,
            severity=severity,
            status=status,
            message=message,
            section_id=section_id,
            remediation=remediation,
        )


qa_engine = QAEngine()
