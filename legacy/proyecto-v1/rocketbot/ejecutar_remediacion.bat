@echo off
setlocal

cd /d "%~dp0.."

if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" "remediacion\remediador.py"
) else (
    python "remediacion\remediador.py"
)

set EXIT_CODE=%ERRORLEVEL%
echo.
echo Remediacion finalizada con codigo %EXIT_CODE%.
exit /b %EXIT_CODE%
