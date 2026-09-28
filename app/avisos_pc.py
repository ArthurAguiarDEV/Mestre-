"""Avisos do PC pelo Telegram: quando desliga/reinicia e quando liga de novo.

- (a) Ao Windows desligar ou reiniciar, ele manda "PC desligando" (WM_QUERYENDSESSION, numa janela
  escondida - so existe enquanto o Assessor roda de verdade, nao no modo texto/comando). Grava tambem
  um arquivo de "desligou limpo" com a hora, para o proximo boot saber que foi um desligamento normal.
- (b) Ao iniciar depois de um boot NOVO do Windows (compara com o ultimo registrado, para nao avisar
  so porque o Assessor reiniciou sozinho): manda "PC ligou". Se nao achou a marca de "desligou limpo"
  daquele boot anterior (e/ou o Log de Eventos do Windows mostra queda de energia/travada: eventos 41
  do Kernel-Power ou 6008 do EventLog), avisa que foi um desligamento inesperado.
- (c) Opcional (desligado por padrao, painel > Celular): pulso a cada 5 min pro healthchecks.io, que
  avisa NA HORA (por e-mail/Telegram deles) se o pulso parar de chegar - por exemplo numa queda de
  energia, quando o PC nao teve tempo de avisar nada.

Um "batimento" (logs/pc_batimento.json) e gravado a cada ~1 min enquanto o Assessor esta rodando: e o
"ultimo sinal" usado para dizer quando o PC parou de responder, se o desligamento foi inesperado.
"""
import json
import logging
import subprocess
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from .config import PASTA_LOGS
from . import segredos

log = logging.getLogger(__name__)

ARQUIVO_BATIMENTO = PASTA_LOGS / "pc_batimento.json"
ARQUIVO_DESLIGOU_LIMPO = PASTA_LOGS / "pc_desligou_limpo.json"
TOLERANCIA_MESMO_BOOT_SEG = 5   # GetTickCount64 varia uns milissegundos entre leituras
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)


# --------------------------------------------------------------------------------------
#  Hora do boot atual (ha quanto tempo o Windows esta ligado)
# --------------------------------------------------------------------------------------
def hora_boot() -> datetime:
    """Hora em que o Windows ligou desta vez (agora - tempo ligado)."""
    import ctypes
    tique_ms = ctypes.windll.kernel32.GetTickCount64()
    return datetime.now() - timedelta(milliseconds=tique_ms)


def mesmo_boot(a, b, tolerancia: int = TOLERANCIA_MESMO_BOOT_SEG) -> bool:
    """Duas horas de boot sao "o mesmo boot" se ficam pertinho uma da outra (poucos segundos)."""
    if not a or not b:
        return False
    return abs((a - b).total_seconds()) <= tolerancia


# --------------------------------------------------------------------------------------
#  Arquivos (batimento = ultimo sinal de vida; desligou_limpo = marca do ultimo boot que se despediu)
# --------------------------------------------------------------------------------------
def _ler_json(caminho: Path) -> dict:
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar_json(caminho: Path, dados: dict) -> None:
    try:
        PASTA_LOGS.mkdir(exist_ok=True)
        caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    except OSError as erro:
        log.debug("Nao consegui gravar %s: %s", caminho.name, erro)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _de_iso(texto: str):
    try:
        return datetime.fromisoformat(texto)
    except (TypeError, ValueError):
        return None


def ler_batimento() -> dict:
    """{"hora": datetime do ultimo sinal, "boot": datetime do boot registrado} (None se nunca gravou)."""
    d = _ler_json(ARQUIVO_BATIMENTO)
    return {"hora": _de_iso(d.get("hora")), "boot": _de_iso(d.get("boot"))}


def bater(boot: datetime | None = None) -> None:
    """Grava o "ainda estou vivo" (chamado a cada ~1 min enquanto o Assessor roda)."""
    _gravar_json(ARQUIVO_BATIMENTO, {"hora": _iso(datetime.now()), "boot": _iso(boot or hora_boot())})


def ler_desligou_limpo() -> dict:
    d = _ler_json(ARQUIVO_DESLIGOU_LIMPO)
    return {"boot": _de_iso(d.get("boot")), "hora": _de_iso(d.get("hora"))}


def marcar_desligou_limpo(boot: datetime | None = None) -> None:
    _gravar_json(ARQUIVO_DESLIGOU_LIMPO, {"boot": _iso(boot or hora_boot()), "hora": _iso(datetime.now())})


