# Tarefa 003 — Organização segura das pastas (retorno do Claude)

**Data:** 30/09/2026 · **Executor:** Claude Code (Opus) · **Revisor:** ChatGPT/Codex
**Branch local:** `entrega/001-validacao-variada` (HEAD `a294459`) · **Sem commit e sem push.**

## Resumo simples

- A pasta `tarefas_ia/` ganhou um índice novo (`README_CENTRAL.md`) que responde em
  um minuto: qual é a tarefa da vez, qual prompt copiar, onde fica o retorno e quem faz
  cada etapa.
- O material do Manus e a fila antiga do Ollama foram **movidos** para
  `tarefas_ia/arquivo/`, sem apagar e sem editar nada (conteúdo conferido por hash).
- Nenhum arquivo do aplicativo, do protótipo CrewAI/Ollama, de configuração ou de dados
  pessoais foi tocado. Nenhum arquivo versionado no Git foi movido: tudo o que mudou de
  lugar ainda não estava no Git.

## Antes de começar

- Lidos: `AGENTS.md`, `CLAUDE.md`, `COORDENACAO_IA.md`, `ORQUESTRACAO_IA.md`,
  `tasks/lessons.md`, `tarefas_ia/003-organizacao-pastas.md`, `tarefas_ia/README_CENTRAL.md`.
- `git status` inicial: só `MELHORIAS.md` modificado (+2 linhas, trabalho do usuário) e
  vários arquivos não versionados (`.agents/`, `.codex/`, `agentes_crewai/`, partes de
  `tarefas_ia/`). `MELHORIAS.md` não foi tocado.
- Busca de referências antes de mover: `grep` por `tarefas_ia`, `prompts_prontos`,
  `hoje.md`, `PROMPT_MANUS`, `PROMPT_CLAUDE`, `README_CENTRAL`, `central_tarefas`,
  `execucoes`, `resultados/` e `manus` no repositório inteiro (fora de `venv`, `.git`,
  `modelos`, `navegador_mestre`). O código do aplicativo (`app/`) não usa nenhum desses
  caminhos.

## Arquivado (movido para `tarefas_ia/arquivo/`)

| De | Para |
|---|---|
| `tarefas_ia/PROMPT_MANUS_COMANDOS.md` | `tarefas_ia/arquivo/manus/PROMPT_MANUS_COMANDOS.md` |
| `tarefas_ia/PROMPT_MANUS_PASTAS.md` | `tarefas_ia/arquivo/manus/PROMPT_MANUS_PASTAS.md` |
| `tarefas_ia/PROMPT_MANUS_PERFIS.md` | `tarefas_ia/arquivo/manus/PROMPT_MANUS_PERFIS.md` |
| `tarefas_ia/PROMPT_MANUS_VALIDACAO.md` | `tarefas_ia/arquivo/manus/PROMPT_MANUS_VALIDACAO.md` |
| `tarefas_ia/manus/hoje.md` | `tarefas_ia/arquivo/manus/hoje.md` |
| `tarefas_ia/prompts_prontos/*-manus.md` (5) | `tarefas_ia/arquivo/manus/prompts_prontos/` |
| `tarefas_ia/ollama/hoje.md` | `tarefas_ia/arquivo/ollama/hoje.md` |
| `tarefas_ia/prompts_prontos/*-ollama.md` (5) | `tarefas_ia/arquivo/ollama/prompts_prontos/` |

Total: 16 arquivos. As pastas `tarefas_ia/manus/` e `tarefas_ia/ollama/` ficaram vazias e
foram removidas (só a pasta vazia; nenhum arquivo). Todos estavam fora do Git (`??`).

## Criado ou reescrito

- `tarefas_ia/README_CENTRAL.md` (reescrito): "Em um minuto", "Quem faz o quê",
  tabela de cartões com situação, mapa de cada pasta (ativo/histórico/protótipo), seção
  separada do protótipo CrewAI/Ollama e regras fixas. O comando antigo do
  `central_tarefas.py` foi mantido na seção do protótipo.
- `tarefas_ia/arquivo/README.md` (novo): o que foi arquivado, de onde veio e por quê.
- Este relatório.

## Mantido no lugar (e por quê)

| Caminho | Motivo |
|---|---|
| `tarefas_ia/001-*.md`, `002-*.md`, `003-*.md` | Cartões; `COORDENACAO_IA.md` cita o caminho do 001 |
| `PROMPT_CLAUDE_EXECUTOR.md`, `PROMPT_CLAUDE_ORGANIZACAO.md`, `PROMPT_CHATGPT_COORDENADOR.md` | Prompts ativos; mover para subpasta teria pouco ganho e quebraria referências |
| `PLANO_MESTRE_2026-09-29.md` | Citado pelo prompt do ChatGPT; versionado no Git |
| `resultados/` inteiro, incluindo os 4 relatórios `*-manus.md*` | Retornos do Claude citam `resultados/CODIGO-DA-TAREFA-manus.md` e `resultados/perfis-manus.md.md`; as frentes "comandos complexos" e "validação dinâmica" ainda usam essas análises como referência. São registros, não fila |
| `fila/`, `prompts_prontos/` (claude/chatgpt), `claude/hoje.md`, `chatgpt/hoje.md` | Caminhos escritos pelo `central_tarefas.py`; o índice marca como histórico |
| `execucoes/` | Caminho fixo em `agentes_crewai/orquestrador.py` |
| `agentes_crewai/` inteiro | Protótipo CrewAI/Ollama: intacto, conforme o cartão |

