"""Chaves e senhas (Azure, Telegram) FORA da pasta do projeto.

Ficam em %APPDATA%\\Mestre\\segredos.json (no Linux: ~/.config/Mestre). Assim nunca vao
parar num .zip, no GitHub nem numa conversa. O painel le e grava por aqui.
"""
import json
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)


def arquivo() -> Path:
    base = os.environ.get("MESTRE_SEGREDOS") or os.environ.get("APPDATA") or str(Path.home() / ".config")
    return Path(base) / "Mestre" / "segredos.json"


def _todos() -> dict:
    try:
        return json.loads(arquivo().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def ler(chave: str, padrao: str = "") -> str:
    return str(_todos().get(chave) or padrao)


def salvar(**valores) -> None:
    dados = _todos()
    dados.update({k: str(v).strip() for k, v in valores.items()})
    destino = arquivo()
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
