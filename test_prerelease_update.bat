@echo off
chcp 65001 >nul
setlocal

set "TEST_DIR=%~dp0dist\PoENavi-v2.4-updater-test"
set "TEST_CLIENT=%TEST_DIR%\PoENavi.exe"
set "POENAVI_USER_DATA_DIR=%~dp0.prerelease-test-user-data"

if not exist "%TEST_CLIENT%" (
    echo ERROR: v2.4.0 updater-enabled test client was not found.
    echo Build and place it in dist\PoENavi-v2.4-updater-test.
    pause
    exit /b 1
)
if not exist "%TEST_DIR%\PoENaviUpdater.exe" (
    echo ERROR: PoENaviUpdater.exe was not found in the v2.4.0 test client.
    echo The official v2.4.0 Release cannot be used for this test.
    pause
    exit /b 1
)

set "POENAVI_UPDATE_TEST_TAG=v2.5.0"
if exist "%POENAVI_USER_DATA_DIR%" rmdir /s /q "%POENAVI_USER_DATA_DIR%"
echo Starting PoENavi in pre-release update test mode for v2.5.0.
echo Test user data: %POENAVI_USER_DATA_DIR%
start "" "%TEST_CLIENT%"
