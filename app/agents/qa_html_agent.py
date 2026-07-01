"""
QA HTML deterministique — Sprint 9 v3 + Sprint 10 Chantier E.

Sprint 8 v2 : verifiait uniquement les nombres dans le texte visible.
Sprint 9 v3 : ferme 3 failles supplementaires :
  1. Donnees Chart.js dans les blocs <script> (ex: data: [45321, 12000])
  2. Detection heuristique des affirmations qualitatives non sourcees
  3. Coherence du manifest avec default=str pour les dates Python

Sprint 10 Chantier E :
  4. Detection de HTML tronque (balises div/table non equilibrees)
     Un HTML tronque (maxOutputTokens atteint) serait serve tel quel dans l'iframe.
     Check en premier pour rejeter rapidement avant les autres verifications.

HONNETETE SUR LES LIMITES :
  Ce QA est heuristique — il reduit le risque d'hallucination, il ne l'annule pas.
  La vraie garantie reste : (a) prompt strict avec source_of_truth explicite,
  (b) temperature basse (0.4), (c) le fallback deterministique PPTX toujours present.

API publique :
  validate_html(html: str, manifest: dict) -> tuple[bool, list[str]]
    ok=True si aucun probleme detecte
    issues : liste des problemes avec categorie prefixee
             (texte:, chart:, claim:, html_tronque:)
"""
from __future__ import annotations

import json
import re


# -----------------------------------------------------------------------------
# Normalisation des nombres
# -----------------------------------------------------------------------------

# Fix Sprint 13b — l'ancienne regex \d[\d\s.,]*\d collait deux nombres adjacents
# a travers les sauts de ligne ("48238 \n 28.0" devenait le token "48238...28.0"
# → normalise "48238280" introuvable → FAUX POSITIF sur des valeurs 100 % tracees).
# Nouvelle regex : nombre a groupes de milliers francais (espace/insecable/fine)
# OU nombre simple avec decimale — jamais de \n ni de doubles espaces.
_NUM_RE = re.compile(
    r"\d{1,3}(?:[   ]\d{3})+(?:[.,]\d+)?"   # 2 251 / 267 991 / 1 447,54
    r"|\d+(?:[.,]\d+)?"                                # 48238 / 28.0 / 4,6
)


def _numbers(text: str) -> list[str]:
    """
    Extrait les nombres significatifs d'un texte, apres avoir retire
    les valeurs CSS (px, em, %, etc.) qui ne sont pas des donnees.
    Retourne des chaines brutes (avec eventuels separateurs).
    """
    text = re.sub(r"\d+(\.\d+)?(px|em|rem|%|vh|vw|pt|s|ms|deg)\b", " ", text)
    # "/100" (denominateur d'echelle des scores, ex "43.1/100") n'est pas une donnee
    text = re.sub(r"/\s*100\b", " ", text)
    return _NUM_RE.findall(text)


def _normalize(n: str) -> str:
    """Normalise un nombre : retire separateurs d'espace/virgule/point pour comparaison."""
    return re.sub(r"[\s  ,.]", "", n)


def _candidates(raw: str) -> set[str]:
    """
    Formes equivalentes d'un nombre pour la recherche dans l'index manifest.

    Fix Sprint 13b : "28.0" affiche pour la valeur manifest 28 est la MEME donnee,
    pas une invention. On genere donc aussi la forme entiere ("28.0" → "28")
    et la forme sans zero final ("4.60" → "4.6").
    """
    cands = {_normalize(raw)}
    numeric = raw.replace(" ", "").replace(" ", "").replace(" ", "").replace(",", ".")
    try:
        x = float(numeric)
        if x == int(x):
            cands.add(str(int(x)))
        # forme decimale canonique sans zeros de queue ("4.60" → "46" deja couvert,
        # "28.0" → "28")
        cands.add(re.sub(r"[\s,.]", "", repr(x).rstrip("0").rstrip(".")))
    except ValueError:
        pass
    return cands