# --------------------------------------------------------------------------------------
#  Log de Eventos do Windows: queda de energia / travamento (41 Kernel-Power, 6008 EventLog)
# --------------------------------------------------------------------------------------
def houve_queda_no_log(desde: datetime, timeout: float = 6.0) -> bool:
    """True se o Log do Windows tem um evento 41 (Kernel-Power) ou 6008 (EventLog) depois de "desde"
    (sinal de que o PC desligou sem passar pelo jeito normal). Nunca trava: da erro -> assume que nao viu nada."""
    filtro = ("*[System[(EventID=41 or EventID=6008) and TimeCreated[@SystemTime>='"
              + desde.strftime("%Y-%m-%dT%H:%M:%S") + "']]]")
    try:
        r = subprocess.run(
            ["wevtutil", "qe", "System", "/q:" + filtro, "/c:1", "/f:text"],
            capture_output=True, text=True, timeout=timeout, creationflags=SEM_JANELA)
        return bool(r.stdout and r.stdout.strip())
    except Exception as erro:
        log.debug("Nao consegui checar o Log de Eventos: %s", erro)
        return False


# --------------------------------------------------------------------------------------
#  Mandar a mensagem (reusa o envio do Telegram ja usado pelo robo em app/recebidos.py)
# --------------------------------------------------------------------------------------
def avisar_telegram(texto: str, timeout: float = 3.0) -> bool:
    from . import recebidos   # import tardio: evita ciclo (recebidos nao depende deste arquivo)
    chat = segredos.ler("telegram_chat")
    if not chat:
        return False
    try:
        recebidos.enviar_texto(int(chat), texto, timeout=timeout)
        return True
    except Exception as erro:
        log.info("Aviso do PC nao foi mandado pro Telegram: %s", erro)
        return False


def _ligado(cfg: dict) -> bool:
    return bool(((cfg or {}).get("avisos_pc") or {}).get("ligado", True))


# --------------------------------------------------------------------------------------
#  (a) Ao desligar/reiniciar: chamado pela janela escondida (main.py) em WM_QUERYENDSESSION
# --------------------------------------------------------------------------------------
def pulso_desligando(cfg: dict) -> None:
    """Rapido (poucos segundos) e nunca trava o desligamento: grava a marca e tenta avisar."""
    marcar_desligou_limpo()
    if not _ligado(cfg):
        return
    texto = f"💤 PC desligando/reiniciando ({datetime.now():%H:%M})"

    def trabalho():
        avisar_telegram(texto, timeout=3.0)
    t = threading.Thread(target=trabalho, daemon=True)
    t.start()
    t.join(timeout=3.5)   # da uma chance de mandar, mas nunca segura o desligamento por mais que isso


# --------------------------------------------------------------------------------------
#  (b) Ao iniciar: compara o boot atual com o ultimo registrado
# --------------------------------------------------------------------------------------
def decidir_aviso_ligou(boot_atual: datetime, batimento: dict, desligou_limpo: dict,
                         houve_queda: bool = False) -> tuple[str, str]:
    """Funcao pura (facil de testar): devolve (situacao, texto_da_mensagem).

    situacao: "mesmo_boot" (Assessor so reiniciou, nao avisa nada), "primeira_vez" (nunca tinha
    batimento, so comeca a registrar), "normal" (PC ligou depois de um desligamento normal) ou
    "inesperado" (o PC sumiu sem avisar: queda de energia ou travou).
    """
    boot_anterior = batimento.get("boot")
    if boot_anterior is None:
        return "primeira_vez", ""
    if mesmo_boot(boot_atual, boot_anterior):
        return "mesmo_boot", ""
    # boot novo: o desligamento anterior foi limpo?
    marca_bate = mesmo_boot(desligou_limpo.get("boot"), boot_anterior)
    if marca_bate and not houve_queda:
        return "normal", f"✅ PC ligou ({datetime.now():%H:%M})"
    ultimo_sinal = batimento.get("hora")
    if ultimo_sinal:
        quando = f"{ultimo_sinal:%H:%M} de {ultimo_sinal:%d/%m}"
    else:
        quando = "?"
    return "inesperado", ("⚠️ o PC tinha desligado sem avisar (queda de energia ou travou), "
                           f"último sinal às {quando}")


