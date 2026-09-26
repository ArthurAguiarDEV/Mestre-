@echo off
chcp 65001 >nul
title Instalando o Mestre
cd /d "%~dp0.."
echo.
echo ==========================================================
echo    INSTALANDO O MESTRE - isso pode levar de 5 a 15 minutos
echo ==========================================================
echo.
where py >nul 2>nul
if errorlevel 1 (
  echo [ERRO] O Python nao foi encontrado.
  echo Instale o Python 3.12 pelo site python.org e marque a opcao
  echo "Add python.exe to PATH". Depois rode este arquivo de novo.
  pause
  exit /b 1
)
if not exist venv (
  echo [1/4] Criando o ambiente do Mestre...
  py -3.12 -m venv venv 2>nul || py -3 -m venv venv
)
call venv\Scripts\activate.bat
echo [2/4] Atualizando o instalador de pacotes...
python -m pip install --upgrade pip --quiet
echo [3/4] Instalando as bibliotecas (a parte mais demorada)...
pip install -r requirements.txt
if errorlevel 1 (
  echo [ERRO] Falha ao instalar as bibliotecas. Tire um print desta tela.
  pause
  exit /b 1
)
echo [4/4] Baixando os modelos de voz...
python -m app.baixar_modelos
if errorlevel 1 (
  echo [ERRO] Falha ao baixar os modelos. Verifique a internet e rode de novo.
  pause
  exit /b 1
)
echo.
echo ==========================================================
echo    PRONTO! Use o atalho Mestre na area de trabalho
echo ==========================================================
pause
