"""Boca do Mestre: transforma texto em fala.

Fala em segundo plano (voz > fala_em_segundo_plano, padrao ligado): `falar` so poe o texto na FILA e volta na
hora; uma linha separada gera e toca, frase a frase (a 1a frase comeca a tocar enquanto as seguintes sao
geradas). Assim o microfone continua ouvindo enquanto ele fala, e `parar()` corta o som e a fila inteira na hora
("Assessor, para"). Quem precisa que a fala termine antes de seguir (desligar, reiniciar, bloquear) chama
`esperar()`.
"""
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


def dividir_frases(texto: str, maximo: int = 220) -> list[str]:
    """Quebra nas frases; junta as muito curtas para nao picotar. Frase enorme (sem ponto) e quebrada nas
    virgulas, para a 1a parte comecar a tocar logo."""
    partes, atual = [], ""
    for frase in re.split(r"(?<=[.!?])\s+", texto.strip()):
        atual = f"{atual} {frase}".strip()
        if len(atual) >= 40:
            partes.append(atual)
            atual = ""
    if atual:
        partes.append(atual)
    finais = []
    for parte in partes:
        while len(parte) > maximo:
            corte = max(parte.rfind(", ", 60, maximo), parte.rfind("; ", 60, maximo))
            if corte < 0:
                break
            finais.append(parte[:corte + 1])
            parte = parte[corte + 2:].strip()
        finais.append(parte)
    return [f for f in finais if f] or [texto]


