# Checklist de validação — Assessor (versão 13, 27/09/2026)

Como usar: fale cada frase trocando "Mestre" pela sua palavra (**Assessor**). Marque `[x]` o que funcionou.
O que falhar, fale "isso tá errado, era outra coisa" logo depois: vira FEEDBACK no MELHORIAS.md com o áudio.

⚠️ = problema já visto nos logs ou no teste automático. Valide com atenção.

## 1. Novidades desta versão (validar primeiro)

- [ ] **Brave com suas contas:** "abre a Disney no monitor 2" → abre JÁ LOGADO, sem "link não confiável"
- [ ] Se abrir deslogado: painel → Sites → **Perfil do Brave** = nome do perfil (veja em `brave://version`) → salvar → repetir
- [ ] "toca Agentes da Shield na Disney" → digita na busca, clica no título e em continuar assistindo
- [ ] **Novo projeto:** "quero começar um novo projeto" → pergunta tipo, nome, objetivo, prazo
- [ ] A pasta aparece em `C:\Ias\projetos\<nome>` com subpastas e PLANO.md
- [ ] O PLANO.md tem a seção **Pesquisa na internet** com links
- [ ] Fala 3 caminhos + a 4ª opção (mandar pro Claude); escolher "dois" grava os passos
- [ ] Painel → Projetos → chave **Pesquisa automática** desligada = não pesquisa
- [ ] Painel mostra versão 13 e salva sem erro

## 2. Pontos de atenção já conhecidos

- [ ] ⚠️ "bom dia" não responde (nenhum comando atende). Tem rotina "bom dia" cadastrada no painel?
- [ ] ⚠️ A extensão do Brave às vezes "não respondeu" (log de 26/09 13:13): YouTube e streaming ficam limitados. Painel avisa se está desatualizada?
- [ ] ⚠️ "abre HBO no segundo monitor" respondeu "não conheço": falta HBO Max na lista de sites
- [ ] ⚠️ "abre o spotify" deve abrir o PROGRAMA, não um canal do YouTube
- [ ] ⚠️ Telegram: o 1º chat vira o seu, executa comando e ignora estranhos
- [ ] ⚠️ Exportar o histórico gera arquivo com resumo e frases mal ouvidas
- [ ] ⚠️ Ditado longo e "pensar em segundo plano" terminam e entregam a resposta

## 3. Todos os comandos

### Mídia e volume

- [ ] "Assessor, pausa"
- [ ] "Assessor, pausa a música"
- [ ] "Assessor, pausa o Spotify"
- [ ] "Assessor, despausa"
- [ ] "Assessor, continua a música"
- [ ] "Assessor, volta a tocar"
- [ ] "Assessor, próxima música"
- [ ] "Assessor, pula essa"
- [ ] "Assessor, próxima"
- [ ] "Assessor, música anterior"
- [ ] "Assessor, volta a música"
- [ ] "Assessor, para a música"
- [ ] "Assessor, aumenta o volume"
- [ ] "Assessor, diminui o volume"
- [ ] "Assessor, abaixa o som"
- [ ] "Assessor, sobe o volume um pouco"
- [ ] "Assessor, volume no 30"
- [ ] "Assessor, volume máximo"
- [ ] "Assessor, muta"
- [ ] "Assessor, tira do mudo"
- [ ] "Assessor, aumenta o volume do Spotify"
- [ ] "Assessor, diminui o Spotify"
- [ ] "Assessor, abaixa o Spotify"
- [ ] "Assessor, coloca o Spotify no máximo"
- [ ] "Assessor, coloque no volume máximo do Spotify"
- [ ] "Assessor, Spotify no 50"
- [ ] "Assessor, muta o Spotify"
- [ ] "Assessor, tira o som do Spotify"
- [ ] "Assessor, volta o som do Spotify"
- [ ] "Assessor, Spotify mais alto"
- [ ] "Assessor, toca a playlist Foco no Spotify"
- [ ] "Assessor, toca Legião Urbana no Spotify"
- [ ] "Assessor, bota Coldplay no Spotify"
- [ ] "Assessor, próximo"
- [ ] "Assessor, pause Spotify"
- [ ] "Assessor, pula essa música do Spotify"
- [ ] "Assessor, continua Spotify"
- [ ] "Assessor, multa o Spotify"
- [ ] "Assessor, diminui o Spotify em 20%"
- [ ] "Assessor, tirar o vídeo do YouTube do mudo"
- [ ] "Assessor, aumentar o volume do YouTube"
- [ ] "Assessor, tocar Feliz do DJ Petroski"

