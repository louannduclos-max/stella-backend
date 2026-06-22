from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.brand_profiles import router as brand_profiles_router
from app.api.routes.competition import router as competition_router
from app.api.routes.config import router as config_router
from app.api.routes.income import router as income_router
from app.api.routes.integration import router as integration_router
from app.api.routes.mobility import router as mobility_router
from app.api.routes.pricing import router as pricing_router
from app.api.routes.seniors import router as seniors_router
from app.api.routes.studies import router as studies_router
from app.api.routes.tourism import router as tourism_router
from app.api.routes.transit import router as transit_router
from app.api.routes.agents import router as agents_router
from app.api.routes.webhook import router as webhook_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook_router)   # POST /generate-study (sans préfixe)
app.include_router(agents_router)    # POST /agents/* (stubs Phase 2)
app.include_router(studies_router)
app.include_router(config_router)
app.include_router(brand_profiles_router)
app.include_router(integration_router)
app.include_router(competition_router)
app.include_router(seniors_router)
app.include_router(income_router)
app.include_router(tourism_router)
app.include_router(pricing_router)
app.include_router(mobility_router)
app.include_router(transit_router)


@app.get("/")
def root() -> dict:
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "config": ["/config/kpis", "/config/scores", "/config/sections", "/config/sources", "/config/brand-profiles"],
        "competition": "/competition/probe?city=Auray&country=FR",
        "seniors": "/seniors/probe?city=Auray&country=FR&postal_code=56400",
        "income": "/income/probe?city=Auray&country=FR&postal_code=56400",
        "tourism": "/tourism/probe?city=Auray&country=FR&postal_code=56400&region=Bretagne",
        "pricing": "/pricing/probe?city=Auray&country=FR&postal_code=56400",
        "mobility": "/mobility/probe?city=Auray&country=FR&postal_code=56400",
        "transit": "/transit/probe?city=Auray&country=FR&postal_code=56400",
        "google_places_configured": bool(settings.google_places_api_key),
        "cors_allow_origins": settings.cors_allow_origins,
        "cors_allow_origin_regex": settings.cors_allow_origin_regex,
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "google_places_configured": bool(settings.google_places_api_key),
    }
