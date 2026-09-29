"""Validar atualizacao: o usuario fala as frases do ROTEIRO_VALIDACAO.md e o painel confere.

Fluxo (painel > Validar atualização):
  1. ler_roteiro() transforma as tabelas "Novidades" e "Sempre testar" em itens
     (frase | o que deve acontecer | comando esperado).
  2. O painel mostra uma frase; o usuario FALA normalmente ao assistente (outro processo).
  3. capturar(desde) pega o que o assistente registrou DEPOIS da frase aparecer:
     memoria/ouvido.jsonl (OUVI, o texto do Whisper, e o audio se a validacao estiver ligada) e
     memoria/historico.jsonl (ENTENDI = texto depois do vocabulario + rota/comando; FIZ = o que falou).
  4. conferir() sugere ok/falha comparando com o comando esperado; o usuario confirma.
  5. No fim: gerar_relatorio() (exportacoes/validacao_AAAA-MM-DD_HHMM.md) e salvar_feedbacks()
     (cada falha vira "- [ ] FEEDBACK: ..." no MELHORIAS.md).

ultimo_relatorio() devolve o relatorio mais novo. O botão "Mandar para o Claude corrigir" usa
pedido_de_correcao() + salvar_pedido_correcao() + comando_para_abrir_claude() (app/sistema.py abre o
terminal de verdade, com o mesmo comando).
"""
import re
import shutil
import time
import hashlib
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path

from .config import PASTA_LOGS, PASTA_PROJETO
from .texto import normalizar

ARQUIVO_ROTEIRO = PASTA_PROJETO / "ROTEIRO_VALIDACAO.md"
PASTA_EXPORTACOES = PASTA_PROJETO / "exportacoes"
ARQUIVO_MELHORIAS = PASTA_PROJETO / "MELHORIAS.md"
# Enquanto este arquivo existir (e for recente), o ouvido guarda o audio de cada frase em PASTA_AUDIOS
ARQUIVO_ATIVA = PASTA_LOGS / "validacao_ativa"
PASTA_AUDIOS = PASTA_LOGS / "validacao"
VALIDADE_ATIVA = 3 * 3600      # painel fechou sem avisar: depois de 3 h para de guardar audio
MAXIMO_AUDIOS = 120
ESCOLHAS = {"Só novidades": ("novidades",), "Só sempre testar": ("sempre",), "Tudo": ("novidades", "sempre", "outros")}
NOMES_SECAO = {"novidades": "Novidades", "sempre": "Sempre testar", "outros": "Outros"}
# Rotas que tambem contam como o comando esperado (o comando continua a conversa por uma pergunta)
EQUIVALENTES = {
    "_cmd_ensinar_rotina": ("rotina falada", "resposta: nomear_rotina"),
    "_cmd_pensamento": ("resposta: responder_aviso_pensamento",),
}
TIPOS_ITEM = frozenset({"fala", "sequencia", "acao_manual", "observacao", "pre_condicao", "espera", "teste_automatico"})


@dataclass(frozen=True)
class Etapa:
    id: str
    tipo: str
    texto: str
    independente: bool = True


# =====================================================================
#  Roteiro
# =====================================================================
@dataclass
class Item:
    secao: str                  # "novidades" | "sempre" | "outros"
    grupo: str                  # o "###" de cima (ou o nome da secao)
    frase: str                  # 1a coluna como esta no roteiro (sem as crases)
    falas: list[str]            # o que falar (os trechos entre crases), na ordem
    o_que: str                  # 2a coluna
    esperado: str               # 3a coluna, como esta no roteiro
    comandos: list[str] = field(default_factory=list)   # _cmd_* esperados
    tipo: str = ""              # comando | ia | ignorado | acordar | qualquer | chamou | manual | ""
    manual: bool = False        # (painel)/(visual)/(automático): nao ha frase para falar
    id: str = ""
    tipo_item: str = "fala"
    etapas: list[Etapa] = field(default_factory=list)
    origem_id: str = ""

    @property
    def exige_microfone(self) -> bool:
        return self.tipo_item in ("fala", "sequencia") and not self.manual

    def para_falar(self, palavra: str = "") -> str:
        """As frases com "Mestre" trocado pela palavra de ativacao escolhida (convencao do roteiro)."""
        if not self.exige_microfone:
            return ""
        texto = " → ".join(self.falas or [self.frase])
        return re.sub(r"\bMestre\b", palavra, texto) if palavra else texto


def _id_estavel(secao: str, grupo: str, primeira: str, explicito: str = "") -> str:
    """O ID implícito não depende da posição; um ID explícito sobrevive a mudanças no texto."""
    if explicito:
        return explicito
    chave = "\x1f".join((secao, normalizar(grupo), normalizar(primeira)))
    return "val-" + hashlib.sha256(chave.encode("utf-8")).hexdigest()[:16]


