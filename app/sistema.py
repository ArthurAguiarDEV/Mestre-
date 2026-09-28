"""Acoes no Windows: teclas, volume, tela, abrir programas e sites.

Fora do Windows (so para testes) as acoes apenas aparecem no log.
"""
import logging
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

EH_WINDOWS = sys.platform == "win32"
# MESTRE_SIMULAR=1 (usado pelo teste automatico): as acoes so aparecem no diario, nada abre de verdade
SIMULADO = not EH_WINDOWS or os.environ.get("MESTRE_SIMULAR") == "1"
log = logging.getLogger(__name__)

if EH_WINDOWS:
    import ctypes

    user32 = ctypes.windll.user32

# Codigos de teclas do Windows
VK_VOLUME_MUTE = 0xAD
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_RETURN = 0x0D
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002


def _tecla(codigo: int, vezes: int = 1) -> None:
    if SIMULADO:
        log.info("[simulado] tecla %s x%d", hex(codigo), vezes)
        return
    # Teclas de midia e volume sao "estendidas": sem essa marca alguns programas (Spotify) ignoram
    extra = 0x0001 if 0xA6 <= codigo <= 0xB7 else 0
    varredura = user32.MapVirtualKeyW(codigo, 0)
    for _ in range(vezes):
        user32.keybd_event(codigo, varredura, extra, 0)
        user32.keybd_event(codigo, varredura, extra | KEYEVENTF_KEYUP, 0)
        time.sleep(0.02)


def volume(acao: str, vezes: int = 5) -> None:
    # Cada toque muda o volume em 2%.
    if acao == "aumentar":
        _tecla(VK_VOLUME_UP, vezes)
    elif acao == "diminuir":
        _tecla(VK_VOLUME_DOWN, vezes)
    elif acao == "maximo":
        _tecla(VK_VOLUME_UP, 50)
    elif acao == "mudo":
        _tecla(VK_VOLUME_MUTE)


def play_pause() -> None:
    _tecla(VK_MEDIA_PLAY_PAUSE)


def midia(acao: str) -> None:
    """acao: "tocar_pausar" | "proxima" | "anterior" | "parar" (vale para Spotify, YouTube e outros players)."""
    _tecla({"tocar_pausar": VK_MEDIA_PLAY_PAUSE, "proxima": 0xB0, "anterior": 0xB1, "parar": 0xB2}[acao])


def _pycaw():
    try:
        from pycaw.pycaw import AudioUtilities
        return AudioUtilities
    except Exception as erro:
        log.info("pycaw indisponivel (%s): volume por programa desligado", erro)
        return None


def volume_do_programa(processo: str, acao: str, quanto: float = 0.1) -> str:
    """Muda o volume SO de um programa (ex.: Spotify.exe) no mixer do Windows.

    acao: "aumentar" | "diminuir" | "definir" (quanto = 0..1). Devolve "" se deu certo ou o motivo.
    """
    if SIMULADO:
        log.info("[simulado] volume de %s: %s %.2f", processo, acao, quanto)
        return ""
    au = _pycaw()
    if au is None:
        return "sem_biblioteca"
    try:
        import comtypes
        comtypes.CoInitialize()   # obrigatorio fora da linha principal (a escuta roda em outra linha)
    except Exception:
        pass
    achou = False
    try:
        for sessao in au.GetAllSessions():
            if sessao.Process and sessao.Process.name().lower() == processo.lower():
                vol = sessao.SimpleAudioVolume
                if acao in ("mudo", "som"):
                    vol.SetMute(1 if acao == "mudo" else 0, None)
                else:
                    atual = vol.GetMasterVolume()
                    novo = quanto if acao == "definir" else atual + (quanto if acao == "aumentar" else -quanto)
                    vol.SetMute(0, None)
                    vol.SetMasterVolume(max(0.0, min(1.0, novo)), None)
                    global ULTIMO_NIVEL
                    ULTIMO_NIVEL = max(0.0, min(1.0, novo))
                achou = True
    except Exception as erro:
        log.exception("Volume do programa falhou")
        return f"erro: {erro}"
    return "" if achou else "nao_tocando"


