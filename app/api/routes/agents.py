"""
Stubs des endpoints agents Stella — Phase 2.

Ces endpoints définissent le contrat d'interface avec les 13 agents futurs.
Ils reçoivent et valident les payloads, les journalisent, et retournent une réponse
structurée avec statut "accepted" ou "rejected".

Agents concernés (Phase 2) :
  - Sourcing Scout / Crawler Reasoner → crawl-plan/validate
  - Field Extractor / Quality Gate   → extraction/submit
  - Slide Planner / Layout Designer  → slides/playlist
  - Visual QA                        → visual-qa/report

Note architecturale :
  - Le backend Stella reste la source de vérité.
  - Les agents sont des workers isolés qui soumettent des proposals.
  - Le backend valide, accepte ou rejette chaque proposal.
  - Aucune logique métier n'est déléguée aux agents sans validation backend.
"""

import logging
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


# ---------------------------------------------------------------------------
# Schémas inline (Pydantic importé localement pour éviter les imports cycliques)
# ---------------------------------------------------------------------------
from pydantic import BaseModel, Field  # noqa: E402


class AgentResponse(BaseModel):
    request_id: str
    status: str          # "accepted" | "rejected"
    message: str
    received_at: str
    payload_keys: list[str] = Field(default_factory=list)


def _make_response(status: str, message: str, payload: dict) -> AgentResponse:
    return AgentResponse(
        request_id=f"areq_{uuid4().hex[:12]}",
        status=status,
        message=message,
        received_at=datetime.now(UTC).isoformat(),
        payload_keys=list(payload.keys()),
    )


# ---------------------------------------------------------------------------
# 1. Crawl Plan Validate
# ---------------------------------------------------------------------------
class CrawlPlanProposal(BaseModel):
    study_id: str
    agent_id: str = "sourcing_scout"
    urls: list[str] = Field(..., min_length=1, max_length=200)
    source_themes: list[str] = Field(default_factory=list)
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    notes: str | None = None


@router.post("/crawl-plan/validate", response_model=AgentResponse)
def validate_crawl_plan(proposal: CrawlPlanProposal) -> AgentResponse:
    """
    Soumettre un plan de crawl pour validation backend.

    L'agent Sourcing Scout / Crawler Reasoner propose une liste d'URLs
    et de thèmes à crawler pour une étude donnée.
    Le backend valide que :
    - l'étude existe
    - les URLs ne sont pas dans la liste noire
    - le plan est cohérent avec les thèmes attendus de l'étude
    """
    from app.repositories.studies_repo import studies_repo
    study = studies_repo.get(proposal.study_id)
    if not study:
        raise HTTPException(status_code=404, detail=f"Study '{proposal.study_id}' not found")

    logger.info(
        "[agent:crawl-plan] study=%s agent=%s urls=%d themes=%s",
        proposal.study_id, proposal.agent_id,
        len(proposal.urls), proposal.source_themes,
    )

    # Validation : au moins 1 URL, pas de domaines bloqués (extensible)
    blocked = [u for u in proposal.urls if any(b in u for b in ["localhost", "127.0.0.1"])]
    if blocked:
        return _make_response(
            "rejected",
            f"URLs bloquées détectées : {blocked[:3]}",
            proposal.model_dump(),
        )

    return _make_response(
        "accepted",
        f"Plan de crawl accepté — {len(proposal.urls)} URLs, {len(proposal.source_themes)} thèmes",
        proposal.model_dump(),
    )


# ---------------------------------------------------------------------------
# 2. Extraction Submit
# ---------------------------------------------------------------------------
class ExtractionResult(BaseModel):
    study_id: str
    agent_id: str = "field_extractor"
    source_url: str
    theme_id: str
    extracted_fields: dict = Field(default_factory=dict)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    raw_text_excerpt: str | None = None


