@echo off
chcp 65001 >nul
cd /d "%~dp0.."
set "PASTA=%CD%\"
set "ATALHO=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Mestre.lnk"
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%ATALHO%'); $s.TargetPath='wscript.exe'; $s.Arguments='\"%PASTA%iniciar_oculto.vbs\"'; $s.WorkingDirectory='%PASTA%'; $s.Save()"
if exist "%ATALHO%" (
  echo [OK] O Mestre vai ligar sozinho sempre que voce entrar no Windows.
  echo Para desfazer, rode o 7_desativar_inicio_automatico.bat
) else (
  echo [ERRO] Nao consegui criar o atalho.
)
pause
