# Roteiro de validação — Assessor

Como usar: fale cada frase trocando "Mestre" pela sua palavra de ativação (ex.: **Assessor**).
Depois de qualquer mudança, fale primeiro "Mestre, reinicia". Marque `[x]` o que funcionou. O
que falhar, fale "isso tá errado, era outra coisa" logo depois: vira FEEDBACK no MELHORIAS.md
(com o áudio).

Cada linha é: `frase falada | o que deve acontecer | comando esperado (_cmd_*)`. Uma linha sem
frase pra falar (ação no painel, teste automático, checagem visual) tem `(painel)`,
`(automático)` ou `(visual)` no lugar da frase.

Na validação do painel, cada linha recebe um ID estável mesmo no formato antigo. Para manter o
mesmo ID ao reescrever uma linha, acrescente `<!-- validacao id=nome-unico tipo=fala -->` na
primeira coluna. Os tipos possíveis são `fala`, `sequencia`, `acao_manual`, `observacao`,
`pre_condicao`, `espera` e `teste_automatico`. Uma sequência de falas entre crases é conferida
etapa por etapa; pausas que completam a mesma frase continuam uma tentativa só. Instruções
manuais nunca são tratadas como frases para o microfone.

Este arquivo substitui o antigo CHECKLIST_VALIDACAO.md (o texto dele virou uma lista solta,
sem comando esperado, difícil de conferir por script; ficou só um aviso apontando pra cá).

## 1. Novidades (desta leva)

### Painel: menu lateral desliza como no protótipo B

A barra de ícones (68 px) fica sempre fixa. Os nomes e grupos ficam numa "gaveta" já montada atrás
dos ícones e só deslizam para o lado; a página não muda de tamanho nem de lugar.

| Frase/ação | O que deve acontecer | Comando esperado |
|---|---|---|
| (painel) Pare o mouse na barra de ícones por um instante | Os nomes e grupos deslizam de trás dos ícones, suaves e já prontos (sem texto aparecendo aos pedaços); a página fica parada | (painel) |
| (painel) Só passe o mouse rápido por cima da barra | Não abre | (painel) |
| (painel) Tire o mouse do menu (para a página) | Fecha deslizando; a página não se mexe | (painel) |
| (painel) Abra e feche 10 vezes seguidas; e entre/saia rápido no meio do movimento | Inverte de onde está, sem piscar, sem travar e sem deslocar a página | (painel) |
| (painel) Passe o mouse pelos itens com o menu aberto | O destaque acompanha na hora (ícone + nome num destaque só) | (painel) |
| (painel) Clique num ícone e depois num nome | Abre a página uma vez; o menu recolhe e só reabre depois que o mouse sair e voltar | (painel) |
| (painel) Depois do clique, com o mouse ainda na barra, pare em outro ícone | Aparece o balãozinho (só com o menu fechado) | (painel) |
| (painel) Janela no tamanho mínimo: gire a roda do mouse sobre os ícones ou nomes | A lista rola (ícones e nomes juntos) até "Aparência"; sem barra de rolagem grande (só um fio discreto na gaveta) | (painel) |
| (visual) Repita com o Windows em escala 125% e 150% | Ícones, nomes e destaques alinhados, nada cortado | (visual) |

### Painel > Sistema > Tempos: quanto tempo cada etapa leva

Nova página no painel que mostra a média e o pior caso das últimas 50 vezes de cada etapa: da
fala ao texto (Whisper), da frase ao comando, o tempo de cada IA configurada e o tempo até o
Assessor começar a falar. Serve para achar o que está lento.

| Frase/ação | O que deve acontecer | Comando esperado |
|---|---|---|
| (painel) Abra o painel, menu SISTEMA > "Tempos" | Mostra uma lista com etapa / média / pior caso / quantas amostras | (painel) |
| (painel) Clique em "Atualizar" | A lista atualiza sem travar o painel (lê em segundo plano) | (painel) |
| Fale algumas frases com o Assessor e volte na página "Tempos" | Depois de "Atualizar", aparecem "Fala → texto (Whisper)" e "Frase → comando" com pelo menos 1 amostra | (painel) |
| (automático) `venv\Scripts\python -m testes.teste_basico` | `tempos_resumo`/`registrar_tempo` e a página "Tempos" OK | (automático) |

