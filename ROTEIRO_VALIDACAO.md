# Roteiro de validação — Assessor

Como usar: fale cada frase trocando "Mestre" pela sua palavra de ativação (ex.: **Assessor**).
Depois de qualquer mudança, fale primeiro "Mestre, reinicia". Marque `[x]` o que funcionou. O
que falhar, fale "isso tá errado, era outra coisa" logo depois: vira FEEDBACK no MELHORIAS.md
(com o áudio).

Cada linha é: `frase falada | o que deve acontecer | comando esperado (_cmd_*)`. Uma linha sem
frase pra falar (ação no painel, teste automático, checagem visual) tem `(painel)`,
`(automático)` ou `(visual)` no lugar da frase.

Na validação do painel, cada linha tem um ID fixo `<!-- validacao id=nome-unico -->` na
primeira coluna. Preserve esse ID ao reescrever ou mover a linha. Cada grupo tem um comentário
`<!-- validacao-grupo id=nome-unico caminhos=app/arquivo.py rotas=_cmd_exemplo -->` logo abaixo
do título. Liste apenas caminhos e rotas realmente ligados ao grupo, separados por vírgula;
sem metadados, o modo Direcionado informa o arquivo sem mapeamento e usa só as regressões
essenciais. Os tipos opcionais são `fala`, `sequencia`, `acao_manual`, `observacao`,
`pre_condicao`, `espera` e `teste_automatico`. Uma sequência de falas entre crases é conferida
etapa por etapa; pausas que completam a mesma frase continuam uma tentativa só. Instruções
manuais nunca são tratadas como frases para o microfone.
No painel, **Rápido** usa quatro falas essenciais da seção "Sempre testar", **Direcionado**
usa os arquivos alterados no Git, falhas abertas com ID e grupos escolhidos, sempre com as
quatro regressões essenciais; **Completo** inclui todas as linhas aplicáveis. Feedbacks antigos
sem ID são sinalizados até terem uma associação explícita, sem adivinhar pelo texto.

Este arquivo substitui o antigo CHECKLIST_VALIDACAO.md (o texto dele virou uma lista solta,
sem comando esperado, difícil de conferir por script; ficou só um aviso apontando pra cá).

## 1. Novidades (desta leva)

