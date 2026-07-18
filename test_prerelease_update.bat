@echo off
chcp 65001 >nul
setlocal

if not exist "%~dp0dist\PoENavi\PoENavi.exe" (
    echo ERROR: dist\PoENavi\PoENavi.exe がありません。
    echo 先にテスト用v2.4.0クライアントをビルドしてください。
    pause
    exit /b 1
)

set "POENAVI_UPDATE_TEST_TAG=v2.5.0"
echo Pre-release v2.5.0 を参照するテストモードでPoENaviを起動します。
start "" "%~dp0dist\PoENavi\PoENavi.exe"
