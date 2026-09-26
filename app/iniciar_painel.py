"""Abre o painel e, se der erro, MOSTRA o motivo (em vez de sumir calado).

O erro tambem fica gravado em logs/painel_erro.log.
"""
import socket
import sys
import traceback

from .config import PASTA_LOGS

PORTA_PAINEL = 47631   # o painel aberto escuta aqui; um segundo clique no atalho so traz ele para frente


def avisar_painel_aberto() -> bool:
    """True se ja existe um painel aberto (e ele foi trazido para frente)."""
    try:
        socket.create_connection(("127.0.0.1", PORTA_PAINEL), timeout=0.5).close()
        return True
    except OSError:
        return False

DICAS = {  # a primeira que aparecer no erro vence
    "duplicate key": ("O config.yaml tem uma seção repetida (ex.: \"voz:\" duas vezes). "
                      "Esta versão conserta isso sozinha; se ainda aparecer, mande este erro para o Claude."),
    "no module named 'tkinter'": ("O Python foi instalado sem o componente de janelas (tcl/tk).\n"
                                  "Conserto: Configurações do Windows > Aplicativos > Python 3.12 > Modificar > Modify >\n"
                                  "marque \"tcl/tk and IDLE\" > Next > Install. Depois abra o painel de novo."),
    "no module named '_tkinter'": "O Python está sem o componente de janelas (tcl/tk). Reinstale marcando \"tcl/tk and IDLE\".",
    "no module named 'customtkinter'": "Falta a biblioteca do painel. Rode o INSTALAR_E_CRIAR_ATALHO.bat (pasta principal).",
    "no module named 'ruamel'": "Falta a biblioteca que salva o config. Rode o INSTALAR_E_CRIAR_ATALHO.bat (pasta principal).",
    "scannererror": "O config.yaml tem um erro de digitação (TAB, recuo ou aspas). Veja a linha indicada abaixo.",
    "parsererror": "O config.yaml tem um erro de digitação (TAB, recuo ou aspas). Veja a linha indicada abaixo.",
}


def _avisar(texto: str) -> None:
    print(texto, file=sys.stderr)
    try:
        import tkinter as tk
        from tkinter import messagebox

        raiz = tk.Tk()
        raiz.withdraw()
        messagebox.showerror("Mestre - o painel não abriu", texto)
        raiz.destroy()
    except Exception:
        pass  # sem tkinter nao da para mostrar janela; fica no log e no terminal


def main() -> None:
    if avisar_painel_aberto():
        return
    try:
        from .painel import main as abrir

        abrir()
    except Exception as erro:
        detalhe = traceback.format_exc()
        PASTA_LOGS.mkdir(exist_ok=True)
        (PASTA_LOGS / "painel_erro.log").write_text(detalhe, encoding="utf-8")
        dica = next((d for chave, d in DICAS.items() if chave in detalhe.lower()),
                    "Mande este erro para o Claude (ele também está em logs\\painel_erro.log).")
        _avisar(f"{dica}\n\nErro: {erro}")
        sys.exit(1)


if __name__ == "__main__":
    main()
