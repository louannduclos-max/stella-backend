"""
Test de non-régression — Golden Check.

Charge une étude de référence connue (fixture JSON) et vérifie des invariants
de base AVANT tout push. Ne remplace pas une revue visuelle, mais attrape les
régressions grossières automatiquement :
  - slide entièrement vide
  - SWOT sans bullets
  - nombre mal formaté (collé à son unité sans espace)
  - objet hors canvas
  - champs Data-Depth manquants (benchmark, concurrents, barème APA)

Usage :
  python tests/golden_check.py           # run check
  python tests/golden_check.py --save <study_id>  # créer la fixture de référence

Intégrer dans le workflow : lancer AVANT tout push qui touche au pipeline slides.
"""
import json
import re
import sys
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "golden_reference_study.json"

# ─────────────────────────────────────────────────────────────────────────────
# Invariants
# ─────────────────────────────────────────────────────────────────────────────

def _check_no_empty_slides(slides: list) -> list[str]:
    failures = []
    for slide in slides:
        objects = slide.get("objects", [])
        non_empty = [
            o for o in objects
            if o.get("text") or o.get("children") or o.get("items") or o.get("chart_data")
        ]
        if len(non_empty) == 0:
            failures.append(f"Slide {slide['slide_id']} : entièrement vide ({len(objects)} objets)")
    return failures


def _check_swot_bullets(slides: list) -> list[str]:
    failures = []
    for slide in slides:
        if slide.get("section_id") != "swot":
            continue
        for obj in slide.get("objects", []):
            if obj.get("data_object_type") not in ("swot_quadrant", "shape"):
                continue
            children = obj.get("children") or []
            bullets = [c for c in children if c.get("role") == "bullet"]
            # Attendre des bullets uniquement sur les shapes avec label SWOT
            if obj.get("id", "").startswith("kpi-card") and not bullets:
                label = next((c.get("text", "") for c in children if c.get("role") == "label"), "")
                if label in ("Forces", "Faiblesses", "Opportunités", "Menaces"):
                    failures.append(f"SWOT {obj.get('id')} ({label}) : aucun bullet")
    return failures


def _check_number_formatting(slides: list) -> list[str]:
    """Détecte les nombres collés à leur unité sans espace (ex: '45321hab' au lieu de '45 321 hab')."""
    failures = []
    pattern = re.compile(r"\d{4,}[a-zA-Zàéèêô]")
    for slide in slides:
        for obj in slide.get("objects", []):
            text = obj.get("text") or ""
            if pattern.search(text):
                failures.append(
                    f"{obj.get('id')} (slide {slide['slide_id']}) : nombre mal formaté → '{text[:50]}'"
                )
    return failures


def _check_canvas_bounds(slides: list) -> list[str]:
    """Vérifie qu'aucun objet ne dépasse le canvas (tolérance 40px)."""
    failures = []
    CANVAS_W, CANVAS_H, TOLERANCE = 1920, 1080, 40
    for slide in slides:
        for obj in slide.get("objects", []):
            right = obj.get("left", 0) + obj.get("width", 0)
            bottom = obj.get("top", 0) + obj.get("height", 0)
            if right > CANVAS_W + TOLERANCE:
                failures.append(f"{obj.get('id')} (slide {slide['slide_id']}) : déborde droite ({right}px)")
            if bottom > CANVAS_H + TOLERANCE:
                failures.append(f"{obj.get('id')} (slide {slide['slide_id']}) : déborde bas ({bottom}px)")
    return failures


def _check_data_depth(study) -> list[str]:
    """
    Vérifie que les champs Data-Depth Sprint sont présents et cohérents.
    Ces checks s'assurent que le pipeline d'enrichissement a bien tourné.
    """
    failures = []

    # 1 — Au moins une métrique avec benchmark national
    metrics_with_benchmark = [
        m for m in (study.metrics or [])
        if m.national_benchmark is not None
    ]
    if not metrics_with_benchmark:
        failures.append(
            "DATA_DEPTH: aucune métrique avec national_benchmark "
            "— vérifier benchmark_engine.enrich_metrics() dans run_study.py"
        )

    # 2 — Liste concurrentielle non vide
    # (peut être vide si Places n'a rien renvoyé — warning non bloquant)
    if not (study.competitors or []):
        failures.append(
            "DATA_DEPTH (warning): study.competitors vide "
            "— Google Places n'a peut-être rien renvoyé ou build_competitors_from_places() non appelé"
        )

    # 3 — Barème financement présent pour une étude FR
    country = (study.country or "FR").upper()
    if country == "FR" and study.funding_scale is None:
        failures.append(
            "DATA_DEPTH: funding_scale absent pour une étude FR "
            "— vérifier get_funding_scale() dans run_study.py Phase 3"
        )

    return failures


# ─────────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────────

def run_golden_check() -> bool:
    if not FIXTURE.exists():
        print("⚠️  Pas de fixture golden. Génère-en une avec :")
        print("   python tests/golden_check.py --save <study_id>")
        return True  # ne bloque pas si pas encore créée

    # Import local — on suppose qu'on tourne depuis la racine du projet
    try:
        from app.api.schemas.common import Study
        from app.services.slides_5_0_builder import build_slides_5_0_for_study
    except ImportError as e:
        print(f"❌ Import raté (lancer depuis la racine du projet) : {e}")
        return False

    study = Study.model_validate(json.loads(FIXTURE.read_text()))
    payload = build_slides_5_0_for_study(study)
    slides = payload.get("slides", [])

    failures: list[str] = []
    # Checks slides (rendu PPTX)
    failures += _check_no_empty_slides(slides)
    failures += _check_swot_bullets(slides)
    failures += _check_number_formatting(slides)
    failures += _check_canvas_bounds(slides)
    # Checks manifest Data-Depth (Sprint 7)
    failures += _check_data_depth(study)

    if failures:
        print(f"❌ GOLDEN CHECK ÉCHOUÉ — {len(failures)} problème(s) :")
        for f in failures:
            print(f"   - {f}")
        return False

    print(f"✅ Golden check OK — {len(slides)} slides, aucune régression détectée")
    return True


def save_golden_fixture(study_id: str) -> None:
    """
    À lancer une fois manuellement sur une étude jugée visuellement correcte,
    pour créer la fixture de référence.
    """
    try:
        from app.repositories.studies_repo import studies_repo
    except ImportError as e:
        print(f"❌ Import raté : {e}")
        return

    study = studies_repo.get(study_id)
    if study is None:
        print(f"❌ Étude {study_id} introuvable")
        return

    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(
        json.dumps(study.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"✅ Fixture sauvegardée : {FIXTURE}")
    print(f"   Étude : {study_id}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--save":
        save_golden_fixture(sys.argv[2])
    else:
        ok = run_golden_check()
        sys.exit(0 if ok else 1)