def volume_do_pc(porcento: int) -> None:
    """Volume do Windows num valor exato (0 a 100)."""
    if SIMULADO:
        log.info("[simulado] volume do PC em %d%%", porcento)
        return
    au = _pycaw()
    if au is not None:
        try:
            import comtypes
            comtypes.CoInitialize()
            au.GetSpeakers().EndpointVolume.SetMasterVolumeLevelScalar(max(0, min(100, porcento)) / 100, None)
            return
        except Exception:
            pass
    _tecla(VK_VOLUME_DOWN, 50)          # sem a biblioteca: zera e sobe de 2 em 2
    _tecla(VK_VOLUME_UP, max(0, min(100, porcento)) // 2)


# --- Monitores ---------------------------------------------------------------------------
ULTIMO_NIVEL: float | None = None    # volume_do_programa guarda aqui o nivel novo (0..1), para ele falar
MONITOR_ALVO: int | None = None     # o Executor define por comando ("... no monitor 2"); None = padrao
SEMPRE_NO_PRINCIPAL = True          # painel > Programas e sites > Monitores
SITES_NO_BRAVE = True               # painel > Programas e sites: abrir sites no Brave


MARCAS_MONITOR = {"GSM": "LG", "LGD": "LG", "AOC": "AOC", "SAM": "Samsung", "SEC": "Samsung", "DEL": "Dell",
                  "ACR": "Acer", "ASU": "ASUS", "AUS": "ASUS", "BNQ": "BenQ", "HWP": "HP", "HPN": "HP",
                  "LEN": "Lenovo", "PHL": "Philips", "MSI": "MSI", "GBT": "Gigabyte", "VSC": "ViewSonic",
                  "XMI": "Xiaomi", "HKC": "HKC", "PNR": "Pichau", "AUO": "AUO", "BOE": "BOE"}


def _marca_e_hz(dispositivo: str) -> tuple[str, int]:
    """Marca (pelo codigo do fabricante que o Windows guarda) e taxa de atualizacao (Hz)."""
    from ctypes import wintypes

    class DISPLAY_DEVICE(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("DeviceName", wintypes.WCHAR * 32), ("DeviceString", wintypes.WCHAR * 128),
                    ("StateFlags", wintypes.DWORD), ("DeviceID", wintypes.WCHAR * 128), ("DeviceKey", wintypes.WCHAR * 128)]

    class DEVMODE(ctypes.Structure):
        _fields_ = [("dmDeviceName", wintypes.WCHAR * 32), ("dmSpecVersion", wintypes.WORD), ("dmDriverVersion", wintypes.WORD),
                    ("dmSize", wintypes.WORD), ("dmDriverExtra", wintypes.WORD), ("dmFields", wintypes.DWORD),
                    ("dmPositionX", wintypes.LONG), ("dmPositionY", wintypes.LONG), ("dmDisplayOrientation", wintypes.DWORD),
                    ("dmDisplayFixedOutput", wintypes.DWORD), ("dmColor", ctypes.c_short), ("dmDuplex", ctypes.c_short),
                    ("dmYResolution", ctypes.c_short), ("dmTTOption", ctypes.c_short), ("dmCollate", ctypes.c_short),
                    ("dmFormName", wintypes.WCHAR * 32), ("dmLogPixels", wintypes.WORD), ("dmBitsPerPel", wintypes.DWORD),
                    ("dmPelsWidth", wintypes.DWORD), ("dmPelsHeight", wintypes.DWORD), ("dmDisplayFlags", wintypes.DWORD),
                    ("dmDisplayFrequency", wintypes.DWORD)]
    marca, hz = "", 0
    try:
        dd = DISPLAY_DEVICE()
        dd.cb = ctypes.sizeof(DISPLAY_DEVICE)
        if user32.EnumDisplayDevicesW(dispositivo, 0, ctypes.byref(dd), 0):
            partes = dd.DeviceID.split("\\")          # MONITOR\GSM5B7F\{...}
            codigo = partes[1][:3].upper() if len(partes) > 1 else ""
            marca = MARCAS_MONITOR.get(codigo, "")
            if not marca and "generic" not in dd.DeviceString.lower() and "gen" not in dd.DeviceString.lower()[:4]:
                marca = dd.DeviceString
        dm = DEVMODE()
        dm.dmSize = ctypes.sizeof(DEVMODE)
        if user32.EnumDisplaySettingsW(dispositivo, -1, ctypes.byref(dm)):   # -1 = configuracao atual
            hz = int(dm.dmDisplayFrequency)
    except Exception as erro:
        log.info("Nao consegui ler nome/Hz do monitor: %s", erro)
    return marca, hz


def monitores() -> list[dict]:
    """Monitores do PC: 1 = principal; depois os de maior Hz; empate: da esquerda para a direita.

    Cada um: {"numero", "x", "y", "largura", "altura", "marca", "hz", "descricao"} (area util, sem a barra).
    """
    if not EH_WINDOWS:
        return []
    from ctypes import wintypes

    class INFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                    ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD), ("szDevice", wintypes.WCHAR * 32)]
    achados = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(wintypes.RECT), wintypes.LPARAM)
    def cada(hmon, _hdc, _ret, _):
        info = INFO()
        info.cbSize = ctypes.sizeof(INFO)
        user32.GetMonitorInfoW(hmon, ctypes.byref(info))
        r = info.rcWork
        marca, hz = _marca_e_hz(info.szDevice)
        achados.append({"principal": bool(info.dwFlags & 1), "x": r.left, "y": r.top,
                        "largura": r.right - r.left, "altura": r.bottom - r.top, "marca": marca, "hz": hz})
        return True
    user32.EnumDisplayMonitors(None, None, cada, 0)
    achados.sort(key=lambda m: (not m["principal"], -m["hz"], m["x"]))
    for i, m in enumerate(achados, 1):
        m["numero"] = i
        m["descricao"] = " ".join(x for x in (m["marca"], f"{m['hz']} Hz" if m["hz"] else "") if x) or "monitor"
    return achados