@router.post("/extraction/submit", response_model=AgentResponse)
def submit_extraction(result: ExtractionResult) -> AgentResponse:
    """
    Soumettre le résultat d'extraction d'un agent Field Extractor / Quality Gate.

    Le backend valide :
    - que l'étude existe
    - que le theme_id est connu dans SECTION_REGISTRY
    - que les champs extraits ont une confidence suffisante
    """
    from app.repositories.studies_repo import studies_repo
    from app.services.section_registry import SECTION_REGISTRY

    study = studies_repo.get(result.study_id)
    if not study:
        raise HTTPException(status_code=404, detail=f"Study '{result.study_id}' not found")

    known_themes = {s["section_id"] for s in SECTION_REGISTRY}
    if result.theme_id not in known_themes:
        return _make_response(
            "rejected",
            f"theme_id '{result.theme_id}' inconnu. Thèmes valides : {sorted(known_themes)[:5]}…",
            result.model_dump(),
        )

    if result.confidence < 0.5:
        return _make_response(
            "rejected",
            f"Confidence trop basse ({result.confidence:.2f} < 0.5) — extraction rejetée",
            result.model_dump(),
        )

    logger.info(
        "[agent:extraction] study=%s agent=%s theme=%s fields=%d confidence=%.2f",
        result.study_id, result.agent_id,
        result.theme_id, len(result.extracted_fields), result.confidence,
    )

    return _make_response(
        "accepted",
        f"Extraction acceptée — {len(result.extracted_fields)} champs, theme={result.theme_id}",
        result.model_dump(),
    )


# ---------------------------------------------------------------------------
# 3. Slides Playlist
# ---------------------------------------------------------------------------
class SlidePlaylistProposal(BaseModel):
    study_id: str
    agent_id: str = "slide_planner"
    proposed_sections: list[str] = Field(..., min_length=1)
    layout_overrides: dict[str, str] = Field(default_factory=dict)  # section_id → layout_type
    narrative_tone: str = "professional"  # professional | accessible | executive
    notes: str | None = None


@router.post("/slides/playlist", response_model=AgentResponse)
def submit_slide_playlist(proposal: SlidePlaylistProposal) -> AgentResponse:
    """
    Soumettre une proposition de playlist de slides.

    L'agent Slide Planner propose l'ordre et les layouts des slides.
    Le backend valide que :
    - toutes les sections proposées sont dans SECTION_REGISTRY
    - les sections obligatoires (cover, verdict, executive_summary) sont présentes
    - les layout_overrides correspondent à des layouts connus
    """
    from app.repositories.studies_repo import studies_repo
    from app.services.section_registry import SECTION_REGISTRY

    study = studies_repo.get(proposal.study_id)
    if not study:
        raise HTTPException(status_code=404, detail=f"Study '{proposal.study_id}' not found")

    known_sections = {s["section_id"] for s in SECTION_REGISTRY}
    unknown = [s for s in proposal.proposed_sections if s not in known_sections]
    if unknown:
        return _make_response(
            "rejected",
            f"Sections inconnues : {unknown}",
            proposal.model_dump(),
        )

    mandatory = {"cover", "verdict", "executive_summary"}
    missing_mandatory = mandatory - set(proposal.proposed_sections)
    if missing_mandatory:
        return _make_response(
            "rejected",
            f"Sections obligatoires manquantes : {sorted(missing_mandatory)}",
            proposal.model_dump(),
        )

    known_layouts = {
        "Hero-Split-6040", "Sidebar-Analysis-7030",
        "Grid-Asymmetric-3Columns", "Matrix-4Quadrants", "Timeline-Horizontal-3Steps",
    }
    bad_layouts = {k: v for k, v in proposal.layout_overrides.items() if v not in known_layouts}
    if bad_layouts:
        return _make_response(
            "rejected",
            f"Layouts inconnus : {bad_layouts}. Valides : {sorted(known_layouts)}",
            proposal.model_dump(),
        )

    logger.info(
        "[agent:slides-playlist] study=%s agent=%s sections=%d overrides=%d tone=%s",
        proposal.study_id, proposal.agent_id,
        len(proposal.proposed_sections), len(proposal.layout_overrides),
        proposal.narrative_tone,
    )

    return _make_response(
        "accepted",
        f"Playlist acceptée — {len(proposal.proposed_sections)} slides, ton={proposal.narrative_tone}",
        proposal.model_dump(),
    )


# ---------------------------------------------------------------------------
# 4. Visual QA Report
# ---------------------------------------------------------------------------
class VisualQAIssue(BaseModel):
    object_id: str
    issue_type: str   # "overlap" | "contrast" | "overflow" | "whitespace"
    severity: str     # "error" | "warning" | "info"
    description: str
    apca_score: float | None = None


