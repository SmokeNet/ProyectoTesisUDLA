@echo off
setlocal
cd /d "%~dp0.."

if exist "venv\Scripts\python.exe" (
  "venv\Scripts\python.exe" "continuidad\gestor_continuidad.py"
) else (
  python "continuidad\gestor_continuidad.py"
)

set EXIT_CODE=%ERRORLEVEL%
endlocal
exit /b %EXIT_CODE%
