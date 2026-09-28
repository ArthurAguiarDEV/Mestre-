"""Avatar robô na área de trabalho: a parte SEM janela (roda no processo do Assessor e nos testes).

O desenho animado fica em `app/avatar_janela.py`, num PROCESSO SEPARADO com PySide6 (o Assessor não carrega o Qt).
Este arquivo tem:
- `visual(dados, rodando, pausado)`: estado do Assessor (logs/estado_agora.json) -> estado do avatar;
- `Animador`: estado -> números de cada quadro (sem Qt: o teste confere sem abrir janela);
- `posicao_padrao(...)`: logo acima do relógio (canto inferior direito da área de trabalho do monitor principal);
- `iniciar(...)` / `acompanhar(...)` / `encerrar()`: liga o processo do avatar; se falhar, o Assessor volta à bolinha;
- `enviar_nivel(...)`: volume da fala (0 a 1) para a boca, por UDP em 127.0.0.1 (leve, sem disco).
"""
import importlib.util
import json
import logging
import math
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

log = logging.getLogger(__name__)

TAMANHO = 112          # lado do robô na tela (px lógicos; o Windows aumenta em 125/150%)
FOLGA = 14             # borda transparente em volta (a entrada "pula" um pouco para fora)
LADO_JANELA = TAMANHO + 2 * FOLGA
PORTA_NIVEL = 47634    # 47631 painel, 47632 extensão, 47633 voz natural
ESTADOS = ("ligando", "idle", "ouvindo", "pensando", "falando", "pausado", "voltando", "descansando", "desligado")
DURACAO = {"entrar": 1.25, "voltar": 0.9, "sair": 0.75, "desligar": 0.9}

# --- estado do Assessor -> estado do avatar -------------------------------------------------------


def visual(dados: dict, rodando: bool = True, pausado: bool = False) -> str:
    """Um dos ESTADOS (sem "voltando": ele é a animação de sair do pausado)."""
    nome = str(dados.get("nome") or "")
    if not rodando or nome == "desligado":
        return "desligado"
    if pausado or nome == "pausado":
        return "pausado"
    if nome == "iniciando":
        return "ligando"
    if dados.get("descanso"):
        return "descansando"
    if nome == "falando":
        return "falando"
    if nome in ("gravando", "conversa"):
        return "ouvindo"
    if dados.get("pensamento") == "pensando" or nome in ("pensando", "trabalhando", "transcrevendo"):
        return "pensando"
    return "idle"


# --- contas das animações (iguais às do protótipo em CSS) -------------------------------------------