def verificar_ao_iniciar(cfg: dict) -> None:
    """Chamado 1x, logo no comeco do main.py (modo normal, ja com o Telegram configuravel)."""
    boot_atual = hora_boot()
    batimento = ler_batimento()
    desligou_limpo = ler_desligou_limpo()
    houve_queda = False
    boot_anterior = batimento.get("boot")
    ultimo_sinal = batimento.get("hora")
    if boot_anterior is not None and not mesmo_boot(boot_atual, boot_anterior) and ultimo_sinal:
        # boot novo: confere no Log do Windows se teve queda de energia/travamento desde o ultimo sinal
        houve_queda = houve_queda_no_log(ultimo_sinal)
    situacao, texto = decidir_aviso_ligou(boot_atual, batimento, desligou_limpo, houve_queda)
    bater(boot_atual)   # sempre atualiza o batimento pro boot atual (evita reavisar so pq o Assessor reiniciou)
    if situacao in ("normal", "inesperado") and _ligado(cfg) and texto:
        threading.Thread(target=avisar_telegram, args=(texto,), kwargs={"timeout": 8.0}, daemon=True).start()


# --------------------------------------------------------------------------------------
#  Thread que grava o batimento a cada ~1 min enquanto o Assessor esta rodando
# --------------------------------------------------------------------------------------
def iniciar_batimento(rodando) -> None:
    def laco():
        while rodando():
            bater()
            time.sleep(60)
    threading.Thread(target=laco, daemon=True).start()


# --------------------------------------------------------------------------------------
#  (c) Pulso opcional pro healthchecks.io (desligado por padrao)
# --------------------------------------------------------------------------------------
def pulso_healthchecks(cfg: dict) -> bool:
    c = (cfg or {}).get("avisos_pc") or {}
    if not c.get("healthchecks_ligado"):
        return False
    url = str(c.get("healthchecks_url") or "").strip()
    if not url:
        return False
    import requests
    try:
        requests.get(url, timeout=10)
        return True
    except Exception as erro:
        log.debug("Pulso do healthchecks nao foi (sem problema, ele mesmo detecta o silencio): %s", erro)
        return False


def iniciar_pulso_healthchecks(cfg: dict, rodando) -> None:
    if not ((cfg.get("avisos_pc") or {}).get("healthchecks_ligado")):
        return

    def laco():
        while rodando():
            pulso_healthchecks(cfg)
            time.sleep(5 * 60)
    threading.Thread(target=laco, daemon=True).start()


# --------------------------------------------------------------------------------------
#  Janela escondida so para receber WM_QUERYENDSESSION/WM_ENDSESSION (desligar/reiniciar o Windows)
# --------------------------------------------------------------------------------------
def iniciar_vigia_desligamento(cfg: dict) -> None:
    """So funciona no Windows, no modo normal (nao no --texto/--comando). Roda numa thread propria
    com o proprio la�o de mensagens; nao interfere no tkinter/PySide do indicador."""
    import ctypes
    from ctypes import wintypes

    WM_QUERYENDSESSION = 0x0011
    WM_DESTROY = 0x0002
    _avisado = {"feito": False}

    def wndproc(hwnd, msg, wparam, lparam):
        if msg == WM_QUERYENDSESSION and not _avisado["feito"]:
            _avisado["feito"] = True
            try:
                pulso_desligando(cfg)
            except Exception:
                log.exception("Aviso de desligamento falhou")
        return ctypes.windll.user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def laco():
        try:
            WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM)
            proc = WNDPROC(wndproc)

            class WNDCLASS(ctypes.Structure):
                _fields_ = [("style", ctypes.c_uint), ("lpfnWndProc", WNDPROC), ("clsExtra", ctypes.c_int),
                            ("wndExtra", ctypes.c_int), ("hInstance", wintypes.HINSTANCE),
                            ("hIcon", wintypes.HICON), ("hCursor", wintypes.HANDLE),
                            ("hbrBackground", wintypes.HANDLE), ("lpszMenuName", wintypes.LPCWSTR),
                            ("lpszClassName", wintypes.LPCWSTR)]

            wc = WNDCLASS()
            wc.lpfnWndProc = proc
            wc.hInstance = ctypes.windll.kernel32.GetModuleHandleW(None)
            wc.lpszClassName = "AssessorVigiaDesligamento"
            if not ctypes.windll.user32.RegisterClassW(ctypes.byref(wc)):
                log.debug("Nao consegui registrar a janela do vigia de desligamento (classe ja existia?)")
            hwnd = ctypes.windll.user32.CreateWindowExW(
                0, wc.lpszClassName, "Assessor (vigia de desligamento)", 0, 0, 0, 0, 0, None, None, wc.hInstance, None)
            if not hwnd:
                log.info("Vigia de desligamento nao conseguiu criar a janela escondida")
                return
            msg = wintypes.MSG()
            while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
        except Exception:
            log.exception("Vigia de desligamento parou de funcionar")

    threading.Thread(target=laco, daemon=True).start()
