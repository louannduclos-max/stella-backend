from fastapi import APIRouter, HTTPException, Query

from app.core.mobility_registry import (
    ES_CAR_DEPENDENCY_BY_REGION,
    ES_CAR_DEPENDENCY_DEFAULT,
    ES_PARKING_BY_REGION,
    ES_PARKING_DEFAULT,
    ES_RUSH_HOUR_PENALTY_BY_REGION,
    ES_RUSH_HOUR_PENALTY_DEFAULT,
    FR_CAR_DEPENDENCY_BY_DEPT,
    FR_CAR_DEPENDENCY_DEFAULT,
    FR_PARKING_BY_DEPT,
    FR_PARKING_DEFAULT,
    FR_RUSH_HOUR_PENALTY_BY_DEPT,
    FR_RUSH_HOUR_PENALTY_DEFAULT,
    TRAVEL_TIME_SPREAD_BY_DENSITY,
)
from app.services.external.geo_api_gouv import geo_api_gouv

router = APIRouter(prefix="/mobility", tags=["mobility"])


@router.get("/probe")
def probe_mobility(
    city: str = Query(..., min_length=2),
    country: str = Query("FR", min_length=2, max_length=2),
    postal_code: str | None = None,
    region: str | None = None,
) -> dict:
    country = country.upper()
    if country not in {"FR", "ES"}:
        raise HTTPException(status_code=400, detail="Country must be FR or ES")
    if country == "FR":
        return _probe_fr(city, postal_code)
    return _probe_es(city, region)


def _probe_fr(city: str, postal_code: str | None) -> dict:
    commune = geo_api_gouv.resolve_commune(city, postal_code)
    if not commune:
        raise HTTPException(status_code=404, detail="Commune non résolue.")
    code_insee = commune.get("code") or ""
    population = int(commune.get("population") or 0)
    surface_km2 = float(commune.get("surface") or 100) / 100
    density = round(population / surface_km2, 1) if surface_km2 > 0 else 0
    density_level = _density_level(density)
    dept = code_insee[:3] if code_insee.startswith("97") else code_insee[:2]

    car_share = FR_CAR_DEPENDENCY_BY_DEPT.get(dept, FR_CAR_DEPENDENCY_DEFAULT)
    rush_penalty = FR_RUSH_HOUR_PENALTY_BY_DEPT.get(dept, FR_RUSH_HOUR_PENALTY_DEFAULT)
    parking = FR_PARKING_BY_DEPT.get(dept, FR_PARKING_DEFAULT)
    travel_spread = TRAVEL_TIME_SPREAD_BY_DENSITY[density_level]
    dept_known = dept in FR_CAR_DEPENDENCY_BY_DEPT

    return {
        "country": "FR",
        "city": commune.get("nom"),
        "code_insee": code_insee,
        "department": dept,
        "density": density,
        "density_level": density_level,
        "travel_time_spread_min": travel_spread,
        "car_dependency_share_pct": car_share,
        "rush_hour_penalty_min": rush_penalty,
        "parking_constraint_index": parking,
        "confidence": "B" if dept_known else "D",
    }


def _probe_es(city: str, region: str | None) -> dict:
    if not region:
        raise HTTPException(status_code=400, detail="region requis pour ES.")
    car_share = ES_CAR_DEPENDENCY_BY_REGION.get(region)
    rush_penalty = ES_RUSH_HOUR_PENALTY_BY_REGION.get(region)
    parking = ES_PARKING_BY_REGION.get(region)
    key = region if car_share is not None else None
    if car_share is None:
        needle = region.lower()
        for name, val in ES_CAR_DEPENDENCY_BY_REGION.items():
            if name.lower() in needle or needle in name.lower():
                car_share = val
                rush_penalty = ES_RUSH_HOUR_PENALTY_BY_REGION.get(name, ES_RUSH_HOUR_PENALTY_DEFAULT)
                parking = ES_PARKING_BY_REGION.get(name, ES_PARKING_DEFAULT)
                key = name
                break
    if car_share is None:
        car_share = ES_CAR_DEPENDENCY_DEFAULT
        rush_penalty = ES_RUSH_HOUR_PENALTY_DEFAULT
        parking = ES_PARKING_DEFAULT
        key = "default"

    density_level = "urban"
    travel_spread = TRAVEL_TIME_SPREAD_BY_DENSITY[density_level]

    return {
        "country": "ES",
        "city": city,
        "region_input": region,
        "region_resolved": key,
        "density_level_hypothesis": density_level,
        "travel_time_spread_min": travel_spread,
        "car_dependency_share_pct": car_share,
        "rush_hour_penalty_min": rush_penalty,
        "parking_constraint_index": parking,
        "confidence": "B" if key != "default" else "D",
    }


def _density_level(density: float) -> str:
    if density >= 4000:
        return "very_urban"
    if density >= 1500:
        return "urban"
    if density >= 300:
        return "periurban"
    return "rural"
