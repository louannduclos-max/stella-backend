@echo off
cd /d "D:\claude\stella\stella V2.1"
echo.
echo === NarrativeAgent : Vertex AI → GEMINI_API_KEY (gratuit) ===

if exist ".git\index.lock" del /f /q ".git\index.lock"

git add app/agents/narrative_agent.py
git commit -m "fix(narrative_agent): remplacer Vertex AI par GEMINI_API_KEY (gratuit, deja configure)"
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo === SUCCES ===
    git log --oneline -3
) else (
    echo ERREUR push
)
pause
