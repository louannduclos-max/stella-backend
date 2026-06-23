"""
Export PPTX pixel-perfect depuis un payload slides_5_0.

Conversion : px (canvas 1920×1080) → EMU (English Metric Units)
  1 px à 96 dpi → 1 pt → 12700 EMU
  PPTX 16:9 standard = 12192000 × 6858000 EMU
  Scale X = 12192000 / 1920 = 6350 EMU/px
  Scale Y = 6858000 / 1080 = 6350 EMU/px  ← identique (format carré EMU/px)
"""

from __future__ import annotations

import io
import logging
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Pt

from app.api.schemas.common import Study
from app.services.slides_5_0_builder import build_slides_5_0_for_study

logger = logging.getLogger(__name__)

# Canvas PPTX 16:9 standard (EMU)
_SLIDE_W_EMU = 12192000
_SLIDE_H_EMU = 6858000

# Canvas Stella 5.0 (px)
_CANVAS_W_PX = 1920
_CANVAS_H_PX = 1080

# Facteur de conversion px → EMU
_PX_TO_EMU = _SLIDE_W_EMU / _CANVAS_W_PX  # = 6350.0


def _px(value: float | int | None, fallback: int = 0) -> Emu:
    """Convertit des pixels canvas Stella en EMU PPTX."""
    if value is None:
        return Emu(fallback * _PX_TO_EMU)
    return Emu(int(value * _PX_TO_EMU))


def _hex_to_rgb(hex_color: str | None) -> RGBColor | None:
    """Parse '#RRGGBB' → RGBColor. Retourne None si invalide."""
    if not hex_color:
        return None
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return None
    try:
        return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except ValueError:
        return None


# Couleurs par défaut (fond sombre Stella)
_DARK_BG = RGBColor(0x0A, 0x10, 0x1A)   # #0A101A
_LIGHT_BG = RGBColor(0xFF, 0xFF, 0xFF)   # #FFFFFF
_DEFAULT_TEXT_DARK = RGBColor(0xE2, 0xE8, 0xF0)   # slide sombre → texte clair
_DEFAULT_TEXT_LIGHT = RGBColor(0x1E, 0x29, 0x3B)  # slide claire → texte sombre


def _add_text_box(slide: Any, obj: dict, is_dark_bg: bool) -> None:
    """Ajoute un objet textbox sur le slide PPTX."""
    text = obj.get("text") or ""
    style = obj.get("style") or {}

    left = _px(obj.get("left"))
    top = _px(obj.get("top"))
    width = _px(obj.get("width", 200))
    height = _px(obj.get("height", 40))

    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True

    # Children (texte hiérarchisé)
    children = obj.get("children") or []
    if children:
        for i, child in enumerate(children):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            run = p.add_run()
            run.text = child.get("text") or ""
            child_style = child.get("style") or {}
            _apply_run_style(run, child_style, is_dark_bg)
    else:
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = text
        _apply_run_style(run, style, is_dark_bg)


def _apply_run_style(run: Any, style: dict, is_dark_bg: bool) -> None:
    """Applique font-size, color, bold, italic à un run PPTX."""
    font = run.font

    # Taille : fontSize (px) → Pt (1px ≈ 0.75pt à 96dpi)
    font_size_px = style.get("fontSize") or style.get("font_size")
    if font_size_px:
        try:
            font.size = Pt(float(str(font_size_px).replace("px", "").strip()) * 0.75)
        except (ValueError, TypeError):
            pass

    # Couleur
    color_val = style.get("color") or style.get("colour")
    rgb = _hex_to_rgb(str(color_val)) if color_val else None
    if rgb:
        font.color.rgb = rgb
    else:
        font.color.rgb = _DEFAULT_TEXT_DARK if is_dark_bg else _DEFAULT_TEXT_LIGHT

    # Graisse
    font_weight = style.get("fontWeight") or style.get("font_weight", "")
    if str(font_weight) in ("700", "bold"):
        font.bold = True

    # Italique
    if style.get("fontStyle") == "italic":
        font.italic = True


