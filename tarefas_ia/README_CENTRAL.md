# Central de tarefas das IAs

Esta pasta guarda as tarefas que as IAs fazem no Mestre. Nada aqui manda mensagem
sozinho: você copia o prompt e cola no chat da IA certa. O repasse é local, em sequência
e por arquivos: uma IA por vez trabalha nesta pasta e deixa o resultado em `resultados/`.

## Em um minuto

| Pergunta | Resposta |
|---|---|
| Qual é a tarefa da vez? | **008 — auditoria e organização concluída para revisão**. Aurora + personagem já implementados; consulte `../docs/ESTADO_ATUAL.md`. B1+B2 tem sete falhas reproduzidas. |
| Qual prompt copiar para o Claude? | Não repetir 004, 005 ou 006. A próxima correção deve partir das pendências em `../docs/ESTADO_ATUAL.md`. |
| Onde fica o retorno? | `tarefas_ia/resultados/<número do cartão>-<assunto>-claude.md` |
| Quem faz cada etapa? | Veja **Quem faz o quê** logo abaixo. |

## Quem faz o quê (fluxo ativo)

| Etapa | Quem |
|---|---|
| 1. Contar o que quer | Você |
| 2. Escrever o cartão e o prompt | ChatGPT/Codex (coordena) |
| 3. Aprovar o cartão | Você |
| 4. Executar o cartão e salvar o retorno em `resultados/` | Claude (executa) |
| 5. Revisar o retorno e o que mudou | ChatGPT/Codex (revisa) |
| 6. Testar no Windows (voz, janelas, aparência) | Você |
| 7. Problema no teste → vira cartão novo | ChatGPT/Codex |
| 8. Commit e GitHub, só depois de você escrever **OK para publicar** | Quem você mandar |

Só essas duas IAs estão no fluxo ativo. O Manus foi desativado: o material dele está
em `arquivo/`. O ciclo completo está em `ORQUESTRACAO_IA.md` e `COORDENACAO_IA.md`.

## Cartões

| Cartão | Assunto | Prompt | Situação (30/09) |
|---|---|---|---|
| `008-auditoria-organizacao.md` | Auditoria global, organização e checkpoint | — | Evidências independentes em `../docs/ESTADO_ATUAL.md`; publicação desta entrega autorizada pelo usuário; sem aceite físico presumido |
| `007-integracao-aurora-personagem.md` | Integração Aurora + personagem | — | Registro retrospectivo; 195 testes e 302 frases aprovados; verificação gráfica OK; validação física pendente |
| `006-avatar-personagem.md` | Personagem 2D (homem/mulher, fantasias Marvel/DC, jeito por personalidade) no lugar do robô | `PROMPT_CLAUDE_006_AVATAR.md` | Feito na noite de 30/09 + 2ª rodada na manhã de 30/09 (animação lisa, braço, rosto, 52 fantasias, atalho **Mestre - TESTE personagem**), sem commit/push; `resultados/006-avatar-personagem-claude.md` e `resultados/006-pesquisa-avatar-claude.md`; **pronto_para_revisao**; teste em `design/avatar-2026-09/index.html` |
| `004-fluxo-duas-ias.md` | Gerador e instruções para duas IAs | `PROMPT_CLAUDE_004.md` | Executado e aprovado tecnicamente; `resultados/004-revisao-codex.md`; sem commit/push |
| `005-novo-layout.md` | Aurora: nova interface, Mídias e telas e visão geral organizada | `PROMPT_CLAUDE_005_LAYOUT.md` | Implementado; `resultados/005-layout-claude.md`; atualizado pelo 007. Não executar novamente; aceite físico pendente |
| `003-organizacao-pastas.md` | Organizar esta pasta | `PROMPT_CLAUDE_ORGANIZACAO.md` | Organização inicial revisada; pendências delimitadas no 004. Retorno: `resultados/003-organizacao-claude.md` |
| `002-orquestracao-ia.md` | Orquestração das IAs | — | Primeira entrega feita (`ORQUESTRACAO_IA.md`, `prompts/`); próximos passos dependem de cartão novo |
| `001-validacao-variada.md` | Testes variados na validação | `PROMPT_CLAUDE_EXECUTOR.md` | Implementado no commit `fe65b4b` (branch `entrega/001-validacao-variada`); confirmar revisão e teste com o ChatGPT/Codex |

Quem criar ou terminar um cartão atualiza esta tabela. O plano geral das frentes está
em `PLANO_MESTRE_2026-09-29.md`.

## O que tem em cada lugar

| Caminho | Para que serve | Ativo? |
|---|---|---|
| `00N-*.md` | Cartões (a tarefa oficial) | Sim |
| `PROMPT_CLAUDE_*.md` | Prompts para colar no Claude | Sim |
| `PROMPT_CHATGPT_COORDENADOR.md` | Prompt para colar no ChatGPT/Codex | Sim |
| `PLANO_MESTRE_2026-09-29.md` | Ordem das frentes de trabalho | Sim |
| `resultados/` | Retornos atuais das IAs; cinco relatos antigos foram preservados em `arquivo/resultados/` na auditoria 008 | Sim |
| `fila/`, `prompts_prontos/`, `claude/hoje.md`, `chatgpt/hoje.md` | Criados pelo `central_tarefas.py`. Os itens de 29/09 aparecem "pendente" mesmo depois de tratados; as filas antigas estão em `arquivo/chatgpt/` e `arquivo/claude/` | Só histórico: a tarefa da vez é o cartão. Os `hoje.md` atuais só apontam para o cartão da vez |
| `execucoes/` | Saídas do protótipo local (`orquestrador.py`) | Protótipo |
| `arquivo/` | Material do Manus, fila antiga do Ollama e as filas de 29/09 do ChatGPT/Claude (veja `arquivo/README.md`) | Não |

## Protótipo local CrewAI/Ollama (separado do fluxo ativo)

A pasta `agentes_crewai/` é um teste que roda **só no seu PC** com o Ollama. Ele não
conversa com o ChatGPT nem com o Claude e não é necessário para o fluxo acima.

- `crew.py`: exemplo simples, salva em `agentes_crewai/resultado.md`.
- `orquestrador.py`: planeja um pedido e salva em `tarefas_ia/execucoes/`.
- `central_tarefas.py`: cria cartão e prompts em `fila/` e `prompts_prontos/`.

```powershell
cd C:\Ias\Mestre-repo\agentes_crewai
..\venv\Scripts\python.exe central_tarefas.py "Descreva aqui a melhoria desejada"
```

O `central_tarefas.py` gera cartão, JSON, prompts e filas **somente para `chatgpt` e
`claude`**, a partir de uma única lista (`AGENTES`). O Ollama continua sendo o motor de IA
local do assistente e do protótipo CrewAI, mas não recebe tarefas do gerador. Nas
recomendações, Sonnet/Opus valem só para o Claude; o ChatGPT/Codex usa o modelo
configurado no app. Recomendação escrita não muda a configuração do chat: ajuste no seletor.

## Regras que valem sempre

- Nada de commit, push ou publicação sem você escrever **OK para publicar**.
- Não apagar arquivo antigo: mover para `arquivo/` e anotar em `arquivo/README.md`.
- Não colocar `config.yaml`, `aprendido.yaml`, logs, áudios, histórico ou chaves em entregas.
