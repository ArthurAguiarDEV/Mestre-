"""Animações, expressões e PERSONALIDADES do personagem, tudo em dados (o app e a página de teste leem o mesmo).

Uma pose é um dicionário "no.canal" -> número. Canais: x y r sx sy (posição, giro em graus no sentido horário da tela,
escala). Nos braços (braco, antebraco, mao), `r` POSITIVO no lado esquerdo (da tela) gira para fora; no lado direito
tudo é espelhado: o NEGATIVO gira para fora. Pose simétrica = mesmo número com o sinal trocado nos dois lados.
Faixa (trilha) de um clipe: {"seno": [base, amplitude, ciclos, fase]} (ciclos SEMPRE inteiros: o clipe emenda) ou
{"k": [[t, valor], ...]} com t de 0 a 1 (curva contínua entre os pontos, sem passar do valor de nenhum deles).
Clipe: dur (s), loop, trilhas, expr (expressão enquanto toca), boca (lista [[t, visema]]), extras (enfeites da janela).
Depois da pose, MOLAS dão inércia (braço atrasa e balança, cabelo e capa ficam para trás): ninguém para seco.
"""
from .arte import n


def S(base, amp, ciclos=1, fase=0.0) -> dict:
    return {"seno": [n(base), n(amp), int(ciclos), n(fase)]}


def K(*pares) -> dict:
    return {"k": [[n(t), n(v)] for t, v in pares]}


def clip(dur, trilhas, loop=False, expr=None, boca=None, extras=None, gesto=False) -> dict:
    d = {"dur": dur, "loop": loop, "trilhas": trilhas}
    if expr:
        d["expr"] = expr
    if boca:
        d["boca"] = boca
    if extras:
        d["extras"] = extras
    if gesto:
        d["gesto"] = True
    return d


ASSENTA = 0.93   # a pose "segurada" vai cedendo um pouco (nunca fica congelada)


def _seg(t0, t1, v):
    """Chega em v em t0, vai assentando até t1 e volta a 0 (pose que vem e vai)."""
    return K((0, 0), (t0, v), (t1, v * ASSENTA), (1, 0))


def _pos(chaves: dict, t0=0.2, t1=0.85) -> dict:
    """{canal: valor}: cada canal vai até o valor, assenta e volta."""
    return {c: _seg(t0, t1, v) for c, v in chaves.items()}


def _vai_e_vem(t0, t1, v, amp, vezes) -> dict:
    """Chega em v, oscila `vezes` vezes em volta de v (+-amp) e volta a 0 (aceno, palmas, coçar)."""
    pts = [(0, 0), (t0, v)]
    passo = (t1 - t0) / (2 * vezes)
    for i in range(1, 2 * vezes):
        pts.append((t0 + passo * i, v + (amp if i % 2 else -amp)))
    return K(*pts, (t1, v), (1, 0))


