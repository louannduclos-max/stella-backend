from fastapi import APIRouter, HTTPException, Query

from app.services.external.google_places_api import classify_competitors, google_places
from app.services.external.geo_api_gouv import geo_api_gouv
from app.services.external.ine_geo import ine_geo

router = APIRouter(prefix="/competition", tags=["competition"])


@router.get("/probe")
def probe_competition(
    city: str = Query(..., min_length=2),
    country: str = Query("FR", min_length=2, max_length=2),
    postal_code: str | None = None,
    radius_minutes: int = Query(15, ge=5, le=60),
) -> dict:
    if country.upper() not in {"FR", "ES"}:
        raise HTTPException(status_code=400, detail="Country must be FR or ES")

    country = country.upper()
    lat, lon = _resolve_coords(city, country, postal_code)
    if lat is None or lon is None:
        raise HTTPException(status_code=404, detail="Coordonnées non résolues pour cette ville.")

    if not google_places.is_configured():
        return {
            "city": city,
            "country": country,
            "lat": lat,
            "lon": lon,
            "live": False,
            "message": "GOOGLE_PLACES_API_KEY non configurée - configure la variable d'environnement.",
            "competitor_count": 0,
            "competitors": [],
        }

    radius_m = int(radius_minutes * 60 * 9)
    places = google_places.search_competitors(lat, lon, country, radius_m)
    classification = classify_competitors(places)
    return {
        "city": city,
        "country": country,
        "lat": lat,
        "lon": lon,
        "live": True,
        "radius_minutes": radius_minutes,
        "radius_meters": radius_m,
        "competitor_count": classification["total"],
        "franchises": classification["franchises"],
        "associations": classification["associations"],
        "brands_found": classification["brands_found"],
        "brand_presence_flag": classification["brand_presence_flag"],
        "competitors": places,
    }


def _resolve_coords(city: str, country: str, postal_code: str | None):
    if country == "FR":
        commune = geo_api_gouv.resolve_commune(city, postal_code)
        if commune and commune.get("centre", {}).get("coordinates"):
            lon, lat = commune["centre"]["coordinates"]
            return lat, lon
        return None, None
    municipio = ine_geo.resolve_municipio(city)
    if municipio:
        try:
            return float(municipio.get("Latitud")), float(municipio.get("Longitud"))
        except (TypeError, ValueError):
            return None, None
    return None, None