### Sugestões de 29/09: "para", print sem travar e Telegram com "mande"
<!-- validacao-grupo id=grupo-sugestoes-29-09-para-print-telegram caminhos=app/comandos/assistente.py,app/comandos/celular.py,app/recebidos.py,vocabulario.yaml -->

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, me conta uma curiosidade` e logo depois `Mestre, para` <!-- validacao id=item-178 --> | Não fala a curiosidade (descarta o que a IA ia responder) e não diz nada | `_cmd_parar` |
| Enquanto ele fala algo comprido: `Mestre, chega` <!-- validacao id=item-179 --> | Para de falar na hora | `_cmd_parar` |
| `Mestre, para o vídeo` <!-- validacao id=item-180 --> | Continua pausando o vídeo (não confunde com o "para") | `_cmd_youtube_controle` |
| `Mestre, manda um print no Telegram` e logo em seguida `Mestre, que horas são?` <!-- validacao id=item-181 --> | Responde as horas na hora (o print sobe em segundo plano, não trava mais a escuta); as fotos chegam no Telegram | `_cmd_print_telegram` |
| (Telegram) escreva `Mande print pro robô` <!-- validacao id=item-182 --> | Chegam as fotos (antes ia pro projeto no Claude) | (Telegram) |
| (Telegram) escreva `Mande desligar` e depois `cancela` <!-- validacao id=item-183 --> | Pergunta "Tem certeza...?" e depois cancela | (Telegram) |
| (Telegram) escreva `Mestre oque tá tocando` <!-- validacao id=item-184 --> | Responde no próprio Telegram o que está tocando | (Telegram) |
| (Telegram) escreva `Mestre dormir ou suspender` e depois `cancela` <!-- validacao id=item-185 --> | Pergunta "Tem certeza...?" e depois cancela | (Telegram) |

### Painel: menu lateral desliza como no protótipo B
<!-- validacao-grupo id=grupo-painel-menu-lateral-desliza-como-no-prototipo-b caminhos=app/painel.py -->

A barra de ícones (68 px) fica sempre fixa. Os nomes e grupos ficam numa "gaveta" já montada atrás
dos ícones e só deslizam para o lado; a página não muda de tamanho nem de lugar.

| Frase/ação | O que deve acontecer | Comando esperado |
|---|---|---|
| (painel) Pare o mouse na barra de ícones por um instante <!-- validacao id=item-001 --> | Os nomes e grupos deslizam de trás dos ícones, suaves e já prontos (sem texto aparecendo aos pedaços); a página fica parada | (painel) |
| (painel) Só passe o mouse rápido por cima da barra <!-- validacao id=item-002 --> | Não abre | (painel) |
| (painel) Tire o mouse do menu (para a página) <!-- validacao id=item-003 --> | Fecha deslizando; a página não se mexe | (painel) |
| (painel) Abra e feche 10 vezes seguidas; e entre/saia rápido no meio do movimento <!-- validacao id=item-004 --> | Inverte de onde está, sem piscar, sem travar e sem deslocar a página | (painel) |
| (painel) Passe o mouse pelos itens com o menu aberto <!-- validacao id=item-005 --> | O destaque acompanha na hora (ícone + nome num destaque só) | (painel) |
| (painel) Clique num ícone e depois num nome <!-- validacao id=item-006 --> | Abre a página uma vez; o menu recolhe e só reabre depois que o mouse sair e voltar | (painel) |
| (painel) Depois do clique, com o mouse ainda na barra, pare em outro ícone <!-- validacao id=item-007 --> | Aparece o balãozinho (só com o menu fechado) | (painel) |
| (painel) Janela no tamanho mínimo: gire a roda do mouse sobre os ícones ou nomes <!-- validacao id=item-008 --> | A lista rola (ícones e nomes juntos) até "Aparência"; sem barra de rolagem grande (só um fio discreto na gaveta) | (painel) |
| (visual) Repita com o Windows em escala 125% e 150% <!-- validacao id=item-009 --> | Ícones, nomes e destaques alinhados, nada cortado | (visual) |

### Painel > Sistema > Tempos: quanto tempo cada etapa leva
<!-- validacao-grupo id=grupo-painel-sistema-tempos-quanto-tempo-cada-etapa-le caminhos=app/memoria.py -->

Nova página no painel que mostra a média e o pior caso das últimas 50 vezes de cada etapa: da
fala ao texto (Whisper), da frase ao comando, o tempo de cada IA configurada e o tempo até o
Assessor começar a falar. Serve para achar o que está lento.

| Frase/ação | O que deve acontecer | Comando esperado |
|---|---|---|
| (painel) Abra o painel, menu SISTEMA > "Tempos" <!-- validacao id=item-010 --> | Mostra uma lista com etapa / média / pior caso / quantas amostras | (painel) |
| (painel) Clique em "Atualizar" <!-- validacao id=item-011 --> | A lista atualiza sem travar o painel (lê em segundo plano) | (painel) |
| Fale algumas frases com o Assessor e volte na página "Tempos" <!-- validacao id=item-012 --> | Depois de "Atualizar", aparecem "Fala → texto (Whisper)" e "Frase → comando" com pelo menos 1 amostra | (painel) |
| (automático) `venv\Scripts\python -m testes.teste_basico` <!-- validacao id=item-013 --> | `tempos_resumo`/`registrar_tempo` e a página "Tempos" OK | (automático) |

### Conserto: "mover janela" pro monitor (quando falava e não acontecia nada)
<!-- validacao-grupo id=grupo-conserto-mover-janela-pro-monitor-quando-falava- caminhos=app/comandos/janelas.py rotas=_cmd_mover,_cmd_abrir -->

Causa: quando você falava o nome do monitor colado, sem uma palavra como "no"/"pro" no meio
(ex.: "mover YouTube monitor 2"), ou dizia o número/nome ANTES da palavra "monitor" (ex.:
"...para o segundo monitor"), o Assessor não reconhecia o pedido de mover e às vezes a
"YouTube" respondia só "já estava aberto" sem trocar de monitor. Também faltava o verbo
"transfere"/"transferir".

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, mover YouTube monitor 2` (sem "pro" no meio) <!-- validacao id=item-014 --> | Manda a janela/aba do YouTube pro monitor 2 | `_cmd_mover` |
| `Mestre, joga o YouTube monitor 2` <!-- validacao id=item-015 --> | Mesma coisa | `_cmd_mover` |
| `Mestre, transfere a janela do YouTube pro monitor secundário` <!-- validacao id=item-016 --> | Manda pro monitor 2 | `_cmd_mover` |
| `Mestre, transfere a tela do YouTube para o segundo monitor` (número ANTES de "monitor") <!-- validacao id=item-017 --> | Manda pro monitor 2 | `_cmd_mover` |
| `Mestre, passa a janela do YouTube pro monitor secundário` <!-- validacao id=item-018 --> | Manda pro monitor 2 | `_cmd_mover` |
| `Mestre, manda a Netflix pro terceiro monitor` <!-- validacao id=item-019 --> | Manda pro monitor 3 | `_cmd_mover` |
| Se o YouTube já estiver no monitor pedido <!-- validacao id=item-020 --> | Fala que já está lá (não fica mudo) | `_cmd_mover` / `_cmd_youtube` |
| `Mestre, abre o YouTube no monitor 2` (continua sendo ABRIR, não mover) <!-- validacao id=item-021 --> | Abre/leva o YouTube pro monitor 2 (comportamento de sempre) | `_cmd_youtube` |
| (automático) `venv\Scripts\python -m testes.teste_basico` <!-- validacao id=item-022 --> | Novos casos de "mover janela" sem preposição e com o nome antes de "monitor" OK | (automático) |

