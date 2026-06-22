from app.api.schemas.common import Study
from app.core.enums import ConfidenceGrade, FreshnessLevel, GeoLevel, SourceType
from app.core.score_config import DEFAULT_METRIC_BASELINES
from app.services.collectors.base import BaseCollector
from app.services.external.geo_api_gouv import geo_api_gouv
from app.services.external.ine_geo import ine_geo


class DemographyCollector(BaseCollector):
    theme_id = "demography"
    supported_countries = {"FR", "ES"}

    def collect(self, study: Study):
        country = study.country
        if country == "FR":
            return self._collect_fr(study)
        if country == "ES":
            return self._collect_es(study)
        return [], []

    def _collect_fr(self, study: Study):
        postal = study.geo_scope.postal_codes[0] if study.geo_scope.postal_codes else None
        commune = geo_api_gouv.resolve_commune(study.geo_scope.city, postal)

        src = self._new_source(
            country="FR",
            title="API Découpage administratif - geo.api.gouv.fr (INSEE)",
            url="https://geo.api.gouv.fr/communes",
            publisher="Etalab / INSEE",
            source_type=SourceType.OFFICIAL_NATIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=ConfidenceGrade.A if commune else ConfidenceGrade.C,
        )

        if commune:
            population = int(commune.get("population") or DEFAULT_METRIC_BASELINES["population_total"])
            surface_km2 = float(commune.get("surface") or 100) / 100
            density = round(population / surface_km2, 1) if surface_km2 > 0 else DEFAULT_METRIC_BASELINES["density_population"]
            fallback = False
            note = None
            study.geo_scope.municipality_code = commune.get("code") or study.geo_scope.municipality_code
        else:
            population = DEFAULT_METRIC_BASELINES["population_total"]
            density = DEFAULT_METRIC_BASELINES["density_population"]
            fallback = True
            note = "Commune non résolue via geo.api.gouv.fr - baseline appliquée."

        metrics = [
            self._new_metric("population_total", "Population totale",
                population, "habitants", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id],
                ConfidenceGrade.A if not fallback else ConfidenceGrade.C,
                fallback=fallback, fallback_note=note),
            self._new_metric("population_growth_5y", "Croissance population 5 ans",
                DEFAULT_METRIC_BASELINES["population_growth_5y"], "%", "5y",
                GeoLevel.MUNICIPALITY, [src.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("density_population", "Densité de population",
                density, "hab/km²", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id],
                ConfidenceGrade.A if not fallback else ConfidenceGrade.C,
                fallback=fallback),
        ]
        return metrics, [src]

    def _collect_es(self, study: Study):
        municipio = ine_geo.resolve_municipio(study.geo_scope.city, study.geo_scope.province)

        src = self._new_source(
            country="ES",
            title="INE - Cifras de población municipal (API JSON)",
            url="https://servicios.ine.es/wstempus/js/ES/MUNICIPIOS",
            publisher="INE",
            source_type=SourceType.OFFICIAL_NATIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=ConfidenceGrade.A if municipio else ConfidenceGrade.C,
        )

        if municipio:
            code = municipio.get("Codigo") or municipio.get("Id")
            if code:
                study.geo_scope.municipality_code = str(code)
            fallback = False
            note = "Municipio résolu via INE."
        else:
            fallback = True
            note = "Municipio non résolu via INE - baseline appliquée."

        population = DEFAULT_METRIC_BASELINES["population_total"]
        density = DEFAULT_METRIC_BASELINES["density_population"]

        metrics = [
            self._new_metric("population_total", "Population totale",
                population, "habitants", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id],
                ConfidenceGrade.C, fallback=True, fallback_note=note),
            self._new_metric("population_growth_5y", "Croissance population 5 ans",
                DEFAULT_METRIC_BASELINES["population_growth_5y"], "%", "5y",
                GeoLevel.MUNICIPALITY, [src.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("density_population", "Densité de population",
                density, "hab/km²", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id], ConfidenceGrade.C, fallback=True),
        ]
        return metrics, [src]
