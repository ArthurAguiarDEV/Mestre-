"""Roupas do dia a dia. Cada roupa tem `pecas` por gênero ("m"/"f"): slot -> primitivas, desenhadas POR CIMA do corpo.

Cores: $r1 = peça principal (camisa, blusão...), $r2 = detalhe (gravata, faixa, solado...), $r3 = parte de baixo
(calça, saia, short). `cores` = sugestão que o painel aplica ao escolher a roupa.
Slots: torso, braco_sup, braco_inf, mao, perna (lado esquerdo; o direito é o espelho).
"""
from .arte import el, pa, rr, traco
from .catalogo_corpo import TORSO_D, segmento

LINHA = "$linha"


def _g(cor: str) -> list:
    return ["v", cor + "+", cor + "-"]


def _gh(cor: str) -> list:
    return ["h", cor + "-", cor + "+"]


def tronco(g: str, cor: str = "$r1") -> dict:
    return pa(TORSO_D[g], _g(cor), LINHA, 1.8)


def gola_redonda(cor: str = "$r1") -> list:
    return [pa("M -8 -45 Q 0 -35 8 -45 Q 0 -41 -8 -45 Z", cor + "--", LINHA, 1.4)]


def manga_curta(cor: str = "$r1") -> dict:
    return {"braco_sup": [rr(-6.6, -5.5, 13.2, 15, 6, _gh(cor), LINHA, 1.6)]}


def manga_longa(cor: str = "$r1", punho: str | None = "$r2") -> dict:
    d = {"braco_sup": segmento(6.6, _gh(cor)), "braco_inf": segmento(6.1, _gh(cor))}
    if punho:
        d["braco_inf"].append(rr(-6.3, 13.4, 12.6, 6, 2.6, _gh(punho), LINHA, 1.4))
    return d


def calca(cor: str = "$r3", ate: float = 44) -> dict:
    return rr(-7.9, -4, 15.8, ate + 4, 7.2, _gh(cor), LINHA, 1.6)


def tenis(cor: str = "$r2") -> list:
    return [rr(-10.6, 40.5, 20.4, 11.6, 5.6, ["v", "$branco", "#D9D9E4"], LINHA, 1.6),
            rr(-10.6, 48.2, 20.4, 4.6, 2.3, cor, LINHA, 1.3),
            traco("M -6.5 44.6 L 2.5 44.6", "#9A9AAE", 1.6), traco("M -6 47 L 2 47", "#9A9AAE", 1.4)]


def sapato(cor: str = "#2E2530") -> list:
    return [rr(-10.6, 41, 20.4, 11, 5.4, ["v", cor + "", cor], LINHA, 1.6),
            rr(-10.6, 49, 20.4, 3.8, 1.9, "#151015", LINHA, 1.2),
            el(-4.5, 44.6, 4.2, 1.6, "#FFFFFF", None, 0, 0.35)]


def bota(cor: str = "#3B2F38") -> list:
    return [rr(-9.6, 30, 19.2, 22, 6, _gh(cor), LINHA, 1.6),
            rr(-11, 48, 22, 5, 2.4, "#1A1216", LINHA, 1.3),
            traco("M -9 36 L 9 36", "#FFFFFF", 1.6, o=0.25)]


def _junta(*partes) -> dict:
    """Mescla dicionários slot -> lista (na ordem: o que vem depois desenha por cima)."""
    saida: dict = {}
    for p in partes:
        for slot, prims in p.items():
            saida.setdefault(slot, []).extend(prims)
    return saida


def _camiseta(g):
    return _junta(
        {"torso": [tronco(g), *gola_redonda(), traco("M -21 -8 Q 0 -4 21 -8", "$r1--", 1.2, o=0.5)],
         "perna": [calca(), *tenis()]}, manga_curta())


