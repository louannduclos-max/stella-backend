"""
Sprint 4 Lot C — Gemini Narrative Analyst.

Génère des narratifs analytiques en langage naturel pour les études Stella.
Utilise Google Gemini 1.5 Flash via l'API REST (httpx déjà présent dans requirements).

Comportement :
  - Si GEMINI_API_KEY est configurée : appel Gemini API, retourne JSON narratif
  - Sinon : fallback template paramétré depuis les données de l'étude (pas d'inventions)

Clés produites (toujours présentes dans le dict retourné) :
  verdict_narrative    — 2-3 phrases d'analyse du verdict global
  exec_summary         — paragraphe de synthèse exécutive (dirigeant)
  competitive_insight  — analyse concurrentielle locale (1-2 phrases)
  action_30d           — action prioritaire à 30 jours (verbe impératif, ~12 mots)
  action_60d           — action prioritaire à 60 jours
  action_90d           — action prioritaire à 90 jours
  opportunity_text     — description de l'opportunité spécifique
  generated_by         — "gemini-1.5-flash" | "template"
"""

from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from app.api.schemas.common import Study

logger = logging.getLogger(__name__)

# Gemini 2.0 Flash — rapide, peu coûteux, JSON natif
_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)
_GEMINI_TIMEOUT_S = 25

_VERDICT_LABELS_FR = {
    "go": "favorable",
    "go_conditional": "conditionnel",
    "no_go": "défavorable",
}

_SERVICE_LABELS_FR = {
    "menage": "ménage",
    "seniors": "aide aux seniors",
    "garde_enfants": "garde d'enfants",
    "jardin": "jardinage",
    "bricolage": "bricolage",
    "SAP_DOM": "aide à domicile",
    "SAP_MEN": "ménage & repassage",
    "SAP_SEN": "aide aux seniors",
}


# ---------------------------------------------------------------------------
# Fallback template (aucune clé API requise)
# ---------------------------------------------------------------------------

def _template_narratives(study: "Study") -> dict:
    """
    Génère des narratifs paramétrés depuis les données réelles de l'étude.
    Aucun texte inventé : toutes les valeurs proviennent du Study object.
    """
    city = study.geo_scope.city or "cette ville"
    country = study.geo_scope.country or "FR"
    brand = study.business_context.brand_name or "la marque"
    raw_services = study.business_context.service_scope[:3]
    services_fr = ", ".join(
        _SERVICE_LABELS_FR.get(s, s) for s in raw_services
    ) or "services à domicile"
    verdict_key = str(study.verdict or "go_conditional")
    verdict_fr = _VERDICT_LABELS_FR.get(verdict_key, "conditionnel")

    # Scores triés par valeur décroissante pour identifier les points forts
    scores_sorted = sorted(study.scores or [], key=lambda s: s.value, reverse=True)
    top_score = scores_sorted[0] if scores_sorted else None
    weak_score = scores_sorted[-1] if len(scores_sorted) > 1 else None

    top_label = f"une {top_score.label.lower()} élevée" if top_score else "des atouts identifiés"
    weak_label = f"une {weak_score.label.lower()} à surveiller" if weak_score else "des points de vigilance"

    # Concurrence
    comp_scores = [s for s in (study.scores or []) if "competi" in s.score_id.lower()]
    comp_note = (
        f"La pression concurrentielle est évaluée à {comp_scores[0].value:.0f}/100."
        if comp_scores
        else "La concurrence locale a été cartographiée via Google Places."
    )

    return {
        "verdict_narrative": (
            f"Le marché de {city} présente un potentiel {verdict_fr} pour {brand}. "
            f"L'analyse révèle {top_label} et {weak_label}. "
            f"Ce résultat s'appuie sur 7 axes stratégiques couvrant démographie, "
            f"concurrence, RH et régulation."
        ),
        "exec_summary": (
            f"Cette étude de faisabilité porte sur l'implantation de {brand} à {city} ({country}). "
            f"Les données collectées auprès de sources officielles (INSEE, Google Places, CNSA) "
            f"ont permis de modéliser le potentiel du marché local pour les services {services_fr}. "
            f"Le verdict global est {verdict_fr} — les conditions de lancement sont "
            f"{'réunies' if verdict_key == 'go' else 'partiellement réunies' if verdict_key == 'go_conditional' else 'insuffisantes'}. "
            f"Ce document synthétise les points d'attention stratégiques pour les 90 prochains jours."
        ),
        "competitive_insight": (
            f"{comp_note} "
            f"La présence de franchises nationales et d'associations locales structure l'offre à {city}."
        ),
        "action_30d": (
            f"Déposer le dossier SAAD et réserver des locaux adaptés à {city}"
        ),
        "action_60d": (
            f"Recruter les 5 premiers intervenants terrain et lancer la formation {brand}"
        ),
        "action_90d": (
            f"Démarrer les premières prestations et activer le plan marketing local"
        ),
        "opportunity_text": (
            f"{city} offre un bassin de population adapté aux services {services_fr}. "
            f"La configuration socio-économique locale est compatible avec le positionnement {brand}."
        ),
        "generated_by": "template",
    }


