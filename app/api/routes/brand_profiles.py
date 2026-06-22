from fastapi import APIRouter, HTTPException, Query

from app.core.brand_profiles import get_brand_profile, list_brand_profiles

router = APIRouter(prefix="/config/brand-profiles", tags=["config"])


@router.get("")
def list_profiles(country: str | None = Query(default=None)) -> dict:
    items = list_brand_profiles(country=country)
    return {"count": len(items), "items": items}


@router.get("/{slug}")
def get_profile(slug: str) -> dict:
    profile = get_brand_profile(slug)
    if not profile:
        raise HTTPException(status_code=404, detail="Brand profile not found")
    return profile
