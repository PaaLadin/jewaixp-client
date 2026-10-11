@echo off
cd /d "%~dp0"
set LOG=%~dp0install_log.txt

echo JewAIXP client - Python installer >> "%LOG%"
echo time: %DATE% %TIME% >> "%LOG%"
echo folder: %CD% >> "%LOG%"
echo. >> "%LOG%"

echo === JewAIXP client ===
echo Python 3.4.4 installer wrapper
echo.

if exist "C:\Python34\python.exe" (
    echo [ OK ] Python already installed at C:\Python34
    echo [ OK ] already installed >> "%LOG%"
    "C:\Python34\python.exe" --version
    goto :addpath
)

if not exist "python-3.4.4.msi" (
    echo [FAIL] python-3.4.4.msi not found in this folder.
    echo Download it from https://www.python.org/ftp/python/3.4.4/python-3.4.4.msi
    echo [FAIL] msi missing >> "%LOG%"
    echo.
    pause
    exit /b 1
)

echo Installing Python 3.4.4 to C:\Python34 ...
msiexec /i "python-3.4.4.msi" /qn TARGETDIR=C:\Python34 ALLUSERS=1 /norestart
if not exist "C:\Python34\python.exe" (
    echo [FAIL] install failed. Run as Administrator.
    echo [FAIL] install failed >> "%LOG%"
    pause
    exit /b 1
)
echo [ OK ] installed
echo [ OK ] installed >> "%LOG%"

:addpath
reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2>nul | findstr /i "C:\Python34" >nul
if not errorlevel 1 (
    echo [ OK ] already in PATH
    goto :done
)
for /f "tokens=2*" %%A in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path ^| findstr /i "Path"') do set OLDPATH=%%B
set NEWPATH=%OLDPATH%;C:\Python34;C:\Python34\Scripts
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path /t REG_EXPAND_SZ /d "%NEWPATH%" /f
echo [ OK ] PATH updated
echo [ OK ] PATH updated >> "%LOG%"

:done
echo.
echo === done ===
echo Next steps:
echo   1. rename xp_client.example.json to xp_client.json
echo   2. edit server URL inside
echo   3. double-click run_client.bat
echo.
pause