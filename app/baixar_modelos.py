"""Baixa os modelos de reconhecimento de voz (roda uma vez, na instalacao)."""
import urllib.request
import zipfile

from .config import PASTA_MODELOS, carregar_config

VOSK_URL = "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"


def baixar_vosk() -> None:
    destino = PASTA_MODELOS / "vosk-model-small-pt-0.3"
    if destino.exists():
        print("[ok] Modelo Vosk ja existe.")
        return
    PASTA_MODELOS.mkdir(exist_ok=True)
    arquivo_zip = PASTA_MODELOS / "vosk.zip"
    print("Baixando o modelo Vosk em portugues (~31 MB)...")

    def progresso(blocos, tamanho_bloco, total):
        if total > 0:
            print(f"\r  {min(100, blocos * tamanho_bloco * 100 // total)}%", end="")

    urllib.request.urlretrieve(VOSK_URL, arquivo_zip, progresso)
    print("\nDescompactando...")
    with zipfile.ZipFile(arquivo_zip) as z:
        z.extractall(PASTA_MODELOS)
    arquivo_zip.unlink()
    print("[ok] Modelo Vosk instalado.")


def baixar_whisper() -> None:
    o = carregar_config().get("ouvido", {})
    if not o.get("usar_whisper", True):
        return
    tamanho = o.get("modelo_whisper", "small")
    print(f"Baixando o modelo Whisper '{tamanho}' (pode passar de 400 MB, tenha paciencia)...")
    from faster_whisper import WhisperModel

    WhisperModel(tamanho, device="cpu", compute_type="int8")
    print("[ok] Modelo Whisper pronto.")


if __name__ == "__main__":
    baixar_vosk()
    baixar_whisper()
    print("\nTodos os modelos estao prontos!")
