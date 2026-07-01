@echo off
cd /d "D:\claude\stella\stella V2.1"
echo.
echo === Fix keywords Places API + push ===

if exist ".git\index.lock" del /f /q ".git\index.lock"

git add app/services/external/google_places_api.py
git commit -m "fix: SAP_KEYWORDS_FR - remplacer keywords REQUEST_DENIED par keywords valides (probe Auray)"
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo === SUCCES ===
    git log --oneline -3
) else (
    echo ERREUR push
)
pause
