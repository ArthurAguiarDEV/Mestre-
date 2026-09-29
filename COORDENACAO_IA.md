# Passagem de tarefas entre Codex, Claude e Manus

Este repositório é a fonte comum das tarefas do projeto Mestre. Uma conversa de IA não vê
automaticamente as outras conversas. Para ler uma tarefa, ela precisa acessar a branch e o
commit indicados pelo usuário. Um commit só local também não aparece no GitHub.

## Ciclo de uma tarefa

1. O usuário descreve o objetivo. A IA organiza um cartão em `tarefas_ia/` com comportamento
   esperado, limites e critérios verificáveis. O usuário aprova o cartão antes da implementação.
2. A IA registra o cartão em commit e publica uma branch de passagem. Ela informa ao usuário
   o endereço da branch e o hash do commit. Se a publicação falhar, informa que o repasse
   ainda está apenas no PC.
3. O implementador lê o cartão **naquele commit** e confirma a base. Trabalha numa branch
   própria ou cópia isolada. Não edita uma cópia em uso por outra IA.
4. O implementador executa os testes indicados e registra suas mudanças em commit. A entrega
   traz branch, hash, arquivos alterados, testes com resultado e o que exige teste humano.
   Publica a branch de entrega para que o revisor tenha acesso ao commit.
5. Codex revisa o commit contra o cartão, confere os testes e relata falhas ou dúvidas. O
   usuário verifica no Windows o que depende de microfone, janelas ou aparência. Só então
   se decide integrar na branch principal e preparar atualização do Mestre.

Não tratar commit, teste automático ou resposta de IA como prova de que o comportamento
funcionou no computador do usuário. O relatório de validação deve registrar o que foi visto.

## Regras para quem recebe uma tarefa

- Leia `CLAUDE.md` ou `AGENTS.md`, `tasks/lessons.md` e o cartão. Verifique no código se o
  cartão continua válido; informe divergência antes de ampliar o escopo.
- Não inclua `config.yaml`, chaves, histórico pessoal, logs, áudios ou `aprendido.yaml` no
  commit de entrega. Preserve alterações locais que já estavam na cópia.
- Não use a branch `claude/noite-2026-09-29` como base da tarefa piloto: há mudanças parciais
  de outra etapa sem revisão. Não misture esse trabalho ao cartão 001.
- Não integre na `main` nem publique uma versão do aplicativo como parte da entrega do
  cartão. Entregue uma branch e um commit para revisão.
- Para mudanças de código, execute `venv\Scripts\python -m testes.teste_basico` no Windows.
  Se não houver ambiente pronto, relate o impedimento e os testes que conseguiu executar.

## Estado da fila

- **001 — Orientar testes variados na validação:** aprovado pelo usuário para iniciar o
  primeiro ciclo. Cartão em `tarefas_ia/001-validacao-variada.md`; aguarda implementação
  em branch separada e retorno do commit para revisão.
- **Etapa B2 da noite de 29/09:** interrompida com alterações sem commit na cópia do Claude;
  precisa de revisão própria antes de qualquer integração. Não faz parte da tarefa 001.
- **Layout e avatar:** permanecem para avaliação após o primeiro ciclo e uma sessão de
  testes mais ampla. Nenhum cartão de implementação foi aprovado para eles neste ciclo.

## Mensagem curta para passar a tarefa

> Leia `COORDENACAO_IA.md` e `tarefas_ia/001-validacao-variada.md` na branch e no commit
> indicados. Implemente apenas o cartão 001 em uma branch própria. Execute os testes do
> projeto. Faça um commit, publique a branch e me devolva o hash, os testes e o que devo
> conferir no Windows. Não integre na `main` nem misture a etapa B2 interrompida.
