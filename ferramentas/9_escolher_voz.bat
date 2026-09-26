@echo off
chcp 65001 >nul
title Mestre - escolher voz
cd /d "%~dp0.."
call venv\Scripts\activate.bat
python -m app.vozes
pause
