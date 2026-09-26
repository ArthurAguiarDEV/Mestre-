---
description: Analisa o historico exportado do Mestre (exportacoes/) e propoe comandos, frases de teste e vocabulario novos
allowed-tools: Read, Glob, Grep, Skill
model: sonnet
---

# Analisar historico

1. Abra o arquivo mais recente de `exportacoes/historico_para_claude_*.md` (use Glob e pegue o de data maior).
2. Siga as 4 perguntas do cabecalho do proprio arquivo:
   frases que foram para a IA mas eram comandos simples; erros de transcricao do Whisper; frases ignoradas que pareciam chamar; os feedbacks.
3. Para cada achado, diga a CAMADA certa da correcao: vocabulario.yaml, ouvido.palavras_conhecidas, Transcritor.PROMPT, regex de `_cmd_*` ou glossario da skill corrigir-transcricao. Regex so quando for comando de YouTube/navegador ou quando vocabulario nao resolve.
4. Liste as linhas novas para `testes/frases.py` (frase -> `_cmd_*` esperado, e armadilhas).
5. Use a skill `refinar-pedido` para transformar em cartoes e ESPERE o "ok". Nao implemente neste comando.
