"""Estilos de cabelo. Desenhados nas coordenadas da CABEÇA (origem no pescoço; testa em y=-70; topo do crânio -96).

`tras` fica atrás do rosto E do corpo (cabelo comprido, rabo de cavalo); `frente` cobre a testa e o topo da cabeça.
Cor: $cabelo (a escolhida) com + / - para luz e sombra.
"""
import math

from .arte import el, pa, par, rr, traco

H = ["v", "$cabelo+", "$cabelo-"]
LN = "$cabelo--"


def _cap(d: str, extra=()) -> list:
    return [pa(d, H, LN, 2), *extra]


def _luz(d: str, o=0.5, lw=3.4):
    return traco(d, "$cabelo++", lw, o=o)


def _fio(d: str):
    return traco(d, LN, 1.5, o=0.42)


def _cacheado() -> dict:
    tras, frente = [], []
    circ = [(0, -66, 50)]
    for i in range(16):
        a = math.radians(i * 360 / 16)
        circ.append((round(math.cos(a) * 48, 1), round(-64 + math.sin(a) * 42, 1), 16))
    for x, y, r in circ:
        tras.append(el(x, y, r, r * (0.96 if r < 40 else 0.92), "$cabelo", LN, 4))
    for x, y, r in circ:
        tras.append(el(x, y, r, r * (0.96 if r < 40 else 0.92), "$cabelo"))
    tras.append(el(-16, -92, 26, 11, "$cabelo++", None, 0, 0.32))
    franja = [(-42, -70, 12), (-29, -80, 13), (-14, -87, 13), (0, -89, 13), (14, -87, 13), (29, -80, 13), (42, -70, 12)]
    for x, y, r in franja:
        frente.append(el(x, y, r, r * 0.95, "$cabelo", LN, 4))
    for x, y, r in franja:
        frente.append(el(x, y, r, r * 0.95, "$cabelo"))
    frente.append(el(-16, -95, 16, 6, "$cabelo++", None, 0, 0.3))
    return {"nome": "Cacheado", "tras": tras, "frente": frente}


def _espetado() -> dict:
    d = ("M -52 -42 C -58 -66 -52 -84 -42 -92 L -48 -112 L -32 -100 L -30 -122 L -15 -104 L -6 -126 L 4 -105 "
         "L 14 -124 L 21 -103 L 35 -116 L 35 -96 L 49 -102 L 43 -86 C 54 -76 57 -60 52 -42 C 50 -50 47 -56 44 -60 "
         "L 36 -70 L 28 -62 L 20 -74 L 10 -63 L 2 -75 L -8 -63 L -17 -74 L -26 -62 L -34 -70 L -44 -60 "
         "C -47 -56 -50 -50 -52 -42 Z")
    return {"nome": "Espetado", "tras": [], "frente": _cap(d, [_luz("M -28 -108 L -14 -98", 0.55, 3), _luz("M 6 -110 L 14 -100", 0.55, 3)])}