### YouTube

- [ ] "Assessor, tela cheia"
- [ ] "Assessor, coloca em tela cheia"
- [ ] "Assessor, deixa em tela cheia"
- [ ] "Assessor, sai da tela cheia"
- [ ] "Assessor, tira da tela cheia"
- [ ] "Assessor, tela cheia com chat"
- [ ] "Assessor, modo cinema"
- [ ] "Assessor, liga a legenda"
- [ ] "Assessor, dá um like"
- [ ] "Assessor, dá like"
- [ ] "Assessor, curte esse vídeo"
- [ ] "Assessor, deixa um gostei"
- [ ] "Assessor, se inscreve no canal"
- [ ] "Assessor, inscreve"
- [ ] "Assessor, fecha o chat"
- [ ] "Assessor, esconde o chat"
- [ ] "Assessor, abre o chat"
- [ ] "Assessor, lê os títulos"
- [ ] "Assessor, quais são os vídeos"
- [ ] "Assessor, abre o terceiro vídeo"
- [ ] "Assessor, clica no segundo vídeo"
- [ ] "Assessor, abre o primeiro resultado"
- [ ] "Assessor, quero o quarto vídeo"
- [ ] "Assessor, abre o vídeo do Manual do Mundo"
- [ ] "Assessor, avança 30 segundos"
- [ ] "Assessor, volta 10 segundos"
- [ ] "Assessor, avança 2 minutos"
- [ ] "Assessor, próximo vídeo"
- [ ] "Assessor, vai pro próximo vídeo"
- [ ] "Assessor, pula esse vídeo"
- [ ] "Assessor, vídeo anterior"
- [ ] "Assessor, pausa o vídeo"
- [ ] "Assessor, para o vídeo"
- [ ] "Assessor, continua o vídeo"
- [ ] "Assessor, despausa o vídeo"
- [ ] "Assessor, dá play no vídeo"
- [ ] "Assessor, vai pras inscrições"
- [ ] "Assessor, abre o assistir mais tarde"
- [ ] "Assessor, abre os shorts"
- [ ] "Assessor, abre o histórico do YouTube"
- [ ] "Assessor, mostra os vídeos que eu gostei"
- [ ] "Assessor, abre o YouTube"
- [ ] "Assessor, abre o último vídeo do Manual do Mundo"
- [ ] "Assessor, pesquisa receita de pão no YouTube"
- [ ] "Assessor, toca Legião Urbana no YouTube"
- [ ] "Assessor, abre o canal Manual do Mundo"
- [ ] "Assessor, abre o YouTube no monitor 2"
- [ ] "Meu Assessor, coloque em tela cheia"
- [ ] "Fala, meu Assessor. Abre o canal do FRTT."
- [ ] "Assessor, pesquise pelo canal FRTT"
- [ ] "Assessor, se inscreva nesse canal"
- [ ] "Assessor, o segundo vídeo da janela"
- [ ] "Assessor, selecione o primeiro vídeo com o nome I hate how much I love Jumanji"
- [ ] "Assessor, tocar os terceiros vídeos dessa lista"
- [ ] "Assessor, selecione o canal do primeiro vídeo"
- [ ] "Assessor, reproduz o último vídeo desse canal"
- [ ] "Assessor, abre o segundo vídeo do monitor 2"
- [ ] "Assessor, o terceiro vídeo da tela 2"
- [ ] "Assessor, pausa o vídeo do monitor 2"
- [ ] "Assessor, abre o vídeo com o nome Como seria o GTA 6 no monitor 2"

### Streaming (Netflix, Disney...)

