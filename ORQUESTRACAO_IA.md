# Orquestração de IAs do Mestre

Este arquivo define o caminho oficial de uma melhoria. Ele é a fonte comum para
ChatGPT/Codex e Claude.

## Regra principal

O trabalho pode ser automatizado até a entrega para teste humano. Nenhum agente
faz commit, publica no GitHub ou integra na branch principal sem o comando explícito
do usuário: **OK para publicar**.

## Estados da melhoria

`recebido` → `refinado` → `avaliado` → `planejado` → `implementando` →
`revisando` → `testando` → `pronto_para_testar` → `aguardando_feedback` →
`corrigindo` → `pronto_para_testar`.

Se o usuário responder **OK para publicar**, o estado passa para `publicando` e,
somente então, a entrega pode ser commitada e enviada ao GitHub.

## Pacote de contexto obrigatório

Todo agente deve receber, nesta ordem:

1. `AGENTS.md` ou `CLAUDE.md`, conforme a ferramenta;
2. `COORDENACAO_IA.md`;
3. `tasks/lessons.md`;
4. este arquivo;
5. o cartão em `tarefas_ia/`;
6. apenas os arquivos necessários para a etapa atual.

O agente não deve presumir que outro chat viu uma mensagem. O que precisa ser
compartilhado deve estar em arquivo, commit ou relatório.

## Agentes e responsabilidades

| Ordem | Agente | Entrega |
|---|---|---|
| 1 | Refinador | pedido corrigido, cartões e dúvidas |
| 2 | Avaliador | nível de esforço e modelo recomendado |
| 3 | Planejador | plano técnico, arquivos e testes |
| 4 | Implementador | alteração mínima no código |
| 5 | Revisor | achados contra as regras do Mestre |
| 6 | Testador | testes automáticos e limitações do teste humano |
| 7 | Entregador | relatório para o usuário, sem publicar |
| 8 | Corretor de feedback | transforma o teste do usuário em nova tarefa |

## Como IAs externas entram

ChatGPT/Codex coordena e revisa. Claude implementa. Se não houver API ou conector,
o sistema gera um pacote de contexto para copiar/colar, sem fingir que consultou
uma IA externa.

## Regras de segurança

- Nunca salvar chaves em arquivos do projeto.
- Nunca incluir `config.yaml`, `aprendido.yaml`, logs, áudios ou histórico pessoal
  em uma entrega, salvo autorização específica.
- Nunca apagar arquivo só porque parece antigo; primeiro registrar a suspeita e
  conferir referências, testes e Git.
- Falha de teste bloqueia a entrega.
- Alteração visual fica depois da estabilização da orquestração.
