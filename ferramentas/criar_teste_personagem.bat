@echo off
rem Cria ou atualiza a copia de TESTE do personagem e o atalho "Mestre - TESTE personagem" na area de trabalho.
rem O config.yaml de uso nao e tocado.
cd /d "%~dp0.."
venv\Scripts\python.exe -m ferramentas.criar_teste_personagem
pause
