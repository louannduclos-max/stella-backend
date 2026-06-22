from datetime import date
from pydantic import BaseModel, Field

from app.core.enums import RenderType, StudyStatus
from .common import BusinessContext, GeoScope, Study


class StudyCreateRequest(BaseModel):
    country: str = Field(..., min_length=2, max_length=2)
    language: str = Field(default="fr")
    city: str = Field(..., min_length=2)
    region: str | None = None
    postal_codes: list[str] = Field(default_factory=list)
    study_type: str = Field(default="market_feasibility_multiservice")
    business_context: BusinessContext
    outputs: list[RenderType] = Field(default_factory=lambda: [RenderType.JSON, RenderType.HTML])
    study_date: date = Field(default_factory=date.today)
    # Multi-tenant — tous optionnels, rétrocompatibles
    tenant_id: str | None = None              # slug filiale (ex: "interdomicilio")
    company_id: str | None = None             # UUID Supabase companies.id
    external_study_id: str | None = None      # UUID Supabase studies.id → utilisé comme study_id backend
    brand_profile_override: dict | None = None  # inline depuis company_branding Supabase


class StudyCreateResponse(BaseModel):
    study_id: str
    status: StudyStatus


class StudyRunResponse(BaseModel):
    study_id: str
    status: StudyStatus
    message: str


class StudySectionsResponse(BaseModel):
    study_id: str
    status: StudyStatus
    sections: list[dict]


class StudyResponse(Study):
    pass
