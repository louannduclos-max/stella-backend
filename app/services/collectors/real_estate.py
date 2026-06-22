from app.api.schemas.common import Study
from app.core.enums import ConfidenceGrade, FreshnessLevel, GeoLevel, SourceType
from app.core.score_config import DEFAULT_METRIC_BASELINES
from app.services.collectors.base import BaseCollector
from app.services.external.dvf_api import dvf_api
from app.services.external.geo_api_gouv import geo_api_gouv
from app.services.external.idealista_api import idealista_api
from app.services.external.meilleurs_agents_api import meilleurs_agents


class RealEstateCollector(BaseCollector):
    theme_id = "real_estate"
    supported_countries = {"FR", "ES"}

    def collect(self, study: Study):
        country = study.country
        if country == "FR":
            return self._collect_fr(study)
        if country == "ES":
            return self._collect_es(study)
        return [], []

    def _collect_fr(self, study: Study):
        code_insee = study.geo_scope.municipality_code
        if not code_insee:
            postal = study.geo_scope.postal_codes[0] if study.geo_scope.postal_codes else None
            commune = geo_api_gouv.resolve_commune(study.geo_scope.city, postal)
            if commune:
                code_insee = commune.get("code")

        dvf_stats = dvf_api.fetch_commune_stats(code_insee) if code_insee else None
        rent_live = meilleurs_agents.fetch_rental_price_m2(study.geo_scope.city, code_insee)

        src_dvf = self._new_source(
            country="FR",
            title="DVF - Demandes de Valeurs Foncières (data.gouv.fr)",
            url="https://app.dvf.etalab.gouv.fr/",
            publisher="data.gouv.fr / Etalab",
            source_type=SourceType.OFFICIAL_NATIONAL,
            authority_level=1,
            freshness=FreshnessLevel.QUARTERLY,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=ConfidenceGrade.A if dvf_stats else ConfidenceGrade.C,
        )
        src_market = self._new_source(
            country="FR",
            title="MeilleursAgents - loyers & prix marché",
            url="https://www.meilleursagents.com/",
            publisher="MeilleursAgents",
            source_type=SourceType.COMMERCIAL,
            authority_level=3,
            freshness=FreshnessLevel.MONTHLY,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=ConfidenceGrade.A if rent_live else ConfidenceGrade.D,
        )

        sids = [src_dvf.source_id, src_market.source_id]

        if dvf_stats:
            house = dvf_stats.get("house_price_m2") or DEFAULT_METRIC_BASELINES["real_estate_price_house_m2"]
            apt = dvf_stats.get("apartment_price_m2") or DEFAULT_METRIC_BASELINES["real_estate_price_apartment_m2"]
            transactions = dvf_stats.get("transactions_count") or 0
            fallback_price = False
            note_price = f"DVF agrégé sur {transactions} transactions commune INSEE {code_insee}."
            grade_price = ConfidenceGrade.B
        else:
            house = DEFAULT_METRIC_BASELINES["real_estate_price_house_m2"]
            apt = DEFAULT_METRIC_BASELINES["real_estate_price_apartment_m2"]
            fallback_price = True
            note_price = "DVF non résolu - baseline appliquée."
            grade_price = ConfidenceGrade.D

        if rent_live and rent_live.get("rental_price_m2"):
            rent = float(rent_live["rental_price_m2"])
            fallback_rent = False
            note_rent = "MeilleursAgents live."
            grade_rent = ConfidenceGrade.B
        else:
            rent = DEFAULT_METRIC_BASELINES["rental_price_m2"]
            fallback_rent = True
            note_rent = "MeilleursAgents non branché (API privée) - baseline appliquée."
            grade_rent = ConfidenceGrade.D

        metrics = [
            self._new_metric("real_estate_price_house_m2", "Prix maisons au m²",
                round(house, 1), "EUR/m²", "latest",
                GeoLevel.MUNICIPALITY, [src_dvf.source_id], grade_price,
                fallback=fallback_price, fallback_note=note_price),
            self._new_metric("real_estate_price_apartment_m2", "Prix appartements au m²",
                round(apt, 1), "EUR/m²", "latest",
                GeoLevel.MUNICIPALITY, [src_dvf.source_id], grade_price,
                fallback=fallback_price, fallback_note=note_price),
            self._new_metric("real_estate_avg_transaction", "Prix moyen transaction",
                DEFAULT_METRIC_BASELINES["real_estate_avg_transaction"], "EUR", "latest",
                GeoLevel.MUNICIPALITY, sids, ConfidenceGrade.C, fallback=True),
            self._new_metric("rental_price_m2", "Loyer moyen au m²",
                round(rent, 2), "EUR/m²/mois", "latest",
                GeoLevel.MUNICIPALITY, [src_market.source_id], grade_rent,
                fallback=fallback_rent, fallback_note=note_rent),
            self._new_metric("real_estate_price_growth_5y", "Évolution prix immo 5 ans",
                DEFAULT_METRIC_BASELINES["real_estate_price_growth_5y"], "%", "5y",
                GeoLevel.MUNICIPALITY, sids, ConfidenceGrade.C, fallback=True),
            self._new_metric("real_estate_premium_zone_share", "Part zones premium",
                DEFAULT_METRIC_BASELINES["real_estate_premium_zone_share"], "%", "latest",
                GeoLevel.MUNICIPALITY, sids, ConfidenceGrade.D, fallback=True),
        ]
        return metrics, [src_dvf, src_market]

    def _collect_es(self, study: Study):
        live = idealista_api.fetch_price_m2(study.geo_scope.city, study.geo_scope.province)

        src = self._new_source(
            country="ES",
            title="Idealista - índices precios vivienda",
            url="https://www.idealista.com/sala-de-prensa/informes-precio-vivienda/",
            publisher="Idealista",
            source_type=SourceType.COMMERCIAL,
            authority_level=3,
            freshness=FreshnessLevel.MONTHLY,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=ConfidenceGrade.A if live else ConfidenceGrade.C,
        )

        if live:
            house = float(live.get("house_price_m2") or DEFAULT_METRIC_BASELINES["real_estate_price_house_m2"])
            apt = float(live.get("apartment_price_m2") or DEFAULT_METRIC_BASELINES["real_estate_price_apartment_m2"])
            rent = float(live.get("rental_price_m2") or DEFAULT_METRIC_BASELINES["rental_price_m2"])
            fallback = False
            note = "Idealista live."
            grade = ConfidenceGrade.B
        else:
            house = DEFAULT_METRIC_BASELINES["real_estate_price_house_m2"]
            apt = DEFAULT_METRIC_BASELINES["real_estate_price_apartment_m2"]
            rent = DEFAULT_METRIC_BASELINES["rental_price_m2"]
            fallback = True
            note = "Idealista API privée non branchée - baseline appliquée."
            grade = ConfidenceGrade.D

        metrics = [
            self._new_metric("real_estate_price_house_m2", "Precio vivienda unifamiliar m²",
                round(house, 1), "EUR/m²", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("real_estate_price_apartment_m2", "Precio piso m²",
                round(apt, 1), "EUR/m²", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("real_estate_avg_transaction", "Precio medio transacción",
                DEFAULT_METRIC_BASELINES["real_estate_avg_transaction"], "EUR", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id], ConfidenceGrade.D, fallback=True),
            self._new_metric("rental_price_m2", "Alquiler medio m²",
                round(rent, 2), "EUR/m²/mes", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id], grade,
                fallback=fallback, fallback_note=note),
            self._new_metric("real_estate_price_growth_5y", "Evolución precios 5 años",
                DEFAULT_METRIC_BASELINES["real_estate_price_growth_5y"], "%", "5y",
                GeoLevel.MUNICIPALITY, [src.source_id], ConfidenceGrade.D, fallback=True),
            self._new_metric("real_estate_premium_zone_share", "Zonas premium %",
                DEFAULT_METRIC_BASELINES["real_estate_premium_zone_share"], "%", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id], ConfidenceGrade.D, fallback=True),
        ]
        return metrics, [src]


