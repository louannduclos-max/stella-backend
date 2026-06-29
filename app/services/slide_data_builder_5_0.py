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


def _swot_bullets_from_data(study: Study, quadrant: str) -> List[str]:
    """
    Chantier C — Génère des bullets SWOT argumentés depuis les données réelles.
    Logique déterministe (pas de LLM) — fallback si Slide Builder Agent non disponible.
    Chaque bullet = 1 fait chiffré + son implication business (max 15 mots).
    """
    by_id = {m.metric_id: m for m in study.metrics}

    def val(metric_id: str) -> str | None:
        m = by_id.get(metric_id)
        if m is None:
            return None
        v = m.value
        u = m.unit or ""
        return f"{v}{u}" if v is not None and v != "" else None

    if quadrant == "forces":
        bullets: List[str] = []
        if v := val("seniors_60_plus_share"):
            bullets.append(f"{v} de seniors — marché adressable en expansion structurelle")
        if v := val("median_income"):
            bullets.append(f"Revenu médian {v} — capacité de paiement confirmée")
        if v := val("population_total"):
            bullets.append(f"{v} habitants dans la zone — densité suffisante")
        if v := val("taxable_households_share"):
            bullets.append(f"{v} de foyers imposables — tissu CSP+ présent")
        return bullets or ["Attractivité démographique favorable"]

    elif quadrant == "opportunites":
        bullets = []
        if v := val("competitor_count_15min"):
            bullets.append(f"Seulement {v} concurrents en 15 min — marché peu saturé")
        if v := val("real_estate_price_house_m2"):
            bullets.append(f"Immobilier à {v} — zone accessible aux franchisés")
        if v := val("population_growth_5y"):
            bullets.append(f"Croissance population {v} — dynamique démographique positive")
        bullets.append("Aucune offre premium positionnée sur la zone")
        return bullets

    elif quadrant == "faiblesses":
        bullets = []
        if v := val("unemployment_rate"):
            bullets.append(f"Taux de chômage {v} — recrutement à anticiper")
        if v := val("car_dependency_share"):
            bullets.append(f"Dépendance voiture {v} — politique mobilité RH nécessaire")
        if v := val("care_worker_pool"):
            bullets.append(f"Bassin soins {v} pers. — marché du travail tendu sur ce profil")
        return bullets or ["Bassin d'emploi à consolider"]

    elif quadrant == "menaces":
        bullets = []
        if v := val("competitor_count_15min"):
            bullets.append(f"{v} acteurs existants — veille concurrentielle recommandée")
        if v := val("franchise_brand_count"):
            bullets.append(f"{v} franchises nationales présentes — notoriété à construire")
        bullets.append("Complexité réglementaire SAAD — agrément départemental requis")
        return bullets or ["Environnement réglementaire à surveiller"]

    return []


def _swot_quadrants(study: Study) -> List[Dict[str, Any]]:
    # Fix 1 — mapper sur les vrais score_ids : scr_{name} (ex: scr_market_attractiveness)
    score_by_id = {s.score_id: s for s in study.scores}

    mapping = [
        ("Forces",       "forces",       ["scr_market_attractiveness", "scr_premium_potential", "scr_recurring_revenue_potential"]),
        ("Faiblesses",   "faiblesses",   ["scr_execution_risk", "scr_rh_feasibility"]),
        ("Opportunités", "opportunites", ["scr_recurring_revenue_potential", "scr_premium_potential"]),
        ("Menaces",      "menaces",      ["scr_competitive_pressure", "scr_regulatory_complexity"]),
    ]

    quadrants: List[Dict[str, Any]] = []
    for quadrant_label, quadrant_key, candidates in mapping:
        score = None
        for sid in candidates:
            if sid in score_by_id:
                score = score_by_id[sid]
                break
        # Chantier C — bullets déterministes depuis les métriques réelles
        bullets = _swot_bullets_from_data(study, quadrant_key)
        if score:
            quadrants.append({
                "label": quadrant_label,
                "value": f"{round(score.value)}/100",
                "trend": score.label,        # nom lisible du score (ex : "Attractivité marché")
                "fallback_used": False,
                "bullets": bullets,          # nouveauté Sprint 2
            })
        else:
            quadrants.append({
                "label": quadrant_label,
                "value": "Non calculé",
                "trend": None,
                "fallback_used": True,
                "bullets": bullets,
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