from app.api.schemas.common import Study
from app.core.enums import ConfidenceGrade, FreshnessLevel, GeoLevel, SourceType
from app.core.regulation_registry import (
    ES_REGULATION_BY_REGION,
    ES_REGULATION_DEFAULT,
    FR_APA_TARIFS,
    FR_PUBLIC_AID_BY_DEPT,
    FR_PUBLIC_AID_DEFAULT,
    FR_REGULATORY_BARRIER_BY_DEPT,
    FR_REGULATORY_BARRIER_DEFAULT,
)
from app.core.score_config import DEFAULT_METRIC_BASELINES
from app.services.collectors.base import BaseCollector


class RegulationCollector(BaseCollector):
    theme_id = "regulation"
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
        apa_rate = FR_APA_TARIFS.get(dept) if dept else None
        barrier = FR_REGULATORY_BARRIER_BY_DEPT.get(dept, FR_REGULATORY_BARRIER_DEFAULT) if dept else FR_REGULATORY_BARRIER_DEFAULT
        aid_coverage = FR_PUBLIC_AID_BY_DEPT.get(dept, FR_PUBLIC_AID_DEFAULT) if dept else FR_PUBLIC_AID_DEFAULT

        src_cd = self._new_source(
            country="FR",
            title=f"Conseil départemental {dept or '??'} - APA & autorisations SAAD",
            url="https://www.pour-les-personnes-agees.gouv.fr/beneficier-daides/lapa-domicile",
            publisher=f"CD {dept}" if dept else "Conseils départementaux",
            source_type=SourceType.OFFICIAL_REGIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.PROVINCE,
            confidence=ConfidenceGrade.B if dept else ConfidenceGrade.D,
        )
        src_nat = self._new_source(
            country="FR",
            title="service-public.fr - cadre national SAP",
            url="https://www.service-public.fr/",
            publisher="DGCS / service-public.fr",
            source_type=SourceType.OFFICIAL_NATIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.COUNTRY,
            confidence=ConfidenceGrade.A,
        )

        sids = [src_cd.source_id, src_nat.source_id]
        fallback = dept is None
        note = f"Référentiel département {dept}." if dept else "Département non résolu - baseline appliquée."
        grade = ConfidenceGrade.B if dept else ConfidenceGrade.D

        metrics = [
            self._new_metric("regulatory_barrier_level", "Barrière réglementaire",
                barrier, "indice", "latest",
                GeoLevel.PROVINCE, sids, grade, fallback=fallback, fallback_note=note),
            self._new_metric("public_aid_coverage", "Couverture aides publiques",
                aid_coverage, "indice", "latest",
                GeoLevel.PROVINCE, sids, grade, fallback=fallback, fallback_note=note),
            self._new_metric("saad_authorization_required", "Autorisation SAAD requise",
                1, "bool", "latest",
                GeoLevel.COUNTRY, [src_nat.source_id], ConfidenceGrade.A, fallback=False),
            self._new_metric("apa_hourly_rate", "Tarif APA horaire",
                apa_rate if apa_rate is not None else DEFAULT_METRIC_BASELINES["apa_hourly_rate"],
                "EUR/h", "latest",
                GeoLevel.PROVINCE, [src_cd.source_id],
                ConfidenceGrade.B if apa_rate is not None else ConfidenceGrade.D,
                fallback=apa_rate is None,
                fallback_note=note if apa_rate is None else None),
        ]
        return metrics, [src_cd, src_nat]

    def _collect_es(self, study: Study):
        region = (study.geo_scope.region or "").strip()
        province = (study.geo_scope.province or "").strip()
        key = region or province
        config = ES_REGULATION_BY_REGION.get(key) if key else None
        if not config:
            for region_name, payload in ES_REGULATION_BY_REGION.items():
                if region_name.lower() in (region.lower(), province.lower()):
                    config = payload
                    key = region_name
                    break
        if not config:
            config = ES_REGULATION_DEFAULT
            key = "default"

        src_reg = self._new_source(
            country="ES",
            title=f"Comunidad Autónoma {key} - Ley de Dependencia / SAAD",
            url="https://www.imserso.es/",
            publisher=f"Comunidad {key}" if key != "default" else "IMSERSO",
            source_type=SourceType.OFFICIAL_REGIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.REGION,
            confidence=ConfidenceGrade.B if key != "default" else ConfidenceGrade.D,
        )
        src_nat = self._new_source(
            country="ES",
            title="BOE - cadre national servicios a domicilio",
            url="https://www.boe.es/",
            publisher="BOE / IMSERSO",
            source_type=SourceType.OFFICIAL_NATIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.COUNTRY,
            confidence=ConfidenceGrade.A,
        )

        sids = [src_reg.source_id, src_nat.source_id]
        fallback = key == "default"
        note = f"Referencial comunidad {key}." if not fallback else "Comunidad no resuelta - baseline aplicada."
        grade = ConfidenceGrade.B if not fallback else ConfidenceGrade.D

        metrics = [
            self._new_metric("regulatory_barrier_level", "Barrera reglamentaria",
                config["barrier"], "indice", "latest",
                GeoLevel.REGION, sids, grade, fallback=fallback, fallback_note=note),
            self._new_metric("public_aid_coverage", "Cobertura ayudas públicas",
                config["aid_coverage"], "indice", "latest",
                GeoLevel.REGION, sids, grade, fallback=fallback, fallback_note=note),
            self._new_metric("saad_authorization_required", "Autorización SAAD requerida",
                1, "bool", "latest",
                GeoLevel.COUNTRY, [src_nat.source_id], ConfidenceGrade.A, fallback=False),
            self._new_metric("apa_hourly_rate", "Tarifa Ley Dependencia",
                config["saad_hourly_rate"], "EUR/h", "latest",
                GeoLevel.REGION, [src_reg.source_id], grade,
                fallback=fallback, fallback_note=note),
        ]
        return metrics, [src_reg, src_nat]

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
