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
