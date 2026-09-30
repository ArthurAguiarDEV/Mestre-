"""Sugestoes de melhoria: 1x por dia olha o que aconteceu e monta uma lista (NAO muda nada no projeto).

Le memoria/historico.jsonl e memoria/ouvido.jsonl desde a ultima analise (no minimo as ultimas 24 h) e procura:
  - frases descartadas pelo ouvido, agrupadas pelo `motivo` (curta demais, voz nao reconhecida...);
  - "sem a palavra de ativacao" com uma palavra parecida com ela (o Whisper escreveu de outro jeito);
  - frases que cairam na IA ("rota": "ia") mas comecam com verbo de comando (abre, toca, pausa, volume...);
  - "nao entendi";
  - o mesmo pedido repetido logo em seguida (sinal de que a primeira vez deu errado);
  - jeitos novos de falar que funcionaram (para entrar em testes/frases.py).
Grava em memoria/sugestoes.json. Sem IA obrigatoria: se a IA estiver ligada, o Agendador pede um resumo
curto em segundo plano (nunca trava nada).

Agendador: thread dentro do Assessor (app/main.py) que roda 1x por dia na hora do config
(sugestoes > hora, padrao "08:00"); se o PC estava desligado nessa hora, roda na proxima abertura.
O painel (Sistema > Sugestões de melhoria) lista, marca e manda as marcadas para o Claude pelo mesmo fluxo
supervisionado da validacao (validacao.salvar_pedido_correcao / prompt_curto / comando_para_abrir_claude).
"""
import json
import logging
import re
import threading
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path

from .config import PASTA_PROJETO
from .texto import normalizar

log = logging.getLogger(__name__)
ARQUIVO_SUGESTOES = PASTA_PROJETO / "memoria" / "sugestoes.json"
ARQUIVO_FRASES_TESTE = PASTA_PROJETO / "testes" / "frases.py"
HORA_PADRAO = "08:00"
JANELA_MINIMA = 24 * 3600          # sempre olha pelo menos as ultimas 24 h
JANELA_MAXIMA = 7 * 24 * 3600      # PC desligado uma semana: olha no maximo 7 dias
REPETIDO_SEGUNDOS = 30             # o mesmo pedido de novo em ate 30 s = provavelmente deu errado
MAX_EVIDENCIAS = 12
ATRASO_INICIAL = 60                # o agendador espera o Assessor terminar de ligar
INTERVALO = 60                     # confere a hora uma vez por minuto (aguenta o PC hibernar)

VERBOS_COMANDO = {
    "abre", "abrir", "abra", "abri", "toca", "tocar", "toque", "pausa", "pausar", "pause", "volume", "aumenta",
    "aumentar", "abaixa", "abaixar", "diminui", "diminuir", "fecha", "fechar", "feche", "liga", "desliga", "para",
    "proximo", "proxima", "volta", "voltar", "pula", "pular", "coloca", "colocar", "bota", "botar", "poe", "mostra",
    "minimiza", "maximiza", "muda", "mudar", "troca", "trocar", "joga", "jogar", "manda", "tira", "tirar", "print",
    "busca", "buscar", "pesquisa", "pesquisar", "procura", "procurar", "silencia", "mudo", "separa", "junta",
    "continua", "retoma", "reinicia", "curte", "curtir", "passa", "avanca", "roda", "rodar", "executa",
}
ENCHIMENTO = {"e", "ai", "ei", "oi", "po", "pode", "por", "favor", "ah", "entao", "ne", "tipo", "o", "a", "me"}
# o mesmo pedido de novo e normal nestes (aumenta o volume, aumenta o volume...)
REPETIR_E_NORMAL = ("_cmd_volume", "_cmd_midia", "_cmd_youtube_controle", "_cmd_pensamento")
# rotas que nao sao "jeito de pedir um comando" (continuar a conversa, feedback...)
FORA_DAS_VARIACOES = ("_cmd_pensamento", "_cmd_feedback", "_cmd_conversinha", "_cmd_obrigado")
CONSELHOS_MOTIVO = {
    "curta demais": "Frases jogadas fora por serem curtas demais. Se eram pedidos de verdade, baixar a fala "
                    "mínima (painel > Áudio > Ajustes de captação).",
    "voz não reconhecida": "O ouvido achou que não era a sua voz. Talvez baixar a exigência ou regravar a sua "
                           "voz (painel > Áudio > Responder só à minha voz).",
    "transcrição vazia": "Barulho que virou frase vazia. Se estava falando, conferir o microfone e o limite de volume.",
    "cortada": "Frases cortadas porque o assistente começou a falar por cima.",
}
LIMITE_MOTIVO = {"voz não reconhecida": 1, "curta demais": 2}   # os outros: a partir de 2


