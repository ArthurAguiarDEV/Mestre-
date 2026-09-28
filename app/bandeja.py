"""Icone do Mestre perto do relogio do Windows (bandeja do sistema).

Clique: abre o painel. Botao direito: pausar, reiniciar, desligar.
Se a biblioteca pystray nao estiver instalada, o Mestre funciona igual, so sem o icone.
"""
import logging
from pathlib import Path

from . import estado

log = logging.getLogger(__name__)
ARQUIVO_ICONE = Path(__file__).with_name("icone.png")


def imagem_do_icone():
    """Logo "Onda" (o "A" com a onda de voz) na cor de destaque escolhida no Painel > Aparencia."""
    try:
        from . import tema

        return tema.desenhar_icone(tamanho=64)
    except Exception:
        from PIL import Image

        if ARQUIVO_ICONE.exists():
            return Image.open(ARQUIVO_ICONE)
        return Image.new("RGBA", (64, 64), (245, 166, 200, 255))


def iniciar(abrir_painel, reiniciar, desligar, nome: str = "Mestre"):
    """Mostra o icone (roda em segundo plano). Devolve o icone ou None."""
    try:
        import pystray
    except Exception as erro:  # biblioteca faltando ou sistema sem bandeja
        log.info("Sem icone na bandeja (%s). Para ter: rode o INSTALAR_E_CRIAR_ATALHO.bat", erro)
        return None

    def alternar_pausa(icone, _item):
        estado.pausar(not estado.pausado())
        if not estado.pausado():
            estado.definir("ouvindo")
        icone.update_menu()

    def sair(icone, _item):
        icone.stop()
        desligar()

    menu = pystray.Menu(
        pystray.MenuItem("Abrir o painel", lambda *_: abrir_painel(), default=True),
        pystray.MenuItem(lambda _: "Retomar a escuta" if estado.pausado() else "Pausar a escuta", alternar_pausa),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(f"Reiniciar o {nome}", lambda *_: reiniciar()),
        pystray.MenuItem(f"Desligar o {nome}", sair),
    )
    try:
        icone = pystray.Icon("mestre", imagem_do_icone(), f"{nome} · clique para abrir o painel", menu)
        icone.run_detached()
        return icone
    except Exception as erro:
        log.warning("Nao consegui mostrar o icone na bandeja: %s", erro)
        return None
