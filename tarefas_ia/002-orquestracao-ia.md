# Cartão 002 — Centralizar a orquestração de IAs

## Objetivo

Criar uma fonte comum para prompts, estados, responsabilidades e limites dos
agentes que trabalham no projeto Mestre.

## Primeira entrega

- `ORQUESTRACAO_IA.md` com o ciclo oficial e a aprovação humana.
- `prompts/` com os contratos dos agentes.
- `AUDITORIA_ARQUIVOS.md` com o inventário inicial sem exclusões.

## Critérios de aceite

- [ ] Existe uma ordem única de agentes.
- [ ] Refinamento e avaliação de esforço acontecem antes da implementação.
- [ ] A entrega para o usuário acontece antes do commit.
- [ ] O feedback do usuário pode virar uma nova tarefa ligada à original.
- [ ] Nenhuma chave ou dado pessoal entra no pacote de contexto.

## Fora do escopo desta primeira entrega

- Integração automática com APIs do Claude, Manus ou GitHub.
- Alteração visual completa do painel.
- Criação dos avatares.
- Exclusão de arquivos antigos.

## Próxima etapa

Criar o coordenador executável do CrewAI, usando Ollama local e os prompts desta
pasta. Ele deverá salvar cada estado e parar em `pronto_para_testar`.
