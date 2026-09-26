@echo off
chcp 65001 >nul
title Mestre - modo texto
cd /d "%~dp0.."
call venv\Scripts\activate.bat
python -m app.main --texto
pause
