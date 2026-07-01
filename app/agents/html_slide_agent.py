"""
HTMLSlideAgent — génère le contenu HTML d'UNE slide à partir du manifest.

Sprint 8 — Chemin B (Bascule HTML génératif).
Ce sprint teste UNE slide (concurrence) avant de généraliser.

Principe :
  - L'agent reçoit les données brutes de la section (sous-ensemble du manifest)
  - Il lit les instructions de layout depuis app/skills/{brand}/sections/{section}.md
  - Il génère UNIQUEMENT le bloc <main> ({MAIN_CONTENT}) en HTML
  - Le squelette header/footer/CSS vient de app/skills/{brand}/base_slide.html
  - La QA déterministe (qa_html_agent.py) vérifie ensuite que chaque chiffre est tracé

Modèle : configurable via GEMINI_MODEL (défaut gemini-2.5-flash)
Temperature : 0.4 (assez bas pour la fiabilité structurelle)
maxOutputTokens : 4096 (une slide HTML fait ~2000-3000 tokens)

Sécurités :
  - Seules les données passées en section_data sont envoyées au LLM
    (pas tout le manifest, pour limiter le risque d'invention)
  - Si l'API échoue : retourne None (pas de HTML inventé, pas de crash)
  - Le fallback dans run_study.py reste le layout_engine PPTX
"""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
_GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)
_GEMINI_TIMEOUT_S = 45

SKILLS_DIR = Path(__file__).parent.parent / "skills"

# ─────────────────────────────────────────────────────────────────────────────
# Chantier E — Données bornées par section + budget tokens
# ─────────────────────────────────────────────────────────────────────────────
# Chaque section ne recoit que les cles manifest dont elle a besoin.
# Avantages : cout reduit, cloisonnement, pas d'invention par association.
# L'agent ne "voit" pas les donnees des autres sections.
#
# INVARIANT : toutes les valeurs numeriques affichees sont dans SECTION_DATA_KEYS
# -> le QA peut les verifier (elles sont dans le sous-manifest envoye).

SECTION_DATA_KEYS: dict[str, list[str]] = {
    "executive_summary":    ["metrics", "verdict", "score_composite",
                             "market_sizing", "funding_scale", "narratives"],
    "benchmark_comparison": ["benchmark_rows"],
    "funding_feasibility":  ["funding_scale", "market_sizing"],
    "demographics":         ["demographics_pie", "metrics"],
    # Sprint 12 : competition_table (directs/indirects + domain + stars pré-calculés)
    # competition_table est pré-calculé dans slide_precompute._compute_competition_table
    # competitors_top gardé en fallback si competition_table absent (vieilles études)
    "competition":          ["competition_table", "competitors_top",
                             "competitors_total_count", "competition_avg_rating",
                             "narratives"],
    "competition_mapping":  ["competition_table", "competitors_top",
                             "competitors_total_count", "competition_avg_rating",
                             "narratives"],
    "verdict":              ["verdict", "scores_radar", "score_composite", "narratives"],
    "swot":                 ["scores"],
    # Fix Sprint 13 : manifest n'a AUCUNE clé "action_plan" — la slide recevait
    # {action_plan: null}. Les actions réelles sont dans narratives (action_30d/60d/90d).
    "action_plan":          ["narratives", "verdict"],
    # Sprint 13b — nouvelles slides (données 100 % présentes dans le manifest)
    "cover":                ["verdict", "score_composite", "competitors_total_count",
                             "metrics"],
    "employment_talent":    ["metrics"],
    "income_housing":       ["metrics"],
    "methodology_sources":  ["sources"],
    # Sprint 13d — deck complet 15/15 (dernières sections registry)
    "market_scorecard":     ["scores", "score_composite", "verdict", "narratives"],
    "target_segments":      ["metrics", "market_sizing"],
    "real_estate":          ["metrics"],
    "microzones":           ["microzones", "metrics"],
    "regulation_feasibility": ["metrics", "funding_scale"],
    # Sprint 11 — sections manquantes (TypeError sur fallback dict[:8])
    # "study" EXCLU de geo_analysis : contient created_at/updated_at (datetime) non-sérialisables
    # par json.dumps dans _build_prompt → TypeError → crash worker → "Failed to fetch"
    "geo_analysis":         ["metrics", "microzones"],
    "market_overview":      ["metrics", "market_sizing", "competitors_total_count",
                             "narratives"],
}

