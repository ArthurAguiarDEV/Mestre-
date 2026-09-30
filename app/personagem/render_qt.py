"""Desenhista do personagem com Qt (QPainter). Só é importado no processo do avatar e nas ferramentas de prévia.

Recebe a CENA (cena.py) e a POSE (dicionário "no.canal" -> número, veja animacao.py) e pinta. Nada aqui decide o que o
personagem faz: só percorre a árvore de nós, aplica posição/giro/escala e desenha as primitivas.
"""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient

ALTURA_BASE = 224.0   # altura do personagem em unidades (pés em y=0, topo do cabelo ~ -208; espetado chega a -224)


def _qcor(hexa: str, alfa: float = 1.0) -> QColor:
    c = QColor(hexa)
    c.setAlphaF(max(0.0, min(1.0, alfa)))
    return c


def _caminho(d: str) -> tuple[QPainterPath, list]:
    """Caminho SVG (só M L Q C Z absolutos) -> QPainterPath e a caixa dos pontos (para gradientes)."""
    toks = d.split()
    path, pts, i = QPainterPath(), [], 0
    while i < len(toks):
        c = toks[i]
        i += 1
        if c == "Z":
            path.closeSubpath()
            continue
        qtd = {"M": 2, "L": 2, "Q": 4, "C": 6}[c]
        v = [float(x) for x in toks[i:i + qtd]]
        i += qtd
        pts += list(zip(v[0::2], v[1::2]))
        pt = [QPointF(v[j], v[j + 1]) for j in range(0, qtd, 2)]
        if c == "M":
            path.moveTo(pt[0])
        elif c == "L":
            path.lineTo(pt[0])
        elif c == "Q":
            path.quadTo(pt[0], pt[1])
        else:
            path.cubicTo(pt[0], pt[1], pt[2])
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return path, [min(xs), min(ys), max(xs), max(ys)]


def _brush(f, caixa) -> QBrush:
    if not f:
        return QBrush(Qt.NoBrush)
    if isinstance(f, str):
        return QBrush(_qcor(f))
    tipo, cores = f[0], f[1:]
    x0, y0, x1, y1 = caixa
    if tipo == "v":
        g = QLinearGradient(0, y0, 0, y1)
    elif tipo == "h":
        g = QLinearGradient(x0, 0, x1, 0)
    else:
        g = QRadialGradient(QPointF((x0 + x1) / 2, (y0 + y1) / 2), max(x1 - x0, y1 - y0) / 2)
    n = len(cores)
    for i, cor in enumerate(cores):
        g.setColorAt(i / (n - 1) if n > 1 else 0, _qcor(cor))
    return QBrush(g)


class _Prim:
    __slots__ = ("path", "brush", "pen", "o", "v", "liga", "desl", "c")

    def __init__(self, p: dict):
        t = p["t"]
        if t == "el":
            path = QPainterPath()
            path.addEllipse(QPointF(p["x"], p["y"]), p["rx"], p["ry"])
            caixa = [p["x"] - p["rx"], p["y"] - p["ry"], p["x"] + p["rx"], p["y"] + p["ry"]]
        elif t == "rr":
            path = QPainterPath()
            path.addRoundedRect(QRectF(p["x"], p["y"], p["w"], p["h"]), p["r"], p["r"])
            caixa = [p["x"], p["y"], p["x"] + p["w"], p["y"] + p["h"]]
        else:
            path, caixa = _caminho(p["d"])
        self.path = path
        self.brush = _brush(p.get("f"), caixa)
        if p.get("s") and p.get("lw"):
            self.pen = QPen(_qcor(p["s"]), p["lw"], Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        else:
            self.pen = QPen(Qt.NoPen)
        self.o = float(p.get("o", 1))
        self.v, self.liga, self.desl = p.get("v"), p.get("liga"), p.get("desl")
        self.c = bool(p.get("c"))


class _No:
    __slots__ = ("id", "pos", "z", "seg", "mir", "inv", "contorno", "prims", "antes", "depois")

    def __init__(self, n: dict):
        self.id, self.pos = n["id"], n["pos"]
        self.z, self.seg, self.mir = n.get("z", 0), n.get("seg"), bool(n.get("mir"))
        self.inv, self.contorno = bool(n.get("inv")), bool(n.get("contorno"))
        self.prims = [_Prim(p) for p in n["prims"]]
        filhos = [_No(f) for f in n["filhos"]]
        self.antes = [f for f in filhos if f.z < 0]
        self.depois = [f for f in filhos if f.z >= 0]


class Desenhista:
    """Compila a cena uma vez (caminhos e pincéis do Qt) e pinta quadro a quadro com a pose."""

    def __init__(self, cena: dict):
        self.cena = cena
        self.raiz = _No(cena["raiz"])
        self.sombra = [_Prim(p) for p in cena["sombra"]]

    # -- a pose: "no.canal" -> valor; o que não vier é o padrão (0, ou 1 nas escalas) ----------------------
    def desenhar(self, p: QPainter, pose: dict) -> None:
        """Pinta o personagem com os pés em (0, 0) do painter (o chamador põe/escala onde quiser)."""
        base = p.opacity()
        for pr in self.sombra:
            self._prim(p, pr, pose, base * pose.get("sombra.o", 1.0))
        self._no(p, self.raiz, pose, base)

    def _no(self, p: QPainter, no: _No, pose: dict, base: float, fase: int = 0) -> None:
        """fase 0 = tudo; num nó com `contorno` (o braço) desenha antes só os contornos (prims `c`) do galho inteiro
        (fase 1) e depois o resto (fase 2): os recheios cobrem as linhas de dentro e o cotovelo fica sem emenda."""
        if fase == 0 and no.contorno:
            self._no(p, no, pose, base, 1)
            self._no(p, no, pose, base, 2)
            return
        g = pose.get
        x, y, r = g(no.id + ".x", 0.0), g(no.id + ".y", 0.0), g(no.id + ".r", 0.0)
        sx, sy = g(no.id + ".sx", 1.0), g(no.id + ".sy", 1.0)
        if no.seg:
            x += g(no.seg + ".x", 0.0)
            y += g(no.seg + ".y", 0.0)
            r += g(no.seg + ".r", 0.0)
            sx *= g(no.seg + ".sx", 1.0)
            sy *= g(no.seg + ".sy", 1.0)
        p.save()
        p.translate(no.pos[0] + x, no.pos[1] + y)
        if r:
            p.rotate(-r if no.inv else r)
        p.scale(-sx if no.mir else sx, sy)
        for f in no.antes:
            self._no(p, f, pose, base, fase)
        for pr in no.prims:
            if not fase or (fase == 1) == pr.c:
                self._prim(p, pr, pose, base)
        for f in no.depois:
            self._no(p, f, pose, base, fase)
        p.restore()

    @staticmethod
    def _prim(p: QPainter, pr: _Prim, pose: dict, base: float) -> None:
        if pr.v is not None and pose.get("boca.v", "fechada") != pr.v:
            return
        o = pr.o * base
        if pr.liga:
            o *= max(0.0, min(1.0, pose.get(pr.liga, 0.0)))
        if pr.desl:
            o *= 1.0 - max(0.0, min(1.0, pose.get(pr.desl, 0.0)))
        if o <= 0.004:
            return
        p.setOpacity(o)
        p.setPen(pr.pen)
        p.setBrush(pr.brush)
        p.drawPath(pr.path)
        p.setOpacity(base)
