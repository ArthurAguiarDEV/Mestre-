"""Central do Mestre: e o que o atalho "Mestre" da area de trabalho abre.

1. Liga o Mestre (se estiver marcado no painel e ele ainda nao estiver ligado).
2. Abre o painel (ou traz para frente o que ja estiver aberto).

    pythonw -m app.central              (normal)
    pythonw -m app.central --sem-ligar  (so o painel)
"""
import sys

from . import sistema
from .iniciar_painel import avisar_painel_aberto
from .iniciar_painel import main as abrir_painel


def _ligar_ao_abrir() -> bool:
    try:
        import yaml

        from .config import ARQUIVO_CONFIG

        cfg = yaml.safe_load(ARQUIVO_CONFIG.read_text(encoding="utf-8")) or {}
        return bool((cfg.get("central") or {}).get("ligar_mestre_ao_abrir", True))
    except Exception:
        return True   # config com erro: o painel mostra o problema; ligar nao atrapalha


def main() -> None:
    if "--sem-ligar" not in sys.argv and _ligar_ao_abrir() and not sistema.mestre_ligado():
        sistema.iniciar_mestre()
    if avisar_painel_aberto():
        return
    abrir_painel()


if __name__ == "__main__":
    main()
