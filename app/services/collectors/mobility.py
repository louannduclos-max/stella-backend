from app.api.schemas.common import Study
from app.core.enums import ConfidenceGrade, FreshnessLevel, GeoLevel, SourceType
from app.core.mobility_registry import (
    ES_CAR_DEPENDENCY_BY_REGION,
    ES_CAR_DEPENDENCY_DEFAULT,
    ES_PARKING_BY_REGION,
    ES_PARKING_DEFAULT,
    ES_RUSH_HOUR_PENALTY_BY_REGION,
    ES_RUSH_HOUR_PENALTY_DEFAULT,
    FR_CAR_DEPENDENCY_BY_DEPT,
    FR_CAR_DEPENDENCY_DEFAULT,
    FR_PARKING_BY_DEPT,
    FR_PARKING_DEFAULT,
    FR_RUSH_HOUR_PENALTY_BY_DEPT,
    FR_RUSH_HOUR_PENALTY_DEFAULT,
    TRAVEL_TIME_SPREAD_BY_DENSITY,
)
from app.core.score_config import DEFAULT_METRIC_BASELINES
from app.services.collectors.base import BaseCollector
from app.services.external.osrm_api import osrm_api


class MobilityCollector(BaseCollector):
    theme_id = "operations"
    supported_countries = {"FR", "ES"}

    def collect(self, study: Study):
        country = study.country
        if country == "FR":
            return self._collect_fr(study)
        if country == "ES":
            return self._collect_es(study)
        return [], []

    def _collect_fr(self, study: Study):
        dept = self._resolve_dept(study)
        density_level = self._density_level(study)

        car_share = FR_CAR_DEPENDENCY_BY_DEPT.get(dept, FR_CAR_DEPENDENCY_DEFAULT) if dept else FR_CAR_DEPENDENCY_DEFAULT
        rush_penalty = FR_RUSH_HOUR_PENALTY_BY_DEPT.get(dept, FR_RUSH_HOUR_PENALTY_DEFAULT) if dept else FR_RUSH_HOUR_PENALTY_DEFAULT
        parking = FR_PARKING_BY_DEPT.get(dept, FR_PARKING_DEFAULT) if dept else FR_PARKING_DEFAULT
        travel_spread = TRAVEL_TIME_SPREAD_BY_DENSITY[density_level]

        dept_known = dept is not None and dept in FR_CAR_DEPENDENCY_BY_DEPT
        fallback = not dept_known
        note = f"INSEE mobilité département {dept} - densité {density_level}." if dept_known else "Département non résolu - baseline appliquée."
        grade = ConfidenceGrade.B if dept_known else ConfidenceGrade.D

        src_insee = self._new_source(
            country="FR",
            title=f"INSEE - Mobilités domicile-travail dépt {dept or '??'}",
            url="https://www.insee.fr/fr/statistiques",
            publisher="INSEE",
            source_type=SourceType.OFFICIAL_NATIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.PROVINCE,
            confidence=grade,
        )
        src_osm = self._new_source(
            country="FR",
            title="OpenStreetMap + OSRM - axes & temps de trajet",
            url="https://www.openstreetmap.org/",
            publisher="OSM",
            source_type=SourceType.SEMI_OFFICIAL,
            authority_level=2,
            freshness=FreshnessLevel.MONTHLY,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=ConfidenceGrade.C,
        )

        sids = [src_insee.source_id, src_osm.source_id]

        metrics = [
            self._new_metric("travel_time_spread", "Dispersion trajets",
                travel_spread, "min", "latest",
                GeoLevel.MUNICIPALITY, [src_osm.source_id], ConfidenceGrade.C,
                fallback=True, fallback_note=f"Estimation via densité {density_level}."),
            self._new_metric("parking_constraint_index", "Contrainte stationnement",
                parking, "indice", "latest",
                GeoLevel.MUNICIPALITY, [src_osm.source_id, src_insee.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("car_dependency_share", "Dépendance automobile",
                car_share, "%", "latest",
                GeoLevel.PROVINCE, [src_insee.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("rush_hour_penalty", "Pénalité heures pointe",
                rush_penalty, "min", "latest",
                GeoLevel.MUNICIPALITY, sids, grade,
                fallback=fallback, fallback_note=note),
        ]
        return metrics, [src_insee, src_osm]

    def _collect_es(self, study: Study):
        region = (study.geo_scope.region or study.geo_scope.province or "").strip()
        density_level = self._density_level(study)

        car_share = ES_CAR_DEPENDENCY_BY_REGION.get(region)
        rush_penalty = ES_RUSH_HOUR_PENALTY_BY_REGION.get(region)
        parking = ES_PARKING_BY_REGION.get(region)
        key = region if car_share is not None else None

        if car_share is None and region:
            needle = region.lower()
            for name, val in ES_CAR_DEPENDENCY_BY_REGION.items():
                if name.lower() in needle or needle in name.lower():
                    car_share = val
                    rush_penalty = ES_RUSH_HOUR_PENALTY_BY_REGION.get(name, ES_RUSH_HOUR_PENALTY_DEFAULT)
                    parking = ES_PARKING_BY_REGION.get(name, ES_PARKING_DEFAULT)
                    key = name
                    break
        if car_share is None:
            car_share = ES_CAR_DEPENDENCY_DEFAULT
            rush_penalty = ES_RUSH_HOUR_PENALTY_DEFAULT
            parking = ES_PARKING_DEFAULT
            key = "default"

        travel_spread = TRAVEL_TIME_SPREAD_BY_DENSITY[density_level]
        fallback = key == "default"
        note = f"INE movilidad comunidad {key} - densidad {density_level}." if not fallback else "Comunidad no resuelta - baseline aplicada."
        grade = ConfidenceGrade.B if not fallback else ConfidenceGrade.D

        src_ine = self._new_source(
            country="ES",
            title=f"INE - Encuesta de Movilidad comunidad {key}",
            url="https://www.ine.es/",
            publisher="INE",
            source_type=SourceType.OFFICIAL_NATIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.REGION,
            confidence=grade,
        )
        src_osm = self._new_source(
            country="ES",
            title="OpenStreetMap + OSRM - axes & temps de trajet",
            url="https://www.openstreetmap.org/",
            publisher="OSM",
            source_type=SourceType.SEMI_OFFICIAL,
            authority_level=2,
            freshness=FreshnessLevel.MONTHLY,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=ConfidenceGrade.C,
        )

        sids = [src_ine.source_id, src_osm.source_id]

        metrics = [
            self._new_metric("travel_time_spread", "Dispersión trayectos",
                travel_spread, "min", "latest",
                GeoLevel.MUNICIPALITY, [src_osm.source_id], ConfidenceGrade.C,
                fallback=True, fallback_note=f"Estimación por densidad {density_level}."),
            self._new_metric("parking_constraint_index", "Restricción aparcamiento",
                parking, "indice", "latest",
                GeoLevel.MUNICIPALITY, [src_osm.source_id, src_ine.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("car_dependency_share", "Dependencia automóvil",
                car_share, "%", "latest",
                GeoLevel.REGION, [src_ine.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("rush_hour_penalty", "Penalización hora punta",
                rush_penalty, "min", "latest",
                GeoLevel.REGION, sids, grade,
                fallback=fallback, fallback_note=note),
        ]
        return metrics, [src_ine, src_osm]

    def _density_level(self, study: Study) -> str:
        density = None
        for m in study.metrics:
            if m.metric_id == "density_population":
                try:
                    density = float(m.value)
                except (TypeError, ValueError):
                    density = None
                break
        if density is None:
            return "periurban"
        if density >= 4000:
            return "very_urban"
        if density >= 1500:
            return "urban"
        if density >= 300:
            return "periurban"
        return "rural"

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


mobility_collector = MobilityCollector()
