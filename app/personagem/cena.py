"""Monta a CENA do personagem (árvore de nós com primitivas de cores já resolvidas) a partir do perfil.

Sem Qt: o teste automático confere sem abrir janela. O desenhista do app (render_qt.py) e o da página de teste
(personagem.js, que repete estas mesmas poucas linhas) só percorrem a árvore e pintam.
"""
import copy
import re

from . import catalogo as cat
from .arte import resolver_prim

PERFIL_PADRAO = {
    "genero": "m", "pele": "morena_clara", "cabelo": "curto", "cabelo_cor": "castanho_escuro",
    "olhos_cor": "castanho", "roupa": "camiseta", "roupa_cor1": "azul", "roupa_cor2": "branco",
    "roupa_cor3": "marinho", "traje": "", "acessorios": [], "escala": 1.0,
    "rosto": "redondo", "olhos_estilo": "normal", "sobrancelha": "normal", "nariz": "botao", "bochechas": "rosadas",
}
_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _cor(valor, tabela, padrao: str) -> str:
    """id da paleta OU #RRGGBB -> #RRGGBB (valor inválido cai no padrão)."""
    if isinstance(valor, str):
        if _HEX.match(valor):
            return valor.upper()
        for id_, _nome, hexa in tabela:
            if id_ == valor:
                return hexa
    return next(h for i, _n, h in tabela if i == padrao)


def normalizar(perfil: dict | None) -> dict:
    """Perfil vindo do config (pode ser antigo, incompleto ou ter lixo): devolve um perfil válido e completo."""
    p = dict(PERFIL_PADRAO)
    for k, v in (perfil or {}).items():
        if k in p:
            p[k] = v
    p["genero"] = "f" if str(p["genero"]).lower().startswith("f") else "m"
    if p["cabelo"] not in cat.CABELOS:
        p["cabelo"] = PERFIL_PADRAO["cabelo"] if p["genero"] == "m" else "longo"
    if p["roupa"] not in cat.ROUPAS:
        p["roupa"] = PERFIL_PADRAO["roupa"]
    p["traje"] = p["traje"] if p["traje"] in cat.TRAJES else ""
    for opc in cat.ROSTO_ORDEM:
        if not isinstance(p[opc], str) or p[opc] not in cat.ROSTO["m"][opc]:
            p[opc] = PERFIL_PADRAO[opc]
    acs = p["acessorios"] if isinstance(p["acessorios"], (list, tuple)) else []
    p["acessorios"] = [a for i, a in enumerate(acs) if a in cat.ACESSORIOS and a not in acs[:i]]
    try:
        p["escala"] = max(0.6, min(1.6, float(p["escala"])))
    except (TypeError, ValueError):
        p["escala"] = 1.0
    return p


def paleta(p: dict, traje: dict | None) -> dict:
    """Todas as fichas de cor usadas nas primitivas, já em #RRGGBB."""
    pal = dict(cat.PALETA_FIXA)
    pal["pele"] = _cor(p["pele"], cat.PELES, "morena_clara")
    pal["cabelo"] = _cor(p["cabelo_cor"], cat.CORES_CABELO, "castanho_escuro")
    pal["olhos"] = _cor(p["olhos_cor"], cat.CORES_OLHOS, "castanho")
    pal["r1"] = _cor(p["roupa_cor1"], cat.CORES_ROUPA, "azul")
    pal["r2"] = _cor(p["roupa_cor2"], cat.CORES_ROUPA, "branco")
    pal["r3"] = _cor(p["roupa_cor3"], cat.CORES_ROUPA, "marinho")
    if traje:
        pal.update(traje.get("cores", {}))
    return pal


def _no(molde: dict, slots: dict, pal: dict, genero: str) -> dict:
    no = {"id": molde["id"], "pos": list(molde.get("pos_f") if genero == "f" and molde.get("pos_f") else molde["pos"])}
    for k in ("z", "seg", "mir", "inv", "contorno"):
        if molde.get(k):
            no[k] = molde[k]
    ss = molde.get("slot", [])
    prims = [x for s in ([ss] if isinstance(ss, str) else ss) for x in slots.get(s, [])]
    no["prims"] = [resolver_prim(x, pal) for x in prims]
    no["filhos"] = [_no(f, slots, pal, genero) for f in molde.get("filhos", [])]
    return no


def montar(perfil: dict | None) -> dict:
    """Perfil -> {"perfil", "sombra": [...], "raiz": nó}. Sempre válido (o perfil passa por `normalizar`)."""
    p = normalizar(perfil)
    g = p["genero"]
    traje = cat.TRAJES.get(p["traje"]) if p["traje"] else None
    pal = paleta(p, traje)
    slots = copy.deepcopy(cat.CORPO[g])
    olhos_traje = (traje or {}).get("olhos", "normal")
    for opc in cat.ROSTO_ORDEM:   # rosto escolhido (com fantasia: cabeça redonda, e olho da máscara se ela tiver)
        val = "redondo" if traje and opc == "rosto" else p[opc]
        if opc == "olhos_estilo" and olhos_traje != "normal":
            val = None
        for slot, prims in (cat.ROSTO[g][opc][val]["slots"].items() if val else ()):
            slots[slot] = copy.deepcopy(prims)
    if olhos_traje != "normal":
        for slot, prims in cat.OLHOS[g][olhos_traje].items():
            slots[slot] = copy.deepcopy(prims)
    pecas = traje["pecas"][g] if traje else cat.ROUPAS[p["roupa"]]["pecas"][g]
    for slot, prims in pecas.items():
        slots.setdefault(slot, []).extend(copy.deepcopy(prims))
    esconde = set((traje or {}).get("esconde", []))
    balanco = 0.0
    if "cabelo" not in esconde:
        cab = cat.CABELOS[(traje or {}).get("forca_cabelo") or p["cabelo"]]
        slots["cabelo_tras"] = copy.deepcopy(cab.get("tras", []))
        slots["cabelo_frente"] = copy.deepcopy(cab.get("frente", []))
        balanco = cab.get("balanco", 0.3)
    for id_ in p["acessorios"]:
        for slot, prims in cat.ACESSORIOS[id_]["pecas"].items():
            if slot in esconde or (slot in ("acessorio", "mascara_cima", "mascara_baixo") and "acessorio" in esconde):
                continue
            slots.setdefault(slot, []).extend(copy.deepcopy(prims))
    for s in esconde:
        if s in ("sobr", "boca"):
            slots[s] = []
    return {"perfil": p, "sombra": [resolver_prim(x, pal) for x in cat.SOMBRA], "balanco": balanco,
            "raiz": _no(cat.RIG, slots, pal, g)}


def nos(cena_ou_no: dict):
    """Percorre todos os nós da cena (na ordem do desenho de cima para baixo)."""
    no = cena_ou_no.get("raiz", cena_ou_no)
    yield no
    for f in no["filhos"]:
        yield from nos(f)
