"""Acessórios (óculos, fone, boné...). Cada um desenha em slots do rosto: `acessorio` (por cima de tudo) ou
`mascara_baixo` (por baixo dos olhos e da boca: barba, bigode). Coordenadas da CABEÇA (origem no pescoço)."""
import math

from .arte import el, pa, par, rr, traco

_ARO = "#2E2530"


def _oculos():
    aros = par(el(-19, -40, 15.5, 15, None, _ARO, 3.2), el(-19, -40, 14.6, 14, "#BEE3FF", None, 0, 0.16))
    return {"acessorio": [*aros, traco("M -3.6 -42 Q 0 -45 3.6 -42", _ARO, 3),
                          *par(traco("M -34.5 -42 L -49 -46", _ARO, 2.8)),
                          *par(traco("M -27 -50 Q -22 -53 -16 -52", "#FFFFFF", 1.8, o=0.6))]}


def _oculos_sol():
    lentes = par(pa("M -36 -50 Q -19 -54 -3 -50 L -5 -33 Q -19 -26 -34 -33 Z", ["v", "#2B2733", "#0E0C12"], _ARO, 2.6))
    return {"acessorio": [*lentes, traco("M -4 -47 Q 0 -49 4 -47", _ARO, 3), *par(traco("M -36 -47 L -50 -50", _ARO, 3)),
                          *par(traco("M -30 -46 L -22 -48", "#FFFFFF", 2, o=0.45))]}


def _fone():
    return {"acessorio": [traco("M -51 -52 C -52 -118 52 -118 51 -52", "#2E2A38", 7), traco("M -51 -52 C -52 -118 52 -118 51 -52", "#5B5470", 2.4, o=0.8),
                          *par(rr(-62, -66, 14, 32, 7, ["h", "#3A3446", "#5B5470"], "#1E1A26", 1.8), rr(-59.4, -58, 5.6, 16, 2.6, "$r2", None))]}


def _headset():
    f = _fone()["acessorio"]
    return {"acessorio": [*f, traco("M -54 -38 Q -50 -14 -28 -8", "#2E2A38", 3.4), el(-26, -8, 4.4, 3.4, "#2E2A38", "#1E1A26", 1.2)]}


def _bone():
    return {"acessorio": [pa("M -53 -58 C -60 -108 60 -108 53 -58 C 30 -68 -30 -68 -53 -58 Z", ["v", "$r1+", "$r1-"], "$linha", 2),
                          pa("M -47 -60 C -20 -50 30 -50 60 -63 C 60 -72 52 -73 46 -70 C 20 -62 -20 -62 -47 -60 Z", ["v", "$r1", "$r1--"], "$linha", 2),
                          el(0, -101, 4.4, 3.4, "$r1--", "$linha", 1.4), traco("M -30 -90 Q -12 -100 8 -98", "#FFFFFF", 3, o=0.3)]}


def _chapeu():
    return {"acessorio": [pa("M -66 -66 C -30 -56 30 -56 66 -66 C 62 -76 50 -76 44 -76 C 20 -66 -20 -66 -44 -76 C -50 -76 -62 -76 -66 -66 Z", ["v", "#4A3A3F", "#2A2024"], "$linha", 2),
                          pa("M -37 -72 C -40 -104 -30 -118 0 -118 C 30 -118 40 -104 37 -72 C 20 -66 -20 -66 -37 -72 Z", ["v", "#5B484E", "#2E2428"], "$linha", 2),
                          pa("M -38 -78 C -20 -70 20 -70 38 -78 L 37.6 -86 C 20 -78 -20 -78 -37.6 -86 Z", "$r2", "$linha", 1.4)]}


def _laco():
    return {"acessorio": [pa("M 28 -94 C 14 -110 12 -84 28 -94 Z", ["v", "$r2+", "$r2-"], "$linha", 1.6),
                          pa("M 28 -94 C 44 -110 46 -84 28 -94 Z", ["v", "$r2+", "$r2-"], "$linha", 1.6),
                          el(28, -94, 4.6, 4.6, "$r2--", "$linha", 1.4)]}


def _bigode():
    return {"mascara_baixo": [*par(pa("M 0 -25.5 Q -7 -32 -15 -26 Q -18 -24 -22 -27 Q -16 -18 -6 -21 Q -2 -22 0 -22 Z", ["v", "$cabelo+", "$cabelo-"], "$cabelo--", 1.6))]}


def _barba():
    return {"mascara_baixo": [pa("M -47 -38 Q -52 -2 0 6 Q 52 -2 47 -38 Q 34 -22 22 -26 Q 10 -22 0 -24 Q -10 -22 -22 -26 Q -34 -22 -47 -38 Z",
                                 ["v", "$cabelo+", "$cabelo-"], "$cabelo--", 2)]}


def _brincos():
    return {"acessorio": [*par(el(-51, -36, 3.4, 4.4, "#F2C94C", "$linha", 1.2), el(-51, -30, 2.2, 3, "#F2C94C", "$linha", 1))]}


