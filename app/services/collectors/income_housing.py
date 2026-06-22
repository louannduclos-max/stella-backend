from app.api.schemas.common import Study
from app.core.enums import ConfidenceGrade, FreshnessLevel, GeoLevel, SourceType
from app.core.income_registry import (
    ES_HOME_OWNERSHIP_BY_REGION,
    ES_HOME_OWNERSHIP_DEFAULT,
    ES_MEDIAN_INCOME_BY_REGION,
    ES_MEDIAN_INCOME_DEFAULT,
    ES_TAXABLE_BY_REGION,
    ES_TAXABLE_DEFAULT,
    FR_HOME_OWNERSHIP_BY_DEPT,
    FR_HOME_OWNERSHIP_DEFAULT,
    FR_MEDIAN_INCOME_BY_DEPT,
    FR_MEDIAN_INCOME_DEFAULT,
    FR_TAXABLE_DEFAULT,
    FR_TAXABLE_HOUSEHOLDS_BY_DEPT,
)
from app.core.score_config import DEFAULT_METRIC_BASELINES
from app.services.collectors.base import BaseCollector
from app.services.external.filosofi_api import filosofi_api
from app.services.external.ine_renta_api import ine_renta_api


class IncomeHousingCollector(BaseCollector):
    theme_id = "income_housing"
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
        live = filosofi_api.fetch_commune_income(study.geo_scope.municipality_code)

        median_income = (live or {}).get("median_income") if live else FR_MEDIAN_INCOME_BY_DEPT.get(dept)
        if median_income is None:
            median_income = FR_MEDIAN_INCOME_DEFAULT
            income_fallback = True
            income_note = "Département non résolu - revenu médian national appliqué."
            income_grade = ConfidenceGrade.D
        else:
            income_fallback = False
            income_note = f"Filosofi - revenu médian département {dept}."
            income_grade = ConfidenceGrade.B

        taxable = FR_TAXABLE_HOUSEHOLDS_BY_DEPT.get(dept, FR_TAXABLE_DEFAULT) if dept else FR_TAXABLE_DEFAULT
        ownership = FR_HOME_OWNERSHIP_BY_DEPT.get(dept, FR_HOME_OWNERSHIP_DEFAULT) if dept else FR_HOME_OWNERSHIP_DEFAULT
        tenants = round(100 - ownership - 4, 1)
        dept_known = dept is not None and dept in FR_MEDIAN_INCOME_BY_DEPT
        habitat_grade = ConfidenceGrade.B if dept_known else ConfidenceGrade.D

        src_filosofi = self._new_source(
            country="FR",
            title=f"INSEE Filosofi - Revenus localisés dépt {dept or '??'}",
            url="https://www.insee.fr/fr/statistiques/2021289",
            publisher="INSEE Filosofi",
            source_type=SourceType.OFFICIAL_NATIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=income_grade,
        )
        src_recensement = self._new_source(
            country="FR",
            title="INSEE - Recensement (logement & ménages)",
            url="https://www.insee.fr/fr/statistiques",
            publisher="INSEE",
            source_type=SourceType.OFFICIAL_NATIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=habitat_grade,
        )

        metrics = [
            self._new_metric("median_income", "Revenu médian",
                median_income, "EUR", "latest",
                GeoLevel.MUNICIPALITY, [src_filosofi.source_id], income_grade,
                fallback=income_fallback, fallback_note=income_note),
            self._new_metric("taxable_households_share", "Ménages imposables",
                taxable, "%", "latest",
                GeoLevel.MUNICIPALITY, [src_filosofi.source_id], habitat_grade,
                fallback=not dept_known,
                fallback_note=f"Référentiel dépt {dept}." if dept_known else "Baseline appliquée."),
            self._new_metric("home_ownership_share", "Propriétaires occupants",
                ownership, "%", "latest",
                GeoLevel.MUNICIPALITY, [src_recensement.source_id], habitat_grade,
                fallback=not dept_known,
                fallback_note=f"Recensement dépt {dept}." if dept_known else "Baseline appliquée."),
            self._new_metric("tenants_share", "Locataires",
                tenants, "%", "latest",
                GeoLevel.MUNICIPALITY, [src_recensement.source_id], habitat_grade,
                fallback=not dept_known),
            self._new_metric("secondary_residences_share", "Résidences secondaires",
                DEFAULT_METRIC_BASELINES["secondary_residences_share"], "%", "latest",
                GeoLevel.MUNICIPALITY, [src_recensement.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("vacant_housing_share", "Logements vacants",
                DEFAULT_METRIC_BASELINES["vacant_housing_share"], "%", "latest",
                GeoLevel.MUNICIPALITY, [src_recensement.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("houses_vs_apartments_share", "Maisons vs appartements",
                DEFAULT_METRIC_BASELINES["houses_vs_apartments_share"], "%", "latest",
                GeoLevel.MUNICIPALITY, [src_recensement.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("avg_house_surface", "Surface moyenne maisons",
                DEFAULT_METRIC_BASELINES["avg_house_surface"], "m²", "latest",
                GeoLevel.MUNICIPALITY, [src_recensement.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("avg_apartment_surface", "Surface moyenne appartements",
                DEFAULT_METRIC_BASELINES["avg_apartment_surface"], "m²", "latest",
                GeoLevel.MUNICIPALITY, [src_recensement.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("avg_land_surface", "Surface moyenne terrain",
                DEFAULT_METRIC_BASELINES["avg_land_surface"], "m²", "latest",
                GeoLevel.MUNICIPALITY, [src_recensement.source_id], ConfidenceGrade.D, fallback=True),
        ]
        return metrics, [src_filosofi, src_recensement]

    def _collect_es(self, study: Study):
        region = (study.geo_scope.region or study.geo_scope.province or "").strip()
        live = ine_renta_api.fetch_municipio_renta(study.geo_scope.municipality_code)

        income_config = ES_MEDIAN_INCOME_BY_REGION.get(region)
        ownership = ES_HOME_OWNERSHIP_BY_REGION.get(region)
        taxable = ES_TAXABLE_BY_REGION.get(region)
        key = region if income_config else None

        if not income_config and region:
            needle = region.lower()
            for name, val in ES_MEDIAN_INCOME_BY_REGION.items():
                if name.lower() in needle or needle in name.lower():
                    income_config = val
                    ownership = ES_HOME_OWNERSHIP_BY_REGION.get(name, ES_HOME_OWNERSHIP_DEFAULT)
                    taxable = ES_TAXABLE_BY_REGION.get(name, ES_TAXABLE_DEFAULT)
                    key = name
                    break

        if income_config is None:
            income_config = ES_MEDIAN_INCOME_DEFAULT
            ownership = ES_HOME_OWNERSHIP_DEFAULT
            taxable = ES_TAXABLE_DEFAULT
            key = "default"

        median_income = (live or {}).get("median_income") if live else income_config
        fallback = key == "default" and not live
        note = f"INE Atlas Renta - comunidad {key}." if not fallback else "Comunidad no resuelta - baseline aplicada."
        grade = ConfidenceGrade.B if not fallback else ConfidenceGrade.D
        tenants = round(100 - ownership - 5, 1)

        src_ine_renta = self._new_source(
            country="ES",
            title=f"INE Atlas de Distribución de la Renta - {key}",
            url="https://www.ine.es/experimental/atlas/exp_atlas_tab.htm",
            publisher="INE",
            source_type=SourceType.OFFICIAL_NATIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=grade,
        )
        src_ine_censo = self._new_source(
            country="ES",
            title="INE - Censo de población y viviendas",
            url="https://www.ine.es/",
            publisher="INE",
            source_type=SourceType.OFFICIAL_NATIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=grade,
        )

        metrics = [
            self._new_metric("median_income", "Renta media",
                median_income, "EUR", "latest",
                GeoLevel.MUNICIPALITY, [src_ine_renta.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("taxable_households_share", "Hogares con renta declarada",
                taxable, "%", "latest",
                GeoLevel.MUNICIPALITY, [src_ine_renta.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("home_ownership_share", "Propietarios",
                ownership, "%", "latest",
                GeoLevel.MUNICIPALITY, [src_ine_censo.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("tenants_share", "Inquilinos",
                tenants, "%", "latest",
                GeoLevel.MUNICIPALITY, [src_ine_censo.source_id], grade,
                fallback=fallback),
            self._new_metric("secondary_residences_share", "Viviendas secundarias",
                DEFAULT_METRIC_BASELINES["secondary_residences_share"], "%", "latest",
                GeoLevel.MUNICIPALITY, [src_ine_censo.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("vacant_housing_share", "Viviendas vacías",
                DEFAULT_METRIC_BASELINES["vacant_housing_share"], "%", "latest",
                GeoLevel.MUNICIPALITY, [src_ine_censo.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("houses_vs_apartments_share", "Casas vs pisos",
                DEFAULT_METRIC_BASELINES["houses_vs_apartments_share"], "%", "latest",
                GeoLevel.MUNICIPALITY, [src_ine_censo.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("avg_house_surface", "Superficie media casas",
                DEFAULT_METRIC_BASELINES["avg_house_surface"], "m²", "latest",
                GeoLevel.MUNICIPALITY, [src_ine_censo.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("avg_apartment_surface", "Superficie media pisos",
                DEFAULT_METRIC_BASELINES["avg_apartment_surface"], "m²", "latest",
                GeoLevel.MUNICIPALITY, [src_ine_censo.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("avg_land_surface", "Superficie media terreno",
                DEFAULT_METRIC_BASELINES["avg_land_surface"], "m²", "latest",
                GeoLevel.MUNICIPALITY, [src_ine_censo.source_id], ConfidenceGrade.D, fallback=True),
        ]
        return metrics, [src_ine_renta, src_ine_censo]

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