# maxOutputTokens calibre par section — evite la troncature HTML
# Les sections avec tableaux/graphiques ont besoin de plus de tokens
# Sprint 13d — budgets relevés PARTOUT. Constat récurrent (13a/13b/13c) :
# la seule cause de QA FAIL restante était html_tronque, sur des sections à
# 3000-4096 tokens (Gemini 2.5-flash écrit des styles inline verbeux).
# Le coût marginal de tokens de sortie est négligeable versus une slide cassée,
# et le cache fige désormais la première génération réussie.
SECTION_MAX_TOKENS: dict[str, int] = {
    "benchmark_comparison": 8192,
    "competition_mapping":  8192,
    "competition":          8192,
    "methodology_sources":  8192,   # tableaux longs
    "microzones":           8192,
}
_DEFAULT_MAX_TOKENS = 6144


# Clés de contexte injectées par _prepare_section_data (pipeline) — internes et sûres.
# Fix Sprint 13 : le double filtrage (_prepare_section_data puis _filter_section_data)
# les jetait, l'agent perdait zone/brand_name référencés par les .md des sections.
_BASE_CONTEXT_KEYS = ("zone", "brand_name", "year", "language")


def _filter_section_data(section_id: str, manifest: dict) -> dict:
    """
    Retourne uniquement les cles manifest pertinentes pour la section.
    Si la section n'a pas de mapping -> retourne les 8 premieres metriques (defaut safe).
    """
    keys = SECTION_DATA_KEYS.get(section_id)
    if keys:
        out = {k: manifest.get(k) for k in keys}
        for bk in _BASE_CONTEXT_KEYS:
            if bk in manifest and bk not in out:
                out[bk] = manifest[bk]
        return out
    # Defaut : les 8 premieres metriques (sections sans mapping explicite)
    # ATTENTION : manifest["metrics"] est un dict {count, items, by_id} — pas une list
    metrics_obj = manifest.get("metrics") or {}
    items = metrics_obj.get("items", []) if isinstance(metrics_obj, dict) else []
    return {"metrics": items[:8]}


# ─────────────────────────────────────────────────────────────────────────────
# Chargement du skill
# ─────────────────────────────────────────────────────────────────────────────

def _load_skill(brand: str) -> dict | None:
    path = SKILLS_DIR / brand / "skill.json"
    if not path.exists():
        logger.warning("[HTMLSlideAgent] skill.json introuvable : %s", path)
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("[HTMLSlideAgent] lecture skill.json échouée : %s", exc)
        return None


def _load_section_instructions(brand: str, section_id: str) -> str | None:
    path = SKILLS_DIR / brand / "sections" / f"{section_id}.md"
    if not path.exists():
        logger.warning("[HTMLSlideAgent] instructions section introuvables : %s", path)
        return None
    return path.read_text(encoding="utf-8")


def _load_base_template(brand: str) -> str | None:
    path = SKILLS_DIR / brand / "base_slide.html"
    if not path.exists():
        logger.warning("[HTMLSlideAgent] base_slide.html introuvable : %s", path)
        return None
    return path.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────────────
