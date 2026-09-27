"""Responder só à voz do dono (verificação de locutor).

Um vídeo tocando na caixa de som (ou outra pessoa na sala) pode dizer algo parecido com a
palavra de ativação. Aqui cada frase que VAI ser executada é comparada com a "impressão de
voz" do dono (média dos embeddings de ~10 frases gravadas no painel > Áudio > Minha voz).

- Modelo: SpeechBrain ECAPA (speechbrain/spkrec-ecapa-voxceleb), grátis e local, em modelos/locutor_ecapa.
- A impressão fica FORA do projeto: %APPDATA%\\Mestre\\voz_dono.json (junto do segredos.json).
- Nunca trava a escuta: o modelo carrega em segundo plano; enquanto não carregou, deixa passar.
- Frase muito curta (< 1 s) quase não tem voz para comparar: dentro da janela de conversa passa,
  fora dela a exigência fica um pouco menor (TOLERANCIA_CURTA).
"""
import json
import logging
import threading
import time
from pathlib import Path

import numpy as np

from .config import PASTA_MODELOS

log = logging.getLogger(__name__)

TAXA = 16000
MODELO_HF = "speechbrain/spkrec-ecapa-voxceleb"
PASTA_MODELO = PASTA_MODELOS / "locutor_ecapa"
EXIGENCIA_PADRAO = 0.40        # cosseno mínimo (mesma pessoa no mesmo mic: ~0,55 a 0,8; outra: ~0 a 0,4)
FRASE_CURTA = 1.0              # segundos
TOLERANCIA_CURTA = 0.10        # frase curta fora da conversa: exige um pouco menos
MAXIMO_SEGUNDOS = 10.0         # frase longa (ditado): compara só os primeiros 10 s (mais rápido)
MINIMO_CADASTRO = 5            # frases mínimas para gerar a impressão

FRASES_CADASTRO = [
    "{palavra}, abre o YouTube.",
    "{palavra}, que horas são agora?",
    "{palavra}, toca a minha playlist no Spotify.",
    "Bom dia, {palavra}. Bora trabalhar.",
    "{palavra}, pesquisa a previsão do tempo para amanhã.",
    "{palavra}, pausa o vídeo e aumenta o volume.",
    "Anota aí: comprar pão e café no fim da tarde.",
    "{palavra}, abre o painel e mostra as melhorias.",
    "Hoje eu vou revisar a folha de pagamento com calma.",
    "{palavra}, pode desligar a tela do segundo monitor.",
]


# --- Configuração ----------------------------------------------------------------------
def opcoes(cfg: dict) -> tuple[bool, float]:
    """(ligado, exigencia) a partir do config (valores padrão se o config for antigo)."""
    o = (cfg or {}).get("ouvido") or {}
    try:
        exigencia = float(o.get("exigencia_voz", EXIGENCIA_PADRAO))
    except (TypeError, ValueError):
        exigencia = EXIGENCIA_PADRAO
    return bool(o.get("so_minha_voz", False)), min(0.9, max(0.05, exigencia))


# --- Impressão de voz (fora do projeto) --------------------------------------------------
def arquivo_impressao() -> Path:
    from . import segredos
    return segredos.arquivo().parent / "voz_dono.json"


def carregar_impressao() -> np.ndarray | None:
    try:
        dados = json.loads(arquivo_impressao().read_text(encoding="utf-8"))
        v = np.asarray(dados["impressao"], dtype=np.float32)
        return v if v.size else None
    except (OSError, ValueError, KeyError, TypeError):
        return None


