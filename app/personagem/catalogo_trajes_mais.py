"""Mais fantasias (2ª rodada, 30/09): heróis Marvel e DC que faltavam + fantasias clássicas (pirata, ninja, astronauta...).

Mesmo aviso de catalogo_trajes.py: versões INSPIRADAS, em cores e formas simples, sem logotipos oficiais, para uso
pessoal. As clássicas não são de ninguém. Formato da tabela: id -> (nome, cores, esconde, olhos, cabelo forçado, fábrica).
"""
from .arte import el, espelhar, pa, par, rr, traco
from .catalogo_corpo import TORSO_D
from .catalogo_roupas import LINHA, _g, _gh, _junta, calca, sapato
from .catalogo_trajes import (bota_alta, cabeca_cheia, capa, capuz, cinto, direita, estrela, lado, luva, manga,
                              orelha_pontuda, tronco)


def _teia(cor: str, o=0.55) -> list:
    """Linhas de teia na máscara (cabeça cheia)."""
    web = [traco(f"M 0 -96 L {x} -8", cor, 1.2, o=o) for x in (-44, -26, -9, 9, 26, 44)]
    web += [traco(f"M {-50 * k:.0f} {-48 - 44 * k:.0f} Q 0 {-34 - 64 * k:.0f} {50 * k:.0f} {-48 - 44 * k:.0f}", cor, 1.2, o=o)
            for k in (0.3, 0.55, 0.8)]
    return web


def _aranha_peito(cor: str) -> list:
    return [pa("M -3 -30 L 3 -30 L 4 -20 L -4 -20 Z", cor), el(0, -32, 2.6, 2.8, cor),
            *[traco(f"M 0 -25 L {sx * 12} {y}", cor, 1.6) for sx in (-1, 1) for y in (-34, -27, -21)]]


def _arco(cor="#6B4A2E") -> list:
    return [traco("M -2 -14 Q 12 10 -2 34", cor, 3), traco("M -2 -14 L -2 34", "#E8E8F0", 1, o=0.8)]


def _casaco(g: str, cor: str, ate=30, abre=4) -> list:
    """Casaco comprido aberto na frente (desenhado no torso, desce por cima das pernas)."""
    w = 24 if g == "m" else 21
    esq = f"M {-w} -38 Q {-w} -46 -15 -46 L {-abre - 3} -46 L {-abre} -16 L {-abre} {ate} Q -18 {ate + 3} -29 {ate - 1} Q -24 10 -22 -2 Z"
    return [pa(esq, _g(cor), LINHA, 1.8), pa(espelhar(pa(esq))["d"], _g(cor), LINHA, 1.8),
            pa(f"M -15 -46 L {-abre - 3} -46 L -13 -34 Z", cor + "--", LINHA, 1.2), pa(f"M 15 -46 L {abre + 3} -46 L 13 -34 Z", cor + "--", LINHA, 1.2)]


# --- MARVEL ---------------------------------------------------------------------------------------------------
def _miles(g):
    n, v = "$c1", "$c2"
    return _junta(
        {"torso": [tronco(g, n), *_aranha_peito(v), *[traco(f"M {x} -44 L {x * 0.6:.0f} 5", v, 1, o=0.55) for x in (-8, 8)],
                   traco("M -21 -26 Q 0 -20 21 -26", v, 1, o=0.45)],
         "perna": [calca(n), traco("M 0 -2 L 0 40", v, 1, o=0.4), *bota_alta(n, 34, sola=v)],
         "mao": luva(v), "mascara_baixo": [cabeca_cheia(n), *_teia(v)]},
        manga(n, n, None))


def _gwen(g):
    b, r, a = "$c1", "$c2", "$c3"
    return _junta(
        {"torso": [tronco(g, b), lado(g, -12, "#26232C"), espelhar(lado(g, -12, "#26232C")), *_aranha_peito("#26232C"),
                   traco("M -21 -30 Q -10 -34 -9 -44", r, 1.6, o=0.8), traco("M 21 -30 Q 10 -34 9 -44", r, 1.6, o=0.8)],
         "perna": [calca("#26232C"), rr(-7.9, 16, 15.8, 3, 1, a, None), *bota_alta(b, 33, sola=a)],
         "mao": luva(b),
         "mascara_baixo": [cabeca_cheia(b), *_teia("#9AA3B2", 0.45)],
         "mascara_cima": [capuz(b, -30, -70, r)]},
        manga("#26232C", b, None))


def _loki(g):
    ve, ou, n = "$c1", "$c2", "$c3"
    chifres = par(pa("M -24 -92 C -34 -118 -44 -136 -30 -150 C -30 -130 -22 -114 -12 -98 Z", _g(ou), LINHA, 1.8))
    return _junta(
        {"torso": [tronco(g, n), pa("M -18 -44 L 0 -20 L 18 -44 L 12 -44 L 0 -28 L -12 -44 Z", _g(ou), LINHA, 1.2),
                   lado(g, -12, ve), espelhar(lado(g, -12, ve)), *cinto(ou, ve)],
         "capa": capa(ve, 84, 46, borda=ou),
         "perna": [calca(n), rr(-8.4, 14, 16.8, 6, 2.4, _g(ou), LINHA, 1.2), *bota_alta(ve, 28, borda=ou)],
         "mao": luva(n),
         "mascara_cima": [capuz(ou, -40, -72), *chifres]},
        manga(ve, n, ou))


