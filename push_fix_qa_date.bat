@echo off
cd /d "%~dp0"
del /f /q .git\index.lock 2>nul

git add app/agents/qa_html_agent.py

git commit -m "fix(qa_html_agent): json.dumps default=str pour date non serialisable"

git push origin main
echo.
echo Push termine. Aller sur Render - Manual Deploy.
pause
