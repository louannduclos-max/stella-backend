from fastapi import APIRouter, HTTPException, Query, Response

from app.core.brand_profiles import get_brand_profile, list_brand_profiles
from app.repositories.studies_repo import studies_repo
from app.services.css_vars_builder import build_css_string, build_css_vars
from app.services.export_pptx import build_pptx_for_study
from app.services.frontend_bindings_builder import build_frontend_component_map
from app.services.frontend_manifest_builder import frontend_manifest_builder
from app.services.lovable_config import build_lovable_config
from app.services.playlist_builder import build_playlist_manifest
from app.services.qa_visual_5_0 import get_qa_visual_5_0_contract
from app.services.slides_5_0_builder import build_slides_5_0_for_study, get_slide_5_0
from app.services.study_bootstrap import ensure_study, find_or_create_study

router = APIRouter(prefix="/integration", tags=["integration"])


@router.get("/css-vars")
def get_css_vars(brand_slug: str | None = Query(default=None)) -> dict:
    if brand_slug and not get_brand_profile(brand_slug):
        raise HTTPException(status_code=404, detail="Brand profile not found")
    return build_css_vars(brand_slug)


@router.get("/css-vars.css")
def get_css_vars_file(brand_slug: str | None = Query(default=None)) -> Response:
    if brand_slug and not get_brand_profile(brand_slug):
        raise HTTPException(status_code=404, detail="Brand profile not found")
    return Response(content=build_css_string(brand_slug), media_type="text/css")


@router.get("/component-map")
def get_component_map() -> dict:
    return build_frontend_component_map()


@router.get("/qa-visual-5_0/contract")
def get_qa_visual_contract() -> dict:
    return get_qa_visual_5_0_contract()


@router.post("/ensure-study")
def post_ensure_study(payload: dict | None = None) -> dict:
    study_id = ensure_study(payload)
    study = studies_repo.get(study_id)
    return {
        "study_id": study_id,
        "status": study.status if study else "ready",
    }


@router.get("/study/{study_id}/status")
def get_study_status(study_id: str) -> dict:
    """Endpoint de polling : retourne le statut courant d'une etude."""
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return {
        "study_id": study.study_id,
        "status": study.status,
        "city": study.geo_scope.city,
        "country": study.geo_scope.country,
        "brand_name": study.business_context.brand_name,
        "verdict": study.verdict,
        "updated_at": study.updated_at.isoformat(),
    }


@router.get("/auto-slides-5_0")
def get_auto_slides_5_0(
    study_id: str | None = Query(default=None),
    city: str | None = Query(default=None),
    country: str | None = Query(default=None),
    region: str | None = Query(default=None),
    postal_codes: str | None = Query(default=None),
    brand_name: str | None = Query(default=None),
    business_model: str | None = Query(default=None),
    brand_slug: str | None = Query(default=None),
) -> dict:
    """
    Endpoint unifie.
    - study_id fourni -> lecture directe (fast path).
    - city+country fournis -> find_or_create_study.
    - Sinon -> DEFAULT_PAYLOAD (Auray/FR/O2, mode demo).
    """
    if study_id:
        study = studies_repo.get(study_id)
        if not study:
            raise HTTPException(status_code=404, detail=f"Study '{study_id}' not found")
    else:
        user_payload: dict | None = None
        if city and country:
            user_payload = {
                "country": country.upper(),
                "city": city,
                "language": "es" if country.upper() == "ES" else "fr",
                "business_context": {
                    "brand_name": brand_name or "Interdomicilio",
                    "business_model": business_model or "franchise",
                    "service_scope": ["seniors", "menage"],
                    "positioning_mode": "premium",
                    "target_customer_segments": ["seniors", "familles"],
                },
            }
            if region:
                user_payload["region"] = region
            if postal_codes:
                user_payload["postal_codes"] = [p.strip() for p in postal_codes.split(",")]

        study_id_resolved = find_or_create_study(user_payload)
        study = studies_repo.get(study_id_resolved)
        if not study:
            raise HTTPException(status_code=500, detail="Auto study creation failed")

    payload = build_slides_5_0_for_study(study)
    payload["auto_created_study_id"] = study.study_id
    return payload


@router.get("/study/{study_id}/slides-5_0")
def get_study_slides_5_0(study_id: str) -> dict:
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return build_slides_5_0_for_study(study)


@router.get("/study/{study_id}/export/pptx")
def export_study_pptx(study_id: str) -> Response:
    """Export PPTX pixel-perfect (canvas 1920x1080 -> EMU)."""
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    try:
        pptx_bytes = build_pptx_for_study(study)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Erreur generation PPTX : {exc}") from exc
    city = study.geo_scope.city.replace(" ", "_")
    brand = study.business_context.brand_name.replace(" ", "_")
    filename = f"Stella_{brand}_{city}_{study_id[:8]}.pptx"
    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/study/{study_id}/slides-5_0/{slide_id}")
def get_study_slide_5_0(study_id: str, slide_id: str) -> dict:
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    payload = build_slides_5_0_for_study(study)
    slide = get_slide_5_0(payload, slide_id)
    if not slide:
        raise HTTPException(status_code=404, detail="Slide not found")
    return slide


@router.get("/frontend-manifest")
def get_frontend_manifest(
    brand_slug: str | None = Query(default=None),
    country: str | None = Query(default=None),
    city: str | None = Query(default=None),
    business_model: str | None = Query(default=None),
) -> dict:
    if brand_slug and not get_brand_profile(brand_slug):
        raise HTTPException(status_code=404, detail="Brand profile not found")
    return frontend_manifest_builder.build_shell(
        brand_slug=brand_slug,
        country=country,
        city=city,
        business_model=business_model,
    )