def _tipo_item(primeira: str, falas: list[str], manual: bool) -> str:
    n = normalizar(primeira).lstrip("( ")
    if primeira.lstrip().startswith("(automático)") or "testes.teste_basico" in primeira:
        return "teste_automatico"
    if re.match(r"^(espere|aguarde|fique .*calado|deixe .* tocar)", n):
        return "espera"
    if re.match(r"^(se |com .* ligado|durante uma resposta)", n):
        return "pre_condicao"
    if re.match(r"^(confira|olhe|observe|verifique)", n) or re.match(
        r"^visual\s+(confira|olhe|observe|verifique)", n
    ):
        return "observacao"
    if manual or re.match(r"^(painel|botao|clique|abra o painel|rode |desligue |religue |feche |toque |arraste )", n):
        return "acao_manual"
    if len(falas) > 1:
        return "sequencia"
    if falas or re.match(r"^(mestre|assessor)\b", n):
        return "fala"
    return "acao_manual"  # legado ambíguo: nunca enviar uma instrução ao microfone


def _celulas(linha: str) -> list[str]:
    """Divide uma linha de tabela markdown pelos "|" (respeita crases e "\\|")."""
    linha = linha.strip()
    if linha.startswith("|"):
        linha = linha[1:]
    if linha.endswith("|") and not linha.endswith("\\|"):
        linha = linha[:-1]
    celulas, atual, crase, i = [], [], False, 0
    while i < len(linha):
        c = linha[i]
        if c == "\\" and i + 1 < len(linha) and linha[i + 1] == "|":
            atual.append("|")
            i += 2
            continue
        if c == "`":
            crase = not crase
        if c == "|" and not crase:
            celulas.append("".join(atual).strip())
            atual = []
        else:
            atual.append(c)
        i += 1
    celulas.append("".join(atual).strip())
    return celulas


def _separador(linha: str) -> bool:
    return bool(re.fullmatch(r"\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?", linha.strip()))


def _secao_do_titulo(titulo: str) -> str:
    n = normalizar(titulo)
    if "novidade" in n:
        return "novidades"
    if "sempre" in n or "regress" in n:
        return "sempre"
    return "outros"


def _tipo_esperado(esperado: str, comandos: list[str], manual: bool) -> str:
    if comandos:
        return "comando"
    n = normalizar(esperado.replace("`", ""))
    if manual or re.search(r"\b(painel|automatico|teste|visual|bandeja)\b", n):
        return "manual"
    if "so chamou" in n:
        return "chamou"
    if "ignorad" in n:
        return "ignorado"
    if "acorda" in n:
        return "acordar"
    if re.search(r"\b(ia|pensar|pensando)\b", n):
        return "ia"
    if "comando falado" in n or "qualquer comando" in n:
        return "qualquer"
    return ""


def ler_roteiro(caminho: Path | None = None, texto: str | None = None) -> list[Item]:
    """Todos os itens das tabelas do roteiro, na ordem. Linhas quebradas ou fora de tabela sao ignoradas."""
    if texto is None:
        caminho = caminho or ARQUIVO_ROTEIRO
        try:
            texto = Path(caminho).read_text(encoding="utf-8-sig")
        except OSError:
            return []
    itens: list[Item] = []
    ids: set[str] = set()
    secao, grupo, em_tabela = "outros", "", False
    linhas = texto.splitlines()
    for n, linha in enumerate(linhas):
        s = linha.strip()
        titulo = re.match(r"^(#{2,6})\s+(.*)$", s)
        if titulo:
            em_tabela = False
            nivel, nome = len(titulo.group(1)), titulo.group(2).strip()
            if nivel == 2:
                secao = _secao_do_titulo(nome)
                grupo = NOMES_SECAO[secao]
            else:
                grupo = nome
            continue
        if not s.startswith("|"):
            em_tabela = False
            continue
        if _separador(s):
            em_tabela = True
            continue
        proxima = linhas[n + 1].strip() if n + 1 < len(linhas) else ""
        if not em_tabela and _separador(proxima):
            continue   # cabecalho da tabela
        if not em_tabela:
            continue
        cel = _celulas(s)
        if not cel or not cel[0]:
            continue
        while len(cel) < 3:
            cel.append("")
        primeira, o_que, esperado = cel[0], cel[1], " | ".join(c for c in cel[2:] if c)
        marcador = re.search(r"<!--\s*validacao\s+id=([a-zA-Z0-9_-]+)(?:\s+tipo=([a-z_]+))?\s*-->", primeira)
        explicito, tipo_explicito = (marcador.group(1), marcador.group(2)) if marcador else ("", "")
        if marcador:
            primeira = (primeira[:marcador.start()] + primeira[marcador.end():]).strip()
        falas = [x.strip() for x in re.findall(r"`([^`]+)`", primeira) if x.strip()]
        manual = primeira.lstrip().startswith("(")   # (painel) (visual) (automático)
        comandos = list(dict.fromkeys(re.findall(r"_cmd_[a-z0-9_]*[a-z0-9]", esperado)))
        tipo_item = tipo_explicito or _tipo_item(primeira, falas, manual)
        if tipo_item not in TIPOS_ITEM:
            raise ValueError(f"Tipo de validação desconhecido: {tipo_item}")
        item_id = _id_estavel(secao, grupo or NOMES_SECAO[secao], primeira, explicito)
        if item_id in ids:
            if explicito:
                raise ValueError(f"ID de validação repetido: {item_id}")
            sufixo = 2
            while f"{item_id}-{sufixo}" in ids:
                sufixo += 1
            item_id = f"{item_id}-{sufixo}"
        ids.add(item_id)
        etapas = []
        if tipo_item == "sequencia":
            # Pausas dentro de uma única frase continuam sendo uma única tentativa.
            continuacao = bool(re.search(r"pausa|…|\.\.\.", primeira, re.IGNORECASE))
            etapas = [Etapa(f"{item_id}-{n + 1}", "fala", fala, not continuacao)
                      for n, fala in enumerate(falas)]
        itens.append(Item(secao=secao, grupo=grupo or NOMES_SECAO[secao], frase=primeira.replace("`", ""),
                          falas=falas, o_que=o_que.replace("`", ""), esperado=esperado.replace("`", ""),
                          comandos=comandos, tipo=_tipo_esperado(esperado, comandos, manual), manual=manual,
                          id=item_id, tipo_item=tipo_item, etapas=etapas))
    return itens


