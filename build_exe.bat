@echo off
chcp 65001 > nul
title Build FTI Inventory Compare Single-File EXE

cd /d "%~dp0"
echo ========================================================
echo   Building FTI IT Asset Inventory Compare Standalone EXE
echo ========================================================
echo.

python build_exe.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build encountered an error.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Build finished successfully!
pause
