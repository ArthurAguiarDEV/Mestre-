> Nota da auditoria 008: este é um relato histórico de múltiplas rodadas. A primeira implementação abaixo foi superada pela segunda rodada e pelo retorno 007. Estado atual em `../../docs/ESTADO_ATUAL.md`; posição atual em `personagem.json`.

# Retorno do cartão 006 — Personagem 2D no lugar do robozinho

**Estado: `pronto_para_revisao` (2ª rodada)** · Executor: Claude Code (1ª rodada Sonnet 5.5, madrugada de 30/09; 2ª rodada Opus 5.5, manhã de 30/09)
Cartão: `tarefas_ia/006-avatar-personagem.md` · Pesquisa: `tarefas_ia/resultados/006-pesquisa-avatar-claude.md`
**Sem commit, sem push.** O padrão do Assessor continua sendo o **robozinho**: o personagem só aparece quando o dono escolher.

## 2ª rodada (manhã de 30/09): depois do feedback do dono

Base conferida: branch `entrega/001-validacao-variada`, HEAD `a294459` (o mesmo); alterações locais de outras IAs preservadas.
Nos arquivos de outras IAs mexi só em: `CLAUDE.md`/`AGENTS.md` (a linha do personagem), `GUIA_PASSO_A_PASSO.md` (seção "O personagem"),
`ROTEIRO_VALIDACAO.md` (itens `item-227` a `item-230` no grupo do personagem), `tasks/lessons.md` (+2 lições), `tarefas_ia/README_CENTRAL.md`
(linha do 006) e `config.exemplo.yaml` (5 chaves do rosto). `app/painel.py` e os testes das outras IAs **não** foram tocados nesta rodada.

**Para o dono ver primeiro**
- **No programa:** feche o Assessor e abra o atalho **Mestre - TESTE personagem** (área de trabalho). É uma cópia separada
  (`C:\Ias\Mestre-TESTE-personagem`, como a do Aurora), já com o personagem e o balão ligados; o seu Assessor e o seu config não mudam.
  Para atualizar a cópia depois de mudanças: `ferramentas\criar_teste_personagem.bat`.
- Página: `design/avatar-2026-09/index.html` (duplo clique) ou o mesmo link privado (republicado).
- Imagens novas em `design/avatar-2026-09/imagens/`: `fantasias-homem.png`/`fantasias-mulher.png` (52), `cabelos.png` (22), `roupas.png` (18),
  `acessorios.png` (27), `rosto.png` (23 opções), `gestos-novos.png`, `falando-parceiro.png`, `pensando-parceiro.png`.

**Por que estava "travado" e o que mudou na animação**
- A página só pintava 24 quadros/s com o boneco parado → agora pinta todo quadro da tela; no app o mínimo subiu de 24 para 30 (60 com movimento).
- Cada ponto-chave parava seco (suavização por trecho) → curva contínua e monotônica (não para no meio, não passa do ponto).
- Poses "seguradas" ficavam congeladas → assentam devagar + um balanço pequeno e contínuo nos braços (`VIDA`).
- **Molas de inércia** (`MOLAS`/`INERCIA` em `catalogo_animacao.py`): braço, antebraço, mão, cabeça, cabelo e capa chegam um pouco atrasados
  e balançam; capa e cabelo comprido ficam para trás ao andar (cabelo curto quase não balança: `balanco` do cabelo).
- **Braço mais solto:** falando, os braços mudam de pose a cada trecho da frase (`POSES_FALA`, cada jeito com as suas: o Parceiro abre as
  mãos e explica; o Coach aponta e conta; o Mordomo põe a mão no peito; o Sério quase não mexe). Parado, gestos novos: mãos na cintura,
  coçar a cabeça, apontar, bater palmas, joinha, mostrar o músculo, braços abertos, olhar as unhas, alongar de lado. A mão gira no punho.
- **Defeito antigo corrigido:** o antebraço e a mão do lado direito giravam ao contrário (herdavam o espelho). Por isso "braços cruzados" e
  "mão no queixo" saíam tortos. Agora o nó tem `inv` e as poses ficam simétricas.