class MicroZonesCollector(BaseCollector):
    theme_id = "microzones"
    supported_countries = {"FR", "ES"}

    def collect(self, study: Study):
        country = study.country
        if country not in self.supported_countries:
            return [], []

        if country == "FR":
            src = self._new_source(
                country="FR",
                title="INSEE - IRIS (sous-zones communales)",
                url="https://www.insee.fr/fr/information/2017499",
                publisher="INSEE",
                source_type=SourceType.OFFICIAL_NATIONAL,
                authority_level=1,
                freshness=FreshnessLevel.ANNUAL,
                coverage=GeoLevel.MUNICIPALITY,
                confidence=ConfidenceGrade.B,
            )
        else:
            src = self._new_source(
                country="ES",
                title="INE - Secciones censales",
                url="https://www.ine.es/",
                publisher="INE",
                source_type=SourceType.OFFICIAL_NATIONAL,
                authority_level=1,
                freshness=FreshnessLevel.ANNUAL,
                coverage=GeoLevel.MUNICIPALITY,
                confidence=ConfidenceGrade.B,
            )

        src_traffic = self._new_source(
            country=country,
            title="Cartographie axes routiers & transports locaux",
            url="https://www.openstreetmap.org/",
            publisher="OpenStreetMap",
            source_type=SourceType.SEMI_OFFICIAL,
            authority_level=2,
            freshness=FreshnessLevel.MONTHLY,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=ConfidenceGrade.C,
        )

        src_ids = [src.source_id, src_traffic.source_id]

        metrics = [
            self._new_metric("neighborhood_count", "Quartiers analysés",
                DEFAULT_METRIC_BASELINES["neighborhood_count"], "quartiers", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("premium_neighborhoods_count", "Quartiers premium",
                DEFAULT_METRIC_BASELINES["premium_neighborhoods_count"], "quartiers", "latest",
                GeoLevel.MUNICIPALITY, src_ids, ConfidenceGrade.D, fallback=True),
            self._new_metric("key_streets_count", "Rues clés",
                DEFAULT_METRIC_BASELINES["key_streets_count"], "rues", "latest",
                GeoLevel.MUNICIPALITY, src_ids, ConfidenceGrade.D, fallback=True),
            self._new_metric("main_traffic_axes", "Axes routiers structurants",
                DEFAULT_METRIC_BASELINES["main_traffic_axes"], "axes", "latest",
                GeoLevel.MUNICIPALITY, [src_traffic.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("transit_lines_count", "Lignes transports en commun",
                DEFAULT_METRIC_BASELINES["transit_lines_count"], "lignes", "latest",
                GeoLevel.MUNICIPALITY, [src_traffic.source_id], ConfidenceGrade.C, fallback=True),
        ]
        return metrics, [src, src_traffic]
