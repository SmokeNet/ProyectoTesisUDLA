@echo off
setlocal
cd /d "%~dp0.."

if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" "playwright-monitor\monitor.py"
) else (
    python "playwright-monitor\monitor.py"
)

set EXIT_CODE=%ERRORLEVEL%
endlocal
exit /b %EXIT_CODE%