### Saída de som: trocar a caixinha de som pelo fone (e vice-versa)
<!-- validacao-grupo id=grupo-saida-de-som-trocar-a-caixinha-de-som-pelo-fone- caminhos=app/comandos/midia.py rotas=_cmd_saida_som,_cmd_volume -->

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, coloca na caixinha de som` <!-- validacao id=item-023 --> | Fala uma confirmação curta ("Pronto, som na caixinha." ou parecido) e o som do PC passa a sair pela caixinha Bluetooth | `_cmd_saida_som` |
| `Mestre, ativa a caixinha` <!-- validacao id=item-024 --> | Mesma troca (é outro jeito de pedir) | `_cmd_saida_som` |
| `Mestre, volta pro fone` (ou `coloca no fone`, `agora tô usando o fone`) <!-- validacao id=item-025 --> | O som volta a sair pelo fone de ouvido | `_cmd_saida_som` |
| `Mestre, troca a saída de som` (sem dizer qual) <!-- validacao id=item-026 --> | Alterna: se está na caixinha vai pro fone, se está no fone vai pra caixinha | `_cmd_saida_som` |
| `Mestre, qual saída de som tá ativa?` <!-- validacao id=item-027 --> | Fala qual das duas está tocando agora | `_cmd_saida_som` |
| Desligue o Bluetooth da caixinha e fale `Mestre, coloca na caixinha` <!-- validacao id=item-028 --> | Avisa que a caixinha não está conectada e pra ligar o Bluetooth (não troca de verdade) | `_cmd_saida_som` |
| `Mestre, abaixa o som` / `Mestre, aumenta o volume do fone` <!-- validacao id=item-029 --> | Continua sendo volume normal, não troca de dispositivo | `_cmd_volume` |
| (painel) **Áudio > Saída de som** <!-- validacao id=item-030 --> | Mostra os dispositivos de som ativos, um campo de apelido pra cada um e o botão "Usar agora" | (painel) |
| (automático) `venv\Scripts\python -m testes.teste_basico` <!-- validacao id=item-031 --> | Itens novos de saída de som (troca por apelido, alterna, não encontrado, armadilha do volume) OK | (automático) |

### Telegram: print, "o que tá tocando", vídeo curto e ligar/desligar à distância
<!-- validacao-grupo id=grupo-telegram-print-o-que-ta-tocando-video-curto-e-li -->

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| (Telegram) mande `print` pro robô <!-- validacao id=item-032 --> | Chegam as fotos, uma por monitor, com legenda "Monitor N" | (Telegram) |
| (Telegram) mande `print do monitor 2` <!-- validacao id=item-033 --> | Chega só o print daquele monitor | (Telegram) |
| `Mestre, manda um print no Telegram` <!-- validacao id=item-034 --> | Fala "Tirando o print..." e chegam as fotos no seu Telegram | `_cmd_print_telegram` |
| (Telegram) mande `o que tá tocando` <!-- validacao id=item-035 --> | Responde com o que toca no Spotify, cada aba do YouTube (tocando/pausado, monitor) e a janela ativa de cada tela | (Telegram) |
| `Mestre, o que tá tocando` <!-- validacao id=item-036 --> | Fala a mesma informação em voz alta | `_cmd_tocando` |
| (Telegram) mande `grava 15 segundos do monitor 1` <!-- validacao id=item-037 --> | Avisa que está gravando e, depois, manda o vídeo daquele monitor | (Telegram) |
| (Telegram) mande `desligar` <!-- validacao id=item-038 --> | Pergunta "Tem certeza que quer desligar o computador? Responda: sim." e não faz nada ainda | (Telegram) |
| (Telegram) responda `sim` <!-- validacao id=item-039 --> | Avisa que vai desligar em 30 segundos | (Telegram) |
| (Telegram) mande `desligar` de novo e, antes do `sim`, mande `cancela` <!-- validacao id=item-040 --> | Cancela, nada acontece | (Telegram) |
| (Telegram) mande `dormir` (ou `suspender`) e confirme com `sim` <!-- validacao id=item-041 --> | O PC entra em suspensão depois de 30 segundos (cancelável com `cancela`) | (Telegram) |
| (Telegram) mande `reiniciar` e confirme com `sim` <!-- validacao id=item-042 --> | O PC reinicia depois de 30 segundos (cancelável com `cancela`) | (Telegram) |
| (automático) `venv\Scripts\python -m testes.teste_basico` <!-- validacao id=item-043 --> | Itens novos do Telegram (print, o que tá tocando, vídeo, energia) OK | (automático) |

### Avatar robô na área de trabalho + logo "Onda"
<!-- validacao-grupo id=grupo-avatar-robo-na-area-de-trabalho-logo-onda -->

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| (visual) Reinicie: `Mestre, reinicia` <!-- validacao id=item-044 --> | O robozinho rosa entra pulando logo acima do relógio, os olhos verdes acendem; a bolinha do topo não aparece mais | (visual) |
| `Mestre, que horas são` <!-- validacao id=item-045 --> | Enquanto você fala: inclina a cabeça, olhos maiores, antena brilha, ondinhas. Na resposta: a boca mexe junto com a voz | `_cmd_hora_data` |
| `Mestre, me explica a teoria da relatividade` e logo `Mestre, me explica buracos negros` <!-- validacao id=item-046 --> | Balão com pontinhos; com 2 na fila aparece o número vermelho "2" | (IA) |
| (visual) Botão direito no robô > Pausar a escuta, depois Retomar <!-- validacao id=item-047 --> | Ele sai de cena; ao retomar volta pulando | (visual) |
| `Mestre, pode descansar` e depois `Mestre, bora voltar a trabalhar` <!-- validacao id=item-048 --> | Olhos fechados e "zzz"; depois acorda | `_cmd_descanso` |
| (visual) Arraste o robô para outro lugar e reinicie <!-- validacao id=item-049 --> | Ele volta no lugar novo; botão direito > Voltar ao lugar padrão leva para cima do relógio | (visual) |
| (visual) Duplo clique no robô <!-- validacao id=item-050 --> | Abre o painel | (visual) |
| (visual) Botão direito > Esconder avatar <!-- validacao id=item-051 --> | Some (volta ao reiniciar); o assistente continua ouvindo | (visual) |
| (visual) `Mestre, desliga` <!-- validacao id=item-052 --> | O robô se despede (olhos apagam) e some junto | `_cmd_encerrar` |
| (painel) Aparência > Indicador na tela > Bolinha, salvar e reiniciar <!-- validacao id=item-053 --> | Volta a bolinha de antes; trocar para "Avatar robô" traz o robô de novo | (painel) |
| (visual) Ícone do atalho, da bandeja perto do relógio e do menu do painel <!-- validacao id=item-054 --> | É o "A" rosa com a onda verde no lugar da barra | (visual) |
| (painel) Aparência: troque a cor de destaque e aplique <!-- validacao id=item-055 --> | O ícone e a cabeça do robô (após reiniciar) seguem a cor nova | (painel) |
| (automático) `venv\Scripts\python -m testes.teste_basico` <!-- validacao id=item-056 --> | Itens "Avatar" e "Logo Onda" OK | (automático) |

### Painel 2.5: menu de ícones, Início em cartões e Voz em abas
<!-- validacao-grupo id=grupo-painel-2-5-menu-de-icones-inicio-em-cartoes-e-vo caminhos=app/painel.py -->

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| (painel) Abra a Central pelo atalho <!-- validacao id=item-057 --> | Abre rápido, no Início; a barra da esquerda mostra só ícones e a versão "2.5" | (painel) |
| (painel) Pare o mouse na barra de ícones da esquerda <!-- validacao id=item-058 --> | Os nomes e os grupos deslizam suaves (sem travar) por cima da página; tire o mouse e eles recolhem | (painel) |
| (painel) Clique num ícone e pare o mouse em outro ícone <!-- validacao id=item-059 --> | Aparece um balãozinho com o nome e o que tem na página (só com o menu fechado) | (painel) |
| (painel) Clique em várias páginas e volte a elas <!-- validacao id=item-060 --> | A página aberta fica destacada em rosa; voltar a uma página já aberta é na hora | (painel) |
| (painel) Início, com o Assessor ligado: fale `Mestre, que horas são` <!-- validacao id=item-061 --> | O cartão de status muda (Ouvindo → Pensando/Falando) e o comando aparece em "Últimos comandos" com OUVI / ENTENDI / FIZ, sem clicar em nada | (painel) |
| (painel) Início: `Mestre, me explica a teoria da relatividade` <!-- validacao id=item-062 --> | A pergunta aparece em "Fila do pensando" com o tempo contando; some quando termina | (painel) |
| (painel) Início > Atalhos rápidos: Pausar, depois Retomar <!-- validacao id=item-063 --> | O status vira "Pausado" e volta para "Ouvindo" | (painel) |
| (painel) Início > Atalhos rápidos: Validar atualização e Sugestões <!-- validacao id=item-064 --> | Abrem as páginas certas | (painel) |
| (painel) Voz: clique nas abas Kokoro, Natural, Edge, Azure, ElevenLabs e Windows <!-- validacao id=item-065 --> | Cada aba mostra só o daquela voz; bolinha verde = ativa, amarela = reserva | (painel) |
| (painel) Voz: numa aba, "Testar" <!-- validacao id=item-066 --> | Fala a frase de teste com aquela voz e mostra em quantos segundos começou | (painel) |
| (painel) Voz: "Ativar esta voz" numa aba e "Usar como reserva" em outra, depois "Salvar e reiniciar" <!-- validacao id=item-067 --> | O resumo do topo mostra "Voz ativa: X · Reserva: Y" e ele passa a falar com a ativa | (painel) |
| (painel) Aparência: troque a cor e salve <!-- validacao id=item-068 --> | Menu, ícones e cartões usam a cor nova depois de reabrir | (painel) |

### Conversa fluida: ouvir enquanto fala, interromper e frase pela metade
<!-- validacao-grupo id=grupo-conversa-fluida-ouvir-enquanto-fala-interromper- caminhos=app/ouvido.py,app/audio.py -->

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, que horas são` e, no meio da resposta, `Mestre, abre o Spotify` <!-- validacao id=item-069 --> | A fala para na hora e o Spotify abre | `_cmd_abrir` |
| `Mestre, me conta uma curiosidade` e, no meio da resposta, `Mestre, para` <!-- validacao id=item-070 --> | Só para de falar (não executa nada) | (ignorado: só parou de falar) |
| `Mestre, que horas são` e, enquanto ele responde, `bom dia pessoal` (sem a palavra) <!-- validacao id=item-071 --> | Continua falando; a frase é ignorada (motivo "falando" no ouvido.jsonl) | (ignorado, sem comando) |
| `Mestre, eu queria…` (pausa de 1 s) `…que você abrisse o YouTube` <!-- validacao id=item-072 --> | Uma ordem só: abre o YouTube | `_cmd_youtube` |
| `Mestre, abre o site do` (pausa de 1 s) `YouTube` <!-- validacao id=item-073 --> | Junta as duas partes e abre o YouTube | `_cmd_youtube` |
| Primeira frase logo depois de ligar: `Mestre, que horas são` <!-- validacao id=item-074 --> | Responde tão rápido quanto as outras (o Whisper já foi aquecido) | `_cmd_hora_data` |
| `Mestre, que horas são` e logo depois (sem a palavra) `e colocar isso pra eu ver pelo Telegram` <!-- validacao id=item-075 --> | Não diz "Não conheço..." nem abre nada | (ignorado, sem comando) |
| Painel > Áudio > Ajustes de captação: "Ouvir enquanto fala", "Interromper com …", "Fala frase a frase" e "Espera se a frase parar no meio" <!-- validacao id=item-076 --> | Os campos aparecem, salvam e valem depois de reiniciar | (painel) |