class VisualQAReport(BaseModel):
    study_id: str
    slide_id: str
    agent_id: str = "visual_qa"
    issues: list[VisualQAIssue] = Field(default_factory=list)
    whitespace_ratio: float | None = None
    overall_status: str = "pass"   # "pass" | "warn" | "fail"


# ---------------------------------------------------------------------------
# 5. Slide Preview (Slide Builder Agent)
# ---------------------------------------------------------------------------

@router.post("/slides/preview")
def preview_slide_agent(
    payload: dict,
    x_tenant_id: str = "interdomicilio",
) -> dict:
    """
    Teste l'agent Slide Builder sur une section donnée.
    Utile pour valider un template sans relancer une étude complète.

    Body attendu :
    {
      "section_id": "market_scorecard",
      "manifest_data": { ... }   // manifest complet ou partiel
    }
    """
    from fastapi import Header as _Header  # noqa — import local pour éviter le conflit global

    from app.agents.slide_builder_agent import slide_builder_agent

    section_id = payload.get("section_id", "market_scorecard")
    manifest_data = payload.get("manifest_data", {})
    language = payload.get("language", "fr")

    return slide_builder_agent.build_slide(
        section_id=section_id,
        manifest_data=manifest_data,
        tenant_id=x_tenant_id,
        language=language,
    )


# ---------------------------------------------------------------------------
# 6. Debug — Google Places Probe (Sprint 9 — dual-API diagnostic)
# ---------------------------------------------------------------------------

@router.get("/debug/places-probe")
def debug_places_probe(
    query: str = "aide à domicile Bordeaux",
) -> dict:
    """
    Diagnostic dual-API Google Places — teste Legacy textsearch ET New API.

    Appeler : GET /agents/debug/places-probe?query=aide+à+domicile+Bordeaux

    Interprétation :
    - new.count > 0, legacy en erreur  → migrer sur New API (cas attendu)
    - legacy.count > 0                 → garder Legacy, bug ailleurs (keyword/radius)
    - Les deux REQUEST_DENIED          → clé non activée pour Places API (New)
                                          ou clé restreinte par référent HTTP

    Décision après résultat :
      new.count > 0 → implémenter A.2 (collector New API)
      legacy.count > 0 → ajuster SAP_KEYWORDS_FR et radius dans google_places_api.py
    """
    import os
    import httpx

    key = os.environ.get("GOOGLE_PLACES_API_KEY", "")
    if not key:
        return {"error": "GOOGLE_PLACES_API_KEY absente de l'env Render"}

    out: dict = {}

    # --- Legacy Text Search ---
    try:
        r = httpx.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={"query": query, "key": key},
            timeout=10,
        )
        d = r.json()
        out["legacy_textsearch"] = {
            "http": r.status_code,
            "status": d.get("status"),
            "count": len(d.get("results", [])),
            "error": d.get("error_message"),
            "names": [p["name"] for p in d.get("results", [])[:5]],
        }
    except Exception as e:
        out["legacy_textsearch"] = {"exception": str(e)}

    # --- New Places API (Places API (New)) ---
    try:
        r = httpx.post(
            "https://places.googleapis.com/v1/places:searchText",
            headers={
                "Content-Type": "application/json",
                "X-Goog-Api-Key": key,
                "X-Goog-FieldMask": (
                    "places.displayName,places.formattedAddress,"
                    "places.rating,places.userRatingCount,places.types"
                ),
            },
            json={"textQuery": query, "languageCode": "fr"},
            timeout=10,
        )
        d = r.json()
        out["new_places_api"] = {
            "http": r.status_code,
            "count": len(d.get("places", [])),
            "error": d.get("error", {}).get("message"),
            "names": [
                p.get("displayName", {}).get("text", "?")
                for p in d.get("places", [])[:5]
            ],
        }
    except Exception as e:
        out["new_places_api"] = {"exception": str(e)}

    # --- Recommandation automatique ---
    new_ok = out.get("new_places_api", {}).get("count", 0) > 0
    legacy_ok = out.get("legacy_textsearch", {}).get("count", 0) > 0
    if new_ok:
        recommendation = "NEW_API_OK → implémenter A.2 (New Places API collector)"
    elif legacy_ok:
        recommendation = "LEGACY_OK → bug dans collector (keyword/radius), pas dans l'API"
    else:
        recommendation = "BOTH_FAIL → vérifier activation 'Places API (New)' dans Google Cloud Console"

    return {
        "query": query,
        "key_present": bool(key),
        "key_prefix": key[:8] + "..." if key else "",
        "recommendation": recommendation,
        "results": out,
    }