**Boneco polido:** braço em cápsula com o contorno pintado antes dos recheios (nó com `contorno`, primitivas `c`): o cotovelo dobra sem
emenda e sem a "bolinha" de boneco articulado; mão com polegar (luvas também); mangas compridas sem costura no cotovelo.

**Mais variedade** (pesquisa rápida: criadores como Picrew/Charat separam rosto, olhos, nariz, boca, cabelo, roupa e acessórios; fantasias
mais pedidas incluem Miles, Gwen, Loki, Arlequina...):
- Rosto novo (aba Rosto na página; 5 campos no painel): formato (redondo, oval, quadrado, coração), olhos (normal, grandão, amendoado,
  pontinho, cílios longos), sobrancelhas (5), nariz (5), bochechas (rosadas, bem coradas, sardas, sem). Com fantasia, o rosto volta ao redondo
  (as máscaras foram desenhadas nele) e o olho da máscara manda.
- 22 cabelos (+ raspado, careca, moicano, coque alto, repicado, black power, dreads, ondulado, franja reta, franja de lado, trança lateral,
  dois coques); 17 cores de cabelo; 9 tons de pele; 10 cores de olho.
- 18 roupas (+ listrada, regata e bermuda, suéter, colete, jardineira, quimono, marinheiro, pijama, blusa e saia, vestido de festa) em 18 cores.
- 27 acessórios (+ máscara de baile, boina, gorro, chapéu de bruxo, coroa, tiara, faixa, orelhas de gato, chifrinhos, auréola, flor,
  presilha de estrela, colar, cachecol, gravata-borboleta, pintinha, curativo).
- 52 fantasias: +10 Marvel (Aranha Miles, Aranha Gwen, Loki, Visão, Gavião Arqueiro, Feiticeira Escarlate, Senhor das Estrelas, Simbionte,
  Tempestade, Ciclope), +8 DC (Supergirl, Batgirl, Arlequina, Asa Noturna, Hera Venenosa, Ravena, Besouro Azul, Canário Negro) e
  10 **clássicas** (pirata, ninja, astronauta, mago, cavaleiro, vampiro, bombeiro, chef, detetive, cowboy) em `catalogo_trajes_mais.py`.

**Arquivos desta rodada:** novos `app/personagem/catalogo_trajes_mais.py`, `ferramentas/criar_teste_personagem.py` + `.bat`;
alterados `app/personagem/{animacao,catalogo,catalogo_animacao,catalogo_acessorios,catalogo_cabelos,catalogo_corpo,catalogo_roupas,
catalogo_trajes,cena,janela,render_qt}.py`, `app/painel_personagem.py`, `app/personagem/opcoes.py`, `design/avatar-2026-09/{personagem.js,demo.js,index.html,artefato.html,imagens/}`,
`ferramentas/verificar_personagem.py`, `testes/teste_personagem.py` (+8 testes; 1 teste de piscar ficou mais robusto).

**Testes (resultados reais)**
- `venv\Scripts\python -m testes.teste_basico`: **193 testes OK + 302 de 302 frases** (46 do personagem).
- `venv\Scripts\python -m ferramentas.verificar_personagem`: **TUDO CERTO** — 106 visuais (52 fantasias × 2 corpos) sem mancha; 22 cabelos,
  18 roupas, 27 acessórios; cada uma das 23 opções de rosto muda o desenho; janela abre nos 5 estados; **cena JS = Python em 184/184 perfis**;
  **animação JS = Python em 7.505 quadros** (maior diferença 5,7e-14, molas incluídas); abas Fantasia (53) e Rosto (23) sem erro de JavaScript.
- Cópia de teste: o app carrega de `C:\Ias\Mestre-TESTE-personagem` com `avatar > modelo = personagem` e `indicador = texto_avatar`; prévia gerada.

