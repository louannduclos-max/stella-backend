import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
SAFE_MARGIN = 80
HEADER_TOP = 60
TITLE_TOP = 90
# SEPARATOR_TOP supprime (Sprint 5 - trait = marqueur visuel IA)
CONTENT_TOP_DEFAULT = 200
GRID_STEP = 20
MIN_VERTICAL_GAP = 24
MIN_HORIZONTAL_GAP = 40
WHITESPACE_MAX_OCCUPIED_RATIO = 0.65


def _header_objects(eyebrow: str, title: str) -> List[Dict[str, Any]]:
    return [
        {
            "id": "slide-eyebrow",
            "data_object": True,
            "data_object_type": "textbox",
            "left": SAFE_MARGIN,
            "top": HEADER_TOP,
            "width": CANVAS_WIDTH - 2 * SAFE_MARGIN,
            "height": 24,
            "text": eyebrow,
            "style": {"font_size": 16, "font_weight": 500, "color": "var(--text-muted)", "text_transform": "uppercase", "letter_spacing": "0.05em"},
        },
        {
            "id": "slide-title",
            "data_object": True,
            "data_object_type": "textbox",
            "left": SAFE_MARGIN,
            "top": TITLE_TOP,
            "width": CANVAS_WIDTH - 2 * SAFE_MARGIN,
            "height": 50,
            "text": title,
            "style": {"font_size": 48, "font_weight": 700, "color": "var(--primary-color)"},
        },
    ]


def _kpi_card(idx, left, top, width, height, label, value, trend, fallback_used=False):
    children = [
        {"role": "label", "text": label, "style": {"font_size": 14, "font_weight": 500, "color": "var(--text-muted)", "text_transform": "uppercase"}},
        {"role": "value", "text": value, "style": {"font_size": 72, "font_weight": 800, "color": "var(--primary-color)"}},
    ]
    if trend:
        children.append({"role": "trend", "text": trend, "style": {"font_size": 20, "font_weight": 600, "color": "var(--secondary-color)"}})
    if fallback_used:
        children.append({"role": "badge", "text": "estimation", "style": {"font_size": 11, "font_weight": 600, "color": "var(--text-muted)", "text_transform": "uppercase", "letter_spacing": "0.08em"}})
    return {
        "id": f"kpi-card-{idx:02d}",
        "data_object": True,
        "data_object_type": "shape",
        "left": left, "top": top, "width": width, "height": height,
        "style": {"background": "var(--bg-light)", "border": "1px solid rgba(226, 232, 240, 0.8)", "border_radius": 8, "padding": 30},
        "children": children,
    }


