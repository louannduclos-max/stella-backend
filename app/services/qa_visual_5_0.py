CONTRACT_5_0 = {
    "version": "5.0.0",
    "canvas": {"width": 1920, "height": 1080},
    "safe_margin_px": 80,
    "grid_step_px": 20,
    "typography": {
        "title_min_px": 42,
        "title_default_px": 48,
        "title_weight": 700,
        "kpi_value_min_px": 64,
        "kpi_value_default_px": 72,
        "kpi_value_weight": 800,
        "kpi_label_px": 14,
        "body_min_px": 24,
        "body_weight": 400,
        "metadata_min_px": 12,
        "metadata_max_px": 16,
    },
    "spacing": {
        "min_vertical_gap_px": 24,
        "min_horizontal_gap_px": 40,
    },
    "whitespace": {
        "min_ratio": 0.35,
        "max_occupied_ratio": 0.65,
    },
    "ratios_allowed": ["70/30", "60/40", "40/30/30", "4quadrants", "timeline_3steps"],
    "kpi_rules": {
        "max_cover": 6,
        "max_analytic": 3,
        "card": {
            "border_radius_px": 8,
            "padding_px": 30,
            "border": "1px solid rgba(226, 232, 240, 0.8)",
        },
    },
    "contrast": {
        "body_min_apca": 4.5,
        "title_min_apca": 3.0,
        "standard": "APCA + WCAG AA",
    },
    "checks": [
        "overlap_geometry",
        "contrast_apca",
        "dom_manifest_text_consistency",
    ],
    "anti_patterns_forbidden": [
        "left_accent_rounded_border",
        "hidden_text",
        "clickable_hyperlinks",
        "system_default_fonts_without_fallback",
        "relative_positioning_on_slide_container",
        "fluid_percentages_on_slide_container",
        "hardcoded_text_in_layouts",
    ],
    "fallbacks": {
        "missing_value_label": "Donnée non disponible (TBD)",
        "font_fallback_chain": "Inter, 'IBM Plex Sans', Arial, sans-serif",
    },
    "rebut_conditions": [
        "relative_positioning_on_slide_container",
        "whitespace_below_35_percent",
        "text_or_number_absent_from_manifest",
        "raw_markdown_in_dom",
        "title_below_42_px",
        "body_below_24_px",
    ],
    "self_healing_hooks": {
        "text_overflow_step_px": 2,
        "text_overflow_min_body_px": 24,
        "overlap_translation_safety_px": 20,
    },
    "outputs": {
        "html_is_source_of_truth": True,
        "pptx_pixel_perfect_from_html": True,
        "pdf_canvas_1920x1080_margin_0": True,
    },
}


def get_qa_visual_5_0_contract() -> dict:
    return CONTRACT_5_0
