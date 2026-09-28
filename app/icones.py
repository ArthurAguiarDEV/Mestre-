"""Icones de linha do painel (menu lateral, cartoes do Inicio, abas da Voz).

Desenhados com o Pillow na hora (nada baixado): cada icone e pensado numa grade de 24 x 24, como os
do prototipo (exportacoes/prototipos/prototipos_v25.html), desenhado grande (8x) e reduzido pelo
CTkImage no tamanho certo para a escala da tela (100/125/150%): fica nitido em qualquer monitor.
"""
from functools import lru_cache

ESCALA = 8          # desenha em 192 x 192 e o customtkinter reduz
TRACO = 1.8         # espessura da linha (na grade de 24)


def _rgb(cor: str) -> tuple[int, int, int, int]:
    cor = cor.lstrip("#")
    return int(cor[0:2], 16), int(cor[2:4], 16), int(cor[4:6], 16), 255


def _pontos_arco(cx, cy, r, de, ate, passos=28):
    import math
    return [(cx + r * math.cos(math.radians(de + (ate - de) * i / passos)),
             cy + r * math.sin(math.radians(de + (ate - de) * i / passos))) for i in range(passos + 1)]


def _quad(p0, p1, p2, passos=16):
    """Curva (como o Q do SVG) virando pontos."""
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
            for t in (i / passos for i in range(passos + 1))]


class _Caneta:
    def __init__(self, d, cor):
        self.d, self.cor = d, cor
        self.w = round(TRACO * ESCALA)

    def _p(self, pts):
        return [(x * ESCALA, y * ESCALA) for x, y in pts]

    def linha(self, *pts):
        pts = self._p(pts)
        self.d.line(pts, fill=self.cor, width=self.w, joint="curve")
        for x, y in (pts[0], pts[-1]):   # pontas redondas
            r = self.w / 2
            self.d.ellipse((x - r, y - r, x + r, y + r), fill=self.cor)

    def fechada(self, *pts):
        self.linha(*pts, pts[0])

    def caixa(self, x1, y1, x2, y2, raio=2.0):
        e = ESCALA
        self.d.rounded_rectangle((x1 * e, y1 * e, x2 * e, y2 * e), radius=raio * e, outline=self.cor, width=self.w)

    def circulo(self, cx, cy, r):
        e = ESCALA
        self.d.ellipse(((cx - r) * e, (cy - r) * e, (cx + r) * e, (cy + r) * e), outline=self.cor, width=self.w)

    def ponto(self, cx, cy, r=1.1):
        e = ESCALA
        self.d.ellipse(((cx - r) * e, (cy - r) * e, (cx + r) * e, (cy + r) * e), fill=self.cor)

    def arco(self, cx, cy, r, de, ate):
        self.linha(*_pontos_arco(cx, cy, r, de, ate))

    def curva(self, p0, p1, p2):
        self.linha(*_quad(p0, p1, p2))

    def cheio(self, *pts):
        self.d.polygon(self._p(pts), fill=self.cor)


def _casa(c):
    c.linha((3, 11), (12, 4), (21, 11))
    c.linha((5, 10), (5, 20), (19, 20), (19, 10))
    c.linha((10, 20), (10, 14), (14, 14), (14, 20))


def _rosto(c):
    c.circulo(12, 12, 9)
    c.curva((8.5, 14.5), (12, 18.2), (15.5, 14.5))
    c.ponto(9, 9.5, 1.2)
    c.ponto(15, 9.5, 1.2)


def _conversa(c):
    c.fechada((4, 5), (20, 5), (20, 15), (9, 15), (4, 19))
    c.linha((8, 9), (16, 9))
    c.linha((8, 12), (13, 12))


def _voz(c):
    for x, y1, y2 in ((4, 10, 14), (8, 7, 17), (12, 4, 20), (16, 8, 16), (20, 11, 13)):
        c.linha((x, y1), (x, y2))


def _mic(c):
    c.caixa(9, 3, 15, 14, 3)
    c.arco(12, 11, 7, 0, 180)
    c.linha((12, 18), (12, 21))
    c.linha((9, 21), (15, 21))


def _youtube(c):
    c.caixa(3, 6, 21, 18, 4)
    c.fechada((10.5, 9.5), (14.5, 12), (10.5, 14.5))


def _musica(c):
    c.linha((9, 18), (9, 6), (20, 4), (20, 16))
    c.circulo(6.5, 18, 2.5)
    c.circulo(17.5, 16, 2.5)


