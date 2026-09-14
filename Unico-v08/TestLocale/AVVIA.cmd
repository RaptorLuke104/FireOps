@echo off
setlocal
cd /d "%~dp0"
where py.exe >nul 2>&1
if errorlevel 1 (
    echo Python Launcher non trovato. Installa Python 3.11 o successivo a 64 bit da python.org.
    echo Se Python e gia installato senza launcher, apri questa cartella in un terminale e usa: python prova.py
    pause
    exit /b 1
)
py -3 -u prova.py
set "rc=%errorlevel%"
echo.
echo Test terminato. Codice uscita: %rc%
pause
exit /b %rc%