def monitor(numero: int | None) -> dict | None:
    lista = monitores()
    if not lista:
        return None
    return next((m for m in lista if m["numero"] == numero), lista[0])


def mover_janela_para_monitor(hwnd: int, numero: int | None, maximizar: bool = True) -> bool:
    if SIMULADO:
        log.info("[simulado] janela para o monitor %s", numero)
        return True
    m = monitor(numero)
    if not m or not hwnd:
        return False
    user32.ShowWindow(hwnd, 9)   # restaura (maximizada nao muda de monitor)
    user32.SetWindowPos(hwnd, 0, m["x"] + 40, m["y"] + 40, max(800, m["largura"] - 80),
                        max(600, m["altura"] - 80), 0x0004 | 0x0040)   # SWP_NOZORDER | SWP_SHOWWINDOW
    if maximizar:
        user32.ShowWindow(hwnd, 3)
    return True


def _monitor_desejado() -> int | None:
    """O monitor deste comando (ou o principal, se estiver marcado no painel)."""
    if MONITOR_ALVO:
        return MONITOR_ALVO
    return 1 if SEMPRE_NO_PRINCIPAL else None


def _posicionar_janela_nova(antes: int, numero: int, espera: float = 6.0) -> None:
    """Espera a janela que acabou de abrir aparecer na frente e leva para o monitor pedido."""
    fim = time.time() + espera
    while time.time() < fim:
        atual = user32.GetForegroundWindow()
        if atual and atual != antes:
            time.sleep(0.4)   # deixa a janela terminar de abrir
            mover_janela_para_monitor(user32.GetForegroundWindow(), numero)
            return
        time.sleep(0.15)


def depois_de_abrir(antes: int | None) -> None:
    """Chamado logo apos abrir algo: posiciona em segundo plano (nao atrasa a resposta)."""
    numero = _monitor_desejado()
    if SIMULADO or not EH_WINDOWS or not numero or len(monitores()) < 2 and not MONITOR_ALVO:
        if numero and SIMULADO:
            log.info("[simulado] abrir no monitor %s", numero)
        return
    import threading as _th
    _th.Thread(target=_posicionar_janela_nova, args=(antes or 0, numero), daemon=True).start()


def janela_da_frente() -> int:
    return user32.GetForegroundWindow() if EH_WINDOWS else 0


# --- Janelas e atalhos de teclado ------------------------------------------------------
TECLAS = {"alt": 0x12, "ctrl": 0x11, "shift": 0x10, "win": 0x5B, "tab": 0x09, "f4": 0x73, "f5": 0x74,
          "f11": 0x7A, "esquerda": 0x25, "direita": 0x27, "t": 0x54, "w": 0x57, "d": 0x44, "pgdn": 0x22,
          "pgup": 0x21, "home": 0x24, "end": 0x23, "mais": 0xBB, "menos": 0xBD, "0": 0x30, "esc": 0x1B,
          "n": 0x4E}


def tecla_letra(letra: str) -> None:
    """Aperta uma letra (a-z) na janela da frente (atalhos do YouTube: f, t, c, j, l)."""
    if SIMULADO:
        log.info("[simulado] tecla %s", letra)
        return
    _tecla(ord(letra.upper()))


def atalho(*nomes: str) -> None:
    """Aperta uma combinacao, ex.: atalho("ctrl", "w") fecha a aba."""
    if SIMULADO:
        log.info("[simulado] atalho %s", "+".join(nomes))
        return
    codigos = [TECLAS[n] for n in nomes]
    for c in codigos:
        user32.keybd_event(c, 0, 0, 0)
    time.sleep(0.03)
    for c in reversed(codigos):
        user32.keybd_event(c, 0, KEYEVENTF_KEYUP, 0)


def janela_ativa(acao: str) -> None:
    """acao: "minimizar" | "maximizar" | "restaurar" (a janela que esta na frente)."""
    if SIMULADO:
        log.info("[simulado] janela: %s", acao)
        return
    hwnd = user32.GetForegroundWindow()
    if hwnd:
        user32.ShowWindow(hwnd, {"minimizar": 6, "maximizar": 3, "restaurar": 9}[acao])


def tirar_print() -> Path:
    """Salva um print da tela inteira em Imagens/Mestre e devolve o arquivo."""
    from datetime import datetime

    pasta = Path.home() / "Pictures" / "Mestre"
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / f"print_{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    if SIMULADO:
        log.info("[simulado] print em %s", arquivo)
        return arquivo
    from PIL import ImageGrab

    ImageGrab.grab(all_screens=True).save(arquivo)
    return arquivo


def acordar_tela() -> None:
    """Mexe o mouse 1 pixel e aperta Shift: o monitor liga."""
    if SIMULADO:
        log.info("[simulado] acordar tela")
        return
    user32.mouse_event(0x0001, 1, 1, 0, 0)
    user32.mouse_event(0x0001, -1, -1, 0, 0)
    _tecla(VK_SHIFT)


