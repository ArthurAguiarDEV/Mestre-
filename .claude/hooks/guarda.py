"""Hook PreToolUse (Bash/PowerShell): bloqueia comandos destrutivos antes de rodar.
Sai com codigo 2 = bloqueado; a mensagem volta para o Claude pedir confirmacao ao usuario."""
import json
import re
import sys

PERIGOSOS = [
    r"\brm\s+-\w*r\w*f|\brm\s+-\w*f\w*r",
    r"git\s+push\s+.*(--force|-f\b)",
    r"git\s+reset\s+--hard",
    r"git\s+clean\s+-\w*f",
    r"Remove-Item\b.*-Recurse",
    r"\b(rd|rmdir)\s+/s",
    r"\bformat\s+[a-z]:",
]

dados = json.load(sys.stdin)
cmd = dados.get("tool_input", {}).get("command", "")
for padrao in PERIGOSOS:
    if re.search(padrao, cmd, re.IGNORECASE):
        print(f"Bloqueado pelo hook guarda.py ({padrao}). Peca confirmacao ao usuario antes.", file=sys.stderr)
        sys.exit(2)
sys.exit(0)