### Captação da voz (não cortar depois de "Assessor")
<!-- validacao-grupo id=grupo-captacao-da-voz-nao-cortar-depois-de-assessor caminhos=app/ouvido.py,app/audio.py -->

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre…` (pausa de 2 s) `abre o YouTube` <!-- validacao id=item-077 --> | Não responde na pausa; junta as duas partes e abre o YouTube | `_cmd_youtube` |
| `Mestre` (sozinho, e fica quieto) <!-- validacao id=item-078 --> | Uns 3 s depois responde curto ("Às ordens", "Ouvindo") e fica na conversa | (só chamou) |
| `que horas são` (logo depois da resposta acima, sem a palavra) <!-- validacao id=item-079 --> | Responde a hora sem precisar chamar de novo | `_cmd_hora_data` |
| `E aí Mestre…` (pausa) `bora trabalhar` <!-- validacao id=item-080 --> | Roda a rotina de trabalho numa frase só | `_cmd_rotinas` |
| Painel > Áudio > "Espera depois de só …" em 0 e salvar <!-- validacao id=item-081 --> | "Mestre" sozinho volta a responder na hora | (painel) |

### Fila do "pensando" (várias perguntas seguidas sem travar)
<!-- validacao-grupo id=grupo-fila-do-pensando-varias-perguntas-seguidas-sem-t caminhos=app/comandos/ia.py rotas=_cmd_pensamento -->

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, o que é um buraco negro` <!-- validacao id=item-082 --> | Indicador fica "pensando" (roxo); não fala nada ainda | (vai pensar, sem comando) |
| `Mestre, me dá uma dica de livro` (logo em seguida, sem esperar a 1ª) <!-- validacao id=item-083 --> | Entra na fila; não trava nem repete a pergunta | (vai pensar, sem comando) |
| `Mestre, que horas são` (no meio da fila) <!-- validacao id=item-084 --> | Responde na hora, sem esperar as duas de cima terminarem | `_cmd_hora_data` |
| `Mestre, pode falar` (depois de avisar que terminou de pensar) <!-- validacao id=item-085 --> | Fala a resposta da pergunta pendente | `_cmd_pensamento` |
| `Mestre, o que é a Via Láctea` e depois `Mestre, cancela o pensamento` <!-- validacao id=item-086 --> | Descarta a pergunta pendente e diz "Beleza, deixei pra lá." | `_cmd_pensamento` |