def escolher(itens: list[Item], escolha: str) -> list[Item]:
    secoes = ESCOLHAS.get(escolha, ESCOLHAS["Tudo"])
    return [i for i in itens if i.secao in secoes]


# =====================================================================
#  O que o assistente registrou
# =====================================================================
def _ts(registro: dict) -> float:
    """Hora do registro (segundos). Registros antigos (sem "ts") usam a "data" (so ate o minuto)."""
    try:
        if registro.get("ts") is not None:
            return float(registro["ts"])
    except (TypeError, ValueError):
        pass
    texto = str(registro.get("data") or "")
    for formato in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            momento = datetime.strptime(texto, formato)
            return momento.timestamp() + (59 if formato.endswith("%M") else 0)
        except ValueError:
            continue
    return 0.0


# tipos do historico que sao o pedido principal (Telegram, IA guardada... nao contam)
TIPOS_PEDIDO = ("comando", "voz_nao_reconhecida")


def capturar(desde: float, historico: list[dict] | None = None, ouvidas: list[dict] | None = None) -> dict | None:
    """O que aconteceu depois de `desde` (a frase apareceu na tela). None = nada ainda.

    Devolve {"ouvi", "entendi", "rota", "fiz", "audio", "ts"}.
    """
    if historico is None or ouvidas is None:
        from . import memoria
        historico = memoria.historico(80) if historico is None else historico
        ouvidas = memoria.ouvidas(80) if ouvidas is None else ouvidas
    novos = [h for h in historico if _ts(h) >= desde]
    pedidos = [h for h in novos if h.get("tipo") in TIPOS_PEDIDO and h.get("rota") != "_cmd_feedback"]
    ouvidos = [o for o in ouvidas if _ts(o) >= desde and (o.get("chamou") or o.get("conversa")
                                                           or o.get("voz_nao_reconhecida") is not None)]
    if not pedidos and not ouvidos:
        return None
    pedido = pedidos[-1] if pedidos else None
    if pedido:   # a frase ouvida que gerou o pedido: a ultima ate ele
        antes = [o for o in ouvidos if _ts(o) <= _ts(pedido) + 1]
        ouvido = antes[-1] if antes else (ouvidos[-1] if ouvidos else None)
    else:
        ouvido = ouvidos[-1]
    rota = str(pedido.get("rota") or pedido.get("tipo") or "") if pedido else ""
    entendi = str(pedido.get("entendi") or "") if pedido else ""
    if pedido and pedido.get("tipo") == "voz_nao_reconhecida":
        rota = "ignorado (voz não reconhecida)"
    if pedido:   # a IA transformou em comando depois (em segundo plano)?
        virou = [h for h in novos if h.get("tipo") == "ia virou comando" and _ts(h) >= _ts(pedido)]
        if virou:
            v = virou[-1]
            rota = str(v.get("rota") or rota)
            entendi = f"{entendi} → IA: {v.get('ia_texto') or v.get('entendi') or ''}".strip()
    if pedido:
        fiz = str(pedido.get("resposta") or "").strip() or "(não falou nada)"
    else:
        fiz = "(nada registrado: ignorado ou ainda trabalhando)"
    return {"ouvi": str((ouvido or {}).get("texto") or (pedido or {}).get("pedido") or ""),
            "entendi": entendi, "rota": rota, "fiz": fiz, "pedidos": len(pedidos),
            "audio": str((ouvido or {}).get("audio") or ""),
            "ts": max(_ts(pedido) if pedido else 0.0, _ts(ouvido) if ouvido else 0.0)}


