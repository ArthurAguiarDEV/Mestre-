"""Esqueleto, corpo, rosto e paletas do personagem (dados de desenho; veja arte.py).

Medidas em unidades do personagem: pés em y=0, topo do cabelo perto de y=-200, largura ~ +-60.
O desenho vai para a tela em `escala` (padrão: 170 px de altura, o triplo do bonequinho pixelado do jogo).
Cada nó do esqueleto tem a origem no seu PONTO DE GIRO (ombro, quadril, pescoço...); os filhos usam a
posição relativa ao pai. Lado esquerdo = esquerda da TELA; o direito é o mesmo desenho espelhado (`mir`).
"""
from .arte import el, mapear_d, par, pa, rr, traco

# --- paletas escolhíveis --------------------------------------------------------------------------------
PELES = [("muito_clara", "Muito clara", "#FFE9DE"), ("clara", "Clara", "#FBDCC8"), ("rosada", "Rosada", "#F5C6A8"),
         ("morena_clara", "Morena clara", "#E2AA7C"), ("oliva", "Oliva", "#D1A574"), ("morena", "Morena", "#C48656"),
         ("parda", "Parda", "#9C6640"), ("escura", "Escura", "#6C4128"), ("retinta", "Retinta", "#4B2B1C")]
CORES_CABELO = [("preto", "Preto", "#2B2226"), ("castanho_escuro", "Castanho escuro", "#4B3226"),
                ("castanho", "Castanho", "#7A4E32"), ("loiro", "Loiro", "#E7C36A"), ("platinado", "Platinado", "#F2E7C9"),
                ("ruivo", "Ruivo", "#B8502B"), ("laranja", "Laranja", "#E8792E"), ("vinho", "Vinho", "#7A2338"),
                ("cinza", "Cinza", "#AAB0BA"), ("branco", "Branco", "#EEEEF4"), ("rosa", "Rosa", "#F58CB4"),
                ("lilas", "Lilás", "#B9A0E8"), ("azul", "Azul", "#5B8DEF"), ("azul_escuro", "Azul-escuro", "#2D3F7C"),
                ("turquesa", "Turquesa", "#3FC1C9"), ("verde", "Verde", "#4DBE8B"), ("roxo", "Roxo", "#8F62D8")]
CORES_OLHOS = [("castanho", "Castanho", "#7A4A2A"), ("preto", "Preto", "#332A2F"), ("azul", "Azul", "#4A8FE0"),
               ("verde", "Verde", "#3FA56B"), ("mel", "Mel", "#C08A2E"), ("ambar", "Âmbar", "#D9A441"),
               ("cinza", "Cinza", "#7D8794"), ("turquesa", "Turquesa", "#2FB5B5"), ("roxo", "Roxo", "#8B5FD0"),
               ("vermelho", "Vermelho", "#C63A3A")]
CORES_ROUPA = [("branco", "Branco", "#F2F2F6"), ("preto", "Preto", "#2C2A33"), ("cinza", "Cinza", "#8A8F9B"),
               ("bege", "Bege", "#D8C3A0"), ("vermelho", "Vermelho", "#D9384A"), ("vinho", "Vinho", "#7E2440"),
               ("laranja", "Laranja", "#F08A2C"), ("amarelo", "Amarelo", "#F2C93A"), ("dourado", "Dourado", "#D9A93A"),
               ("verde", "Verde", "#3FAE6B"), ("oliva", "Verde-oliva", "#6B7A3A"), ("turquesa", "Turquesa", "#2FAFB0"),
               ("azul", "Azul", "#3F7BE0"), ("marinho", "Azul-marinho", "#26356B"), ("lilas", "Lilás", "#B79CE0"),
               ("roxo", "Roxo", "#8B5FD0"), ("rosa", "Rosa", "#F27CA8"), ("marrom", "Marrom", "#7A5236")]

PALETA_FIXA = {"linha": "#3B2A30", "branco": "#FFFFFF", "boca_linha": "#8A3A45", "boca_dentro": "#5B1F2B",
               "lingua": "#F27C8C", "blush": "#FF7C8E", "lente": "#FFFFFF", "sombra": "#000000"}

