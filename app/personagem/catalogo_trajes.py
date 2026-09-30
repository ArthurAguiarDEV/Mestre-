"""Fantasias de heróis (Marvel e DC) — versões INSPIRADAS, desenhadas do zero em cores e formas simples.

Uso pessoal no Assessor do dono: são paletas e silhuetas, sem logotipos oficiais (os emblemas são formas abstratas).
Personagens e marcas pertencem aos seus donos; se este projeto um dia for distribuído, revise esta lista.

Cada fantasia: nome, universo, `cores` (fichas $c1..$c6 e, se quiser, pele/cabelo), `esconde` (slots do rosto que
somem: cabelo, sobr, boca, acessorio), `olhos` (normal|lente|visor|fenda), `forca_cabelo`, `expressao`, e `pecas`
por gênero. Uma fantasia SUBSTITUI a roupa; o resto (cabelo, acessórios, tom de pele) continua o do usuário.
Slots extras: capa, mascara_baixo (antes dos olhos), mascara_cima (depois), adereco_e / adereco_d (o objeto na mão;
o lado direito nasce espelhado, por isso use `direita(...)`).
Para acrescentar um herói: escreva `_meu_heroi(g)` e registre em `_HEROIS` (Marvel aqui, DC em catalogo_trajes_dc.py).
"""
import math

from .arte import el, espelhar, mapear_d, pa, par, rr, traco
from .catalogo_corpo import CABECA_D, TORSO_D, mao, segmento
from .catalogo_roupas import LINHA, _g, _gh, _junta, calca

# --- peças reaproveitáveis -----------------------------------------------------------------------------------


def direita(prims: list) -> list:
    """Objeto da mão direita: o nó é espelhado, então o desenho vai espelhado de volta para sair certo na tela."""
    return [espelhar(p) for p in prims]


def tronco(g: str, cor: str) -> dict:
    return pa(TORSO_D[g], _g(cor), LINHA, 1.8)


def lado(g: str, x_int: float, cor: str) -> dict:
    """Faixa lateral do tronco (esquerda), do ombro até a barra; a direita é `espelhar`."""
    if g == "m":
        d = f"M -23 -38 Q -23 -45 -15 -45 L {x_int} -45 L {x_int} 6 L -13 6 Q -21 6 -21 0 Z"
    else:
        d = (f"M -20 -38 Q -20 -45 -13 -45 L {x_int} -45 L {x_int} 7 L -16 7 Q -21 7 -21 5 "
             f"Q -15.5 -8 -15.5 -16 Q -18 -28 -20 -38 Z")
    return pa(d, _g(cor), LINHA, 1.4)


def estrela(cx, cy, raio, cor, pontas=5, fundo=None, giro=-90, contorno=None) -> dict:
    r = raio * (fundo or 0.42)
    pts = []
    for i in range(pontas * 2):
        a = math.radians(giro + i * 180 / pontas)
        k = raio if i % 2 == 0 else r
        pts.append(f"{cx + k * math.cos(a):.1f} {cy + k * math.sin(a):.1f}")
    return pa("M " + " L ".join(pts) + " Z", cor, contorno, 1.2 if contorno else 0)


def raio(cx, cy, e, cor, contorno=None) -> dict:
    """Raio (relâmpago) centrado em (cx, cy), altura ~ 24*e."""
    pts = [(3, -12), (-5, 1), (0, 1), (-3, 12), (6, -2), (1, -2)]
    return pa("M " + " L ".join(f"{cx + x * e:.1f} {cy + y * e:.1f}" for x, y in pts) + " Z", cor, contorno, 1.2 if contorno else 0)


def losango(cx, cy, w, h, cor, contorno=LINHA, lw=1.4) -> dict:
    return pa(f"M {cx} {cy - h / 2} L {cx + w / 2} {cy} L {cx} {cy + h / 2} L {cx - w / 2} {cy} Z", cor, contorno, lw)


def cinto(cor: str, fivela: str | None = None, y=-6.5, larg=43) -> list:
    d = [rr(-larg / 2, y, larg, 7.2, 3, _g(cor), LINHA, 1.4)]
    if fivela:
        d.append(rr(-4.6, y - 0.6, 9.2, 8.4, 2.2, _g(fivela), LINHA, 1.3))
    return d


