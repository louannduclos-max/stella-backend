import uuid

from app.api.schemas.common import Competitor, Study
from app.core.enums import ConfidenceGrade, FreshnessLevel, GeoLevel, SourceType
from app.core.score_config import DEFAULT_METRIC_BASELINES
from app.services.collectors.base import BaseCollector
from app.services.external.geo_api_gouv import geo_api_gouv
from app.services.external.google_places_api import (
    USE_NEW_PLACES_API,
    classify_competitors,
    google_places,
    google_places_new,
)
from app.services.external.ine_geo import ine_geo


# Fix 5 — rayon élargi : 8km était trop court pour les villes moyennes/rurales
RADIUS_15MIN_M = 15000   # ~15 km / 15 min voiture
RADIUS_30MIN_M = 30000   # ~30 km / 30 min voiture


class CompetitionCollector(BaseCollector):
    theme_id = "competition"
    supported_countries = {"FR", "ES"}

    def collect(self, study: Study):
        country = study.country
        if country not in self.supported_countries:
            return [], []

        lat, lon = self._resolve_coords(study)
        city = study.geo_scope.city or ""
        live15, live30, classification15 = self._fetch_live(country, lat, lon, city=city)

        # Titre et URL distincts selon l'API utilisee (traceabilite logs)
        _src_title = (
            "Google Places API (New) - Text Search acteurs SAP"
            if USE_NEW_PLACES_API
            else "Google Places API - acteurs SAP locaux"
        )
        _src_url = (
            "https://places.googleapis.com/v1/places:searchText"
            if USE_NEW_PLACES_API
            else "https://maps.googleapis.com/maps/api/place/nearbysearch"
        )
        src = self._new_source(
            country=country,
            title=_src_title,
            url=_src_url,
            publisher="Google Places",
            source_type=SourceType.COMMERCIAL,
            authority_level=3,
            freshness=FreshnessLevel.REALTIME,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=ConfidenceGrade.A if live15 is not None else ConfidenceGrade.C,
        )
        src_assoc = self._new_source(
            country=country,
            title="Annuaire associations & CCAS" if country == "FR" else "Directorio asociaciones & ayuntamientos",
            url="https://www.admr.org/" if country == "FR" else "https://www.imserso.es/",
            publisher="ADMR / UNA / CCAS" if country == "FR" else "IMSERSO / Comunidades",
            source_type=SourceType.SEMI_OFFICIAL,
            authority_level=2,
            freshness=FreshnessLevel.QUARTERLY,
            coverage=GeoLevel.MUNICIPALITY,
            confidence=ConfidenceGrade.C,
        )

        sids = [src.source_id]

        if live15 is not None:
            count_15 = len(live15)
            count_30 = len(live30) if live30 is not None else count_15
            franchises = classification15.get("franchises", 0)
            associations = classification15.get("associations", 0)
            brand_flag = classification15.get("brand_presence_flag", 0)
            top_density_raw = round(franchises * 8 + count_15 * 1.5)
            top_density_capped = top_density_raw >= 100
            top_density = min(100, top_density_raw)
            fallback = False
            if USE_NEW_PLACES_API:
                note = (
                    f"Google Places New API (Text Search) - {count_15} acteurs. "
                    f"Sans rayon : count_30=count_15 (estimation, pas de distinction 15/30 min)."
                )
            else:
                note = f"Google Places live - {count_15} acteurs a 15 min, {count_30} a 30 min."
            grade = ConfidenceGrade.B
            # Construire la liste nommée de concurrents (Chantier 2 Data-Depth)
            brand_profile = study.brand_profile_override or {}
            direct_names = brand_profile.get("direct_competitors")
            # source_id distinct pour New API (spec : traceabilite)
            _competitor_source_id = "google_places_new" if USE_NEW_PLACES_API else src.source_id
            study.competitors = build_competitors_from_places(
                live15, direct_competitor_names=direct_names, source_id=_competitor_source_id,
            )
        else:
            count_15 = DEFAULT_METRIC_BASELINES["competitor_count_15min"]
            count_30 = DEFAULT_METRIC_BASELINES["competitor_count_30min"]
            franchises = DEFAULT_METRIC_BASELINES["franchise_brand_count"]
            associations = DEFAULT_METRIC_BASELINES["association_competitor_count"]
            brand_flag = DEFAULT_METRIC_BASELINES["brand_presence_flag"]
            top_density = DEFAULT_METRIC_BASELINES["top_competitor_density"]
            top_density_capped = False
            fallback = True
            note = "Google Places non disponible - estimation nationale appliquée."
            grade = ConfidenceGrade.D

        metrics = [
            self._new_metric("competitor_count_15min", "Concurrents 15 min",
                count_15, "acteurs", "latest",
                GeoLevel.MUNICIPALITY, sids, grade, fallback=fallback, fallback_note=note),
            self._new_metric("competitor_count_30min", "Concurrents 30 min",
                count_30, "acteurs", "latest",
                GeoLevel.MUNICIPALITY, sids, grade, fallback=fallback, fallback_note=note),
            self._new_metric("top_competitor_density", "Densité top concurrents",
                top_density, "indice", "latest",
                GeoLevel.MUNICIPALITY, sids, grade, fallback=fallback or top_density_capped,
                fallback_note=note if (fallback or top_density_capped) else None),
            self._new_metric("brand_presence_flag", "Présence grand réseau",
                brand_flag, "bool", "latest",
                GeoLevel.MUNICIPALITY, sids, grade, fallback=fallback),
            self._new_metric("franchise_brand_count", "Franchises présentes",
                franchises, "marques", "latest",
                GeoLevel.MUNICIPALITY, sids, grade, fallback=fallback),
            self._new_metric("association_competitor_count", "Associations",
                associations, "acteurs", "latest",
                GeoLevel.MUNICIPALITY, [src.source_id, src_assoc.source_id], grade, fallback=fallback),
            self._new_metric("ccas_presence_flag", "CCAS local" if country == "FR" else "Ayuntamiento social",
                DEFAULT_METRIC_BASELINES["ccas_presence_flag"], "bool", "latest",
                GeoLevel.MUNICIPALITY, [src_assoc.source_id], ConfidenceGrade.C, fallback=True),
            self._new_metric("recent_openings_2y", "Ouvertures récentes 2 ans",
                DEFAULT_METRIC_BASELINES["recent_openings_2y"], "acteurs", "2y",
                GeoLevel.MUNICIPALITY, sids, ConfidenceGrade.D, fallback=True),
        ]
        return metrics, [src, src_assoc]

    def _resolve_coords(self, study: Study) -> tuple[float | None, float | None]:
        country = study.country
        if country == "FR":
            postal = study.geo_scope.postal_codes[0] if study.geo_scope.postal_codes else None
            commune = geo_api_gouv.resolve_commune(study.geo_scope.city, postal)
            if commune and commune.get("centre", {}).get("coordinates"):
                lon, lat = commune["centre"]["coordinates"]
                return lat, lon
        else:
            municipio = ine_geo.resolve_municipio(study.geo_scope.city, study.geo_scope.province)
            if municipio:
                try:
                    return float(municipio.get("Latitud")), float(municipio.get("Longitud"))
                except (TypeError, ValueError):
                    return None, None
        return None, None

    def _fetch_live(self, country: str, lat: float | None, lon: float | None, city: str = ""):
        """
        Fetch live Places data. Bascule sur New Places API si USE_NEW_PLACES_API=true.
        Activer via : GOOGLE_PLACES_API_NEW=true sur Render (après probe A.1 OK).
        """
        if USE_NEW_PLACES_API:
            # New Places API — requêtes textuelles, pagination avec sleep(3)
            if not google_places_new.is_configured() or not city:
                return None, None, {}
            places15 = google_places_new.collect_competitors(city, country)
            # Pour la New API, on n'a pas de rayon → count_30 = count_15 (estimation)
            places30 = places15
            classification = classify_competitors(places15)
            return places15, places30, classification
        else:
            # Legacy Nearby Search (défaut — actif tant que probe non confirmé)
            if not google_places.is_configured() or lat is None or lon is None:
                return None, None, {}
            places15 = google_places.search_competitors(lat, lon, country, RADIUS_15MIN_M)
            places30 = google_places.search_competitors(lat, lon, country, RADIUS_30MIN_M)
            classification = classify_competitors(places15)
            return places15, places30, classification


