"""Servidor da VOZ NATURAL (Chatterbox multilingue). Roda com o Python do ambiente SEPARADO
modelos/voz_natural/venv (torch e companhia ficam la, sem mexer nas bibliotecas do Mestre).

O Mestre liga este programa sozinho e pede as falas por http://127.0.0.1:47633:
  GET  /estado                     -> {"pronto": true/false, "placa": "cuda"|"cpu", "erro": ""}
  POST /falar {"texto", "referencia", "destino"} -> grava o .wav em "destino" e devolve {"ok": true}
Desliga sozinho quando o Mestre fecha. Nao importa nada do Mestre (roda em outro Python).
"""
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORTA = int(sys.argv[1]) if len(sys.argv) > 1 else 47633
PAI = int(sys.argv[2]) if len(sys.argv) > 2 else 0
estado = {"pronto": False, "placa": "", "erro": ""}
modelo = None
trava = threading.Lock()
referencia_atual = [""]


def carregar() -> None:
    global modelo
    try:
        import torch
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        placa = "cuda" if torch.cuda.is_available() else "cpu"
        estado["placa"] = placa
        modelo = ChatterboxMultilingualTTS.from_pretrained(device=placa)
        estado["pronto"] = True
    except Exception as erro:   # (vai para o diario do Mestre pelo /estado)
        estado["erro"] = f"{type(erro).__name__}: {erro}"


def falar(texto: str, referencia: str, destino: str) -> None:
    import soundfile   # (vem junto com o librosa, que o chatterbox usa)

    with trava:
        if referencia and referencia != referencia_atual[0]:
            modelo.prepare_conditionals(referencia, exaggeration=0.5)   # a "voz" (timbre) da referencia
            referencia_atual[0] = referencia
        # sem referencia: a voz padrao do modelo
        onda = modelo.generate(texto, language_id="pt", exaggeration=0.5, cfg_weight=0.5)
        parcial = destino + ".parcial.wav"
        soundfile.write(parcial, onda.squeeze(0).cpu().numpy(), modelo.sr)
        os.replace(parcial, destino)


class Atendente(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _json(self, codigo: int, dados: dict) -> None:
        corpo = json.dumps(dados).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        self._json(200, estado)

    def do_POST(self):
        dados = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
        if not estado["pronto"]:
            self._json(503, {"erro": estado["erro"] or "carregando"})
            return
        try:
            falar(str(dados.get("texto", "")), str(dados.get("referencia", "")), str(dados["destino"]))
            self._json(200, {"ok": True})
        except Exception as erro:
            self._json(500, {"erro": f"{type(erro).__name__}: {erro}"})


def pai_vivo() -> bool:
    if not PAI:
        return True
    if os.name == "nt":
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x00100000, False, PAI)   # SYNCHRONIZE
        if not h:
            return False
        vivo = ctypes.windll.kernel32.WaitForSingleObject(h, 0) == 0x102   # WAIT_TIMEOUT = ainda rodando
        ctypes.windll.kernel32.CloseHandle(h)
        return vivo
    try:
        os.kill(PAI, 0)
        return True
    except OSError:
        return False


def vigiar_pai() -> None:
    while pai_vivo():
        time.sleep(3)
    os._exit(0)


if __name__ == "__main__":
    servidor = ThreadingHTTPServer(("127.0.0.1", PORTA), Atendente)
    threading.Thread(target=vigiar_pai, daemon=True).start()
    threading.Thread(target=carregar, daemon=True).start()
    servidor.serve_forever()