def ultimos_comandos(quantos: int = 5, historico: list[dict] | None = None,
                     ouvidas: list[dict] | None = None) -> list[dict]:
    """Os ultimos pedidos com OUVI/ENTENDI/FIZ (painel > Inicio), mais recente primeiro.

    Mesmo casamento da validacao: a frase ouvida e a ultima transcricao ate o pedido.
    Devolve [{"hora", "ouvi", "entendi", "fiz", "ts"}].
    """
    if historico is None or ouvidas is None:
        from . import memoria
        historico = memoria.historico(120) if historico is None else historico
        ouvidas = memoria.ouvidas(200) if ouvidas is None else ouvidas
    pedidos = [h for h in historico if (h.get("tipo") in TIPOS_PEDIDO or "comando" in str(h.get("tipo") or ""))
               and h.get("tipo") != "ia virou comando"]
    ouvidos = [o for o in ouvidas if o.get("chamou") or o.get("conversa") or o.get("junto_da_palavra")]
    saida = []
    for i in range(len(pedidos) - 1, max(-1, len(pedidos) - 1 - quantos), -1):
        pedido = pedidos[i]
        quando = _ts(pedido)
        antes = _ts(pedidos[i - 1]) if i > 0 else 0.0
        candidatos = [o for o in ouvidos if antes < _ts(o) <= quando + 1]
        ouvi = str(candidatos[-1].get("texto") or "") if candidatos else ""
        entendi = str(pedido.get("entendi") or "")
        rota = str(pedido.get("rota") or "")
        if rota and rota not in entendi:
            entendi = f"{entendi}  ({rota})" if entendi else rota
        saida.append({"hora": time.strftime("%H:%M", time.localtime(quando)) if quando else "",
                      "ouvi": ouvi or str(pedido.get("pedido") or ""), "entendi": entendi or "—",
                      "fiz": str(pedido.get("resposta") or "").strip() or "(não falou nada)", "ts": quando})
    return saida


def fala_nova(desde: float, ouvidas: list[dict] | None = None) -> str:
    """A ultima frase transcrita depois de `desde` (para o "o certo era..." falado)."""
    if ouvidas is None:
        from . import memoria
        ouvidas = memoria.ouvidas(40)
    novas = [o for o in ouvidas if _ts(o) >= desde and str(o.get("texto") or "").strip()]
    return str(novas[-1]["texto"]).strip() if novas else ""


def conferir(item: Item, captura: dict | None) -> str | None:
    """"ok", "falha" ou None (nada para comparar: o usuario decide)."""
    if not item.exige_microfone:
        return None
    rota = str((captura or {}).get("rota") or "")
    if item.tipo == "ignorado":
        return "ok" if (not captura or not rota or rota.startswith("ignorado")) else "falha"
    if not captura:
        return None
    if not rota:   # ouviu, mas o historico ainda nao tem o pedido (trabalhando)
        return None
    if item.tipo == "comando":
        for esperado in item.comandos:
            if esperado in rota or rota.startswith(EQUIVALENTES.get(esperado, ("\0",))):
                return "ok"
        return "falha"
    if item.tipo == "ia":
        return "ok" if rota == "ia" else "falha"
    if item.tipo == "acordar":
        return "ok" if rota == "saiu do descanso" else "falha"
    if item.tipo == "qualquer":
        return "ok" if "_cmd_" in rota else "falha"
    if item.tipo == "chamou":
        return "ok" if rota == "so chamou" else "falha"
    return None


def explicar(item: Item, captura: dict | None, sugestao: str | None) -> str:
    """Frase curta para a tela: por que sugeriu ok/falha."""
    rota = str((captura or {}).get("rota") or "") or "nada"
    esperado = ", ".join(item.comandos) or item.esperado or "?"
    if sugestao == "ok":
        return f"Bateu: esperado {esperado}, atendeu {rota}."
    if sugestao == "falha":
        return f"Não bateu: esperado {esperado}, atendeu {rota}."
    if not item.exige_microfone:
        return "Confira você mesmo e marque."
    if not captura:
        return "Esperando você falar..."
    return "Não dá para conferir sozinho: confira e marque."


# =====================================================================
#  Sessao (usada pelo painel e pelo teste)
# =====================================================================
def _proveniencia() -> tuple[str, str, str]:
    """Congela a origem da validação no início, antes de o roteiro ou o app mudarem."""
    from .versao import VERSAO

    try:
        hash_roteiro = hashlib.sha256(ARQUIVO_ROTEIRO.read_bytes()).hexdigest()
    except OSError:
        hash_roteiro = "indisponível"
    commit = "indisponível"
    try:
        git = PASTA_PROJETO / ".git"
        if git.is_file():
            git = (PASTA_PROJETO / git.read_text(encoding="utf-8").strip().removeprefix("gitdir:").strip()).resolve()
        comum = git
        if (git / "commondir").exists():
            comum = (git / (git / "commondir").read_text(encoding="utf-8").strip()).resolve()
        cabeca = (git / "HEAD").read_text(encoding="utf-8").strip()
        if cabeca.startswith("ref: "):
            referencia = cabeca.removeprefix("ref: ")
            arquivo_ref = comum / referencia
            if arquivo_ref.exists():
                commit = arquivo_ref.read_text(encoding="utf-8").strip()
            else:
                for linha in (comum / "packed-refs").read_text(encoding="utf-8").splitlines():
                    if linha.endswith(" " + referencia):
                        commit = linha.split(" ", 1)[0]
                        break
        else:
            commit = cabeca
    except OSError:
        pass
    return commit, hash_roteiro, str(VERSAO)