ESTILOS = {
    "curto": ("Curto", [], _cap(
        "M -52 -42 C -58 -92 -30 -107 0 -107 C 30 -107 58 -92 52 -42 C 50 -50 47 -56 44 -60 C 40 -68 33 -70 28 -69 "
        "C 20 -75 8 -71 0 -75 C -8 -71 -20 -75 -28 -69 C -33 -70 -40 -68 -44 -60 C -47 -56 -50 -50 -52 -42 Z",
        [_luz("M -30 -94 Q -10 -104 14 -100"), _fio("M 10 -105 Q 16 -90 8 -76"), _fio("M -14 -105 Q -8 -92 -18 -78")])),
    "topete": ("Topete", [], _cap(
        "M -52 -42 C -60 -80 -46 -104 -14 -110 C 6 -130 48 -124 57 -96 C 60 -80 56 -60 52 -42 C 50 -50 47 -56 44 -60 "
        "C 40 -68 32 -70 24 -68 C 12 -80 -6 -78 -14 -70 C -24 -72 -36 -68 -44 -60 C -47 -56 -50 -50 -52 -42 Z",
        [_luz("M -22 -108 Q 10 -126 46 -108", 0.5, 3.6), _fio("M 18 -120 Q 30 -100 22 -82")])),
    "social": ("Social (risca)", [], _cap(
        "M -52 -42 C -58 -90 -30 -108 4 -108 C 34 -108 58 -92 52 -42 C 50 -50 47 -56 44 -60 C 38 -70 28 -72 20 -70 "
        "C 6 -70 -8 -76 -22 -74 C -34 -72 -40 -66 -44 -60 C -47 -56 -50 -50 -52 -42 Z",
        [traco("M -12 -107 Q -8 -92 -24 -75", LN, 1.8, o=0.7), _luz("M 0 -103 Q 26 -100 42 -84", 0.5, 3)])),
    "coque": ("Coque", [], [
        pa("M -52 -42 C -58 -90 -30 -106 0 -106 C 30 -106 58 -90 52 -42 C 50 -52 46 -62 40 -68 C 26 -78 -26 -78 -40 -68 "
           "C -46 -62 -50 -52 -52 -42 Z", H, LN, 2),
        el(0, -114, 18, 15.5, H, LN, 2), traco("M -14 -104 Q 0 -98 14 -104", "$r1", 4.6),
        _luz("M -12 -120 Q 0 -128 12 -120", 0.55, 3), _luz("M -30 -94 Q -10 -102 12 -99", 0.45, 3)]),
    "longo": ("Longo", [pa(
        "M -57 -56 C -68 -20 -64 24 -58 56 Q -40 62 -30 58 L 30 58 Q 40 62 58 56 C 64 24 68 -20 57 -56 "
        "C 53 -104 -53 -104 -57 -56 Z", H, LN, 2)], [
        pa("M -53 -26 C -62 -90 -30 -108 0 -108 C 30 -108 62 -90 53 -26 C 52 -42 50 -54 46 -62 "
           "C 36 -72 18 -76 0 -86 C -18 -76 -36 -72 -46 -62 C -50 -54 -52 -42 -53 -26 Z", H, LN, 2),
        traco("M 0 -108 L 0 -87", LN, 1.6, o=0.55), _luz("M -30 -98 Q -14 -104 -2 -102", 0.5, 3),
        _luz("M 30 -98 Q 14 -104 2 -102", 0.5, 3)]),
    "rabo": ("Rabo de cavalo", [
        pa("M 22 -96 C 70 -116 92 -70 74 -22 C 68 -4 60 6 48 12 C 58 -16 54 -50 34 -68 Z", H, LN, 2)], [
        pa("M -52 -42 C -58 -92 -30 -107 0 -107 C 30 -107 58 -92 52 -42 C 50 -52 46 -60 40 -66 C 32 -60 22 -74 6 -72 "
           "C -6 -70 -18 -74 -28 -68 C -36 -70 -42 -62 -46 -56 C -49 -52 -51 -47 -52 -42 Z", H, LN, 2),
        el(33, -88, 6.4, 9, "$r1", "$linha", 1.6), _luz("M -30 -94 Q -10 -104 14 -100"),
        _fio("M 10 -105 Q 16 -90 8 -76")]),
    "chanel": ("Chanel", [pa(
        "M -59 -58 C -68 -30 -63 -6 -54 8 L 54 8 C 63 -6 68 -30 59 -58 C 55 -108 -55 -108 -59 -58 Z", H, LN, 2)], [
        pa("M -55 -6 C -64 -70 -30 -110 0 -110 C 30 -110 64 -70 55 -6 C 51 -20 49 -40 47 -56 L 42 -64 "
           "C 22 -60 -22 -60 -42 -64 L -47 -56 C -49 -40 -51 -20 -55 -6 Z", H, LN, 2),
        _luz("M -30 -98 Q -10 -106 14 -102"), _fio("M 0 -108 Q 3 -90 0 -66")]),
    "chiquinha": ("Maria-chiquinha", par(pa(
        "M -46 -78 C -82 -82 -92 -40 -80 -2 C -76 10 -64 14 -57 9 C -68 -10 -62 -42 -42 -62 Z", H, LN, 2)), [
        pa("M -52 -42 C -58 -92 -30 -107 0 -107 C 30 -107 58 -92 52 -42 C 50 -50 47 -56 44 -60 C 40 -68 30 -70 22 -68 "
           "C 12 -74 4 -70 0 -74 C -4 -70 -12 -74 -22 -68 C -30 -70 -40 -68 -44 -60 C -47 -56 -50 -50 -52 -42 Z", H, LN, 2),
        traco("M 0 -107 L 0 -76", LN, 1.5, o=0.5), *par(el(-49, -74, 6.4, 8.6, "$r1", "$linha", 1.6)),
        _luz("M -30 -94 Q -10 -104 14 -100")]),
}

# --- mais estilos (2ª rodada, 30/09) --------------------------------------------------------------------------------
# touca rente ao crânio (base de raspado, moicano, samurai...): linha do cabelo em y=-74
TOUCA = ("M -52 -46 C -56 -86 -30 -101 0 -101 C 30 -101 56 -86 52 -46 C 50 -58 46 -67 40 -73 "
         "C 26 -80 -26 -80 -40 -73 C -46 -67 -50 -58 -52 -46 Z")


def _touca(o=1.0) -> dict:
    return pa(TOUCA, H, LN, 2, o=o)