def luva(cor: str) -> list:
    return mao(_g(cor), 1.12)


def manga(sup: str, inf: str | None = None, punho: str | None = None) -> dict:
    return {"braco_sup": segmento(6.6, _gh(sup)),
            "braco_inf": segmento(6.1, _gh(inf or sup))
            + ([rr(-6.6, 12, 13.2, 8.6, 3.2, _gh(punho), LINHA, 1.5)] if punho else [])}


def bota_alta(cor: str, topo=27, sola="#1A1216", borda: str | None = None) -> list:
    d = [rr(-10, topo, 20, 53 - topo, 6, _gh(cor), LINHA, 1.6), rr(-11, 48.6, 22, 4.6, 2.3, sola, LINHA, 1.2)]
    if borda:
        d.append(rr(-10.4, topo - 0.5, 20.8, 4.4, 2, _gh(borda), LINHA, 1.3))
    return d


def capa(cor: str, comp=80, larg=44, borda: str | None = None, recorte: int = 0) -> list:
    if recorte:   # barra em ondas (capa do morcego)
        pts, passo = [], 2 * larg / recorte
        baixo = "".join(f" Q {larg - passo * (i + 0.5):.1f} {comp + 12} {larg - passo * (i + 1):.1f} {comp}" for i in range(recorte))
        d = f"M -19 3 Q -24 8 -28 22 Q -44 56 {-larg} {comp} L {larg} {comp}" + baixo + " Q 44 56 28 22 Q 24 8 19 3 Z"
        d = f"M -19 3 Q -24 8 -28 22 Q -44 56 {-larg} {comp} " + "".join(
            f"Q {-larg + passo * (i + 0.5):.1f} {comp + 13} {-larg + passo * (i + 1):.1f} {comp} " for i in range(recorte)
        ) + "Q 44 56 28 22 Q 24 8 19 3 Z"
    else:
        d = f"M -19 3 Q -24 8 -28 22 Q -44 56 {-larg} {comp} Q 0 {comp + 13} {larg} {comp} Q 44 56 28 22 Q 24 8 19 3 Z"
    prims = [pa(d, _g(cor), LINHA, 1.8), traco("M -6 14 Q -12 50 -14 84", cor + "--", 1.8, o=0.35),
             traco("M 8 14 Q 14 50 16 84", cor + "--", 1.8, o=0.35)]
    if borda:
        prims.append(traco(f"M {-larg + 2} {comp - 1} Q 0 {comp + 11} {larg - 2} {comp - 1}", borda, 3.2))
    return prims


def cabeca_cheia(cor: str, borda: str = LINHA) -> dict:
    """Capacete/capuz que cobre a cabeça toda."""
    d = mapear_d(CABECA_D, lambda x: x * 1.05, lambda y: (y + 50) * 1.05 - 50)
    return pa(d, _g(cor), borda, 2)


def capuz(cor: str, base=-34, meio=-60, borda: str = LINHA) -> dict:
    """Capuz que deixa a parte de baixo do rosto de fora: `meio` = altura da borda no centro; `base` nas laterais."""
    y = round((-98 - 0.25 * base) / 0.75, 1)   # controle da curva para o topo do capuz chegar a y=-98
    d = (f"M -53 {base} C -62 {y} 62 {y} 53 {base} C 50 {base - 8} 48 {meio + 8} 40 {meio + 2} "
         f"C 20 {meio - 4} -20 {meio - 4} -40 {meio + 2} C -48 {meio + 8} -50 {base - 8} -53 {base} Z")
    return pa(d, _g(cor), borda, 2)


def orelha_pontuda(x, alt, cor: str) -> list:
    """Par de orelhas pontudas sobre a cabeça (esquerda em x<0)."""
    return par(pa(f"M {-x - 8} -92 L {-x - 4} {-92 - alt} L {-x + 9} -96 Z", _g(cor), LINHA, 1.6))


# --- MARVEL --------------------------------------------------------------------------------------------------


