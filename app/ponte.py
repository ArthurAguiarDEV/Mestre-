"""Ponte entre o Mestre e a extensao do Brave (pasta extensao_brave/).

Um servidorzinho SO no proprio PC (127.0.0.1:47632). A extensao pergunta "tem pedido?"
(/proximo), faz a acao na aba do YouTube e devolve a resposta (/resposta).
O painel consulta /estado para mostrar se a extensao esta conectada.
"""
import itertools
import json
import logging
import queue
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

log = logging.getLogger(__name__)
PORTA = 47632


class Ponte:
    def __init__(self, porta: int = PORTA):
        self.porta = porta
        self._fila: queue.Queue = queue.Queue()
        self._respostas: dict = {}
        self._eventos: dict = {}
        self._ids = itertools.count(1)
        self.ultimo_contato = 0.0
        self.versao = ""   # versao da extensao (vem em cada /proximo)
        self._servidor = None

    # --- lado do Mestre ----------------------------------------------------------------
    def iniciar(self) -> bool:
        if self._servidor:
            return True
        ponte = self

        class Atendente(BaseHTTPRequestHandler):
            def log_message(self, *args):   # sem poluir o diario
                pass

            def _json(self, codigo: int, dados=None):
                corpo = json.dumps(dados or {}).encode("utf-8")
                self.send_response(codigo)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)

            def do_GET(self):
                if self.path.startswith("/proximo"):
                    ponte.ultimo_contato = time.time()
                    achado = re.search(r"[?&]v=([\d.]+)", self.path)
                    ponte.versao = achado.group(1) if achado else "1"
                    try:
                        pedido = ponte._fila.get(timeout=20)   # espera ate 20 s por um pedido
                    except queue.Empty:
                        self.send_response(204)
                        self.end_headers()
                        return
                    self._json(200, pedido)
                elif self.path.startswith("/estado"):
                    self._json(200, {"extensao_conectada": ponte.conectada(), "versao": ponte.versao})
                else:
                    self._json(404)

            def do_POST(self):
                if not self.path.startswith("/resposta"):
                    self._json(404)
                    return
                tamanho = int(self.headers.get("Content-Length") or 0)
                try:
                    dados = json.loads(self.rfile.read(tamanho) or b"{}")
                except ValueError:
                    dados = {}
                ponte.ultimo_contato = time.time()
                ident = dados.get("id")
                if ident in ponte._eventos:
                    ponte._respostas[ident] = dados
                    ponte._eventos[ident].set()
                self._json(200)

        try:
            self._servidor = ThreadingHTTPServer(("127.0.0.1", self.porta), Atendente)
        except OSError as erro:
            log.warning("Ponte do Brave nao abriu a porta %d: %s", self.porta, erro)
            return False
        threading.Thread(target=self._servidor.serve_forever, daemon=True).start()
        log.info("Ponte do Brave ouvindo em 127.0.0.1:%d", self.porta)
        return True

    def conectada(self) -> bool:
        return time.time() - self.ultimo_contato < 45

    def pedir(self, acao: str, arg=None, espera: float = 8.0, aba: int | None = None):
        """Manda um pedido para a extensao e devolve o resultado (ou levanta TimeoutError/RuntimeError).
        aba: as acoes do YouTube vao para essa aba (senao, a do YouTube que voce usou por ultimo)."""
        ident = next(self._ids)
        evento = threading.Event()
        self._eventos[ident] = evento
        pedido = {"id": ident, "acao": acao, "arg": arg}
        if aba:
            pedido["aba"] = aba
        self._fila.put(pedido)
        try:
            if not evento.wait(espera):
                raise TimeoutError("a extensao do Brave nao respondeu")
            dados = self._respostas.pop(ident, {})
        finally:
            self._eventos.pop(ident, None)
        if dados.get("erro"):
            raise RuntimeError(dados["erro"])
        return dados.get("resultado", dados.get("ok"))


VERSAO_EXTENSAO = "2.2"   # a da pasta extensao_brave (manifest.json)


def desatualizada(versao: str) -> bool:
    try:
        return tuple(int(x) for x in (versao or "0").split(".")) < tuple(int(x) for x in VERSAO_EXTENSAO.split("."))
    except ValueError:
        return True


def versao_da_extensao() -> str:
    """Para o painel: a versao que esta rodando no Brave ("" = nao conectada)."""
    try:
        import urllib.request

        with urllib.request.urlopen(f"http://127.0.0.1:{PORTA}/estado", timeout=1) as r:
            dados = json.loads(r.read())
            return str(dados.get("versao") or "1") if dados.get("extensao_conectada") else ""
    except Exception:
        return ""


def extensao_conectada() -> bool:
    """Para o painel (outro programa): pergunta ao Mestre se a extensao esta conversando com ele."""
    try:
        import urllib.request

        with urllib.request.urlopen(f"http://127.0.0.1:{PORTA}/estado", timeout=1) as r:
            return bool(json.loads(r.read()).get("extensao_conectada"))
    except Exception:
        return False
