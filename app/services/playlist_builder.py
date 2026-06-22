from app.core.brand_profiles import get_brand_profile
from app.services.section_registry import SECTION_REGISTRY


VISUAL_ANCHOR_BY_SECTION = {
    "cover": "hero_kpi_ring",
    "executive_summary": "kpi_cards_grid",
    "methodology_sources": "sources_trust_grid",
    "market_scorecard": "score_bars_dashboard",
    "demographics": "population_split_chart",
    "target_segments": "segment_cards",
    "employment_talent": "talent_kpi_board",
    "income_housing": "income_housing_dual_panel",
    "real_estate": "real_estate_price_cards",
    "microzones": "microzones_heat_table",
    "competition_mapping": "competition_matrix",
    "regulation_feasibility": "regulation_focus_cards",
    "swot": "swot_quadrants",
    "verdict": "verdict_signal_card",
    "action_plan": "action_timeline",
}


LAYOUT_BY_INDEX = {
    1: "cover_70_30",
    2: "hero_title_plus_kpis",
    3: "two_columns_sources",
}


def _resolve_profile(brand_slug: str | None) -> dict:
    return get_brand_profile(brand_slug) if brand_slug else get_brand_profile("o2")



def build_playlist_manifest(
    brand_slug: str | None = None,
    *,
    country: str | None = None,
    city: str | None = None,
    business_model: str | None = None,
    study_id: str | None = None,
) -> dict:
    profile = _resolve_profile(brand_slug)
    slides = []

    for idx, section in enumerate(SECTION_REGISTRY, start=1):
        slides.append(
            {
                "slide_index": idx,
                "slide_id": f"slide_{idx:02d}_{section['section_id']}",
                "section_id": section["section_id"],
                "title": section["display_name"],
                "component": section["component_main"],
                "fallback_component": section.get("component_fallback"),
                "render_types": [str(r) for r in section["render_types"]],
                "layout": LAYOUT_BY_INDEX.get(idx, "asymmetric_70_30" if idx % 2 else "asymmetric_30_70"),
                "visual_anchor": VISUAL_ANCHOR_BY_SECTION.get(section["section_id"], "kpi_cards_grid"),
                "priority": str(section["priority"]),
                "required": section["required"],
                "expected_kpis": section["expected_kpis"],
                "slot_keys": list(section["slot_contract"].keys()),
                "design_rules": {
                    "large_title": True,
                    "no_fabricated_text": True,
                    "boxed_numbers": True,
                    "max_paragraph_sentences": 3,
                    "avoid_overlap": True,
                    "contrast_check_required": True,
                },
            }
        )

    return {
        "version": "1.0.0",
        "methodology": "Diapositive 5.0",
        "playlist_mode": "playlist_first",
        "study_id": study_id,
        "brand_slug": profile["slug"],
        "brand_name": profile["brand_name"],
        "country": country or profile["country"],
        "city": city,
        "business_model": business_model or profile.get("business_model_default"),
        "audience": "decision_makers",
        "data_source_contract": "stella_master_json",
        "visual_system": {
            "font_family": profile["font_family"],
            "palette": profile["palette"],
            "asymmetry_ratio": "70/30",
            "strict_rules": [
                "no fabricated text",
                "large titles",
                "asymmetric layouts",
                "boxed KPI numbers",
                "multimedia only when backed by source data",
                "double verification required",
            ],
        },
        "verification": {
            "geometric_overlap_test": True,
            "contrast_check": True,
        },
        "slides": slides,
    }
