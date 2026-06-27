@echo off
setlocal

cd /d "%~dp0.."

if exist "venv\Scripts\python.exe" (
    "venv\Scripts\python.exe" "rocketbot\robot_observabilidad.py"
) else (
    python "rocketbot\robot_observabilidad.py"
)

set EXIT_CODE=%ERRORLEVEL%
echo.
echo Flujo Rocketbot finalizado con codigo %EXIT_CODE%.
exit /b %EXIT_CODE%