**O que o dono confere no Windows (roteiro itens 227–230)**
1. Atalho **Mestre - TESTE personagem** (com o outro Assessor fechado): o personagem aparece acima do relógio.
2. Se o movimento ficou liso e o braço solto (parado, falando e andando). Se ainda achar pouco ou muito, dá para ajustar só números (molas e poses).
3. Painel da cópia > Aparência > Personagem: os 5 campos novos do rosto e as cores em duas linhas (só testei o painel escondido).
4. A voz de verdade com a boca (continua não testável aqui) e as fantasias novas na tela real.

## Para o dono ver primeiro

- Página de teste (boneco no canto de baixo da tela, arrastável por ela toda): duplo clique em
  `design/avatar-2026-09/index.html`, ou o link privado **https://claude.ai/artifact/DjjQLcdMKc39WjYPmMNATL**
  (dentro do Artefato o “canto de baixo” é o da moldura da página; se ficar estranho, use o arquivo local).
- Imagens prontas em `design/avatar-2026-09/imagens/` (24 fantasias em homem e mulher, cabelos, roupas, acessórios, poses).
- No Assessor: Painel > Aparência > **Personagem no lugar do robozinho** > Avatar = Personagem > salvar > `Mestre, reinicia`.

## Base conferida antes de editar

Branch `entrega/001-validacao-variada`, HEAD `a294459`. Já havia alterações locais de outras IAs, preservadas:
`app/painel.py` (layout Aurora), `app/avatar_janela.py`, `icones.py`, `overlay.py`, `tema.py`, `app/layout.py`, `CLAUDE.md`, `AGENTS.md`,
`GUIA_PASSO_A_PASSO.md`, `ROTEIRO_VALIDACAO.md`, `MELHORIAS.md`, `tasks/lessons.md`, `testes/teste_basico.py` e
`testes/teste_regressoes_sem_interface.py`. Nesses arquivos mexi **só** nos pontos listados abaixo. `app/avatar_janela.py` (o robô) não foi tocado.

## O que foi feito

**Arquivos novos** (tudo desenhado do zero; nenhuma dependência nova):

| Caminho | O que é |
|---|---|
| `app/personagem/arte.py`, `catalogo_corpo.py`, `catalogo_cabelos.py`, `catalogo_roupas.py`, `catalogo_trajes.py` (Marvel), `catalogo_trajes_dc.py`, `catalogo_acessorios.py`, `catalogo.py` | O catálogo, em **dados** (formas + cores em “fichas”): corpo homem/mulher, 10 cabelos, 8 roupas, **24 fantasias**, 10 acessórios |
| `app/personagem/catalogo_animacao.py` | 36 clipes de animação, 11 expressões e os **5 jeitos** (um por estilo de `personalidades.ESTILOS`) |
| `app/personagem/cena.py`, `animacao.py`, `passeio.py`, `opcoes.py` | Perfil→cena; estado→pose (piscar, olhar o mouse, gestos, boca); passeio pela tela; medidas e config. **Sem Qt** |
| `app/personagem/render_qt.py`, `janela.py`, `previa.py` | Desenhista QPainter, a janela do avatar (processo separado) e o PNG de prévia. Só aqui entra o Qt |
| `app/painel_personagem.py` | Seção “Personagem” do painel (prévia, cores, cabelo, roupa, fantasia, acessórios, tamanho, jeito, passeio) |
| `design/avatar-2026-09/` | Página de teste (`index.html`, `artefato.html`, `modelo.html`, `demo.js`, `personagem.js`), `COMECAR.md`, `imagens/` |
| `ferramentas/gerar_demo_personagem.py`, `previa_personagem.py`, `verificar_personagem.py` | Gera a página a partir do catálogo; folhas/poses em PNG; verificação Qt + navegador |
| `testes/teste_personagem.py` | 38 testes sem janela (entram na suíte principal) |
| `tarefas_ia/006-avatar-personagem.md`, `PROMPT_CLAUDE_006_AVATAR.md`, `resultados/006-*.md` | Cartão, prompt refinado, pesquisa e este retorno |