def _janelas(c):
    c.caixa(3, 4, 21, 18, 2)
    c.linha((3, 8), (21, 8))
    c.linha((8, 21), (16, 21))


def _rotina(c):
    c.arco(12, 12, 8, -40, 270)
    c.linha((20, 4), (20, 9), (15, 9))
    c.linha((12, 8), (12, 12), (15, 14))


def _atalho(c):
    c.fechada((13, 3), (5, 14), (11, 14), (10, 21), (18, 10), (12, 10))


def _maleta(c):
    c.caixa(3, 7, 21, 20, 2)
    c.linha((8, 7), (8, 5), (10, 3), (14, 3), (16, 5), (16, 7))
    c.linha((3, 13), (21, 13))


def _celular(c):
    c.caixa(7, 2.5, 17, 21.5, 2.5)
    c.linha((11, 18.5), (13, 18.5))


def _historico(c):
    c.linha((4, 6), (20, 6))
    c.linha((4, 12), (20, 12))
    c.linha((4, 18), (14, 18))


def _lampada(c):
    c.linha((9, 18), (15, 18))
    c.linha((10, 21), (14, 21))
    c.arco(12, 9, 6, 145, 395)
    c.linha((8.6, 13.9), (9.5, 16), (14.5, 16), (15.4, 13.9))


def _check(c):
    c.circulo(12, 12, 9)
    c.linha((8, 12.5), (10.7, 15.2), (16, 9.5))


def _brilho(c):
    c.fechada((12, 3), (13.8, 8.2), (19, 10), (13.8, 11.8), (12, 17), (10.2, 11.8), (5, 10), (10.2, 8.2))
    c.fechada((19, 16), (19.7, 18), (21.7, 18.7), (19.7, 19.4), (19, 21.4), (18.3, 19.4), (16.3, 18.7), (18.3, 18))


def _paleta(c):
    c.arco(12, 12, 9, 80, 330)
    c.curva((12, 21), (13.5, 21), (13.5, 19.5))
    c.linha((13.5, 19.5), (12.5, 17.5))
    c.curva((12.5, 17.5), (12.5, 15.5), (14.5, 15.5))
    c.linha((14.5, 15.5), (17, 15.5))
    c.curva((17, 15.5), (21, 15.5), (20, 7.5))
    for x, y in ((7.5, 11), (10, 7), (15, 7.5)):
        c.ponto(x, y, 1.2)


def _play(c):
    c.fechada((7, 5), (19, 12), (7, 19))


def _parar(c):
    c.caixa(6, 6, 18, 18, 2)


def _pausa(c):
    c.linha((9, 5), (9, 19))
    c.linha((15, 5), (15, 19))


def _reiniciar(c):
    c.arco(12, 12, 8, 180, 320)
    c.linha((20, 3), (20, 8), (15, 8))
    c.arco(12, 12, 8, 0, 140)
    c.linha((4, 21), (4, 16), (9, 16))


def _teclado(c):
    c.caixa(2.5, 6, 21.5, 18, 2)
    for x in (6, 10, 14, 18):
        c.ponto(x, 10, 1.1)
    c.linha((7, 14), (17, 14))


def _baixar(c):
    c.linha((12, 4), (12, 15))
    c.linha((7, 10), (12, 15), (17, 10))
    c.linha((5, 20), (19, 20))


def _alto(c):
    c.fechada((4, 9), (4, 15), (8, 15), (13, 19), (13, 5), (8, 9))
    c.arco(13, 12, 4.5, -50, 50)
    c.arco(13, 12, 8, -50, 50)


def _estrela(c):
    c.fechada((12, 3.5), (14.6, 8.8), (20.5, 9.7), (16.2, 13.8), (17.2, 19.6), (12, 16.9), (6.8, 19.6),
              (7.8, 13.8), (3.5, 9.7), (9.4, 8.8))


def _chip(c):
    c.caixa(6, 6, 18, 18, 2)
    for a in (9, 15):
        c.linha((a, 2), (a, 6))
        c.linha((a, 18), (a, 22))
        c.linha((2, a), (6, a))
        c.linha((18, a), (22, a))


def _nuvem(c):
    c.arco(7, 13.5, 4.5, 90, 250)
    c.arco(12, 10.5, 6, 200, 350)
    c.arco(17.5, 14, 4.2, 280, 450)
    c.linha((7, 18), (17.5, 18))


