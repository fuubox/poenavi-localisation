@echo off
chcp 65001 >nul
set "POENAVI_USER_DATA_DIR=%~dp0.dev-user-data-act1"
set "POENAVI_ACT1_GUIDE_DEV=1"
echo ============================================
echo   PoENavi - Act 1 Guide Editor
echo ============================================
echo User data: %POENAVI_USER_DATA_DIR%
echo Guide editor: PoE1 Act 1 only
echo.
python main.py
echo.
pause
