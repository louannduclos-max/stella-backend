@echo off
cd /d "D:\claude\stella\stella V2.1"
echo === Nettoyage working tree ===

del /f /q generate_test_pptx.py 2>nul
del /f /q generate_test_pptx_direct.py 2>nul
del /f /q stella_auray_2025.pptx 2>nul
del /f /q stella_test_output.pptx 2>nul

rem Garder do_push.bat et just_push_sprint2.bat
del /f /q push_clean_backend.bat 2>nul
del /f /q push_pptx_fix.bat 2>nul
del /f /q push_security_fix.bat 2>nul
del /f /q push_sprint1_fixes.bat 2>nul
del /f /q push_sprint2_backend.bat 2>nul

echo.
echo Fichiers restants :
git status --short
pause