### Ensinar rotina falando
<!-- validacao-grupo id=grupo-ensinar-rotina-falando caminhos=app/comandos/rotinas.py rotas=_cmd_ensinar_rotina -->

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, vou te mostrar uma nova rotina` <!-- validacao id=item-087 --> | Indicador muda pra "gravando"; confirma que começou | `_cmd_ensinar_rotina` |
| `Mestre, abre o Gmail` (ainda gravando) <!-- validacao id=item-088 --> | Executa normalmente E grava esse passo na rotina | `_cmd_abrir` |
| `Mestre, pronto` <!-- validacao id=item-089 --> | Pergunta a frase pra chamar a rotina depois | `_cmd_ensinar_rotina` |
| `<sua frase, ex.: "modo revisão">` <!-- validacao id=item-090 --> | Confirma quantos passos e frases ficaram salvos | `_cmd_ensinar_rotina` |
| `Mestre, partiu modo revisão` <!-- validacao id=item-091 --> | Roda a rotina que você acabou de ensinar | `_cmd_rotinas` |
| `Mestre, vou te mostrar uma nova rotina` → `Mestre, abre o Spotify` → `Mestre, cancela a rotina` <!-- validacao id=item-092 --> | Sai sem salvar nada | `_cmd_ensinar_rotina` |

### Responder só à minha voz
<!-- validacao-grupo id=grupo-responder-so-a-minha-voz -->

| Frase / ação | O que deve acontecer | Comando esperado |
|---|---|---|
| (painel) aba "Voz do dono" → gravar sua voz → Salvar <!-- validacao id=item-093 --> | Cadastro salvo fora do projeto (`%APPDATA%\Mestre\voz_dono.json`) | (painel) |
| (painel) botão "Testar" falando uma frase qualquer <!-- validacao id=item-094 --> | Mostra se reconheceu você (nota alta) | (painel) |
| Toque um vídeo/podcast com alguém dizendo "Mestre, ..." perto do microfone <!-- validacao id=item-095 --> | NÃO executa (a voz não é a sua) | (ignorado, sem comando) |
| Fale você mesmo o mesmo comando logo depois <!-- validacao id=item-096 --> | Executa normalmente | (o comando falado) |

### Voz natural: um servidor só
<!-- validacao-grupo id=grupo-voz-natural-um-servidor-so -->

| Frase / ação | O que deve acontecer | Comando esperado |
|---|---|---|
| Com o Assessor ligado e a voz "Natural" escolhida, abra o painel > Voz e clique "Testar" <!-- validacao id=item-097 --> | Não sobe um segundo processo do servidor da voz natural (confira no Gerenciador de Tarefas: só um `python.exe` de `modelos/voz_natural`) | (painel) |
| `Mestre, reinicia` com a voz "Natural" escolhida <!-- validacao id=item-098 --> | Assim que liga, fala com a Kokoro/Edge enquanto a Natural carrega (uns 60 s na 1ª vez); depois que ela fica pronta (painel > Voz mostra "ligada"), as falas seguintes já saem na voz Natural | (o comando falado) |
| (painel) Voz > Natural > "Reinstalar" <!-- validacao id=item-099 --> | Encerra sozinho o servidor antigo antes de baixar de novo (não trava em "Failed to remove ~orch") | (painel) |

### YouTube sem perguntar a tela (recarregue a extensão no Brave e dê F5 nas abas)
<!-- validacao-grupo id=grupo-youtube-sem-perguntar-a-tela-recarregue-a-extens -->

| Frase / ação | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, pausa o vídeo` (YouTube em 2 telas, só um tocando) <!-- validacao id=item-100 --> | Pausa o que está tocando, sem perguntar a tela | `_cmd_youtube_controle` |
| `Mestre, continua o vídeo` (um pausado, mesmo que à mão) <!-- validacao id=item-101 --> | Volta o vídeo pausado por último, sem perguntar | `_cmd_youtube_controle` |
| `Mestre, pausa o vídeo` (os dois vídeos tocando) <!-- validacao id=item-102 --> | Pergunta "No monitor 1 ou no 2?" e usa a resposta | `_cmd_youtube_controle` |

### Validação contínua e sugestões diárias
<!-- validacao-grupo id=grupo-validacao-continua-e-sugestoes-diarias caminhos=app/validacao.py,app/sugestoes.py,app/painel.py -->

