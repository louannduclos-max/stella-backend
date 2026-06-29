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
# 6. Debug — Google Places Probe
# ---------------------------------------------------------------------------

@router.get("/debug/places-probe")
def debug_places_probe(
    city: str = "Auray",
    lat: float = 47.6667,
    lng: float = -2.9833,
    radius: int = 15000,
) -> dict:
    """
    Endpoint de diagnostic temporaire — teste Google Places Nearby Search directement.
    Appeler : GET /agents/debug/places-probe?city=Auray
    Interpréter le statut :
    - REQUEST_DENIED → clé non autorisée sur Places API
    - OK count=0     → radius trop petit ou mots-clés inadaptés
    - OK count=N     → bug dans le collector, pas dans l'API
    """
    import os
    import httpx

    key = os.environ.get("GOOGLE_PLACES_API_KEY", "")
    if not key:
        return {"error": "GOOGLE_PLACES_API_KEY absent de l'env Render"}

    keywords = [
        "aide à domicile",
        "aide aux personnes âgées",
        "aide aux seniors",
        "services à domicile",
        "Interdomicilio",
        "Azaé",
        "O2 Care Services",
        "Vitalliance",
        "senior",
    ]
    results = {}
    for kw in keywords:
        try:
            r = httpx.get(
                "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                params={
                    "location": f"{lat},{lng}",
                    "radius": radius,
                    "keyword": kw,
                    "key": key,
                },
                timeout=10,
            )
            data = r.json()
            results[kw] = {
                "status": data.get("status"),
                "count": len(data.get("results", [])),
                "error_message": data.get("error_message"),
                "names": [p["name"] for p in data.get("results", [])[:3]],
            }
        except Exception as e:
            results[kw] = {"status": "EXCEPTION", "error": str(e)}

    total = sum(r.get("count", 0) for r in results.values() if isinstance(r.get("count"), int))
    return {
        "city": city,
        "coords": {"lat": lat, "lng": lng},
        "radius_m": radius,
        "key_present": bool(key),
        "key_prefix": key[:8] + "..." if key else "",
        "total_results": total,
        "by_keyword": results,
    }


@router.post("/visual-qa/report", response_model=AgentResponse)
def submit_visual_qa_report(report: VisualQAReport) -> AgentResponse:
    """
    Soumettre un rapport de QA visuelle depuis l'agent Visual QA.

    Le backend enregistre les issues et peut déclencher une re-génération
    ou un marquage de statut 'qa_failed' si des erreurs bloquantes sont détectées.
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
        # En Phase 2 : mettre à jour study.status = "qa_failed"
        return _make_response(
            "accepted",
            f"Rapport QA enregistré — {len(errors)} erreur(s) bloquante(s), statut=fail (re-génération à planifier)",
            report.model_dump(),
        )

    return _make_response(
        "accepted",
        f"Rapport QA enregistré — {len(warnings)} avertissement(s), statut={report.overall_status}",
        report.model_dump(),
    )
