from pydantic import BaseModel, Field

from app.core.enums import ConfidenceGrade


class Neighborhood(BaseModel):
    neighborhood_id: str
    name: str
    code: str | None = None
    population: int | None = None
    seniors_60_plus_share: float | None = None
    median_income: float | None = None
    real_estate_price_m2: float | None = None
    rental_price_m2: float | None = None
    premium_flag: bool = False
    premium_score: float = 0.0
    notes: str | None = None
    confidence_grade: ConfidenceGrade = ConfidenceGrade.D


class Street(BaseModel):
    street_id: str
    name: str
    neighborhood_id: str | None = None
    street_type: str = "rue"
    target_segment: str | None = None
    priority: str = "P2"
    avg_real_estate_price_m2: float | None = None
    notes: str | None = None


class TrafficAxis(BaseModel):
    axis_id: str
    name: str
    axis_type: str = "structurant"
    daily_traffic: int | None = None
    rush_hour_penalty_min: float | None = None
    serves_neighborhoods: list[str] = Field(default_factory=list)
    notes: str | None = None


class TransitLine(BaseModel):
    line_id: str
    name: str
    mode: str = "bus"
    frequency_peak: str | None = None
    compatibility_sap_hours: bool | None = None
    notes: str | None = None


class MicroZonesSnapshot(BaseModel):
    neighborhoods: list[Neighborhood] = Field(default_factory=list)
    streets: list[Street] = Field(default_factory=list)
    traffic_axes: list[TrafficAxis] = Field(default_factory=list)
    transit_lines: list[TransitLine] = Field(default_factory=list)
