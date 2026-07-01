"""
Slides 5.0 builder — chemin unique et propre.

Architecture Sprint 5 :
  layout_engine_5_0 (deterministique, source de verite positions)
    -> validate_slide_objects (schema unique, rejette les malformes)
    -> [optionnel] NarrativeAgent.fill_text_slots (enrichit les slots texte)
    -> [optionnel] QAAgent.validate_and_merge (revert slot par slot si echec)

Sprint 9 — Chemin B HTML generatif (USE_HTML_SLIDE_AGENT=true) :
  ThreadPoolExecutor parallelise les appels Gemini (sync-safe, pas asyncio)
  Circuit breaker partage par etude : 3 echecs -> bascule tout en deterministique
  Cache Supabase (slide_cache.py) : 0 appel Gemini si section_data identique
  Le deterministique PPTX reste le fallback garanti pour chaque slide

Sprint 10 v2 (Chantier D) :
  _section_has_data() verifie que la section a assez de donnees avant d'appeler
  Gemini (evite l'hallucination + rejet QA). La slide PPTX reste toujours produite.

INVARIANT : le pipeline produit TOUJOURS 15 slides, meme si Gemini tombe.
  html_content=None -> renderer frontend utilise le PPTX deterministique.

slide_builder_agent (Vertex AI / Sprint 2) n'est PLUS dans le chemin actif.
"""
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from app.api.schemas.common import Study
from app.schemas.slide_objects import validate_slide_objects
from app.services.css_vars_builder import build_css_vars_for_study
from app.services.layout_engine_5_0 import build_slide_5_0
from app.services.master_json_builder import master_json_builder
from app.services.section_registry import SECTION_REGISTRY
from app.services.slide_data_builder_5_0 import build_slide_data_5_0, collect_expected_strings

logger = logging.getLogger(__name__)

USE_NARRATIVE_AGENT = os.environ.get("SLIDE_BUILDER_USE_AGENT", "false").lower() == "true"
USE_HTML_AGENT = os.environ.get("USE_HTML_SLIDE_AGENT", "false").lower() == "true"
_MAX_PARALLEL = int(os.environ.get("HTML_AGENT_PARALLELISM", "5"))

FALLBACK = "Donnee non disponible (TBD)"


# -----------------------------------------------------------------------------
# Circuit breaker — partage par etude, thread-safe (faille v2 corrigee)
# -----------------------------------------------------------------------------
# En v2, le breaker etait local a chaque appel => jamais declenche.
# Ici il vit le temps d'une generation et est partage entre les threads du pool.
# 3 echecs Gemini consecutifs => is_open=True => toutes les slides restantes
# basculent en deterministique sans attendre N*timeout.

class _Breaker:
    def __init__(self, threshold: int = 3):
        self.failures = 0
        self.threshold = threshold
        self.lock = threading.Lock()

    def record_failure(self) -> None:
        with self.lock:
            self.failures += 1

    def record_success(self) -> None:
        with self.lock:
            self.failures = 0

    @property
    def is_open(self) -> bool:
        return self.failures >= self.threshold


_breakers: dict[str, _Breaker] = {}
_breakers_lock = threading.Lock()


def _get_breaker(study_id: str) -> _Breaker:
    with _breakers_lock:
        if study_id not in _breakers:
            _breakers[study_id] = _Breaker()
        return _breakers[study_id]


# Sections structurelles toujours incluses meme si donnees manquantes
_ALWAYS_INCLUDE = {"cover", "executive_summary", "swot", "verdict"}


# -----------------------------------------------------------------------------
# Chantier D — garde "donnees suffisantes" pour le chemin B HTML (Sprint 10)
# -----------------------------------------------------------------------------
# Si une section n'a pas assez de donnees, on ne genere pas de slide HTML
# (l'agent hallucinerait ou produirait une slide vide). La slide PPTX deterministe
# reste toujours produite — l'invariant "15 slides garanties" n'est pas touche.

_SECTION_DATA_REQUIREMENTS: dict = {
    "funding_feasibility": lambda m: m.get("funding_scale") is not None,
    "benchmark_comparison": lambda m: len(m.get("benchmark_rows", [])) >= 3,
    "demographics":         lambda m: m.get("demographics_pie") is not None,
    "competition_mapping":  lambda m: len(m.get("competitors_top", [])) >= 1,
}