### Conserto: "mover janela" pro monitor (quando falava e não acontecia nada)

Causa: quando você falava o nome do monitor colado, sem uma palavra como "no"/"pro" no meio
(ex.: "mover YouTube monitor 2"), ou dizia o número/nome ANTES da palavra "monitor" (ex.:
"...para o segundo monitor"), o Assessor não reconhecia o pedido de mover e às vezes a
"YouTube" respondia só "já estava aberto" sem trocar de monitor. Também faltava o verbo
"transfere"/"transferir".

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, mover YouTube monitor 2` (sem "pro" no meio) | Manda a janela/aba do YouTube pro monitor 2 | `_cmd_mover` |
| `Mestre, joga o YouTube monitor 2` | Mesma coisa | `_cmd_mover` |
| `Mestre, transfere a janela do YouTube pro monitor secundário` | Manda pro monitor 2 | `_cmd_mover` |
| `Mestre, transfere a tela do YouTube para o segundo monitor` (número ANTES de "monitor") | Manda pro monitor 2 | `_cmd_mover` |
| `Mestre, passa a janela do YouTube pro monitor secundário` | Manda pro monitor 2 | `_cmd_mover` |
| `Mestre, manda a Netflix pro terceiro monitor` | Manda pro monitor 3 | `_cmd_mover` |
| Se o YouTube já estiver no monitor pedido | Fala que já está lá (não fica mudo) | `_cmd_mover` / `_cmd_youtube` |
| `Mestre, abre o YouTube no monitor 2` (continua sendo ABRIR, não mover) | Abre/leva o YouTube pro monitor 2 (comportamento de sempre) | `_cmd_youtube` |
| (automático) `venv\Scripts\python -m testes.teste_basico` | Novos casos de "mover janela" sem preposição e com o nome antes de "monitor" OK | (automático) |

### Saída de som: trocar a caixinha de som pelo fone (e vice-versa)

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, coloca na caixinha de som` | Fala uma confirmação curta ("Pronto, som na caixinha." ou parecido) e o som do PC passa a sair pela caixinha Bluetooth | `_cmd_saida_som` |
| `Mestre, ativa a caixinha` | Mesma troca (é outro jeito de pedir) | `_cmd_saida_som` |
| `Mestre, volta pro fone` (ou `coloca no fone`, `agora tô usando o fone`) | O som volta a sair pelo fone de ouvido | `_cmd_saida_som` |
| `Mestre, troca a saída de som` (sem dizer qual) | Alterna: se está na caixinha vai pro fone, se está no fone vai pra caixinha | `_cmd_saida_som` |
| `Mestre, qual saída de som tá ativa?` | Fala qual das duas está tocando agora | `_cmd_saida_som` |
| Desligue o Bluetooth da caixinha e fale `Mestre, coloca na caixinha` | Avisa que a caixinha não está conectada e pra ligar o Bluetooth (não troca de verdade) | `_cmd_saida_som` |
| `Mestre, abaixa o som` / `Mestre, aumenta o volume do fone` | Continua sendo volume normal, não troca de dispositivo | `_cmd_volume` |
| (painel) **Áudio > Saída de som** | Mostra os dispositivos de som ativos, um campo de apelido pra cada um e o botão "Usar agora" | (painel) |
| (automático) `venv\Scripts\python -m testes.teste_basico` | Itens novos de saída de som (troca por apelido, alterna, não encontrado, armadilha do volume) OK | (automático) |

