---
description: Fecha a melhoria atual - teste automatico, revisao por outro agente, MELHORIAS.md e resumo para o usuario
allowed-tools: Agent, Bash, Read, Edit
---

# Entregar

Contrato: nao pule etapas. Se uma etapa falhar duas vezes, PARE e explique.

1. Rode `venv\Scripts\python -m testes.teste_basico`. Tudo precisa dar OK. Falhou: corrija e rode de novo.
2. Use a ferramenta Agent com `subagent_type: revisor-windows` para revisar o que mudou. Corrija os achados graves; liste os outros.
3. Se corrigiu algo no passo 2, rode o teste do passo 1 de novo.
4. Marque com `[x]` os itens atendidos no MELHORIAS.md. Atualize o GUIA_PASSO_A_PASSO.md se mudou algo que o usuario usa.
5. Atualize o `ROTEIRO_VALIDACAO.md`: na seção "Novidades", acrescente uma linha (frase | o que
   deve acontecer | comando `_cmd_*` esperado) para cada coisa nova ou corrigida nesta entrega
   que dá pra validar falando. Se o usuario pedir para comecar uma leva nova, MOVA as linhas de
   "Novidades" que ja foram validadas para um "## Historico" no fim do arquivo antes de
   acrescentar as novas (nao acumule leva antiga com a nova).
6. Se o projeto tem git (`git status` funciona): `git add -A` e `git commit` com uma mensagem curta em portugues do que mudou.
7. Resumo para o usuario, em portugues simples: o que mudou, o que ele deve testar FALANDO (frases exatas do ROTEIRO_VALIDACAO.md) depois de "Mestre, reinicia", e o que ficou pendente.