# ---------------------------------------------------------------------------
# 7. Debug — HTML Slide (Sprint 8 — Chemin B test décisif)
# ---------------------------------------------------------------------------

@router.get("/debug/html-slide")
def debug_html_slide(
    study_id: str,
    section_id: str = "competition",
) -> object:
    """
    Génère UNE slide en HTML pour test visuel.

    Retourne le HTML brut (à ouvrir dans un navigateur) si le QA passe.
    Si le QA échoue : retourne un JSON avec les nombres non tracés.

    Usage :
      GET /agents/debug/html-slide?study_id=18f460c9-245b-4443-aa65-23eb2032089c
      GET /agents/debug/html-slide?study_id=...&section_id=competition

    Exige :
      - GEMINI_API_KEY configuré sur Render
      - L'étude doit avoir des competitors_top dans son manifest
    """
    from fastapi.responses import Response as FastAPIResponse

    from app.repositories.studies_repo import studies_repo
    from app.agents.html_slide_agent import html_slide_agent
    from app.agents.qa_html_agent import validate_html
    from app.services.master_json_builder import master_json_builder

    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(404, f"Study '{study_id}' not found")

    manifest = master_json_builder.build(study)

    # Fix Sprint 13 — le debug utilise EXACTEMENT le même chemin de préparation
    # que la prod (_prepare_section_data). L'ancien cas spécial divergeait :
    # pas de competition_table, zone/brand perdus → "QA PASS en debug" ne
    # prouvait rien sur le pipeline réel.
    from app.services.slides_5_0_builder import _prepare_section_data
    section_data = _prepare_section_data(study, section_id, manifest)

    # Sprint 13c — cache branché sur le debug (même clé que la prod) :
    # une slide validée QA est FIGÉE (fini la roulette Gemini à chaque affichage),
    # et la galerie devient quasi instantanée. Invalidation auto par SKILL_VERSION.
    from fastapi.responses import Response as _Resp
    from app.services.slide_cache import cache_get, cache_set, slide_cache_key
    _cache_key = slide_cache_key(section_id, section_data)
    _cached = cache_get(_cache_key)
    if _cached:
        return _Resp(content=_cached, media_type="text/html")

    logger.info(
        "[debug/html-slide] study=%s section=%s data_keys=%s",
        study_id, section_id, list(section_data.keys()),
    )

    # Fix Sprint 13 — titre et numéro par section (plus de "Cartographie
    # concurrentielle" en dur sur toutes les slides de debug).
    from app.services.section_registry import SECTION_REGISTRY
    _titles = {s["section_id"]: s["display_name"] for s in SECTION_REGISTRY}
    _numbers = {s["section_id"]: i + 1 for i, s in enumerate(SECTION_REGISTRY)}
    # Sections skill hors registry (alias/enrichies)
    _titles.setdefault("competition", "Concurrence")
    _titles.setdefault("benchmark_comparison", "Benchmark national")
    _titles.setdefault("funding_feasibility", "Financement & solvabilité")
    _titles.setdefault("market_overview", "Vue d'ensemble du marché")
    _titles.setdefault("geo_analysis", "Analyse géographique")
    section_title = _titles.get(section_id, section_id.replace("_", " ").capitalize())
    section_number = _numbers.get(section_id, 11)

    main_content = html_slide_agent.generate_main_content(
        section_id=section_id,
        section_number=section_number,
        section_data=section_data,
        brand=study.tenant_id or "interdomicilio",
        language="fr",
    )

    if not main_content:
        return {
            "error": "génération HTML échouée (Gemini indisponible ou skill manquant)",
            "html": None,
            "study_id": study_id,
        }

    qa_ok, issues = validate_html(main_content, manifest)

    full_html = html_slide_agent.assemble_slide(
        section_id=section_id,
        section_number=section_number,
        section_title=section_title,
        section_subtitle=f"Marché {study.geo_scope.city or ''}",
        main_content=main_content,
        brand=study.tenant_id or "interdomicilio",
        language="fr",
        study_type="Étude de faisabilité",
        zone=study.geo_scope.city or "",
        year="2026",
    )

    if qa_ok:
        logger.info("[debug/html-slide] QA OK — slide HTML retournée")
        cache_set(_cache_key, full_html)  # Sprint 13c : figer la slide validée
        return FastAPIResponse(content=full_html, media_type="text/html")
    else:
        logger.warning(
            "[debug/html-slide] QA FAIL — %d issues : %s",
            len(issues), issues[:5],
        )
        return {
            "qa_failed": True,
            "issue_count": len(issues),
            "issues": issues[:20],
            "html": full_html,
        }