def _moletom(g):
    return _junta(
        {"torso": [tronco(g), pa("M -17 -44 Q -22 -30 -12 -25 Q 0 -20 12 -25 Q 22 -30 17 -44 Q 0 -36 -17 -44 Z", "$r1--", LINHA, 1.6),
                   traco("M -4 -33 L -5 -18", "$r2", 2.2), traco("M 4 -33 L 5 -18", "$r2", 2.2),
                   pa("M -14 -9 L 14 -9 L 17 3 L -17 3 Z", _g("$r1-"), LINHA, 1.4)],
         "perna": [calca(), rr(-8.4, 34, 16.8, 6, 3, "$r3--", LINHA, 1.3), *tenis()]}, manga_longa("$r1", "$r1--"))


def _blazer_paineis(g):
    w = 23 if g == "m" else 20
    esq = (f"M {-w} -38 Q {-w} -45 -15 -45 L -8 -45 L -1 -22 L -3 6 L -13 6 Q -21 6 -21 0 Z")
    dir_ = (f"M {w} -38 Q {w} -45 15 -45 L 8 -45 L 1 -22 L 3 6 L 13 6 Q 21 6 21 0 Z")
    return [pa(esq, _g("$r1"), LINHA, 1.8), pa(dir_, _g("$r1"), LINHA, 1.8),
            pa("M -8 -45 L -1 -22 L -12 -30 Z", "$r1--", LINHA, 1.2), pa("M 8 -45 L 1 -22 L 12 -30 Z", "$r1--", LINHA, 1.2),
            el(0, -8, 1.8, 1.8, "#F2C94C")]


def _social(g):
    return _junta(
        {"torso": [pa(TORSO_D[g], _g("$branco"), LINHA, 1.8),
                   pa("M -3.6 -44 L 3.6 -44 L 5 -33 L 0 -12 L -5 -33 Z", _g("$r2"), LINHA, 1.3),
                   *_blazer_paineis(g)],
         "perna": [calca("$r3"), *sapato()]}, manga_longa("$r1", "$branco"))


def _vestido(g):
    saia = pa("M -16 -18 Q -19 0 -29 32 Q 0 40 29 32 Q 19 0 16 -18 Z", _g("$r1"), LINHA, 1.8)
    return _junta(
        {"torso": [saia, tronco(g), *gola_redonda(), rr(-16.6, -17, 33.2, 5.4, 2.4, _g("$r2"), LINHA, 1.4),
                   traco("M -24 30 Q 0 37 24 30", "$r2", 2.2, o=0.9)],
         "perna": [rr(-7.6, 14, 15.2, 32, 6.5, ["h", "#E9E9F2", "#FFFFFF"], LINHA, 1.5),
                   rr(-10.4, 41.5, 20, 10.5, 5.2, _g("$r3"), LINHA, 1.6), traco("M -9 43.5 L 7 43.5", "#FFFFFF", 1.4, o=0.5)]},
        {"braco_sup": [rr(-6.9, -5.6, 13.8, 12.5, 6.2, _gh("$r1"), LINHA, 1.6)]})


def _esporte(g):
    return _junta(
        {"torso": [tronco(g), pa("M -8 -45 Q 0 -34 8 -45 Q 0 -41 -8 -45 Z", "$r2", LINHA, 1.4),
                   pa("M -20 -29 L 20 -29 L 19.5 -23 L -19.5 -23 Z", "$r2", None, 0, 0.92),
                   traco("M -19 -38 Q -13 -36 -9 -44", LINHA, 1.4, o=0.6), traco("M 19 -38 Q 13 -36 9 -44", LINHA, 1.4, o=0.6)],
         "braco_sup": [rr(-5.8, -5, 11.6, 8, 4, _gh("$r1"), None, 0)],
         "perna": [rr(-7.6, 16, 15.2, 30, 6.5, ["h", "#E9E9F2", "#FFFFFF"], LINHA, 1.5),
                   calca("$r3", 24), rr(-7.9, 14, 15.8, 3.4, 1.4, "$r2", None),
                   *tenis("$r2")]})