def _add_shape(slide: Any, obj: dict, css_vars: dict, is_dark_bg: bool) -> None:
    """
    Ajoute un rectangle coloré (shape background) + rend les children comme text boxes.

    Les shapes Stella (KPI cards, hero-identity, timeline steps) contiennent des children
    (label / value / trend / zone_name / verdict / narrative…) qui sont emboîtés dans le shape.
    En PPTX, on les rend comme text boxes positionnés à l'intérieur du shape.
    """
    from pptx.util import Emu as _E
    from pptx.enum.shapes import MSO_SHAPE_TYPE  # noqa: F401

    left_px: int = obj.get("left") or 0
    top_px: int = obj.get("top") or 0
    width_px: int = obj.get("width") or 100
    height_px: int = obj.get("height") or 100

    left = _px(left_px)
    top = _px(top_px)
    width = _px(width_px)
    height = _px(height_px)

    style = obj.get("style") or {}
    bg_color_raw = style.get("backgroundColor") or style.get("background")

    # Résolution des CSS vars (ex: "var(--stella-primary)")
    if bg_color_raw and str(bg_color_raw).startswith("var("):
        var_name = str(bg_color_raw)[4:-1]  # strip "var(" and ")"
        bg_color_raw = css_vars.get(var_name, "#1A5BA0")

    rgb = _hex_to_rgb(str(bg_color_raw)) if bg_color_raw else None

    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        left, top, width, height,
    )
    shape.line.fill.background()  # pas de bordure

    if rgb:
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb
    else:
        shape.fill.background()

    # --- Rendu des children (label / value / trend / zone_name / verdict / narrative…) ---
    # Les children sont empilés verticalement dans les limites du shape.
    # Chaque child produit une text box positionnée absolument dans le shape.
    children = obj.get("children") or []
    if children:
        _INNER_PAD_PX = 16   # padding interne horizontal
        _CHILD_GAP_PX = 6    # espacement vertical entre children

        # Estimation de hauteur par child selon font_size
        def _child_h(child_style: dict) -> int:
            fs = child_style.get("font_size") or child_style.get("fontSize") or 18
            try:
                fs = int(float(str(fs).replace("px", "").strip()))
            except (ValueError, TypeError):
                fs = 18
            return max(24, int(fs * 1.6))

        # Répartition verticale : on empile les children en commençant en haut du shape
        cursor_top_px = top_px + _INNER_PAD_PX
        for child in children:
            child_text = child.get("text") or ""
            if not child_text:
                continue
            child_style = child.get("style") or {}
            margin_top = child_style.get("margin_top") or 0
            child_height_px = _child_h(child_style)
            cursor_top_px += margin_top

            child_obj = {
                "left": left_px + _INNER_PAD_PX,
                "top": cursor_top_px,
                "width": width_px - 2 * _INNER_PAD_PX,
                "height": child_height_px,
                "text": child_text,
                "style": child_style,
            }
            _add_text_box(slide, child_obj, is_dark_bg)
            cursor_top_px += child_height_px + _CHILD_GAP_PX


def _apply_slide_background(prs_slide: Any, background: str, css_vars: dict) -> None:
    """Colore le fond du slide (dark / light)."""
    from pptx.oxml.ns import qn
    import lxml.etree as etree

    is_dark = background == "dark"
    bg_hex = css_vars.get("--stella-bg", "#0A101A") if is_dark else "#FFFFFF"
    rgb = _hex_to_rgb(bg_hex) or (_DARK_BG if is_dark else _LIGHT_BG)

    bg = prs_slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = rgb


def build_pptx_for_study(study: Study) -> bytes:
    """
    Génère un fichier .pptx en mémoire depuis une Study Stella 5.0.
    Retourne les bytes du fichier PPTX.
    """
    payload = build_slides_5_0_for_study(study)
    slides_data = payload.get("slides", [])
    css_vars_dict: dict = (payload.get("css_vars") or {}).get("variables") or {}

    prs = Presentation()
    prs.slide_width = Emu(_SLIDE_W_EMU)
    prs.slide_height = Emu(_SLIDE_H_EMU)

    # Layout vide (blank)
    blank_layout = prs.slide_layouts[6]

    for slide_info in slides_data:
        prs_slide = prs.slides.add_slide(blank_layout)
        background = slide_info.get("background", "dark")
        is_dark = background == "dark"

        # Fond du slide
        _apply_slide_background(prs_slide, background, css_vars_dict)

        # Objets positionnés
        objects = slide_info.get("objects") or []
        for obj in objects:
            obj_type = obj.get("data_object_type", "textbox")
            try:
                if obj_type == "textbox":
                    _add_text_box(prs_slide, obj, is_dark)
                elif obj_type == "shape":
                    _add_shape(prs_slide, obj, css_vars_dict, is_dark)
                # chart et image → placeholder texte (P1)
                elif obj_type in ("chart", "image", "icon"):
                    _add_text_box(
                        prs_slide,
                        {**obj, "text": f"[{obj_type.upper()}]", "children": []},
                        is_dark,
                    )
            except Exception as exc:
                logger.warning("[pptx] objet %s ignoré : %s", obj.get("id"), exc)

        # Notes du slide = section_id + titre
        notes_slide = prs_slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = f"{slide_info.get('section_id', '')} — {slide_info.get('title', '')}"

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()