# --- esqueleto ------------------------------------------------------------------------------------------
# slot = de onde vêm as primitivas do nó (corpo, roupa, fantasia...); z<0 = desenhado ANTES do pai;
# seg = acompanha a pose de outro nó; mir = versão espelhada; pos_f = posição só para o corpo feminino;
# inv = giro invertido (antebraço e mão direitos já estão dentro do braço espelhado: assim, no lado direito,
# todo giro positivo fecha para dentro, igual ao braço); contorno = contornos do galho antes dos recheios.
RIG = {"id": "raiz", "pos": [0, 0], "filhos": [
    {"id": "capa", "pos": [0, -98], "slot": "capa", "z": -2, "seg": "torso"},
    {"id": "perna_e", "pos": [-10, -52], "slot": "perna"},
    {"id": "perna_d", "pos": [10, -52], "slot": "perna", "mir": True},
    {"id": "torso", "pos": [0, -56], "slot": "torso", "filhos": [
        {"id": "cabelo_tras", "pos": [0, -46], "slot": "cabelo_tras", "z": -1, "seg": "cabeca"},
        {"id": "cabeca", "pos": [0, -46], "slot": ["cabeca", "bochecha", "nariz"], "filhos": [
            {"id": "mascara_baixo", "pos": [0, 0], "slot": "mascara_baixo"},
            {"id": "olho_e", "pos": [-19, -40], "slot": "olho_fechado", "filhos": [
                {"id": "abertura_e", "pos": [0, 0], "slot": "olho", "filhos": [
                    {"id": "iris_e", "pos": [0, 0], "slot": "iris"}]}]},
            {"id": "olho_d", "pos": [19, -40], "slot": "olho_fechado", "mir": True, "filhos": [
                {"id": "abertura_d", "pos": [0, 0], "slot": "olho", "filhos": [
                    {"id": "iris_d", "pos": [0, 0], "slot": "iris"}]}]},
            {"id": "sobr_e", "pos": [-19, -63], "slot": "sobr"},
            {"id": "sobr_d", "pos": [19, -63], "slot": "sobr", "mir": True},
            {"id": "boca", "pos": [0, -19], "slot": "boca"},
            {"id": "cabelo_frente", "pos": [0, 0], "slot": "cabelo_frente"},
            {"id": "acessorio", "pos": [0, 0], "slot": "acessorio"},
            {"id": "mascara_cima", "pos": [0, 0], "slot": "mascara_cima"}]},
        {"id": "braco_e", "pos": [-24, -38], "pos_f": [-21, -38], "slot": "braco_sup", "contorno": True, "filhos": [
            {"id": "antebraco_e", "pos": [0, 17], "slot": "braco_inf", "filhos": [
                {"id": "mao_e", "pos": [0, 17], "slot": ["mao", "adereco_e"]}]}]},
        {"id": "braco_d", "pos": [24, -38], "pos_f": [21, -38], "slot": "braco_sup", "mir": True, "contorno": True, "filhos": [
            {"id": "antebraco_d", "pos": [0, 17], "slot": "braco_inf", "inv": True, "filhos": [
                {"id": "mao_d", "pos": [0, 17], "slot": ["mao", "adereco_d"], "inv": True}]}]}]}]}

# --- silhuetas ------------------------------------------------------------------------------------------
TORSO_D = {
    "m": "M -23 -38 Q -23 -45 -15 -45 L 15 -45 Q 23 -45 23 -38 L 21 0 Q 21 6 13 6 L -13 6 Q -21 6 -21 0 Z",
    "f": "M -20 -38 Q -20 -45 -13 -45 L 13 -45 Q 20 -45 20 -38 Q 18 -28 15.5 -16 Q 15.5 -8 21 5 Q 21 7 16 7 "
         "L -16 7 Q -21 7 -21 5 Q -15.5 -8 -15.5 -16 Q -18 -28 -20 -38 Z",
}
CABECA_D = ("M 0 -96 C 30 -96 52 -76 52 -48 C 52 -22 34 -3 0 -3 "
            "C -34 -3 -52 -22 -52 -48 C -52 -76 -30 -96 0 -96 Z")


