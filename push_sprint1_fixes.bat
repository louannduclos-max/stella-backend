@echo off
cd /d "D:\claude\stella\stella V2.1"
echo.
echo === Sprint 1 fixes — commit + push backend ===
del /f /q ".git\index.lock" 2>nul

git add app/services/slide_data_builder_5_0.py
git add app/services/layout_engine_5_0.py
git add app/services/export_pptx.py
git add app/services/collectors/competition.py
git add app/services/external/google_places_api.py

echo.
echo Fichiers a committer :
git diff --cached --name-only

git commit -m "fix(sprint1): SWOT reel + kpi_list + verdict lisible + erreurs masquees + rayon concurrence"
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR commit
    pause
    exit /b 1
)

git pull --rebase origin main
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR pull — abort rebase
    git rebase --abort 2>nul
    pause
    exit /b 1
)

git push origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo === SUCCES ===
    git log --oneline -5
) else (
    echo ERREUR push
)

pause
