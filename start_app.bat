@echo off
chcp 65001 > nul
title FTI IT Asset Inventory Compare System

cd /d "%~dp0"

echo ========================================================
echo   FTI IT Asset Inventory Compare Automation System
echo   Clean Business Edition (Auto-Detect Free Port)
echo ========================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found in system PATH.
    echo Please install Python 3.10+ or run the Standalone EXE version.
    echo.
    pause
    exit /b 1
)

echo Starting Application...
python run.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application terminated with error code %ERRORLEVEL%.
    pause
)
