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


def o_que_esta_tocando(executor) -> str:
    """Spotify (pelo título da janela), abas do YouTube (título, tocando/pausado, monitor) e a
    janela ativa de cada monitor. Usado pelo comando de voz "o que tá tocando" e pelo Telegram."""
    from . import sistema

    partes = []
    spotify = next((j for j in sistema.janelas_abertas()
                    if j["exe"] == "spotify.exe" and j["titulo"].strip().lower() != "spotify"), None)
    partes.append(f"No Spotify: {spotify['titulo']}." if spotify else "O Spotify não está tocando nada agora.")

    try:
        abas = executor._abas_abertas()
    except Exception:
        abas = []
    youtube = [a for a in abas if "youtube.com/watch" in (a.get("url") or "")]
    if youtube:
        descricoes = []
        for a in youtube:
            situacao = "tocando" if a.get("audivel") else ("pausado" if a.get("video_pausado") else "parado")
            monitor = None
            try:
                monitor = executor._monitor_da_aba(a, abas)
            except Exception:
                pass
            onde = f", monitor {monitor}" if monitor else ""
            descricoes.append(f"{a.get('titulo') or 'um vídeo'} ({situacao}{onde})")
        partes.append("No YouTube: " + "; ".join(descricoes) + ".")

    ativas = sistema.janela_ativa_por_monitor()
    if ativas:
        partes.append("Nas telas: " + "; ".join(f"monitor {n}: {t}" for n, t in sorted(ativas.items())) + ".")
    return " ".join(partes)


def pesquisar_web(termo: str, quantidade: int = 5) -> list[dict]:
    """Artigos na internet sobre o termo (busca do Google Noticias em RSS, gratis e sem cadastro):
    [{"titulo", "link", "resumo"}]. (Buscas "normais" gratis bloqueiam robos ou trazem resultados errados.)"""
    try:
        r = requests.get("https://news.google.com/rss/search", headers=CABECALHO, timeout=12,
                         params={"q": termo, "hl": "pt-BR", "gl": "BR", "ceid": "BR:pt-419"})
        r.raise_for_status()
        saida = []
        for i in list(ET.fromstring(r.content).iter("item"))[:quantidade]:
            titulo = i.findtext("title") or ""
            fonte = re.search(r"\s+-\s+([^-]+)$", titulo)
            saida.append({"titulo": re.sub(r"\s+-\s+[^-]+$", "", titulo).strip(), "link": (i.findtext("link") or "").strip(),
                          "resumo": fonte.group(1).strip() if fonte else ""})
        return [x for x in saida if x["titulo"]]
    except Exception as erro:
        log.warning("Pesquisa na internet indisponivel: %s", erro)
        return []
