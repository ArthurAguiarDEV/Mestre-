"""Hook Stop do projeto Mestre: roda o teste automatico antes do Claude encerrar.

So roda se algum arquivo de codigo mudou desde o ultimo teste que passou
(marcador em logs/.ultimo_teste_ok), entao perguntas simples nao custam nada.
Se algo FALHOU, devolve os itens ao Claude (saida 2) e ele continua corrigindo.
Para desligar numa sessao: defina MESTRE_SEM_TESTE_AUTO=1.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJETO = Path(__file__).resolve().parents[2]
MARCADOR = PROJETO / "logs" / ".ultimo_teste_ok"
VIGIAR = [("app", "*.py"), ("testes", "*.py"), ("extensao_brave", "*"), (".", "vocabulario.yaml")]


def mais_recente() -> float:
    t = 0.0
    for pasta, padrao in VIGIAR:
        base = PROJETO / pasta
        if not base.exists():
            continue
        arquivos = [base / padrao] if (base / padrao).is_file() else base.rglob(padrao)
        for a in arquivos:
            if a.is_file() and "__pycache__" not in a.parts:
                t = max(t, a.stat().st_mtime)
    return t


def main() -> None:
    try:
        dados = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        dados = {}
    if os.environ.get("MESTRE_SEM_TESTE_AUTO") == "1":
        return
    if dados.get("stop_hook_active"):
        return  # ja bloqueamos uma vez nesta resposta: nao entrar em laco
    if MARCADOR.exists() and mais_recente() <= MARCADOR.stat().st_mtime:
        return  # nada de codigo mudou desde o ultimo teste bom
    python = PROJETO / "venv" / "Scripts" / "python.exe"
    if not python.exists():
        return
    try:
        r = subprocess.run([str(python), "-m", "testes.teste_basico"], cwd=str(PROJETO), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=840,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    except subprocess.TimeoutExpired:
        print("[teste automatico] Passou de 14 minutos e foi interrompido. Rode manualmente: "
              "venv\\Scripts\\python -m testes.teste_basico", file=sys.stderr)
        sys.exit(2)
    saida = (r.stdout or "") + (r.stderr or "")
    falhas = [l.strip() for l in saida.splitlines() if "FALHOU" in l]
    if r.returncode != 0 or falhas:
        resumo = "\n".join(falhas[:30]) or "\n".join(saida.splitlines()[-30:])
        print("[teste automatico] Antes de encerrar, corrija o que falhou (ou explique por que nao da):\n" + resumo,
              file=sys.stderr)
        sys.exit(2)
    MARCADOR.parent.mkdir(exist_ok=True)
    MARCADOR.write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")


if __name__ == "__main__":
    main()
