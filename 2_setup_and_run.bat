@echo off
cd /d "%~dp0"
title JewAIXP setup

set PY=
where python >nul 2>&1
if not errorlevel 1 set PY=python
if "%PY%"=="" if exist "C:\Python34\python.exe" set PY=C:\Python34\python.exe
if "%PY%"=="" if exist "C:\Python27\python.exe" set PY=C:\Python27\python.exe

if "%PY%"=="" (
    echo [FAIL] python not found.
    echo Run 1_install_python.bat first (as Administrator).
    pause
    exit /b 1
)

echo Running setup wizard...
"%PY%" setup_client.py

echo.
echo Starting client...
"%PY%" xp_client.py
pause