def _manifest_index(manifest: dict) -> str:
    """
    Serialise le manifest en index texte plat pour la recherche de nombres.
    default=str gere les date/datetime Python non serialisables (Sprint 8 fix).
    On normalise aussi : retire separateurs pour comparaison uniforme.
    """
    raw = json.dumps(manifest, ensure_ascii=False, default=str)
    return re.sub(r"[\s,]", "", raw).replace(".", "")


# -----------------------------------------------------------------------------
# Extraction depuis le HTML texte visible (hors <script>/<style>)
# -----------------------------------------------------------------------------

_STRIP_SCRIPT_STYLE = re.compile(
    r"<(script|style)[^>]*>[\s\S]*?</\1>", re.IGNORECASE
)
_STRIP_COMMENTS = re.compile(r"<!--[\s\S]*?-->")
_STRIP_TAGS = re.compile(r"<[^>]+>")

# Annees et numeros de section : toujours whitelistes (pas de donnees metier)
_YEAR_PATTERN = re.compile(r"^(19|20)\d{2}$")


def _visible_text(html: str) -> str:
    """Extrait le texte visible du HTML (retire scripts, styles, balises)."""
    text = _STRIP_SCRIPT_STYLE.sub(" ", html)
    text = _STRIP_COMMENTS.sub(" ", text)
    text = _STRIP_TAGS.sub(" ", text)
    # Fix Sprint 13b : decoder les separateurs de milliers en entites HTML
    # ("2&nbsp;251") sinon l'extracteur voit "2" et "251" separement.
    text = re.sub(r"&(nbsp|#160|#8239|thinsp);", " ", text)
    return text


def _check_visible_numbers(html: str, idx: str) -> list[str]:
    """
    Faille 1 (heritee Sprint 8) : verifie les nombres dans le texte visible.
    Retourne les nombres suspects (non traces dans le manifest).
    """
    text = _visible_text(html)
    issues = []
    for raw in _numbers(text):
        clean = _normalize(raw)
        if len(clean) < 3:
            continue
        if _YEAR_PATTERN.match(clean):
            continue
        # Fix Sprint 13b : accepter les formes equivalentes ("28.0" == 28)
        if not any(c in idx for c in _candidates(raw)):
            issues.append(f"texte:{raw.strip()}")
    return issues


# -----------------------------------------------------------------------------
# Extraction depuis les donnees Chart.js (faille v2 comblee)
# -----------------------------------------------------------------------------

_CHARTJS_DATA = re.compile(r"\bdata\s*:\s*\[([\d\s.,]+)\]")


