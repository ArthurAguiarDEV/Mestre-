# 004 — Consolidar o fluxo ChatGPT/Codex + Claude

Status: executada pelo Claude e revisada pelo Codex em 30/09/2026; aprovada tecnicamente.
Revisão: `tarefas_ia/resultados/004-revisao-codex.md`. Sem commit/push.
Coordenador/revisor: ChatGPT/Codex. Executor: Claude Code.
Base inspecionada: `C:\Ias\Mestre-repo`, branch `entrega/001-validacao-variada`, HEAD `a294459`.
Prompt: `tarefas_ia/PROMPT_CLAUDE_004.md`.
Retorno: `tarefas_ia/resultados/004-fluxo-duas-ias-claude.md`.
Esforço recomendado: médio. Modelo: Sonnet disponível no Claude Code.

## Pedido refinado

Retirar Manus e Ollama da distribuição de novas tarefas e atualizar instruções antigas.
Ollama continua disponível no assistente e no protótipo local CrewAI. Não confundir
um agente destinatário de prompts com o motor de IA local usado pelo programa.

## Implementação delimitada

1. Em `agentes_crewai/central_tarefas.py`, gerar cartão, JSON, prompts e filas somente
   para `chatgpt` e `claude`. Montar a lista textual de agentes a partir da mesma
   definição de agentes usada para gerar os arquivos, evitando duas listas divergentes.
2. Manter compatibilidade com o comando atual e os caminhos de cartões/retornos.
   Não reescrever arquivos históricos nem criar pastas Manus/Ollama ao executar o gerador.
   Não remover `crew.py`, `orquestrador.py`, requirements, modelos nem integração do app com Ollama.
3. Corrigir recomendações de modelo: Sonnet/Opus pertencem ao Claude; no prompt do
   ChatGPT/Codex usar o modelo configurado no app e indicar o esforço recomendado.
   Escrever que recomendações em texto não alteram automaticamente a configuração do chat.
4. Atualizar `COORDENACAO_IA.md`, `ORQUESTRACAO_IA.md`, `tasks/lessons.md`,
   `agentes_crewai/README.md`, `tarefas_ia/README_CENTRAL.md` e os prompts gerais
   somente onde houver orientação operacional desatualizada. O repasse atual é local,
   sequencial, por arquivos. Retirar instruções conflitantes que mandam fazer commit/push
   durante o repasse sem autorização específica para a entrega atual.
5. Nas filas `chatgpt/hoje.md` e `claude/hoje.md`, preservar o conteúdo antigo em arquivo
   histórico com manifesto de/para antes de criar uma orientação atual. Não deduzir
   conclusão a partir da mera existência de relatório. Apontar para o índice atual e o
   cartão 004; o cartão 005 é estudo visual, aguardando escolha do usuário para integração.
6. Atualizar a situação documental do 003: organização inicial revisada; pendências do
   gerador/documentação transferidas para 004. Não renomear relatórios antigos desnecessariamente.

## Critérios e verificação

- Em diretório temporário, gerar uma tarefa e conferir: exatamente dois prompts, dois
  agentes no JSON/cartão e duas filas; nenhum diretório/arquivo novo para Manus/Ollama.
- Repetir com outro pedido: os dois itens permanecem nas filas; IDs diferentes e caminhos
  existentes. Não gerar lixo de teste na fila real do usuário.
- Conferir que o gerador funciona sem rede, sem API, sem iniciar Ollama/CrewAI.
- Verificar que arquivos arquivados e os dois scripts do protótipo permanecem idênticos.
- Executar `venv\Scripts\python -m testes.teste_basico` conforme regra do projeto e
  registrar código de saída/resultado real. Separar falha anterior de regressão causada.
- Conferir referências e `git diff --check`. Nenhuma alteração em `app/` nesta entrega.

## Limites

Preservar alterações locais, inclusive `MELHORIAS.md`, dados e configurações pessoais.
Não incluir segredos nos relatórios. Não editar `design/layout-2026-09/`: o Codex está
criando as propostas ali. Não executar a tarefa de layout junto com esta.
Não fazer commit, push ou mover pastas fora do escopo. A autorização de publicação
da entrega anterior não se aplica a esta entrega.

## Entrega

Relatório com arquivos, decisões, testes efetivamente executados, pendências e estado
`pronto_para_revisao`. Codex confere. Esta etapa não requer teste de voz do usuário.
Economia de contexto: ler somente os arquivos citados; executar o plano em uma sessão,
sem carregar o histórico inteiro do projeto ou pedir revisão ao Manus.