def _section_has_data(section_id: str, manifest: dict) -> bool:
    """
    Retourne True si la section dispose de donnees suffisantes pour une slide HTML.
    False -> chemin B bypasse pour cette section, pas d'appel Gemini.
    La slide PPTX deterministe est produite independamment de cette valeur.
    """
    check = _SECTION_DATA_REQUIREMENTS.get(section_id)
    if check is None:
        return True  # pas de contrainte connue -> on laisse l'agent essayer
    try:
        return bool(check(manifest))
    except Exception:
        return False


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _is_slide_data_empty(slide_data: Dict[str, Any]) -> bool:
    """
    Retourne True si TOUS les slots de donnees primaires d'un slide
    sont a la valeur FALLBACK. Les champs statiques (title/eyebrow)
    ne sont pas comptes.
    """
    for key in ("metrics", "columns", "steps", "hero_kpis", "quadrants"):
        items = slide_data.get(key)
        if items is not None and isinstance(items, list) and len(items) > 0:
            non_fallback = [
                item for item in items
                if isinstance(item, dict) and item.get("value") not in (None, FALLBACK, "")
            ]
            if non_fallback:
                return False
            return True
    return False


def _resolve_brand_slug(study: Study) -> str | None:
    """
    Resout le slug de marque depuis tenant_id ou brand_name.
    Priorite : brand_name (ex: "o2") > tenant_id (ex: "interdomicilio") > None.
    """
    from app.core.brand_profiles import get_brand_profile

    brand_words = (study.business_context.brand_name or "").strip().lower().split()
    if brand_words and get_brand_profile(brand_words[0]):
        return brand_words[0]

    if study.tenant_id and get_brand_profile(study.tenant_id):
        return study.tenant_id

    return study.tenant_id or None


# -----------------------------------------------------------------------------
# Preparation des donnees section -> prompt (Sprint 9 — Chemin B)
# -----------------------------------------------------------------------------

def _prepare_section_data(study: Study, section_id: str, manifest: dict) -> dict:
    """
    Extrait du manifest uniquement les donnees pertinentes pour la section.

    RÉÉCRIT Sprint 13 — UNE SEULE SOURCE DE MAPPING : SECTION_DATA_KEYS
    (html_slide_agent). L'ancienne version dupliquait le mapping en branches
    if/elif locales, systématiquement désynchronisées :
      - geo_analysis / market_overview : aucune branche → fallback metrics[:8],
        jamais de microzones ni market_sizing (constaté : slides pleines de n.d.)
      - verdict : lisait manifest["verdict"] inexistant au top-level
      - competition : competition_table jamais transmise (Sprint 12 cassé)
    Constat gallery 01/07 : 5 sections sur 10 en QA FAIL, 4 affamées de données.

    Les noms externes (Places) sont sanitisés avant d'entrer dans le prompt.
    Ne jamais passer le manifest complet au LLM.
    """
    from app.agents.html_slide_agent import _filter_section_data
    from app.agents.sanitize import (
        sanitize_competition_table,
        sanitize_competitors_for_prompt,
    )

    data = _filter_section_data(section_id, manifest)

    # Sanitisation des données externes (Places) pour la concurrence
    if section_id in ("competition", "competition_mapping"):
        if data.get("competition_table"):
            data["competition_table"] = sanitize_competition_table(
                data["competition_table"]
            )
        if data.get("competitors_top"):
            data["competitors_top"] = sanitize_competitors_for_prompt(
                data["competitors_top"]
            )

    # Contexte interne (sûr) — utilisé par les .md des sections
    data.update({
        "zone": study.geo_scope.city or "",
        "brand_name": study.business_context.brand_name or "",
        "year": "2026",
        "language": study.language or "fr",
        # Sprint 14a — l'intention client (wizard + brand profile) accompagne
        # chaque section : le manifest la porte au top-level ("intent").
        "intent": manifest.get("intent"),
    })
    return data


# -----------------------------------------------------------------------------
# Generation HTML d'une slide (Sprint 9 — Chemin B, thread-safe)
# -----------------------------------------------------------------------------