def build_competitors_from_places(
    places_results: list[dict],
    direct_competitor_names: list[str] | None = None,
    source_id: str = "google_places",
) -> list[Competitor]:
    """
    Convertit les résultats bruts Google Places en objets Competitor.
    - Déduplique par nom normalisé (Places peut renvoyer le même établissement
      via plusieurs keywords).
    - Trie : directs d'abord, puis par note décroissante.
    - N'invente aucune valeur — les champs absents restent None.
    """
    direct_names = [d.lower().strip() for d in (direct_competitor_names or [])]
    seen_names: set[str] = set()
    competitors: list[Competitor] = []

    for place in places_results:
        name = place.get("name")
        if not name:
            continue
        key = name.lower().strip()
        if key in seen_names:
            continue
        seen_names.add(key)

        is_direct = any(dc in key for dc in direct_names) if direct_names else False

        competitors.append(Competitor(
            competitor_id=f"comp_{uuid.uuid4().hex[:8]}",
            name=name,
            address=place.get("address") or place.get("vicinity"),
            rating=place.get("rating"),
            reviews_count=place.get("user_ratings_total"),
            category=(place.get("types") or [None])[0],
            is_direct_competitor=is_direct,
            source_id=source_id,
            confidence_grade=ConfidenceGrade.B,
        ))

    competitors.sort(key=lambda c: (not c.is_direct_competitor, -(c.rating or 0)))
    return competitors


competition_collector = CompetitionCollector()