def _jaqueta(g):
    w = 23 if g == "m" else 20
    esq = f"M {-w} -38 Q {-w} -45 -15 -45 L -6 -45 L -3 -16 L -3.5 6 L -13 6 Q -21 6 -21 0 Z"
    dir_ = f"M {w} -38 Q {w} -45 15 -45 L 6 -45 L 3 -16 L 3.5 6 L 13 6 Q 21 6 21 0 Z"
    return _junta(
        {"torso": [pa(TORSO_D[g], _g("$r2"), LINHA, 1.8), pa(esq, _g("$r1"), LINHA, 1.8), pa(dir_, _g("$r1"), LINHA, 1.8),
                   pa("M -15 -45 L -6 -45 L -13 -34 Z", "$r1--", LINHA, 1.2), pa("M 15 -45 L 6 -45 L 13 -34 Z", "$r1--", LINHA, 1.2),
                   traco("M 0 -40 L 0 6", "#C9CBD6", 1.5), el(0, -36, 1.8, 1.8, "#C9CBD6")],
         "perna": [calca("$r3"), *bota()]}, manga_longa("$r1", "$r1--"))


def _jaleco(g):
    casaco = pa("M -24 -38 Q -24 -45 -15 -45 L -6 -45 L -2 -18 L -3 33 Q -18 36 -30 32 Q -24 12 -22 -2 Z", _g("$r1"), LINHA, 1.8)
    casaco_d = pa("M 24 -38 Q 24 -45 15 -45 L 6 -45 L 2 -18 L 3 33 Q 18 36 30 32 Q 24 12 22 -2 Z", _g("$r1"), LINHA, 1.8)
    return _junta(
        {"torso": [pa(TORSO_D[g], _g("$r2"), LINHA, 1.8), casaco, casaco_d,
                   pa("M -15 -45 L -6 -45 L -12 -32 Z", "$r1--", LINHA, 1.2), pa("M 15 -45 L 6 -45 L 12 -32 Z", "$r1--", LINHA, 1.2),
                   rr(-19, 8, 12, 9, 2, _g("$r1-"), LINHA, 1.2), rr(7, 8, 12, 9, 2, _g("$r1-"), LINHA, 1.2),
                   rr(-16, -32, 3, 12, 1.4, "#4A9CE8", None), traco("M 0 -12 L 0 33", LINHA, 1.2, o=0.4)],
         "perna": [calca("$r3"), *sapato()]}, manga_longa("$r1", "$r1--"))


def _camisa(g):
    return _junta(
        {"torso": [tronco(g), traco("M 0 -42 L 0 6", "$r1--", 1.4),
                   pa("M -13 -45 L -1 -45 L -2 -30 Z", "$r1+", LINHA, 1.2), pa("M 13 -45 L 1 -45 L 2 -30 Z", "$r1+", LINHA, 1.2),
                   *[el(0, y, 1.5, 1.5, "$r1--") for y in (-24, -13, -2)]],
         "perna": [calca("$r3"), *sapato("#5A4034")]},
        {"braco_sup": segmento(6.6, _gh("$r1")),
         "braco_inf": [*segmento(6.1, _gh("$r1"), ate=2), rr(-6.6, 2.2, 13.2, 5.6, 2.6, _gh("$r1-"), LINHA, 1.4)]})


# --- mais roupas (2ª rodada, 30/09) ---------------------------------------------------------------------------------
def pernas_de_fora(ate: float = 22, cor: str = "$r3") -> list:
    """Bermuda/short até `ate` (a perna de pele aparece embaixo)."""
    return [rr(-7.9, -4, 15.8, ate + 4, 6.4, _gh(cor), LINHA, 1.6), traco(f"M -7 {ate - 3} L 7 {ate - 3}", cor + "--", 1.2, o=0.5)]


def _regata(g):
    cava = [pa("M -23.6 -38 Q -23.6 -46 -15 -46 L -11 -46 Q -12 -34 -21.4 -28 Z", ["h", "$pele-", "$pele"], LINHA, 1.4),
            pa("M 23.6 -38 Q 23.6 -46 15 -46 L 11 -46 Q 12 -34 21.4 -28 Z", ["h", "$pele", "$pele-"], LINHA, 1.4)]
    return {"torso": [tronco(g), *cava, pa("M -10 -45 Q 0 -32 10 -45 Q 0 -40 -10 -45 Z", "$r1--", LINHA, 1.2)],
            "perna": [*pernas_de_fora(20), *tenis()]}


