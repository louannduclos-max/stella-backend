"""
Webhook endpoint appelé par le frontend wizard d'étude.

Le front (wizard-submit.server.ts) envoie :
  POST /generate-study
  Authorization: Bearer <WEBHOOK_SECRET>
  {
    "study_id": "<supabase-uuid>",   <- devient le study_id backend
    "study_data": {
      "city_name": "Lyon",
      "postal_code": "69001",
      "code_insee": "69123",
      "lat": 45.76, "lon": 4.83,
      "country_code": "FR",          <- résolu par geo.api.gouv.fr / Google
      "company_id": "<uuid>",
      "study_type": "market_feasibility_multiservice",
      "included_activity_families": ["SAP_DOM", "SAP_MEN"],
      "kpis_enriched": [{code, label, kpi_group, display_order}],
      "client_name": "Interdomicilio Lyon",
      "language": "fr",
      "title": "...",
      "radius_km": 5,
    }
  }

Réponse immédiate : { "study_id": "...", "generation_status": "pending" }
Pipeline en arrière-plan → callbacks de progression vers FRONT_WEBHOOK_URL.
"""

import threading
import logging
from fastapi import APIRouter, HTTPException, Request

from app.core.config import get_settings
from app.services.progress_notifier import notify_front

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhook"])


@router.post("/generate-study")
def post_generate_study(payload: dict, request: Request) -> dict:
    """
    Webhook de déclenchement de génération d'étude depuis le wizard front.
    Vérifie le Bearer token, mappe study_data -> StudyCreateRequest, pipeline en background.
    """
    # 1. Vérification Bearer
    settings = get_settings()
    if settings.webhook_secret:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authorization header manquant ou invalide")
        token = auth_header[len("Bearer "):]
        if token != settings.webhook_secret:
            raise HTTPException(status_code=403, detail="Webhook secret invalide")

    # 2. Extraction des champs
    supabase_study_id: str | None = payload.get("study_id")
    study_data: dict = payload.get("study_data") or {}

    if not supabase_study_id:
        raise HTTPException(status_code=422, detail="Champ 'study_id' manquant")

    city = study_data.get("city_name") or study_data.get("city", "")
    if not city:
        raise HTTPException(status_code=422, detail="Champ 'study_data.city_name' manquant")

    # Résolution du pays : country_code (déjà résolu par le front via geo.api.gouv.fr)
    country = (
        study_data.get("country_code")
        or study_data.get("country")
        or ("ES" if (study_data.get("language") or "").startswith("es") else "FR")
    ).upper()[:2]

    language = study_data.get("language") or ("es" if country == "ES" else "fr")
    client_name = study_data.get("client_name") or "Interdomicilio"
    study_type = study_data.get("study_type") or "market_feasibility_multiservice"
    postal_code = study_data.get("postal_code")

    # Mapping included_activity_families -> service_scope
    # Le front envoie soit string[] (codes SAP), soit dict[] (enriched)
    families_raw = study_data.get("included_activity_families") or []
    service_scope: list[str] = []
    for f in families_raw:
        if isinstance(f, str) and f.strip():
            service_scope.append(f.strip())
        elif isinstance(f, dict):
            code = f.get("code") or f.get("activity_code") or f.get("activity_label") or ""
            if code:
                service_scope.append(code)
    if not service_scope:
        service_scope = ["menage", "seniors", "aide_domicilio"]

    # 3. Construction du payload interne Stella
    internal_payload: dict = {
        "country": country,
        "language": language,
        "city": city,
        "study_type": study_type,
        "postal_codes": [postal_code] if postal_code else [],
        "business_context": {
            "brand_name": client_name,
            "business_model": study_data.get("business_model") or "franchise",
            "service_scope": service_scope,
            "positioning_mode": study_data.get("positioning_mode") or "premium",
            "target_customer_segments": study_data.get("target_customer_segments") or ["seniors", "familles"],
            "study_goal": study_data.get("study_objective"),
        },
        # Champs multi-tenant (company_id déjà résolu par le front)
        "external_study_id": supabase_study_id,
        "tenant_id": study_data.get("tenant_id"),
        "company_id": study_data.get("company_id"),
        "brand_profile_override": study_data.get("brand_profile_override"),
        # Sprint 14b — le front classe déjà les choix client (kpi_master & co) :
        # on les transmet ENFIN au lieu de les jeter. Alimente intent + composer.
        "wizard_selections": {
            "kpis": study_data.get("kpis"),
            "kpis_enriched": study_data.get("kpis_enriched"),
            "kpi_selected": study_data.get("kpi_selected"),
            "analysis_axes": study_data.get("analysis_axes"),
            "target_publics": study_data.get("target_publics"),
            "commune_types": study_data.get("commune_types"),
            "zone_focus": study_data.get("zone_focus"),
            "risks": study_data.get("risks"),
            "road_axes": study_data.get("road_axes"),
            "demographic_segments": study_data.get("demographic_segments"),
            "reference_years": study_data.get("reference_years"),
            "palette_key": study_data.get("palette_key"),
            "deliverable_format": study_data.get("deliverable_format"),
            "study_family_code": study_data.get("study_family_code"),
            "study_category_code": study_data.get("study_category_code"),
            "study_subtype_code": study_data.get("study_subtype_code"),
        },
    }

    # 4. Vérifier que l'étude n'existe pas déjà (idempotence)
    from app.repositories.studies_repo import studies_repo
    existing = studies_repo.get(supabase_study_id)
    if existing:
        logger.info(
            "[webhook] étude déjà existante %s (statut: %s) — skip création",
            supabase_study_id, existing.status,
        )
        return {"study_id": supabase_study_id, "generation_status": existing.status}

    # 5. Lancer le pipeline en arrière-plan
    def _run() -> None:
        # Notifier immédiatement que le traitement a démarré
        notify_front(
            study_id=supabase_study_id,
            status="processing",
            progress=5,
            phase=1,
            phase_total=5,
            phase_label="Préparation du brief",
            eta_seconds=240,
        )

        pptx_bytes: bytes | None = None
        error_msg: str | None = None
        final_status = "done"

        try:
            # Le pipeline lui-même émettra les callbacks de phase 2→5
            study_id_out = ensure_study(internal_payload, run_pipeline=True)
            logger.info("[webhook] pipeline terminé pour study_id=%s", supabase_study_id)

            # Générer le PPTX si l'étude est prête
            study_obj = studies_repo.get(study_id_out)
            if study_obj:
                try:
                    from app.services.export_pptx import build_pptx_for_study
                    pptx_bytes = build_pptx_for_study(study_obj)
                    logger.info(
                        "[webhook] PPTX généré (%d octets) pour study_id=%s",
                        len(pptx_bytes), supabase_study_id,
                    )
                except Exception as pptx_exc:
                    logger.warning(
                        "[webhook] génération PPTX échouée pour study_id=%s : %s",
                        supabase_study_id, pptx_exc,
                    )

        except Exception as exc:
            logger.exception(
                "[webhook] pipeline échoué pour study_id=%s : %s", supabase_study_id, exc
            )
            error_msg = str(exc)[:2000]
            final_status = "error"

        # Callback final : done (avec PPTX) ou error
        notify_front(
            study_id=supabase_study_id,
            status=final_status,
            progress=100 if final_status == "done" else None,
            phase=5,
            phase_total=5,
            phase_label="Finalisation" if final_status == "done" else None,
            eta_seconds=0,
            pptx_bytes=pptx_bytes,
            error_message=error_msg,
        )

    from app.services.study_bootstrap import ensure_study

    thread = threading.Thread(
        target=_run,
        daemon=True,
        name=f"stella-pipeline-{supabase_study_id[:8]}",
    )
    thread.start()

    logger.info(
        "[webhook] génération démarrée study_id=%s city=%s country=%s",
        supabase_study_id, city, country,
    )
    return {"study_id": supabase_study_id, "generation_status": "pending"}
