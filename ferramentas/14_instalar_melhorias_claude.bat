@echo off
title Mestre - instalar as melhorias do Claude Code
cd /d "%~dp0.."
if not exist "_melhorias_claude\claude" (
  echo [ERRO] Nao achei a pasta _melhorias_claude. Nada foi feito.
  pause
  exit /b 1
)
echo Este instalador copia para a pasta .claude do projeto:
echo   - settings.local.json  (permissoes + 2 hooks: conferir edicao e teste ao encerrar)
echo   - hooks\conferir_edicao.py e hooks\testar_ao_parar.py
echo   - agents\revisor-windows.md
echo   - commands\pedido.md, entregar.md, analisar-historico.md
echo   - rules\ferramentas-claude.md
echo   - skills\avaliar-esforco\SKILL.md
echo Nenhum arquivo existente do .claude e apagado. CLAUDE.md e settings.json nao sao tocados.
echo.
if exist ".claude\settings.local.json" (
  echo [AVISO] Ja existe .claude\settings.local.json. Vou guardar uma copia como settings.local.json.antes
  copy /y ".claude\settings.local.json" ".claude\settings.local.json.antes" >nul
)
choice /c SN /m "Instalar agora"
if errorlevel 2 (
  echo Cancelado. Nada foi feito.
  pause
  exit /b 0
)
xcopy "_melhorias_claude\claude" ".claude" /E /I /Y /Q
if errorlevel 1 (
  echo [ERRO] A copia falhou. Tire um print desta tela.
  pause
  exit /b 1
)
echo.
echo PRONTO. Abra o Claude Code nesta pasta e digite /pedido ou /entregar.
echo Para desfazer: apague os arquivos listados acima dentro de .claude
pause
