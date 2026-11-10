@echo off
title ZyroX Bot Runner
cd /d "%~dp0bot"

echo ========================================================
echo               Starting ZyroX Discord Bot
echo ========================================================
echo.

:: Clean up any lingering CodeX instances on port 8000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)

python CodeX.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Bot stopped with an error (exit code: %ERRORLEVEL%).
    pause
)
