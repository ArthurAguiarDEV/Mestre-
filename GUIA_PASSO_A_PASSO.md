# 🎙️ MESTRE: seu assistente pessoal por voz
### Guia completo, do zero, para quem não é programador

> **Como usar este guia:** faça uma etapa de cada vez, na ordem. Cada etapa diz **o que fazer**, **o que você deve ver** e **o que fazer se der errado**. Não pule etapas.

---

## 📋 Índice

1. [O que é o Mestre](#1-o-que-é-o-mestre)
2. [O que é possível e o que não é (leia antes!)](#2-o-que-é-possível-e-o-que-não-é)
3. [Como ele funciona por dentro](#3-como-ele-funciona-por-dentro)
4. **Etapa 1**: [Instalar o Python](#etapa-1--instalar-o-python)
5. **Etapa 2**: [Colocar a pasta do Mestre no PC](#etapa-2--colocar-a-pasta-do-mestre-no-pc)
6. **Etapa 3**: [Instalar o Mestre](#etapa-3--instalar-o-mestre)
7. **Etapa 4**: [Testar digitando](#etapa-4--testar-digitando)
8. **Etapa 5**: [Testar falando](#etapa-5--testar-falando)
9. **Etapa 6**: ["Acordar o PC" por voz (energia e senha)](#etapa-6--acordar-o-pc-por-voz)
10. **Etapa 7**: [Ligar sozinho com o Windows](#etapa-7--ligar-sozinho-com-o-windows)
11. **Etapa 8**: [Ligar o seu Agente IPM do Claude](#etapa-8--ligar-o-seu-agente-ipm-do-claude)
12. **Etapa 9** (opcional): [Dar um "cérebro" grátis ao Mestre (Ollama)](#etapa-9-opcional--cérebro-grátis-com-ollama)
13. **Etapa 10** (opcional, pago): [Usar o Claude como cérebro](#etapa-10-opcional-pago--claude-como-cérebro)
14. **Etapa 11** (versão 2): [Atualizar sem perder suas configurações](#etapa-11--atualizar-para-a-versão-2)
15. **Etapa 12**: [Falar solto: vocabulário, modo conversa e atalhos](#etapa-12--falar-solto)
16. **Etapa 13**: [Voz e personalidade](#etapa-13--voz-e-personalidade)
17. **Etapa 14**: [Melhorar o Mestre falando com ele (Claude Code)](#etapa-14--melhorar-o-mestre-falando-com-ele)
18. **Etapa 15** (versão 3): [Atualizar para a versão 3](#etapa-15--atualizar-para-a-versão-3)
19. **Etapa 16**: [Painel de configurações (sem editar arquivo)](#etapa-16--painel-de-configurações)
20. **Etapa 17**: [Calibrar e testar o microfone](#etapa-17--calibrar-e-testar-o-microfone)
21. **Etapa 18**: [O indicador na tela](#etapa-18--o-indicador-na-tela)
22. **Etapa 19**: [Trazer todas as suas inscrições do YouTube](#etapa-19--inscrições-do-youtube)
23. **Etapa 20**: [Rotinas mais ricas: clima, notícias, resumo do dia](#etapa-20--rotinas-mais-ricas)
24. **Etapa 21**: [Refinar seus pedidos (skill) e projetos parecidos](#etapa-21--refinar-seus-pedidos)
25. **Etapa 22** (versão 4): [Ditado longo, feedback, nomes, voz fluida e painel novo](#etapa-22--versão-4)
26. **Etapa 23** (versão 5): [Atalho único, Central, painel rápido e teste automático](#etapa-23--versão-5)
27. **Etapa 24** (versão 6): [Ditar melhorias, IA em segundo plano, aparência e páginas](#etapa-24--versão-6)
28. **Etapa 25** (versão 7): [App Claude, histórico e memória, Spotify, projetos guiados](#etapa-25--versão-7)
29. **Etapa 26** (versão 8): [Música, janelas e YouTube por voz; envio ao Claude; avisos curtos](#etapa-26--versão-8)
30. **Etapa 27** (versão 9): [Brave, monitores, envio ao Claude maximizado, volume só do Spotify](#etapa-27--versão-9)
31. **Etapa 28** (versão 10): [Extensão do Brave, sites prontos, monitores por marca, vocabulário amplo, ditado caprichado](#etapa-28--versão-10)
32. **Etapa 29** (versão 11): [Assessor x Mestre, pensando em silêncio, YouTube direto, janelas e abas nos monitores, exportar o histórico](#etapa-29--versão-11)
33. **Etapa 30** (versão 12): [Voz Kokoro e Azure, modo descanso, streamings, juntar janelas, áudios do celular](#etapa-30--versão-12)
34. **Etapa 31** (versão 13): [Painel novo, streamings digitando na busca, tela certa do YouTube, IA sem "pode falar", vozes Natural e ElevenLabs, aviso do Telegram, desligar na hora, validar a atualização no painel](#etapa-31--versão-13)
35. **Etapa 32** (versão 2.5): [Painel repaginado: menu de ícones, Início em cartões, voz em abas com reserva](#etapa-32--versão-25)
36. **Etapa 33**: [Novidades do Telegram: print, "o que tá tocando", vídeo curto, ligar/desligar à distância](#etapa-33-novidades-do-telegram-print-o-que-tá-tocando-vídeo-curto-e-energia-à-distância)
37. [Personalizar: canais, programas, sites e rotinas](#personalizar)
38. [Lista de todos os comandos de voz](#lista-de-comandos)
39. [Problemas comuns e soluções](#problemas-comuns)
40. [Próximos passos: levar para o celular](#próximos-passos)

---

## 1. O que é o Mestre

O Mestre é um programa que fica ligado no seu computador, **ouvindo o microfone**. Quando você fala **"Mestre"**, ele acorda, entende o que você pediu e **executa e responde por voz**.

Exemplos reais:

| Você fala | O Mestre faz |
|---|---|
| "E aí Mestre, bora trabalhar!" | Liga a tela, dá bom dia e abre Gmail e Claude |
| "Mestre, abre o último vídeo do Manual do Mundo" | Acha o vídeo mais recente do canal e abre |
| "Mestre, pergunta pro agente IPM como classificar um chamado de folha" | Abre seu projeto no Claude, cola a pergunta e envia |
| "Mestre, me lembra de beber água em 20 minutos" | Avisa por voz daqui a 20 minutos |
| "Mestre, desliga a tela" | Apaga o monitor e continua ouvindo |

**Custo:** R$ 0. Tudo usa programas gratuitos e roda no seu PC.

---

## 2. O que é possível e o que não é

Isto é importante para a apresentação: são **limites do Windows e do hardware**, não do projeto.

### ❌ Acordar o PC da **suspensão** por voz: não é possível
Quando o PC está **suspenso** (modo de espera/sleep), o processador e o microfone ficam **desligados**. Nenhum programa consegue ouvir nada nesse estado. É como pedir para alguém dormindo anotar um recado.

### ✅ A solução que funciona igual: "tela apagada, PC acordado"
- O PC **nunca suspende** quando está na tomada.
- A **tela desliga sozinha** após 10 minutos (economiza quase tudo).
- O Mestre continua ouvindo com um "vigia" levíssimo (usa ~1–3% do processador).
- Você diz *"E aí Mestre, bora trabalhar"*, e **a tela liga e tudo abre**.

Na prática, a experiência é a mesma de "acordar o PC por voz". O arquivo `ferramentas\5_configurar_energia.bat` configura isso para você.

### ❌ Digitar sua senha para desbloquear: não é possível (e não seria seguro)
O Windows **proíbe** programas de digitar na tela de bloqueio. É uma proteção de segurança proposital. Além disso, se funcionasse, **qualquer pessoa** (ou uma gravação da sua voz) poderia desbloquear seu PC.

### ✅ As alternativas seguras
| Opção | Como fica | Segurança |
|---|---|---|
| **A) Não pedir senha ao acordar a tela** (recomendado para PC em casa) | Tela apaga → você fala → tela liga já na área de trabalho | Boa se só você usa o PC |
| **B) Windows Hello** (rosto ou digital) | Você fala, a tela liga, você olha para a câmera e ela destrava sozinha | Ótima |
| **C) Manter a senha** | Você fala, a tela liga, você digita a senha, e as coisas já estão abertas atrás | Máxima |

Com o comando *"Mestre, bloqueia o computador"* você bloqueia de verdade quando sair de perto.

### ⚠️ Se o PC for **reiniciado ou desligado**
O Mestre só liga **depois que você entra no Windows** (faz login). Mantenha o PC ligado para usar o "acordar por voz".

---

## 3. Como ele funciona por dentro

```
 🎤 Microfone
    │
    ▼
 ① VIGIA (Vosk): escuta o tempo todo, mas só reconhece a palavra "Mestre".
    │          Levíssimo, offline.
    ▼  ouviu "Mestre"!
 ② OUVIDO FINO (Whisper): transcreve a frase inteira com alta precisão.
    │          "E aí Mestre, bora trabalhar" → comando: "bora trabalhar"
    ▼
 ③ COMANDOS: procura o que fazer (rotinas, YouTube, volume, programas...).
    │          Se não achar e o "cérebro" estiver ligado, pergunta para a IA.
    ▼
 ④ VOZ (Edge TTS): responde falando, com voz natural em português.
```

**Por que dois "ouvidos"?** O vigia é leve para ficar ligado 24 horas sem pesar o PC. O Whisper é preciso, mas pesado, então só trabalha quando você chama.

### Arquivos do projeto (o que é cada coisa)

| Arquivo / pasta | Para que serve | Você mexe? |
|---|---|---|
| `INSTALAR_E_CRIAR_ATALHO.bat` (pasta principal) | Instala tudo e cria o atalho **Mestre** | Clica uma vez |
| `ferramentas\1_instalar.bat` | Instalação completa (o de cima já chama este) | Se precisar |
| `ferramentas\2_testar_por_texto.bat` | Testa digitando | Sim, para testar |
| `ferramentas\3_iniciar_mestre.bat` | Liga o Mestre com janela (para ver o que acontece) | Sim |
| `ferramentas\4_ativar_inicio_automatico.bat` | Faz o Mestre ligar com o Windows | Clica uma vez |
| `ferramentas\5_configurar_energia.bat` | Deixa o PC acordado com a tela apagada | Clica uma vez |
| `ferramentas\6_listar_microfones.bat` | Mostra seus microfones | Se precisar |
| `ferramentas\7_desativar_inicio_automatico.bat` | Desfaz o início automático | Se precisar |
| `ferramentas\8_parar_mestre.bat` | Desliga o Mestre que está rodando escondido | Se precisar |
| `config.yaml` | **Todas as configurações**: canais, programas, sites, rotinas | **Sim, é aqui que você personaliza** |
| `vocabulario.yaml` | Jeitos de falar: sinônimos, enfeites e atalhos (Etapa 12) | Sim |
| `aprendido.yaml` | O que você ensina por voz (atalhos, voz escolhida) | Não precisa |
| `MELHORIAS.md` | Ideias anotadas por voz para o Claude Code (Etapa 14) | Se quiser |
| `CLAUDE.md` | Manual do projeto para o Claude Code | Não precisa |
| `ferramentas\9_escolher_voz.bat` | Ouve e escolhe a voz do Mestre (Etapa 13) | Sim |
| `perfis/` | Instruções da IA (inclusive a do agente IPM) | Sim, Etapa 8 |
| `notas/` | Suas anotações por voz | Só lê |
| `respostas/` | Respostas longas da IA | Só lê |
| `logs/mestre.log` | "Diário" do que o Mestre fez (para achar erros) | Só se der erro |
| `app/` | O código do programa | Não precisa |

---

## Etapa 1: Instalar o Python

O Python é a "linguagem" em que o Mestre foi escrito. Precisa estar instalado no PC.

1. Abra o navegador e entre em **https://www.python.org/downloads/windows/**
2. Procure **Python 3.12** (qualquer 3.12.x) e clique em **"Windows installer (64-bit)"**.
3. Abra o arquivo baixado.
4. ⚠️ **MUITO IMPORTANTE:** na primeira tela, **marque a caixinha "Add python.exe to PATH"** (fica embaixo).
5. Clique em **"Install Now"** e espere terminar. Clique em **"Close"**.

**✅ Como conferir:** aperte `Windows + R`, digite `cmd` e dê Enter. Na janela preta, digite `py --version` e Enter. Deve aparecer algo como `Python 3.12.x`.

**❌ Se aparecer "não é reconhecido":** desinstale o Python (Configurações > Aplicativos) e instale de novo, **marcando a caixinha do PATH**.

> Por que a 3.12 e não a mais nova? Algumas bibliotecas de voz demoram a suportar a versão mais recente. A 3.12 é a mais segura.

---

## Etapa 2: Colocar a pasta do Mestre no PC

1. Baixe o arquivo **`mestre.zip`** (que te enviei nesta conversa) **no computador**.
   - Dica: abra esta conversa no PC pelo **claude.ai** e baixe o arquivo por lá.
2. Crie a pasta `C:\Mestre` (ou em Documentos, como preferir).
   - ⚠️ Evite colocar dentro do OneDrive. Ele fica sincronizando os modelos de voz e deixa tudo lento.
3. Clique com o botão direito no `mestre.zip` > **Extrair tudo...** > escolha `C:\Mestre` > **Extrair**.

**✅ Como conferir:** dentro de `C:\Mestre\mestre` você vê o arquivo `INSTALAR_E_CRIAR_ATALHO.bat`, o `config.yaml`, a pasta `app` etc.

---

## Etapa 3: Instalar o Mestre

1. Dê **dois cliques** em `INSTALAR_E_CRIAR_ATALHO.bat` (na pasta principal do Mestre). Ele instala tudo e cria o atalho **Mestre** na área de trabalho.
2. Se aparecer uma tela azul **"O Windows protegeu o computador"**: clique em **"Mais informações"** > **"Executar assim mesmo"**. (É normal para arquivos baixados da internet.)
3. Uma janela preta vai mostrar o progresso em 4 passos. **Espere**: a primeira vez leva de 5 a 15 minutos, porque baixa ~600 MB (bibliotecas + modelos de voz).
4. No final aparece **`PRONTO!`** e a **Central do Mestre** abre sozinha.

**❌ Se der erro:** tire um print da janela e me mande. Os erros mais comuns estão em [Problemas comuns](#problemas-comuns).

---

## Etapa 4: Testar digitando

Antes de falar, vamos conferir que os comandos funcionam.

1. Dê dois cliques em `ferramentas\2_testar_por_texto.bat`.
2. Onde aparece `VOCE:`, digite e aperte Enter:
   - `e aí mestre, que horas são?` → ele deve **falar** a hora
   - `mestre bora trabalhar` → deve abrir o Gmail e o Claude
   - `mestre abre o último vídeo do manual do mundo` → deve abrir o vídeo
   - `mestre o que você sabe fazer` → lista as habilidades
3. Para sair, digite `sair`.

**✅ Deu certo se:** você ouviu a voz e as páginas abriram.
**❌ Sem som:** confira o volume e a saída de áudio do Windows. Veja [Problemas comuns](#problemas-comuns).

---

## Etapa 5: Testar falando

1. Dê dois cliques em `ferramentas\3_iniciar_mestre.bat`.
2. Na **primeira vez**, o Windows pode perguntar se permite o acesso ao microfone: clique em **Sim/Permitir**.
3. Espere ouvir: **"Mestre online. É só chamar."** (na primeira vez pode levar ~1 minuto carregando).
4. Fale **de forma natural, a um palmo ou dois do microfone**:
   - *"E aí Mestre, que horas são?"*
   - *"Mestre!"* → ele responde *"Pois não?"* → *"Abre a calculadora"*
   - *"Mestre, bora trabalhar"*
5. A janela preta mostra `Ouvi: '...'` com o que ele entendeu. Isso ajuda a ajustar.
6. Para desligar: feche a janela preta.

**Dicas:**
- Fale a frase inteira de uma vez e faça uma pequena pausa no final. A pausa é o sinal de "terminei".
- A resposta demora ~1 a 3 segundos (tempo do Whisper pensar). Se estiver lento, veja [Problemas comuns](#problemas-comuns).
- Se ele não reage, rode `ferramentas\6_listar_microfones.bat` e confira se o microfone certo está sendo usado.

---

## Etapa 6: "Acordar o PC" por voz

Aqui configuramos o esquema **"tela apagada, PC acordado"** explicado na [seção 2](#2-o-que-é-possível-e-o-que-não-é).

### 6.1 Energia (automático)
1. Clique com o **botão direito** em `ferramentas\5_configurar_energia.bat` > **Executar como administrador**.
2. Ele configura: *nunca suspender na tomada* e *tela apaga em 10 minutos*.
3. No final, ele abre sozinho a tela de **Opções de entrada** do Windows (próximo passo).

### 6.2 Senha ao acordar (escolha UMA opção)

**Opção A: Não pedir senha quando a tela acordar** (mais prático)
1. Na tela que abriu (**Configurações > Contas > Opções de entrada**), procure:
   *"Se você se ausentou, quando o Windows deve exigir que você entre novamente?"*
2. Escolha **"Nunca"**.
3. Ainda em Configurações, vá em **Personalização > Tela de bloqueio > Proteção de tela** e confira se **"Ao reiniciar, exibir a tela de logon"** está **desmarcado**.

**Opção B: Windows Hello** (mais seguro)
1. Em **Opções de entrada**, configure **Reconhecimento facial** ou **Impressão digital** (precisa de câmera ou leitor compatível).
2. Quando o Mestre acordar a tela, basta olhar para a câmera.

### 6.3 Teste
1. Com o Mestre ligado, diga: *"Mestre, desliga a tela"*.
2. Espere a tela apagar. Diga: *"E aí Mestre, bora trabalhar!"*
3. ✅ A tela deve acender, ele te cumprimenta e abre suas coisas.

> 💡 **Notebook:** deixe na tomada. Na bateria, o Windows continua suspendendo normalmente (de propósito, para não gastar bateria).

---

## Etapa 7: Ligar sozinho com o Windows

1. Dê dois cliques em `ferramentas\4_ativar_inicio_automatico.bat`.
2. Deve aparecer: **`[OK] O Mestre vai ligar sozinho...`**
3. A partir de agora, sempre que você entrar no Windows, o Mestre liga **escondido** (sem janela preta) e fala *"Mestre online"*.

- Para desligar o Mestre escondido: `ferramentas\8_parar_mestre.bat` ou diga *"Mestre, encerrar assistente"*.
- Para parar de ligar sozinho: `ferramentas\7_desativar_inicio_automatico.bat`.
- Para ver o que ele está fazendo: abra `logs\mestre.log` com o Bloco de Notas.

---

## Etapa 8: Ligar o seu Agente IPM do Claude

### Entenda primeiro
Os **Projetos do claude.ai** (como o seu agente IPM) **não têm uma "porta de acesso" (API)** para outros programas. Por isso existem dois caminhos:

| | **Modo "site"** (padrão) | **Modo "cérebro"** |
|---|---|---|
| Como funciona | O Mestre abre **seu projeto no claude.ai**, cola a pergunta e envia | O Mestre usa uma **cópia** das instruções do projeto e responde **por voz** |
| Usa o Claude de verdade? | ✅ Sim, com todas as instruções e arquivos do projeto | Só se usar a API paga (Etapa 10). Grátis = Ollama (Etapa 9) |
| Resposta | Na tela do Claude | Falada (e na tela, se for longa) |
| Custo | Grátis (usa sua conta do Claude) | Ollama: grátis / API: pago |
| Configuração | 2 minutos | 15 a 30 minutos |

👉 **Comece pelo modo "site".**

### 8.1 Modo "site" (recomendado)
1. No PC, abra **claude.ai** no navegador **padrão** e faça login (marque "manter conectado").
2. Entre no seu projeto **Agente IPM**.
3. Clique na **barra de endereço**, copie o link (`Ctrl+C`). Vai ser algo como:
   `https://claude.ai/project/0199a1b2-c3d4-...`
4. Abra o `config.yaml` com o Bloco de Notas (botão direito > Abrir com > Bloco de Notas).
5. Ache a seção **`agente_ipm:`** e troque o `link_projeto`:
   ```yaml
     link_projeto: "https://claude.ai/project/0199a1b2-c3d4-..."
   ```
6. Salve (`Ctrl+S`) e reinicie o Mestre.
7. Teste: *"Mestre, pergunta pro agente IPM como abrir um chamado de erro na folha"*.

✅ O Claude abre no projeto e, após ~7 segundos, a pergunta é colada e enviada.

**Ajustes:**
- Se colar **antes** da página carregar: aumente `segundos_para_carregar` para `10`.
- Se preferir revisar antes de enviar: `enviar_automaticamente: false` (ele só cola).
- Só *"Mestre, abre o agente IPM"* abre o projeto sem perguntar nada.

### 8.1b O agente IPM no dia a dia (versão 2)

Três jeitos de mandar um caso para o agente, conforme o tamanho:

| Situação | O que falar | O que acontece |
|---|---|---|
| **Pergunta rápida** | *"Mestre, agente IPM, como classifico um chamado de erro na folha?"* | Abre o projeto, cola e envia |
| **Caso longo** (ditado) | *"Mestre, ditado pro agente IPM"* → fale o caso em várias frases → *"pronto"* | Ele vai dizendo "anotado" a cada frase e envia tudo junto no final |
| **Texto de tela** (erro, log, e-mail) | Selecione o texto e aperte `Ctrl+C` → *"Mestre, manda o que eu copiei pro agente IPM e pergunta como resolver"* | Envia sua instrução + o texto copiado |

Durante o ditado:
- *"apaga a última"* → remove a última frase ditada.
- *"cancela"* → desiste sem enviar.
- Você **não** precisa falar "Mestre" entre as frases. Ele fica esperando por até 30 segundos de silêncio.

**Para ouvir a resposta:** quando o Claude terminar, clique no botão **Copiar** que aparece embaixo da resposta e diga *"Mestre, lê pra mim"*. Se a resposta for longa, ele fala o começo e abre o resto na tela.

**Outros jeitos de chamar o agente:** "agente IPM", "Claude da IPM", "assistente IPM"... Para ensinar outros, veja a Etapa 12.

**Dica de fluxo de trabalho:**
1. *"Mestre, bora trabalhar"* (a rotina já pode abrir o Atende.Net e o projeto IPM, basta colocar os links nela).
2. Achou um erro? Copie a mensagem → *"Mestre, manda o que eu copiei pro agente IPM e redige um chamado P031"*.
3. Resposta pronta → **Copiar** → *"Mestre, lê pra mim"*.

### 8.2 Modo "cérebro" (resposta falada)
1. Faça a **Etapa 9** (Ollama, grátis) ou a **Etapa 10** (Claude API, pago).
2. Copie as instruções do projeto: siga o arquivo `perfis\agente_ipm\COMO_PREENCHER.txt`.
3. No `config.yaml`, mude `modo: "site"` para `modo: "cerebro"`.
4. Reinicie o Mestre e pergunte.

> As **skills** que você já tem no Claude (*chamado-p031* e *arquivos-integracao-ipm*) podem ser copiadas para `perfis\agente_ipm\conhecimento\` como texto, para o modo cérebro seguir o mesmo padrão.

---

## Etapa 9 (opcional): Cérebro grátis com Ollama

Sem cérebro, o Mestre só entende os **comandos da lista**. Com o cérebro, ele **conversa e responde qualquer pergunta**.

O **Ollama** roda uma IA **no seu PC, de graça, sem internet**.

**Precisa:** 8 GB de RAM (16 GB é melhor). Com placa de vídeo fica bem mais rápido, mas não é obrigatório.

1. Entre em **https://ollama.com/download**, baixe a versão Windows e instale (Next, Next, Install).
2. Abra o **cmd** (`Windows + R` > `cmd`) e digite:
   ```
   ollama pull qwen2.5:7b
   ```
   (baixa ~4,7 GB. Em PC mais simples, use `ollama pull llama3.2:3b` com ~2 GB)
3. Teste no cmd: `ollama run qwen2.5:7b "diga oi em portugues"`. Deve responder. Digite `/bye` para sair.
4. No `config.yaml`, seção `cerebro:`, mude:
   ```yaml
     tipo: "ollama"
     ollama_modelo: "qwen2.5:7b"
   ```
5. Reinicie o Mestre e pergunte: *"Mestre, me explica o que é inflação em uma frase"*.

> ⚖️ **Honestamente:** a IA local é boa para o dia a dia, mas **bem mais fraca que o Claude** em análises complexas como as do IPM. Por isso o modo "site" é o padrão para o agente IPM.

---

## Etapa 10 (opcional, pago): Claude como cérebro

Use só se quiser respostas **faladas** com a qualidade do Claude.

- ⚠️ A **API é cobrada à parte** da assinatura do claude.ai (Pro/Max **não** incluem API). Cobra por uso; perguntas curtas custam centavos.
1. Crie a conta em **https://console.anthropic.com**, adicione créditos e crie uma **API key** (começa com `sk-ant-`).
2. No cmd, digite (trocando pela sua chave):
   ```
   setx ANTHROPIC_API_KEY "sk-ant-SUA-CHAVE-AQUI"
   ```
3. **Feche e abra** o Mestre (ou reinicie o PC).
4. No `config.yaml`: `tipo: "claude"`.
5. Dica de economia: em `claude_modelo`, `"claude-haiku-4-5"` é bem mais barato para conversas simples.

🔒 **Nunca** coloque a chave dentro do `config.yaml` nem mande para ninguém.

---

## Etapa 11: Atualizar para a versão 2

Você já tem a versão 1 instalada. Para atualizar **sem perder** o que configurou:

1. **Desligue o Mestre** (feche a janela preta ou rode `ferramentas\8_parar_mestre.bat`).
2. Baixe o arquivo **`mestre_atualizacao_v2.zip`**.
3. Botão direito > **Extrair tudo...** > escolha a **mesma pasta** onde o Mestre está (ex.: `C:\Mestre`). Assim a pasta `mestre` de dentro do zip cai em cima da sua.
4. Quando o Windows perguntar, escolha **"Substituir os arquivos no destino"**.
   - O zip de atualização **não traz** o `config.yaml`, então seu link do agente IPM, seus canais e suas rotinas ficam como estão.
5. Rode `ferramentas\2_testar_por_texto.bat` e digite: `pô mestre, bota aí o youtube`. Na janela deve aparecer `Entendi como: 'abre ai o youtube'`.

Não precisa instalar nada de novo, porque as bibliotecas são as mesmas.

> **Opcional:** as opções novas (conversa, personalidade, voz) agora se ajustam pelo **painel** (Etapa 16). Não precisa copiar nada para o `config.yaml`. Se já copiou e alguma seção ficou repetida, o painel conserta sozinho e guarda o original em `config.yaml.antes_do_conserto`.

---

## Etapa 12: Falar solto

A versão 1 exigia frases quase exatas. A versão 2 tem **três camadas** para entender o seu jeito de falar:

### 12.1 Vocabulário (automático)
Antes de procurar o comando, o Mestre "limpa e traduz" o que você falou:

```
Você fala:     "Pô Mestre, será que você consegue botar aí o YouTube pra mim?"
1. Tira enfeites:  "botar o youtube"
2. Troca sinônimos:  "abre o youtube"
3. Executa:  abre o YouTube ✅
```

A janela preta mostra a linha **`Entendi como: ...`**, então você vê exatamente o que ele entendeu.

Isso fica no arquivo **`vocabulario.yaml`** (abra com o Bloco de Notas). Ele tem 4 partes:
- **ignorar_no_inicio**: "o que eu quero fazer é", "você pode", "dá pra", "será que"...
- **ignorar_em_qualquer_lugar**: "por favor", "pra mim", "pô", "cara", "tipo"...
- **sinonimos**: todos os jeitos de dizer "abre" (bota, coloca, põe, mostra, quero ver...), "bora" (vamos, partiu...), etc.
- **atalhos**: frase curta → comando completo.

Achou um jeito de falar que ele não entende? Acrescente na lista de sinônimos certa. Exemplo: para ele entender "manda ver o YouTube", adicione `"manda ver"` na lista do `"abre"`.

### 12.2 Modo conversa (sem repetir "Mestre")
Depois de cada resposta, o Mestre **continua ouvindo por 10 segundos** sem precisar do "Mestre":

> **Você:** "E aí Mestre, abre o YouTube"
> **Mestre:** "Já é!"
> **Você:** "agora aumenta o volume" ← sem "Mestre"
> **Você:** "e desliga a tela daqui a pouco…" ← ainda dentro da janela

Frases que ele não entende durante essa janela são **ignoradas em silêncio** (para não responder à TV). Ajuste em `config.yaml` > `conversa` > `janela_segundos`.
Sem o "Mestre", um "abre ..." só vale se ele conhecer o que é para abrir; senão ignora em silêncio (ex.: "e colocar isso pra eu ver pelo Telegram" no meio de uma conversa).
A janela de 10 segundos só começa a contar **quando ele termina de falar**.

### 12.2b Conversa fluida: interromper e frase pela metade
- **Ele ouve enquanto fala.** Pode chamar no meio da resposta: "Mestre, para" faz ele **calar na hora**; "Mestre, abre o Spotify" faz ele parar **e** abrir. Enquanto ele fala, só vale frase que **começa com "Mestre"** (o resto é a própria voz dele saindo da caixa de som e é ignorado). Com fone de ouvido funciona melhor ainda; com caixa de som ajuda ligar "Responder só à minha voz" (Etapa 17.1).
- **Resposta longa começa logo:** ele fala a 1ª frase enquanto prepara as outras.
- **Frase pela metade espera o resto:** se você para no meio ("Mestre, eu queria…", "abre o site do…"), ele espera mais um pouquinho (1,5 s) e junta com o que vier depois, em vez de executar pedaços.
- Tudo isso fica no **painel > Áudio > Ajustes de captação**: "Ouvir enquanto fala", "Interromper com …", "Fala frase a frase" e "Espera se a frase parar no meio" (0 desliga). Salve e diga "Mestre, reinicia".

### 12.3 Atalhos ensinados por voz
Dois jeitos:

**Em diálogo:**
> **Você:** "Mestre, aprende um atalho"
> **Mestre:** "Bora! Qual frase você vai falar?"
> **Você:** "modo cinema"
> **Mestre:** "E quando você falar modo cinema, o que eu faço?"
> **Você:** "desliga a tela"
> **Mestre:** "Aprendido!"

**Numa frase só** (com uma pausa no meio):
> "Mestre, quando eu falar **hora do rock**, abre o último vídeo do Manual do Mundo"

- *"Mestre, quais são os atalhos?"* → lista os atalhos.
- *"Mestre, esquece o atalho modo cinema"* → apaga.
- Ficam salvos em `aprendido.yaml`.

### 12.4 Entender QUALQUER frase (opcional, com IA)
As três camadas acima são grátis e instantâneas, mas só entendem o que está no vocabulário. Para entender **qualquer** jeito de falar ("tô a fim de ver aquele canal de ciência"), ligue o cérebro (**Etapa 9**, Ollama grátis). Quando nenhum comando reconhecer a frase, a IA "traduz" para um comando ou responde conversando, com a personalidade do Mestre.

---

## Etapa 13: Voz e personalidade

### 13.1 Ouvir e escolher a voz
Duas formas:

**A) Pelo computador (todas as vozes):** dê dois cliques em **`ferramentas\9_escolher_voz.bat`**. Ele toca a mesma frase com cada voz disponível:
- **ENTER** → próxima voz
- **número** → escolhe essa
- **S** → sai

**B) Falando (vozes favoritas):**
- *"Mestre, apresenta as vozes"* → ele fala com cada uma das favoritas.
- *"Mestre, usa a voz do Andrew"* → escolhe essa.
- *"Mestre, muda a voz"* → passa para a próxima.

**Que vozes existem (grátis):**

| Voz | Tipo | Como soa |
|---|---|---|
| **Antonio** | pt-BR, masculina | A padrão. Clara, de "locutor" |
| **Francisca** | pt-BR, feminina | Clara e simpática |
| **Thalita** | pt-BR, feminina, *Multilingual* | Mais nova e mais expressiva |
| **Andrew**, **Brian** | Masculinas, *Multilingual* (EUA) | Falam português com entonação bem natural, de conversa, e um leve sotaque |
| **Ava**, **Emma** | Femininas, *Multilingual* (EUA) | Idem, femininas |
| **Remy**, **Giuseppe** | Masculinas, *Multilingual* (França/Itália) | Mais "personagem" |
| **Duarte**, **Raquel** | Português de Portugal | Sotaque lusitano |

> 💡 As vozes **Multilingual** foram feitas para conversa e costumam soar **menos robóticas**. Teste o **Andrew** e a **Thalita** primeiro. A lista exata depende da Microsoft, e o `ferramentas\9_escolher_voz.bat` mostra as que existem no dia.

### 13.2 Ajustar o jeito de falar
- *"Mestre, fala mais rápido"* / *"mais devagar"*
- *"Mestre, fala mais grave"* / *"mais agudo"*
- *"Mestre, voz normal"* → volta ao original

Tudo fica salvo e vale depois de reiniciar.

### 13.3 Personalidade
O Mestre não repete mais sempre a mesma frase. Ele sorteia entre várias ("Já é!", "Deixa comigo.", "Fala, chefe!"). Para mudar o jeito dele, edite a seção **`personalidade`** do `config.yaml` (veja o `config.yaml novo (instalação completa)`):
- **falas**: as frases de cada situação (ao ligar, quando você chama, quando não entende...). Pode colocar quantas quiser.
- **descricao**: como ele conversa quando o cérebro (IA) está ligado. Ex.: *"mordomo britânico, formal e irônico"* ou *"parceiro brasileiro, bem-humorado, me chama de chefe"*.

> ⚖️ **Honestamente:** as vozes grátis da Microsoft são das melhores gratuitas, mas ainda são "leitura de texto". Vozes com emoção de verdade (risos, pausas, sussurros), como a do ElevenLabs, são pagas. Dá para plugar depois, se quiser.

---

## Etapa 14: Melhorar o Mestre falando com ele

O que você fez agora (mandar ideias de melhoria para o Claude) pode virar rotina **por voz**:

```
Você:  "Mestre, anota uma melhoria: quero que ele leia minha agenda do Google de manhã"
       (repete quantas vezes quiser, ao longo dos dias)
Você:  "Mestre, aplica as melhorias"
       → abre uma janela com o Claude Code, que lê a lista e programa as mudanças
Você:  "Mestre, reinicia"   → volta com as novidades
```

- *"Mestre, lê minhas melhorias"* → fala a lista de pendentes.
- As ideias ficam em **`MELHORIAS.md`**. O Claude marca com `[x]` o que já fez.
- O arquivo **`CLAUDE.md`** é o "manual do projeto" que o Claude Code lê antes de mexer: ele explica como o Mestre é organizado e como testar.

### 14.1 Instalar o Claude Code (uma vez só)
O Claude Code já vem com a sua assinatura do Claude (Pro ou Max): **sem custo extra**.

1. Aperte `Windows`, digite **PowerShell** e abra.
2. Cole esta linha e aperte Enter:
   ```
   irm https://claude.ai/install.ps1 | iex
   ```
3. Feche e abra o PowerShell. Digite `claude` e Enter. Na primeira vez ele abre o navegador para você **entrar com sua conta do Claude**.
4. Pronto. Digite `/exit` para sair.
5. *(Opcional, recomendado)* Instale o [Git for Windows](https://git-scm.com/download/win) (Next, Next, Install). O Claude Code trabalha melhor com ele.

### 14.2 Como é trabalhar com ele
- Quando você diz *"Mestre, aplica as melhorias"*, abre uma janela preta com o Claude Code trabalhando.
- Ele **pede sua permissão** antes de mudar arquivos ou rodar comandos. Leia e aperte **Enter** para aceitar, ou escolha a opção de permitir sempre na sessão.
- No final, ele explica o que mudou e o que você deve testar. Você pode **conversar com ele ali mesmo** ("não gostei, deixa a voz mais baixa"), como faz comigo.
- Terminou? Feche a janela e diga *"Mestre, reinicia"*.

> 💡 **Prefere sem terminal?** O app **Claude para desktop** tem uma aba **Code** que faz o mesmo com janelas normais: abra a pasta do Mestre por lá e peça *"implemente o MELHORIAS.md"*.

> 🔒 **Segurança:** mantenha uma cópia da pasta do Mestre (ou conecte o GitHub) antes de pedir mudanças grandes. Se algo quebrar, é só voltar a cópia.

---

## Etapa 15: Atualizar para a versão 3

A versão 3 usa **duas bibliotecas novas** (a do painel e a que salva o config). Por isso, desta vez é preciso rodar o instalador de novo:

1. **Desligue o Mestre** (`ferramentas\8_parar_mestre.bat`).
2. Extraia o **`mestre_atualizacao_v3.zip`** por cima da pasta, como na Etapa 11 (**Substituir** tudo). Seu `config.yaml` não é tocado.
3. Rode o **`ferramentas\1_instalar.bat`** de novo. Ele só baixa o que falta, então é rápido.
4. Rode o **`ferramentas\10_painel.bat`**. O painel abre, e dali você ajusta tudo (Etapas 16 e 17).

> O que muda sozinho, mesmo com o config antigo: o Mestre passa a usar o **modo preciso** (o Whisper ouve toda frase, em vez do modelo leve), mede o ruído do ambiente ao ligar e mostra o **indicador** no topo da tela.

---

## Etapa 16: Painel de configurações

Chega de editar YAML no Bloco de Notas. Abra o painel de um destes jeitos:
- dois cliques em **`ferramentas\10_painel.bat`**;
- **duplo clique no indicador** (a pílula no topo da tela);
- falando: *"Mestre, abre o painel"*.

| Aba | O que dá para fazer |
|---|---|
| **Início** | Ver se o Mestre está ligado, ligar/reiniciar/desligar, abrir o guia, o log e os áudios de diagnóstico |
| **Áudio** | Escolher o microfone, **testar e calibrar** (Etapa 17), ajustar sensibilidade, ganho e modelo do Whisper |
| **Voz** | Escolher a voz numa lista, ajustar velocidade e tom com barras, **ouvir antes de salvar** |
| **Conversa** | Tempo do modo conversa, sua cidade (clima), personalidade e as frases que ele sorteia |
| **Agente IPM** | Modo, link do projeto, tempo de espera e envio automático |
| **YouTube** | Lista de canais e os botões para **importar suas inscrições** (Etapa 19) |
| **Programas e sites** | Adicionar programas com o botão **"Procurar programa no PC..."** e sites |
| **Rotinas** | Criar e editar rotinas: frases, ações numa lista com ↑ ↓ ✕ (Etapa 20) |
| **Atalhos** | Ver, editar e apagar os atalhos que você ensinou por voz |
| **Melhorias** | Ver e escrever a lista de ideias; botão **"Refinar e aplicar com o Claude Code"** |

> Na versão 2.5 o menu virou uma barra de ícones (pare o mouse em cima dela para ver os nomes). Onde fica cada página: veja a [Etapa 32](#etapa-32--versão-25).

Depois de mudar, clique em **"Salvar e reiniciar o Mestre"** (canto de baixo).
- O painel guarda uma cópia do arquivo antigo (`config.yaml.bak`) e **mantém seus comentários**.
- O `config.yaml` continua existindo, para quem quiser editar à mão.

---

## Etapa 17: Calibrar e testar o microfone

O problema de "ele não reconhece minha voz" quase sempre é um destes três:
1. O **limite de volume** está errado: sua voz fica abaixo dele e é tratada como silêncio.
2. O microfone está **baixo** (ou é o microfone errado).
3. O **modelo do Whisper** é pequeno demais para o seu PC ou para o seu jeito de falar.

A aba **Áudio** do painel resolve os três, nesta ordem:

1. **Microfone:** escolha o certo na lista (fone com microfone costuma ser melhor que o do notebook).
2. Clique em **"▶ Ligar teste"**. A barra mostra, ao vivo, o volume que chega ao Mestre. A **linha branca** é o limite.
   - Falando normal, a barra deve passar **bem** da linha e ficar **verde**.
   - Em silêncio, deve ficar **bem abaixo** da linha, em cinza.
3. Fique quieto e clique em **"Medir ruído (3s de silêncio)"**. O limite é ajustado sozinho para o seu ambiente.
4. Se ao falar a barra mal passa da linha, aumente o **Ganho** (ex.: 2.0).
5. Clique em **"● Gravar frase"** e fale como falaria com o Mestre: *"E aí Mestre, abre o último vídeo do Manual do Mundo"*. A gravação para sozinha quando você faz uma pausa.
6. Clique em **"Ouvir gravação"**: é **exatamente** o que chega ao Mestre. Cortou o começo ou o fim? Ajuste o limite ou a "Pausa que encerra a frase".
7. Clique em **"Transcrever"**: mostra o que o Whisper entendeu e quanto tempo levou.
   - Errou palavras? Troque o **Modelo** para `medium` (ou `large-v3-turbo`) e/ou o **Capricho** para `preciso`, e clique em Transcrever de novo. Compare.
   - Ficou lento demais (mais de 3–4 s)? Volte para `small` ou `base`.
8. **Salvar e reiniciar o Mestre.**

**Qual modelo usar:**

| Modelo | Qualidade | Tempo típico por frase (PC sem placa de vídeo) |
|---|---|---|
| `base` | razoável | ~0,5 s |
| `small` | boa (padrão) | ~1–2 s |
| `medium` | muito boa | ~3–6 s |
| `large-v3-turbo` | a melhor, perto da transcrição deste chat | lento sem placa NVIDIA; rápido com ela |

> 💡 **Tem placa de vídeo NVIDIA?** Veja o que diz a linha **"Onde rodar o Whisper"** na aba Áudio.
> - Se disser **"faltam as bibliotecas"**, rode o **`ferramentas\11_ativar_placa_de_video.bat`**. Ele baixa cerca de 1,5 GB de bibliotecas da NVIDIA e testa a placa no final.
> - Com a placa pronta, o `large-v3-turbo` fica rápido. A transcrição do chat do Claude roda em servidores enormes; no seu PC, esse modelo é o que chega mais perto.
> - Enquanto a placa não estiver pronta, o Mestre usa o processador sozinho, sem erro.

**Modo de detecção** (na mesma aba):
- **Preciso (Whisper ouve tudo):** padrão da versão 3. Entende bem melhor, mas usa mais o processador quando há conversa ao redor.
- **Leve (Vosk procura "Mestre"):** o jeito da versão 1/2. Quase não pesa, mas erra mais para ativar.

**Diagnóstico contínuo:** ligue **"Guardar áudios ouvidos"**. O Mestre guarda as últimas 30 frases em `logs\audios`, com o arquivo `transcricoes.txt` mostrando o que ele entendeu de cada uma. Assim você ouve o que chegou quando algo der errado. O botão **"Áudios de diagnóstico"** da aba Início abre a pasta.

### 17.1 Responder só à sua voz

Um vídeo tocando na caixa de som (ou outra pessoa na sala) pode dizer algo parecido com o nome dele, e ele obedecia.
Agora ele pode **comparar cada pedido com a sua voz** e ignorar as outras. Roda no seu PC, grátis
(um modelo de uns 85 MB, baixado na primeira vez para `modelos\locutor_ecapa`).

**Cadastrar (uma vez só):**
1. Painel > **Áudio** > cartão **"Minha voz"** > **"● Cadastrar minha voz"**.
2. Aparece uma frase na caixinha. Leia em voz alta, do seu jeito normal, no lugar onde você costuma falar com ele.
   Quando você faz uma pausa, ele passa sozinho para a próxima. São 10 frases (menos de 1 minuto).
   Errou ou quer parar? Clique em **"■ Parar cadastro"** (nada é salvo).
3. No fim, a chave **"Responder só à minha voz"** liga sozinha. A sua "impressão de voz" fica guardada
   fora da pasta do projeto, em `%APPDATA%\Mestre\voz_dono.json`.
4. Clique em **Salvar e reiniciar**.

**Testar:**
1. Clique em **"Testar"** e fale uma frase normal. Aparece a **nota** (de 0 a 1): sua voz costuma dar 0,55 ou mais.
2. Agora ponha um vídeo com alguém falando para tocar na caixa de som e clique em **"Testar"** de novo, sem falar.
   A nota do vídeo deve ficar **abaixo** da exigência (padrão 0,40) e aparecer "não reconhecida".
3. Depois de reiniciar, faça o teste de verdade: com o vídeo tocando, fale um pedido normal (ele deve obedecer).
   Quando o vídeo disser algo parecido com o nome dele, ele deve ficar quieto. No Histórico aparece
   "(ignorado: voz não reconhecida, nota ...)".

**Régua "Quão exigente":**
- Ele está ignorando **você**? Puxe a régua para a esquerda (ex.: 0,30) ou refaça o cadastro no lugar/microfone de sempre.
- O **vídeo** ainda passa? Puxe para a direita (ex.: 0,50).
- Frases bem curtas (menos de 1 segundo, como "sim", "não") têm pouca voz para comparar: dentro da conversa
  elas passam, e fora dela a exigência fica um pouco menor.
- Logo depois de ligar, o reconhecimento da voz leva alguns segundos para carregar; nesse meio-tempo ele aceita qualquer voz.
- **Áudios do celular/Telegram** não passam por essa verificação (o Telegram já sabe que é você).
- Quer desligar? Desligue a chave (ou **"Apagar cadastro"**) e salve.

### 17.2 Detector local da palavra (opcional, começa desligado)

Hoje o Whisper transcreve **toda** frase que passa do limite de volume, inclusive o vídeo que está tocando
(nos seus registros, 2 de cada 3 frases transcritas não tinham "Assessor"). O detector local é um "ouvido"
bem leve (uns 2% de UM núcleo do processador) que procura só a palavra. Ligado, só vai para o Whisper a frase
em que ele ouviu "Assessor": menos processador e placa de vídeo gastos à toa e menos chance de o vídeo disparar
um comando. Dentro da conversa, na espera depois de "Assessor", no ditado e no modo descanso ele não filtra nada.

**1. Treinar (uma vez, uns 20 a 40 minutos, grátis, no seu PC):**
1. Rode o **`ferramentas\15_treinar_palavra.bat`**.
2. Ele pergunta se você quer **gravar a sua voz falando a palavra 30 vezes** (responda `s`: é o que mais
   melhora o acerto; varie o jeito: normal, baixo, alto, rápido, longe do microfone, com "ô"/"e aí" antes).
3. Ele pergunta se quer **gravar 5 minutos do ambiente** com um vídeo tocando (responda `s` e NÃO fale a
   palavra nesse tempo: ele aprende o que ignorar).
4. O resto é sozinho: vozes do PC (Kokoro) e da internet (Edge) falando a palavra de vários jeitos, frases que o
   microfone já ouviu sem a palavra, ruídos. No fim aparece quanto ele acerta nas **suas gravações reais**.
   O modelo fica em `modelos\palavra\assessor.npz` (se mudar a palavra de ativação, treine de novo).

**2. Ligar:** painel > **Áudio** > **"Detector local da palavra"** > ligar > **Salvar e reiniciar**.
A linha embaixo diz se o modelo está pronto ou "Modelo não encontrado".

**3. Ajustar:**
- Ele não te ouve (você chama e nada)? Puxe **"Exigência do detector"** para a esquerda (ex.: 0,30) ou treine de
  novo com mais gravações suas. Os descartes aparecem no `memoria\ouvido.jsonl` com o motivo
  "sem a palavra (detector local)" e a nota dele.
- O vídeo ainda passa? Puxe para a direita (ex.: 0,70). O Whisper continua conferindo a palavra depois.
- Deu problema? Desligue a chave: volta ao jeito de sempre.

---

## Etapa 18: O indicador na tela

### Texto + robô (padrão a partir da 2.6)

Um **robozinho rosa** fica **logo acima do relógio** (canto de baixo, à direita), sempre por cima das janelas e
sem botão na barra de tarefas. Em cima dele fica um **balão de texto bem legível** dizendo o que está
acontecendo — mais fácil de entender do que só os símbolos do robô:

| Balão | Significa |
|---|---|
| (sem balão) | Ligado, ouvindo em silêncio — tela limpa |
| "Gravando…" / "Ouvindo…" | Detectou sua voz / modo conversa (sem precisar repetir a palavra) |
| "Pensando: *resumo da sua pergunta*" (e "· Na fila: N" se tiver mais pedidos esperando) | A IA está pensando |
| "Falando…" | Respondendo |
| "Pausado" | Microfone em pausa |
| "Descansando" | Modo descanso: só *"bora voltar a trabalhar"* acorda |
| "Ligando…" / "Desligando…" | Iniciando ou encerrando o assistente |

O robô fica **menor** enquanto o balão está ativo, e a cor da borda do balão muda com a situação (verde
ouvindo, roxo pensando, azul-claro falando). Selo verde com ✓ = a resposta pensada está pronta: diga
*"pode falar"*.

- **Arraste** para onde quiser (ele lembra o lugar). **Duplo clique** abre o painel.
- **Passe o mouse** por cima: o que ele está fazendo, a última frase que ouviu e a última resposta.
- **Botão direito:** Pausar/Retomar a escuta, Abrir painel, **Voltar ao lugar padrão** e **Esconder avatar** (volta quando reiniciar).
- Prefere só o robô, sem o balão? Painel > **Aparência** > "Indicador na tela" > **Só robô**. Prefere a
  bolinha de antes? Escolha **Bolinha**. Salve e reinicie.
- O avatar usa a biblioteca grátis **PySide6** (o INSTALAR_E_CRIAR_ATALHO.bat e a atualização instalam). Se ela
  faltar ou der erro, aparece a bolinha sozinha.
- Ele gasta muito pouco: parado quase nada, e quando está pausado não desenha nada.

O ícone do programa (atalho, bandeja do relógio e menu do painel) também mudou: é o **"A" com uma onda de voz
verde** no lugar da barra, na cor de destaque que você escolher na Aparência.

### A bolinha (opção)

Uma pílula pequena fica **no topo da tela, sempre visível**, mostrando o que o Mestre está fazendo:

| Cor | Mensagem | Significa |
|---|---|---|
| 🟢 verde | Ouvindo · diga "Mestre" | Ligado e esperando |
| 🔴 vermelho (piscando) | Gravando sua voz... | Detectou fala e está gravando |
| 🟠 laranja | Entendendo... | O Whisper está transcrevendo |
| 🔵 azul | Fazendo: *comando* | Executando o que você pediu |
| 🟣 roxo | Pensando... | A IA (cérebro) está pensando |
| 🩵 azul-claro | *o que ele está falando* | Falando |
| 🟢 verde | Pode falar sem "Mestre" (7s) | Modo conversa, com contagem regressiva |
| ⚪ cinza | Pausado | Microfone em pausa |

- A **barrinha** embaixo do texto é o volume do microfone ao vivo, e o risco é o limite. Ótimo para ver se ele está te ouvindo.
- **Passe o mouse** por cima: aparece a última frase que ele ouviu e a última resposta.
- **Arraste** para onde quiser (ele lembra o lugar). **Duplo clique** abre o painel.
- **Botão direito:** abrir painel, **pausar/retomar a escuta** (ótimo para reuniões), reiniciar, desligar.
- Não quer o indicador? No painel ou no `config.yaml`: `indicador > mostrar: false`.

---

## Etapa 19: Inscrições do YouTube

Em vez de cadastrar canal por canal, traga **todas as suas inscrições**. Na aba **YouTube** do painel:

**Jeito 1: Google Takeout (funciona sempre, recomendado)**
1. Clique em **"Como exportar do Takeout?"**. Ele abre o site e mostra os passos:
   - clique em **Desmarcar tudo**;
   - marque **YouTube e YouTube Music**;
   - em **"Todos os dados do YouTube incluídos"**, deixe só **inscrições**;
   - **Criar exportação**.
2. O Google manda um e-mail com o link (alguns minutos). Baixe e extraia o .zip.
3. No painel: **"Importar do Google Takeout (.csv)"** → escolha o arquivo `inscricoes.csv` (ou `subscriptions.csv`).
4. Os canais aparecem na lista. Se quiser, **renomeie** para o jeito que você fala (ex.: "Manual do Mundo" → "manual"). Clique em **Salvar**.

**Jeito 2: pelo Firefox (se você usa Firefox logado no YouTube)**
- Feche o Firefox e clique em **"Importar do Firefox"**.
- O Chrome e o Edge **bloqueiam** isso desde 2024, por segurança. Nesses, use o Takeout.

Depois é só falar: *"Mestre, abre o último vídeo do <canal>"*. Os nomes dos canais também ajudam o Whisper a reconhecer esses nomes quando você fala.

---

## Etapa 20: Rotinas mais ricas

Novas ações para as rotinas (na aba **Rotinas** do painel, no botão **"+ Adicionar ação"**):

| Ação | O que faz |
|---|---|
| Falar a data de hoje | "Hoje é sexta-feira, 25 de setembro." |
| Falar o clima | Temperatura, mínima/máxima e aviso de chuva (grátis, sem cadastro). Cidade na aba Conversa |
| Ler manchetes | As principais notícias do Google Notícias (você escolhe quantas) |
| Ler minhas anotações | As últimas notas que você ditou |
| Avisar melhorias pendentes | "Você tem 3 melhorias anotadas" |
| Abrir pasta | Qualquer pasta do PC (ex.: a pasta do trabalho) |
| Qualquer comando falado | Qualquer coisa que você falaria, ex.: "toca lofi no youtube" |

A versão 3 já vem com (no `config.yaml` novo; no antigo, crie pelo painel):
- **Bora trabalhar:** liga a tela, cumprimenta, fala a data e o clima, abre e-mail e Claude, lê suas notas e avisa as melhorias.
- **Bom dia:** cumprimenta, fala data, clima e 3 manchetes.

Também dá para falar direto: *"Mestre, como tá o tempo?"*, *"vai chover?"*, *"quais as notícias?"*, *"notícias sobre tecnologia"*.

### Ensinar uma rotina falando (sem abrir o painel)

1. Fale: *"Assessor, vou te mostrar uma nova rotina"* (também vale *"grava uma rotina"*, *"aprende uma rotina nova"*, *"quero te ensinar uma rotina"*).
2. Fale os comandos um de cada vez, do jeito de sempre: *"Assessor, abre o Gmail"*, *"Assessor, abre o Claude"*, *"Assessor, toca a playlist Foco no Spotify"*. **Cada um já acontece na hora** e fica gravado.
   - Para a rotina falar algo: *"fala assim: bom trabalho!"*. Para esperar: *"espera 5 segundos"*.
   - O que não dá para repetir (conversa com a IA, ditado, "desliga"...) ele avisa: *"Esse passo não entra na rotina."*
3. No fim fale *"pronto"* (ou *"terminei"*, *"fim da rotina"*). Ele pergunta: *"Rotina aprendida. Qual frase eu uso para chamar?"*
4. Fale a frase, por exemplo *"modo mergulho"*. Se ela já for de outro comando, ele pede outra.
5. Ele salva a rotina no `config.yaml` (aparece no painel, aba **Rotinas**). Com a IA ligada, ela inventa em segundo plano uns 50 outros jeitos de pedir (*"partiu modo mergulho"*, *"bora pro modo mergulho"*...), tira as repetidas e as que roubariam outros comandos (tipo "abre o Gmail" ou "pausa"), e ele avisa quantas frases ficaram. Sem IA, ficam a sua frase e alguns jeitos simples (*"rotina modo mergulho"*, *"roda a rotina modo mergulho"*...).

Desistiu no meio? *"cancela a rotina"* sai sem salvar nada.

**Ideias para a sua rotina de trabalho** (monte no painel):
- Abrir o **Atende.Net** e o **projeto do agente IPM** (ação "Abrir site").
- Abrir a **pasta dos arquivos de integração** (ação "Abrir pasta").
- **Volume** baixo e "desligar a tela" numa rotina "modo reunião".

---

## Etapa 21: Refinar seus pedidos

### A skill "refinar-pedido"
Você fala as ideias soltas, do jeito que vem (como faz aqui comigo). A skill **refinar-pedido** transforma isso num pedido organizado:
- separa cada ideia;
- escreve o que você quer;
- define como saber que ficou pronto;
- aponta limites reais;
- faz perguntas com sugestão de resposta, para você só confirmar.

Ela é usada em **dois lugares**:
1. **No Claude Code do seu PC (automático):** a skill fica em `.claude\skills\refinar-pedido` dentro da pasta do Mestre. Quando você diz *"Mestre, aplica as melhorias"*, o Claude Code refina cada ideia, **mostra para você confirmar** e só depois programa. Também dá para chamar à mão, dentro do Claude Code: `/refinar-pedido <sua ideia>`.
2. **No claude.ai (aqui no chat):** envie o arquivo **`refinar-pedido.zip`** no mesmo lugar onde você enviou as skills do IPM (Configurações do claude.ai, na parte de Skills). Aí, em qualquer conversa, peça *"refina esse pedido: …"*.

### Projetos parecidos (grátis, no GitHub)
Pesquisei projetos abertos com a mesma ideia. O que aproveitamos de cada um:

| Projeto | O que é | O que o Mestre aproveitou |
|---|---|---|
| [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT) | Biblioteca de voz para texto em tempo real (detecção de voz + palavra de ativação + faster-whisper) | A ideia de sinais de "começou/parou de gravar" (o indicador) e os ajustes do Whisper (beam, filtro de voz) |
| [openWakeWord](https://github.com/dscripka/openWakeWord) | Detector de palavra de ativação treinável | Candidato futuro: treinar um detector só para "Mestre" (mais leve que o Whisper) |
| [Raziel](https://github.com/sourajit-ayush/Raziel) | Assistente offline para Windows (openWakeWord + faster-whisper + Ollama + Piper) | Confirma a arquitetura do Mestre. Ideias de controle do PC |
| [whisper-local](https://github.com/drajb/whisper-local) | Ditado offline com tecla de atalho (push-to-talk) | Ideia futura: **segurar uma tecla para falar**, sem precisar dizer "Mestre" |
| [local-voice-assistant](https://github.com/DownTheMyrWash/local-voice-assistant) | Assistente local com Ollama + faster-whisper + Coqui TTS | Referência para o cérebro local |

---

## Etapa 22: Versão 4

**Para atualizar:** feche o Mestre, extraia o **`mestre_atualizacao_v4.zip`** por cima da pasta (**Substituir**) e abra o `ferramentas\10_painel.bat`. Não precisa rodar o instalador: as bibliotecas são as mesmas da versão 3. O seu `config.yaml` não é tocado, e as opções novas usam valores padrão até você mudar no painel.

### 22.1 Pedidos longos: o ditado
Antes, uma pausa de 0,8 segundo encerrava a frase: se você parasse para pensar, ele cortava. Agora:
- **Frases normais** podem ter até **60 segundos** (ajuste em Painel > Áudio > "Tamanho máximo de uma frase").
- **Pedidos longos, do tamanho que você quiser:**
  1. *"Mestre, vou ditar"*.
  2. Fale à vontade, com pausas para pensar. Ele anota **em silêncio**, e o indicador mostra *"Ditando · 3 trechos"*.
  3. *"apaga a última"* tira o último trecho; *"cancela"* desiste de tudo.
  4. *"pronto"* encerra. Ele pergunta: *"Mando pro agente IPM, salvo como melhoria, anoto ou copio?"*
- Atalhos que já dizem o destino: *"Mestre, ditado pro agente IPM"* e *"Mestre, ditar uma melhoria"*.
- O ditado termina sozinho depois de 60 segundos de silêncio (ajustável em Painel > Áudio).

É o jeito de fazer **dentro do Mestre** o que você faz aqui no chat: ditar a ideia inteira, que vira um item de melhoria para o Claude Code.

### 22.2 Feedback falado
Quando ele errar, logo em seguida:
- *"Mestre, isso tá errado, era Canção Nova"*, ou
- *"Mestre, você errou"* → ele pergunta *"O que era pra eu ter feito?"*.

Ele guarda no `MELHORIAS.md`:
- o que **ouviu**;
- o que **entendeu**;
- o que **respondeu**;
- a sua **correção**;
- o **áudio** daquele momento, em `logs\feedback`.

No *"Mestre, aplica as melhorias"*, o Claude Code usa isso para corrigir.

### 22.3 Nomes, palavra de ativação e personalidade
Tudo no **Painel > Personalidade**:
- **Nome do assistente:** como ele se apresenta.
- **Como ele te chama:** o seu apelido. Todas as frases passam a usar esse apelido.
- **Palavra de ativação:** "mestre" por padrão. Troque por outra palavra (ex.: "jarvis") e salve. Os jeitos parecidos são gerados sozinhos. Escolha uma palavra fácil de falar e pouco comum na conversa.
- **Estilo:** 5 estilos prontos, cada um com 5 a 15 frases por situação:
  - Parceiro brasileiro
  - Mordomo elegante
  - Estilo Jarvis
  - Coach animado
  - Sério e direto
- **Como usar os estilos:** escolha um e clique em **Aplicar estilo**. As frases aparecem nas caixas, e você edita do seu jeito (uma por linha, com `{apelido}`, `{nome}` e `{saudacao}`). Frase apagada no painel não volta.
- **Situações novas:** quando você agradece ("valeu") e ao desligar.

### 22.4 Mais rápido e menos robótico
- **Ao ligar**, ele cumprimenta **na hora**. O indicador mostra *"Carregando o ouvido..."* até o reconhecimento de voz ficar pronto.
- **Frases fixas** ("Pois não?", "Já é!", "Abrindo…") ficam guardadas prontas e saem instantâneas a partir da segunda vez.
- **Respostas longas** começam a tocar a primeira frase enquanto as outras são preparadas.
- **Fala fluida** (Painel > Voz, ligada por padrão): tira as vírgulas que viram aquela pausa "de robô". Teste com e sem no botão **Ouvir**.
- As vozes marcadas com **★** (Multilingual) são as mais naturais.

### 22.5 Pesquisas com acento
*"toca Canção Nova no YouTube"* pesquisa **"Canção Nova"**, com acento e cedilha. Antes saía "cancao nova". Vale também para a pesquisa no Google e para nomes de canal.

### 22.6 Painel novo
Modo escuro com detalhes em rosa claro, menu lateral com ícones, fonte Segoe UI e explicação curta em cada opção. A página **Início** mostra o estado do Mestre e as frases novas que você pode usar.

### 22.7 A skill de refinar pedidos aqui no Claude
Você já enviou a skill **refinar-pedido** para o claude.ai. Para usar numa conversa, cole ou dite o pedido e peça *"refina esse pedido"*. Ele volta organizado em cartões, como os desta versão, para você confirmar antes de qualquer implementação.

## Etapa 23: Versão 5

### 23.1 Atualizar (só desta vez, com 2 cliques)
1. Feche o painel. Se o Mestre estiver ligado, desligue (botão direito no indicador > Desligar).
2. Extraia o **`mestre_atualizacao_v5.zip`** por cima da pasta do Mestre (**Substituir**).
3. Dê dois cliques em **`INSTALAR_E_CRIAR_ATALHO.bat`**, na pasta principal. Ele:
   - instala 2 bibliotecas novas, pequenas: a do ícone perto do relógio;
   - cria o atalho **Mestre** na área de trabalho e no menu Iniciar, com ícone próprio;
   - guarda os `.bat` antigos na pasta **`ferramentas`**;
   - abre a Central.

**Das próximas vezes**, sem extrair nada: Central > **Atualizar o Mestre (.zip)** e escolha o arquivo que eu mandar. Suas configurações, notas e melhorias não são tocadas, e uma cópia do que foi trocado fica em `logs`.

### 23.2 O atalho único e a Central
Um clique no atalho **Mestre**:
1. liga o Mestre, se ele estiver desligado (dá para desligar isso na Central);
2. abre a **Central**, que é o painel. Na página **Início**:
   - **Ligar**, **Reiniciar**, **Pausar escuta** e **Desligar**;
   - **Testar digitando**: o antigo `2_testar_por_texto`;
   - **Teste automático**: confere o básico sozinho (veja 23.5);
   - **Atualizar o Mestre (.zip)**.

Clicou no atalho com a Central já aberta? Ela só vem para a frente. Não abre uma segunda janela.

### 23.3 Ícone perto do relógio
Com o Mestre ligado, aparece um ícone rosa com "M" perto do relógio do Windows. Se não aparecer, clique na setinha **^** ao lado do relógio.
- **Clique:** abre a Central.
- **Botão direito:** Pausar a escuta, Reiniciar ou Desligar.

### 23.4 O que foi consertado
- **Painel que não abria:** as 1.901 inscrições viravam uns 7.600 pedacinhos de tela montados de uma vez. Aqui no teste eram 43 segundos; no Windows, com dois monitores, bem mais. Agora abre em cerca de 3 segundos.
  - A lista mostra 40 canais por vez. Use a **busca** para achar os outros.
  - **Testar** abre o canal no navegador.
  - **Apagar todos os canais** limpa a lista, se você quiser recomeçar.
- **Programa com o mesmo nome de um canal:** entre 1.901 inscrições é fácil existir um canal "Spotify" ou "Discord". Antes, *"abre o spotify"* ia para o YouTube. Agora **programa e site ganham do canal**.
- **Caminho de programa com aspas:** o "Copiar como caminho" do Windows coloca aspas no caminho, e antes ele não abria. Agora abre.
- **Programa novo fora do lugar:** ele era salvo embaixo do título "SITES" no config. Agora fica no lugar certo.
- **Botão Testar** em cada programa e site. Se o caminho estiver errado, ele avisa na hora.
- **Rotinas: "▶ Salvar e testar"** roda a rotina pela primeira frase dela, igual a quando você fala. Se essa frase já disparar **outra** rotina, ele avisa para você trocar.
- **Menos peso na IA e no reconhecimento de voz:** os 1.901 nomes de canal não vão mais inteiros para eles.

### 23.5 Teste automático
Central > **Teste automático** (ou `ferramentas\12_teste_automatico.bat`). Ele trabalha numa **cópia** da pasta e nada abre de verdade. O teste:
1. abre o painel com 2.000 canais;
2. adiciona programa, site, canal e rotina, e salva;
3. confere o arquivo;
4. fala os comandos por escrito;
5. testa a atualização por .zip.

No fim mostra **OK** ou **FALHOU** em cada item. O Claude Code roda esse mesmo teste antes de entregar melhorias.

### 23.6 Onde foram parar os .bat
Na pasta **`ferramentas`**, com os mesmos nomes. Você quase não precisa mais deles. Os que ainda servem para emergência:
- `10b_painel_diagnostico.bat`: se a Central não abrir, mostra o motivo;
- `3_iniciar_mestre.bat`: liga o Mestre com a janela preta visível, para ver o que ele ouve;
- `4_ativar_inicio_automatico.bat`: faz o Mestre ligar junto com o Windows. **Se você já tinha ativado, rode de novo**, porque o caminho mudou.

## Etapa 24: Versão 6

### 24.1 Atualizar
Abra a Central (atalho **Mestre**) > **Atualizar o Mestre (.zip)** e escolha o **`mestre_atualizacao_v6.zip`**. Pronto: ele troca os arquivos, confere as bibliotecas e reabre sozinho. Não precisa extrair nada.

### 24.2 Ditar melhorias (e mandar para o lugar certo)
1. *"Mestre, quero ditar melhorias"*.
2. Fale o quanto quiser, com pausas para pensar. O indicador mostra **"Ditando 1:20 · diga finalizei"**.
3. Termine com **"finalizei"** ou **"terminei"** (ou "pronto" dito sozinho). "Manda", "envia" ou "pronto" no meio de uma frase **não** encerram mais.
4. Abre uma janelinha com o texto: corrija o que quiser.
5. Escolha o destino **clicando** ou **falando**:

| Você fala | Vai para |
|---|---|
| "manda", "pro projeto", "pro Claude Code", "pras melhorias" | **Projeto Mestre**: salva no `MELHORIAS.md`, abre a conversa do Claude Code e cola o texto |
| "pro agente", "pro IPM" | **Agente IPM** |
| "só salva" | Só a lista de melhorias |
| "copia" | Área de transferência (Ctrl+V) |
| "cancela" | Descarta |

Também funciona:
- *"Mestre, vou ditar"*: no fim, ele pergunta o destino;
- *"Mestre, ditado pro agente IPM"*: já vai para o agente.

Detalhes:
- **Silêncio:** se você ficar 3 minutos calado, ele fecha o ditado **sem perder o texto**. O tempo muda em Painel > Áudio.
- **Onde ajustar a conversa:** o link fica em Painel > **IPM e projeto**. Já vem apontando para esta conversa do Claude Code.
- **Texto inteiro:** o que você fala enquanto ele transcreve o trecho anterior também entra. Antes, isso se perdia.
- **Acentos:** o texto sai do jeito que foi falado, com acentos e pontuação.

### 24.3 Quando a IA (Ollama) demora
- Se passar de **10 segundos**, ele avisa *"Tá demorando. Te aviso quando terminar."* e **volta a te ouvir**. Comandos simples funcionam enquanto isso.
- No indicador aparece uma **segunda bolinha**:
  - **roxa, "Pensando… 23s"**: a IA ainda está pensando;
  - **verde, "Concluído"**: a resposta está pronta. Ele avisa *"Terminei de pensar. Quer ouvir?"* e **não fala a resposta sem você pedir**.
- Para ouvir: *"pode falar"*, *"qual a resposta?"* ou clique na bolinha verde.
- *"espera"*: a resposta continua guardada.
- *"cancela"* ou *"para de pensar"*: descarta.

Em Painel > **Conversa**:
- os tempos;
- o jeito de avisar: por voz, só na tela ou falando direto;
- o **modelo do Ollama**. Um modelo mais leve (`llama3.2:3b`) responde bem mais rápido.

### 24.4 Nome novo em todo lugar
Trocou o nome ou a palavra de ativação (ex.: Jarvis)? O indicador passa a mostrar *"diga Jarvis"*. O menu, o ícone, a Central e os botões usam o nome escolhido. O teste automático confere isso.

### 24.5 Aparência
Painel > **Aparência**:
- **Cor de destaque:** 6 cores prontas ou "Escolher cor...";
- **Fundo:** Grafite, Preto ou Azul-noite;
- **Fonte:** 6 opções;
- **Tamanho do texto:** Normal, Grande ou Maior.

A **prévia** muda na hora. **Aplicar** reabre a Central com o visual novo, e o ícone perto do relógio muda de cor junto. O ícone do atalho da área de trabalho às vezes demora a atualizar, porque o Windows guarda uma cópia.

### 24.6 Páginas nas listas
Canais, programas, sites e atalhos agora têm **◀ Anterior · Página 3 de 48 · Próxima ▶**. A busca filtra **enquanto você digita**, sem precisar de Enter; **✕ Limpar** volta tudo.

### 24.7 Skills: corrigir a transcrição e refinar
- Nova skill **corrigir-transcricao**: arruma o texto ditado (ex.: "OLA" → Ollama, "EPM" → IPM, "cloud code" → Claude Code) sem mudar o sentido.
- A **refinar-pedido** passou a chamar essa correção primeiro. A resposta começa com **"Entendi assim:"**, e depois vêm os cartões.
- **No Claude Code do projeto** já vale sozinho: a regra está no `CLAUDE.md`, e um lembrete automático roda a cada mensagem.
- **No claude.ai:** envie os dois .zip (`corrigir-transcricao.zip` e o `refinar-pedido.zip` novo) no mesmo lugar de antes (Configurações do claude.ai, parte de Skills). O novo substitui o antigo.

## Etapa 25: Versão 7

### 25.1 Atualizar
Central > **Atualizar o Mestre (.zip)** > escolha o **`mestre_atualizacao_v7.zip`**.

### 25.2 Atualizar o Ollama (a IA grátis)
1. **Prompt de Comando** → `ollama --version` mostra a versão.
2. Baixe o instalador em **ollama.com/download** e instale por cima. Nada se perde. Outro jeito: o ícone da lhama perto do relógio pode mostrar **"Restart to update"**.
3. `ollama list` mostra os modelos instalados.
4. Baixe um modelo rápido. Dá para fazer pelos botões do Painel > **Conversa**:
   - `ollama pull llama3.2:3b` (leve, uns 2 GB);
   - `ollama pull gemma3:4b` (bom em português).
5. Painel > Conversa > **Modelo do Ollama**: escolha na lista, que mostra o que está instalado, e salve.
6. Apague o modelo antigo com `ollama rm <nome>`, se quiser liberar espaço.

O Mestre agora **carrega o modelo ao ligar** e o mantém carregado por 1 hora, então a primeira pergunta não demora mais que as outras.

### 25.3 Ditado vai para o app Claude
No fim do ditado de melhorias, *"manda"* faz o Mestre:
1. trazer a janela do **app Claude** para a frente (ele abre o app, se estiver fechado);
2. clicar na caixa de mensagem, colar e enviar.

O texto chega com o aviso para eu corrigir a transcrição e refinar.
- **Deixe o app aberto nesta conversa**: ele cola na conversa que estiver aberta.
- **Se clicar no lugar errado**, ajuste em Painel > **IPM e projetos** > "Onde fica a caixa de texto".
- **Outras opções:** *Claude Code no terminal* (o mais garantido, numa conversa nova) ou *Navegador*.
- **Se nada aparecer:** o texto fica **copiado**; é só dar Ctrl+V.

### 25.4 Histórico e memória
- **Nada se perde:** respostas da IA ficam guardadas mesmo que você não as ouça.
- **Por voz:**
  - *"repete a resposta"*;
  - *"lê as últimas respostas"*;
  - *"o que você respondeu sobre relatividade?"*.
- **Memória:** *"lembra que eu trabalho na IPM de manhã"* fica guardado, e a IA usa isso nas respostas.
  - *"o que você lembra de mim?"* lê a lista;
  - *"esquece que…"* apaga.
  - **Por assunto:** os fatos ficam separados em `memoria/fatos/` (pessoas, projetos, preferências, casa,
    trabalho, geral) e não num arquivo só; ele decide o assunto pela frase (e, com a IA ligada, ela pode
    confirmar o assunto em segundo plano, sem travar a escuta). Nas respostas, ele manda pra IA só o índice
    e os assuntos ligados à sua pergunta — não a memória toda.
- **Central > Histórico:** tudo que você pediu e ouviu, com busca, e a lista da memória (agora em uma caixa
  por assunto), que dá para editar.
- **Corrigido:** *"pode falar"* virava *"falar"* e a resposta guardada sumia. Agora, depois de *"Terminei de pensar"*, você pode dizer *"Mestre"* e depois *"pode falar"*.
- **Mais rápido:** ele libera você em **3 segundos** (antes eram 10).

### 25.5 Spotify
1. Painel > **Spotify** > **+ Adicionar playlist**: escreva o nome que você vai falar e cole o link. No Spotify: `···` > Compartilhar > **Copiar link da playlist**.
2. Diga *"Mestre, toca a playlist Foco no Spotify"*: ele abre no **app** e aperta Play.
3. Nome que não está na lista abre a **busca** do app (*"toca Legião Urbana no Spotify"*).

Se o Spotify ignorar o Play, é um clique. Tocar uma música exata sem clicar exige a API do Spotify, com conta Premium.

### 25.6 Projetos guiados
1. *"Mestre, quero começar um novo projeto"*.
2. Ele pergunta o **tipo** (código, trabalho, vida pessoal, estudo ou outro), o **nome**, o **objetivo** e se tem **prazo** ou algo já pronto.
3. Ele cria a pasta `Documentos\Projetos\<nome>`, com subpastas e um **PLANO.md**.
4. A IA pensa (bolinha roxa) e traz **3 caminhos**. Diga **"um"**, **"dois"** ou **"três"**:
   - os passos entram no plano como caixinhas;
   - ele abre pesquisas prontas no navegador.
5. Ou diga **"quatro"** / *"nenhum, manda pro Claude"*. Ele pergunta o destino:
   - **Claude Code**: abre o Claude Code **na pasta do projeto**;
   - **agente IPM**;
   - **chat novo** no claude.ai, já com o plano.
6. Depois:
   - *"abre o projeto App de Receitas"*;
   - *"anota no projeto App de Receitas que…"*;
   - *"o que falta no projeto App de Receitas?"*;
   - *"quais são os meus projetos?"*.

A pasta dos projetos muda em Painel > **IPM e projetos**.

### 25.7 Páginas e fontes
- **Páginas:** trocar de página agora é instantâneo, sem piscar, e a lista volta para o topo.
- **Fontes:** Painel > Aparência > **Fonte** tem 32 fontes do Windows (só aparecem as que existem no seu PC). A caixinha **"todas do PC"** mostra qualquer fonte instalada.

### 25.8 Skills
A skill **corrigir-transcricao** aprendeu "OMA" → Ollama. Envie o `corrigir-transcricao.zip` novo no claude.ai, no mesmo lugar de antes.

## Etapa 26: Versão 8

### 26.1 Atualizar
Central > **Atualizar o Mestre (.zip)** > **`mestre_atualizacao_v8.zip`**. Esta versão instala 3 bibliotecas novas (a própria atualização faz isso; pode levar 1 ou 2 minutos).

### 26.2 Música por voz (Spotify e qualquer player)
| Você fala | O que acontece |
|---|---|
| "pausa", "pausa o Spotify", "para a música", "continua", "despausa", "volta a tocar" | Pausa ou continua |
| "próxima", "pula essa", "próxima música" | Próxima faixa |
| "música anterior", "volta a música" | Faixa anterior |
| "aumenta o volume", "diminui o volume" (+ "um pouco", "bastante") | Volume do PC |
| "volume no 30" | Volume do PC em 30% |
| "aumenta o volume do Spotify", "Spotify no volume 40" | **Só o Spotify** (o resto do PC fica igual) |

### 26.3 Janelas e navegador
- **Janelas:** *"fecha essa janela"*, *"minimiza"*, *"maximiza"*, *"minimiza tudo"*, *"troca de janela"*.
- **Abas e páginas:** *"nova aba"*, *"fecha a aba"*, *"reabre a aba"*, *"volta a página"*, *"atualiza"*.
- **Rolagem e zoom:** *"rola pra baixo"*, *"rola pra cima"*, *"vai pro topo"*, *"aumenta o zoom"*.
- **Print:** *"tira um print"* salva na pasta Imagens\Mestre.

Tudo age na janela que está na frente.

### 26.4 YouTube por voz
O YouTube agora abre numa **janela do Edge controlada pelo Mestre**, com perfil separado.
- **Primeira vez:** Painel > **YouTube** > **"Abrir a janela para entrar na minha conta"**. Entre na sua conta do Google e feche a janela. O login fica guardado.
- **Na tela:** *"tela cheia"*, *"sai da tela cheia"*, *"modo cinema"*, *"legenda"*.
- **No vídeo:** *"avança 30 segundos"*, *"volta 10"*, *"próximo vídeo"*.
- **Na sua conta:** *"dá like"*, *"se inscreve"* (ele não desfaz se você já tiver dado like ou já for inscrito).
- **Em lives:** *"fecha o chat"*, *"abre o chat"*, *"tela cheia com chat"* (a janela inteira em tela cheia com o chat visível).
- **Numa busca:** *"lê os títulos"*, *"abre o terceiro vídeo"*, *"abre o vídeo do Manual do Mundo"*.
- **Pausar e continuar:** use os comandos de música de cima.

Se um dia o YouTube mudar os botões e algo parar de funcionar, é só avisar.

### 26.5 Envio automático ao app Claude
- **Como ele envia agora:** acha a **caixa de mensagem dentro do app**, pelo recurso de acessibilidade do Windows, em vez de clicar numa posição da tela. Depois cola e envia.
- **Para testar:** Painel > **IPM e projetos** > **"Testar envio para o app Claude"**.
- **Se não aparecer nada:** mande para o Claude o último print da pasta `logs\diagnostico`.

### 26.6 Avisos curtinhos no "pensando"
Agora são *"Segundo plano."* e *"Pronto, chefe."*, já prontos no cache (saem sem atraso). Em Painel > Conversa > **Aviso do pensando** dá para trocar por um **bipe**, que é ainda mais curto.

### 26.7 Transcrição melhor
Painel > Áudio > **"Palavras que ele deve conhecer"**: Ollama, IPM, Claude Code e outras. O reconhecimento de voz erra menos essas palavras. Acrescente as suas.

## Etapa 27: Versão 9

### 27.1 Atualizar
Central > **Atualizar o Mestre (.zip)** > **`mestre_atualizacao_v9.zip`**.

### 27.2 YouTube no Brave
Painel > **YouTube**:
- **Navegador:** Brave (o padrão agora), Edge ou Chrome. O Mestre acha o Brave sozinho; se não achar, avisa e usa o Edge.
- **Modo:**
  - **Janela controlada:** todos os comandos (like, inscrever, chat, "abre o terceiro vídeo"). Usa o Brave de verdade, com um **perfil do Mestre**. Na primeira vez, clique em **"Abrir a janela para entrar na minha conta"**, entre no Google e feche a janela.
  - **Meu navegador normal:** o seu Brave de sempre, com extensões e login. Só funcionam os comandos de tecla: tela cheia, cinema, legenda, avançar e próximo vídeo.

Por que não dá para ter os dois ao mesmo tempo? O Brave e o Chrome não deixam nenhum programa controlar o seu perfil principal. É uma trava de segurança contra vírus.

### 27.3 Monitores
- **Padrão:** tudo que ele abre vai para o **monitor principal**, maximizado. Dá para desligar em Painel > Programas e sites > Monitores.
- **Outro monitor:** *"abre o YouTube no monitor 2"*, *"abre o canal Manual do Mundo na tela 3"*, *"… no monitor secundário"*.
- **Mover a janela da frente:** *"joga essa janela pro monitor 3"*.
- **Numeração:** **1 = principal**; os outros vão da esquerda para a direita. O botão **"Identificar monitores"** mostra o número em cada tela.
- **Nomes:** dá para dar um nome a cada monitor (ex.: "da TV") e falar *"no monitor da TV"*.

### 27.4 Envio ao app Claude
- **Como funciona agora:** o Mestre **maximiza** o app Claude no monitor principal antes de colar. Então a caixa de mensagem fica sempre no mesmo lugar.
- **Sem clique às cegas:** ele coloca o cursor na caixa **sem clicar**. Se precisar clicar, clica **uma vez só**.
- **O mais garantido:** Painel > **IPM e projetos** > **"Ensinar onde fica a caixa"**. Em 5 segundos, pare o mouse em cima da caixa de mensagem do Claude e clique em **Salvar**. A partir daí ele usa exatamente esse lugar.
- **Para conferir:** **"Testar envio para o app Claude"**.

### 27.5 Volume só do Spotify
- *"muta o Spotify"* / *"tira o som do Spotify"*, *"volta o som do Spotify"*, *"diminui o volume do Spotify"*, *"Spotify no 30"*.
- **Não mexe no volume do computador.** Se faltar algo, ele avisa em vez de mexer no Windows.
- **Para conferir:** Painel > **Spotify** > **"Testar volume só do Spotify"**, com uma música tocando.

## Etapa 28: Versão 10

### 28.1 Atualizar
Central > **Atualizar o Mestre (.zip)** > **`mestre_atualizacao_v10.zip`**.

### 28.2 YouTube no SEU Brave (extensão do Mestre)
O Google não deixa entrar na conta num navegador controlado por programa. Então agora o Mestre usa o **seu Brave de sempre** e uma **extensão** faz a ponte. Instale uma vez:
1. Painel > **YouTube** > **"Abrir a pasta da extensão"** (é a pasta `extensao_brave`).
2. No Brave, digite `brave://extensions`.
3. Ligue o **Modo de desenvolvedor** (canto superior direito).
4. Clique em **"Carregar sem compactação"** e escolha a pasta `extensao_brave`.
5. Abra o YouTube no Brave (ou aperte F5 se já estiver aberto).

Com o Mestre ligado, o painel mostra **"● extensão conectada"**. Aí funcionam todos os comandos no seu Brave, com a sua conta: *"dá like"*, *"se inscreve"*, *"fecha o chat"*, *"lê os títulos"*, *"abre o terceiro vídeo"*, *"avança 30 segundos"*, *"tela cheia"*…

A extensão só age em páginas do YouTube e só conversa com o Mestre **no seu PC** (endereço 127.0.0.1). De vez em quando o Brave pode mostrar um aviso sobre extensões em modo de desenvolvedor: é só fechar.

### 28.3 Sites prontos (abrem no Brave)
Já vêm cadastrados:
- **Streaming:** Netflix, Prime Video, Disney, HBO Max, Globoplay, Twitch;
- **Compras:** Amazon, Mercado Livre, Shopee;
- **Redes e e-mail:** TikTok, Instagram, WhatsApp, Gmail;
- **IAs:** ChatGPT, Gemini, Claude ("claude site"), Copilot, Perplexity, DeepSeek, Grok.

*"abre a Netflix"*, *"abre o ChatGPT no monitor 3"*. Os seus sites antigos continuam. A opção **"abrir os sites no Brave"** fica em Painel > Programas e sites.

### 28.4 Monitores por marca
O Mestre lê a **marca e os Hz** de cada monitor:
- **1 = principal** (a sua LG 240 Hz);
- depois os de mais Hz: **2 = AOC 240 Hz**, **3 = 144 Hz**.

Dá para falar *"no monitor LG"*, *"no monitor AOC"*, *"no monitor de 144"*, *"no terciário"*. O botão **"Identificar monitores"** mostra "1 · LG 240 Hz" em cada tela. Se algum nome não bater, dê o seu nome no painel.

### 28.5 Volume do Spotify por voz
*"coloca o Spotify no máximo"*, *"volume máximo do Spotify"*, *"Spotify no 50"*, *"abaixa o Spotify"*, *"Spotify mais alto"*, *"muta o Spotify"*. Ele **confirma falando**: *"Spotify em 60 por cento"*.

### 28.6 Fale do seu jeito
Agora o Mestre entende muitas variações. Exemplos para o ditado de melhorias:
- *"quero melhorar uma coisa no projeto"*;
- *"tenho umas ideias pra você"*;
- *"quero criar novas melhorias"*;
- *"quero fazer uns ajustes no projeto"*;
- *"modo melhorias"*.

O mesmo vale para YouTube, janelas, Spotify, projetos e histórico. São 155 frases testadas.

### 28.7 Ditado caprichado
Durante o ditado, o reconhecimento de voz usa a **precisão máxima**, não corta as pontas das palavras e leva o **texto anterior como contexto**. Um headset perto da boca ajuda muito. Para pedidos grandes de melhoria, ditar aqui no app do Claude continua sendo o caminho de melhor qualidade.

## Etapa 29: Versão 11

### 29.1 Atualizar
1. Central > **Atualizar o Mestre (.zip)** > **`mestre_atualizacao_v11.zip`**.
2. **Recarregue a extensão** (ela mudou):
   1. No Brave, digite `brave://extensions`.
   2. No cartão **"Mestre - comandos de voz no Brave"**, clique na **setinha redonda** (recarregar).
   3. Aperte **F5** nas abas do YouTube que já estavam abertas.

### 29.2 Quem é quem
**Ele** é o **Assessor**. A palavra que acorda ele é *"assessor"*. **Você** é o **Mestre**.

Antes, uma troca automática de palavras virava o seu apelido ("Mestre") em "Assessor", e ele parecia falar sozinho. Isso foi corrigido. Na primeira vez que ligar a versão 11, o nome dele passa a ser **"Assessor"** sozinho.

Confira em Painel > **Personalidade**:
- **Nome DELE:** Assessor;
- **Como ele chama VOCÊ:** Mestre;
- **Palavra que acorda ele:** assessor.

Embaixo aparece um exemplo de como fica. Se o nome dele e o seu estiverem iguais, aparece um aviso amarelo.

### 29.3 Pensando em silêncio
Ele **não fala mais** "vou pensando" nem "pronto, pode falar". Só o indicador muda: **roxo** enquanto pensa, **verde** quando terminou. Quando quiser ouvir, diga *"assessor, pode falar"*.

Para voltar a ter aviso: Painel > **Conversa** > "Aviso do pensando" (silêncio, bipe ou voz) e "Quando terminar".

### 29.4 YouTube: comandos diretos, sem passar pela IA
Valem na aba do YouTube que você está vendo:

| Você fala | O que acontece |
|---|---|
| *"próximo vídeo"*, *"pula esse vídeo"* | vai para o próximo |
| *"vídeo anterior"* | volta para o vídeo de antes |
| *"pausa o vídeo"*, *"para o vídeo"* | pausa **o vídeo** (não mexe no Spotify) |
| *"continua o vídeo"*, *"dá play no vídeo"* | continua |
| *"vai pras inscrições"*, *"abre o histórico do YouTube"*, *"abre o assistir mais tarde"*, *"abre os shorts"*, *"mostra os vídeos que eu gostei"* | abre a página do YouTube |
| *"quero ver o vídeo do David Jones"*, *"abre o vídeo do GTA 6"* | lê os vídeos que estão na tela (**título e canal**) e abre o certo |
| *"lê os títulos"* | fala os 5 primeiros, com o nome do canal |

*"próximo"* sozinho pula a música ou o vídeo que estiver tocando.

### 29.5 Navegador: páginas e abas
- *"volta a página"*, *"volta pra página anterior"*;
- *"avança a página"*, *"vai para a próxima página"*;
- *"próxima aba"*, *"aba anterior"*.

Se o Brave está na frente, ele usa as teclas. Se você está em outro programa (com o Brave no outro monitor), a extensão faz na aba que você usou por último.

### 29.6 Janelas e abas independentes nos 3 monitores
Ele acha a janela **pelo nome**: aba do Brave (Netflix, YouTube, Gmail…) ou programa (Spotify, Discord…).

- *"joga a Netflix pro monitor 3"*: leva a janela onde a Netflix está (as outras abas dessa janela vão junto).
- *"separa a Netflix pro monitor 2"*: tira **só a Netflix** para uma janela dela e manda para o monitor 2.
- *"joga a Netflix desse navegador pro monitor 2"*: o mesmo que separar.
- *"separa a Netflix pro monitor 2 e deixa o YouTube no principal"*: a Netflix vai sozinha para o 2 e o YouTube fica (ou vai) para o principal.
- *"abre a Netflix no monitor 2"*:
  - se a Netflix já está aberta, ele usa **essa** aba (separa e manda);
  - se não está, abre **numa janela nova** já no monitor 2. A janela que você já tinha não se mexe mais.
- *"abre o Gmail"* com o Gmail já aberto: traz a aba dele para a frente.
- *"manda o Spotify pro monitor AOC"*: janela de programa, pelo nome.
- *"joga essa janela pro monitor 2"*: a janela da frente.

Separar abas precisa da **extensão** (é ela que enxerga as abas). Sem a extensão, ele acha só pelo título da janela.

### 29.7 Exportar o histórico para o Claude
Painel > **Histórico** > **"Exportar para o Claude"**:
1. Escolha o período: hoje, 7 dias, 30 dias ou tudo.
2. A pasta abre com o arquivo já marcado.
3. **Arraste o arquivo para a conversa com o Claude** (aqui).

Por voz: *"assessor, exporta o histórico"* (ou *"… de hoje"*).

O arquivo mostra:
- o que ele **ouviu**, como **entendeu** e **qual comando atendeu**;
- as frases que foram para a IA ou deram "não entendi" (as que viram comando novo);
- as frases que a IA transformou em comando (comando que falta no vocabulário);
- tudo que o microfone transcreveu, inclusive as frases ignoradas, e as que parecem ter tentado chamar ele (a palavra de ativação mal ouvida);
- os seus feedbacks ("isso tá errado").

É só texto, sem áudio. Fica na pasta `exportacoes`. As frases do microfone começam a ser guardadas a partir desta versão.

## Etapa 30: Versão 12

### 30.1 Atualizar
1. Central > **Atualizar o Mestre (.zip)** > **`mestre_atualizacao_v12.zip`**. Ela instala a biblioteca da voz nova (demora um pouco mais desta vez).
2. **Recarregue a extensão** (versão 2.1, com permissões novas):
   1. `brave://extensions`;
   2. no cartão **"Mestre - comandos de voz no Brave"**, clique na **setinha redonda**;
   3. se o Brave pedir para aceitar permissões novas, aceite;
   4. aperte **F5** nas abas do YouTube.
3. Painel > **YouTube**: deve aparecer **"● extensão conectada (versão 2.1)"**. Se aparecer ⚠ com a versão velha, a extensão não foi recarregada. Era por isso que ele não achava os vídeos na página inicial do YouTube.

### 30.2 Voz Kokoro (no seu PC)
Na primeira vez que ligar, ele **baixa a voz sozinho** (330 MB). Enquanto baixa, fala com a voz de antes. Também dá para baixar no Painel > **Voz** > **"Baixar a voz Kokoro"**.

- Três vozes: **Alex** (masculina), **Dora** (feminina) e **Santa** (masculina, mais grave).
- Painel > Voz: escolha, escreva uma frase e clique em **▶ Ouvir**. Embaixo aparece em quantos segundos ela começou a falar.
- Por voz: *"assessor, apresenta as vozes"* e *"usa a voz da Dora"*.
- Se a Kokoro falhar, ele usa a voz Edge sozinho.

### 30.3 Voz da Azure (para testar)
As vozes da Azure são da mesma família da Edge (Antonio, Francisca...). A diferença é a estabilidade e as vozes **Multilingual**, que são mais expressivas (ex.: Thalita Multilingual, Macerio Multilingual). O plano grátis dá umas **8 horas de fala por mês**.
1. Entre em **portal.azure.com** e crie a conta grátis. Ela pede um cartão só para confirmar quem você é; o plano F0 não cobra.
2. **Criar um recurso** > pesquise **"Speech"** (Serviços de Fala) > **Criar**.
3. Preencha:
   - Grupo de recursos: novo, `assessor`;
   - Região: **Brazil South**;
   - Nome: `assessor-voz`;
   - Tipo de preço: **Free F0**.
4. **Revisar e criar** > **Criar** > **Ir para o recurso**.
5. Menu **"Chaves e ponto de extremidade"**: copie a **KEY 1** e a **Região** (`brazilsouth`).
6. Painel > **Voz** > **Azure**: cole a chave e a região > **"Salvar chave e testar"**. Ele fala uma frase de teste.
7. Em "Motor de voz", escolha **Azure (chave)** e salve.

A chave fica guardada no seu usuário do Windows (`%APPDATA%\Mestre\segredos.json`), **fora** da pasta do projeto.

### 30.4 Modo descanso
- *"assessor, pode descansar"* (ou *"fica quieto"*, *"modo descanso"*, *"dá um tempo"*): o indicador fica cinza, **"Descansando"**. Ele não responde a nada.
- *"bora voltar a trabalhar"* (com ou sem "assessor"), *"assessor, volta"*, *"voltei"*: ele volta.
- *"tá por aí?"* durante o descanso: ele só avisa que está descansando.
- Para desligar o microfone de verdade, use **Pausar** no ícone perto do relógio.

A lista dos **30 jeitos de chamar** está no Painel > **Início**.

### 30.5 Correções do seu histórico
- *"**Meu** assessor, …"*: o "meu" não estraga mais o comando.
- Quando a IA descobre que era um comando, ela **faz sozinha**, sem você dizer "pode falar".
- *"e aí"*, *"tchau"*: resposta na hora. Barulhos ("oh") são ignorados.
- *"volte na página anterior"*, *"se inscreva nesse canal"*, *"pause Spotify"*, *"pula essa música do Spotify"*, *"muta o Spotify"* (mesmo escrito "multa"): funcionam direto.
- *"diminui o Spotify em 20"*: baixa 20 (antes ia **para** 20).
- *"tira o vídeo do mudo"*, *"aumenta o volume do YouTube"*: mexe só no vídeo.
- *"na janela principal"*, *"no monitor da esquerda / da direita / do meio"*: viram monitor.
- *"pesquise pelo canal FRTT"*: procura FRTT (antes procurava "pesquisa pelo frtt").
- Às 3h da manhã ele diz "boa noite".

### 30.6 YouTube
- *"o segundo vídeo da janela"*, *"tocar o terceiro vídeo dessa lista"*;
- *"selecione o vídeo com o nome …"*;
- *"abre o canal do primeiro vídeo"*;
- *"reproduz o último vídeo desse canal"*: o canal da aba que você está vendo.

Se ele disser que não achou vídeos, exporte o histórico: vai junto um "retrato" da página para eu ajustar.

### 30.7 Streamings
*"toca Agentes da Shield na Disney"*, *"assiste Stranger Things na Netflix"*, *"toca … no Prime / na HBO / no Globoplay"*:
1. ele abre a **busca** do streaming (na aba dele, se já estiver aberta);
2. clica no **resultado** com o nome;
3. clica em **"Continuar assistindo"** ou **"Assistir"**.

Sem dizer onde (*"quero continuar assistindo a série …"*), ele pergunta em qual.

Esses sites mudam o visual e alguns bloqueiam cliques automáticos. A busca sempre abre. Se o play não for, diga *"clica em assistir"*, *"clica em episódio 3"*, *"clica em continuar"*: o **"clica em …"** funciona em qualquer site no Brave.

*"toca Feliz do DJ Petroski"* (sem dizer onde): vai para o **Spotify**. Dá para trocar para YouTube no Painel > Spotify.

### 30.8 Juntar janelas (qualquer monitor)
- *"junta o YouTube com a Disney"* ou *"traz o YouTube pra janela da Disney"*: o YouTube vira uma aba na janela da Disney, no monitor onde ela estiver.
- *"junta todas as janelas no principal"*: todas as abas do Brave numa janela só, no monitor principal.

### 30.9 Áudios do celular
Começou o áudio com **"Assessor, …"**? Ele **executa** como comando. Senão, vai para o **destino** do Painel > **Celular** (padrão: o projeto no app do Claude, com o aviso de corrigir e refinar). O texto fica guardado na pasta `recebidos`.

**Caminho 1: pasta sincronizada (o mais simples)**
1. No PC, instale o **Google Drive para computador** e entre com a sua conta (ou use o OneDrive, que já vem no Windows).
2. No Drive, crie a pasta **`Assessor audios`**. No PC ela aparece em `G:\Meu Drive\Assessor audios`.
3. Painel > **Celular** > **"Escolher pasta..."** > essa pasta > **Salvar e reiniciar**.
4. No celular: no áudio do WhatsApp (ou do gravador), toque e segure > **Compartilhar** > **Drive** > pasta `Assessor audios` > **Salvar**.
5. Em alguns segundos ele transcreve e manda. O áudio vai para a subpasta `lidos`.

**Caminho 2: Telegram (de qualquer lugar)**
1. No Telegram, procure **@BotFather** > **/newbot**.
2. Dê um nome (ex.: *Meu Assessor*) e um usuário terminado em `bot` (ex.: `arthur_assessor_bot`). Ele responde com um **token**.
3. Painel > **Celular** > cole o token > **"Salvar token e testar"** > **Salvar e reiniciar**.
4. No Telegram, abra o seu robô e toque em **Iniciar**. Ele responde: *"Pronto! Este chat agora é o seu."* Só esse chat é atendido.
5. Mande áudio ou texto. Ele responde com o que entendeu e o que fez.

Os dois caminhos precisam do PC e do Assessor ligados. A transcrição é feita no seu PC, de graça.

## Etapa 31: Versão 13

### 31.1 Atualizar
1. Central > **Atualizar o Mestre (.zip)** > **`mestre_atualizacao_v13.zip`**. Nas próximas atualizações, no fim ele vai dizer de qual versão para qual foi (ex.: *"Atualizado da versão 13 para a 14"*).
2. **Recarregue a extensão** (versão 2.2): `brave://extensions` > **setinha redonda** no cartão do Mestre > **F5** nas abas do YouTube e dos streamings.
3. A versão agora aparece no painel: embaixo do menu lateral (**"Versão 13 · extensão 2.2"**), no selo **v13** do canto e em Início. Por voz: *"assessor, qual a sua versão?"*.

### 31.2 Painel novo
- **Menu lateral em grupos**: Assistente, Voz e ouvido, Apps e sites, Integrações e Sistema. A página aberta fica marcada.
- **Cada assunto num cartão.** Explicação longa? Só a primeira frase aparece; clique em **"mais ›"** para ler o resto.
- As opções **avançadas começam fechadas**: clique em **"Mostrar ▾"** (ou no título do cartão).
- Um botão colorido por cartão (a ação principal); os outros são discretos.

### 31.3 Streamings: busca de verdade
A Disney mudou e o link de busca antigo dava "page not found". Agora:
1. ele abre o site (Disney e HBO) ou a busca (Netflix, Prime, Globoplay);
2. **clica na lupa e digita o nome** no campo de busca, como você faria;
3. clica na **capa** do filme ou série (ignora as "pesquisas recentes");
4. clica em **"Continuar assistindo"** ou **"Assistir"**.

Ele aceita nomes um pouco errados (*"Agentes da Shields"* acha *"Agentes da S.H.I.E.L.D."*). Se algum site não funcionar, abra a busca à mão, copie o endereço da barra e me mande.

### 31.4 YouTube (e streamings) em mais de uma tela
Nos comandos de **escolher algo na tela** (*"abre o segundo vídeo"*, *"vídeo com o nome …"*, *"abre o canal do primeiro vídeo"*, *"clica em …"*):
- com o site aberto em **uma** janela só, ele faz direto;
- *"abre o segundo vídeo **do monitor 2**"* (ou *"da tela 2"*, *"no monitor da direita"*): usa a janela desse monitor;
- sem dizer o monitor:
  - **vídeo pelo nome** ou **"clica em …"**: ele procura em todas as janelas e usa a que tem;
  - senão, usa a janela do **monitor onde está o mouse**;
  - se ainda ficar em dúvida, **pergunta**: *"Tem YouTube em mais de uma tela. No monitor 1 ou no 2?"*. Responda *"no dois"*;
- *"pausa o vídeo"* com dois YouTube abertos: pausa o que está **tocando**.

### 31.5 A IA não pede mais "pode falar"
- Terminou de pensar? Ele **já fala a resposta**, assim que você parar de falar. Durante o ditado, ela fica guardada (bolinha verde).
- Quando a IA descobre que era um **comando**, ela executa na hora.
- Quando precisa de você (*"qual dos dois?"*, *"tem certeza?"*), ela **pergunta**; a sua resposta continua o pedido.
- **Memória:** frase que a IA já transformou em comando uma vez vai **direto** nas próximas vezes, sem pensar de novo.
- Quer o jeito antigo? Painel > **Conversa** > "Quando terminar" > **Só mudar a cor no indicador**.

### 31.6 Vozes novas
Painel > **Voz**: clique no cartão da voz. A configuração dela abre logo abaixo. Teste com **▶ Ouvir** (mostra em quantos segundos começou a falar). Se a escolhida falhar, ele fala com a **Kokoro** e depois com a **Edge**, sozinho.

**Natural (grátis, placa de vídeo):** a mais humana das grátis (*Chatterbox*, que fala português).
1. Painel > Voz > cartão **Natural** > **"Instalar a voz natural"**. Ela baixa uns **6 GB** (10 a 40 minutos) num canto separado, sem mexer no resto.
2. **Timbre**: ela imita uma voz de referência. Escolha **Antônio** ou **Francisca** (ele grava a referência com a voz da Microsoft) ou **"Usar um áudio meu..."**: um áudio de uns 10 s, limpo, com a voz que você quer.
3. **Salvar e reiniciar.** Ao ligar, ela leva 1 a 2 minutos para carregar; enquanto isso ele fala com a Kokoro.
- Precisa de placa **NVIDIA** para ficar rápida. Sem ela, funciona, mas devagar.
- Ela é mais lenta para começar a falar que a Kokoro. As frases fixas ficam prontas depois da primeira vez.

**ElevenLabs (paga, a mais natural de todas):**
1. Crie a conta em **elevenlabs.io**.
2. **Developers > API Keys > Create API Key** e copie a chave.
3. Painel > Voz > cartão **ElevenLabs** > cole a chave > **"Salvar chave e testar"**. Ele fala uma frase e carrega as vozes da sua conta. Vozes brasileiras: na **Voice Library** do site, filtre por *Portuguese* e clique em **Add** (depois teste de novo para elas aparecerem na lista).
4. Modelo: **Rápido (Flash)** gasta metade dos créditos e começa a falar mais rápido; **Multilingual v2** é o mais natural.
- O plano grátis dá uns **10 mil caracteres por mês**. As frases fixas ficam guardadas: cada uma só gasta na primeira vez.
- A chave fica no seu usuário do Windows, fora do projeto.

### 31.7 Aviso do Telegram (e da pasta)
Quando chega algo do celular, o indicador fica **azul** por alguns segundos (*"📱 Telegram: abre o YouTube"*). Ele também fala **"Mensagem do Telegram."**. Painel > **Celular** > "Aviso quando chega": tela e voz, só na tela, só a frase ou nenhum. As duas frases (Telegram e pasta) dá para trocar ali.

### 31.8 Desligar na hora
- *"assessor, desliga"*, *"pode desligar"*, *"desliga o assessor"*, *"encerra por hoje"*: ele se despede e fecha. Antes, sem o nome certo, a frase ia para a IA e demorava.
- Se algo segurar o programa (microfone, internet), ele fecha em no máximo 2 segundos.

### 31.9 Validar a atualização dentro do painel
Em vez de conferir o `ROTEIRO_VALIDACAO.md` na mão, o painel te guia frase por frase:
1. Depois de atualizar, fale *"assessor, reinicia"* (o assistente precisa estar **ligado**: é ele quem ouve).
2. Painel > **Sistema** > **Validar atualização**. Escolha **Rápido** (4 falas essenciais), **Direcionado** (marque os grupos que quer testar) ou **Completo** (todo o roteiro). O painel mostra o que entra e quantos itens haverá antes de **▶ Começar**.
3. Aparece uma frase (ex.: *Fale: "Assessor, que horas são"*) e o que deve acontecer. **Fale normalmente**, como no dia a dia.
4. Em 1 ou 2 segundos aparecem três linhas:
   - **OUVI**: o que o reconhecimento de voz escreveu;
   - **ENTENDI**: a frase depois do vocabulário e **qual comando atendeu** (ex.: `_cmd_hora_data`);
   - **FIZ**: o que ele respondeu.
   O painel já sugere **✅** (bateu com o esperado) ou **❌**.
5. Confirme: **✅ Deu certo** ou **❌ Deu errado**. No ❌ aparece "O certo era:": **digite**, ou **fale sem chamar o assistente** (sem a palavra de ativação) que o painel preenche sozinho. Depois **Salvar ❌ e seguir**.
6. Outros botões: **Pular**, **Bloqueado** (faltou uma condição para testar), **Repetir** (fale de novo a mesma frase), **◀ Anterior** e **■ Parar**.
7. Ao parar (ou no fim da lista) sai o relatório `exportacoes/validacao_AAAA-MM-DD_HHMM.md`. Ele registra os itens feitos, bloqueados e não executados, além do commit, versão e hash do roteiro. Se a sessão for interrompida, o relatório é parcial. Cada ❌ de uma frase falada vira um item FEEDBACK na lista de Melhorias, pronto para o Claude Code corrigir. Botão **Abrir o relatório** para ver.
8. Teve falha? O botão **🛠 Mandar para o Claude corrigir** fica ativo (sem falha nenhuma, ele fica desativado). Clique nele: o painel salva o pedido em `exportacoes/pedido_correcao_*.md` e abre uma janela de terminal já com o **Claude Code** rodando (você continua acompanhando e aprovando tudo normalmente, como sempre). Se o Claude Code não estiver instalado no PC, o painel avisa e copia o pedido para você colar onde quiser.

Linhas de painel, observação, pré-condição, espera ou teste automático não têm frase para falar: faça o que a tela diz e marque o resultado. Se uma pré-condição não estiver atendida, marque **Bloqueado**; os próximos itens daquele grupo aparecem como bloqueados no relatório, sem contar como falha do produto. Sequências de falas independentes aparecem uma etapa por vez. Enquanto a validação está aberta, o assistente guarda o áudio de cada frase em `logs/validacao/` (só as últimas 120).

#### Modo contínuo (o jeito mais rápido)
A caixinha **Modo contínuo** já vem marcada. Com ela:
1. Clique **▶ Começar** e vá falando as frases que aparecem (a frase fica grande na tela).
2. Deu certo? Aparece **✅ Deu certo!** e em 1,5 segundo vem a próxima frase **sozinha**, sem clicar em nada.
3. Deu errado? Ele **para** e mostra em letras grandes o que aconteceu: **OUVI** (o que o reconhecimento escreveu) → **ENTENDI** (e qual comando atendeu) → **FIZ** (o que ele respondeu). Se o ouvido jogou a frase fora, aparece também **DESCARTEI** com o motivo: *curta demais*, *sem a palavra de ativação*, *voz não reconhecida*... Isso mostra exatamente o que ele entendeu. Depois é só **❌ Deu errado** (para anotar "o certo era"), **Repetir** ou **Pular**.
4. Ficou 15 segundos sem ouvir nada? Aparece **"Não ouvi nada — fale de novo ou Pular"**.
5. Linhas sem fala pedem confirmação manual mesmo com o avanço automático ligado; nunca são tratadas como comandos para o microfone.
Prefere o jeito antigo (você confirma cada frase)? Desmarque **Modo contínuo** antes de começar.

### 31.10 Sugestões de melhoria (todo dia às 8h)
O assistente olha sozinho, uma vez por dia, o que aconteceu desde a última olhada (no mínimo as últimas 24 horas) e monta uma **lista de sugestões**. Ele **não muda nada** no projeto: só sugere.
- O que ele procura: frases que o ouvido jogou fora (e por quê), a palavra de ativação escrita errada pelo reconhecimento, frases com cara de comando (abre, toca, pausa, volume...) que caíram na IA, "não entendi", pedidos repetidos logo em seguida (sinal de erro) e jeitos novos de falar que funcionaram.
- Quando: no horário do painel > **Sistema** > **Sugestões de melhoria** > **Horário** (padrão **08:00**). Se o computador estava desligado nesse horário, ele analisa assim que ligar. Dá para desligar em **Analisar todo dia**. Mudou? **Salvar e reiniciar**.
- Na mesma página: **🔍 Analisar agora** faz a análise na hora. As sugestões aparecem em páginas de 8 (◀ ▶), cada uma com as frases, os horários e os motivos.
- Marque as que valem a pena e clique **🛠 Mandar marcadas para o Claude**: o painel salva o pedido em `exportacoes/pedido_sugestoes_*.md` e abre o **Claude Code** no terminal já com ele (igual ao botão da validação; você acompanha e aprova tudo).
- Com a IA ligada, a análise automática ainda ganha um **resumo da IA** no topo da lista (feito em segundo plano, nunca atrapalha).
- Sugestão de "a palavra de ativação escrita errada" (ex.: o reconhecimento ouviu "acesor" em vez de "assessor")? Ela tem um botão **✓ Aplicar** (e dá para marcar várias e clicar **✓ Aplicar marcadas**): SEM passar pelo Claude, ele mostra a troca exata ("vai trocar X por Y e também vai acordar com essa pronúncia"), você confirma, e ele grava sozinho no vocabulário (`aprendido.yaml`) **e** nas variações aceitas da palavra de ativação (`config.yaml`) — então a partir daí ele também **acorda** quando você falar daquele jeito. Recusa trocas que dariam problema (palavra vazia, curta demais, a própria palavra de ativação, ou uma troca que já existe). Depois de aplicar, a sugestão some da lista; se aplicou errado, **↩ Desfazer última aplicação** desfaz nos dois arquivos. As outras sugestões (frases jogadas fora, caíram na IA, "não entendi"...) continuam só indo para o Claude.

## Etapa 32: Versão 2.5

A partir daqui a versão tem ponto: depois da 13 vem a **2.5** (o painel mostra "2.5" embaixo da barra de ícones e no selo **v2.5** do canto).

### 32.1 Menu de ícones (barra da esquerda)
- A barra da esquerda mostra **só os ícones** e nunca muda de tamanho. **Pare o mouse** em cima dela por um instante: os nomes e os grupos deslizam de trás dos ícones, por cima da página. Tire o mouse do menu e eles recolhem. (Só passar rápido por cima não abre.) O ícone do programa no alto também abre/fecha com um clique, e Esc fecha.
- A página não muda de tamanho nem de posição: o menu só passa por cima da borda esquerda enquanto está aberto.
- Ao escolher uma página, o menu recolhe e fica fechado até o mouse sair da barra (para você ver a página inteira).
- A lista não coube na tela (janela pequena ou fonte grande)? Gire a **roda do mouse** em cima dos ícones ou dos nomes.
- Parou o mouse num ícone com o menu fechado (por exemplo, logo depois de escolher uma página)? Aparece um balãozinho com o nome e o que tem na página. Com o menu aberto, os nomes já aparecem e o balão não.
- A página aberta fica com o ícone **rosa** (na cor que você escolheu em Aparência).
- Onde fica cada coisa (de cima para baixo):

| Grupo | Ícone → página |
|---|---|
| **Assistente** | 🏠 casa → **Início** · 🙂 rosto → **Personalidade** · 💬 balão → **Conversa** |
| **Voz e ouvido** | ondas → **Voz** · 🎤 microfone → **Áudio** |
| **Apps e sites** | ▶ tela com play → **YouTube** · ♫ nota → **Spotify** · 🖥 janela → **Programas e sites** · 🔁 relógio com seta → **Rotinas** · ⚡ raio → **Atalhos** |
| **Integrações** | 💼 maleta → **IPM e projetos** · 📱 celular → **Celular** |
| **Sistema** | ☰ linhas → **Histórico** · 💡 lâmpada → **Melhorias** · ✔ círculo com check → **Validar atualização** · ✨ brilho → **Sugestões de melhoria** · 🎨 paleta → **Aparência** |

- Cada página só é montada na primeira vez que você abre (por isso o painel abre mais rápido). Depois, voltar a ela é na hora.

### 32.2 Início em cartões
- **Status** (em cima): o que ele está fazendo agora — **Ouvindo**, **Pensando**, **Falando**, **Descansando**, **Pausado** ou **Desligado** — com os botões **Ligar** e **Desligar** e a chave "Ligar sozinho quando eu abrir a Central". O rostinho à esquerda é o lugar do avatar (na próxima versão ele se mexe conforme o estado).
- **Fila do pensando**: as perguntas que a IA está resolvendo em segundo plano, com o tempo contando.
- **Atalhos rápidos**: Reiniciar, Pausar/Retomar, Validar atualização, Sugestões, Testar digitando, Teste automático, Atualizar (.zip), Ouvir a voz e Microfone.
- **Últimos comandos**: os 5 últimos pedidos com **OUVI** (o que o microfone entendeu), **ENTENDI** (a frase depois do vocabulário e qual comando atendeu) e **FIZ** (o que ele respondeu).
- Tudo se atualiza sozinho a cada segundo, sem você clicar.
- Mais abaixo continuam: Novidades da versão, Jeitos de chamar e Atalhos úteis.

### 32.3 Voz em abas (com reserva)
- No topo: **"Voz ativa: X · Reserva: Y"**.
- Uma aba por voz: **Kokoro**, **Natural**, **Edge**, **Azure**, **ElevenLabs** e **Windows**. Bolinha **verde** = a ativa; **amarela** = a reserva.
- Em cada aba só o que é daquela voz (qual voz, chave, baixar/instalar) e três botões:
  - **Ativar esta voz**: ele passa a falar com ela.
  - **Testar**: fala a frase de teste com essa voz (sem precisar ativar) e mostra em quantos segundos começou.
  - **Usar como reserva**: se a voz ativa falhar (sem internet, sem chave, ainda carregando), ele fala com a reserva. Se a reserva também falhar, ainda tenta a Kokoro e a Edge.
- Embaixo, **Frase de teste e ajustes**: a frase, **▶ Ouvir** (com a voz ativa), velocidade, tom e fala fluida (valem para todas).
- Mudou? **Salvar e reiniciar**.

---

## Etapa 33: Novidades do Telegram (print, "o que tá tocando", vídeo curto e energia à distância)

Agora o seu robô do Telegram (o mesmo da Etapa 31, "Caminho 2: Telegram") faz mais coisa. Tudo
sem precisar falar "Assessor": é só mandar a mensagem direto pro robô, de qualquer lugar.

### 33.1 Print da tela
- Mande **`print`**: chegam as fotos, uma por monitor, cada uma com a legenda "Monitor N".
- Mande **`print do monitor 2`**: chega só o print daquele monitor.
- Falando no PC: *"Assessor, manda um print no Telegram"*.

### 33.2 "O que tá tocando?"
- Mande **`o que tá tocando`**: ele responde com a música do Spotify, cada aba do YouTube aberta
  (título, se está tocando ou pausada, e em qual monitor) e a janela ativa de cada tela.
- Falando no PC: *"Assessor, o que tá tocando"* — ele fala a mesma resposta.

### 33.3 Vídeo curto
- Mande **`grava 15 segundos do monitor 1`**: ele avisa que está gravando e, no final, manda o
  vídeo daquele monitor. Sem dizer quanto tempo, grava 15 segundos (máximo 60).

### 33.4 Desligar, suspender ou reiniciar pelo Telegram
- Mande **`desligar`**, **`dormir`** (ou `suspender`) ou **`reiniciar`**.
- Ele sempre pergunta primeiro: *"Tem certeza que quer... Responda: sim."* Nada acontece até você
  responder **`sim`**.
- Depois do `sim`, ele avisa que vai fazer em **30 segundos**. Pra cancelar dentro desses 30
  segundos (ou enquanto ele só está esperando a confirmação), mande **`cancela`**.
- No modo de teste (`MESTRE_SIMULAR=1`) nada acontece de verdade — só aparece no diário.

### 33.5 Ligar o PC de fora de casa
Essas novidades só funcionam com o PC **ligado**. Se você desligou pelo Telegram e quiser ligar
de novo estando fora de casa, o jeito mais simples e barato é uma **tomada inteligente Wi-Fi**:

1. **Compre uma tomada inteligente Wi-Fi** (tem barata, com app grátis **Tuya**, **Smart Life** ou
   **Positivo Casa Inteligente**). Ligue o PC nela.
2. **Na BIOS do PC**, procure a opção **"Restore on AC Power Loss"** (às vezes chamada de "AC Back
   Function", "Power Loss Recall" ou "After Power Loss" — o nome muda por fabricante) e deixe em
   **"Power On"** (ligado). Assim, quando a tomada volta a dar energia, o PC liga sozinho, sem
   precisar apertar o botão.
3. **No Windows**, se o PC não ligar direito depois de ficar sem energia, desative a
   **"Inicialização Rápida"**: Painel de Controle > Opções de Energia > "Escolher a função dos
   botões de energia" > "Alterar configurações não disponíveis no momento" > desmarque
   **"Ativar inicialização rápida"**.
4. Como o Assessor já abre sozinho com o Windows (atalho de inicialização, Etapa 7), o fluxo fica:
   **desligar pelo Telegram** → esperar **1 minuto** (pra garantir que desligou de verdade) →
   **desligar e ligar a tomada** pelo app do celular → o PC liga e o Assessor abre sozinho.

> ⚠️ **Nunca corte a tomada com o PC ligado** — desligue sempre pelo Telegram (ou normalmente)
> antes de mexer na tomada, senão arquivos abertos podem se perder.

**Alternativa (sem comprar nada): Wake-on-LAN.** Se o seu roteador permitir "acordar" o PC pela
rede, dá pra ligar sem tomada inteligente. O roteador da Vivo Fibra (`192.168.15.1`) geralmente
**não** tem essa opção no menu dele, mas o PC (ligado por cabo) tem placa de rede Realtek, que
**suporta** Wake-on-LAN — então se um dia você trocar de roteador por um que tenha essa função, o
PC já está pronto para usar.

---

## Etapa 34: Troca de IA sozinho (se uma demorar ou falhar)

Antes, se o Ollama estivesse fechado ou travado, o Mestre simplesmente não conseguia responder.
Agora ele tem uma **lista ordenada de IAs**: se a primeira demorar demais ou der erro, ele tenta a
próxima sozinho, na hora, sem travar a escuta. Quem falhou fica **"de castigo"** por um tempo
(não é tentada de novo até passar) e volta a entrar na roda depois.

- **Ordem padrão:** Ollama (modelo principal) → Ollama (modelo menor, se você escolher um) → Claude
  API (se tiver uma chave salva).
- **Painel > Conversa**, seção **"Troca de IA sozinho (se uma demorar ou falhar)"**:
  - **1ª, 2ª e 3ª opção:** escolha a ordem que preferir.
  - **Modelo do Ollama menor (opcional):** um modelo mais leve para servir de 2ª tentativa
    (ex.: `llama3.2:3b`). Deixe em branco para não usar.
  - **Baixar modelo menor:** não precisa digitar nada no terminal. Escolha um modelo pequeno
    sugerido na lista (com o tamanho aproximado do download) e clique em **"Baixar modelo menor"**.
    O download roda em segundo plano (dá pra continuar usando o painel) e mostra o progresso em %.
    Ao terminar, ele já preenche e **salva sozinho** o campo "Modelo do Ollama menor" acima. Se o
    modelo escolhido já estiver baixado, aparece "✓ já está baixado" e o botão **"Testar"** liga,
    pra confirmar que ele responde. Se o Ollama não estiver instalado ou aberto, aparece uma
    mensagem clara explicando o que fazer.
  - **Tempo por tentativa (s):** quanto tempo espera cada IA antes de desistir e ir pra próxima.
  - **Tempo de castigo (min):** quanto tempo uma IA que falhou fica de fora antes de ser tentada
    de novo.
  - **Chave da API do Claude (opcional):** cole aqui para o Claude entrar na lista como opção
    (fica salva fora do projeto, em `segredos.json`, nunca no `config.yaml`).
- **Log:** cada resposta registra qual IA respondeu de fato (`logs\mestre.log`), útil para conferir
  se ele está usando a que você espera.

**Para testar:** feche o Ollama (ou desligue a rede dele) e faça uma pergunta de conversa livre —
se você configurou uma 2ª opção (outro modelo do Ollama ou o Claude com chave), o Mestre continua
respondendo por ela, sem travar. Reabra o Ollama: depois do tempo de castigo, ele volta a ser a
1ª tentativa.

---

## Etapa 35: Aviso se o PC desligar (healthchecks.io)

Duas coisas novas, para você saber se o PC desligou (ou se a energia faltou) mesmo estando longe
de casa. As duas mandam mensagem pelo mesmo robô do Telegram da Etapa 31.

### 35.1 O que já vem pronto (sem configurar nada)
- Quando o Windows desliga ou reinicia (normalmente), o Assessor manda **"💤 PC
  desligando/reiniciando"**.
- Quando o PC liga de novo, ele manda **"✅ PC ligou"**. Se da última vez o PC tinha sumido sem
  avisar (queda de energia, travou, ou alguém desligou na tomada), ele manda um aviso diferente:
  **"⚠️ o PC tinha desligado sem avisar..."**, com a hora do último sinal dele.
- Painel > **Celular**, seção **"3. Avisos do PC"**: dá para desligar esse aviso se não quiser.

### 35.2 healthchecks.io (opcional, mas recomendado)
O problema do aviso acima: numa queda de energia de verdade, o PC não tem tempo de mandar nada —
ele simplesmente apaga. O **healthchecks.io** resolve isso: o Assessor manda um sinalzinho a cada 5
minutos, e se esse sinal **parar de chegar**, o healthchecks avisa você na hora (por e-mail e, se
quiser, pelo Telegram deles também) — mesmo com o PC desligado.

1. Vá em **healthchecks.io** e crie uma **conta grátis**.
2. Clique em **"Add Check"** (criar um check novo). Em **"Period"** (período), coloque **5 minutos**;
   em **"Grace Time"** (tolerância), coloque **5 minutos** também.
3. Nas integrações do check (**Integrations**), ligue o **e-mail** (já vem pronto, geralmente) e,
   se quiser, o **Telegram** — o próprio site do healthchecks tem um robô deles que você liga em dois
   cliques (não é o robô do Assessor, é outro, só para esse aviso).
4. Copie a **URL do ping** (algo como `https://hc-ping.com/xxxxxxxx-xxxx-xxxx-...`).
5. No Assessor: **Painel > Celular**, seção **"3. Avisos do PC"** — cole a URL no campo **"URL do
   ping"**, ligue o interruptor **"Pulso pro healthchecks.io"** e clique em **"Testar pulso"** para
   conferir que funcionou (o site mostra "Last Ping: agora mesmo").
6. Salve e reinicie o Assessor.

**Resumindo:** os avisos de "PC ligou/desligou" (35.1) vêm do próprio PC, então só funcionam se ele
conseguir avisar. O healthchecks (35.2) é quem avisa **na hora**, de fora, quando o PC nem teve
chance.

---

## Etapa 36: Trocar a saída de som falando (caixinha/fone)

Se você tem a **caixinha de som Bluetooth** e o **fone de ouvido**, agora dá para trocar qual um
está tocando o som sem mexer no Windows.

- **"Mestre, coloca na caixinha de som"** (ou "ativa a caixinha", "joga o som pra caixinha", "troca
  pra caixinha") — muda o som pra caixinha Bluetooth.
- **"Mestre, volta pro fone"** (ou "coloca no fone", "agora tô usando o fone", "som no fone") — muda
  de volta pro fone.
- **"Mestre, troca a saída de som"** — sem dizer qual: alterna entre os dois.
- **"Mestre, qual saída de som tá ativa?"** — ele fala qual está tocando agora.

Se a caixinha estiver com o Bluetooth desligado, ele avisa: *"A caixinha de som não está conectada.
Liga o Bluetooth dela e tenta de novo."*

**Painel > Áudio**, seção **"Saída de som"**: mostra os dispositivos de som que o Windows enxerga
agora, com um campo pra você escrever o apelido de cada um (o padrão já vem com "caixinha" e "fone")
e um botão **"Usar agora"** pra trocar na hora, sem precisar salvar. Se você usa outros nomes (por
exemplo "home office" e "caixa da sala"), é só trocar os apelidos ali e salvar.

## Etapa 37: Ver o que está lento (Tempos)

Nova página **Painel > Sistema > Tempos**: mostra quanto tempo cada etapa está levando, pra achar
o que está deixando ele mais devagar.

- **Fala → texto (Whisper):** quanto tempo ele demora pra transcrever o que você falou.
- **Frase → comando:** quanto tempo demora entre entender o pedido e executar.
- **IA:** um tempo por provedor (Ollama, Claude, Groq...), pra saber qual está mais rápido.
- **Até começar a falar:** quanto tempo demora entre a decisão de responder e o som começar a sair.

Cada linha mostra a **média** e o **pior caso** das últimas 50 vezes, e quantas vezes ele já mediu.
Clique em **"Atualizar"** para reler (não trava o painel: ele lê em segundo plano). Quanto mais você
usa o Assessor, mais completa fica a lista.

---

## Personalizar

Tudo fica no **`config.yaml`** (abra com o Bloco de Notas). Regras de ouro:
- **Nunca use TAB**, só espaços. Mantenha o recuo igual ao das linhas vizinhas.
- Textos **entre aspas**.
- Salvou? **Reinicie o Mestre.**
- Se quebrar, o Mestre mostra *"ERRO NO config.yaml"* e a linha do problema.

### Adicionar um canal do YouTube
1. Abra o canal no YouTube. Na barra de endereço aparece `youtube.com/@NomeDoCanal`.
2. No `config.yaml`, em `canais_youtube:`, adicione uma linha:
   ```yaml
     "apelido que você vai falar": "@NomeDoCanal"
   ```
3. Fale: *"Mestre, abre o último vídeo do apelido"*.

### Adicionar um programa
1. Ache o programa no menu Iniciar > botão direito > **Abrir local do arquivo** > botão direito no atalho > **Propriedades** > copie o **Destino**.
2. Em `programas:`, adicione (troque `\` por `\\`):
   ```yaml
     "spotify": "C:\\Users\\SeuUsuario\\AppData\\Roaming\\Spotify\\Spotify.exe"
   ```

### Adicionar um site
```yaml
  "atende": "https://endereco-do-sistema.com.br"
```

### Criar uma rotina nova
Copie um bloco de rotina existente e mude. Exemplo, uma rotina de estudos:
```yaml
  - nome: "Estudar"
    frases: ["hora de estudar", "bora estudar"]
    acoes:
      - acordar_tela: true
      - falar: "{saudacao}! Modo estudo ativado."
      - volume: "diminuir"
      - abrir_site: "https://www.youtube.com/@CienciaTodoDia"
      - abrir_programa: "bloco de notas"
```
Ações possíveis: `acordar_tela`, `falar`, `abrir_programa`, `abrir_site`, `youtube_ultimo_video`, `youtube_canal`, `esperar`, `volume`, `bloquear`, `desligar_tela`, `comando` (qualquer frase que você falaria, ex.: `comando: "toca lofi no youtube"`). Também dá para criar uma rotina **falando** (veja a Etapa 20).

### Trocar a voz
Veja a [Etapa 13](#etapa-13--voz-e-personalidade): dá para trocar falando. No painel: **Voz** > aba da voz > **Ativar esta voz** (e **Usar como reserva** em outra; Etapa 32).

---

## Lista de comandos

Sempre com **"Mestre"** antes (ou depois: *"bora trabalhar, Mestre"* também funciona). Durante o **modo conversa** (10 segundos depois de cada resposta) não precisa dizer "Mestre".

Os exemplos abaixo são só um ponto de partida: fale do seu jeito ("pô, bota aí o YouTube", "tem como você abrir a calculadora?"). Se algum jeito não funcionar, ensine na Etapa 12.

| Categoria | Exemplos do que falar |
|---|---|
| **Rotinas** | "bora trabalhar" · "hora do café" · "bora relaxar" · "boa noite" |
| **YouTube** | "abre o último vídeo do Manual do Mundo" · "abre o canal Nerdologia" · "toca lofi no YouTube" · "pesquisa receita de bolo no YouTube" · "abre o YouTube" |
| **Mídia** | "pausa" · "continua" |
| **Agente IPM** | "agente IPM, ..." · "ditado pro agente IPM" (… "pronto") · "manda o que eu copiei pro agente IPM" · "abre o agente IPM" |
| **Área de transferência** | "lê pra mim" · "lê o que eu copiei" |
| **Rotina falada** | "vou te mostrar uma nova rotina" → comandos → "pronto" → a frase de chamar · "cancela a rotina" |
| **Ensinar** | "aprende um atalho" · "quando eu falar X, [comando]" · "quais são os atalhos" · "esquece o atalho X" |
| **Voz** | "apresenta as vozes" · "muda a voz" · "usa a voz do Andrew" · "fala mais rápido/devagar" · "fala mais grave/agudo" · "voz normal" |
| **Melhorias** | "anota uma melhoria: ..." · "lê minhas melhorias" · "aplica as melhorias" · "reinicia" |
| **Clima e notícias** | "como tá o tempo?" · "vai chover?" · "quais as notícias?" · "notícias sobre futebol" |
| **Painel** | "abre o painel" |
| **Ditado longo** | "vou ditar" … "pronto" · "apaga a última" · "cancela" · "ditar uma melhoria" |
| **Feedback** | "isso tá errado, era …" · "você errou" · "não era isso" |
| **Educação** | "valeu" · "obrigado" |
| **Programas e sites** | "abre a calculadora" · "abre o Gmail" · "abre o WhatsApp" · "abre o Excel" |
| **Hora e data** | "que horas são?" · "que dia é hoje?" |
| **Volume** | "aumenta o volume" · "abaixa o volume" · "volume no máximo" · "muta" |
| **Saída de som** | "coloca na caixinha de som" · "volta pro fone" · "troca a saída de som" · "qual saída de som tá ativa?" |
| **Tela e PC** | "desliga a tela" · "liga a tela" · "bloqueia o computador" · "desliga o computador" · "cancela o desligamento" · "reinicia o computador" |
| **Lembretes** | "me lembra de beber água em 20 minutos" · "lembrete em 1 hora reunião" |
| **Anotações** | "anota comprar pão" · "lê minhas notas" · "abre minhas notas" |
| **Pesquisa** | "pesquisa previsão do tempo" · "procura no Google restaurantes perto" |
| **Assistente** | "o que você sabe fazer?" · "esquece a conversa" · "encerrar assistente" |
| **Conversa livre** | Qualquer pergunta (precisa do cérebro ligado, Etapas 9 ou 10) |

---

## Problemas comuns

| Problema | Solução |
|---|---|
| `py` não é reconhecido | Reinstale o Python marcando **"Add python.exe to PATH"** (Etapa 1) |
| Erro instalando `vosk` ou `faster-whisper` | Confirme que é o Python **3.12 64-bit**. Instale o [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) e rode o `ferramentas\1_instalar.bat` de novo |
| Não fala nada | Veja se o som do Windows está ligado. Sem internet, a voz "edge" falha: troque `motor: "windows"` no `config.yaml` |
| Não reage quando chamo | Rode `ferramentas\6_listar_microfones.bat`, pegue o número do seu microfone e coloque em `ouvido > microfone`. Confira **Configurações > Privacidade > Microfone > Permitir que aplicativos da área de trabalho acessem** |
| Entende errado | Veja o `Ouvi: '...'` na janela. Fale mais perto do microfone. Troque `modelo_whisper` para `"medium"` (mais preciso, mais lento) |
| Muito lento para responder | Troque `modelo_whisper` para `"base"` ou `"tiny"` |
| Liga sozinho com frases parecidas | Tire variações de `variacoes_aceitas` (deixe só `"mestre"`) |
| O último vídeo não abre | O YouTube muda às vezes. Atualize: abra o cmd na pasta do Mestre e rode `venv\Scripts\pip install -U yt-dlp` |
| Agente IPM cola a pergunta antes da hora | Aumente `segundos_para_carregar` |
| Agente IPM não cola nada | Deixe o Claude logado no navegador **padrão**. Se o cursor não estiver na caixa de mensagem, clique nela uma vez |
| Tela não acorda | Alguns monitores demoram. A tela pode ter entrado em suspensão: refaça a Etapa 6.1 como administrador |
| Não entende meu jeito de falar | Veja na janela a linha `Entendi como: ...`. Adicione o seu jeito em `vocabulario.yaml` (sinônimos) ou ensine um atalho por voz |
| Responde coisas que a TV fala | Diminua `conversa > janela_segundos` para `5` (ou `0` para desligar o modo conversa) |
| "Aplica as melhorias" não abre nada | O Claude Code não está instalado: veja a Etapa 14 |
| Não reconhece minha voz / corta palavras | Faça a **Etapa 17** (calibração). Ligue "Guardar áudios ouvidos" e ouça o que chegou |
| Ativa sozinho com barulho | Painel > Áudio > "Medir ruído" de novo, ou suba o limite |
| O PC fica pesado | Painel > Áudio: modelo `base` ou modo **Leve (Vosk)** |
| "Library cublas64_12.dll is not found" | Você tem placa NVIDIA, mas faltam as bibliotecas dela. A versão atual já usa o processador sozinho. Para usar a placa (muito mais rápido): `ferramentas\11_ativar_placa_de_video.bat` |
| Central/painel não abre | Rode o **`ferramentas\10b_painel_diagnostico.bat`**: ele mostra o motivo na tela. Com muitos canais do YouTube, atualize para a versão 5 (Etapa 23) |
| Painel não abre (a janela preta pisca e some) | Rode o **`ferramentas\10b_painel_diagnostico.bat`**: ele mostra o motivo na tela. Os mais comuns: faltam bibliotecas (o `ferramentas\10_painel.bat` agora instala sozinho) ou o Python sem "tcl/tk" (veja a mensagem). O erro fica em `logs\painel_erro.log` |
| Indicador sumiu | Ele pode estar atrás de um jogo em tela cheia. Reinicie o Mestre ou veja `indicador > mostrar` |
| Corta minha fala no meio | Painel > Áudio: aumente "Pausa que encerra a frase" (ex.: 1,2 s). Para pedidos longos, use o ditado |
| Não responde mais por "mestre" | Você trocou a palavra de ativação no painel: use a nova (Painel > Personalidade) |
| Qualquer outro erro | Abra `logs\mestre.log` com o Bloco de Notas, copie as últimas linhas e me mande |

---

## Próximos passos

**Fase 1 (agora):** Mestre no PC, comandos por voz, rotinas e agente IPM pelo site. ✅

**Fase 2:** mais integrações
- Agenda do Google (*"Mestre, o que tenho hoje?"*)
- Controle do Spotify
- Rotina de "bom dia" com clima e notícias

**Fase 3:** celular
- O "cérebro" vira um pequeno servidor no PC.
- O celular vira um "controle remoto de voz" (app ou página web) que fala com ele pela rede de casa.
- Enquanto isso, o **Claude Dispatch** (que você já usou) já permite mandar tarefas do celular para o PC.

---
*Projeto Mestre · versão 13 · feito com Claude Code*
