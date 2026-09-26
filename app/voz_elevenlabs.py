"""Voz da ElevenLabs: a mais natural de todas (paga; o plano gratis da uns 10 mil caracteres por mes).

Precisa de uma conta em elevenlabs.io e da CHAVE da API (painel > Voz). A chave fica em
segredos.py (fora da pasta do projeto). Sem biblioteca extra: so HTTP.
As falas fixas ficam guardadas (cache): cada frase repetida so gasta creditos na primeira vez.
"""
import json
import logging
import urllib.request
from pathlib import Path

from . import segredos

log = logging.getLogger(__name__)
API = "https://api.elevenlabs.io/v1"
# Vozes prontas da ElevenLabs (falam portugues com o modelo multilingue). Suas vozes aparecem no painel.
VOZES = {"pNInz6obpgDQGcFmaJgB": "Adam (masculina, grave)", "TX3LPaxmHKxFdv7VOQHJ": "Liam (masculina, jovem)",
         "onwK4e9ZLuTAKqWW03F9": "Daniel (masculina, calma)", "EXAVITQu4vr4xnSDxMaL": "Sarah (feminina)",
         "XrExE9yKIg1WjnnlVkGX": "Matilda (feminina, calorosa)"}
VOZ_PADRAO = "pNInz6obpgDQGcFmaJgB"
MODELOS = {"eleven_flash_v2_5": "Rápido (Flash v2.5, gasta metade)",
           "eleven_multilingual_v2": "Mais natural (Multilingual v2)"}
MODELO_PADRAO = "eleven_flash_v2_5"


def configurado() -> bool:
    return bool(segredos.ler("elevenlabs_chave"))


def _velocidade(velocidade: str) -> float:
    """ "+10%" -> 1.1 (a ElevenLabs aceita de 0,7 a 1,2)."""
    try:
        return max(0.7, min(1.2, 1 + int(str(velocidade).strip().rstrip("%") or 0) / 100))
    except ValueError:
        return 1.0


def gerar(texto: str, voz: str, modelo: str, velocidade: str, destino: Path) -> None:
    chave = segredos.ler("elevenlabs_chave")
    if not chave:
        raise RuntimeError("falta a chave da ElevenLabs (painel > Voz)")
    corpo = {"text": texto, "model_id": modelo or MODELO_PADRAO,
             "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "speed": _velocidade(velocidade)}}
    if (modelo or MODELO_PADRAO) == "eleven_flash_v2_5":
        corpo["language_code"] = "pt"
    pedido = urllib.request.Request(
        f"{API}/text-to-speech/{voz or VOZ_PADRAO}?output_format=mp3_44100_128", method="POST",
        data=json.dumps(corpo).encode("utf-8"),
        headers={"xi-api-key": chave, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    with urllib.request.urlopen(pedido, timeout=20) as r:
        destino.write_bytes(r.read())


def minhas_vozes(chave: str = "") -> dict:
    """Para o painel: {id: nome} das vozes da sua conta (inclui as que voce adicionou da biblioteca)."""
    chave = chave or segredos.ler("elevenlabs_chave")
    pedido = urllib.request.Request(f"{API}/voices", headers={"xi-api-key": chave})
    with urllib.request.urlopen(pedido, timeout=15) as r:
        dados = json.loads(r.read())
    return {v["voice_id"]: v.get("name", v["voice_id"]) for v in dados.get("voices", [])}