def _visao(g):
    ve, am, ou = "$c1", "$c2", "$c3"
    return _junta(
        {"torso": [tronco(g, ve), pa("M -21 -38 Q -21 -45 -14 -45 L 14 -45 Q 21 -45 21 -38 L 20 -20 L -20 -20 Z", _g("$pele"), None),
                   pa("M -12 -45 L 0 -30 L 12 -45", None, ou, 2), *cinto(ou, None),
                   *[traco(f"M {x} -20 L {x} 4", "$c1--", 1.2, o=0.5) for x in (-12, -4, 4, 12)]],
         "capa": capa(am, 80, 44),
         "perna": [calca(ve), *bota_alta(ve, 30, borda=ou)],
         "mao": luva(ve),
         "mascara_cima": [pa("M -4 -80 L 4 -80 L 6 -70 L 0 -64 L -6 -70 Z", ["r", "#FFF6B0", "#E6B62A"], LINHA, 1.2),
                          *[traco(f"M {x} -96 Q {x * 0.8:.0f} -76 {x * 0.4:.0f} -64", "$pele--", 1.4, o=0.5) for x in (-24, 24)]]},
        manga(ve, ve, None))


def _gaviao(g):
    ro, n = "$c1", "$c2"
    aljava = [rr(10, 4, 11, 30, 3, _gh("#6B4A2E"), LINHA, 1.4), *[traco(f"M {x} 4 L {x + 2} -8", "#E8E8F0", 1.6) for x in (13, 16, 19)]]
    return _junta(
        {"torso": [tronco(g, n), pa("M -21 -38 Q -21 -45 -14 -45 L -6 -45 L -2 6 L -13 6 Q -21 6 -21 0 Z", _g(ro), LINHA, 1.6),
                   traco("M -18 -44 L 18 2", "#6B4A2E", 3), *cinto(n, ro)],
         "capa": aljava,
         "perna": [calca(n), *bota_alta(ro, 30)],
         "mao": luva(ro), "adereco_e": _arco()},
        manga(ro, n, None))


def _feiticeira(g):
    v, e = "$c1", "$c2"
    tiara = pa("M -34 -84 L -24 -110 L -14 -90 L 0 -118 L 14 -90 L 24 -110 L 34 -84 Q 0 -96 -34 -84 Z", _g(v), LINHA, 1.8)
    return _junta(
        {"torso": [tronco(g, e), pa("M -16 -44 L 0 -18 L 16 -44 L 10 -44 L 0 -28 L -10 -44 Z", _g(v), LINHA, 1.2), *cinto(v, None),
                   *_casaco(g, v, 30)],
         "perna": [calca(e), *bota_alta(v, 26)],
         "mao": luva(v),
         "mascara_cima": [tiara]},
        manga(v, v, None))


def _star_lord(g):
    ca, pr, le = "$c1", "$c2", "$c3"
    return _junta(
        {"torso": [tronco(g, pr), *_casaco(g, ca, 26, 6), rr(-5, -30, 10, 8, 2, "#8E929E", LINHA, 1.2)],
         "perna": [calca(pr), *bota_alta("#5A4034", 30)],
         "mao": luva("#5A4034"),
         "mascara_baixo": [cabeca_cheia("#8E929E"), traco("M -40 -64 Q 0 -80 40 -64", "#5B5F6B", 2.2),
                           *par(traco("M -36 -24 L -20 -20", "#5B5F6B", 1.8)), el(0, -30, 6, 4, "#6E727E", LINHA, 1.2)]},
        manga(ca, ca, None))


def _venom(g):
    n, b = "$c1", "$c2"
    simbolo = [pa("M -3 -32 Q -16 -40 -21 -24 Q -12 -30 -6 -24 Q -12 -12 -16 2 Q -6 -12 0 -18 Q 6 -12 16 2 Q 12 -12 6 -24 "
                  "Q 12 -30 21 -24 Q 16 -40 3 -32 Z", b)]
    return _junta(
        {"torso": [tronco(g, n), *simbolo],
         "perna": [calca(n), *bota_alta(n, 32, sola="#0E0C12")],
         "mao": luva(n) + [*[traco(f"M {x} 10 L {x * 1.3:.1f} 17", b, 1.6) for x in (-3, 0, 3)]],
         "mascara_baixo": [cabeca_cheia(n), traco("M -30 -80 Q 0 -94 30 -80", "#3A3846", 2, o=0.7)]},
        manga(n, n, None))


