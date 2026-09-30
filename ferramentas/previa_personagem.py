"""Prévia do personagem em PNG (sem abrir janela): serve para conferir o desenho e para o painel mostrar a miniatura.

    venv\\Scripts\\python -m ferramentas.previa_personagem --saida previa.png
    venv\\Scripts\\python -m ferramentas.previa_personagem --perfil "{\\"genero\\": \\"f\\", \\"traje\\": \\"batman\\"}" --saida f.png
    venv\\Scripts\\python -m ferramentas.previa_personagem --folha trajes --saida folha_trajes.png
"""
import argparse
import json
import math
import sys
from pathlib import Path

from PySide6.QtCore import QRectF, Qt  # noqa: E402
from PySide6.QtGui import QColor, QFont, QGuiApplication, QImage, QPainter  # noqa: E402

from app.personagem import catalogo as cat  # noqa: E402
from app.personagem.cena import montar  # noqa: E402
from app.personagem.render_qt import ALTURA_BASE, Desenhista  # noqa: E402


def desenhar_em(p: QPainter, perfil: dict, pose: dict | None, x: float, y_pes: float, altura: float) -> None:
    esc = altura / ALTURA_BASE
    p.save()
    p.translate(x, y_pes)
    p.scale(esc, esc)
    Desenhista(montar(perfil)).desenhar(p, pose or {})
    p.restore()


def imagem(perfis: list, colunas: int = 1, altura: int = 300, rotulos: list | None = None, pose: dict | None = None,
           fundo: str = "#EEE7F4") -> QImage:
    larg_cel, alt_cel = int(altura * 0.85), int(altura * 1.18)
    linhas = (len(perfis) + colunas - 1) // colunas
    img = QImage(larg_cel * colunas, alt_cel * linhas, QImage.Format_ARGB32_Premultiplied)
    img.fill(QColor(fundo))
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    for i, perfil in enumerate(perfis):
        cx, cy = (i % colunas) * larg_cel + larg_cel / 2, (i // colunas) * alt_cel
        desenhar_em(p, perfil, pose, cx, cy + alt_cel - 30, altura * 0.93)
        if rotulos:
            p.setPen(QColor("#40304A"))
            f = QFont("Segoe UI")
            f.setPixelSize(max(11, altura // 18))
            p.setFont(f)
            p.drawText(QRectF(cx - larg_cel / 2, cy + alt_cel - 24, larg_cel, 22), Qt.AlignCenter, rotulos[i])
    p.end()
    return img


def imagem_poses(quadros: list, colunas: int, altura: int, rotulos: list) -> QImage:
    larg_cel, alt_cel = int(altura * 0.95), int(altura * 1.18)
    linhas = (len(quadros) + colunas - 1) // colunas
    img = QImage(larg_cel * colunas, alt_cel * linhas, QImage.Format_ARGB32_Premultiplied)
    img.fill(QColor("#EEE7F4"))
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    for i, (perfil, pose) in enumerate(quadros):
        cx, cy = (i % colunas) * larg_cel + larg_cel / 2, (i // colunas) * alt_cel
        desenhar_em(p, perfil, pose, cx, cy + alt_cel - 30, altura * 0.93)
        p.setPen(QColor("#40304A"))
        f = QFont("Segoe UI")
        f.setPixelSize(max(11, altura // 18))
        p.setFont(f)
        p.drawText(QRectF(cx - larg_cel / 2, cy + alt_cel - 24, larg_cel, 22), Qt.AlignCenter, rotulos[i])
    p.end()
    return img


def quadros_de(perfil: dict, alvo: str, arq: str, n: int, nivel: float = 0.0) -> tuple[list, list]:
    """Poses de uma animação (estado ou gesto) em n instantes: [(perfil, pose)], [rótulo]."""
    from app.personagem import catalogo_animacao as A
    from app.personagem.animacao import Animador
    an = Animador(arq, None, 7)
    if alvo in A.CLIPES and not A.CLIPES[alvo]["loop"]:
        estado, dur = "idle", A.CLIPES[alvo]["dur"] / max(0.3, A.ARQUETIPOS[arq]["vel"])
    else:
        estado, dur = alvo, 3.0
    an.mudar(estado, 0.0)
    an.quadro(0.0)
    if estado == "idle" and alvo in A.CLIPES:
        an.gesto(alvo, 0.5)
    t, saida, rot = 0.0, [], []
    marcos = [0.5 + dur * i / max(1, n - 1) for i in range(n)] if estado == "idle" and alvo in A.CLIPES else [1.0 + dur * i / n for i in range(n)]
    dt, fim = 1 / 60, marcos[-1]
    while t < fim + 1e-6:
        if estado == "falando":
            an.nivel(0.55 + 0.4 * math.sin(t * 9), t)
        q = an.quadro(t)
        if marcos and t + 1e-6 >= marcos[0]:
            saida.append((perfil, dict(q["pose"]))), rot.append(f"{alvo} {t - (0.5 if estado == 'idle' and alvo in A.CLIPES else 1.0):.2f}s")
            marcos.pop(0)
        t += dt
    return saida, rot


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--perfil", default="{}", help="JSON do perfil (o que faltar vem do padrão)")
    ap.add_argument("--folha", choices=["trajes", "cabelos", "roupas", "acessorios", "tudo"], default="")
    ap.add_argument("--genero", default="", help="m ou f (na folha, os dois se vazio)")
    ap.add_argument("--altura", type=int, default=300)
    ap.add_argument("--colunas", type=int, default=6)
    ap.add_argument("--animar", default="", help="estado (idle/ouvindo/pensando/falando/descansando) ou gesto (acenar...)")
    ap.add_argument("--arq", default="parceiro", help="jeito: parceiro|mordomo|jarvis|coach|serio")
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--saida", default="previa_personagem.png")
    a = ap.parse_args()
    QGuiApplication(sys.argv[:1])
    base = json.loads(a.perfil)
    perfis, rotulos = [], []
    if a.animar:
        quadros, rotulos = quadros_de(base, a.animar, a.arq, a.frames)
        larg = max(1, min(len(quadros), a.colunas))
        img = imagem_poses(quadros, larg, a.altura, rotulos)
        Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
        img.save(a.saida)
        print(f"salvo: {a.saida} ({len(quadros)} quadros)")
        return 0
    if not a.folha:
        perfis, rotulos = [base], None
    else:
        generos = [a.genero] if a.genero else ["m", "f"]
        fonte = {"trajes": ("traje", cat.TRAJES), "cabelos": ("cabelo", cat.CABELOS), "roupas": ("roupa", cat.ROUPAS)}
        for g in generos:
            if a.folha == "acessorios":
                for id_, ac in cat.ACESSORIOS.items():
                    perfis.append(dict(base, genero=g, acessorios=[id_]))
                    rotulos.append(ac["nome"])
                continue
            campo, tabela = fonte.get(a.folha, ("traje", cat.TRAJES))
            for id_, item in tabela.items():
                extra = {}
                if campo == "roupa" and item.get("cores"):   # cores sugeridas da roupa (o painel faz o mesmo)
                    extra = dict(zip(("roupa_cor1", "roupa_cor2", "roupa_cor3"), item["cores"]))
                perfis.append(dict(base, genero=g, **{campo: id_}, **extra))
                rotulos.append(item["nome"])
    img = imagem(perfis, colunas=1 if not a.folha else a.colunas, altura=a.altura, rotulos=rotulos)
    Path(a.saida).parent.mkdir(parents=True, exist_ok=True)
    img.save(a.saida)
    print(f"salvo: {a.saida} ({img.width()}x{img.height()}, {len(perfis)} personagem(ns))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
