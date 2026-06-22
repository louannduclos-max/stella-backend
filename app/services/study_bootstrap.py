from typing import Any, Dict

from app.api.schemas.studies import StudyCreateRequest
from app.pipelines.run_study import study_pipeline
from app.repositories.studies_repo import studies_repo
from app.services.study_factory import study_factory


DEFAULT_PAYLOAD: Dict[str, Any] = {
    "country": "FR",
    "language": "fr",
    "city": "Auray",
    "region": "Bretagne",
    "postal_codes": ["56400"],
    "study_type": "market_feasibility_multiservice",
    "business_context": {
        "brand_name": "O2",
        "business_model": "franchise",
        "service_scope": ["menage", "seniors", "garde_enfants"],
        "positioning_mode": "premium",
        "target_customer_segments": ["seniors", "familles"],
    },
}


def _find_existing(city: str, country: str, brand_name: str | None = None) -> str | None:
    """
    Cherche une étude existante correspondant à city + country (+ brand optionnel).
    Retourne son study_id si trouvée, None sinon.
    """
    city_norm = city.strip().lower()
    country_norm = country.strip().upper()
    for study in studies_repo.all():
        if (
            study.geo_scope.city.strip().lower() == city_norm
            and study.geo_scope.country.strip().upper() == country_norm
        ):
            if brand_name is None:
                return study.study_id
            if study.business_context.brand_name.strip().lower() == brand_name.strip().lower():
                return study.study_id
    return None


def _build_create_request(data: Dict[str, Any]) -> StudyCreateRequest:
    """
    Construit un StudyCreateRequest depuis un dict payload (form, webhook, ou DEFAULT_PAYLOAD).
    Extrait les champs multi-tenant optionnels proprement.
    """
    # Champs multi-tenant — extraits du payload racine
    extra = {
        "tenant_id": data.get("tenant_id"),
        "company_id": data.get("company_id"),
        "external_study_id": data.get("external_study_id"),
        "brand_profile_override": data.get("brand_profile_override"),
    }
    # On fusionne les champs métier avec les extras (StudyCreateRequest ignore les clés inconnues
    # via model_config = {"extra": "ignore"} si besoin ; ici on injecte explicitement)
    base = {k: v for k, v in data.items() if k not in extra}
    return StudyCreateRequest(**base, **{k: v for k, v in extra.items() if v is not None})


def ensure_study(payload: Dict[str, Any] | None = None, *, run_pipeline: bool = True) -> str:
    """Crée toujours une nouvelle étude (comportement d'origine, conservé pour compatibilité)."""
    data = payload or DEFAULT_PAYLOAD
    request = _build_create_request(data)
    study = study_factory.build(request)
    studies_repo.save(study)
    if run_pipeline:
        study_pipeline.run(study.study_id)
    return study.study_id


def find_or_create_study(payload: Dict[str, Any] | None = None, *, run_pipeline: bool = True) -> str:
    """
    Cherche d'abord une étude existante pour city + country + brand.
    Si trouvée → retourne son study_id (fast path, pas de recalcul).
    Si non trouvée → crée et lance le pipeline.
    """
    data = payload or DEFAULT_PAYLOAD
    city = data.get("city", "")
    country = data.get("country", "")
    brand_name = (data.get("business_context") or {}).get("brand_name")
    tenant_id = data.get("tenant_id")

    if city and country:
        existing_id = _find_existing(city, country, brand_name)
        if existing_id:
            # Vérifier que l'étude appartient bien au bon tenant si spécifié
            if not tenant_id:
                return existing_id
            from app.repositories.studies_repo import studies_repo as _repo
            s = _repo.get(existing_id)
            if s and s.tenant_id == tenant_id:
                return existing_id

    return ensure_study(payload, run_pipeline=run_pipeline)
