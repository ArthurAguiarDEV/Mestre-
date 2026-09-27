"""Mestre - assistente pessoal por voz."""
import os

if os.environ.get("MESTRE_SIMULAR") == "1":
    # Teste automatico: toda janela tkinter (painel, indicador, dialogos) nasce invisivel e sem
    # botao na barra de tarefas. Os widgets continuam funcionando para o teste clicar e ler.
    import tkinter as _tk

    def _esconder(janela):
        try:
            janela.wm_attributes("-alpha", 0.0)
            janela.wm_attributes("-toolwindow", True)
        except _tk.TclError:
            pass

    _tk_init, _top_init = _tk.Tk.__init__, _tk.Toplevel.__init__

    def _tk_novo(self, *a, **k):
        _tk_init(self, *a, **k)
        _esconder(self)

    def _top_novo(self, *a, **k):
        _top_init(self, *a, **k)
        _esconder(self)

    _tk.Tk.__init__, _tk.Toplevel.__init__ = _tk_novo, _top_novo
