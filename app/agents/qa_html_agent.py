"""
QA HTML déterministe — Sprint 9 v3 (renforcé).

Sprint 8 v2 : vérifiait uniquement les nombres dans le texte visible.
Sprint 9 v3 : ferme 3 failles supplémentaires :
  1. Données Chart.js dans les blocs <script> (ex: data: [45321, 12000])
     → un graphique pouvait afficher des valeurs sans traçabilité
  2. Détection heuristique des affirmations qualitatives fausses
     (superlatifs non sourcés : "le plus grand", "leader du marché", etc.)
  3. Cohérence du manifest avec default=str pour les dates Python

HONNÊTETÉ SUR LES LIMITES :
  Ce QA est heuristique — il réduit le risque d'hallucination, il ne l'annule pas.
  La vraie garantie reste : (a) prompt strict avec source_of_truth explicite,
  (b) température basse (0.4), (c) le fallback déterministe PPTX toujours présent.
  Ne pas présenter ce QA comme une preuve absolue dans les handoffs.

API publique :
  validate_html(html: str, manifest: dict) -> tuple[bool, list[str]]
    ok=True si aucun problème détecté
    issues : liste des problèmes avec catégorie préfixée (texte:, chart:, claim:)
"""
from __future__ import annotations

import json
import re


# ─────────────────────────────────────────────────────────────────────────────
# Normalisation des nombres
# ─────────────────────────────────────────────────────────────────────────────

def _numbers(text: str) -> list[str]:
    """
    Extrait les nombres significatifs d'un texte, après avoir retiré
    les valeurs CSS (px, em, %, etc.) qui ne sont pas des données.
    Retourne des chaînes brutes (avec éventuels séparateurs).
    """
    # Retire d'abord les valeurs CSS numériques pour éviter les faux positifs
    text = re.sub(r"\d+(\.\d+)?(px|em|rem|%|vh|vw|pt|s|ms|deg)\b", " ", text)
    return re.findall(r"\d[\d\s.,]*\d|\d+", text)


def _normalize(n: str) -> str:
    """Normalise un nombre : retire séparateurs d'espace/virgule/point pour comparaison."""
    return re.sub(r"[\s,.]", "", n)


def _manifest_index(manifest: dict) -> str:
    """
    Sérialise le manifest en index texte plat pour la recherche de nombres.
    default=str gère les date/datetime Python non sérialisables (Sprint 8 fix).
    On normalise aussi : retire séparateurs pour comparaison uniforme.
    """
    raw = json.dumps(manifest, ensure_ascii=False, default=str)
    return re.sub(r"[\s,]", "", raw).replace(".", "")


# ─────────────────────────────────────────────────────────────────────────────
# Extraction depuis le HTML texte visible (hors <script>/<style>)
# ─────────────────────────────────────────────────────────────────────────────

_STRIP_SCRIPT_STYLE = re.compile(
    r"<(script|style)[^>]*>[\s\S]*?</\1>", re.IGNORECASE
)
_STRIP_COMMENTS = re.compile(r"<!--[\s\S]*?-->")
_STRIP_TAGS = re.compile(r"<[^>]+>")

# Années et numéros de section : toujours whitelistés (pas de données métier)
_YEAR_PATTERN = re.compile(r"^(19|20)\d{2}$")


def _visible_text(html: str) -> str:
    """Extrait le texte visible du HTML (retire scripts, styles, balises)."""
    text = _STRIP_SCRIPT_STYLE.sub(" ", html)
    text = _STRIP_COMMENTS.sub(" ", text)
    text = _STRIP_TAGS.sub(" ", text)
    return text


def _check_visible_numbers(html: str, idx: str) -> list[str]:
    """
    Faille 1 (héritée Sprint 8) : vérifie les nombres dans le texte visible.
    Retourne les nombres suspects (non tracés dans le manifest).
    """
    text = _visible_text(html)
    issues = []
    for raw in _numbers(text):
        clean = _normalize(raw)
        # Ignore les nombres trop courts (chiffres isolés, indices)
        if len(clean) < 3:
            continue
        # Whitelist : années
        if _YEAR_PATTERN.match(clean):
            continue
        if clean not in idx:
            issues.append(f"texte:{raw.strip()}")
    return issues


# ─────────────────────────────────────────────────────────────────────────────
# Extraction depuis les données Chart.js (faille v2 comblée)
# ─────────────────────────────────────────────────────────────────────────────

# Pattern Chart.js : data: [45321, 12000, 890]
_CHARTJS_DATA = re.compile(r"\bdata\s*:\s*\[([\d\s.,]+)\]")


def _check_chartjs_data(html: str, idx: str) -> list[str]:
    """
    Faille v2 : les données Chart.js sont dans des blocs <script> → ignorées par
    le QA v2. Un graphique pouvait afficher des valeurs inventées.

    On extrait tous les tableaux `data: [...]` et on vérifie chaque valeur.
    """
    issues = []
    for arr_match in _CHARTJS_DATA.finditer(html):
        arr_content = arr_match.group(1)
        for n in re.findall(r"\d+(?:\.\d+)?", arr_content):
            clean = _normalize(n)
            if len(clean) < 3:
                continue
            if _YEAR_PATTERN.match(clean):
                continue
            if clean not in idx:
                issues.append(f"chart:{n}")
    return issues


# ─────────────────────────────────────────────────────────────────────────────
# Détection d'affirmations non sourcées (faille v2 — heuristique)
# ─────────────────────────────────────────────────────────────────────────────

# Superlatifs et claims marketing sans source → red flags
_RED_FLAGS = [
    r"\ble plus grand\b",
    r"\ble meilleur\b",
    r"\bla meilleure\b",
    r"\bnuméro\s*un\b",
    r"\bleader du marché\b",
    r"\bleader\s+incontesté\b",
    r"\btoujours\b",
    r"\bgaranti\b",
    r"\bsans\s+équivalent\b",
    r"\binégalé\b",
    r"\bréférence\s+absolue\b",
]


def _check_red_flags(html: str) -> list[str]:
    """
    Faille v2 : le QA ne détectait pas les affirmations qualitatives inventées.
    Heuristique : signale les superlatifs quantitatifs non sourcés par un chiffre.

    Note : best-effort — peut avoir des faux positifs (ex: un nom propre contenant
    "meilleur"). À calibrer selon les retours terrain.
    """
    text = _visible_text(html)
    issues = []
    for pat in _RED_FLAGS:
        if re.search(pat, text, re.IGNORECASE):
            issues.append(f"claim:{pat}")
    return issues


# ─────────────────────────────────────────────────────────────────────────────
# API publique
# ─────────────────────────────────────────────────────────────────────────────

def validate_html(html: str, manifest: dict) -> tuple[bool, list[str]]:
    """
    Valide que le HTML ne contient aucun nombre non tracé ni affirmation suspecte.

    Vérifie :
    1. Nombres dans le texte visible (hors CSS)
    2. Données dans les blocs Chart.js data: [...] (faille v2)
    3. Superlatifs/claims marketing non sourcés (faille v2)

    Returns:
        (ok, issues)
        ok=True si aucun problème
        issues : liste préfixée "texte:", "chart:", "claim:" pour debug
    """
    idx = _manifest_index(manifest)

    issues: list[str] = []
    issues.extend(_check_visible_numbers(html, idx))
    issues.extend(_check_chartjs_data(html, idx))
    issues.extend(_check_red_flags(html))

    return (len(issues) == 0), issues