def _tempestade(g):
    n, pr, ou = "$c1", "$c2", "$c3"
    asas = [pa("M -19 3 Q -40 20 -60 60 Q -40 56 -30 70 Q -20 50 0 40 Q 20 50 30 70 Q 40 56 60 60 Q 40 20 19 3 Z", _g(pr), LINHA, 1.8)]
    return _junta(
        {"torso": [tronco(g, n), pa("M -12 -44 L 0 -26 L 12 -44", None, ou, 2), *cinto(ou, None)],
         "capa": asas,
         "perna": [calca(n), *bota_alta(n, 26, borda=ou)],
         "mao": luva(n),
         "mascara_cima": [pa("M -30 -84 Q 0 -96 30 -84 L 29 -79 Q 0 -90 -29 -79 Z", _g(ou), LINHA, 1.2), el(0, -89, 3, 3, "#E0303A", LINHA, 1)]},
        manga(n, n, None))


def _ciclope(g):
    az, am = "$c1", "$c2"
    return _junta(
        {"torso": [tronco(g, az), traco("M -21 -30 L 0 -18 L 21 -30", am, 3), rr(-4, -24, 8, 8, 1.6, _g("#C9202E"), LINHA, 1.1),
                   *cinto(am, "#C9202E")],
         "perna": [calca(az), *bota_alta(am, 28)],
         "mao": luva(am),
         "mascara_baixo": [capuz(az, -34, -74)],
         "mascara_cima": [rr(-44, -48, 88, 15, 7, _g("#D9A93A"), LINHA, 1.6), rr(-36, -45, 72, 9, 4.5, ["h", "#FF6A6A", "#C9202E"], LINHA, 1.2),
                          traco("M -30 -43 L 18 -43", "#FFFFFF", 1.4, o=0.6)]},
        manga(az, az, am))


# --- DC -------------------------------------------------------------------------------------------------------
def _supergirl(g):
    az, ve, am = "$c1", "$c2", "$c3"
    saia = pa("M -18 -6 Q -22 8 -27 20 Q 0 27 27 20 Q 22 8 18 -6 Z", _g(ve), LINHA, 1.6)
    return _junta(
        {"torso": [saia, tronco(g, az), pa("M -10 -38 L 10 -38 L 8.5 -26 L 0 -16 L -8.5 -26 Z", _g(am), LINHA, 1.4),
                   pa("M -6 -35 L 6 -35 L 4.8 -27 L 0 -21.5 L -4.8 -27 Z", _g(ve), None), *cinto(am, None)],
         "capa": capa(ve, 80, 44),
         "perna": [rr(-7.6, 16, 15.2, 30, 6.5, _gh(az), LINHA, 1.5), *bota_alta(ve, 30)],
         "mao": luva(az)},
        manga(az, az, None))


def _batgirl(g):
    n, am, ro = "$c1", "$c2", "$c3"
    morcego = pa("M -11 -30 Q -6 -35 -3 -31 L 0 -33 L 3 -31 Q 6 -35 11 -30 Q 8 -23 3 -23 L 0 -19 L -3 -23 Q -8 -23 -11 -30 Z", am, None)
    return _junta(
        {"torso": [tronco(g, n), morcego, rr(-21.5, -6.8, 43, 8, 3, _g(am), LINHA, 1.4)],
         "capa": capa(ro, 80, 44, recorte=4),
         "perna": [calca(n), *bota_alta(am, 28)],
         "mao": luva(am),
         "mascara_baixo": [capuz(n, -30, -28)],
         "mascara_cima": [*orelha_pontuda(30, 20, n)]},
        manga(n, n, None))


def _arlequina(g):
    ve, n = "$c1", "$c2"
    diam = [pa(f"M {x} {y - 5} L {x + 4} {y} L {x} {y + 5} L {x - 4} {y} Z", "#F4F4F8", LINHA, 1) for x, y in ((-10, -30), (10, -14))]
    return _junta(
        {"torso": [tronco(g, ve), pa("M 0 -45 L 15 -45 Q 21 -45 21 -38 L 21 0 Q 21 6 13 6 L 0 6 Z", _g(n), LINHA, 1.6), *diam,
                   pa("M -12 -45 L 0 -38 L 12 -45 L 0 -41 Z", "#F4F4F8", LINHA, 1.2), *cinto("#F4F4F8", None)],
         "perna": [calca(ve), *bota_alta(n, 30)],
         "mao": luva(n),
         "mascara_cima": [*par(pa("M -34 -46 Q -19 -56 -6 -46 L -8 -36 Q -19 -30 -32 -36 Z", n, None, 0, 0.35))]},
        manga(n, ve, "#F4F4F8"))


def _asa_noturna(g):
    n, az = "$c1", "$c2"
    return _junta(
        {"torso": [tronco(g, n), pa("M -23 -40 L -18 -44 L 0 -22 L 18 -44 L 23 -40 L 0 -14 Z", _g(az), LINHA, 1.2), *cinto(n, None)],
         "perna": [calca(n), *bota_alta(n, 30, sola="#0E0C12")],
         "mao": luva(az),
         "acessorio": [*par(el(-19, -40, 15, 13.6, None, "#1E1C24", 6), pa("M -33 -46 L -44 -52 L -36 -40 Z", "#1E1C24", None)),
                       pa("M -5 -46 Q 0 -49 5 -46 L 4 -38 Q 0 -40 -4 -38 Z", "#1E1C24", None)]},
        manga(n, n, None), {"braco_sup": [pa("M -6.6 2 L 6.6 -3 L 6.6 3 L -6.6 8 Z", _g(az), None)]})


