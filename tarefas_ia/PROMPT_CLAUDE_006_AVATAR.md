# Tarefa 006 — Personagem 2D no lugar do robozinho

Modelo: **planejar** com Claude Opus (esforço alto/extra); **executar** cada fatia com Sonnet (esforço médio).
O trabalho já foi feito na noite de 30/09 (veja o retorno); este prompt serve para **continuar/ajustar** com
o mesmo padrão: dados primeiro, um desenhista por tecnologia, testes antes de mexer em tela.

```text
Leia CLAUDE.md, tasks/lessons.md, COORDENACAO_IA.md, tarefas_ia/006-avatar-personagem.md e o retorno
tarefas_ia/resultados/006-avatar-personagem-claude.md. Confira branch, HEAD e mudanças locais antes de editar e preserve o
que já estava na cópia (outras IAs editam painel.py, layout.py e testes). Não faça commit nem push.

Objetivo: o Assessor mostra um personagem 2D liso (sem pixels, ~176 px, o triplo do bonequinho de jogo), de homem ou
mulher, customizável (pele, olhos, cabelo, roupa, acessórios, fantasias de heróis Marvel/DC), no lugar do robozinho
(opcional: avatar > modelo). Cada personalidade tem jeito próprio de ficar na tela, se mexer, passear e falar; a boca
acompanha a voz. Há uma página de teste no navegador (boneco arrastável pela tela).

Regras que valem sempre:
- Tudo é DADO. Desenho em app/personagem/catalogo_*.py (primitivas de arte.py); jeitos em catalogo_animacao.py.
  O mesmo catálogo alimenta o Qt (render_qt.py) e a página (design/avatar-2026-09/personagem.js). Depois de mexer
  no catálogo: venv\Scripts\python -m ferramentas.gerar_demo_personagem.
- Sem Qt fora de render_qt.py, janela.py e previa.py. Animador, cena, passeio e opcoes se testam sem janela.
- Cores só por arte.resolver_cor ($ficha com +/-, ou #hex). Fantasias: cores e formas próprias, sem logotipo oficial.
- Grátis, sem serviço externo. O robô continua o padrão e é a reserva se o personagem falhar.
- Um cartão por vez, uma fatia por vez. Para ver o desenho: ferramentas/previa_personagem.py (--folha trajes, --animar).

Testes: venv\Scripts\python -m testes.teste_basico (inclui testes/teste_personagem.py) e, no Windows,
venv\Scripts\python -m ferramentas.verificar_personagem (Qt + paridade JS x Python).
Termine em pronto_para_revisao, com o que o usuário deve conferir no Windows.
```
