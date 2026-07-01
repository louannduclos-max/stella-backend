from datetime import datetime, date
from typing import Any
from pydantic import BaseModel, Field, HttpUrl

from app.api.schemas.microzones import MicroZonesSnapshot
from app.core.enums import (
    ConfidenceGrade,
    FreshnessLevel,
    GeoLevel,
    PriorityEnum,
    QASeverity,
    RenderType,
    SourceType,
    StudyStatus,
    VerdictEnum,
)


class GeoScope(BaseModel):
    city: str
    country: str
    region: str | None = None
    province: str | None = None
    municipality_code: str | None = None
    postal_codes: list[str] = Field(default_factory=list)
    geo_level_primary: GeoLevel = GeoLevel.MUNICIPALITY
    comparison_scopes: list[GeoLevel] = Field(default_factory=list)
    radius_minutes: int | None = 30


class BusinessContext(BaseModel):
    brand_name: str
    business_model: str
    service_scope: list[str]
    positioning_mode: str
    target_customer_segments: list[str]
    pricing_positioning: str | None = None
    study_goal: str | None = None


class Source(BaseModel):
    source_id: str
    theme_id: str
    country: str
    source_type: SourceType
    authority_level: int
    freshness_level: FreshnessLevel
    coverage_level: GeoLevel
    title: str
    url: HttpUrl | str
    publisher: str | None = None
    publication_date: date | None = None
    accessed_at: datetime
    confidence_grade: ConfidenceGrade
    notes: str | None = None


class Metric(BaseModel):
    metric_id: str
    theme_id: str
    name: str
    label: str
    value: str | int | float
    unit: str | None = None
    period: str
    geo_level: GeoLevel
    source_ids: list[str]
    confidence_grade: ConfidenceGrade
    fallback_used: bool = False
    fallback_note: str | None = None
    # ─── Benchmark national (Data-Depth sprint) ───────────────────────────────
    national_benchmark: str | int | float | None = None
    benchmark_source_id: str | None = None
    benchmark_year: int | None = None          # traçabilité temporelle
    benchmark_interpretation: str | None = None  # ex: "1.4× la moyenne nationale"


class ScoreDriver(BaseModel):
    metric_name: str
    normalized_value: int | float
    weight: float


class Score(BaseModel):
    score_id: str
    name: str
    label: str
    weight: int | float
    value: int | float
    confidence_grade: ConfidenceGrade
    drivers: list[ScoreDriver]
    missing_inputs_count: int = 0
    status: str = "final"


class Citation(BaseModel):
    citation_id: str
    source_id: str
    claim_text: str
    url: HttpUrl | str
    locator: str | None = None
    confidence_grade: ConfidenceGrade


class Section(BaseModel):
    section_id: str
    display_name: str
    priority: PriorityEnum
    required: bool
    component_main: str
    component_fallback: str | None = None
    render_types: list[RenderType]
    slot_contract: dict[str, Any] = Field(default_factory=dict)
    expected_kpis: list[str] = Field(default_factory=list)
    slots: dict[str, Any] = Field(default_factory=dict)
    citations: list[str] = Field(default_factory=list)
    qa_status: str = "pending"


class Artifact(BaseModel):
    artifact_id: str
    artifact_type: RenderType
    status: str
    path: str
    generated_at: datetime
    version: str


class QAResult(BaseModel):
    qa_id: str
    test_id: str
    severity: QASeverity
    status: str
    message: str
    section_id: str | None = None
    remediation: str


class Competitor(BaseModel):
    """Acteur concurrentiel nommé, issu de Google Places."""
    competitor_id: str
    name: str
    address: str | None = None
    city: str | None = None
    rating: float | None = None
    reviews_count: int | None = None
    category: str | None = None
    distance_min: int | None = None   # minutes voiture (non rempli pour l'instant)
    is_direct_competitor: bool = False
    domain: str | None = None          # domaine d'expertise (Sprint 12 — déduit par classifier agent)
    source_id: str
    confidence_grade: ConfidenceGrade = ConfidenceGrade.B


class FundingScale(BaseModel):
    """Barème de financement (APA en FR, SAAD en ES, etc.)."""
    country: str
    type: str
    source: str
    year: int
    scale_rows: list[dict]
    participation: dict


class Study(BaseModel):
    study_id: str
    version: str
    status: StudyStatus
    country: str
    language: str
    study_type: str
    study_date: date
    # Multi-tenant : slug de la filiale (ex: "interdomicilio") + UUID Supabase optionnel
    tenant_id: str = "interdomicilio"
    company_id: str | None = None              # UUID Supabase companies.id
    brand_profile_override: dict | None = None  # company_branding + presets inline depuis Supabase
    geo_scope: GeoScope
    business_context: BusinessContext
    sources: list[Source] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)
    scores: list[Score] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)
    artifacts: list[Artifact] = Field(default_factory=list)
    qa_results: list[QAResult] = Field(default_factory=list)
    microzones: MicroZonesSnapshot = Field(default_factory=MicroZonesSnapshot)
    verdict: VerdictEnum | None = None
    # Sprint 4 Lot C — narratifs LLM (Gemini ou template). Clés : verdict_narrative,
    # exec_summary, competitive_insight, action_30d/60d/90d, opportunity_text, generated_by
    narratives: dict | None = None
    # Data-Depth sprint — acteurs nommés + barème financement
    competitors: list[Competitor] = Field(default_factory=list)
    funding_scale: FundingScale | None = None
    created_at: datetime
    updated_at: datetime
