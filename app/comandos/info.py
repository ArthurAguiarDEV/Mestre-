"""Informacoes: clima, noticias, hora e data.

Mixin do Executor (app/comandos/__init__.py): os metodos usam self.voz, self.cfg, self.falar...
do nucleo e chamam metodos dos outros mixins pelo self.
"""
import random
import re
from datetime import datetime
from .. import informacoes

from .base import DIAS, MESES


class InfoMixin:
    # =================================================================
    #  Clima e noticias
    # =================================================================
    def _cidade(self) -> str:
        return (self.cfg.get("assistente") or {}).get("cidade") or "São Paulo"

    def _cmd_clima(self, t: str) -> bool:
        if not re.search(r"\b(como (ta|esta|vai estar) o tempo|clima|previsao do tempo|vai chover|temperatura|ta frio|ta calor|quantos graus)\b", t):
            return False
        achado = re.search(r"\b(em|de|no|na) ([a-z ]{3,})$", t)
        cidade = achado.group(2).strip() if achado and "tempo" not in achado.group(2) else self._cidade()
        self.voz.falar(informacoes.clima(cidade))
        return True

    def _cmd_noticias(self, t: str) -> bool:
        if not re.search(r"\b(noticias|manchetes|novidades do dia|o que ta acontecendo)\b", t):
            return False
        achado = re.search(r"\b(sobre|de) (.+)$", t)
        self._falar_noticias(3, achado.group(2) if achado else "")
        return True

    def _falar_noticias(self, quantidade: int, assunto: str = "") -> None:
        manchetes = informacoes.noticias(quantidade, assunto)
        if not manchetes:
            self.voz.falar("Não consegui buscar as notícias agora.")
            return
        self.voz.falar("As principais notícias: " + ". ".join(manchetes) + ".")

    # =================================================================
    #  Hora e data
    # =================================================================
    def _cmd_hora_data(self, t: str) -> bool:
        agora = datetime.now()
        if re.search(r"\b(que horas sao|que horas|horas sao)\b", t):
            minutos = "em ponto" if agora.minute == 0 else f"e {agora.minute}"
            hora = {0: "meia-noite", 12: "meio-dia"}.get(agora.hour)
            if hora:
                self.voz.falar(f"É {hora} {minutos}.")
            else:
                self.voz.falar(random.choice([f"São {agora.hour} {minutos}.", f"Agora são {agora.hour} {minutos}."]))
            return True
        if re.search(r"\b(que dia e hoje|que dia|qual a data)\b", t):
            self.voz.falar(f"Hoje é {DIAS[agora.weekday()]}, {agora.day} de {MESES[agora.month - 1]}.")
            return True
        return False