### Telegram: print, "o que tá tocando", vídeo curto e ligar/desligar à distância

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| (Telegram) mande `print` pro robô | Chegam as fotos, uma por monitor, com legenda "Monitor N" | (Telegram) |
| (Telegram) mande `print do monitor 2` | Chega só o print daquele monitor | (Telegram) |
| `Mestre, manda um print no Telegram` | Fala "Tirando o print..." e chegam as fotos no seu Telegram | `_cmd_print_telegram` |
| (Telegram) mande `o que tá tocando` | Responde com o que toca no Spotify, cada aba do YouTube (tocando/pausado, monitor) e a janela ativa de cada tela | (Telegram) |
| `Mestre, o que tá tocando` | Fala a mesma informação em voz alta | `_cmd_tocando` |
| (Telegram) mande `grava 15 segundos do monitor 1` | Avisa que está gravando e, depois, manda o vídeo daquele monitor | (Telegram) |
| (Telegram) mande `desligar` | Pergunta "Tem certeza que quer desligar o computador? Responda: sim." e não faz nada ainda | (Telegram) |
| (Telegram) responda `sim` | Avisa que vai desligar em 30 segundos | (Telegram) |
| (Telegram) mande `desligar` de novo e, antes do `sim`, mande `cancela` | Cancela, nada acontece | (Telegram) |
| (Telegram) mande `dormir` (ou `suspender`) e confirme com `sim` | O PC entra em suspensão depois de 30 segundos (cancelável com `cancela`) | (Telegram) |
| (Telegram) mande `reiniciar` e confirme com `sim` | O PC reinicia depois de 30 segundos (cancelável com `cancela`) | (Telegram) |
| (automático) `venv\Scripts\python -m testes.teste_basico` | Itens novos do Telegram (print, o que tá tocando, vídeo, energia) OK | (automático) |

### Avatar robô na área de trabalho + logo "Onda"

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| (visual) Reinicie: `Mestre, reinicia` | O robozinho rosa entra pulando logo acima do relógio, os olhos verdes acendem; a bolinha do topo não aparece mais | (visual) |
| `Mestre, que horas são` | Enquanto você fala: inclina a cabeça, olhos maiores, antena brilha, ondinhas. Na resposta: a boca mexe junto com a voz | `_cmd_hora_data` |
| `Mestre, me explica a teoria da relatividade` e logo `Mestre, me explica buracos negros` | Balão com pontinhos; com 2 na fila aparece o número vermelho "2" | (IA) |
| (visual) Botão direito no robô > Pausar a escuta, depois Retomar | Ele sai de cena; ao retomar volta pulando | (visual) |
| `Mestre, pode descansar` e depois `Mestre, bora voltar a trabalhar` | Olhos fechados e "zzz"; depois acorda | `_cmd_descanso` |
| (visual) Arraste o robô para outro lugar e reinicie | Ele volta no lugar novo; botão direito > Voltar ao lugar padrão leva para cima do relógio | (visual) |
| (visual) Duplo clique no robô | Abre o painel | (visual) |
| (visual) Botão direito > Esconder avatar | Some (volta ao reiniciar); o assistente continua ouvindo | (visual) |
| (visual) `Mestre, desliga` | O robô se despede (olhos apagam) e some junto | `_cmd_encerrar` |
| (painel) Aparência > Indicador na tela > Bolinha, salvar e reiniciar | Volta a bolinha de antes; trocar para "Avatar robô" traz o robô de novo | (painel) |
| (visual) Ícone do atalho, da bandeja perto do relógio e do menu do painel | É o "A" rosa com a onda verde no lugar da barra | (visual) |
| (painel) Aparência: troque a cor de destaque e aplique | O ícone e a cabeça do robô (após reiniciar) seguem a cor nova | (painel) |
| (automático) `venv\Scripts\python -m testes.teste_basico` | Itens "Avatar" e "Logo Onda" OK | (automático) |

### Painel 2.5: menu de ícones, Início em cartões e Voz em abas

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| (painel) Abra a Central pelo atalho | Abre rápido, no Início; a barra da esquerda mostra só ícones e a versão "2.5" | (painel) |
| (painel) Pare o mouse na barra de ícones da esquerda | Os nomes e os grupos deslizam suaves (sem travar) por cima da página; tire o mouse e eles recolhem | (painel) |
| (painel) Clique num ícone e pare o mouse em outro ícone | Aparece um balãozinho com o nome e o que tem na página (só com o menu fechado) | (painel) |
| (painel) Clique em várias páginas e volte a elas | A página aberta fica destacada em rosa; voltar a uma página já aberta é na hora | (painel) |
| (painel) Início, com o Assessor ligado: fale `Mestre, que horas são` | O cartão de status muda (Ouvindo → Pensando/Falando) e o comando aparece em "Últimos comandos" com OUVI / ENTENDI / FIZ, sem clicar em nada | (painel) |
| (painel) Início: `Mestre, me explica a teoria da relatividade` | A pergunta aparece em "Fila do pensando" com o tempo contando; some quando termina | (painel) |
| (painel) Início > Atalhos rápidos: Pausar, depois Retomar | O status vira "Pausado" e volta para "Ouvindo" | (painel) |
| (painel) Início > Atalhos rápidos: Validar atualização e Sugestões | Abrem as páginas certas | (painel) |
| (painel) Voz: clique nas abas Kokoro, Natural, Edge, Azure, ElevenLabs e Windows | Cada aba mostra só o daquela voz; bolinha verde = ativa, amarela = reserva | (painel) |
| (painel) Voz: numa aba, "Testar" | Fala a frase de teste com aquela voz e mostra em quantos segundos começou | (painel) |
| (painel) Voz: "Ativar esta voz" numa aba e "Usar como reserva" em outra, depois "Salvar e reiniciar" | O resumo do topo mostra "Voz ativa: X · Reserva: Y" e ele passa a falar com a ativa | (painel) |
| (painel) Aparência: troque a cor e salve | Menu, ícones e cartões usam a cor nova depois de reabrir | (painel) |

