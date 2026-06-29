import logging
from typing import Any, Dict, List

from app.api.schemas.common import Study
from app.services.css_vars_builder import build_css_vars_for_study
from app.services.layout_engine_5_0 import build_slide_5_0
from app.services.master_json_builder import master_json_builder
from app.services.section_registry import SECTION_REGISTRY
from app.services.slide_data_builder_5_0 import build_slide_data_5_0, collect_expected_strings

logger = logging.getLogger(__name__)

FALLBACK = "Donnée non disponible (TBD)"

# Sections structurelles toujours incluses même si données manquantes
_ALWAYS_INCLUDE = {"cover", "executive_summary", "swot", "verdict"}


def _is_slide_data_empty(slide_data: Dict[str, Any]) -> bool:
    """
    Retourne True si TOUS les slots de données primaires d'un slide
    sont à la valeur FALLBACK (les champs statiques comme title/eyebrow
    ne sont pas comptés).
    Utilisé pour filtrer les slides sans contenu réel.
    """
    # Slots spécifiques selon le type de layout
    for key in ("metrics", "columns", "steps", "hero_kpis", "quadrants"):
        items = slide_data.get(key)
        if items is not None and isinstance(items, list) and len(items) > 0:
            non_fallback = [
                item for item in items
                if isinstance(item, dict) and item.get("value") not in (None, FALLBACK, "")
            ]
            # Si au moins un slot a une vraie valeur -> slide non vide
            if non_fallback:
                return False
            # Tous les slots sont FALLBACK -> slide vide
            return True
    # Pas de liste de data trouvée -> considéré non vide (slide structurel)
    return False


def _resolve_brand_slug(study: Study) -> str | None:
    """
    Résout le slug de marque depuis tenant_id ou brand_name.
    Priorité : brand_name (ex: "o2") > tenant_id (ex: "interdomicilio") > None.
    """
    from app.core.brand_profiles import get_brand_profile

    # 1. Essayer le premier mot du brand_name (ex: "O2 Grenoble" -> "o2")
    brand_words = (study.business_context.brand_name or "").strip().lower().split()
    if brand_words and get_brand_profile(brand_words[0]):
        return brand_words[0]

    # 2. Essayer tenant_id
    if study.tenant_id and get_brand_profile(study.tenant_id):
        return study.tenant_id

    # 3. Fallback : tenant_id même sans profil enregistré (permet CSS vars par défaut)
    return study.tenant_id or None


def _build_slide_fallback(
    study: Study,
    section: Dict[str, Any],
) -> Dict[str, Any]:
    """Fallback : utilise layout_engine_5_0 existant si l'agent échoue."""
    section_id = section["section_id"]
    expected_kpis = section.get("expected_kpis") or []
    display_name = section.get("display_name")
    slide_data = build_slide_data_5_0(study, section_id, expected_kpis, display_name=display_name)
    layout = build_slide_5_0(section_id, slide_data)
    return {
        "title": slide_data["title"],
        "layout": layout["layout"],
        "background": layout["background"],
        "canvas": layout["canvas"],
        "safe_margin": layout["safe_margin"],
        "objects": layout["objects"],
        "fallback_used": False,
    }


def build_slides_5_0_for_study(study: Study) -> Dict[str, Any]:
    slides: List[Dict[str, Any]] = []
    skipped: List[str] = []

    # Construire le manifest une seule fois (source de vérité pour l'agent)
    manifest = master_json_builder.build(study)

    # Tentative d'import de l'agent (silencieux si non disponible)
    _agent = None
    try:
        from app.agents.slide_builder_agent import slide_builder_agent
        _agent = slide_builder_agent
    except Exception as _e:
        logger.debug("[slides_builder] Slide Builder Agent non disponible : %s", _e)

    for idx, section in enumerate(SECTION_REGISTRY, start=1):
        section_id = section["section_id"]
        display_name = section.get("display_name", section_id)

        # ── Fallback pré-check : si agent non dispo, utiliser le layout engine ──
        if _agent is None:
            slide_data_check = build_slide_data_5_0(
                study,
                section_id,
                section.get("expected_kpis") or [],
                display_name=display_name,
            )
            if section_id not in _ALWAYS_INCLUDE and _is_slide_data_empty(slide_data_check):
                skipped.append(section_id)
                continue
            layout_fb = build_slide_5_0(section_id, slide_data_check)
            slides.append({
                "slide_index": idx,
                "slide_id": f"slide_{idx:02d}_{section_id}",
                "section_id": section_id,
                "title": slide_data_check["title"],
                "layout": layout_fb["layout"],
                "background": layout_fb["background"],
                "canvas": layout_fb["canvas"],
                "safe_margin": layout_fb["safe_margin"],
                "objects": layout_fb["objects"],
                "agent_generated": False,
                "expected_kpis": section.get("expected_kpis", []),
            })
            continue

        # ── Tentative avec le Slide Builder Agent ──
        try:
            agent_layout = _agent.build_slide(
                section_id=section_id,
                manifest_data=manifest,
                tenant_id=study.tenant_id or "interdomicilio",
                language=study.language or "fr",
            )
            slides.append({
                "slide_index": idx,
                "slide_id": f"slide_{idx:02d}_{section_id}",
                "section_id": section_id,
                "title": display_name,
                **agent_layout,
                "expected_kpis": section.get("expected_kpis", []),
            })
        except Exception as exc:
            # ── Fallback silencieux sur layout_engine_5_0 ──
            logger.warning(
                "[slides_builder] Agent KO pour '%s' → fallback layout_engine. Raison : %s",
                section_id,
                exc,
            )
            expected_kpis = section.get("expected_kpis") or []
            slide_data = build_slide_data_5_0(
                study, section_id, expected_kpis, display_name=display_name
            )
            if section_id not in _ALWAYS_INCLUDE and _is_slide_data_empty(slide_data):
                skipped.append(section_id)
                continue
            layout = build_slide_5_0(section_id, slide_data)
            slides.append({
                "slide_index": idx,
                "slide_id": f"slide_{idx:02d}_{section_id}",
                "section_id": section_id,
                "title": slide_data["title"],
                "layout": layout["layout"],
                "background": layout["background"],
                "canvas": layout["canvas"],
                "safe_margin": layout["safe_margin"],
                "objects": layout["objects"],
                "agent_generated": False,
                "fallback_reason": str(exc),
                "expected_kpis": section.get("expected_kpis", []),
            })

    brand_slug = _resolve_brand_slug(study)
    css_vars = build_css_vars_for_study(brand_slug, study.brand_profile_override)

    return {
        "version": "5.0.0",
        "study_id": study.study_id,
        "tenant_id": study.tenant_id,
        "canvas": {"width": 1920, "height": 1080},
        "brand_slug": brand_slug,
        "css_vars": css_vars,
        "slides": slides,
        "skipped_sections": skipped,
    }


def get_slide_5_0(payload: Dict[str, Any], slide_id: str) -> Dict[str, Any] | None:
    """Récupère un slide par son slide_id dans le payload slides_5_0."""
    for slide in payload.get("slides", []):
        if slide.get("slide_id") == slide_id:
            return slide
    return None