| Frase / ação | O que deve acontecer | Comando esperado |
|---|---|---|
| (painel) Sistema > Validar atualização → deixe "Modo contínuo" marcado → Começar e fale as frases uma atrás da outra <!-- validacao id=item-103 --> | Cada frase que dá certo ganha ✅ sozinha e a próxima aparece em ~1,5 s, sem clique; linhas (painel)/(visual) ficam de fora | (painel) |
| (painel) no modo contínuo, fale outra coisa no lugar da frase (ex.: `Mestre, abre o bloco de notas`) <!-- validacao id=item-104 --> | Para no ❌ e mostra grande OUVI → ENTENDI (com o comando) → FIZ | (painel) |
| (painel) no modo contínuo, fale a frase SEM a palavra de ativação <!-- validacao id=item-105 --> | Uns 4 s depois para no ❌ com DESCARTEI “...” (sem a palavra de ativação) | (painel) |
| (painel) no modo contínuo, fique uns 15 s calado <!-- validacao id=item-106 --> | Aparece "Não ouvi nada — fale de novo ou Pular" | (painel) |
| (painel) no modo contínuo, marque "Incluir linhas de painel/visual" e comece de novo <!-- validacao id=item-107 --> | As linhas (painel)/(visual) voltam; nelas ele para e espera você marcar ✅ ou ❌ | (painel) |
| (painel) Sistema > Sugestões de melhoria → 🔍 Analisar agora <!-- validacao id=item-108 --> | Lista as sugestões (descartadas, caíram na IA, não entendi, repetidos, jeitos novos) em páginas de 8, com frases, horários e motivos | (painel) |
| (painel) marque 1 ou 2 sugestões → "🛠 Mandar marcadas para o Claude" <!-- validacao id=item-109 --> | Salva `exportacoes/pedido_sugestoes_*.md` e abre o Claude Code no terminal já com o pedido | (painel) |
| (painel) Sugestões de melhoria → Horário 08:00, ligado → Salvar e reiniciar; no outro dia abra a página <!-- validacao id=item-110 --> | "Última análise: ... (automática)" das 8h (ou de quando o PC ligou, se estava desligado) | (painel) |

### Memória da IA e modelos offline
<!-- validacao-grupo id=grupo-memoria-da-ia-e-modelos-offline caminhos=app/comandos/ia.py,app/memoria.py rotas=_cmd_pensamento -->

| Frase / ação | O que deve acontecer | Comando esperado |
|---|---|---|
| `Assessor, me dá uma dica de livro` <!-- validacao id=item-111 --> | Pensa e responde com uma dica (conversa), NÃO abre o YouTube | (vai pensar, sem comando) |
| Desligue o Wi-Fi do computador e reinicie o Assessor (`Mestre, reinicia`) <!-- validacao id=item-112 --> | Liga normal, escuta e entende comandos (Whisper e o reconhecimento de voz sobem do que já está baixado, sem precisar de internet) | (nenhum, é o ligar) |

### Outras novidades
<!-- validacao-grupo id=grupo-outras-novidades -->

| Frase / ação | O que deve acontecer | Comando esperado |
|---|---|---|
| (automático) `venv\Scripts\python -m testes.teste_basico` <!-- validacao id=item-113 --> | Linha "Nenhum erro escondido nos botões" fecha OK, teste completo 277 de 277 | (teste automático) |
| (visual) olhe o ícone perto do relógio (bandeja) <!-- validacao id=item-114 --> | Ícone novo, na cor escolhida em Aparência | (bandeja) |
| (painel) abra o painel, ensine uma rotina nova por voz SEM fechar o painel, depois clique Salvar no painel <!-- validacao id=item-115 --> | A rotina nova continua no config.yaml; uma rotina que você apagar no painel continua apagada | (painel) |
| (painel) Sistema > Validar atualização → "Só novidades" → Começar; fale a frase que aparece; marque ✅/❌ (no ❌ diga "o certo era") → Parar <!-- validacao id=item-116 --> | Mostra OUVI / ENTENDI (com o comando) / FIZ de cada frase e sugere ✅/❌; no fim cria `exportacoes/validacao_AAAA-MM-DD_HHMM.md` e cada ❌ vira FEEDBACK no MELHORIAS.md | (painel) |
| (painel) depois de um relatório com falha, clique "🛠 Mandar para o Claude corrigir" <!-- validacao id=item-117 --> | Salva o pedido em `exportacoes/pedido_correcao_*.md` e abre um terminal (Windows Terminal ou cmd) com o Claude Code interativo já com o pedido; sem falha nenhuma o botão fica desativado | (painel) |

