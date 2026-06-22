from app.api.schemas.common import Study
from app.core.enums import ConfidenceGrade, FreshnessLevel, GeoLevel, SourceType
from app.core.score_config import DEFAULT_METRIC_BASELINES
from app.core.seniors_registry import (
    ES_SAAD_BENEFICIARIES_BY_REGION,
    ES_SAAD_DEFAULT,
    FR_APA_RATE_DEFAULT,
    FR_APA_RATE_PER_1000_75PLUS,
    FR_SINGLE_SENIOR_SHARE_BY_DEPT,
    FR_SINGLE_SENIOR_SHARE_DEFAULT,
)
from app.services.collectors.base import BaseCollector
from app.services.external.cnsa_api import cnsa_api
from app.services.external.imserso_api import imserso_api


class TargetSegmentsCollector(BaseCollector):
    theme_id = "target_segments"
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
        live = cnsa_api.fetch_apa_dept(dept)
        population = self._lookup_population(study)

        src_insee = self._new_source(
            country="FR",
            title="INSEE - Ménages & âges (commune)",
            url="https://www.insee.fr/fr/statistiques",
            publisher="INSEE",
            source_type=SourceType.OFFICIAL_NATIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=ConfidenceGrade.B,
        )
        src_cnsa = self._new_source(
            country="FR",
            title=f"CNSA - Bénéficiaires APA département {dept or '??'}",
            url="https://www.cnsa.fr/grands-chantiers/donnees-statistiques",
            publisher=f"CNSA / CD {dept}" if dept else "CNSA",
            source_type=SourceType.OFFICIAL_REGIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.PROVINCE,
            confidence=ConfidenceGrade.B if dept else ConfidenceGrade.D,
        )

        seniors_60 = DEFAULT_METRIC_BASELINES["seniors_60_plus_share"]
        seniors_75 = DEFAULT_METRIC_BASELINES["seniors_75_plus_share"]

        apa_rate = (live or {}).get("rate_per_1000_75plus") if live else FR_APA_RATE_PER_1000_75PLUS.get(dept)
        if apa_rate is None:
            apa_rate = FR_APA_RATE_DEFAULT
            apa_fallback = True
            apa_note = "Département non résolu ou hors registre - taux APA national appliqué."
            apa_grade = ConfidenceGrade.D
        else:
            apa_fallback = False
            apa_note = f"CNSA - {apa_rate}‰ bénéficiaires APA / 75+ département {dept}."
            apa_grade = ConfidenceGrade.B

        seniors_75_count = population * (seniors_75 / 100)
        dependency_apa = int(round(seniors_75_count * (apa_rate / 1000)))

        single_share = FR_SINGLE_SENIOR_SHARE_BY_DEPT.get(dept, FR_SINGLE_SENIOR_SHARE_DEFAULT) if dept else FR_SINGLE_SENIOR_SHARE_DEFAULT
        avg_household_size = 2.2
        total_households = population / avg_household_size if population > 0 else 0
        single_seniors = int(round(total_households * (single_share / 100)))

        metrics = [
            self._new_metric("seniors_60_plus_share", "Part 60+",
                seniors_60, "%", "latest",
                GeoLevel.MUNICIPALITY, [src_insee.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("seniors_75_plus_share", "Part 75+",
                seniors_75, "%", "latest",
                GeoLevel.MUNICIPALITY, [src_insee.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("single_senior_households", "Ménages seniors seuls",
                single_seniors if single_seniors > 0 else DEFAULT_METRIC_BASELINES["single_senior_households"],
                "ménages", "latest",
                GeoLevel.MUNICIPALITY, [src_insee.source_id],
                ConfidenceGrade.C if dept else ConfidenceGrade.D,
                fallback=dept is None or single_seniors == 0,
                fallback_note=f"Estimé via part ménages seniors seuls dépt {dept} = {single_share}%." if dept else "Baseline appliquée."),
            self._new_metric("households_with_children_share", "Ménages avec enfants",
                DEFAULT_METRIC_BASELINES["households_with_children_share"], "%", "latest",
                GeoLevel.MUNICIPALITY, [src_insee.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("working_age_women_share", "Femmes 25-54",
                DEFAULT_METRIC_BASELINES["working_age_women_share"], "%", "latest",
                GeoLevel.MUNICIPALITY, [src_insee.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("dependency_ratio_apa", "Bénéficiaires APA estimés",
                dependency_apa if dependency_apa > 0 else DEFAULT_METRIC_BASELINES["dependency_ratio_apa"],
                "personnes", "latest",
                GeoLevel.MUNICIPALITY, [src_cnsa.source_id, src_insee.source_id],
                apa_grade,
                fallback=apa_fallback or dependency_apa == 0,
                fallback_note=apa_note),
        ]
        return metrics, [src_insee, src_cnsa]

    def _collect_es(self, study: Study):
        region = (study.geo_scope.region or study.geo_scope.province or "").strip()
        live = imserso_api.fetch_saad_region(region)
        config = None
        key = None
        if region:
            config = ES_SAAD_BENEFICIARIES_BY_REGION.get(region)
            if config:
                key = region
            else:
                needle = region.lower()
                for name, payload in ES_SAAD_BENEFICIARIES_BY_REGION.items():
                    if name.lower() in needle or needle in name.lower():
                        config = payload
                        key = name
                        break
        if not config:
            config = ES_SAAD_DEFAULT
            key = "default"
        if live:
            config = {**config, **live}

        population = self._lookup_population(study)

        src_ine = self._new_source(
            country="ES",
            title="INE - Hogares & edades (municipio)",
            url="https://www.ine.es/",
            publisher="INE",
            source_type=SourceType.OFFICIAL_NATIONAL,
            authority_level=1,
            freshness=FreshnessLevel.ANNUAL,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=ConfidenceGrade.B,
        )
        src_imserso = self._new_source(
            country="ES",
            title=f"IMSERSO - SAAD comunidad {key}",
            url="https://www.imserso.es/dependencia-y-discapacidad/saad",
            publisher=f"IMSERSO / {key}" if key != "default" else "IMSERSO",
            source_type=SourceType.OFFICIAL_REGIONAL,
            authority_level=1,
            freshness=FreshnessLevel.QUARTERLY,
            coverage=GeoLevel.REGION,
            confidence=ConfidenceGrade.B if key != "default" else ConfidenceGrade.D,
        )

        seniors_60 = DEFAULT_METRIC_BASELINES["seniors_60_plus_share"]
        seniors_75 = DEFAULT_METRIC_BASELINES["seniors_75_plus_share"]
        seniors_65_share = (seniors_60 + seniors_75) / 2

        seniors_65_count = population * (seniors_65_share / 100)
        dependency_saad = int(round(seniors_65_count * (config["rate_per_1000_65plus"] / 1000)))

        avg_household_size = 2.5
        total_households = population / avg_household_size if population > 0 else 0
        single_seniors = int(round(total_households * (config["single_senior_share"] / 100)))

        fallback = key == "default"
        note = f"IMSERSO comunidad {key}." if not fallback else "Comunidad no resuelta - baseline aplicada."
        grade = ConfidenceGrade.B if not fallback else ConfidenceGrade.D

        metrics = [
            self._new_metric("seniors_60_plus_share", "Mayores 60+",
                seniors_60, "%", "latest",
                GeoLevel.MUNICIPALITY, [src_ine.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("seniors_75_plus_share", "Mayores 75+",
                seniors_75, "%", "latest",
                GeoLevel.MUNICIPALITY, [src_ine.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("single_senior_households", "Hogares mayores solos",
                single_seniors if single_seniors > 0 else DEFAULT_METRIC_BASELINES["single_senior_households"],
                "hogares", "latest",
                GeoLevel.MUNICIPALITY, [src_ine.source_id, src_imserso.source_id],
                grade,
                fallback=fallback or single_seniors == 0,
                fallback_note=note),
            self._new_metric("households_with_children_share", "Hogares con niños",
                DEFAULT_METRIC_BASELINES["households_with_children_share"], "%", "latest",
                GeoLevel.MUNICIPALITY, [src_ine.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("working_age_women_share", "Mujeres 25-54",
                DEFAULT_METRIC_BASELINES["working_age_women_share"], "%", "latest",
                GeoLevel.MUNICIPALITY, [src_ine.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("dependency_ratio_apa", "Beneficiarios SAAD estimados",
                dependency_saad if dependency_saad > 0 else DEFAULT_METRIC_BASELINES["dependency_ratio_apa"],
                "personas", "latest",
                GeoLevel.REGION, [src_imserso.source_id, src_ine.source_id],
                grade,
                fallback=fallback or dependency_saad == 0,
                fallback_note=note),
        ]
        return metrics, [src_ine, src_imserso]

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
