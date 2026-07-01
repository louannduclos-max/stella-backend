@echo off
cd /d "D:\claude\stella\stella V2.1"
if exist ".git\index.lock" del /f /q ".git\index.lock"
if exist ".git\HEAD.lock" del /f /q ".git\HEAD.lock"
echo === Push backend fixes ===
git add app/agents/slide_builder_agent.py
git add app/agents/narrative_agent.py
git add app/services/gemini_analyst.py
git add app/services/progress_notifier.py
git add app/repositories/studies_repo.py
git commit -m "fix: date encoder + gemini-2.0-flash + print diagnostics notify_front"
git push origin main
echo.
git log --oneline -3
pause
