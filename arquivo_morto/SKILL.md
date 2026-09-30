---
name: refinar-pedido
description: Transforma um pedido falado ou escrito de forma solta (ideias misturadas, frases longas, ditado por voz) num pedido claro e organizado, pronto para implementar. Use SEMPRE que o usuário mandar um pedido novo para o Mestre (inclusive os que chegam com "[Pedido ditado por voz no Mestre...]"), itens do MELHORIAS.md, ou pedir "melhora esse prompt", "organiza meu pedido", "refina essa ideia". Primeiro corrige a transcrição (skill corrigir-transcricao), depois organiza em cartões e espera o "ok".
---

# Refinar pedido

O usuário fala por voz e não é programador. Os pedidos chegam longos, com várias ideias
juntas, repetições e palavras de transcrição ("né", "tipo assim", "entendeu?"). Seu trabalho
é **entender a intenção** e devolver um pedido claro, **sem inventar requisitos**.

## Passos

0. **Corrija a transcrição primeiro.** Use a skill **corrigir-transcricao** (se ela não estiver
   disponível, siga as mesmas regras: corrigir escrita e nomes próprios sem mudar o sentido,
   ex.: "OLA" → Ollama, "EPM" → empresa, "cloud code" → Claude Code). Mostre o resultado em
   **"Entendi assim:"** (curto) antes dos cartões, para ele conferir se você entendeu certo.
1. **Separe as ideias.** Um pedido falado costuma ter 3–8 ideias diferentes. Liste cada uma
   separadamente, uma frase cada, na ordem em que apareceram.
2. **Para cada ideia, escreva o cartão abaixo.** Use as palavras do usuário sempre que puder.
3. **Marque o que é incerto.** Se faltar informação para fazer bem feito, escreva a dúvida
   em "Perguntas", com uma sugestão de resposta padrão (para ele só confirmar).
4. **Aponte limites reais** (do Windows, de custo, de privacidade) sem rodeios, com a alternativa.
5. **Sugira uma ordem de execução**: primeiro o que destrava os outros ou dá mais resultado com menos esforço.
6. **Mostre o resultado ao usuário e espere o "ok"** antes de implementar qualquer coisa.

## Formato do cartão

```
### <número>. <título curto, verbo no infinitivo>
**O que ele quer:** <1–2 frases, na linguagem dele>
**Por quê:** <o problema que isso resolve>
**Como fica para ele:** <o que ele vai ver, falar ou clicar quando estiver pronto>
**Pronto quando:**
- [ ] <critério testável, de preferência uma frase que ele fala ou um clique>
- [ ] <...>
**Fora do escopo:** <o que NÃO faz parte, para não crescer demais>
**Perguntas:** <dúvidas + sugestão padrão; ou "nenhuma">
**Tamanho:** pequeno | médio | grande
```

## Regras

- Português simples, frases curtas, sem jargão (se precisar de um termo técnico, explique entre parênteses).
- Não prometa o que não dá (ex.: "desbloquear o Windows com a senha por voz"): explique o limite e ofereça a alternativa.
- Tudo deve continuar **grátis** e rodando **no PC dele**, a menos que ele peça outra coisa.
- Se o pedido estiver em MELHORIAS.md, reescreva o item lá embaixo da linha original, recuado,
  mantendo a linha original para ele reconhecer o que falou.

## Exemplo

Entrada (ditado):
> "queria que ele lesse minha agenda de manhã, tipo, e também que quando eu falar bom dia ele já
> fale o clima, e sei lá, as notícias, mas não muitas, entendeu?"

Saída:

```
### 1. Ler a agenda do dia no "bom dia"
**O que ele quer:** ouvir os compromissos do dia quando falar "bom dia".
**Por quê:** começar o dia sabendo o que tem, sem abrir o calendário.
**Como fica para ele:** "Mestre, bom dia" → "Hoje você tem 2 compromissos: 10h reunião..."
**Pronto quando:**
- [ ] Falando "bom dia", ele lê os compromissos de hoje em até 5 segundos
- [ ] Se não houver compromissos, ele diz "agenda livre hoje"
**Fora do escopo:** criar ou mudar compromissos por voz.
**Perguntas:** Qual agenda? (sugestão: Google Agenda, via link secreto iCal, grátis)
**Tamanho:** médio

### 2. Clima e poucas notícias no "bom dia"
...
```
