"""Atualiza o Mestre a partir do .zip que o Claude manda (botao na Central).

Nunca mexe no que e SEU: config.yaml, aprendido.yaml, MELHORIAS.md, notas,
respostas, logs, modelos e o venv. Guarda uma copia de seguranca do que trocar.
"""
import subprocess
import sys
import time
import zipfile
from pathlib import Path

from .config import PASTA_PROJETO

PROTEGIDOS = {"config.yaml", "aprendido.yaml", "MELHORIAS.md", "mestre.pid"}
PASTAS_PROTEGIDAS = {"venv", "modelos", "logs", "notas", "respostas", "memoria", "navegador_mestre", "exportacoes", "recebidos",
                     ".git"}
PASTAS_SO_NOVOS = {"perfis"}   # instrucoes dos perfis: voce pode ter editado; so entram arquivos novos


def _prefixo(nomes: list[str]) -> str:
    """O zip pode vir com uma pasta por fora (mestre/app/...) ou direto (app/...)."""
    for n in nomes:
        if n.endswith("app/main.py"):
            return n[: -len("app/main.py")]
    return ""


def verificar(caminho) -> str:
    """Devolve o problema do arquivo, ou "" se ele e mesmo uma atualizacao do Mestre."""
    try:
        with zipfile.ZipFile(caminho) as z:
            nomes = z.namelist()
    except (zipfile.BadZipFile, OSError) as erro:
        return f"Não consegui abrir o arquivo: {erro}"
    if not any(n.endswith("app/main.py") for n in nomes):
        return "Este .zip não parece ser uma atualização do Mestre (não achei app/main.py dentro)."
    return ""


def versao_atual(pasta: Path = PASTA_PROJETO) -> str:
    """A versao instalada (app/versao.py), lida do arquivo: vale mesmo logo depois de atualizar."""
    import re
    try:
        achado = re.search(r'VERSAO\s*=\s*"([^"]+)"', (pasta / "app" / "versao.py").read_text(encoding="utf-8"))
        return achado.group(1) if achado else "?"
    except OSError:
        return "12 ou anterior"


def versao_do_zip(caminho) -> str:
    import re
    try:
        with zipfile.ZipFile(caminho) as z:
            nome = next((n for n in z.namelist() if n.endswith("app/versao.py")), None)
            if nome:
                achado = re.search(r'VERSAO\s*=\s*"([^"]+)"', z.read(nome).decode("utf-8"))
                return achado.group(1) if achado else "?"
    except (zipfile.BadZipFile, OSError):
        pass
    return "?"


def _protegido(relativo: str) -> bool:
    partes = Path(relativo).parts
    return not partes or partes[0] in PASTAS_PROTEGIDAS or relativo in PROTEGIDOS


def aplicar(caminho, pasta: Path = PASTA_PROJETO, instalar_bibliotecas: bool = True) -> str:
    antes = versao_atual(pasta)
    copia = pasta / "logs" / f"antes_da_atualizacao_{time.strftime('%Y%m%d_%H%M%S')}.zip"
    copia.parent.mkdir(exist_ok=True)
    trocados = pulados = 0
    with zipfile.ZipFile(caminho) as z, zipfile.ZipFile(copia, "w", zipfile.ZIP_DEFLATED) as reserva:
        prefixo = _prefixo(z.namelist())
        for info in z.infolist():
            if info.is_dir() or not info.filename.startswith(prefixo):
                continue
            relativo = info.filename[len(prefixo):]
            if ".." in Path(relativo).parts or _protegido(relativo):
                pulados += 1
                continue
            destino = pasta / relativo
            if destino.exists() and Path(relativo).parts[0] in PASTAS_SO_NOVOS:
                pulados += 1
                continue
            if destino.exists():
                reserva.write(destino, relativo)
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(z.read(info))
            trocados += 1
        removidos = _remover_obsoletos(z, prefixo, pasta, reserva)
    depois = versao_atual(pasta)
    resumo = (f"Atualizado da versão {antes} para a {depois}! " if depois not in ("?", antes) else "Atualizado! ") + \
        f"{trocados} arquivos novos ou trocados. Suas configurações ficaram intactas."
    if removidos:
        resumo += f" {removidos} arquivos antigos foram retirados (cópia em logs)."
    if instalar_bibliotecas:
        resumo += "\n" + instalar_requisitos(pasta)
    return resumo


def _remover_obsoletos(z: zipfile.ZipFile, prefixo: str, pasta: Path, reserva: zipfile.ZipFile) -> int:
    """O zip pode trazer OBSOLETOS.txt: arquivos velhos para retirar (um por linha)."""
    try:
        linhas = z.read(prefixo + "OBSOLETOS.txt").decode("utf-8").splitlines()
    except KeyError:
        return 0
    n = 0
    for linha in linhas:
        relativo = linha.strip()
        if not relativo or relativo.startswith("#") or ".." in relativo or _protegido(relativo):
            continue
        alvo = pasta / relativo
        if alvo.is_file():
            reserva.write(alvo, relativo)
            alvo.unlink()
            n += 1
    return n


def instalar_requisitos(pasta: Path = PASTA_PROJETO) -> str:
    """Instala bibliotecas novas do requirements.txt (as que ja existem sao puladas rapido)."""
    python = Path(sys.executable)
    if python.name.lower() == "pythonw.exe":
        python = python.with_name("python.exe")
    try:
        r = subprocess.run([str(python), "-m", "pip", "install", "-q", "-r", str(pasta / "requirements.txt")],
                           cwd=str(pasta), capture_output=True, text=True, timeout=900,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except Exception as erro:
        return f"Não consegui instalar as bibliotecas ({erro}). Rode o ferramentas\\1_instalar.bat."
    if r.returncode != 0:
        return "Não consegui instalar alguma biblioteca nova. Rode o ferramentas\\1_instalar.bat."
    return "Bibliotecas conferidas."