def desligar_tela() -> None:
    """Desliga so o monitor (o PC continua ligado e ouvindo)."""
    if SIMULADO:
        log.info("[simulado] desligar tela")
        return
    HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER = 0xFFFF, 0x0112, 0xF170
    user32.PostMessageW(HWND_BROADCAST, WM_SYSCOMMAND, SC_MONITORPOWER, 2)


def bloquear() -> None:
    if SIMULADO:
        log.info("[simulado] bloquear")
        return
    user32.LockWorkStation()


def desligar_pc(segundos: int = 60) -> None:
    _executar(["shutdown", "/s", "/t", str(segundos)])


def reiniciar_pc(segundos: int = 60) -> None:
    _executar(["shutdown", "/r", "/t", str(segundos)])


def cancelar_desligamento() -> None:
    _executar(["shutdown", "/a"])


def abrir_site(url: str) -> None:
    log.info("Abrindo site: %s", url)
    if SIMULADO and EH_WINDOWS:
        return
    antes = janela_da_frente()
    brave = None
    if SITES_NO_BRAVE and url.startswith("http"):
        from .navegador import caminho_do_brave
        brave = caminho_do_brave()
    if url.startswith("spotify:"):
        webbrowser.open(url)
        return
    # Pediu um monitor: abre numa JANELA NOVA e so ela vai para la (antes a aba nova abria na janela
    # que ja existia e a janela inteira, com as outras abas, mudava de monitor).
    ja_aberto = bool(brave) and any(e == "brave.exe" for _, _, e in _janelas_visiveis())
    if brave:
        from .navegador import comando_do_brave
        subprocess.Popen(comando_do_brave(brave, "--new-window", url) if MONITOR_ALVO else comando_do_brave(brave, url))
    else:
        webbrowser.open(url, new=1 if MONITOR_ALVO else 2)
    if MONITOR_ALVO or not ja_aberto:   # sem monitor pedido, uma aba nova nao arrasta a janela que ja existia
        depois_de_abrir(antes)


def _limpar_alvo(alvo: str) -> str:
    """Tira aspas (o "Copiar como caminho" do Windows coloca) e espacos."""
    return str(alvo).strip().strip('"').strip("'").strip()


def _parece_caminho(alvo: str) -> bool:
    return "\\" in alvo or "/" in alvo or alvo.lower().endswith((".exe", ".lnk", ".bat", ".url"))


def problema_no_programa(alvo: str) -> str:
    """Explica o que esta errado com o programa (ou "" se parece certo)."""
    alvo = _limpar_alvo(alvo)
    if not alvo:
        return "O campo do programa está vazio."
    if EH_WINDOWS and _parece_caminho(alvo) and not alvo.startswith(("http", "ms-")) and not Path(alvo).exists():
        return (f"Não achei este arquivo:\n{alvo}\n\nUse o botão “Procurar programa no PC...” "
                "para escolher o programa certo.")
    return ""


def abrir_programa(alvo: str) -> bool:
    """Abre um programa pelo nome curto (notepad, chrome) ou caminho completo."""
    alvo = _limpar_alvo(alvo)
    log.info("Abrindo programa: %s", alvo)
    problema = problema_no_programa(alvo)
    if problema:
        log.error("Nao consegui abrir o programa: %s", problema.replace("\n", " "))
        return False
    if SIMULADO:
        log.info("[simulado] abrir %s", alvo)
        return True
    antes = janela_da_frente()
    try:
        os.startfile(alvo)
        depois_de_abrir(antes)
        return True
    except OSError:
        pass
    try:
        # "start" do Windows encontra programas registrados (chrome, winword...)
        subprocess.Popen(f'start "" "{alvo}"', shell=True)
        return True
    except OSError as erro:
        log.error("Nao consegui abrir %s: %s", alvo, erro)
        return False


def abrir_arquivo(caminho) -> None:
    if not SIMULADO:
        os.startfile(str(caminho))
    else:
        log.info("[simulado] abrir arquivo %s", caminho)


def mostrar_na_pasta(caminho) -> None:
    """Abre o Explorador de Arquivos com o arquivo ja selecionado (para arrastar para o Claude)."""
    if SIMULADO:
        log.info("[simulado] mostrar na pasta %s", caminho)
        return
    import subprocess
    subprocess.Popen(["explorer", "/select,", str(caminho)])


def colar_e_enviar(texto: str, enviar: bool = True) -> None:
    """Copia o texto, aperta Ctrl+V e (opcional) Enter na janela em foco."""
    if SIMULADO:
        log.info("[simulado] colar: %s", texto)
        return
    import pyperclip

    pyperclip.copy(texto)
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    _tecla(VK_V)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    if enviar:
        time.sleep(0.4)
        _tecla(VK_RETURN)


