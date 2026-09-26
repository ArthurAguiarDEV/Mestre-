"""Navegador controlado pelo Mestre (para o YouTube "ver" a pagina e agir nela).

Usa o Brave (ou Edge/Chrome) que ja esta no PC, com um PERFIL SEPARADO so do Mestre
(pasta navegador_mestre/). Na primeira vez, entre na sua conta do YouTube nessa janela:
o login fica guardado. Biblioteca: playwright (gratis). Nao baixa navegador nenhum.

Tudo roda numa linha propria (o Playwright exige), e os comandos esperam a resposta.
"""
import logging
import os
import queue
import threading

from .config import PASTA_PROJETO

log = logging.getLogger(__name__)
PASTA_PERFIL = PASTA_PROJETO / "navegador_mestre"


def caminho_do_brave() -> str | None:
    """Onde o Brave esta instalado (ou None)."""
    from pathlib import Path

    for base in (os.environ.get("LOCALAPPDATA"), os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)")):
        if base:
            exe = Path(base) / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe"
            if exe.exists():
                return str(exe)
    return None


PERFIL_BRAVE = ""   # "Profile 1"... (config: janelas.perfil_brave). Vazio = o ultimo que voce usou


def perfil_do_brave() -> str:
    """A pasta do perfil do Brave que voce usa (com suas contas). Sem isso, o "--new-window" pode abrir
    num perfil vazio, e o login do Google la chama o navegador de "nao confiavel"."""
    if PERFIL_BRAVE:
        return PERFIL_BRAVE
    import json
    from pathlib import Path

    try:
        estado = Path(os.environ.get("LOCALAPPDATA", "")) / "BraveSoftware" / "Brave-Browser" / "User Data" / "Local State"
        return str(json.loads(estado.read_text(encoding="utf-8")).get("profile", {}).get("last_used") or "")
    except Exception:
        return ""


def comando_do_brave(brave: str, *args: str) -> list[str]:
    """brave.exe [--profile-directory=<seu perfil>] + argumentos."""
    perfil = perfil_do_brave()
    return [brave] + ([f"--profile-directory={perfil}"] if perfil else []) + list(args)


