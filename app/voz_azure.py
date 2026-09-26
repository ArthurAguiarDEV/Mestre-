"""Voz da Azure (Microsoft): gratis ate 500 mil letras por mes (umas 8 horas de fala).

Precisa de uma conta na Azure, um recurso "Speech" e a CHAVE + REGIAO (painel > Voz).
A chave fica em segredos.py (fora da pasta do projeto). Sem biblioteca extra: so HTTP.
"""
import logging
import urllib.request
from pathlib import Path
from xml.sax.saxutils import escape

from . import segredos

log = logging.getLogger(__name__)
VOZES = ["pt-BR-AntonioNeural", "pt-BR-FranciscaNeural", "pt-BR-ThalitaMultilingualNeural",
         "pt-BR-MacerioMultilingualNeural", "pt-BR-DonatoNeural", "pt-BR-FabioNeural", "pt-BR-HumbertoNeural",
         "pt-BR-JulioNeural", "pt-BR-NicolauNeural", "pt-BR-ValerioNeural", "pt-BR-BrendaNeural",
         "pt-BR-ElzaNeural", "pt-BR-GiovannaNeural", "pt-BR-LeilaNeural", "pt-BR-LeticiaNeural",
         "pt-BR-ManuelaNeural", "pt-BR-YaraNeural"]


def configurado() -> bool:
    return bool(segredos.ler("azure_chave") and segredos.ler("azure_regiao"))


def gerar(texto: str, voz: str, velocidade: str, tom: str, destino: Path) -> None:
    chave, regiao = segredos.ler("azure_chave"), segredos.ler("azure_regiao", "brazilsouth")
    if not chave:
        raise RuntimeError("falta a chave da Azure (painel > Voz)")
    ssml = (f"<speak version='1.0' xml:lang='pt-BR' xmlns='http://www.w3.org/2001/10/synthesis'>"
            f"<voice name='{escape(voz)}'><prosody rate='{escape(velocidade)}' pitch='{escape(tom)}'>"
            f"{escape(texto)}</prosody></voice></speak>")
    pedido = urllib.request.Request(
        f"https://{regiao}.tts.speech.microsoft.com/cognitiveservices/v1", data=ssml.encode("utf-8"), method="POST",
        headers={"Ocp-Apim-Subscription-Key": chave, "Content-Type": "application/ssml+xml",
                 "X-Microsoft-OutputFormat": "audio-24khz-48kbitrate-mono-mp3", "User-Agent": "Mestre"})
    with urllib.request.urlopen(pedido, timeout=15) as r:
        destino.write_bytes(r.read())
