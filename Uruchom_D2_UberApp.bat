@echo off
setlocal enabledelayedexpansion
title D2 UberApp - Launcher
cd /d "%~dp0"

echo ===================================================
echo           D2 UberApp - Diablo II Resurrected
echo               AI Companion & Stash Vault
echo ===================================================
echo.

:: 1. Check if local runtime exists
if exist "runtime\python.exe" (
    echo [OK] Wykryto przenosny runtime Python w folderze runtime\
    set "PYTHON_EXE=runtime\python.exe"
    goto :RUN_APP
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
echo [INFO] Nie wykryto srodowiska Python na Twoim komputerze.
echo Pobieranie lekkiego, bezpiecznego pakietu przenosnego Python (python.org)...
echo To jednorazowa operacja (ok. 20 MB). Za chwile aplikacja wystartuje!
echo.

if not exist "runtime" mkdir runtime

powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Write-Host 'Pobieranie runtime Python 3.11...'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile 'runtime\python-embed.zip'; Write-Host 'Rozpakowywanie...'; Expand-Archive -Path 'runtime\python-embed.zip' -DestinationPath 'runtime' -Force; Remove-Item 'runtime\python-embed.zip'; Write-Host 'Pobieranie get-pip.py...'; Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'runtime\get-pip.py';}"

if not exist "runtime\python.exe" (
    echo [BLAD] Nie udalo sie automatycznie pobrac pakietu runtime.
    echo Zainstaluj Pythona ze strony: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Fix python._pth to allow site-packages
powershell -Command "(Get-Content 'runtime\python311._pth') -replace '#import site', 'import site' | Set-Content 'runtime\python311._pth'"

echo Konfigurowanie bibliotek wewnatrz runtime...
runtime\python.exe runtime\get-pip.py --no-warn-script-location >nul 2>&1
runtime\python.exe -m pip install --no-warn-script-location -r requirements.txt

set "PYTHON_EXE=runtime\python.exe"
goto :RUN_APP

:CHECK_DEPS
%PYTHON_EXE% -c "import flask, PIL, google.genai" >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalowanie wymaganych bibliotek...
    %PYTHON_EXE% -m pip install -r requirements.txt
)

:RUN_APP
echo.
echo [START] Zwalnianie portu 5005...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5005" ^| findstr "LISTENING"') do (
    if not "%%a"=="0" taskkill /f /pid %%a >nul 2>nul
)

echo [START] Uruchamianie D2 UberApp...
%PYTHON_EXE% app.py

if errorlevel 1 (
    echo.
    echo [BLAD] Aplikacja zostala zatrzymana z bledem.
    pause
)