def _homem_de_ferro(g):
    v, o = "$c1", "$c2"
    return _junta(
        {"torso": [tronco(g, v), pa("M -17 -41 Q 0 -30 17 -41 L 14 -21 Q 0 -13 -14 -21 Z", _g(o), LINHA, 1.4),
                   el(0, -28, 6.8, 6.8, "$c3", LINHA, 1.4), el(0, -28, 3.6, 3.6, "#FFFFFF", None, 0, 0.92), *cinto(o, None)],
         "perna": [calca(v), el(0, 22, 5.2, 5.6, _g(o), LINHA, 1.4), *bota_alta(o, 28)],
         "mao": luva(o),
         "mascara_baixo": [cabeca_cheia(v), pa("M -37 -72 Q 0 -83 37 -72 L 35 -13 Q 0 1 -35 -13 Z", _g(o), LINHA, 1.8),
                           traco("M 0 -80 L 0 -74", v + "--", 2), traco("M -30 -30 Q 0 -25 30 -30", o + "--", 1.4, o=0.6)],
         "mascara_cima": [traco("M -33 -68 Q -34 -40 -30 -16", o + "--", 1.4, o=0.5), traco("M 33 -68 Q 34 -40 30 -16", o + "--", 1.4, o=0.5)]},
        manga(v, o, None), {"braco_sup": [el(0, -1.5, 8.6, 7, _g(o), LINHA, 1.5)]})


def _homem_aranha(g):
    v, a = "$c1", "$c2"
    web = [traco(f"M 0 -96 L {x} -8", "$c3", 1.2, o=0.55) for x in (-44, -26, -9, 9, 26, 44)]
    web += [traco(f"M {-50 * k:.0f} {-48 - 44 * k:.0f} Q 0 {-34 - 64 * k:.0f} {50 * k:.0f} {-48 - 44 * k:.0f}", "$c3", 1.2, o=0.5) for k in (0.3, 0.55, 0.8)]
    aranha = [pa("M -3 -30 L 3 -30 L 4 -20 L -4 -20 Z", "$c3"), el(0, -32, 2.6, 2.8, "$c3"),
              *[traco(f"M 0 -25 L {sx * 12} {y}", "$c3", 1.6) for sx in (-1, 1) for y in (-34, -27, -21)]]
    return _junta(
        {"torso": [tronco(g, v), lado(g, -13, a), espelhar(lado(g, -13, a)), *aranha,
                   *[traco(f"M {x} -44 L {x * 0.6:.0f} 5", "$c3", 1, o=0.4) for x in (-6, 6)]],
         "perna": [calca(a), *bota_alta(v, 31)],
         "mao": luva(v),
         "mascara_baixo": [cabeca_cheia(v), *web],
         "mascara_cima": []},
        manga(v, v, None), {"braco_inf": [rr(-6.1, 10, 12.2, 10, 4.5, _gh(a), LINHA, 1.4)]})


def _capitao_america(g):
    az, ve, br = "$c1", "$c2", "$c3"
    listras = [rr(-19 + 0.5 * i, -14 + 4.4 * i, 38 - i, 2.7, 0, ve if i % 2 == 0 else br, None) for i in range(5)]
    return _junta(
        {"torso": [tronco(g, az), estrela(0, -27, 9.5, br), *listras, *cinto("$c4", "$c5")],
         "perna": [calca(az), *bota_alta(ve, 26, borda=br)],
         "mao": luva("$c4"),
         "mascara_baixo": [capuz(az, -30, -68)],
         "mascara_cima": [*par(pa("M -50 -64 L -66 -76 L -58 -58 L -68 -64 L -52 -48 Z", br, LINHA, 1.2))]},
        manga(az, az, "$c4"),
        {"adereco_e": [el(-3, 12, 15.5, 15.5, _g(ve), LINHA, 1.8), el(-3, 12, 11, 11, br, None), el(-3, 12, 6.8, 6.8, az, None),
                       estrela(-3, 12, 5.6, br)]})