def _mechas(xs, y0, comp, larg=10, cor="$cabelo") -> list:
    """Mechas penduradas (dreads) a partir de y0."""
    saida = []
    for x in xs:
        saida.append(pa(f"M {x - larg / 2} {y0} L {x - larg / 2 + 1} {y0 + comp} Q {x} {y0 + comp + larg * .6} "
                        f"{x + larg / 2 - 1} {y0 + comp} L {x + larg / 2} {y0} Z", ["h", cor + "-", cor + "+"], LN, 1.8))
        saida += [traco(f"M {x - larg / 2 + 1.5} {y} L {x + larg / 2 - 1.5} {y + 2.5}", LN, 1.2, o=0.45)
                  for y in range(int(y0) + 14, int(y0 + comp) - 4, 12)]
    return saida


def _black_power() -> dict:
    tras = [el(0, -74, 70, 60, H, LN, 2.2)]
    for x, y in ((-38, -104), (-10, -118), (22, -112), (46, -88), (-54, -70), (54, -56), (-44, -40), (30, -126)):
        tras.append(el(x, y, 7, 6, "$cabelo-", None, 0, 0.35))
    tras.append(el(-22, -112, 22, 9, "$cabelo++", None, 0, 0.28))
    return {"nome": "Black power", "tras": tras, "frente": [_touca(), _luz("M -26 -92 Q -8 -99 12 -96", 0.35, 3)], "balanco": 0.35}


def _tranca_lateral() -> dict:
    elos = [el(44 + i * 1.2, -40 + i * 11, 9 - i * 0.35, 7.2, H, LN, 1.8) for i in range(8)]
    return {"nome": "Trança lateral", "tras": [], "frente": [
        pa("M -52 -42 C -58 -92 -30 -107 0 -107 C 30 -107 58 -92 54 -44 C 50 -56 46 -62 40 -66 C 26 -76 10 -72 -4 -76 "
           "C -16 -70 -30 -72 -40 -66 C -46 -60 -50 -52 -52 -42 Z", H, LN, 2),
        *elos, el(53.6, 48, 5, 4, "$r1", "$linha", 1.4), pa("M 50 52 L 58 66 L 47 60 Z", H, LN, 1.6),
        _luz("M -30 -94 Q -10 -104 14 -100"), _fio("M 20 -104 Q 34 -90 40 -66")], "balanco": 0.7}