class Sessao:
    def __init__(self, itens: list[Item], escolha: str = "Tudo", excluidos: list[Item] | None = None):
        self.excluidos = list(excluidos or [])
        self.itens_carregados = len(itens) + len(self.excluidos)
        self.itens = []
        for item in itens:
            if item.tipo_item == "sequencia" and item.etapas and all(e.independente for e in item.etapas):
                for pos, etapa in enumerate(item.etapas):
                    comandos = ([item.comandos[pos]] if len(item.comandos) == len(item.etapas)
                                else item.comandos[:1] if len(item.comandos) == 1 else [])
                    # No legado, o esperado pode descrever apenas a última fala.
                    tipo = "comando" if comandos else (item.tipo if pos == len(item.etapas) - 1 else "")
                    self.itens.append(replace(item, id=etapa.id, origem_id=item.id, frase=etapa.texto,
                                              falas=[etapa.texto], tipo_item="fala", etapas=[],
                                              comandos=comandos, tipo=tipo))
            else:
                self.itens.append(item)
        self.escolha = escolha
        self.indice = 0
        self.inicio = datetime.now()
        self.resultados: dict[int, dict] = {}   # indice -> resultado da etapa/item
        self.exibida_em = time.time()
        self.commit, self.hash_roteiro, self.versao = _proveniencia()
        self.interrompida = False

    @property
    def atual(self) -> Item | None:
        return self.itens[self.indice] if 0 <= self.indice < len(self.itens) else None

    @property
    def acabou(self) -> bool:
        return self.indice >= len(self.itens)

    def mostrar(self, indice: int | None = None) -> None:
        if indice is not None:
            self.indice = max(0, min(indice, len(self.itens)))
        self.exibida_em = time.time()

    def marcar(self, veredito: str, captura: dict | None = None, sugestao: str | None = None,
               certo_era: str = "") -> None:
        """veredito: ok | falha | pulado | bloqueado. Vai para o próximo item."""
        if self.atual is None:
            return
        if veredito not in ("ok", "falha", "pulado", "bloqueado"):
            raise ValueError(f"Veredito desconhecido: {veredito}")
        self.resultados[self.indice] = {"veredito": veredito, "captura": captura or {}, "sugestao": sugestao,
                                        "certo_era": certo_era.strip()}
        self.mostrar(self.indice + 1)

    def lista(self) -> list[tuple[Item, dict]]:
        return [(self.itens[i], r) for i, r in sorted(self.resultados.items())]

    def lista_completa(self) -> list[tuple[Item, dict]]:
        lista = [(item, self.resultados.get(i, {"veredito": "nao_executado", "captura": {}}))
                 for i, item in enumerate(self.itens)]
        lista.extend((item, {"veredito": "nao_executado", "captura": {}, "motivo": "fora do modo contínuo"})
                     for item in self.excluidos)
        return lista


# =====================================================================
#  Modo continuo: avanca sozinho no ✅, so para no ❌
# =====================================================================
AVANCO_SEGUNDOS = 1.5     # depois do ✅, espera isso e passa para a proxima frase
SILENCIO_SEGUNDOS = 15    # nada ouvido nesse tempo: "não ouvi nada — fale de novo ou Pular"
ESPERA_IA = 15            # caiu na IA: espera a IA virar o comando certo antes de dar ❌
ESPERA_DESCARTE = 4       # frase descartada parecida com a esperada: espera isso (pode vir a certa) e da ❌
ESPERA_IGNORADO = 3       # frase que deve ser ignorada: ouviu e nada aconteceu nesse tempo = ✅


def manual(item: Item) -> bool:
    """Linha sem frase para falar ((painel)/(visual)/(automático)): fica fora do modo continuo por padrao."""
    return not item.exige_microfone


def para_continuo(itens: list[Item], incluir_manuais: bool = False) -> list[Item]:
    return [i for i in itens if incluir_manuais or not manual(i)]


def _parecida(texto: str, item: Item) -> bool:
    """A frase ouvida parece com o que era para falar? (so assim um descarte conta como a tentativa)"""
    from difflib import SequenceMatcher

    ouvido = set(normalizar(texto).split())
    if not ouvido:
        return False
    for fala in item.falas or [item.frase]:
        esperado = normalizar(re.sub(r"\bMestre\b", "", fala))
        palavras = set(esperado.split())
        if not palavras:
            continue
        comum = len(ouvido & palavras) / len(palavras)
        if comum >= 0.5 or SequenceMatcher(None, normalizar(texto), esperado).ratio() >= 0.6:
            return True
    return False


def descartes(desde: float, ouvidas: list[dict] | None = None) -> list[dict]:
    """Frases que o ouvido jogou fora depois de `desde`, com o motivo (curta demais, sem a palavra,
    voz não reconhecida...). "só a palavra: esperando o resto" e "terminou no meio" nao sao descarte (o resto
    ainda vem), nem "interrompeu a fala" (a ordem de parar foi atendida)."""
    if ouvidas is None:
        from . import memoria
        ouvidas = memoria.ouvidas(80)
    lista = []
    for o in ouvidas:
        motivo = str(o.get("motivo") or "")
        if _ts(o) >= desde and motivo and not motivo.startswith(("só a palavra", "terminou no meio", "interrompeu")):
            lista.append({"texto": str(o.get("texto") or ""), "motivo": motivo, "ts": _ts(o),
                          "data": str(o.get("data") or "")})
    return lista


