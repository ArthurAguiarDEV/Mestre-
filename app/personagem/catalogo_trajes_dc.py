"""Fantasias inspiradas em heróis da DC (mesmas peças e mesmo aviso de catalogo_trajes.py)."""
from .arte import el, espelhar, pa, par, rr, traco
from .catalogo_corpo import TORSO_D
from .catalogo_roupas import LINHA, _g, _gh, _junta, calca
from .catalogo_trajes import (bota_alta, capa, capuz, cinto, direita, estrela, lado, luva, manga, orelha_pontuda, raio,
                              tronco)


def _superman(g):
    az, ve, am = "$c1", "$c2", "$c3"
    return _junta(
        {"torso": [tronco(g, az), pa("M -10 -38 L 10 -38 L 8.5 -26 L 0 -16 L -8.5 -26 Z", _g(am), LINHA, 1.4),
                   pa("M -6 -35 L 6 -35 L 4.8 -27 L 0 -21.5 L -4.8 -27 Z", _g(ve), None), *cinto(am, None)],
         "capa": capa(ve, 84, 46),
         "perna": [rr(-8.4, -4, 16.8, 17, 7, _gh(ve), LINHA, 1.5), rr(-7.9, 12, 15.8, 32, 6.5, _gh(az), LINHA, 1.5), *bota_alta(ve, 28)],
         "mao": luva(az)},
        manga(az, az, None))


def _batman(g):
    n, c, am, fo = "$c1", "$c2", "$c3", "$c4"
    bolsas = [rr(x, -6.5, 7, 8.4, 2, _g("#C9A227"), LINHA, 1.2) for x in (-16, -9, 9, 16)]
    morcego = pa("M -11 -30 Q -6 -35 -3 -31 L 0 -33 L 3 -31 Q 6 -35 11 -30 Q 8 -23 3 -23 L 0 -19 L -3 -23 Q -8 -23 -11 -30 Z", n, None)
    return _junta(
        {"torso": [tronco(g, c), lado(g, -13, n), espelhar(lado(g, -13, n)), morcego, rr(-21.5, -6.8, 43, 8, 3, _g(am), LINHA, 1.4), *bolsas],
         "capa": [*capa(n, 84, 46, borda=fo, recorte=4)],
         "perna": [calca(n), *bota_alta(n, 27, sola="#0F0D12")],
         "mao": luva(n),
         "mascara_baixo": [capuz(n, -30, -28)],
         "mascara_cima": [*orelha_pontuda(30, 26, n)]},
        manga(c, n, None), {"braco_inf": [pa(f"M -6.2 {y} L -11.5 {y + 3} L -6.2 {y + 5.5} Z", n, LINHA, 1.1) for y in (7, 12)]})


def _mulher_maravilha(g):
    ve, az, ou, pr = "$c1", "$c2", "$c3", "$c4"
    estrelas = [estrela(x, y, 2.6, "#FFFFFF") for x, y in ((-3, 1), (3, 8), (-2, 11))]
    return _junta(
        {"torso": [tronco(g, ve), pa("M -14 -45 L 0 -22 L 14 -45 L 10 -45 L 0 -32 L -10 -45 Z", _g(ou), LINHA, 1.2),
                   estrela(0, -25, 6, ou), *cinto(ou, None), rr(-21.5, 1, 43, 3.4, 1.4, _g(ou), None)],
         "perna": [rr(-8, -4, 16, 21, 7, _gh(az), LINHA, 1.5), *estrelas, *bota_alta(ve, 27, borda=ou)],
         "mao": luva(pr),
         "adereco_e": [el(-2, 10, 9, 9, None, ou, 2.4), el(-2, 10, 5.5, 5.5, None, ou, 1.6, 0.8)],
         "mascara_cima": [pa("M -31 -85 Q 0 -98 31 -85 L 30 -78.5 Q 0 -90 -30 -78.5 Z", _g(ou), LINHA, 1.3), estrela(0, -86, 4.4, ve, contorno=LINHA)]},
        {"braco_inf": [rr(-6.6, 9, 13.2, 11, 4, _gh(pr), LINHA, 1.5)]})


