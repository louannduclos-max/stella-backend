@echo off
cd /d "D:\claude\stella\stella V2.1"
echo.
echo === Sprint 2 Backend — commit + push ===
del /f /q ".git\index.lock" 2>nul

git add app/templates/slides/template_kpi_analysis.json
git add app/templates/slides/template_swot.json
git add app/templates/slides/template_cover.json
git add app/templates/slides/template_verdict.json
git add app/templates/slides/template_competition.json
git add app/agents/__init__.py
git add app/agents/slide_builder_agent.py
git add app/services/collectors/geo_resolver.py
git add app/services/master_json_builder.py
git add app/services/slides_5_0_builder.py
git add app/services/slide_data_builder_5_0.py
git add app/api/routes/agents.py
git add requirements.txt

echo.
echo Fichiers a committer :
git diff --cached --name-only

git commit -m "feat(sprint2): agent slide builder + templates JSON + geo resolver EPCI + SWOT bullets deterministe"
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR commit
    pause
    exit /b 1
)

git pull --rebase origin main
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR pull
    git rebase --abort 2>nul
    pause
    exit /b 1
)

git push origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo === SUCCES ===
    git log --oneline -4
) else (
    echo ERREUR push
)

pause