def _suave(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return 0.5 - 0.5 * math.cos(math.pi * x)


def _onda(t: float, periodo: float, atraso: float = 0.0) -> float:
    """0 -> 1 -> 0 (ease-in-out) a cada período."""
    fase = ((t - atraso) / periodo) % 1.0
    return _suave(fase * 2 if fase < 0.5 else 2 - fase * 2)


def _quadros(p: float, pontos: list) -> tuple:
    """Keyframes: [(0, (a, b...)), (0.5, (...)), (1, (...))] com transição suave entre eles."""
    p = max(0.0, min(1.0, p))
    for (t0, v0), (t1, v1) in zip(pontos, pontos[1:]):
        if p <= t1:
            k = _suave((p - t0) / (t1 - t0)) if t1 > t0 else 1.0
            return tuple(a + (b - a) * k for a, b in zip(v0, v1))
    return tuple(pontos[-1][1])


def amplitude_falsa(t: float, semente: float = 1.3) -> float:
    """Boca "falando" quando o volume real não chega (motor sem arquivo, porta ocupada...)."""
    silaba = 0.5 + 0.5 * math.sin(t * 12.5 + semente)
    envelope = 0.55 + 0.45 * math.sin(t * 2.1 + semente * 1.7)
    palavra = 1.0 if math.sin(t * 1.6 + semente * 2.3) > -0.55 else 0.08
    tremor = 0.15 * math.sin(t * 31 + semente * 3)
    return max(0.0, min(1.0, silaba ** 1.4 * envelope * palavra + tremor * palavra))


# (in: dy, sx, sy, opacidade) — dy em unidades da grade de 200 (o protótipo usa % da altura)
_ENTRAR = [(0, (50, .12, .12, 0)), (.5, (-14, 1.1, 1.1, 1)), (.72, (0, .95, 1.05, 1)), (.88, (0, 1.02, .98, 1)),
           (1, (0, 1, 1, 1))]
_VOLTAR = [(0, (250, 1, 1, 0)), (.45, (-24, .92, 1.1, 1)), (.68, (0, 1.1, .9, 1)), (.84, (0, .98, 1.02, 1)),
           (1, (0, 1, 1, 1))]
_SAIR = [(0, (0, 1, 1, 1)), (.22, (6, 1.1, .88, 1)), (.42, (-28, .92, 1.08, 1)), (1, (270, .8, 1, 0))]
_DESLIGAR = [(0, (0, 1, 1, 1)), (.3, (4, 1.06, .92, 1)), (1, (60, .9, .9, 0))]


class Animador:
    """Guarda o estado e calcula cada quadro. Sem Qt: a janela só desenha o que ele manda."""

    def __init__(self):
        self.base = ""            # estado atual (um dos ESTADOS, "ligando"/"voltando" viram "idle")
        self.anim = ""            # animação de passagem: entrar, voltar, sair, desligar
        self.anim_ini = 0.0
        self.fila = 0             # tamanho da fila do "pensando" (selo com o número quando > 1)
        self.pronto = False       # resposta da IA pronta (selo verde)
        self._amp = 0.0
        self._amp_real = 0.0
        self._amp_ts = 0.0
        self._t = None
        self._s = {}              # valores que mudam devagar (transições do CSS)

    # --- mudanças -----------------------------------------------------------------------
    def mudar(self, novo: str, agora: float, fila: int = 0, pronto: bool = False) -> str:
        """Troca de estado. Devolve a animação de passagem que começou ("" = nenhuma)."""
        self.fila, self.pronto = int(fila or 0), bool(pronto)
        anterior = self.base
        anim = ""
        if novo == "ligando":
            base, anim = "idle", ("entrar" if anterior in ("", "desligado") else "")
        elif novo == "voltando":
            base, anim = "idle", "voltar"
        elif novo == "pausado":
            base, anim = "pausado", ("sair" if anterior not in ("pausado", "") else "")
        elif novo == "desligado":
            base, anim = "desligado", ("desligar" if anterior not in ("desligado", "pausado", "") else "")
        else:
            base = novo
            if anterior == "pausado":
                anim = "voltar"
            elif anterior in ("", "desligado"):
                anim = "entrar"
        if base == anterior and not anim:
            return ""
        self.base = base
        if anim:
            self.anim, self.anim_ini = anim, agora
        return anim

    def nivel(self, valor: float, agora: float) -> None:
        """Volume da fala (0 a 1) que chegou do Assessor."""
        self._amp_real, self._amp_ts = max(0.0, min(1.0, float(valor))), agora

    def _anim_p(self, agora: float) -> float:
        if not self.anim:
            return 1.0
        p = (agora - self.anim_ini) / DURACAO[self.anim]
        if p >= 1.0 and self.anim in ("entrar", "voltar"):
            self.anim = ""
        return min(1.0, p)

    def visivel(self, agora: float) -> bool:
        if self.base in ("pausado", "desligado", ""):
            return bool(self.anim) and self._anim_p(agora) < 1.0
        return True

    def terminou(self, agora: float) -> bool:
        """Desligado e a animação de despedida acabou: a janela pode fechar."""
        return self.base == "desligado" and not (self.anim == "desligar" and self._anim_p(agora) < 1.0)

    def fps(self, agora: float) -> int:
        """Quadros por segundo que valem a pena agora (0 = parado, não gasta nada)."""
        if not self.visivel(agora):
            return 0
        if self.anim or self.base in ("falando", "ouvindo") or self._mexendo():
            return 60
        if self.base == "pensando":
            return 30
        return 20   # idle/descansando: balanço lento, 20 quadros bastam

    def _mexendo(self) -> bool:
        return any(abs(v - self._alvos().get(k, v)) > 0.01 for k, v in self._s.items())

    def _alvos(self) -> dict:
        b = self.base
        return {
            "tilt": -7.0 if b == "ouvindo" else 0.0,
            "olhos": 1.18 if b == "ouvindo" else 1.0,
            "olhos_y": 0.1 if b == "descansando" else 1.0,
            "look_x": 5.0 if b == "pensando" else 0.0,
            "look_y": -7.0 if b == "pensando" else 0.0,
            "ondas": 1.0 if b in ("ouvindo", "falando") else 0.0,
            "balao": 1.0 if b == "pensando" else 0.0,
            "zzz": 1.0 if b == "descansando" else 0.0,
            "selo": 1.0 if (b == "pensando" and self.fila > 1) or self.pronto else 0.0,
            "boca": 1.0 if b == "falando" else 0.0,
            "luz": 0.0 if b == "desligado" else 1.0,
        }

    # --- um quadro ----------------------------------------------------------------------
    def quadro(self, agora: float) -> dict:
        dt = 0.0 if self._t is None else max(0.0, min(0.2, agora - self._t))
        self._t = agora
        alvos = self._alvos()
        tempos = {"boca": 0.06, "ondas": 0.1, "balao": 0.15, "selo": 0.15, "zzz": 0.1, "luz": 0.12}
        for k, alvo in alvos.items():
            if k not in self._s:
                self._s[k] = alvo
            else:   # aproxima do alvo (≈ transition .3-.5s do CSS)
                self._s[k] += (alvo - self._s[k]) * (1 - math.exp(-dt / tempos.get(k, 0.12)))
        s, b, t = self._s, self.base, agora
        p = self._anim_p(agora)   # (antes do resto: a entrada que acabou ja sai de "anim")
        q = {"visivel": self.visivel(agora), "base": b, "anim": self.anim, "fila": self.fila, "pronto": self.pronto}

        # entrar / voltar / sair / desligar (a caixa toda)
        pontos = {"entrar": _ENTRAR, "voltar": _VOLTAR, "sair": _SAIR, "desligar": _DESLIGAR}.get(self.anim)
        if pontos:
            q["in_dy"], q["in_sx"], q["in_sy"], q["in_op"] = _quadros(p, pontos)
        else:
            q["in_dy"], q["in_sx"], q["in_sy"], q["in_op"] = 0.0, 1.0, 1.0, (0.0 if b in ("pausado", "desligado") else 1.0)
        q["flash_esc"], q["flash_op"] = 1.0, 0.0
        q["boot"] = 1.0
        if self.anim == "entrar":   # olhos "ligam" e um anel verde se abre
            tb = (agora - self.anim_ini) / 1.1
            q["boot"] = _quadros(tb, [(0, (0,)), (.55, (0,)), (.78, (1.25,)), (1, (1,))])[0]
            tf = (agora - self.anim_ini - 0.35) / 0.9
            if 0 <= tf <= 1:
                q["flash_esc"], q["flash_op"] = 0.3 + 1.4 * tf, 0.9 * (1 - tf)

        # corpo: balanço (idle/ouvindo), respiração (descansando), sombra
        rig_dy, rig_sx, rig_sy, sombra = 0.0, 1.0, 1.0, 0.0
        if b in ("idle", "ouvindo"):
            sombra = _onda(t, 3.2 if b == "idle" else 1.7)
            rig_dy = -5 * sombra
        elif b == "descansando":
            r = _onda(t, 4.0)
            rig_sx, rig_sy = 1 + 0.035 * r, 1 - 0.035 * r
        # amplitude da fala (real se chegou há pouco; senão a falsa)
        if b == "falando":
            alvo = self._amp_real if agora - self._amp_ts < 0.3 else amplitude_falsa(t)
            self._amp += (alvo - self._amp) * (1 - 0.65 ** (dt * 60))
        else:
            self._amp *= 0.5 ** (dt * 30)
        a = self._amp
        if b == "falando":
            rig_dy, rig_sx, rig_sy = -a * 4, 1 + a * 0.02, 1 - a * 0.015
        q.update(rig_dy=rig_dy, rig_sx=rig_sx, rig_sy=rig_sy, amp=a,
                 sombra_sx=1 - 0.14 * sombra, sombra_op=0.4 - 0.12 * sombra)

        q["tilt"] = s["tilt"] + (-4 * math.cos(2 * math.pi * t / 2.4) if b == "pensando" else 0.0)
        # olhos: piscar a cada 4,6 s (menos dormindo), escala, olhar para cima (pensando)
        fase = (t % 4.6) / 4.6
        piscar = 1.0 if b == "descansando" else _quadros(fase, [(0, (1,)), (.91, (1,)), (.94, (.08,)), (1, (1,))])[0]
        q["olhos_sx"] = s["olhos"]
        q["olhos_sy"] = s["olhos"] * s["olhos_y"] * piscar * q["boot"]
        q["look_x"], q["look_y"], q["luz"] = s["look_x"], s["look_y"], s["luz"]
        # antena/peito: brilho
        if b == "ouvindo":
            brilho = 0.35 + 0.65 * _onda(t, 1.0)
        elif b == "pensando":
            brilho = 0.35 + 0.65 * _onda(t, 2.4)
        else:
            brilho = {"falando": 1.0, "descansando": 0.12}.get(b, 0.35)
        q["brilho"] = brilho * s["luz"]
        # ondas de voz ao lado
        if b == "falando":
            q["barras"] = [max(0.2, min(1.1, 0.25 + min(1, a * (1.1 - i * 0.2) + 0.2 * math.sin(t * 9 + i * 2))))
                           for i in range(3)]
        else:
            q["barras"] = [0.3 + 0.7 * _onda(t, 0.8, -d) for d in (0.0, 0.27, 0.53)]
        q["ondas"] = s["ondas"]
        # balão com pontinhos (pensando)
        q["balao"] = s["balao"]
        pontos_bal = []
        for atraso in (0.0, 0.15, 0.3):
            f = ((t - atraso) / 1.1) % 1.0
            k = _suave(f / 0.3) if f < 0.3 else (_suave(1 - (f - 0.3) / 0.3) if f < 0.6 else 0.0)
            pontos_bal.append((-5 * k, 0.45 + 0.55 * k))
        q["pontos"] = pontos_bal
        # zzz (descansando)
        q["zzz"] = s["zzz"]
        zs = []
        for atraso in (0.0, 1.0, 2.0):
            f = ((t - atraso) / 3.0) % 1.0
            e = 1 - (1 - f) ** 2   # ease-out
            op = f / 0.25 if f < 0.25 else 1 - (f - 0.25) / 0.75
            zs.append((16 * e, 8 - 38 * e, 0.5 + 0.65 * e, max(0.0, op)))
        q["zs"] = zs
        # selo: número da fila (pensando) ou resposta pronta
        q["selo"] = s["selo"]
        q["selo_texto"] = "✓" if self.pronto and not (b == "pensando" and self.fila > 1) else str(self.fila)
        q["boca"] = s["boca"]
        q["boca_sx"], q["boca_sy"] = 0.9 + a * 0.2, 0.12 + a * 0.95
        return q


# --- posição na tela ----------------------------------------------------------------------------


def posicao_padrao(area: tuple, lado: int = LADO_JANELA, folga: int = FOLGA, margem: int = 8) -> tuple[int, int]:
    """Logo acima do relógio: canto inferior direito da área de trabalho (sem a barra de tarefas).
    area = (esquerda, topo, direita, baixo) do monitor principal, com direita/baixo exclusivos."""
    esq, topo, dir_, baixo = area
    x = dir_ - lado + folga - margem
    y = baixo - lado + folga - 4
    return max(esq - folga, x), max(topo - folga, y)


def posicao_valida(pos, telas: list, lado: int = LADO_JANELA) -> bool:
    """A posição salva ainda cai (pelo menos o meio do robô) em algum monitor? telas = [(esq, topo, dir, baixo)]."""
    try:
        x, y = int(pos[0]), int(pos[1])
    except (TypeError, ValueError, IndexError):
        return False
    cx, cy = x + lado // 2, y + lado // 2
    return any(e <= cx < d and t <= cy < b for e, t, d, b in telas)


def arquivo_posicao() -> Path:
    base = os.environ.get("MESTRE_SEGREDOS") or os.environ.get("APPDATA") or str(Path.home() / ".config")
    return Path(base) / "Mestre" / "avatar.json"


def ler_posicao():
    try:
        dados = json.loads(arquivo_posicao().read_text(encoding="utf-8"))
        return int(dados["x"]), int(dados["y"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


def salvar_posicao(pos) -> None:
    arq = arquivo_posicao()
    try:
        if pos is None:
            arq.unlink(missing_ok=True)
            return
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(json.dumps({"x": int(pos[0]), "y": int(pos[1])}), encoding="utf-8")
    except OSError:
        pass


# --- configuração: avatar ou bolinha --------------------------------------------------------------
TIPOS = {"avatar": "Avatar robô", "bolinha": "Bolinha"}


def tipo_escolhido(cfg: dict) -> str:
    tipo = str((cfg.get("indicador") or {}).get("tipo") or "avatar").strip().lower()
    return tipo if tipo in TIPOS else "avatar"


def pyside_instalado() -> bool:
    try:
        return importlib.util.find_spec("PySide6") is not None
    except (ImportError, ValueError):
        return False


# --- processo do avatar (ligado pelo Assessor) ----------------------------------------------------
ATIVO = False            # True = o avatar está na tela (a voz manda o volume para a boca)
_processo: subprocess.Popen | None = None


def _python_sem_janela() -> str:
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    return str(pythonw) if pythonw.exists() else sys.executable


def iniciar(nome: str = "Assessor", palavra: str = "assessor"):
    """Abre o avatar num processo separado. None = não deu (sem PySide6, teste automático...): use a bolinha."""
    global _processo, ATIVO
    if os.environ.get("MESTRE_SIMULAR") == "1":
        return None   # teste automático: nada aparece na tela
    if not pyside_instalado():
        log.info("Avatar: PySide6 não instalado, usando a bolinha")
        return None
    from .config import PASTA_PROJETO
    try:
        _processo = subprocess.Popen(
            [_python_sem_janela(), "-m", "app.avatar_janela", "--pai", str(os.getpid()), "--nome", nome,
             "--palavra", palavra], cwd=str(PASTA_PROJETO), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except OSError as erro:
        log.warning("Avatar não abriu (%s): usando a bolinha", erro)
        return None
    ATIVO = True
    return _processo


def acompanhar(processo, rodando) -> str:
    """Fica de olho no avatar enquanto o Assessor roda (linha principal).
    Devolve "falhou" (fechou com erro: use a bolinha), "escondido" (o usuário escondeu) ou "desligou"."""
    global ATIVO
    while rodando():
        codigo = processo.poll()
        if codigo is not None:
            ATIVO = False
            if codigo == 0:
                log.info("Avatar escondido pelo usuário")
                while rodando():
                    time.sleep(0.3)
                return "escondido"
            log.warning("Avatar fechou com erro (código %s): usando a bolinha", codigo)
            return "falhou"
        time.sleep(0.2)
    return "desligou"


def encerrar(espera: float = 1.0) -> None:
    """Assessor desligando: dá tempo da despedida (o avatar lê "desligado") e fecha de vez."""
    global ATIVO
    ATIVO = False
    p = _processo
    if p is None or p.poll() is not None:
        return
    try:
        p.wait(espera)
    except subprocess.TimeoutExpired:
        try:
            p.terminate()
        except OSError:
            pass


# --- volume da fala -> boca (UDP local, só enquanto fala) ---------------------------------------
_sock = None


def enviar_nivel(valor: float) -> None:
    global _sock
    if not ATIVO:
        return
    try:
        if _sock is None:
            _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _sock.sendto(f"{max(0.0, min(1.0, valor)):.3f}".encode(), ("127.0.0.1", PORTA_NIVEL))
    except OSError:
        pass


_envelopes: dict = {}
PASSO_ENVELOPE = 1 / 30   # um valor a cada ~33 ms


def envelope(arquivo: Path) -> list[float] | None:
    """Volume (0 a 1) a cada 33 ms do áudio que vai tocar. Guardado (as falas fixas repetem). None = não deu."""
    try:
        chave = (str(arquivo), arquivo.stat().st_mtime)
    except OSError:
        return None
    if chave in _envelopes:
        return _envelopes[chave]
    try:
        import numpy as np

        if arquivo.suffix.lower() == ".wav":
            import wave
            with wave.open(str(arquivo), "rb") as w:
                taxa, canais, largura = w.getframerate(), w.getnchannels(), w.getsampwidth()
                bruto = w.readframes(w.getnframes())
            tipo = {1: np.int8, 2: np.int16, 4: np.int32}.get(largura)
            if tipo is None:
                return None
            amostras = np.frombuffer(bruto, dtype=tipo).astype(np.float32)
            if canais > 1:
                amostras = amostras[: len(amostras) // canais * canais].reshape(-1, canais).mean(axis=1)
        else:   # mp3 (edge, azure, elevenlabs): o pygame decodifica
            import pygame
            import pygame.sndarray
            som = pygame.mixer.Sound(str(arquivo))
            amostras = pygame.sndarray.array(som).astype(np.float32)
            if amostras.ndim > 1:
                amostras = amostras.mean(axis=1)
            taxa = pygame.mixer.get_init()[0]
        passo = max(1, int(taxa * PASSO_ENVELOPE))
        n = len(amostras) // passo
        if n == 0:
            return None
        rms = np.sqrt((amostras[: n * passo].reshape(n, passo) ** 2).mean(axis=1))
        topo = float(np.percentile(rms, 95)) or 1.0
        valores = [round(min(1.0, float(v) / topo), 3) for v in rms]
    except Exception as erro:   # formato estranho: a boca usa o movimento "falso"
        log.debug("Envelope da fala falhou: %s", erro)
        return None
    if len(_envelopes) > 80:
        _envelopes.clear()
    _envelopes[chave] = valores
    return valores


def nivel_no_tempo(valores: list[float], ms: int) -> float:
    if not valores or ms < 0:
        return 0.0
    i = int(ms / 1000 / PASSO_ENVELOPE)
    return valores[i] if i < len(valores) else 0.0


# --- o Assessor ainda está vivo? ------------------------------------------------------------------


def processo_vivo(pid: int) -> bool:
    if pid <= 0:
        return True
    if sys.platform != "win32":
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
    import ctypes
    k32 = ctypes.windll.kernel32
    h = k32.OpenProcess(0x00100000 | 0x1000, False, pid)   # SYNCHRONIZE | QUERY_LIMITED_INFORMATION
    if not h:
        return False
    try:
        return k32.WaitForSingleObject(h, 0) == 0x102   # WAIT_TIMEOUT = ainda rodando
    finally:
        k32.CloseHandle(h)
