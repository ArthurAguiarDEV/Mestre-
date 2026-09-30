"""Exporta o historico para o Claude analisar (painel > Histórico > "Exportar para o Claude").

Gera exportacoes/historico_para_claude_<data>.md com:
  - um resumo (quantos pedidos foram para comando, para a IA, "nao entendi"...);
  - as frases que foram para a IA (candidatas a virar comando simples);
  - as frases ouvidas SEM a palavra de ativacao que parecem ter tentado chamar;
  - os feedbacks ("isso ta errado");
  - a lista completa de pedidos e de tudo que o microfone transcreveu.
So texto (nada de audio). Voce arrasta o arquivo para a conversa com o Claude.
"""
from collections import Counter
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path

from . import memoria
from .config import PASTA_PROJETO, palavras_ativacao
from .texto import normalizar

PASTA_EXPORTACOES = PASTA_PROJETO / "exportacoes"
PERIODOS = {"hoje": 0, "7 dias": 7, "30 dias": 30, "tudo": None}

INSTRUCOES = (
    "> **Claude:** este arquivo foi exportado do assistente de voz Mestre (Python, pasta `app/`).\n"
    "> Analise e me explique em português simples:\n"
    "> 1. frases que foram para a IA ou deram \"não entendi\", mas eram comandos simples → quais padrões\n"
    ">    faltam nos comandos (`_cmd_*` no pacote `app/comandos/`) e quais frases entram em `testes/frases.py`;\n"
    "> 2. erros de transcrição do Whisper (palavras trocadas) → o que entra em `ouvido.palavras_conhecidas`,\n"
    ">    no `vocabulario.yaml` e no glossário da skill corrigir-transcricao;\n"
    "> 3. frases ignoradas que parecem ter tentado chamar (palavra de ativação mal ouvida);\n"
    "> 4. os feedbacks (\"isso tá errado\").\n"
    "> Depois use a skill refinar-pedido para propor as melhorias e espere o meu \"ok\".\n"
)


def _data(item: dict) -> datetime | None:
    texto = str(item.get("data") or "")
    for formato in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue
    return None


def _no_periodo(itens: list[dict], dias: int | None, agora: datetime) -> list[dict]:
    if dias is None:
        return itens
    inicio = datetime(agora.year, agora.month, agora.day) - timedelta(days=dias)
    return [i for i in itens if (_data(i) or agora) >= inicio]


def _celula(texto, limite: int = 160) -> str:
    texto = " ".join(str(texto or "").split()).replace("|", "/")
    return texto if len(texto) <= limite else texto[:limite - 1] + "…"


def _tentou_chamar(texto: str, palavra: str) -> bool:
    """Frase ignorada que comeca com algo parecido com a palavra de ativacao (ex.: "a sessor")."""
    partes = normalizar(texto).split()[:4]
    candidatos = partes + [a + b for a, b in zip(partes, partes[1:])]
    return any(SequenceMatcher(None, c, palavra).ratio() >= 0.6 for c in candidatos if len(c) >= 3)


def _grupo_da_rota(rota: str) -> str:
    rota = str(rota or "")
    if rota.startswith("_cmd_"):
        return "comando"
    if rota.startswith("resposta"):
        return "resposta a uma pergunta"
    return rota or "(sem registro: versão antiga)"


