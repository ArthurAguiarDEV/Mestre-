# Plano Mestre — lapidação da validação e organização

Este plano deixa a fila preparada para Claude e ChatGPT/Codex. A execução
deve seguir a ordem abaixo. Nenhuma alteração visual ou exclusão de arquivo entra
antes das três primeiras frentes serem testadas.

## Ordem

1. Perfis e contexto dos streamings — esforço alto, Opus/Sonnet.
2. Perguntas para comandos complexos e aprendizado confirmado — esforço extra, Opus.
3. Validação dinâmica sem repetir sempre as mesmas perguntas — esforço alto, Opus.
4. Auditoria e organização de pastas — esforço alto, Opus para planejar; médio para executar.
5. Repaginação total do layout — esforço extra, Opus, somente depois da base estabilizada.

## Fluxo por frente

ChatGPT/Codex organiza e aprova o plano → Claude implementa →
ChatGPT/Codex revisa diff e testes → usuário testa → feedback volta para uma nova tarefa.

## Regra de consumo

Não usar Manus neste projeto por enquanto. Use Claude para implementação e
ChatGPT/Codex para coordenação, revisão e roteiro de teste.

## Estado atual

- Validação e mídia: implementação local sem commit, testes automáticos verdes.
- Perfis de streaming: implementados e enviados para teste humano.
- Perguntas para comandos complexos: ainda não implementadas.
- Validação variável: parcialmente implementada; precisa evitar repetição real.
- Organização de pastas: inventário iniciado, nenhum arquivo movido ou apagado.
- Layout: aguardando as frentes anteriores.
