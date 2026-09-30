# Plano Mestre — lapidação da validação e organização

Este plano deixa a fila preparada para Manus, Claude e ChatGPT/Codex. A execução
deve seguir a ordem abaixo. Nenhuma alteração visual ou exclusão de arquivo entra
antes das três primeiras frentes serem testadas.

## Ordem

1. Perfis e contexto dos streamings — esforço alto, Opus/Sonnet.
2. Perguntas para comandos complexos e aprendizado confirmado — esforço extra, Opus.
3. Validação dinâmica sem repetir sempre as mesmas perguntas — esforço alto, Opus.
4. Auditoria e organização de pastas — esforço alto, Opus para planejar; médio para executar.
5. Repaginação total do layout — esforço extra, Opus, somente depois da base estabilizada.

## Fluxo por frente

Manus faz análise somente leitura → Claude implementa o plano aprovado →
ChatGPT/Codex revisa diff e testes → usuário testa → feedback volta para uma nova tarefa.

## Regra de consumo

Não é necessário gastar Manus em cada rodada. Use Manus para decisões de arquitetura
e auditorias. Use Claude para implementação. Use ChatGPT/Codex para coordenação,
revisão e roteiro de teste. Use Ollama para análises locais simples.

## Estado atual

- Validação e mídia: implementação local sem commit, testes automáticos verdes.
- Perfis de streaming: ainda não implementados.
- Perguntas para comandos complexos: ainda não implementadas.
- Validação variável: parcialmente implementada; precisa evitar repetição real.
- Organização de pastas: inventário iniciado, nenhum arquivo movido ou apagado.
- Layout: aguardando as frentes anteriores.