def _thor(g):
    m, p, c = "$c1", "$c2", "$c3"
    disco = [el(x, -25, 4, 4, _g(p), LINHA, 1.2) for x in (-11, 11)]
    return _junta(
        {"torso": [tronco(g, m), pa("M -17 -41 Q 0 -32 17 -41 L 13 -12 Q 0 -6 -13 -12 Z", _g(p), LINHA, 1.4), *disco,
                   el(0, -26, 5, 5, _g(c), LINHA, 1.2), *cinto("#3B2F38", p)],
         "capa": capa(c, 84, 46),
         "perna": [calca("#2E3446"), rr(-8.2, 18, 16.4, 8, 3, _g(p), LINHA, 1.3), *bota_alta("#3B2F38", 30, borda=p)],
         "mao": luva(p),
         "adereco_d": direita([rr(-2.1, 0, 4.2, 24, 1.6, "#6B4A2E", LINHA, 1.2), rr(-11, -12, 22, 15, 2.6, _g("#9AA3B2"), LINHA, 1.6),
                               traco("M -8 -8 L 8 -8", "#DDE3EE", 1.6, o=0.6)])},
        manga("#2E3446", p, p), {"braco_sup": [el(0, -1.5, 8, 6.6, _g(p), LINHA, 1.5)]})


def _hulk(g):
    calca_ = "$c1"
    rasgo = "M -8.2 26 L -5 23 L -2 27 L 1 23 L 4 27 L 8.2 24 L 8.2 32 L -8.2 32 Z"
    return _junta(
        {"torso": [traco("M -12 -34 Q 0 -27 12 -34", "$pele--", 1.8, o=0.7), traco("M 0 -30 L 0 -16", "$pele--", 1.6, o=0.5),
                   traco("M -10 -12 L 10 -12", "$pele--", 1.4, o=0.4), traco("M -10 -6 L 10 -6", "$pele--", 1.4, o=0.4),
                   pa("M -22 -2 Q 0 4 22 -2 L 21.5 6 Q 13 8 0 8 Q -13 8 -21.5 6 Z", _g(calca_), LINHA, 1.6)],
         "perna": [rr(-8, -4, 16, 40, 7, _gh(calca_), LINHA, 1.6), pa("M -8 36 L -5 32 L -2 37 L 1 32 L 4 37 L 8 33 L 8 40 L -8 40 Z", calca_ + "--", None)],
         },
        {})


def _pantera_negra(g):
    n, s = "$c1", "$c2"
    return _junta(
        {"torso": [tronco(g, n), pa("M -16 -44 L 0 -30 L 16 -44 L 12 -44 L 0 -35 L -12 -44 Z", _g(s), LINHA, 1.2),
                   traco("M -20 -16 L 0 -10 L 20 -16", s, 2, o=0.7), *cinto("#23212B", s)],
         "perna": [calca(n), *bota_alta(n, 27, borda=s)],
         "mao": luva(n) + [*[traco(f"M {x} 8 L {x * 1.15:.1f} 17", "#DDE3EE", 1.8) for x in (-3, 0, 3)]],
         "mascara_baixo": [cabeca_cheia(n), traco("M -30 -60 Q -20 -30 -12 -14", s, 1.6, o=0.5), traco("M 30 -60 Q 20 -30 12 -14", s, 1.6, o=0.5)],
         "mascara_cima": [*orelha_pontuda(30, 20, n)]},
        manga(n, n, s), {"braco_inf": [rr(-6.5, 11, 13, 4, 1.8, s, None)]})


def _viuva_negra(g):
    n, l = "$c1", "$c2"
    return _junta(
        {"torso": [tronco(g, n), traco("M -17 -38 Q -8 -30 0 -44", "$c3", 1.4, o=0.6), traco("M 17 -38 Q 8 -30 0 -44", "$c3", 1.4, o=0.6),
                   traco("M -20 -20 L 20 -14", "#4A4652", 1.6, o=0.9), *cinto("#3A3540", l), rr(-21, -3, 42, 3, 1.2, "#4A4652", None)],
         "perna": [calca(n), rr(-8.4, 10, 16.8, 14, 6, _gh("#2A2730"), LINHA, 1.4), *bota_alta("#26232C", 29)],
         "mao": luva("#26232C")},
        manga(n, n, None), {"braco_inf": [rr(-6.6, 12, 13.2, 7, 3, _gh(l), LINHA, 1.4), *[el(x, 15.5, 1.1, 1.1, "#FFD8B0") for x in (-3.4, 0, 3.4)]]})


