@echo off
cd /d "%~dp0"
title JewAIXP client

set PY=
where python >nul 2>&1
if not errorlevel 1 set PY=python
if "%PY%"=="" if exist "C:\Python34\python.exe" set PY=C:\Python34\python.exe
if "%PY%"=="" if exist "C:\Python27\python.exe" set PY=C:\Python27\python.exe

if "%PY%"=="" (
    echo [FAIL] python not found. Run 1_install_python.bat first.
    pause
    exit /b 1
)

echo === JewAIXP ICQ-client ===
echo server from xp_client.json
echo.
"%PY%" xp_client.py

echo.
echo === client exited ===
pause