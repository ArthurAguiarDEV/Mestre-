"""O que o Mestre esta fazendo agora. O indicador na tela (overlay) le daqui.

Estados: iniciando, ouvindo, gravando, transcrevendo, trabalhando, pensando,
         falando, conversa, pausado
"""
import json
import os
import threading
import time

from .config import PASTA_LOGS

ARQUIVO_PAUSA = PASTA_LOGS / "pausado"   # existe = microfone em pausa (usado pelo painel)
# o painel roda em outro processo: le daqui o que o Assessor esta fazendo (Inicio > cartao de status)
ARQUIVO_AGORA = PASTA_LOGS / "estado_agora.json"
PUBLICOS = ("nome", "detalhe", "desde", "pensamento", "pensamento_pergunta", "pensamento_desde",
            "pensamentos_fila", "pensamentos_lista", "descanso", "ultima_frase", "ultima_resposta")

_trava = threading.Lock()
_atual = {"nome": "iniciando", "detalhe": "", "desde": time.time(), "nivel": 0.0,
          "limiar": 0.0, "conversa_ate": 0.0, "ultima_frase": "", "ultima_resposta": "",
          "ditado": 0, "ditado_desde": 0.0, "ditado_contexto": "", "ultimo_audio": b"", "audio_anterior": b"",
          # IA pensando em segundo plano: "" | "pensando" | "pronto"
          "pensamento": "", "pensamento_pergunta": "", "pensamento_desde": 0.0, "pensamentos_fila": 0,
          "pensamentos_lista": [],   # [{"pergunta", "inicio", "estado"}] (fila do pensando, no painel)
          # "pode descansar": so "bora voltar a trabalhar" acorda
          "descanso": False,
          # aviso rapido no indicador (ex.: "Telegram: abre o YouTube") ate o horario "aviso_ate"
          "aviso": "", "aviso_ate": 0.0}


def avisar(texto: str, segundos: float = 7.0) -> None:
    atualizar(aviso=texto, aviso_ate=time.time() + segundos)


def definir(nome: str, detalhe: str = "") -> None:
    with _trava:
        mudou = _atual.get("nome") != nome or _atual.get("detalhe") != detalhe
        _atual.update(nome=nome, detalhe=detalhe, desde=time.time())
    if mudou:
        _publicar()


def atualizar(**campos) -> None:
    with _trava:
        mudou = any(k in PUBLICOS and _atual.get(k) != v for k, v in campos.items())
        _atual.update(campos)
    if mudou:
        _publicar()


def _publicar() -> None:
    """Grava o essencial num arquivo pequeno (so quando muda: nada de escrever a cada bloco de audio)."""
    with _trava:
        dados = {k: _atual.get(k) for k in PUBLICOS}
    dados.update(pid=os.getpid(), ts=round(time.time(), 2))
    try:
        PASTA_LOGS.mkdir(exist_ok=True)
        temporario = ARQUIVO_AGORA.with_suffix(f".{os.getpid()}.tmp")
        temporario.write_text(json.dumps(dados, ensure_ascii=False, default=str), encoding="utf-8")
        os.replace(temporario, ARQUIVO_AGORA)
    except (OSError, TypeError, ValueError):
        pass   # (o painel lendo ao mesmo tempo: fica para a proxima mudanca)


def ler_de_fora() -> dict:
    """O que o Assessor (outro processo) publicou por ultimo. {} se nao tem."""
    try:
        return json.loads(ARQUIVO_AGORA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


# situacao mostrada no painel (Inicio): chave -> (titulo, explicacao)
SITUACOES = {
    "ouvindo": ("Ouvindo", "Pode falar: diga a palavra de ativação e o pedido."),
    "pensando": ("Pensando", "A IA está trabalhando no seu pedido."),
    "falando": ("Falando", "Respondendo agora."),
    "descansando": ("Descansando", "Fica quieto até você dizer “bora voltar a trabalhar”."),
    "pausado": ("Pausado", "A escuta está pausada: ele não ouve o microfone."),
    "desligado": ("Desligado", "Clique em “Ligar” para ele começar a ouvir."),
}


def situacao(dados: dict, rodando: bool, esta_pausado: bool) -> str:
    """Resume o estado publicado em uma das SITUACOES (ouvindo/pensando/falando/descansando/pausado/desligado)."""
    if not rodando:
        return "desligado"
    if esta_pausado or dados.get("nome") == "pausado":
        return "pausado"
    if dados.get("descanso"):
        return "descansando"
    nome = dados.get("nome") or ""
    if nome == "falando":
        return "falando"
    if dados.get("pensamento") == "pensando" or nome in ("pensando", "trabalhando", "transcrevendo"):
        return "pensando"
    return "ouvindo"


def ler() -> dict:
    with _trava:
        return dict(_atual)


def pausado() -> bool:
    return ARQUIVO_PAUSA.exists()


def pausar(sim: bool) -> None:
    PASTA_LOGS.mkdir(exist_ok=True)
    if sim:
        ARQUIVO_PAUSA.write_text("pausado pelo painel ou pelo indicador")
    else:
        ARQUIVO_PAUSA.unlink(missing_ok=True)