- [ ] "Assessor, toca Agentes da Shield na Disney"
- [ ] "Assessor, reproduzir na Disney aberta na janela principal o seriado Agentes da Shield"
- [ ] "Assessor, quero continuar assistindo a série Agentes da Shield"
- [ ] "Assessor, assiste Stranger Things na Netflix"
- [ ] "Assessor, clica em continuar assistindo"
- [ ] "Assessor, clica em continuar assistindo do monitor 3"

### Abrir sites e programas

- [ ] "Assessor, abre a Netflix"
- [ ] "Assessor, abre o ChatGPT"
- [ ] "Assessor, abre o Gemini"
- [ ] "Assessor, abre o Mercado Livre"
- [ ] "Assessor, abre a Shopee"
- [ ] "Assessor, abre o TikTok"
- [ ] "Assessor, abre a Twitch"
- [ ] "Assessor, abre o Prime Video"
- [ ] "Assessor, abre a Disney"
- [ ] "Assessor, abre o Gmail"
- [ ] "Assessor, entra no Perplexity"
- [ ] "Assessor, abre a calculadora"
- [ ] "Assessor, abre a Netflix no monitor 3"
- [ ] "Assessor, abre o ChatGPT no monitor terciário"
- [ ] "Assessor, abre a Netflix na janela principal"

### Janelas, abas e monitores

- [ ] "Assessor, fecha essa janela"
- [ ] "Assessor, minimiza"
- [ ] "Assessor, minimiza essa janela"
- [ ] "Assessor, maximiza a janela"
- [ ] "Assessor, minimiza tudo"
- [ ] "Assessor, mostra a área de trabalho"
- [ ] "Assessor, troca de janela"
- [ ] "Assessor, nova aba"
- [ ] "Assessor, abre uma nova aba"
- [ ] "Assessor, fecha a aba"
- [ ] "Assessor, reabre a aba"
- [ ] "Assessor, volta a página"
- [ ] "Assessor, página anterior"
- [ ] "Assessor, atualiza a página"
- [ ] "Assessor, recarrega"
- [ ] "Assessor, rola pra baixo"
- [ ] "Assessor, desce a página"
- [ ] "Assessor, rola pra cima"
- [ ] "Assessor, vai pro topo"
- [ ] "Assessor, aumenta o zoom"
- [ ] "Assessor, diminui o zoom"
- [ ] "Assessor, tira um print"
- [ ] "Assessor, joga essa janela pro monitor 2"
- [ ] "Assessor, manda essa janela pro monitor secundário"
- [ ] "Assessor, leva essa janela pra tela 3"
- [ ] "Assessor, vai para a próxima página"
- [ ] "Assessor, volta pra página anterior"
- [ ] "Assessor, avança a página"
- [ ] "Assessor, próxima aba"
- [ ] "Assessor, vai pra próxima aba"
- [ ] "Assessor, aba anterior"
- [ ] "Assessor, volta uma aba"
- [ ] "Assessor, joga a Netflix pro monitor 3"
- [ ] "Assessor, manda o Spotify pro monitor secundário"
- [ ] "Assessor, leva o YouTube pro terciário"
- [ ] "Assessor, passa a janela da Netflix pra tela 2"
- [ ] "Assessor, separa a Netflix pro monitor 2 e deixa o YouTube no principal"
- [ ] "Assessor, quero que você jogue a Netflix desse navegador para o monitor 2 e o YouTube deixe no meu principal"
- [ ] "Assessor, coloca o Spotify no monitor principal"
- [ ] "Assessor, volte na página anterior"
- [ ] "Assessor, junta o YouTube com a Disney"
- [ ] "Assessor, juntar a janela do HBO Max com a do Disney"
- [ ] "Assessor, traz o YouTube pra janela da Disney"
- [ ] "Assessor, junta todas as janelas no principal"
- [ ] "Assessor, manda o Spotify pra janela principal"

### Ditado, melhorias e projetos