def _hera(g):
    ve, fo = "$c1", "$c2"
    folhas = [pa(f"M {x} {y} Q {x - 6} {y - 7} {x} {y - 13} Q {x + 6} {y - 7} {x} {y} Z", _g(fo), LINHA, 1)
              for x, y in ((-12, -24), (0, -30), (12, -24), (-8, -8), (8, -8), (0, -12))]
    return _junta(
        {"torso": [tronco(g, ve), *folhas, traco("M -20 -2 Q 0 6 20 -2", fo, 2.4)],
         "perna": [calca(ve), traco("M -6 0 Q 6 14 -4 30", fo, 2), *bota_alta(fo, 30)], "mascara_cima": [el(34, -86, 7, 4, _g(fo), LINHA, 1.2), el(-34, -88, 6, 3.4, _g(fo), LINHA, 1.2)]},
        manga(ve, "$pele", None))


def _ravena(g):
    az, n, ve = "$c1", "$c2", "$c3"
    return _junta(
        {"torso": [tronco(g, n), traco("M -12 -44 Q 0 -40 12 -44", ve, 2), el(0, -40, 3, 3, _g(ve), LINHA, 1), *cinto(ve, None)],
         "capa": capa(az, 88, 48),
         "perna": [calca(n), *bota_alta(az, 28)],
         "mao": luva(n),
         "mascara_baixo": [capuz(az, -24, -76)],
         "mascara_cima": [el(0, -66, 3, 3, ["r", "#FF8A8A", ve], LINHA, 1)]},
        manga(n, n, None))


def _besouro(g):
    az, n, le = "$c1", "$c2", "$c3"
    return _junta(
        {"torso": [tronco(g, az), lado(g, -10, n), espelhar(lado(g, -10, n)),
                   pa("M 0 -40 L 10 -30 L 0 -14 L -10 -30 Z", _g(le), LINHA, 1.2), *cinto(n, None)],
         "capa": [*par(pa("M -10 4 Q -34 10 -36 44 Q -20 30 -6 34 Z", _g(az), LINHA, 1.6))],
         "perna": [calca(az), rr(-7.9, 8, 3.4, 30, 1.6, n, None), *bota_alta(n, 30)],
         "mao": luva(n),
         "mascara_baixo": [cabeca_cheia(az), pa("M -44 -60 Q 0 -80 44 -60 L 40 -56 Q 0 -74 -40 -56 Z", n, None)]},
        manga(az, n, None))


def _canario(g):
    n, ou = "$c1", "$c2"
    return _junta(
        {"torso": [tronco(g, n), *_casaco(g, "#2E2A32", -10, 8), *cinto(ou, None), el(0, -44, 3, 2, "#2E2A32", None)],
         "perna": [rr(-7.9, -4, 15.8, 50, 7, _gh("$pele"), LINHA, 1.6),
                   *[traco(f"M -8 {y} L 8 {y + 8}", "#2E2A32", 0.9, o=0.7) for y in range(0, 36, 5)],
                   *[traco(f"M 8 {y} L -8 {y + 8}", "#2E2A32", 0.9, o=0.7) for y in range(0, 36, 5)], *bota_alta(n, 30)],
         "mao": luva(n)},
        manga("#2E2A32", "#2E2A32", None))


# --- CLÁSSICAS (não são de ninguém) -----------------------------------------------------------------------------
def _pirata(g):
    ve, co, ma = "$c1", "$c2", "$c3"
    chapeu = [pa("M -66 -72 C -40 -60 40 -60 66 -72 C 50 -84 36 -122 0 -122 C -36 -122 -50 -84 -66 -72 Z", _g("#26232C"), LINHA, 2),
              traco("M -54 -76 Q 0 -66 54 -76", "#D9A93A", 2.2), traco("M -8 -106 L 8 -92", "#F4F4F8", 2.6), traco("M 8 -106 L -8 -92", "#F4F4F8", 2.6)]
    tapa = [pa("M 8 -52 Q 19 -56 30 -52 L 29 -32 Q 19 -26 9 -32 Z", "#1E1C24", LINHA, 1.2), traco("M 8 -50 L -40 -74", "#1E1C24", 1.6),
            traco("M 30 -50 L 50 -56", "#1E1C24", 1.6)]
    listras = [rr(-22, y, 44, 3.4, 0, ve, None, 0, 0.9) for y in (-38, -30, -22, -14, -6)]
    return _junta(
        {"torso": [tronco(g, "#F4F4F8"), *listras, pa(TORSO_D[g], None, LINHA, 1.8), *_casaco(g, co, 0, 9), *cinto(ma, "#D9A93A")],
         "perna": [calca(ma), *bota_alta("#26232C", 26, borda="#4A3A30")],
         "adereco_d": direita([rr(-1.5, 0, 3, 8, 1, "#6B4A2E", LINHA, 1), pa("M -2.4 8 L 2.4 8 L 1.2 34 Q 0 38 -1.2 34 Z", ["h", "#DDE3EE", "#9AA3B2"], LINHA, 1.2),
                               rr(-6, 6, 12, 3, 1.4, "#D9A93A", LINHA, 1)]),
         "mascara_cima": [*chapeu, *tapa]},
        manga(co, co, "#F4F4F8"))