def gerar(cfg: dict, periodo: str = "7 dias", agora: datetime | None = None) -> Path:
    """Cria o arquivo e devolve o caminho."""
    agora = agora or datetime.now()
    dias = PERIODOS.get(periodo, 7)
    pedidos = _no_periodo(memoria.historico(100000), dias, agora)
    ouvidas = _no_periodo(memoria.ouvidas(100000), dias, agora)
    a = cfg.get("assistente") or {}
    variacoes = palavras_ativacao(cfg)
    palavra = variacoes[0]
    cb = cfg.get("cerebro") or {}
    o = cfg.get("ouvido") or {}

    principais = [p for p in pedidos if p.get("tipo") not in ("ia virou comando", "ia executou comando")]
    grupos = Counter(_grupo_da_rota(p.get("rota")) for p in principais)
    comandos = Counter(p["rota"] for p in principais if str(p.get("rota", "")).startswith("_cmd_"))
    para_ia = [p for p in principais if p.get("rota") in ("ia", "nao_entendi")]
    viraram = [p for p in pedidos if p.get("tipo") == "ia virou comando"]
    ignoradas = [x for x in ouvidas if not x.get("chamou") and not x.get("conversa")]
    suspeitas = [x for x in ignoradas if _tentou_chamar(x.get("texto", ""), palavra)]
    tempos = [float(x.get("transcricao_seg") or 0) for x in ouvidas if x.get("transcricao_seg") is not None]

    L = [f"# Histórico do Mestre para o Claude analisar\n",
         f"Exportado em {agora:%d/%m/%Y %H:%M} · período: **{periodo}**\n", INSTRUCOES,
         "## Configuração\n",
         f"- Palavra de ativação: **{palavra}** (aceita também: {', '.join(variacoes[1:12]) or '-'})",
         f"- Nome dele: **{a.get('nome') or 'Mestre'}** · como ele chama o usuário: **{a.get('apelido_usuario') or 'chefe'}**",
         f"- Whisper: `{o.get('modelo_whisper', '?')}` (precisão {o.get('precisao', '-')}) · ativação por: `{o.get('modo_ativacao', 'whisper')}`",
         f"- IA: `{cb.get('tipo', 'nenhum')}` (`{cb.get('ollama_modelo', '')}`) · config versão {cfg.get('versao_config', '?')}\n",
         "## Resumo\n",
         f"- **{len(principais)}** pedidos e **{len(ouvidas)}** frases transcritas pelo microfone "
         f"({len(ignoradas)} ignoradas por não terem a palavra de ativação).",
         "- Para onde os pedidos foram: " + (", ".join(f"{g}: {n}" for g, n in grupos.most_common()) or "-"),
         f"- Transcrição: {sum(tempos) / len(tempos):.1f} s em média, a mais lenta {max(tempos):.1f} s."
         if tempos else "- Transcrição: sem dados ainda (só aparecem frases ditas depois desta versão).", ""]
    if comandos:
        L += ["**Comandos mais usados:** " + ", ".join(f"`{c}` ({n})" for c, n in comandos.most_common(15)), ""]

    L += ["## Frases que foram para a IA ou deram \"não entendi\"\n",
          "Candidatas a virar comando simples (as repetidas primeiro).\n"]
    repetidas = Counter(normalizar(p.get("pedido", "")) for p in para_ia)
    exemplos = {normalizar(p.get("pedido", "")): p for p in para_ia}
    if repetidas:
        L += ["| Vezes | O que ouvi | Entendi como | Para onde foi | Resposta |", "|---|---|---|---|---|"]
        for chave, n in repetidas.most_common(80):
            p = exemplos[chave]
            L.append(f"| {n} | {_celula(p.get('pedido'))} | {_celula(p.get('entendi'))} | {p.get('rota')} | "
                     f"{_celula(p.get('resposta'), 100)} |")
    else:
        L.append("(nenhuma)")
    L.append("")

    L += ["## Frases que a IA transformou em comando\n",
          "Funcionaram, mas passaram pela IA (lento): faltam no vocabulário.\n"]
    if viraram:
        L += ["| Hora | O que ouvi | A IA entendeu | Comando |", "|---|---|---|---|"]
        L += [f"| {p.get('data')} | {_celula(p.get('pedido'))} | {_celula(p.get('entendi'))} | {p.get('rota')} |"
              for p in viraram[-80:]]
    else:
        L.append("(nenhuma)")
    L.append("")

    L += [f"## Frases ignoradas que parecem ter chamado \"{palavra}\"\n",
          "O Whisper pode ter escrito a palavra de ativação de outro jeito.\n"]
    if suspeitas:
        L += ["| Hora | Texto |", "|---|---|"] + [f"| {x.get('data')} | {_celula(x.get('texto'))} |" for x in suspeitas[-60:]]
    else:
        L.append("(nenhuma)")
    L.append("")

    melhorias = PASTA_PROJETO / "MELHORIAS.md"
    feedbacks = [l.strip() for l in melhorias.read_text(encoding="utf-8").splitlines()
                 if "FEEDBACK:" in l] if melhorias.exists() else []
    L += ["## Feedbacks (\"isso tá errado\")\n"] + ([f"- {_celula(l, 400)}" for l in feedbacks[-40:]] or ["(nenhum)"]) + [""]

    retrato = PASTA_PROJETO / "logs" / "youtube_retrato.txt"
    if retrato.exists():
        L += ["## Retrato da página do YouTube (a última vez que ele não achou vídeos)\n", "```",
              retrato.read_text(encoding="utf-8")[:6000], "```", ""]

    L += ["## Todos os pedidos (em ordem)\n"]
    if principais:
        L += ["| Hora | O que ouvi | Entendi como | Quem atendeu | Resposta |", "|---|---|---|---|---|"]
        L += [f"| {p.get('data')} | {_celula(p.get('pedido'))} | {_celula(p.get('entendi'))} | "
              f"{p.get('rota') or p.get('tipo', '')} | {_celula(p.get('resposta'), 120)} |" for p in principais[-1500:]]
    else:
        L.append("(nada no período)")
    L.append("")

    L += ["## Tudo que o microfone transcreveu\n",
          "Chamou = tinha a palavra de ativação · Conversa = veio logo depois de uma resposta (sem precisar chamar).\n"]
    if ouvidas:
        L += ["| Hora | Texto | Chamou | Conversa | Ditado | Áudio (s) | Transcrição (s) |", "|---|---|---|---|---|---|---|"]
        sim = lambda v: "sim" if v else ""   # noqa: E731
        L += [f"| {x.get('data')} | {_celula(x.get('texto'), 220)} | {sim(x.get('chamou'))} | {sim(x.get('conversa'))} | "
              f"{sim(x.get('ditado'))} | {x.get('audio_seg', '')} | {x.get('transcricao_seg', '')} |" for x in ouvidas[-3000:]]
    else:
        L.append("(nada no período: as frases do microfone começam a ser guardadas nesta versão)")

    PASTA_EXPORTACOES.mkdir(exist_ok=True)
    arquivo = PASTA_EXPORTACOES / f"historico_para_claude_{agora:%Y-%m-%d_%H%M}.md"
    arquivo.write_text("\n".join(L) + "\n", encoding="utf-8")
    return arquivo