def _doutor_estranho(g):
    az, ve, ou = "$c1", "$c2", "$c3"
    return _junta(
        {"torso": [tronco(g, az), pa("M -12 -45 L 0 -20 L 12 -45 L 8 -45 L 0 -32 L -8 -45 Z", _g(ve), LINHA, 1.2),
                   *cinto("#8A5A2E", ou), el(0, -24, 6.6, 6.6, _g(ou), LINHA, 1.4), el(0, -24, 3.4, 3.4, "#57D68D", LINHA, 1)],
         "capa": [*capa(ve, 84, 46, borda=ou), pa("M -21 2 L -32 -12 Q -24 -6 -8 0 Z", _g(ve + "-"), LINHA, 1.4), pa("M 21 2 L 32 -12 Q 24 -6 8 0 Z", _g(ve + "-"), LINHA, 1.4)],
         "perna": [calca("#2A2436"), *bota_alta("#6B4A2E", 29)],
         "mao": luva("#8A5A2E")},
        manga(az, az, "#8A5A2E"), {"braco_sup": [el(0, -1.5, 7.6, 6.4, _g(ve), LINHA, 1.4)]})


def _deadpool(g):
    v, p = "$c1", "$c2"
    return _junta(
        {"torso": [tronco(g, v), lado(g, -14, p), espelhar(lado(g, -14, p)), traco("M -20 -40 L 18 4", "#4A3A40", 3), traco("M 20 -40 L -18 4", "#4A3A40", 3),
                   *cinto(p, "#8C8C99")],
         "capa": [rr(-30, 0, 5, 44, 2.4, "#3B3B46", LINHA, 1.2), rr(25, 0, 5, 44, 2.4, "#3B3B46", LINHA, 1.2)],
         "perna": [calca(v), rr(-7.9, 24, 15.8, 4, 0, p, None), *bota_alta(p, 30)],
         "mao": luva(p),
         "mascara_baixo": [cabeca_cheia(v), *par(pa("M -13 -56 Q -40 -62 -40 -34 Q -36 -22 -16 -30 Q -6 -44 -13 -56 Z", p, LINHA, 1.4))]},
        manga(v, v, p))


def _wolverine(g):
    am, az = "$c1", "$c2"
    garras = [traco(f"M {x} 8 L {x * 1.4:.1f} 26", "#E4E8F2", 2.4) for x in (-3.4, 0, 3.4)] + [
        traco(f"M {x} 8 L {x * 1.4:.1f} 26", "#7A8296", 0.9, o=0.7) for x in (-3.4, 0, 3.4)]
    return _junta(
        {"torso": [tronco(g, am), lado(g, -12, az), espelhar(lado(g, -12, az)), traco("M -11 -44 L -6 -18", az, 2), traco("M 11 -44 L 6 -18", az, 2),
                   *cinto("#3B2F38", "#C9A227")],
         "perna": [calca(az), *bota_alta(am, 28, borda=az)],
         "mao": [*garras, *luva(am)],
         "mascara_baixo": [capuz(az, -36, -64)],
         "mascara_cima": [*orelha_pontuda(30, 24, az), traco("M -20 -80 L -8 -66", am, 3), traco("M 20 -80 L 8 -66", am, 3)]},
        manga(am, am, az))


def _capita_marvel(g):
    az, ve, ou = "$c1", "$c2", "$c3"
    return _junta(
        {"torso": [tronco(g, az), pa("M -21 -20 L 21 -14 L 21 2 L -21 2 Z", _g(ve), None), estrela(0, -28, 9.5, ou, 8, 0.5),
                   *cinto(ou, None)],
         "perna": [calca(az), *bota_alta(ve, 27, borda=ou)],
         "mao": luva(ve),
         "capa": []},
        manga(az, az, ou), {"braco_inf": [rr(-6.4, 9, 12.8, 11, 4, _gh(ve), LINHA, 1.4)]})


