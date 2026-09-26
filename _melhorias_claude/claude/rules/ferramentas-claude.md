# Ferramentas do Claude Code neste projeto

- `/pedido [texto]`: corrigir transcricao -> refinar -> avaliar esforco de cada cartao -> esperar o ok.
- `/entregar`: teste automatico -> agente `revisor-windows` -> MELHORIAS.md [x] -> commit (se houver git) -> resumo.
- `/analisar-historico`: le o export mais recente em `exportacoes/` e propoe vocabulario, regex e frases de teste.
- Hooks (em `.claude/settings.local.json`): ao gravar, `.bat/.vbs` precisam de CRLF e sem acentos, a versao da extensao tem de bater, e `.py` nao pode ter erro de sintaxe. Ao encerrar a resposta, se codigo mudou, o teste automatico roda sozinho e o que FALHOU volta para voce corrigir.

## Economia de sessao
- Um item por sessao. Itens alto/extra: plano primeiro (plan mode), depois sessao nova para implementar em esforco medio.
- `app/comandos.py` e `app/painel.py` sao enormes: nunca leia inteiros. Use Grep pelo nome da funcao e leia so o trecho, ou peca a um subagente (Explore) para localizar.
- Nao leia `navegador_mestre/`, `venv/`, `modelos/` nem as pastas de versoes antigas em `C:\Ias`.
