from app.api.schemas.common import Metric, Source, Study
from app.services.collectors import ACTIVE_COLLECTORS


class ConsolidationEngine:
    def collect_all(self, study: Study) -> tuple[list[Metric], list[Source]]:
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