def avaliar_continuo(item: Item, desde: float, agora: float | None = None, historico: list[dict] | None = None,
                     ouvidas: list[dict] | None = None) -> dict:
    """Decide sozinho o que fazer com a frase da tela no modo continuo.

    estado: "esperando" | "ok" (avanca) | "falha" (para e mostra OUVI → ENTENDI → FIZ + motivos) |
            "silencio" (nada ouvido em SILENCIO_SEGUNDOS) | "conferir" (nao da para decidir: o usuario marca)
    """
    agora = time.time() if agora is None else agora
    if manual(item):
        return {"estado": "conferir", "captura": None, "descartes": [], "sugestao": None}
    if historico is None or ouvidas is None:
        from . import memoria
        historico = memoria.historico(80) if historico is None else historico
        ouvidas = memoria.ouvidas(80) if ouvidas is None else ouvidas
    captura = capturar(desde, historico, ouvidas)
    fora = descartes(desde, ouvidas)
    parecidos = [d for d in fora if _parecida(d["texto"], item)]
    novas = [o for o in ouvidas if _ts(o) >= desde]
    r = {"estado": "esperando", "captura": captura, "descartes": parecidos or fora[-3:], "sugestao": None}
    if manual(item):
        r["estado"] = "conferir"
        return r
    sugestao = conferir(item, captura)
    rota = str((captura or {}).get("rota") or "")
    ultimo = max([_ts(o) for o in novas] + [float((captura or {}).get("ts") or 0)] + [desde])
    if item.tipo == "ignorado":
        if rota and not rota.startswith("ignorado"):
            r.update(estado="falha", sugestao="falha")
        elif novas and agora - ultimo >= ESPERA_IGNORADO:
            r.update(estado="ok", sugestao="ok")
        elif not novas and agora - desde >= SILENCIO_SEGUNDOS:
            r["estado"] = "silencio"
        return r
    if sugestao == "ok":
        falas = 1 if item.tipo_item == "sequencia" and item.etapas and not all(
            e.independente for e in item.etapas
        ) else max(1, len(item.falas))
        if int((captura or {}).get("pedidos") or 0) >= falas:
            r.update(estado="ok", sugestao="ok")
        return r   # varias falas ("A → B"): espera a ultima
    if sugestao == "falha":
        if rota == "ia" and item.tipo == "comando" and agora - float(captura.get("ts") or 0) < ESPERA_IA:
            return r   # a IA pode transformar no comando certo em segundo plano
        r.update(estado="falha", sugestao="falha")
        return r
    if captura and rota:   # atendeu, mas o roteiro nao diz o comando: o usuario confere
        r["estado"] = "conferir"
        return r
    if parecidos and agora - parecidos[-1]["ts"] >= ESPERA_DESCARTE:
        r.update(estado="falha", sugestao="falha")   # falou a frase e ela foi jogada fora
        return r
    if not parecidos and agora - ultimo >= SILENCIO_SEGUNDOS:
        r["estado"] = "silencio"   # nada (ou so "Mestre" sozinho) ha 15 s
    return r


def texto_descartes(lista: list[dict]) -> str:
    """Linhas curtas para a tela: 'descartei "abre o yutubi" (curta demais)'."""
    return "\n".join(f"descartei “{d['texto'] or '(nada)'}” ({d['motivo']})" for d in lista)



# =====================================================================
#  Relatorio e FEEDBACK
# =====================================================================
def _limpar(texto) -> str:
    return " ".join(str(texto or "").split()).replace('"', "'")


def linha_feedback(item: Item, r: dict) -> str:
    """No formato do CLAUDE.md: FEEDBACK: ouvi "..." · entendi "..." · respondi "..." · o certo era: ..."""
    c = r.get("captura") or {}
    entendi = _limpar(c.get("entendi"))
    if c.get("rota"):
        entendi = f"{entendi} ({c.get('rota')})" if entendi else str(c.get("rota"))
    certo = _limpar(r.get("certo_era")) or _limpar(item.o_que)
    esperado = ", ".join(item.comandos) or _limpar(item.esperado)
    linha = (f"FEEDBACK: ouvi \"{_limpar(c.get('ouvi')) or _limpar(item.para_falar())}\" · entendi \"{entendi}\" · "
             f"respondi \"{_limpar(c.get('fiz'))}\" · o certo era: {certo} (validação: esperado {esperado})")
    if c.get("descartado"):
        linha += f" (ouvido: {_limpar(c['descartado'])})"
    if c.get("audio"):
        linha += f" [áudio: {c['audio']}]"
    return linha