class Navegador:
    def __init__(self, canal: str = "brave"):
        self.canal = canal   # "brave" | "msedge" | "chrome"
        self.aviso = ""      # ex.: "Nao achei o Brave: abri no Edge"
        self._fila: queue.Queue = queue.Queue()
        self._linha: threading.Thread | None = None
        self._ctx = None
        self._pagina = None

    @staticmethod
    def disponivel() -> bool:
        import importlib.util

        return importlib.util.find_spec("playwright") is not None

    # --- linha propria do Playwright ------------------------------------------------
    def _laco(self) -> None:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            self._pw = pw
            while True:
                funcao, resposta = self._fila.get()
                if funcao is None:
                    break
                try:
                    resposta.put((True, funcao()))
                except Exception as erro:  # a pagina fechou, o YouTube mudou etc.
                    log.warning("Navegador: %s", erro)
                    resposta.put((False, erro))

    def rodar(self, funcao, espera: float = 40):
        """Roda funcao() na linha do navegador e devolve o resultado (ou levanta o erro)."""
        if not self._linha or not self._linha.is_alive():
            self._linha = threading.Thread(target=self._laco, daemon=True)
            self._linha.start()
        resposta: queue.Queue = queue.Queue()
        self._fila.put((funcao, resposta))
        ok, valor = resposta.get(timeout=espera)
        if not ok:
            raise valor
        return valor

    def _garantir_pagina(self):
        """(na linha do navegador) Abre o navegador se preciso e devolve a aba."""
        if self._ctx is not None:
            try:
                if self._pagina is None or self._pagina.is_closed():
                    abertas = [p for p in self._ctx.pages if not p.is_closed()]
                    self._pagina = abertas[-1] if abertas else self._ctx.new_page()
                return self._pagina
            except Exception:
                self._ctx = None   # voce fechou a janela: abre de novo
        PASTA_PERFIL.mkdir(exist_ok=True)
        opcoes = dict(user_data_dir=str(PASTA_PERFIL), headless=False, no_viewport=True,
                      args=["--start-maximized", "--autoplay-policy=no-user-gesture-required"],
                      ignore_default_args=["--enable-automation"])
        exe = os.environ.get("MESTRE_NAVEGADOR_EXE")   # (testes)
        if not exe and self.canal == "brave":
            exe = caminho_do_brave()
            if not exe:
                self.aviso = "Não achei o Brave neste PC. Abri no Edge."
                log.warning("Brave nao encontrado: usando o Edge")
        if exe:
            opcoes["executable_path"] = exe
        else:
            opcoes["channel"] = self.canal if self.canal != "brave" else "msedge"
        self._ctx = self._pw.chromium.launch_persistent_context(**opcoes)
        self._pagina = self._ctx.pages[0] if self._ctx.pages else self._ctx.new_page()
        return self._pagina

    def aberto(self) -> bool:
        try:
            return self._ctx is not None and self.rodar(
                lambda: self._pagina is not None and not self._pagina.is_closed(), espera=5)
        except Exception:
            return False

    # --- acoes gerais --------------------------------------------------------------------
    def abrir(self, url: str, monitor: dict | None = None) -> None:
        def f():
            pagina = self._garantir_pagina()
            pagina.goto(url, wait_until="domcontentloaded")
            pagina.bring_to_front()
            if monitor:
                self._levar_para(pagina, monitor)
        self.rodar(f)

    def _levar_para(self, pagina, m: dict) -> None:
        """(na linha do navegador) Poe a janela no monitor pedido, maximizada."""
        cdp = self._ctx.new_cdp_session(pagina)
        janela = cdp.send("Browser.getWindowForTarget")["windowId"]
        cdp.send("Browser.setWindowBounds", {"windowId": janela, "bounds": {"windowState": "normal"}})
        cdp.send("Browser.setWindowBounds", {"windowId": janela, "bounds": {
            "left": m["x"] + 40, "top": m["y"] + 40, "width": max(800, m["largura"] - 80), "height": max(600, m["altura"] - 80)}})
        cdp.send("Browser.setWindowBounds", {"windowId": janela, "bounds": {"windowState": "maximized"}})

    def endereco(self) -> str:
        return self.rodar(lambda: self._pagina.url if self._pagina and not self._pagina.is_closed() else "", espera=5)

    def tecla(self, tecla: str) -> None:
        def f():
            pagina = self._garantir_pagina()
            pagina.bring_to_front()
            pagina.evaluate("() => { const a = document.activeElement; if (a && a.blur) a.blur(); }")
            pagina.keyboard.press(tecla)
        self.rodar(f)

    def js(self, codigo: str, argumento=None):
        return self.rodar(lambda: self._garantir_pagina().evaluate(codigo, argumento))

    def janela_tela_cheia(self, sim: bool) -> None:
        """Tela cheia da JANELA do navegador (a pagina continua inteira, com o chat)."""
        def f():
            pagina = self._garantir_pagina()
            cdp = self._ctx.new_cdp_session(pagina)
            janela = cdp.send("Browser.getWindowForTarget")["windowId"]
            cdp.send("Browser.setWindowBounds", {"windowId": janela,
                                                 "bounds": {"windowState": "fullscreen" if sim else "normal"}})
        self.rodar(f)


# --- YouTube -------------------------------------------------------------------------------
JS_LIKE = """() => {
  const b = document.querySelector('like-button-view-model button, #segmented-like-button button, ytd-toggle-button-renderer#like-button button');
  if (!b) return 'nao_achei';
  if (b.getAttribute('aria-pressed') === 'true') return 'ja';
  b.click(); return 'ok';
}"""
JS_INSCREVER = """() => {
  const b = document.querySelector('#subscribe-button button, ytd-subscribe-button-renderer button, yt-subscribe-button-view-model button');
  if (!b) return 'nao_achei';
  const t = (b.innerText || b.getAttribute('aria-label') || '').toLowerCase();
  if (t.includes('inscrito') || t.includes('subscribed')) return 'ja';
  b.click(); return 'ok';
}"""
JS_CHAT = """(mostrar) => {
  const frame = document.querySelector('ytd-live-chat-frame');
  if (!frame) return 'sem_chat';
  const aberto = !frame.hasAttribute('collapsed');
  if (aberto === mostrar) return 'ja';
  const b = frame.querySelector('#show-hide-button button') || frame.querySelector('#show-hide-button');
  if (!b) return 'nao_achei';
  b.click(); return 'ok';
}"""
JS_RESULTADOS = """() => Array.from(document.querySelectorAll(
  'ytd-video-renderer a#video-title, ytd-rich-item-renderer a#video-title-link, ytd-compact-video-renderer a#video-title-link, ytd-rich-grid-media a#video-title-link'))
  .filter(e => e.offsetParent !== null && e.href && !e.href.includes('/shorts/'))
  .map(e => ({titulo: (e.getAttribute('title') || e.textContent || '').trim(), link: e.href}))"""
