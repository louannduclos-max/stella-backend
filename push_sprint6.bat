@echo off
echo ============================================================
echo   PUSH SPRINT 6 — Stella Backend + Frontend
echo ============================================================

:: --- BACKEND ---
echo.
echo [1/4] Staging backend Sprint 6 files...
cd /d "%~dp0"
del /f /q .git\index.lock 2>nul

git add app/services/layout_engine_5_0.py
git add app/services/slide_data_builder_5_0.py
git add app/core/slot_contracts.py
git add app/services/gemini_analyst.py
git add app/agents/narrative_agent.py
git add app/services/collectors/competition.py
git add tests/golden_check.py

echo [2/4] Committing backend...
git commit -m "fix(sprint6): SWOT bullets + slides vides + formatage nombres + gemini-2.5-flash + grammaire verdict + density flag

Bug 1: layout_engine_5_0 — _swot_card() avec bullets (max 4), remplace _kpi_card sur slide SWOT
Bug 2: slide_data_builder_5_0 — branches dédiées market_scorecard (scores) et methodology_sources (sources)
Bug 2: slot_contracts — SECTION_EXPECTED_KPIS market_scorecard documenté (branche dédiée)
Bug 3: slide_data_builder_5_0 — _format_number() separateur milliers + espace avant unite
Bug 4: gemini_analyst — verdict narrative sans accord de genre arbitraire
Bug 5: competition — top_density saturation (>=100) flaggée fallback_used=True
Bug 6: gemini-2.0-flash -> gemini-2.5-flash dans gemini_analyst + narrative_agent"

echo [3/4] Pushing backend...
git push origin main

:: --- FRONTEND ---
echo [4/4] Committing + pushing frontend (wizard timeout)...
cd /d "%~dp0front"
del /f /q .git\index.lock 2>nul

git add src/lib/wizard-submit.server.ts

git commit -m "fix(sprint6): wizard-submit AbortSignal.timeout 15s -> 60s (cold start Render)"

git push origin main

echo.
echo ============================================================
echo   SPRINT 6 POUSSE. Render va redéployer automatiquement.
echo   Attendre ~2 min puis générer une étude de validation.
echo ============================================================
pause
