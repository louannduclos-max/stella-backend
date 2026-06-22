from fastapi import APIRouter, HTTPException, Query

from app.core.pricing_registry import (
    ES_BRAND_PRICING,
    ES_PRICING_BY_REGION,
    ES_PRICING_DEFAULT,
    FR_BRAND_PRICING,
    FR_PRICING_BY_DEPT,
    FR_PRICING_DEFAULT,
)
from app.services.external.geo_api_gouv import geo_api_gouv

router = APIRouter(prefix="/pricing", tags=["pricing"])


@router.get("/probe")
def probe_pricing(
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
    dept = code_insee[:3] if code_insee.startswith("97") else code_insee[:2]

    config = FR_PRICING_BY_DEPT.get(dept, FR_PRICING_DEFAULT)
    dept_known = dept in FR_PRICING_BY_DEPT

    return {
        "country": "FR",
        "city": commune.get("nom"),
        "code_insee": code_insee,
        "department": dept,
        "avg_hourly_price_cleaning_eur": config["cleaning"],
        "avg_hourly_price_care_eur": config["care"],
        "regulated_saad_rate_eur": config["saad_regulated"],
        "pricing_source": "FR dept registry" if dept_known else "national default",
        "brand_benchmarks": FR_BRAND_PRICING,
        "confidence": "B" if dept_known else "D",
    }


def _probe_es(city: str, region: str | None) -> dict:
    if not region:
        raise HTTPException(status_code=400, detail="region requis pour ES.")
    config = ES_PRICING_BY_REGION.get(region)
    key = region if config else None
    if not config:
        needle = region.lower()
        for name, payload in ES_PRICING_BY_REGION.items():
            if name.lower() in needle or needle in name.lower():
                config = payload
                key = name
                break
    if not config:
        config = ES_PRICING_DEFAULT
        key = "default"

    return {
        "country": "ES",
        "city": city,
        "region_input": region,
        "region_resolved": key,
        "avg_hourly_price_cleaning_eur": config["cleaning"],
        "avg_hourly_price_care_eur": config["care"],
        "regulated_saad_rate_eur": config["saad_regulated"],
        "brand_benchmarks": ES_BRAND_PRICING,
        "confidence": "B" if key != "default" else "D",
    }
