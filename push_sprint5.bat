@echo off
cd /d "D:\claude\stella\stella V2.1"
if exist ".git\index.lock" del /f /q ".git\index.lock"
if exist ".git\HEAD.lock" del /f /q ".git\HEAD.lock"
echo === Sprint 5 — Consolidation architecture + qualite deck-grade ===
echo.

git add app/schemas/__init__.py
git add app/schemas/slide_objects.py
git add app/agents/qa_agent.py
git add app/services/slides_5_0_builder.py
git add app/services/layout_engine_5_0.py
git add app/services/export_pptx.py
git add app/services/slide_data_builder_5_0.py
git add tests/__init__.py
git add tests/golden_check.py
git add tests/fixtures/.gitkeep

git commit -m "feat: Sprint 5 - consolidation archi + graphiques natifs PPTX

Chantier 1 : slides_5_0_builder.py - chemin unique, slide_builder_agent retire
Chantier 2 : app/schemas/slide_objects.py - schema Pydantic unique, validate_slide_objects()
Chantier 3 : app/agents/qa_agent.py - QA deterministique slot par slot
Chantier 4 : layout_engine_5_0 - slot narratif analysis-narrative (fill_with_narrative)
Chantier 5 : layout_engine_5_0 - suppression slide-separator (marqueur visuel IA)
Chantier 6 : export_pptx.py - graphiques natifs pie + bar + chart_native dispatcher
             slide_data_builder_5_0 - demographics_chart_data + swot_chart_data
Chantier 7 : tests/golden_check.py - test non-regression + save_golden_fixture()

SLIDE_BUILDER_USE_AGENT=false sur Render (rollback Chantier 0)
Ne pas reactiver true avant que golden check passe."

git push origin main
echo.
git log --oneline -5
pause
