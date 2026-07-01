@echo off
cd /d "D:\claude\stella\stella V2.1"
echo.
echo === Fix requirements.txt + push ===

if exist ".git\index.lock" del /f /q ".git\index.lock"

git add requirements.txt
git commit -m "fix: retirer google-auth-httpx (n'existe pas sur PyPI)"
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo === SUCCES — push OK ===
    git log --oneline -3
) else (
    echo ERREUR push
)
pause
