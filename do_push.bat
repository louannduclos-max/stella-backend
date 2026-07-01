@echo off
cd /d "D:\claude\stella\stella V2.1"
echo === git push origin main ===
git push origin main
if %ERRORLEVEL% EQU 0 (
    echo === SUCCES ===
) else (
    echo === ERREUR - code %ERRORLEVEL% ===
)
pause