# --- Janelas do Windows (para mandar texto ao app Claude) ------------------------------
NAVEGADORES = ("chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe")


def _janelas_visiveis() -> list[tuple[int, str, str]]:
    """(identificador, titulo, programa.exe) de cada janela aberta."""
    if not EH_WINDOWS:
        return []
    from ctypes import wintypes

    k32 = ctypes.windll.kernel32
    achadas = []

    def programa(hwnd) -> str:
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        processo = k32.OpenProcess(0x1000, False, pid.value)
        if not processo:
            return ""
        caminho = ctypes.create_unicode_buffer(1024)
        tamanho = wintypes.DWORD(1024)
        k32.QueryFullProcessImageNameW(processo, 0, caminho, ctypes.byref(tamanho))
        k32.CloseHandle(processo)
        return Path(caminho.value).name.lower()

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def cada(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            if n:
                titulo = ctypes.create_unicode_buffer(n + 1)
                user32.GetWindowTextW(hwnd, titulo, n + 1)
                achadas.append((hwnd, titulo.value, programa(hwnd)))
        return True
    user32.EnumWindows(cada, 0)
    return achadas


IGNORAR_JANELAS = {"textinputhost.exe", "shellexperiencehost.exe", "searchhost.exe", "startmenuexperiencehost.exe",
                   "lockapp.exe", "systemsettings.exe"}


def _escondida(hwnd: int) -> bool:
    """Janelas "fantasma" do Windows (apps da loja suspensos): visiveis para o Windows, invisiveis para voce."""
    try:
        valor = ctypes.c_int(0)
        ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(valor), ctypes.sizeof(valor))  # CLOAKED
        return bool(valor.value)
    except Exception:
        return False


def monitor_da_janela(hwnd: int) -> int | None:
    """Em qual monitor (numero do Mestre) esta o meio da janela."""
    if not EH_WINDOWS or not hwnd:
        return None
    from ctypes import wintypes
    r = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(r)):
        return None
    cx, cy = (r.left + r.right) // 2, (r.top + r.bottom) // 2
    for m in monitores():
        if m["x"] <= cx < m["x"] + m["largura"] and m["y"] <= cy < m["y"] + m["altura"] + 60:
            return m["numero"]
    return None


def monitor_do_mouse() -> int | None:
    """Em qual monitor (numero do Mestre) o mouse esta: e onde voce provavelmente esta olhando."""
    if not EH_WINDOWS:
        return None
    from ctypes import wintypes
    ponto = wintypes.POINT()
    if not user32.GetCursorPos(ctypes.byref(ponto)):
        return None
    for m in monitores():
        if m["x"] <= ponto.x < m["x"] + m["largura"] and m["y"] <= ponto.y < m["y"] + m["altura"] + 60:
            return m["numero"]
    return None


def monitor_do_ponto(x: int, y: int) -> int | None:
    """Monitor que contem o ponto (ex.: o meio de uma janela do navegador, vindo da extensao)."""
    for m in monitores():
        if m["x"] <= x < m["x"] + m["largura"] and m["y"] <= y < m["y"] + m["altura"] + 60:
            return m["numero"]
    return None


def janelas_abertas() -> list[dict]:
    """Janelas de programas que voce ve: {"hwnd", "titulo", "exe", "monitor"}."""
    lista = []
    for hwnd, titulo, exe in _janelas_visiveis():
        if exe in IGNORAR_JANELAS or titulo in ("Program Manager", "") or _escondida(hwnd):
            continue
        if user32.GetWindow(hwnd, 4):   # tem "dono" (caixinhas e menus de outra janela)
            continue
        lista.append({"hwnd": hwnd, "titulo": titulo, "exe": exe, "monitor": monitor_da_janela(hwnd)})
    return lista


def janela_pelo_titulo(inicio: str, exe: str = "brave.exe", espera: float = 2.5) -> int | None:
    """A janela do programa cujo titulo comeca com o texto (ex.: a aba que a extensao acabou de separar)."""
    if SIMULADO or not EH_WINDOWS:
        return None
    inicio = (inicio or "").strip().lower()[:30]
    fim = time.time() + espera
    while True:
        da_frente = janela_da_frente()
        achadas = [h for h, t, e in _janelas_visiveis() if e == exe and inicio and t.lower().startswith(inicio)]
        if achadas:
            return da_frente if da_frente in achadas else achadas[0]
        if time.time() >= fim:
            break
        time.sleep(0.2)
    return da_frente if any(h == da_frente and e == exe for h, _, e in _janelas_visiveis()) else None


def programa_da_frente() -> str:
    """O .exe da janela que esta na frente (ex.: "brave.exe")."""
    if not EH_WINDOWS:
        return ""
    h = janela_da_frente()
    return next((e for hw, _, e in _janelas_visiveis() if hw == h), "")


def trazer_para_frente(hwnd: int) -> None:
    if SIMULADO or not hwnd:
        return
    _trazer_para_frente(hwnd)


