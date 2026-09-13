@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
title D2 UberApp - Diablo II Resurrected AI Companion
cd /d "%~dp0"

echo ===================================================================
echo        ⚔️  D2 UberApp - Diablo II Resurrected AI Companion  ⚔️
echo          AI Vault, Roll Evaluation & Online Trading Hub
echo ===================================================================
echo.

:: 1. Check if local portable runtime exists
if exist "runtime\python.exe" (
    echo [OK] Portable Python runtime detected in runtime\
    set "PYTHON_EXE=runtime\python.exe"
    goto :CHECK_DEPS
)

:: 2. Check system python
where python >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_EXE=python"
    goto :CHECK_DEPS
)

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_EXE=py -3"
    goto :CHECK_DEPS
)

:: 3. Python is not installed - offer automatic portable setup
echo [EN] Python environment not detected on this system.
echo [PL] Nie wykryto srodowiska Python na Twoim komputerze.
echo.
echo [INFO] Downloading lightweight portable Python runtime (~20 MB)...
echo [INFO] Pobieranie lekkiego, bezpiecznego pakietu przenosnego Python...
echo.

if not exist "runtime" mkdir runtime

powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Write-Host 'Downloading Python 3.11 runtime...'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile 'runtime\python-embed.zip'; Write-Host 'Extracting...'; Expand-Archive -Path 'runtime\python-embed.zip' -DestinationPath 'runtime' -Force; Remove-Item 'runtime\python-embed.zip'; Write-Host 'Downloading get-pip.py...'; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'runtime\get-pip.py';}"

if not exist "runtime\python.exe" (
    echo [ERROR] Automatic portable runtime download failed.
    echo [BLAD] Nie udalo sie automatycznie pobrac pakietu runtime.
    echo Please install Python manually from: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Fix python._pth to allow site-packages
powershell -Command "(Get-Content 'runtime\python311._pth') -replace '#import site', 'import site' | Set-Content 'runtime\python311._pth'"

echo [INFO] Installing required libraries into portable runtime...
runtime\python.exe runtime\get-pip.py --no-warn-script-location >nul 2>&1
runtime\python.exe -m pip install --no-warn-script-location -r requirements.txt

set "PYTHON_EXE=runtime\python.exe"
goto :RUN_APP

:CHECK_DEPS
%PYTHON_EXE% -c "import flask, PIL, google.genai" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing missing dependencies / Instalowanie bibliotek...
    %PYTHON_EXE% -m pip install -r requirements.txt
)

:RUN_APP
echo.
echo [INFO] Freeing port 5005 if in use...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5005" ^| findstr "LISTENING"') do (
    if not "%%a"=="0" taskkill /f /pid %%a >nul 2>nul
)

echo.
echo ===================================================================
echo   [STATUS] Server running at:  http://127.0.0.1:5005
echo   [HOTKEY] In D2R: Hover cursor over item and press F10
echo   [POMOC]  W grze: Najedz kursorem na przedmiot i wcisnij F10
echo   [AUDIO]  Chime confirms capture, Gemini AI analyzes in ~1.2s
echo   [MARKET] 1-Click trade export: https://d2uberappmarket.tw5.org
echo ===================================================================
echo   [NOTICE] Keep this console window open while playing.
echo ===================================================================
echo.

%PYTHON_EXE% app.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application stopped with an error.
    echo [BLAD] Aplikacja zostala zatrzymana z bledem.
    pause
)
