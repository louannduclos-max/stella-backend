@echo off
cd /d "%~dp0"
del /f /q .git\index.lock 2>nul

git add ^
  app/services/gemini_analyst.py ^
  app/agents/narrative_agent.py ^
  app/agents/slide_builder_agent.py ^
  app/agents/html_slide_agent.py ^
  app/agents/qa_html_agent.py ^
  app/api/routes/agents.py ^
  app/skills/interdomicilio/skill.json ^
  app/skills/interdomicilio/base_slide.html ^
  app/skills/interdomicilio/sections/competition.md ^
  tests/golden_check.py

git commit -m "feat(sprint8): fix Gemini + HTML slide agent (Chemin B test decisif)

Etape 1 - Fix Gemini (bloquant)
- gemini_analyst.py : GEMINI_MODEL env var, maxOutputTokens 1024->4096,
  logging HTTP status + body 500 car., _safe_parse_json defensif
  (retire fences markdown, tente jusqu au dernier } valide)
- narrative_agent.py : meme corrections + fix lstrip buggy (etait strip
  de caracteres, pas de chaine), maxOutputTokens 2000->4096
- slide_builder_agent.py : VERTEX_MODEL via env var (coherence)

Etape 3 - Golden check etendu
- tests/golden_check.py : _check_data_depth() verifie national_benchmark
  present, competitors non vides, funding_scale present pour etude FR

Etape 4 - Chemin B : slide concurrence en HTML (test decisif)
- app/skills/interdomicilio/skill.json : charte marque (couleurs, polices, CDN)
- app/skills/interdomicilio/base_slide.html : squelette header/footer/CSS
  (kpi-row, comp-table, strategic-box, etc.)
- app/skills/interdomicilio/sections/competition.md : instructions layout
  tableau concurrentiel (KPI cards + table + strategic box)
- app/agents/html_slide_agent.py : HTMLSlideAgent.generate_main_content()
  + assemble_slide() temperature=0.4, maxOutputTokens=4096
- app/agents/qa_html_agent.py : validate_html() - extrait nombres du HTML,
  verifie traceabilite dans manifest (whitelist CSS/annees/sections)
- app/api/routes/agents.py : GET /agents/debug/html-slide?study_id=...
  retourne HTML brut si QA OK, JSON avec nombres non traces sinon

Env var a ajouter sur Render : GEMINI_MODEL=gemini-2.5-flash
USE_HTML_SLIDE_AGENT reste absent - test isole via endpoint debug uniquement"

git push origin main
echo.
echo Push termine.
echo.
echo === ACTIONS MANUELLES ===
echo 1. Render dashboard - Manual Deploy - Deploy latest commit
echo 2. Ajouter env var : GEMINI_MODEL=gemini-2.5-flash
echo 3. Tester : GET https://stella-backend-mtap.onrender.com/agents/debug/html-slide?study_id=18f460c9-245b-4443-aa65-23eb2032089c
echo 4. Ouvrir le HTML dans le navigateur - capturer ecran
echo 5. Coller log Render + capture dans handoff Sprint 8
pause
