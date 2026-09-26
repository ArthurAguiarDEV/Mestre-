"""Audios do celular -> texto -> Assessor ou Claude.

Dois caminhos (painel > Celular), os dois gratis e rodando no seu PC:
  1. PASTA SINCRONIZADA: no celular, "Compartilhar" o audio (WhatsApp, gravador...) para o Google Drive /
     OneDrive, numa pasta que tambem aparece no PC. O Mestre ve o arquivo novo e transcreve.
  2. TELEGRAM: um robo seu no Telegram. Voce manda audio (ou texto) para ele de qualquer lugar.

O que ele faz com o texto:
  - comeca com a palavra de ativacao ("Assessor, abre o YouTube")  -> executa como comando;
  - senao -> o destino escolhido no painel: "projeto" (app do Claude, padrao), "nota" ou "ipm".
Tudo fica guardado em recebidos/ (texto) e o audio vai para a subpasta "lidos".
"""
import json
import logging
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from . import estado, memoria, segredos
from .config import PASTA_PROJETO, palavras_ativacao
from .texto import extrair_comando

log = logging.getLogger(__name__)
PASTA_TEXTOS = PASTA_PROJETO / "recebidos"
EXTENSOES = {".ogg", ".opus", ".oga", ".m4a", ".mp3", ".wav", ".aac", ".amr", ".3gp", ".webm", ".mp4", ".flac"}
CABECALHO = "[Áudio do celular transcrito pelo {nome}: corrija a transcrição e refine antes de implementar.]\n\n"


def pasta_padrao() -> Path:
    documentos = Path.home() / "Documents"
    return (documentos if documentos.exists() else Path.home()) / "Assessor" / "audios"


def pasta_de_entrada(cfg: dict) -> Path:
    escolhida = str((cfg.get("recebidos") or {}).get("pasta") or "").strip()
    return Path(escolhida).expanduser() if escolhida else pasta_padrao()


