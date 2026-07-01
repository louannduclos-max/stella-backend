"""
Cache HTML des slides — Sprint 9 (E) + Sprint 10 (Chantier C).

POURQUOI :
  Gemini coute ~$0.001-0.005 par appel. 15 slides x N etudes = cout cumulatif.
  Regenerer une etude identique (meme section_data) doit couter 0 appel Gemini.

CLE DE CACHE STABLE (faille v2 corrigee) :
  v2 utilisait json.dumps(section_data) sans precautions -> instable si :
  - section_data contient des objets Pydantic ou des dates Python
  - L'ordre des cles varie selon Python version
  Solution : serialisation canonique (sort_keys=True, default=str)
  + SKILL_VERSION pour invalider le cache lors de changements de skill.

SKILL_VERSION AUTOMATIQUE (Sprint 10 Chantier C) :
  Plus de bump manuel : la version est le hash du contenu des fichiers skill.
  Modifier un .md, .html, .json, .css -> hash change -> cache invalide auto.
  Calcule au demarrage du process, pas a chaque appel.

STOCKAGE :
  Table Supabase : slide_html_cache (key TEXT PK, html TEXT, created_at TIMESTAMPTZ)

UTILISATION :
  key = slide_cache_key(section_id, section_data)
  cached = cache_get(key)
  if cached:
      return cached
  html = call_gemini(...)
  cache_set(key, html)
  return html
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Sprint 10 (Chantier C) : SKILL_VERSION = hash automatique des fichiers skill.
# Plus de bump manuel. Modifier un .md ou .html -> hash change -> cache invalide.
_SKILL_DIR = Path(__file__).parent.parent / "skills" / "interdomicilio"


def _compute_skill_version() -> str:
    """Hash SHA256 de tous les fichiers du skill (html, md, json, css).
    Calcule au demarrage du process. Change automatiquement a chaque modif."""
    h = hashlib.sha256()
    try:
        for f in sorted(_SKILL_DIR.rglob("*")):
            if f.is_file() and f.suffix in {".html", ".md", ".json", ".css"}:
                h.update(f.read_bytes())
        version = h.hexdigest()[:12]
        logger.info("[slide_cache] SKILL_VERSION auto = %s", version)
        return version
    except Exception as exc:
        logger.warning("[slide_cache] SKILL_VERSION fallback '0.0.0': %s", exc)
        return "0.0.0"


SKILL_VERSION = _compute_skill_version()  # calcule au demarrage, jamais a la main


# -----------------------------------------------------------------------------
# Cle de cache
# -----------------------------------------------------------------------------

def slide_cache_key(section_id: str, section_data: dict) -> str:
    """
    Genere une cle de cache stable et deterministe pour une slide HTML.

    Stabilite garantie par :
    - sort_keys=True : ordre des cles canonique
    - default=str : gere les dates Python (sinon crash)
    - ensure_ascii=True : evite les variations d'encodage
    - Prefixe SKILL_VERSION : invalide le cache si le skill change

    Returns:
        Cle courte et lisible (prefixe "slide_html:" + 20 chars hex)
    """
    canonical = json.dumps(
        section_data,
        sort_keys=True,
        ensure_ascii=True,
        default=str,
    )
    content = f"{SKILL_VERSION}|{section_id}|{canonical}"
    h = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return f"slide_html:{h[:20]}"


# -----------------------------------------------------------------------------
# Operations Supabase
# -----------------------------------------------------------------------------

def cache_get(key: str) -> str | None:
    """
    Recupere le HTML en cache pour une cle donnee.
    Retourne None si absent ou si Supabase est indisponible.
    """
    try:
        from app.core.supabase_client import get_supabase_client
        sb = get_supabase_client()
        resp = sb.table("slide_html_cache").select("html").eq("key", key).execute()
        rows = resp.data or []
        if rows:
            logger.info("[slide_cache] HIT %s", key)
            return rows[0]["html"]
        logger.debug("[slide_cache] MISS %s", key)
        return None
    except Exception as exc:
        # Le cache est best-effort : une erreur Supabase ne bloque pas la generation
        logger.warning("[slide_cache] get failed (%s): %s", key, exc)
        return None


def cache_set(key: str, html: str) -> None:
    """
    Stocke un HTML en cache.
    Silencieux en cas d'erreur (best-effort).
    """
    try:
        from app.core.supabase_client import get_supabase_client
        sb = get_supabase_client()
        sb.table("slide_html_cache").upsert(
            {"key": key, "html": html},
            on_conflict="key",
        ).execute()
        logger.info("[slide_cache] SET %s (%d chars)", key, len(html))
    except Exception as exc:
        logger.warning("[slide_cache] set failed (%s): %s", key, exc)
