@echo off
cd /d "D:\claude\stella\stella V2.1"
echo.
echo === Trigger CF Pages redeploy (commit vide) ===

if exist ".git\index.lock" del /f /q ".git\index.lock"

git commit --allow-empty -m "chore: trigger CF Pages redeploy (nouvelles cles Supabase)"
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo === SUCCES — CF Pages va rebuilder dans ~2 min ===
    git log --oneline -3
) else (
    echo ERREUR push
)
pause