def _pele_v(a="$pele+", b="$pele-"):
    return ["v", a, b]


JUNTA = 17   # do ombro ao cotovelo e do cotovelo ao punho (as posições do RIG)


def segmento(r: float, f, s: str = "$linha", lw: float = 1.6, ate: float = JUNTA) -> list:
    """Pedaço de braço (ou manga) em cápsula centrada nas juntas: contorno grosso marcado `c` + recheio sem linha.
    O nó do braço tem `contorno`: o desenhista pinta todos os contornos do galho antes dos recheios, então o
    cotovelo dobra sem emenda. Barra de manga que precisa de linha vai como traço/peça normal por cima."""
    caixa = (-r, -r, 2 * r, ate + 2 * r, r)
    return [rr(*caixa, None, s, lw * 2, c=1), rr(*caixa, f)]


MAO_D = "M -5.2 1.4 Q -6.7 8.6 -3.4 11.5 Q 0 13.5 3.6 11.3 Q 6.3 8.2 5.2 1.4 Q 0 -1.7 -5.2 1.4 Z"
POLEGAR_D = "M 3.4 2.6 Q 8.7 3 8.2 7.5 Q 7 9.8 4 8.2 Z"


def mao(f, k: float = 1.0, s: str = "$linha", lw: float = 1.6) -> list:
    """Mão em luva de desenho (palma + polegar para dentro); `k` aumenta (luvas de fantasia)."""
    def esc(d):
        return mapear_d(d, lambda x: x * k, lambda y: y * k)
    return [pa(esc(POLEGAR_D), f, s, lw), pa(esc(MAO_D), f, s, lw),
            traco(esc("M -1.2 8.8 Q -1.4 10.6 -0.8 12"), s, 1.1, o=0.45)]


def corpo(g: str) -> dict:
    """Corpo nu (só pele) por nó: as roupas e fantasias desenham por cima nos mesmos slots."""
    p = {}
    p["perna"] = [rr(-7, -3, 14, 53, 7, ["h", "$pele-", "$pele+"], "$linha", 1.6),
                  el(-1.5, 47, 9, 5.4, "$pele", "$linha", 1.6)]
    p["torso"] = [el(0, -46, 7, 5, "$pele-", "$linha", 1.4),
                  pa(TORSO_D[g], _pele_v("$pele", "$pele-"), "$linha", 1.8)]
    p["braco_sup"] = segmento(5.5, ["h", "$pele-", "$pele+"])
    p["braco_inf"] = segmento(5.0, ["h", "$pele-", "$pele+"])
    p["mao"] = mao(["v", "$pele+", "$pele"])
    p["cabeca"] = cabeca(CABECA_D)
    p["bochecha"] = BOCHECHAS["rosadas"][1]
    p["nariz"] = NARIZES["botao"][1]
    return p


# --- rosto escolhível: formato da cabeça, bochechas, nariz (olhos e sobrancelhas logo abaixo) ------------------
FORMATOS = {   # a fantasia volta para o redondo (as máscaras foram desenhadas nele)
    "redondo": ("Redondo", CABECA_D),
    "oval": ("Oval", "M 0 -96 C 30 -96 52 -76 52 -50 C 52 -24 30 0 0 0 C -30 0 -52 -24 -52 -50 C -52 -76 -30 -96 0 -96 Z"),
    "quadrado": ("Quadrado", "M 0 -96 C 30 -96 52 -76 52 -48 C 52 -22 46 -4 0 -4 C -46 -4 -52 -22 -52 -48 C -52 -76 -30 -96 0 -96 Z"),
    "coracao": ("Coração", "M 0 -97 C 32 -97 54 -78 52 -52 C 50 -28 24 -1 0 0 C -24 -1 -50 -28 -52 -52 C -54 -78 -32 -97 0 -97 Z"),
}


