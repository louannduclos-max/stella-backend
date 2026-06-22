from fastapi import APIRouter, HTTPException, Query

from app.core.seniors_registry import (
    ES_SAAD_BENEFICIARIES_BY_REGION,
    ES_SAAD_DEFAULT,
    FR_APA_RATE_DEFAULT,
    FR_APA_RATE_PER_1000_75PLUS,
    FR_SINGLE_SENIOR_SHARE_BY_DEPT,
    FR_SINGLE_SENIOR_SHARE_DEFAULT,
)
from app.services.external.geo_api_gouv import geo_api_gouv

router = APIRouter(prefix="/seniors", tags=["seniors"])


@router.get("/probe")
def probe_seniors(
    city: str = Query(..., min_length=2),
    country: str = Query("FR", min_length=2, max_length=2),
    postal_code: str | None = None,
    region: str | None = None,
    seniors_75_plus_share: float = Query(12.0, ge=0, le=60),
) -> dict:
    country = country.upper()
    if country not in {"FR", "ES"}:
        raise HTTPException(status_code=400, detail="Country must be FR or ES")

    if country == "FR":
        return _probe_fr(city, postal_code, seniors_75_plus_share)
    return _probe_es(city, region, seniors_75_plus_share)


def _probe_fr(city: str, postal_code: str | None, seniors_75_share: float) -> dict:
    commune = geo_api_gouv.resolve_commune(city, postal_code)
    if not commune:
        raise HTTPException(status_code=404, detail="Commune non résolue via geo.api.gouv.fr")

    code_insee = commune.get("code") or ""
    population = int(commune.get("population") or 0)
    dept = code_insee[:3] if code_insee.startswith("97") else code_insee[:2]

    apa_rate = FR_APA_RATE_PER_1000_75PLUS.get(dept, FR_APA_RATE_DEFAULT)
    apa_known = dept in FR_APA_RATE_PER_1000_75PLUS
    single_share = FR_SINGLE_SENIOR_SHARE_BY_DEPT.get(dept, FR_SINGLE_SENIOR_SHARE_DEFAULT)

    seniors_75_count = population * (seniors_75_share / 100)
    dependency_apa = int(round(seniors_75_count * (apa_rate / 1000)))
    total_households = population / 2.2 if population > 0 else 0
    single_seniors = int(round(total_households * (single_share / 100)))

    return {
        "country": "FR",
        "city": commune.get("nom"),
        "code_insee": code_insee,
        "department": dept,
        "population": population,
        "seniors_75_plus_share_input": seniors_75_share,
        "apa_rate_per_1000_75plus": apa_rate,
        "apa_rate_source": "CNSA registry" if apa_known else "national default",
        "dependency_ratio_apa": dependency_apa,
        "single_senior_share_dept": single_share,
        "single_senior_households": single_seniors,
        "confidence": "B" if apa_known else "D",
    }


def _probe_es(city: str, region: str | None, seniors_75_share: float) -> dict:
    config = None
    key = None
    if region:
        config = ES_SAAD_BENEFICIARIES_BY_REGION.get(region)
        if config:
            key = region
        else:
            needle = region.lower()
            for name, payload in ES_SAAD_BENEFICIARIES_BY_REGION.items():
                if name.lower() in needle or needle in name.lower():
                    config = payload
                    key = name
                    break
    if not config:
        config = ES_SAAD_DEFAULT
        key = "default"

    population = 100000
    seniors_65_share = seniors_75_share + 18.0
    seniors_65_count = population * (seniors_65_share / 100)
    dependency_saad = int(round(seniors_65_count * (config["rate_per_1000_65plus"] / 1000)))
    total_households = population / 2.5
    single_seniors = int(round(total_households * (config["single_senior_share"] / 100)))

    return {
        "country": "ES",
        "city": city,
        "region": region,
        "region_resolved": key,
        "population_hypothesis": population,
        "seniors_65_plus_share_estimated": round(seniors_65_share, 1),
        "saad_rate_per_1000_65plus": config["rate_per_1000_65plus"],
        "dependency_ratio_saad": dependency_saad,
        "single_senior_share": config["single_senior_share"],
        "single_senior_households": single_seniors,
        "confidence": "B" if key != "default" else "D",
    }
