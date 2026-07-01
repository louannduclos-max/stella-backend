@echo off
cd /d "D:\claude\stella\stella V2.1"
if exist ".git\index.lock" del /f /q ".git\index.lock"
if exist ".git\HEAD.lock" del /f /q ".git\HEAD.lock"
git add app/repositories/studies_repo.py
git commit -m "diag: print SUPABASE_URL project_id"
git push origin main
echo.
git log --oneline -3
pause
