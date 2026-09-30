# Retorno 007 — Revisão conjunta Aurora (005) + personagem (006)

**Estado: `pronto_para_revisao`** · Executor: Claude Code (Opus 5.5) · 30/09/2026, manhã · **Sem commit, sem push.**
Base conferida: branch `entrega/001-validacao-variada`, HEAD `a294459`; 52 alterações locais (de outras IAs e minhas) preservadas.
Lidos: `AGENTS.md`, cartões 005 e 006, `resultados/005-layout-claude.md`, `resultados/006-avatar-personagem-claude.md`.
A "auditoria do personagem no chat" citada no pedido **não chegou até mim** (não está em arquivo). Trabalhei a partir dos três pontos
nomeados no pedido e da minha própria revisão. Se a auditoria tiver outros itens, eles ainda precisam vir para cá.

## Qual cópia abrir

**`C:\Ias\Mestre-TESTE-personagem`**, pelo atalho **Mestre - TESTE personagem** da área de trabalho. É a cópia com o layout Aurora **e** o
personagem juntos, já com `avatar > modelo: "personagem"` e `indicador > tipo: "texto_avatar"`. Feche antes o outro Mestre/Assessor, porque
os dois disputam o microfone. A cópia `C:\Ias\Mestre-TESTE-layout-aurora` também ficou igual ao código atual, mas o config dela continua
com o robô, então o personagem só aparece lá se você escolher "Personagem" no painel.

## O que foi corrigido

| Ponto | Antes | Agora |
|---|---|---|
| Posição inicial | O personagem lia o `%APPDATA%\Mestre\avatar.json` do robô: uma janela de outro tamanho herdava o lugar do robô (no PC do dono, lá no alto da tela, `(1998, 38)`), e "Voltar ao lugar padrão" do personagem apagava o lugar do robô | Cada um tem o seu arquivo: o robô continua com `avatar.json` e o personagem usa `personagem.json` (`avatar.arquivo_posicao/ler_posicao/salvar_posicao(..., modelo)`; em `janela.py`, `POSICAO = "personagem"`). Sem lugar salvo, o personagem nasce no padrão, acima do relógio |
| Texto do painel | Dizia ao mesmo tempo "vale depois de reiniciar" e "muda na hora", e não avisava que com o Indicador em **Bolinha** nenhum avatar abre. Esse era o motivo de o dono não ver o personagem: o config dele está em `bolinha` | O texto agora explica: trocar Robozinho/Personagem vale depois de salvar e reiniciar; com o personagem já na tela, visual, jeito e passeio mudam segundos depois de salvar (a janela relê o config quando o arquivo muda). Aviso ao vivo, logo abaixo do "Avatar", quando Personagem + Indicador "Bolinha" estão juntos |
| Prévia do painel | A linha secundária chamava `p.after(...)` (Tkinter fora da linha principal) | A linha secundária só põe o PNG numa fila (`queue.Queue`); `colher()` roda na linha principal com `after` e aplica. Só olha a fila enquanto há prévia a caminho |
| Teclado no Aurora | No Aurora só o `CTkButton` entra no Tab. Na seção do personagem, os 10 menus, as 27 caixas de acessório e a régua do tamanho ficavam fora; as bolinhas de cor não diziam o nome | `focavel()` na seção: Tab com anel de foco; Enter/Espaço abre o menu ou marca a caixa; as setas mexem no tamanho. Cada grupo de cores mostra o nome da escolhida por escrito, e o nome da cor em foco ou sob o mouse |
| Cópias de teste | Aurora sem nenhum código do personagem (painel sem os ganchos, `main`/`voz`/`avatar` antigos); cópia do personagem sem as correções acima | As duas **iguais ao código atual** (0 diferenças em `app/`, `design/`, `ferramentas/`, `testes/`), com config, memória e escolhas de cada cópia mantidos. Nova opção `criar_teste_personagem --so-codigo <pasta>` (só age em pasta com `COPIA_DE_TESTE.txt`). Antes de sincronizar, conferi que a cópia do Aurora não tinha nada que faltasse no repositório: só faltava o personagem |

Arquivos: `app/avatar.py` (posição por modelo), `app/personagem/janela.py` (`POSICAO`), `app/painel_personagem.py` (texto, aviso, fila da
prévia, teclado, nome das cores), `ferramentas/criar_teste_personagem.py` (`--so-codigo`), `testes/teste_personagem.py` (+2 testes).
`app/painel.py` **não** foi tocado nesta rodada.

## O que foi realmente testado (aqui, no Windows)

- `venv\Scripts\python -m testes.teste_basico`: **195 testes OK + 302 de 302 frases** (48 do personagem, 2 novos: lugar do personagem
  separado do robô; a função da linha secundária da prévia não chama nada de Tk, só `put` na fila).
- `venv\Scripts\python -m ferramentas.verificar_personagem`: **TUDO CERTO**. 106 visuais, 22 cabelos, 18 roupas, 27 acessórios e 23 opções
  de rosto desenham. A janela abre nos 5 estados. JS = Python em 184/184 cenas e 7.505 quadros de animação. A página não dá erro de JS.
- **Painel Aurora inteiro, escondido, na cópia `Mestre-TESTE-personagem`** (`Painel()` + `mostrar_pagina("Aparência")`):
  - a seção monta com 20 campos;
  - o aviso aparece com Personagem + Bolinha e some com "Texto + robô";
  - a prévia foi aplicada pela linha principal (imagem presente, 0 pendentes);
  - no Tab entram 147/147 botões, 10 menus do personagem, 27 caixas e a régua;
  - as ligações de Enter/Espaço/setas existem nos controles.
- Montagem e gravação da seção no `config.exemplo.yaml` em memória: os 5 campos do rosto, cabelo e fantasia foram gravados certo.
- As duas cópias comparadas arquivo a arquivo com o repositório: 0 diferenças no código.

## O que ainda depende de você no Windows (visual ou voz)

1. Abrir **Mestre - TESTE personagem**: o personagem deve nascer **acima do relógio**, e não no alto da tela, porque agora não herda o lugar
   do robô. Depois de arrastar, ele deve voltar no mesmo lugar após reiniciar.
2. A **voz de verdade** com a boca (`Mestre, que horas são`): nunca foi testável aqui.
3. O **teclado de verdade** no painel da cópia (Aparência > Personagem): Tab passa pelos menus, caixas e tamanho, com o anel de foco
   visível; Enter abre o menu; Espaço marca a caixa; setas mudam o tamanho. Aqui só confirmei que as ligações existem, porque a janela
   escondida não recebe foco.
4. O **encaixe visual** da seção no Aurora (modo claro e noturno, 125%/150%): as cores em duas linhas com o nome embaixo, e o aviso da Bolinha.
5. Mudar o visual com o personagem na tela e **salvar**: ele troca em poucos segundos, sem reiniciar.
   Trocar Robozinho ↔ Personagem pede reinício.
6. Se ainda achar a animação travada ou o braço preso, dizer onde (parado, falando, andando): o ajuste é só de números.

## Pendências e observações

- **Acessibilidade no resto do painel Aurora:** o mesmo problema (menus, caixas e réguas fora do Tab) deve existir nas outras páginas,
  porque o remendo `_tornar_focavel` do `painel.py` só cobre `CTkButton`. Corrigi só a seção do personagem, sem mexer no `painel.py`
  (outra IA edita esse arquivo). Sugestão: levar o `focavel()` para o `painel.py` num cartão próprio.
- O personagem continua **opcional**. O padrão segue "robo" e o config de uso do dono (`bolinha`) não foi tocado.
- Commit/push só com o "OK para publicar".
