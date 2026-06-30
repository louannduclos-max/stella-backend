from typing import Any, Dict, List

from app.api.schemas.common import Study


FALLBACK = "Donnee non disponible (TBD)"


def _format_metric(metric):
    if not metric:
        return {"label": FALLBACK, "value": FALLBACK, "trend": None, "fallback_used": True, "confidence_grade": "E"}
    value = metric.get("value")
    unit = metric.get("unit") or ""
    text_value = f"{value}{unit}" if value is not None and value != "" else FALLBACK
    fallback_used = bool(metric.get("fallback_used", False))
    return {
        "label": metric.get("label") or metric.get("name") or FALLBACK,
        "value": text_value,
        "trend": "Source : estimation nationale" if fallback_used else None,
        "fallback_used": fallback_used,
        "confidence_grade": metric.get("confidence_grade", "C"),
    }


def _format_verdict(verdict) -> str:
    if verdict is None:
        return "Non determine"
    val = verdict.value if hasattr(verdict, "value") else str(verdict)
    val = val.split(".")[-1]
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


def _swot_bullets_from_data(study: Study, quadrant: str) -> List[str]:
    by_id = {m.metric_id: m for m in study.metrics}

    def val(metric_id: str):
        m = by_id.get(metric_id)
        if m is None:
            return None
        v = m.value
        u = m.unit or ""
        return f"{v}{u}" if v is not None and v != "" else None

    if quadrant == "forces":
        bullets: List[str] = []
        if v := val("seniors_60_plus_share"):
            bullets.append(f"{v} de seniors -- marche adressable en expansion structurelle")
        if v := val("median_income"):
            bullets.append(f"Revenu median {v} -- capacite de paiement confirmee")
        if v := val("population_total"):
            bullets.append(f"{v} habitants dans la zone -- densite suffisante")
        if v := val("taxable_households_share"):
            bullets.append(f"{v} de foyers imposables -- tissu CSP+ present")
        return bullets or ["Attractivite demographique favorable"]

    elif quadrant == "opportunites":
        bullets = []
        if v := val("competitor_count_15min"):
            bullets.append(f"Seulement {v} concurrents en 15 min -- marche peu sature")
        if v := val("real_estate_price_house_m2"):
            bullets.append(f"Immobilier a {v} -- zone accessible aux franchises")
        if v := val("population_growth_5y"):
            bullets.append(f"Croissance population {v} -- dynamique demographique positive")
        bullets.append("Aucune offre premium positionnee sur la zone")
        return bullets

    elif quadrant == "faiblesses":
        bullets = []
        if v := val("unemployment_rate"):
            bullets.append(f"Taux de chomage {v} -- recrutement a anticiper")
        if v := val("car_dependency_share"):
            bullets.append(f"Dependance voiture {v} -- politique mobilite RH necessaire")
        if v := val("care_worker_pool"):
            bullets.append(f"Bassin soins {v} pers. -- marche du travail tendu sur ce profil")
        return bullets or ["Bassin d'emploi a consolider"]

    elif quadrant == "menaces":
        bullets = []
        if v := val("competitor_count_15min"):
            bullets.append(f"{v} acteurs existants -- veille concurrentielle recommandee")
        if v := val("franchise_brand_count"):
            bullets.append(f"{v} franchises nationales presentes -- notoriete a construire")
        bullets.append("Complexite reglementaire SAAD -- agrement departemental requis")
        return bullets or ["Environnement reglementaire a surveiller"]

    return []


