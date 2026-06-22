import json

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.encoders import jsonable_encoder

from app.api.schemas.studies import (
    StudyCreateRequest,
    StudyCreateResponse,
    StudyResponse,
    StudyRunResponse,
    StudySectionsResponse,
)
from app.repositories.studies_repo import studies_repo
from app.services.lovable_config import build_lovable_config
from app.services.html_renderer import html_renderer
from app.services.master_json_builder import master_json_builder
from app.services.study_factory import study_factory
from app.pipelines.run_study import study_pipeline

router = APIRouter(prefix="/studies", tags=["studies"])


@router.post("", response_model=StudyCreateResponse)
def create_study(payload: StudyCreateRequest) -> StudyCreateResponse:
    study = study_factory.build(payload)
    studies_repo.save(study)
    return StudyCreateResponse(study_id=study.study_id, status=study.status)


@router.get("/{study_id}", response_model=StudyResponse)
def get_study(study_id: str) -> StudyResponse:
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return StudyResponse(**study.model_dump())


@router.post("/{study_id}/run", response_model=StudyRunResponse)
def run_study(study_id: str) -> StudyRunResponse:
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    study_pipeline.run(study_id)
    refreshed = studies_repo.get(study_id)
    return StudyRunResponse(
        study_id=study_id,
        status=refreshed.status,
        message=f"Pipeline exécuté - {len(refreshed.metrics)} métriques / {len(refreshed.scores)} scores / verdict {refreshed.verdict}",
    )


@router.get("/{study_id}/sections", response_model=StudySectionsResponse)
def get_study_sections(study_id: str) -> StudySectionsResponse:
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return StudySectionsResponse(
        study_id=study_id,
        status=study.status,
        sections=[section.model_dump() for section in study.sections],
    )


@router.get("/{study_id}/metrics")
def get_study_metrics(study_id: str) -> dict:
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return {
        "study_id": study_id,
        "metrics": [m.model_dump() for m in study.metrics],
        "sources": [s.model_dump() for s in study.sources],
    }


@router.get("/{study_id}/scores")
def get_study_scores(study_id: str) -> dict:
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return {
        "study_id": study_id,
        "verdict": study.verdict,
        "scores": [s.model_dump() for s in study.scores],
    }


@router.get("/{study_id}/microzones")
def get_study_microzones(study_id: str) -> dict:
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return {
        "study_id": study_id,
        "microzones": study.microzones.model_dump(),
    }


@router.get("/{study_id}/lovable-config")
def get_study_lovable_config(
    study_id: str,
    brand_slug: str | None = Query(default=None),
) -> dict:
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return build_lovable_config(
        business_model=study.business_context.business_model,
        study_id=study_id,
        brand_slug=brand_slug,
    )


@router.get("/{study_id}/master-json")
def get_study_master_json(study_id: str) -> dict:
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return master_json_builder.build(study)


@router.get("/{study_id}/master-json/export")
def export_study_master_json(study_id: str) -> Response:
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    payload = jsonable_encoder(master_json_builder.build(study))
    filename = f"stella_master_{study_id}.json"
    return Response(
        content=json.dumps(payload, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{study_id}/preview-html")
def preview_study_html(
    study_id: str,
    brand_slug: str | None = Query(default=None),
) -> Response:
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    return Response(
        content=html_renderer.render(study, brand_slug=brand_slug),
        media_type="text/html",
    )


@router.get("/{study_id}/preview-html/export")
def export_study_html(
    study_id: str,
    brand_slug: str | None = Query(default=None),
) -> Response:
    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(status_code=404, detail="Study not found")
    filename = f"stella_preview_{study_id}.html"
    return Response(
        content=html_renderer.render(study, brand_slug=brand_slug),
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
