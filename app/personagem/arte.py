"""Ferramentas para DESENHAR o personagem em forma de dados (primitivas), sem Qt e sem tela.

O desenho é dado, não código de pintura: cada peça é uma lista de primitivas (elipse, retângulo redondo,
caminho) com cores em "fichas" ($pele, $cabelo+, $c1-...). O mesmo catálogo é lido por dois desenhistas:
`render_qt.py` (app, QPainter) e `design/avatar-2026-09/personagem.js` (página de teste, Canvas).

Primitivas (dicionários curtos; o que for padrão fica de fora):
    el: x y rx ry           elipse
    rr: x y w h r           retângulo redondo
    pa: d                   caminho SVG SÓ com comandos absolutos M L Q C Z (números separados por espaço)
    comuns: f (preenchimento) s (contorno) lw (espessura) o (opacidade 0-1)
            v (só desenha se a boca estiver neste "visema"), liga/desl (opacidade presa a um canal da pose)
Preenchimento `f` = "#RRGGBB" | "$ficha" | ["v", cima, baixo] | ["h", esq, dir] | ["r", centro, borda]
"""
import re

_NUM = re.compile(r"[MLQCZ]|-?\d+(?:\.\d+)?")


def n(v: float):
    """Número enxuto: 2 casas, inteiro quando for redondo (o JSON fica pequeno e igual nos dois lados)."""
    v = round(float(v), 2)
    return int(v) if v == int(v) else v


def _prim(t: str, **campos) -> dict:
    p = {"t": t}
    for k, v in campos.items():
        if v is None or v == 0 and k in ("lw",) or v == 1 and k == "o":
            continue
        p[k] = n(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v
    return p


def el(x, y, rx, ry, f=None, s=None, lw=0, o=1, **k) -> dict:
    return _prim("el", x=x, y=y, rx=rx, ry=ry, f=f, s=s, lw=lw, o=o, **k)


def rr(x, y, w, h, r, f=None, s=None, lw=0, o=1, **k) -> dict:
    return _prim("rr", x=x, y=y, w=w, h=h, r=r, f=f, s=s, lw=lw, o=o, **k)


def pa(d: str, f=None, s=None, lw=0, o=1, **k) -> dict:
    """Caminho. `d` como "M 0 0 L 10 10 Q 5 5 0 0 Z" (a vírgula também vale: "M 0,0 L 10,10")."""
    return _prim("pa", d=normalizar_d(d), f=f, s=s, lw=lw, o=o, **k)


def traco(d: str, s, lw=2.4, o=1, **k) -> dict:
    """Linha sem preenchimento (sobrancelha, boca, cílios)."""
    return pa(d, None, s, lw, o, **k)


def normalizar_d(d: str) -> str:
    """Caminho em forma canônica: comando e números separados por 1 espaço, números enxutos."""
    saida = []
    for t in _NUM.findall(d):
        saida.append(t if t in "MLQCZ" else str(n(float(t))))
    return " ".join(saida)


def _pares(d: str):
    """Itera o caminho: ("M", [x, y]) ... ("Z", [])."""
    toks = d.split()
    i = 0
    while i < len(toks):
        c = toks[i]
        i += 1
        qtd = {"M": 2, "L": 2, "Q": 4, "C": 6, "Z": 0}[c]
        yield c, [float(x) for x in toks[i:i + qtd]]
        i += qtd


def mapear_d(d: str, fx, fy) -> str:
    """Aplica fx(x) e fy(y) a todo ponto do caminho."""
    saida = []
    for c, nums in _pares(d):
        saida.append(c)
        for j, v in enumerate(nums):
            saida.append(str(n(fx(v) if j % 2 == 0 else fy(v))))
    return " ".join(saida)


def espelhar(p: dict) -> dict:
    """Cópia da primitiva refletida no eixo x (o outro lado do corpo/rosto)."""
    q = dict(p)
    if p["t"] == "el":
        q["x"] = n(-p["x"])
    elif p["t"] == "rr":
        q["x"] = n(-p["x"] - p["w"])
    else:
        q["d"] = mapear_d(p["d"], lambda x: -x, lambda y: y)
    if isinstance(q.get("f"), list) and q["f"][0] == "h":
        q["f"] = ["h", q["f"][2], q["f"][1]]
    return q


def mover(p: dict, dx: float = 0, dy: float = 0) -> dict:
    q = dict(p)
    if p["t"] in ("el", "rr"):
        q["x"], q["y"] = n(p["x"] + dx), n(p["y"] + dy)
    else:
        q["d"] = mapear_d(p["d"], lambda x: x + dx, lambda y: y + dy)
    return q


def par(*prims: dict) -> list:
    """Lado esquerdo + o mesmo refletido para o direito (cabelo, orelhas, olhos...)."""
    return [x for p in prims for x in (p, espelhar(p))]


# --- cores: fichas "$nome" com sufixos de + (clareia) e - (escurece) ------------------------------------

PASSO_CLARO = 0.22
PASSO_ESCURO = 0.24
_ESCURO = (26, 15, 20)


def _rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _hex(r, g, b) -> str:
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(v + 0.5))) for v in (r, g, b))


def misturar(a: str, b: str, k: float) -> str:
    """a -> b em k (0 a 1). Arredonda sempre para cima no .5 (igual ao JavaScript: Math.floor(x + .5))."""
    ra, rb = _rgb(a), _rgb(b)
    return _hex(*(x + (y - x) * k for x, y in zip(ra, rb)))


def resolver_cor(token, paleta: dict) -> str:
    """"#RRGGBB | $ficha, com + (clareia) ou - (escurece) no fim (ex.: "$pele--", "#3B2F38-") -> "#RRGGBB"."""
    if token is None:
        return token
    m = re.fullmatch(r"(#[0-9A-Fa-f]{6}|\$[a-z0-9_]+)([+-]*)", token)
    if not m:
        raise ValueError(f"cor inválida: {token!r}")
    base = m.group(1)
    base = base.upper() if base[0] == "#" else paleta[base[1:]]
    for ch in m.group(2):
        base = misturar(base, "#FFFFFF", PASSO_CLARO) if ch == "+" else misturar(base, "#%02X%02X%02X" % _ESCURO, PASSO_ESCURO)
    return base.upper()


def resolver_prim(p: dict, paleta: dict) -> dict:
    """Cópia da primitiva com todas as fichas de cor trocadas por #RRGGBB."""
    q = dict(p)
    f = p.get("f")
    if isinstance(f, list):
        q["f"] = [f[0]] + [resolver_cor(c, paleta) for c in f[1:]]
    elif f:
        q["f"] = resolver_cor(f, paleta)
    if p.get("s"):
        q["s"] = resolver_cor(p["s"], paleta)
    return q
