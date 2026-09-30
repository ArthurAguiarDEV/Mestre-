# 006 — Personagem 2D no lugar do robozinho (homem/mulher, fantasias, personalidades)

Status: **pronto para revisão — 2ª rodada** (1ª: madrugada de 30/09; 2ª: manhã de 30/09, depois do feedback do dono; sem commit/push).

## 2ª rodada (manhã de 30/09): o que o dono disse e o que foi feito

**Entendi assim:** gostou da página e dos testes, era isso que esperava. Não conseguiu validar no programa (não achou o
"executável"; só validou a cópia do layout Aurora). Achou as animações um pouco travadas e o braço pouco móvel; pediu
para polir as animações e o boneco. A customização ficou boa, mas falta opção: procurar na internet e trazer mais
cabelos, mais "cabeça" (rosto) [?], mais fantasias, mais tudo.

| Cartão | Esforço · modelo | Feito |
|---|---|---|
| 1. Atalho de teste no programa | médio · Sonnet | `ferramentas/criar_teste_personagem.bat` cria `C:\Ias\Mestre-TESTE-personagem` (usa o venv/modelos daqui) + atalho **Mestre - TESTE personagem**; config da cópia com personagem + balão; o config de uso não é tocado |
| 2. Animação lisa e braço solto | alto · Opus | curva contínua entre pontos (sem parar em cada um), molas de inércia (braço, antebraço, mão, cabeça, cabelo, capa), "vida" contínua nos braços, braços da fala mudando de pose a cada trecho (`POSES_FALA`, por jeito), 9 gestos novos com os braços, página a 60 quadros/s sempre e app a 30 parado (antes 24); corrigido o antebraço direito que girava ao contrário |
| 3. Polir o boneco | alto · Opus | braço em cápsula com contorno pintado antes (cotovelo sem emenda), mão com polegar, mangas longas sem costura |
| 4. Mais variedade (pesquisa: Picrew/Charat e fantasias mais pedidas) | médio · Opus | rosto escolhível (4 formatos, 5 olhos, 5 sobrancelhas, 5 narizes, 4 bochechas), 22 cabelos (+12), 17 cores de cabelo, 9 peles, 10 cores de olho, 18 roupas (+10) em 18 cores, 27 acessórios (+17), 52 fantasias (+10 Marvel, +8 DC, +10 clássicas) |

Pronto quando (2ª rodada): [x] atalho de teste criado e conferido (o app carrega da cópia com o personagem ligado) ·
[x] suíte verde (193 testes + 302 frases) · [x] verificação Qt + paridade JS×Python (106 visuais, 184 perfis, 7.505 quadros) ·
[ ] o dono ver no Windows se ficou liso e bonito (roteiro itens 227–230).
Retorno: `tarefas_ia/resultados/006-avatar-personagem-claude.md` · Pesquisa: `tarefas_ia/resultados/006-pesquisa-avatar-claude.md`.
Nota de escopo: o cartão 005 deixava “novo avatar” fora da rodada do layout; este cartão nasce de um pedido explícito e novo do usuário.

## Entendi assim (transcrição corrigida)

O usuário mandou o print de uma interface de avatares de um jogo (bonequinhos pixelados, estilo MapleStory) e quer que os
avatares do projeto, que antes eram o robozinho, passem a ser personagens assim. Mas **sem pixels**: mais bonitos, lisos,
maiores (**uns 3× o tamanho do bonequinho do print**), e **customizáveis**: homem e mulher, cabelo, roupas, tudo que der
para personalizar, e **fantasias** de heróis (todos que der da Marvel e da DC: Homem de Ferro, Homem-Aranha,
Super-Homem, Batman, Flash…). Cada **personalidade** do Assessor tem ações diferentes: jeito de ficar na tela, movimentos,
padrões de ficar se mexendo e de falar. Quando o Assessor fala, **o boneco fala junto** (boca). Antes de implementar:
pesquisar projetos parecidos, grátis, e se houver mais de um ou dois, validar qual é o melhor (custo grátis, benefício
otimizado). Depois: passo a passo, validações e testes, **sem commit**, para ele validar de manhã. Deixar pronto um **modelo
de teste na internet** (link): o boneco aparece no canto de baixo da tela e dá para **mexer pela tela toda**.

## Por quê

