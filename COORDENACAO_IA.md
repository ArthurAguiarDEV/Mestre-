# Passagem de tarefas entre ChatGPT/Codex e Claude

Este repositório é a fonte comum das tarefas do projeto Mestre. Uma conversa de IA não vê
automaticamente as outras conversas: o que precisa ser compartilhado fica em arquivo.

Hoje o repasse é **local, em sequência e por arquivos**: cartão, prompt e retorno ficam em
`tarefas_ia/` neste PC, e só uma IA edita o projeto por vez. Só participam o ChatGPT/Codex
(coordena e revisa) e o Claude (executa). Repasse por branch ou commit no GitHub acontece
apenas quando o usuário autorizar, para aquela entrega. O índice do dia a dia é
`tarefas_ia/README_CENTRAL.md`.

## Ciclo de uma tarefa

1. O usuário descreve o objetivo. O ChatGPT/Codex organiza um cartão em `tarefas_ia/` com
   comportamento esperado, limites e critérios verificáveis, mais o prompt para o Claude.
   O usuário aprova o cartão antes da implementação.
2. O Codex entrega ao usuário o cartão e o prompt a copiar para o Claude. Nada de commit,
   push ou branch de passagem nesta etapa.
3. O Claude lê o cartão, confere branch, HEAD e mudanças locais antes de editar e preserva o
   que já estava na cópia. Não edita arquivos que outra IA esteja editando.
4. O Claude executa os testes indicados e salva o retorno em `tarefas_ia/resultados/` com
   arquivos alterados, testes com resultado real, pendências e o estado `pronto_para_revisao`.
   Sem commit nem push, salvo autorização específica do usuário para a entrega.
5. O Codex revisa as alterações contra o cartão, confere os testes e relata falhas ou
   dúvidas. O usuário verifica no Windows o que depende de microfone, janelas ou aparência.
   Só então se decide integrar na branch principal e preparar atualização do Mestre.
6. Commit, push, branch de passagem ou integração só com o **OK para publicar** do usuário
   (veja `ORQUESTRACAO_IA.md`). A autorização vale para uma entrega; não passa para a
   seguinte. Quando houver publicação, informe a branch e o hash: um commit só local não
   aparece no GitHub.

Não tratar commit, teste automático ou resposta de IA como prova de que o comportamento
funcionou no computador do usuário. O relatório de validação deve registrar o que foi visto.

## Regras para quem recebe uma tarefa

- Leia `CLAUDE.md` ou `AGENTS.md`, `tasks/lessons.md` e o cartão. Verifique no código se o
  cartão continua válido; informe divergência antes de ampliar o escopo.
- Não inclua `config.yaml`, chaves, histórico pessoal, logs, áudios ou `aprendido.yaml` no
  commit de entrega. Preserve alterações locais que já estavam na cópia.
- Não use a branch `claude/noite-2026-09-29` como base da tarefa piloto: há mudanças parciais
  de outra etapa sem revisão. Não misture esse trabalho ao cartão 001.
- Não integre na `main`, não faça commit nem push e não publique uma versão do aplicativo
  como parte da entrega, a menos que o cartão traga essa autorização. Entregue o retorno
  em `tarefas_ia/resultados/` para revisão.
- Para mudanças de código, execute `venv\Scripts\python -m testes.teste_basico` no Windows.
  Se não houver ambiente pronto, relate o impedimento e os testes que conseguiu executar.

## Estado da fila — verificado em 30/09/2026

Fonte atual: `docs/ESTADO_ATUAL.md` e `tarefas_ia/README_CENTRAL.md`.

- 003/004: organização inicial e fluxo com duas IAs implementados e revisados.
- 005/006/007: Aurora, personagem e integração implementados. Suíte atual: 195 testes e 302 frases; verificação gráfica OK. Aceite físico pendente.
- B1+B2: a interrupção de 29/09 foi resolvida no histórico (`53087e6`, depois `1fe641b` na integração). A auditoria atual reproduziu sete falhas; não incorporar sem corrigir e revisar.
- 008: auditoria e organização global, com autorização explícita nesta conversa para arquivos, commits e GitHub. A publicação é de uma branch de revisão, não uma versão final aprovada. Essa autorização não se estende a tarefas futuras.
- Manus continua desativado; relatórios históricos preservados.

## Mensagem curta para passar a tarefa

> Leia `COORDENACAO_IA.md` e o cartão `tarefas_ia/<número>-<assunto>.md`. Confira branch,
> HEAD e mudanças locais. Implemente apenas esse cartão, execute os testes do projeto e
> salve o retorno em `tarefas_ia/resultados/`. Termine em `pronto_para_revisao` e diga o que
> devo conferir no Windows. Não faça commit nem push e não misture a etapa B2 interrompida.
