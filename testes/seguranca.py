"""Barreira de testes: instalada antes de importar app, sem criar recursos nativos.

Não é uma sandbox para código hostil. Bloqueia os pontos de saída usados pelo
projeto; testes de integrações devem substituir esses pontos por doubles.
"""
import ctypes
import importlib.abc
import os
import socket
import subprocess
import sys
import webbrowser
import _tkinter


class EfeitoRealBloqueado(BaseException):
    """Não pode ser engolido pelos fallbacks `except Exception` do aplicativo."""


tentativas = []
_instalada = False


def bloquear(nome):
    def proibido(*args, **kwargs):
        tentativas.append(nome)
        raise EfeitoRealBloqueado(f"Teste tentou efeito real: {nome}")
    return proibido


class _SemBibliotecasNativas(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        raiz = fullname.split('.')[0]
        if raiz in {
            'PySide6', 'PyQt5', 'PyQt6', 'pyautogui', 'pynput', 'keyboard',
            'mouse', 'sounddevice', 'pyaudio', 'pygame', 'winsound', 'pyttsx3',
            'uiautomation', 'comtypes', 'pycaw', 'pystray', 'playwright',
        } or raiz.startswith('win32') or fullname == 'PIL.ImageGrab':
            bloquear('import ' + fullname)()


def instalar():
    global _instalada
    if _instalada:
        return
    # Falhar se o app já foi importado: SIMULADO é decidido durante o import.
    if any(n == 'app' or n.startswith('app.') for n in sys.modules):
        raise RuntimeError('A barreira deve ser instalada antes de importar app')
    _instalada = True
    os.environ['MESTRE_SIMULAR'] = '1'
    # urllib3 testa IPv6 abrindo um socket ao importar. Não consultar hardware/rede.
    socket.has_ipv6 = False
    for modulo, nomes in (
        (subprocess, ('run', 'call', 'check_call', 'check_output')),
        (os, ('startfile', 'system', 'popen', 'kill', '_exit', 'spawnl', 'spawnv', 'spawnve', 'spawnle')),
        (webbrowser, ('open', 'open_new', 'open_new_tab')),
        (socket.socket, ('connect', 'connect_ex', 'bind', 'sendto')),
        (_tkinter, ('create',)),
    ):
        for nome in nomes:
            if hasattr(modulo, nome):
                setattr(modulo, nome, bloquear(f'{getattr(modulo, "__name__", "socket")}.{nome}'))
    sys.meta_path.insert(0, _SemBibliotecasNativas())
    subprocess.Popen.__init__ = bloquear('subprocess.Popen')

    # Também cobre referências capturadas antes de um monkeypatch e loaders ctypes.
    def auditar(evento, args):
        if (evento in {'subprocess.Popen', 'os.system', 'os.startfile', 'os.startfile/2',
                       'os.posix_spawn', 'os.exec', 'os.spawn', 'ctypes.dlopen',
                       'ctypes.dlsym', 'socket.connect', 'socket.bind', 'socket.sendto'}):
            bloquear(evento)()
    sys.addaudithook(auditar)