@router.get("/debug/manifest")
def debug_manifest(study_id: str) -> dict:
    """
    Retourne les valeurs Sprint 10 precalculees pour une etude (debug).

    Verifie que slide_precompute.py a bien calcule :
    benchmark_rows, demographics_pie, scores_radar, competition_avg_rating.

    Usage :
      GET /agents/debug/manifest?study_id=18f460c9-245b-4443-aa65-23eb2032089c
    """
    import json
    from app.repositories.studies_repo import studies_repo
    from app.services.master_json_builder import master_json_builder

    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(404, f"Study '{study_id}' not found")

    manifest = master_json_builder.build(study)

    sprint10_check = {
        "benchmark_rows_count":   len(manifest.get("benchmark_rows") or []),
        "benchmark_rows_sample":  (manifest.get("benchmark_rows") or [])[:2],
        "demographics_pie":       manifest.get("demographics_pie"),
        "scores_radar":           manifest.get("scores_radar"),
        "competition_avg_rating": manifest.get("competition_avg_rating"),
        "competitors_top_count":  len(manifest.get("competitors_top") or []),
        "funding_scale_present":  manifest.get("funding_scale") is not None,
        "market_sizing_present":  manifest.get("market_sizing") is not None,
    }

    logger.info("[debug/manifest] study=%s sprint10=%s", study_id, sprint10_check)

    return {
        "study_id": study_id,
        "sprint10_precompute": sprint10_check,
        "manifest_keys": list(manifest.keys()),
        "manifest_full": json.loads(json.dumps(manifest, default=str)),
    }


# ---------------------------------------------------------------------------
# 7bis. Debug — Galerie visuelle (Sprint 13)
# ---------------------------------------------------------------------------

@router.get("/debug/slides-gallery")
def debug_slides_gallery(study_id: str) -> object:
    """
    Page HTML unique affichant TOUTES les sections d'une étude en iframes.

    Règle de validation Stella : "QA PASS ≠ validé — capture visuelle obligatoire".
    Cet endpoint rend la validation visuelle possible en UNE navigation au lieu
    de N appels manuels à /debug/html-slide.

    Zéro coût backend supplémentaire : la page ne fait que pointer des iframes
    vers /agents/debug/html-slide — chaque slide se génère (ou sort du cache)
    indépendamment, pas de timeout global.

    Usage :
      GET /agents/debug/slides-gallery?study_id=29604753-ae5f-4d30-a5ac-04b25be29115
    """
    from fastapi.responses import Response as FastAPIResponse
    from app.repositories.studies_repo import studies_repo

    study = studies_repo.get(study_id)
    if not study:
        raise HTTPException(404, f"Study '{study_id}' not found")

    sections = [
        # Ordre deck (Sprint 13b : + cover, employment_talent, income_housing,
        # methodology_sources)
        "cover", "executive_summary", "market_overview", "demographics",
        "employment_talent", "income_housing", "geo_analysis",
        "benchmark_comparison", "competition_mapping", "funding_feasibility",
        "swot", "verdict", "action_plan", "methodology_sources",
    ]
    city = study.geo_scope.city or ""

    cards = "\n".join(
        f"""
        <div class="card">
          <div class="card-head">
            <span class="num">{i + 1}</span>
            <span class="sid">{sid}</span>
            <a href="/agents/debug/html-slide?study_id={study_id}&section_id={sid}"
               target="_blank">ouvrir seule ↗</a>
          </div>
          <div class="frame-wrap">
            <iframe loading="lazy" sandbox="allow-scripts"
                    referrerpolicy="no-referrer"
                    src="/agents/debug/html-slide?study_id={study_id}&section_id={sid}"></iframe>
          </div>
        </div>"""
        for i, sid in enumerate(sections)
    )

    html = f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<title>Stella — Galerie {city} ({study_id[:8]})</title>
