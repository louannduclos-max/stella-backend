from app.api.schemas.common import Study
from app.core.enums import ConfidenceGrade, FreshnessLevel, GeoLevel, SourceType
from app.core.pricing_registry import (
    ES_BRAND_PRICING,
    ES_PRICING_BY_REGION,
    ES_PRICING_DEFAULT,
    FR_BRAND_PRICING,
    FR_PRICING_BY_DEPT,
    FR_PRICING_DEFAULT,
)
from app.core.score_config import DEFAULT_METRIC_BASELINES
from app.services.collectors.base import BaseCollector
from app.services.external.pricing_scraper import pricing_scraper


class PricingCollector(BaseCollector):
    theme_id = "pricing"
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
        code_insee = study.geo_scope.municipality_code
        live = pricing_scraper.fetch_local_pricing("FR", code_insee)

        config = FR_PRICING_BY_DEPT.get(dept) if dept else None
        dept_known = config is not None
        if not config:
            config = FR_PRICING_DEFAULT
        if live:
            config = {**config, **live}

        cleaning, care, saad = config["cleaning"], config["care"], config["saad_regulated"]

        src_brands = self._new_source(
            country="FR",
            title="Relevés tarifs concurrents SAP FR (O2/Shiva/Apef/Vitalliance/Destia)",
            url="https://www.o2.fr/services-personne-tarifs",
            publisher="Concurrents franchisés",
            source_type=SourceType.COMMERCIAL,
            authority_level=3,
            freshness=FreshnessLevel.QUARTERLY,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=ConfidenceGrade.B if dept_known else ConfidenceGrade.D,
        )
        src_cd = self._new_source(
            country="FR",
            title=f"CD {dept or '??'} - Tarif SAAD conventionné",
            url="https://www.pour-les-personnes-agees.gouv.fr/",
            publisher=f"CD {dept}" if dept else "Conseils départementaux",
            source_type=SourceType.OFFICIAL_REGIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.PROVINCE,
            confidence=ConfidenceGrade.B if dept_known else ConfidenceGrade.D,
        )

        sids = [src_brands.source_id, src_cd.source_id]
        fallback = not dept_known
        note = f"Grille tarifaire département {dept}." if dept_known else "Département non résolu - baseline appliquée."
        grade = ConfidenceGrade.B if dept_known else ConfidenceGrade.D

        metrics = [
            self._new_metric("avg_hourly_price_cleaning", "Prix horaire ménage",
                cleaning, "EUR/h", "latest",
                GeoLevel.MUNICIPALITY, [src_brands.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("avg_hourly_price_care", "Prix horaire aide à domicile",
                care, "EUR/h", "latest",
                GeoLevel.MUNICIPALITY, [src_brands.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("regulated_saad_rate", "Tarif SAAD conventionné",
                saad, "EUR/h", "latest",
                GeoLevel.PROVINCE, [src_cd.source_id], grade,
                fallback=fallback, fallback_note=note),
        ]
        return metrics, [src_brands, src_cd]

    def _collect_es(self, study: Study):
        region = (study.geo_scope.region or study.geo_scope.province or "").strip()
        live = pricing_scraper.fetch_local_pricing("ES", study.geo_scope.municipality_code)

        config = ES_PRICING_BY_REGION.get(region)
        key = region if config else None
        if not config and region:
            needle = region.lower()
            for name, payload in ES_PRICING_BY_REGION.items():
                if name.lower() in needle or needle in name.lower():
                    config = payload
                    key = name
                    break
        if not config:
            config = ES_PRICING_DEFAULT
            key = "default"
        if live:
            config = {**config, **live}

        cleaning, care, saad = config["cleaning"], config["care"], config["saad_regulated"]
        fallback = key == "default"
        note = f"Tarifas comunidad {key}." if not fallback else "Comunidad no resuelta - baseline aplicada."
        grade = ConfidenceGrade.B if not fallback else ConfidenceGrade.D

        src_brands = self._new_source(
            country="ES",
            title="Relevés tarifas concurrentes (Interdomicilio/Eulen/Clece/Serhogarsystem)",
            url="https://www.interdomicilio.com/",
            publisher="Concurrentes ES",
            source_type=SourceType.COMMERCIAL,
            authority_level=3,
            freshness=FreshnessLevel.QUARTERLY,
            coverage=GeoLevel.REGION,
            confidence=grade,
        )
        src_imserso = self._new_source(
            country="ES",
            title=f"IMSERSO - Tarifa Ley Dependencia comunidad {key}",
            url="https://www.imserso.es/",
            publisher=f"Comunidad {key}" if key != "default" else "IMSERSO",
            source_type=SourceType.OFFICIAL_REGIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.REGION,
            confidence=grade,
        )

        metrics = [
            self._new_metric("avg_hourly_price_cleaning", "Precio hora limpieza",
                cleaning, "EUR/h", "latest",
                GeoLevel.REGION, [src_brands.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("avg_hourly_price_care", "Precio hora ayuda a domicilio",
                care, "EUR/h", "latest",
                GeoLevel.REGION, [src_brands.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("regulated_saad_rate", "Tarifa SAAD regulada",
                saad, "EUR/h", "latest",
                GeoLevel.REGION, [src_imserso.source_id], grade,
                fallback=fallback, fallback_note=note),
        ]
        return metrics, [src_brands, src_imserso]

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