def _listrada(g):
    listras = [rr(-22, y, 44, 3.6, 0, "$r2", None, 0, 0.92) for y in (-36, -27, -18, -9, 0)]
    return _junta(
        {"torso": [tronco(g), *listras, pa(TORSO_D[g], None, LINHA, 1.8), *gola_redonda()],
         "perna": [calca(), *tenis()]},
        manga_curta(), {"braco_sup": [rr(-6.6, 1, 13.2, 3, 0, "$r2", None), traco("M -6.2 9 Q 0 11 6.2 9", LINHA, 1.4)]})


def _sueter(g):
    losangos = [pa(f"M {x} -24 L {x + 4} -19 L {x} -14 L {x - 4} -19 Z", "$r2", None) for x in (-15, -5, 5, 15)]
    return _junta(
        {"torso": [tronco(g), rr(-21, -26, 42, 14, 0, "$r1-", None, 0, 0.5), *losangos,
                   pa("M -11 -45 Q 0 -36 11 -45 L 9 -41 Q 0 -33 -9 -41 Z", "$r1-", LINHA, 1.2),
                   *[traco(f"M {x} -1 L {x} 5", "$r1--", 1.1, o=0.6) for x in range(-16, 18, 4)]],
         "perna": [calca(), *sapato("#5A4034")]}, manga_longa("$r1", "$r1-"))


def _jardineira(g):
    peito = pa("M -14 -30 L 14 -30 L 16 6 L -16 6 Z", _g("$r3"), LINHA, 1.6)
    return _junta(
        {"torso": [tronco(g, "$r1"), *gola_redonda(), peito, rr(-7, -25, 14, 9, 2, "$r3-", LINHA, 1.2),
                   traco("M -12 -30 L -17 -44", "$r3-", 3.4), traco("M 12 -30 L 17 -44", "$r3-", 3.4),
                   el(-12.4, -28.6, 1.9, 1.9, "$r2", LINHA, 1), el(12.4, -28.6, 1.9, 1.9, "$r2", LINHA, 1)],
         "perna": [calca("$r3"), rr(-8.6, 36, 17.2, 5, 2.4, "$r3-", LINHA, 1.2), *tenis("$r2")]}, manga_curta("$r1"))


def _quimono(g):
    esq = pa("M -21 -38 Q -21 -45 -14 -45 L -6 -45 L 8 -14 L 2 6 L -13 6 Q -21 6 -21 0 Z", _g("$r1"), LINHA, 1.8)
    dir_ = pa("M 21 -38 Q 21 -45 14 -45 L 6 -45 L -4 -26 L -1 6 L 13 6 Q 21 6 21 0 Z", _g("$r1"), LINHA, 1.8)
    return _junta(
        {"torso": [tronco(g, "$r1-"), dir_, esq, rr(-22, -8, 44, 6.6, 2.4, _g("$r2"), LINHA, 1.4),
                   pa("M -4 -3 L -9 12 L -4 11 L -1 -2 Z", "$r2", LINHA, 1.1), pa("M 3 -3 L 7 12 L 2 11 L 0 -2 Z", "$r2", LINHA, 1.1)],
         "perna": [rr(-9, -4, 18, 46, 7, _gh("$r1"), LINHA, 1.6), el(-1.5, 47, 9, 5.4, "$pele", LINHA, 1.6)]},
        {"braco_sup": segmento(7.4, _gh("$r1")), "braco_inf": [*segmento(7, _gh("$r1"), ate=8), traco("M -7 14 Q 0 16 7 14", LINHA, 1.4)]})


