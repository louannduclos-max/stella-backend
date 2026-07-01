@echo off
cd /d "D:\claude\stella\stella V2.1"
echo.
echo === Push backend commits vers GitHub ===
git log --oneline -4
echo.
git stash push -m "wip-temp-push" 2>nul
git pull --rebase origin main
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR pull rebase
    git rebase --abort 2>nul
    pause
    exit /b 1
)
git push origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo === SUCCES — backend pousse ===
) else (
    echo ERREUR push
)
pause
