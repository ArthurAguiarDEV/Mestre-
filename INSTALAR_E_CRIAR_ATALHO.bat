@echo off
chcp 65001 >nul
title Mestre - instalar e criar o atalho
cd /d "%~dp0"
echo.
echo ==========================================================
echo    MESTRE - instalar / atualizar e criar o atalho
echo ==========================================================
echo  Pode rodar quantas vezes quiser: so completa o que falta.
echo.

if not exist venv\Scripts\python.exe (
  echo Primeira vez: instalando tudo. Isso leva de 5 a 15 minutos.
  call ferramentas\1_instalar.bat
  if not exist venv\Scripts\python.exe exit /b 1
) else (
  echo [1/3] Conferindo as bibliotecas - so baixa as novas...
  venv\Scripts\python.exe -m pip install -q -r requirements.txt
  if errorlevel 1 (
    echo [ERRO] Nao consegui instalar. Verifique a internet e tire um print desta janela.
    pause
    exit /b 1
  )
)

echo [2/3] Criando o atalho "Mestre" na area de trabalho e no menu Iniciar...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$pasta = (Get-Location).Path;" ^
  "$w = New-Object -ComObject WScript.Shell;" ^
  "foreach ($lugar in @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))) {" ^
  "  $s = $w.CreateShortcut((Join-Path $lugar 'Mestre.lnk'));" ^
  "  $s.TargetPath = (Join-Path $pasta 'venv\Scripts\pythonw.exe');" ^
  "  $s.Arguments = '-m app.central';" ^
  "  $s.WorkingDirectory = $pasta;" ^
  "  $s.IconLocation = (Join-Path $pasta 'app\icone.ico');" ^
  "  $s.Description = 'Central do Mestre: ligar, desligar e configurar';" ^
  "  $s.Save() }"
if errorlevel 1 (
  echo [ERRO] Nao consegui criar o atalho. Tire um print desta janela.
  pause
  exit /b 1
)

echo [3/3] Guardando os arquivos antigos na pasta ferramentas...
for %%f in (1_instalar.bat 2_testar_por_texto.bat 3_iniciar_mestre.bat 4_ativar_inicio_automatico.bat 5_configurar_energia.bat 6_listar_microfones.bat 7_desativar_inicio_automatico.bat 8_parar_mestre.bat 9_escolher_voz.bat 10_painel.bat 10b_painel_diagnostico.bat 11_ativar_placa_de_video.bat) do (
  if exist "ferramentas\%%f" if exist "%%f" del "%%f"
)

echo.
echo ==========================================================
echo    PRONTO! Use o atalho "Mestre" da area de trabalho.
echo    Se ficou um atalho antigo repetido, pode apagar o velho.
echo ==========================================================
echo Abrindo a Central agora...
start "" venv\Scripts\pythonw.exe -m app.central
timeout /t 5 >nul