CLIPES: dict = {
    # --- bases (repetem) ------------------------------------------------------------------------------
    "parado": clip(6.4, {
        "torso.sy": S(1, .012, 2), "torso.y": S(0, -.7, 2), "cabeca.y": S(0, -.6, 2, .1), "cabeca.r": S(0, 1.4, 1),
        "braco_e.r": S(7, 3, 2, .3), "braco_d.r": S(-7, -2.6, 3, .55), "antebraco_e.r": S(8, 4, 2, .42),
        "antebraco_d.r": S(-8, -3.4, 3, .7), "mao_e.r": S(3, 5, 2, .55), "mao_d.r": S(-3, -5, 3, .8),
        "capa.r": S(0, 1.8, 1), "cabelo_frente.r": S(0, .7, 2, .3), "cabelo_tras.r": S(0, 1.4, 1, .5)}, True),
    "levitar": clip(3.2, {"raiz.y": S(-9, -3.5, 1), "sombra.sx": S(.8, -.05, 1), "sombra.o": S(.55, -.12, 1),
                          "capa.r": S(0, 3, 1, .25), "braco_e.r": S(0, 3, 1, .2), "braco_d.r": S(0, -3, 1, .2)}, True),
    "quicar": clip(1.6, {"raiz.y": S(-1.6, -1.6, 2, .25), "torso.sy": S(1, .025, 2, .5), "cabeca.y": S(0, -1, 2, .5),
                         "braco_e.r": S(0, 2.5, 2, .4), "braco_d.r": S(0, -2.5, 2, .4)}, True),
    "ouvir_inclinar": clip(3.2, {
        "cabeca.r": S(-8, 1, 1), "cabeca.x": S(-3, .6, 1), "torso.r": S(-2, .4, 1), "braco_e.r": S(16, 2.5, 2, .3),
        "braco_d.r": S(-22, -2.5, 2, .3), "antebraco_e.r": S(10, 4, 2, .5), "antebraco_d.r": S(-14, -4, 2, .5),
        "mao_e.r": S(0, 6, 2, .6), "torso.y": S(0, -.6, 2), "cabeca.y": S(0, -.5, 2, .1)}, True),
    "ouvir_atento": clip(3.2, {
        "cabeca.r": S(-3, .4, 1), "cabeca.y": S(-2, -.4, 2), "torso.y": S(-1, -.4, 2), "braco_e.r": S(3, 1.4, 2),
        "braco_d.r": S(-3, -1.4, 2), "antebraco_e.r": S(4, 2, 2, .3), "antebraco_d.r": S(-4, -2, 2, .3)}, True),
    "ouvir_holo": clip(3.2, {
        "cabeca.r": S(-5, 1, 1), "braco_e.r": S(48, 3, 2, .3), "antebraco_e.r": S(-20, 4, 2), "braco_d.r": S(-14, -2, 2, .3),
        "mao_e.r": S(-10, 8, 2, .2), "torso.y": S(0, -.6, 2)}, True, extras=["holo"]),
    "pensar_queixo": clip(3.2, {
        "cabeca.r": S(7, 1.2, 1), "cabeca.y": S(0, -.5, 2), "braco_d.r": S(16, 1.2, 2), "antebraco_d.r": S(142, 3, 2, .2),
        "mao_d.r": S(-20, 6, 4, .1), "braco_e.r": S(-12, 1.4, 2, .3), "antebraco_e.r": S(-58, 2, 2, .3),
        "torso.y": S(0, -.6, 2), "torso.r": S(1.5, .4, 1)}, True),
    "pensar_holo": clip(3.2, {
        "cabeca.r": S(6, 1.2, 1), "braco_e.r": S(44, 3, 2), "antebraco_e.r": S(-30, 12, 4), "braco_d.r": S(-44, -3, 2, .5),
        "antebraco_d.r": S(30, -12, 4, .3), "mao_e.r": S(0, 10, 4, .1), "mao_d.r": S(0, -10, 4, .4), "torso.y": S(0, -.6, 2)},
        True, extras=["holo"]),
    "pensar_cruzado": clip(3.2, {
        "cabeca.r": S(-4, .8, 1), "braco_e.r": S(-38, .8, 2), "antebraco_e.r": S(-62, 1, 2), "braco_d.r": S(38, .8, 2, .3),
        "antebraco_d.r": S(62, 1, 2, .3), "mao_d.r": S(0, 8, 4, .2), "torso.y": S(0, -.5, 2)}, True),
    "dormir": clip(6.4, {
        "cabeca.r": S(9, 1.6, 1), "cabeca.y": S(4, 1.2, 1), "torso.sy": S(.99, .018, 1), "torso.y": S(1, -.6, 1),
        "braco_e.r": S(4, .8, 1), "braco_d.r": S(-4, -.8, 1), "antebraco_e.r": S(-6, 1, 1), "antebraco_d.r": S(6, 1, 1),
        "capa.r": S(0, .8, 1), "cabelo_frente.r": S(0, .5, 1, .3)}, True),
    "andar": clip(.72, {
        "perna_e.r": S(0, 24, 1), "perna_d.r": S(0, -24, 1), "perna_e.y": S(-1.6, -1.6, 2, .25), "perna_d.y": S(-1.6, -1.6, 2, .75),
        "braco_e.r": S(8, -22, 1), "braco_d.r": S(-8, -22, 1), "antebraco_e.r": S(14, 10, 1, .2), "antebraco_d.r": S(-14, 10, 1, .2),
        "mao_e.r": S(0, 14, 1, .35), "mao_d.r": S(0, 14, 1, .35),
        "torso.y": S(-1.7, -1.7, 2, .25), "torso.r": S(0, 3, 1), "cabeca.r": S(0, 2, 1, .5), "cabeca.y": S(0, -.8, 2, .5),
        "capa.r": S(0, 8, 1, .2), "cabelo_tras.r": S(0, 4, 1, .3), "raiz.y": S(-.6, -.6, 2, .25)}, True, gesto=False),
    # --- falando: a cabeça e o tronco acompanham o ritmo; os braços vêm de POSES_FALA (uma "batida" por frase) -------
    "falar_gesticular": clip(3.2, {
        "braco_e.r": S(6, 5, 1), "antebraco_e.r": S(8, 7, 2, .2), "braco_d.r": S(-6, -5, 1, .5), "antebraco_d.r": S(-8, -7, 2, .7),
        "mao_e.r": S(0, 8, 3, .1), "mao_d.r": S(0, -8, 3, .6),
        "cabeca.r": S(0, 4, 1, .25), "cabeca.y": S(0, -1.5, 3), "torso.r": S(0, 2, 1, .4), "torso.y": S(0, -1, 3)}, True, gesto=True),
    "falar_discreto": clip(3.2, {
        "braco_d.r": S(-4, -3, 1), "antebraco_d.r": S(-6, -5, 1, .3), "braco_e.r": S(4, 1, 2), "mao_d.r": S(0, -6, 2, .3),
        "cabeca.y": S(0, -1, 2), "cabeca.r": S(0, 2, 1, .25), "torso.y": S(0, -.5, 2)}, True, gesto=True),
    "falar_empolgado": clip(3.2, {
        "braco_e.r": S(10, 10, 2), "antebraco_e.r": S(10, 10, 2, .3), "braco_d.r": S(-10, -10, 2, .5), "antebraco_d.r": S(-10, -10, 2, .8),
        "mao_e.r": S(0, 12, 4, .1), "mao_d.r": S(0, -12, 4, .6),
        "raiz.y": S(-2, -2, 4), "torso.r": S(0, 4, 2, .3), "cabeca.r": S(0, 6, 2, .25), "cabeca.y": S(0, -2, 4, .1)}, True, gesto=True),
    "falar_contido": clip(3.2, {
        "cabeca.y": S(0, -1.2, 2), "cabeca.r": S(0, 1.6, 1), "braco_d.r": S(-4, -2, 1), "braco_e.r": S(4, 1.4, 1, .5),
        "mao_d.r": S(0, -4, 2, .2)}, True, gesto=True),
    "falar_holo": clip(3.2, {
        "braco_e.r": S(40, 8, 1), "antebraco_e.r": S(-20, 8, 2), "braco_d.r": S(-40, -8, 1, .5), "antebraco_d.r": S(20, -8, 2, .5),
        "mao_e.r": S(-8, 10, 2, .2), "mao_d.r": S(8, -10, 2, .7),
        "cabeca.r": S(0, 2, 1, .25), "torso.y": S(0, -.5, 2)}, True, extras=["holo"], gesto=True),
    # --- gestos avulsos (tocam uma vez) --------------------------------------------------------------------
    "acenar": clip(2.0, {
        "braco_d.r": K((0, 0), (.15, -146), (.85, -140), (1, 0)),
        "antebraco_d.r": _vai_e_vem(.15, .88, -30, 26, 3), "mao_d.r": _vai_e_vem(.18, .88, -8, 22, 3),
        "braco_e.r": _seg(.2, .85, 10), "cabeca.r": _seg(.2, .85, -5), "torso.r": _seg(.2, .85, 2)}, expr="feliz"),
    "alongar": clip(2.8, {
        **_pos({"braco_e.r": 172, "braco_d.r": -172, "antebraco_e.r": -10, "antebraco_d.r": 10, "mao_e.r": -30,
                "mao_d.r": 30, "cabeca.y": -3}, .3, .7),
        "torso.sy": K((0, 1), (.3, 1.06), (.7, 1.05), (1, 1)), "torso.r": K((0, 0), (.35, 3), (.55, -3), (.7, 0), (1, 0))},
        expr="radiante"),
    "pular": clip(1.1, {
        "raiz.y": K((0, 0), (.14, 3), (.42, -38), (.58, -37), (.8, 0), (.88, 2.5), (1, 0)),
        "raiz.sy": K((0, 1), (.14, .92), (.3, 1.06), (.6, 1.04), (.8, .94), (.9, 1.03), (1, 1)),
        "raiz.sx": K((0, 1), (.14, 1.06), (.3, .96), (.6, .97), (.8, 1.05), (.9, .98), (1, 1)),
        "braco_e.r": K((0, 0), (.14, -12), (.4, 140), (.6, 136), (.85, 10), (1, 0)),
        "braco_d.r": K((0, 0), (.14, 12), (.4, -140), (.6, -136), (.85, -10), (1, 0)),
        "antebraco_e.r": K((0, 0), (.14, 10), (.4, 20), (.85, 0), (1, 0)), "antebraco_d.r": K((0, 0), (.14, -10), (.4, -20), (.85, 0), (1, 0)),
        "perna_e.r": K((0, 0), (.4, 14), (.6, 13), (.8, 0), (1, 0)), "perna_d.r": K((0, 0), (.4, -14), (.6, -13), (.8, 0), (1, 0)),
        "sombra.sx": K((0, 1), (.42, .68), (.58, .68), (.8, 1), (1, 1)), "sombra.o": K((0, 1), (.42, .45), (.58, .45), (.8, 1), (1, 1)),
        "capa.r": K((0, 0), (.14, 0), (.4, 10), (.8, -8), (1, 0))}, expr="radiante"),
    "dancar": clip(3.6, {
        "torso.r": S(0, 7, 2), "raiz.y": S(-2.5, -2.5, 4), "braco_e.r": S(60, 45, 2), "braco_d.r": S(-60, -45, 2, .5),
        "antebraco_e.r": S(30, 30, 2, .25), "antebraco_d.r": S(-30, -30, 2, .75), "mao_e.r": S(0, 20, 4), "mao_d.r": S(0, -20, 4, .5),
        "perna_e.r": S(0, 10, 2), "perna_d.r": S(0, 10, 2, .5),
        "cabeca.r": S(0, 6, 2, .25), "cabeca.y": S(0, -2, 4), "capa.r": S(0, 8, 2, .3), "cabelo_tras.r": S(0, 6, 2, .3),
        "sombra.sx": S(.96, .04, 4)}, expr="radiante"),
    "olhar_em_volta": clip(3.0, {
        "cabeca.r": K((0, 0), (.2, -8), (.4, -7.5), (.5, 0), (.62, 8), (.82, 7.5), (1, 0)),
        "cabeca.x": K((0, 0), (.2, -3), (.4, -2.8), (.5, 0), (.62, 3), (.82, 2.8), (1, 0)),
        "iris_e.x": K((0, 0), (.15, -3.4), (.4, -3.4), (.5, 0), (.6, 3.4), (.85, 3.4), (1, 0)),
        "iris_d.x": K((0, 0), (.15, -3.4), (.4, -3.4), (.5, 0), (.6, 3.4), (.85, 3.4), (1, 0)),
        "braco_e.r": K((0, 0), (.2, 6), (.5, 0), (.62, -4), (1, 0)), "braco_d.r": K((0, 0), (.2, 4), (.5, 0), (.62, -6), (1, 0)),
        "torso.r": K((0, 0), (.2, -2), (.4, -2), (.5, 0), (.62, 2), (.82, 2), (1, 0))}),
    "assobiar": clip(2.8, {
        "cabeca.r": S(0, 4, 2), "torso.r": S(0, 2, 2, .25), "raiz.y": S(-.6, -.6, 4), "braco_e.r": _seg(.15, .9, 10),
        "antebraco_e.r": _seg(.15, .9, 12), "mao_e.r": S(0, 12, 4), "braco_d.r": S(-4, -4, 2, .25), "capa.r": S(0, 3, 2)},
        expr="feliz", boca=[[0, "fechada"], [.12, "o_peq"], [.9, "o_peq"], [1, "fechada"]], extras=["notas"]),
    "reverencia": clip(2.6, {
        "torso.sy": K((0, 1), (.3, .88), (.62, .89), (1, 1)), "torso.y": K((0, 0), (.3, 5), (.62, 4.6), (1, 0)),
        "cabeca.y": K((0, 0), (.3, 10), (.62, 9.4), (1, 0)), "cabeca.sy": K((0, 1), (.3, .95), (.62, .95), (1, 1)),
        "braco_d.r": _seg(.3, .62, 34), "antebraco_d.r": _seg(.3, .62, 108), "mao_d.r": _seg(.3, .62, 10),
        "braco_e.r": _seg(.3, .62, -24), "antebraco_e.r": _seg(.3, .62, -30)}, expr="calmo"),
    "ajustar_gravata": clip(2.2, {
        "braco_d.r": _seg(.25, .75, 30), "antebraco_d.r": K((0, 0), (.25, 150), (.4, 138), (.5, 152), (.6, 138), (.75, 148), (1, 0)),
        "mao_d.r": K((0, 0), (.25, 10), (.45, -12), (.6, 10), (.75, 0), (1, 0)),
        "cabeca.y": _seg(.25, .75, -2), "cabeca.r": _seg(.25, .75, 3)}, expr="neutro"),
    "escanear": clip(3.6, {
        "cabeca.r": K((0, 0), (.25, -10), (.5, 0), (.75, 10), (1, 0)),
        "iris_e.x": K((0, 0), (.25, -3), (.5, 0), (.75, 3), (1, 0)), "iris_d.x": K((0, 0), (.25, -3), (.5, 0), (.75, 3), (1, 0)),
        "braco_e.r": _seg(.2, .8, 56), "antebraco_e.r": _seg(.2, .8, 50), "mao_e.r": K((0, 0), (.2, -20), (.5, 10), (.8, -20), (1, 0))},
        expr="neutro", extras=["holo"]),
    "holograma": clip(3.0, {
        **_pos({"braco_e.r": 72, "braco_d.r": -72, "antebraco_e.r": -30, "antebraco_d.r": 30}, .25, .75),
        "mao_e.r": K((0, 0), (.25, -15), (.4, 5), (.55, -15), (.75, 0), (1, 0)),
        "mao_d.r": K((0, 0), (.25, 15), (.4, -5), (.55, 15), (.75, 0), (1, 0)),
        "cabeca.r": _seg(.25, .75, 3)}, expr="neutro", extras=["holo"]),
    "punho": clip(1.6, {
        "braco_d.r": K((0, 0), (.15, -40), (.3, -108), (.42, -92), (.55, -108), (.7, -92), (.85, -20), (1, 0)),
        "antebraco_d.r": K((0, 0), (.3, -76), (.85, -72), (1, 0)), "raiz.y": K((0, 0), (.3, -6), (.42, 0), (.55, -6), (.7, 0), (1, 0)),
        "braco_e.r": _seg(.3, .8, -10), "antebraco_e.r": _seg(.3, .8, -40),
        "torso.r": _seg(.3, .8, 3), "cabeca.r": _seg(.3, .8, -5)}, expr="radiante"),
    "correr_parado": clip(2.0, {
        "perna_e.r": S(0, 35, 4), "perna_d.r": S(0, 35, 4, .5), "raiz.y": S(-2, -2, 8), "braco_e.r": S(20, 40, 4, .5),
        "braco_d.r": S(-20, -40, 4), "antebraco_e.r": S(-50, 10, 4, .6), "antebraco_d.r": S(50, 10, 4, .1),
        "torso.r": S(0, 3, 4), "cabeca.r": S(0, 2, 4, .25), "capa.r": S(0, 8, 4)}, expr="radiante"),
    "celebrar": clip(2.8, {
        "raiz.y": K((0, 0), (.1, 3), (.25, -36), (.4, 0), (.5, 3), (.65, -36), (.8, 0), (.88, 2), (1, 0)),
        "braco_e.r": K((0, 0), (.15, 168), (.85, 160), (1, 0)), "braco_d.r": K((0, 0), (.15, -168), (.85, -160), (1, 0)),
        "antebraco_e.r": S(0, 10, 4, .2), "antebraco_d.r": S(0, -10, 4, .2), "mao_e.r": S(0, 18, 4), "mao_d.r": S(0, -18, 4),
        "torso.r": S(0, 4, 2),
        "sombra.sx": K((0, 1), (.25, .7), (.4, 1), (.65, .7), (.8, 1), (1, 1))}, expr="radiante"),
    "cruzar_bracos": clip(3.5, {
        **_pos({"braco_e.r": -38, "antebraco_e.r": -62, "braco_d.r": 38, "antebraco_d.r": 62, "cabeca.r": -2}, .2, .85)}, expr="neutro"),
    "olhar_relogio": clip(3.0, {
        "braco_e.r": _seg(.2, .85, -14), "antebraco_e.r": _seg(.2, .85, -118), "mao_e.r": _seg(.2, .85, -20),
        "cabeca.y": _seg(.3, .8, 3), "cabeca.r": _seg(.3, .8, -3),
        "iris_e.y": _seg(.3, .8, 3), "iris_d.y": _seg(.3, .8, 3), "iris_e.x": _seg(.3, .8, -2), "iris_d.x": _seg(.3, .8, -2)},
        expr="neutro"),
    "dar_de_ombros": clip(1.7, {
        "braco_e.r": _seg(.2, .7, 30), "braco_d.r": _seg(.2, .7, -30), "antebraco_e.r": _seg(.2, .7, 40), "antebraco_d.r": _seg(.2, .7, -40),
        "mao_e.r": _seg(.2, .7, 30), "mao_d.r": _seg(.2, .7, -30),
        "torso.y": _seg(.2, .7, -3), "cabeca.r": _seg(.2, .7, -8)}, expr="duvida"),
    "surpresa": clip(1.3, {
        "raiz.y": K((0, 0), (.1, -12), (.3, -6), (.5, 0), (1, 0)), "torso.sy": K((0, 1), (.1, 1.05), (.5, 1), (1, 1)),
        "braco_e.r": K((0, 0), (.15, 40), (.8, 30), (1, 0)), "braco_d.r": K((0, 0), (.15, -40), (.8, -30), (1, 0)),
        "antebraco_e.r": K((0, 0), (.15, 30), (.8, 20), (1, 0)), "antebraco_d.r": K((0, 0), (.15, -30), (.8, -20), (1, 0)),
        "sombra.sx": K((0, 1), (.1, .8), (.5, 1), (1, 1))}, expr="surpreso"),
    "assentir": clip(1.0, {"cabeca.y": K((0, 0), (.2, 5), (.4, -1), (.6, 5), (.8, -1), (1, 0))}, expr="feliz"),
    "negar": clip(1.2, {"cabeca.r": K((0, 0), (.15, -10), (.4, 10), (.65, -10), (.85, 6), (1, 0))}, expr="neutro"),
    "bocejar": clip(2.6, {
        "cabeca.y": _seg(.2, .8, -3), "torso.sy": K((0, 1), (.3, 1.03), (.7, 1.03), (1, 1)), "braco_e.r": _seg(.2, .8, 14),
        "braco_d.r": _seg(.2, .8, -150), "antebraco_d.r": _seg(.2, .8, 118), "mao_d.r": _seg(.2, .8, 20)},
        expr="sonolento", boca=[[0, "fechada"], [.2, "A"], [.8, "A"], [1, "fechada"]]),
    # --- gestos novos com os braços (2ª rodada, 30/09) -------------------------------------------------------
    "maos_na_cintura": clip(3.4, {
        **_pos({"braco_e.r": 42, "antebraco_e.r": -84, "mao_e.r": -40, "braco_d.r": -42, "antebraco_d.r": 84, "mao_d.r": 40,
                "torso.y": -1}, .2, .82),
        "cabeca.r": K((0, 0), (.25, 4), (.5, -3), (.8, 2), (1, 0))}, expr="feliz"),
    "cocar_cabeca": clip(2.6, {
        "braco_d.r": _seg(.22, .8, -118), "antebraco_d.r": _vai_e_vem(.22, .8, -64, 5, 4), "mao_d.r": _vai_e_vem(.25, .8, 20, 14, 4),
        "cabeca.r": _seg(.22, .8, -7), "braco_e.r": _seg(.25, .8, 6)}, expr="duvida"),
    "apontar": clip(2.2, {
        "braco_d.r": K((0, 0), (.18, -94), (.3, -88), (.8, -86), (1, 0)), "antebraco_d.r": _seg(.18, .8, -6),
        "mao_d.r": _seg(.18, .8, -6), "cabeca.r": _seg(.2, .8, 6), "cabeca.x": _seg(.2, .8, 2),
        "iris_e.x": _seg(.15, .8, 3.4), "iris_d.x": _seg(.15, .8, 3.4), "braco_e.r": _seg(.2, .8, -6)}, expr="curioso"),
    "bater_palmas": clip(2.4, {
        "braco_e.r": _seg(.15, .85, -18), "braco_d.r": _seg(.15, .85, 18),
        "antebraco_e.r": _vai_e_vem(.15, .85, -30, 11, 5), "antebraco_d.r": _vai_e_vem(.15, .85, 30, 11, 5),
        "mao_e.r": _seg(.15, .85, -20), "mao_d.r": _seg(.15, .85, 20),
        "raiz.y": S(0, -1.2, 5), "cabeca.r": S(0, 3, 2)}, expr="radiante"),
    "joinha": clip(2.2, {
        "braco_d.r": _seg(.2, .8, 4), "antebraco_d.r": _seg(.2, .8, 156), "mao_d.r": _seg(.2, .8, 75),
        "cabeca.r": _seg(.2, .8, -4), "raiz.y": K((0, 0), (.25, -3), (.35, 0), (1, 0))}, expr="radiante"),
    "flexionar": clip(2.4, {
        **_pos({"braco_e.r": 88, "braco_d.r": -88}, .2, .8),
        "antebraco_e.r": _vai_e_vem(.2, .8, 92, 8, 3), "antebraco_d.r": _vai_e_vem(.2, .8, -92, 8, 3),
        "torso.sy": K((0, 1), (.25, 1.03), (.8, 1.03), (1, 1)), "cabeca.r": _seg(.2, .8, 3)}, expr="radiante"),
    "bracos_abertos": clip(2.4, {
        **_pos({"braco_e.r": 74, "braco_d.r": -74, "antebraco_e.r": 18, "antebraco_d.r": -18, "mao_e.r": 20, "mao_d.r": -20,
                "cabeca.y": -2}, .2, .78),
        "raiz.y": K((0, 0), (.15, 2), (.3, -6), (.45, 0), (1, 0))}, expr="radiante"),
    "olhar_unhas": clip(3.2, {
        "braco_d.r": _seg(.2, .82, 22), "antebraco_d.r": _seg(.2, .82, 132), "mao_d.r": K((0, 0), (.2, -30), (.5, -10), (.82, -28), (1, 0)),
        "cabeca.r": _seg(.25, .8, 5), "iris_e.y": _seg(.25, .8, 2.5), "iris_d.y": _seg(.25, .8, 2.5),
        "iris_e.x": _seg(.25, .8, 2), "iris_d.x": _seg(.25, .8, 2)}, expr="neutro"),
    "alongar_lado": clip(3.2, {
        "braco_e.r": K((0, 0), (.2, 160), (.5, 150), (.62, 20), (1, 0)), "braco_d.r": K((0, 0), (.4, -10), (.55, -160), (.85, -150), (1, 0)),
        "antebraco_e.r": K((0, 0), (.2, 30), (.5, 30), (.62, 0), (1, 0)), "antebraco_d.r": K((0, 0), (.55, -30), (.85, -30), (1, 0)),
        "torso.r": K((0, 0), (.25, 7), (.5, 6), (.6, 0), (.72, -7), (.88, -6), (1, 0)),
        "cabeca.r": K((0, 0), (.25, 5), (.5, 5), (.6, 0), (.72, -5), (.88, -5), (1, 0))}, expr="calmo"),
}