def _flash(g):
    ve, am = "$c1", "$c2"
    return _junta(
        {"torso": [tronco(g, ve), el(0, -26, 9, 9, _g(am), LINHA, 1.4), raio(0, -26, 0.42, ve), *cinto(am, None),
                   traco("M -21 -12 L 21 -10", am, 1.6, o=0.6)],
         "perna": [calca(ve), raio(0, 16, 0.34, am), *bota_alta(ve, 28, borda=am)],
         "mao": luva(ve),
         "mascara_baixo": [capuz(ve, -30, -52)],
         "mascara_cima": [*par(pa("M -50 -56 L -72 -62 L -58 -46 L -68 -46 L -50 -40 Z", _g(am), LINHA, 1.3))]},
        manga(ve, ve, am))


def _aquaman(g):
    la, ve, ou = "$c1", "$c2", "$c3"
    escamas = [traco(f"M {x - 3} {y} Q {x} {y + 4} {x + 3} {y}", la + "--", 1.2, o=0.6) for y in (-36, -28, -20, -12) for x in (-12, -4, 4, 12)]
    esc_perna = [traco(f"M {x - 3} {y} Q {x} {y + 4} {x + 3} {y}", ve + "--", 1.2, o=0.6) for y in (2, 10, 18, 26, 34) for x in (-3, 4)]
    tridente = direita([rr(-1.8, -6, 3.6, 40, 1.4, _g(ou), LINHA, 1.2), pa("M -9 -22 Q -9 -12 0 -8 Q 9 -12 9 -22 L 6 -22 L 6 -14 L 1.4 -14 L 1.4 -26 L -1.4 -26 L -1.4 -14 L -6 -14 L -6 -22 Z", _g(ou), LINHA, 1.3)])
    return _junta(
        {"torso": [tronco(g, la), *escamas, *cinto("#3A5A3C", ou)],
         "perna": [calca(ve), *esc_perna, *bota_alta(ou, 30, borda=ve)],
         "mao": luva(ou), "adereco_d": tridente,
         "mascara_baixo": [pa("M -46 -34 Q -50 -2 0 5 Q 50 -2 46 -34 Q 32 -20 0 -22 Q -32 -20 -46 -34 Z", _g("$cabelo"), "$cabelo--", 1.8)]},
        manga(la, ou, None))


def _lanterna_verde(g):
    ve, n, br = "$c1", "$c2", "$c3"
    return _junta(
        {"torso": [tronco(g, n), pa("M -12 -45 L 12 -45 L 9 -8 L -9 -8 Z", _g(ve), None), el(0, -27, 7, 7, _g(br), LINHA, 1.4), el(0, -27, 4, 4, ve, None),
                   *cinto(n, ve)],
         "perna": [calca(n), traco("M 0 4 L 0 28", ve, 2.4, o=0.8), *bota_alta(n, 29, borda=ve)],
         "mao": luva(br),
         "adereco_d": direita([el(0, 5, 3.6, 3.6, None, "#7CFFB0", 2.6), el(0, 5, 8, 8, "#7CFFB0", None, 0, 0.25)]),
         "mascara_baixo": [pa("M -47 -50 Q 0 -60 47 -50 L 45 -30 Q 0 -25 -45 -30 Z", _g(ve), LINHA, 1.8)]},
        manga(ve, ve, br))


def _flecha_verde(g):
    ve, es, ma = "$c1", "$c2", "$c3"
    aljava = [rr(14, -30, 9, 46, 3, _g(ma), LINHA, 1.4), *[traco(f"M {17 + i * 3} -30 L {17 + i * 3} -40", ve, 2) for i in range(3)]]
    arco = [traco("M 2 -8 Q -14 12 2 32", "#6B4A2E", 3.6), traco("M 2 -8 L 2 32", "#E9E9F2", 1)]
    return _junta(
        {"torso": [tronco(g, ve), traco("M -20 -40 L 18 4", ma, 3.4), *cinto(ma, "#C9A227"), pa("M -12 -45 L 0 -30 L 12 -45 Z", _g(es), LINHA, 1.2)],
         "capa": aljava,
         "perna": [calca(es), *bota_alta(ma, 29)],
         "mao": luva(ma), "adereco_e": arco,
         "mascara_baixo": [capuz(ve, -22, -50), pa("M -46 -52 Q 0 -60 46 -52 L 44 -32 Q 0 -27 -44 -32 Z", "#1E1E24", LINHA, 1.6),
                           pa("M -13 -22 Q 0 -8 13 -22 Q 8 -10 0 -6 Q -8 -10 -13 -22 Z", "$cabelo", "$cabelo--", 1.4)],
         "mascara_cima": [pa("M -14 -100 L 0 -124 L 14 -100 Z", _g(ve), LINHA, 1.4)]},
        manga(ve, ve, ma))