def _check_chartjs_data(html: str, idx: str) -> list[str]:
    """
    Faille v2 : les donnees Chart.js sont dans des blocs <script>.
    On extrait tous les tableaux data: [...] et on verifie chaque valeur.
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
            # Fix Sprint 13b : formes equivalentes ("28.0" == 28)
            if not any(c in idx for c in _candidates(n)):
                issues.append(f"chart:{n}")
    return issues


# -----------------------------------------------------------------------------
# Detection d'affirmations non sourcees (faille v2 — heuristique)
# -----------------------------------------------------------------------------

_RED_FLAGS = [
    r"\ble plus grand\b",
    r"\ble meilleur\b",
    r"\bla meilleure\b",
    r"\bnumero\s*un\b",
    r"\bleader du marche\b",
    r"\bleader\s+inconteste\b",
    r"\btoujours\b",
    r"\bgaranti\b",
    r"\bsans\s+equivalent\b",
    r"\binegale\b",
    r"\breference\s+absolue\b",
]


def _check_red_flags(html: str) -> list[str]:
    """
    Faille v2 : le QA ne detectait pas les affirmations qualitatives inventees.
    Heuristique : signale les superlatifs non sources par un chiffre.
    """
    text = _visible_text(html)
    issues = []
    for pat in _RED_FLAGS:
        if re.search(pat, text, re.IGNORECASE):
            issues.append(f"claim:{pat}")
    return issues


# -----------------------------------------------------------------------------
# Detection de HTML tronque (Sprint 10 Chantier E)
# -----------------------------------------------------------------------------

def _check_html_structure(html: str) -> list[str]:
    """
    Sprint 10 Chantier E — Detection de HTML tronque.

    Un HTML tronque (maxOutputTokens atteint en milieu de balise) a plus de <div>
    ouverts que fermes. Ce check evite de servir un HTML mal forme a l'iframe.

    Limite : ne detecte que les tronques nets. Un tronque entre deux <div> valides
    passerait. Suffisant pour le cas le plus frequent (arret en milieu de tableau).
    """
    issues = []
    open_divs = html.count("<div")
    close_divs = html.count("</div>")
    if open_divs != close_divs:
        issues.append(f"html_tronque:div open={open_divs} close={close_divs}")
    if html.count("<table") != html.count("</table>"):
        issues.append("html_tronque:table non fermee")
    return issues


# -----------------------------------------------------------------------------
# API publique
# -----------------------------------------------------------------------------

def validate_html(html: str, manifest: dict) -> tuple[bool, list[str]]:
    """
    Valide que le HTML ne contient aucun nombre non trace ni affirmation suspecte.

    Verifie (v3 Sprint 9 + Sprint 10 Chantier E) :
    0. HTML tronque — balises div/table non equilibrees (Chantier E Sprint 10)
    1. Nombres dans le texte visible (hors CSS)
    2. Donnees dans les blocs Chart.js data: [...] (faille v2)
    3. Superlatifs/claims marketing non sources (faille v2)

    Returns:
        (ok, issues)
        ok=True si aucun probleme
        issues : liste prefixee "html_tronque:", "texte:", "chart:", "claim:"
    """
    idx = _manifest_index(manifest)

    issues: list[str] = []
    issues.extend(_check_html_structure(html))          # Sprint 10 : check tronque en premier
    issues.extend(_check_template_leakage(html))        # Sprint 13 : Jinja/placeholder brut
    issues.extend(_check_empty_main(html))              # Sprint 13 : slide quasi vide
    issues.extend(_check_visible_numbers(html, idx))
    issues.extend(_check_chartjs_data(html, idx))
    issues.extend(_check_red_flags(html))

    return (len(issues) == 0), issues


# -----------------------------------------------------------------------------
# Sprint 13 — checks de FORME (observés en prod le 01/07/2026)
# -----------------------------------------------------------------------------

_TEMPLATE_PATTERNS = re.compile(r"\{\{|\}\}|\{%|%\}")


def _check_template_leakage(html: str) -> list[str]:
    """
    Detecte la syntaxe de template ({{ var }}, {% for %}) dans le HTML.

    Cas reel observe (gallery Bordeaux 01/07) : Gemini a produit un template
    Jinja complet ('{{ competition_table.count_total }}', '{% for comp in ... %}')
    au lieu de recopier les valeurs. Le QA chiffres ne voyait rien (peu de
    digits) → la slide etait servie avec du code brut visible.
    """
    # IMPORTANT : sur le texte VISIBLE uniquement — les configs Chart.js
    # legitimes contiennent des '}}' (fermetures d'objets JS imbriques).
    matches = _TEMPLATE_PATTERNS.findall(_visible_text(html))
    if matches:
        return [f"template:syntaxe {{{{...}}}} ou {{%...%}} detectee ({len(matches)} occurrences) — l'agent a genere un template au lieu de recopier les valeurs"]
    return []


def _check_empty_main(html: str, min_chars: int = 120) -> list[str]:
    """
    Detecte une slide quasi vide : moins de min_chars caracteres de texte
    visible. 'QA PASS' sur une slide vide etait le piege n°3 du guide —
    ce check le ferme partiellement.
    """
    text = _visible_text(html)
    compact = re.sub(r"\s+", " ", text).strip()
    if len(compact) < min_chars:
        return [f"vide:texte visible {len(compact)} car. (< {min_chars}) — slide probablement vide"]
    return []