def gerar_relatorio(sessao: Sessao, nome: str = "", agora: datetime | None = None,
                    pasta: Path | None = None) -> Path:
    agora = agora or datetime.now()
    pasta = Path(pasta or PASTA_EXPORTACOES)
    lista = sessao.lista_completa()
    oks = [(i, r) for i, r in lista if r["veredito"] == "ok"]
    falhas = [(i, r) for i, r in lista if r["veredito"] == "falha"]
    pulados = [(i, r) for i, r in lista if r["veredito"] == "pulado"]
    bloqueados = [(i, r) for i, r in lista if r["veredito"] == "bloqueado"]
    nao_executados = [(i, r) for i, r in lista if r["veredito"] == "nao_executado"]
    conferidos = len(oks) + len(falhas) + len(pulados) + len(bloqueados)
    L = [f"# Validação da atualização{(' do ' + nome) if nome else ''}\n",
         f"Feita em {agora:%d/%m/%Y %H:%M} · roteiro: **{sessao.escolha}** · "
         f"{conferidos} de {sessao.itens_carregados} itens conferidos"
         f"{' · relatório parcial (sessão interrompida)' if sessao.interrompida or nao_executados else ''}\n",
         f"- **Commit:** `{sessao.commit}`",
         f"- **SHA-256 do ROTEIRO_VALIDACAO.md:** `{sessao.hash_roteiro}`",
         f"- **Versão do aplicativo:** {sessao.versao}",
         f"- **Itens carregados:** {sessao.itens_carregados}",
         "## Resumo\n",
         f"- ✅ **{len(oks)} ok**",
         f"- ❌ **{len(falhas)} falhas**",
         f"- ⏭ {len(pulados)} pulados",
         f"- 🚫 {len(bloqueados)} bloqueados",
         f"- ◻ {len(nao_executados)} não executados", ""]
    pre_condicoes = [(i, r) for i, r in lista if i.tipo_item == "pre_condicao"]
    L += ["## Pré-condições\n"]
    L += [f"- `{i.id}` · {i.frase} · {r['veredito']}" for i, r in pre_condicoes] or ["(nenhuma)"]
    L.append("")
    for titulo, grupo in (("Itens bloqueados", bloqueados), ("Itens não executados", nao_executados)):
        L += [f"## {titulo}\n"]
        L += [f"- `{i.id}` · {i.frase}" + (f" · {r['motivo']}" if r.get("motivo") else "")
              for i, r in grupo] or ["(nenhum)"]
        L.append("")
    L += ["## Falhas\n"]
    if not falhas:
        L.append("(nenhuma)\n")
    for item, r in falhas:
        c = r.get("captura") or {}
        L += [f"### {item.para_falar() or item.frase}\n", f"- **ID:** `{item.id}`",
              f"- **Grupo:** {NOMES_SECAO.get(item.secao, item.secao)} › {item.grupo}",
              f"- **Ouvi:** {c.get('ouvi') or '(nada)'}",
              f"- **Entendi:** {c.get('entendi') or '(nada)'} → `{c.get('rota') or 'nenhum comando'}`",
              f"- **Fiz:** {c.get('fiz') or '(nada)'}",
              *([f"- **Descartado pelo ouvido:** {_limpar(c['descartado'])}"] if c.get("descartado") else []),
              f"- **Esperado:** {item.o_que} · `{', '.join(item.comandos) or item.esperado}`",
              f"- **O certo era:** {r.get('certo_era') or '(não disse)'}"]
        if c.get("audio"):
            L.append(f"- **Áudio:** `{c['audio']}`")
        L.append("")
    L += ["## Todos os itens\n", "| Resultado | ID | Tipo | Item | Entendi → comando | Esperado |",
          "|---|---|---|---|---|---|"]
    marca = {"ok": "✅", "falha": "❌", "pulado": "⏭", "bloqueado": "🚫", "nao_executado": "◻"}
    for item, r in lista:
        c = r.get("captura") or {}
        cel = lambda t: _limpar(t).replace("|", "/")[:140]   # noqa: E731
        L.append(f"| {marca.get(r['veredito'], '?')} | {item.id} | {item.tipo_item} | "
                 f"{cel(item.para_falar() or item.frase)} | "
                 f"{cel(c.get('entendi'))} → {cel(c.get('rota')) or '-'} | {cel(', '.join(item.comandos) or item.esperado)} |")
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / f"validacao_{agora:%Y-%m-%d_%H%M}.md"
    sufixo = 2
    while arquivo.exists():
        arquivo = pasta / f"validacao_{agora:%Y-%m-%d_%H%M}_{sufixo}.md"
        sufixo += 1
    arquivo.write_text("\n".join(L) + "\n", encoding="utf-8")
    return arquivo


def salvar_feedbacks(sessao: Sessao, arquivo: Path | None = None, agora: datetime | None = None) -> list[str]:
    """Cada falha vira "- [ ] (data) FEEDBACK: ..." no fim do MELHORIAS.md. Devolve as linhas escritas."""
    arquivo = Path(arquivo or ARQUIVO_MELHORIAS)
    agora = agora or datetime.now()
    linhas = [f"- [ ] ({agora:%d/%m/%Y}) {linha_feedback(i, r)}" for i, r in sessao.lista()
              if r["veredito"] == "falha" and i.exige_microfone]
    if not linhas:
        return []
    atual = arquivo.read_text(encoding="utf-8") if arquivo.exists() else "# Melhorias\n\n"
    if atual and not atual.endswith("\n"):
        atual += "\n"
    arquivo.write_text(atual + "\n".join(linhas) + "\n", encoding="utf-8")
    return linhas


def ultimo_relatorio(pasta: Path | None = None) -> Path | None:
    """O relatorio de validacao mais novo (exportacoes/validacao_*.md), ou None."""
    pasta = Path(pasta or PASTA_EXPORTACOES)
    arquivos = sorted(pasta.glob("validacao_*.md")) if pasta.exists() else []
    return arquivos[-1] if arquivos else None


