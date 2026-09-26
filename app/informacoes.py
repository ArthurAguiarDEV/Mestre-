"""Clima e noticias, gratis e sem cadastro.

- Clima: wttr.in (servico publico e gratuito)
- Noticias: manchetes do Google Noticias em portugues (RSS)
"""
import logging
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote

import requests

log = logging.getLogger(__name__)
CABECALHO = {"User-Agent": "Mestre-assistente/3.0"}


def clima(cidade: str) -> str:
    try:
        r = requests.get(f"https://wttr.in/{quote(cidade)}?format=j1&lang=pt", headers=CABECALHO, timeout=10)
        r.raise_for_status()
        dados = r.json()
        agora = dados["current_condition"][0]
        descricao = (agora.get("lang_pt") or agora.get("weatherDesc") or [{"value": ""}])[0]["value"].lower()
        hoje = dados["weather"][0]
        chuva = max(int(h.get("chanceofrain", 0)) for h in hoje.get("hourly", [{"chanceofrain": 0}]))
        frase = (f"Em {cidade} agora faz {agora['temp_C']} graus, {descricao}. "
                 f"Hoje a mínima é {hoje['mintempC']} e a máxima {hoje['maxtempC']}.")
        if chuva >= 50:
            frase += f" Chance de chuva de {chuva} por cento, leva o guarda-chuva!"
        return frase
    except Exception as erro:
        log.warning("Clima indisponivel: %s", erro)
        return "Não consegui ver o clima agora."


def noticias(quantidade: int = 3, assunto: str = "") -> list[str]:
    url = ("https://news.google.com/rss/search?q=" + quote(assunto) if assunto
           else "https://news.google.com/rss") + "&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    url = url.replace("rss&", "rss?", 1)
    try:
        r = requests.get(url, headers=CABECALHO, timeout=10)
        r.raise_for_status()
        titulos = [i.findtext("title") or "" for i in ET.fromstring(r.content).iter("item")]
        # "Titulo da noticia - Nome do jornal" -> "Titulo da noticia"
        return [re.sub(r"\s+-\s+[^-]+$", "", t).strip() for t in titulos[:quantidade] if t]
    except Exception as erro:
        log.warning("Noticias indisponiveis: %s", erro)
        return []