def _generate_one_html(
    section: dict,
    section_idx: int,
    study: Study,
    manifest: dict,
    breaker: _Breaker,
) -> str | None:
    """
    Genere le HTML complet d'une slide via HTMLSlideAgent.
    Retourne None en cas d'echec -> la slide sera servie en deterministique (PPTX).

    Integre :
    - Circuit breaker : si is_open -> bypass immediat (economie timeout)
    - Chantier D : verif donnees suffisantes avant appel Gemini
    - Cache Supabase : si section_data identique -> 0 appel Gemini
    - QA deterministique : si nombres non traces -> None (pas de HTML invente)
    """
    if breaker.is_open:
        logger.info("[slides_builder] breaker ouvert -> fallback %s", section["section_id"])
        return None

    # Chantier D : verifier que la section dispose de donnees suffisantes
    # AVANT d'appeler Gemini (evite l'hallucination + le rejet QA qui suivrait)
    section_id = section["section_id"]
    if not _section_has_data(section_id, manifest):
        logger.info(
            "[slides_builder] donnees insuffisantes -> pas de HTML pour %s",
            section_id,
        )
        return None

    try:
        from app.agents.html_slide_agent import html_slide_agent
        from app.agents.qa_html_agent import validate_html
        from app.services.slide_cache import cache_get, cache_set, slide_cache_key

        brand = study.tenant_id or "interdomicilio"
        language = (study.language or "fr")[:2]

        section_data = _prepare_section_data(study, section_id, manifest)

        # Lookup cache avant Gemini
        cache_key = slide_cache_key(section_id, section_data)
        cached = cache_get(cache_key)
        if cached:
            breaker.record_success()
            return cached

        # Generation Gemini
        main = html_slide_agent.generate_main_content(
            section_id=section_id,
            section_number=section_idx,
            section_data=section_data,
            brand=brand,
            language=language,
        )
        if not main:
            breaker.record_failure()
            return None

        # QA deterministique
        ok, issues = validate_html(main, manifest)
        if not ok:
            logger.info(
                "[slides_builder] QA FAIL %s — %d issues : %s",
                section_id, len(issues), issues[:3],
            )
            breaker.record_failure()
            return None

        # Assemblage HTML complet
        full_html = html_slide_agent.assemble_slide(
            section_id=section_id,
            section_number=section_idx,
            section_title=section.get("display_name", section_id),
            section_subtitle="Marche " + (study.geo_scope.city or ""),
            main_content=main,
            brand=brand,
            language=language,
            zone=study.geo_scope.city or "",
            year="2026",
        )

        # Mise en cache
        cache_set(cache_key, full_html)
        breaker.record_success()
        return full_html

    except Exception as exc:
        logger.warning(
            "[slides_builder] _generate_one_html KO %s -> fallback : %s",
            section.get("section_id"), exc,
        )
        breaker.record_failure()
        return None


# -----------------------------------------------------------------------------
# Pipeline principal
# -----------------------------------------------------------------------------

