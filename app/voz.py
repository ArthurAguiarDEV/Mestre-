"""Boca do Mestre: transforma texto em fala."""
import asyncio
import hashlib
import logging
import queue
import re
import tempfile
import threading
import time
from pathlib import Path

from . import estado

log = logging.getLogger(__name__)
LIMITE_CACHE = 90   # frases ate este tamanho ficam guardadas prontas


def fluir(texto: str) -> str:
    """Fala mais fluida: tira virgulas e reticencias que viram pausas "de robo".

    Mantem pontos finais (a pausa entre frases soa natural) e virgulas entre numeros.
    """
    texto = re.sub(r"\.{2,}|…", ".", texto)
    texto = re.sub(r"(?<!\d),(?!\d)", "", texto)
    texto = re.sub(r"\s*[;–—]\s*", ". ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _vozes_kokoro() -> dict:
    from .voz_kokoro import VOZES
    return VOZES


def dividir_frases(texto: str) -> list[str]:
    """Quebra nas frases; junta as muito curtas para nao picotar."""
    partes, atual = [], ""
    for frase in re.split(r"(?<=[.!?])\s+", texto.strip()):
        atual = f"{atual} {frase}".strip()
        if len(atual) >= 40:
            partes.append(atual)
            atual = ""
    if atual:
        partes.append(atual)
    return partes or [texto]


class Voz:
    def __init__(self, cfg: dict, mudo: bool = False):
        c = cfg.get("voz", {})
        # kokoro (no PC) | natural (placa de video) | edge (internet, gratis) | azure | elevenlabs | windows
        self.motor = c.get("motor", "kokoro")
        self.voz_edge = c.get("voz_edge", "pt-BR-AntonioNeural")
        self.voz_kokoro = c.get("voz_kokoro", "pm_alex")
        self.voz_azure = c.get("voz_azure", "pt-BR-AntonioNeural")
        self.voz_natural = c.get("voz_natural", "antonio")
        self.voz_elevenlabs = c.get("voz_elevenlabs", "pNInz6obpgDQGcFmaJgB")
        self.modelo_elevenlabs = c.get("modelo_elevenlabs", "eleven_flash_v2_5")
        self.velocidade = c.get("velocidade", "+0%")
        self.tom = c.get("tom", "+0Hz")
        self.fluida = bool(c.get("fluida", True))
        self.trocas: list[tuple[str, str]] = []   # (padrao, troca) aplicadas antes de falar
        self.registro: list[str] | None = None   # o Executor junta aqui o que foi falado (historico)
        self.mudo = mudo
        # Enquanto fala, o ouvido ignora o microfone (para nao ouvir a si mesmo).
        self.falando = threading.Event()
        self.terminou_em = 0.0
        self._trava = threading.Lock()
        self._pasta = Path(tempfile.gettempdir()) / "mestre_voz"
        self._pasta.mkdir(exist_ok=True)
        self._pygame_ok = False

    def configurar(self, voz=None, velocidade=None, tom=None) -> None:
        """Troca voz, velocidade ("+10%") ou tom ("-5Hz"); None mantem como esta."""
        if voz and self.motor == "kokoro" and voz in _vozes_kokoro():
            self.voz_kokoro = voz
        elif voz and self.motor == "azure" and voz.startswith("pt-"):
            self.voz_azure = voz
        elif voz and self.motor == "natural" and "-" not in voz:
            self.voz_natural = voz
        elif voz and self.motor == "elevenlabs" and "-" not in voz and "_" not in voz:
            self.voz_elevenlabs = voz
        if voz and "-" in voz:   # (nomes da Microsoft: "pt-BR-AntonioNeural"; os da Kokoro: "pm_alex")
            self.voz_edge = voz
        self.velocidade = velocidade or self.velocidade
        self.tom = tom or self.tom

    def trocar(self, texto: str) -> str:
        """Aplica as trocas numa passada so: o que ja foi trocado nao e trocado de novo
        (ex.: apelido "Mestre" nao pode virar o nome da palavra de ativacao)."""
        if not self.trocas:
            return texto
        padrao = "|".join(f"({p})" for p, _ in self.trocas)
        return re.sub(padrao, lambda m: next(self.trocas[i][1] for i, g in enumerate(m.groups()) if g is not None),
                      texto)

    def falar(self, texto: str) -> None:
        if not texto:
            return
        texto = self.trocar(texto)
        if self.registro is not None:
            self.registro.append(texto)
        print(f"MESTRE: {texto}")
        log.info("Falando: %s", texto)
        estado.atualizar(ultima_resposta=texto)
        if self.mudo:
            return
        with self._trava:
            self.falando.set()
            anterior = estado.ler()["nome"]
            estado.atualizar(ultima_resposta=texto)
            estado.definir("falando", texto)
            try:
                if self.motor != "windows" and self._falar_por_partes(texto):
                    return
                self._falar_windows(texto)
            finally:
                self.terminou_em = time.time()
                self.falando.clear()
                if estado.ler()["nome"] == "falando":
                    estado.definir(anterior if anterior != "falando" else "ouvindo")

    def bipe(self, tipo: str = "pronto") -> None:
        """Um toque curtinho (0,15 s) no lugar de uma fala: "fundo" = grave, "pronto" = dois agudos."""
        if self.mudo:
            return
        arquivo = self._pasta / f"bipe_{tipo}.wav"
        if not arquivo.exists():
            import wave

            import numpy as np

            taxa = 22050
            notas = [(440, 0.14)] if tipo == "fundo" else [(880, 0.08), (1175, 0.1)]
            partes = []
            for freq, dur in notas:
                t = np.linspace(0, dur, int(taxa * dur), False)
                envelope = np.minimum(1, np.minimum(t, dur - t) * 60)
                partes.append(np.sin(2 * np.pi * freq * t) * envelope * 0.35)
            onda = (np.concatenate(partes) * 32767).astype(np.int16)
            with wave.open(str(arquivo), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(taxa)
                w.writeframes(onda.tobytes())
        self.falando.set()
        try:
            self._tocar(arquivo)
        except Exception as erro:
            log.warning("Nao consegui tocar o bipe: %s", erro)
        finally:
            self.terminou_em = time.time()
            self.falando.clear()

    def falar_em_segundo_plano(self, texto: str) -> None:
        threading.Thread(target=self.falar, args=(texto,), daemon=True).start()

    # --- Vozes naturais: kokoro (no PC), natural (placa de video), edge (internet, gratis), azure e
    #     elevenlabs (chave) --------------------------------------------------------------------------
    def _motor_pronto(self, motor: str) -> bool:
        if motor == "kokoro":
            from . import voz_kokoro
            return voz_kokoro.pronto()
        if motor == "natural":
            from . import voz_natural
            return voz_natural.instalado()
        if motor == "azure":
            from . import voz_azure
            return voz_azure.configurado()
        if motor == "elevenlabs":
            from . import voz_elevenlabs
            return voz_elevenlabs.configurado()
        return motor == "edge"

    def _motores(self) -> list[str]:
        """O escolhido e, se ele nao estiver pronto ou falhar: a Kokoro (no PC) e depois a Edge."""
        return [m for m in dict.fromkeys([self.motor, "kokoro", "edge"]) if self._motor_pronto(m)]

    def _voz_do_motor(self, motor: str) -> str:
        return {"kokoro": self.voz_kokoro, "azure": self.voz_azure, "natural": self.voz_natural,
                "elevenlabs": f"{self.voz_elevenlabs}|{self.modelo_elevenlabs}"}.get(motor, self.voz_edge)

    def _arquivo_cache(self, parte: str, motor: str | None = None) -> Path:
        motor = motor or self.motor
        chave = hashlib.md5(f"{motor}|{self._voz_do_motor(motor)}|{self.velocidade}|{self.tom}|{parte}".encode()).hexdigest()
        return self._pasta / "cache" / f"{chave}{'.wav' if motor in ('kokoro', 'natural') else '.mp3'}"

    def _gerar(self, parte: str, motor: str | None = None) -> tuple[Path, bool]:
        """Gera (ou pega do cache) o audio de um pedaco. Devolve (arquivo, e_temporario)."""
        motor = motor or self.motor
        cache = self._arquivo_cache(parte, motor)
        if cache.exists() and cache.stat().st_size > 0:
            return cache, False
        guardar = len(parte) <= LIMITE_CACHE
        destino = cache if guardar else self._pasta / f"fala_{time.time_ns()}{cache.suffix}"
        destino.parent.mkdir(exist_ok=True)
        temporario = destino.with_name(destino.stem + ".parcial")
        if motor == "kokoro":
            from . import voz_kokoro
            voz_kokoro.gerar(parte, self.voz_kokoro, voz_kokoro.velocidade(self.velocidade), temporario)
        elif motor == "natural":
            from . import voz_natural
            voz_natural.gerar(parte, self.voz_natural, temporario)
        elif motor == "azure":
            from . import voz_azure
            voz_azure.gerar(parte, self.voz_azure, self.velocidade, self.tom, temporario)
        elif motor == "elevenlabs":
            from . import voz_elevenlabs
            voz_elevenlabs.gerar(parte, self.voz_elevenlabs, self.modelo_elevenlabs, self.velocidade, temporario)
        else:
            import edge_tts

            async def gerar():
                await edge_tts.Communicate(parte, self.voz_edge, rate=self.velocidade, pitch=self.tom).save(str(temporario))

            asyncio.run(gerar())
        temporario.replace(destino)
        return destino, not guardar

    def _gerar_com_reserva(self, parte: str) -> tuple[Path, bool]:
        erro = None
        for motor in self._motores():
            try:
                return self._gerar(parte, motor)
            except Exception as e:   # sem internet, chave errada, modelo faltando...
                log.warning("Voz %s falhou (%s)", motor, e)
                erro = e
        raise erro or RuntimeError("nenhuma voz pronta")

    def _falar_por_partes(self, texto: str) -> bool:
        """Fala por partes: a 1a frase comeca a tocar enquanto as seguintes sao geradas."""
        partes = dividir_frases(fluir(texto) if self.fluida else texto)
        prontos: queue.Queue = queue.Queue()

        def produzir():
            for parte in partes:
                try:
                    prontos.put(self._gerar_com_reserva(parte))
                except Exception as erro:
                    prontos.put(erro)
                    return
            prontos.put(None)

        threading.Thread(target=produzir, daemon=True).start()
        tocou_algo = False
        while True:
            item = prontos.get()
            if item is None:
                return True
            if isinstance(item, Exception):
                log.warning("Voz natural falhou (%s). Usando a voz do Windows.", item)
                return tocou_algo
            arquivo, temporario = item
            self._tocar(arquivo)
            tocou_algo = True
            if temporario:
                arquivo.unlink(missing_ok=True)

    _falar_edge = _falar_por_partes   # (nome antigo)

    def aquecer(self, frases: list[str]) -> None:
        """Prepara em segundo plano o audio das falas fixas (depois saem na hora).
        ElevenLabs: nao (gastaria os creditos; cada frase fica guardada na primeira vez que ele fala)."""
        def trabalho():
            if self.motor == "kokoro":
                from . import voz_kokoro
                voz_kokoro.aquecer()
            if self.motor == "natural":   # liga o servidor e espera o modelo carregar (1 a 2 minutos)
                from . import voz_natural
                voz_natural.iniciar()
                fim = time.time() + 600
                while time.time() < fim and not voz_natural.pronta():
                    if voz_natural.estado().get("erro"):
                        log.warning("Voz natural nao ligou: %s", voz_natural.estado()["erro"])
                        return
                    time.sleep(3)
            for f in frases:
                while self.motor == "natural" and estado.ler()["nome"] in ("gravando", "transcrevendo", "falando"):
                    time.sleep(0.5)   # (a placa de video fica livre para o Whisper enquanto voce fala)
                for parte in dividir_frases(fluir(f) if self.fluida else f):
                    if len(parte) <= LIMITE_CACHE and not self._arquivo_cache(parte).exists():
                        try:
                            self._gerar(parte)
                        except Exception:
                            return  # sem internet / modelo ainda baixando: tenta de novo na proxima vez
        if self.motor not in ("windows", "elevenlabs") and not self.mudo and self._motor_pronto(self.motor):
            threading.Thread(target=trabalho, daemon=True).start()

    def _tocar(self, arquivo: Path) -> None:
        import pygame

        if not self._pygame_ok:
            pygame.mixer.init()
            self._pygame_ok = True
        pygame.mixer.music.load(str(arquivo))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.02)
        pygame.mixer.music.unload()

    # --- Voz do Windows (offline) ----------------------------------------
    def _falar_windows(self, texto: str) -> None:
        try:
            import pyttsx3

            motor = pyttsx3.init()
            for v in motor.getProperty("voices"):
                if "portug" in (v.name or "").lower() or "pt" in str(v.languages).lower():
                    motor.setProperty("voice", v.id)
                    break
            motor.say(texto)
            motor.runAndWait()
        except Exception as erro:
            log.error("Nenhuma voz disponivel: %s", erro)