# Prompt
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """
Tu es un expert en design de slides d'études de faisabilité commerciale.
Tu génères du HTML propre et professionnel pour des présentations d'analyse de marché.

Règles ABSOLUES :
1. Tu génères UNIQUEMENT le bloc <main> intérieur — jamais de <html>, <head>, <body>, <style> globaux.
2. Tu utilises EXCLUSIVEMENT les classes CSS définies dans base_slide.html (kpi-row, kpi-card, comp-table, etc.).
3. Tu n'inventes AUCUNE valeur absente des données fournies. Si une donnée manque : "n.d."
4. Tu ne génères PAS de <script> sauf si les instructions de section l'autorisent explicitement pour un graphique Chart.js.
5. Le HTML doit être directement insérable dans {MAIN_CONTENT} du template.
6. Langue : {LANGUAGE}.
7. Tu écris les VALEURS LITTÉRALES dans le HTML — JAMAIS de syntaxe de template
   ou de placeholder. INTERDIT : "{{valeur}}", "{% for %}", "${valeur}", "[VALEUR]".
   Quand les instructions disent "recopier competition_table.count_total",
   tu écris le nombre lui-même (ex: 32), pas le nom de la variable.
8. HTML CONCIS : privilégie les classes CSS existantes aux longs styles inline.
   Ne répète pas un même bloc de styles — factorise via les classes. Le HTML
   complet doit tenir dans le budget sans être coupé.
9. NARRATION : chaque strategic-box contient 3 à 4 phrases d'analyse de niveau
   consultant, structurées ainsi : constat chiffré (valeurs affichées sur la
   slide) → implication métier concrète → recommandation actionnable. Jamais
   une phrase générique unique. Si le JSON fournit un texte `narratives.*`
   pertinent, l'utiliser comme base et le compléter — sans introduire de
   nouveau chiffre.
"""

def _build_prompt(
    section_instructions: str,
    section_data: dict,
    skill: dict,
    language: str,
) -> str:
    brand_name = skill.get("brand_name", "")
    colors_summary = json.dumps(skill.get("colors", {}), ensure_ascii=False)

    return f"""Tu génères le contenu HTML de la section suivante pour une étude de faisabilité {brand_name}.

## Instructions de layout

{section_instructions}

## Données réelles (source de vérité — ne pas inventer)

```json
{json.dumps(section_data, ensure_ascii=False, indent=2)}
```

## Classes CSS disponibles (depuis base_slide.html)

Couleurs : {colors_summary}
Classes : kpi-row, kpi-card, kpi-icon, kpi-value, kpi-label,
          comp-table, is-direct, badge-direct, badge-indirect, rating-stars,
          strategic-box, strat-icon, section-accent-bar

## Consigne

Génère UNIQUEMENT le HTML intérieur du bloc <main class="slide-body">.
Pas de doctype, pas de <html>, pas de <head>, pas de <style> globaux.
Si les instructions de section autorisent un graphique Chart.js, tu peux inclure un bloc <script> apres le contenu principal.
Commence directement par les éléments de contenu (div, table, etc.).
"""


# ─────────────────────────────────────────────────────────────────────────────
# Appel Gemini
# ─────────────────────────────────────────────────────────────────────────────

