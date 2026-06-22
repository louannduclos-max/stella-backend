from app.api.schemas.common import Study
from app.core.enums import ConfidenceGrade, FreshnessLevel, GeoLevel, SourceType
from app.core.score_config import DEFAULT_METRIC_BASELINES
from app.services.collectors.base import BaseCollector
from app.services.external.france_travail_api import france_travail
from app.services.external.sepe_api import sepe_api


class EmploymentCollector(BaseCollector):
    theme_id = "employment"
    supported_countries = {"FR", "ES"}

    def collect(self, study: Study):
        country = study.country
        if country == "FR":
            return self._collect_fr(study)
        if country == "ES":
            return self._collect_es(study)
        return [], []

    def _collect_fr(self, study: Study):
        code_insee = study.geo_scope.municipality_code
        live = france_travail.fetch_local_employment(code_insee)

        src = self._new_source(
            country="FR",
            title="France Travail - stats offres & demandes d'emploi",
            url="https://api.francetravail.io/",
            publisher="France Travail",
            source_type=SourceType.SEMI_OFFICIAL,
            authority_level=2,
            freshness=FreshnessLevel.QUARTERLY,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=ConfidenceGrade.A if live else ConfidenceGrade.C,
        )

        if live:
            unemp = float(live.get("unemployment_rate") or DEFAULT_METRIC_BASELINES["unemployment_rate"])
            pool = int(live.get("care_worker_pool") or DEFAULT_METRIC_BASELINES["care_worker_pool"])
            seekers = int(live.get("jobseekers_service_sector") or DEFAULT_METRIC_BASELINES["jobseekers_service_sector"])
            fallback = False
            note = "Données France Travail live."
            grade = ConfidenceGrade.B
        else:
            unemp = DEFAULT_METRIC_BASELINES["unemployment_rate"]
            pool = DEFAULT_METRIC_BASELINES["care_worker_pool"]
            seekers = DEFAULT_METRIC_BASELINES["jobseekers_service_sector"]
            fallback = True
            note = "France Travail non branché (OAuth requis) - baseline appliquée."
            grade = ConfidenceGrade.D

        metrics = [
            self._new_metric("unemployment_rate", "Taux de chômage",
                unemp, "%", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("care_worker_pool", "Vivier care/services",
                pool, "personnes", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("jobseekers_service_sector", "Demandeurs services",
                seekers, "personnes", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id], grade,
                fallback=fallback, fallback_note=note),
        ]
        return metrics, [src]

    def _collect_es(self, study: Study):
        municipio = study.geo_scope.municipality_code
        live = sepe_api.fetch_local_paro(municipio)

        src = self._new_source(
            country="ES",
            title="SEPE - Servicio Público de Empleo Estatal",
            url="https://www.sepe.es/",
            publisher="SEPE / datos.gob.es",
            source_type=SourceType.OFFICIAL_NATIONAL,
            authority_level=1,
            freshness=FreshnessLevel.MONTHLY,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=ConfidenceGrade.A if live else ConfidenceGrade.C,
        )

        if live:
            unemp = float(live.get("paro_rate") or DEFAULT_METRIC_BASELINES["unemployment_rate"])
            pool = int(live.get("care_pool") or DEFAULT_METRIC_BASELINES["care_worker_pool"])
            seekers = int(live.get("service_seekers") or DEFAULT_METRIC_BASELINES["jobseekers_service_sector"])
            fallback = False
            note = "Données SEPE live."
            grade = ConfidenceGrade.B
        else:
            unemp = DEFAULT_METRIC_BASELINES["unemployment_rate"]
            pool = DEFAULT_METRIC_BASELINES["care_worker_pool"]
            seekers = DEFAULT_METRIC_BASELINES["jobseekers_service_sector"]
            fallback = True
            note = "SEPE non branché (datos.gob.es à câbler V2) - baseline appliquée."
            grade = ConfidenceGrade.D

        metrics = [
            self._new_metric("unemployment_rate", "Tasa de paro",
                unemp, "%", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("care_worker_pool", "Bolsa cuidadores/servicios",
                pool, "personas", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("jobseekers_service_sector", "Demandantes servicios",
                seekers, "personas", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id], grade,
                fallback=fallback, fallback_note=note),
        ]
        return metrics, [src]
