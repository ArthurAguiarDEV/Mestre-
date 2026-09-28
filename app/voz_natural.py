"""Voz NATURAL gratis, na placa de video: Chatterbox multilingue (Resemble AI, licenca MIT).

Mais natural que a Kokoro (entonacao de gente), mas mais pesada: precisa de uma placa NVIDIA
para ficar rapida (no processador funciona, porem devagar). Por isso ela mora num ambiente
SEPARADO (modelos/voz_natural/venv, uns 6 GB com o modelo): as bibliotecas dela (torch...)
nunca mexem nas do Mestre. O Mestre liga o servidor dela (app/voz_natural_servidor.py) sozinho.

Timbre ("voz"): a Chatterbox imita a voz de um audio de referencia de ~10 s. Opcoes:
  antonio / francisca -> o Mestre grava a referencia com a voz da Microsoft (uma vez)
  meu_audio           -> um audio seu (painel > Voz > "Usar um áudio meu")
  padrao              -> a voz que vem com o modelo (sotaque de fora)
Enquanto ela carrega (ou se falhar), o Mestre fala com a Kokoro/Edge.
"""
import json
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

from .config import PASTA_PROJETO

log = logging.getLogger(__name__)
PASTA = PASTA_PROJETO / "modelos" / "voz_natural"
VENV = PASTA / "venv"
REFERENCIAS = PASTA / "referencias"
MARCA = PASTA / "instalado.ok"
PORTA = 47633
PASTA_LOGS = PASTA_PROJETO / "logs"
ARQUIVO_PID = PASTA_LOGS / "voz_natural.pid"   # pid de quem esta rodando (usado ao reinstalar)
PASTA_TRAVA = PASTA_LOGS / "voz_natural.trava"   # mutex entre PROCESSOS (painel e Assessor); mkdir e atomico
VOZES = {"antonio": "Antônio (timbre da voz da Microsoft)", "francisca": "Francisca (timbre da voz da Microsoft)",
         "meu_audio": "Um áudio meu (10 segundos)", "padrao": "Padrão do modelo (sotaque de fora)"}
VOZ_PADRAO = "antonio"
TEXTO_REFERENCIA = ("Oi! Tudo certo por aí? Eu sou o seu assistente e estou aqui para ajudar no que você precisar. "
                    "Pode pedir para abrir um programa, tocar uma música ou pesquisar alguma coisa na internet.")
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
_servidor: subprocess.Popen | None = None
_trava = threading.Lock()
_ultimo_estado = {"quando": 0.0, "dados": {}}


def python_do_ambiente() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def instalado() -> bool:
    return MARCA.exists() and python_do_ambiente().exists()


def tem_placa_nvidia() -> bool:
    return bool(shutil.which("nvidia-smi")) or Path(r"C:\Windows\System32\nvidia-smi.exe").exists()


def placa_serie_50() -> bool:
    """Placa NVIDIA de arquitetura 12.x (RTX 50): precisa do PyTorch feito para CUDA 12.8."""
    try:
        r = subprocess.run(["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"],
                           capture_output=True, text=True, timeout=15, creationflags=NO_WINDOW)
        return any(linha.strip().split(".")[0].isdigit() and int(linha.strip().split(".")[0]) >= 12
                   for linha in r.stdout.splitlines())
    except Exception:
        return False


def _python_base() -> str:
    python = Path(sys.executable)
    if python.name.lower() == "pythonw.exe":
        python = python.with_name("python.exe")
    return str(python)


