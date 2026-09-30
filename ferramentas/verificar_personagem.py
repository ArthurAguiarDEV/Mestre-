"""Confere o personagem "de verdade" (Qt e navegador). Não roda dentro da barreira dos testes seguros: rode no Windows.

    venv\\Scripts\\python -m ferramentas.verificar_personagem            # tudo
    venv\\Scripts\\python -m ferramentas.verificar_personagem --sem-navegador

1. Desenho (Qt, sem janela): as fantasias x 2 corpos, os cabelos, as roupas, os acessórios e o rosto desenham (nada some, nada fica preto).
2. Janela (Qt offscreen): a janela do personagem abre e desenha em todos os estados e jeitos, sem erro.
3. Navegador (Edge, sem tela): a cena e a animação montadas em JavaScript (página de teste) são IGUAIS às do Python.
"""
import argparse
import json
import math
import os
import random
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.personagem import catalogo as cat  # noqa: E402
from app.personagem import catalogo_animacao as A  # noqa: E402
from app.personagem import cena  # noqa: E402
from app.personagem.animacao import Animador  # noqa: E402

FALHAS: list = []


def ok(cond: bool, msg: str) -> None:
    print(("  ok   " if cond else "  FALHA ") + msg)
    if not cond:
        FALHAS.append(msg)


