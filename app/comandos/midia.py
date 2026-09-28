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
    # nome falado -> (rotulo pra falar, lista de .exe pra tentar, na ordem)
    PROCESSOS_POR_NOME = {
        "brave": ("Brave", ["brave.exe"]),
        "chrome": ("Chrome", ["chrome.exe"]),
        "edge": ("Edge", ["msedge.exe"]),
        "msedge": ("Edge", ["msedge.exe"]),
        "microsoft edge": ("Edge", ["msedge.exe"]),
        "navegador": ("navegador", ["brave.exe", "chrome.exe", "msedge.exe"]),
    }

    def _programa_da_frase(self, texto: str) -> tuple[str, list[str]] | None:
        """"do navegador", "do Brave", "do Chrome"... -> (rotulo, [exe, ...]). Nao pega so "volume"/"som" soltos."""
        m = re.search(r"\b(navegador|brave|chrome|microsoft edge|edge|msedge)\b", texto)
        return self.PROCESSOS_POR_NOME.get(m.group(1)) if m else None

    def _cmd_volume(self, t: str) -> bool:
        puro = self._pedido_puro()
        texto = t + " | " + puro
        # (o Whisper as vezes escreve "Spotfy", "espotifai"... e "multa" no lugar de "muta")
        do_spotify = bool(re.search(r"\b(e?spot\w*|spotify)\b", texto))
        programa = None if do_spotify else self._programa_da_frase(texto)
        do_programa = do_spotify or programa is not None
        if do_spotify or re.search(r"\bmulta (o )?(som|audio|video|youtube|pc|computador|navegador|brave|chrome|edge)\b", texto):
            texto = re.sub(r"\bmulta\b", "muta", texto)
            puro = re.sub(r"\bmulta\b", "muta", puro)
        falou_de_volume = re.search(r"\b(volume|som|mais alto|mais baixo|muta|mudo|silencia|desmuta)\b", texto)
        # "coloca o Spotify no maximo", "abaixa o Spotify"/"abaixa o navegador", "Spotify no 50" (sem a palavra "volume")
        if not falou_de_volume and not (do_programa and re.search(
                r"\b(aumenta|abaixa|diminui|sobe|baixa|maximo|minimo|mais alto|mais baixo|no \d+|em \d+)\b", texto)):
            return False
        volta_som = re.search(r"\b(desmuta|tira do mudo|tirar do mudo|do mudo|som de volta|volta o som|liga o som)\b", texto)
        tira_som = re.search(r"\b(muta|mudo|silencia|tira o som|desliga o som|sem som)\b", texto)
        # "tira o vídeo do mudo", "aumenta o volume do YouTube": so o video (nao o PC inteiro)
        if not do_programa and re.search(r"\b(video|youtube)\b", texto):
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
        rotulo, exes = ("Spotify", ["Spotify.exe"]) if do_spotify else (programa or (None, None))
        if do_programa and (volta_som or tira_som):
            self._volume_programa(exes, rotulo, "som" if volta_som else "mudo", 0)
            return True
        if volta_som or tira_som:
            sistema.volume("mudo")
            return True
        numero = None if relativo else re.search(r"\b(?:no|em|para|pra|a|volume)\s+(?:volume\s+)?(\d{1,3})\s*(%|por ?cento)?", puro)
        if do_programa and re.search(r"\b(maximo|no talo|tudo)\b", texto):
            self._volume_programa(exes, rotulo, "definir", 1.0)
            return True
        if do_programa and re.search(r"\bminimo\b", texto):
            self._volume_programa(exes, rotulo, "definir", 0.1)
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
        if do_programa:
            self._volume_programa(exes, rotulo, acao, int(numero.group(1)) / 100 if numero else passo)
            return True
        if acao == "definir":
            sistema.volume_do_pc(int(numero.group(1)))
        elif re.search(r"\b(maximo|tudo)\b", texto):
            sistema.volume("maximo")
        else:
            sistema.volume(acao, vezes=int(passo * 50))
        return True

    def _volume_spotify(self, acao: str, quanto: float) -> None:
        """Mexe SO no Spotify (o volume do Windows fica como esta). Mantido pelo nome antigo (Spotify chama
        direto ao tocar uma playlist); usa o mesmo caminho generico de _volume_programa."""
        self._volume_programa(["Spotify.exe"], "Spotify", acao, quanto)

    def _volume_programa(self, exes: list[str], rotulo: str, acao: str, quanto: float) -> None:
        """Mexe SO no volume de um programa (Spotify, Brave, Chrome, Edge...) no mixer do Windows: o
        volume geral do PC fica como esta. `exes` pode ter mais de um nome (ex.: "navegador" tenta Brave,
        Chrome e Edge, o que estiver com uma sessao de audio ativa)."""
        sistema.ULTIMO_NIVEL = None
        motivo = "nao_tocando"
        for exe in exes:
            motivo = sistema.volume_do_programa(exe, acao, quanto)
            if motivo != "nao_tocando":
                break
        if not motivo:
            if acao == "mudo":
                self.voz.falar(f"{rotulo} mudo.")
            elif acao == "som":
                self.voz.falar(f"Som do {rotulo} de volta.")
            elif sistema.ULTIMO_NIVEL is not None:
                self.voz.falar(f"{rotulo} em {round(sistema.ULTIMO_NIVEL * 100)} por cento.")
        elif motivo == "nao_tocando":
            self.voz.falar(f"Não achei o {rotulo} tocando agora.")
        elif motivo == "sem_biblioteca":
            self.voz.falar(f"Pra mexer só no {rotulo} falta uma biblioteca. Use Atualizar o Mestre na Central. "
                           "Não mexi no volume do computador.")
        elif motivo:
            self.voz.falar(f"Não consegui mexer no volume do {rotulo}. O erro ficou no diário.")

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
