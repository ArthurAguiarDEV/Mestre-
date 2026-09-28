@echo off
title Assessor - treinar a palavra de ativacao
cd /d "%~dp0.."
echo Treina o detector local da palavra de ativacao (gratis, no seu PC, uns 20 a 40 minutos).
echo Ele usa as vozes do PC, os audios que o microfone ja ouviu e, se voce quiser, a SUA voz.
echo.
set GRAVAR=0
set AMBIENTE=0
set /p RESP=Quer gravar voce falando a palavra 30 vezes agora? (s/n) 
if /i "%RESP%"=="s" set GRAVAR=30
set /p RESP2=Quer gravar 5 minutos do ambiente com um video tocando (sem falar a palavra)? (s/n) 
if /i "%RESP2%"=="s" set AMBIENTE=5
echo.
venv\Scripts\python.exe ferramentas\treinar_palavra.py --gravar-minha-voz %GRAVAR% --gravar-ambiente %AMBIENTE%
echo.
echo Depois: painel, Audio, ligar "Detector local da palavra" e Salvar.
pause
