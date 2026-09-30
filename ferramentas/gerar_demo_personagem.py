"""Gera a página de teste do personagem (design/avatar-2026-09/) a partir do catálogo em Python.

    venv\\Scripts\\python -m ferramentas.gerar_demo_personagem            # escreve index.html e artefato.html
    venv\\Scripts\\python -m ferramentas.gerar_demo_personagem --verificar # só confere se estão em dia (o teste automático usa)

`index.html` = página completa para abrir com duplo clique. `artefato.html` = o mesmo conteúdo sem <html>/<head> (para publicar
como Artefato). Os dados (catálogo, clipes, falas das personalidades) são embutidos: a página não precisa de nada de fora.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from app import personalidades  # noqa: E402
from app.personagem import catalogo, catalogo_animacao as anim  # noqa: E402
from app.personagem.passeio import NOMES_MODO  # noqa: E402

PASTA = RAIZ / "design" / "avatar-2026-09"

JEITOS = {
    "parceiro": ("Parceiro brasileiro", "Solto e simpático: acena, dança, pula, assobia e passeia perto do lugar dele. Fala com as mãos.", 1.05, 1.05),
    "mordomo": ("Mordomo elegante", "Postura reta e devagar: faz reverência, ajusta a gravata e quase não sai do lugar. Fala com gestos pequenos.", 0.92, 0.85),
    "jarvis": ("Estilo Jarvis", "Flutua com um brilho azul, escaneia o ambiente e mexe em hologramas. Voa pela tela em vez de andar.", 1.0, 0.95),
    "coach": ("Coach animado", "Energia total: soco no ar, pulos, corrida parada e comemoração. Anda rápido pela tela toda.", 1.15, 1.15),
    "serio": ("Sério e direto", "Braços cruzados, olha o relógio e mexe pouco. Fica parado e fala só com a cabeça.", 1.0, 0.9),
}
GESTOS = [("acenar", "Acenar"), ("pular", "Pular"), ("dancar", "Dançar"), ("alongar", "Alongar"), ("olhar_em_volta", "Olhar em volta"),
          ("assobiar", "Assobiar"), ("reverencia", "Reverência"), ("ajustar_gravata", "Ajustar a gravata"), ("escanear", "Escanear"),
          ("holograma", "Holograma"), ("punho", "Soco no ar"), ("correr_parado", "Correr parado"), ("celebrar", "Comemorar"),
          ("cruzar_bracos", "Braços cruzados"), ("olhar_relogio", "Olhar o relógio"), ("dar_de_ombros", "Dar de ombros"),
          ("surpresa", "Susto"), ("assentir", "Sim"), ("negar", "Não"), ("bocejar", "Bocejar")]


def _falas(estilo: str) -> dict:
    troca = {"{apelido}": "Mestre", "{nome}": "Assessor", "{saudacao}": "Boa noite"}
    saida = {}
    for situacao, frases in personalidades.ESTILOS[estilo]["falas"].items():
        lista = []
        for f in frases:
            for k, v in troca.items():
                f = f.replace(k, v)
            lista.append(f)
        saida[situacao] = lista
    return saida


def dados() -> dict:
    arqs = anim.ARQUETIPOS
    estilo_de = {v: k for k, v in anim.ESTILO_PARA_ARQUETIPO.items()}
    return {
        "catalogo": catalogo.como_dados(), "animacao": anim.como_dados(),
        "falas": {a: _falas(estilo_de[a]) for a in arqs},
        "jeitos": {a: {"nome": JEITOS[a][0].split()[0] if a != "jarvis" else "Jarvis", "estilo": estilo_de[a], "descricao": JEITOS[a][1],
                       "taxa": JEITOS[a][2], "tom": JEITOS[a][3]} for a in arqs},
        "gestos": GESTOS, "modos_passeio": NOMES_MODO,
    }


def _js(nome: str) -> str:
    return (PASTA / nome).read_text(encoding="utf-8").rstrip() + "\n"


def montar() -> tuple[str, str]:
    """(artefato.html, index.html)"""
    d = json.dumps(dados(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    modelo = (PASTA / "modelo.html").read_text(encoding="utf-8")
    frag = modelo.replace("__DADOS_JSON__", d).replace("__PERSONAGEM_JS__", _js("personagem.js")).replace("__DEMO_JS__", _js("demo.js"))
    inicio = ('<!doctype html>\n<html lang="pt-BR">\n<head>\n<meta charset="utf-8">\n'
              '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
              '<style>:root{color-scheme:light}body{margin:0}[hidden]{display:none!important}img{max-width:100%}</style>\n')
    # o <title>, o <link> e o <style> do modelo vão para o <head>; o resto para o <body>
    corpo_ini = frag.index("<div class=\"pagina\">")
    return frag, inicio + frag[:corpo_ini] + "</head>\n<body>\n" + frag[corpo_ini:] + "</body>\n</html>\n"


def main() -> int:
    frag, completo = montar()
    alvo = {"artefato.html": frag, "index.html": completo}
    if "--verificar" in sys.argv:
        velhos = [n for n, t in alvo.items() if not (PASTA / n).exists() or (PASTA / n).read_text(encoding="utf-8") != t]
        print("em dia" if not velhos else "DESATUALIZADO: " + ", ".join(velhos))
        return 1 if velhos else 0
    for nome, texto in alvo.items():
        (PASTA / nome).write_text(texto, encoding="utf-8", newline="\n")
        print(f"escrito: design/avatar-2026-09/{nome} ({len(texto) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
