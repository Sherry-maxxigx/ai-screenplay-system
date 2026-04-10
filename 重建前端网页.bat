@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"

set "FORCE_FRONTEND_BUILD=1"
set "NO_BROWSER=1"
call "%~dp0start_local_web.bat"
set "EXIT_CODE=%ERRORLEVEL%"

if "%EXIT_CODE%"=="0" (
  echo.
  echo Frontend rebuild completed.
  echo The local backend was started for verification and can now be closed if you do not need it.
) else (
  echo.
  echo Frontend rebuild failed. Please read the message above.
)

pause
endlocal
exit /b %EXIT_CODE%