def desenho() -> None:
    print("1) Desenho no Qt")
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QColor, QImage, QPainter
    from PySide6.QtWidgets import QApplication

    from app.personagem.render_qt import ALTURA_BASE, Desenhista
    QApplication.instance() or QApplication(sys.argv[:1])

    def imagem(perfil: dict, pose: dict | None = None) -> QImage:
        img = QImage(200, 260, QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        p.translate(100, 250)
        p.scale(240 / ALTURA_BASE, 240 / ALTURA_BASE)
        Desenhista(cena.montar(perfil)).desenhar(p, pose or {})
        p.end()
        return img

    def cobertura(perfil: dict, pose: dict | None = None) -> tuple[float, int]:
        img = imagem(perfil, pose)
        opacos = pretos = 0
        for y in range(0, 260, 2):
            for x in range(0, 200, 2):
                c = QColor(img.pixel(x, y))
                if img.pixelColor(x, y).alpha() > 200:
                    opacos += 1
                    pretos += c.red() + c.green() + c.blue() < 24
        return opacos / (100 * 130), pretos

    piores = []
    for g in "mf":
        for tid in [""] + list(cat.TRAJES):
            cob, pretos = cobertura({"genero": g, "traje": tid})
            piores.append((cob, g, tid, pretos))
            if not (0.10 < cob < 0.85):
                ok(False, f"{g}/{tid or 'roupa'}: cobertura estranha {cob:.2f}")
    ok(not [1 for c, *_ in piores if not 0.10 < c < 0.85], f"{len(piores)} visuais (2 corpos x fantasias) desenham com cobertura normal")
    ok(all(pretos < 250 for *_x, pretos in piores), "nenhum visual tem mancha preta grande (cor inválida)")
    for cab in cat.CABELOS:
        for g in "mf":
            cob, _ = cobertura({"genero": g, "cabelo": cab})
            if not 0.12 < cob < 0.9:
                ok(False, f"cabelo {cab}/{g}: cobertura {cob:.2f}")
    ok(True, f"{len(cat.CABELOS)} cabelos x 2 corpos desenham")
    for rou in cat.ROUPAS:
        cobertura({"roupa": rou})
    for ac in cat.ACESSORIOS:
        cobertura({"acessorios": [ac]})
    ok(True, f"{len(cat.ROUPAS)} roupas e {len(cat.ACESSORIOS)} acessórios desenham")
    base = imagem({}, {})
    diferentes = [f"{o}={v}" for o in cat.ROSTO_ORDEM for v in cat.ROSTO["m"][o]
                  if v != cena.PERFIL_PADRAO[o] and imagem({o: v}, {}) == base]
    ok(not diferentes, f"cada opção de rosto muda o desenho ({sum(len(cat.ROSTO['m'][o]) for o in cat.ROSTO_ORDEM)} opções)"
       + (": iguais ao padrão " + ", ".join(diferentes) if diferentes else ""))
    a, b = imagem({"traje": "batman"}, {"boca.v": "A"}), imagem({"traje": "batman"}, {"boca.v": "fechada"})
    ok(a != b, "a forma da boca muda o desenho")
    c, d = imagem({}, {"olhos.feliz": 1, "olhos.oculto": 1}), imagem({}, {})
    ok(c != d, "olho feliz/fechado muda o desenho")


def janela() -> None:
    """Uma janela por processo (como no uso real): cada estado do Assessor num Python novo."""
    print("2) Janela do personagem (Qt offscreen)")
    import subprocess
    bons = []
    for estado in ("iniciando", "conversa", "pensando", "falando", "descansando"):
        r = subprocess.run([sys.executable, "-m", "ferramentas.verificar_personagem", "--janela-um", estado], cwd=str(RAIZ),
                           capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and "DESENHOU" in r.stdout:
            bons.append(estado)
        else:
            print("   ", estado, "->", (r.stdout + r.stderr).strip()[-300:])
    ok(len(bons) == 5, "abre, anima, muda de jeito/fantasia/passeio e desenha em todos os estados: " + ", ".join(bons))


def janela_um(estado: str) -> int:
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from app import estado as est
    est.pausado = lambda: False
    from app.personagem import janela as jan
    app = QApplication(sys.argv[:1])
    arq = Path(tempfile.gettempdir()) / f"estado_verificar_personagem_{estado}.json"
    arq.write_text(json.dumps({"nome": estado, "pid": 0}), encoding="utf-8")
    j = jan.Personagem(argparse.Namespace(pai=0, nome="Assessor", palavra="assessor", estado=str(arq), tipo="texto_avatar"))
    rnd = random.Random(5)
    for jeito in A.ARQUETIPOS:
        j.aplicar_opcoes(dict(j.op, arquetipo=jeito, perfil=cena.normalizar({"traje": rnd.choice(list(cat.TRAJES)), "genero": rnd.choice("mf"), "escala": 1.2})))
    j.aplicar_opcoes(dict(j.op, passeio="tela"))
    fim = {}
    QTimer.singleShot(1200, lambda: (fim.update(pm=j.grab(), q=j._p), app.quit()))
    app.exec()
    pm = fim.get("pm")
    j.fechar()
    if pm is not None and pm.width() == j.largura and fim.get("q") is not None:
        print("DESENHOU", estado)
        return 0
    print("NAO DESENHOU", estado)
    return 1


def _igual(a, b) -> bool:
    """Igualdade profunda: números por valor (1 e 1.0 são o mesmo), o resto exato."""
    if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None:
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_igual(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_igual(x, y) for x, y in zip(a, b))
    return a == b


def navegador() -> None:
    print("3) Navegador: cena e animação do JavaScript = Python")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  (playwright não instalado: pulei)")
        return
    from ferramentas import gerar_demo_personagem as g
    frag, completo = g.montar()
    arquivo = Path(tempfile.gettempdir()) / "personagem_verificar.html"
    arquivo.write_text(completo, encoding="utf-8")
    rnd = random.Random(2026)
    perfis = []
    for i in range(80):
        perfis.append({"genero": rnd.choice("mf"), "pele": rnd.choice(cat.PELES)[0], "cabelo": rnd.choice(list(cat.CABELOS)),
                       "cabelo_cor": rnd.choice(cat.CORES_CABELO)[0], "olhos_cor": rnd.choice(cat.CORES_OLHOS)[0], "roupa": rnd.choice(list(cat.ROUPAS)),
                       "roupa_cor1": rnd.choice(cat.CORES_ROUPA)[0], "roupa_cor2": rnd.choice(cat.CORES_ROUPA)[0], "roupa_cor3": rnd.choice(cat.CORES_ROUPA)[0],
                       "traje": rnd.choice([""] + list(cat.TRAJES)), "acessorios": rnd.sample(list(cat.ACESSORIOS), rnd.randint(0, 3)), "escala": rnd.choice([0.6, 1, 1.3]),
                       **{opc: rnd.choice(list(cat.ROSTO["m"][opc])) for opc in cat.ROSTO_ORDEM}})
    perfis += [{"genero": g_, "traje": t} for g_ in "mf" for t in cat.TRAJES]
    js_cena = """(perfis) => perfis.map(p => window.__personagem.montar(p))"""
    js_anim = """(cen) => {
      const P = window.Personagem, A = window.__personagem.A, saida = [];
      for (const c of cen) {
        const an = new P.Animador(A, c.arq, c.expr || null, c.seed); const poses = [];
        for (const ev of c.eventos) {
          const [t, tipo, a, b] = ev;
          if (tipo === 'mudar') an.mudar(a, t); else if (tipo === 'nivel') an.nivel(a, t); else if (tipo === 'texto') an.texto(a);
          else if (tipo === 'gesto') an.gesto(a, t); else if (tipo === 'andar') an.andar(a, b); else if (tipo === 'olhar') an.olhar(a, b);
          else if (tipo === 'balanco') an.balanco = a;
          else if (tipo === 'q') { const q = an.quadro(t); poses.push([q.pose, q.extras, q.gesto]); }
        }
        saida.push(poses);
      }
      return saida;
    }"""

    def cenarios():
        cs = []
        for arq in A.ARQUETIPOS:
            ev = [(0.0, "mudar", "idle", None)]
            for i in range(int(25 * 30)):
                t = i / 30
                if i == 60:
                    ev.append((t, "olhar", 0.6, -0.3))
                ev.append((t, "q", None, None))
            cs.append({"arq": arq, "seed": 7, "eventos": ev})
            ev = [(0.0, "mudar", "idle", None), (0.0, "q", None, None), (1.0, "mudar", "falando", None), (1.0, "texto", "Beleza, deixa comigo agora mesmo", None)]
            for i in range(30, 30 * 8):
                t = i / 30
                ev.append((t, "nivel", round(0.5 + 0.5 * math.sin(t * 9), 6), None))
                ev.append((t, "q", None, None))
            for est, t0 in (("pensando", 8.0), ("ouvindo", 11.0), ("descansando", 13.0), ("idle", 16.0)):
                ev.append((t0, "mudar", est, None))
                for i in range(90):
                    ev.append((t0 + i / 30, "q", None, None))
            ev.append((19.0, "balanco", 0.4, None))
            ev.append((19.0, "andar", 1, 1.2))
            for i in range(90):
                ev.append((19 + i / 30, "q", None, None))
            ev.append((22.0, "gesto", "acenar", None))
            for i in range(90):
                ev.append((22 + i / 30, "q", None, None))
            cs.append({"arq": arq, "seed": 99, "expr": "bravo" if arq == "coach" else None, "eventos": ev})
        return cs

    def py_anim(c):
        an = Animador(c["arq"], c.get("expr"), c["seed"])
        poses = []
        for t, tipo, a, b in c["eventos"]:
            if tipo == "mudar":
                an.mudar(a, t)
            elif tipo == "nivel":
                an.nivel(a, t)
            elif tipo == "texto":
                an.texto(a)
            elif tipo == "gesto":
                an.gesto(a, t)
            elif tipo == "andar":
                an.andar(a, b)
            elif tipo == "olhar":
                an.olhar(a, b)
            elif tipo == "balanco":
                an.balanco = a
            else:
                q = an.quadro(t)
                poses.append((q["pose"], q["extras"], q["gesto"]))
        return poses

    try:
        with sync_playwright() as pw:
            try:
                nav = pw.chromium.launch(channel="msedge", headless=True)
            except Exception:
                nav = pw.chromium.launch(headless=True)
            pagina = nav.new_page()
            erros = []
            pagina.on("pageerror", lambda e: erros.append(str(e)))
            pagina.goto(arquivo.as_uri())
            pagina.wait_for_function("window.__personagem !== undefined", timeout=15000)
            cenas_js = pagina.evaluate(js_cena, perfis)
            iguais = sum(_igual(c, cena.montar(p)) for c, p in zip(cenas_js, perfis))
            ok(iguais == len(perfis), f"cena montada em JS = Python ({iguais}/{len(perfis)} perfis, inclui as {len(cat.TRAJES)} fantasias nos 2 corpos)")
            cs = cenarios()
            anim_js = pagina.evaluate(js_anim, cs)
            piores, total = 0.0, 0
            for c, js in zip(cs, anim_js):
                py = py_anim(c)
                if len(py) != len(js):
                    ok(False, f"animação {c['arq']}: número de quadros difere")
                    continue
                for (pp, pe, pg), (jp, je, jg) in zip(py, js):
                    total += 1
                    if pg != jg:
                        piores = max(piores, 999)
                    for k in set(pp) | set(jp):
                        a, b = pp.get(k), jp.get(k)
                        if isinstance(a, str) or isinstance(b, str):
                            piores = max(piores, 0 if a == b else 999)
                        elif a is None or b is None:
                            piores = max(piores, 999)
                        else:
                            piores = max(piores, abs(a - b))
                    for k in pe:
                        if k == "aura":
                            piores = max(piores, 0 if pe[k] == je[k] else 999)
                        else:
                            piores = max(piores, abs(pe[k] - je[k]))
            ok(piores < 1e-6, f"animação JS = Python em {total} quadros, {len(cs)} cenários (maior diferença {piores:.2g})")
            ok(not erros, "a página abre sem erro de JavaScript" + (": " + erros[0][:120] if erros else ""))
            # usar a página: trocar de fantasia e de jeito por dentro dela
            pagina.evaluate("document.querySelector('[data-aba=\"fantasia\"]').click()")
            n = pagina.evaluate("document.querySelectorAll('.grade-thumbs .thumb').length")
            ok(n == 1 + len(cat.TRAJES), f"aba Fantasia mostra 'sem fantasia' + {len(cat.TRAJES)} fantasias ({n})")
            pagina.evaluate("document.querySelector('[data-aba=\"rosto\"]').click()")
            n = pagina.evaluate("document.querySelectorAll('.grade-thumbs .thumb').length")
            esperado = sum(len(cat.ROSTO["m"][o]) for o in cat.ROSTO_ORDEM)
            ok(n == esperado, f"aba Rosto mostra as {esperado} opções de rosto ({n})")
            ok(not erros, "trocar de aba não dá erro de JavaScript" + (": " + erros[0][:120] if erros else ""))
            nav.close()
    except Exception as erro:
        ok(False, f"navegador não rodou: {erro}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-navegador", action="store_true")
    ap.add_argument("--janela-um", default="", help="(uso interno) abre uma janela no estado dado")
    a = ap.parse_args()
    if a.janela_um:
        return janela_um(a.janela_um)
    desenho()
    janela()
    if not a.sem_navegador:
        navegador()
    print("\n" + ("TUDO CERTO" if not FALHAS else f"{len(FALHAS)} FALHA(S): " + "; ".join(FALHAS)))
    return 1 if FALHAS else 0


if __name__ == "__main__":
    sys.exit(main())
