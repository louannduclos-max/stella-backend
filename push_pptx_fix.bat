@echo off
cd /d "%~dp0"
echo.
echo === Push PPTX children fix (Sprint 5 Lot A) ===
git log --oneline -4
echo.
echo === Stage export_pptx.py ===
git add "app/services/export_pptx.py"
git status --short -- "app/services/export_pptx.py"
echo.
echo === Commit ===
git commit -m "fix: PPTX children render via shape text frame natif (plus robuste)"
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR commit
    pause
    exit /b 1
)
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
echo === Push ===
git push origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo === SUCCES - Render redeploie dans 2-3 min ===
    echo Ensuite regenerer une etude pour tester le PPTX
) else (
    echo ERREUR push
)
pause