# =====================================================================
#  Leitura
# =====================================================================
def _ts(registro: dict) -> float:
    from .validacao import _ts as ts
    return ts(registro)


def _data(registro: dict) -> str:
    t = _ts(registro)
    return datetime.fromtimestamp(t).strftime("%d/%m %H:%M") if t else str(registro.get("data") or "")


def _conselho(motivo: str) -> str:
    for chave, texto in CONSELHOS_MOTIVO.items():
        if motivo.startswith(chave):
            return texto
    return "Frases jogadas fora pelo ouvido com este motivo: conferir se eram pedidos de verdade."


def _sem_palavra(texto: str, palavras: list[str]) -> str:
    """A frase normalizada, sem a palavra de ativacao nem enchimento no comeco."""
    n = normalizar(texto).split()
    while n and (n[0] in palavras or n[0] in ENCHIMENTO):
        n = n[1:]
    while n and n[-1] in palavras:   # "pode descansar, Assessor"
        n = n[:-1]
    return " ".join(n)


def _primeiro_verbo(texto: str) -> str:
    for p in normalizar(texto).split()[:3]:
        if p in VERBOS_COMANDO:
            return p
        if p not in ENCHIMENTO:
            return ""
    return ""


def _parecida_com_palavra(texto: str, palavra: str, variacoes: list[str]) -> str:
    """Uma das 3 primeiras palavras parece a palavra de ativacao (mas nao e nenhuma das variacoes aceitas)?"""
    for p in normalizar(texto).split()[:3]:
        if p in variacoes or len(p) < 4:
            continue
        if SequenceMatcher(None, p, palavra).ratio() >= 0.7:
            return p
    return ""


def _sugestao(tipo: str, chave: str, titulo: str, detalhe: str, evidencias: list[dict]) -> dict:
    return {"id": f"{tipo}:{chave}", "tipo": tipo, "titulo": titulo, "detalhe": detalhe,
            "quantas": len(evidencias), "evidencias": evidencias[-MAX_EVIDENCIAS:]}


