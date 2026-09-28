"""Coisas do celular pedidas falando no PC: mandar um print pro Telegram e "o que tá tocando".

Mixin do Executor (app/comandos/__init__.py): os metodos usam self.voz, self.cfg, self.caixa
(app/recebidos.py, se o Telegram estiver ligado)... A maioria dos comandos novos do Telegram
(print, o que ta tocando, video curto, desligar/suspender/reiniciar) e tratada direto em
app/recebidos.py (Caixa._comando_especial), pois so fazem sentido vindo do celular.
"""
import re
from .. import informacoes, segredos, sistema


class CelularMixin:
    # =================================================================
    #  Print pro Telegram e "o que ta tocando", pedidos falando no PC
    # =================================================================
    def _cmd_print_telegram(self, t: str) -> bool:
        if not re.search(r"\bmanda(r)?( um)? print( da tela)?( no| pro| para o) telegram\b", t):
            return False
        caixa = getattr(self, "caixa", None)
        chat = segredos.ler("telegram_chat")
        if not caixa or not chat:
            self.voz.falar("Ainda não tenho o seu chat do Telegram. Mande um “oi” pro robô primeiro.")
            return True
        self.voz.falar("Tirando o print e mandando pro Telegram.")
        prints = sistema.tirar_prints_por_monitor()
        try:
            caixa.enviar_fotos(int(chat), [(p["arquivo"], p["descricao"]) for p in prints])
        except Exception:
            self.voz.falar("Não consegui mandar o print pro Telegram agora.")
        return True

    def _cmd_tocando(self, t: str) -> bool:
        if not re.search(r"\bo que (ta|esta) (tocando|passando)\b", t):
            return False
        self.voz.falar(informacoes.o_que_esta_tocando(self))
        return True
