@echo off
cd /d "D:\claude\stella\stella V2.1\front"
if exist ".git\index.lock" del /f /q ".git\index.lock"
if exist ".git\HEAD.lock" del /f /q ".git\HEAD.lock"
echo === Fix TS + Force CF Pages redeploy ===
git add src/lib/generate-study.functions.ts
git add src/lib/supabase-browser.ts
git add src/lib/wizard.functions.ts
git commit -m "fix: restaurer 3 fichiers tronques - debloquer build CF Pages"
git push origin main
echo.
git log --oneline -3
pause