- [ ] "Assessor, quero ditar melhorias"
- [ ] "Assessor, quero melhorar uma coisa no projeto"
- [ ] "Assessor, quero melhorar isso aqui no meu projeto"
- [ ] "Assessor, quero criar novas melhorias"
- [ ] "Assessor, tenho uma ideia pro projeto"
- [ ] "Assessor, tenho umas ideias pra você"
- [ ] "Assessor, tenho algumas sugestões de melhoria"
- [ ] "Assessor, bora anotar umas melhorias"
- [ ] "Assessor, quero passar umas melhorias"
- [ ] "Assessor, quero fazer uns ajustes no projeto"
- [ ] "Assessor, quero dar um feedback do projeto"
- [ ] "Assessor, vamos melhorar o Assessor"
- [ ] "Assessor, quero registrar melhorias"
- [ ] "Assessor, modo melhorias"
- [ ] "Assessor, vou ditar"
- [ ] "Assessor, vou falar um texto longo"
- [ ] "Assessor, lê minhas melhorias"
- [ ] "Assessor, quais são as melhorias"
- [ ] "Assessor, aplica as melhorias"
- [ ] "Assessor, pergunta pro agente IPM como abrir um chamado"
- [ ] "Assessor, abre o agente IPM"
- [ ] "Assessor, ditado pro agente IPM"
- [ ] "Assessor, quero começar um novo projeto"
- [ ] "Assessor, cria um projeto novo"
- [ ] "Assessor, bora iniciar um projeto"
- [ ] "Assessor, quais são os meus projetos"
- [ ] "Assessor, exporta o histórico"
- [ ] "Assessor, exporta o histórico de hoje"
- [ ] "Assessor, manda o histórico pro Claude"
- [ ] "Assessor, gera o relatório dos testes"
- [ ] "Assessor, anota uma melhoria deixar o painel azul com letras maiores"
- [ ] "Assessor, isso tá errado, era outra coisa"

### Memória e histórico

- [ ] "Assessor, repete a resposta"
- [ ] "Assessor, repete"
- [ ] "Assessor, fala de novo"
- [ ] "Assessor, qual foi a última resposta"
- [ ] "Assessor, lê as últimas respostas"
- [ ] "Assessor, o que você respondeu sobre relatividade"
- [ ] "Assessor, lembra que eu trabalho de manhã"
- [ ] "Assessor, guarda que meu aniversário é em maio"
- [ ] "Assessor, o que você lembra de mim"
- [ ] "Assessor, me lembra de beber água em 10 minutos"
- [ ] "Assessor, anota comprar pão"

### Conversa, rotinas e sistema

- [ ] "Assessor, e aí"
- [ ] "E aí, meu Assessor, tá por aí?"
- [ ] "Assessor, tchau tchau"
- [ ] "Assessor, bye"
- [ ] "Assessor, descansar"
- [ ] "Assessor, pode descansar"
- [ ] "Assessor, fica quieto"
- [ ] "Assessor, modo descanso"
- [ ] "Assessor, que horas são"
- [ ] "Assessor, que dia é hoje"
- [ ] "Assessor, bora trabalhar"
- [ ] "Assessor, bom dia"
- [ ] "Assessor, desliga a tela"
- [ ] "Assessor, bloqueia o computador"
- [ ] "Assessor, valeu"
- [ ] "Assessor, abre o painel"
- [ ] "Assessor, qual é a sua versão?"
- [ ] "Assessor, em que versão você está"
- [ ] "Assessor, desliga"
- [ ] "Assessor, pode desligar"
- [ ] "Assessor, pode se desligar"
- [ ] "Assessor, desliga o Assessor"
- [ ] "Assessor, encerra por hoje"
- [ ] "Assessor, desliga o PC"

### Vão para a IA (não é comando)

- [ ] "Assessor, quero uma sugestão de filme"
- [ ] "Assessor, me dá uma ideia de receita"

## 4. Voz, microfone e painel

- [ ] Fala a palavra de ativação baixo e de longe: acorda
- [ ] Ruído (TV, música) não acorda sozinho
- [ ] Indicador na tela muda: ouvindo → gravando → pensando
- [ ] Voz escolhida fala; se falhar, cai para outra sem travar
- [ ] Pausar/retomar pela bandeja (perto do relógio)
- [ ] "Assessor, reinicia" volta em poucos segundos
- [ ] Áudio do celular (Telegram/pasta) vira comando ou nota
- [ ] Atualizar por .zip na Central mantém config, notas e MELHORIAS
