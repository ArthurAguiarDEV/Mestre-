"""Voz Kokoro: gratis, roda NO SEU PC (sem internet depois de baixar), rapida e natural.

Modelo de 330 MB (uma vez so) em modelos/kokoro/. Biblioteca: kokoro-onnx.
Usa a placa de video se o onnxruntime-gpu estiver instalado; senao, o processador
(num Ryzen de 8 nucleos gera a fala umas 5 vezes mais rapido do que ela dura).
"""
import logging
import threading
import urllib.request
import wave
from pathlib import Path

from .config import PASTA_PROJETO

log = logging.getLogger(__name__)
PASTA = PASTA_PROJETO / "modelos" / "kokoro"
URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
ARQUIVOS = {"kokoro-v1.0.onnx": 310_000_000, "voices-v1.0.bin": 28_000_000}
VOZES = {"pm_alex": "Alex (masculina)", "pf_dora": "Dora (feminina)", "pm_santa": "Santa (masculina, mais grave)"}
VOZ_PADRAO = "pm_alex"
_kokoro = None
_trava = threading.Lock()


def biblioteca_instalada() -> bool:
    import importlib.util
    return importlib.util.find_spec("kokoro_onnx") is not None


def baixado() -> bool:
    return all((PASTA / nome).exists() for nome in ARQUIVOS)


def pronto() -> bool:
    return baixado() and biblioteca_instalada()


def baixar(progresso=None) -> str:
    """Baixa o modelo (uma vez). progresso(0..1) opcional. Devolve "" ou o erro."""
    PASTA.mkdir(parents=True, exist_ok=True)
    total = sum(ARQUIVOS.values())
    feito = 0
    try:
        for nome, tamanho in ARQUIVOS.items():
            destino = PASTA / nome
            if destino.exists():
                feito += tamanho
                continue
            parcial = destino.with_suffix(".parcial")
            with urllib.request.urlopen(URL + nome, timeout=60) as r, open(parcial, "wb") as f:
                while True:
                    bloco = r.read(1 << 20)
                    if not bloco:
                        break
                    f.write(bloco)
                    feito += len(bloco)
                    if progresso:
                        progresso(min(1.0, feito / total))
            parcial.replace(destino)
        return ""
    except Exception as erro:
        log.warning("Nao consegui baixar a voz Kokoro: %s", erro)
        return str(erro)


def _carregar():
    global _kokoro
    if _kokoro is None:
        import onnxruntime as ort
        from kokoro_onnx import Kokoro

        modelo, vozes = str(PASTA / "kokoro-v1.0.onnx"), str(PASTA / "voices-v1.0.bin")
        if "CUDAExecutionProvider" in ort.get_available_providers():
            try:
                sessao = ort.InferenceSession(modelo, providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
                _kokoro = Kokoro.from_session(sessao, vozes)
                log.info("Voz Kokoro na placa de video")
            except Exception as erro:
                log.info("Kokoro na placa de video falhou (%s): usando o processador", erro)
        if _kokoro is None:
            _kokoro = Kokoro(modelo, vozes)
    return _kokoro


def velocidade(texto_edge: str) -> float:
    """ "+10%" (o formato da voz edge, que o painel usa) -> 1.1"""
    try:
        return max(0.5, min(2.0, 1 + int(str(texto_edge).replace("%", "").replace("+", "")) / 100))
    except ValueError:
        return 1.0


def gerar(texto: str, voz: str, vel: float, destino: Path) -> None:
    import numpy as np

    with _trava:   # um de cada vez (o modelo nao e dividido entre linhas)
        audio, taxa = _carregar().create(texto, voice=voz if voz in VOZES else VOZ_PADRAO, speed=vel, lang="pt-br")
    onda = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(taxa)
        w.writeframes(onda.tobytes())


def aquecer() -> None:
    """Carrega o modelo em segundo plano ao ligar (a primeira fala ja sai rapida)."""
    if pronto():
        threading.Thread(target=lambda: _gerar_silencioso(), daemon=True).start()


def _gerar_silencioso() -> None:
    try:
        with _trava:
            _carregar().create("Oi.", voice=VOZ_PADRAO, lang="pt-br")
    except Exception as erro:
        log.info("Kokoro nao aqueceu: %s", erro)