def _ciborgue(g):
    pr, es, az, ve = "$c1", "$c2", "$c3", "$c4"
    circ = [traco("M -14 -38 L -14 -22 L -6 -22", az, 1.6), traco("M 14 -38 L 14 -14 L 6 -14", az, 1.6), el(0, -26, 4.6, 4.6, None, az, 1.8),
            traco("M -18 -8 L 18 -8", az, 1.4, o=0.8)]
    return _junta(
        {"torso": [tronco(g, es), lado(g, -10, pr), *circ, *cinto("#2A3040", pr)],
         "perna": [calca(es), traco("M 0 2 L 0 26", az, 2, o=0.8), el(0, 22, 5, 5, _g(pr), LINHA, 1.3), *bota_alta(pr, 30)],
         "mao": luva(pr),
         "mascara_baixo": [pa("M 0 -96 C -34 -96 -52 -76 -52 -48 C -52 -22 -34 -3 0 -3 Z", _g(pr), LINHA, 2),
                           traco("M -26 -84 Q -44 -70 -46 -50", az, 1.6, o=0.8), traco("M -34 -22 L -8 -22", az, 1.4, o=0.7)],
         "mascara_cima": [el(-19, -40, 10, 12.5, "#1A1015", LINHA, 1.6), el(-19, -40, 7, 9, ve, None), el(-22, -43, 2.6, 2.8, "#FFFFFF")]},
        manga(es, pr, az), {"braco_sup": [el(0, -1.5, 7.6, 6.4, _g(pr), LINHA, 1.4)]})


def _shazam(g):
    ve, ou, br = "$c1", "$c2", "$c3"
    return _junta(
        {"torso": [tronco(g, ve), el(0, -26, 10, 10, _g(br), LINHA, 1.5), raio(0, -26, 0.45, ou, LINHA), *cinto(ou, None)],
         "capa": capa(br, 84, 46, borda=ou),
         "perna": [calca(ve), *bota_alta(ou, 27, borda=br)],
         "mao": luva(br)},
        manga(ve, ve, ou))


def _robin(g):
    ve, verde, am, n = "$c1", "$c2", "$c3", "$c4"
    return _junta(
        {"torso": [tronco(g, ve), lado(g, -14, n), espelhar(lado(g, -14, n)), el(0, -26, 7, 7, _g(am), LINHA, 1.4), *cinto("#3A3540", am)],
         "capa": capa(am, 70, 42, borda=n),
         "perna": [rr(-8, -4, 16, 14, 7, _gh(verde), LINHA, 1.5), rr(-7.9, 8, 15.8, 22, 6.5, _gh(n), LINHA, 1.5), *bota_alta(verde, 29, borda=am)],
         "mao": luva(verde),
         "mascara_baixo": [pa("M -46 -52 Q 0 -60 46 -52 L 44 -30 Q 0 -25 -44 -30 Z", n, LINHA, 1.6)]},
        manga(n, n, verde))


def _mulher_gato(g):
    n, ou, lente = "$c1", "$c2", "$c3"
    garras = [traco(f"M {x} 8 L {x * 1.5:.1f} 24", "#DDE3EE", 2) for x in (-3.4, 0, 3.4)]
    chicote = [traco("M 0 8 Q 20 4 18 28 Q 16 42 30 40", "#6B4A2E", 2.2)]
    return _junta(
        {"torso": [tronco(g, n), traco("M -18 -36 Q -12 -20 -16 -4", "#4A4652", 1.4, o=0.8), traco("M 18 -36 Q 12 -20 16 -4", "#4A4652", 1.4, o=0.8),
                   *cinto("#3A3540", ou), rr(-21.5, -2, 43, 3, 1.2, "#4A4652", None)],
         "perna": [calca(n), *bota_alta(n, 25, sola="#0F0D12")],
         "mao": [*garras, *luva(n)], "adereco_e": chicote,
         "mascara_baixo": [capuz(n, -32, -52)],
         "mascara_cima": [*orelha_pontuda(30, 20, n), *par(el(-19, -84, 8, 7.5, _g("#3A3540"), LINHA, 1.4)), *par(el(-19, -84, 5, 4.6, lente, None, 0, 0.9))]},
        manga(n, n, None))