### Conversa fluida: ouvir enquanto fala, interromper e frase pela metade

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, que horas são` e, no meio da resposta, `Mestre, abre o Spotify` | A fala para na hora e o Spotify abre | `_cmd_abrir` |
| `Mestre, me conta uma curiosidade` e, no meio da resposta, `Mestre, para` | Só para de falar (não executa nada) | (ignorado: só parou de falar) |
| `Mestre, que horas são` e, enquanto ele responde, `bom dia pessoal` (sem a palavra) | Continua falando; a frase é ignorada (motivo "falando" no ouvido.jsonl) | (ignorado, sem comando) |
| `Mestre, eu queria…` (pausa de 1 s) `…que você abrisse o YouTube` | Uma ordem só: abre o YouTube | `_cmd_youtube` |
| `Mestre, abre o site do` (pausa de 1 s) `YouTube` | Junta as duas partes e abre o YouTube | `_cmd_youtube` |
| Primeira frase logo depois de ligar: `Mestre, que horas são` | Responde tão rápido quanto as outras (o Whisper já foi aquecido) | `_cmd_hora_data` |
| `Mestre, que horas são` e logo depois (sem a palavra) `e colocar isso pra eu ver pelo Telegram` | Não diz "Não conheço..." nem abre nada | (ignorado, sem comando) |
| Painel > Áudio > Ajustes de captação: "Ouvir enquanto fala", "Interromper com …", "Fala frase a frase" e "Espera se a frase parar no meio" | Os campos aparecem, salvam e valem depois de reiniciar | (painel) |

### Captação da voz (não cortar depois de "Assessor")

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre…` (pausa de 2 s) `abre o YouTube` | Não responde na pausa; junta as duas partes e abre o YouTube | `_cmd_youtube` |
| `Mestre` (sozinho, e fica quieto) | Uns 3 s depois responde curto ("Às ordens", "Ouvindo") e fica na conversa | (só chamou) |
| `que horas são` (logo depois da resposta acima, sem a palavra) | Responde a hora sem precisar chamar de novo | `_cmd_hora_data` |
| `E aí Mestre…` (pausa) `bora trabalhar` | Roda a rotina de trabalho numa frase só | `_cmd_rotinas` |
| Painel > Áudio > "Espera depois de só …" em 0 e salvar | "Mestre" sozinho volta a responder na hora | (painel) |

### Fila do "pensando" (várias perguntas seguidas sem travar)

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, o que é um buraco negro` | Indicador fica "pensando" (roxo); não fala nada ainda | (vai pensar, sem comando) |
| `Mestre, me dá uma dica de livro` (logo em seguida, sem esperar a 1ª) | Entra na fila; não trava nem repete a pergunta | (vai pensar, sem comando) |
| `Mestre, que horas são` (no meio da fila) | Responde na hora, sem esperar as duas de cima terminarem | `_cmd_hora_data` |
| `Mestre, pode falar` (depois de avisar que terminou de pensar) | Fala a resposta da pergunta pendente | `_cmd_pensamento` |
| `Mestre, o que é a Via Láctea` e depois `Mestre, cancela o pensamento` | Descarta a pergunta pendente e diz "Beleza, deixei pra lá." | `_cmd_pensamento` |

### Ensinar rotina falando

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, vou te mostrar uma nova rotina` | Indicador muda pra "gravando"; confirma que começou | `_cmd_ensinar_rotina` |
| `Mestre, abre o Gmail` (ainda gravando) | Executa normalmente E grava esse passo na rotina | `_cmd_abrir` |
| `Mestre, pronto` | Pergunta a frase pra chamar a rotina depois | `_cmd_ensinar_rotina` |
| `<sua frase, ex.: "modo revisão">` | Confirma quantos passos e frases ficaram salvos | `_cmd_ensinar_rotina` |
| `Mestre, partiu modo revisão` | Roda a rotina que você acabou de ensinar | `_cmd_rotinas` |
| `Mestre, vou te mostrar uma nova rotina` → `Mestre, abre o Spotify` → `Mestre, cancela a rotina` | Sai sem salvar nada | `_cmd_ensinar_rotina` |