# =====================================================================
#  Analise (funcao pura: o teste chama com historico/ouvido sinteticos)
# =====================================================================
def analisar(historico: list[dict], ouvidas: list[dict], desde: float, palavra: str = "mestre",
             variacoes: list[str] | None = None, frases_conhecidas: str | None = None) -> list[dict]:
    """A lista de sugestoes (as mais frequentes primeiro). Nada e alterado."""
    palavra = (normalizar(palavra).split() or ["mestre"])[-1]
    variacoes = [normalizar(v) for v in (variacoes or [palavra])]
    if palavra not in variacoes:
        variacoes.append(palavra)
    if frases_conhecidas is None:
        try:
            frases_conhecidas = ARQUIVO_FRASES_TESTE.read_text(encoding="utf-8")
        except OSError:
            frases_conhecidas = ""
    conhecidas = normalizar(frases_conhecidas)
    ouv = [o for o in ouvidas if _ts(o) >= desde]
    hist = [h for h in historico if _ts(h) >= desde]
    antigos = [h for h in historico if _ts(h) < desde]
    sugestoes: list[dict] = []

    # 1) descartes pelo motivo
    por_motivo: "OrderedDict[str, list]" = OrderedDict()
    grafias: "OrderedDict[str, list]" = OrderedDict()
    for o in ouv:
        motivo = str(o.get("motivo") or "")
        # (esperas e interrupcoes nao sao descarte; "falando" = em geral o eco da propria voz dele)
        if not motivo or motivo.startswith(("só a palavra", "terminou no meio", "interrompeu", "falando")):
            continue
        texto = str(o.get("texto") or "")
        if motivo.startswith("sem a palavra"):
            parecida = _parecida_com_palavra(texto, palavra, variacoes)
            if parecida:
                grafias.setdefault(parecida, []).append({"data": _data(o), "frase": texto, "info": motivo})
            continue   # o resto e conversa normal (TV, outras pessoas): nao vira sugestao
        chave = "cortada" if motivo.startswith("cortada") else motivo
        por_motivo.setdefault(chave, []).append({"data": _data(o), "frase": texto or "(sem texto)", "info": motivo})
    for motivo, ev in por_motivo.items():
        if len(ev) >= LIMITE_MOTIVO.get(motivo, 2):
            sugestoes.append(_sugestao("descartada", normalizar(motivo), f"{len(ev)} frase(s) descartadas: {motivo}",
                                       _conselho(motivo), ev))
    for grafia, ev in grafias.items():
        sugestoes.append(_sugestao(
            "palavra", grafia, f"O Whisper escreveu a palavra de ativação como “{grafia}” ({len(ev)}x)",
            f"Essas frases foram ignoradas por não ter “{palavra}”. Acrescentar “{grafia}” nas variações aceitas "
            "(ou no prompt do Whisper, Transcritor.PROMPT em app/audio.py).", ev))

    # 2) cairam na IA mas tem cara de comando  3) nao entendi
    pedidos = [h for h in hist if h.get("tipo") == "comando" and h.get("rota") != "_cmd_feedback"]
    viraram = [h for h in hist if h.get("tipo") in ("ia executou comando", "ia virou comando")]
    na_ia: "OrderedDict[str, list]" = OrderedDict()
    nao_entendi = []
    for h in pedidos:
        rota = str(h.get("rota") or "")
        frase = str(h.get("pedido") or "")
        entendi = str(h.get("entendi") or "")
        if rota == "ia":
            verbo = _primeiro_verbo(entendi or _sem_palavra(frase, variacoes))
            if verbo:
                virou = [v for v in viraram if -10 <= _ts(v) - _ts(h) <= 120]   # (o "executou" vem antes do pedido)
                info = f"entendi “{entendi}”" + (f" · a IA depois fez {virou[0].get('rota')}" if virou else "")
                na_ia.setdefault(verbo, []).append({"data": _data(h), "frase": frase, "info": info})
        elif rota == "nao_entendi":
            nao_entendi.append({"data": _data(h), "frase": frase, "info": f"entendi “{entendi}”"})
    for verbo, ev in na_ia.items():
        sugestoes.append(_sugestao(
            "ia", verbo, f"Frases com “{verbo}” caíram na IA ({len(ev)}x)",
            "Parecem comandos simples: virar regex no comando certo (pacote app/comandos/, um arquivo por assunto) + linha em testes/frases.py, "
            "para não depender da IA.", ev))
    if nao_entendi:
        sugestoes.append(_sugestao("nao_entendi", "geral", f"“Não entendi” ({len(nao_entendi)}x)",
                                   "Pedidos que nenhum comando atendeu: ver se falta comando, sinônimo no "
                                   "vocabulario.yaml ou se foi erro de transcrição.", nao_entendi))

    # 4) o mesmo pedido repetido logo em seguida
    repetidos = []
    for a, b in zip(pedidos, pedidos[1:]):
        ta, tb = _sem_palavra(a.get("entendi") or a.get("pedido") or "", variacoes), \
            _sem_palavra(b.get("entendi") or b.get("pedido") or "", variacoes)
        if not ta or not tb or 0 > _ts(b) - _ts(a) or _ts(b) - _ts(a) > REPETIDO_SEGUNDOS:
            continue
        if str(a.get("rota") or "").startswith(REPETIR_E_NORMAL) and a.get("rota") == b.get("rota"):
            continue
        if SequenceMatcher(None, ta, tb).ratio() >= 0.75:
            repetidos.append({"data": _data(b), "frase": f"{a.get('pedido')} → {b.get('pedido')}",
                              "info": f"1ª vez: {a.get('rota') or '?'} · 2ª vez: {b.get('rota') or '?'}"})
    if repetidos:
        sugestoes.append(_sugestao("repetido", "geral", f"Pedidos repetidos logo em seguida ({len(repetidos)}x)",
                                   "Pedir de novo em poucos segundos costuma ser sinal de que a 1ª vez deu errado: "
                                   "conferir o que ele fez na 1ª.", repetidos))

    # 5) jeitos novos de falar que funcionaram
    ja_vistos = {(str(h.get("rota")), _sem_palavra(h.get("pedido") or "", variacoes)) for h in antigos}
    novas: "OrderedDict[str, list]" = OrderedDict()
    vistos_agora = set()
    for h in pedidos:
        rota = str(h.get("rota") or "")
        if not rota.startswith("_cmd_") or rota in FORA_DAS_VARIACOES:
            continue
        frase = _sem_palavra(h.get("pedido") or "", variacoes)
        if len(frase.split()) < 2 or (rota, frase) in ja_vistos or (rota, frase) in vistos_agora \
                or (frase and frase in conhecidas):
            continue
        vistos_agora.add((rota, frase))
        novas.setdefault(rota, []).append({"data": _data(h), "frase": str(h.get("pedido") or ""),
                                           "info": f"entendi “{h.get('entendi') or frase}”"})
    for rota, ev in novas.items():
        sugestoes.append(_sugestao(
            "variacao", rota, f"{len(ev)} jeito(s) novo(s) de falar que funcionaram ({rota})",
            f"Acrescentar em testes/frases.py com o comando {rota}, para não quebrar numa mudança futura.", ev))

    ordem = {"descartada": 0, "palavra": 0, "ia": 1, "nao_entendi": 1, "repetido": 1, "variacao": 2}
    sugestoes.sort(key=lambda s: (ordem.get(s["tipo"], 3), -s["quantas"]))
    return sugestoes