# --- mais acessórios (2ª rodada, 30/09) ------------------------------------------------------------------------------
_OURO = ["v", "#FFE08A", "#C9962E"]


def _estrela(cx, cy, r, cor, contorno="$linha"):
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        k = r if i % 2 == 0 else r * 0.45
        pts.append(f"{cx + k * math.cos(a):.1f} {cy + k * math.sin(a):.1f}")
    return pa("M " + " L ".join(pts) + " Z", cor, contorno, 1.3)


def _coroa():
    return {"acessorio": [pa("M -30 -96 L -36 -124 L -18 -108 L 0 -130 L 18 -108 L 36 -124 L 30 -96 Q 0 -102 -30 -96 Z", _OURO, "#7A5A10", 1.8),
                          el(0, -104, 3.4, 3.4, "#D9384A", "#7A1A24", 1), *par(el(-18, -101, 2.6, 2.6, "#3F7BE0", "#1A2F6B", 1)),
                          traco("M -24 -110 L -20 -104", "#FFFFFF", 1.6, o=0.6)]}


def _tiara():
    return {"acessorio": [traco("M -44 -80 Q 0 -104 44 -80", "#C9962E", 4.2), traco("M -44 -80 Q 0 -104 44 -80", "#FFE08A", 1.8),
                          pa("M -7 -95 L 0 -106 L 7 -95 Z", _OURO, "#7A5A10", 1.2), el(0, -96, 2.4, 2.4, "#F27CA8", None)]}


def _orelhas_gato():
    return {"acessorio": [*par(pa("M -46 -80 L -44 -118 L -18 -100 Z", ["v", "$r1+", "$r1-"], "$linha", 1.8),
                               pa("M -41 -86 L -40 -108 L -26 -99 Z", "#F7A8C0", None, 0, 0.9))]}


def _flor():
    petalas = [el(38 + dx, -94 + dy, 5.4, 5.4, ["r", "#FFFFFF", "$r2"], "$linha", 1.2) for dx, dy in ((0, -6), (5.7, -1.9), (3.5, 4.9), (-3.5, 4.9), (-5.7, -1.9))]
    return {"acessorio": [*petalas, el(38, -94, 3, 3, "#F2C94C", "$linha", 1)]}


def _estrelinha():
    return {"acessorio": [_estrela(-38, -92, 8, _OURO, "#7A5A10"), traco("M -40 -96 L -38 -93", "#FFFFFF", 1.2, o=0.7)]}


def _bandana():
    return {"acessorio": [pa("M -54 -66 Q 0 -84 54 -66 L 53 -56 Q 0 -74 -53 -56 Z", ["v", "$r1+", "$r1-"], "$linha", 1.8),
                          pa("M 50 -64 L 66 -56 L 60 -50 Z", "$r1-", "$linha", 1.4), pa("M 50 -60 L 62 -44 L 54 -42 Z", "$r1-", "$linha", 1.4)]}


def _boina():
    return {"acessorio": [pa("M -50 -84 C -58 -114 40 -126 60 -98 C 54 -86 -16 -80 -50 -84 Z", ["v", "$r1+", "$r1-"], "$linha", 2),
                          el(8, -114, 3, 3, "$r1-", "$linha", 1.2), traco("M -30 -102 Q 0 -114 30 -106", "#FFFFFF", 2.4, o=0.25)]}


def _gorro():
    return {"acessorio": [pa("M -52 -66 C -58 -120 58 -120 52 -66 Z", ["v", "$r1+", "$r1-"], "$linha", 2),
                          *[traco(f"M {x} -108 L {x * 1.12:.1f} -74", "$r1--", 1.3, o=0.5) for x in (-30, -15, 0, 15, 30)],
                          rr(-55, -76, 110, 14, 6, ["v", "$r2+", "$r2-"], "$linha", 1.8), el(0, -118, 9, 8.4, ["r", "$r2+", "$r2"], "$linha", 1.6)]}


def _chapeu_bruxa():
    return {"acessorio": [pa("M -68 -70 C -30 -60 30 -60 68 -70 C 60 -80 40 -82 30 -80 C 10 -74 -10 -74 -30 -80 C -40 -82 -60 -80 -68 -70 Z",
                             ["v", "#4A3A6A", "#241A38"], "$linha", 2),
                          pa("M -30 -78 C -24 -110 0 -140 26 -150 C 14 -130 22 -100 30 -78 C 10 -72 -10 -72 -30 -78 Z", ["v", "#5A4A7E", "#2A2040"], "$linha", 2),
                          pa("M -29 -86 C -10 -80 12 -80 30 -86 L 30 -80 C 12 -74 -10 -74 -30 -80 Z", "$r2", "$linha", 1.2)]}


