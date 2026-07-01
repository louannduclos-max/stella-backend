@echo off
cd /d "D:\claude\stella\stella V2.1"
if exist ".git\index.lock" del /f /q ".git\index.lock"
if exist ".git\HEAD.lock" del /f /q ".git\HEAD.lock"
echo === Push diagnostic Supabase project_id ===
git add app/repositories/studies_repo.py
git commit -m "diag: log Supabase project_id au demarrage"
git push origin main
echo.
git log --oneline -3
pause