def _ninja(g):
    n, fa = "$c1", "$c2"
    return _junta(
        {"torso": [tronco(g, n), pa("M -12 -45 L 2 -20 L -4 -20 L -16 -44 Z", "$c1+", None, 0, 0.6), *cinto(fa, None),
                   pa("M 6 -4 L 14 12 L 9 12 L 3 -2 Z", fa, LINHA, 1)],
         "perna": [calca(n), rr(-8.2, 30, 16.4, 12, 3, "$c1+", LINHA, 1.2), *bota_alta(n, 40)],
         "mao": luva(n),
         "capa": [traco("M -8 2 L 26 -14", "#3A3846", 4), el(28, -15, 3, 3, "#9AA3B2", LINHA, 1)],
         "mascara_baixo": [cabeca_cheia(n), rr(-44, -56, 88, 32, 14, _g("$pele"), LINHA, 1.6)],
         "mascara_cima": [pa("M -54 -66 Q 0 -80 54 -66 L 53 -58 Q 0 -72 -53 -58 Z", _g(fa), LINHA, 1.4),
                          pa("M 50 -64 L 70 -54 L 64 -48 Z", fa, LINHA, 1.2), pa("M 50 -60 L 66 -40 L 58 -38 Z", fa, LINHA, 1.2)]},
        manga(n, n, None))


def _astronauta(g):
    b, la, az = "$c1", "$c2", "$c3"
    return _junta(
        {"torso": [tronco(g, b), rr(-11, -34, 22, 16, 3, _g("#C9CFDB"), LINHA, 1.3),
                   *[el(x, -26, 2.2, 2.2, c, LINHA, 0.8) for x, c in ((-6, "#D9384A"), (0, "#3F7BE0"), (6, "#3FAE6B"))],
                   el(-14, -40, 4.4, 4.4, _g(az), LINHA, 1), *cinto("#9AA3B2", la)],
         "capa": [rr(-22, 6, 44, 38, 8, _g("#C9CFDB"), LINHA, 1.6)],
         "perna": [calca(b), rr(-7.9, 18, 15.8, 4, 1, la, None), *bota_alta("#C9CFDB", 34, borda=la)],
         "mao": luva(la),
         "mascara_cima": [el(0, -52, 62, 58, "#BEE3FF", "#9AA3B2", 3, 0.18), el(0, -52, 62, 58, None, "#E8EEF6", 3.2),
                          traco("M -40 -86 Q -30 -100 -10 -104", "#FFFFFF", 4, o=0.55), traco("M -48 -70 Q -46 -76 -44 -80", "#FFFFFF", 3, o=0.4)]},
        manga(b, b, la), {"braco_sup": [rr(-6.6, 0, 13.2, 3, 1, az, None)]})


def _mago(g):
    ro, ou = "$c1", "$c2"
    estrelas = [estrela(x, y, 3, ou) for x, y in ((-12, -30), (10, -14), (-6, 6), (12, 22), (-14, 28))]
    manto = pa("M -22 -38 Q -22 -46 -14 -46 L 14 -46 Q 22 -46 22 -38 L 30 46 Q 0 54 -30 46 Z", _g(ro), LINHA, 1.8)
    chapeu = [pa("M -62 -72 C -30 -62 30 -62 62 -72 C 50 -82 36 -82 30 -80 L -30 -80 C -36 -82 -50 -82 -62 -72 Z", _g(ro), LINHA, 2),
              pa("M -30 -80 C -26 -110 -8 -140 20 -154 C 10 -130 22 -100 30 -80 Z", _g(ro), LINHA, 2),
              estrela(0, -104, 6, ou), estrela(14, -126, 3.6, ou)]
    return _junta(
        {"torso": [manto, *estrelas, traco("M -24 40 Q 0 48 24 40", ou, 2)],
         "perna": [rr(-9.4, 44, 18.8, 9, 4.5, _g("#5A4034"), LINHA, 1.5)],
         "adereco_d": direita([rr(-2, -30, 4, 70, 2, _gh("#6B4A2E"), LINHA, 1.2), el(0, -34, 6.4, 6.4, ["r", "#FFFFFF", "#6FD3FF"], LINHA, 1.2)]),
         "mascara_cima": chapeu},
        manga(ro, ro, ou))


