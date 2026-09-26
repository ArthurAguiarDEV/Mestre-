@echo off
chcp 65001 >nul
title Mestre - teste automatico
cd /d "%~dp0.."
echo Testando o basico do Mestre numa COPIA (seu config nao e tocado). Leva uns 30 segundos...
echo.
venv\Scripts\python.exe -m testes.teste_basico
echo.
echo Se algo FALHOU, tire um print desta janela e mande para o Claude.
pause
