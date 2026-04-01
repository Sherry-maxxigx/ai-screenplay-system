@echo off
chcp 65001 >nul
setlocal

cd /d "%~dp0"

echo ========================================================
echo 以【无 Docker】模式启动 AI编剧系统...
echo ========================================================

set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%backend"
set "FRONTEND_DIR=%ROOT_DIR%frontend"
set "PYTHON_EXE=%ROOT_DIR%.venv\Scripts\python.exe"
set "NODE_DIR="

if exist "%PYTHON_EXE%" (
  echo 使用虚拟环境 Python: %PYTHON_EXE%
) else (
  set "PYTHON_EXE=python"
  echo 未检测到 .venv，改用系统 Python
)

if exist "%ProgramFiles%\nodejs\node.exe" set "NODE_DIR=%ProgramFiles%\nodejs"
if not defined NODE_DIR if exist "%ProgramFiles(x86)%\nodejs\node.exe" set "NODE_DIR=%ProgramFiles(x86)%\nodejs"
if not defined NODE_DIR if exist "%LocalAppData%\Programs\nodejs\node.exe" set "NODE_DIR=%LocalAppData%\Programs\nodejs"
if defined NODE_DIR set "PATH=%NODE_DIR%;%PATH%"

where node >nul 2>nul
if errorlevel 1 (
  echo [错误] 未检测到 Node.js
  pause
  exit /b 1
)

"%PYTHON_EXE%" --version >nul 2>nul
if errorlevel 1 (
  echo [错误] 未检测到 Python，请先安装 Python 3.10+
  pause
  exit /b 1
)

"%PYTHON_EXE%" -c "import uvicorn" >nul 2>nul
if errorlevel 1 (
  echo 正在安装后端依赖（首次可能需要几分钟）...
  "%PYTHON_EXE%" -m pip install -r "%BACKEND_DIR%\requirements.txt"
  if errorlevel 1 (
    echo [错误] 后端依赖安装失败
    pause
    exit /b 1
  )
)

set "NEED_NPM_INSTALL=0"
if not exist "%FRONTEND_DIR%\node_modules" set "NEED_NPM_INSTALL=1"
if not exist "%FRONTEND_DIR%\node_modules\.bin\vite.cmd" set "NEED_NPM_INSTALL=1"

if "%NEED_NPM_INSTALL%"=="1" (
  echo 正在安装/修复前端依赖（可能需要几分钟）...
  call npm --prefix "%FRONTEND_DIR%" install
  if errorlevel 1 (
    echo [错误] 前端依赖安装失败，请检查网络后重试
    pause
    exit /b 1
  )
)

echo 正在后台启动后端与前端（不弹出终端窗口）...

powershell -NoProfile -ExecutionPolicy Bypass -Command "$py='%PYTHON_EXE%'; $wd='%BACKEND_DIR%'; Start-Process -WindowStyle Hidden -FilePath $py -WorkingDirectory $wd -ArgumentList '-m','uvicorn','main:app','--host','0.0.0.0','--port','8000','--reload'"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$wd='%FRONTEND_DIR%'; Start-Process -WindowStyle Hidden -FilePath 'cmd.exe' -WorkingDirectory $wd -ArgumentList '/c','npm run dev -- --host 0.0.0.0 --port 3000'"

timeout /t 5 /nobreak >nul
start http://localhost:3000/

echo.
echo ========================================================
echo 已后台启动：
echo   前端: http://localhost:3000
echo   后端: http://localhost:8000/docs
echo ========================================================

endlocal
exit /b 0
