@echo off
cd /d "D:\claude\stella\stella V2.1"
echo.
echo === Push Sprint 2 + Sprint 3 ===

rem --- Supprimer le verrou index si present ---
if exist ".git\index.lock" (
    echo Suppression de index.lock...
    del /f /q ".git\index.lock"
)

rem --- Verifier l'etat ---
git status --short

rem --- Ajouter uniquement les fichiers Sprint 3 ---
echo.
echo Staging fichiers Sprint 3...

git add app/agents/narrative_agent.py
git add app/agents/slide_builder_agent.py
git add app/api/routes/agents.py
git add app/services/consolidation_engine.py
git add app/services/slides_5_0_builder.py
git add cleanup_working_tree.bat

rem --- Committer Sprint 3 ---
echo.
echo Commit Sprint 3...
git commit -m "Sprint 3 backend : geo_resolver pipeline, Places probe, USE_AGENT flag, NarrativeAgent"

rem --- Pousser Sprint 2 + Sprint 3 ---
echo.
echo Push vers GitHub (Sprint 2 + Sprint 3)...
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo === SUCCES ===
    git log --oneline -5
) else (
    echo ERREUR push — verifier connexion et credentials
)
pause