def _marinheiro(g):
    gola = pa("M -18 -45 L -22 -30 L -8 -30 L 0 -18 L 8 -30 L 22 -30 L 18 -45 L 8 -45 L 0 -34 L -8 -45 Z", _g("$r2"), LINHA, 1.5)
    baixo = ({"perna": [rr(-8.6, 14, 17.2, 32, 6.5, ["h", "#E9E9F2", "#FFFFFF"], LINHA, 1.5), *sapato("#3B2F38")],
              "torso": [pa("M -17 -4 Q -21 10 -27 24 Q 0 30 27 24 Q 21 10 17 -4 Z", _g("$r2"), LINHA, 1.6),
                        *[traco(f"M {x} -2 L {x * 1.5:.1f} 25", "$r2--", 1.1, o=0.5) for x in (-10, -3, 4, 11)]]}
             if g == "f" else {"perna": [calca("$r2"), *sapato("#3B2F38")], "torso": []})
    return _junta(
        {"torso": [*baixo["torso"], tronco(g, "$branco"), gola, traco("M -20 -32 L -9 -32", "$branco", 1.2, o=0.8),
                   traco("M 20 -32 L 9 -32", "$branco", 1.2, o=0.8), pa("M 0 -24 L -7 -19 L -6 -14 L 0 -19 L 6 -14 L 7 -19 Z", "$r1", LINHA, 1.2)],
         "perna": baixo["perna"]}, manga_curta("$branco"), {"braco_sup": [rr(-6.6, 3.5, 13.2, 3, 1, "$r2", None)]})


def _pijama(g):
    bolinhas = [el(x, y, 1.8, 1.8, "$r2", None, 0, 0.9) for x, y in ((-12, -34), (6, -38), (14, -24), (-6, -20), (-15, -8), (4, -6), (12, 0))]
    return _junta(
        {"torso": [tronco(g), *bolinhas, pa("M -10 -45 L 0 -34 L 10 -45 L 6 -45 L 0 -39 L -6 -45 Z", "$r2", LINHA, 1.2),
                   *[el(0, y, 1.3, 1.3, "$r1--") for y in (-28, -18, -8)]],
         "perna": [calca("$r1"), el(-2, 10, 1.8, 1.8, "$r2"), el(3, 24, 1.8, 1.8, "$r2"), el(-3, 34, 1.8, 1.8, "$r2"),
                   rr(-9, 42, 18, 10, 5, _g("$r3"), LINHA, 1.5), el(-1, 44, 4, 2.4, "$r3+", None, 0, 0.8)]},
        manga_longa("$r1", "$r2"))


def _colete(g):
    w = 22 if g == "m" else 19
    esq = f"M {-w} -36 Q {-w} -44 -14 -44 L -9 -44 L -2 -22 L -2 6 L -13 6 Q -20 6 -20 0 Z"
    dir_ = f"M {w} -36 Q {w} -44 14 -44 L 9 -44 L 2 -22 L 2 6 L 13 6 Q 20 6 20 0 Z"
    return _junta(
        {"torso": [pa(TORSO_D[g], _g("$branco"), LINHA, 1.8), pa("M -9 -45 L -1 -45 L -2 -36 Z", "#FFFFFF", LINHA, 1.1),
                   pa("M 9 -45 L 1 -45 L 2 -36 Z", "#FFFFFF", LINHA, 1.1), pa(esq, _g("$r1"), LINHA, 1.6), pa(dir_, _g("$r1"), LINHA, 1.6),
                   *[el(-3.6, y, 1.4, 1.4, "$r2") for y in (-18, -10, -2)], pa("M -3 -44 L 3 -44 L 1.6 -30 L -1.6 -30 Z", "$r2", LINHA, 1.1)],
         "perna": [calca("$r3"), *sapato()]},
        {"braco_sup": segmento(6.6, _gh("$branco")), "braco_inf": [*segmento(6.1, _gh("$branco"), ate=2),
                                                                   rr(-6.6, 2.2, 13.2, 5.6, 2.6, _gh("$branco"), LINHA, 1.4)]})


def _saia(g):
    saia = pa("M -18 -8 Q -22 8 -28 24 Q 0 32 28 24 Q 22 8 18 -8 Z", _g("$r3"), LINHA, 1.8)
    return _junta(
        {"torso": [saia, *[traco(f"M {x} -6 L {x * 1.45:.1f} 26", "$r3--", 1.1, o=0.5) for x in (-11, -4, 3, 10)],
                   pa("M -21 -38 Q -21 -45 -14 -45 L 14 -45 Q 21 -45 21 -38 L 19 -6 L -19 -6 Z", _g("$r1"), LINHA, 1.8),
                   pa("M -8 -45 Q 0 -38 8 -45 Q 0 -42 -8 -45 Z", "$r1--", LINHA, 1.2), rr(-19.5, -9, 39, 4.6, 2, "$r2", LINHA, 1.2)],
         "perna": [rr(-7.6, 16, 15.2, 30, 6.5, ["h", "$pele-", "$pele+"], LINHA, 1.5),
                   rr(-10.4, 41.5, 20, 10.5, 5.2, _g("$r2"), LINHA, 1.6)]},
        {"braco_sup": [rr(-6.9, -5.6, 13.8, 12, 6.2, _gh("$r1"), LINHA, 1.6)]})


