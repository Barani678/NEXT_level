@echo off
title ZyroX Dashboard Runner
cd /d "%~dp0dashboard"

echo ========================================================
echo               Starting ZyroX Next.js Dashboard
echo ========================================================
echo.

where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Node.js was not detected on PATH.
    echo [!] To run the frontend web dashboard, install Node.js from:
    echo     https://nodejs.org (LTS version)
    echo.
    pause
    exit /b 1
)

if not exist node_modules (
    echo [*] Installing dashboard dependencies...
    npm install
)

echo [*] Launching dashboard at http://localhost:3000 ...
npm run dev
pause

