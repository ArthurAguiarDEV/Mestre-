"""PNG do personagem (fundo transparente) para o painel mostrar a prévia. Roda num processo à parte, sem abrir janela.

    python -m app.personagem.previa --perfil "{...json...}" --saida previa.png [--altura 300]
"""
import argparse
import json
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter

from .cena import montar
from .render_qt import ALTURA_BASE, Desenhista


def gerar(perfil: dict, saida: str, altura: int = 300, pose: dict | None = None) -> None:
    larg, alt = int(altura * 0.95), int(altura * 1.06)
    img = QImage(larg, alt, QImage.Format_ARGB32_Premultiplied)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.translate(larg / 2, alt - altura * 0.04)
    esc = altura / ALTURA_BASE
    p.scale(esc, esc)
    Desenhista(montar(perfil)).desenhar(p, pose or {"boca.v": "sorriso"})
    p.end()
    if not img.save(saida):
        raise OSError("não consegui gravar " + saida)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--perfil", default="{}")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--altura", type=int, default=300)
    a = ap.parse_args()
    try:
        gerar(json.loads(a.perfil), a.saida, a.altura)
    except (ValueError, OSError) as erro:
        print(erro, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
