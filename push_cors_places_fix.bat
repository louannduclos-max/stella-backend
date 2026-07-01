@echo off
cd /d "D:\claude\stella\stella V2.1"
echo.
echo === Fix CORS + keywords Places + push ===

if exist ".git\index.lock" del /f /q ".git\index.lock"

git add app/core/config.py
git add app/services/external/google_places_api.py

git commit -m "fix: CORS ajouter stellav1front.pages.dev + regex pages.dev | keywords SAP valides"
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo === SUCCES ===
    git log --oneline -3
) else (
    echo ERREUR push
)
pause
