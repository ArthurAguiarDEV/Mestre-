@echo off
chcp 65001 >nul
title Mestre - ativar a placa de video NVIDIA
cd /d "%~dp0.."
echo.
echo ================================================================
echo  Ativar a placa de video NVIDIA para o Whisper
echo ================================================================
echo  - Deixa o reconhecimento de voz MUITO mais rapido.
echo  - Baixa cerca de 1,5 GB de bibliotecas da NVIDIA: cuBLAS e cuDNN.
echo  - Precisa do driver da NVIDIA atualizado.
echo  - Se der errado, nada quebra: o Mestre continua usando o processador.
echo.
pause
venv\Scripts\python.exe -m pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"
if errorlevel 1 (
  echo.
  echo [ERRO] Nao consegui baixar. Verifique a internet e rode de novo.
  pause
  exit /b 1
)
echo.
echo Testando a placa de video...
venv\Scripts\python.exe -c "import sys; from app.audio import gpu_disponivel; sys.exit(0 if gpu_disponivel() else 1)"
if errorlevel 1 (
  echo.
  echo [AVISO] As bibliotecas foram instaladas, mas a placa ainda nao respondeu.
  echo Atualize o driver da NVIDIA pelo app NVIDIA ou em nvidia.com/drivers,
  echo reinicie o PC e rode este arquivo de novo.
) else (
  echo.
  echo [OK] Placa de video pronta!
  echo Agora abra o painel, aba Audio: escolha o modelo large-v3-turbo,
  echo clique em Transcrever para testar e depois em Salvar e reiniciar o Mestre.
)
pause