**Arquivos existentes alterados** (só o necessário):

| Arquivo | Mudança |
|---|---|
| `app/avatar.py` | `MODELOS`, `modelo_escolhido(cfg)`, `modulo_da_janela`, `iniciar(..., modelo)`, `enviar_texto(frase)` (UDP `t:<frase>`, sem efeito com o avatar desligado) |
| `app/main.py` | `_mostrar_avatar` usa o modelo escolhido; **se o personagem der erro, cai no robozinho** e só depois na bolinha |
| `app/voz.py` | +5 linhas: manda a frase falada ao avatar antes de tocar cada parte (as vogais dão a forma da boca) |
| `app/painel.py` | **2 ganchos**: `painel_personagem.montar(self, pagina)` no fim de `_aba_aparencia` e `painel_personagem.salvar(self, c)` em `_salvar_aparencia` |
| `config.exemplo.yaml` | Seção `avatar:` (modelo, jeito, passeio, personagem) com valores padrão e comentários. O `config.yaml` do dono **não foi tocado** (o código tem padrão) |
| `testes/teste_basico.py` | Inclui `teste_personagem` na suíte principal (1 import + 1 linha) |
| `testes/saidas_reais.json`, `testes/README.md` | Inventário de saídas reais revisado: +3 (`painel_personagem`: prévia por subprocess e `webbrowser.open` da página local; `janela.py`: abrir o painel), com a explicação da proteção |
| `CLAUDE.md`, `AGENTS.md` | Uma linha nova na tabela de arquivos (só o trecho novo) |
| `GUIA_PASSO_A_PASSO.md`, `ROTEIRO_VALIDACAO.md` | Seção “O personagem” na Etapa 18; grupo novo de 12 itens (ids `item-215` a `item-226`) |
| `tasks/lessons.md`, `tarefas_ia/README_CENTRAL.md` | 2 lições `erro → regra`; linha do cartão 006 na tabela |

## Como ficou (resumo do comportamento)

- **Visual:** personagem vetorial liso, estilo “chibi”, **176 px de altura** (o do print tem uns 55 px: ~3×); escala 60% a 160%.
- **Customização:** 6 tons de pele, 7 cores de olhos, 10 cabelos × 11 cores, 8 roupas (3 cores cada), 10 acessórios, tamanho.
- **Fantasias (24, inspiradas, sem logotipo):** Marvel: Homem de Ferro, Homem-Aranha, Capitão América, Thor, Hulk, Pantera Negra,
  Viúva Negra, Doutor Estranho, Deadpool, Wolverine, Capitã Marvel, Homem-Formiga. DC: Super-Homem, Batman, Mulher-Maravilha, Flash,
  Aquaman, Lanterna Verde, Arqueiro Verde, Ciborgue, Shazam, Robin, Mulher-Gato, Coringa. Cada uma em homem e mulher.
- **Jeitos por personalidade:** Parceiro brasileiro (acena, dança, pula, assobia; passeia perto), Mordomo elegante (reverência, gravata;
  quase parado), Estilo Jarvis (flutua com brilho azul, escaneia, hologramas; voa pela tela), Coach animado (soco no ar, pulos, corrida
  parada; anda rápido pela tela toda), Sério e direto (braços cruzados, olha o relógio; parado). Também dá para forçar outro jeito
  (`avatar > jeito`) e escolher o passeio (Automático, Parado, Perto, Tela toda, Livre) no painel ou no botão direito.
- **Fala:** a boca segue o **volume real da voz** e troca de forma (A E I O U, lábios fechados) a cada sílaba, usando as **vogais da
  frase**; o corpo gesticula com mais ou menos força conforme o volume. Sem volume (voz sem arquivo) ele usa uma fala simulada.
- **Vida:** pisca, olha para o mouse (o quanto depende do jeito), gestos sorteados de tempos em tempos, poses próprias para ouvindo,
  pensando (mão no queixo/hologramas + balão) e descansando (olhos fechados + zzz). Só passeia com o Assessor parado.
