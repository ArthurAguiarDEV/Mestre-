---
name: avaliar-esforco
description: Use antes de mandar um pedido grande ao Claude Code ou quando o usuário perguntar qual esforço/modelo usar, "valida esse prompt", "quanto isso vai gastar" ou /avaliar-esforco. Classifica em baixo, médio, alto, extra ou máximo e diz como gastar menos.
argument-hint: [o pedido que você vai mandar]
model: haiku
effort: low
---

# Avaliar esforço do pedido

Objetivo: dizer, ANTES de executar, qual nível de esforço (`/effort`) e qual modelo o pedido realmente precisa, e como quebrá-lo para gastar menos da sessão. Esta skill NÃO executa o pedido.

Pedido a avaliar: $ARGUMENTS
(Se vier vazio, avalie a última mensagem do usuário com um pedido.)

## Passo 1: separar os itens

Texto ditado costuma juntar várias ideias. Um pedido com 3 ideias são 3 avaliações.

## Passo 2: pontuar cada item (0 a 2 por critério)

| Critério | 0 | 1 | 2 |
|---|---|---|---|
| Clareza | Diz exatamente o que fazer | 1–2 decisões em aberto | Vago, várias interpretações |
| Tamanho | 1 arquivo, poucas linhas | 2–4 arquivos | 5+ arquivos ou arquivo gigante (comandos.py, painel.py) |
| Raciocínio | Mecânico (texto, config, vocabulário, cor) | Lógica nova comum | Bug sem causa, threads, arquitetura, refatoração grande |
| Risco | Fácil de desfazer | Algo usado todo dia | Irreversível, dados, integrações |
| Verificação | Teste automático prova | Teste parcial | Só dá para provar no PC / sem teste |

## Passo 3: nível

| Soma | Nível (`/effort`) | Modelo |
|---|---|---|
| 0–2 | baixo (`low`) | Sonnet ou Haiku |
| 3–4 | médio (`medium`) | Sonnet |
| 5–6 | alto (`high`) | Opus |
| 7–8 | extra (`xhigh`) | Opus |
| 9–10 | máximo (`max`) | Opus, só depois de quebrar |

Regras acima da soma:
- Implementar plano JÁ aprovado: no máximo médio.
- Planejar algo com Tamanho 2: pelo menos alto.
- Debug com traceback/log claro: médio. Sem pista: alto ou extra.
- Soma 9–10: recomende quebrar antes de recomendar `max`.

## Passo 4: gastar menos (2–3 dicas concretas)

O que mais consome a sessão é contexto (arquivos grandes relidos, conversa longa) e número de voltas, não só o esforço.
1. Um item por sessão (`/clear` entre eles); itens mecânicos em lote no nível baixo.
2. Planejar caro, executar barato: plano em alto/extra; sessão nova em médio para implementar.
3. Subagente para ler muito: "use um subagente para achar onde X está em comandos.py e me dar só as linhas".
4. Apontar arquivo e função evita busca.
5. Contexto acima de ~40%: `/compact` com dica ou `/clear` + resumo antes do pedido.
6. Teste automático uma vez no fim (o hook já faz isso).

## Saída (curta, neste formato)

```
NÍVEL: <baixo|médio|alto|extra|máximo>  ·  MODELO: <Haiku|Sonnet|Opus>
Por quê: <1 frase>
Pontuação: clareza X · tamanho X · raciocínio X · risco X · verificação X = N

Quebrar em: (se mais de 1 item ou soma ≥ 7)
1. <item> → <nível>

Para gastar menos:
- <dica 1>
- <dica 2>

Comando: /effort <nível>   (e /model <modelo> se mudar)
```

Critério desconhecido: pontue pelo pior caso e diga isso em meia frase.

## Gotchas
- Pedido ditado longo quase nunca é "extra" inteiro: costuma ser 1 item alto + vários baixos.
- Alto como padrão desperdiça sessão: vocabulário, texto do guia, cor do painel e config são baixo.
- Dividir comandos.py: planejamento extra, execução médio, uma fatia por sessão.
- Não recomende `max` para pedido vago: vago pede refinar-pedido, não mais esforço.
