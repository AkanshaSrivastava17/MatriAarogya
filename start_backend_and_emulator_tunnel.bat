@echo off
title SanRaksha Backend & Emulator Tunnel
cd /d "%~dp0"

echo ========================================================
echo      SanRaksha Backend Server & Emulator Port Setup     
echo ========================================================
echo.

:: Try to configure adb reverse if an emulator/device is connected
where adb >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [1/2] Configuring adb reverse tcp:8000 tcp:8000...
    adb reverse tcp:8000 tcp:8000 2>nul
) else (
    if exist "%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" (
        echo [1/2] Configuring adb reverse tcp:8000 tcp:8000 using Android SDK path...
        "%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe" reverse tcp:8000 tcp:8000 2>nul
    ) else (
        echo [1/2] Notice: adb not found in PATH or standard SDK directory.
    )
)

echo [2/2] Starting FastAPI Backend on http://0.0.0.0:8000 ...
echo.
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

pause