def cabeca(d: str) -> list:
    return (par(el(-50.5, -46, 6.2, 9.5, "$pele-", "$linha", 1.6), el(-50, -46, 2.6, 4.6, "$pele--"))
            + [pa(d, _pele_v(), "$linha", 2)])


BOCHECHAS = {
    "rosadas": ("Rosadas", par(el(-29.5, -26, 8.6, 4.8, "$blush", None, 0, 0.36))),
    "coradas": ("Bem coradas", par(el(-29.5, -26, 9.6, 5.4, "$blush", None, 0, 0.62),
                                   traco("M -34 -27 L -32 -24", "#FFFFFF", 1.4, o=0.5), traco("M -29 -27 L -27 -24", "#FFFFFF", 1.4, o=0.5))),
    "sardas": ("Sardas", par(el(-29.5, -26, 8.6, 4.8, "$blush", None, 0, 0.22),
                             *[el(x, y, 1.1, 1.1, "$pele--", None, 0, 0.8) for x, y in ((-36, -30), (-31, -27.5), (-26, -30.5),
                                                                                        (-33, -24), (-28, -24.5), (-22, -27))])),
    "sem": ("Sem", []),
}
NARIZES = {
    "botao": ("Botão", [traco("M -1.6 -29 Q 0 -27.2 1.6 -29", "$pele--", 1.7)]),
    "ponto": ("Pontinho", [el(0, -28.6, 1.6, 1.2, "$pele--")]),
    "arrebitado": ("Arrebitado", [traco("M -1 -34 Q 3.4 -30 2.4 -28.2 Q 0.4 -27.2 -1.6 -28.4", "$pele--", 1.6)]),
    "reto": ("Reto", [traco("M 0.6 -36 L 2 -29.4 Q 0.6 -28 -1.4 -28.8", "$pele--", 1.6)]),
    "sem": ("Sem", []),
}
SOBRANCELHAS = {
    "normal": ("Normal", [traco("M -9.5 1.4 Q 0 -3.2 9.5 1.2", "$cabelo-", 3.6)]),
    "grossa": ("Grossa", [traco("M -9.8 1.6 Q 0 -3.6 9.8 1.2", "$cabelo-", 5.4)]),
    "fina": ("Fina", [traco("M -9.2 1.2 Q 0 -3 9.2 1", "$cabelo-", 2.2)]),
    "reta": ("Reta", [traco("M -9.5 0.6 L 9.5 -0.2", "$cabelo-", 3.8)]),
    "arqueada": ("Arqueada", [traco("M -9.5 2.6 Q -3 -5 9.5 0.2", "$cabelo-", 3.4)]),
}
OLHOS_ESCOLHA = {"normal": "Normal", "grande": "Grandão", "amendoado": "Amendoado", "pontinho": "Pontinho",
                 "cilios": "Cílios longos"}
ROSTO_ORDEM = ["rosto", "bochechas", "nariz", "sobrancelha", "olhos_estilo"]   # chave do perfil, na ordem em que aplica
ROSTO_ROTULOS = {"rosto": "Formato do rosto", "olhos_estilo": "Olhos", "sobrancelha": "Sobrancelhas", "nariz": "Nariz",
                 "bochechas": "Bochechas"}