### Responder só à minha voz

| Frase / ação | O que deve acontecer | Comando esperado |
|---|---|---|
| (painel) aba "Voz do dono" → gravar sua voz → Salvar | Cadastro salvo fora do projeto (`%APPDATA%\Mestre\voz_dono.json`) | (painel) |
| (painel) botão "Testar" falando uma frase qualquer | Mostra se reconheceu você (nota alta) | (painel) |
| Toque um vídeo/podcast com alguém dizendo "Mestre, ..." perto do microfone | NÃO executa (a voz não é a sua) | (ignorado, sem comando) |
| Fale você mesmo o mesmo comando logo depois | Executa normalmente | (o comando falado) |

### Voz natural: um servidor só

| Frase / ação | O que deve acontecer | Comando esperado |
|---|---|---|
| Com o Assessor ligado e a voz "Natural" escolhida, abra o painel > Voz e clique "Testar" | Não sobe um segundo processo do servidor da voz natural (confira no Gerenciador de Tarefas: só um `python.exe` de `modelos/voz_natural`) | (painel) |
| `Mestre, reinicia` com a voz "Natural" escolhida | Assim que liga, fala com a Kokoro/Edge enquanto a Natural carrega (uns 60 s na 1ª vez); depois que ela fica pronta (painel > Voz mostra "ligada"), as falas seguintes já saem na voz Natural | (o comando falado) |
| (painel) Voz > Natural > "Reinstalar" | Encerra sozinho o servidor antigo antes de baixar de novo (não trava em "Failed to remove ~orch") | (painel) |

### YouTube sem perguntar a tela (recarregue a extensão no Brave e dê F5 nas abas)