### Memória por assunto (memoria/fatos/ em vez de um arquivo só)
<!-- validacao-grupo id=grupo-memoria-por-assunto-memoria-fatos-em-vez-de-um-a caminhos=app/memoria.py rotas=_cmd_memoria -->

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, lembra que minha esposa se chama Ana` <!-- validacao id=item-118 --> | Guarda o fato normal ("Guardado na memória") | `_cmd_memoria` |
| `Mestre, lembra que eu trabalho na IPM de manhã` <!-- validacao id=item-119 --> | Guarda o fato normal | `_cmd_memoria` |
| `Mestre, lembra que eu prefiro café sem açúcar` <!-- validacao id=item-120 --> | Guarda o fato normal | `_cmd_memoria` |
| (painel) Central > Histórico > seção Memória <!-- validacao id=item-121 --> | Em vez de uma caixa só, aparecem várias caixas menores, uma por assunto (Pessoas, Projetos, Preferências, Casa, Trabalho, Geral), cada uma com uma descrição em cima; o fato da Ana está em Pessoas, o do trabalho está em Trabalho e o do café está em Preferências | (painel) |
| (visual) confira a pasta `memoria/fatos/` do projeto <!-- validacao id=item-122 --> | Tem um arquivo por assunto (`pessoas.md`, `projetos.md`, `preferencias.md`, `casa.md`, `trabalho.md`, `geral.md`) e um `INDICE.md` com um resumo de cada um | (visual) |
| `Mestre, o que você sabe sobre mim?` <!-- validacao id=item-123 --> | Lê os fatos guardados, misturando os assuntos, igual antes | `_cmd_memoria` |
| `Mestre, esquece que eu prefiro café sem açúcar` <!-- validacao id=item-124 --> | Apaga só esse fato (o da Ana e o do trabalho continuam) | `_cmd_memoria` |
| (se você já tinha uma memória antiga, de antes desta versão) reinicie o Assessor uma vez <!-- validacao id=item-125 --> | Os fatos antigos (que estavam todos juntos em `memoria/fatos.md`) aparecem separados por assunto em `memoria/fatos/`, e o `memoria/fatos.md` antigo vira `memoria/fatos.md.antes_da_migracao` (nada se perde) | (automático, ao religar) |
| (com a IA ligada — Ollama ou Claude) `Mestre, lembra que meu cachorro se chama Bidu` e, alguns segundos depois, confira `memoria/fatos/casa.md` <!-- validacao id=item-126 --> | O fato aparece lá (a IA pode ter ajudado a confirmar o assunto em segundo plano, sem travar a escuta) | `_cmd_memoria` |
| (automático) `venv\Scripts\python -m testes.teste_basico` <!-- validacao id=item-127 --> | Itens de "memória por assunto" (migração, classificação, contexto pra IA, esquecer) OK | (automático) |

### Troca de IA sozinho (se uma demorar ou falhar)
<!-- validacao-grupo id=grupo-troca-de-ia-sozinho-se-uma-demorar-ou-falhar -->

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| (painel) Conversa > seção "Troca de IA sozinho (se uma demorar ou falhar)" <!-- validacao id=item-128 --> | Aparecem os campos 1ª/2ª/3ª opção, "Modelo do Ollama menor", "Tempo por tentativa (s)", "Tempo de castigo (min)" e "Chave da API do Claude" | (painel) |
| (painel) Escolha uma ordem diferente (ex.: 1ª Claude, 2ª Ollama), salve e reabra o painel <!-- validacao id=item-129 --> | A ordem escolhida continua marcada | (painel) |
| Feche o Ollama (ou desligue a rede dele) e, com uma 2ª opção configurada (outro modelo do Ollama ou Claude com chave salva), pergunte algo de conversa livre: `Mestre, me conta uma curiosidade` <!-- validacao id=item-130 --> | Ele continua respondendo (pela 2ª opção), sem travar a escuta nem ficar mudo | `_cmd_pensamento` (IA) |
| Religue o Ollama e pergunte de novo antes do "tempo de castigo" passar <!-- validacao id=item-131 --> | Continua respondendo pela 2ª opção (a 1ª ainda está de castigo) | (IA) |
| Espere passar o "tempo de castigo" configurado e pergunte de novo <!-- validacao id=item-132 --> | Volta a tentar a 1ª opção primeiro | (IA) |
| (visual) confira `logs\mestre.log` depois de uma pergunta de conversa livre <!-- validacao id=item-133 --> | Tem uma linha dizendo qual IA respondeu de fato | (visual) |
| (com um config.yaml antigo, de antes desta versão, sem as chaves novas) reinicie o Assessor <!-- validacao id=item-134 --> | A IA continua respondendo normalmente pelo Ollama, do jeito de sempre (os padrões do código cobrem a falta das chaves novas) | (automático, ao religar) |
| (automático) `venv\Scripts\python -m testes.teste_basico` <!-- validacao id=item-135 --> | Itens de "Troca de IA sozinho" (1ª lenta cai pra 2ª, castigo, castigo expira, ordem respeitada) OK | (automático) |

### Detector local da palavra (opcional, começa desligado)
<!-- validacao-grupo id=grupo-detector-local-da-palavra-opcional-comeca-deslig -->

| Frase / ação | O que deve acontecer | Comando esperado |
|---|---|---|
| (painel) Áudio > "Reconhecimento de voz (Whisper)" <!-- validacao id=item-136 --> | Aparecem "Detector local da palavra" (desligado), "Exigência do detector" e a linha de situação ("Modelo pronto" ou "Modelo não encontrado") | (painel) |
| Com o detector DESLIGADO: `Assessor, que horas são?` <!-- validacao id=item-137 --> | Responde como sempre | `_cmd_hora_data` |
| Rode `ferramentas\15_treinar_palavra.bat` (responda `s` para gravar sua voz 30 vezes) <!-- validacao id=item-138 --> | Termina mostrando quantas das suas gravações reais ele achou e cria `modelos\palavra\assessor.npz` | (ferramenta) |
| (painel) ligue o detector > Salvar e reiniciar; depois `Assessor, que horas são?` <!-- validacao id=item-139 --> | Responde normal (no ouvido.jsonl a frase tem `nota_detector`) | `_cmd_hora_data` |
| `Assessor` (pausa de 2 s) `abre o YouTube` <!-- validacao id=item-140 --> | Vira uma frase só, como antes | `_cmd_abrir` |
| Deixe um vídeo com gente falando tocar 5 minutos sem chamar <!-- validacao id=item-141 --> | Nada executa; no ouvido.jsonl os trechos aparecem com motivo "sem a palavra (detector local)" (sem transcrição) | (ignorado, sem comando) |
| Durante uma resposta longa: `Assessor, para` <!-- validacao id=item-142 --> | Para de falar na hora (o interromper continua igual) | (só parou) |
| Na janela de conversa, logo depois de uma resposta: `e amanhã?` (sem a palavra) <!-- validacao id=item-143 --> | Continua valendo sem a palavra | (o comando falado) |
| Modo descanso + `bora voltar a trabalhar` <!-- validacao id=item-144 --> | Acorda normalmente | `_cmd_descanso` |
| (automático) `venv\Scripts\python -m testes.teste_basico` <!-- validacao id=item-145 --> | Itens "Detector: ..." OK | (automático) |

### Indicador na tela: balão de texto + robô menor (novo padrão)
<!-- validacao-grupo id=grupo-indicador-na-tela-balao-de-texto-robo-menor-novo -->

| Frase / ação | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, reinicia` (config sem mexer no Indicador) <!-- validacao id=item-146 --> | Aparece o robô perto do relógio COM um balão escuro em cima, texto branco legível | (visual) |
| Fale qualquer pedido e espere ele processar <!-- validacao id=item-147 --> | O balão muda: (some quando só ouvindo em silêncio) → "Gravando…"/"Ouvindo…" → "Pensando: <resumo do que você pediu>" → "Falando…" | (visual) |
| Peça algo que dispare a IA em segundo plano e, sem esperar, peça outra coisa <!-- validacao id=item-148 --> | O balão de "Pensando" mostra "· Na fila: 2" (ou o número de pedidos esperando) | (visual) |
| `Mestre, pode descansar` <!-- validacao id=item-149 --> | Balão mostra "Descansando" | `_cmd_descanso` |
| Botão direito no indicador > "Pausar a escuta" <!-- validacao id=item-150 --> | Balão mostra "Pausado" antes de sumir | (painel/menu) |
| (painel) Aparência > "Indicador na tela" > **"Só robô"** > salvar > `Mestre, reinicia` <!-- validacao id=item-151 --> | O robô volta ao tamanho normal, sem balão | (painel) |
| (painel) Aparência > "Indicador na tela" > **"Bolinha"** > salvar > `Mestre, reinicia` <!-- validacao id=item-152 --> | Volta a pílula antiga (sem o robô) | (painel) |
| (automático) `venv\Scripts\python -m testes.teste_basico` <!-- validacao id=item-153 --> | Itens "Balão: ..." (texto por estado, resumo da pergunta, fila, tamanho da janela) e "Painel: Indicador..." OK | (automático) |

