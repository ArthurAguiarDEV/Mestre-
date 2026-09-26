"""Hook PostToolUse do projeto Mestre: confere o arquivo que o Claude acabou de gravar.

Transforma regras do CLAUDE.md em verificacao automatica:
  - .bat/.vbs: quebra de linha CRLF e texto sem acentos
  - extensao do Brave: versao do manifest.json igual a ponte.VERSAO_EXTENSAO
  - .py: sem erro de sintaxe
Saida 2 = o Claude recebe a mensagem e corrige. Saida 0 = tudo certo.
Nao usa bibliotecas de fora (roda com o Python do Windows, via "py -3").
"""
import json
import py_compile
import re
import sys
from pathlib import Path

PROJETO = Path(__file__).resolve().parents[2]


def avisar(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(2)


def main() -> None:
    try:
        dados = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return
    caminho = (dados.get("tool_input") or {}).get("file_path") or ""
    if not caminho:
        return
    arq = Path(caminho)
    if not arq.is_absolute():
        arq = PROJETO / arq
    if not arq.is_file():
        return
    nome = arq.name.lower()

    if nome.endswith((".bat", ".vbs")):
        b = arq.read_bytes()
        problemas = []
        if re.search(rb"(?<!\r)\n", b):
            problemas.append("quebra de linha LF (precisa ser CRLF)")
        if any(c > 127 for c in b):
            problemas.append("caracteres acentuados/nao-ASCII (o cmd do Windows mostra errado)")
        if problemas:
            avisar(f"[regra do projeto] {arq.name}: " + "; ".join(problemas) +
                   ". Regrave com CRLF e sem acentos (regra dos .bat/.vbs no CLAUDE.md).")

    if nome == "manifest.json" or (nome == "ponte.py" and arq.parent.name == "app"):
        try:
            m = json.loads((PROJETO / "extensao_brave" / "manifest.json").read_text(encoding="utf-8"))
            p = re.search(r'VERSAO_EXTENSAO\s*=\s*"([^"]+)"',
                          (PROJETO / "app" / "ponte.py").read_text(encoding="utf-8"))
            if p and m.get("version") != p.group(1):
                avisar(f"[regra do projeto] Versao da extensao diferente: manifest.json = {m.get('version')}, "
                       f"ponte.VERSAO_EXTENSAO = {p.group(1)}. Suba as duas juntas.")
        except (OSError, ValueError):
            pass

    if nome.endswith(".py"):
        try:
            py_compile.compile(str(arq), doraise=True, cfile=str(PROJETO / "logs" / "_conferir.pyc"))
        except py_compile.PyCompileError as erro:
            avisar(f"[regra do projeto] Erro de sintaxe em {arq.name}:\n{erro.msg}")
        except OSError:
            pass


if __name__ == "__main__":
    main()