def _pc(c):
    c.caixa(3, 4, 21, 16, 2)
    c.linha((9, 20), (15, 20))
    c.linha((12, 16), (12, 20))


def _chave(c):
    c.circulo(8, 15, 4)
    c.linha((11, 12), (20, 3))
    c.linha((16, 7), (19, 10))


def _robo(c):
    c.caixa(4, 7, 20, 20, 4)
    c.linha((12, 3), (12, 7))
    c.ponto(12, 3, 1.4)
    c.ponto(9, 13, 1.5)
    c.ponto(15, 13, 1.5)
    c.linha((9.5, 17), (14.5, 17))


DESENHOS = {
    "casa": _casa, "rosto": _rosto, "conversa": _conversa, "voz": _voz, "mic": _mic, "youtube": _youtube,
    "musica": _musica, "janelas": _janelas, "rotina": _rotina, "atalho": _atalho, "maleta": _maleta,
    "celular": _celular, "historico": _historico, "lampada": _lampada, "check": _check, "brilho": _brilho,
    "paleta": _paleta, "play": _play, "parar": _parar, "pausa": _pausa, "reiniciar": _reiniciar,
    "teclado": _teclado, "baixar": _baixar, "alto": _alto, "estrela": _estrela, "chip": _chip,
    "nuvem": _nuvem, "pc": _pc, "chave": _chave, "robo": _robo,
}


@lru_cache(maxsize=256)
def imagem(nome: str, cor: str):
    """O icone (Pillow, RGBA, 192 x 192) na cor pedida. Guardado em cache: cada um e desenhado uma vez."""
    from PIL import Image, ImageDraw

    lado = 24 * ESCALA
    im = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    DESENHOS.get(nome, _estrela)(_Caneta(ImageDraw.Draw(im), _rgb(cor)))
    return im


@lru_cache(maxsize=256)
def ctk_icone(nome: str, cor: str, tamanho: int = 20):
    """CTkImage pronto para botao/rotulo (o customtkinter reduz para a escala da tela)."""
    import customtkinter as ctk

    im = imagem(nome, cor)
    return ctk.CTkImage(light_image=im, dark_image=im, size=(tamanho, tamanho))


def _ponto(c):
    e = ESCALA
    c.d.ellipse((5 * e, 5 * e, 19 * e, 19 * e), fill=c.cor)


def _vazio(c):
    pass


DESENHOS.update(ponto=_ponto, vazio=_vazio)


@lru_cache(maxsize=16)
def avatar(cor: str, tamanho: int = 280):
    """Rosto de robo parado (lugar reservado do avatar no Inicio; a versao animada vem depois)."""
    from PIL import Image, ImageDraw

    g = tamanho * 3   # desenha grande e reduz: bordas lisas
    im = Image.new("RGBA", (g, g), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = g / 120   # grade de 120 x 120, igual ao SVG do prototipo

    def p(x, y):
        return (x * u, y * u)
    destaque = _rgb(cor)
    escuro = (28, 17, 23, 255)
    anel = (*destaque[:3], 70)
    d.ellipse((*p(6, 6), *p(114, 114)), outline=anel, width=round(2 * u))
    d.line([p(60, 22), p(60, 12)], fill=destaque, width=round(3 * u))
    d.ellipse((*p(55, 6), *p(65, 16)), fill=destaque)
    d.rounded_rectangle((*p(18, 20), *p(102, 102)), radius=30 * u, fill=destaque)
    for x in (45, 75):
        d.ellipse((*p(x - 6, 50), *p(x + 6, 66)), fill=escuro)
        d.ellipse((*p(x - 2.5, 52), *p(x + 0.5, 56)), fill=(255, 255, 255, 200))
    d.arc((*p(44, 66), *p(76, 88)), start=20, end=160, fill=escuro, width=round(3.5 * u))
    for x in (30, 90):   # bochechas
        d.ellipse((*p(x - 5, 72), *p(x + 5, 78)), fill=(*(int(v * 0.86) for v in destaque[:3]), 255))
    return im.resize((tamanho, tamanho), Image.LANCZOS)


@lru_cache(maxsize=8)
def logo(cor: str, tamanho: int = 128):
    """Logo "Onda" (o "A" com a onda de voz) para o menu do painel. Mesmo desenho do ícone da bandeja e do atalho."""
    from . import tema

    return tema.desenhar_icone(cor, tamanho)
