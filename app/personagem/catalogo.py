"""Catálogo do personagem: junta as peças desenhadas nos módulos catalogo_*.py.

`CATALOGO` (dict só com dados JSON) é o que a página de teste recebe; o app usa os mesmos objetos aqui.
Para acrescentar cabelo, roupa, fantasia ou acessório: mexa no módulo do assunto e rode
`venv\\Scripts\\python -m ferramentas.gerar_demo_personagem` (o teste automático confere se o demo está em dia).
"""
from . import catalogo_corpo as _c
from .catalogo_acessorios import ACESSORIOS
from .catalogo_cabelos import CABELOS
from .catalogo_roupas import ROUPAS
from .catalogo_trajes import TRAJES, _monta
from .catalogo_trajes_dc import DC
from .catalogo_trajes_mais import CLASSICAS, DC2, MARVEL2

TRAJES.update(_monta(MARVEL2, "Marvel"))
TRAJES.update(_monta(DC, "DC"))
TRAJES.update(_monta(DC2, "DC"))
TRAJES.update(_monta(CLASSICAS, "Clássicas"))
UNIVERSOS = ["Marvel", "DC", "Clássicas"]   # a ordem dos grupos no painel e na página
for _id, _expr in (("hulk", "bravo"), ("batman", "bravo"), ("venom", "bravo")):   # cara de parado da fantasia
    TRAJES[_id]["expressao"] = _expr

PELES, CORES_CABELO, CORES_OLHOS, CORES_ROUPA = _c.PELES, _c.CORES_CABELO, _c.CORES_OLHOS, _c.CORES_ROUPA
PALETA_FIXA, RIG = _c.PALETA_FIXA, _c.RIG
SOMBRA = _c.sombra()
CORPO = {g: _c.slots_corpo(g) for g in ("m", "f")}
OLHOS = {g: _c.olhos(g) for g in ("m", "f")}


def _rosto(g: str) -> dict:
    """Opções do rosto (chave do perfil -> valor -> nome + slots que troca)."""
    def op(tabela, slot):
        return {k: {"nome": nome, "slots": {slot: prims}} for k, (nome, prims) in tabela.items()}
    return {"rosto": {k: {"nome": nome, "slots": {"cabeca": _c.cabeca(d)}} for k, (nome, d) in _c.FORMATOS.items()},
            "bochechas": op(_c.BOCHECHAS, "bochecha"), "nariz": op(_c.NARIZES, "nariz"),
            "sobrancelha": op(_c.SOBRANCELHAS, "sobr"),
            "olhos_estilo": {k: {"nome": nome, "slots": OLHOS[g][k]} for k, nome in _c.OLHOS_ESCOLHA.items()}}


ROSTO = {g: _rosto(g) for g in ("m", "f")}
ROSTO_ORDEM, ROSTO_ROTULOS = _c.ROSTO_ORDEM, _c.ROSTO_ROTULOS


def _nomes(d: dict) -> list:
    return [[k, v["nome"]] for k, v in d.items()]


def como_dados() -> dict:
    """Tudo em dicionário JSON-ável (entra no demo HTML e no teste de paridade)."""
    return {
        "peles": PELES, "cores_cabelo": CORES_CABELO, "cores_olhos": CORES_OLHOS, "cores_roupa": CORES_ROUPA,
        "paleta_fixa": PALETA_FIXA, "rig": RIG, "sombra": SOMBRA, "corpo": CORPO, "olhos": OLHOS,
        "cabelos": CABELOS, "roupas": ROUPAS, "trajes": TRAJES, "acessorios": ACESSORIOS,
        "rosto": ROSTO, "rosto_ordem": ROSTO_ORDEM, "rosto_rotulos": ROSTO_ROTULOS, "universos": UNIVERSOS,
    }
