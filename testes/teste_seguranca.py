"""Regressões sem hardware. Ramo de produção só roda com doubles nas saídas."""
import ast
import ctypes
import importlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
import webbrowser

from testes.seguranca import EfeitoRealBloqueado, tentativas
from app import navegador, ponte, sistema


def inventario():
    encontrados = []
    raiz = Path(__file__).resolve().parents[1]
    for arquivo in sorted((raiz / 'app').rglob('*.py')):
        for no in ast.walk(ast.parse(arquivo.read_text(encoding='utf-8'))):
            if not isinstance(no, ast.Call):
                continue
            chamada = ast.unparse(no.func)
            if (chamada.startswith(('subprocess.', 'webbrowser.'))
                    or chamada in {'os.startfile', '_os.startfile', 'os.system', 'os.popen'}
                    or chamada.endswith('.launch_persistent_context')):
                encontrados.append(f'{arquivo.relative_to(raiz).as_posix()}:{chamada}')
    return sorted(encontrados)


class Seguranca(unittest.TestCase):
    def setUp(self):
        self.inicio = len(tentativas)

    def tearDown(self):
        self.assertEqual(tentativas[self.inicio:], [], 'Houve tentativa de efeito real')

    def test_barreira_antes_do_app(self):
        self.assertEqual(os.environ['MESTRE_SIMULAR'], '1')
        self.assertTrue(sistema.SIMULADO)

    def test_barreira_bloqueia_antes_do_efeito(self):
        import tkinter
        chamadas = [
            lambda: webbrowser.open('https://example.com'),
            lambda: subprocess.Popen(['brave.exe']),
            lambda: subprocess.run(['cmd', '/c', 'start']),
            lambda: os.system('start https://example.com'),
            lambda: ctypes.CDLL('user32.dll'),
            lambda: tkinter.Tk(),
            lambda: importlib.import_module('sounddevice'),
            lambda: importlib.import_module('PySide6'),
            lambda: importlib.import_module('pyautogui'),
            lambda: importlib.import_module('playwright'),
        ]
        if hasattr(os, 'startfile'):
            chamadas.append(lambda: os.startfile('https://example.com'))
        with socket.socket() as sock:
            chamadas.append(lambda: sock.connect(('127.0.0.1', 47632)))
            for chamar in chamadas:
                with self.subTest(chamar=chamar):
                    antes = len(tentativas)
                    with self.assertRaises(EfeitoRealBloqueado):
                        chamar()
                    self.assertEqual(len(tentativas), antes + 1)
                    del tentativas[antes:]  # somente as violações esperadas deste teste

    def test_sites_simulados_em_ambas_plataformas(self):
        for windows in (False, True):
            for brave in (False, True):
                for monitor in (None, 2):
                    with self.subTest(windows=windows, brave=brave, monitor=monitor), \
                            patch.object(sistema, 'EH_WINDOWS', windows), \
                            patch.object(sistema, 'SITES_NO_BRAVE', brave), \
                            patch.object(sistema, 'MONITOR_ALVO', monitor):
                        for url in ('https://example.com', 'https://youtube.com', 'spotify:track:teste'):
                            sistema.abrir_site(url)

    def test_brave_youtube_direto_e_extensao(self):
        p = ponte.Ponte()
        p.ultimo_contato = ponte.time.time()
        for exe in (None, 'brave.exe', 'msedge.exe'):
            for yt in (navegador.YouTubeNoNavegadorNormal(exe),
                       navegador.YouTubeNoBraveComExtensao(exe, p)):
                for monitor in (None, 2):
                    with patch.object(sistema, 'MONITOR_ALVO', monitor):
                        yt.abrir('https://youtube.com/watch?v=teste', {'numero': 2})
                        yt.proximo()
                        yt.pausar(False)
                        yt.tela_cheia(True)
                        yt.modo_cinema()
                        yt.legenda()
                        yt.volume_video('mudo')
                        yt.pular(10)
                        yt.like()
                        yt.chat(True)
                        self.assertEqual(yt.resultados(), [])

    def test_playwright_nao_inicia_nem_executa_callback(self):
        nav = navegador.Navegador()
        callback = Mock()
        nav.rodar(callback)
        callback.assert_not_called()
        nav._laco()
        nav.abrir('https://youtube.com', {'numero': 2})
        nav.tecla('f')
        nav.js('video.play()')
        nav.janela_tela_cheia(True)
        nav._levar_para(Mock(), {'numero': 2})
        self.assertIsNone(nav._linha)
        self.assertIsNone(nav._ctx)
        with self.assertRaisesRegex(RuntimeError, 'simulacao'):
            nav._garantir_pagina()

    def test_ponte_nao_conecta_nem_enfileira(self):
        p = ponte.Ponte()
        p.ultimo_contato = ponte.time.time()
        self.assertFalse(p.iniciar())
        self.assertFalse(p.conectada())
        for acao in ('abrir', 'focar_youtube', 'separar', 'juntar', 'continuar', 'volume'):
            self.assertIsNone(p.pedir(acao, 'teste', aba=1))
        self.assertTrue(p._fila.empty())
        self.assertIsNone(p._servidor)
        self.assertFalse(ponte.extensao_conectada())
        self.assertEqual(ponte.versao_da_extensao(), '')

    def test_producao_ponte_preserva_protocolo_com_doubles(self):
        p = ponte.Ponte()
        p.ultimo_contato = ponte.time.time()
        p._respostas[1] = {'resultado': 'ok'}
        evento = Mock()
        evento.wait.return_value = True
        with patch.object(sistema, 'SIMULADO', False), patch.object(ponte.threading, 'Event', return_value=evento):
            self.assertTrue(p.conectada())
            self.assertEqual(p.pedir('abrir', 'https://youtube.com', aba=7), 'ok')
        self.assertEqual(p._fila.get_nowait(), {'id': 1, 'acao': 'abrir', 'arg': 'https://youtube.com', 'aba': 7})
        self.assertEqual(p._eventos, {})

    def test_sistema_sem_processos_janelas_teclas_mouse(self):
        self.assertTrue(sistema.abrir_programa('spotify'))
        sistema.abrir_arquivo('arquivo.txt')
        sistema.mostrar_na_pasta('arquivo.txt')
        sistema.abrir_painel()
        sistema.abrir_revisao_ditado()
        sistema.iniciar_mestre()
        sistema.reiniciar_mestre()
        sistema.parar_mestre()
        self.assertFalse(sistema.mestre_ligado())
        sistema.parar_pid('123')
        self.assertIn('simulado', sistema.rodar_comando('abrir youtube'))
        sistema.abrir_terminal_com('echo teste', '.', 'teste')
        sistema.abrir_com_comando(['cmd'], '.')
        sistema.abrir_app_claude()
        sistema.preparar_janela_do_claude()
        sistema.atalho('ctrl', 't')
        sistema.tecla_letra('f')
        sistema.midia('tocar_pausar')
        sistema.volume('aumentar')
        sistema.volume_do_pc(50)
        sistema.colar_e_enviar('teste')
        sistema.copiar('teste')
        sistema.clicar_e_colar_na_janela_ativa('teste')
        sistema.trazer_para_frente(123)
        sistema._trazer_para_frente(123)
        sistema._clicar_na_caixa_de_mensagem(123, 90)
        sistema._posicionar_janela_nova(123, 2)
        sistema.mover_janela_para_monitor(123, 2)
        self.assertEqual(sistema.monitores(), [])
        self.assertEqual(sistema._janelas_visiveis(), [])
        self.assertEqual(sistema.janela_da_frente(), 0)
        self.assertIsNone(sistema.monitor_do_mouse())

    def test_selecao_youtube_em_todos_os_modos(self):
        from app.comandos.video import VideoMixin
        for modo in ('normal', 'extensao', 'controlado'):
            ex = VideoMixin()
            ex.cfg = {'youtube': {'modo': modo, 'navegador': 'brave'}}
            ex.voz = Mock()
            with self.subTest(modo=modo), patch.object(navegador, 'caminho_do_brave', return_value='brave.exe'):
                self.assertIsNotNone(ex._yt())
                ex._abrir_youtube('https://youtube.com')

    def test_producao_sites_preserva_chamadas_com_doubles(self):
        with patch.object(sistema, 'SIMULADO', False), \
                patch.object(sistema, 'janela_da_frente', return_value=123), \
                patch.object(sistema, '_janelas_visiveis', return_value=[]), \
                patch.object(sistema, 'depois_de_abrir') as posicionar, \
                patch.object(navegador, 'caminho_do_brave', return_value='brave.exe'), \
                patch.object(navegador, 'perfil_do_brave', return_value='Profile 1'), \
                patch.object(subprocess, 'Popen') as popen, \
                patch.object(webbrowser, 'open') as abrir:
            for monitor in (None, 2):
                with patch.object(sistema, 'MONITOR_ALVO', monitor), patch.object(sistema, 'SITES_NO_BRAVE', True):
                    sistema.abrir_site('https://example.com')
                    esperado = ['brave.exe', '--profile-directory=Profile 1']
                    if monitor:
                        esperado.append('--new-window')
                    popen.assert_called_with(esperado + ['https://example.com'])
                    posicionar.assert_called_with(123)
            with patch.object(sistema, 'SITES_NO_BRAVE', False), patch.object(sistema, 'MONITOR_ALVO', None):
                sistema.abrir_site('https://example.com')
                abrir.assert_called_with('https://example.com', new=2)
                sistema.abrir_site('spotify:track:teste')
                abrir.assert_called_with('spotify:track:teste')

    def test_producao_brave_direto_com_doubles(self):
        with patch.object(sistema, 'SIMULADO', False), \
                patch.object(sistema, 'janela_da_frente', return_value=123), \
                patch.object(sistema, 'depois_de_abrir') as posicionar, \
                patch.object(navegador, 'perfil_do_brave', return_value=''), \
                patch.object(subprocess, 'Popen') as popen:
            navegador.YouTubeNoNavegadorNormal('brave.exe').abrir('https://youtube.com')
            popen.assert_called_once_with(['brave.exe', '--new-window', 'https://youtube.com'])
            posicionar.assert_called_once_with(123)

    def test_producao_playwright_com_contexto_falso(self):
        nav = navegador.Navegador('msedge')
        nav._pw = Mock()
        pagina = Mock()
        nav._pw.chromium.launch_persistent_context.return_value.pages = [pagina]
        with tempfile.TemporaryDirectory() as pasta, \
                patch.object(sistema, 'SIMULADO', False), \
                patch.object(navegador, 'PASTA_PERFIL', Path(pasta)), \
                patch.dict(os.environ, {'MESTRE_NAVEGADOR_EXE': ''}):
            self.assertIs(nav._garantir_pagina(), pagina)
            opcoes = nav._pw.chromium.launch_persistent_context.call_args.kwargs
            self.assertEqual(opcoes['channel'], 'msedge')
            self.assertFalse(opcoes['headless'])

    def test_inventario_de_saidas_revisado(self):
        esperado = json.loads(Path(__file__).with_name('saidas_reais.json').read_text(encoding='utf-8'))
        self.assertEqual(inventario(), esperado, 'Nova saída real: revisar barreira e inventário')


if __name__ == '__main__':
    unittest.main()
