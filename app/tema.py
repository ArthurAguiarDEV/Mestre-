"""Visual do Mestre: cores e fonte do painel, do indicador e do icone.

O padrao e grafite escuro com rosa claro. Voce escolhe outra cor de destaque, outro fundo,
a fonte e o tamanho do texto no Painel > Aparencia (fica salvo em config.yaml > aparencia).
"""
import json
import sys
import tempfile
from pathlib import Path

# --- Opcoes que aparecem no painel ----------------------------------------------
CORES = {            # nome: cor de destaque
    "Rosa": "#F5A6C8",
    "Lilás": "#C3A6F5",
    "Azul": "#8DB8F7",
    "Verde-água": "#7EE2C8",
    "Laranja": "#F7B98D",
    "Amarelo": "#F2D67A",
}
FUNDOS = {           # nome: (fundo, menu lateral, blocos, campos, borda)
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
PADRAO = {"cor": "Rosa", "fundo": "Grafite", "fonte": "Segoe UI", "tamanho": "Normal"}


# --- Contas de cor ------------------------------------------------------------------
def _rgb(cor: str) -> tuple[int, int, int]:
    cor = cor.lstrip("#")
    return int(cor[0:2], 16), int(cor[2:4], 16), int(cor[4:6], 16)


def _hex(r: float, g: float, b: float) -> str:
    return "#{:02X}{:02X}{:02X}".format(*(max(0, min(255, round(x))) for x in (r, g, b)))


def misturar(cor_a: str, cor_b: str, quanto_b: float) -> str:
    a, b = _rgb(cor_a), _rgb(cor_b)
    return _hex(*(x + (y - x) * quanto_b for x, y in zip(a, b)))


def cor_valida(cor: str) -> bool:
    try:
        _rgb(cor)
        return len(cor.lstrip("#")) == 6
    except (ValueError, IndexError):
        return False


def paleta(aparencia: dict | None = None) -> dict:
    """Todas as cores a partir de 4 escolhas (cor, fundo, fonte, tamanho)."""
    a = {**PADRAO, **{k: v for k, v in (aparencia or {}).items() if v}}
    destaque = CORES.get(a["cor"], a["cor"] if cor_valida(str(a["cor"])) else CORES["Rosa"])
    fundo, lateral, cartao, campo, borda = FUNDOS.get(a["fundo"], FUNDOS["Grafite"])
    r, g, b = _rgb(destaque)
    claro = (0.299 * r + 0.587 * g + 0.114 * b) > 150
    fonte = str(a["fonte"]).strip() or PADRAO["fonte"]   # qualquer fonte instalada no PC vale
    if sys.platform != "win32" and fonte in FONTES:
        fonte = "DejaVu Sans"   # (so nos testes fora do Windows)
    return {
        "FUNDO": fundo, "LATERAL": lateral, "CARTAO": cartao, "CAMPO": campo, "BORDA": borda,
        "ROSA": destaque,                                   # (o nome ficou "ROSA", mas e a cor de destaque)
        "ROSA_CLARO": misturar(destaque, "#FFFFFF", 0.3),
        "ROSA_FUNDO": misturar(fundo, destaque, 0.14),
        "ROSA_FORTE": misturar(destaque, "#000000", 0.4),
        "TEXTO_NO_ROSA": "#1c1117" if claro else "#FFFFFF",
        "SECUNDARIO": misturar(cartao, "#FFFFFF", 0.06),
        "SECUNDARIO_HOVER": misturar(cartao, "#FFFFFF", 0.12),
        "FONTE": fonte,
        "TAMANHO": TAMANHOS.get(a["tamanho"], 14),
    }


def _ler_aparencia() -> dict:
    try:
        import yaml

        from .config import ARQUIVO_CONFIG

        return (yaml.safe_load(ARQUIVO_CONFIG.read_text(encoding="utf-8")) or {}).get("aparencia") or {}
    except Exception:
        return {}


# --- Cores em uso (lidas do config ao abrir) ---------------------------------------
TEXTO = "#EDEAF0"
TEXTO_FRACO = "#9d98a8"
PERIGO = "#5c2432"
PERIGO_HOVER = "#7a3044"
SUCESSO = "#7EE2B8"
AVISO = "#F2C27A"
_p = paleta(_ler_aparencia())
FUNDO, LATERAL, CARTAO, CAMPO, BORDA = _p["FUNDO"], _p["LATERAL"], _p["CARTAO"], _p["CAMPO"], _p["BORDA"]
ROSA, ROSA_CLARO, ROSA_FUNDO, ROSA_FORTE = _p["ROSA"], _p["ROSA_CLARO"], _p["ROSA_FUNDO"], _p["ROSA_FORTE"]
TEXTO_NO_ROSA, SECUNDARIO, SECUNDARIO_HOVER = _p["TEXTO_NO_ROSA"], _p["SECUNDARIO"], _p["SECUNDARIO_HOVER"]
FONTE, TAMANHO = _p["FONTE"], _p["TAMANHO"]


def fonte(tamanho_base: int = 14, negrito: bool = False):
    """Fonte do painel. tamanho_base e o tamanho no modo "Normal"; cresce junto no Grande/Maior."""
    import customtkinter as ctk

    return ctk.CTkFont(family=FONTE, size=tamanho_base + TAMANHO - 14, weight="bold" if negrito else "normal")


def aplicar() -> None:
    """Gera o tema a partir do tema escuro do customtkinter e ativa."""
    import customtkinter as ctk

    base = Path(ctk.__file__).parent / "assets" / "themes" / "dark-blue.json"
    tema = json.loads(base.read_text(encoding="utf-8"))
    par = lambda cor: [cor, cor]  # noqa: E731  (mesma cor no modo claro e escuro)
    mudar = {
        "CTk": {"fg_color": par(FUNDO)},
        "CTkToplevel": {"fg_color": par(FUNDO)},
        "CTkFrame": {"fg_color": par(CARTAO), "top_fg_color": par(CARTAO), "border_color": par(BORDA), "corner_radius": 12},
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
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme(str(arquivo))


# --- Icone (bandeja do relogio e atalho) --------------------------------------------
def desenhar_icone(cor: str | None = None, tamanho: int = 512):
    """O "M" do Mestre na cor de destaque. Devolve uma imagem do Pillow."""
    from PIL import Image, ImageDraw, ImageFont

    cor = cor or ROSA
    r, g, b = _rgb(cor)
    im = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    u = tamanho / 512
    d.rounded_rectangle((16 * u, 16 * u, tamanho - 16 * u, tamanho - 16 * u), radius=120 * u, fill=(r, g, b, 255))
    d.rounded_rectangle((52 * u, 52 * u, tamanho - 52 * u, tamanho - 52 * u), radius=92 * u, fill=(28, 17, 23, 255))
    fonte_m = None
    for nome in ("arialbd.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            fonte_m = ImageFont.truetype(nome, int(290 * u))
            break
        except OSError:
            continue
    fonte_m = fonte_m or ImageFont.load_default()
    caixa = d.textbbox((0, 0), "M", font=fonte_m)
    w, h = caixa[2] - caixa[0], caixa[3] - caixa[1]
    d.text(((tamanho - w) / 2 - caixa[0], (tamanho - h) / 2 - caixa[1]), "M", font=fonte_m, fill=(r, g, b, 255))
    d.ellipse((tamanho - 150 * u, tamanho - 150 * u, tamanho - 80 * u, tamanho - 80 * u), fill=(126, 226, 184, 255))
    return im


def salvar_icones(cor: str | None = None) -> None:
    """Regrava app/icone.png e app/icone.ico na cor escolhida (atalho e janela)."""
    im = desenhar_icone(cor)
    pasta = Path(__file__).parent
    im.resize((256, 256)).save(pasta / "icone.png")
    im.save(pasta / "icone.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
