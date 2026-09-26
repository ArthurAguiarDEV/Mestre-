---
name: corrigir-transcricao
description: Corrige um texto que veio de transcrição de voz (ditado, Whisper, microfone do celular) antes de qualquer outra coisa - erros de português, letras e palavras faltando, nomes próprios escritos errado (ex. "OLA" → Ollama, "EPM" → IPM, "cloud code" → Claude Code) - sem mudar o sentido. Use sempre que o usuário mandar um pedido falado/ditado, um texto com cara de transcrição, ou pedir "corrige a transcrição", "arruma esse texto que eu ditei". Vem ANTES do refinar-pedido.
---

# Corrigir transcrição

O usuário dita por voz. O texto chega com erros de reconhecimento: palavras trocadas por outras
de som parecido, letras faltando, sem pontuação, nomes próprios deformados e muitas palavras de
apoio ("né", "tipo assim", "entendeu?"). Seu trabalho é devolver **o mesmo pedido, bem escrito**.

## Regras

1. **Nunca mude o sentido.** Não acrescente ideias, não tire pedidos, não "melhore" a opinião dele.
2. **Corrija a escrita:** ortografia, acentos, concordância, pontuação e letras faltando.
3. **Troque palavras que o reconhecimento errou** usando o contexto e o glossário abaixo.
   Só troque quando tiver certeza razoável; se estiver em dúvida, mantenha e marque com `[?]`.
4. **Tire muletas e repetições** ("né", "tipo assim", "entendeu", "enfim", frases repetidas),
   mas mantenha tudo que tem conteúdo.
5. **Frases curtas.** Quebre frases enormes em frases menores e em parágrafos por assunto.
6. Português do Brasil, linguagem simples. Mantenha a primeira pessoa ("eu quero…").

## Glossário (o que o Whisper costuma errar → o certo)

| Ouvido como | Certo |
|---|---|
| OLA, OMA, Olá, olama, o lama, lhama, LLAM, "IA da OMA" | **Ollama** (IA grátis que roda no PC) |
| EPM, IPN, IBM, ipê eme | **IPM** (empresa / agente IPM) |
| atende net, atendeu net | **Atende.Net** |
| cloud, clóvis, cláudio, Claudia | **Claude** |
| cloud code, clock code, claude cold | **Claude Code** |
| esquio, esquil, squil, skil | **skill** (habilidade) |
| prompt, pronto (quando fala de "mandar um pronto") | **prompt** |
| mestre, mestres, mestra | **Mestre** (é como o assistente chama o USUÁRIO; também o nome do programa) |
| a sessor, acessor, assesor, assessora, sessor (chamando o assistente) | **Assessor** (o assistente; palavra de ativação) |
| jarvis, jarves, járvis | **Jarvis** |
| pop up, popape | **pop-up** |
| multa (o Spotify, o som) | **muta** |
| Petrovski, Petrovsk, Petroski | **DJ Petroski** |
| Engentes na Shield, agentes da xilde, agentes da Shields | **Agentes da S.H.I.E.L.D.** |
| avenida Disney | **abre a Disney** [?] |
| Kokoro, cocoro, cocorô | **Kokoro** (voz que roda no PC) |
| Ajur, azur, azure | **Azure** (Microsoft) |
| eleven labs, onze labs, elevenlabs | **ElevenLabs** (voz paga, a mais natural) |
| chater box, chatter box, chat box (falando de voz) | **Chatterbox** (voz natural grátis na placa de vídeo) |
| iutube, you tube | **YouTube** |
| uísper, whisper | **Whisper** |
| config ponto yaml, config iamel | **config.yaml** |
| melhorias ponto md | **MELHORIAS.md** |
| guit rub, github | **GitHub** |
| painel, paine | **painel** |
| paginamento | **paginação** |
| lateralizada | **foi para o lado** (segundo plano) |
| espotifai, spotfy | **Spotify** |

O glossário cresce: quando o usuário corrigir uma palavra, acrescente aqui a linha nova.

## Formato da resposta

```
**Entendi assim:**
<o texto corrigido, em parágrafos curtos>

<se houve trocas importantes, uma linha:> Troquei: "OLA" → Ollama · "EPM" → IPM · [?] = não tenho certeza
```

Depois disso, siga para o **refinar-pedido** (cartões + esperar o "ok"), usando o texto corrigido.
Se o pedido for curto e claro (uma ideia só), mostre o "Entendi assim" em uma linha e siga.
