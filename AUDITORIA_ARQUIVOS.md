# Auditoria de arquivos

**Atualização de 30/09/2026:** veja [estado verificado](docs/ESTADO_ATUAL.md). Inventário, hashes e mapa dos 41 movimentos estão em `C:\Ias\auditoria-2026-09-30`. O registro de 29/09 abaixo foi preservado como histórico.

# Auditoria inicial de arquivos

Data: 2026-09-29

Esta lista é um inventário de organização, não uma autorização para apagar arquivos.

## Ativos principais

- `app/`: código do Mestre.
- `testes/`: testes automáticos.
- `ferramentas/`: atalhos e rotinas do Windows.
- `memoria/`, `tarefas_ia/`, `tasks/`: contexto e coordenação.
- `prompts/`, `ORQUESTRACAO_IA.md`: nova camada de agentes.
- `agentes_crewai/`: protótipo local do CrewAI com Ollama.

## Arquivos gerados ou pessoais que não devem entrar em commits de entrega

- `config.yaml`
- `aprendido.yaml`
- `logs/`
- `exportacoes/`
- históricos, áudios e resultados de execução

## Possíveis antigos ou duplicados

- `arquivo_morto/`: manter arquivado até confirmar referências.
- `_melhorias_claude/`: configuração ativa do Claude Code; não é arquivo morto.
- `config.exemplo.yaml`: modelo de configuração; não é configuração do usuário.
- `agentes_crewai/resultado.md`: saída gerada; pode ser limpa ou ignorada depois
  que o fluxo estiver consolidado.
- Cópias fora deste repositório em `C:\Ias\mestre*`, zips e pastas de correção:
  precisam de comparação antes de qualquer remoção.

## Próxima auditoria

Pesquisar referências e uso real de cada item antes de propor arquivamento. Nenhum
arquivo será apagado automaticamente.
