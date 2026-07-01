@echo off
cd /d "D:\claude\stella\stella V2.1"
echo.
echo === Push Sprint 2 (commit 112f43f deja fait) ===
git push origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo === SUCCES ===
    git log --oneline -3
) else (
    echo ERREUR push
)
pause
