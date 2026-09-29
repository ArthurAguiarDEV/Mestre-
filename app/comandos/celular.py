"""Coisas do celular pedidas falando no PC: mandar um print pro Telegram e "o que tá tocando".

Mixin do Executor (app/comandos/__init__.py): os metodos usam self.voz, self.cfg, self.caixa
(app/recebidos.py, se o Telegram estiver ligado)... A maioria dos comandos novos do Telegram
(print, o que ta tocando, video curto, desligar/suspender/reiniciar) e tratada direto em
app/recebidos.py (Caixa._comando_especial), pois so fazem sentido vindo do celular.
"""
import logging
import re
import threading
from .. import informacoes, segredos, sistema

log = logging.getLogger(__name__)


class CelularMixin:
    # =================================================================
    #  Print pro Telegram e "o que ta tocando", pedidos falando no PC
    # =================================================================
    def _cmd_print_telegram(self, t: str) -> bool:
        if not re.search(r"\b(manda(r)?|mande)( um)? print( da tela)?( no| pro| para o) telegram\b", t):
            return False
        caixa = getattr(self, "caixa", None)
        chat = segredos.ler("telegram_chat")
        if not caixa or not chat:
            self.voz.falar("Ainda não tenho o seu chat do Telegram. Mande um “oi” pro robô primeiro.")
            return True
        self.voz.falar("Tirando o print e mandando pro Telegram.")
        # tirar e subir as fotos leva segundos: numa linha separada, para nao travar a escuta
        threading.Thread(target=self._mandar_prints_telegram, args=(caixa, int(chat)), daemon=True).start()
        return True

    def _mandar_prints_telegram(self, caixa, chat: int) -> None:
        try:
            prints = sistema.tirar_prints_por_monitor()
            caixa.enviar_fotos(chat, [(p["arquivo"], p["descricao"]) for p in prints])
        except Exception:
            log.exception("Nao consegui mandar o print pro Telegram")
            self.voz.falar("Não consegui mandar o print pro Telegram agora.")

    def _cmd_tocando(self, t: str) -> bool:
        if not re.search(r"\bo que (ta|esta) (tocando|passando)\b", t):
            return False
        self.voz.falar(informacoes.o_que_esta_tocando(self))
        return True