# =====================================================================
#  Arquivo memoria/sugestoes.json
# =====================================================================
def ler(arquivo: Path | None = None) -> dict:
    try:
        return json.loads(Path(arquivo or ARQUIVO_SUGESTOES).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def ultima_analise(arquivo: Path | None = None) -> float | None:
    try:
        return float(ler(arquivo).get("ts"))
    except (TypeError, ValueError):
        return None


def _gravar(dados: dict, arquivo: Path) -> None:
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    temp = arquivo.with_suffix(".tmp")
    temp.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    temp.replace(arquivo)


# =====================================================================
#  Botao "Aplicar" (so tipo "palavra": Whisper escreveu a palavra de ativacao errado).
#  Grava direto no vocabulario (sem IA); os outros tipos continuam so indo ao Claude.
# =====================================================================
def troca_da_sugestao(sugestao: dict, palavra_oficial: str) -> tuple[str, str] | None:
    """Para uma sugestao tipo "palavra": (jeito ouvido, palavra oficial) a trocar. None se nao for desse tipo."""
    if (sugestao or {}).get("tipo") != "palavra":
        return None
    partes = str(sugestao.get("id") or "").split(":", 1)
    jeito = normalizar(partes[1]) if len(partes) > 1 else ""
    return (jeito, normalizar(palavra_oficial)) if jeito else None


def marcar_aplicada(sugestao_id: str, jeito: str, oficial: str, arquivo: Path | None = None,
                     no_config: bool = False) -> None:
    """Marca a sugestao como aplicada (some da lista ativa) e guarda no historico p/ Desfazer.

    no_config: True se "jeito" tambem foi acrescentado em config.yaml (assistente > variacoes_aceitas),
    pra ele ACORDAR com essa pronuncia (nao so traduzir); o Desfazer usa isso pra saber se tira de la tambem."""
    arquivo = Path(arquivo or ARQUIVO_SUGESTOES)
    dados = ler(arquivo)
    for s in dados.get("sugestoes") or []:
        if s.get("id") == sugestao_id:
            s["aplicada"] = True
    dados.setdefault("aplicadas", []).append({
        "id": sugestao_id, "jeito": jeito, "oficial": oficial, "no_config": bool(no_config),
        "quando": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    })
    _gravar(dados, arquivo)


def desfazer_ultima_aplicacao(arquivo: Path | None = None) -> dict | None:
    """Tira a marca "aplicada" da ultima sugestao aplicada (ela volta a aparecer na lista)."""
    arquivo = Path(arquivo or ARQUIVO_SUGESTOES)
    dados = ler(arquivo)
    aplicadas = dados.get("aplicadas") or []
    if not aplicadas:
        return None
    ultima = aplicadas.pop()
    for s in dados.get("sugestoes") or []:
        if s.get("id") == ultima.get("id"):
            s.pop("aplicada", None)
    _gravar(dados, arquivo)
    return ultima


def ultima_aplicacao(arquivo: Path | None = None) -> dict | None:
    aplicadas = ler(arquivo).get("aplicadas") or []
    return aplicadas[-1] if aplicadas else None


def _palavra_do_config(cfg: dict | None) -> tuple[str, list[str]]:
    from .config import palavras_ativacao
    variacoes = palavras_ativacao(cfg or {})
    return variacoes[0], variacoes


def rodar(cfg: dict | None = None, agora: float | None = None, historico: list[dict] | None = None,
          ouvidas: list[dict] | None = None, arquivo: Path | None = None, automatica: bool = False) -> dict:
    """Analisa desde a ultima analise (no minimo 24 h, no maximo 7 dias) e grava o sugestoes.json."""
    arquivo = Path(arquivo or ARQUIVO_SUGESTOES)
    agora = time.time() if agora is None else agora
    if historico is None or ouvidas is None:
        from . import memoria
        historico = memoria.historico(5000) if historico is None else historico
        ouvidas = memoria.ouvidas(5000) if ouvidas is None else ouvidas
    ultima = ultima_analise(arquivo)
    desde = agora - JANELA_MINIMA if ultima is None else min(ultima, agora - JANELA_MINIMA)
    desde = max(desde, agora - JANELA_MAXIMA)
    palavra, variacoes = _palavra_do_config(cfg)
    lista = analisar(historico, ouvidas, desde, palavra, variacoes)
    dados = {"gerado_em": datetime.fromtimestamp(agora).strftime("%d/%m/%Y %H:%M"), "ts": round(agora, 2),
             "desde": round(desde, 2), "desde_texto": datetime.fromtimestamp(desde).strftime("%d/%m/%Y %H:%M"),
             "automatica": automatica, "sugestoes": lista, "resumo_ia": ""}
    _gravar(dados, arquivo)
    log.info("Sugestões de melhoria: %d (desde %s)", len(lista), dados["desde_texto"])
    return dados


def resumir_com_ia(cerebro, dados: dict, arquivo: Path | None = None) -> str:
    """Resumo curto das sugestoes pela IA (Ollama/Claude). Chame SEMPRE numa thread: pode demorar."""
    if not cerebro or not getattr(cerebro, "ligado", False) or not dados.get("sugestoes"):
        return ""
    linhas = [f"- {s['titulo']}: " + "; ".join(e["frase"] for e in s["evidencias"][:4]) for s in dados["sugestoes"]]
    pedido = "Resuma em até 5 linhas, em português simples, o que mais vale corrigir:\n" + "\n".join(linhas)
    sistema = ("Voce ajuda a melhorar um assistente de voz. Recebe uma lista de problemas do dia (frases descartadas, "
               "que cairam na IA, repetidas). Responda so com o resumo, sem inventar nada.")
    try:
        mensagens = [{"role": "user", "content": pedido}]
        if cerebro.tipo == "ollama":
            resumo = cerebro._ollama(sistema, mensagens)
        else:
            resumo = cerebro._claude_api(sistema, mensagens)
    except Exception as erro:
        log.warning("A IA nao conseguiu resumir as sugestoes: %s", erro)
        return ""
    arquivo = Path(arquivo or ARQUIVO_SUGESTOES)
    atual = ler(arquivo)
    if atual.get("ts") == dados.get("ts"):   # nao escreve por cima de uma analise mais nova
        atual["resumo_ia"] = str(resumo or "").strip()
        _gravar(atual, arquivo)
    return str(resumo or "").strip()


# =====================================================================
#  Agendamento (1x por dia, dentro do Assessor)
# =====================================================================
def hora_config(texto) -> tuple[int, int]:
    """ "08:00", "8", "8h", "8h30", "08.30" -> (8, 0)/(8, 30). Invalido: a hora padrao."""
    m = re.fullmatch(r"\s*(\d{1,2})\s*(?:[:h.]\s*(\d{2})?)?\s*", str(texto or ""))
    if m and int(m.group(1)) < 24 and int(m.group(2) or 0) < 60:
        return int(m.group(1)), int(m.group(2) or 0)
    return 8, 0   # HORA_PADRAO


def hora_texto(texto) -> str:
    h, m = hora_config(texto)
    return f"{h:02d}:{m:02d}"


def proxima_execucao(hora, ultima: float | None, agora: datetime | None = None) -> datetime:
    """Quando a proxima analise deve rodar. <= agora = rodar ja (inclusive se o PC estava desligado na hora)."""
    agora = agora or datetime.now()
    h, m = hora_config(hora)
    hoje = agora.replace(hour=h, minute=m, second=0, microsecond=0)
    ultimo_horario = hoje if agora >= hoje else hoje - timedelta(days=1)
    if ultima is None or ultima < ultimo_horario.timestamp():
        return agora   # atrasada: roda agora
    return ultimo_horario + timedelta(days=1)


def configuracao(cfg: dict | None) -> tuple[bool, str]:
    s = (cfg or {}).get("sugestoes") or {}
    return bool(s.get("ligado", True)), hora_texto(s.get("hora", HORA_PADRAO))


class Agendador:
    """Thread do Assessor: confere uma vez por minuto se ja passou da hora e roda a analise."""

    def __init__(self, cfg: dict, cerebro=None, rodando=lambda: True):
        self.cfg, self.cerebro, self.rodando = cfg, cerebro, rodando
        self.ligado, self.hora = configuracao(cfg)

    def iniciar(self) -> None:
        if self.ligado:
            threading.Thread(target=self._laco, daemon=True, name="sugestoes").start()

    def passo(self, agora: datetime | None = None) -> bool:
        """Roda a analise se ja esta na hora. True = rodou."""
        agora = agora or datetime.now()
        if proxima_execucao(self.hora, ultima_analise(), agora) > agora:
            return False
        dados = rodar(self.cfg, agora=agora.timestamp(), automatica=True)
        if self.cerebro is not None and getattr(self.cerebro, "ligado", False):
            threading.Thread(target=resumir_com_ia, args=(self.cerebro, dados), daemon=True).start()
        return True

    def _laco(self) -> None:
        time.sleep(ATRASO_INICIAL)
        while self.rodando():
            try:
                self.passo()
            except Exception:
                log.exception("Sugestões de melhoria: a análise falhou (tento de novo mais tarde)")
            time.sleep(INTERVALO)


def iniciar_agendador(cfg: dict, cerebro=None, rodando=lambda: True) -> Agendador:
    agendador = Agendador(cfg, cerebro, rodando)
    agendador.iniciar()
    return agendador


# =====================================================================
#  Pedido para o Claude (as marcadas no painel)
# =====================================================================
def pedido_para_claude(sugestoes: list[dict], gerado_em: str = "", nome: str = "assistente") -> str:
    """O pedido em portugues com as sugestoes marcadas e as evidencias (frases, horarios, motivos)."""
    L = [f"Sugestões de melhoria do {nome}{(' (análise de ' + gerado_em + ')') if gerado_em else ''}. "
         "Siga o CLAUDE.md: corrigir-transcricao/refinar não são necessários (a lista veio do próprio app). "
         "Para cada sugestão descubra a camada certa (transcrição, vocabulário, regex de comando, resposta ou "
         "ajuste de captação), corrija, acrescente as frases em testes/frases.py quando couber, rode o teste "
         "automático e rode /entregar. Se alguma não valer a pena, explique por quê.", ""]
    for n, s in enumerate(sugestoes, 1):
        L += [f"## {n}. {s.get('titulo')}", "", str(s.get("detalhe") or ""), "", "Evidências:"]
        for e in s.get("evidencias") or []:
            L.append(f"- {e.get('data')} · “{e.get('frase')}” · {e.get('info')}")
        L.append("")
    return "\n".join(L).strip() + "\n"
