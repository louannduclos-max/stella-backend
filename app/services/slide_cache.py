"""
Cache HTML des slides — Sprint 9 (E).

POURQUOI :
  Gemini coûte ~$0.001–0.005 par appel. 15 slides × N études = coût cumulatif.
  Régénérer une étude identique (même section_data) doit coûter 0 appel Gemini.

CLÉ DE CACHE STABLE (faille v2 corrigée) :
  v2 utilisait json.dumps(section_data) sans précautions → instable si :
  - section_data contient des objets Pydantic ou des dates Python
  - L'ordre des clés varie selon Python version
  Solution : sérialisation canonique (sort_keys=True, default=str)
  + SKILL_VERSION pour invalider le cache lors de changements de skill.

STOCKAGE :
  Table Supabase : slide_html_cache (key TEXT PK, html TEXT, created_at TIMESTAMPTZ)
  Créer avec :
    CREATE TABLE IF NOT EXISTS slide_html_cache (
      key TEXT PRIMARY KEY,
      html TEXT NOT NULL,
      created_at TIMESTAMPTZ DEFAULT now()
    );

BUMP SKILL_VERSION quand le skill change :
  - Modification de base_slide.html
  - Modification d'un fichier sections/*.md
  → Sinon on servirait du vieux HTML avec le nouveau skill

UTILISATION :
  # Avant Gemini
  key = slide_cache_key(section_id, section_data)
  cached = cache_get(key)
  if cached:
      return cached

  # Après Gemini
  html = call_gemini(...)
  cache_set(key, html)
  return html
"""
from __future__ import annotations

import hashlib
import json
import logging

logger = logging.getLogger(__name__)

# Bumper à chaque changement de skill (base_slide.html ou sections/*.md)
# Format : "MAJOR.MINOR.PATCH"
SKILL_VERSION = "1.0.0"


# ─────────────────────────────────────────────────────────────────────────────
# Clé de cache
# ─────────────────────────────────────────────────────────────────────────────

def slide_cache_key(section_id: str, section_data: dict) -> str:
    """
    Génère une clé de cache stable et déterministe pour une slide HTML.

    Stabilité garantie par :
    - sort_keys=True : ordre des clés canonique
    - default=str : gère les dates Python (sinon crash)
    - ensure_ascii=True : évite les variations d'encodage
    - Préfixe SKILL_VERSION : invalide le cache si le skill change

    Returns:
        Clé courte et lisible (préfixe "slide_html:" + 20 chars hex)
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


# ─────────────────────────────────────────────────────────────────────────────
# Opérations Supabase
# ─────────────────────────────────────────────────────────────────────────────

def cache_get(key: str) -> str | None:
    """
    Récupère le HTML en cache pour une clé donnée.
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
        # Le cache est best-effort : une erreur Supabase ne doit pas bloquer la génération
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