JS_PULAR = "(s) => { const v = document.querySelector('video'); if (!v) return false; v.currentTime = Math.max(0, v.currentTime + s); return true; }"
JS_TELA_CHEIA = "() => !!document.fullscreenElement"
JS_VOLUME = """(p) => { const v = document.querySelector('video'); if (!v) return 'sem_video';
  if (p.acao === 'mudo') v.muted = true; else if (p.acao === 'som') v.muted = false;
  else { v.muted = false; v.volume = Math.max(0, Math.min(1, p.acao === 'definir' ? p.valor :
         v.volume + (p.acao === 'mais' ? 1 : -1) * p.valor)); }
  return 'ok'; }"""
JS_PAUSAR = """(pausar) => { const v = document.querySelector('video'); if (!v) return 'sem_video';
  if (v.paused === pausar) return 'ja'; pausar ? v.pause() : v.play(); return 'ok'; }"""


class YouTube:
    """Acoes do YouTube na janela controlada pelo Mestre."""
    completo = True   # consegue like, chat, resultados...

    def __init__(self, navegador: Navegador):
        self.nav = navegador

    def na_pagina_do_youtube(self) -> bool:
        try:
            return "youtube.com" in self.nav.endereco()
        except Exception:
            return False

    def tela_cheia(self, sim: bool) -> None:
        if bool(self.nav.js(JS_TELA_CHEIA)) != sim:
            self.nav.tecla("f")

    def modo_cinema(self) -> None:
        self.nav.tecla("t")

    def legenda(self) -> None:
        self.nav.tecla("c")

    def proximo(self) -> None:
        self.nav.tecla("Shift+N")

    def pausar(self, pausar: bool) -> str:
        return str(self.nav.js(JS_PAUSAR, pausar))

    def info(self) -> dict:
        return {"url": self.nav.endereco()}

    def volume_video(self, acao: str, valor: float = 0.15) -> str:
        return str(self.nav.js(JS_VOLUME, {"acao": acao, "valor": valor}))

    def pular(self, segundos: int) -> bool:
        return bool(self.nav.js(JS_PULAR, segundos))

    def like(self) -> str:
        return self.nav.js(JS_LIKE)

    def inscrever(self) -> str:
        return self.nav.js(JS_INSCREVER)

    def chat(self, mostrar: bool) -> str:
        return self.nav.js(JS_CHAT, mostrar)

    def tela_cheia_com_chat(self) -> None:
        """O YouTube nao mostra o chat na tela cheia dele: usa a janela inteira + modo cinema."""
        if self.nav.js(JS_TELA_CHEIA):
            self.nav.tecla("f")
        self.chat(True)
        self.nav.janela_tela_cheia(True)

    def resultados(self) -> list[dict]:
        return self.nav.js(JS_RESULTADOS) or []

    def abrir(self, link: str, monitor: dict | None = None) -> None:
        self.nav.abrir(link, monitor)


class YouTubeNoNavegadorNormal:
    """Modo "meu Brave normal": abre no seu navegador de sempre e usa as TECLAS do YouTube.

    Funciona: tela cheia, modo cinema, legenda, avancar/voltar, proximo video.
    Nao funciona (precisa enxergar a pagina): like, inscrever, chat, abrir o N-esimo, ler titulos.
    """
    NAO_DA = "sem_controle"
    completo = False

    def __init__(self, exe: str | None):
        self.exe = exe

    def abrir(self, link: str, monitor: dict | None = None) -> None:
        from . import sistema
        if not self.exe:
            sistema.abrir_site(link)
            return
        import subprocess
        antes = sistema.janela_da_frente()
        subprocess.Popen(comando_do_brave(self.exe, "--new-window", link) if "brave" in str(self.exe).lower() else [self.exe, "--new-window", link])
        sistema.depois_de_abrir(antes)

    def na_pagina_do_youtube(self) -> bool:
        from . import sistema
        if not sistema.EH_WINDOWS:
            return False
        titulo = next((t for h, t, _ in sistema._janelas_visiveis() if h == sistema.janela_da_frente()), "")
        return "youtube" in titulo.lower()

    def _tecla(self, *teclas: str) -> None:
        from . import sistema
        for t in teclas:
            sistema.tecla_letra(t)

    def tela_cheia(self, sim: bool) -> None:
        from . import sistema
        self._tecla("f") if sim else sistema.atalho("esc")

    def modo_cinema(self) -> None:
        self._tecla("t")

    def legenda(self) -> None:
        self._tecla("c")

    def proximo(self) -> None:
        from . import sistema
        sistema.atalho("shift", "n")

    def pular(self, segundos: int) -> bool:
        vezes = max(1, round(abs(segundos) / 10))
        self._tecla(*(["l" if segundos > 0 else "j"] * vezes))
        return True

    def pausar(self, pausar: bool) -> str:
        from . import sistema
        sistema.midia("tocar_pausar")
        return "ok"

    def info(self) -> dict:
        return {}

    def volume_video(self, acao: str, valor: float = 0.15) -> str:
        """Sem a extensao: so da para mutar/desmutar (tecla M do YouTube)."""
        if acao in ("mudo", "som"):
            self._tecla("m")
            return "ok"
        return self.NAO_DA

    def like(self) -> str:
        return self.NAO_DA

    def inscrever(self) -> str:
        return self.NAO_DA

    def chat(self, mostrar: bool) -> str:
        return self.NAO_DA

    def tela_cheia_com_chat(self) -> None:
        from . import sistema
        sistema.atalho("f11")

    def resultados(self) -> list[dict]:
        return []