# --- braços enquanto fala: uma "batida" (pose) por trecho da frase, sorteada da lista do jeito --------------------
# Somam por cima do clipe de fala, com força pelo volume da voz; a troca de uma para a outra passa pelas molas.
POSES_FALA: dict = {
    "repouso": {},
    "mao_d_aberta": {"braco_d.r": -30, "antebraco_d.r": -22, "mao_d.r": -18},
    "mao_e_aberta": {"braco_e.r": 30, "antebraco_e.r": 22, "mao_e.r": 18},
    "duas_abertas": {"braco_e.r": 34, "antebraco_e.r": 26, "mao_e.r": 16, "braco_d.r": -34, "antebraco_d.r": -26, "mao_d.r": -16},
    "explicar_d": {"braco_d.r": 6, "antebraco_d.r": 104, "mao_d.r": -24},
    "explicar_e": {"braco_e.r": -6, "antebraco_e.r": -104, "mao_e.r": 24},
    "apontar_leve": {"braco_d.r": -62, "antebraco_d.r": -12, "mao_d.r": -6},
    "peito": {"braco_d.r": 20, "antebraco_d.r": 118, "mao_d.r": 10},
    "ombros": {"braco_e.r": 22, "antebraco_e.r": 34, "mao_e.r": 24, "braco_d.r": -22, "antebraco_d.r": -34, "mao_d.r": -24},
    "contar": {"braco_e.r": -8, "antebraco_e.r": -116, "braco_d.r": 8, "antebraco_d.r": 116, "mao_e.r": 10, "mao_d.r": -10},
    "holo_abrir": {"braco_e.r": 30, "antebraco_e.r": -10, "braco_d.r": -30, "antebraco_d.r": 10, "mao_e.r": -20, "mao_d.r": 20},
}
TROCA_FALA = [0.75, 1.6]   # s entre uma batida e outra (dividido pela pressa do jeito)