class Voz:
    def __init__(self, cfg: dict, mudo: bool = False):
        c = cfg.get("voz", {})
        # kokoro (no PC) | natural (placa de video) | edge (internet, gratis) | azure | elevenlabs | windows
        self.motor = c.get("motor", "kokoro")
        self.reserva = str(c.get("reserva") or "kokoro")   # se o escolhido falhar (painel > Voz > "Usar como reserva")
        self.voz_edge = c.get("voz_edge", "pt-BR-AntonioNeural")
        self.voz_kokoro = c.get("voz_kokoro", "pm_alex")
        self.voz_azure = c.get("voz_azure", "pt-BR-AntonioNeural")
        self.voz_natural = c.get("voz_natural", "antonio")
        self.voz_elevenlabs = c.get("voz_elevenlabs", "pNInz6obpgDQGcFmaJgB")
        self.modelo_elevenlabs = c.get("modelo_elevenlabs", "eleven_flash_v2_5")
        self.velocidade = c.get("velocidade", "+0%")
        self.tom = c.get("tom", "+0Hz")
        self.fluida = bool(c.get("fluida", True))
        # Fala em segundo plano (a escuta continua enquanto ele fala), frase a frase (a 1a frase sai logo) e
        # interromper dizendo a palavra de ativacao (o Ouvido le esta opcao)
        self.em_segundo_plano = bool(c.get("fala_em_segundo_plano", True))
        self.frase_a_frase = bool(c.get("frase_a_frase", True))
        self.interromper = bool(c.get("interromper_com_palavra", True))
        self.trocas: list[tuple[str, str]] = []   # (padrao, troca) aplicadas antes de falar
        self.registro: list[str] | None = None   # o Executor junta aqui o que foi falado (historico)
        self.mudo = mudo
        # Enquanto fala, o ouvido trata o microfone como eco (so aceita frase que comeca com a palavra).
        self.falando = threading.Event()
        self.terminou_em = 0.0
        self._trava = threading.Lock()
        # Fila da fala em segundo plano: (texto ou ("bipe", tipo), geracao). parar() sobe a geracao: o que e de
        # geracao velha (tocando ou na fila) e cortado.
        self._fila: queue.Queue = queue.Queue()
        self._trava_fila = threading.Lock()
        self._linha: threading.Thread | None = None
        self._pendentes = 0
        self._textos: list[str] = []   # o que esta tocando + o que esta na fila (o ouvido reconhece o proprio eco)
        self._geracao = 0
        self._ocioso = threading.Event()
        self._ocioso.set()
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
        if self.em_segundo_plano:   # volta na hora: a escuta continua enquanto ele fala
            self._enfileirar(texto)
            return
        with self._trava:
            self.falando.set()
            anterior = estado.ler()["nome"]
            estado.atualizar(ultima_resposta=texto)
            estado.definir("falando", texto)
            try:
                self._falar_agora(texto)
            finally:
                self.terminou_em = time.time()
                self.falando.clear()
                if estado.ler()["nome"] == "falando":
                    estado.definir(anterior if anterior != "falando" else "ouvindo")

    def _falar_agora(self, texto: str) -> None:
        geracao = self._geracao
        if self.motor != "windows" and self._falar_por_partes(texto):
            return
        if geracao == self._geracao:   # (interrompido no meio: nao cai na voz do Windows)
            self._falar_windows(texto)

    # --- Fala em segundo plano -----------------------------------------------------------------------
    def _enfileirar(self, item) -> None:
        with self._trava_fila:
            self._pendentes += 1
            self._ocioso.clear()
            self.falando.set()   # (o microfone ja vira "eco": ele vai falar)
            if isinstance(item, str):
                self._textos.append(item)
            self._fila.put((item, self._geracao))
            if self._linha is None or not self._linha.is_alive():
                self._linha = threading.Thread(target=self._trabalhar, name="fala", daemon=True)
                self._linha.start()

    def _trabalhar(self) -> None:
        while True:
            item, geracao = self._fila.get()
            try:
                if geracao == self._geracao:
                    if isinstance(item, tuple):   # ("bipe", tipo)
                        self._tocar(self._arquivo_bipe(item[1]))
                    else:
                        estado.definir("falando", item)
                        self._falar_agora(item)
            except Exception:
                log.exception("Erro ao falar")
            finally:
                with self._trava_fila:
                    if isinstance(item, str) and item in self._textos:
                        self._textos.remove(item)
                    self._pendentes = max(0, self._pendentes - 1)
                    if self._pendentes == 0:
                        self._terminou()

    def _terminou(self) -> None:
        """Fila vazia: libera o microfone e volta o indicador (chamado com a _trava_fila)."""
        self.terminou_em = time.time()
        self.falando.clear()
        self._textos.clear()
        self._ocioso.set()
        e = estado.ler()
        if e["nome"] == "falando":
            estado.definir("conversa" if e["conversa_ate"] > time.time() else "ouvindo")

    def texto_falando(self) -> str:
        """O que ele esta falando agora (e o que ainda vai falar)."""
        with self._trava_fila:
            return " ".join(self._textos)

    def parar(self) -> bool:
        """Corta o som NA HORA e joga fora o resto da fila. Devolve True se estava falando."""
        with self._trava_fila:
            estava = self._pendentes > 0
            self._geracao += 1
            while True:
                try:
                    self._fila.get_nowait()
                except queue.Empty:
                    break
                self._pendentes = max(0, self._pendentes - 1)
            self._textos.clear()
            if self._pendentes == 0:
                self._terminou()
        if estava:
            log.info("Fala interrompida")
        return estava

    def esperar(self, limite: float = 30.0) -> bool:
        """Espera a fila de fala terminar (desligar, reiniciar, bloquear a tela...). True = terminou."""
        if self.mudo or not self.em_segundo_plano:
            return True
        return self._ocioso.wait(limite)

    def bipe(self, tipo: str = "pronto") -> None:
        """Um toque curtinho (0,15 s) no lugar de uma fala: "fundo" = grave, "pronto" = dois agudos."""
        if self.mudo:
            return
        if self.em_segundo_plano:   # (na mesma fila: nao corta a fala que esta tocando)
            self._enfileirar(("bipe", tipo))
            return
        self.falando.set()
        try:
            self._tocar(self._arquivo_bipe(tipo))
        except Exception as erro:
            log.warning("Nao consegui tocar o bipe: %s", erro)
        finally:
            self.terminou_em = time.time()
            self.falando.clear()

    def _arquivo_bipe(self, tipo: str) -> Path:
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
        return arquivo

    def falar_em_segundo_plano(self, texto: str) -> None:
        if self.em_segundo_plano:
            self.falar(texto)   # (ja volta na hora e respeita a ordem da fila)
            return
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
        """O escolhido e, se ele nao estiver pronto ou falhar: a reserva, a Kokoro (no PC) e depois a Edge."""
        return [m for m in dict.fromkeys([self.motor, getattr(self, "reserva", "kokoro"), "kokoro", "edge"])
                if self._motor_pronto(m)]

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
        if motor == "natural":   # a placa de video fica livre para o Whisper: espera ele terminar de transcrever
            from .audio import esperar_whisper
            esperar_whisper(10)
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

    def partes(self, texto: str) -> list[str]:
        """Pedacos que viram audio: frase a frase (padrao) ou o texto todo de uma vez."""
        if not self.frase_a_frase:
            return [fluir(texto) if self.fluida else texto]
        return [fluir(p) if self.fluida else p for p in dividir_frases(texto)]

    def _falar_por_partes(self, texto: str) -> bool:
        """Fala por partes: a 1a frase comeca a tocar enquanto as seguintes sao geradas.
        parar() no meio: o produtor para de gerar e o tocador corta o som (a fila inteira)."""
        partes = self.partes(texto)
        prontos: queue.Queue = queue.Queue()
        geracao = self._geracao
        inicio = time.time()
        primeira = True

        def produzir():
            for parte in partes:
                if geracao != self._geracao:   # interrompido: nem gera o resto
                    break
                try:
                    prontos.put(self._gerar_com_reserva(parte))
                except Exception as erro:
                    prontos.put(erro)
                    return
            prontos.put(None)

        threading.Thread(target=produzir, daemon=True).start()
        tocou_algo = False
        n_parte = 0
        while True:
            item = prontos.get()
            if item is None:
                return True
            if isinstance(item, Exception):
                log.warning("Voz natural falhou (%s). Usando a voz do Windows.", item)
                return tocou_algo
            arquivo, temporario = item
            texto_parte = partes[n_parte] if n_parte < len(partes) else ""
            n_parte += 1
            if geracao == self._geracao:
                if primeira:
                    from . import memoria
                    memoria.registrar_tempo("ate_falar", time.time() - inicio)
                    primeira = False
                from . import avatar
                avatar.enviar_texto(texto_parte)   # o personagem usa as vogais da frase na boca
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
                for parte in self.partes(f):
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
        geracao = self._geracao
        from . import avatar   # avatar na tela: a boca segue o volume da fala (UDP local, só enquanto fala)
        niveis = avatar.envelope(arquivo) if avatar.ATIVO else None
        pygame.mixer.music.load(str(arquivo))
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            if geracao != self._geracao:   # parar(): corta na hora
                pygame.mixer.music.stop()
                break
            if niveis:
                avatar.enviar_nivel(avatar.nivel_no_tempo(niveis, pygame.mixer.music.get_pos()))
            time.sleep(0.02)
        if niveis:
            avatar.enviar_nivel(0.0)
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
