"""
Slides 5.0 builder — chemin unique et propre.

Architecture Sprint 5 :
  layout_engine_5_0 (déterministe, source de vérité positions)
    → validate_slide_objects (schéma unique, rejette les malformés)
    → [optionnel] NarrativeAgent.fill_text_slots (enrichit les slots texte)
    → [optionnel] QAAgent.validate_and_merge (revert slot par slot si échec)

slide_builder_agent (Vertex AI / Sprint 2) n'est PLUS dans le chemin actif.
Le fichier est conservé dans le repo mais ne doit pas être appelé ici.
"""
import logging
import os
from typing import Any, Dict, List

from app.api.schemas.common import Study
from app.schemas.slide_objects import validate_slide_objects
from app.services.css_vars_builder import build_css_vars_for_study
from app.services.layout_engine_5_0 import build_slide_5_0
from app.services.master_json_builder import master_json_builder
from app.services.section_registry import SECTION_REGISTRY
from app.services.slide_data_builder_5_0 import build_slide_data_5_0, collect_expected_strings

logger = logging.getLogger(__name__)

USE_NARRATIVE_AGENT = os.environ.get("SLIDE_BUILDER_USE_AGENT", "false").lower() == "true"

FALLBACK = "Donnée non disponible (TBD)"

# Sections structurelles toujours incluses même si données manquantes
_ALWAYS_INCLUDE = {"cover", "executive_summary", "swot", "verdict"}


def _is_slide_data_empty(slide_data: Dict[str, Any]) -> bool:
    """
    Retourne True si TOUS les slots de données primaires d'un slide
    sont à la valeur FALLBACK. Les champs statiques (title/eyebrow)
    ne sont pas comptés.
    """
    for key in ("metrics", "columns", "steps", "hero_kpis", "quadrants"):
        items = slide_data.get(key)
        if items is not None and isinstance(items, list) and len(items) > 0:
            non_fallback = [
                item for item in items
                if isinstance(item, dict) and item.get("value") not in (None, FALLBACK, "")
            ]
            if non_fallback:
                return False
            return True
    return False


def _resolve_brand_slug(study: Study) -> str | None:
    """
    Résout le slug de marque depuis tenant_id ou brand_name.
    Priorité : brand_name (ex: "o2") > tenant_id (ex: "interdomicilio") > None.
    """
    from app.core.brand_profiles import get_brand_profile

    brand_words = (study.business_context.brand_name or "").strip().lower().split()
    if brand_words and get_brand_profile(brand_words[0]):
        return brand_words[0]

    if study.tenant_id and get_brand_profile(study.tenant_id):
        return study.tenant_id

    return study.tenant_id or None


def build_slides_5_0_for_study(study: Study) -> Dict[str, Any]:
    slides: List[Dict[str, Any]] = []
    skipped: List[str] = []

    # Manifest — source de vérité pour l'agent et le QA
    manifest = master_json_builder.build(study)

    # Import optionnel de NarrativeAgent (silencieux si indispo)
    _narrative_agent = None
    if USE_NARRATIVE_AGENT:
        try:
            from app.agents.narrative_agent import narrative_agent as _na
            _narrative_agent = _na
            logger.info("[slides_builder] NarrativeAgent actif")
        except Exception as _e:
            logger.warning("[slides_builder] NarrativeAgent non disponible : %s", _e)

    # Import optionnel de QAAgent (toujours dispo car déterministe, mais gardons la défense)
    _qa_agent = None
    if USE_NARRATIVE_AGENT:
        try:
            from app.agents.qa_agent import qa_agent as _qa
            _qa_agent = _qa
        except Exception as _e:
            logger.warning("[slides_builder] QAAgent non disponible : %s", _e)

    if not USE_NARRATIVE_AGENT:
        logger.info("[slides_builder] Mode déterministe pur (SLIDE_BUILDER_USE_AGENT=false)")

    for idx, section in enumerate(SECTION_REGISTRY, start=1):
        section_id = section["section_id"]
        display_name = section.get("display_name", section_id)
        expected_kpis = section.get("expected_kpis") or []

        # 1. Build données + layout déterministe — TOUJOURS, jamais bypass
        slide_data = build_slide_data_5_0(study, section_id, expected_kpis, display_name=display_name)

        # Filtrage des slides sans données (sauf sections structurelles)
        if section_id not in _ALWAYS_INCLUDE and _is_slide_data_empty(slide_data):
            skipped.append(section_id)
            continue

        layout = build_slide_5_0(section_id, slide_data)

        # 2. Validation schéma unique — rejette les objets malformés ou hors canvas
        objects = validate_slide_objects(layout["objects"])

        # 3. Enrichissement narratif optionnel + QA slot par slot
        if _narrative_agent:
            try:
                enriched = _narrative_agent.fill_text_slots(
                    objects, manifest, language=study.language or "fr"
                )
                if _qa_agent:
                    objects = _qa_agent.validate_and_merge(
                        agent_objects=enriched,
                        deterministic_objects=objects,
                        manifest=manifest,
                    )
                else:
                    objects = enriched
            except Exception as e:
                logger.warning("[slides_builder] NarrativeAgent KO sur '%s' → fallback déterministe : %s", section_id, e)
                # objects reste la version déterministe validée — jamais d'échec visible

        slides.append({
            "slide_index": idx,
            "slide_id": f"slide_{idx:02d}_{section_id}",
            "section_id": section_id,
            "title": slide_data["title"],
            "layout": layout["layout"],
            "background": layout["background"],
            "canvas": layout["canvas"],
            "safe_margin": layout["safe_margin"],
            "whitespace_ratio": layout.get("whitespace_ratio", 0.0),
            "whitespace_compliant": layout.get("whitespace_compliant", True),
            "expected_kpis": expected_kpis,
            "slide_data": slide_data,
            "objects": objects,
            "expected_strings": collect_expected_strings(slide_data),
            "agent_generated": _narrative_agent is not None,
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
