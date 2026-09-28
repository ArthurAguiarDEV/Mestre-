"""Palavra de ativacao local (opcional, DESLIGADA por padrao): um detector leve que ouve so a palavra
(ex.: "Assessor") ANTES do Whisper.

Ideia do openWakeWord (Apache-2.0), reimplementada aqui sem a biblioteca:
  1. espectrograma mel (modelos/palavra/melspectrogram.onnx, do openWakeWord v0.5.1, Apache-2.0)
  2. "speech embedding" do Google (modelos/palavra/embedding_model.onnx, Apache-2.0): 96 numeros a cada 80 ms
  3. um classificador pequeno treinado NESTE PC (modelos/palavra/<palavra>.npz: pesos de uma rede de 3 camadas,
     roda em numpy) olha os ultimos 16 (1,28 s) e da a nota 0..1 de "falaram a palavra agora".
So precisa do onnxruntime (ja vem com a voz Kokoro). Custa ~1,3 ms de processador a cada 80 ms (~1,6% de
UM nucleo), contra o Whisper transcrevendo toda frase que passa do limite de volume (video tocando = quase tudo).

O treino fica em ferramentas/treinar_palavra.py (ferramentas/15_treinar_palavra.bat).
Sem os arquivos (ou sem onnxruntime) o recurso fica indisponivel e o Ouvido segue o fluxo de sempre.
"""
import importlib.util
import logging
from collections import deque
from pathlib import Path

import numpy as np

from .config import caminho_do_projeto

log = logging.getLogger(__name__)

PASTA = "modelos/palavra"
MEL, EMBEDDING = "melspectrogram.onnx", "embedding_model.onnx"
LIMIAR_PADRAO = 0.5
QUADRO = 1280          # 80 ms a 16 kHz: o passo do detector
CONTEXTO = 480         # amostras anteriores usadas no espectrograma (8 quadros mel novos por passo)
JANELA_MEL = 76        # quadros mel por embedding
JANELA_EMB = 16        # embeddings que o classificador olha (1,28 s)


def nome_arquivo(palavra: str) -> str:
    """ "Assessor" -> "assessor.npz" (so letras/numeros)."""
    from .texto import normalizar

    base = "".join(c for c in normalizar(palavra or "palavra") if c.isalnum()) or "palavra"
    return f"{base}.npz"


def opcoes(cfg: dict) -> tuple[bool, Path, float]:
    """(ligado, arquivo do modelo, limiar). Config antigo: desligado, modelo da palavra configurada, 0.5."""
    from .config import palavras_ativacao

    o = (cfg or {}).get("ouvido") or {}
    ligado = bool(o.get("detector_palavra", False))
    try:
        limiar = min(0.95, max(0.05, float(o.get("detector_limiar", LIMIAR_PADRAO))))
    except (TypeError, ValueError):
        limiar = LIMIAR_PADRAO
    arquivo = o.get("detector_modelo") or f"{PASTA}/{nome_arquivo(palavras_ativacao(cfg or {})[0])}"
    return ligado, caminho_do_projeto(str(arquivo)), limiar


def biblioteca_instalada() -> bool:
    return importlib.util.find_spec("onnxruntime") is not None


def situacao(cfg: dict) -> tuple[bool, str]:
    """(pronto, texto para o painel). Nao carrega nada (rapido)."""
    ligado, arquivo, limiar = opcoes(cfg)
    pasta = arquivo.parent
    if not biblioteca_instalada():
        return False, "Indisponível: falta a biblioteca onnxruntime (rode a atualização/instalação de novo)."
    faltam = [n for n in (MEL, EMBEDDING) if not (pasta / n).exists()]
    if faltam or not arquivo.exists():
        return False, (f"Modelo não encontrado ({arquivo.name}). Treine com ferramentas\\15_treinar_palavra.bat "
                       "(uns 30 minutos, grátis, no seu PC). Enquanto isso o Whisper ouve tudo, como sempre.")
    estado = "ligado" if ligado else "desligado"
    return True, f"✔ Modelo pronto ({arquivo.name}), {estado}, exigência {limiar:.2f}."