def info_impressao() -> dict:
    try:
        return json.loads(arquivo_impressao().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def salvar_impressao(embeddings: list[np.ndarray]) -> np.ndarray:
    """Média dos embeddings (cada um normalizado) -> impressão de voz. Grava e devolve."""
    if not embeddings:
        raise ValueError("nenhuma frase gravada")
    vs = [normalizar(e) for e in embeddings]
    media = normalizar(np.mean(vs, axis=0))
    notas = [cosseno(v, media) for v in vs]
    destino = arquivo_impressao()
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps({"impressao": [round(float(x), 6) for x in media], "frases": len(vs),
                                   "data": time.strftime("%d/%m/%Y %H:%M"),
                                   "nota_minima_cadastro": round(min(notas), 3)}), encoding="utf-8")
    return media


def apagar_impressao() -> None:
    arquivo_impressao().unlink(missing_ok=True)


# --- Matemática ------------------------------------------------------------------------
def normalizar(v) -> np.ndarray:
    v = np.asarray(v, dtype=np.float32).reshape(-1)
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def cosseno(a, b) -> float:
    return float(np.dot(normalizar(a), normalizar(b)))


def decidir(nota: float | None, exigencia: float, duracao: float, em_conversa: bool = False) -> tuple[bool, str]:
    """A regra (sem modelo): aceita? e por quê. nota None = não deu para comparar (passa)."""
    if nota is None:
        return True, "sem nota"
    if duracao < FRASE_CURTA:
        if em_conversa:
            return True, "frase curta na conversa"
        exigencia = exigencia - TOLERANCIA_CURTA
    return (nota >= exigencia), ("reconhecida" if nota >= exigencia else "voz não reconhecida")


def bytes_para_float(audio: bytes) -> np.ndarray:
    return np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0


def ler_wav(caminho) -> np.ndarray:
    """Um .wav qualquer (mono/estéreo, 16 bits, qualquer taxa) -> float32 mono em 16 kHz."""
    import wave

    with wave.open(str(caminho), "rb") as w:
        canais, taxa, largura = w.getnchannels(), w.getframerate(), w.getsampwidth()
        bruto = w.readframes(w.getnframes())
    if largura != 2:
        raise ValueError("só .wav de 16 bits")
    a = np.frombuffer(bruto, dtype=np.int16).astype(np.float32) / 32768.0
    if canais > 1:
        a = a.reshape(-1, canais).mean(axis=1)
    if taxa != TAXA:
        n = int(len(a) * TAXA / taxa)
        a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)
    return a


# --- Modelo (SpeechBrain) ----------------------------------------------------------------
def _baixar_modelo() -> Path:
    """Baixa os arquivos do modelo direto para modelos/locutor_ecapa (cópias reais: o Windows
    sem "modo desenvolvedor" não deixa criar atalhos simbólicos)."""
    necessarios = ("hyperparams.yaml", "embedding_model.ckpt", "mean_var_norm_emb.ckpt", "classifier.ckpt",
                   "label_encoder.txt")
    if all((PASTA_MODELO / n).exists() for n in necessarios):
        return PASTA_MODELO
    import os
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    from huggingface_hub import hf_hub_download

    PASTA_MODELO.mkdir(parents=True, exist_ok=True)
    for nome in necessarios:
        hf_hub_download(MODELO_HF, nome, local_dir=str(PASTA_MODELO))
    return PASTA_MODELO


def carregar_modelo():
    """Devolve uma função audio_float32_16k -> embedding (np.ndarray). Demora uns segundos."""
    import os
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")   # (torch e o Whisper trazem a mesma DLL do OpenMP)
    import torch
    from speechbrain.inference.speaker import EncoderClassifier
    from speechbrain.utils.fetching import LocalStrategy

    pasta = _baixar_modelo()
    torch.set_num_threads(max(1, min(4, torch.get_num_threads())))
    modelo = EncoderClassifier.from_hparams(source=str(pasta), savedir=str(pasta), run_opts={"device": "cpu"},
                                            local_strategy=LocalStrategy.NO_LINK)
    modelo.eval()

    def extrair(a: np.ndarray) -> np.ndarray:
        with torch.no_grad():
            e = modelo.encode_batch(torch.from_numpy(np.ascontiguousarray(a, dtype=np.float32)).unsqueeze(0))
        return e.squeeze().cpu().numpy().astype(np.float32)
    return extrair


