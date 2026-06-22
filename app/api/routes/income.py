from fastapi import APIRouter, HTTPException, Query

from app.core.income_registry import (
    ES_HOME_OWNERSHIP_BY_REGION,
    ES_HOME_OWNERSHIP_DEFAULT,
    ES_MEDIAN_INCOME_BY_REGION,
    ES_MEDIAN_INCOME_DEFAULT,
    ES_TAXABLE_BY_REGION,
    ES_TAXABLE_DEFAULT,
    FR_HOME_OWNERSHIP_BY_DEPT,
    FR_HOME_OWNERSHIP_DEFAULT,
    FR_MEDIAN_INCOME_BY_DEPT,
    FR_MEDIAN_INCOME_DEFAULT,
    FR_TAXABLE_DEFAULT,
    FR_TAXABLE_HOUSEHOLDS_BY_DEPT,
)
from app.services.external.geo_api_gouv import geo_api_gouv

router = APIRouter(prefix="/income", tags=["income"])


@router.get("/probe")
def probe_income(
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

    income = FR_MEDIAN_INCOME_BY_DEPT.get(dept, FR_MEDIAN_INCOME_DEFAULT)
    income_known = dept in FR_MEDIAN_INCOME_BY_DEPT
    ownership = FR_HOME_OWNERSHIP_BY_DEPT.get(dept, FR_HOME_OWNERSHIP_DEFAULT)
    taxable = FR_TAXABLE_HOUSEHOLDS_BY_DEPT.get(dept, FR_TAXABLE_DEFAULT)

    return {
        "country": "FR",
        "city": commune.get("nom"),
        "code_insee": code_insee,
        "department": dept,
        "median_income_eur": income,
        "income_source": "Filosofi registry" if income_known else "national default",
        "taxable_households_share_pct": taxable,
        "home_ownership_share_pct": ownership,
        "tenants_share_pct": round(100 - ownership - 4, 1),
        "confidence": "B" if income_known else "D",
    }


def _probe_es(city: str, region: str | None) -> dict:
    if not region:
        raise HTTPException(status_code=400, detail="region requis pour ES (ex: 'Comunidad Valenciana').")
    income = ES_MEDIAN_INCOME_BY_REGION.get(region)
    ownership = ES_HOME_OWNERSHIP_BY_REGION.get(region)
    taxable = ES_TAXABLE_BY_REGION.get(region)
    key = region if income else None
    if not income:
        needle = region.lower()
        for name, val in ES_MEDIAN_INCOME_BY_REGION.items():
            if name.lower() in needle or needle in name.lower():
                income = val
                ownership = ES_HOME_OWNERSHIP_BY_REGION.get(name, ES_HOME_OWNERSHIP_DEFAULT)
                taxable = ES_TAXABLE_BY_REGION.get(name, ES_TAXABLE_DEFAULT)
                key = name
                break
    if not income:
        income = ES_MEDIAN_INCOME_DEFAULT
        ownership = ES_HOME_OWNERSHIP_DEFAULT
        taxable = ES_TAXABLE_DEFAULT
        key = "default"

    return {
        "country": "ES",
        "city": city,
        "region_input": region,
        "region_resolved": key,
        "median_income_eur": income,
        "taxable_households_share_pct": taxable,
        "home_ownership_share_pct": ownership,
        "tenants_share_pct": round(100 - ownership - 5, 1),
        "confidence": "B" if key != "default" else "D",
    }
