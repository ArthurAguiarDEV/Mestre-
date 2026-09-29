# 001 — Ajudar o usuário a validar mais do que as quatro falas rápidas

**Estado:** aprovado para implementação em 29/09/2026.

## Problema relatado

O usuário entrou no menu de validação e sentiu que repetia sempre as mesmas quatro perguntas
curtas. Ele ainda não experimentou os demais modos e quer uma sessão com maior diversidade
antes de decidir novos ajustes de layout e avatar.

## Objetivo

Na página **Sistema > Validar atualização**, deixar claro, antes de começar, que o modo
Rápido tem sempre quatro falas; mostrar como usar o Direcionado para testar outras áreas;
e oferecer um próximo passo visível após concluir o Rápido. Usar os modos existentes.

## Comportamento esperado

1. Ao abrir a página, o usuário vê uma explicação curta para Rápido, Direcionado e Completo.
   A explicação diz que o Rápido repete quatro verificações essenciais e que o Direcionado
   permite escolher áreas ou usar as mudanças e falhas detectadas.
2. Ao selecionar Direcionado sem nenhuma área nova detectada ou marcada, a página avisa
   claramente que o plano ficaria só nas quatro falas essenciais e orienta a marcar grupos.
   O usuário vê a quantidade e os grupos antes de começar.
3. Depois de terminar o Rápido, a página oferece uma ação simples para escolher áreas no
   Direcionado e continuar a validação. Não inicia outra sessão sem o clique do usuário.
4. Quando o usuário marca, por exemplo, um grupo de painel e outro de voz, o plano inclui
   itens dessas áreas além das quatro falas essenciais, sem repetir o mesmo item duas vezes.
5. Rápido, Direcionado e Completo continuam gerando os relatórios atuais; um resultado de
   rota automática não deve aprovar sozinho uma ação visual ou física.

## Limites

- Não criar um quarto modo, nem sortear perguntas sem critério: o usuário deve saber o que
  será testado antes de começar.
- Não alterar a lógica dos comandos de voz, avatar ou menu lateral nesta tarefa.
- Não misturar as mudanças interrompidas da etapa B2 do Claude.
- Manter a palavra de ativação e os nomes configuráveis; evitar texto fixo "Mestre" na tela.

## Arquivos e verificação

Arquivos prováveis: `app/painel.py`, `app/validacao.py`, `GUIA_PASSO_A_PASSO.md` e testes
de regressão. Ajustar só os necessários. Conferir no teste automatizado:

- Rápido conserva as mesmas quatro falas.
- Direcionado sem área nova dá orientação explícita.
- Dois grupos marcados incluem itens dos dois grupos e não duplicam as quatro falas.
- Concluir o Rápido oferece a passagem para Direcionado sem iniciar sozinho.
- `venv\Scripts\python -m testes.teste_basico` termina com OK.

Teste humano depois da revisão: abrir a página no Windows, concluir Rápido, usar a ação
oferecida, marcar dois grupos diferentes e confirmar que aparecem itens variados e que o
relatório corresponde ao que foi feito.

## Entrega esperada do implementador

Branch e hash do commit; resumo das mudanças; resultado dos testes; passos curtos para o
usuário testar no Windows; pendências ou limites. Não integrar na `main`.