class Verificador:
    """Guarda o modelo e a impressão; `verificar(audio)` diz se a frase é do dono.

    extrair: função audio -> embedding (o teste passa uma falsa; None = SpeechBrain, carregado em
    segundo plano por `carregar_em_segundo_plano`).
    """

    def __init__(self, ligado: bool = False, exigencia: float = EXIGENCIA_PADRAO, extrair=None):
        self.ligado = ligado
        self.exigencia = exigencia
        self._extrair = extrair
        self._trava = threading.Lock()
        self._carregando = False
        self.erro = ""
        self._impressao = None
        self._mtime = None
        self.ultima_nota: float | None = None

    @classmethod
    def do_config(cls, cfg: dict) -> "Verificador":
        ligado, exigencia = opcoes(cfg)
        v = cls(ligado, exigencia)
        if ligado and v.impressao() is not None:
            v.carregar_em_segundo_plano()
        elif ligado:
            log.info("'Responder só à minha voz' ligado, mas a voz não foi cadastrada: aceitando todas.")
        return v

    @property
    def pronto(self) -> bool:
        return self._extrair is not None

    def carregar_em_segundo_plano(self, ao_terminar=None) -> None:
        if self._extrair is not None or self._carregando:
            if ao_terminar and self._extrair is not None:
                ao_terminar(True)
            return
        self._carregando = True

        def trabalho():
            inicio = time.time()
            try:
                extrair = carregar_modelo()
                with self._trava:
                    self._extrair = extrair
                log.info("Reconhecimento da sua voz pronto (%.1fs para carregar).", time.time() - inicio)
                ok = True
            except Exception as erro:
                self.erro = str(erro)
                log.warning("Não consegui carregar o reconhecimento de voz (%s): aceitando todas as vozes.", erro)
                ok = False
            finally:
                self._carregando = False
            if ao_terminar:
                ao_terminar(ok)
        threading.Thread(target=trabalho, daemon=True, name="locutor").start()

    def impressao(self) -> np.ndarray | None:
        """A impressão salva (relida se o painel gravou uma nova)."""
        try:
            mtime = arquivo_impressao().stat().st_mtime
        except OSError:
            self._impressao, self._mtime = None, None
            return None
        if mtime != self._mtime:
            self._impressao, self._mtime = carregar_impressao(), mtime
        return self._impressao

    def embedding(self, audio: bytes | np.ndarray) -> np.ndarray:
        a = bytes_para_float(audio) if isinstance(audio, (bytes, bytearray)) else np.asarray(audio, dtype=np.float32)
        a = a[:int(MAXIMO_SEGUNDOS * TAXA)]
        with self._trava:
            return normalizar(self._extrair(a))

    def nota(self, audio) -> float | None:
        """Cosseno entre a frase e a impressão (None se não der para comparar)."""
        imp = self.impressao()
        if imp is None or self._extrair is None:
            return None
        return cosseno(self.embedding(audio), imp)

    def verificar(self, audio, em_conversa: bool = False) -> tuple[bool, float | None, str]:
        """(aceita, nota, motivo). Desligado, sem cadastro, modelo carregando ou erro: aceita."""
        if not self.ligado:
            return True, None, "desligado"
        if self.impressao() is None:
            return True, None, "sem cadastro"
        if self._extrair is None:
            return True, None, "modelo carregando"
        n = len(audio) / (TAXA * 2) if isinstance(audio, (bytes, bytearray)) else len(audio) / TAXA
        try:
            nota = self.nota(audio)
        except Exception as erro:   # nunca derruba a escuta
            log.warning("Falha ao comparar a voz (%s): aceitando.", erro)
            return True, None, "erro"
        self.ultima_nota = nota
        aceita, motivo = decidir(nota, self.exigencia, n, em_conversa)
        return aceita, nota, motivo