@router.get("/playlist")
def get_playlist_manifest(
    brand_slug: str | None = Query(default=None),
    country: str | None = Query(default=None),
    city: str | None = Query(default=None),
    business_model: str | None = Query(default=None),
) -> dict:
    if brand_slug and not get_brand_profile(brand_slug):
        raise HTTPException(status_code=404, detail="Brand profile not found")
    return build_playlist_manifest(
        brand_slug=brand_slug,
        country=country,
        city=city,
        business_model=business_model,
    )


@router.get("/lovable-pack")
def get_lovable_pack(
    brand_slug: str | None = Query(default=None),
    country: str | None = Query(default=None),
) -> dict:
    profile = get_brand_profile(brand_slug) if brand_slug else None
    if brand_slug and not profile:
        raise HTTPException(status_code=404, detail="Brand profile not found")
    lovable = build_lovable_config(
        business_model=(profile or {}).get("business_model_default"),
        brand_slug=brand_slug,
    )
    css = build_css_vars(brand_slug)
    playlist = build_playlist_manifest(
        brand_slug=brand_slug,
        country=country,
        business_model=(profile or {}).get("business_model_default"),
    )
    return {
        "version": "1.0.0",
        "brand_profile": profile,
        "brand_profiles_available": list_brand_profiles(country=country),
        "css": css,
        "component_map": build_frontend_component_map(),
        "playlist": playlist,
        "lovable_config": lovable,
        "endpoints": {
            "list_brands": "/config/brand-profiles",
            "brand_detail": "/config/brand-profiles/{slug}",
            "css_vars_json": "/integration/css-vars?brand_slug={slug}",
            "css_vars_file": "/integration/css-vars.css?brand_slug={slug}",
            "component_map": "/integration/component-map",
            "frontend_manifest": "/integration/frontend-manifest?brand_slug={slug}",
            "playlist": "/integration/playlist?brand_slug={slug}",
            "lovable_config": "/config/lovable?brand_slug={slug}",
            "create_study": "POST /studies",
            "run_study": "POST /studies/{id}/run",
            "study_master_json": "/studies/{id}/master-json",
            "study_preview_html": "/studies/{id}/preview-html?brand_slug={slug}",
            "study_lovable_config": "/studies/{id}/lovable-config?brand_slug={slug}",
            "study_frontend_manifest": "/integration/study/{id}/frontend-manifest?brand_slug={slug}",
            "study_playlist": "/integration/study/{id}/playlist?brand_slug={slug}",
            "export_pptx": "/integration/study/{id}/export/pptx",
        },
    }


@router.get("/study/{study_id}/frontend-manifest")
def get_study_frontend_manifest(
    study_id: str,
    brand_slug: str | None = Query(default=None),
) -> dict:
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return frontend_manifest_builder.build_for_study(study, brand_slug=brand_slug)


@router.get("/study/{study_id}/playlist")
def get_study_playlist_manifest(
    study_id: str,
    brand_slug: str | None = Query(default=None),
) -> dict:
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    resolved_slug = brand_slug
    if not resolved_slug and study.business_context.brand_name:
        candidate = study.business_context.brand_name.lower().split()[0]
        if get_brand_profile(candidate):
            resolved_slug = candidate
    return build_playlist_manifest(
        brand_slug=resolved_slug,
        study_id=study_id,
        country=study.geo_scope.country,
        city=study.geo_scope.city,
        business_model=study.business_context.business_model,
    )



def _build_study_endpoints(study_id: str, slug: str | None) -> dict:
    s = slug or ""
    return {
        "master_json": f"/studies/{study_id}/master-json",
        "master_json_export": f"/studies/{study_id}/master-json/export",
        "preview_html": f"/studies/{study_id}/preview-html?brand_slug={s}",
        "metrics": f"/studies/{study_id}/metrics",
        "scores": f"/studies/{study_id}/scores",
        "microzones": f"/studies/{study_id}/microzones",
        "sections": f"/studies/{study_id}/sections",
        "frontend_manifest": f"/integration/study/{study_id}/frontend-manifest?brand_slug={s}",
        "playlist": f"/integration/study/{study_id}/playlist?brand_slug={s}",
        "export_pptx": f"/integration/study/{study_id}/export/pptx",
    }


@router.get("/study/{study_id}/lovable-pack")
def get_study_lovable_pack(
    study_id: str,
    brand_slug: str | None = Query(default=None),
) -> dict:
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    resolved_slug = brand_slug
    if not resolved_slug and study.business_context.brand_name:
        candidate = study.business_context.brand_name.lower().split()[0]
        if get_brand_profile(candidate):
            resolved_slug = candidate
    profile = get_brand_profile(resolved_slug) if resolved_slug else None
    lovable = build_lovable_config(
        business_model=study.business_context.business_model,
        study_id=study_id,
        brand_slug=resolved_slug,
    )
    css = build_css_vars(resolved_slug)
    playlist = build_playlist_manifest(
        brand_slug=resolved_slug,
        study_id=study_id,
        country=study.geo_scope.country,
        city=study.geo_scope.city,
        business_model=study.business_context.business_model,
    )
    return {
        "version": "1.0.0",
        "study_id": study_id,
        "resolved_brand_slug": resolved_slug,
        "brand_profile": profile,
        "css": css,
        "component_map": build_frontend_component_map(),
        "frontend_manifest": frontend_manifest_builder.build_for_study(study, brand_slug=resolved_slug),
        "playlist": playlist,
        "lovable_config": lovable,
        "data_endpoints": _build_study_endpoints(study_id, resolved_slug),
    }
