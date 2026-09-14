@echo off
setlocal
cd /d "%~dp0"
py -3 install_tips.py
set "rc=%errorlevel%"
echo.
pause
exit /b %rc%
