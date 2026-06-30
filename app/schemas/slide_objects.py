"""
Schéma unique des objets de slide. Tous les renderers (PPTX, HTML, React)
doivent consommer EXACTEMENT cette forme. Tout objet qui ne valide pas
est retiré (avec log), jamais affiché à moitié ou cassé.
"""
import logging
from typing import Any, Literal

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

ObjectType = Literal[
    "textbox", "shape", "kpi_card", "swot_quadrant", "bullet_list",
    "score_badge", "verdict_badge", "score_bars", "competitor_card",
    "highlight_box", "kpi_list", "chart_native",
]

# Limites canvas — un objet hors de ces bornes est invalide
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
SAFE_MARGIN = 80
_OVERFLOW_TOLERANCE = 40  # tolérance 40 px pour les arrondis


class SlideChild(BaseModel):
    role: str | None = None
    text: str | None = None
    style: dict[str, Any] | None = None


class SlideObject(BaseModel):
    id: str
    data_object: bool = True
    data_object_type: ObjectType
    left: int
    top: int
    width: int
    height: int
    text: str | None = None
    style: dict[str, Any] | None = None
    children: list[SlideChild] | None = None
    items: list[dict[str, Any]] | None = None
    chart_id: str | None = None
    chart_data: dict[str, Any] | None = None
    fill_with_narrative: bool | None = None
    max_chars: int | None = None
    narrative_role: str | None = None
    source: Literal["deterministic", "agent"] | None = "deterministic"


def validate_slide_objects(raw_objects: list[dict]) -> list[dict]:
    """
    Valide chaque objet contre le schéma Pydantic.
    Retire silencieusement (avec log) tout objet malformé ou hors canvas.
    Ne lève jamais d'exception — un objet invalide ne doit jamais
    faire planter la génération d'une étude entière.
    """
    valid: list[dict] = []
    for raw in raw_objects:
        try:
            obj = SlideObject.model_validate(raw)
        except ValidationError as e:
            logger.warning("[schema] Objet rejeté (%s) : %s", raw.get("id", "?"), e)
            continue

        if obj.top + obj.height > CANVAS_HEIGHT - SAFE_MARGIN + _OVERFLOW_TOLERANCE:
            logger.warning("[schema] Objet hors canvas (bas) : %s", obj.id)
            continue
        if obj.left + obj.width > CANVAS_WIDTH - SAFE_MARGIN + _OVERFLOW_TOLERANCE:
            logger.warning("[schema] Objet hors canvas (droite) : %s", obj.id)
            continue

        valid.append(obj.model_dump(exclude_none=True))
    return valid