# --- olhos (3 estilos) e sobrancelhas -------------------------------------------------------------------
def olhos(g: str) -> dict:
    """Estilos do OLHO ESQUERDO (o direito é o espelho). Nós: olho_fechado (não escala), olho, iris."""
    fechado = [traco("M -10 0 Q 0 6.5 10 0", "$linha", 3.2, liga="olhos.fechado"),
               traco("M -10.5 3.5 Q 0 -8.5 10.5 3.5", "$linha", 3.4, liga="olhos.feliz")]
    normal = {
        "olho": [el(0, 0, 11, 13.6, "$branco", "$linha", 1.8),
                 traco("M -12.4 -4 Q -9.5 -15 0 -15.2 Q 9.5 -15 12.4 -4", "$linha", 3.6)]
        + ([traco("M -11.5 -7 Q -15 -8.6 -16.4 -13.4", "$linha", 2.4), traco("M -12.4 -3 Q -16.6 -4 -18.2 -8", "$linha", 2.2)]
           if g == "f" else []),
        "iris": [el(0, 0.8, 8.8, 11.2, ["v", "$olhos+", "$olhos-"]),
                 el(0, 0.8, 8.8, 11.2, None, "$olhos--", 1.1),
                 el(0, 1.8, 4.5, 5.8, "#1A1015"),
                 el(-3.2, -3.4, 3.3, 3.7, "#FFFFFF"), el(3.4, 4.8, 1.6, 1.6, "#FFFFFF", None, 0, 0.9)],
        "olho_fechado": fechado}
    cilios_f = [traco("M -11.5 -7 Q -15 -8.6 -16.4 -13.4", "$linha", 2.4), traco("M -12.4 -3 Q -16.6 -4 -18.2 -8", "$linha", 2.2)]
    grande = {
        "olho": [el(0, -0.6, 12.6, 15.4, "$branco", "$linha", 1.8),
                 traco("M -14 -5 Q -10.6 -17.4 0 -17.6 Q 10.6 -17.4 14 -5", "$linha", 3.8)] + (cilios_f if g == "f" else []),
        "iris": [el(0, 1, 10.2, 12.8, ["v", "$olhos+", "$olhos-"]), el(0, 1, 10.2, 12.8, None, "$olhos--", 1.1),
                 el(0, 2.2, 5, 6.6, "#1A1015"), el(-3.8, -4.2, 4, 4.4, "#FFFFFF"), el(4, 5.6, 2, 2, "#FFFFFF", None, 0, 0.9),
                 el(-4.6, 5.4, 1.3, 1.3, "#FFFFFF", None, 0, 0.8)],
        "olho_fechado": fechado}
    amendoado = {
        "olho": [pa("M -12.6 1.4 Q -8 -10.6 2 -11 Q 10.4 -10.6 13.2 -1.6 Q 8.6 9 -1.6 9.4 Q -10.4 8.8 -12.6 1.4 Z", "$branco", "$linha", 1.8),
                 traco("M -13.6 0.4 Q -8.6 -12.4 2 -12.6 Q 11 -12 14.4 -2.4", "$linha", 3.6),
                 traco("M 13.4 -2.6 L 16.4 -5.4", "$linha", 2.4)] + (cilios_f[:1] if g == "f" else []),
        "iris": [el(0.4, 0, 7.4, 8.6, ["v", "$olhos+", "$olhos-"]), el(0.4, 0, 7.4, 8.6, None, "$olhos--", 1.1),
                 el(0.4, 0.8, 3.8, 4.6, "#1A1015"), el(-2.4, -3, 2.8, 3, "#FFFFFF"), el(3, 3.6, 1.3, 1.3, "#FFFFFF", None, 0, 0.9)],
        "olho_fechado": fechado}
    pontinho = {
        "olho": [],
        "iris": [el(0, 1, 5, 6.6, "#1A1015"), el(-1.7, -1.4, 1.8, 2, "#FFFFFF"), el(1.6, 3.4, 0.9, 0.9, "#FFFFFF", None, 0, 0.8)],
        "olho_fechado": fechado}
    cilios = {"olho": normal["olho"][:2] + cilios_f + [traco("M -9 -12.6 Q -11 -15.4 -12.4 -19", "$linha", 2)],
              "iris": normal["iris"], "olho_fechado": fechado}
    lente = {  # máscara do Homem-Aranha: olho grande e branco, sem pupila
        "olho": [pa("M -13.5 -9 Q -2 -13.5 13.5 -3 Q 8 12 -6 11.5 Q -15 7 -13.5 -9 Z", "$lente", "$linha", 2.4)],
        "iris": [], "olho_fechado": [traco("M -12 -2 Q 0 8 13 -1", "$linha", 3.4, liga="olhos.fechado"),
                                     traco("M -12 3 Q 0 -8 13 2", "$linha", 3.4, liga="olhos.feliz")]}
    visor = {  # capacete do Homem de Ferro: fresta luminosa
        "olho": [el(0, 1, 15, 9, "$lente", None, 0, 0.22),
                 pa("M -12 -4 L 11 -2 L 9 5 L -10 4 Z", "$lente", "$linha", 1.8)],
        "iris": [], "olho_fechado": [traco("M -11 1 L 10 2", "$linha", 3.4, liga="olhos.fechado"),
                                     traco("M -11 3 Q 0 -6 10 3", "$linha", 3.2, liga="olhos.feliz")]}
    fenda = {  # capuz do Batman: fenda estreita e branca
        "olho": [pa("M -13 -3 Q 0 -10 13 -4 L 11 4.5 Q 0 6.5 -11 4.5 Z", "$lente", "$linha", 1.8)],
        "iris": [], "olho_fechado": [traco("M -12 1 L 11 2", "$linha", 3.4, liga="olhos.fechado"),
                                     traco("M -11 3 Q 0 -6 11 3", "$linha", 3.2, liga="olhos.feliz")]}
    estilos = {"normal": normal, "grande": grande, "amendoado": amendoado, "pontinho": pontinho, "cilios": cilios,
               "lente": lente, "visor": visor, "fenda": fenda}
    for e in estilos.values():   # olho fechado/feliz esconde o olho aberto (sem fio de cabelo no meio)
        for slot in ("olho", "iris"):
            e[slot] = [dict(p, desl="olhos.oculto") for p in e[slot]]
    return estilos


