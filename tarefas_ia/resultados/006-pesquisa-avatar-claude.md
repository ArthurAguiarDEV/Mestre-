# Pesquisa e validação — avatar 2D customizável, grátis (cartão 006)

Feita em 30/09/2026 (busca na internet). Critérios do usuário: **custo grátis**, **melhor benefício para o sistema**
(Windows, Python/PySide6, PC dele), visual **liso e bonito** (não pixelado), **customizável** (homem/mulher, cabelo,
roupas, fantasias), **personalidades** com movimentos e **boca acompanhando a voz**.

## O que foi encontrado

| Projeto | O que é | Licença (segundo a busca) | Serve como base? |
|---|---|---|---|
| [Universal LPC Spritesheet Character Generator](https://github.com/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator) | Gerador de bonecos em camadas (base masculina/feminina, cabelo, roupas, armas) | Arte mista: CC0, CC-BY-SA, CC-BY, OGA-BY, GPL (exige créditos e, em parte, mesma licença) | **Não como base**: é pixel art (o usuário não quer pixels) e a licença cria obrigações. **Ideia aproveitada:** personagem em camadas |
| [Shimeji-ee](https://github.com/chaoskagami/shimeji-ee) | Mascote de área de trabalho que anda, sobe e brinca; ações definidas em XML | New BSD | **Não** (Java, sprites prontos por personagem). **Ideia aproveitada:** comportamentos por personagem (andar, parar, brincar) |
| [Open-LLM-VTuber](https://docs.llmvtuber.com/en/docs/intro/) | Companheiro por voz com avatar Live2D, modo “desktop pet” transparente, boca pela voz | Código aberto (Live2D Cubism como peça externa) | **Não** (pesado, Live2D). **Ideia aproveitada:** boca pelo volume da voz (o Assessor já enviava o volume por UDP) |
| [AIRI (moeru-ai)](https://mintlify.com/moeru-ai/airi/introduction) | Plataforma de companheiro com Live2D/VRM, olhar, piscar e animações de espera | MIT | **Não** (web/Tauri, modelos prontos). **Ideia aproveitada:** piscar, olhar para o mouse, animação de espera |
| [Amica](https://docs.heyamica.com/) | Conversa por voz com avatar 3D VRM, fala com lábios e emoções | MIT | **Não** (3D, three.js). **Ideia aproveitada:** expressões (emoção → rosto) |
| Live2D Cubism ([licença](https://www.live2d.com/en/sdk/license/)) | Padrão de avatares 2D animados | SDK gratuito para indivíduos/pequenas empresas (<10 milhões de ienes/ano), **mas proprietário**; editor grátis tem limites (1 textura 2048 px, 100 malhas) | **Não**: cada visual/fantasia precisaria ser um modelo desenhado à mão, sem troca de roupa por dados |
| [Ready Player Me](https://avatarsdk.com/blog/2026/07/07/ready-player-me-migration-guide/) | Criador de avatares 3D | **Encerrou a plataforma pública em 31/01/2026** (comprado pela Netflix) | **Não**: não existe mais |
| [DiceBear](https://www.dicebear.com/) / Avataaars | Geradores SVG de avatares (cabelo, roupa, acessórios) | MIT (DiceBear; estilos com licenças próprias) | **Não**: são retratos, sem corpo inteiro, sem gestos |
| [CharacterStudio (M3-org)](https://github.com/M3-org/CharacterStudio) | Criador de avatares VRM 3D no navegador | MIT | **Não**: 3D, precisa de modelos e three.js |
| [Inochi2D](https://www.animationandvideo.com/2023/06/inochi2d-free-open-source-2d-vtuber.html) / [Open Avatar Creator](https://github.com/Hera-Berg/open-avatar-creator) | Ferramentas abertas de rigging 2D | Apache-2.0 (Open Avatar Creator) | **Não**: exigem a arte desenhada (PSD) para cada visual |
| Rive ([runtimes](https://rive.app/docs/runtimes)) | Animação vetorial interativa com máquina de estados | Runtimes abertos; editor é serviço externo | **Não**: sem runtime em Python/PySide6 |
| [Water Companion](https://pypi.org/project/water-companion/) e similares | Mascotes de área de trabalho desenhados só com **QPainter**, sem imagens | Abertos | **Confirma a abordagem**: dá para desenhar um personagem inteiro em código no PySide6 |
| maplestory.io / arte do MapleStory | Renderizador de personagens do jogo | Arte protegida pela Nexon | **Descartado**: copiar a arte do jogo é infração; o print é só referência de estilo |

## Decisão

**Nenhum projeto grátis serve pronto**: os 2D bonitos são pixel art (LPC) ou dependem de modelos desenhados (Live2D,
Inochi2D); os que falam e têm troca de roupa são 3D/web pesados (Amica, AIRI, VRM) ou acabaram (Ready Player Me).

**Escolha: um personagem vetorial próprio, feito de DADOS** (custo zero, sem licença de terceiros, leve, no PySide6 que o
Assessor já usa), copiando só as **ideias** dos melhores:

- camadas trocáveis por peça (LPC): corpo + roupa/fantasia + cabelo + acessórios como listas de formas;
- comportamento por personagem (Shimeji): cada personalidade tem seu conjunto de gestos e seu jeito de passear;
- boca pelo volume (Open-LLM-VTuber/AIRI): o volume real da voz já chega por UDP; acrescentei as vogais da frase;
- piscar, olhar o mouse e animação de espera (AIRI), expressões por emoção (Amica).

Vantagens: um catálogo só alimenta o app (QPainter) e a página de teste (Canvas), com teste automático de que os dois
desenham o mesmo; acrescentar cabelo/roupa/herói é escrever dados; nenhuma dependência nova. Custo: a arte foi desenhada
à mão em código (estilo “chibi” liso, 224 unidades de altura, 176 px na tela).

## Cuidados de propriedade

- As **fantasias são inspiradas** (paletas e silhuetas simples), sem logotipos oficiais; personagens e marcas são dos
  donos. Uso pessoal; se o projeto for distribuído publicamente, revisar essa lista.
- Nada da arte do MapleStory foi usada (só o estilo do print como referência).
