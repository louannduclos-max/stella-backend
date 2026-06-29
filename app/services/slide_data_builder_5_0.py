from typing import Any, Dict, List

from app.api.schemas.common import Study


FALLBACK = "Donnée non disponible (TBD)"


def _format_metric(metric: Dict[str, Any] | None) -> Dict[str, Any]:
    if not metric:
        return {"label": FALLBACK, "value": FALLBACK, "trend": None, "fallback_used": True, "confidence_grade": "E"}
    value = metric.get("value")
    unit = metric.get("unit") or ""
    text_value = f"{value}{unit}" if value is not None and value != "" else FALLBACK
    fallback_used = bool(metric.get("fallback_used", False))
    return {
        "label": metric.get("label") or metric.get("name") or FALLBACK,
        "value": text_value,
        # Fix 4 — masquer les messages d'erreur techniques ; badge "estimation" suffit côté UI
        "trend": "Source : estimation nationale" if fallback_used else None,
        "fallback_used": fallback_used,
        "confidence_grade": metric.get("confidence_grade", "C"),
    }


def _format_verdict(verdict) -> str:
    """Fix 3 — normalise VerdictEnum → label lisible ('NO GO', 'GO', 'GO CONDITIONAL')."""
    if verdict is None:
        return "Non déterminé"
    # VerdictEnum(str, Enum) : .value = "GO" | "GO_CONDITIONAL" | "NO_GO"
    val = verdict.value if hasattr(verdict, "value") else str(verdict)
    val = val.split(".")[-1]   # strip éventuel préfixe "VerdictEnum."
    return val.replace("_", " ")


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
    # Fix 1 — mapper sur les vrais score_ids : scr_{name} (ex: scr_market_attractiveness)
    score_by_id = {s.score_id: s for s in study.scores}

    mapping = [
        ("Forces",       ["scr_market_attractiveness", "scr_premium_potential", "scr_recurring_revenue_potential"]),
        ("Faiblesses",   ["scr_execution_risk", "scr_rh_feasibility"]),
        ("Opportunités", ["scr_recurring_revenue_potential", "scr_premium_potential"]),
        ("Menaces",      ["scr_competitive_pressure", "scr_regulatory_complexity"]),
    ]

    quadrants: List[Dict[str, Any]] = []
    for quadrant_label, candidates in mapping:
        score = None
        for sid in candidates:
            if sid in score_by_id:
                score = score_by_id[sid]
                break
        if score:
            quadrants.append({
                "label": quadrant_label,
                "value": f"{round(score.value)}/100",
                "trend": score.label,        # nom lisible du score (ex : "Attractivité marché")
                "fallback_used": False,
            })
        else:
            quadrants.append({
                "label": quadrant_label,
                "value": "Non calculé",
                "trend": None,
                "fallback_used": True,
            })
    return quadrants


def _action_steps(study: Study) -> List[Dict[str, Any]]:
    n = study.narratives or {}
    return [
        {"label": "30 jours", "value": n.get("action_30d") or FALLBACK, "trend": None},
        {"label": "60 jours", "value": n.get("action_60d") or FALLBACK, "trend": None},
        {"label": "90 jours", "value": n.get("action_90d") or FALLBACK, "trend": None},
    ]


def build_slide_data_5_0(study: Study, section_id: str, expected_kpis: List[str], display_name: str | None = None) -> Dict[str, Any]:
    # FIX: utiliser display_name depuis section_registry (FR) plutôt qu'auto-générer
    # depuis section_id en anglais ("Employment Talent" → "Emploi & vivier RH").
    title = display_name or section_id.replace("_", " ").title()
    # Fix 3 — normaliser le verdict (évite "VerdictEnum.NO_GO")
    verdict_str = _format_verdict(study.verdict)
    base = {
        "title": title,
        "eyebrow": (study.geo_scope.city or FALLBACK).upper(),
        "zone_name": study.geo_scope.city or FALLBACK,
        "verdict_label": verdict_str,
        "score_label": verdict_str,
        "source_label": "Source : INSEE / Stella Engine",
    }

    n = study.narratives or {}
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
            "narrative_text": n.get("verdict_narrative") or "",
        })
    elif section_id == "executive_summary":
        by_id = _metrics_by_id(study)
        all_metrics = [_format_metric(by_id.get(m)) for m in expected_kpis]
        base.update({
            "metrics": all_metrics[:3],           # sidebar droite (3 KPI cards)
            "metrics_extended": all_metrics,       # Fix 2 — liste complète zone gauche
            "chart_id": section_id,
            "narrative_text": n.get("exec_summary") or "",
        })
    elif section_id == "action_plan":
        base.update({
            "steps": _action_steps(study),
        })
    else:
        # Fix 2 — toutes les métriques disponibles pour la zone gauche (kpi_list)
        by_id = _metrics_by_id(study)
        all_metrics = [_format_metric(by_id.get(m)) for m in expected_kpis]
        base.update({
            "metrics": all_metrics[:3],           # sidebar droite (3 KPI cards)
            "metrics_extended": all_metrics,       # zone gauche : liste complète
            "chart_id": section_id,
        })
    return base


def collect_expected_strings(slide_data: Dict[str, Any]) -> List[str]:
    strings: List[str] = []
    if isinstance(slide_data, dict):
        for key, value in slide_data.items():
            if isinstance(value, str):
                strings.ap