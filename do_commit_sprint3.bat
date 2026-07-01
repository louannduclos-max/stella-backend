@echo off
cd /d "D:\claude\stella\stella V2.1\front"
del /f ".git\index.lock" 2>nul
del /f ".git\HEAD.lock" 2>nul
del /f ".git\MERGE_HEAD.lock" 2>nul
del /f ".git\CHERRY_PICK_HEAD.lock" 2>nul
git add public/stella/generation.jsx
git commit -m "sprint3: navigation slides + PPTX button + F3 redirect + F2.3 viewer link"
echo.
echo === RESULTAT COMMIT ===
echo Exit code: %ERRORLEVEL%
pause
