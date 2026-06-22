from typing import Any, Dict, List

from app.api.schemas.common import Study
from app.services.css_vars_builder import build_css_vars_for_study
from app.services.layout_engine_5_0 import build_slide_5_0
from app.services.section_registry import SECTION_REGISTRY
from app.services.slide_data_builder_5_0 import build_slide_data_5_0, collect_expected_strings

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


def build_slides_5_0_for_study(study: Study) -> Dict[str, Any]:
    slides: List[Dict[str, Any]] = []
    skipped: List[str] = []
    for idx, section in enumerate(SECTION_REGISTRY, start=1):
        section_id = section["section_id"]
        expected_kpis = section.get("expected_kpis") or []
        # FIX: passer display_name (FR) au builder pour éviter l'auto-génération anglaise
        display_name = section.get("display_name")
        slide_data = build_slide_data_5_0(study, section_id, expected_kpis, display_name=display_name)

        # Filtrage des slides sans données réelles (sauf slides structurels obligatoires)
        if section_id not in _ALWAYS_INCLUDE and _is_slide_data_empty(slide_data):
            skipped.append(section_id)
            continue

        layout = build_slide_5_0(section_id, slide_data)
        slides.append(
            {
                "slide_index": idx,
                "slide_id": f"slide_{idx:02d}_{section_id}",
                "section_id": section_id,
                "title": slide_data["title"],
                "layout": layout["layout"],
                "background": layout["background"],
                "canvas": layout["canvas"],
                "safe_margin": layout["safe_margin"],
                "objects": layout["objects"],
            }
        )

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