def relatorio_tem_falhas(relatorio: Path | None) -> bool:
    """True se `relatorio` existe e teve pelo menos 1 falha (olha o resumo "❌ **N falhas**")."""
    if not relatorio:
        return False
    try:
        texto = Path(relatorio).read_text(encoding="utf-8")
    except OSError:
        return False
    m = re.search(r"\*\*(\d+)\s+falhas\*\*", texto)
    return bool(m) and int(m.group(1)) > 0


# =====================================================================
#  "Mandar para o Claude corrigir" (botao na pagina, usa o ultimo relatorio)
# =====================================================================
def pedido_de_correcao(relatorio: Path) -> str:
    """O pedido curto em portugues, pronto para mandar ao Claude Code corrigir as falhas do relatorio."""
    try:
        caminho = Path(relatorio).relative_to(PASTA_PROJETO).as_posix()
    except ValueError:
        caminho = Path(relatorio).as_posix()
    return (f"Corrija as falhas do relatório de validação {caminho}. Siga o CLAUDE.md: "
            "corrigir-transcricao/refinar não são necessários (é relatório do app); para cada falha descubra "
            "a camada certa (transcrição, vocabulário, regex, resposta), corrija, rode o teste automático "
            "e rode /entregar.")


def salvar_pedido_correcao(pedido: str, agora: datetime | None = None, pasta: Path | None = None,
                           prefixo: str = "pedido_correcao") -> Path:
    """Salva o pedido em exportacoes/<prefixo>_AAAA-MM-DD_HHMM.md (as Sugestões usam "pedido_sugestoes")."""
    agora = agora or datetime.now()
    pasta = Path(pasta or PASTA_EXPORTACOES)
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / f"{prefixo}_{agora:%Y-%m-%d_%H%M}.md"
    arquivo.write_text(pedido.strip() + "\n", encoding="utf-8")
    return arquivo


def prompt_curto(arquivo: Path) -> str:
    """Frase curta para o terminal: so letras, espaco, ponto e barra (o Windows Terminal quebra o
    comando em ';' e o cmd se atrapalha com aspas). O pedido completo fica no arquivo."""
    try:
        caminho = Path(arquivo).relative_to(PASTA_PROJETO).as_posix()
    except ValueError:
        caminho = Path(arquivo).as_posix()
    return f"Leia o arquivo {caminho} e faca o que ele pede"


def localizar_claude() -> str | None:
    """O executavel do Claude Code: no PATH (claude/claude.exe) ou em ~/.local/bin/claude.exe. None = nao achou."""
    exe = shutil.which("claude") or shutil.which("claude.exe")
    if exe:
        return exe
    alvo = Path.home() / ".local" / "bin" / "claude.exe"
    return str(alvo) if alvo.exists() else None


def comando_para_abrir_claude(pedido: str) -> list[str] | None:
    """Os argumentos (para subprocess, sem shell) que abrem um terminal VISIVEL com o Claude Code
    INTERATIVO (sem -p/headless, sem flag de permissao) ja com `pedido` como prompt inicial.

    Windows Terminal (wt.exe) se estiver no PATH, senao cmd /k. None = nao achou o Claude Code (nem no
    PATH, nem em ~/.local/bin/claude.exe); quem chamar deve avisar o usuario e copiar o pedido.
    """
    claude = localizar_claude()
    if not claude:
        return None
    comando_claude = [claude, pedido]
    wt = shutil.which("wt.exe") or shutil.which("wt")
    if wt:
        return [wt, "-d", str(PASTA_PROJETO)] + comando_claude
    return ["cmd", "/k"] + comando_claude


# =====================================================================
#  Audio de cada frase (so enquanto a validacao esta aberta no painel)
# =====================================================================
def ligar_audio(sim: bool) -> None:
    try:
        if sim:
            PASTA_LOGS.mkdir(exist_ok=True)
            ARQUIVO_ATIVA.write_text("validacao aberta no painel", encoding="utf-8")
        else:
            ARQUIVO_ATIVA.unlink(missing_ok=True)
    except OSError:
        pass


def audio_ligado() -> bool:
    try:
        return time.time() - ARQUIVO_ATIVA.stat().st_mtime < VALIDADE_ATIVA
    except OSError:
        return False


def guardar_audio(audio: bytes) -> str:
    """Chamado pelo ouvido para cada frase. Devolve o caminho relativo (logs/validacao/x.wav) ou ""."""
    if not audio or not audio_ligado():
        return ""
    try:
        from .audio import salvar_wav

        PASTA_AUDIOS.mkdir(parents=True, exist_ok=True)
        arquivo = PASTA_AUDIOS / f"{datetime.now():%Y%m%d_%H%M%S_%f}.wav"
        salvar_wav(audio, arquivo)
        for antigo in sorted(PASTA_AUDIOS.glob("*.wav"))[:-MAXIMO_AUDIOS]:
            antigo.unlink(missing_ok=True)
        return arquivo.relative_to(PASTA_PROJETO).as_posix()
    except Exception:
        return ""