def janela_do_app_claude() -> int | None:
    for hwnd, titulo, exe in _janelas_visiveis():
        if exe == "claude.exe":
            return hwnd
    return None


def _trazer_para_frente(hwnd: int) -> None:
    user32.ShowWindow(hwnd, 9)                 # restaura se estiver minimizada
    user32.keybd_event(0x12, 0, 0, 0)          # um "Alt" solto: o Windows deixa trocar de janela
    user32.keybd_event(0x12, 0, KEYEVENTF_KEYUP, 0)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.6)


def _clicar_na_caixa_de_mensagem(hwnd: int, altura: int, posicao: list | None = None) -> None:
    """UM clique na caixa de mensagem: na posicao que voce ensinou (painel) ou no meio do rodape."""
    from ctypes import wintypes

    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    if posicao and len(posicao) == 2:
        x = r.left + int((r.right - r.left) * float(posicao[0]))
        y = r.top + int((r.bottom - r.top) * float(posicao[1]))
    else:
        x, y = (r.left + r.right) // 2, r.bottom - altura
    user32.SetCursorPos(x, y)
    user32.mouse_event(0x0002, 0, 0, 0, 0)     # botao esquerdo: aperta
    user32.mouse_event(0x0004, 0, 0, 0, 0)     # solta
    time.sleep(0.3)