class Caixa:
    """Vigia a pasta e o Telegram em segundo plano e entrega o texto ao Executor."""

    def __init__(self, cfg: dict, executor, transcritor):
        self.cfg = cfg
        self.executor = executor
        self.transcritor = transcritor
        c = cfg.get("recebidos") or {}
        self.usar_pasta = bool(c.get("pasta_ligada", True))
        self.usar_telegram = bool(c.get("telegram_ligado", True))
        self.destino = str(c.get("destino") or "projeto")
        self.pasta = pasta_de_entrada(cfg)
        self.aviso = str(c.get("aviso") or "tela_e_voz")
        self.frases = {"telegram": str(c.get("frase_telegram") or "Mensagem do Telegram."),
                       "pasta": str(c.get("frase_pasta") or "Áudio do celular.")}
        self._vistos: dict[str, float] = {}

    def iniciar(self) -> None:
        if self.usar_pasta:
            threading.Thread(target=self._vigiar_pasta, daemon=True).start()
        if self.usar_telegram and segredos.ler("telegram_token"):
            threading.Thread(target=self._vigiar_telegram, daemon=True).start()

    # --- o que fazer com o texto -------------------------------------------------------
    def avisar(self, texto: str, origem: str) -> None:
        """Aviso curto de que chegou algo do celular: no indicador e/ou uma frase falada (painel > Celular)."""
        de = "telegram" if "telegram" in origem.lower() else "pasta"
        if self.aviso in ("tela_e_voz", "tela"):
            estado.avisar(("📱 Telegram: " if de == "telegram" else "📱 Celular: ") + texto)
        if self.aviso in ("tela_e_voz", "voz") and self.frases[de].strip():
            try:
                self.executor.voz.falar(self.frases[de])
            except Exception as erro:
                log.info("Aviso do celular nao foi falado: %s", erro)

    def entregar(self, texto: str, origem: str) -> str:
        """Devolve uma frase curta dizendo o que foi feito (o Telegram responde com ela)."""
        texto = (texto or "").strip()
        if not texto:
            return "Não entendi nada nesse áudio."
        self.avisar(texto, origem)
        PASTA_TEXTOS.mkdir(exist_ok=True)
        with open(PASTA_TEXTOS / f"{datetime.now():%Y-%m-%d}.md", "a", encoding="utf-8") as f:
            f.write(f"- ({datetime.now():%H:%M}, {origem}) {texto}\n")
        achou, comando = extrair_comando(texto, palavras_ativacao(self.cfg))
        if achou and comando:
            self.executor.executar(comando, texto)
            memoria.registrar(texto, "", f"{origem} (comando)")
            return f"Executei: {comando}"
        destino = self.destino
        nome = getattr(self.executor, "nome", "Assessor")
        with self.executor._trava_execucao:
            if destino == "nota":
                from .config import PASTA_NOTAS
                PASTA_NOTAS.mkdir(exist_ok=True)
                with open(PASTA_NOTAS / "notas.txt", "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now():%d/%m/%Y %H:%M}] (celular) {texto}\n")
                feito = "Guardei nas suas notas."
            elif destino == "ipm":
                self.executor._enviar_ao_agente(texto)
                feito = "Mandei pro agente IPM."
            else:
                self.executor._enviar_ao_projeto(CABECALHO.format(nome=nome) + texto)
                feito = "Mandei pro projeto no app do Claude (e salvei nas melhorias)."
        memoria.registrar(texto, feito, origem)
        return feito

    # --- 1) pasta sincronizada ------------------------------------------------------------
    def _vigiar_pasta(self) -> None:
        self.pasta.mkdir(parents=True, exist_ok=True)
        lidos = self.pasta / "lidos"
        log.info("Vigiando a pasta de audios do celular: %s", self.pasta)
        while self.executor.rodando:
            try:
                for arquivo in sorted(self.pasta.iterdir()):
                    if arquivo.suffix.lower() not in EXTENSOES or not arquivo.is_file():
                        continue
                    tamanho = arquivo.stat().st_size
                    # so quando parar de crescer (o Drive ainda pode estar baixando)
                    if self._vistos.get(arquivo.name) != tamanho:
                        self._vistos[arquivo.name] = tamanho
                        continue
                    self._processar_arquivo(arquivo, lidos)
            except Exception:
                log.exception("Erro vigiando a pasta de audios")
            time.sleep(4)

    def _processar_arquivo(self, arquivo: Path, lidos: Path) -> None:
        log.info("Audio novo na pasta: %s", arquivo.name)
        texto = self.transcritor.transcrever_arquivo(arquivo)
        lidos.mkdir(exist_ok=True)
        destino = lidos / f"{datetime.now():%Y%m%d_%H%M%S}_{arquivo.name}"
        try:
            arquivo.replace(destino)
        except OSError:
            pass
        self._vistos.pop(arquivo.name, None)
        self.entregar(texto, "áudio da pasta")

    # --- 2) Telegram ------------------------------------------------------------------------
    def _api(self, metodo: str, espera: float = 35, **dados):
        token = segredos.ler("telegram_token")
        corpo = urllib.parse.urlencode(dados).encode() if dados else None
        with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/{metodo}", data=corpo, timeout=espera) as r:
            resposta = json.loads(r.read())
        if not resposta.get("ok"):
            raise RuntimeError(resposta.get("description") or "Telegram recusou")
        return resposta["result"]

    def responder(self, chat: int, texto: str) -> None:
        try:
            self._api("sendMessage", espera=15, chat_id=chat, text=texto[:3500])
        except Exception as erro:
            log.info("Telegram nao respondeu: %s", erro)

    def _vigiar_telegram(self) -> None:
        log.info("Telegram ligado: esperando mensagens do seu robo")
        proximo = 0
        while self.executor.rodando:
            try:
                for item in self._api("getUpdates", offset=proximo, timeout=25):
                    proximo = item["update_id"] + 1
                    self._mensagem_telegram(item.get("message") or {})
            except Exception as erro:
                log.info("Telegram: %s (tento de novo em 20 s)", erro)
                time.sleep(20)

    def _mensagem_telegram(self, msg: dict) -> None:
        chat = (msg.get("chat") or {}).get("id")
        if not chat:
            return
        dono = segredos.ler("telegram_chat")
        if not dono:   # a primeira conversa com o robo vira a SUA (so ela e atendida)
            segredos.salvar(telegram_chat=chat, telegram_nome=(msg.get("from") or {}).get("first_name", ""))
            self.responder(chat, "Pronto! Este chat agora é o seu. Mande áudios ou textos: "
                                 "começando com a palavra de ativação eu executo; senão, mando pro projeto no Claude.")
            if (msg.get("text") or "").startswith("/start"):
                return
        elif str(chat) != dono:
            log.warning("Telegram: mensagem de outro chat (%s) ignorada", chat)
            return
        audio = msg.get("voice") or msg.get("audio") or msg.get("video_note") or (
            msg.get("document") if str((msg.get("document") or {}).get("mime_type", "")).startswith("audio") else None)
        if audio:
            self.responder(chat, "Recebi o áudio. Transcrevendo...")
            try:
                caminho = self._baixar_do_telegram(audio["file_id"])
                texto = self.transcritor.transcrever_arquivo(caminho)
                caminho.unlink(missing_ok=True)
            except Exception as erro:
                log.exception("Telegram: erro no audio")
                self.responder(chat, f"Não consegui transcrever: {erro}")
                return
            feito = self.entregar(texto, "áudio do Telegram")
            self.responder(chat, f"📝 {texto}\n\n→ {feito}")
            return
        texto = (msg.get("text") or "").strip()
        if texto and not texto.startswith("/"):
            self.responder(chat, "→ " + self.entregar(texto, "texto do Telegram"))

    def _baixar_do_telegram(self, file_id: str) -> Path:
        info = self._api("getFile", espera=20, file_id=file_id)
        token = segredos.ler("telegram_token")
        destino = PASTA_TEXTOS / "tmp" / Path(info["file_path"]).name
        destino.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(f"https://api.telegram.org/file/bot{token}/{info['file_path']}", timeout=60) as r:
            destino.write_bytes(r.read())
        return destino


def testar_telegram(token: str) -> str:
    """Para o painel: confere o token e devolve o @ do robo (ou levanta o erro)."""
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token.strip()}/getMe", timeout=15) as r:
        dados = json.loads(r.read())
    if not dados.get("ok"):
        raise RuntimeError(dados.get("description") or "token recusado")
    return "@" + dados["result"]["username"]
