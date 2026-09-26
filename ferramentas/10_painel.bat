@echo off
chcp 65001 >nul
title Mestre - abrindo o painel
cd /d "%~dp0.."
if not exist logs mkdir logs

if not exist venv\Scripts\python.exe (
  echo [ERRO] O Mestre ainda nao foi instalado nesta pasta.
  echo Rode primeiro o 1_instalar.bat
  pause
  exit /b 1
)

echo Verificando o que o painel precisa...
venv\Scripts\python.exe -c "import tkinter" 2>nul
if errorlevel 1 (
  echo.
  echo [ERRO] O Python foi instalado SEM o componente de janelas - tcl/tk.
  echo Conserto:
  echo  1. Configuracoes do Windows ^> Aplicativos ^> Python 3.12 ^> Modificar
  echo  2. Clique em Modify, marque "tcl/tk and IDLE", Next, Install
  echo  3. Abra este arquivo de novo
  pause
  exit /b 1
)

venv\Scripts\python.exe -c "import customtkinter, ruamel.yaml" 2>nul
if errorlevel 1 (
  echo Faltam bibliotecas do painel. Instalando agora, aguarde...
  venv\Scripts\python.exe -m pip install -r requirements.txt
  venv\Scripts\python.exe -c "import customtkinter, ruamel.yaml" 2>nul
  if errorlevel 1 (
    echo.
    echo [ERRO] Nao consegui instalar. Tire um print desta janela e mande para o Claude.
    pause
    exit /b 1
  )
)

echo Abrindo o painel...
start "" venv\Scripts\pythonw.exe -m app.central --sem-ligar