def instalar(progresso=None) -> str:
    """Cria o ambiente separado e instala tudo (uns 6 GB; 10 a 40 minutos). Devolve "" ou o erro."""
    progresso = progresso or (lambda texto: None)
    PASTA.mkdir(parents=True, exist_ok=True)
    diario = PASTA_PROJETO / "logs" / "voz_natural_instalacao.log"
    diario.parent.mkdir(exist_ok=True)
    if instalado():   # reinstalando: encerra o servidor antigo antes (senao o torch fica preso)
        progresso("Encerrando o servidor antigo...")
        parar(matar_todos=True)
    py = str(python_do_ambiente())
    indice = "https://download.pytorch.org/whl/" + ("cu124" if tem_placa_nvidia() else "cpu")
    passos = [("Criando o ambiente separado...", [_python_base(), "-m", "venv", str(VENV)]),
              ("Atualizando o instalador...", [py, "-m", "pip", "install", "-q", "--upgrade", "pip"]),
              ("Baixando o PyTorch para a " + ("placa de vídeo" if "cu" in indice else "CPU") + " (uns 2,5 GB)...",
               [py, "-m", "pip", "install", "-q", "torch==2.6.0", "torchaudio==2.6.0", "--index-url", indice]),
              ("Instalando a voz Chatterbox...", [py, "-m", "pip", "install", "-q", "chatterbox-tts"])]
    if placa_serie_50():
        # RTX 50 (Blackwell, sm_120): o torch 2.6 (cu124) que a Chatterbox pede nao roda nela ("no kernel
        # image"). Depois da Chatterbox, troca pelo torch 2.8 feito para CUDA 12.8.
        passos.append(("Ajustando o PyTorch para a sua placa RTX 50 (uns 3 GB)...",
                       [py, "-m", "pip", "install", "-q", "--force-reinstall", "--no-deps", "torch==2.8.0",
                        "torchaudio==2.8.0", "--index-url", "https://download.pytorch.org/whl/cu128"]))
    with open(diario, "a", encoding="utf-8") as d:
        for texto, comando in passos:
            if comando[1:3] == ["-m", "venv"] and python_do_ambiente().exists():
                continue
            progresso(texto)
            d.write(f"\n=== {time.strftime('%d/%m/%Y %H:%M')} {texto}\n$ {' '.join(comando)}\n")
            d.flush()
            try:
                r = subprocess.run(comando, capture_output=True, text=True, timeout=3600, creationflags=NO_WINDOW)
            except Exception as erro:
                d.write(f"ERRO: {erro}\n")
                return f"Falhou em “{texto}”: {erro}"
            d.write(r.stdout[-6000:] + r.stderr[-6000:])
            if r.returncode != 0:
                return f"Falhou em “{texto}”. Detalhes em logs/{diario.name}."
    MARCA.write_text(time.strftime("%d/%m/%Y %H:%M"), encoding="utf-8")
    progresso("Baixando o modelo de voz (uns 3 GB) e ligando pela primeira vez...")
    iniciar()
    fim = time.time() + 3600
    while time.time() < fim:
        e = estado(forcar=True)
        if e.get("pronto"):
            placa = "placa de vídeo" if e.get("placa") == "cuda" else "processador (vai ser devagar)"
            progresso(f"Pronta! Rodando no {placa}.")
            return ""
        if e.get("erro"):
            return f"Instalou, mas o modelo não ligou: {e['erro']}"
        time.sleep(3)
    return "O modelo demorou demais para baixar. Tente de novo mais tarde (o que já baixou fica)."


def _adquirir_trava(tempo: float = 10.0) -> bool:
    """Mutex entre PROCESSOS (painel e Assessor podem chamar iniciar() ao mesmo tempo):
    criar uma pasta e atomico no Windows, entao so quem consegue criar "ganha" a vez."""
    PASTA_LOGS.mkdir(parents=True, exist_ok=True)
    fim = time.time() + tempo
    while True:
        try:
            PASTA_TRAVA.mkdir()
            return True
        except FileExistsError:
            try:
                if time.time() - PASTA_TRAVA.stat().st_mtime > 15:
                    PASTA_TRAVA.rmdir()   # trava presa (o processo que a criou morreu): destrava sozinho
                    continue
            except OSError:
                pass
            if time.time() > fim:
                return False
            time.sleep(0.1)


def _soltar_trava() -> None:
    try:
        PASTA_TRAVA.rmdir()
    except OSError:
        pass


def iniciar() -> bool:
    """Liga o servidor da voz (se instalado e ainda desligado). So um por vez, mesmo com o painel
    e o Assessor chamando ao mesmo tempo: a trava de pasta (`_adquirir_trava`) serializa a
    checagem-e-ligacao entre processos, e so solta depois que a porta ja responde (assim quem
    estava esperando a trava encontra o servidor pronto e nao sobe outro)."""
    global _servidor
    if not instalado():
        return False
    with _trava:
        if _servidor and _servidor.poll() is None:
            return True
    if not _adquirir_trava():
        return bool(estado(forcar=True))   # alguem mais esta cuidando disso: confere pela porta mesmo assim
    try:
        if estado(forcar=True):   # ja tem um rodando (deste processo ou de outro: painel, Assessor...)
            return True
        with _trava:
            ambiente = dict(os.environ, HF_HOME=str(PASTA / "hf"), PYTHONIOENCODING="utf-8")
            diario = open(PASTA_PROJETO / "logs" / "voz_natural_servidor.log", "a", encoding="utf-8")
            _servidor = subprocess.Popen([str(python_do_ambiente()), str(PASTA_PROJETO / "app" / "voz_natural_servidor.py"),
                                          str(PORTA), str(os.getpid())], cwd=str(PASTA), env=ambiente,
                                         stdout=diario, stderr=subprocess.STDOUT, creationflags=NO_WINDOW)
            ARQUIVO_PID.write_text(str(_servidor.pid))
        log.info("Voz natural: servidor ligado (carregando o modelo)")
        fim = time.time() + 10
        while time.time() < fim and not estado(forcar=True):
            time.sleep(0.2)
        return True
    finally:
        _soltar_trava()