## 2. Sempre testar (regressão fixa — todo dia a dia)

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, bom dia` <!-- validacao id=item-154 --> | Roda a rotina "Bom dia" (se cadastrada) ou fica quieto se não tiver | `_cmd_rotinas` |
| `Mestre, bora trabalhar` <!-- validacao id=item-155 --> | Roda a rotina "Bora trabalhar" (abre Gmail, Claude...) | `_cmd_rotinas` |
| `Mestre, abre o Gmail` <!-- validacao id=item-156 --> | Abre o Gmail no navegador | `_cmd_abrir` |
| `Mestre, abre o Spotify` <!-- validacao id=item-157 --> | Abre o PROGRAMA Spotify (não o canal do YouTube) | `_cmd_abrir` |
| `Mestre, abre o YouTube` <!-- validacao id=rapido-youtube tipo=fala --> | Abre o YouTube | `_cmd_youtube` |
| `Mestre, toca Legião Urbana no Spotify` <!-- validacao id=item-159 --> | Toca o artista/playlist no Spotify | `_cmd_spotify` |
| `Mestre, aumenta o volume` <!-- validacao id=rapido-volume tipo=fala --> | Sobe o volume geral | `_cmd_volume` |
| `Mestre, pausa a música` <!-- validacao id=item-161 --> | Pausa o que estiver tocando | `_cmd_midia` |
| `Mestre, dá um like` (com um vídeo do YouTube aberto) <!-- validacao id=item-162 --> | Curte o vídeo | `_cmd_youtube_controle` |
| `Mestre, próximo vídeo` <!-- validacao id=item-163 --> | Pula pro próximo vídeo | `_cmd_youtube_controle` |
| `Mestre, joga essa janela pro monitor 2` <!-- validacao id=item-164 --> | Move a janela ativa pro monitor 2 | `_cmd_mover` |
| `Mestre, minimiza tudo` <!-- validacao id=item-165 --> | Minimiza todas as janelas | `_cmd_janela` |
| `Mestre, nova aba` <!-- validacao id=item-166 --> | Abre uma aba nova no navegador | `_cmd_janela` |
| `Mestre, anota comprar pão` <!-- validacao id=rapido-anotacao tipo=fala --> | Guarda a nota | `_cmd_notas` |
| `Mestre, vou ditar` <!-- validacao id=item-168 --> | Começa o ditado (janela de revisão no fim) | `_cmd_ditado` |
| `Mestre, o que você acha de aprender python` <!-- validacao id=item-169 --> | Vai pensar (fila da IA), fala ou mostra a resposta depois | (IA, sem comando) |
| `Mestre, pode descansar` <!-- validacao id=item-170 --> | Fica quieto; só acorda com "bora voltar a trabalhar" | `_cmd_descanso` |
| `Mestre, bora voltar a trabalhar` (com ele descansando) <!-- validacao id=item-171 --> | Acorda e volta a atender normalmente | (acorda no ouvido, sem `_cmd_`) |
| `Mestre, reinicia` <!-- validacao id=item-172 --> | Reinicia o Assessor com as mudanças, em poucos segundos | `_cmd_reiniciar` |
| `Mestre, que horas são` <!-- validacao id=rapido-hora tipo=fala --> | Fala a hora atual | `_cmd_hora_data` |
| `Mestre, repete` <!-- validacao id=item-174 --> | Repete a última resposta | `_cmd_historico` |
| `Mestre, lembra que eu trabalho de manhã` <!-- validacao id=item-175 --> | Guarda o fato pra lembrar depois | `_cmd_memoria` |
| `Mestre, abre o painel` <!-- validacao id=item-176 --> | Abre a janela do painel | `_cmd_painel` |
| (painel) Sistema > Validar atualização <!-- validacao id=item-177 --> | Lê este roteiro e vai perguntando cada frase, com OUVI/ENTENDI/FIZ | (painel) |