def _aureola():
    return {"acessorio": [el(0, -122, 30, 7, None, "#F2C94C", 4.4), el(0, -122, 30, 7, None, "#FFF4C2", 1.6),
                          el(0, -122, 36, 11, None, "#FFE08A", 6, 0.22)]}


def _chifres():
    return {"acessorio": [*par(pa("M -34 -96 Q -46 -112 -40 -128 Q -30 -114 -22 -100 Z", ["v", "#F25C5C", "#A8202A"], "$linha", 1.6))]}


def _mascara_baile():
    return {"acessorio": [*par(el(-19, -40, 15.6, 14.6, None, "$r1", 6.2), el(-19, -40, 18.8, 17.8, None, "$linha", 1.4),
                               pa("M -34 -50 Q -50 -64 -52 -76 Q -40 -64 -30 -56 Z", ["v", "$r1+", "$r1-"], "$linha", 1.3)),
                          pa("M -5 -46 Q 0 -50 5 -46 L 4 -38 Q 0 -40 -4 -38 Z", "$r1", "$linha", 1.2)]}


def _cachecol():
    return {"torso": [rr(-20, -50, 40, 10, 5, ["v", "$r1+", "$r1-"], "$linha", 1.6),
                      rr(7, -44, 10, 30, 3.4, ["h", "$r1-", "$r1"], "$linha", 1.5),
                      *[traco(f"M {x} -14 L {x} -9", "$r1-", 1.4) for x in (9, 12, 15)], traco("M 7 -26 L 17 -26", "$r2", 2.2)]}


def _gravata_borboleta():
    return {"torso": [pa("M 0 -42 L -9 -47 L -9 -37 Z", ["v", "$r2+", "$r2-"], "$linha", 1.3),
                      pa("M 0 -42 L 9 -47 L 9 -37 Z", ["v", "$r2+", "$r2-"], "$linha", 1.3), el(0, -42, 2.4, 2.6, "$r2-", "$linha", 1.1)]}


def _colar():
    return {"torso": [traco("M -12 -45 Q 0 -30 12 -45", "#C9962E", 1.8), el(0, -33.6, 3.4, 4, _OURO, "#7A5A10", 1.1),
                      el(-0.8, -34.6, 1, 1.2, "#FFFFFF", None, 0, 0.7)]}


def _pinta():
    return {"acessorio": [el(15, -20, 1.5, 1.5, "#3B2A30")]}


def _curativo():
    return {"acessorio": [pa("M 22 -30 L 36 -36 L 38 -31 L 24 -25 Z", "#F2D2A8", "$linha", 1.2),
                          *[el(x, y, 0.6, 0.6, "#C9A07A") for x, y in ((28.6, -31.4), (30.6, -32.2), (29.6, -29.8), (31.6, -30.6))]]}


ACESSORIOS: dict = {
    "oculos": {"nome": "Óculos", "pecas": _oculos()},
    "oculos_sol": {"nome": "Óculos escuros", "pecas": _oculos_sol()},
    "mascara_baile": {"nome": "Máscara de baile", "pecas": _mascara_baile()},
    "fone": {"nome": "Fone de ouvido", "pecas": _fone()},
    "headset": {"nome": "Headset com microfone", "pecas": _headset()},
    "bone": {"nome": "Boné", "pecas": _bone()},
    "chapeu": {"nome": "Chapéu", "pecas": _chapeu()},
    "boina": {"nome": "Boina", "pecas": _boina()},
    "gorro": {"nome": "Gorro", "pecas": _gorro()},
    "chapeu_bruxa": {"nome": "Chapéu de bruxo", "pecas": _chapeu_bruxa()},
    "coroa": {"nome": "Coroa", "pecas": _coroa()},
    "tiara": {"nome": "Tiara", "pecas": _tiara()},
    "bandana": {"nome": "Faixa na testa", "pecas": _bandana()},
    "orelhas_gato": {"nome": "Orelhas de gato", "pecas": _orelhas_gato()},
    "chifres": {"nome": "Chifrinhos", "pecas": _chifres()},
    "aureola": {"nome": "Auréola", "pecas": _aureola()},
    "laco": {"nome": "Laço no cabelo", "pecas": _laco()},
    "flor": {"nome": "Flor no cabelo", "pecas": _flor()},
    "estrelinha": {"nome": "Presilha de estrela", "pecas": _estrelinha()},
    "brincos": {"nome": "Brincos", "pecas": _brincos()},
    "colar": {"nome": "Colar", "pecas": _colar()},
    "cachecol": {"nome": "Cachecol", "pecas": _cachecol()},
    "gravata_borboleta": {"nome": "Gravata-borboleta", "pecas": _gravata_borboleta()},
    "bigode": {"nome": "Bigode", "pecas": _bigode()},
    "barba": {"nome": "Barba", "pecas": _barba()},
    "pinta": {"nome": "Pintinha", "pecas": _pinta()},
    "curativo": {"nome": "Curativo", "pecas": _curativo()},
}
