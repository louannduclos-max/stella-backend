import httpx

from app.core.config import get_settings


NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
TEXT_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"


# Fix 5 — keywords enrichis pour meilleure détection SAP (notamment villes moyennes)
SAP_KEYWORDS_FR = [
    "services à la personne",
    "aide à domicile",
    "aide aux personnes âgées",
    "aide aux seniors",
    "ménage à domicile",
    "garde enfants à domicile",
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


class GooglePlacesClient:
    """Client Google Places API - concurrence SAP réelle."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.api_key = get_settings().google_places_api_key

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search_competitors(self, lat: float, lon: float, country: str, radius_m: int) -> list[dict]:
        if not self.is_configured():
            return []
        keywords = SAP_KEYWORDS_FR if country == "FR" else SAP_KEYWORDS_ES
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
                            "language": "fr" if country == "FR" else "es",
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


google_places = GooglePlacesClient()


def classify_competitors(places: list[dict]) -> dict:
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
