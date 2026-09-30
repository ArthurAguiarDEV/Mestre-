# Estudo de layout — entrega do Codex

Data: 30/09/2026. Estado: **pronto_para_escolher**.

## Entrega

Galeria: `design/layout-2026-09/index.html`.
Protótipo: `app.html`, `app.css` e `app.js` na mesma pasta.
Três estruturas distintas: Órbita (lateral), Aurora (horizontal/editorial), Pulso
(estação de controle com trilho e foco em monitores). Todas têm claro/escuro,
fontes e ícones próprios da direção visual, oito áreas navegáveis e subabas.

O estudo usa dados demonstrativos e nenhuma API. Controles de sistema/mídia são
simulações identificadas. Feedback e resultados demonstrativos podem ser baixados.
Preferência é registrada no navegador, não enviada a uma IA nem gravada automaticamente
no cartão de escolha. O nome/perfil Arthur Magnífico veio do próprio pedido.

Guia de integração: `design/layout-2026-09/GUIA_IMPLEMENTACAO.md`, com mapa das 18 páginas,
tokens, adaptação de tamanho, limites, fatias de implementação e critérios de entrega.
Prompt futuro: `tarefas_ia/PROMPT_CLAUDE_005_LAYOUT.md`.

## Inspeção e verificações

- Painel atual visualizado em cópia temporária com configuração de exemplo e perfil
  isolado: páginas Início e Áudio. Não usei a cópia de produção nem ativei gravação.
- Inspeção visual das capturas desktop dos três modelos e validação mobile; uma falha de
  encaixe de seção da Aurora foi corrigida antes da entrega.
- Verificação automatizada por Playwright/Edge instalado: larguras 1440, 800 e 390 px,
  troca de tema, todas as áreas em tela estreita, busca de Spotify, controles, conversa
  simulada, quatro etapas de validação, resumo, nova rodada e download da preferência.
- Resultado salvo em `design/layout-2026-09/verificacao-ui.json`: PASS, zero erros de
  JavaScript e zero chamadas HTTP externas no teste local. Galeria com três previews carregados.
- Suíte do repositório: 147 testes OK e 302/302 frases (exit 0); ver revisão do 004.
- Não é auditoria completa de acessibilidade nem teste de integração do layout no Mestre.

## Execução local

Pode abrir index.html diretamente no navegador. Há também `servir_previa.py`, que serve
somente esta pasta em `http://127.0.0.1:8846/` para a prévia no Codex. Processo local,
sem publicação na internet. Para encerrar esse servidor, feche apenas o processo dessa
prévia; não encerre indiscriminadamente os processos Python do computador.

## Aguardando

Escolha do usuário e ajustes desejados. Implementação no CustomTkinter, atalho de teste
e revisão visual do aplicativo serão a etapa seguinte. O estudo não constitui aprovação
automática de uma proposta, implementação de funções novas ou autorização de commit.