def _coringa(g):
    ro, ve, la = "$c1", "$c2", "$c3"
    return _junta(
        {"torso": [pa(TORSO_D[g], _g(la), LINHA, 1.8), pa("M -10 -45 L 10 -45 L 8 -8 L -8 -8 Z", _g(ve), None),
                   pa("M -3.4 -43 L 3.4 -43 L 4.4 -32 L 0 -14 L -4.4 -32 Z", _g(ro + "-"), LINHA, 1.2),
                   pa("M -23 -38 Q -23 -45 -15 -45 L -9 -45 L -2 -20 L -3 6 L -13 6 Q -21 6 -21 0 Z" if g == "m" else
                      "M -20 -38 Q -20 -45 -13 -45 L -9 -45 L -2 -20 L -3 7 L -16 7 Q -21 7 -21 5 Q -15.5 -8 -15.5 -16 Q -18 -28 -20 -38 Z", _g(ro), LINHA, 1.6),
                   pa("M 23 -38 Q 23 -45 15 -45 L 9 -45 L 2 -20 L 3 6 L 13 6 Q 21 6 21 0 Z" if g == "m" else
                      "M 20 -38 Q 20 -45 13 -45 L 9 -45 L 2 -20 L 3 7 L 16 7 Q 21 7 21 5 Q 15.5 -8 15.5 -16 Q 18 -28 20 -38 Z", _g(ro), LINHA, 1.6),
                   el(11, -30, 2, 2, "#F2C94C")],
         "perna": [calca(ro), *bota_alta("#2A2630", 33)],
         "mao": luva("#EDE8F5"),
         "mascara_baixo": [*par(el(-19, -40, 14.5, 16.5, "#2B2226", None, 0, 0.33))]},
        manga(ro, ro, "#EDE8F5"))


DC = {
    "superman": ("Super-Homem", {"c1": "#2A56C6", "c2": "#D0202E", "c3": "#F2C94C"}, [], "normal", None, _superman),
    "batman": ("Batman", {"c1": "#23222B", "c2": "#6C7284", "c3": "#F2C94C", "c4": "#3A4A7A", "lente": "#F6F6FA"},
               ["cabelo", "sobr", "acessorio"], "fenda", None, _batman),
    "mulher_maravilha": ("Mulher-Maravilha", {"c1": "#D0202E", "c2": "#2A56C6", "c3": "#F2C94C", "c4": "#C9CDD8", "cabelo": "#2B2226"},
                         [], "normal", "longo", _mulher_maravilha),
    "flash": ("Flash", {"c1": "#C9202E", "c2": "#F2C94C"}, ["cabelo", "acessorio"], "normal", None, _flash),
    "aquaman": ("Aquaman", {"c1": "#E8912B", "c2": "#2E9E76", "c3": "#F2C94C", "cabelo": "#E7C36A"}, [], "normal", "longo", _aquaman),
    "lanterna_verde": ("Lanterna Verde", {"c1": "#2FBF62", "c2": "#1E1E24", "c3": "#F4F4F8", "lente": "#F6F6FA"}, [], "normal", None, _lanterna_verde),
    "flecha_verde": ("Arqueiro Verde", {"c1": "#2E8B57", "c2": "#1F5A3A", "c3": "#7A4E32", "cabelo": "#E7C36A"}, ["cabelo", "acessorio"], "normal", None, _flecha_verde),
    "ciborgue": ("Ciborgue", {"c1": "#C9D0DE", "c2": "#3A4256", "c3": "#4FC3F7", "c4": "#E53935"}, [], "normal", None, _ciborgue),
    "shazam": ("Shazam", {"c1": "#D0202E", "c2": "#F2C94C", "c3": "#F4F4F8"}, [], "normal", None, _shazam),
    "robin": ("Robin", {"c1": "#D0202E", "c2": "#3FAE4A", "c3": "#F2C94C", "c4": "#1E1E24"}, [], "normal", None, _robin),
    "mulher_gato": ("Mulher-Gato", {"c1": "#24222B", "c2": "#F2C94C", "c3": "#5AD1E8"}, ["cabelo", "acessorio"], "normal", None, _mulher_gato),
    "coringa": ("Coringa", {"c1": "#6C3FA3", "c2": "#3FAE6B", "c3": "#F08A2C", "pele": "#F4F1EA", "cabelo": "#3FAE6B",
                            "boca_linha": "#B01E2A", "boca_dentro": "#6A0F18", "lingua": "#E0506A"}, [], "normal", "topete", _coringa),
}