def _homem_formiga(g):
    v, p = "$c1", "$c2"
    return _junta(
        {"torso": [tronco(g, v), pa("M -21 -22 L 21 -22 L 22 -14 L -22 -14 Z", _g(p), None, 0, o=0.9), el(0, -28, 6, 3.6, p, None), el(-4.5, -28, 3.6, 3.6, p), el(4.5, -28, 3.6, 3.6, p),
                   *cinto("#3B3B46", p)],
         "perna": [calca("#3B3B46"), *bota_alta(v, 28, borda=p)],
         "mao": luva(p),
         "mascara_baixo": [cabeca_cheia(p)],
         "mascara_cima": [*par(el(-42, -58, 5, 12, _g(v), LINHA, 1.4)), el(0, -84, 5, 4, v, None)]},
        manga(v, v, p))


_MARVEL = {
    "homem_de_ferro": ("Homem de Ferro", {"c1": "#C4262E", "c2": "#F2C94C", "c3": "#9BEFFF", "lente": "#F4FBFF", "boca_linha": "#7A5A10", "boca_dentro": "#4A3208", "lingua": "#8A5A10"},
                       ["cabelo", "sobr", "acessorio"], "visor", None, _homem_de_ferro),
    "homem_aranha": ("Homem-Aranha", {"c1": "#D3202F", "c2": "#1F3F94", "c3": "#251419", "lente": "#F6F6FA", "boca_linha": "#8A121C", "boca_dentro": "#5A0B12", "lingua": "#B23040"},
                     ["cabelo", "sobr", "acessorio"], "lente", None, _homem_aranha),
    "capitao_america": ("Capitão América", {"c1": "#2D4BA8", "c2": "#C9202E", "c3": "#F4F4F8", "c4": "#7A4A2E", "c5": "#F2C94C"},
                        ["cabelo", "acessorio"], "normal", None, _capitao_america),
    "thor": ("Thor", {"c1": "#3C4A63", "c2": "#B7BFCC", "c3": "#C6303A", "cabelo": "#E7C36A"}, [], "normal", "longo", _thor),
    "hulk": ("Hulk", {"c1": "#7A4FA8", "pele": "#6FBF4A", "cabelo": "#2B2226"}, [], "normal", "espetado", _hulk),
    "pantera_negra": ("Pantera Negra", {"c1": "#23212B", "c2": "#B9B4D8", "lente": "#F6F6FA", "boca_linha": "#5A5470", "boca_dentro": "#2A2836", "lingua": "#6E6890"},
                      ["cabelo", "sobr", "acessorio"], "lente", None, _pantera_negra),
    "viuva_negra": ("Viúva Negra", {"c1": "#2A2830", "c2": "#E8632B", "c3": "#5A5560", "cabelo": "#B8502B"}, [], "normal", None, _viuva_negra),
    "doutor_estranho": ("Doutor Estranho", {"c1": "#2D5FA6", "c2": "#C22B2B", "c3": "#F2C94C", "cabelo": "#2B2226"}, [], "normal", "social", _doutor_estranho),
    "deadpool": ("Deadpool", {"c1": "#C4202A", "c2": "#1E1A22", "lente": "#F6F6FA", "boca_linha": "#7A1218", "boca_dentro": "#4A0A10", "lingua": "#A02030"},
                 ["cabelo", "sobr", "acessorio"], "lente", None, _deadpool),
    "wolverine": ("Wolverine", {"c1": "#F2C31E", "c2": "#2447A0"}, ["cabelo", "acessorio"], "normal", None, _wolverine),
    "capita_marvel": ("Capitã Marvel", {"c1": "#2B3F9E", "c2": "#D62B33", "c3": "#F2C94C", "cabelo": "#E7C36A"}, [], "normal", None, _capita_marvel),
    "homem_formiga": ("Homem-Formiga", {"c1": "#C4262E", "c2": "#C9CFDB", "lente": "#1B1622"}, ["cabelo", "sobr", "acessorio"], "lente", None, _homem_formiga),
}


def _monta(tabela: dict, universo: str) -> dict:
    saida = {}
    for id_, (nome, cores, esconde, olhos, cabelo, fabrica) in tabela.items():
        d = {"nome": nome, "universo": universo, "cores": dict(cores), "esconde": esconde, "olhos": olhos,
             "pecas": {"m": fabrica("m"), "f": fabrica("f")}}
        if cabelo:
            d["forca_cabelo"] = cabelo
        saida[id_] = d
    return saida


TRAJES: dict = _monta(_MARVEL, "Marvel")