# --- inércia: molas por canal (frequência em Hz, amortecimento 0-1; menos = balança mais) -------------------------
MOLAS: dict = {
    "raiz.r": [3, .7], "torso.r": [4, .65], "cabeca.r": [4.5, .6], "cabeca.x": [4, .8],
    "braco_e.r": [3.6, .52], "braco_d.r": [3.6, .52], "antebraco_e.r": [3.1, .42], "antebraco_d.r": [3.1, .42],
    "mao_e.r": [2.7, .36], "mao_d.r": [2.7, .36],
    "cabelo_tras.r": [1.9, .24], "cabelo_frente.r": [2.6, .32], "capa.r": [1.5, .26],
}
# o que fica para trás quando o corpo gira ou anda: canal -> [fator do giro, canais somados, graus por passo, limite]
INERCIA: dict = {
    "capa.r": [-0.6, ["raiz.r", "torso.r"], 10, 16],
    "cabelo_tras.r": [-0.45, ["raiz.r", "torso.r", "cabeca.r"], 3, 6],
}
# vida: um balanço pequeno e contínuo nos braços (a pose nunca fica congelada): canal -> [amplitude, Hz, fase]
VIDA: dict = {
    "braco_e.r": [1.2, .31, .3], "braco_d.r": [-1.2, .27, 1.1], "antebraco_e.r": [1.8, .37, .7],
    "antebraco_d.r": [-1.8, .33, 2.0], "mao_e.r": [3, .46, 0], "mao_d.r": [-3, .41, 1.3],
}