| Frase / ação | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, pausa o vídeo` (YouTube em 2 telas, só um tocando) | Pausa o que está tocando, sem perguntar a tela | `_cmd_youtube_controle` |
| `Mestre, continua o vídeo` (um pausado, mesmo que à mão) | Volta o vídeo pausado por último, sem perguntar | `_cmd_youtube_controle` |
| `Mestre, pausa o vídeo` (os dois vídeos tocando) | Pergunta "No monitor 1 ou no 2?" e usa a resposta | `_cmd_youtube_controle` |

### Validação contínua e sugestões diárias

| Frase / ação | O que deve acontecer | Comando esperado |
|---|---|---|
| (painel) Sistema > Validar atualização → deixe "Modo contínuo" marcado → Começar e fale as frases uma atrás da outra | Cada frase que dá certo ganha ✅ sozinha e a próxima aparece em ~1,5 s, sem clique; linhas (painel)/(visual) ficam de fora | (painel) |
| (painel) no modo contínuo, fale outra coisa no lugar da frase (ex.: `Mestre, abre o bloco de notas`) | Para no ❌ e mostra grande OUVI → ENTENDI (com o comando) → FIZ | (painel) |
| (painel) no modo contínuo, fale a frase SEM a palavra de ativação | Uns 4 s depois para no ❌ com DESCARTEI “...” (sem a palavra de ativação) | (painel) |
| (painel) no modo contínuo, fique uns 15 s calado | Aparece "Não ouvi nada — fale de novo ou Pular" | (painel) |
| (painel) no modo contínuo, marque "Incluir linhas de painel/visual" e comece de novo | As linhas (painel)/(visual) voltam; nelas ele para e espera você marcar ✅ ou ❌ | (painel) |
| (painel) Sistema > Sugestões de melhoria → 🔍 Analisar agora | Lista as sugestões (descartadas, caíram na IA, não entendi, repetidos, jeitos novos) em páginas de 8, com frases, horários e motivos | (painel) |
| (painel) marque 1 ou 2 sugestões → "🛠 Mandar marcadas para o Claude" | Salva `exportacoes/pedido_sugestoes_*.md` e abre o Claude Code no terminal já com o pedido | (painel) |
| (painel) Sugestões de melhoria → Horário 08:00, ligado → Salvar e reiniciar; no outro dia abra a página | "Última análise: ... (automática)" das 8h (ou de quando o PC ligou, se estava desligado) | (painel) |

### Memória da IA e modelos offline

| Frase / ação | O que deve acontecer | Comando esperado |
|---|---|---|
| `Assessor, me dá uma dica de livro` | Pensa e responde com uma dica (conversa), NÃO abre o YouTube | (vai pensar, sem comando) |
| Desligue o Wi-Fi do computador e reinicie o Assessor (`Mestre, reinicia`) | Liga normal, escuta e entende comandos (Whisper e o reconhecimento de voz sobem do que já está baixado, sem precisar de internet) | (nenhum, é o ligar) |

### Outras novidades

| Frase / ação | O que deve acontecer | Comando esperado |
|---|---|---|
| (automático) `venv\Scripts\python -m testes.teste_basico` | Linha "Nenhum erro escondido nos botões" fecha OK, teste completo 277 de 277 | (teste automático) |
| (visual) olhe o ícone perto do relógio (bandeja) | Ícone novo, na cor escolhida em Aparência | (bandeja) |
| (painel) abra o painel, ensine uma rotina nova por voz SEM fechar o painel, depois clique Salvar no painel | A rotina nova continua no config.yaml; uma rotina que você apagar no painel continua apagada | (painel) |
| (painel) Sistema > Validar atualização → "Só novidades" → Começar; fale a frase que aparece; marque ✅/❌ (no ❌ diga "o certo era") → Parar | Mostra OUVI / ENTENDI (com o comando) / FIZ de cada frase e sugere ✅/❌; no fim cria `exportacoes/validacao_AAAA-MM-DD_HHMM.md` e cada ❌ vira FEEDBACK no MELHORIAS.md | (painel) |
| (painel) depois de um relatório com falha, clique "🛠 Mandar para o Claude corrigir" | Salva o pedido em `exportacoes/pedido_correcao_*.md` e abre um terminal (Windows Terminal ou cmd) com o Claude Code interativo já com o pedido; sem falha nenhuma o botão fica desativado | (painel) |

### Memória por assunto (memoria/fatos/ em vez de um arquivo só)

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, lembra que minha esposa se chama Ana` | Guarda o fato normal ("Guardado na memória") | `_cmd_memoria` |
| `Mestre, lembra que eu trabalho na IPM de manhã` | Guarda o fato normal | `_cmd_memoria` |
| `Mestre, lembra que eu prefiro café sem açúcar` | Guarda o fato normal | `_cmd_memoria` |
| (painel) Central > Histórico > seção Memória | Em vez de uma caixa só, aparecem várias caixas menores, uma por assunto (Pessoas, Projetos, Preferências, Casa, Trabalho, Geral), cada uma com uma descrição em cima; o fato da Ana está em Pessoas, o do trabalho está em Trabalho e o do café está em Preferências | (painel) |
| (visual) confira a pasta `memoria/fatos/` do projeto | Tem um arquivo por assunto (`pessoas.md`, `projetos.md`, `preferencias.md`, `casa.md`, `trabalho.md`, `geral.md`) e um `INDICE.md` com um resumo de cada um | (visual) |
| `Mestre, o que você sabe sobre mim?` | Lê os fatos guardados, misturando os assuntos, igual antes | `_cmd_memoria` |
| `Mestre, esquece que eu prefiro café sem açúcar` | Apaga só esse fato (o da Ana e o do trabalho continuam) | `_cmd_memoria` |
| (se você já tinha uma memória antiga, de antes desta versão) reinicie o Assessor uma vez | Os fatos antigos (que estavam todos juntos em `memoria/fatos.md`) aparecem separados por assunto em `memoria/fatos/`, e o `memoria/fatos.md` antigo vira `memoria/fatos.md.antes_da_migracao` (nada se perde) | (automático, ao religar) |
| (com a IA ligada — Ollama ou Claude) `Mestre, lembra que meu cachorro se chama Bidu` e, alguns segundos depois, confira `memoria/fatos/casa.md` | O fato aparece lá (a IA pode ter ajudado a confirmar o assunto em segundo plano, sem travar a escuta) | `_cmd_memoria` |
| (automático) `venv\Scripts\python -m testes.teste_basico` | Itens de "memória por assunto" (migração, classificação, contexto pra IA, esquecer) OK | (automático) |

