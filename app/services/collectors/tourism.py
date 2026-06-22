from app.api.schemas.common import Study
from app.core.enums import ConfidenceGrade, FreshnessLevel, GeoLevel, SourceType
from app.core.score_config import DEFAULT_METRIC_BASELINES
from app.core.tourism_registry import (
    ES_TOURISM_BY_REGION,
    ES_TOURISM_DEFAULT,
    FR_HIGH_TOURISM_DEPTS,
    FR_TOURISM_BY_REGION,
    FR_TOURISM_DEFAULT,
)
from app.services.collectors.base import BaseCollector
from app.services.external.dge_api import dge_api
from app.services.external.turespana_api import turespana_api


class TourismCollector(BaseCollector):
    theme_id = "tourism"
    supported_countries = {"FR", "ES"}

    def collect(self, study: Study):
        country = study.country
        if country == "FR":
            return self._collect_fr(study)
        if country == "ES":
            return self._collect_es(study)
        return [], []

    def _collect_fr(self, study: Study):
        region = (study.geo_scope.region or "").strip()
        dept = self._resolve_dept(study)
        live = dge_api.fetch_tourism_region(region)

        config = FR_TOURISM_BY_REGION.get(region)
        key = region if config else None
        if not config and region:
            needle = region.lower()
            for name, payload in FR_TOURISM_BY_REGION.items():
                if name.lower() in needle or needle in name.lower():
                    config = payload
                    key = name
                    break
        if not config:
            config = FR_TOURISM_DEFAULT
            key = "default"
        if live:
            config = {**config, **live}

        dept_boost = FR_HIGH_TOURISM_DEPTS.get(dept) if dept else None
        if dept_boost:
            overnight_factor = dept_boost
            seasonality_index = round(min(config["seasonality_index"] * 1.2, 5.0), 2)
            revenue_multiplier = round(min(config["revenue_multiplier"] * 1.15, 2.5), 2)
            note = f"Profil touristique renforcé via département {dept}."
        else:
            overnight_factor = 1.0
            seasonality_index = config["seasonality_index"]
            revenue_multiplier = config["revenue_multiplier"]
            note = f"CRT - profil tourisme région {key}." if key != "default" else "Région non résolue - baseline appliquée."

        population = self._lookup_population(study)
        overnight_stays = int(round(population * config["overnight_stays_per_capita"] * overnight_factor))

        fallback = key == "default"
        grade = ConfidenceGrade.B if not fallback else ConfidenceGrade.D

        src_crt = self._new_source(
            country="FR",
            title=f"CRT {key} - Observatoire tourisme régional",
            url="https://www.entreprises.gouv.fr/fr/tourisme/donnees-statistiques",
            publisher=f"CRT {key}" if key != "default" else "DGE",
            source_type=SourceType.OFFICIAL_REGIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.REGION,
            confidence=grade,
        )
        src_local = self._new_source(
            country="FR",
            title=f"Office de Tourisme département {dept or '??'}",
            url="https://www.tourisme.fr/",
            publisher=f"OT département {dept}" if dept else "Offices de tourisme",
            source_type=SourceType.OFFICIAL_LOCAL,
            authority_level=2,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.PROVINCE,
            confidence=ConfidenceGrade.C,
        )

        sids = [src_crt.source_id, src_local.source_id]

        metrics = [
            self._new_metric("tourism_overnight_stays", "Nuitées touristiques",
                overnight_stays if overnight_stays > 0 else DEFAULT_METRIC_BASELINES["tourism_overnight_stays"],
                "nuitées", "annual",
                GeoLevel.MUNICIPALITY, sids, grade,
                fallback=fallback or overnight_stays == 0,
                fallback_note=note),
            self._new_metric("tourism_seasonality_index", "Indice saisonnalité",
                seasonality_index, "indice", "annual",
                GeoLevel.MUNICIPALITY, sids, grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("seasonal_revenue_multiplier", "Coef CA été/hiver",
                revenue_multiplier, "x", "annual",
                GeoLevel.MUNICIPALITY, sids, grade,
                fallback=fallback, fallback_note=note),
        ]
        return metrics, [src_crt, src_local]

    def _collect_es(self, study: Study):
        region = (study.geo_scope.region or study.geo_scope.province or "").strip()
        live = turespana_api.fetch_tourism_region(region)

        config = ES_TOURISM_BY_REGION.get(region)
        key = region if config else None
        if not config and region:
            needle = region.lower()
            for name, payload in ES_TOURISM_BY_REGION.items():
                if name.lower() in needle or needle in name.lower():
                    config = payload
                    key = name
                    break
        if not config:
            config = ES_TOURISM_DEFAULT
            key = "default"
        if live:
            config = {**config, **live}

        population = self._lookup_population(study)
        overnight_stays = int(round(population * config["overnight_stays_per_capita"]))

        fallback = key == "default"
        note = f"INE EOH / Turespaña - comunidad {key}." if not fallback else "Comunidad no resuelta - baseline aplicada."
        grade = ConfidenceGrade.B if not fallback else ConfidenceGrade.D

        src_ine = self._new_source(
            country="ES",
            title=f"INE EOH - Encuesta Ocupación Hotelera {key}",
            url="https://www.ine.es/dyngs/INEbase/es/operacion.htm?c=Estadistica_C&cid=1254736177015",
            publisher="INE",
            source_type=SourceType.OFFICIAL_NATIONAL,
            authority_level=1,
            freshness=FreshnessLevel.MONTHLY,
            coverage=GeoLevel.REGION,
            confidence=grade,
        )
        src_turespana = self._new_source(
            country="ES",
            title="Turespaña - Estadísticas turismo",
            url="https://www.tourspain.es/",
            publisher="Turespaña",
            source_type=SourceType.OFFICIAL_NATIONAL,
            authority_level=2,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.REGION,
            confidence=grade,
        )

        sids = [src_ine.source_id, src_turespana.source_id]

        metrics = [
            self._new_metric("tourism_overnight_stays", "Pernoctaciones turísticas",
                overnight_stays if overnight_stays > 0 else DEFAULT_METRIC_BASELINES["tourism_overnight_stays"],
                "pernoctaciones", "annual",
                GeoLevel.REGION, sids, grade,
                fallback=fallback or overnight_stays == 0,
                fallback_note=note),
            self._new_metric("tourism_seasonality_index", "Índice estacionalidad",
                config["seasonality_index"], "indice", "annual",
                GeoLevel.REGION, sids, grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("seasonal_revenue_multiplier", "Coef CA verano/invierno",
                config["revenue_multiplier"], "x", "annual",
                GeoLevel.REGION, sids, grade,
                fallback=fallback, fallback_note=note),
        ]
        return metrics, [src_ine, src_turespana]

    def _resolve_dept(self, study: Study) -> str | None:
        code_insee = study.geo_scope.municipality_code
        if code_insee and len(code_insee) >= 2:
            if code_insee.startswith("97") and len(code_insee) >= 3:
                return code_insee[:3]
            if code_insee[:2] in ("2A", "2B"):
                return code_insee[:2]
            return code_insee[:2]
        if study.geo_scope.postal_codes:
            postal = study.geo_scope.postal_codes[0]
            if postal and len(postal) >= 2:
                if postal.startswith("20"):
                    try:
                        n = int(postal[:5])
                        return "2A" if 20000 <= n <= 20190 else "2B"
                    except ValueError:
                        return "2A"
                return postal[:2]
        return None

    def _lookup_population(self, study: Study) -> int:
        for metric in study.metrics:
            if metric.metric_id == "population_total":
                try:
                    return int(metric.value)
                except (TypeError, ValueError):
                    return DEFAULT_METRIC_BASELINES["population_total"]
        return DEFAULT_METRIC_BASELINES["population_total"]
