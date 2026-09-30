# 005 — Escolher e implementar a nova interface do Mestre

Status: Aurora aprovada pelo usuário; pronta para implementação pelo Claude. Tarefa 004 revisada.
Frente aprovada: Aurora + detalhamento de Mídias e telas + cartão “Seu espaço, organizado” na visão geral.
Estudo: `design/layout-2026-09/index.html`.
Especificação: `design/layout-2026-09/GUIA_IMPLEMENTACAO.md`.
Escolha: `design/layout-2026-09/ESCOLHA_LAYOUT.md`.

## O que o usuário quer

No mínimo três propostas realmente diferentes de dashboard, menus, tipografia,
ícones, nomes e organização. Design limpo, legível, adaptável e com modo noturno.
Propostas concretas para escolher; depois implementar a escolhida no programa.

## Entrega de design (esta rodada)

- Órbita: painel de comando com navegação lateral e foco em estado/ações.
- Aurora: navegação horizontal, tipografia editorial e espaço para leitura.
- Pulso: estação de controle compacta, organizada por ambientes e monitores.
- Protótipos locais navegáveis com claro/escuro, busca, telas de mídia, voz e testes;
  dados demonstrativos identificados. Não conectam microfone, serviços nem comandos reais.
- Mapeamento de todas as páginas existentes, guia de integração e roteiro visual.

## Implementação aprovada

1. Usar a decisão registrada em `design/layout-2026-09/ESCOLHA_LAYOUT.md`.
2. Revisar 004 e executar o prompt `PROMPT_CLAUDE_005_LAYOUT.md`.
3. Migrar em fatias: estrutura e tema; navegação e início; agrupamento das páginas;
   validação e feedback. Manter IDs internos, configurações e funções atuais.
4. Adaptar ao CustomTkinter existente; HTML é referência visual, não novo backend.
   Não introduzir Electron, serviço web, React ou dependência paga por conta própria.
5. Validar carregamento sob demanda, salvamento apenas de páginas montadas, execução
   em segundo plano, teclado, escala 100/125/150%, janela pequena e três monitores.

## Pronto quando

- A escolha explícita está registrada e o protótipo correspondente foi respeitado.
- Todas as funcionalidades antigas continuam acessíveis; textos/ícones são claros.
- Claro/escuro e redimensionamento não ocultam controles ou avisos.
- Uma validação mostra uma ação, resultado esperado e resposta do usuário por vez.
- Testes automáticos passaram; usuário recebeu atalho de TESTE apontando para a cópia
  de validação correta, com alvo conferido, sem substituir o atalho de uso diário.
- Retorno em `tarefas_ia/resultados/005-layout-claude.md`, pronto_para_testar.

Fora desta rodada: novo avatar, novos comandos, streaming adicional, refatoração do
motor de voz, automação de publicação. Commit/push dependem de autorização própria.