def _cavaleiro(g):
    pr, ve = "$c1", "$c2"
    return _junta(
        {"torso": [tronco(g, pr), pa("M -12 -44 L 12 -44 L 10 -8 L 0 0 L -10 -8 Z", _g(ve), LINHA, 1.4),
                   traco("M 0 -38 L 0 -10", "#F2C94C", 3), traco("M -7 -28 L 7 -28", "#F2C94C", 3), *cinto("#5A4034", "#F2C94C")],
         "perna": [calca(pr), el(0, 22, 6, 5, _g(pr), LINHA, 1.2), *bota_alta(pr, 30)],
         "mao": luva(pr),
         "adereco_d": direita([rr(-6, 6, 12, 3, 1.4, "#D9A93A", LINHA, 1), rr(-1.6, 0, 3.2, 8, 1, "#6B4A2E", LINHA, 1),
                               pa("M -2.6 9 L 2.6 9 L 2 40 L 0 44 L -2 40 Z", ["h", "#EEF2F8", "#9AA3B2"], LINHA, 1.2)]),
         "mascara_baixo": [cabeca_cheia(pr), rr(-40, -54, 80, 28, 6, _g(pr + "-"), LINHA, 1.6),
                           *[traco(f"M {x} -30 L {x} -20", LINHA, 1.4, o=0.6) for x in (-10, 0, 10)]],
         "mascara_cima": [pa("M -4 -100 C -10 -130 20 -138 30 -120 C 16 -124 8 -118 4 -100 Z", _g(ve), LINHA, 1.6)]},
        manga(pr, pr, None), {"braco_sup": [el(0, -1.5, 8.6, 7, _g(pr), LINHA, 1.5)]})


def _vampiro(g):
    n, ve = "$c1", "$c2"
    gola = [pa("M -24 -44 L -40 -70 L -18 -52 Z", _g(ve), LINHA, 1.4), pa("M 24 -44 L 40 -70 L 18 -52 Z", _g(ve), LINHA, 1.4)]
    return _junta(
        {"torso": [pa(TORSO_D[g], _g("#F4F4F8"), LINHA, 1.8), pa("M -12 -30 L 12 -30 L 14 6 L -14 6 Z", _g(ve), LINHA, 1.4),
                   pa("M -5 -44 L 0 -36 L 5 -44 Z", "#F4F4F8", LINHA, 1), el(0, -32, 3, 3, "#D9384A", LINHA, 1),
                   *_casaco(g, n, 8, 12), *gola],
         "capa": [pa("M -19 3 Q -30 20 -48 84 Q 0 96 48 84 Q 30 20 19 3 Z", _g(ve), LINHA, 1.8)],
         "perna": [calca(n), *sapato()]},
        manga(n, n, "#F4F4F8"))


def _bombeiro(g):
    ca, am, ve = "$c1", "$c2", "$c3"
    capacete = [pa("M -54 -62 C -58 -112 58 -112 54 -62 Z", _g(ve), LINHA, 2), pa("M -64 -62 Q 0 -54 64 -62 L 60 -54 Q 0 -46 -60 -54 Z", _g(ve), LINHA, 1.6),
                pa("M -9 -100 L 9 -100 L 7 -76 L -7 -76 Z", _g("#F2C94C"), LINHA, 1.3)]
    return _junta(
        {"torso": [tronco(g, ca), rr(-22, -20, 44, 4, 0, am, None), rr(-22, -8, 44, 4, 0, am, None), traco("M 0 -44 L 0 6", LINHA, 1.4, o=0.5),
                   *[el(-3.4, y, 1.4, 1.4, "#26232C") for y in (-34, -26)]],
         "perna": [calca(ca), rr(-7.9, 24, 15.8, 3.6, 0, am, None), *bota_alta("#26232C", 30)],
         "mao": luva("#26232C"),
         "mascara_cima": capacete},
        manga(ca, ca, None), {"braco_inf": [rr(-6.1, 6, 12.2, 3.4, 0, am, None)]})


def _chef(g):
    b, ve = "$c1", "$c2"
    chapeu = [rr(-34, -92, 68, 18, 5, _g("#F4F4F8"), LINHA, 1.8),
              pa("M -34 -88 C -52 -110 -34 -134 -14 -124 C -8 -142 14 -142 18 -124 C 36 -134 54 -110 34 -88 Z", _g("#FFFFFF"), LINHA, 2)]
    return _junta(
        {"torso": [tronco(g, b), pa("M -21 -38 L 8 -40 L 21 -30", None, LINHA, 1.2),
                   *[el(x, y, 1.6, 1.6, "#9AA3B2", LINHA, 0.8) for x in (-6, 6) for y in (-30, -20, -10)],
                   pa("M -12 -45 L 0 -36 L 12 -45 L 6 -40 L 0 -44 L -6 -40 Z", _g(ve), LINHA, 1.2)],
         "perna": [calca("#3A3846"), traco("M -7 4 L 7 4", "#8A8F9B", 1, o=0.5), *sapato()],
         "adereco_d": direita([rr(-1.5, 2, 3, 14, 1.2, "#6B4A2E", LINHA, 1), el(0, 22, 6, 7.4, _g("#C9CFDB"), LINHA, 1.2)]),
         "mascara_cima": chapeu},
        manga(b, b, None))


