@echo off
cd /d "%~dp0.."
if not exist mestre.pid (
  echo O Mestre nao parece estar ligado.
  pause
  exit /b 0
)
set /p PID=<mestre.pid
taskkill /PID %PID% /F >nul 2>nul
del mestre.pid 2>nul
echo [OK] Mestre desligado.
pause
