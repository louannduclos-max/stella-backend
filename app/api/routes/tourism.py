from fastapi import APIRouter, HTTPException, Query

from app.core.tourism_registry import (
    ES_TOURISM_BY_REGION,
    ES_TOURISM_DEFAULT,
    FR_HIGH_TOURISM_DEPTS,
    FR_TOURISM_BY_REGION,
    FR_TOURISM_DEFAULT,
)
from app.services.external.geo_api_gouv import geo_api_gouv

router = APIRouter(prefix="/tourism", tags=["tourism"])


@router.get("/probe")
def probe_tourism(
    city: str = Query(..., min_length=2),
    country: str = Query("FR", min_length=2, max_length=2),
    postal_code: str | None = None,
    region: str | None = None,
) -> dict:
    country = country.upper()
    if country not in {"FR", "ES"}:
        raise HTTPException(status_code=400, detail="Country must be FR or ES")
    if country == "FR":
        return _probe_fr(city, postal_code, region)
    return _probe_es(city, region)


def _probe_fr(city: str, postal_code: str | None, region: str | None) -> dict:
    commune = geo_api_gouv.resolve_commune(city, postal_code)
    if not commune:
        raise HTTPException(status_code=404, detail="Commune non résolue.")
    code_insee = commune.get("code") or ""
    population = int(commune.get("population") or 0)
    dept = code_insee[:3] if code_insee.startswith("97") else code_insee[:2]
    region_resolved = region or commune.get("region", {}).get("nom") if isinstance(commune.get("region"), dict) else region

    config = FR_TOURISM_BY_REGION.get(region_resolved) if region_resolved else None
    key = region_resolved if config else None
    if not config and region_resolved:
        needle = region_resolved.lower()
        for name, payload in FR_TOURISM_BY_REGION.items():
            if name.lower() in needle or needle in name.lower():
                config = payload
                key = name
                break
    if not config:
        config = FR_TOURISM_DEFAULT
        key = "default"

    boost = FR_HIGH_TOURISM_DEPTS.get(dept) or 1.0
    overnight = int(round(population * config["overnight_stays_per_capita"] * boost))
    seasonality = round(config["seasonality_index"] * (1.2 if boost > 1.0 else 1.0), 2)
    multiplier = round(config["revenue_multiplier"] * (1.15 if boost > 1.0 else 1.0), 2)

    return {
        "country": "FR",
        "city": commune.get("nom"),
        "code_insee": code_insee,
        "department": dept,
        "region_resolved": key,
        "population": population,
        "dept_tourism_boost": boost,
        "tourism_overnight_stays": overnight,
        "tourism_seasonality_index": seasonality,
        "seasonal_revenue_multiplier": multiplier,
        "confidence": "B" if key != "default" else "D",
    }


def _probe_es(city: str, region: str | None) -> dict:
    if not region:
        raise HTTPException(status_code=400, detail="region requis pour ES.")
    config = ES_TOURISM_BY_REGION.get(region)
    key = region if config else None
    if not config:
        needle = region.lower()
        for name, payload in ES_TOURISM_BY_REGION.items():
            if name.lower() in needle or needle in name.lower():
                config = payload
                key = name
                break
    if not config:
        config = ES_TOURISM_DEFAULT
        key = "default"

    population = 100000
    overnight = int(round(population * config["overnight_stays_per_capita"]))

    return {
        "country": "ES",
        "city": city,
        "region_input": region,
        "region_resolved": key,
        "population_hypothesis": population,
        "tourism_overnight_stays": overnight,
        "tourism_seasonality_index": config["seasonality_index"],
        "seasonal_revenue_multiplier": config["revenue_multiplier"],
        "confidence": "B" if key != "default" else "D",
    }
