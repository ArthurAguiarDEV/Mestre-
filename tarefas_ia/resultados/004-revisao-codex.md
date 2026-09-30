# Revisão do 004 — ChatGPT/Codex

Data: 30/09/2026. Base: a294459, entrega/001-validacao-variada.
Resultado: **escopo do gerador e das instruções revisado e aprovado tecnicamente**.
Não houve commit/push. O layout aguarda escolha visual do usuário.

## Evidências conferidas

- Relatório `004-fluxo-duas-ias-claude.md` e código atual de `central_tarefas.py` lidos.
- Teste independente em TemporaryDirectory: dois pedidos diferentes geraram dois cartões,
  dois JSONs e quatro prompts; exatamente ChatGPT/Codex e Claude. As duas filas conservaram
  ambos os IDs. Nenhuma pasta Manus/Ollama foi criada. Recomendações Sonnet/Opus somente
  para Claude. O teste não acrescentou tarefas à fila do usuário.
- `venv\Scripts\python -m testes.teste_basico`: exit 0; 147 testes em 17,444 s, OK;
  302/302 frases de vocabulário corretas. Esta execução não comprova microfone ou tela reais.
- A cópia continua com alterações locais e material não versionado; isso não é publicação.
- A preservação histórica por hashes anteriores à movimentação é evidência do relatório
  do Claude; não afirmo ter produzido independentemente aqueles hashes anteriores.

## Ajustes finais da revisão

O relatório apontava comandos antigos de entrega que mandavam fazer commit automaticamente.
Atualizei apenas o passo 6 em `.claude/commands/entregar.md` e seu espelho
`.agents/skills/source-command-entregar/SKILL.md`: preparar relatório/diff, exigir o
OK da entrega atual para publicar e adicionar só caminhos revisados. Nenhum comando de
entrega foi executado. Outros passos desse comando não foram usados nesta tarefa.

A pendência de `design/layout-2026-09/index.html` foi resolvida: galeria e três protótipos
foram criados pelo Codex nesta rodada. README_CENTRAL e COMECAR passam a indicar a escolha
visual como próxima ação, sem pedir que o usuário repita a execução do 004.

## Próximo passo

Usuário escolhe Órbita, Aurora ou Pulso (ou uma combinação descrita). Codex registra
`ESCOLHA_LAYOUT.md` e fecha o recorte de implementação com o prompt 005 já preparado.
Não é necessário teste de voz para aceitar a alteração do gerador.
