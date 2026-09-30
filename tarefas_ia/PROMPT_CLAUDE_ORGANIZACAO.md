# Prompt para Claude — executar a organização segura

**Esforço:** alto
**Modelo:** Claude Opus recomendado (Sonnet basta para uma revisão documental sem movimentações extensas).

```text
Você é o executor técnico do projeto Mestre. Faça a tarefa descrita em
`tarefas_ia/003-organizacao-pastas.md`.

Antes de qualquer alteração:
1. Leia `AGENTS.md`, `CLAUDE.md`, `COORDENACAO_IA.md`, `ORQUESTRACAO_IA.md`,
   `tasks/lessons.md`, o cartão 003 e o `tarefas_ia/README_CENTRAL.md`.
2. Confira `git status` e preserve todas as mudanças locais. Não reverta nem
   sobrescreva trabalho existente.
3. Faça inventário dos arquivos e procure referências aos caminhos antes de
   mover qualquer item. Prefira manter caminhos conhecidos quando o benefício
   de mover for pequeno.

Implemente somente a organização autorizada no cartão. Arquive, não apague,
materiais antigos do Manus e filas antigas do Ollama. Mantenha o protótipo
CrewAI/Ollama intacto; ele é distinto do fluxo atual ChatGPT/Codex + Claude.
Não mova diretórios do aplicativo nem altere código funcional, layout, atalhos,
configurações pessoais, dados aprendidos ou segredos. Atualize toda referência
a um caminho que mudar. Não faça commit nem push.

Ao terminar, confira por leitura e busca que os caminhos citados existem e que
não restaram referências operacionais quebradas. Não execute a suíte de testes:
esta tarefa é documental/organizacional e não deve alterar funcionalidades.
Entregue um relatório em `tarefas_ia/resultados/003-organizacao-claude.md`
com resumo simples, arquivos movidos/arquivados/mantidos, referências
atualizadas, comandos de verificação e dúvidas/itens que preferiu não mover.
Se houver risco de sobrescrever uma alteração local ou dúvida sobre a função
de um arquivo, pare essa parte e explique no relatório; não adivinhe.
```

## Como usar

1. No Claude Code, abra o projeto `C:\Ias\Mestre-repo`.
2. Cole o texto do bloco acima.
3. Quando terminar, não peça commit/push ainda. Volte aqui e diga:
   “Claude terminou a tarefa 003; revise o relatório e diga o próximo passo.”
