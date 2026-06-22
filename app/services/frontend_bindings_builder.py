from app.services.section_registry import SECTION_REGISTRY


DEFAULT_PROPS_BY_COMPONENT = {
    "cover_hero_stats_v1": ["study", "playlist_slide", "brand_profile", "palette", "scores"],
    "dashboard_kpi_v1": ["study", "playlist_slide", "metrics", "scores", "brand_profile"],
    "sources_grid_v1": ["study", "playlist_slide", "sources", "brand_profile"],
    "score_dashboard_7_v1": ["study", "playlist_slide", "scores", "brand_profile"],
    "dual_chart_demography_v1": ["study", "playlist_slide", "metrics", "brand_profile"],
    "segment_mix_cards_v1": ["study", "playlist_slide", "metrics", "brand_profile"],
    "rh_dashboard_v1": ["study", "playlist_slide", "metrics", "brand_profile"],
    "income_housing_dual_v1": ["study", "playlist_slide", "metrics", "brand_profile"],
    "real_estate_dashboard_v1": ["study", "playlist_slide", "metrics", "brand_profile"],
    "microzones_map_table_v1": ["study", "playlist_slide", "microzones", "brand_profile"],
    "competition_dense_table_v1": ["study", "playlist_slide", "metrics", "sources", "brand_profile"],
    "regulation_focus_v1": ["study", "playlist_slide", "metrics", "sources", "brand_profile"],
    "swot_quadrants_v1": ["study", "playlist_slide", "scores", "metrics", "brand_profile"],
    "verdict_card_v1": ["study", "playlist_slide", "verdict", "scores", "brand_profile"],
    "action_plan_timeline_v1": ["study", "playlist_slide", "verdict", "qa_results", "brand_profile"],
}


FALLBACK_PROPS = ["study", "playlist_slide", "brand_profile"]



def _frontend_name(component_name: str) -> str:
    return "Stella" + "".join(part.capitalize() for part in component_name.split("_"))



def build_frontend_component_map() -> dict:
    items = []
    for section in SECTION_REGISTRY:
        component = section["component_main"]
        fallback = section.get("component_fallback")
        items.append(
            {
                "section_id": section["section_id"],
                "component": component,
                "frontend_component": _frontend_name(component),
                "fallback_component": fallback,
                "frontend_fallback_component": _frontend_name(fallback) if fallback else None,
                "props_required": DEFAULT_PROPS_BY_COMPONENT.get(component, FALLBACK_PROPS),
                "render_types": [str(r) for r in section["render_types"]],
            }
        )

    return {
        "version": "1.0.0",
        "resolver": "section_registry.component_main -> frontend_component",
        "items": items,
    }