# --- expressões (rosto) ---------------------------------------------------------------------------------
# sobr_e / sobr_d: altura das sobrancelhas; sobr_r: giro da esquerda (a direita gira ao contrário); aber: abertura
# dos olhos (0-1,1); feliz: olhos em arco; boca: visema em repouso; olhar: [x, y] da íris
EXPRESSOES: dict = {
    "neutro": {"sobr_e": 0, "sobr_d": 0, "sobr_r": 0, "aber": 1, "feliz": 0, "boca": "fechada", "olhar": [0, 0]},
    "feliz": {"sobr_e": -1.5, "sobr_d": -1.5, "sobr_r": 0, "aber": 1, "feliz": 0, "boca": "sorriso", "olhar": [0, 0]},
    "radiante": {"sobr_e": -2, "sobr_d": -2, "sobr_r": -3, "aber": 1, "feliz": 1, "boca": "sorriso_aberto", "olhar": [0, 0]},
    "curioso": {"sobr_e": -4.5, "sobr_d": 0, "sobr_r": -5, "aber": 1.06, "feliz": 0, "boca": "o_peq", "olhar": [1, -1]},
    "pensando": {"sobr_e": -3, "sobr_d": -1, "sobr_r": 6, "aber": 1, "feliz": 0, "boca": "linha", "olhar": [2.6, -3.4]},
    "sonolento": {"sobr_e": 1, "sobr_d": 1, "sobr_r": -4, "aber": .3, "feliz": 0, "boca": "fechada", "olhar": [0, 2]},
    "dormindo": {"sobr_e": 1.5, "sobr_d": 1.5, "sobr_r": -4, "aber": .04, "feliz": 0, "boca": "fechada", "olhar": [0, 0]},
    "bravo": {"sobr_e": 2, "sobr_d": 2, "sobr_r": 14, "aber": .9, "feliz": 0, "boca": "linha", "olhar": [0, 0]},
    "surpreso": {"sobr_e": -6.5, "sobr_d": -6.5, "sobr_r": -4, "aber": 1.12, "feliz": 0, "boca": "o_peq", "olhar": [0, 0]},
    "calmo": {"sobr_e": -.5, "sobr_d": -.5, "sobr_r": 0, "aber": .06, "feliz": 0, "boca": "fechada", "olhar": [0, 1]},
    "duvida": {"sobr_e": -3, "sobr_d": -3, "sobr_r": -9, "aber": 1, "feliz": 0, "boca": "linha", "olhar": [0, 0]},
}

