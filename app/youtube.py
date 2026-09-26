"""YouTube: ultimo video de um canal e busca de videos (gratis, sem chave de API)."""
import logging
from urllib.parse import quote_plus

log = logging.getLogger(__name__)

_OPCOES = {"quiet": True, "no_warnings": True, "extract_flat": True,
           "skip_download": True, "playlistend": 1}


def _primeiro_video(endereco: str) -> str | None:
    try:
        import yt_dlp

        with yt_dlp.YoutubeDL(_OPCOES) as ydl:
            info = ydl.extract_info(endereco, download=False)
        entradas = [e for e in (info.get("entries") or []) if e]
        if entradas:
            return f"https://www.youtube.com/watch?v={entradas[0]['id']}"
    except Exception as erro:  # sem internet, canal errado, YouTube mudou etc.
        log.warning("Falha ao consultar o YouTube (%s): %s", endereco, erro)
    return None


def url_canal(arroba: str) -> str:
    """'@manualdomundo', 'manualdomundo' ou um link completo -> link do canal."""
    arroba = arroba.strip().rstrip("/")
    if arroba.startswith("http"):
        return arroba
    return f"https://www.youtube.com/{arroba if arroba.startswith('@') else '@' + arroba}"


def ultimo_video(arroba: str) -> str | None:
    """Link do video mais recente do canal (ex.: '@manualdomundo')."""
    return _primeiro_video(url_canal(arroba) + "/videos")


def buscar_video(termo: str) -> str | None:
    """Link do primeiro resultado da busca."""
    return _primeiro_video(f"ytsearch1:{termo}")


def url_busca(termo: str, mais_recentes: bool = False) -> str:
    url = f"https://www.youtube.com/results?search_query={quote_plus(termo)}"
    return url + "&sp=CAI%253D" if mais_recentes else url


# --- Importar as inscricoes do YouTube ---------------------------------------
def importar_takeout_csv(caminho) -> dict[str, str]:
    """Arquivo 'inscricoes.csv' / 'subscriptions.csv' do Google Takeout.

    Colunas: ID do canal, URL do canal, Titulo do canal (a ordem e a mesma em qualquer idioma).
    """
    import csv

    canais = {}
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        for linha in csv.reader(f):
            if len(linha) >= 3 and linha[1].startswith("http"):
                canais[linha[2].strip()] = linha[1].strip().replace("http://", "https://")
    return canais


def importar_opml(caminho) -> dict[str, str]:
    """Arquivo OPML/XML de inscricoes (exportado por leitores de RSS ou pelo YouTube antigo)."""
    import re
    import xml.etree.ElementTree as ET

    canais = {}
    for item in ET.parse(caminho).iter("outline"):
        feed = item.get("xmlUrl") or ""
        achado = re.search(r"channel_id=([\w-]+)", feed)
        if achado:
            canais[(item.get("title") or item.get("text") or achado.group(1)).strip()] = \
                f"https://www.youtube.com/channel/{achado.group(1)}"
    return canais


def importar_do_navegador(navegador: str = "firefox") -> dict[str, str]:
    """Le as inscricoes usando o login do navegador (funciona bem no Firefox;
    o Chrome e o Edge bloqueiam desde 2024 - use o Google Takeout)."""
    import yt_dlp

    opcoes = dict(_OPCOES, playlistend=None, cookiesfrombrowser=(navegador,))
    with yt_dlp.YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info("https://www.youtube.com/feed/channels", download=False)
    canais = {}
    for e in info.get("entries") or []:
        if e and (e.get("title") or e.get("channel")):
            url = e.get("url") or e.get("channel_url") or ""
            if url:
                canais[(e.get("title") or e.get("channel")).strip()] = url
    return canais