def _swot_quadrants(study: Study) -> List[Dict[str, Any]]:
    score_by_id = {s.score_id: s for s in study.scores}
    mapping = [
        ("Forces",       "forces",       ["scr_market_attractiveness", "scr_premium_potential", "scr_recurring_revenue_potential"]),
        ("Faiblesses",   "faiblesses",   ["scr_execution_risk", "scr_rh_feasibility"]),
        ("Opportunites", "opportunites", ["scr_recurring_revenue_potential", "scr_premium_potential"]),
        ("Menaces",      "menaces",      ["scr_competitive_pressure", "scr_regulatory_complexity"]),
    ]
    quadrants: List[Dict[str, Any]] = []
    for quadrant_label, quadrant_key, candidates in mapping:
        score = None
        for sid in candidates:
            if sid in score_by_id:
                score = score_by_id[sid]
                break
        bullets = _swot_bullets_from_data(study, quadrant_key)
        if score:
            quadrants.append({"label": quadrant_label, "value": f"{round(score.value)}/100",
                "trend": score.label, "fallback_used": False, "bullets": bullets})
        else:
            quadrants.append({"label": quadrant_label, "value": "Non calcule",
                "trend": None, "fallback_used": True, "bullets": bullets})
    return quadrants


def _action_steps(study: Study) -> List[Dict[str, Any]]:
    n = study.narratives or {}
    return [
        {"label": "30 jours", "value": n.get("action_30d") or FALLBACK, "trend": None},
        {"label": "60 jours", "value": n.get("action_60d") or FALLBACK, "trend": None},
        {"label": "90 jours", "value": n.get("action_90d") or FALLBACK, "trend": None},
    ]


def build_slide_data_5_0(study: Study, section_id: str, expected_kpis: List[str], display_name: str | None = None) -> Dict[str, Any]:
    title = display_name or section_id.replace("_", " ").title()
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
        base.update({"hero_kpis": _hero_kpis(study, expected_kpis)})

    elif section_id in {"target_segments", "competition_mapping"}:
        base.update({"columns": _columns(study, expected_kpis)})

    elif section_id == "swot":
        quadrants_data = _swot_quadrants(study)
        swot_chart_categories = [q["label"] for q in quadrants_data]
        swot_chart_values = []
        for q in quadrants_data:
            v = q.get("value", "0/100")
            try:
                swot_chart_values.append(float(str(v).split("/")[0]))
            except (ValueError, TypeError):
                swot_chart_values.append(0.0)
        base.update({
            "quadrants": quadrants_data,
            "swot_chart_data": {
                "type": "bar",
                "categories": swot_chart_categories,
                "values": swot_chart_values,
                "title": "Scores SWOT",
            } if any(v > 0 for v in swot_chart_values) else None,
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
            "metrics": all_metrics[:3],
            "metrics_extended": all_metrics,
            "chart_id": section_id,
            "narrative_text": n.get("exec_summary") or "",
        })

    elif section_id == "action_plan":
        base.update({"steps": _action_steps(study)})

    elif section_id == "demographics":
        by_id = _metrics_by_id(study)
        all_metrics = [_format_metric(by_id.get(m)) for m in expected_kpis]
        seniors_metric = by_id.get("seniors_60_plus_share")
        demo_chart_data = None
        if seniors_metric and seniors_metric.get("value") is not None:
            try:
                seniors_share = float(seniors_metric["value"])
                if 0 < seniors_share < 100:
                    demo_chart_data = {
                        "type": "pie",
                        "categories": ["60 ans et +", "Moins de 60 ans"],
                        "values": [seniors_share, round(100 - seniors_share, 1)],
                        "title": "Repartition par age",
                    }
            except (TypeError, ValueError):
                pass
        base.update({
            "metrics": all_metrics[:3],
            "metrics_extended": all_metrics,
            "chart_id": section_id,
            "demographics_chart_data": demo_chart_data,
        })

    else:
        by_id = _metrics_by_id(study)
        all_metrics = [_format_metric(by_id.get(m)) for m in expected_kpis]
        base.update({
            "metrics": all_metrics[:3],
            "metrics_extended": all_metrics,
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
                    if isinstance(item, dict):
                        for v in item.values():
                            if isinstance(v, str):
                                strings.append(v)
    return strings
