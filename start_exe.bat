@echo off
chcp 65001 > nul
title FTI IT Asset Compare Standalone Executable

cd /d "%~dp0"

echo ========================================================
echo   Starting FTI IT Asset Compare Standalone Executable
echo ========================================================
echo.

set "EXE_MAIN=%~dp0FTI_Inventory_Compare.exe"
set "EXE_DRIVE=E:\FTI_Inventory_Compare.exe"

if exist "%EXE_MAIN%" (
    echo Launching %EXE_MAIN%...
    start "" "%EXE_MAIN%"
    exit /b 0
)

if exist "%EXE_DRIVE%" (
    echo Launching %EXE_DRIVE%...
    start "" "%EXE_DRIVE%"
    exit /b 0
)

echo [Notice] Pre-built executable not found.
echo Building standalone executable now...
call "%~dp0build_exe.bat"

if exist "%EXE_MAIN%" (
    start "" "%EXE_MAIN%"
    exit /b 0
)

pause
