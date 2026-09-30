"""Visual do Mestre: cores e fonte do painel, do indicador e do icone.

Layout Aurora: marfim + ameixa no modo claro (padrao) e um noturno ameixa. Voce escolhe o modo,
outra cor de destaque, outro fundo (do modo noturno), a fonte e o tamanho do texto no Painel > Ajustes >
Aparencia (fica salvo em config.yaml > aparencia). Configuracao antiga (cor/fundo/fonte/tamanho) continua valendo.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

# --- Opcoes que aparecem no painel ----------------------------------------------
AMEIXA = "#7654A0"   # destaque padrao do claro (no noturno vira AMEIXA_NOTURNA)
AMEIXA_NOTURNA = "#D5B7F0"
CORES = {            # nome: cor de destaque
    "Ameixa": AMEIXA,
    "Rosa": "#F5A6C8",
    "Lilás": "#C3A6F5",
    "Azul": "#8DB8F7",
    "Verde-água": "#7EE2C8",
    "Laranja": "#F7B98D",
    "Amarelo": "#F2D67A",
}
FUNDOS = {           # (modo noturno) nome: (fundo, cabecalho, blocos, campos, borda)
    "Ameixa": ("#19171D", "#242129", "#242129", "#302B36", "#463C4F"),
    "Grafite": ("#121216", "#18181e", "#1e1e26", "#262630", "#2c2c38"),
    "Preto": ("#08080a", "#0f0f12", "#16161a", "#1e1e23", "#26262d"),
    "Azul-noite": ("#0e1320", "#131a2a", "#192236", "#212b42", "#2a3550"),
}
FONTES = [  # todas vem com o Windows 10/11 (o painel so mostra as que existem no seu PC)
    "Segoe UI", "Segoe UI Semibold", "Segoe UI Light", "Calibri", "Calibri Light", "Arial", "Arial Black",
    "Verdana", "Tahoma", "Trebuchet MS", "Georgia", "Cambria", "Candara", "Constantia", "Corbel",
    "Bahnschrift", "Consolas", "Lucida Console", "Lucida Sans Unicode", "Franklin Gothic Medium",
    "Century Gothic", "Palatino Linotype", "Book Antiqua", "Sitka Text", "Segoe Print", "Segoe Script",
    "Ink Free", "Comic Sans MS", "Gabriola", "Courier New", "Times New Roman", "Impact",
]
TAMANHOS = {"Normal": 14, "Grande": 16, "Maior": 18}
MODOS = {"claro": "Claro", "escuro": "Noturno"}
PADRAO = {"cor": "Ameixa", "fundo": "Ameixa", "fonte": "Segoe UI", "tamanho": "Normal", "modo": "claro"}
FONTE_TITULO = "Georgia"   # titulos editoriais (vem com o Windows); o corpo usa a fonte escolhida

FORA_DA_TELA = (-32000, -32000)   # ponto fora de qualquer monitor real


def testando() -> bool:
    """True durante o teste automatico (testes/teste_basico.py, MESTRE_SIMULAR=1): nenhuma
    janela pode aparecer na tela. No uso normal (sem essa variavel) nada muda."""
    return os.environ.get("MESTRE_SIMULAR") == "1"


def posicao_janela(x: int, y: int) -> tuple[int, int]:
    """x, y normais, OU um ponto fora da tela durante o teste automatico (os widgets
    continuam existindo e funcionando: so a posicao muda, nada some da janela em si)."""
    return FORA_DA_TELA if testando() else (x, y)


# --- Contas de cor ------------------------------------------------------------------
def _rgb(cor: str) -> tuple[int, int, int]:
    cor = cor.lstrip("#")
    return int(cor[0:2], 16), int(cor[2:4], 16), int(cor[4:6], 16)


def _hex(r: float, g: float, b: float) -> str:
    return "#{:02X}{:02X}{:02X}".format(*(max(0, min(255, round(x))) for x in (r, g, b)))


def misturar(cor_a: str, cor_b: str, quanto_b: float) -> str:
    a, b = _rgb(cor_a), _rgb(cor_b)
    return _hex(*(x + (y - x) * quanto_b for x, y in zip(a, b)))


def _luz(cor: str) -> float:
    def canal(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = _rgb(cor)
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def _contraste(cor_a: str, cor_b: str) -> float:
    """Razao de contraste (WCAG) entre duas cores: 4,5 ou mais = texto normal legivel."""
    claro, escuro = sorted((_luz(cor_a), _luz(cor_b)), reverse=True)
    return (claro + 0.05) / (escuro + 0.05)


def cor_valida(cor: str) -> bool:
    try:
        _rgb(cor)
        return len(cor.lstrip("#")) == 6
    except (ValueError, IndexError):
        return False


def paleta(aparencia: dict | None = None) -> dict:
    """Todas as cores a partir das escolhas (modo, cor, fundo, fonte, tamanho)."""
    a = {**PADRAO, **{k: v for k, v in (aparencia or {}).items() if v}}
    modo = "escuro" if str(a["modo"]).lower() in ("escuro", "noturno", "dark") else "claro"
    bruto = CORES.get(a["cor"], a["cor"] if cor_valida(str(a["cor"])) else AMEIXA)   # a cor que a pessoa escolheu
    fonte = str(a["fonte"]).strip() or PADRAO["fonte"]   # qualquer fonte instalada no PC vale
    if sys.platform != "win32" and fonte in FONTES:
        fonte = "DejaVu Sans"   # (so nos testes fora do Windows)
    comum = {"FONTE": fonte, "TAMANHO": TAMANHOS.get(a["tamanho"], 14), "MODO": modo, "COR_INDICADOR": CORES["Rosa"] if bruto == AMEIXA else bruto}
    if modo == "claro":
        destaque = bruto
        if bruto != AMEIXA:   # escurece ate o texto branco do botao principal ficar legivel (4,5:1) sobre ela
            quanto = 0.3
            while quanto < 0.9 and _contraste("#FFFFFF", misturar(bruto, "#000000", quanto)) < 4.6:
                quanto += 0.05
            destaque = misturar(bruto, "#000000", quanto)
        fundo, lateral, cartao, campo, borda = "#F5F1E9", "#FFFDF8", "#FFFDF8", "#ECE6DD", "#D8D0C5"
        fundo_destaque = "#EEE5F5" if destaque == AMEIXA else misturar(cartao, destaque, 0.13)
        return {**comum, "FUNDO": fundo, "LATERAL": lateral, "CARTAO": cartao, "CAMPO": campo, "BORDA": borda,
                "ROSA": destaque, "ROSA_CLARO": misturar(destaque, "#FFFFFF", 0.18),
                "ROSA_FUNDO": fundo_destaque, "ROSA_FORTE": misturar(destaque, "#FFFFFF", 0.3),
                "TEXTO_NO_ROSA": "#FFFFFF", "SECUNDARIO": misturar(cartao, "#000000", 0.08),
                "SECUNDARIO_HOVER": misturar(cartao, "#000000", 0.14),
                "TEXTO": "#302D38", "TEXTO_FRACO": "#6B6170", "SUCESSO": "#2E7D5B", "SUCESSO_FUNDO": "#DCEFE5",
                "AVISO": "#855423", "AVISO_FUNDO": "#F6E7D3", "PERIGO": "#EBCBD1", "PERIGO_HOVER": "#E0B5BE",
                "LILAS": "#6B4E96", "AZUL_ROTULO": "#2F5C9E"}
    destaque = AMEIXA_NOTURNA if bruto == AMEIXA else bruto
    fundo, lateral, cartao, campo, borda = FUNDOS.get(a["fundo"], FUNDOS["Ameixa"])
    quanto = 0.0   # cor personalizada escura: clareia ate ficar legivel (4,5:1) sobre os blocos
    while quanto < 0.9 and _contraste(misturar(destaque, "#FFFFFF", quanto), cartao) < 4.5:
        quanto += 0.05
    destaque = misturar(destaque, "#FFFFFF", quanto) if quanto else destaque
    return {**comum, "FUNDO": fundo, "LATERAL": lateral, "CARTAO": cartao, "CAMPO": campo, "BORDA": borda,
            "ROSA": destaque,                                   # (o nome ficou "ROSA", mas e a cor de destaque)
            "ROSA_CLARO": misturar(destaque, "#FFFFFF", 0.3),
            "ROSA_FUNDO": "#3B2D4B" if destaque == AMEIXA_NOTURNA and a["fundo"] == "Ameixa"
            else misturar(fundo, destaque, 0.14),
            "ROSA_FORTE": misturar(destaque, "#000000", 0.4),
            "TEXTO_NO_ROSA": "#1c1117" if _contraste("#1c1117", destaque) >= _contraste("#FFFFFF", destaque) else "#FFFFFF",
            "SECUNDARIO": misturar(cartao, "#FFFFFF", 0.06),
            "SECUNDARIO_HOVER": misturar(cartao, "#FFFFFF", 0.12),
            "TEXTO": "#F5EEF8", "TEXTO_FRACO": "#BCAFC7", "SUCESSO": "#7EE2B8", "SUCESSO_FUNDO": "#1A2A24",
            "AVISO": "#F2C27A", "AVISO_FUNDO": "#2A2419", "PERIGO": "#5c2432", "PERIGO_HOVER": "#7a3044",
            "LILAS": "#C3A6F5", "AZUL_ROTULO": "#8DB8F7"}


def _ler_aparencia() -> dict:
    try:
        import yaml

        from .config import ARQUIVO_CONFIG

        return (yaml.safe_load(ARQUIVO_CONFIG.read_text(encoding="utf-8")) or {}).get("aparencia") or {}
    except Exception:
        return {}


# --- Cores em uso (lidas do config ao abrir) ---------------------------------------
_p = paleta(_ler_aparencia())
MODO = _p["MODO"]
COR_INDICADOR = _p["COR_INDICADOR"]   # cor do indicador/icone: a escolhida pura (padrao Ameixa = o rosa de sempre)
TEXTO, TEXTO_FRACO, LILAS, AZUL_ROTULO = _p["TEXTO"], _p["TEXTO_FRACO"], _p["LILAS"], _p["AZUL_ROTULO"]
PERIGO, PERIGO_HOVER = _p["PERIGO"], _p["PERIGO_HOVER"]
SUCESSO, SUCESSO_FUNDO, AVISO, AVISO_FUNDO = _p["SUCESSO"], _p["SUCESSO_FUNDO"], _p["AVISO"], _p["AVISO_FUNDO"]
FUNDO, LATERAL, CARTAO, CAMPO, BORDA = _p["FUNDO"], _p["LATERAL"], _p["CARTAO"], _p["CAMPO"], _p["BORDA"]
ROSA, ROSA_CLARO, ROSA_FUNDO, ROSA_FORTE = _p["ROSA"], _p["ROSA_CLARO"], _p["ROSA_FUNDO"], _p["ROSA_FORTE"]
TEXTO_NO_ROSA, SECUNDARIO, SECUNDARIO_HOVER = _p["TEXTO_NO_ROSA"], _p["SECUNDARIO"], _p["SECUNDARIO_HOVER"]
FONTE, TAMANHO = _p["FONTE"], _p["TAMANHO"]


def fonte(tamanho_base: int = 14, negrito: bool = False):
    """Fonte do painel. tamanho_base e o tamanho no modo "Normal"; cresce junto no Grande/Maior."""
    import customtkinter as ctk

    return ctk.CTkFont(family=FONTE, size=tamanho_base + TAMANHO - 14, weight="bold" if negrito else "normal")


def fonte_titulo(tamanho_base: int = 28):
    """Fonte editorial (Georgia) dos titulos grandes; cresce junto com o tamanho do texto."""
    import customtkinter as ctk

    familia = FONTE_TITULO if sys.platform == "win32" else "DejaVu Serif"
    return ctk.CTkFont(family=familia, size=tamanho_base + TAMANHO - 14, weight="normal")


def aplicar() -> None:
    """Gera o tema a partir do tema escuro do customtkinter e ativa."""
    import customtkinter as ctk

    base = Path(ctk.__file__).parent / "assets" / "themes" / "dark-blue.json"
    tema = json.loads(base.read_text(encoding="utf-8"))
    par = lambda cor: [cor, cor]  # noqa: E731  (mesma cor no modo claro e escuro)
    mudar = {
        "CTk": {"fg_color": par(FUNDO)},
        "CTkToplevel": {"fg_color": par(FUNDO)},
        "CTkFrame": {"fg_color": par(CARTAO), "top_fg_color": par(CARTAO), "border_color": par(BORDA), "corner_radius": 16},
        "CTkButton": {"fg_color": par(ROSA), "hover_color": par(ROSA_CLARO), "text_color": par(TEXTO_NO_ROSA),
                      "border_color": par(BORDA), "corner_radius": 10},
        "CTkLabel": {"text_color": par(TEXTO)},
        "CTkEntry": {"fg_color": par(CAMPO), "border_color": par(BORDA), "text_color": par(TEXTO),
                     "placeholder_text_color": par(TEXTO_FRACO), "corner_radius": 8},
        "CTkCheckBox": {"fg_color": par(ROSA), "hover_color": par(ROSA_CLARO), "checkmark_color": par(TEXTO_NO_ROSA),
                        "border_color": par(BORDA), "text_color": par(TEXTO)},
        "CTkSwitch": {"fg_color": par(SECUNDARIO), "progress_color": par(ROSA), "button_color": par(TEXTO),
                      "button_hover_color": par("#ffffff"), "text_color": par(TEXTO)},
        "CTkProgressBar": {"fg_color": par(CAMPO), "progress_color": par(ROSA), "border_color": par(BORDA)},
        "CTkSlider": {"fg_color": par(CAMPO), "progress_color": par(ROSA_FORTE), "button_color": par(ROSA),
                      "button_hover_color": par(ROSA_CLARO)},
        "CTkOptionMenu": {"fg_color": par(CAMPO), "button_color": par(SECUNDARIO_HOVER),
                          "button_hover_color": par(ROSA_FORTE), "text_color": par(TEXTO), "corner_radius": 8},
        "CTkComboBox": {"fg_color": par(CAMPO), "border_color": par(BORDA), "button_color": par(SECUNDARIO_HOVER),
                        "button_hover_color": par(ROSA_FORTE), "text_color": par(TEXTO)},
        "CTkScrollbar": {"button_color": par(SECUNDARIO_HOVER), "button_hover_color": par(ROSA_FORTE)},
        "CTkSegmentedButton": {"fg_color": par(CAMPO), "selected_color": par(ROSA_FORTE),
                               "selected_hover_color": par(ROSA_FORTE), "unselected_color": par(CAMPO),
                               "unselected_hover_color": par(SECUNDARIO_HOVER), "text_color": par(TEXTO)},
        "CTkTextbox": {"fg_color": par(CAMPO), "border_color": par(BORDA), "text_color": par(TEXTO),
                       "scrollbar_button_color": par(SECUNDARIO_HOVER), "scrollbar_button_hover_color": par(ROSA_FORTE)},
        "CTkScrollableFrame": {"label_fg_color": par(CARTAO)},
        "DropdownMenu": {"fg_color": par(CAMPO), "hover_color": par(ROSA_FUNDO), "text_color": par(TEXTO)},
    }
    for widget, valores in mudar.items():
        if widget in tema:
            tema[widget].update({k: v for k, v in valores.items() if k in tema[widget]})
    for sistema in ("Windows", "Linux", "macOS"):
        if sistema in tema.get("CTkFont", {}):
            tema["CTkFont"][sistema].update(family=FONTE, size=TAMANHO)
    arquivo = Path(tempfile.gettempdir()) / "mestre_tema.json"
    arquivo.write_text(json.dumps(tema), encoding="utf-8")
    ctk.set_appearance_mode("light" if MODO == "claro" else "dark")
    ctk.set_default_color_theme(str(arquivo))


# --- Icone (bandeja do relogio, atalho, janela e menu do painel): logo "Onda" -------------------
VERDE_ONDA = "#7DE3B8"


def tons_logo(cor: str) -> tuple[str, str, str]:
    """(claro, meio, escuro) do "A". Rosa padrão = cores exatas do protótipo; outra cor = misturas."""
    if cor.upper() == "#F5A6C8":
        return "#FFD3E5", "#F5A6C8", "#D9829F"
    return misturar(cor, "#FFFFFF", 0.5), cor, misturar(cor, "#000000", 0.12)


def desenhar_icone(cor: str | None = None, tamanho: int = 512, simples: bool | None = None):
    """Logo "Onda": o "A" na cor de destaque e a barra do A virou uma onda de voz verde.
    Até 40 px usa a versão simplificada (traço mais grosso, 3 barras, sem brilho). Desenha em 4x e reduz.
    Devolve uma imagem RGBA do Pillow (grade de 256, igual ao SVG do protótipo)."""
    import numpy as np
    from PIL import Image, ImageDraw

    cor = cor if cor and cor_valida(cor) else COR_INDICADOR
    simples = tamanho <= 40 if simples is None else simples
    g = max(64, tamanho * 4)
    u = g / 256

    def mascara(desenho):
        m = Image.new("L", (g, g), 0)
        desenho(ImageDraw.Draw(m))
        return m

    def gradiente(x1, y1, x2, y2, paradas):
        """Degradê linear (userSpaceOnUse) como no SVG."""
        yy, xx = np.mgrid[0:g, 0:g].astype(np.float32) / u
        dx, dy = x2 - x1, y2 - y1
        t = np.clip(((xx - x1) * dx + (yy - y1) * dy) / (dx * dx + dy * dy), 0, 1)
        pos = [p for p, _ in paradas]
        canais = [np.interp(t, pos, [_rgb(c)[i] for _, c in paradas]) for i in range(3)]
        return Image.fromarray(np.dstack(canais + [np.full_like(t, 255)]).astype(np.uint8), "RGBA")

    im = Image.new("RGBA", (g, g), (0, 0, 0, 0))
    # placa escura arredondada (degradê de cima para baixo)
    placa = mascara(lambda d: d.rounded_rectangle((8 * u, 8 * u, 248 * u, 248 * u), radius=64 * u, fill=255))
    im.paste(gradiente(0, 8, 0, 248, [(0, "#2C1F26"), (1, "#140E11")]), (0, 0), placa)
    if not simples:
        borda = Image.new("RGBA", (g, g), (0, 0, 0, 0))
        ImageDraw.Draw(borda).rounded_rectangle((9.5 * u, 9.5 * u, 246.5 * u, 246.5 * u), radius=62.5 * u,
                                                outline=(*_rgb(cor), 56), width=max(1, round(3 * u)))
        im.alpha_composite(borda)
        # brilho redondo atrás do A
        yy, xx = np.mgrid[0:g, 0:g].astype(np.float32) / u
        r = np.sqrt((xx - 128) ** 2 + (yy - 150) ** 2) / 96
        alfa = np.clip(1 - r, 0, 1) * 0.45 * 0.5 * 255
        halo = np.dstack([np.full_like(r, c) for c in _rgb(cor)] + [alfa]).astype(np.uint8)
        halo_im = Image.fromarray(halo, "RGBA")
        halo_im.putalpha(Image.fromarray(np.minimum(np.array(placa), alfa).astype(np.uint8), "L"))
        im.alpha_composite(halo_im)
    # o "A" (traço grosso com pontas e junta redondas)
    largura = (46 if simples else 38) * u
    pontos = [(62 * u, 206 * u), (128 * u, 54 * u), (194 * u, 206 * u)]

    def letra(d):
        d.line(pontos, fill=255, width=round(largura), joint="curve")
        for x, y in pontos:
            d.ellipse((x - largura / 2, y - largura / 2, x + largura / 2, y + largura / 2), fill=255)
    claro, meio, escuro = tons_logo(cor)
    im.paste(gradiente(40, 40, 220, 230, [(0, claro), (0.55, meio), (1, escuro)]), (0, 0), mascara(letra))
    # a onda de voz no lugar da barra do A (contorno escuro por baixo, como paint-order: stroke)
    barras = ([(96, 14, 44), (128, 14, 64), (160, 14, 44)] if simples
              else [(92, 11, 26), (110, 11, 46), (128, 11, 62), (146, 11, 46), (164, 11, 26)])
    contorno = (5 if simples else 4) / 2
    d = ImageDraw.Draw(im)
    for x, w, h in barras:
        for folga, tinta in ((contorno, (28, 20, 24, 255)), (0, (*_rgb(VERDE_ONDA), 255))):
            caixa = ((x - w / 2 - folga) * u, (158 - h / 2 - folga) * u, (x + w / 2 + folga) * u, (158 + h / 2 + folga) * u)
            d.rounded_rectangle(caixa, radius=(w / 2 + folga) * u, fill=tinta)
    return im.resize((tamanho, tamanho), Image.LANCZOS)


TAMANHOS_ICO = (16, 24, 32, 48, 64, 128, 256)


def definir_icone_da_barra() -> None:
    """Faz o Windows mostrar o ícone do programa na barra de tarefas, não o do Python."""
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Assessor.Painel")
    except Exception:
        pass


def salvar_icones(cor: str | None = None) -> None:
    """Regrava app/icone.png (256) e app/icone.ico (16 a 256, cada tamanho desenhado para ele) na cor escolhida."""
    pasta = Path(__file__).parent
    desenhar_icone(cor, 256).save(pasta / "icone.png")
    imagens = [desenhar_icone(cor, t) for t in TAMANHOS_ICO]
    imagens[-1].save(pasta / "icone.ico", sizes=[(t, t) for t in TAMANHOS_ICO], append_images=imagens[:-1])