def _detetive(g):
    be, ma = "$c1", "$c2"
    chapeu = [pa("M -62 -68 C -30 -58 30 -58 62 -68 C 58 -76 48 -76 42 -74 C 20 -66 -20 -66 -42 -74 C -48 -76 -58 -76 -62 -68 Z", _g(ma), LINHA, 2),
              pa("M -36 -72 C -38 -104 -26 -114 0 -106 C 26 -114 38 -104 36 -72 C 20 -66 -20 -66 -36 -72 Z", _g(ma), LINHA, 2),
              pa("M -37 -78 C -20 -70 20 -70 37 -78 L 36.6 -84 C 20 -76 -20 -76 -36.6 -84 Z", "#26232C", LINHA, 1.2)]
    return _junta(
        {"torso": [tronco(g, "#F4F4F8"), pa("M -3 -44 L 3 -44 L 4 -30 L 0 -14 L -4 -30 Z", "#7E2440", LINHA, 1.1),
                   *_casaco(g, be, 34, 5), rr(-22, -8, 44, 5, 2, _g(be + "-"), LINHA, 1.2)],
         "perna": [calca("#3A3846"), *sapato("#5A4034")],
         "adereco_d": direita([rr(-1.6, 2, 3.2, 12, 1.2, "#26232C", LINHA, 1), el(0, 22, 8, 8, "#BEE3FF", "#9A7A3A", 2.4, 0.9),
                               traco("M -3 18 Q 0 16 3 18", "#FFFFFF", 1.4, o=0.8)]),
         "mascara_cima": chapeu},
        manga(be, be, None))


def _cowboy(g):
    co, je, ve = "$c1", "$c2", "$c3"
    chapeu = [pa("M -70 -70 C -60 -60 -40 -62 -30 -66 C -10 -62 10 -62 30 -66 C 40 -62 60 -60 70 -70 C 64 -78 56 -76 44 -74 "
                 "C 20 -66 -20 -66 -44 -74 C -56 -76 -64 -78 -70 -70 Z", _g(co), LINHA, 2),
              pa("M -36 -72 C -40 -100 -30 -116 -10 -108 C 0 -114 0 -114 10 -108 C 30 -116 40 -100 36 -72 C 20 -66 -20 -66 -36 -72 Z", _g(co), LINHA, 2),
              pa("M -37 -78 C -20 -70 20 -70 37 -78 L 36.6 -84 C 20 -76 -20 -76 -36.6 -84 Z", "#3A2A20", LINHA, 1.2)]
    return _junta(
        {"torso": [tronco(g, "#E9E2D0"), *[traco(f"M {x} -44 L {x} 6", ve, 1.2, o=0.35) for x in (-14, -7, 7, 14)],
                   *[traco(f"M -21 {y} L 21 {y}", ve, 1.2, o=0.35) for y in (-34, -20, -6)],
                   pa("M -21 -38 Q -21 -45 -14 -45 L -7 -45 L -4 6 L -13 6 Q -21 6 -21 0 Z", _g(co), LINHA, 1.6),
                   pa("M 21 -38 Q 21 -45 14 -45 L 7 -45 L 4 6 L 13 6 Q 21 6 21 0 Z", _g(co), LINHA, 1.6),
                   pa("M -10 -45 L 0 -34 L 10 -45 L 6 -45 L 0 -40 L -6 -45 Z", _g(ve), LINHA, 1.1),
                   *cinto("#5A4034", "#D9A93A")],
         "perna": [calca(je), *bota_alta(co, 28, borda="#3A2A20")],
         "mascara_cima": chapeu},
        manga("#E9E2D0", "#E9E2D0", None))


