# Roteiro de validação — Assessor

Como usar: fale cada frase trocando "Mestre" pela sua palavra de ativação (ex.: **Assessor**).
Depois de qualquer mudança, fale primeiro "Mestre, reinicia". Marque `[x]` o que funcionou. O
que falhar, fale "isso tá errado, era outra coisa" logo depois: vira FEEDBACK no MELHORIAS.md
(com o áudio).

Cada linha é: `frase falada | o que deve acontecer | comando esperado (_cmd_*)`. Uma linha sem
frase pra falar (ação no painel, teste automático, checagem visual) tem `(painel)`,
`(automático)` ou `(visual)` no lugar da frase.

Este arquivo substitui o antigo CHECKLIST_VALIDACAO.md (o texto dele virou uma lista solta,
sem comando esperado, difícil de conferir por script; ficou só um aviso apontando pra cá).

## 1. Novidades (desta leva)

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
| (painel) Passe o mouse na barra de ícones da esquerda | Ela abre suave (sem travar) mostrando os nomes e os grupos; tire o mouse e ela fecha | (painel) |
| (painel) Pare o mouse em cima de um ícone | Aparece um balãozinho com o nome e o que tem na página | (painel) |
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
| (automático) `venv\Scripts\python -m testes.teste_basico` | Linha "Nenhum erro escondido nos botões" fecha OK, teste completo 275 de 275 | (teste automático) |
| (visual) olhe o ícone perto do relógio (bandeja) | Ícone novo, na cor escolhida em Aparência | (bandeja) |
| (painel) abra o painel, ensine uma rotina nova por voz SEM fechar o painel, depois clique Salvar no painel | A rotina nova continua no config.yaml; uma rotina que você apagar no painel continua apagada | (painel) |
| (painel) Sistema > Validar atualização → "Só novidades" → Começar; fale a frase que aparece; marque ✅/❌ (no ❌ diga "o certo era") → Parar | Mostra OUVI / ENTENDI (com o comando) / FIZ de cada frase e sugere ✅/❌; no fim cria `exportacoes/validacao_AAAA-MM-DD_HHMM.md` e cada ❌ vira FEEDBACK no MELHORIAS.md | (painel) |
| (painel) depois de um relatório com falha, clique "🛠 Mandar para o Claude corrigir" | Salva o pedido em `exportacoes/pedido_correcao_*.md` e abre um terminal (Windows Terminal ou cmd) com o Claude Code interativo já com o pedido; sem falha nenhuma o botão fica desativado | (painel) |

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