def _vestido_festa(g):
    saia = pa("M -15 -16 Q -20 10 -34 50 Q 0 60 34 50 Q 20 10 15 -16 Z", _g("$r1"), LINHA, 1.8)
    brilho = [el(x, y, 1.3, 1.3, "#FFFFFF", None, 0, 0.8) for x, y in ((-12, 10), (8, 22), (-20, 36), (16, 40), (0, 32), (-4, 4))]
    return _junta(
        {"torso": [saia, *brilho, traco("M -30 48 Q 0 57 30 48", "$r1--", 1.6, o=0.6),
                   pa("M -19 -32 Q -10 -38 0 -32 Q 10 -38 19 -32 L 16 -14 L -16 -14 Z", _g("$r1"), LINHA, 1.6),
                   rr(-16.6, -17, 33.2, 4.4, 2, "$r2", LINHA, 1.2), el(0, -15, 3, 3, "$r2+", LINHA, 1.1)],
         "perna": [rr(-9.4, 44, 18.8, 9, 4.5, _g("$r3"), LINHA, 1.5)]})


ROUPAS: dict = {
    "camiseta": {"nome": "Camiseta e jeans", "cores": ["azul", "vermelho", "marinho"]},
    "listrada": {"nome": "Camiseta listrada", "cores": ["branco", "marinho", "azul"]},
    "regata": {"nome": "Regata e bermuda", "cores": ["amarelo", "branco", "azul"]},
    "moletom": {"nome": "Moletom", "cores": ["cinza", "laranja", "preto"]},
    "sueter": {"nome": "Suéter", "cores": ["vinho", "bege", "marrom"]},
    "camisa": {"nome": "Camisa social", "cores": ["branco", "marrom", "marinho"]},
    "colete": {"nome": "Colete", "cores": ["cinza", "vinho", "preto"]},
    "social": {"nome": "Terno", "cores": ["preto", "vermelho", "preto"]},
    "jaqueta": {"nome": "Jaqueta de couro", "cores": ["preto", "branco", "marinho"]},
    "jardineira": {"nome": "Jardineira", "cores": ["amarelo", "vermelho", "azul"]},
    "esporte": {"nome": "Esporte", "cores": ["vermelho", "branco", "preto"]},
    "quimono": {"nome": "Quimono de luta", "cores": ["branco", "preto", "branco"]},
    "jaleco": {"nome": "Jaleco", "cores": ["branco", "azul", "cinza"]},
    "marinheiro": {"nome": "Marinheiro", "cores": ["vermelho", "marinho", "branco"]},
    "pijama": {"nome": "Pijama", "cores": ["azul", "amarelo", "marinho"]},
    "vestido": {"nome": "Vestido", "cores": ["rosa", "branco", "vermelho"]},
    "saia": {"nome": "Blusa e saia", "cores": ["branco", "vermelho", "marinho"]},
    "vestido_festa": {"nome": "Vestido de festa", "cores": ["roxo", "dourado", "roxo"]},
}
_FABRICA = {"camiseta": _camiseta, "moletom": _moletom, "camisa": _camisa, "social": _social, "vestido": _vestido,
            "esporte": _esporte, "jaqueta": _jaqueta, "jaleco": _jaleco, "regata": _regata, "listrada": _listrada,
            "sueter": _sueter, "jardineira": _jardineira, "quimono": _quimono, "marinheiro": _marinheiro, "pijama": _pijama,
            "colete": _colete, "saia": _saia, "vestido_festa": _vestido_festa}
for _id, _f in _FABRICA.items():
    ROUPAS[_id]["pecas"] = {"m": _f("m"), "f": _f("f")}
