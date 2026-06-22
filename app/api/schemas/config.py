from pydantic import BaseModel


class ConfigPayloadResponse(BaseModel):
    name: str
    version: str
    items: list[dict]


class LovableConfigResponse(BaseModel):
    name: str
    version: str
    study_id: str | None = None
    business_model: str | None = None
    brand_profile: dict | None = None
    payload: dict
