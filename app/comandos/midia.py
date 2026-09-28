"""Volume (geral e por programa), teclas de midia e Spotify.

Mixin do Executor (app/comandos/__init__.py): os metodos usam self.voz, self.cfg, self.falar...
do nucleo e chamam metodos dos outros mixins pelo self.
"""
import random
import re
import threading
from urllib.parse import quote
from .. import sistema
from ..texto import melhor_correspondencia

from .base import link_spotify


class MidiaMixin:
    # =================================================================
    #  Spotify: playlists cadastradas no painel e busca
    # =================================================================
    def _cmd_spotify(self, t: str) -> bool:
        if "spotify" not in t:
            return False
        c = self.cfg.get("spotify") or {}
        playlists = c.get("playlists") or {}
        if re.fullmatch(r"(abre|liga|abrir)( o)? spotify", t):
            if melhor_correspondencia("spotify", self.cfg.get("programas") or {}):
                return False   # voce cadastrou o programa: quem abre e o comando "abre"
            sistema.abrir_site("spotify:")
            self.falar("ok")
            return True
        achado = re.search(r"\b(?:toca|tocar|coloca|bota|poe|abre|play)\b\s+(?:a |o |uma |um )?(playlist |lista |album |musica )?(.+?)"
                           r"(?: no| do| pelo)? spotify\b", t)
        if not achado:
            return False
        nome = achado.group(2).strip()
        chave = melhor_correspondencia(nome, playlists) if playlists else None
        if chave:
            self.voz.falar(random.choice([f"Soltando a playlist {chave}.", f"Bora de {chave}.", f"Abrindo {chave} no Spotify."]))
            sistema.abrir_site(link_spotify(playlists[chave]))
            if c.get("apertar_play", True):
                threading.Timer(float(c.get("segundos_para_tocar", 4)), sistema.play_pause).start()
            return True
        termo = self._original(nome)
        self.voz.falar(f"Procurando {termo} no Spotify.")
        sistema.abrir_site("spotify:search:" + quote(termo))
        return True

    # =================================================================
    #  Volume e midia
    # =================================================================
    def _cmd_volume(self, t: str) -> bool:
        puro = self._pedido_puro()
        texto = t + " | " + puro
        # (o Whisper as vezes escreve "Spotfy", "espotifai"... e "multa" no lugar de "muta")
        do_spotify = bool(re.search(r"\b(e?spot\w*|spotify)\b", texto))
        if do_spotify or re.search(r"\bmulta (o )?(som|audio|video|youtube|pc|computador)\b", texto):
            texto = re.sub(r"\bmulta\b", "muta", texto)
            puro = re.sub(r"\bmulta\b", "muta", puro)
        falou_de_volume = re.search(r"\b(volume|som|mais alto|mais baixo|muta|mudo|silencia|desmuta)\b", texto)
        # "coloca o Spotify no maximo", "abaixa o Spotify", "Spotify no 50" (sem a palavra "volume")
        if not falou_de_volume and not (do_spotify and re.search(
                r"\b(aumenta|abaixa|diminui|sobe|baixa|maximo|minimo|mais alto|mais baixo|no \d+|em \d+)\b", texto)):
            return False
        volta_som = re.search(r"\b(desmuta|tira do mudo|tirar do mudo|do mudo|som de volta|volta o som|liga o som)\b", texto)
        tira_som = re.search(r"\b(muta|mudo|silencia|tira o som|desliga o som|sem som)\b", texto)
        # "tira o vídeo do mudo", "aumenta o volume do YouTube": so o video (nao o PC inteiro)
        if not do_spotify and re.search(r"\b(video|youtube)\b", texto):
            yt = self._yt()
            if yt and hasattr(yt, "volume_video"):
                n = re.search(r"\b(\d{1,3})\s*(%|por ?cento)?", puro)
                acao_v = ("som" if volta_som else "mudo" if tira_som else "definir" if n and not re.search(
                    r"\b(aumenta|abaixa|sobe|diminui|mais|menos)\b", texto) else
                          "mais" if re.search(r"\b(aumenta|sobe|mais alto|maximo)\b", texto) else "menos")
                valor = 1.0 if re.search(r"\bmaximo\b", texto) else (int(n.group(1)) / 100 if n else 0.15)
                r = yt.volume_video(acao_v, valor)
                if r not in ("sem_video", "sem_controle"):
                    return True
        # "diminui o Spotify em 20", "aumenta mais 10": muda DE 20 em 20, nao PARA 20
        relativo = re.search(r"\b(?:em|mais|menos)\s+(\d{1,3})\b", puro) if re.search(
            r"\b(aumenta|aumentar|sobe|abaixa|diminui|diminuiu|diminuir|baixa|reduz|reduzir|menos|mais)\b", texto) else None
        if do_spotify and (volta_som or tira_som):
            self._volume_spotify("som" if volta_som else "mudo", 0)
            return True
        if volta_som or tira_som:
            sistema.volume("mudo")
            return True
        numero = None if relativo else re.search(r"\b(?:no|em|para|pra|a|volume)\s+(?:volume\s+)?(\d{1,3})\s*(%|por ?cento)?", puro)
        if do_spotify and re.search(r"\b(maximo|no talo|tudo)\b", texto):
            self._volume_spotify("definir", 1.0)
            return True
        if do_spotify and re.search(r"\bminimo\b", texto):
            self._volume_spotify("definir", 0.1)
            return True
        acao = ("definir" if numero else
                "aumentar" if re.search(r"\b(aumenta|aumentar|sobe|subir|mais alto|aumente|maximo|tudo)\b", texto) else
                "diminuir" if re.search(r"\b(abaixa|abaixar|diminui|diminuiu|diminuir|diminua|baixa|baixar|reduz|reduzir|"
                                        r"mais baixo|menos)\b", texto) else None)
        if acao is None:
            return False
        passo = 0.2 if re.search(r"\b(bastante|muito|bem)\b", texto) else 0.05 if re.search(r"\b(pouco|pouquinho)\b", texto) else 0.1
        if relativo:
            passo = min(100, int(relativo.group(1))) / 100
            if re.search(r"\bmenos\s+\d", puro):
                acao = "diminuir"
        if do_spotify:
            self._volume_spotify(acao, int(numero.group(1)) / 100 if numero else passo)
            return True
        if acao == "definir":
            sistema.volume_do_pc(int(numero.group(1)))
        elif re.search(r"\b(maximo|tudo)\b", texto):
            sistema.volume("maximo")
        else:
            sistema.volume(acao, vezes=int(passo * 50))
        return True

    def _volume_spotify(self, acao: str, quanto: float) -> None:
        """Mexe SO no Spotify (o volume do Windows fica como esta)."""
        sistema.ULTIMO_NIVEL = None
        motivo = sistema.volume_do_programa("Spotify.exe", acao, quanto)
        if not motivo:
            if acao == "mudo":
                self.voz.falar("Spotify mudo.")
            elif acao == "som":
                self.voz.falar("Som do Spotify de volta.")
            elif sistema.ULTIMO_NIVEL is not None:
                self.voz.falar(f"Spotify em {round(sistema.ULTIMO_NIVEL * 100)} por cento.")
        elif motivo == "nao_tocando":
            self.voz.falar("Não achei o Spotify tocando agora.")
        elif motivo == "sem_biblioteca":
            self.voz.falar("Pra mexer só no Spotify falta uma biblioteca. Use Atualizar o Mestre na Central. "
                           "Não mexi no volume do computador.")
        elif motivo:
            self.voz.falar("Não consegui mexer no volume do Spotify. O erro ficou no diário.")

    def _cmd_midia(self, t: str) -> bool:
        """Pausar, continuar, proxima e anterior: vale para Spotify, YouTube e qualquer player."""
        puro = self._pedido_puro()
        fim = r"( (do|no|o)? ?spotify)?( ai| por favor)?"
        if any(re.fullmatch(r"(proxima|proximo|proxima musica|proxima faixa|pula|pula essa|pula a musica|passa essa|"
                            r"passa a musica|outra musica|muda a musica|avanca a musica|manda a proxima|vai pra proxima|"
                            r"pula essa musica|pula essa faixa|passa essa musica|proxima do spotify)"
                            + fim, x) for x in (t, puro)):
            sistema.midia("proxima")
            return True
        if any(re.fullmatch(r"(anterior|musica anterior|faixa anterior|volta a musica|volta uma musica|"
                            r"volta essa musica)" + fim, x) for x in (t, puro)):
            sistema.midia("anterior")
            return True
        pausa = r"(pausa|pausar|pause|despausa|despausar|continua|continuar|play|volta a tocar|volta a toca|toca de novo)"
        # ("pausa o vídeo" fica com o YouTube: pausa o vídeo certo, sem soltar o Spotify por engano)
        alvo = r"( (o |a |essa |esta )?(musica|som|spotify|player))?( (do|no) spotify)?( ai| por favor)?"
        if re.fullmatch(pausa + alvo, t) or re.fullmatch(pausa + alvo, puro) or re.fullmatch(
                r"(para|pare) (a musica|o spotify|o som)", puro):
            sistema.midia("tocar_pausar")
            return True
        return False