def sobrancelha() -> list:
    return [traco("M -9.5 1.4 Q 0 -3.2 9.5 1.2", "$cabelo-", 3.6)]


# --- boca: um desenho por "visema" -----------------------------------------------------------------------
def boca() -> list:
    dentro, linha, lingua = "$boca_dentro", "$boca_linha", "$lingua"
    dentes = pa("M -7.4 0.6 Q 0 4.2 7.4 0.6 L 6.6 2.4 Q 0 5.6 -6.6 2.4 Z", "#FFFFFF")
    return [
        traco("M -5.5 0 Q 0 4.2 5.5 0", linha, 2.6, v="fechada"),
        traco("M -8.4 -1.4 Q 0 8.6 8.4 -1.4", linha, 2.8, v="sorriso"),
        pa("M -10 -2.4 Q 0 15 10 -2.4 Q 0 0.6 -10 -2.4 Z", dentro, linha, 2, v="sorriso_aberto"),
        dentes | {"v": "sorriso_aberto"},
        el(0, 6.6, 4.6, 2.6, lingua, None, 0, 1, v="sorriso_aberto"),
        traco("M -5.6 1 L 5.6 1", linha, 2.6, v="linha"),
        el(0, 1.6, 3.4, 4.2, dentro, linha, 2, v="o_peq"),
        el(0, 3.6, 7.2, 8.4, dentro, linha, 2.2, v="A"),
        el(0, 7.4, 4.4, 2.8, lingua, None, 0, 1, v="A"),
        rr(-8.8, 0, 17.6, 7.8, 3.9, dentro, linha, 2.2, v="E"),
        rr(-8.2, 0.6, 16.4, 4.6, 2.3, dentro, linha, 2.2, v="I"),
        el(0, 3.4, 5, 6.4, dentro, linha, 2.2, v="O"),
        el(0, 3.2, 3.7, 4.6, dentro, linha, 2.2, v="U"),
        traco("M -5.5 1 L 5.5 1", linha, 2.8, v="M"),
    ]


def sombra() -> list:
    return [el(0, 0, 46, 7.5, "$sombra", None, 0, 0.3)]


def slots_corpo(g: str) -> dict:
    """Todos os slots do corpo nu (inclui rosto)."""
    o = olhos(g)["normal"]
    return dict(corpo(g), olho=o["olho"], iris=o["iris"], olho_fechado=o["olho_fechado"],
                sobr=sobrancelha(), boca=boca())
