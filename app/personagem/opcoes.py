"""Medidas da janela e opções do personagem lidas do config.yaml (sem Qt: o teste automático confere sem abrir janela)."""
import math

from .. import avatar
from . import catalogo_animacao as A
from .animacao import arquetipo_do_estilo
from .cena import normalizar
from .passeio import MODOS

ALTURA_PADRAO_PX = 176        # altura do personagem na tela com escala 1.0 (o triplo do bonequinho pixelado do jogo)
MEIA_LARGURA = 96             # meia largura do desenho em unidades (rabo de cavalo, capa, asas cabem)
FOLGA = 18                    # borda transparente em volta
ALTURA_BALAO = 44
VAO_BALAO = 8
ALTURA_BASE = 224.0           # altura do desenho em unidades (igual a render_qt.ALTURA_BASE)


def dimensoes(escala: float, balao: bool) -> dict:
    """Tamanhos da janela em px para uma escala (função pura)."""
    alt = ALTURA_PADRAO_PX * escala
    es = alt / ALTURA_BASE
    larg_p = 2 * MEIA_LARGURA * es
    larg = max(larg_p + 2 * (FOLGA + 34), avatar.LARGURA_BALAO_MAX if balao else 0)
    altura = alt + 2 * FOLGA + 24 + ((ALTURA_BALAO + VAO_BALAO) if balao else 0)
    return {"altura_px": alt, "escala": es, "larg_personagem": larg_p, "largura": int(math.ceil(larg)), "altura": int(math.ceil(altura))}


def opcoes_do_config(cfg: dict) -> dict:
    """config.yaml -> o que o personagem precisa (tudo com valor padrão: config antigo não quebra)."""
    av = (cfg or {}).get("avatar") or {}
    perfil = normalizar(av.get("personagem"))
    estilo = str(((cfg or {}).get("personalidade") or {}).get("estilo") or "")
    jeito = str(av.get("jeito") or "").strip().lower()
    passeio = str(av.get("passeio") or "personalidade").strip().lower()
    return {"perfil": perfil, "arquetipo": arquetipo_do_estilo(estilo, jeito if jeito in A.ARQUETIPOS else None),
            "passeio": passeio if passeio in MODOS or passeio == "personalidade" else "personalidade"}


def escrever_config(c, modelo: str, jeito: str, passeio: str, perfil: dict) -> None:
    """Grava `avatar > ...` no config (ruamel: os comentários do arquivo ficam). `perfil` já normalizado."""
    from .. import configuracao
    av = configuracao.secao(c, "avatar")
    av["modelo"] = configuracao.aspas(modelo if modelo in avatar.MODELOS else "robo")
    av["jeito"] = configuracao.aspas(jeito if jeito in A.ARQUETIPOS else "")
    av["passeio"] = configuracao.aspas(passeio if passeio in MODOS or passeio == "personalidade" else "personalidade")
    pers = configuracao.secao(av, "personagem")
    for k in ("genero", "pele", "cabelo", "cabelo_cor", "olhos_cor", "roupa", "roupa_cor1", "roupa_cor2", "roupa_cor3", "traje",
              "rosto", "olhos_estilo", "sobrancelha", "nariz", "bochechas"):
        pers[k] = configuracao.aspas(perfil[k])
    pers["acessorios"] = configuracao.lista_em_linha(list(perfil["acessorios"]))
    pers["escala"] = round(float(perfil["escala"]), 2)