def build_slides_5_0_for_study(study: Study) -> Dict[str, Any]:
    slides: List[Dict[str, Any]] = []
    skipped: List[str] = []

    # Manifest — source de verite pour l'agent et le QA
    # Sprint 10 : manifest enrichi par precompute_slide_values() (benchmark_rows, etc.)
    manifest = master_json_builder.build(study)

    # Import optionnel de NarrativeAgent (silencieux si indispo)
    _narrative_agent = None
    if USE_NARRATIVE_AGENT:
        try:
            from app.agents.narrative_agent import narrative_agent as _na
            _narrative_agent = _na
            logger.info("[slides_builder] NarrativeAgent actif")
        except Exception as _e:
            logger.warning("[slides_builder] NarrativeAgent non disponible : %s", _e)

    # Import optionnel de QAAgent
    _qa_agent = None
    if USE_NARRATIVE_AGENT:
        try:
            from app.agents.qa_agent import qa_agent as _qa
            _qa_agent = _qa
        except Exception as _e:
            logger.warning("[slides_builder] QAAgent non disponible : %s", _e)

    if not USE_NARRATIVE_AGENT:
        logger.info("[slides_builder] Mode deterministique pur (SLIDE_BUILDER_USE_AGENT=false)")

    # -- Chemin B : generation HTML en parallele (USE_HTML_SLIDE_AGENT=true) --
    # IMPORTANT : ne pas utiliser asyncio (pipeline sync). ThreadPoolExecutor
    # seul est compatible. Le deterministique PPTX est TOUJOURS construit en fallback.
    html_by_section: dict[str, str | None] = {}
    if USE_HTML_AGENT:
        breaker = _get_breaker(study.study_id)
        logger.info(
            "[slides_builder] Chemin B HTML actif (parallelism=%d)", _MAX_PARALLEL
        )
        with ThreadPoolExecutor(max_workers=_MAX_PARALLEL) as executor:
            futures = {
                executor.submit(
                    _generate_one_html, section, idx, study, manifest, breaker
                ): section["section_id"]
                for idx, section in enumerate(SECTION_REGISTRY, start=1)
            }
            for future in as_completed(futures):
                sid = futures[future]
                try:
                    html_by_section[sid] = future.result()
                except Exception as exc:
                    logger.warning(
                        "[slides_builder] future KO %s : %s", sid, exc
                    )
                    html_by_section[sid] = None
    # -- Fin Chemin B ---------------------------------------------------------

    for idx, section in enumerate(SECTION_REGISTRY, start=1):
        section_id = section["section_id"]
        display_name = section.get("display_name", section_id)
        expected_kpis = section.get("expected_kpis") or []

        # 1. Build donnees + layout deterministique — TOUJOURS, jamais bypass
        slide_data = build_slide_data_5_0(study, section_id, expected_kpis, display_name=display_name)

        # Filtrage des slides sans donnees (sauf sections structurelles)
        if section_id not in _ALWAYS_INCLUDE and _is_slide_data_empty(slide_data):
            skipped.append(section_id)
            continue

        layout = build_slide_5_0(section_id, slide_data)

        # 2. Validation schema unique — rejette les objets malformes ou hors canvas
        objects = validate_slide_objects(layout["objects"])

        # 3. Enrichissement narratif optionnel + QA slot par slot
        if _narrative_agent:
            try:
                enriched = _narrative_agent.fill_text_slots(
                    objects, manifest, language=study.language or "fr"
                )
                if _qa_agent:
                    objects = _qa_agent.validate_and_merge(
                        agent_objects=enriched,
                        deterministic_objects=objects,
                        manifest=manifest,
                    )
                else:
                    objects = enriched
            except Exception as e:
                logger.warning(
                    "[slides_builder] NarrativeAgent KO sur '%s' -> fallback deterministique : %s",
                    section_id, e,
                )

        slides.append({
            "slide_index": idx,
            "slide_id": f"slide_{idx:02d}_{section_id}",
            "section_id": section_id,
            "title": slide_data["title"],
            "layout": layout["layout"],
            "background": layout["background"],
            "canvas": layout["canvas"],
            "safe_margin": layout["safe_margin"],
            "whitespace_ratio": layout.get("whitespace_ratio", 0.0),
            "whitespace_compliant": layout.get("whitespace_compliant", True),
            "expected_kpis": expected_kpis,
            "slide_data": slide_data,
            "objects": objects,
            "expected_strings": collect_expected_strings(slide_data),
            "agent_generated": _narrative_agent is not None,
            # html_content=None si USE_HTML_AGENT=false ou si QA a echoue
            # -> le renderer frontend utilise le PPTX deterministique (fallback garanti)
            "html_content": html_by_section.get(section_id) if USE_HTML_AGENT else None,
        })

    brand_slug = _resolve_brand_slug(study)
    css_vars = build_css_vars_for_study(brand_slug, study.brand_profile_override)

    return {
        "version": "5.0.0",
        "study_id": study.study_id,
        "tenant_id": study.tenant_id,
        "canvas": {"width": 1920, "height": 1080},
        "brand_slug": brand_slug,
        "css_vars": css_vars,
        "slides": slides,
        "skipped_sections": skipped,
        "use_html": USE_HTML_AGENT,
    }


def get_slide_5_0(payload: Dict[str, Any], slide_id: str) -> Dict[str, Any] | None:
    """Recupere un slide par son slide_id dans le payload slides_5_0."""
    for slide in payload.get("slides", []):
        if slide.get("slide_id") == slide_id:
            return slide
    return None