O robozinho é simpático, mas o dono quer um companheiro com identidade (aparência que ele escolhe) e com vida (cada
personalidade se mexe e fala de um jeito), para o Assessor parecer um personagem de verdade.

## Como fica para o usuário

- Painel > Aparência > **Personagem**: escolhe Avatar = Personagem, monta o visual (com prévia), o jeito e o passeio.
- O personagem aparece acima do relógio (176 px de altura), pisca, olha o mouse, faz gestos, passeia conforme o jeito,
  pensa/ouve/descansa com poses próprias e fala com a boca acompanhando a voz.
- Página de teste no navegador (`design/avatar-2026-09/index.html`; também publicada como link): o mesmo boneco,
  arrastável pela tela, com fala, gestos e um trecho de config para copiar.
- O robozinho continua como padrão até ele aprovar; um clique volta para ele.

## Pronto quando

- [x] Pesquisa feita e opções comparadas (grátis, licença, custo-benefício), decisão registrada.
- [x] Personagem 2D vetorial (sem pixels), ~3× o bonequinho do print, homem e mulher.
- [x] Customização: 6 tons de pele, 7 cores de olhos, 10 cabelos × 11 cores, 8 roupas × 12 cores (3 peças), 10 acessórios, tamanho.
- [x] 24 fantasias (12 Marvel + 12 DC), incluindo Homem de Ferro, Homem-Aranha, Super-Homem, Batman e Flash.
- [x] 5 jeitos (um por personalidade do Assessor) com gestos, postura, passeio e jeito de falar próprios.
- [x] Boca sincronizada com o volume da voz e com as vogais da frase; gestos no ritmo da voz.
- [x] Passeio pela tela (parado / perto / tela toda / flutuando), nunca sai da tela, para ao falar/pensar.
- [x] Integração: `avatar > modelo`, painel (seção em Aparência), config exemplo, queda automática para o robô se der erro.
- [x] Página de teste no navegador + link publicado.
- [x] Testes automáticos (38 novos, suíte inteira verde: 185 testes + 302 frases) e verificação Qt + paridade JS×Python.
- [ ] **Validação humana no Windows** (aparência real, transparência, monitores, voz de verdade): ver o retorno.
- [ ] Decisão do usuário sobre tornar o personagem o padrão e sobre publicar (OK para publicar).

## Fora do escopo

Todos os heróis do mundo (o catálogo é dado: acrescentar um é escrever uma função em `catalogo_trajes*.py`); logotipos
oficiais; 3D/Live2D; animações prontas de terceiros; commit/push; mudar o padrão do Assessor sem o OK dele.

## Perguntas (com sugestão)

1. O personagem deve virar o **padrão** no lugar do robô? *Sugestão: sim, depois que ele aprovar a aparência.*
2. Passeio automático ligado por padrão? *Sugestão: sim (é o pedido), com “Parado no lugar” à mão no botão direito.*
3. Mais heróis/fantasias? *Sugestão: pedir os nomes; cada um leva ~30 linhas.*

## Tamanho, esforço e modelo (avaliar-esforco)

**Tamanho: grande.** NÍVEL: **extra** · MODELO: **Opus** — clareza 1 · tamanho 2 · raciocínio 2 · risco 1 · verificação 2 = 8.
Quebrado em 6 fatias (foi assim que foi feito):

| Fatia | Esforço · modelo |
|---|---|
| 1. Pesquisa e validação das opções | médio · Sonnet |
| 2. Motor de dados: corpo, cena, desenho, catálogo (cabelos, roupas, fantasias) | alto · Opus |
| 3. Animação e personalidades: clipes, boca, passeio | alto · Opus |
| 4. Janela do app + integração (avatar, main, voz, config) | médio · Sonnet |
| 5. Página de teste no navegador (link) | médio · Sonnet |
| 6. Painel, testes, guia e roteiro | médio · Sonnet |

Para gastar menos: planejar as fatias 2 e 3 em plan mode (alto) e executar as outras em Sonnet médio; dados novos
(mais heróis) são baixo/Sonnet; nunca ler `painel.py` inteiro (Grep pelo nome); usar `ferramentas/previa_personagem.py`
para ver o resultado em imagem em vez de abrir o app. Comando: `/effort xhigh` e `/model opus` só para planejar.
