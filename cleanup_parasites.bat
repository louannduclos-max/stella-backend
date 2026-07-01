@echo off
cd /d "D:\claude\stella\stella V2.1"
echo.
echo === Nettoyage fichiers parasites (HANDOFF, pptx test, scripts test) ===

del /f /q "HANDOFF_BLOC2.md" 2>nul
del /f /q "HANDOFF_NEXT_COWORK.md" 2>nul
del /f /q "HANDOFF_SESSION.md" 2>nul
del /f /q "HANDOFF_SESSION_20260629.md" 2>nul
del /f /q "HANDOFF_SPRINT2_BACKEND.md" 2>nul
del /f /q "HANDOFF_SPRINT3_20260629.md" 2>nul
del /f /q "HANDOFF_SPRINT3_BACKEND.md" 2>nul
del /f /q "generate_test_pptx.py" 2>nul
del /f /q "generate_test_pptx_direct.py" 2>nul
del /f /q "stella_auray_2025.pptx" 2>nul
del /f /q "stella_test_output.pptx" 2>nul

echo Fichiers parasites supprimes.
echo.
echo === Etat git apres nettoyage ===
git status --short
pause
