@echo off
cd /d "%~dp0"
echo.
echo === SECURITE — Retrait cle service_role hardcodee ===
echo.
git log --oneline -3
echo.
echo === Stage studies_repo.py ===
git add "app/repositories/studies_repo.py"
git status --short -- "app/repositories/studies_repo.py"
echo.
echo === Commit ===
git commit -m "security: retirer SUPABASE_SERVICE_ROLE_KEY hardcodee — lecture strict os.environ"
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR commit
    pause
    exit /b 1
)
echo.
echo === Pull rebase ===
git checkout -- requirements.txt 2>nul
git pull --rebase origin main
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR pull rebase
    git rebase --abort
    pause
    exit /b 1
)
echo.
echo === Push ===
git push origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo === SUCCES - Clé retirée du code ===
    echo RAPPEL : poser la nouvelle cle sur Render avant de regenerer une etude
) else (
    echo ERREUR push
)
pause
