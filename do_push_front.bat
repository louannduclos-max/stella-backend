@echo off
cd /d "D:\claude\stella\stella V2.1\front"
echo === git push front origin main ===
git push origin main
if %ERRORLEVEL% EQU 0 (
    echo === SUCCES FRONT ===
) else (
    echo === ERREUR - code %ERRORLEVEL% ===
)
pause
