"""Pecas de audio usadas pelo Mestre e pela calibracao do painel.

- Segmentador: corta o som do microfone em "frases" usando um limite de volume
  (o "limiar"). Abaixo do limiar e silencio/ruido; acima e fala.
- Transcritor: Whisper (faster-whisper), transforma a frase em texto.
"""
import logging
import os
import sys
import threading
import time
import wave
from collections import deque
from pathlib import Path

import numpy as np

from .config import PASTA_LOGS

log = logging.getLogger(__name__)

TAXA = 16000            # amostras por segundo
BLOCO = 1600            # 0,1 segundo por bloco
PASTA_DIAGNOSTICO = PASTA_LOGS / "audios"
# Ligado enquanto o Whisper transcreve: a voz natural (placa de video) espera, para nao disputar a placa.
TRANSCREVENDO = threading.Event()


def esperar_whisper(limite: float = 10.0) -> None:
    """Espera o Whisper terminar a transcricao em andamento (no maximo `limite` segundos)."""
    fim = time.time() + limite
    while TRANSCREVENDO.is_set() and time.time() < fim:
        time.sleep(0.05)


def nivel(bloco: bytes | np.ndarray) -> float:
    """Volume do bloco (RMS), de 0 a ~32000."""
    a = np.frombuffer(bloco, dtype=np.int16) if isinstance(bloco, (bytes, bytearray)) else bloco
    return float(np.sqrt(np.mean(a.astype(np.float32) ** 2))) if len(a) else 0.0


def aplicar_ganho(bloco: bytes, ganho: float) -> bytes:
    if abs(ganho - 1.0) < 0.01:
        return bloco
    a = np.frombuffer(bloco, dtype=np.int16).astype(np.float32) * ganho
    return np.clip(a, -32768, 32767).astype(np.int16).tobytes()


def para_whisper(audio: bytes) -> np.ndarray:
    """int16 -> float32 com o volume normalizado (voz baixa fica audivel pro Whisper)."""
    a = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
    pico = float(np.max(np.abs(a))) if len(a) else 0.0
    if 0.01 < pico < 0.9:
        a = a * (0.9 / pico)
    return a