### Troca de IA sozinho (se uma demorar ou falhar)

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| (painel) Conversa > seção "Troca de IA sozinho (se uma demorar ou falhar)" | Aparecem os campos 1ª/2ª/3ª opção, "Modelo do Ollama menor", "Tempo por tentativa (s)", "Tempo de castigo (min)" e "Chave da API do Claude" | (painel) |
| (painel) Escolha uma ordem diferente (ex.: 1ª Claude, 2ª Ollama), salve e reabra o painel | A ordem escolhida continua marcada | (painel) |
| Feche o Ollama (ou desligue a rede dele) e, com uma 2ª opção configurada (outro modelo do Ollama ou Claude com chave salva), pergunte algo de conversa livre: `Mestre, me conta uma curiosidade` | Ele continua respondendo (pela 2ª opção), sem travar a escuta nem ficar mudo | `_cmd_pensamento` (IA) |
| Religue o Ollama e pergunte de novo antes do "tempo de castigo" passar | Continua respondendo pela 2ª opção (a 1ª ainda está de castigo) | (IA) |
| Espere passar o "tempo de castigo" configurado e pergunte de novo | Volta a tentar a 1ª opção primeiro | (IA) |
| (visual) confira `logs\mestre.log` depois de uma pergunta de conversa livre | Tem uma linha dizendo qual IA respondeu de fato | (visual) |
| (com um config.yaml antigo, de antes desta versão, sem as chaves novas) reinicie o Assessor | A IA continua respondendo normalmente pelo Ollama, do jeito de sempre (os padrões do código cobrem a falta das chaves novas) | (automático, ao religar) |
| (automático) `venv\Scripts\python -m testes.teste_basico` | Itens de "Troca de IA sozinho" (1ª lenta cai pra 2ª, castigo, castigo expira, ordem respeitada) OK | (automático) |

### Detector local da palavra (opcional, começa desligado)

| Frase / ação | O que deve acontecer | Comando esperado |
|---|---|---|
| (painel) Áudio > "Reconhecimento de voz (Whisper)" | Aparecem "Detector local da palavra" (desligado), "Exigência do detector" e a linha de situação ("Modelo pronto" ou "Modelo não encontrado") | (painel) |
| Com o detector DESLIGADO: `Assessor, que horas são?` | Responde como sempre | `_cmd_hora_data` |
| Rode `ferramentas\15_treinar_palavra.bat` (responda `s` para gravar sua voz 30 vezes) | Termina mostrando quantas das suas gravações reais ele achou e cria `modelos\palavra\assessor.npz` | (ferramenta) |
| (painel) ligue o detector > Salvar e reiniciar; depois `Assessor, que horas são?` | Responde normal (no ouvido.jsonl a frase tem `nota_detector`) | `_cmd_hora_data` |
| `Assessor` (pausa de 2 s) `abre o YouTube` | Vira uma frase só, como antes | `_cmd_abrir` |
| Deixe um vídeo com gente falando tocar 5 minutos sem chamar | Nada executa; no ouvido.jsonl os trechos aparecem com motivo "sem a palavra (detector local)" (sem transcrição) | (ignorado, sem comando) |
| Durante uma resposta longa: `Assessor, para` | Para de falar na hora (o interromper continua igual) | (só parou) |
| Na janela de conversa, logo depois de uma resposta: `e amanhã?` (sem a palavra) | Continua valendo sem a palavra | (o comando falado) |
| Modo descanso + `bora voltar a trabalhar` | Acorda normalmente | `_cmd_descanso` |
| (automático) `venv\Scripts\python -m testes.teste_basico` | Itens "Detector: ..." OK | (automático) |

### Indicador na tela: balão de texto + robô menor (novo padrão)

