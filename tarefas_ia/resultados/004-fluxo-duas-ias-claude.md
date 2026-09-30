# Retorno do cartão 004 — Fluxo ChatGPT/Codex + Claude

**Estado: `pronto_para_revisao`** · Executor: Claude Code (Sonnet, esforço médio) · 30/09/2026
Cartão: `tarefas_ia/004-fluxo-duas-ias.md` · Sem commit, sem push, sem alteração em `app/`
nem em `design/layout-2026-09/`.

## Base conferida antes de editar

- Branch `entrega/001-validacao-variada`, HEAD `a294459`.
- Alterações locais que já existiam e foram preservadas: `MELHORIAS.md` e
  `tarefas_ia/README_CENTRAL.md` (modificados); `.agents/`, `.codex/`, `agentes_crewai/`,
  `design/`, cartões 003/004/005, prompts, `arquivo/`, `chatgpt/`, `claude/`, `execucoes/`,
  `fila/`, `prompts_prontos/`, `resultados/` (não rastreados).
- `MELHORIAS.md` não foi tocado.

## O que mudou

| Arquivo | Mudança |
|---|---|
| `agentes_crewai/central_tarefas.py` | `AGENTES` agora é um dicionário com só `chatgpt` e `claude` (rótulo, função, instrução). Cartão (`Agentes convidados`), JSON (`agentes`), prompts e filas saem dessa mesma definição. Nova `recomendacao_modelo()`: Sonnet/Opus só no prompt do Claude; no do ChatGPT/Codex vale "o modelo configurado no seu app". Os prompts e o cartão dizem que a recomendação escrita não altera o seletor do chat. JSON mantém `modelo` (compatível) e ganhou `modelo_vale_para: "claude"`. A mensagem final imprime os caminhos reais e os agentes. Mesmo comando, mesmos caminhos (`fila/`, `prompts_prontos/`, `resultados/`, `<agente>/hoje.md`). |
| `COORDENACAO_IA.md` | Ciclo reescrito como repasse **local, sequencial, por arquivos**. Removidos "registrar cartão em commit e publicar branch de passagem", "entrega traz branch/hash" e "publica a branch de entrega". Commit/push só com o "OK para publicar" e valendo para uma entrega. A regra "entregue uma branch e um commit" virou "entregue o retorno em `resultados/`". Mensagem curta de repasse trocada (era do cartão 001 com commit e branch). "Estado da fila" ganhou nota de que é registro de 29/09; o texto antigo não foi reescrito. |
| `ORQUESTRACAO_IA.md` | Seção "Como IAs externas entram": só ChatGPT/Codex e Claude recebem tarefas; Manus desativado; Ollama é motor local do app/CrewAI, não destinatário; retorno do Claude = `pronto_para_revisao`; Sonnet/Opus são do Claude. |
| `tasks/lessons.md` | Cabeçalho sem Manus/GPT; duas lições (`erro → regra`): destinatários do gerador e modelo do ChatGPT; commit/push automático no repasse. Fim de linha CRLF preservado. |
| `agentes_crewai/README.md` | Nova seção "Gerador de tarefas para as IAs" (dois agentes, sem rede/API/Ollama, papel do Ollama). |
| `tarefas_ia/README_CENTRAL.md` | Frase sobre repasse local; linha do 004 (executado, aguarda revisão); linha de `fila/`/`hoje.md`; linha de `arquivo/`; o aviso de que o gerador "ainda gera Manus/Ollama" foi trocado por descrição do comportamento novo. Conteúdo que o Codex já tinha escrito foi mantido. |
| `tarefas_ia/chatgpt/hoje.md`, `tarefas_ia/claude/hoje.md` | Reescritos como orientação atual (004 agora; 005 é estudo visual aguardando escolha) e ponteiro para o histórico. O gerador continua acrescentando itens no fim. |
| `tarefas_ia/arquivo/chatgpt/hoje-2026-09-29.md`, `tarefas_ia/arquivo/claude/hoje-2026-09-29.md` | **Novos.** Cópia sem edição do conteúdo antigo, conferida por SHA-256 antes de reescrever os originais. |
| `tarefas_ia/arquivo/README.md` | Seção nova com o manifesto de/para e os dois SHA-256. Resto do arquivo intacto. |
| `tarefas_ia/003-organizacao-pastas.md` | Só a linha de Status: organização inicial revisada; pendências do gerador e da documentação transferidas para o 004. Relatório antigo não foi renomeado. |
| `tarefas_ia/PROMPT_CHATGPT_COORDENADOR.md` | Lê o índice atual; troca "não altere o layout antes da aprovação das frentes…" (instrução parada no tempo) por repasse local, sem commit/push sem OK, e layout só após escolha do usuário e revisão do 004. |

Revisados e **sem alteração** (nada desatualizado): `prompts/00_global.md` a `08_feedback.md` e
`prompts/README.md` (já proíbem commit sem autorização; falam de papéis, não de Manus/Ollama),
`tarefas_ia/PROMPT_CLAUDE_EXECUTOR.md`, `PROMPT_CLAUDE_004.md`, `PLANO_MESTRE_2026-09-29.md`.

## Decisões

1. **Status das filas antigas não foi deduzido.** Os 5 itens de 29/09 continuam "pendente" no
   arquivo histórico; a nova orientação diz que isso não prova o estado real. Existirem relatórios
   em `resultados/` não foi usado para marcar nada como concluído.