MARVEL2 = {
    "miles": ("Aranha (Miles)", {"c1": "#1E1C22", "c2": "#D3202F", "lente": "#F6F6FA", "boca_linha": "#8A121C", "boca_dentro": "#5A0B12",
                                 "lingua": "#B23040"}, ["cabelo", "sobr", "acessorio"], "lente", None, _miles),
    "aranha_gwen": ("Aranha (Gwen)", {"c1": "#F4F4F8", "c2": "#F27CA8", "c3": "#3FC1C9", "lente": "#F6F6FA", "boca_linha": "#8A5A6A",
                                      "boca_dentro": "#4A2A36", "lingua": "#D9708A"}, ["cabelo", "sobr", "acessorio"], "lente", None, _gwen),
    "loki": ("Loki", {"c1": "#2E7D4F", "c2": "#D4A92A", "c3": "#1E2A24", "cabelo": "#1E1A1E"}, ["acessorio"], "normal", "longo", _loki),
    "visao": ("Visão", {"c1": "#2E8B57", "c2": "#E6B62A", "c3": "#D4A92A", "pele": "#C8404A"}, ["cabelo", "acessorio"], "normal", None, _visao),
    "gaviao_arqueiro": ("Gavião Arqueiro", {"c1": "#5B3C88", "c2": "#26232C"}, [], "normal", "curto", _gaviao),
    "feiticeira_escarlate": ("Feiticeira Escarlate", {"c1": "#B3202E", "c2": "#3A1A24", "cabelo": "#8E2A1E"}, ["acessorio"], "normal", "ondulado", _feiticeira),
    "star_lord": ("Senhor das Estrelas", {"c1": "#8E2A26", "c2": "#3A3A44", "c3": "#E0303A", "lente": "#FF5A5A", "boca_linha": "#4A4E5A",
                                          "boca_dentro": "#2A2C34", "lingua": "#5A5E6A"}, ["cabelo", "sobr", "acessorio"], "lente", None, _star_lord),
    "venom": ("Simbionte", {"c1": "#15131A", "c2": "#F4F4F8", "lente": "#FFFFFF", "boca_linha": "#F4F4F8", "boca_dentro": "#5A0B24",
                            "lingua": "#E0507A"}, ["cabelo", "sobr", "acessorio"], "lente", None, _venom),
    "tempestade": ("Tempestade", {"c1": "#26232C", "c2": "#C9CFDB", "c3": "#F2C94C", "cabelo": "#EEEEF4"}, ["acessorio"], "normal", "longo", _tempestade),
    "ciclope": ("Ciclope", {"c1": "#2B3F9E", "c2": "#F2C94C", "lente": "#FF6A6A"}, ["acessorio"], "visor", None, _ciclope),
}
DC2 = {
    "supergirl": ("Supergirl", {"c1": "#2A56C6", "c2": "#D0202E", "c3": "#F2C94C", "cabelo": "#E7C36A"}, [], "normal", "longo", _supergirl),
    "batgirl": ("Batgirl", {"c1": "#2B2A36", "c2": "#F2C94C", "c3": "#3A2A5A", "cabelo": "#C0442A"}, ["acessorio"], "normal", "longo", _batgirl),
    "arlequina": ("Arlequina", {"c1": "#C9202E", "c2": "#1E1C24", "cabelo": "#F2E7C9"}, [], "normal", "chiquinha", _arlequina),
    "asa_noturna": ("Asa Noturna", {"c1": "#1E1C24", "c2": "#2F7BE0", "cabelo": "#1E1A1E"}, ["acessorio"], "normal", "social", _asa_noturna),
    "hera_venenosa": ("Hera Venenosa", {"c1": "#2E8B57", "c2": "#4DBE6B", "cabelo": "#B8402B"}, [], "normal", "ondulado", _hera),
    "ravena": ("Ravena", {"c1": "#2A2F6B", "c2": "#1E1C24", "c3": "#D9384A", "cabelo": "#4B3A8A"}, ["acessorio"], "normal", "chanel", _ravena),
    "besouro_azul": ("Besouro Azul", {"c1": "#2F6FE0", "c2": "#1E1C24", "c3": "#F2C94C", "lente": "#FFE08A", "boca_linha": "#1E3A7A",
                                      "boca_dentro": "#0E1A3A", "lingua": "#3A5AAA"}, ["cabelo", "sobr", "acessorio"], "lente", None, _besouro),
    "canario_negro": ("Canário Negro", {"c1": "#1E1C24", "c2": "#D9A93A", "cabelo": "#E7C36A"}, [], "normal", "longo", _canario),
}
CLASSICAS = {
    "pirata": ("Pirata", {"c1": "#C9202E", "c2": "#7A2338", "c3": "#5A4034"}, ["acessorio"], "normal", None, _pirata),
    "ninja": ("Ninja", {"c1": "#26232C", "c2": "#D9384A"}, ["cabelo", "acessorio"], "normal", None, _ninja),
    "astronauta": ("Astronauta", {"c1": "#F4F4F8", "c2": "#F08A2C", "c3": "#3F7BE0"}, ["acessorio"], "normal", None, _astronauta),
    "mago": ("Mago", {"c1": "#4B3A8A", "c2": "#F2C94C"}, ["acessorio"], "normal", None, _mago),
    "cavaleiro": ("Cavaleiro", {"c1": "#AEB6C4", "c2": "#2B4BA8", "lente": "#1A1A22"}, ["cabelo", "sobr", "acessorio"], "fenda", None, _cavaleiro),
    "vampiro": ("Vampiro", {"c1": "#1E1C24", "c2": "#9E1A2A", "pele": "#EFE8EC", "cabelo": "#1E1A1E"}, [], "normal", "social", _vampiro),
    "bombeiro": ("Bombeiro", {"c1": "#3A3846", "c2": "#F2C94C", "c3": "#D0202E"}, ["acessorio"], "normal", None, _bombeiro),
    "chef": ("Chef de cozinha", {"c1": "#F4F4F8", "c2": "#D9384A"}, ["acessorio"], "normal", None, _chef),
    "detetive": ("Detetive", {"c1": "#C9A97A", "c2": "#5A4034"}, ["acessorio"], "normal", None, _detetive),
    "cowboy": ("Cowboy", {"c1": "#8A5A2E", "c2": "#3F5AA8", "c3": "#D9384A"}, ["acessorio"], "normal", None, _cowboy),
}