# --- personalidades ---------------------------------------------------------------------------------------
# vel: pressa dos movimentos; amp: tamanho dos gestos; base: clipes que se somam ao "parado" (flutuar, quicar);
# postura: ajustes fixos do "parado"; estado -> clipe/expressão; idle: [(gesto, peso)] sorteados a cada `intervalo` s;
# fala: [(pose de POSES_FALA, peso)] dos braços enquanto fala;
# passeio: modo (fixo|curto|tela|livre), alcance (px), vel (px/s), pausa [min, max] (s), andar (anda|flutua)
ARQUETIPOS: dict = {
    "parceiro": {
        "nome": "Parceiro", "vel": 1.0, "amp": 1.0, "base": [], "postura": {},
        "estado": {"idle": ["parado", "feliz"], "ouvindo": ["ouvir_inclinar", "curioso"], "pensando": ["pensar_queixo", "pensando"],
                   "falando": ["falar_gesticular", "feliz"], "descansando": ["dormir", "dormindo"]},
        "idle": [["acenar", 3], ["alongar", 1], ["dancar", 2], ["pular", 1], ["olhar_em_volta", 3], ["assobiar", 2], ["dar_de_ombros", 1],
                 ["maos_na_cintura", 2], ["cocar_cabeca", 2], ["bater_palmas", 1], ["joinha", 2], ["apontar", 1]],
        "fala": [["mao_d_aberta", 3], ["mao_e_aberta", 3], ["duas_abertas", 2], ["explicar_d", 2], ["explicar_e", 2], ["ombros", 1],
                 ["repouso", 1]],
        "intervalo": [5, 11], "piscar": [2.6, 5.5], "olhar_mouse": 1.0,
        "passeio": {"modo": "curto", "alcance": 280, "vel": 70, "pausa": [6, 14], "andar": "anda"},
        "chegada": "acenar", "aura": ""},
    "mordomo": {
        "nome": "Mordomo", "vel": .78, "amp": .8, "base": [], "postura": {"braco_e.r": -5, "braco_d.r": 5, "cabeca.y": -1.5, "antebraco_e.r": -12, "antebraco_d.r": 12},
        "estado": {"idle": ["parado", "calmo"], "ouvindo": ["ouvir_atento", "neutro"], "pensando": ["pensar_queixo", "pensando"],
                   "falando": ["falar_discreto", "neutro"], "descansando": ["dormir", "dormindo"]},
        "idle": [["reverencia", 3], ["ajustar_gravata", 3], ["olhar_em_volta", 1], ["assentir", 2], ["olhar_unhas", 1]],
        "fala": [["peito", 2], ["mao_d_aberta", 2], ["explicar_d", 1], ["repouso", 3]],
        "intervalo": [9, 20], "piscar": [3.4, 7], "olhar_mouse": .5,
        "passeio": {"modo": "curto", "alcance": 120, "vel": 34, "pausa": [16, 36], "andar": "anda"},
        "chegada": "reverencia", "aura": ""},
    "jarvis": {
        "nome": "Jarvis", "vel": .95, "amp": .9, "base": ["levitar"], "postura": {"braco_e.r": 10, "braco_d.r": -10},
        "estado": {"idle": ["parado", "neutro"], "ouvindo": ["ouvir_holo", "curioso"], "pensando": ["pensar_holo", "pensando"],
                   "falando": ["falar_holo", "neutro"], "descansando": ["dormir", "dormindo"]},
        "idle": [["escanear", 4], ["holograma", 3], ["olhar_em_volta", 2], ["assentir", 1], ["apontar", 1]],
        "fala": [["holo_abrir", 3], ["explicar_d", 2], ["explicar_e", 2], ["repouso", 1]],
        "intervalo": [7, 15], "piscar": [3, 6], "olhar_mouse": 1.2,
        "passeio": {"modo": "livre", "alcance": 380, "vel": 46, "pausa": [8, 20], "andar": "flutua"},
        "chegada": "holograma", "aura": "#5AD7FF"},
    "coach": {
        "nome": "Coach", "vel": 1.5, "amp": 1.3, "base": ["quicar"], "postura": {"braco_e.r": 14, "braco_d.r": -14, "antebraco_e.r": 18, "antebraco_d.r": -18},
        "estado": {"idle": ["parado", "feliz"], "ouvindo": ["ouvir_inclinar", "curioso"], "pensando": ["pensar_queixo", "pensando"],
                   "falando": ["falar_empolgado", "radiante"], "descansando": ["dormir", "dormindo"]},
        "idle": [["punho", 3], ["pular", 3], ["correr_parado", 2], ["alongar", 2], ["celebrar", 1], ["dancar", 1], ["flexionar", 2],
                 ["bater_palmas", 2], ["joinha", 2], ["bracos_abertos", 1]],
        "fala": [["duas_abertas", 3], ["apontar_leve", 3], ["explicar_d", 2], ["contar", 2], ["mao_d_aberta", 2]],
        "intervalo": [4, 8], "piscar": [2.4, 5], "olhar_mouse": 1.0,
        "passeio": {"modo": "tela", "alcance": 900, "vel": 130, "pausa": [3, 8], "andar": "anda"},
        "chegada": "celebrar", "aura": ""},
    "serio": {
        "nome": "Sério", "vel": .85, "amp": .7, "base": [], "postura": {"braco_e.r": 1.5, "braco_d.r": -1.5, "antebraco_e.r": 0, "antebraco_d.r": 0},
        "estado": {"idle": ["parado", "neutro"], "ouvindo": ["ouvir_atento", "neutro"], "pensando": ["pensar_cruzado", "pensando"],
                   "falando": ["falar_contido", "neutro"], "descansando": ["dormir", "dormindo"]},
        "idle": [["cruzar_bracos", 5], ["olhar_relogio", 2], ["olhar_em_volta", 1], ["negar", 1], ["maos_na_cintura", 1],
                 ["alongar_lado", 1]],
        "fala": [["repouso", 4], ["explicar_d", 2], ["mao_d_aberta", 1], ["contar", 1]],
        "intervalo": [11, 24], "piscar": [4, 9], "olhar_mouse": .3,
        "passeio": {"modo": "fixo", "alcance": 0, "vel": 50, "pausa": [30, 60], "andar": "anda"},
        "chegada": "assentir", "aura": ""},
}

