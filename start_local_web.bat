@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"

set "PYTHON_EXE="
if exist ".venv\Scripts\python.exe" set "PYTHON_EXE=%cd%\.venv\Scripts\python.exe"
if not defined PYTHON_EXE set "PYTHON_EXE=python"

echo Starting local backend and static web app...
echo.
echo Frontend URL: http://localhost:8000/ai-screenplay-system/
echo API Docs:     http://localhost:8000/docs
echo.

start "screenplay-local-backend" /b "%PYTHON_EXE%" backend\launch_local.py

timeout /t 4 /nobreak >nul
echo Backend should now be starting in the background.
echo Open http://localhost:8000/ai-screenplay-system/ in your browser.

endlocal
exit /b 0
