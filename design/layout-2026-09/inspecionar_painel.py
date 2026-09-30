"""Prévia do painel existente com dados de exemplo, isolada do Mestre instalado."""
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

with tempfile.TemporaryDirectory(prefix="mestre_inspecao_layout_") as temporary:
    sandbox = Path(temporary)
    shutil.copytree(ROOT / "app", sandbox / "app", ignore=shutil.ignore_patterns("__pycache__"))
    for name in ("config.exemplo.yaml", "vocabulario.yaml", "ROTEIRO_VALIDACAO.md"):
        shutil.copy2(ROOT / name, sandbox / name)
    shutil.copy2(sandbox / "config.exemplo.yaml", sandbox / "config.yaml")
    (sandbox / "logs").mkdir()
    (sandbox / "profile").mkdir()
    os.environ["MESTRE_SIMULAR"] = "1"
    os.environ["APPDATA"] = str(sandbox / "profile")
    os.chdir(sandbox)
    sys.path.insert(0, str(sandbox))
    from app import painel, tema

    painel.escutar_chamados = lambda janela: None
    tema.posicao_janela = lambda x, y: (x, y)
    window = painel.Painel()
    window.wm_attributes("-alpha", 1.0)
    window.wm_attributes("-toolwindow", False)
    window.title("Mestre — referência visual isolada")
    window.protocol("WM_DELETE_WINDOW", window.destroy)
    if len(sys.argv) > 1:
        window.mostrar_pagina(sys.argv[1])
    window.after(1800000, window.destroy)
    try:
        window.mainloop()
    finally:
        os.chdir(ROOT)