class Caracteristicas:
    """Audio int16 a 16 kHz -> um embedding de 96 numeros a cada 80 ms (em fluxo, bloco a bloco).
    O treino usa esta MESMA classe: o que ele aprende e exatamente o que o detector ve ao vivo."""

    def __init__(self, pasta: Path, threads: int = 1):
        import onnxruntime as ort

        so = ort.SessionOptions()
        so.intra_op_num_threads = threads
        so.inter_op_num_threads = 1
        so.log_severity_level = 3
        cpu = ["CPUExecutionProvider"]
        self._mel = ort.InferenceSession(str(Path(pasta) / MEL), so, providers=cpu)
        self._emb = ort.InferenceSession(str(Path(pasta) / EMBEDDING), so, providers=cpu)
        self.reiniciar()

    def reiniciar(self) -> None:
        self._pendente = np.zeros(0, np.float32)
        self._cauda = np.zeros(CONTEXTO, np.float32)
        self._mels = np.ones((JANELA_MEL, 32), np.float32)
        self.embeddings: deque = deque(maxlen=64)

    def adicionar(self, amostras: np.ndarray) -> int:
        """Recebe amostras int16 (qualquer tamanho). Devolve quantos embeddings novos sairam."""
        self._pendente = np.concatenate([self._pendente, np.asarray(amostras).astype(np.float32)])
        novos = 0
        while len(self._pendente) >= QUADRO:
            quadro, self._pendente = self._pendente[:QUADRO], self._pendente[QUADRO:]
            janela = np.concatenate([self._cauda, quadro])
            self._cauda = janela[-CONTEXTO:]
            mel = np.squeeze(self._mel.run(None, {"input": janela[None, :]})[0]) / 10 + 2
            self._mels = np.vstack([self._mels, mel.reshape(-1, 32)[-8:]])[-JANELA_MEL:]
            emb = self._emb.run(None, {"input_1": self._mels[None, :, :, None].astype(np.float32)})[0]
            self.embeddings.append(np.asarray(emb, np.float32).reshape(-1))
            novos += 1
        return novos

    def ultimas(self, n: int = JANELA_EMB, fim: int = 0) -> np.ndarray | None:
        """Os `n` embeddings que terminam `fim` passos antes do ultimo, forma (1, n, 96). None se ainda nao ha."""
        total = len(self.embeddings)
        if total < n + fim:
            return None
        lista = list(self.embeddings)[total - n - fim: total - fim]
        return np.stack(lista)[None, :, :].astype(np.float32)


class Classificador:
    """Rede pequena (entrada 16x96 -> 64 -> 32 -> 1) em numpy. Pesos num .npz gravado pelo treino."""

    def __init__(self, pesos: dict):
        self.media = np.asarray(pesos["media"], np.float32)
        self.desvio = np.asarray(pesos["desvio"], np.float32)
        self.camadas = [(np.asarray(pesos[f"w{i}"], np.float32), np.asarray(pesos[f"b{i}"], np.float32))
                        for i in range(1, 10) if f"w{i}" in pesos]
        self.n = int(np.asarray(pesos.get("n", JANELA_EMB)))

    @classmethod
    def abrir(cls, arquivo: Path) -> "Classificador":
        with np.load(str(arquivo)) as z:
            return cls({k: z[k] for k in z.files})

    def notas(self, janelas: np.ndarray) -> np.ndarray:
        """(lote, n, 96) -> notas 0..1 (lote,)"""
        x = (np.asarray(janelas, np.float32).reshape(len(janelas), -1) - self.media) / self.desvio
        for i, (w, b) in enumerate(self.camadas):
            x = x @ w + b
            if i < len(self.camadas) - 1:
                x = np.maximum(x, 0.0)
        return (1.0 / (1.0 + np.exp(-np.clip(x, -30, 30)))).reshape(-1)


class Detector:
    """Da a nota (0..1) de "falaram a palavra" a cada bloco de audio. `ouvir(bloco)` -> maior nota do bloco."""

    def __init__(self, arquivo: Path, limiar: float = LIMIAR_PADRAO, threads: int = 1):
        self.arquivo = Path(arquivo)
        self.limiar = float(limiar)
        self.rede = Classificador.abrir(self.arquivo)
        self.n = self.rede.n
        self.caracteristicas = Caracteristicas(self.arquivo.parent, threads)

    def nota(self, janela: np.ndarray) -> float:
        return float(self.rede.notas(janela)[0])

    def ouvir(self, bloco: bytes | np.ndarray) -> float:
        a = np.frombuffer(bloco, dtype=np.int16) if isinstance(bloco, (bytes, bytearray)) else bloco
        novos = self.caracteristicas.adicionar(a)
        melhor = 0.0
        for fim in range(novos):
            janela = self.caracteristicas.ultimas(self.n, fim)
            if janela is not None:
                melhor = max(melhor, self.nota(janela))
        return melhor

    def reiniciar(self) -> None:
        self.caracteristicas.reiniciar()


def carregar(cfg: dict) -> tuple["Detector | None", str]:
    """(detector, motivo). None quando desligado, sem modelo ou sem biblioteca: o Ouvido segue como sempre."""
    ligado, arquivo, limiar = opcoes(cfg)
    if not ligado:
        return None, "desligado"
    pronto, texto = situacao(cfg)
    if not pronto:
        log.warning("Detector da palavra ligado, mas indisponível: %s", texto)
        return None, texto
    try:
        d = Detector(arquivo, limiar)
    except Exception as erro:   # modelo corrompido, onnxruntime quebrado...
        log.warning("Detector da palavra não carregou (%s): o Whisper ouve tudo, como sempre", erro)
        return None, f"erro ao carregar: {erro}"
    log.info("Detector da palavra ligado (%s, exigência %.2f): só frases com a palavra vão ao Whisper",
             arquivo.name, limiar)
    return d, "pronto"