## Referências atualizadas

- `README_CENTRAL.md`: a linha antiga "Registre feedback em `tarefas_ia\feedback\`"
  apontava para uma pasta que **nunca existiu**; foi substituída pela etapa 7 ("problema no
  teste vira cartão novo", como em `ORQUESTRACAO_IA.md`). As instruções que mandavam abrir
  `claude\hoje.md`/`chatgpt\hoje.md` como fonte da tarefa foram trocadas pelos cartões.
- Nenhum outro arquivo ativo citava os caminhos movidos. `agentes_crewai/central_tarefas.py`
  **não precisou de ajuste**: os caminhos que ele usa (`fila/`, `prompts_prontos/`,
  `resultados/`, `<agente>/hoje.md`) continuam válidos.
- Os `hoje.md` arquivados ainda citam `tarefas_ia/prompts_prontos/...-manus.md` e
  `...-ollama.md`. Foram deixados sem edição para preservar o registro; o
  `arquivo/README.md` tem a tabela de/para.

## Verificações executadas

```bash
# 1. conteúdo idêntico antes/depois (hash de cada um dos 16 arquivos)
sha256sum <arquivos antes>  → comparado com os arquivos em tarefas_ia/arquivo/  → "HASHES IGUAIS: 16 arquivos"
# 2. nenhum arquivo sumiu
find tarefas_ia -type f | wc -l   → 61 antes, 61 depois (antes dos 2 READMEs e deste relatório)
# 3. todos os caminhos citados no índice existem
for p in <cada caminho do README_CENTRAL>; do [ -e "$p" ] && echo OK || echo FALTA; done   → todos OK
# 4. sobras de referência aos caminhos movidos
grep -rnE "PROMPT_MANUS|tarefas_ia[/\\](manus|ollama)|prompts_prontos/.*-(manus|ollama)\.md|feedback[/\\]" \
     tarefas_ia agentes_crewai prompts *.md .claude .agents .codex ferramentas app  (fora de tarefas_ia/arquivo)
     → só o aviso intencional no README_CENTRAL; os "feedback/" achados são logs/feedback do app, sem relação
# 5. estado do Git
git status --short   → só README_CENTRAL.md modificado entre os versionados; MELHORIAS.md igual ao início
```

A suíte de testes **não** foi executada, conforme o prompt: nenhum código mudou.

## Dúvidas e itens que preferi não mexer

1. **`central_tarefas.py` ainda gera para Manus e Ollama.** A lista `AGENTES` tem
   `manus` e `ollama`, e o texto do cartão gerado cita "Manus: pesquisa e validação". Se
   alguém rodar o gerador, ele recria `tarefas_ia/manus/` e `tarefas_ia/ollama/`. Não mudei
   porque o cartão só autoriza ajuste "para manter caminhos válidos" e isso muda o
   comportamento do script. Deixei um aviso no índice. Sugestão para um cartão pequeno:
   tirar as duas entradas de `AGENTES` e a linha "Manus" do texto gerado.
2. **`claude/hoje.md` e `chatgpt/hoje.md` estão desatualizados.** Os 5 itens aparecem
   "pendente", mas a validação (`a641ed`) e mídia (`82420f`) já têm retorno do Claude, e
   as 3 entradas de "repaginar painel" são duplicadas. Não editei (seria adivinhar o status
   de cada uma); o índice avisa que a fonte da tarefa é o cartão. Decidir se arquiva essas
   duas filas também.
3. **`COORDENACAO_IA.md` → "Estado da fila"** não cita o cartão 003 e ainda diz que o 001
   "aguarda implementação", mas o commit `fe65b4b` desta branch já traz o cartão 001. Fora
   do escopo (o cartão limita a `tarefas_ia/`); vale atualizar.
4. **`tasks/lessons.md`, linha 4**, ainda lista o Manus entre quem lê o arquivo. Fora do
   escopo; troca sugerida: "(Claude e ChatGPT/Codex)".
5. **Situação dos cartões 001 e 002** no índice foi escrita pelo que o Git e os arquivos
   mostram, não por uma aprovação registrada. O ChatGPT/Codex deve confirmar.
6. **`resultados/perfis-manus.md.md`** tem extensão dupla. Não renomeei porque
   `resultados/perfis-streaming-claude.md` cita esse nome exato.
7. Os arquivos novos e movidos continuam fora do Git (como já estavam). Decidir no commit
   da entrega o que entra: `fila/`, `prompts_prontos/` e `execucoes/` são saídas geradas e
   talvez não devam ser versionados.
