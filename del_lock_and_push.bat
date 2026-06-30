@echo off
echo Suppression du lock git...
cd /d "D:\claude\stella\stella V2.1"
del /f /q ".git\index.lock" 2>nul
echo Lock supprime (ou inexistant)

echo.
echo Staging Sprint 6 backend...
git add app/services/layout_engine_5_0.py
git add app/services/slide_data_builder_5_0.py
git add app/core/slot_contracts.py
git add app/services/gemini_analyst.py
git add app/agents/narrative_agent.py
git add app/services/collectors/competition.py
git add tests/golden_check.py
git add push_sprint6.bat
git add del_lock_and_push.bat

echo Commit backend...
git commit -m "fix(sprint6): SWOT bullets + slides vides + formatage + gemini-2.5-flash + verdict + density

Bug 1 - layout_engine_5_0: _swot_card() lit les bullets (max 4), remplace _kpi_card sur SWOT
Bug 2 - slide_data_builder_5_0: branches market_scorecard (study.scores) + methodology_sources (study.sources)
Bug 2 - slot_contracts: SECTION_EXPECTED_KPIS market_scorecard documente
Bug 3 - slide_data_builder_5_0: _format_number() separateur milliers + espace avant unite
Bug 4 - gemini_analyst: verdict_narrative sans accord genre (plus de 'une X elevee')
Bug 5 - competition: top_density sature (>=100) flague fallback_used=True
Bug 6 - gemini-2.0-flash -> gemini-2.5-flash (gemini_analyst + narrative_agent)"

git push origin main

echo.
echo Staging frontend...
cd /d "D:\claude\stella\stella V2.1\front"
del /f /q ".git\index.lock" 2>nul

git add src/lib/wizard-submit.server.ts
git commit -m "fix(sprint6): wizard-submit AbortSignal.timeout 15s -> 60s (cold start Render)"
git push origin main

echo.
echo === SPRINT 6 POUSSE ===
pause