class YouTubeNoBraveComExtensao(YouTubeNoNavegadorNormal):
    """O SEU Brave (com seus logins) + a extensao do Mestre: todos os comandos.

    Teclas (tela cheia, cinema, legenda) vao direto para a janela; o que precisa "ver"
    a pagina (like, chat, resultados) passa pela extensao (app/ponte.py).
    """

    def __init__(self, exe: str | None, ponte):
        super().__init__(exe)
        self.ponte = ponte
        self.aba_alvo: int | None = None   # a aba do YouTube escolhida pelo Mestre (ex.: a do monitor 2)

    def _p(self, acao: str, arg=None, espera: float = 8.0):
        return self.ponte.pedir(acao, arg, espera=espera, aba=self.aba_alvo)

    @property
    def completo(self) -> bool:
        return self.ponte.conectada()

    def na_pagina_do_youtube(self) -> bool:
        if self.ponte.conectada():
            try:
                return "youtube.com" in str(self._p("endereco", espera=4))
            except Exception:
                return False
        return super().na_pagina_do_youtube()

    def abrir(self, link: str, monitor: dict | None = None) -> None:
        from . import sistema
        # "... no monitor 2": janela nova (so ela vai para la); senao, na aba do YouTube em uso
        if self.ponte.conectada() and not sistema.MONITOR_ALVO:
            try:
                self._p("abrir", link)
                return
            except Exception as erro:
                log.info("Extensao nao abriu o link (%s): abrindo o Brave", erro)
        super().abrir(link, monitor)

    def _pedir(self, acao: str, arg=None):
        if not self.ponte.conectada():
            return self.NAO_DA
        return self._p(acao, arg)

    def _focar(self) -> None:
        """Traz a aba do YouTube para a frente (as teclas vao para a janela da frente)."""
        if self.ponte.conectada():
            try:
                self._p("focar_youtube", espera=4)
                import time
                time.sleep(0.3)
            except Exception as erro:
                log.info("Nao consegui focar o YouTube: %s", erro)

    def _tecla(self, *teclas: str) -> None:
        self._focar()
        super()._tecla(*teclas)

    def tela_cheia(self, sim: bool) -> None:
        from . import sistema
        if sim:
            self._tecla("f")
        else:
            self._focar()
            sistema.atalho("esc")

    def tela_cheia_com_chat(self) -> None:
        self._focar()
        super().tela_cheia_com_chat()

    def proximo(self) -> None:
        if self.ponte.conectada() and self._p("proximo") == "ok":
            return
        self._focar()
        super().proximo()

    def pausar(self, pausar: bool) -> str:
        if self.ponte.conectada():
            return str(self._p("pausar" if pausar else "continuar"))
        return super().pausar(pausar)

    def info(self) -> dict:
        r = self._pedir("info")
        return r if isinstance(r, dict) else {}

    def volume_video(self, acao: str, valor: float = 0.15) -> str:
        if not self.ponte.conectada():
            return super().volume_video(acao, valor)
        return str(self._p("volume", {"acao": acao, "valor": valor}))

    def like(self) -> str:
        return self._pedir("like")

    def inscrever(self) -> str:
        return self._pedir("inscrever")

    def chat(self, mostrar: bool) -> str:
        return self._pedir("chat", mostrar)

    def resultados(self) -> list[dict]:
        r = self._pedir("resultados")
        return r if isinstance(r, list) else []

    def pular(self, segundos: int) -> bool:
        if self.ponte.conectada():
            return bool(self._p("pular", segundos))
        return super().pular(segundos)
