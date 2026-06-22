from typing import Any, Dict, List

from app.api.schemas.common import Study


FALLBACK = "Donnée non disponible (TBD)"


def _format_metric(metric: Dict[str, Any] | None) -> Dict[str, Any]:
    if not metric:
        return {"label": FALLBACK, "value": FALLBACK, "trend": None}
    value = metric.get("value")
    unit = metric.get("unit") or ""
    text_value = f"{value}{unit}" if value is not None and value != "" else FALLBACK
    return {
        "label": metric.get("label") or metric.get("name") or FALLBACK,
        "value": text_value,
        "trend": metric.get("fallback_note") if metric.get("fallback_used") else None,
    }


def _metrics_by_id(study: Study) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for metric in study.metrics:
        out[metric.metric_id] = metric.model_dump(mode="json")
    return out


def _hero_kpis(study: Study, expected: List[str]) -> List[Dict[str, Any]]:
    by_id = _metrics_by_id(study)
    return [_format_metric(by_id.get(metric_id)) for metric_id in expected[:6]]


def _kpi_metrics(study: Study, expected: List[str]) -> List[Dict[str, Any]]:
    by_id = _metrics_by_id(study)
    return [_format_metric(by_id.get(metric_id)) for metric_id in expected[:3]]


def _columns(study: Study, expected: List[str]) -> List[Dict[str, Any]]:
    by_id = _metrics_by_id(study)
    return [_format_metric(by_id.get(metric_id)) for metric_id in expected[:3]]


def _swot_quadrants(study: Study) -> List[Dict[str, Any]]:
    score_by_id = {s.score_id: s for s in study.scores}
    quadrants: List[Dict[str, Any]] = []
    for key in ("strengths_score", "weaknesses_score", "opportunities_score", "threats_score"):
        if key in score_by_id:
            s = score_by_id[key]
            quadrants.append({"label": s.label, "value": f"{s.value}/100", "trend": s.confidence_grade})
        else:
            quadrants.append({"label": FALLBACK, "value": FALLBACK, "trend": None})
    return quadrants


def _action_steps(study: Study) -> List[Dict[str, Any]]:
    return [
        {"label": "30 jours", "value": FALLBACK, "trend": None},
        {"label": "60 jours", "value": FALLBACK, "trend": None},
        {"label": "90 jours", "value": FALLBACK, "trend": None},
    ]


def build_slide_data_5_0(study: Study, section_id: str, expected_kpis: List[str], display_name: str | None = None) -> Dict[str, Any]:
    # FIX: utiliser display_name depuis section_registry (FR) plutôt qu'auto-générer
    # depuis section_id en anglais ("Employment Talent" → "Emploi & vivier RH").
    title = display_name or section_id.replace("_", " ").title()
    base = {
        "title": title,
        "eyebrow": (study.geo_scope.city or FALLBACK).upper(),
        "zone_name": study.geo_scope.city or FALLBACK,
        "verdict_label": study.verdict or FALLBACK,
        "score_label": f"Verdict {study.verdict}" if study.verdict else FALLBACK,
        "source_label": "Source : INSEE / Stella Engine",
    }

    if section_id == "cover":
        base.update({
            "hero_kpis": _hero_kpis(study, expected_kpis),
        })
    elif section_id in {"target_segments", "competition_mapping"}:
        base.update({
            "columns": _columns(study, expected_kpis),
        })
    elif section_id == "swot":
        base.update({
            "quadrants": _swot_quadrants(study),
        })
    elif section_id == "verdict":
        base.update({
            "hero_kpis": _hero_kpis(study, expected_kpis),
        })
    elif section_id == "action_plan":
        base.update({
            "steps": _action_steps(study),
        })
    else:
        base.update({
            "metrics": _kpi_metrics(study, expected_kpis),
            "chart_id": section_id,
        })
    return base


def collect_expected_strings(slide_data: Dict[str, Any]) -> List[str]:
    strings: List[str] = []
    if isinstance(slide_data, dict):
        for key, value in slide_data.items():
            if isinstance(value, str):
                strings.append(value)
            elif isinstance(value, list):
                for item in value:
                    strings.extend(collect_expected_strings(item))
            elif isinstance(value, dict):
                strings.extend(collect_expected_strings(value))
    return [s for s in strings if s and s != FALLBACK]
