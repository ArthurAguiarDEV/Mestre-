"""O que o Mestre esta fazendo agora. O indicador na tela (overlay) le daqui.

Estados: iniciando, ouvindo, gravando, transcrevendo, trabalhando, pensando,
         falando, conversa, pausado
"""
import threading
import time

from .config import PASTA_LOGS

ARQUIVO_PAUSA = PASTA_LOGS / "pausado"   # existe = microfone em pausa (usado pelo painel)

_trava = threading.Lock()
_atual = {"nome": "iniciando", "detalhe": "", "desde": time.time(), "nivel": 0.0,
          "limiar": 0.0, "conversa_ate": 0.0, "ultima_frase": "", "ultima_resposta": "",
          "ditado": 0, "ditado_desde": 0.0, "ditado_contexto": "", "ultimo_audio": b"", "audio_anterior": b"",
          # IA pensando em segundo plano: "" | "pensando" | "pronto"
          "pensamento": "", "pensamento_pergunta": "", "pensamento_desde": 0.0,
          # "pode descansar": so "bora voltar a trabalhar" acorda
          "descanso": False,
          # aviso rapido no indicador (ex.: "Telegram: abre o YouTube") ate o horario "aviso_ate"
          "aviso": "", "aviso_ate": 0.0}


def avisar(texto: str, segundos: float = 7.0) -> None:
    atualizar(aviso=texto, aviso_ate=time.time() + segundos)


def definir(nome: str, detalhe: str = "") -> None:
    with _trava:
        _atual.update(nome=nome, detalhe=detalhe, desde=time.time())


def atualizar(**campos) -> None:
    with _trava:
        _atual.update(campos)


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
