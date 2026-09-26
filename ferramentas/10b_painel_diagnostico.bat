@echo off
chcp 65001 >nul
title Mestre - painel (modo diagnostico)
cd /d "%~dp0.."
echo Abrindo o painel com esta janela aberta. Se der erro, ele aparece aqui.
echo.
venv\Scripts\python.exe -m app.iniciar_painel
echo.
echo ---------------------------------------------------------------
echo Se apareceu algum erro acima, tire um print e mande para o Claude.
echo O erro tambem fica salvo em logs\painel_erro.log
pause