| Frase / ação | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, reinicia` (config sem mexer no Indicador) | Aparece o robô perto do relógio COM um balão escuro em cima, texto branco legível | (visual) |
| Fale qualquer pedido e espere ele processar | O balão muda: (some quando só ouvindo em silêncio) → "Gravando…"/"Ouvindo…" → "Pensando: <resumo do que você pediu>" → "Falando…" | (visual) |
| Peça algo que dispare a IA em segundo plano e, sem esperar, peça outra coisa | O balão de "Pensando" mostra "· Na fila: 2" (ou o número de pedidos esperando) | (visual) |
| `Mestre, pode descansar` | Balão mostra "Descansando" | `_cmd_descanso` |
| Botão direito no indicador > "Pausar a escuta" | Balão mostra "Pausado" antes de sumir | (painel/menu) |
| (painel) Aparência > "Indicador na tela" > **"Só robô"** > salvar > `Mestre, reinicia` | O robô volta ao tamanho normal, sem balão | (painel) |
| (painel) Aparência > "Indicador na tela" > **"Bolinha"** > salvar > `Mestre, reinicia` | Volta a pílula antiga (sem o robô) | (painel) |
| (automático) `venv\Scripts\python -m testes.teste_basico` | Itens "Balão: ..." (texto por estado, resumo da pergunta, fila, tamanho da janela) e "Painel: Indicador..." OK | (automático) |

## 2. Sempre testar (regressão fixa — todo dia a dia)

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, bom dia` | Roda a rotina "Bom dia" (se cadastrada) ou fica quieto se não tiver | `_cmd_rotinas` |
| `Mestre, bora trabalhar` | Roda a rotina "Bora trabalhar" (abre Gmail, Claude...) | `_cmd_rotinas` |
| `Mestre, abre o Gmail` | Abre o Gmail no navegador | `_cmd_abrir` |
| `Mestre, abre o Spotify` | Abre o PROGRAMA Spotify (não o canal do YouTube) | `_cmd_abrir` |
| `Mestre, abre o YouTube` | Abre o YouTube | `_cmd_youtube` |
| `Mestre, toca Legião Urbana no Spotify` | Toca o artista/playlist no Spotify | `_cmd_spotify` |
| `Mestre, aumenta o volume` | Sobe o volume geral | `_cmd_volume` |
| `Mestre, pausa a música` | Pausa o que estiver tocando | `_cmd_midia` |
| `Mestre, dá um like` (com um vídeo do YouTube aberto) | Curte o vídeo | `_cmd_youtube_controle` |
| `Mestre, próximo vídeo` | Pula pro próximo vídeo | `_cmd_youtube_controle` |
| `Mestre, joga essa janela pro monitor 2` | Move a janela ativa pro monitor 2 | `_cmd_mover` |
| `Mestre, minimiza tudo` | Minimiza todas as janelas | `_cmd_janela` |
| `Mestre, nova aba` | Abre uma aba nova no navegador | `_cmd_janela` |
| `Mestre, anota comprar pão` | Guarda a nota | `_cmd_notas` |
| `Mestre, vou ditar` | Começa o ditado (janela de revisão no fim) | `_cmd_ditado` |
| `Mestre, o que você acha de aprender python` | Vai pensar (fila da IA), fala ou mostra a resposta depois | (IA, sem comando) |
| `Mestre, pode descansar` | Fica quieto; só acorda com "bora voltar a trabalhar" | `_cmd_descanso` |
| `Mestre, bora voltar a trabalhar` (com ele descansando) | Acorda e volta a atender normalmente | (acorda no ouvido, sem `_cmd_`) |
| `Mestre, reinicia` | Reinicia o Assessor com as mudanças, em poucos segundos | `_cmd_reiniciar` |
| `Mestre, que horas são` | Fala a hora atual | `_cmd_hora_data` |
| `Mestre, repete` | Repete a última resposta | `_cmd_historico` |
| `Mestre, lembra que eu trabalho de manhã` | Guarda o fato pra lembrar depois | `_cmd_memoria` |
| `Mestre, abre o painel` | Abre a janela do painel | `_cmd_painel` |
| (painel) Sistema > Validar atualização | Lê este roteiro e vai perguntando cada frase, com OUVI/ENTENDI/FIZ | (painel) |
