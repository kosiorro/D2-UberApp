@echo off
setlocal
chcp 65001 >nul
title D2 UberApp - Diablo II Resurrected AI Companion
cd /d "%~dp0"

cls
echo.
echo ===================================================================
echo          D2 UberApp - Diablo II Resurrected AI Companion
echo          AI Vault, Roll Evaluation ^& Online Trading Hub
echo ===================================================================
echo.

REM ============================================================
REM 1. Check portable Python runtime
REM ============================================================

if exist "%~dp0runtime\python.exe" (
    echo [OK] Portable Python runtime detected.
    set "PYTHON_EXE=%~dp0runtime\python.exe"
    goto CHECK_DEPS
)

REM ============================================================
REM 2. Check system Python
REM ============================================================

where python >nul 2>&1
if not errorlevel 1 (
    echo [OK] System Python detected.
    set "PYTHON_EXE=python"
    goto CHECK_DEPS
)

where py >nul 2>&1
if not errorlevel 1 (
    echo [OK] Python Launcher detected.
    set "PYTHON_EXE=py -3"
    goto CHECK_DEPS
)

REM ============================================================
REM 3. Python not found - install portable runtime
REM ============================================================

echo.
echo [EN] Python environment was not detected on this computer.
echo [PL] Nie wykryto środowiska Python na tym komputerze.
echo.
echo [INFO] Downloading portable Python runtime...
echo [INFO] Pobieranie przenośnego środowiska Python...
echo.

if not exist "%~dp0runtime" mkdir "%~dp0runtime"

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ErrorActionPreference='Stop';" ^
    "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12;" ^
    "Write-Host '[1/3] Downloading Python 3.11.9...';" ^
    "Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile '%~dp0runtime\python-embed.zip';" ^
    "Write-Host '[2/3] Extracting Python...';" ^
    "Expand-Archive -Path '%~dp0runtime\python-embed.zip' -DestinationPath '%~dp0runtime' -Force;" ^
    "Remove-Item '%~dp0runtime\python-embed.zip' -Force;" ^
    "Write-Host '[3/3] Downloading pip installer...';" ^
    "Invoke-WebRequest -UseBasicParsing -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile '%~dp0runtime\get-pip.py';"

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to download the portable Python runtime.
    echo [BŁĄD] Nie udało się pobrać przenośnego środowiska Python.
    echo.
    echo Install Python manually:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

if not exist "%~dp0runtime\python.exe" (
    echo.
    echo [ERROR] Python executable was not created.
    echo [BŁĄD] Nie znaleziono pliku runtime\python.exe.
    echo.
    pause
    exit /b 1
)

REM ============================================================
REM 4. Enable site-packages in Embedded Python
REM ============================================================

echo.
echo [INFO] Configuring portable Python...

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
    "$file='%~dp0runtime\python311._pth';" ^
    "$content=Get-Content -LiteralPath $file;" ^
    "$content=$content -replace '^#import site$', 'import site';" ^
    "[System.IO.File]::WriteAllLines($file,$content,[System.Text.Encoding]::ASCII);"

if errorlevel 1 (
    echo [ERROR] Could not configure python311._pth.
    echo [BŁĄD] Nie udało się skonfigurować python311._pth.
    pause
    exit /b 1
)

REM ============================================================
REM 5. Install pip and dependencies
REM ============================================================

echo.
echo [INFO] Installing pip...
"%~dp0runtime\python.exe" "%~dp0runtime\get-pip.py" --no-warn-script-location

if errorlevel 1 (
    echo.
    echo [ERROR] pip installation failed.
    echo [BŁĄD] Instalacja pip nie powiodła się.
    pause
    exit /b 1
)

set "PYTHON_EXE=%~dp0runtime\python.exe"

goto INSTALL_REQUIREMENTS


REM ============================================================
REM Check dependencies
REM ============================================================

:CHECK_DEPS

echo.
echo [INFO] Checking required libraries...

%PYTHON_EXE% -c "import flask, PIL, google.genai" >nul 2>&1

if errorlevel 1 (
    goto INSTALL_REQUIREMENTS
)

echo [OK] Required Python libraries are installed.
goto RUN_APP


REM ============================================================
REM Install requirements
REM ============================================================

:INSTALL_REQUIREMENTS

echo.
echo [INFO] Installing required libraries...
echo [INFO] Instalowanie wymaganych bibliotek...
echo.

if not exist "%~dp0requirements.txt" (
    echo [ERROR] requirements.txt was not found.
    echo [BŁĄD] Nie znaleziono pliku requirements.txt.
    echo.
    pause
    exit /b 1
)

%PYTHON_EXE% -m pip install --disable-pip-version-check --no-warn-script-location -r "%~dp0requirements.txt"

if errorlevel 1 (
    echo.
    echo [ERROR] Dependency installation failed.
    echo [BŁĄD] Instalacja bibliotek nie powiodła się.
    echo.
    pause
    exit /b 1
)


REM ============================================================
REM Run application
REM ============================================================

:RUN_APP

echo.
echo [INFO] Freeing port 5005 if currently in use...

for /f "tokens=5" %%A in ('netstat -aon ^| findstr /R /C:":5005 .*LISTENING"') do (
    if not "%%A"=="0" (
        taskkill /F /PID %%A >nul 2>&1
    )
)

echo.
echo ===================================================================
echo.
echo              D2 UBERAPP IS READY
echo.
echo -------------------------------------------------------------------
echo.
echo   [SERVER]  http://127.0.0.1:5005
echo.
echo   [HOTKEY]  D2R: najedź kursorem na przedmiot i naciśnij F10
echo.
echo   [AUDIO]   Dźwięk potwierdza przechwycenie przedmiotu.
echo             Gemini AI automatycznie analizuje przedmiot.
echo.
echo   [MARKET]  https://d2uberappmarket.tw5.org
echo.
echo -------------------------------------------------------------------
echo.
echo   [WAŻNE]   Pozostaw to okno otwarte podczas gry.
echo.
echo ===================================================================
echo.

%PYTHON_EXE% "%~dp0app.py"

set "APP_EXIT_CODE=%errorlevel%"

if not "%APP_EXIT_CODE%"=="0" (
    echo.
    echo ===================================================================
    echo   [ERROR] Application stopped with exit code %APP_EXIT_CODE%.
    echo   [BŁĄD]  Aplikacja została zatrzymana z błędem.
    echo ===================================================================
    echo.
    pause
)

endlocal
exit /b %APP_EXIT_CODE%