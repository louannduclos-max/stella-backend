from fastapi import APIRouter, HTTPException, Query

from app.core.transit_registry import (
    HIGH_TRANSIT_CITIES_ES,
    HIGH_TRANSIT_CITIES_FR,
    TRANSIT_PROFILE_BY_DENSITY,
    coverage_label,
    coverage_label_es,
)
from app.services.external.geo_api_gouv import geo_api_gouv

router = APIRouter(prefix="/transit", tags=["transit"])


@router.get("/probe")
def probe_transit(
    city: str = Query(..., min_length=2),
    country: str = Query("FR", min_length=2, max_length=2),
    postal_code: str | None = None,
) -> dict:
    country = country.upper()
    if country not in {"FR", "ES"}:
        raise HTTPException(status_code=400, detail="Country must be FR or ES")

    if country == "FR":
        commune = geo_api_gouv.resolve_commune(city, postal_code)
        if not commune:
            raise HTTPException(status_code=404, detail="Commune non résolue.")
        population = int(commune.get("population") or 0)
        surface_km2 = float(commune.get("surface") or 100) / 100
        density = round(population / surface_km2, 1) if surface_km2 > 0 else 0
        city_name = commune.get("nom")
    else:
        population = 0
        density = 1500
        city_name = city

    density_level = _density_level(density)
    profile = TRANSIT_PROFILE_BY_DENSITY[density_level]
    override = HIGH_TRANSIT_CITIES_FR.get(city_name) if country == "FR" else HIGH_TRANSIT_CITIES_ES.get(city_name)
    coverage_pct = override if override is not None else profile["coverage_pct"]
    label = coverage_label(coverage_pct) if country == "FR" else coverage_label_es(coverage_pct)
    lines_count = profile["lines_count"] + (3 if override and override >= 85 else 0)

    return {
        "country": country,
        "city": city_name,
        "density": density,
        "density_level": density_level,
        "transit_lines_estimated": lines_count,
        "modes": profile["modes"],
        "frequency_peak_min": profile["frequency_peak_min"],
        "frequency_offpeak_min": profile["frequency_offpeak_min"],
        "coverage_pct": coverage_pct,
        "coverage_label": label,
        "sap_compatibility": profile["frequency_peak_min"] <= 15,
        "confidence": "B" if override is not None else "C",
    }


def _density_level(density: float) -> str:
    if density >= 4000:
        return "very_urban"
    if density >= 1500:
        return "urban"
    if density >= 300:
        return "periurban"
    return "rural"
