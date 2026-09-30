"""Animador do personagem: estado do Assessor -> POSE do quadro (sem Qt: o teste automático confere sem abrir janela).

Entrada: `mudar(estado)` (idle/ouvindo/pensando/falando/descansando), `nivel(volume)` (0 a 1 da voz), `texto(frase)` (vogais
para a boca), `gesto(nome)`, `andar(direcao)`, `olhar(dx, dy)` (para onde está o mouse).
Saída: `quadro(agora)` -> {"pose": {"no.canal": número}, "extras": {...}}. Quem desenha (render_qt.py / personagem.js)
só aplica a pose. A personalidade (catalogo_animacao.ARQUETIPOS) escolhe os clipes, o ritmo e o tamanho dos gestos.
O sorteio (Aleatorio) é o mesmo nos dois lados: com a mesma semente a página de teste e o app fazem as mesmas escolhas.
"""
import math

from . import catalogo_animacao as A

ESTADOS = ("idle", "ouvindo", "pensando", "falando", "descansando")
TRANSICAO = 0.28       # s para misturar a pose antiga com a nova ao trocar de estado
FADE_GESTO = 0.2       # s de entrada/saída de um gesto avulso
ABERTOS = ("A", "E", "I", "O", "U", "sorriso_aberto", "o_peq")


