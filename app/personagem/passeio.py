"""Passeio do personagem pela tela (sem Qt: só contas, o teste automático confere sem abrir janela).

`Passeio.atualizar(agora, x, y, area, ocupado)` decide, a cada quadro, para onde a janela vai. Quem manda em tudo é a
personalidade (catalogo_animacao.ARQUETIPOS[...]["passeio"]): "fixo" fica parado; "curto" anda perto do lugar de origem;
"tela" anda pela borda de baixo da tela toda; "livre" flutua por qualquer parte da tela.
Regras de bom senso: só anda com o Assessor parado (sem ouvir/pensar/falar), nunca sai da tela, para na hora quando alguém
o arrasta (e o novo lugar vira a origem) e devagar no começo e no fim de cada trecho.
"""
from .animacao import Aleatorio, suave

MODOS = ("fixo", "curto", "tela", "livre")
NOMES_MODO = {"personalidade": "Automático (jeito da personalidade)", "fixo": "Parado no lugar", "curto": "Passeia por perto",
              "tela": "Passeia pela tela toda", "livre": "Flutua livre pela tela"}


class Passeio:
    def __init__(self, modo: str, alcance: float = 280, vel: float = 70, pausa=(6, 14), semente: int = 5):
        self.modo = modo if modo in MODOS else "fixo"
        self.alcance, self.vel, self.pausa = float(alcance), float(vel), tuple(pausa)
        self.rng = Aleatorio(semente)
        self.origem = None            # (x, y) do lugar de "casa"
        self.alvo = None              # (x, y) para onde vai agora
        self.inicio = None            # (x, y, t) de onde saiu
        self.dur = 0.0
        self.espera_ate = None
        self.direcao = 0

    def novo_lugar(self, x: float, y: float) -> None:
        """O usuário arrastou: aqui é a nova casa e o trecho em andamento é cancelado."""
        self.origem, self.alvo, self.inicio, self.direcao = (x, y), None, None, 0
        self.espera_ate = None

    def _escolher(self, x: float, y: float, area: tuple, larg: float) -> tuple:
        """area = (esq, topo, dir, baixo) da tela onde o personagem está; larg = largura do personagem (px)."""
        esq, topo, dir_, baixo = area
        ox, oy = self.origem
        r = self.rng
        if self.modo == "curto":
            lo, hi = max(esq, ox - self.alcance), min(dir_ - larg, ox + self.alcance)
            return (r.entre(lo, max(lo, hi)), oy)
        if self.modo == "tela":
            return (r.entre(esq, max(esq, dir_ - larg)), oy)
        altura_livre = max(0.0, (baixo - topo) * 0.55)
        return (r.entre(esq, max(esq, dir_ - larg)), r.entre(oy - altura_livre, oy))

    def atualizar(self, agora: float, x: float, y: float, area: tuple, ocupado: bool, larg: float = 120.0) -> tuple:
        """-> (x, y, direcao). direcao = -1 esquerda, 0 parado, +1 direita. Sem passeio devolve a mesma posição."""
        if self.origem is None:
            self.origem = (x, y)
        if self.modo == "fixo" or ocupado:
            if ocupado and self.alvo:   # parou de repente (foi falar): fica onde está e a nova casa é aqui
                self.origem, self.alvo, self.inicio = (x, y), None, None
            self.direcao = 0
            self.espera_ate = None if ocupado else self.espera_ate
            return x, y, 0
        if self.alvo is None:
            if self.espera_ate is None:
                self.espera_ate = agora + self.rng.entre(*self.pausa)
            if agora < self.espera_ate:
                return x, y, 0
            alvo = self._escolher(x, y, area, larg)
            dist = ((alvo[0] - x) ** 2 + (alvo[1] - y) ** 2) ** 0.5
            if dist < 40:
                self.espera_ate = agora + self.rng.entre(*self.pausa) * 0.5
                return x, y, 0
            self.alvo, self.inicio = alvo, (x, y, agora)
            self.dur = max(0.8, dist / self.vel)
            self.espera_ate = None
        x0, y0, t0 = self.inicio
        u = (agora - t0) / self.dur
        if u >= 1.0:
            nx, ny, self.direcao = self.alvo[0], self.alvo[1], 0
            self.alvo = self.inicio = None
            return nx, ny, 0
        k = suave(u)
        nx, ny = x0 + (self.alvo[0] - x0) * k, y0 + (self.alvo[1] - y0) * k
        self.direcao = 1 if self.alvo[0] > x0 else -1 if self.alvo[0] < x0 else 0
        # segurança: nunca fora da tela
        nx = min(max(nx, area[0]), max(area[0], area[2] - larg))
        ny = min(max(ny, area[1]), area[3])
        return nx, ny, self.direcao


def do_config(cfg_passeio: str, arq: dict, escala: float = 1.0, semente: int = 5) -> Passeio:
    """cfg_passeio = "personalidade" (o jeito da personalidade) ou um dos MODOS."""
    p = arq["passeio"]
    modo = p["modo"] if cfg_passeio in ("", "personalidade", None) else cfg_passeio
    return Passeio(modo, p["alcance"] * max(0.5, escala), p["vel"] * max(0.5, escala), p["pausa"], semente)