def parar(matar_todos: bool = False) -> None:
    """Desliga o servidor. matar_todos=True (antes de reinstalar): tambem mata um servidor ligado
    por OUTRO processo (painel ou Assessor), lendo o pid em logs/voz_natural.pid — senao os
    arquivos do torch ficam presos e o pip nao consegue trocar ("Failed to remove ~orch")."""
    global _servidor
    if _servidor and _servidor.poll() is None:
        _servidor.kill()
    _servidor = None
    if not matar_todos:
        return
    if ARQUIVO_PID.exists():
        try:
            pid = int(ARQUIVO_PID.read_text().strip())
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True, creationflags=NO_WINDOW)
            else:
                os.kill(pid, 9)
        except Exception:
            pass
        ARQUIVO_PID.unlink(missing_ok=True)
    fim = time.time() + 10
    while time.time() < fim and estado(forcar=True):
        time.sleep(0.3)


def estado(forcar: bool = False) -> dict:
    """{"pronto", "placa", "erro"} do servidor ({} = desligado). Guarda por 2 s (e chamado a cada fala)."""
    if not forcar and time.time() - _ultimo_estado["quando"] < 2:
        return _ultimo_estado["dados"]
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORTA}/estado", timeout=0.8) as r:
            dados = json.loads(r.read())
    except Exception:
        dados = {}
    _ultimo_estado.update(quando=time.time(), dados=dados)
    return dados


def pronta() -> bool:
    return bool(estado().get("pronto"))


def referencia(voz: str) -> str:
    """O audio de referencia do timbre escolhido ("" = voz padrao do modelo)."""
    if voz == "padrao":
        return ""
    REFERENCIAS.mkdir(parents=True, exist_ok=True)
    if voz == "meu_audio":
        meu = next((a for a in sorted(REFERENCIAS.glob("meu_audio.*"))), None)
        return str(meu) if meu else ""
    arquivo = REFERENCIAS / f"{voz}.mp3"
    if not arquivo.exists():   # grava uma vez com a voz da Microsoft (Edge, gratis)
        import asyncio

        import edge_tts
        nome = {"antonio": "pt-BR-AntonioNeural", "francisca": "pt-BR-FranciscaNeural"}.get(voz, "pt-BR-AntonioNeural")
        parcial = arquivo.with_suffix(".parcial.mp3")
        asyncio.run(edge_tts.Communicate(TEXTO_REFERENCIA, nome).save(str(parcial)))
        parcial.replace(arquivo)
    return str(arquivo)


def usar_meu_audio(caminho: str) -> None:
    """Painel: copia o seu audio (wav/mp3/ogg de uns 10 s) para ser a referencia."""
    REFERENCIAS.mkdir(parents=True, exist_ok=True)
    for velho in REFERENCIAS.glob("meu_audio.*"):
        velho.unlink()
    shutil.copy(caminho, REFERENCIAS / f"meu_audio{Path(caminho).suffix.lower()}")


def gerar(texto: str, voz: str, destino: Path) -> None:
    """Gera a fala em destino (.wav). Se o servidor ainda estiver carregando, falha NA HORA
    (o Mestre fala com a Kokoro/Edge enquanto isso)."""
    if not pronta():
        iniciar()
        raise RuntimeError("voz natural ainda carregando")
    corpo = json.dumps({"texto": texto, "referencia": referencia(voz), "destino": str(destino)}).encode("utf-8")
    pedido = urllib.request.Request(f"http://127.0.0.1:{PORTA}/falar", data=corpo, method="POST",
                                    headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(pedido, timeout=60) as r:
        resposta = json.loads(r.read())
    if not resposta.get("ok") or not destino.exists():
        raise RuntimeError(resposta.get("erro") or "a voz natural não gerou o áudio")
