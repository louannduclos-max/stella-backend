from fastapi import APIRouter, Query

from app.api.schemas.config import ConfigPayloadResponse, LovableConfigResponse
from app.core.constants import DEFAULT_VERSION
from app.core.kpi_catalog import KPI_CATALOG
from app.core.score_config import SCORE_CONFIG
from app.services.lovable_config import build_lovable_config
from app.services.section_registry import SECTION_REGISTRY
from app.services.source_registry import SOURCE_REGISTRY

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/kpis", response_model=ConfigPayloadResponse)
def get_kpis() -> ConfigPayloadResponse:
    return ConfigPayloadResponse(name="kpi_catalog", version=DEFAULT_VERSION, items=KPI_CATALOG)


@router.get("/scores", response_model=ConfigPayloadResponse)
def get_scores() -> ConfigPayloadResponse:
    items = [{"score_id": score_id, **payload} for score_id, payload in SCORE_CONFIG.items()]
    return ConfigPayloadResponse(name="score_config", version=DEFAULT_VERSION, items=items)


@router.get("/sections", response_model=ConfigPayloadResponse)
def get_sections() -> ConfigPayloadResponse:
    return ConfigPayloadResponse(name="section_registry", version=DEFAULT_VERSION, items=SECTION_REGISTRY)


@router.get("/sources", response_model=ConfigPayloadResponse)
def get_sources() -> ConfigPayloadResponse:
    return ConfigPayloadResponse(name="source_registry", version=DEFAULT_VERSION, items=SOURCE_REGISTRY)


@router.get("/lovable", response_model=LovableConfigResponse)
def get_lovable_config(
    business_model: str | None = Query(default=None),
    brand_slug: str | None = Query(default=None),
) -> LovableConfigResponse:
    return LovableConfigResponse(**build_lovable_config(business_model=business_model, brand_slug=brand_slug))