class Aleatorio:
    """mulberry32: pequeno sorteador de 32 bits (idêntico ao do personagem.js)."""

    def __init__(self, semente: int = 1):
        self.s = int(semente) & 0xFFFFFFFF

    def prox(self) -> float:
        self.s = (self.s + 0x6D2B79F5) & 0xFFFFFFFF
        t = self.s
        t = ((t ^ (t >> 15)) * (t | 1)) & 0xFFFFFFFF
        t = (t ^ ((t + (((t ^ (t >> 7)) * (t | 61)) & 0xFFFFFFFF)) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0

    def entre(self, a: float, b: float) -> float:
        return a + (b - a) * self.prox()

    def escolher(self, pares: list):
        """[[item, peso], ...] -> item."""
        total = sum(p for _i, p in pares)
        x = self.prox() * total
        for item, peso in pares:
            x -= peso
            if x < 0:
                return item
        return pares[-1][0]


def _lim(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def suave(x: float) -> float:
    x = _lim(x)
    return x * x * (3 - 2 * x)


def padrao(canal: str) -> float:
    """Valor de repouso de um canal (escalas valem 1, o resto 0)."""
    return 1.0 if canal.endswith((".sx", ".sy")) or canal == "sombra.o" else 0.0


def _tangente(k: list, i: int) -> float:
    """Inclinação no ponto i (curva monotônica: nos extremos e nas pontas é 0, então nunca passa do valor)."""
    if i == 0 or i == len(k) - 1:
        return 0.0
    h0, h1 = k[i][0] - k[i - 1][0], k[i + 1][0] - k[i][0]
    if h0 <= 0 or h1 <= 0:
        return 0.0
    d0, d1 = (k[i][1] - k[i - 1][1]) / h0, (k[i + 1][1] - k[i][1]) / h1
    if d0 * d1 <= 0:
        return 0.0
    w1, w2 = 2 * h1 + h0, h1 + 2 * h0
    return (w1 + w2) / (w1 / d0 + w2 / d1)


def avaliar(spec: dict, u: float) -> float:
    """Valor de uma trilha no instante u (0 a 1 dentro do clipe). Pontos `k`: curva contínua (sem parar em cada ponto)."""
    if "seno" in spec:
        base, amp, ciclos, fase = spec["seno"]
        return base + amp * math.sin(2 * math.pi * (ciclos * u + fase))
    k = spec["k"]
    if u <= k[0][0]:
        return k[0][1]
    for i in range(len(k) - 1):
        t0, v0 = k[i]
        t1, v1 = k[i + 1]
        if u <= t1:
            h = t1 - t0
            if h <= 0:
                return v1
            s = (u - t0) / h
            s2, s3 = s * s, s * s * s
            return ((2 * s3 - 3 * s2 + 1) * v0 + (s3 - 2 * s2 + s) * h * _tangente(k, i)
                    + (-2 * s3 + 3 * s2) * v1 + (s3 - s2) * h * _tangente(k, i + 1))
    return k[-1][1]


def pose_do_clipe(clipe: dict, u: float) -> dict:
    return {c: avaliar(spec, u) for c, spec in clipe["trilhas"].items()}


def somar(pose: dict, extra: dict) -> None:
    """Junta `extra` em `pose`: giros e posições somam, escalas multiplicam."""
    for c, v in extra.items():
        if c in pose:
            pose[c] = pose[c] * v if padrao(c) == 1.0 else pose[c] + v
        else:
            pose[c] = v


def misturar(a: dict, b: dict, k: float) -> dict:
    """a -> b em k (0 a 1), canal por canal (o que falta num dos lados vale o repouso)."""
    return {c: a.get(c, padrao(c)) + (b.get(c, padrao(c)) - a.get(c, padrao(c))) * k for c in set(a) | set(b)}


def amplitude_falsa(t: float, semente: float = 1.3) -> float:
    """Boca "falando" quando o volume real não chega (voz sem arquivo, porta ocupada...)."""
    silaba = 0.5 + 0.5 * math.sin(t * 12.5 + semente)
    envelope = 0.55 + 0.45 * math.sin(t * 2.1 + semente * 1.7)
    palavra = 1.0 if math.sin(t * 1.6 + semente * 2.3) > -0.55 else 0.08
    tremor = 0.15 * math.sin(t * 31 + semente * 3)
    return _lim(silaba ** 1.4 * envelope * palavra + tremor * palavra)


def visemas_do_texto(texto: str) -> list:
    """Frase -> sequência de formas de boca (vogais; b/m/p fecham os lábios)."""
    saida = []
    for ch in (texto or "").lower():
        v = A.VISEMAS_VOGAIS.get(ch)
        if v:
            saida.append(v)
        elif ch in "bmp" and saida and saida[-1] != "M":
            saida.append("M")
    return saida


def arquetipo_do_estilo(estilo: str | None, forcado: str | None = None) -> str:
    """Nome do estilo de personalidade do Assessor -> jeito do personagem ("" ou automático = pelo estilo)."""
    if forcado and forcado in A.ARQUETIPOS:
        return forcado
    return A.ESTILO_PARA_ARQUETIPO.get(estilo or "", A.ARQUETIPO_PADRAO)


class Animador:
    def __init__(self, arquetipo: str = A.ARQUETIPO_PADRAO, expressao_parado: str | None = None, semente: int = 1):
        self.arq_id = arquetipo if arquetipo in A.ARQUETIPOS else A.ARQUETIPO_PADRAO
        self.arq = A.ARQUETIPOS[self.arq_id]
        self.expr_parado = expressao_parado if expressao_parado in A.EXPRESSOES else None
        self.rng = Aleatorio(semente)
        self.estado = "idle"
        self.t_estado = 0.0
        self.movendo = 0              # -1 esquerda, 0 parado, +1 direita
        self.ritmo = 1.0              # pressa da caminhada
        self.overlay = None           # gesto avulso tocando: {"nome","t0","dur"}
        self.prox_idle = None
        self.prox_piscar = None
        self.piscando = None
        self.olhar_alvo = (0.0, 0.0)
        self.visemas: list = []       # vogais que faltam falar
        self.visema = "fechada"
        self.t_visema = -9.0
        self._t = None
        self._amp = 0.0
        self._amp_ant = 0.0
        self._amp_real = 0.0
        self._amp_ts = -9.0
        self._de = {}                 # pose de antes da troca de estado
        self._t_troca = -9.0
        self._ultima = {}
        self._face = {}
        self._look = [0.0, 0.0]
        self._ext = {"ondas": 0.0, "pensando": 0.0, "zzz": 0.0, "holo": 0.0, "notas": 0.0}
        self._mola = {}               # canal -> [valor, velocidade] (inércia)
        self._mexendo = False         # alguma mola ainda balançando (pede mais quadros)
        self._batida = None           # pose dos braços da fala agora
        self._batida_ate = 0.0
        self.balanco = 1.0            # quanto o cabelo de trás balança (cabelo comprido 1; curto quase nada)

    # --- entradas --------------------------------------------------------------------------------------
    def mudar(self, estado: str, agora: float) -> None:
        estado = estado if estado in ESTADOS else "idle"
        if estado == self.estado:
            return
        self._de, self._t_troca = {c: v for c, v in self._ultima.items() if not isinstance(v, str)}, agora
        self.estado, self.t_estado = estado, agora
        self.overlay = None
        self.prox_idle = None
        self._batida = None

    def nivel(self, valor: float, agora: float) -> None:
        self._amp_real, self._amp_ts = _lim(float(valor)), agora

    def texto(self, frase: str) -> None:
        self.visemas = visemas_do_texto(frase)

    def gesto(self, nome: str, agora: float) -> bool:
        c = A.CLIPES.get(nome)
        if not c or c["loop"]:
            return False
        self.overlay = {"nome": nome, "t0": agora, "dur": c["dur"] / max(0.3, self.arq["vel"])}
        return True

    def andar(self, direcao: int, ritmo: float = 1.0) -> None:
        self.movendo, self.ritmo = int(direcao), float(ritmo)

    def olhar(self, dx: float, dy: float) -> None:
        self.olhar_alvo = (_lim(dx, -1, 1), _lim(dy, -1, 1))

    def ocupado(self) -> bool:
        return self.estado != "idle" or self.overlay is not None

    def fps(self, agora: float) -> int:
        """Quadros por segundo que valem a pena agora."""
        if self.estado == "descansando":
            return 15
        if self.overlay or self.movendo or self.estado in ("falando", "ouvindo") or agora - self._t_troca < TRANSICAO \
                or self.piscando is not None or self._amp > 0.02 or self._mexendo:
            return 60
        return 30

    # --- o quadro ----------------------------------------------------------------------------------------
    def quadro(self, agora: float) -> dict:
        dt = 0.0 if self._t is None else _lim(agora - self._t, 0.0, 0.2)
        self._t = agora
        arq, est, vel = self.arq, self.estado, self.arq["vel"]
        nome_base, expr_est = arq["estado"][est]
        if est == "idle" and self.movendo and arq["passeio"]["andar"] != "flutua":
            nome_base = "andar"
        clipe = A.CLIPES[nome_base]
        ritmo = (self.ritmo if nome_base == "andar" else 1.0) * vel
        u = ((agora - self.t_estado) * ritmo / clipe["dur"]) % 1.0
        pose = pose_do_clipe(clipe, u)
        amp_s = _lim(self._amp, 0, 1)
        if clipe.get("gesto"):   # o volume da voz controla o tamanho do gesto
            g = (0.3 + 0.7 * amp_s) * arq["amp"]
            pose = {c: v * g for c, v in pose.items()}
        if nome_base == "parado":
            somar(pose, arq["postura"])
        if est != "descansando":
            for extra in arq["base"]:
                ce = A.CLIPES[extra]
                somar(pose, pose_do_clipe(ce, ((agora - self.t_estado) * vel / ce["dur"]) % 1.0))
        if self.movendo and est == "idle":
            pose["raiz.r"] = pose.get("raiz.r", 0.0) + 3.5 * self.movendo
        if self._t_troca + TRANSICAO > agora and self._de:
            pose = misturar(self._de, pose, suave((agora - self._t_troca) / TRANSICAO))

        # gesto avulso por cima
        expr_nome, boca_lista, extras_gesto = expr_est, None, ()
        if est == "idle" and self.expr_parado:
            expr_nome = self.expr_parado
        ov = self.overlay
        if ov:
            ce = A.CLIPES[ov["nome"]]
            dec = agora - ov["t0"]
            if dec >= ov["dur"]:
                self.overlay = ov = None
                self.prox_idle = None
            else:
                w = suave(min(1.0, dec / FADE_GESTO, (ov["dur"] - dec) / FADE_GESTO))
                for c, v in pose_do_clipe(ce, dec / ov["dur"]).items():
                    d = padrao(c)
                    v = d + (v - d) * arq["amp"]
                    pose[c] = pose.get(c, d) + (v - pose.get(c, d)) * w
                if ce.get("expr"):
                    expr_nome = ce["expr"]
                boca_lista, extras_gesto = ce.get("boca"), ce.get("extras", ())
                ov["u"] = dec / ov["dur"]
        # gesto sorteado (só parado, sem andar)
        if est == "idle" and not self.movendo and not self.overlay:
            if self.prox_idle is None:
                self.prox_idle = agora + self.rng.entre(*arq["intervalo"])
            elif agora >= self.prox_idle:
                self.gesto(self.rng.escolher(arq["idle"]), agora)
                self.prox_idle = None
        # braços da fala: uma pose (batida) por trecho, com força pelo volume
        if est == "falando" and arq.get("fala"):
            if self._batida is None or agora >= self._batida_ate:
                self._batida = A.POSES_FALA[self.rng.escolher(arq["fala"])]
                self._batida_ate = agora + self.rng.entre(*A.TROCA_FALA) / vel
            g = (0.35 + 0.65 * amp_s) * arq["amp"]
            somar(pose, {c: v * g for c, v in self._batida.items()})
        # vida: balanço pequeno e contínuo (pose nenhuma fica congelada)
        if est != "descansando":
            for c, (a, hz, fase) in A.VIDA.items():
                pose[c] = pose.get(c, 0.0) + a * math.sin(2 * math.pi * (hz * agora + fase))

        # rosto: expressão suavizada + olhar + piscar
        alvo = A.EXPRESSOES.get(expr_nome, A.EXPRESSOES["neutro"])
        k = 1 - math.exp(-dt / 0.10) if dt else 1.0
        f = self._face
        for c in ("sobr_e", "sobr_d", "sobr_r", "aber", "feliz"):
            f[c] = alvo[c] if c not in f else f[c] + (alvo[c] - f[c]) * k
        seguir = est in ("idle", "ouvindo") and not self.overlay
        ox = alvo["olhar"][0] + (self.olhar_alvo[0] * 3.2 * arq["olhar_mouse"] if seguir else 0.0)
        oy = alvo["olhar"][1] + (self.olhar_alvo[1] * 2.6 * arq["olhar_mouse"] if seguir else 0.0)
        kl = 1 - math.exp(-dt / 0.14) if dt else 1.0
        self._look[0] += (ox - self._look[0]) * kl
        self._look[1] += (oy - self._look[1]) * kl
        self._piscar(agora)
        aber = f["aber"] * (1 - 0.96 * self._curva_piscar(agora)) * (1 - 0.96 * f["feliz"])
        pose["abertura_e.sy"] = pose["abertura_d.sy"] = max(0.03, aber)
        pose["olhos.fechado"] = _lim((0.42 - aber) / 0.3) * (1 - _lim(f["feliz"]))
        pose["olhos.oculto"] = 1 - _lim((aber - 0.10) / 0.2)
        pose["olhos.feliz"] = _lim(f["feliz"])
        for lado, sinal in (("e", 1), ("d", -1)):
            pose[f"sobr_{lado}.y"] = f["sobr_" + lado]
            pose[f"sobr_{lado}.r"] = f["sobr_r"] * sinal
            for eixo, v in (("x", self._look[0]), ("y", self._look[1])):
                pose[f"iris_{lado}.{eixo}"] = pose.get(f"iris_{lado}.{eixo}", 0.0) + v
        if seguir:   # a cabeça acompanha um pouco o olhar
            pose["cabeca.x"] = pose.get("cabeca.x", 0.0) + self.olhar_alvo[0] * 1.6 * arq["olhar_mouse"]
            pose["cabeca.r"] = pose.get("cabeca.r", 0.0) + self.olhar_alvo[0] * 2.4 * arq["olhar_mouse"]

        self._molas(pose, dt)

        # boca
        pose["boca.v"], pose["boca.sy"] = self._boca(agora, dt, alvo["boca"], boca_lista, ov)

        # enfeites da janela (ondas, balão, zzz, notas, holograma)
        e, ex = self._ext, {}
        e_alvo = {"ondas": 1.0 if est in ("ouvindo", "falando") else 0.0, "pensando": 1.0 if est == "pensando" else 0.0,
                  "zzz": 1.0 if est == "descansando" else 0.0,
                  "holo": 1.0 if ("holo" in extras_gesto or "holo" in clipe.get("extras", ())) else 0.0,
                  "notas": 1.0 if "notas" in extras_gesto else 0.0}
        for c, v in e_alvo.items():
            e[c] += (v - e[c]) * (1 - math.exp(-dt / 0.15) if dt else 1.0)
        ex.update({c: round(v, 3) for c, v in e.items()})
        ex["amp"] = round(self._amp, 3)
        ex["aura"] = arq["aura"]
        self._ultima = pose
        return {"pose": pose, "extras": ex, "estado": est, "gesto": (self.overlay or {}).get("nome", ""),
                "arquetipo": self.arq_id}

    # --- pedaços --------------------------------------------------------------------------------------------
    def _molas(self, pose: dict, dt: float) -> None:
        """Inércia: cada canal de MOLAS persegue o valor da pose como uma mola (atrasa, passa um pouquinho e assenta);
        capa e cabelo ainda ficam para trás quando o corpo gira ou anda (INERCIA)."""
        alvo = {c: pose.get(c, 0.0) for c in A.MOLAS}
        for c, (fator, canais, passo, limite) in A.INERCIA.items():
            k = self.balanco if c == "cabelo_tras.r" else 1.0
            giro = sum(pose.get(x, 0.0) for x in canais)
            alvo[c] += _lim((fator * giro + passo * self.movendo) * k, -limite, limite)
        n = max(1, math.ceil(dt * 240 - 1e-9)) if dt > 0 else 0
        h = dt / n if n else 0.0
        mexendo = False
        for c, (hz, zeta) in A.MOLAS.items():
            m = self._mola.get(c)
            if m is None:
                m = self._mola[c] = [alvo[c], 0.0]
            elif n:
                w = 2 * math.pi * hz
                x, v = m
                for _ in range(n):
                    v += (w * w * (alvo[c] - x) - 2 * zeta * w * v) * h
                    x += v * h
                m[0], m[1] = x, v
            pose[c] = m[0]
            mexendo = mexendo or abs(m[1]) > 2.0 or abs(m[0] - alvo[c]) > 0.3
        self._mexendo = mexendo

    def _piscar(self, agora: float) -> None:
        if self.piscando is not None and agora - self.piscando >= 0.16:
            self.piscando = None
        if self.prox_piscar is None:
            self.prox_piscar = agora + self.rng.entre(*self.arq["piscar"])
        elif self.piscando is None and agora >= self.prox_piscar:
            self.piscando = agora
            dupla = self.rng.prox() < 0.15
            self.prox_piscar = agora + (0.3 if dupla else self.rng.entre(*self.arq["piscar"]))

    def _curva_piscar(self, agora: float) -> float:
        if self.piscando is None:
            return 0.0
        u = (agora - self.piscando) / 0.16
        return suave(u * 2) if u < 0.5 else suave(2 - u * 2)

    def _boca(self, agora: float, dt: float, repouso: str, lista, ov) -> tuple:
        """(visema, escala vertical). Falando: segue o volume e troca de vogal a cada sílaba (subida do volume)."""
        if self.estado == "falando":
            alvo = self._amp_real if agora - self._amp_ts < 0.3 else amplitude_falsa(agora)
            self._amp += (alvo - self._amp) * (1 - 0.65 ** (dt * 60))
        else:
            self._amp *= 0.5 ** (dt * 30)
        a = self._amp
        if self.estado == "falando":
            if a > 0.16 and a - self._amp_ant > 0.035 and agora - self.t_visema > 0.075:
                self.visema = self.visemas.pop(0) if self.visemas else A.SEQUENCIA_VISEMAS[int(self.rng.prox() * len(A.SEQUENCIA_VISEMAS))]
                self.t_visema = agora
            self._amp_ant = a
            if a < 0.09:
                return (repouso if repouso != "fechada" else "sorriso"), 1.0
            return self.visema, 0.72 + 0.55 * a
        self._amp_ant = a
        if lista and ov:
            v = repouso
            for t, nome in lista:
                if ov.get("u", 0.0) >= t:
                    v = nome
            return v, 1.0
        return repouso, 1.0
