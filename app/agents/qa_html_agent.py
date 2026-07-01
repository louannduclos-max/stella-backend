"""
QA HTML déterministe — vérifie que chaque nombre visible dans le HTML
est traçable dans le manifest.

Sprint 8 — Chemin B.

Principe :
  - Extraire tous les nombres "significatifs" du HTML (≥ 2 chiffres, pas CSS px/%)
  - Sérialiser le manifest en texte plat
  - Vérifier que chaque nombre trouvé dans le HTML existe dans le manifest
  - Les nombres purement CSS (100px, 80%, 1px, etc.) sont ignorés
  - Les constantes de mise en page (années ≥ 2020 à confirmer, numéros de page, etc.)
    sont acceptées sans traçabilité stricte

Retourne (ok: bool, untraceable: list[str])
  - ok=True si tous les nombres sont tracés
  - untraceable : liste des nombres suspects avec contexte

IMPORTANT : Ce QA est conservateur — il doit avoir peu de faux positifs.
Un nombre "non tracé" bloque l'affichage. Les constantes connues (années,
numéros de section) sont whitelistées.
"""
from __future__ import annotations

import json
import re


# ─────────────────────────────────────────────────────────────────────────────
# Extraction des nombres depuis le HTML
# ─────────────────────────────────────────────────────────────────────────────

# Pattern : chiffres (avec séparateurs espace/apostrophe/virgule) ≥ 2 chiffres consécutifs
_NUMBER_PATTERN = re.compile(r"\b(\d[\d\s ',\.]*\d)\b")

# Valeurs CSS à ignorer : suivi de px, %, em, rem, vh, vw, pt, s, ms
_CSS_UNIT_SUFFIX = re.compile(r"\d+(?:\.\d+)?\s*(?:px|%|em|rem|vh|vw|pt|ms|s)\b", re.IGNORECASE)

# Whitelist : numéros de section (1-20), années (2020-2030)
_WHITELISTED = set(str(n) for n in range(1, 21)) | set(str(y) for y in range(2020, 2031))

# Tags HTML à ignorer pour l'extraction (style, script, commentaires)
_STRIP_TAGS = re.compile(r"<style[^>]*>.*?</style>|<script[^>]*>.*?</script>|<!--.*?-->", re.DOTALL)
_STRIP_HTML_TAGS = re.compile(r"<[^>]+>")


def _extract_visible_numbers(html: str) -> list[tuple[str, str]]:
    """
    Retourne une liste de (nombre_normalisé, contexte) pour chaque nombre
    significatif trouvé dans le texte visible du HTML.
    """
    # Supprimer style, script, commentaires
    text = _STRIP_TAGS.sub(" ", html)
    # Supprimer les balises HTML restantes
    text = _STRIP_HTML_TAGS.sub(" ", text)
    # Supprimer les valeurs CSS dans les attributs style inline
    text = _CSS_UNIT_SUFFIX.sub(" ", text)

    results = []
    for m in _NUMBER_PATTERN.finditer(text):
        raw = m.group(1)
        # Normaliser : supprimer séparateurs d'espacement
        normalized = re.sub(r"[\s ',]", "", raw)
        if len(normalized) < 2:
            continue
        if normalized in _WHITELISTED:
            continue
        # Contexte : 40 caractères autour du match
        start = max(0, m.start() - 40)
        end = min(len(text), m.end() + 40)
        context = text[start:end].strip().replace("\n", " ")
        results.append((normalized, context))
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Traçabilité dans le manifest
# ─────────────────────────────────────────────────────────────────────────────

def _manifest_flat_text(manifest: dict) -> str:
    """Sérialise le manifest en texte plat pour la recherche de nombres."""
    return json.dumps(manifest, ensure_ascii=False)


def _is_traceable(number: str, manifest_text: str) -> bool:
    """
    Retourne True si le nombre (sans séparateurs) apparaît dans le manifest.
    On vérifie aussi la version avec séparateur d'espace (ex: "45 321" → "45321").
    """
    if number in manifest_text:
        return True
    # Certains nombres peuvent être stockés avec virgule décimale en JSON (float)
    # ex: "45321" vs "45321.0" → accepter si le début correspond
    if f'"{number}"' in manifest_text or f": {number}" in manifest_text:
        return True
    return False


# ─────────────────────────────────────────────────────────────────────────────
# API publique
# ─────────────────────────────────────────────────────────────────────────────

def validate_html(html: str, manifest: dict) -> tuple[bool, list[str]]:
    """
    Valide que chaque nombre significatif dans le HTML est traçable dans le manifest.

    Returns:
        (ok, untraceable_list)
        ok=True si aucun nombre suspect
        untraceable_list : liste "nombre → contexte" pour debug
    """
    manifest_text = _manifest_flat_text(manifest)
    numbers = _extract_visible_numbers(html)

    untraceable: list[str] = []
    for number, context in numbers:
        if not _is_traceable(number, manifest_text):
            untraceable.append(f"{number!r} → «{context}»")

    return len(untraceable) == 0, untraceable
