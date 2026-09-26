---
description: Organiza um pedido ditado para o Mestre - corrige a transcricao, refina em cartoes e diz o esforco certo antes de implementar
argument-hint: [pedido ditado, ou "melhorias" para usar o MELHORIAS.md]
allowed-tools: Skill, Read, AskUserQuestion
---

# Pedido: $ARGUMENTS

Se o argumento for "melhorias" (ou vazio), use os itens `- [ ]` do MELHORIAS.md.

1. Use a skill `corrigir-transcricao` e mostre "Entendi assim:".
2. Use a skill `refinar-pedido`: cartoes + ordem sugerida.
3. Use a skill `avaliar-esforco` em CADA cartao e mostre, ao lado de cada um, o nivel (baixo/medio/alto/extra) e o modelo.
4. Sugira a divisao em sessoes: itens baixo/medio juntos numa sessao; cada item alto/extra numa sessao propria, com plano (plan mode) antes.
5. PARE e espere o "ok". Nao implemente nada neste comando.
