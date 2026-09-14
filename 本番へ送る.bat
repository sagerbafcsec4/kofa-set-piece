@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>&1 || (
  echo Python not found. Please install Python first.
  pause & exit /b 1
)
python "deploy.py" %*
echo.
pause