<style>
  body {{ margin:0; padding:24px; background:#111827; color:#e5e7eb;
         font-family: system-ui, sans-serif; }}
  h1 {{ font-size:18px; font-weight:600; }}
  h1 small {{ color:#9ca3af; font-weight:400; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(660px,1fr));
           gap:24px; }}
  .card {{ background:#1f2937; border-radius:10px; padding:12px; }}
  .card-head {{ display:flex; align-items:center; gap:10px; margin-bottom:8px;
                font-size:13px; }}
  .num {{ background:#0095D9; color:#fff; border-radius:6px; padding:1px 8px;
          font-weight:700; }}
  .sid {{ flex:1; font-family:monospace; }}
  .card-head a {{ color:#7dd3fc; text-decoration:none; }}
  .frame-wrap {{ position:relative; width:100%; aspect-ratio:1280/720;
                 overflow:hidden; border-radius:6px; background:#fff; }}
  iframe {{ position:absolute; top:0; left:0; width:1280px; height:720px;
            border:0; transform-origin:top left; }}
</style></head>
<body>
<h1>Stella — validation visuelle <small>{city} · étude {study_id} ·
si une slide affiche du JSON = QA FAIL (lire "issues")</small></h1>
<div class="grid">{cards}</div>
<script>
  // Scale chaque iframe 1280x720 dans son conteneur
  function rescale() {{
    document.querySelectorAll('.frame-wrap').forEach(w => {{
      const f = w.querySelector('iframe');
      f.style.transform = 'scale(' + (w.clientWidth / 1280) + ')';
    }});
  }}
  window.addEventListener('resize', rescale);
  rescale();
</script>
</body></html>"""
    return FastAPIResponse(content=html, media_type="text/html")


@router.delete("/debug/clear-slide-cache")
def clear_slide_cache(study_id: str | None = None) -> dict:
    """
    Vide le cache HTML slides dans Supabase sans redeploy.

    - Sans study_id : vide tout le cache (toutes les études)
    - Avec study_id  : vide uniquement les slides de cette étude

    Usage :
      DELETE /agents/debug/clear-slide-cache
      DELETE /agents/debug/clear-slide-cache?study_id=18f460c9-...
    """
    import os
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise HTTPException(500, "Supabase non configuré")

    sb = create_client(url, key)
    try:
        if study_id:
            # Supprime toutes les entrées dont la clé contient l'study_id
            result = (
                sb.table("slide_html_cache")
                .delete()
                .like("key", f"%{study_id}%")
                .execute()
            )
            deleted = len(result.data) if result.data else 0
            msg = f"Cache vidé pour study_id={study_id} ({deleted} entrées)"
        else:
            # Supprime tout (cle >= vide matche toutes les lignes)
            result = (
                sb.table("slide_html_cache")
                .delete()
                .gte("key", "")
                .execute()
            )
            deleted = len(result.data) if result.data else 0
            msg = "Cache global vide ({} entrees)".format(deleted)

        logger.info("[debug/clear-slide-cache] %s", msg)
        return {"deleted": deleted, "message": msg}

    except Exception as exc:
        logger.error("[debug/clear-slide-cache] erreur : %s", exc)
        raise HTTPException(500, str(exc))


@router.post("/visual-qa/report", response_model=AgentResponse)
def submit_visual_qa_report(report: VisualQAReport) -> AgentResponse:
    """
    Soumettre un rapport de QA visuelle depuis l'agent Visual QA.
    """
    from app.repositories.studies_repo import studies_repo

    study = studies_repo.get(report.study_id)
    if not study:
        raise HTTPException(status_code=404, detail=f"Study '{report.study_id}' not found")

    errors = [i for i in report.issues if i.severity == "error"]
    warnings = [i for i in report.issues if i.severity == "warning"]

    logger.info(
        "[agent:visual-qa] study=%s slide=%s errors=%d warnings=%d status=%s",
        report.study_id, report.slide_id,
        len(errors), len(warnings), report.overall_status,
    )

    if report.overall_status == "fail" or len(errors) > 0:
        return _make_response(
            "accepted",
            f"QA enregistre - {len(errors)} erreur(s) bloquante(s), statut=fail",
            report.model_dump(),
        )

    return _make_response(
        "accepted",
        f"QA enregistre - {len(warnings)} avertissement(s), statut={report.overall_status}",
        report.model_dump(),
    )