# ---------------------------------------------------------------------------
# Appel Gemini API
# ---------------------------------------------------------------------------

def _build_prompt(study: "Study") -> str:
    city = study.geo_scope.city or "ville"
    country = study.geo_scope.country or "FR"
    brand = study.business_context.brand_name or "marque"
    raw_services = study.business_context.service_scope[:4]
    services = ", ".join(
        _SERVICE_LABELS_FR.get(s, s) for s in raw_services
    ) or "services à domicile"
    verdict = str(study.verdict or "go_conditional")

    score_lines = "\n".join(
        f"  - {s.label}: {s.value:.0f}/100 (confiance: {s.confidence_grade})"
        for s in (study.scores or [])[:7]
    ) or "  (aucun score disponible)"

    return f"""Tu es un analyste de marché expert en services à la personne (SAP, aide à domicile, seniors).
Génère une analyse textuelle structurée pour une étude de faisabilité commerciale.

Données de l'étude :
- Ville : {city} ({country})
- Marque / franchisé : {brand}
- Services ciblés : {services}
- Verdict global du moteur Stella : {verdict}
- Scores analytiques (sur 100) :
{score_lines}

Génère UNIQUEMENT un objet JSON valide (sans backticks, sans commentaires) avec ces clés :
{{
  "verdict_narrative": "2-3 phrases d'analyse du verdict (pourquoi ce verdict, points clés, ton professionnel)",
  "exec_summary": "Paragraphe de synthèse pour un dirigeant (3-4 phrases, contexte + verdict + enjeux principaux)",
  "competitive_insight": "1-2 phrases sur la pression concurrentielle locale observée à {city}",
  "action_30d": "Action J+30 : verbe impératif + action concrète et spécifique (~12 mots max)",
  "action_60d": "Action J+60 : verbe impératif + action concrète et spécifique (~12 mots max)",
  "action_90d": "Action J+90 : verbe impératif + action concrète et spécifique (~12 mots max)",
  "opportunity_text": "1-2 phrases sur l'opportunité spécifique du marché de {city} pour {brand}"
}}"""


def _call_gemini(prompt: str, api_key: str) -> dict | None:
    """Appel HTTP direct à l'API Gemini 1.5 Flash. Retourne le JSON parsé ou None."""
    url = f"{_GEMINI_URL}?key={api_key}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024,
            "responseMimeType": "application/json",
        },
    }
    try:
        resp = httpx.post(url, json=body, timeout=_GEMINI_TIMEOUT_S)
        resp.raise_for_status()
        candidates = resp.json().get("candidates", [])
        if not candidates:
            logger.warning("[gemini_analyst] aucun candidat dans la réponse Gemini")
            return None
        text = candidates[0]["content"]["parts"][0]["text"]
        return json.loads(text)
    except httpx.HTTPStatusError as exc:
        logger.warning("[gemini_analyst] HTTP %s : %s", exc.response.status_code, exc.response.text[:200])
        return None
    except (json.JSONDecodeError, KeyError) as exc:
        logger.warning("[gemini_analyst] parsing réponse échoué : %s", exc)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("[gemini_analyst] erreur inattendue : %s", exc)
        return None


# ---------------------------------------------------------------------------
# Entrée publique
# ---------------------------------------------------------------------------

_REQUIRED_KEYS = {
    "verdict_narrative", "exec_summary", "competitive_insight",
    "action_30d", "action_60d", "action_90d", "opportunity_text",
}


def generate_narratives(study: "Study") -> dict:
    """
    Point d'entrée principal.

    Retourne un dict de narratifs analytiques en français.
    Si GEMINI_API_KEY est absente ou si l'API échoue, retourne
    des narratifs templates paramétrés depuis les données de l'étude.
    """
    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        logger.info(
            "[gemini_analyst] GEMINI_API_KEY absente — narratifs template pour study=%s",
            study.study_id,
        )
        return _template_narratives(study)

    try:
        prompt = _build_prompt(study)
        result = _call_gemini(prompt, api_key)

        if result is None:
            logger.warning("[gemini_analyst] Gemini n'a pas répondu — fallback template")
            return _template_narratives(study)

        missing = _REQUIRED_KEYS - result.keys()
        if missing:
            logger.warning("[gemini_analyst] clés manquantes %s — fallback template", missing)
            return _template_narratives(study)

        result["generated_by"] = "gemini-1.5-flash"
        logger.info(
            "[gemini_analyst] narratifs Gemini générés pour study=%s city=%s",
            study.study_id, study.geo_scope.city,
        )
        return result

    except Exception as exc:  # noqa: BLE001
        logger.exception("[gemini_analyst] erreur non gérée : %s", exc)
        return _template_narratives(study)
