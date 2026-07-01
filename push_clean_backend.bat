@echo off
cd /d "%~dp0"
echo.
echo === Push clean backend Sprint4C ===
echo.
git log --oneline -4
echo.

echo === Discard CRLF noise (pas de vrai contenu change) ===
git checkout -- app/repositories/studies_repo.py
git checkout -- requirements.txt
echo.

echo === Pull rebase ===
git pull --rebase origin main
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR pull rebase
    git rebase --abort
    pause
    exit /b 1
)
echo.

echo === Push Sprint4C ===
git push origin main
echo.
if %ERRORLEVEL% EQU 0 (
    echo === SUCCES - Render va redeploy dans 2-3 min ===
) else (
    echo ERREUR push
)
echo.
pause
