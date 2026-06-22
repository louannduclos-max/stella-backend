from abc import ABC, abstractmethod
from datetime import UTC, datetime
from uuid import uuid4

from app.api.schemas.common import Metric, Source, Study
from app.core.enums import ConfidenceGrade, FreshnessLevel, GeoLevel, SourceType


class BaseCollector(ABC):
    theme_id: str = ""
    supported_countries: set[str] = set()

    @abstractmethod
    def collect(self, study: Study) -> tuple[list[Metric], list[Source]]:
        ...

    def _new_source(
        self,
        country: str,
        title: str,
        url: str,
        publisher: str,
        source_type: SourceType,
        authority_level: int,
        freshness: FreshnessLevel,
        coverage: GeoLevel,
        confidence: ConfidenceGrade,
    ) -> Source:
        return Source(
            source_id=f"src_{uuid4().hex[:10]}",
            theme_id=self.theme_id,
            country=country,
            source_type=source_type,
            authority_level=authority_level,
            freshness_level=freshness,
            coverage_level=coverage,
            title=title,
            url=url,
            publisher=publisher,
            accessed_at=datetime.now(UTC),
            confidence_grade=confidence,
        )

    def _new_metric(
        self,
        metric_id: str,
        label: str,
        value,
        unit: str | None,
        period: str,
        geo_level: GeoLevel,
        source_ids: list[str],
        confidence: ConfidenceGrade,
        fallback: bool = False,
        fallback_note: str | None = None,
    ) -> Metric:
        return Metric(
            metric_id=metric_id,
            theme_id=self.theme_id,
            name=metric_id,
            label=label,
            value=value,
            unit=unit,
            period=period,
            geo_level=geo_level,
            source_ids=source_ids,
            confidence_grade=confidence,
            fallback_used=fallback,
            fallback_note=fallback_note,
        )
