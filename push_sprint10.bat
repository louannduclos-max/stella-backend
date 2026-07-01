@echo off
REM ============================================================
REM  PUSH SPRINT 10 — Chantiers A-E (prereqs HTML deck-grade)
REM ============================================================
REM  Fichiers modifies :
REM    app/services/slide_precompute.py     (NOUVEAU  — Chantier A)
REM    app/services/master_json_builder.py  (modifie  — branche precompute)
REM    app/services/slide_cache.py          (modifie  — Chantier C : SKILL_VERSION auto)
REM    app/services/slides_5_0_builder.py   (modifie  — Chantier D : _section_has_data)
REM    app/agents/html_slide_agent.py       (modifie  — Chantier E : budget tokens)
REM    app/agents/qa_html_agent.py          (modifie  — Chantier E : check HTML tronque)
REM    app/skills/interdomicilio/base_slide.html (modifie — Chantier B : CSS inline)
REM
REM  Commits inclus depuis Sprint 9 :
REM    - fix(places-new): pagination body rebuild + source_id traceability

cd /d "D:\claude\stella\stella V2.1"

REM Nettoyer le lock si reste du push precedent
if exist .git\index.lock (
    echo Suppression index.lock residuel...
    del .git\index.lock
)

git add -A

git commit -m "feat(sprint10): chantiers A-E — prereqs HTML deck-grade sans faille

CHANTIER A — slide_precompute.py (NOUVEAU)
  Pre-calcule toutes les valeurs derivees AVANT l'agent :
  benchmark_rows (gap_display pre-calcule, direction up/down/neutral)
  demographics_pie (complement 100-seniors pre-calcule)
  scores_radar (labels + valeurs arrondies)
  competition_avg_rating (moyenne pre-calculee)
  -> L'agent LLM recopie, il ne calcule JAMAIS (corrige faille majeure v1)
  Branche dans master_json_builder.build() en derniere etape.

CHANTIER B — CSS local inline dans base_slide.html
  Remplace CDN Tailwind (dev-only, casse export LibreOffice) par CSS
  utilitaires compact (~15kB) inline : flex, grid, gap, spacing,
  typography, colors (gray/blue/green/red/yellow/orange), borders,
  width/height, display, position, shadows, table utilities.
  Google Fonts + FontAwesome CDN conserves (web viewer OK).

CHANTIER C — SKILL_VERSION automatique (hash fichiers skill)
  slide_cache.py : SKILL_VERSION = hash SHA256 de tous les .html/.md/.json/.css
  du dossier app/skills/interdomicilio/. Calcule au demarrage du process.
  -> Plus de bump manuel oublie. Modifier un .md -> cache invalide automatiquement.

CHANTIER D — _section_has_data() dans slides_5_0_builder.py
  Verifie que la section a assez de donnees AVANT d'appeler Gemini.
  funding_feasibility  : funding_scale non None
  benchmark_comparison : benchmark_rows >= 3 lignes
  demographics         : demographics_pie non None
  competition_mapping  : competitors_top >= 1 acteur
  -> False : pas d'appel Gemini, slide PPTX deterministe servie (invariant OK)

CHANTIER E — Budget tokens + donnees bornees + check tronque
  html_slide_agent.py : SECTION_DATA_KEYS (donnees bornees par section)
  SECTION_MAX_TOKENS (benchmark/competition : 4096, autres : 3000-3500)
  _filter_section_data() : l'agent ne voit que les cles pertinentes pour sa section
  qa_html_agent.py : _check_html_structure() detecte HTML tronque
  (div/table ouverts != fermes -> html_tronque: -> fallback PPTX immediat)"

if errorlevel 1 (
    echo ERREUR : commit echoue.
    exit /b 1
)

git push

if errorlevel 1 (
    echo ERREUR : push echoue.
    exit /b 1
)

echo.
echo ============================================================
echo  Push Sprint 10 OK
echo ============================================================
echo.
echo ACTIONS MANUELLES REQUISES :
echo.
echo 1. RENDER : Manual Deploy
echo    https://dashboard.render.com/web/srv-xxx/deploys
echo.
echo 2. VERIFIER manifest enrichi :
echo    GET https://stella-backend-mtap.onrender.com/agents/debug/html-slide?study_id=18f460c9-245b-4443-aa65-23eb2032089c
echo    -> Verifier que la reponse contient benchmark_rows, demographics_pie, scores_radar
echo.
echo 3. SUPABASE — Creer la table si pas encore fait :
echo    CREATE TABLE IF NOT EXISTS slide_html_cache (
echo      key TEXT PRIMARY KEY,
echo      html TEXT NOT NULL,
echo      created_at TIMESTAMPTZ DEFAULT now()
echo    );
echo.
echo 4. PROBE PLACES (si pas encore fait) :
echo    GET https://stella-backend-mtap.onrender.com/agents/debug/places-probe?query=aide+a+domicile+Bordeaux
echo    -> NEW_API_OK : ajouter GOOGLE_PLACES_API_NEW=true sur Render + redeploy
echo.
echo 5. PROCHAINE ETAPE :
echo    Sections une par une, preuve visuelle a chaque fois :
echo    executive_summary -> benchmark_comparison -> funding_feasibility -> ...
echo    NE PAS activer USE_HTML_SLIDE_AGENT=true avant 10 sections validees.
echo.