def abrir_app_claude() -> int | None:
    """Abre o app Claude (se estiver fechado) e devolve a janela dele."""
    import os as _os

    hwnd = janela_do_app_claude()
    if hwnd:
        return hwnd
    candidatos = [Path(_os.environ.get("LOCALAPPDATA", "")) / "AnthropicClaude" / "claude.exe",
                  Path(_os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Claude" / "Claude.exe"]
    for exe in candidatos:
        if exe.exists():
            subprocess.Popen([str(exe)])
            break
    else:
        try:
            _os.startfile("claude://")
        except OSError:
            return None
    for _ in range(40):                       # espera ate 20 s a janela aparecer
        time.sleep(0.5)
        hwnd = janela_do_app_claude()
        if hwnd:
            time.sleep(2.5)                   # (o app ainda esta carregando a conversa)
            return hwnd
    return None


def _focar_caixa_pela_acessibilidade(hwnd: int, limite: float = 6.0) -> bool:
    """Acha a caixa de mensagem DENTRO do app (pelo recurso de acessibilidade do Windows) e clica nela.

    E bem mais confiavel que clicar numa posicao fixa. Biblioteca: uiautomation (gratis).
    """
    try:
        import uiautomation as auto
    except Exception as erro:
        log.info("uiautomation indisponivel (%s): vou clicar pela posicao", erro)
        return False
    inicio = time.time()
    with auto.UIAutomationInitializerInThread():   # obrigatorio fora da linha principal
        for tentativa in range(3):   # o app monta a arvore de acessibilidade na primeira consulta
            try:
                janela = auto.ControlFromHandle(hwnd)
                jr = janela.BoundingRectangle
                caixas = []
                for controle, _prof in auto.WalkControl(janela, maxDepth=40):
                    if time.time() - inicio > limite:
                        break
                    # So caixas de TEXTO (o "documento" da pagina inteira nao serve: clicar nele
                    # acertava links e botoes, como o de baixar arquivo)
                    if controle.ControlTypeName != "EditControl" or not controle.IsEnabled:
                        continue
                    r = controle.BoundingRectangle
                    if r.width() > 150 and r.height() > 12 and r.top >= jr.top + jr.height() // 3 and r.bottom <= jr.bottom + 2:
                        caixas.append(controle)
                if caixas:
                    caixa = max(caixas, key=lambda c: c.BoundingRectangle.bottom)   # a de baixo = a de digitar
                    caixa.SetFocus()   # so o cursor, sem clique
                    time.sleep(0.2)
                    focado = auto.GetFocusedControl()
                    if focado and focado.ControlTypeName in ("EditControl", "DocumentControl", "GroupControl"):
                        log.info("Caixa de mensagem achada pela acessibilidade: %s", caixa.Name[:60])
                        return True
            except Exception as erro:
                log.info("Acessibilidade (tentativa %d): %s", tentativa + 1, erro)
            time.sleep(1)
    return False


def print_de_diagnostico(nome: str, manter: int = 6) -> Path | None:
    """Guarda um print da tela em logs/diagnostico (para descobrir por que algo nao funcionou)."""
    if SIMULADO:
        return None
    try:
        from datetime import datetime

        from PIL import ImageGrab

        from .config import PASTA_LOGS

        pasta = PASTA_LOGS / "diagnostico"
        pasta.mkdir(parents=True, exist_ok=True)
        arquivo = pasta / f"{nome}_{datetime.now():%Y%m%d_%H%M%S}.png"
        ImageGrab.grab(all_screens=True).save(arquivo)
        for velho in sorted(pasta.glob(f"{nome}_*.png"))[:-manter]:
            velho.unlink(missing_ok=True)
        return arquivo
    except Exception as erro:
        log.warning("Nao consegui salvar o print de diagnostico: %s", erro)
        return None


def preparar_janela_do_claude() -> int | None:
    """Abre/traz o app Claude, no monitor principal e MAXIMIZADO (a caixa fica sempre no mesmo lugar)."""
    hwnd = abrir_app_claude()
    if not hwnd:
        return None
    _trazer_para_frente(hwnd)
    if len(monitores()) > 1:
        mover_janela_para_monitor(hwnd, 1)
    user32.ShowWindow(hwnd, 3)   # maximizada
    time.sleep(0.6)
    if user32.GetForegroundWindow() != hwnd:   # o Windows as vezes nao deixa: tenta de novo
        _trazer_para_frente(hwnd)
    return hwnd


def posicao_do_mouse_no_claude() -> list | None:
    """Painel > "Ensinar onde fica a caixa": onde o mouse esta, em fracao da janela do Claude."""
    from ctypes import wintypes

    hwnd = janela_do_app_claude()
    if not hwnd:
        return None
    ponto, r = wintypes.POINT(), wintypes.RECT()
    user32.GetCursorPos(ctypes.byref(ponto))
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    if not (r.left <= ponto.x <= r.right and r.top <= ponto.y <= r.bottom):
        return None
    return [round((ponto.x - r.left) / (r.right - r.left), 4), round((ponto.y - r.top) / (r.bottom - r.top), 4)]


def enviar_para_app_claude(texto: str, enviar: bool = True, altura_caixa: int = 90, posicao: list | None = None) -> bool:
    """Cola o texto na conversa ABERTA no app Claude do PC. Devolve False se nao achou o app."""
    copiar(texto)
    if SIMULADO:
        log.info("[simulado] app Claude: %s", texto[:80])
        return True
    hwnd = preparar_janela_do_claude()
    if not hwnd:
        log.warning("App Claude nao encontrado (procurei a janela do claude.exe)")
        return False
    if posicao:   # voce ensinou o lugar: e o mais garantido
        _clicar_na_caixa_de_mensagem(hwnd, altura_caixa, posicao)
    elif not _focar_caixa_pela_acessibilidade(hwnd):
        _clicar_na_caixa_de_mensagem(hwnd, altura_caixa)
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    _tecla(VK_V)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    if enviar:
        time.sleep(0.6)
        _tecla(VK_RETURN)
    time.sleep(1.2)
    print_de_diagnostico("envio_claude")
    return True


def enviar_para_claude_terminal(texto: str) -> None:
    """Abre o Claude Code no terminal, na pasta do Mestre, com o pedido salvo em arquivo."""
    from .config import PASTA_LOGS, PASTA_PROJETO

    PASTA_LOGS.mkdir(exist_ok=True)
    (PASTA_LOGS / "pedido_ditado.md").write_text(texto, encoding="utf-8")
    instrucao = ("Leia o arquivo logs/pedido_ditado.md: e um pedido que eu ditei por voz. "
                 "Use a skill corrigir-transcricao, depois a refinar-pedido, e espere meu ok antes de implementar.")
    abrir_terminal_com(f'claude "{instrucao}"', PASTA_PROJETO, "Mestre - pedido ditado")


def clicar_e_colar_na_janela_ativa(texto: str, enviar: bool = True, altura_caixa: int = 90) -> None:
    """Para o navegador: clica na caixa de mensagem da pagina (rodape) antes de colar."""
    if SIMULADO:
        log.info("[simulado] colar: %s", texto[:80])
        return
    copiar(texto)
    hwnd = user32.GetForegroundWindow()
    if hwnd:
        _clicar_na_caixa_de_mensagem(hwnd, altura_caixa)
    user32.keybd_event(VK_CONTROL, 0, 0, 0)
    _tecla(VK_V)
    user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
    if enviar:
        time.sleep(0.5)
        _tecla(VK_RETURN)


def apertar_enter() -> None:
    if SIMULADO:
        log.info("[simulado] Enter")
        return
    _tecla(VK_RETURN)


def copiar(texto: str) -> None:
    """Coloca o texto na area de transferencia (Ctrl+V cola)."""
    try:
        import pyperclip

        pyperclip.copy(texto)
    except Exception as erro:
        log.warning("Nao consegui copiar: %s", erro)


def ler_area_transferencia() -> str:
    """O texto que esta copiado (Ctrl+C)."""
    try:
        import pyperclip

        return pyperclip.paste() or ""
    except Exception as erro:
        log.warning("Nao consegui ler a area de transferencia: %s", erro)
        return ""


def abrir_terminal_com(linha_de_comando: str, pasta, titulo: str) -> None:
    """Abre uma janela de terminal nova, na pasta, rodando a linha de comando.

    A linha vai para um .bat temporario: assim aspas e acentos chegam inteiros.
    """
    if SIMULADO:
        log.info("[simulado] terminal em %s: %s", pasta, linha_de_comando)
        return
    bat = Path(pasta) / "logs" / "_terminal.bat"
    bat.parent.mkdir(exist_ok=True)
    bat.write_text(f'@echo off\r\nchcp 65001 >nul\r\ncd /d "{pasta}"\r\n{linha_de_comando}\r\n',
                   encoding="utf-8")
    subprocess.Popen(["cmd", "/c", "start", titulo, "cmd", "/k", str(bat)], cwd=str(pasta))


def abrir_com_comando(comando: list[str] | None, pasta) -> bool:
    """Abre a janela de terminal ja pronta (validacao.comando_para_abrir_claude): Windows Terminal ou
    cmd, ja rodando o Claude Code interativo. False = `comando` era None (Claude Code nao encontrado)."""
    if not comando:
        return False
    if SIMULADO:
        log.info("[simulado] terminal com o Claude: %s", comando)
        return True
    subprocess.Popen(comando, cwd=str(pasta))
    return True


# --- O proprio Mestre (painel, reiniciar) -----------------------------------
def _python_sem_janela() -> str:
    """pythonw.exe roda sem abrir a janela preta."""
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    return str(pythonw) if pythonw.exists() else sys.executable


def _rodar_modulo(modulo: str) -> None:
    from .config import PASTA_PROJETO

    subprocess.Popen([_python_sem_janela(), "-m", modulo], cwd=str(PASTA_PROJETO))


def abrir_painel() -> None:
    log.info("Abrindo o painel de configuracoes")
    _rodar_modulo("app.iniciar_painel")


def abrir_revisao_ditado() -> None:
    """Janelinha para ler/corrigir o ditado e escolher o destino (app/revisar_ditado.py)."""
    if os.environ.get("MESTRE_SIMULAR") == "1":
        log.info("[simulado] janela de revisao do ditado")
        return
    try:
        _rodar_modulo("app.revisar_ditado")
    except Exception as erro:  # sem janela, o destino continua podendo ser escolhido por voz
        log.warning("Nao consegui abrir a janela de revisao: %s", erro)


def iniciar_mestre() -> None:
    _rodar_modulo("app.main")


def rodar_comando(frase: str, espera: int = 120) -> str:
    """Roda UM comando num Mestre separado (python -m app.main --comando) e devolve o diario."""
    from .config import PASTA_PROJETO

    try:
        python = Path(sys.executable)
        if python.name.lower() == "pythonw.exe":   # o pythonw nao tem saida de texto para lermos
            python = python.with_name("python.exe")
        r = subprocess.run([str(python), "-m", "app.main", "--comando", frase], cwd=str(PASTA_PROJETO),
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=espera,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8"},
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return (r.stdout or "") + (r.stderr or "")
    except subprocess.TimeoutExpired:
        return "(o teste passou do tempo)"


def processo_vivo(pid: str) -> bool:
    try:
        numero = int(str(pid).strip())
    except ValueError:
        return False
    if EH_WINDOWS:
        processo = ctypes.windll.kernel32.OpenProcess(0x1000, False, numero)  # so consultar
        if not processo:
            return False
        codigo = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(processo, ctypes.byref(codigo))
        ctypes.windll.kernel32.CloseHandle(processo)
        return codigo.value == 259  # STILL_ACTIVE
    try:
        os.kill(numero, 0)
        return True
    except OSError:
        return False


def mestre_ligado() -> bool:
    """True se o Mestre esta rodando (o arquivo mestre.pid existe E o processo esta vivo)."""
    from .config import PASTA_PROJETO

    arquivo = PASTA_PROJETO / "mestre.pid"
    if not arquivo.exists():
        return False
    if processo_vivo(arquivo.read_text().strip()):
        return True
    arquivo.unlink(missing_ok=True)  # sobrou de um Mestre que fechou com erro
    return False


def parar_mestre() -> bool:
    """Desliga o Mestre que esta rodando (usado pelo painel)."""
    from .config import PASTA_PROJETO

    arquivo = PASTA_PROJETO / "mestre.pid"
    if not arquivo.exists():
        return False
    parar_pid(arquivo.read_text().strip())
    arquivo.unlink(missing_ok=True)
    return True


def parar_pid(pid: str) -> None:
    comando = ["taskkill", "/PID", pid, "/F"] if EH_WINDOWS else ["kill", pid]
    subprocess.run(comando, capture_output=True, check=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def reiniciar_mestre() -> None:
    """Liga um Mestre novo e desliga o que estava rodando (inclusive este processo)."""
    from .config import PASTA_PROJETO

    arquivo = PASTA_PROJETO / "mestre.pid"
    pid_antigo = arquivo.read_text().strip() if arquivo.exists() else ""
    iniciar_mestre()
    if pid_antigo == str(os.getpid()):
        os._exit(0)  # somos o Mestre antigo: o novo ja esta subindo
    if pid_antigo:
        time.sleep(0.5)
        parar_pid(pid_antigo)


def _executar(comando: list[str]) -> None:
    if SIMULADO:
        log.info("[simulado] %s", " ".join(comando))
        return
    subprocess.run(comando, check=False, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
