@echo off
chcp 65001 >nul
echo.
echo Configurando a energia para o Mestre poder te ouvir sempre:
echo  - Na tomada: o PC NUNCA entra em suspensao
echo  - Na tomada: a TELA desliga sozinha apos 10 minutos (economiza energia)
echo  - Na bateria: nada muda (para nao gastar a bateria do notebook)
echo.
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change monitor-timeout-ac 10
echo [OK] Energia configurada.
echo.
echo Falta um passo manual (veja a Etapa 6 do guia):
echo Configuracoes ^> Contas ^> Opcoes de entrada ^>
echo "Se voce se ausentou, quando o Windows deve exigir que voce entre novamente?" = Nunca
echo.
start ms-settings:signinoptions
pause
