@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"

rem Use the system default browser so the latest local page opens in the user's browser.
call "%~dp0start_local_web.bat"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
  echo.
  echo Start failed. Please read the message above and try again.
  pause
)

endlocal
exit /b %EXIT_CODE%
