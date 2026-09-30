"""Prévia local opcional: python servir_previa.py. Abra http://127.0.0.1:8846/."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        # pythonw não possui stderr; a prévia não registra dados de navegação.
        pass


if __name__ == "__main__":
    handler = partial(QuietHandler, directory=str(Path(__file__).resolve().parent))
    with ThreadingHTTPServer(("127.0.0.1", 8846), handler) as server:
        server.serve_forever()