def _call_gemini_html(prompt: str, api_key: str, max_tokens: int = _DEFAULT_MAX_TOKENS) -> str | None:
    """Appelle Gemini et retourne le HTML brut (string) ou None."""
    url = f"{_GEMINI_URL}?key={api_key}"
    body = {
        "system_instruction": {
            "parts": [{"text": _SYSTEM_PROMPT.replace("{LANGUAGE}", "francais")}]
        },
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            # Sprint 13 : 0.4 → 0.2. Travail de recopie/mise en forme, pas de
            # créativité. Observé en prod à 0.4 : une génération sur N sort un
            # template Jinja au lieu des valeurs (gallery Bordeaux 01/07).
            "temperature": 0.2,
            "maxOutputTokens": max_tokens,
        },
    }
    # Sprint 13d — CAUSE RACINE des troncatures aléatoires : les modèles 2.5
    # "réfléchissent" par défaut et les tokens de thinking se décomptent de
    # maxOutputTokens. Une consigne complexe → gros thinking → HTML coupé net
    # (observé : market_scorecard, 59 caractères sur 6144 tokens de budget).
    # La recopie de valeurs n'a pas besoin de thinking → budget 0.
    if "2.5" in (GEMINI_MODEL or ""):
        body["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}
    try:
        resp = httpx.post(url, json=body, timeout=_GEMINI_TIMEOUT_S)
        logger.warning("[HTMLSlideAgent] HTTP %s model=%s", resp.status_code, GEMINI_MODEL)
        resp.raise_for_status()
        candidates = resp.json().get("candidates", [])
        if not candidates:
            logger.warning("[HTMLSlideAgent] aucun candidat Gemini")
            return None
        raw = candidates[0]["content"]["parts"][0]["text"]
        logger.warning("[HTMLSlideAgent] HTML brut (300 car.) : %s", raw[:300])
        # Retirer éventuelles fences markdown ```html ... ```
        raw = re.sub(r"^```html?\s*", "", raw.strip())
        raw = re.sub(r"\s*```$", "", raw)
        return raw.strip()
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "[HTMLSlideAgent] HTTP %s : %s",
            exc.response.status_code,
            exc.response.text[:300],
        )
        return None
    except Exception as exc:
        logger.warning("[HTMLSlideAgent] erreur : %s", exc)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# API publique
# ─────────────────────────────────────────────────────────────────────────────

class HTMLSlideAgent:

    def generate_main_content(
        self,
        section_id: str,
        section_number: int,
        section_data: dict,
        brand: str = "interdomicilio",
        language: str = "fr",
    ) -> str | None:
        """
        Génère le bloc HTML <main> pour une section.
        Retourne None si l'API échoue ou si le skill est manquant.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.warning("[HTMLSlideAgent] GEMINI_API_KEY absente")
            return None

        skill = _load_skill(brand)
        if not skill:
            return None

        instructions = _load_section_instructions(brand, section_id)
        if not instructions:
            return None

        # Chantier E : donnees bornees par section + budget tokens calibre
        # section_data peut etre pre-filtre par _prepare_section_data() (pipeline).
        # _filter_section_data assure la coherence si appel direct (endpoint debug).
        max_tokens = SECTION_MAX_TOKENS.get(section_id, _DEFAULT_MAX_TOKENS)
        filtered_data = _filter_section_data(section_id, section_data)

        prompt = _build_prompt(
            section_instructions=instructions,
            section_data=filtered_data,
            skill=skill,
            language=language,
        )
        return _call_gemini_html(prompt, api_key, max_tokens=max_tokens)

    def assemble_slide(
        self,
        section_id: str,
        section_number: int,
        section_title: str,
        section_subtitle: str,
        main_content: str,
        brand: str = "interdomicilio",
        language: str = "fr",
        study_type: str = "Étude de faisabilité",
        zone: str = "",
        year: str = "2026",
        total_sections: int = 15,
    ) -> str:
        """
        Assemble le HTML complet de la slide en injectant main_content
        dans le template base_slide.html.
        """
        template = _load_base_template(brand)
        if not template:
            # Fallback minimal si le template est manquant
            return f"<html><body>{main_content}</body></html>"

        skill = _load_skill(brand) or {}
        brand_name = skill.get("brand_name", brand.title())

        replacements: dict[str, Any] = {
            "{LANGUAGE}":        language,
            "{BRAND_NAME}":      brand_name,
            "{SECTION_NUMBER}":  str(section_number),
            "{TOTAL_SECTIONS}":  str(total_sections),
            "{SECTION_TITLE}":   section_title,
            "{SECTION_SUBTITLE}": section_subtitle,
            "{STUDY_TYPE}":      study_type,
            "{ZONE}":            zone,
            "{YEAR}":            year,
            "{MAIN_CONTENT}":    main_content,
        }
        html = template
        for placeholder, value in replacements.items():
            html = html.replace(placeholder, str(value))
        return html


html_slide_agent = HTMLSlideAgent()