def _layout_hero_split_6040(slide_data, background):
    title = slide_data.get("title") or "Donnee non disponible (TBD)"
    eyebrow = slide_data.get("eyebrow") or "STELLA"
    objects = _header_objects(eyebrow, title)
    content_top = CONTENT_TOP_DEFAULT
    left_width = int((CANVAS_WIDTH - 2 * SAFE_MARGIN) * 0.6) - MIN_HORIZONTAL_GAP // 2
    right_left = SAFE_MARGIN + left_width + MIN_HORIZONTAL_GAP
    right_width = CANVAS_WIDTH - SAFE_MARGIN - right_left
    children_hero = [
        {"role": "zone_name", "text": slide_data.get("zone_name") or "TBD", "style": {"font_size": 64, "font_weight": 800, "color": "var(--primary-color)"}},
        {"role": "verdict", "text": slide_data.get("verdict_label") or "TBD", "style": {"font_size": 28, "font_weight": 600, "color": "var(--secondary-color)"}},
        {"role": "score", "text": slide_data.get("score_label") or "TBD", "style": {"font_size": 18, "font_weight": 500, "color": "var(--text-muted)"}},
    ]
    if slide_data.get("narrative_text"):
        children_hero.append({"role": "narrative", "text": slide_data["narrative_text"], "style": {"font_size": 16, "font_weight": 400, "color": "var(--text-muted)", "margin_top": 32}})
    objects.append({
        "id": "hero-identity", "data_object": True, "data_object_type": "shape",
        "left": SAFE_MARGIN, "top": content_top, "width": left_width,
        "height": CANVAS_HEIGHT - content_top - SAFE_MARGIN,
        "style": {"background": "transparent"}, "children": children_hero,
    })
    metrics = (slide_data.get("hero_kpis") or [])[:6]
    available_height = CANVAS_HEIGHT - SAFE_MARGIN - content_top
    n = len(metrics) if metrics else 1
    card_height = max(80, (available_height - MIN_VERTICAL_GAP * (n - 1)) // n)
    cursor_top = content_top
    for idx, metric in enumerate(metrics, start=1):
        if cursor_top + card_height > CANVAS_HEIGHT - SAFE_MARGIN:
            break
        objects.append(_kpi_card(idx, right_left, cursor_top, right_width, card_height,
            metric.get("label") or "TBD", metric.get("value") or "TBD",
            metric.get("trend"), metric.get("fallback_used", False)))
        cursor_top += card_height + MIN_VERTICAL_GAP
    return objects


def _layout_sidebar_analysis_7030(slide_data):
    title = slide_data.get("title") or "Donnee non disponible (TBD)"
    eyebrow = slide_data.get("eyebrow") or "ANALYSE"
    objects = _header_objects(eyebrow, title)
    content_top = CONTENT_TOP_DEFAULT
    left_width = int((CANVAS_WIDTH - 2 * SAFE_MARGIN) * 0.7) - MIN_HORIZONTAL_GAP // 2
    right_left = SAFE_MARGIN + left_width + MIN_HORIZONTAL_GAP
    right_width = CANVAS_WIDTH - SAFE_MARGIN - right_left
    metrics_all = slide_data.get("metrics_extended") or slide_data.get("metrics") or []
    objects.append({
        "id": "analysis-kpi-list", "data_object": True, "data_object_type": "kpi_list",
        "left": SAFE_MARGIN, "top": content_top, "width": left_width,
        "height": CANVAS_HEIGHT - content_top - SAFE_MARGIN,
        "style": {"background": "var(--bg-light)", "border_radius": 8, "padding": 30},
        "items": metrics_all,
    })
    native_chart = slide_data.get("demographics_chart_data") or slide_data.get("swot_chart_data")
    metrics = (slide_data.get("metrics") or [])[:3]
    card_height = 180
    cursor_top = content_top
    if native_chart:
        chart_height = min(300, CANVAS_HEIGHT - content_top - SAFE_MARGIN - MIN_VERTICAL_GAP - card_height * 2)
        if chart_height > 100:
            objects.append({
                "id": "analysis-chart-native", "data_object": True, "data_object_type": "chart_native",
                "left": right_left, "top": cursor_top, "width": right_width, "height": chart_height,
                "chart_data": native_chart,
            })
            cursor_top += chart_height + MIN_VERTICAL_GAP
            metrics = metrics[:2]
    for idx, metric in enumerate(metrics, start=1):
        if cursor_top + card_height > CANVAS_HEIGHT - SAFE_MARGIN:
            break
        objects.append(_kpi_card(idx, right_left, cursor_top, right_width, card_height,
            metric.get("label") or "TBD", metric.get("value") or "TBD",
            metric.get("trend"), metric.get("fallback_used", False)))
        cursor_top += card_height + MIN_VERTICAL_GAP
    narrative_text = slide_data.get("narrative_text") or ""
    if narrative_text and cursor_top < CANVAS_HEIGHT - SAFE_MARGIN - 80:
        narrative_height = min(180, CANVAS_HEIGHT - SAFE_MARGIN - 60 - cursor_top - MIN_VERTICAL_GAP)
        if narrative_height > 40:
            objects.append({
                "id": "narrative-text", "data_object": True, "data_object_type": "textbox",
                "left": right_left, "top": cursor_top + MIN_VERTICAL_GAP,
                "width": right_width, "height": narrative_height,
                "text": narrative_text,
                "style": {"font_size": 13, "font_weight": 400, "color": "var(--text-muted)", "line_height": 1.5},
            })
            cursor_top += narrative_height + MIN_VERTICAL_GAP
    narrative_top = cursor_top + MIN_VERTICAL_GAP
    if narrative_top + 140 <= CANVAS_HEIGHT - SAFE_MARGIN - 60:
        objects.append({
            "id": "analysis-narrative", "data_object": True, "data_object_type": "textbox",
            "left": right_left, "top": narrative_top, "width": right_width, "height": 140,
            "text": "",
            "style": {"font_size": 14, "line_height": 1.5, "color": "var(--stella-text)"},
            "fill_with_narrative": True, "max_chars": 280, "narrative_role": "section_insight",
        })
        cursor_top = narrative_top + 140
    sources_top = max(cursor_top + MIN_VERTICAL_GAP, CANVAS_HEIGHT - SAFE_MARGIN - 60)
    objects.append({
        "id": "analysis-source", "data_object": True, "data_object_type": "textbox",
        "left": right_left, "top": sources_top, "width": right_width, "height": 40,
        "text": slide_data.get("source_label") or "Source : INSEE / Stella Engine",
        "style": {"font_size": 12, "font_weight": 400, "color": "var(--text-muted)"},
    })
    return objects


def _layout_grid_asymmetric_3columns(slide_data):
    title = slide_data.get("title") or "Donnee non disponible (TBD)"
    eyebrow = slide_data.get("eyebrow") or "SEGMENTS"
    objects = _header_objects(eyebrow, title)
    content_top = CONTENT_TOP_DEFAULT
    usable = CANVAS_WIDTH - 2 * SAFE_MARGIN - 2 * MIN_HORIZONTAL_GAP
    hero_width = int(usable * 0.4)
    side_width = int(usable * 0.3)
    columns = (slide_data.get("columns") or [{"label": "TBD", "value": "TBD"} for _ in range(3)])[:3]
    widths = [hero_width, side_width, side_width]
    cursor_left = SAFE_MARGIN
    for idx, column in enumerate(columns, start=1):
        col_width = widths[idx - 1] if idx - 1 < len(widths) else side_width
        objects.append(_kpi_card(idx, cursor_left, content_top, col_width,
            CANVAS_HEIGHT - content_top - SAFE_MARGIN,
            column.get("label") or "TBD", column.get("value") or "TBD",
            column.get("trend"), column.get("fallback_used", False)))
        cursor_left += col_width + MIN_HORIZONTAL_GAP
    return objects


def _swot_card(idx: int, left: int, top: int, width: int, height: int,
               label: str, value: str, description: str | None,
               bullets: list | None) -> Dict[str, Any]:
    """Carte SWOT avec bullets — remplace _kpi_card pour le slide SWOT."""
    children: List[Dict[str, Any]] = [
        {"role": "label", "text": label,
         "style": {"font_size": 16, "font_weight": 700, "color": "var(--primary-color)",
                   "text_transform": "uppercase", "letter_spacing": "0.05em"}},
        {"role": "score", "text": value,
         "style": {"font_size": 28, "font_weight": 800, "color": "var(--secondary-color)"}},
    ]
    if description:
        children.append({
            "role": "description", "text": description,
            "style": {"font_size": 13, "color": "var(--text-muted)"},
        })
    for bullet in (bullets or [])[:4]:
        children.append({
            "role": "bullet", "text": f"• {bullet}",
            "style": {"font_size": 13, "line_height": 1.5, "color": "var(--text-dark)"},
        })
    return {
        "id": f"swot-card-{idx:02d}",
        "data_object": True,
        "data_object_type": "shape",
        "left": left, "top": top, "width": width, "height": height,
        "style": {"background": "var(--bg-light)", "border": "1px solid rgba(226, 232, 240, 0.8)",
                  "border_radius": 8, "padding": 24},
        "children": children,
    }


def _layout_matrix_4quadrants(slide_data):
    title = slide_data.get("title") or "Donnee non disponible (TBD)"
    eyebrow = slide_data.get("eyebrow") or "SWOT"
    objects = _header_objects(eyebrow, title)
    content_top = CONTENT_TOP_DEFAULT
    gap = 40
    quadrant_width = (CANVAS_WIDTH - 2 * SAFE_MARGIN - gap) // 2
    quadrant_height = (CANVAS_HEIGHT - content_top - SAFE_MARGIN - gap) // 2
    quadrants = slide_data.get("quadrants") or [{}, {}, {}, {}]
    positions = [
        (SAFE_MARGIN, content_top),
        (SAFE_MARGIN + quadrant_width + gap, content_top),
        (SAFE_MARGIN, content_top + quadrant_height + gap),
        (SAFE_MARGIN + quadrant_width + gap, content_top + quadrant_height + gap),
    ]
    for idx, (pos, quadrant) in enumerate(zip(positions, quadrants), start=1):
        left, top = pos
        objects.append(_swot_card(
            idx=idx, left=left, top=top, width=quadrant_width, height=quadrant_height,
            label=quadrant.get("label") or "TBD",
            value=quadrant.get("value") or "TBD",
            description=quadrant.get("trend"),
            bullets=quadrant.get("bullets"),
        ))
    return objects


def _layout_timeline_horizontal_3steps(slide_data):
    title = slide_data.get("title") or "Donnee non disponible (TBD)"
    eyebrow = slide_data.get("eyebrow") or "PLAN D'ACTION"
    objects = _header_objects(eyebrow, title)
    content_top = CONTENT_TOP_DEFAULT + 20
    gap = 60
    step_width = (CANVAS_WIDTH - 2 * SAFE_MARGIN - 2 * gap) // 3
    steps = (slide_data.get("steps") or [{}, {}, {}])[:3]
    objects.append({
        "id": "timeline-axis", "data_object": True, "data_object_type": "shape",
        "left": SAFE_MARGIN, "top": content_top + 30,
        "width": CANVAS_WIDTH - 2 * SAFE_MARGIN, "height": 2,
        "style": {"background": "var(--primary-color)", "opacity": 0.6},
    })
    cursor_left = SAFE_MARGIN
    for idx, step in enumerate(steps, start=1):
        objects.append(_kpi_card(idx, cursor_left, content_top + 80, step_width,
            CANVAS_HEIGHT - (content_top + 80) - SAFE_MARGIN,
            step.get("label") or "TBD", step.get("value") or "TBD", step.get("trend")))
        cursor_left += step_width + gap
    return objects


LAYOUTS = {
    "Hero-Split-6040": _layout_hero_split_6040,
    "Sidebar-Analysis-7030": lambda d, bg=None: _layout_sidebar_analysis_7030(d),
    "Grid-Asymmetric-3Columns": lambda d, bg=None: _layout_grid_asymmetric_3columns(d),
    "Matrix-4Quadrants": lambda d, bg=None: _layout_matrix_4quadrants(d),
    "Timeline-Horizontal-3Steps": lambda d, bg=None: _layout_timeline_horizontal_3steps(d),
}

SLIDE_LAYOUT_BY_SECTION = {
    "cover": ("Hero-Split-6040", "dark"),
    "executive_summary": ("Sidebar-Analysis-7030", "light"),
    "methodology_sources": ("Sidebar-Analysis-7030", "light"),
    "market_scorecard": ("Sidebar-Analysis-7030", "light"),
    "demographics": ("Sidebar-Analysis-7030", "light"),
    "target_segments": ("Grid-Asymmetric-3Columns", "light"),
    "employment_talent": ("Sidebar-Analysis-7030", "light"),
    "income_housing": ("Sidebar-Analysis-7030", "light"),
    "real_estate": ("Sidebar-Analysis-7030", "light"),
    "microzones": ("Sidebar-Analysis-7030", "light"),
    "competition_mapping": ("Grid-Asymmetric-3Columns", "light"),
    "regulation_feasibility": ("Sidebar-Analysis-7030", "light"),
    "swot": ("Matrix-4Quadrants", "light"),
    "verdict": ("Hero-Split-6040", "dark"),
    "action_plan": ("Timeline-Horizontal-3Steps", "dark"),
}


def _compute_occupied_ratio(objects):
    CONTENT_IDS = {"hero-identity", "analysis-chart", "analysis-kpi-list", "analysis-chart-native", "timeline-axis"}
    surface = sum(
        obj["width"] * obj["height"]
        for obj in objects
        if obj["id"].startswith("kpi-card") or obj["id"] in CONTENT_IDS
    )
    return surface / float(CANVAS_WIDTH * CANVAS_HEIGHT)


def build_slide_5_0(section_id: str, slide_data: Dict[str, Any]) -> Dict[str, Any]:
    layout_name, background = SLIDE_LAYOUT_BY_SECTION.get(section_id, ("Sidebar-Analysis-7030", "light"))
    builder = LAYOUTS.get(layout_name) or LAYOUTS["Sidebar-Analysis-7030"]
    objects = builder(slide_data, background) if layout_name == "Hero-Split-6040" else builder(slide_data)
    safe_objects = []
    for obj in objects:
        bottom = obj.get("top", 0) + obj.get("height", 0)
        right = obj.get("left", 0) + obj.get("width", 0)
        if bottom > CANVAS_HEIGHT or right > CANVAS_WIDTH:
            logger.warning("[layout_engine] objet %s retire (debordement) bottom=%d right=%d section=%s",
                obj.get("id"), bottom, right, section_id)
            continue
        safe_objects.append(obj)
    occupied_ratio = _compute_occupied_ratio(safe_objects)
    return {
        "section_id": section_id,
        "layout": layout_name,
        "background": background,
        "canvas": {"width": CANVAS_WIDTH, "height": CANVAS_HEIGHT},
        "safe_margin": SAFE_MARGIN,
        "occupied_ratio": occupied_ratio,
        "whitespace_ratio": max(0.0, 1.0 - occupied_ratio),
        "whitespace_compliant": occupied_ratio <= WHITESPACE_MAX_OCCUPIED_RATIO,
        "objects": safe_objects,
    }
