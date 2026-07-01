"""
Google Places API client -- Sprint 9 (A.2).

Deux clients disponibles :
  - GooglePlacesClient (Legacy Nearby Search) : actif si GOOGLE_PLACES_API_NEW=false
  - GooglePlacesNewClient (New Places API)    : actif si GOOGLE_PLACES_API_NEW=true

Le flag GOOGLE_PLACES_API_NEW (Render env var) bascule entre les deux.
Decision basee sur le resultat de /agents/debug/places-probe :
  - new_places_api.count > 0 => definir GOOGLE_PLACES_API_NEW=true sur Render
  - legacy_textsearch.count > 0 => laisser a false (defaut)

PAGINATION (New API uniquement) :
  Le nextPageToken n'est PAS valide immediatement -- delai ~2-5s requis.
  Sans sleep(3), la 2e page renvoie INVALID_ARGUMENT et 0 resultat.
  Max 3 pages x 20 resultats = 60 acteurs max par requete.
"""
import logging
import os
import time
import uuid

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# URLs
NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
TEXT_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
NEW_PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
_NEW_FIELDS = (
    "places.displayName,places.formattedAddress,places.rating,"
    "places.userRatingCount,places.types,nextPageToken"
)

# Flag de bascule -- definir GOOGLE_PLACES_API_NEW=true sur Render apres probe
USE_NEW_PLACES_API = os.environ.get("GOOGLE_PLACES_API_NEW", "false").lower() == "true"

# Keywords valides par probe Places API
SAP_KEYWORDS_FR = [
    "aide a domicile",
    "services a domicile",
    "aide aux seniors",
    "senior service",
    "maintien a domicile",
    "Azae",
    "Vitalliance",
    "O2 Care Services",
    "Petits-fils",
]
SAP_KEYWORDS_ES = [
    "servicios a domicilio",
    "ayuda a domicilio",
    "ayuda a mayores",
    "cuidado de personas mayores",
    "limpieza a domicilio",
    "cuidado de mayores",
]

KNOWN_BRANDS = [
    "O2", "Shiva", "Apef", "Domidom", "Vitalliance", "Destia", "Age d'or",
    "Senior Compagnie", "Generale des services", "Petits-fils", "ADMR",
    "Interdomicilio", "Serhogarsystem", "Eulen", "Clece",
]

ASSOCIATION_HINTS = ["admr", "una", "ccas", "asociacion", "association"]


def _competition_queries(city: str, country: str) -> list[str]:
    """Retourne les requetes textuelles adaptees au pays et a la ville."""
    if (country or "FR").upper() == "ES":
        return [
            f"ayuda a domicilio {city}",
            f"servicio de atencion domiciliaria {city}",
            f"cuidado de personas mayores {city}",
        ]
    return [
        f"aide a domicile {city}",
        f"services a la personne {city}",
        f"aide aux personnes agees {city}",
    ]


class GooglePlacesClient:
    """Client Google Places API Legacy -- Nearby Search. Actif si USE_NEW_PLACES_API=false."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.api_key = get_settings().google_places_api_key

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search_competitors(self, lat: float, lon: float, country: str, radius_m: int) -> list[dict]:
        if not self.is_configured():
            return []
        keywords = SAP_KEYWORDS_FR if (country or "FR").upper() == "FR" else SAP_KEYWORDS_ES
        results: dict[str, dict] = {}
        for kw in keywords:
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    r = client.get(
                        NEARBY_URL,
                        params={
                            "location": f"{lat},{lon}",
                            "radius": radius_m,
                            "keyword": kw,
                            "language": "fr" if (country or "FR").upper() == "FR" else "es",
                            "key": self.api_key,
                        },
                    )
                    r.raise_for_status()
                    payload = r.json()
            except Exception:
                continue
            for place in payload.get("results", []):
                pid = place.get("place_id")
                if not pid or pid in results:
                    continue
                results[pid] = {
                    "place_id": pid,
                    "name": place.get("name"),
                    "address": place.get("vicinity"),
                    "rating": place.get("rating"),
                    "user_ratings_total": place.get("user_ratings_total"),
                    "types": place.get("types", []),
                    "matched_keyword": kw,
                }
        return list(results.values())


class GooglePlacesNewClient:
    """
    Client New Places API (Places API (New)) -- Text Search.
    Actif si GOOGLE_PLACES_API_NEW=true sur Render.
    """

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
        self.api_key = get_settings().google_places_api_key

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def _search_one_query(self, query: str, lang: str) -> list[dict]:
        """Execute une requete avec pagination (max 3 pages = 60 resultats)."""
        results, token = [], None
        for _attempt in range(3):
            body: dict = {
                "textQuery": query,
                "languageCode": lang,
                "pageSize": 20,
            }
            if token:
                body["pageToken"] = token

            try:
                r = httpx.post(
                    NEW_PLACES_URL,
                    headers={
                        "Content-Type": "application/json",
                        "X-Goog-Api-Key": self.api_key,
                        "X-Goog-FieldMask": _NEW_FIELDS,
                    },
                    json=body,
                    timeout=self.timeout,
                )
                if r.status_code != 200:
                    logger.warning(
                        "[places_new] HTTP %s query=%s err=%s",
                        r.status_code, query, r.text[:200],
                    )
                    break
                d = r.json()
                results.extend(d.get("places", []))
                token = d.get("nextPageToken")
                if not token:
                    break
                # IMPORTANT : token non valide immediatement -- delai requis
                time.sleep(3)
            except Exception as exc:
                logger.warning("[places_new] exception query=%s : %s", query, exc)
                break

        return results

    def collect_competitors(self, city: str, country: str) -> list[dict]:
        """
        Collecte les concurrents via New Places API pour une ville.
        Retourne une liste de dicts normalises compatibles avec build_competitors_from_places().
        """
        if not self.is_configured():
            return []

        lang = "fr" if (country or "FR").upper() == "FR" else "es"
        queries = _competition_queries(city, country)

        seen_names: set[str] = set()
        raw_results: list[dict] = []

        for q in queries:
            places = self._search_one_query(q, lang)
            for p in places:
                name = (p.get("displayName") or {}).get("text")
                if not name:
                    continue
                key = name.lower().strip()
                if key in seen_names:
                    continue
                seen_names.add(key)
                raw_results.append({
                    "place_id": f"new_{uuid.uuid4().hex[:8]}",
                    "name": name,
                    "address": p.get("formattedAddress"),
                    "rating": p.get("rating"),
                    "user_ratings_total": p.get("userRatingCount"),
                    "types": p.get("types", []),
                    "matched_keyword": q,
                })

        logger.info(
            "[places_new] city=%s country=%s found=%d",
            city, country, len(raw_results),
        )
        return raw_results


# Singletons
google_places = GooglePlacesClient()
google_places_new = GooglePlacesNewClient()


def classify_competitors(places: list[dict]) -> dict:
    """Classification des acteurs (brands vs associations). Inchange."""
    brands_found: dict[str, int] = {}
    associations = 0
    franchises = 0
    for place in places:
        name = (place.get("name") or "").lower()
        is_assoc = any(h in name for h in ASSOCIATION_HINTS)
        is_brand = False
        for brand in KNOWN_BRANDS:
            if brand.lower() in name:
                brands_found[brand] = brands_found.get(brand, 0) + 1
                is_brand = True
                break
        if is_assoc:
            associations += 1
        elif is_brand:
            franchises += 1
    return {
        "total": len(places),
        "brands_found": brands_found,
        "associations": associations,
        "franchises": franchises,
        "brand_presence_flag": 1 if brands_found else 0,
    }