ESTILO_PARA_ARQUETIPO = {"Parceiro brasileiro": "parceiro", "Mordomo elegante": "mordomo", "Estilo Jarvis": "jarvis",
                         "Coach animado": "coach", "Sério e direto": "serio"}
ARQUETIPO_PADRAO = "parceiro"
# vogais da fala (letra -> visema); consoantes labiais fecham a boca
VISEMAS_VOGAIS = {"a": "A", "á": "A", "à": "A", "â": "A", "ã": "A", "e": "E", "é": "E", "ê": "E", "i": "I", "í": "I",
                  "o": "O", "ó": "O", "ô": "O", "õ": "O", "u": "U", "ú": "U"}
SEQUENCIA_VISEMAS = ["A", "E", "O", "A", "I", "O", "U", "E", "A", "O", "I", "A"]


def como_dados() -> dict:
    return {"clipes": CLIPES, "expressoes": EXPRESSOES, "arquetipos": ARQUETIPOS, "estilo_para_arquetipo": ESTILO_PARA_ARQUETIPO,
            "arquetipo_padrao": ARQUETIPO_PADRAO, "vogais": VISEMAS_VOGAIS, "sequencia_visemas": SEQUENCIA_VISEMAS,
            "poses_fala": POSES_FALA, "troca_fala": TROCA_FALA, "molas": MOLAS, "inercia": INERCIA, "vida": VIDA}