MAIS = {
    "raspado": {"nome": "Raspado", "tras": [], "frente": [_touca(0.92), _luz("M -24 -92 Q -6 -98 12 -95", 0.3, 3)]},
    "careca": {"nome": "Careca", "tras": [], "frente": [el(-16, -84, 13, 6, "#FFFFFF", None, 0, 0.28),
                                                         el(-24, -80, 4, 2.4, "#FFFFFF", None, 0, 0.35)]},
    "moicano": {"nome": "Moicano", "tras": [], "frente": [
        _touca(0.3),
        pa("M -13 -72 C -18 -98 -16 -124 -2 -132 L 2 -120 L 10 -128 C 18 -112 17 -92 13 -72 C 6 -78 -6 -78 -13 -72 Z", H, LN, 2),
        _luz("M -8 -120 Q -6 -100 -6 -82", 0.45, 3)]},
    "black_power": _black_power(),
    "dreads": {"nome": "Dreads", "tras": _mechas([-54, -40, 40, 54], -70, 96) + _mechas([-26, -12, 2, 16, 28], -80, 108),
               "frente": [_touca(), *_mechas([-47, 47], -64, 70, 11), _luz("M -26 -92 Q -8 -99 12 -96", 0.35, 3)],
               "balanco": 1.0},
    "tranca": _tranca_lateral(),
    "franja": {"nome": "Franja reta", "tras": [pa(
        "M -57 -56 C -66 -20 -63 22 -57 48 L 57 48 C 63 22 66 -20 57 -56 C 53 -104 -53 -104 -57 -56 Z", H, LN, 2)], "frente": [
        pa("M -54 -22 C -62 -88 -30 -108 0 -108 C 30 -108 62 -88 54 -22 C 52 -36 50 -50 48 -60 C 46 -66 44 -68 40 -68 "
           "L -40 -68 C -44 -68 -46 -66 -48 -60 C -50 -50 -52 -36 -54 -22 Z", H, LN, 2),
        *[_fio(f"M {x} -96 L {x + 1} -70") for x in (-24, -8, 8, 24)], _luz("M -30 -98 Q -8 -106 16 -102", 0.5, 3)],
        "balanco": 1.0},
    "lateral": {"nome": "Franja de lado", "tras": [pa(
        "M -56 -56 C -64 -30 -60 -4 -52 10 L 52 10 C 60 -4 64 -30 56 -56 C 52 -104 -52 -104 -56 -56 Z", H, LN, 2)], "frente": [
        pa("M -53 -20 C -62 -88 -30 -108 4 -108 C 34 -108 60 -90 54 -30 C 52 -46 48 -60 42 -68 C 30 -74 20 -74 10 -70 "
           "C -6 -66 -22 -62 -36 -50 C -44 -44 -50 -34 -53 -20 Z", H, LN, 2),
        _fio("M 22 -104 Q 4 -86 -30 -58"), _fio("M 36 -98 Q 20 -80 -10 -66"), _luz("M 10 -102 Q 34 -100 46 -84", 0.5, 3)],
        "balanco": 0.6},
    "samurai": {"nome": "Coque alto", "tras": [], "frente": [
        _touca(), traco("M -30 -92 Q -14 -84 -10 -76", LN, 1.4, o=0.5), traco("M 30 -92 Q 14 -84 10 -76", LN, 1.4, o=0.5),
        el(0, -108, 13, 11, H, LN, 2), rr(-7, -99.5, 14, 5, 2.2, "$r1", "$linha", 1.3), _luz("M -8 -114 Q 0 -119 8 -114", 0.5, 2.6)]},
    "ondulado": {"nome": "Ondulado", "tras": [pa(
        "M -57 -56 C -70 -30 -58 -10 -66 10 C -72 26 -58 40 -62 54 Q -40 64 -26 56 L 26 56 Q 40 64 62 54 C 58 40 72 26 66 10 "
        "C 58 -10 70 -30 57 -56 C 53 -104 -53 -104 -57 -56 Z", H, LN, 2),
        traco("M -54 -10 Q -60 10 -52 30", LN, 1.5, o=0.4), traco("M 54 -10 Q 60 10 52 30", LN, 1.5, o=0.4)], "frente": [
        pa("M -53 -24 C -62 -90 -26 -110 6 -108 C 36 -106 62 -88 53 -24 C 52 -40 50 -52 46 -60 C 40 -68 30 -66 22 -72 "
           "C 12 -78 -2 -70 -12 -76 C -24 -72 -38 -70 -46 -60 C -50 -52 -52 -40 -53 -24 Z", H, LN, 2),
        _luz("M -30 -98 Q -10 -106 12 -102"), _fio("M 8 -106 Q 18 -90 22 -74")], "balanco": 1.0},
    "dois_coques": {"nome": "Dois coques", "tras": [], "frente": [
        *par(el(-40, -100, 16, 15, H, LN, 2)), *par(traco("M -50 -90 Q -40 -86 -30 -90", "$r1", 3.4)),
        pa("M -52 -42 C -58 -92 -30 -107 0 -107 C 30 -107 58 -92 52 -42 C 50 -50 47 -56 44 -60 C 40 -68 30 -70 22 -68 "
           "C 12 -74 4 -70 0 -74 C -4 -70 -12 -74 -22 -68 C -30 -70 -40 -68 -44 -60 C -47 -56 -50 -50 -52 -42 Z", H, LN, 2),
        traco("M 0 -107 L 0 -76", LN, 1.5, o=0.5), _luz("M -30 -94 Q -10 -104 14 -100")]},
    "repicado": {"nome": "Repicado", "tras": [], "frente": _cap(
        "M -54 -40 C -60 -92 -30 -108 2 -108 C 34 -108 60 -92 54 -40 L 48 -54 L 46 -44 L 40 -62 L 32 -58 L 28 -70 L 18 -62 "
        "L 12 -74 L 2 -64 L -6 -76 L -14 -64 L -22 -74 L -30 -62 L -36 -70 L -42 -56 L -46 -64 L -50 -48 Z",
        [_luz("M -28 -96 Q -8 -104 14 -100", 0.5, 3), _fio("M 16 -104 L 24 -80"), _fio("M -10 -104 L -16 -82")])},
}

CABELOS: dict = {id_: {"nome": nome, "tras": tras, "frente": frente} for id_, (nome, tras, frente) in ESTILOS.items()}
CABELOS["cacheado"] = _cacheado()
CABELOS["espetado"] = _espetado()
CABELOS.update(MAIS)
# quanto o cabelo de trás balança com o corpo (inércia): comprido 1, curto quase nada
for _id, _b in {"longo": 1.0, "rabo": 0.9, "chanel": 0.6, "chiquinha": 0.8, "cacheado": 0.4}.items():
    CABELOS[_id]["balanco"] = _b
ORDEM = ["curto", "espetado", "topete", "social", "raspado", "careca", "moicano", "samurai", "repicado", "cacheado",
         "black_power", "dreads", "longo", "ondulado", "franja", "lateral", "rabo", "tranca", "chanel", "chiquinha", "coque",
         "dois_coques"]
CABELOS = {k: CABELOS[k] for k in ORDEM}