def salvar_wav(audio: bytes, caminho) -> None:
    with wave.open(str(caminho), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes(audio)


def guardar_diagnostico(audio: bytes, texto: str, maximo: int = 30) -> None:
    """Guarda as ultimas frases ouvidas em logs/audios (para ouvir o que chegou)."""
    PASTA_DIAGNOSTICO.mkdir(parents=True, exist_ok=True)
    nome = time.strftime("%Y%m%d_%H%M%S")
    salvar_wav(audio, PASTA_DIAGNOSTICO / f"{nome}.wav")
    with open(PASTA_DIAGNOSTICO / "transcricoes.txt", "a", encoding="utf-8") as f:
        f.write(f"{nome}.wav  ->  {texto!r}\n")
    for antigo in sorted(PASTA_DIAGNOSTICO.glob("*.wav"))[:-maximo]:
        antigo.unlink(missing_ok=True)


def sugerir_limiar(niveis_silencio: list[float]) -> float:
    """Limiar = um pouco acima do ruido mais alto do ambiente."""
    if not niveis_silencio:
        return 400.0
    ruido = float(np.percentile(niveis_silencio, 95))
    return round(max(ruido * 2.5, ruido + 150, 150.0), 0)


class Segmentador:
    """Recebe blocos de 0,1s e devolve uma frase completa quando a pessoa para de falar."""

    def __init__(self, limiar: float, silencio_fim: float = 0.8, min_fala: float = 0.35,
                 max_fala: float = 60.0, antes: float = 0.4):
        self.limiar = limiar
        self._blocos_silencio_fim = max(1, int(silencio_fim * TAXA / BLOCO))
        self._min_blocos = max(1, int(min_fala * TAXA / BLOCO))
        self._max_blocos = int(max_fala * TAXA / BLOCO)
        self._antes = deque(maxlen=max(1, int(antes * TAXA / BLOCO)))
        self.falando = False
        self._frase: list[bytes] = []
        self._fortes = 0
        self._silencio = 0
        self.descartada = 0.0   # segundos do ultimo trecho jogado fora por ser curto demais (o Ouvido registra)

    @property
    def duracao_atual(self) -> float:
        """Segundos ja gravados da frase em andamento (0 se ninguem esta falando)."""
        return len(self._frase) * BLOCO / TAXA if self.falando else 0.0

    def fechar(self, minimo: float = 0.0) -> bytes | None:
        """Encerra a frase em andamento agora (sem esperar a pausa). None se vazia ou mais curta que
        `minimo` segundos (e que o minimo do Segmentador)."""
        frase = list(self._frase) if self.falando else []
        self.reiniciar()
        if len(frase) < max(self._min_blocos, int(minimo * TAXA / BLOCO)):
            return None
        return b"".join(frase)

    def reiniciar(self) -> None:
        self.falando = False
        self._frase.clear()
        self._antes.clear()
        self._fortes = self._silencio = 0

    def processar(self, bloco: bytes) -> bytes | None:
        v = nivel(bloco)
        if not self.falando:
            self._antes.append(bloco)
            self._fortes = self._fortes + 1 if v >= self.limiar else 0
            if self._fortes >= 2:  # 0,2s acima do limiar: comecou a falar
                self.falando = True
                self._frase = list(self._antes)
                self._silencio = 0
            return None
        self._frase.append(bloco)
        self._silencio = self._silencio + 1 if v < self.limiar * 0.8 else 0
        if self._silencio >= self._blocos_silencio_fim or len(self._frase) >= self._max_blocos:
            frase = self._frase[:len(self._frase) - self._silencio + 2]
            self.reiniciar()
            if len(frase) >= self._min_blocos:
                return b"".join(frase)
            self.descartada = len(frase) * BLOCO / TAXA
        return None


class Transcritor:
    """Whisper local. Usa a placa de video NVIDIA se existir (bem mais rapido)."""

    PROMPT = ("E aí, {palavra}, bora trabalhar. Abre o YouTube. Pergunta pro agente IPM. "
              "Atende.Net, chamado, folha de pagamento.")

    def __init__(self, modelo: str = "small", precisao: str = "equilibrado", dispositivo: str = "auto",
                 palavras_extras: list[str] | None = None, palavra: str = "mestre"):
        self.nome_modelo = modelo
        self.beam = {"rapido": 1, "equilibrado": 3, "preciso": 5}.get(precisao, 3)
        extras = ", ".join((palavras_extras or [])[:40])
        self.prompt = self.PROMPT.format(palavra=palavra.capitalize()) + (f" {extras}." if extras else "")
        self._trava = threading.Lock()
        self._carregar(*self._escolher_dispositivo(dispositivo))

    def _carregar(self, dispositivo: str, tipo: str) -> None:
        from faster_whisper import WhisperModel

        log.info("Carregando Whisper '%s' em %s (%s)...", self.nome_modelo, dispositivo, tipo)
        self.dispositivo = dispositivo
        try:
            # ja baixado antes? carrega so do cache local, sem checar a internet (liga mais rapido)
            self.modelo = WhisperModel(self.nome_modelo, device=dispositivo, compute_type=tipo, local_files_only=True)
        except Exception:
            log.info("Whisper '%s' nao esta no cache local: baixando (precisa de internet)...", self.nome_modelo)
            self.modelo = WhisperModel(self.nome_modelo, device=dispositivo, compute_type=tipo)

    @staticmethod
    def _escolher_dispositivo(dispositivo: str) -> tuple[str, str]:
        if dispositivo in ("auto", "gpu") and gpu_disponivel():
            return "cuda", "float16"
        if dispositivo == "gpu":
            log.warning("Placa de video pedida, mas as bibliotecas da NVIDIA nao estao prontas. Usando o processador. "
                        "Para ativar: ferramentas\\11_ativar_placa_de_video.bat")
        return "cpu", "int8"

    def _rodar(self, audio: bytes, caprichado: bool = False, contexto: str = "") -> str:
        if caprichado:
            # Ditado: precisao maxima, sem cortar pontas de palavras, e o texto anterior como contexto
            prompt = (self.prompt + " " + contexto[-220:]).strip()
            segmentos, _ = self.modelo.transcribe(
                para_whisper(audio), language="pt", beam_size=5, best_of=5,
                initial_prompt=prompt, condition_on_previous_text=True,
                vad_filter=False, no_speech_threshold=0.5,
            )
        else:
            segmentos, _ = self.modelo.transcribe(
                para_whisper(audio), language="pt", beam_size=self.beam,
                initial_prompt=self.prompt, condition_on_previous_text=False,
                vad_filter=True, no_speech_threshold=0.6,
            )
        return " ".join(s.text for s in segmentos).strip()

    def transcrever_arquivo(self, caminho) -> str:
        """Audio de um arquivo (ogg do WhatsApp/Telegram, m4a, mp3...): precisao maxima, frases longas."""
        from faster_whisper import decode_audio

        with self._trava:
            TRANSCREVENDO.set()
            try:
                segmentos, _ = self.modelo.transcribe(
                    decode_audio(str(caminho), sampling_rate=16000), language="pt", beam_size=5, best_of=5,
                    initial_prompt=self.prompt, condition_on_previous_text=True, vad_filter=True)
                return " ".join(s.text for s in segmentos).strip()
            finally:
                TRANSCREVENDO.clear()

    def transcrever(self, audio: bytes, caprichado: bool = False, contexto: str = "") -> str:
        with self._trava:   # o microfone e os audios do celular usam o mesmo modelo, um de cada vez
            TRANSCREVENDO.set()
            try:
                return self._transcrever(audio, caprichado, contexto)
            finally:
                TRANSCREVENDO.clear()

    def aquecer(self) -> float:
        """Transcreve 1 s de quase silencio ao ligar: a 1a frase de verdade nao paga o custo de "acordar" o
        modelo (na placa de video, ~2 s). Devolve quanto tempo levou (0 se falhou)."""
        inicio = time.time()
        try:
            ruido = (np.random.default_rng(0).normal(0, 0.003, TAXA)).astype(np.float32)
            with self._trava:
                segmentos, _ = self.modelo.transcribe(ruido, language="pt", beam_size=self.beam,
                                                      initial_prompt=self.prompt, condition_on_previous_text=False,
                                                      vad_filter=False)
                list(segmentos)   # (o faster-whisper so trabalha de verdade quando le os segmentos)
        except Exception as erro:
            log.info("Nao consegui aquecer o Whisper (%s): a 1a frase pode demorar um pouco mais", erro)
            return 0.0
        gasto = time.time() - inicio
        log.info("Whisper aquecido em %.1fs", gasto)
        return gasto

    def _transcrever(self, audio: bytes, caprichado: bool = False, contexto: str = "") -> str:
        try:
            return self._rodar(audio, caprichado, contexto)
        except (RuntimeError, OSError) as erro:
            # Ex.: "Library cublas64_12.dll is not found": a placa existe, mas falta biblioteca da NVIDIA.
            if self.dispositivo != "cuda":
                raise
            log.warning("A placa de video falhou (%s). Passando a usar o processador.", erro)
            self._carregar("cpu", "int8")
            return self._rodar(audio, caprichado, contexto)


# --- Placa de video NVIDIA -------------------------------------------------------
def _preparar_dlls_nvidia() -> None:
    """No Windows, as bibliotecas da NVIDIA instaladas pelo pip (11_ativar_placa_de_video.bat)
    ficam em site-packages/nvidia/*/bin. Avisa o Windows para procurar la."""
    if sys.platform != "win32":
        return
    import site

    pastas = []
    for base in site.getsitepackages() + [site.getusersitepackages()]:
        pastas += [str(p) for p in Path(base).glob("nvidia/*/bin") if p.is_dir()]
    for pasta in pastas:
        try:
            os.add_dll_directory(pasta)
        except OSError:
            pass
    if pastas:
        os.environ["PATH"] = os.pathsep.join(pastas + [os.environ.get("PATH", "")])


def gpu_disponivel() -> bool:
    """True se existe placa NVIDIA E as bibliotecas (cuBLAS e cuDNN do CUDA 12) carregam."""
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() == 0:
            return False
    except Exception:
        return False
    if sys.platform != "win32":
        return True
    _preparar_dlls_nvidia()
    import ctypes

    for dll in ("cublas64_12.dll", "cudnn64_9.dll"):
        try:
            ctypes.WinDLL(dll)
        except OSError:
            log.info("Placa NVIDIA encontrada, mas falta %s: usando o processador.", dll)
            return False
    return True


def tem_placa_nvidia() -> bool:
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        return False