2. **`hoje.md` ficam no lugar** (só com conteúdo novo) porque o gerador acrescenta neles;
   diferente do Manus/Ollama, que foram movidos no 003.
3. **JSON compatível:** `modelo` foi mantido; o campo extra evita ler "Sonnet" como recomendação
   para o ChatGPT.
4. **Fim de linha:** `COORDENACAO_IA.md` e `tasks/lessons.md` (CRLF) continuam CRLF; os demais, LF.
   O `central_tarefas.py` ficou LF como os outros `.py` da pasta.
5. O Ollama do app (`app/cerebro.py` etc.), `crew.py`, `orquestrador.py`, `requirements.txt`
   e modelos não foram tocados.

## Verificações executadas (resultados reais)

1. **Gerador em pasta temporária** (cópia do script em `%TEMP%\teste004\agentes_crewai\`, apagada
   ao fim; a fila real do usuário não recebeu nada). Duas execuções, exit 0 nas duas:
   - 2 JSONs, cada um com `agentes: ["chatgpt","claude"]`; 2 cartões com exatamente dois
     agentes convidados; **2 prompts por tarefa** (`-chatgpt.md`, `-claude.md`), 4 no total.
   - Pastas criadas: só `chatgpt`, `claude`, `fila`, `prompts_prontos`, `resultados`. **Nenhuma
     pasta ou arquivo Manus/Ollama**; nenhum cartão ou prompt contém "manus"/"ollama".
   - 2ª execução (pedido diferente): IDs diferentes (`…-966829` e `…-d83920`); os dois itens
     ficaram em `chatgpt/hoje.md` e `claude/hoje.md`; todos os prompts citados existem.
   - Esforço/modelo: pedido com "painel" → alto/Opus; pedido simples → médio/Sonnet. Prompt do
     ChatGPT: "use o modelo configurado no seu app"; prompt do Claude: "Opus (Claude Code)".
2. **Sem rede/API/Ollama/CrewAI:** o gerador importa só `json, sys, uuid, datetime, pathlib`;
   busca por `requests/urllib/socket/http/crewai` no arquivo não achou nada.
3. **Arquivos preservados por SHA-256** (comparado com a lista tirada antes de editar, 59
   arquivos): `tarefas_ia/arquivo/**` (manus e ollama), `fila/`, `prompts_prontos/`,
   `resultados/`, `execucoes/`, `design/`, `crew.py`, `orquestrador.py`,
   `agentes_crewai/requirements.txt` e `resultado.md` — todos idênticos. Única diferença
   entre os demais: `arquivo/README.md`, alterado de propósito.
4. **`venv\Scripts\python -m testes.teste_basico`:** código de saída **0**;
   `Ran 147 tests in 16.619s — OK`; `VOCABULARIO: 302 de 302 frases foram para o comando certo`.
   Nenhuma falha, portanto nenhuma falha anterior a separar. (O PowerShell mostrou um
   "NativeCommandError" só porque o unittest escreve no stderr; o exit code real foi 0.)
5. **`git diff --check`:** exit 0; só avisos de conversão LF→CRLF em 3 arquivos. Como os arquivos
   novos não são rastreados, conferi espaços no fim das linhas por busca: 0 nos arquivos editados.
6. **`app/`:** `git status --short app` vazio.
7. **Referências:** conferi todo caminho entre crases nos documentos editados.
   Únicos que não existem, por motivos conhecidos:
   - caminhos antigos em `arquivo/README.md` (a coluna "onde estava" é histórica de propósito);
   - `resultados/004-fluxo-duas-ias-claude.md`: é este relatório;
   - **`design/layout-2026-09/index.html`**, citado no `README_CENTRAL.md` (linha do 005, texto
     que já estava lá). A pasta hoje tem `ESCOLHA_LAYOUT.md`, `app.css`, `app.html`,
     `inspecionar_painel.py`. Não mexi porque o Codex está escrevendo ali.

## Pendências e observações para o Codex

- **`.claude/commands/entregar` e `.agents/skills/source-command-entregar/SKILL.md`** mandam
  `git add -A` e `git commit` ao fim. Fora da lista do cartão e nenhum é "prompt geral";
  não alterei. Vale decidir se esse comando precisa pedir o "OK para publicar" antes.
- `COORDENACAO_IA.md`, seção "Estado da fila": itens 001/002/B2 são de 29/09 e não foram
  reescritos (o cartão pede para não inventar status). A nota no topo remete ao índice atual.
- O console do Git Bash mostra "di?rias" na mensagem final do gerador (página de código do
  terminal); os arquivos gravados estão em UTF-8 corretos. O comportamento já existia.
- `agentes_crewai/__pycache__` foi criado pela compilação; está no `.gitignore`.

## O que o Codex precisa conferir

1. Ler `agentes_crewai/central_tarefas.py` (poucas linhas: `AGENTES`, `recomendacao_modelo`,
   cartão e JSON) e, se quiser, repetir o teste em pasta temporária copiando o script para
   `<temp>\agentes_crewai\`: `ROOT` é sempre a pasta acima do script.
2. Que o novo ciclo em `COORDENACAO_IA.md` (repasse local, commit só com OK) representa a regra
   que o usuário quer, inclusive o ponto 6.
3. Que os `hoje.md` novos e `arquivo/README.md` (manifesto com SHA-256) atendem ao "preservar
   o conteúdo antigo com de/para".
4. Decidir os dois itens de Pendências (`entregar` e `index.html`).
5. Esta etapa **não** exige teste de voz do usuário no Windows.
