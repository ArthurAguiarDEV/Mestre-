# Tarefa 003 — Organização segura das pastas

**Status (30/09/2026):** organização inicial executada pelo Claude e revisada pelo Codex (`tarefas_ia/resultados/003-organizacao-claude.md`). Pendências do gerador (`central_tarefas.py`) e da documentação operacional foram transferidas para o cartão 004.
**Responsável pela execução:** Claude Code
**Coordenador e revisor:** ChatGPT/Codex
**Esforço sugerido:** alto
**Modelo sugerido:** Claude Opus para auditar referências e mover arquivos com segurança; Sonnet é suficiente se o escopo for limitado a documentação.

## Objetivo

Deixar a área de coordenação de IAs fácil de entender e manter, com o fluxo atual restrito a ChatGPT/Codex (coordenação e revisão) e Claude (implementação). Arquivar materiais antigos do Manus e filas antigas do Ollama sem apagar histórico nem quebrar o protótipo CrewAI/Ollama.

## Limites e segurança

- Trabalhar somente na documentação e organização da pasta `tarefas_ia/`, mais ajustes estritamente necessários em `agentes_crewai/central_tarefas.py` para manter caminhos válidos.
- Não reorganizar pastas do aplicativo (`app/`, `testes/`, `ferramentas/`, `extensao_brave/`, `perfis/`, `prompts/`) nesta tarefa: podem ter caminhos usados em execução.
- Não alterar funcionalidades, layout, configurações pessoais, dados aprendidos, segredos ou histórico do Git.
- Não apagar arquivos. Materiais desativados devem ir para uma subpasta de arquivo histórico dentro de `tarefas_ia/`, preservando o conteúdo e atualizando referências.
- Não arquivar nem remover `.agents/`, `.codex/` ou o código do protótipo CrewAI/Ollama. Desativar Manus como agente operacional não significa apagar os relatórios antigos nem remover o protótipo local.
- Preservar todas as alterações locais já existentes; não sobrescrever arquivos modificados pelo usuário.
- Não fazer commit, push, publicação ou criação de atalho. Isso exigirá uma etapa posterior e autorização explícita.

## Entregáveis

1. Um índice simples em `tarefas_ia/README_CENTRAL.md` com: o que está ativo hoje, onde está o cartão atual, onde Claude encontra o prompt, onde salvar retorno, e o que está arquivado.
2. Uma organização coerente para cartões, prompts ativos, filas/execuções e histórico, com mudanças reversíveis e sem caminhos quebrados.
3. Agentes e instruções operacionais atuais sem Manus na fila ativa; Manus pode ser mencionado apenas em registros históricos.
4. Referências a caminhos atualizadas, inclusive no gerador do CrewAI se afetadas.
5. Relatório final com lista “movido”, “mantido”, “arquivado”, referências atualizadas e verificações executadas. Marcar explicitamente qualquer arquivo cuja função permaneça incerta, sem movê-lo.

## Critérios de aceite

- Uma pessoa não técnica consegue identificar em menos de um minuto: próxima tarefa, prompt a copiar, lugar do retorno e quem faz cada etapa.
- Nenhum arquivo foi apagado e nenhum dado/configuração pessoal foi incluído em mudanças.
- Não há referências ativas apontando para caminhos que deixaram de existir.
- O fluxo ativo identifica somente ChatGPT/Codex como coordenador/revisor e Claude como executor.
- A documentação distingue o protótipo local CrewAI/Ollama do fluxo de colaboração com IAs externas.
