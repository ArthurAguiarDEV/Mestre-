# Classificação da suíte antiga

Base analisada: `testes/teste_basico.py` no commit `f0e1b7e`. A classificação
considera o efeito necessário para provar cada comportamento, mesmo quando o
teste antigo tentava esconder a janela com transparência.

## Migráveis sem interface

| Grupo antigo | Situação nesta tarefa |
|---|---|
| Configuração: leitura, gravação, comentários, mapas, mescla de rotina externa e migrações | Recuperado em `teste_regressoes_sem_interface.py` |
| Vocabulário: 277 frases e migração de sites padrão | Já estava recuperado; migração de configuração ganhou testes diretos |
| Validar atualização: parser, captura, conferência, modo contínuo, sessão, relatório, feedback e pedido de correção | Recuperado sem a parte do painel e sem gravar áudio |
| Atualização por `.zip`: versão, substituição, reserva, obsoletos e preservação de dados | Recuperado e ampliado para todas as áreas protegidas e perfis personalizados |
| Importação de Central, bandeja e atualizador | Pendente; deve virar testes unitários de importação sem inicialização lateral |

## Dependentes de substitutos em memória

| Grupo antigo | Substitutos necessários |
|---|---|
| Comandos falados; ditado e pensamento; ensinar rotina | Voz, memória, relógio, arquivos temporários, IA e todas as ações de sistema |
| Vozes do painel, servidor da voz natural e voz de reserva | Geradores de áudio, servidor, processo e relógio |
| Nome/palavra novos e aparência | Modelo dos campos do painel e indicador, sem construir Tk |
| Responder só à voz do dono e captação | Extrator de características, transcritor, blocos de áudio e relógio |
| Fala fluida, interrupção e continuação | Gerador/tocador de voz, filas, eventos e relógio |
| Avisos do PC | PowerShell, eventos do Windows, Telegram e relógio |
| Sugestões de melhoria | Histórico, ouvido, IA, configuração e relógio |
| Troca de IA quando demora ou falha | Provedores de IA, falhas, tempo e fila de trabalho |
| Avatar: cálculo visual, animação e posição | Estado, relógio, armazenamento de posição e emissor UDP |
| Painel com 2.000 canais, paginação, salvamento e rotina externa | Modelo de widgets em memória ou extração da lógica para classes sem Tk |
| Painel 2.5, menu, cartões e página de tempos | Modelo de widgets e fontes de estado/histórico |
| Parte da validação que acompanha o painel | Modelo dos controles, agendador e memória em arquivo temporário |

## Dependentes de validação real

| Grupo antigo | Motivo |
|---|---|
| Renderização e interação do painel, indicador e avatar | Exigem verificar janela, foco, geometria, desenho e eventos reais |
| Reprodução, interrupção e qualidade das vozes | Exigem saída de áudio real e avaliação auditiva |
| Microfone, reconhecimento do dono e captação completa | Exigem microfone, modelos e amostras reais |
| Modelos offline de Whisper/locutor e servidor natural com GPU | Exigem modelos instalados, carga real e possivelmente GPU |
| Posicionamento em monitores, foco, bandeja e integração de janelas | Exigem Windows e dispositivos físicos; proibidos nesta tarefa |

Os testes recuperados nesta etapa não desativam nem contornam
`testes/seguranca.py`. Os grupos pendentes só podem migrar quando seus efeitos
forem separados em substitutos em memória, ou numa validação manual fora da suíte
automática segura.
