import logging

from app.api.schemas.common import Metric, Source, Study
from app.services.collectors import ACTIVE_COLLECTORS

logger = logging.getLogger(__name__)


class ConsolidationEngine:
    def collect_all(self, study: Study) -> tuple[list[Metric], list[Source]]:
        # Enrichir geo_scope avec les données EPCI avant les collectors
        try:
            from app.services.collectors.geo_resolver import resolve_geo_zone
            geo_data = resolve_geo_zone(
                city=study.geo_scope.city,
                postal_code=study.geo_scope.postal_codes[0]
                    if study.geo_scope.postal_codes else None,
            )
            if geo_data:
                # Enrichir sans écraser les données explicitement fournies
                if geo_data.get("epci_nom") and not study.geo_scope.region:
                    study.geo_scope.region = geo_data["epci_nom"]
                if geo_data.get("commune_code") and not study.geo_scope.municipality_code:
                    study.geo_scope.municipality_code = geo_data["commune_code"]
                if geo_data.get("departement_code") and not study.geo_scope.province:
                    study.geo_scope.province = geo_data["departement_code"]
                logger.info(
                    "[geo_resolver] EPCI: %s pop=%s communes=%s dept=%s",
                    geo_data.get("epci_nom"),
                    geo_data.get("epci_population"),
                    geo_data.get("epci_nb_communes"),
                    geo_data.get("departement_nom"),
                )
        except Exception as e:
            logger.warning("[geo_resolver] Échec enrichissement géo : %s", e)
            # Ne pas faire rater le pipeline pour ça

        all_metrics: list[Metric] = []
        all_sources: list[Source] = []
        for collector in ACTIVE_COLLECTORS:
            if study.country not in collector.supported_countries:
                continue
            study.metrics = self._dedupe_metrics(all_metrics)
            metrics, sources = collector.collect(study)
            all_metrics.extend(metrics)
            all_sources.extend(sources)
        return self._dedupe_metrics(all_metrics), all_sources

    def _dedupe_metrics(self, metrics: list[Metric]) -> list[Metric]:
        seen: dict[str, Metric] = {}
        for metric in metrics:
            existing = seen.get(metric.metric_id)
            if not existing or self._is_better(metric, existing):
                seen[metric.metric_id] = metric
        return list(seen.values())

    def _is_better(self, new: Metric, old: Metric) -> bool:
        order = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4}
        return order[new.confidence_grade] < order[old.confidence_grade]


consolidation_engine = ConsolidationEngine()
