@echo off
title Mestre - preparar o git (ponto de restauracao)
cd /d "%~dp0.."
where git >nul 2>nul
if errorlevel 1 (
  echo [ERRO] O Git nao foi encontrado.
  echo Instale o Git for Windows em git-scm.com (Next, Next, Install^) e rode este arquivo de novo.
  pause
  exit /b 1
)
if not exist .git (
  echo [1/3] Criando o historico do projeto...
  git init -q
  git config user.name >nul 2>nul || git config user.name "Mestre"
  git config user.email >nul 2>nul || git config user.email "mestre@local"
) else (
  echo [1/3] O historico ja existe.
)
echo [2/3] Guardando o estado atual...
git add -A
git commit -q -m "ponto de restauracao %date% %time%" && echo Ponto de restauracao criado. || echo Nada mudou desde o ultimo ponto.
echo [3/3] Ultimos pontos guardados:
git log --oneline -5
echo.
echo Para voltar tudo ao ultimo ponto: git checkout . (dentro desta pasta)
pause