- **Tela:** arrastar (o lugar fica salvo no mesmo `avatar.json` do robô), clique = reação, duplo clique = painel, botão direito = menu;
  o config é relido em segundo plano: mudar o visual no painel vale na hora.
- **Desempenho:** ~1,6 ms por quadro (animação + desenho), 24 quadros/s parado e 60 só quando há movimento; nada desenha quando pausado.

## Testes (resultados reais)

- `venv\Scripts\python -m testes.teste_basico`: **185 testes OK + 302 de 302 frases** (inclui os 38 novos).
- `venv\Scripts\python -m ferramentas.verificar_personagem` (Windows, fora da barreira): **TUDO CERTO**: 50 visuais (2 corpos × fantasias)
  desenham sem mancha preta; 10 cabelos, 8 roupas, 10 acessórios; a janela abre e desenha nos 5 estados; **cena montada em JavaScript = Python
  em 128/128 perfis** e **animação JS = Python em 7.505 quadros** (maior diferença 6,8e-14).
- Janela na plataforma real (não offscreen): abre, desenha (fonte do balão ok) e o **passeio andou nos dois sentidos sem sair do monitor**.
- Painel: a seção monta num Tk escondido, gera a prévia (PNG por subprocesso) e grava `avatar > ...` no config **mantendo os comentários**.
- Página no navegador (Edge): sem erro de JavaScript, sem rolagem lateral em 375 px, arrastar e trocar de fantasia funcionam.
- Achados e corrigidos no caminho: cor fixa com sufixo (`"#3B2F38-"`) saía inválida; troca de estado quebrava a mistura de poses
  (texto “boca.v” entrando na conta); olho fechado deixava um fio no meio; capa desenhava por cima das pernas.

## O que o dono precisa conferir no Windows (não dá para provar aqui)

1. **Voz de verdade:** falar (`Mestre, que horas são`) e ver a boca acompanhando; só foi testado com volume simulado e com o teste UDP.
2. **Aparência na tela real** (transparência, 125%/150%, três monitores) e o **balão** sobre o personagem.
3. **Painel:** a seção “Personagem” em Aparência só foi montada num Tk escondido: conferir o encaixe visual (prévia ao lado, cores, menus).
4. **Passeio:** ele anda **na altura em que foi deixado** (padrão: logo acima do relógio; o `avatar.json` atual dele tem uma posição alta,
   então o passeio dele seria lá em cima). Se não gostar: “Voltar ao lugar padrão” no botão direito ou “Parado no lugar”.
5. Se mudar para o personagem e a personalidade for “Sério e direto”, ele quase não se mexe (é o jeito dessa personalidade).

## Decisões tomadas por mim (para ele aprovar ou trocar)

- Robozinho segue como padrão; o personagem é opcional (uma escolha no painel). Se o personagem falhar, volta o robô.
- Passeio **automático por personalidade** quando o personagem estiver ligado (é o que ele pediu), com “Parado no lugar” à mão.
- Fantasias **inspiradas**, sem logotipos oficiais, para uso pessoal. Se o projeto for distribuído, revisar (personagens são de terceiros).
- Não usei nada do MapleStory (só o estilo do print como referência); a pesquisa está em `006-pesquisa-avatar-claude.md`.
- O cartão 005 dizia “fora desta rodada: novo avatar”; segui o pedido novo e explícito do dono em chat.

## Pendências e ideias

- OK do dono para tornar o personagem o padrão e para publicar (commit/push só com “OK para publicar”).
- Mais heróis: cada um leva ~30 linhas (guia em `design/avatar-2026-09/COMECAR.md`).
- Possível: voz diferente por jeito, gestos ligados a eventos (erro, “obrigado”), sentar/dormir de verdade no descanso.
- `app/painel.py` e os testes estão sendo editados por outra IA ao mesmo tempo: se houver conflito, os dois ganchos do painel são os
  pontos a reaplicar (`painel_personagem.montar` e `painel_personagem.salvar`).
