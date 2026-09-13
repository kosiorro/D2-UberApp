@echo off
cd /d "%~dp0"
title D2 UberApp

echo Zwalnianie portu 5005...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5005" ^| findstr "LISTENING"') do (
    if not "%%a"=="0" taskkill /f /pid %%a >nul 2>nul
)

echo Uruchamianie D2 UberApp...
where python >nul 2>nul
if %errorlevel%==0 (
    python app.py
) else (
    where py >nul 2>nul
    if %errorlevel%==0 (
        py -3 app.py
    ) else (
        python3 app.py
    )
)

if errorlevel 1 (
    echo.
    echo Wystapil blad podczas uruchamiania aplikacji.
    echo Upewnij sie, ze zainstalowales wymagane pakiety: pip install -r requirements.txt
    pause
)
