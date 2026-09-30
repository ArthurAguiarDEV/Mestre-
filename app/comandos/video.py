"""YouTube (pagina, canais, controle do que toca), streamings, clicar pelo texto e tocar.

Mixin do Executor (app/comandos/__init__.py): os metodos usam self.voz, self.cfg, self.falar...
do nucleo e chamam metodos dos outros mixins pelo self.
"""
import logging
import random
import re
import threading
import time
from urllib.parse import quote
from .. import sistema, youtube
from ..config import PASTA_PROJETO
from ..texto import achar_numero, contem, melhor_correspondencia, normalizar

from .base import _mesmo_site, _ordinal, _nome_do_canal, _tirar_enfeites
from .perfis import perfil_da_frase

log = logging.getLogger(__package__)  # "app.comandos", o mesmo logger de antes da divisao


class VideoMixin:
    # =================================================================
    #  YouTube "vendo" a pagina (janela do navegador controlada pelo Mestre)
    # =================================================================
    def _yt(self):
        """O YouTube controlado (ou None, se desligado no painel ou sem a biblioteca)."""
        if not (self.cfg.get("youtube") or {}).get("navegador_mestre", True):
            return None
        if getattr(self, "_youtube", None) is None:
            from ..navegador import (Navegador, YouTube, YouTubeNoBraveComExtensao, YouTubeNoNavegadorNormal,
                                    caminho_do_brave)
            c = self.cfg.get("youtube") or {}
            canal = str(c.get("navegador", "brave"))
            modo = str(c.get("modo") or "extensao")
            if modo == "extensao":   # o SEU Brave + a extensao do Mestre (recomendado)
                if getattr(self, "ponte", None) is None:
                    from ..ponte import Ponte
                    self.ponte = Ponte()
                    self.ponte.iniciar()
                self._youtube = YouTubeNoBraveComExtensao(caminho_do_brave(), self.ponte)
            elif modo == "normal":   # o seu navegador de sempre: so os comandos de tecla
                self._youtube = YouTubeNoNavegadorNormal(caminho_do_brave() if canal == "brave" else None)
            elif not Navegador.disponivel():
                log.info("playwright nao instalado: YouTube abre no navegador normal")
                self._youtube = False
                return None
            else:
                self._youtube = YouTube(Navegador(canal))
        return self._youtube or None

    def _abrir_youtube(self, url: str) -> None:
        yt = None if sistema.JANELA_NOVA else self._yt()   # "numa janela nova": não reusa a aba do YouTube
        if yt:
            try:
                yt.abrir(url, sistema.monitor(sistema._monitor_desejado()) if sistema._monitor_desejado() else None)
                aviso = getattr(getattr(yt, "nav", None), "aviso", "")
                if aviso:
                    self.voz.falar(aviso)
                    yt.nav.aviso = ""
                return
            except Exception as erro:
                log.warning("Navegador do Mestre falhou (%s); abrindo no navegador normal", erro)
        sistema.abrir_site(url)

    # =================================================================
    #  "pausa o vídeo da Netflix", "pausa a Disney", "continua o filme": qual serviço, aba e monitor
    # =================================================================
    PAUSAR_VIDEO = r"(pausa|pausar|pause|para|pare|segura)"
    CONTINUAR_VIDEO = r"(continua|continuar|continue|despausa|despausar|solta|da play|volta a tocar)"
    COISA_DE_VIDEO = r"(video|serie|filme|episodio|desenho|anime)"
    ARTIGO_SERVICO = {"YouTube": "o", "Netflix": "a", "Disney": "a", "Prime Video": "o", "HBO Max": "a", "Globoplay": "o"}

    def _servicos_de_video(self) -> dict:
        """nome -> (domínio, jeitos de falar): o YouTube e os streamings."""
        return {"YouTube": ("youtube.com", r"youtube"), **{n: (d, j) for n, (d, _, j) in self.STREAMINGS.items()}}

    def _no(self, servico: str, prep: str = "n") -> str:
        """ "na Netflix", "no YouTube" (prep "d": "da Netflix", "do YouTube")."""
        return f"{prep}{self.ARTIGO_SERVICO.get(servico, 'o')} {servico}"

    def _servico_da_aba(self, aba: dict) -> str | None:
        return next((n for n, (dominio, _) in self._servicos_de_video().items()
                     if _mesmo_site(aba.get("url", ""), dominio)), None)

    def _servico_falado(self, texto: str) -> str | None:
        return next((n for n, (_, jeitos) in self._servicos_de_video().items()
                     if re.search(rf"\b({jeitos})\b", normalizar(texto))), None)

    def _cmd_controle_video(self, t: str) -> bool:
        """Pausar/continuar sabendo QUAL vídeo: o serviço dito, senão o único que está tocando; com mais de
        um, pergunta. Só YouTube (ou sem a extensão) passa para o _cmd_youtube_controle, como sempre."""
        puro, monitor = self._monitor_da_frase(self._pedido_puro())
        jeitos = "|".join(j for _, j in self._servicos_de_video().values())
        achado = re.fullmatch(rf"(?P<verbo>{self.PAUSAR_VIDEO}|{self.CONTINUAR_VIDEO})"
                              rf"(?: (?:o|a|esse|essa|este|esta))?(?: (?P<coisa>{self.COISA_DE_VIDEO}))?"
                              rf"(?: (?:da|do|na|no|em|pela|pelo))?(?: (?:o|a))?(?: (?P<servico>{jeitos}))?"
                              r"(?: (?:ai|agora|por favor))?", puro)
        if not achado or not (achado.group("coisa") or achado.group("servico")):
            return False
        pausar = bool(re.fullmatch(self.PAUSAR_VIDEO, achado.group("verbo")))
        servico = self._servico_falado(achado.group("servico") or "")
        if servico == "YouTube":
            return False   # o _cmd_youtube_controle cuida (aba certa, monitor, teclas de mídia)
        ext = self._extensao()
        if not ext:
            if not servico:
                return False   # sem a extensão não dá para saber o que toca: o de sempre (YouTube/teclas)
            self.voz.falar(f"Pra controlar o vídeo {self._no(servico)} eu preciso da extensão no Brave.")
            return True
        abas = self._abas_abertas()
        de_video: dict[str, list[dict]] = {}   # serviço -> abas dele (só as do monitor dito, se disse)
        for aba in abas:
            s = self._servico_da_aba(aba)
            if s and (monitor is None or self._monitor_da_aba(aba, abas) == monitor):
                de_video.setdefault(s, []).append(aba)
        if servico:
            if not pausar and not de_video.get(servico) and servico in self.STREAMINGS:
                return False   # "continua a série na Disney" sem a Disney aberta: abrir e continuar (_cmd_streaming)
            self._video_no_servico(servico, de_video.get(servico, []), abas, pausar, monitor)
            return True
        tocando = {s: [a for a in lista if a.get("audivel")] for s, lista in de_video.items()} if pausar else {}
        tocando = {s: lista for s, lista in tocando.items() if lista}
        vale = tocando or de_video
        if not vale:
            if monitor is not None:
                return False
            self.perguntar("Não achei vídeo aberto no navegador. Quer que eu use o pause geral do computador?",
                           self._responder_pause_geral, espera=12)
            return True
        if list(vale) == ["YouTube"]:
            return False
        if len(vale) == 1:
            s = next(iter(vale))
            self._video_no_servico(s, vale[s], abas, pausar, monitor)
            return True
        nomes = [self._no(s) for s in vale]
        lista_falada = ", ".join(nomes[:-1]) + " e " + nomes[-1]
        self.perguntar(f"Tem vídeo {'tocando' if tocando else 'aberto'} {lista_falada}. "
                       f"Qual você quer {'pausar' if pausar else 'continuar'}?",
                       lambda r, v=vale, p=pausar, a=abas: self._responder_qual_video(r, v, p, a), espera=12)
        return True

    def _responder_qual_video(self, resposta: str, vale: dict, pausar: bool, abas: list[dict]) -> None:
        servico = self._servico_falado(resposta)
        if servico not in vale:
            self.voz.falar("Não peguei qual. Fala de novo: pausa o vídeo da Netflix, por exemplo.")
        elif servico == "YouTube":
            self._youtube_pausar(pausar)
        else:
            self._video_no_servico(servico, vale[servico], abas, pausar, None)

    def _responder_pause_geral(self, resposta: str) -> None:
        if re.match(r"^(sim|pode|isso|quero|claro|usa|use|manda|ok|beleza|por favor)\b", normalizar(resposta)):
            sistema.midia("tocar_pausar")
        else:
            self.voz.falar("Tá bom. Não mexi em nada.")

    def _youtube_pausar(self, pausar: bool) -> None:
        """A escolha foi o YouTube: o caminho de sempre do YouTube (aba que toca, monitor, pergunta)."""
        acao = "pausar" if pausar else "continuar"
        yt = self._yt()
        if not yt:
            sistema.midia("tocar_pausar")
        elif "aba_alvo" in vars(yt) and self._extensao():
            self._youtube_na_aba_certa(yt, acao, acao + " o video", None)
        else:
            self._acao_youtube_protegida(yt, acao, acao + " o video")

    def _video_no_servico(self, servico: str, candidatas: list[dict], abas: list[dict], pausar: bool,
                          monitor: int | None) -> None:
        """Pausa/continua o vídeo da aba do serviço (a que toca; mais de uma em telas diferentes: pergunta)."""
        from ..ponte import desatualizada
        ext = self._extensao()
        if not candidatas:
            self.voz.falar(f"Não achei aba {self._no(servico, 'd')}" + (f" no monitor {monitor}." if monitor else "."))
            return
        if desatualizada(getattr(ext, "versao", "")):
            self.voz.falar("A extensão do Brave está desatualizada. Recarregue ela: o passo a passo está no painel, "
                           "na página YouTube.")
            return
        if pausar and any(a.get("audivel") for a in candidatas):
            candidatas = [a for a in candidatas if a.get("audivel")]
        dominio = self._servicos_de_video()[servico][0]

        def continuar(aba_id):
            try:
                r = ext.pedir("video", {"aba": aba_id, "dominio": dominio, "pausar": pausar}, espera=5)
            except Exception as erro:
                log.info("Extensao nao controlou o video %s: %s", self._no(servico), erro)
                r = "erro"
            if r == "sem_video":
                self.voz.falar(f"Não achei vídeo {self._no(servico)}.")
            elif r == "ja":
                self.voz.falar("Já estava pausado." if pausar else "Já estava tocando.")
            elif r not in ("ok", True):
                self.voz.falar(f"Não consegui {'pausar' if pausar else 'continuar'} {self._no(servico)}.")
        self._escolher_aba(candidatas, abas, servico, monitor, continuar)

    SELECAO_YOUTUBE = ("abrir_n", "abrir_titulo", "canal_n", "titulos")   # escolher algo QUE ESTA na tela
    CONTROLE_DO_QUE_TOCA = ("pausar", "pular", "proximo", "continuar")

    def _cmd_youtube_controle(self, t: str) -> bool:
        puro = re.sub(r"\b(\w+?)s (videos?|resultados?)\b", r"\1 \2", self._pedido_puro())   # "os terceiros videos"
        puro, monitor_dito = self._monitor_da_frase(puro)   # "... do monitor 2": ONDE esta o YouTube
        t = self._monitor_da_frase(t)[0]
        x = t + "\n" + puro   # (cada uma numa linha: ^ e $ valem para as duas)
        pedidos = [
            ("tela_cheia_chat", r"tela cheia com (o )?chat"),
            ("sair_tela_cheia", r"(sai|sair|tira|tirar|fecha)( da| a)? tela cheia|tela normal"),
            ("tela_cheia", r"(poe|coloca|bota|deixa|abre)?( em| na)? ?tela cheia( sem (o )?chat)?"),
            ("cinema", r"modo cinema|modo teatro"),
            ("legenda", r"\b(legenda|legendas)\b"),
            ("proximo", r"proximo video|pula (o|esse|este) video|outro video|video seguinte|"
                        r"(passa|vai) (pro|para o) proximo( video)?$"),
            ("anterior", r"video anterior|volta (o|pro|para o) video( anterior)?$"),
            ("pausar", r"\b(pausa|pausar|pause|para|pare|segura)( o| esse| este| a)? (video|youtube)\b"),
            ("continuar", r"\b(continua|continuar|continue|despausa|despausar|solta|volta|da play|play)( no| o| esse| este| a)? "
                          r"(video|youtube)\b|\bvolta a rodar o video\b"),
            ("ir", r"\b(vai|vai pra|vai para|abre|abrir|entra|entra em|entra nas|entra no|mostra|me mostra|ir)( as| os| a| o| nas| nos| na| no| pra| para| pras| pros)* "
                   r"(inscricoes|historico( do youtube)?|assistir mais tarde|shorts|playlists|minhas playlists|inicio( do youtube)?|"
                   r"videos que (eu )?gostei|videos curtidos|videos com gostei|downloads|meu canal|seu canal)\b"),
            ("like", r"\b(da|dar|deixa|manda|solta) (um |o )?(like|gostei|joinha)\b|\b(curte|curtir) (o|esse|este) video\b"),
            ("inscrever", r"\b(se )?(inscreve|inscrever|increve|escreve no canal)\b"),
            ("chat_fecha", r"\b(fecha|esconde|tira|oculta|some com) o chat\b"),
            ("chat_abre", r"\b(abre|mostra|volta|liga) o chat\b"),
            ("titulos", r"(le|leia|fala) os (titulos|videos)|quais (sao )?os videos"),
            ("pular", r"\b(avanca|adianta|pula|volta|retrocede)( o video)? (\w+ )?(segundos?|minutos?)\b|"
                      r"^(avanca|adianta|volta um pouco|retrocede)$"),
            ("abrir_titulo", r"\bvideo (com o nome|com nome|chamado|com o titulo|com titulo|que se chama|que tem o nome) (.+)"),
            ("canal_n", r"\bcanal do ((primeiro|segundo|terceiro|quarto|quinto|sexto|setimo|oitavo|nono|decimo)s?|\d+) (video|link|resultado)\b"),
            ("abrir_n", r"\b(abre|clica|coloca|toca|seleciona|escolhe|quero|vai)( no| na| o| a| os| em)? "
                        r"((primeiro|segundo|terceiro|quarto|quinto|sexto|setimo|oitavo|nono|decimo)s?|\d+) "
                        r"(videos?|resultados?|opcao|link)\b|\b(abre|clica|toca)( no| o)? video (numero )?\d+\b|"
                        r"^(o |a )?(primeiro|segundo|terceiro|quarto|quinto|sexto|setimo|oitavo|nono|decimo|\d+) (video|resultado|link)( da| dessa| desta| na)?( janela| tela| pagina| lista)?$"),
            ("abrir_titulo", r"\b(abre|abrir|clica|toca|coloca|bota|poe|seleciona|escolhe|assiste|assistir|ver|mostra)"
                             r"( no| o| esse| aquele| um)? video (do|da|de|dos|das|chamado|sobre|que fala de|que fala sobre|com) (.+)"),
        ]
        acao = next((nome for nome, padrao in pedidos if re.search(padrao, x, re.M)), None)
        if acao is None:
            return False
        yt = self._yt()
        aberto = bool(yt) and yt.na_pagina_do_youtube()
        ext = self._extensao()
        if aberto and ext and hasattr(yt, "ponte") and not getattr(self, "_avisou_extensao", False):
            from ..ponte import desatualizada
            if desatualizada(getattr(ext, "versao", "")):
                self._avisou_extensao = True
                self.voz.falar("A extensão do Brave está desatualizada. Recarregue ela: o passo a passo está no painel, "
                               "na página YouTube.")
        if acao == "ir" and not aberto and not re.search(
                r"\b(youtube|inscricoes|assistir mais tarde|shorts|gostei|curtidos)\b", puro):
            return False   # "abre o histórico" sem YouTube aberto nao e do YouTube
        if not aberto:
            if acao in ("proximo", "anterior", "pausar", "continuar"):   # sem YouTube: teclas de midia
                sistema.midia({"proximo": "proxima", "anterior": "anterior"}.get(acao, "tocar_pausar"))
                return True
            if acao == "ir":
                self._abrir_youtube(self._pagina_do_youtube(puro))
                return True
            if acao in ("tela_cheia", "tela_cheia_chat"):
                sistema.atalho("f11")   # qualquer janela: tela cheia do Windows
                return True
            if acao == "sair_tela_cheia":
                sistema.atalho("esc")
                return True
            if acao == "abrir_titulo" and not re.search(r"\b(com o nome|com nome|chamado|titulo|que se chama)\b", puro):
                return False   # "abre o vídeo do Manual do Mundo" sem YouTube aberto = último vídeo do canal
            self.voz.falar("Isso funciona no YouTube aberto por mim. Fala: abre o YouTube.")
            return True
        monitor = monitor_dito or sistema.MONITOR_ALVO
        if "aba_alvo" in vars(yt) and self._extensao() and (acao in self.SELECAO_YOUTUBE or monitor or
                                                             acao in self.CONTROLE_DO_QUE_TOCA):
            sistema.MONITOR_ALVO = None   # (aqui "no monitor 2" diz onde o YouTube ESTA, nao onde abrir)
            self._youtube_na_aba_certa(yt, acao, puro, monitor)
            return True
        self._acao_youtube_protegida(yt, acao, puro)
        return True

    def _acao_youtube_protegida(self, yt, acao: str, puro: str) -> None:
        try:
            self._acao_youtube(yt, acao, puro)
        except Exception as erro:
            log.warning("YouTube: %s", erro)
            self.voz.falar("Não consegui fazer isso no YouTube agora.")

    def _youtube_na_aba_certa(self, yt, acao: str, puro: str, monitor: int | None) -> None:
        """YouTube aberto em mais de um monitor: age na aba certa (a que tem o vídeo falado, a do monitor
        dito, a do monitor do mouse; pausar = a que está tocando) ou pergunta qual."""
        abas = self._abas_abertas()
        candidatas = self._abas_na_tela(abas, "youtube.com")
        if monitor is None and acao in self.CONTROLE_DO_QUE_TOCA:
            if acao == "continuar":
                # "continua o video": vai para a que foi pausada por ultimo (pelo Mestre ou a mao),
                # sem perguntar, se a extensao souber dizer.
                pausadas = [a for a in candidatas if a.get("video_pausado")]
                if pausadas:
                    candidatas = [max(pausadas, key=lambda a: a.get("video_pausado_em") or 0)]
            else:
                tocando = [a for a in candidatas if a.get("audivel")]
                if len(tocando) == 1:
                    candidatas = tocando
        tem = None
        if acao == "abrir_titulo":
            falado = self._titulo_falado(puro)
            tem = lambda a: bool(self._video_na_tela(falado, self._resultados_da_aba(a["id"])))   # noqa: E731

        def continuar(aba_id):
            yt.aba_alvo = aba_id
            try:
                self._acao_youtube_protegida(yt, acao, puro)
            finally:
                yt.aba_alvo = None
        self._escolher_aba(candidatas, abas, "YouTube", monitor, continuar, tem)

    def _resultados_da_aba(self, aba_id: int) -> list[dict]:
        try:
            r = self._extensao().pedir("resultados", espera=5, aba=aba_id)
            return r if isinstance(r, list) else []
        except Exception as erro:
            log.info("Sem resultados da aba %s: %s", aba_id, erro)
            return []

    @staticmethod
    def _titulo_falado(puro: str) -> str:
        falado = re.split(r"\bvideo (?:com o nome|com nome|chamado|com o titulo|com titulo|que se chama|que tem o nome|"
                          r"do|da|de|dos|das|sobre|que fala de|que fala sobre|com) ", puro, maxsplit=1)
        return falado[1] if len(falado) > 1 else puro

    def _acao_youtube(self, yt, acao: str, puro: str) -> None:
        if acao == "tela_cheia":
            yt.tela_cheia(True)
        elif acao == "tela_cheia_chat":
            yt.tela_cheia_com_chat()
        elif acao == "sair_tela_cheia":
            yt.tela_cheia(False)
            yt.nav.janela_tela_cheia(False)
        elif acao == "cinema":
            yt.modo_cinema()
        elif acao == "legenda":
            yt.legenda()
        elif acao == "proximo":
            yt.proximo()
        elif acao == "anterior":
            if self._extensao():
                self._extensao().pedir("voltar")
            else:
                sistema.midia("anterior")
        elif acao in ("pausar", "continuar"):
            r = yt.pausar(acao == "pausar")
            if r == "sem_video":
                sistema.midia("tocar_pausar")
        elif acao == "ir":
            yt.abrir(self._pagina_do_youtube(puro))
        elif acao in ("like", "inscrever", "chat_fecha", "chat_abre", "titulos", "abrir_n", "abrir_titulo") \
                and not getattr(yt, "completo", False):
            self.voz.falar("Pra isso eu preciso da extensão no Brave. Ela ainda não conectou. "
                           "O passo a passo está no painel, na página YouTube." if hasattr(yt, "ponte") else
                           "No seu Brave normal eu só consigo as teclas do YouTube. Pra isso, use a extensão "
                           "ou a janela controlada, no painel.")
        elif acao == "like":
            r = yt.like()
            self.voz.falar({"ok": "Like dado!", "ja": "Já tinha like.", "nao_achei": "Não achei o botão de like."}.get(r, "Feito."))
        elif acao == "inscrever":
            r = yt.inscrever()
            self.voz.falar({"ok": "Inscrito!", "ja": "Você já é inscrito nesse canal.",
                            "nao_achei": "Não achei o botão de inscrever. Você entrou na sua conta nessa janela?"}.get(r, "Feito."))
        elif acao in ("chat_fecha", "chat_abre"):
            r = yt.chat(acao == "chat_abre")
            if r == "sem_chat":
                self.voz.falar("Esse vídeo não tem chat.")
        elif acao == "pular":
            n = achar_numero(puro) or 10
            if re.search(r"\bminutos?\b", puro):
                n *= 60
            yt.pular(-n if re.search(r"\b(volta|retrocede)\b", puro) else n)
        elif acao == "titulos":
            lista = yt.resultados()[:5]
            if not lista:
                self._guardar_retrato(yt)
            self.voz.falar("Não achei vídeos nesta página." if not lista else
                           ". ".join(f"{i}: {r['titulo']}" + (f", do {r['canal']}" if r.get("canal") else "")
                                     for i, r in enumerate(lista, 1)))
        elif acao == "canal_n":
            lista = yt.resultados()
            n = _ordinal(puro)
            item = lista[n - 1] if lista and n and n <= len(lista) else None
            if not item or not item.get("canal_link"):
                self.voz.falar("Não achei esse canal na tela.")
                return
            yt.abrir(item["canal_link"])
            self.voz.falar(f"Abrindo o canal {item.get('canal') or ''}.")
        elif acao == "abrir_n":
            lista = yt.resultados()
            n = _ordinal(puro)
            if not lista:
                self._guardar_retrato(yt)
            if not n or n > len(lista):
                self.voz.falar(f"Só achei {len(lista)} vídeos aqui." if lista else "Não achei vídeos nesta página.")
                return
            yt.abrir(lista[n - 1]["link"])
            self.voz.falar(f"Abrindo: {lista[n - 1]['titulo'][:60]}.")
        elif acao == "abrir_titulo":
            falado = self._titulo_falado(puro)
            lista = yt.resultados()
            if not lista:
                self._guardar_retrato(yt)
            achado = self._video_na_tela(falado, lista)
            if not achado:
                self.voz.falar("Não achei esse vídeo na tela. Fala: lê os títulos.")
                return
            yt.abrir(achado["link"])
            self.voz.falar(f"Abrindo {achado['titulo'][:60]}.")

    @staticmethod
    def _guardar_retrato(yt) -> None:
        """Nao achou videos na tela: guarda um pedaco da pagina em logs/youtube_retrato.txt (vai na exportacao)."""
        if not hasattr(yt, "ponte"):
            return
        try:
            import json
            r = yt.ponte.pedir("retrato", espera=5)
            (PASTA_PROJETO / "logs").mkdir(exist_ok=True)
            (PASTA_PROJETO / "logs" / "youtube_retrato.txt").write_text(
                json.dumps(r, ensure_ascii=False, indent=1)[:12000], encoding="utf-8")
        except Exception as erro:
            log.info("Sem retrato do YouTube: %s", erro)

    @staticmethod
    def _video_na_tela(falado: str, lista: list[dict]) -> dict | None:
        """O video da tela que combina com o que foi falado: pelo titulo OU pelo canal
        ("o vídeo do David Jones", "o vídeo do GTA 6"). Empate: o que esta mais em cima."""
        from difflib import SequenceMatcher

        falado = re.sub(r"\s+(que (esta|ta) (aqui )?(na|nessa) (tela|pagina)( do youtube)?|da tela|na tela|aqui|ai|"
                        r"do youtube|no youtube)$", "", normalizar(falado)).strip()
        palavras = [w for w in falado.split() if len(w) > 1 and w not in ("do", "da", "de", "o", "a", "e", "no", "na")]
        if not palavras:
            return None
        melhor, nota_melhor = None, 0.0
        for item in lista:
            titulo, canal = normalizar(item.get("titulo", "")), normalizar(item.get("canal", ""))
            nota = 0.0
            for texto in (titulo, canal):
                if not texto:
                    continue
                dentro = sum(1 for w in palavras if re.search(rf"\b{re.escape(w)}\b", texto)) / len(palavras)
                nota = max(nota, dentro, SequenceMatcher(None, falado, texto).ratio())
            if nota > nota_melhor + 0.01:
                melhor, nota_melhor = item, nota
        return melhor if nota_melhor >= 0.6 else None

    @staticmethod
    def _pagina_do_youtube(puro: str) -> str:
        base = "https://www.youtube.com"
        for padrao, caminho in ((r"inscricoes", "/feed/subscriptions"), (r"historico", "/feed/history"),
                                (r"assistir mais tarde", "/playlist?list=WL"), (r"shorts", "/shorts"),
                                (r"playlists", "/feed/playlists"), (r"gostei|curtidos", "/playlist?list=LL"),
                                (r"downloads", "/feed/downloads"), (r"meu canal|seu canal", "/feed/you")):
            if re.search(rf"\b({padrao})\b", puro):
                return base + caminho
        return base + "/"

    # =================================================================
    def _cmd_youtube(self, t: str) -> bool:
        canais = self.cfg.get("canais_youtube") or {}
        fala_de_youtube = re.search(r"\b(youtube|canal|video|ultimo video)\b", t)
        if not fala_de_youtube:
            nome = _tirar_enfeites(t)
            # Programa ou site com esse nome ganha do canal (ex.: canal "Spotify" x programa "spotify")
            outros = {**(self.cfg.get("programas") or {}), **(self.cfg.get("sites") or {})}
            if nome in {_tirar_enfeites(normalizar(k)) for k in outros}:
                return False
            if nome not in {_tirar_enfeites(normalizar(k)) for k in canais}:
                return False

        if re.search(r"\b(desse|deste|nesse|neste|dessa|desta) canal\b", t) and self._ultimo_video_da_pagina():
            return True
        if contem(t, "ultimo video"):
            self._abrir_ultimo_video(t)
            return True

        if re.search(r"\bcanal\b", t):
            self._abrir_canal(t)
            return True

        busca = re.search(r"\b(toca|pesquisa)\b (.+?)( no youtube)?$", t)
        if busca and "youtube" in t:
            termo = self._original(busca.group(2).replace("no youtube", "").strip())
            if busca.group(1) == "pesquisa":
                self.voz.falar(f"Procurando {termo} no YouTube.")
                self._abrir_youtube(youtube.url_busca(termo))
            else:
                self.voz.falar(random.choice([f"Soltando {termo}!", f"Bora de {termo}.", f"Achando {termo} pra você."]))
                self._abrir_youtube(youtube.buscar_video(termo) or youtube.url_busca(termo))
            return True

        if contem(t, "youtube"):
            if self._site_ja_aberto("YouTube", "https://www.youtube.com"):
                return True
            self._abrir_youtube("https://www.youtube.com")
            self.falar("ok")
            return True
        # "abre <nome exato de um canal>": abre o ultimo video dele
        nomes = {normalizar(k) for k in canais}
        if re.search(r"\babre\b", t) and _tirar_enfeites(t) in {_tirar_enfeites(n) for n in nomes}:
            self._abrir_ultimo_video(t)
            return True
        return False

    def _achar_canal(self, frase: str):
        canais = self.cfg.get("canais_youtube") or {}
        nome = _nome_do_canal(frase)
        return (melhor_correspondencia(nome, canais) or melhor_correspondencia(frase, canais), nome)

    def _ultimo_video_da_pagina(self) -> bool:
        """ "toca o último vídeo desse canal": o canal da aba do YouTube que você está vendo."""
        yt = self._yt()
        info = yt.info() if yt and hasattr(yt, "info") else {}
        url = str(info.get("url") or "")
        canal = re.match(r"(https://www\.youtube\.com/(@[^/?#]+|channel/[^/?#]+|c/[^/?#]+))", url)
        base = canal.group(1) if canal else str(info.get("canal_link") or "")
        if not base:
            return False
        self.voz.falar(f"Abrindo o último vídeo {('do ' + info['canal']) if info.get('canal') else 'desse canal'}.")
        yt.abrir(base.rstrip("/") + "/videos")
        for _ in range(8):   # espera a lista de videos aparecer
            time.sleep(0.8)
            lista = yt.resultados()
            if lista:
                yt.abrir(lista[0]["link"])
                return True
        self.voz.falar("Abri os vídeos do canal. O primeiro da lista é o mais novo.")
        return True

    def _abrir_ultimo_video(self, frase: str) -> None:
        canais = self.cfg.get("canais_youtube") or {}
        chave, nome_falado = self._achar_canal(frase)
        if not chave:
            nome_falado = self._original(nome_falado)
            self.voz.falar(f"Não conheço o canal {nome_falado}. Vou abrir a busca pelos vídeos mais recentes.")
            self._abrir_youtube(youtube.url_busca(nome_falado, mais_recentes=True))
            return
        self.voz.falar(random.choice([f"Buscando o último do {chave}.", f"Deixa eu ver o que saiu no {chave}.",
                                      f"Já vou abrir o vídeo mais novo do {chave}."]))
        link = youtube.ultimo_video(canais[chave])
        if link:
            self._abrir_youtube(link)
        else:
            self.voz.falar("Não consegui achar o vídeo, vou abrir o canal.")
            self._abrir_youtube(youtube.url_canal(canais[chave]) + "/videos")

    def _abrir_canal(self, frase: str) -> None:
        canais = self.cfg.get("canais_youtube") or {}
        chave, nome_falado = self._achar_canal(frase)
        if chave:
            self.voz.falar(f"Abrindo o canal {chave}.")
            self._abrir_youtube(youtube.url_canal(canais[chave]))
        else:
            nome_falado = self._original(nome_falado)
            self.voz.falar(f"Não conheço esse canal. Vou pesquisar {nome_falado} no YouTube.")
            self._abrir_youtube(youtube.url_busca(nome_falado))

    # =================================================================
    #  Streamings: "toca Agentes da Shield na Disney"
    # =================================================================
    # nome: (dominio, endereco da busca, jeitos de falar). Com "{}" o nome vai no endereco; sem, o Mestre
    # abre a pagina e DIGITA no campo de busca (a Disney nova nao aceita busca pelo endereco).
    STREAMINGS = {
        "Netflix": ("netflix.com", "https://www.netflix.com/search?q={}", r"netflix|netiflix|netflics"),
        "Disney": ("disneyplus.com", "https://www.disneyplus.com/", r"disney( plus| mais)?"),
        "Prime Video": ("primevideo.com", "https://www.primevideo.com/search/ref=atv_nb_sug?ie=UTF8&phrase={}",
                        r"prime( video)?|amazon prime( video)?"),
        "HBO Max": ("hbomax.com", "https://play.hbomax.com/search", r"hbo( max)?|agaebeo( max)?|max"),
        "Globoplay": ("globoplay.globo.com", "https://globoplay.globo.com/busca/?q={}", r"globo ?play"),
    }
    VERBOS_ASSISTIR = r"(toca|tocar|toque|reproduz|reproduzir|reproduza|assiste|assistir|assista|continua|continuar|" \
                      r"continue|continuar assistindo|coloca|coloque|abre|abra|abrir|poe|bota|procura|procure|pesquisa|" \
                      r"pesquise|quero ver|quero assistir|play|da play|inicia|iniciar|comeca|comecar)"
    TIPOS_DE_VIDEO = r"(a |o )?(serie|seriado|filme|desenho|anime|documentario|novela|episodio|temporada)"

    # "abre minha série", "continua a série que eu estava vendo": não tem título (não procura "minha")
    SEM_TITULO = r"(minha|meu|minhas|meus|aquela|aquele|essa|esse|(o |a )?que eu (estava|tava) (vendo|assistindo))"
    CONTINUAR_SERIE = r"\b(continua|continuar|continue|retoma|retomar|de onde (eu )?parei)\b"
    PAUSA_STREAMING = 1.5   # entre as tentativas na página (os testes põem 0)

    def _cmd_streaming(self, t: str) -> bool:
        """Separa serviço, título, perfil ("no perfil Arthur"), monitor e ação (tocar ou continuar). O que
        faltar e tiver mais de uma possibilidade vira pergunta antes de abrir qualquer coisa."""
        puro, perfil_falado = perfil_da_frase(self._pedido_puro())
        qual = next((nome for nome, (_, _, jeitos) in self.STREAMINGS.items()
                     if re.search(rf"\b(na|no|pela|pelo|da|do|em) ({jeitos})\b", puro)), None)
        sem_preposicao = False
        if not qual and perfil_falado:   # "abre a Netflix no perfil Mestre"
            qual = next((nome for nome, (_, _, jeitos) in self.STREAMINGS.items()
                         if re.search(rf"\b({jeitos})\b", puro)), None)
            sem_preposicao = bool(qual)
        tem_tipo = re.search(rf"\b{self.TIPOS_DE_VIDEO}\b", puro)
        # "quero assistir Fallout": é vídeo mesmo sem dizer onde (pergunta o serviço; "toca X" continua sendo música)
        quer_assistir = re.match(r"^(eu )?(quero |vou |bora )?(assistir|assiste|assista|continuar assistindo|"
                                 r"continua assistindo)\b", puro)
        if not re.search(rf"\b{self.VERBOS_ASSISTIR}\b", t + " " + puro) or not (qual or tem_tipo or quer_assistir):
            return False
        continuar = bool(re.search(self.CONTINUAR_SERIE, puro))
        titulo = puro
        if qual:
            prep = "((na|no|pela|pelo|da|do|em) )?" if sem_preposicao else "(na|no|pela|pelo|da|do|em) "
            titulo = re.sub(rf"\b{prep}({self.STREAMINGS[qual][2]})\b( que (esta|ta) )?"
                            r"( aberta| aberto)?( (na|no) (janela|monitor|tela) \w+)?", " ", titulo)
        titulo = re.sub(rf"\b(quero |eu quero |pode )?{self.VERBOS_ASSISTIR}\b|\b{self.TIPOS_DE_VIDEO}\b|"
                        r"\b(de onde (eu )?parei|do comeco|agora|pra mim|por favor|ai|tocar|assistindo)\b", " ", titulo)
        palavras = titulo.split()
        while palavras and palavras[0] in ("a", "o", "as", "os", "de", "do", "da", "e", "que"):   # so nas pontas
            palavras.pop(0)
        while palavras and palavras[-1] in ("a", "o", "as", "os", "de", "do", "da", "e", "que"):
            palavras.pop()
        titulo = " ".join(palavras)
        if re.fullmatch(self.SEM_TITULO, titulo):
            titulo = ""
        if not titulo:
            if not (tem_tipo or perfil_falado):
                return False
            self._streaming_sem_titulo(qual, perfil_falado, continuar)
            return True
        titulo = self._original(titulo)
        if not qual:
            # nunca escolhe o serviço sozinho (nem pelo histórico): pergunta
            self.perguntar("Em qual serviço? Netflix, Disney, Prime, HBO Max, Globoplay ou YouTube?",
                           lambda r, tt=titulo, pf=perfil_falado, c=continuar: self._responder_streaming(r, tt, pf, c),
                           espera=15)
            return True
        self._escolher_perfil(qual, perfil_falado,
                              lambda perfil, aba: self._tocar_no_streaming(qual, titulo, perfil, aba, continuar))
        return True

    def _responder_streaming(self, resposta: str, titulo: str, perfil_falado: str | None = None,
                             continuar: bool = False) -> None:
        n = normalizar(resposta)
        qual = self._servico_falado(n)
        if qual == "YouTube":
            self.voz.falar(f"Procurando {titulo} no YouTube.")
            self._abrir_youtube(youtube.buscar_video(titulo) or youtube.url_busca(titulo))
        elif qual:
            self._escolher_perfil(qual, perfil_falado,
                                  lambda perfil, aba: self._tocar_no_streaming(qual, titulo, perfil, aba, continuar))
        else:
            self.voz.falar("Não peguei o streaming. Fala de novo: toca a série na Disney, por exemplo.")

    def _streaming_sem_titulo(self, qual: str | None, perfil_falado: str | None, continuar: bool) -> None:
        """ "abre minha série", "continua a série na Disney", "abre a Netflix no perfil Mestre": abre o serviço
        (um só aberto = ele; senão pergunta qual) no perfil certo e pede o nome. Não dá play em nada."""
        if not qual:
            abertos = sorted({s for s in map(self._servico_da_aba, self._abas_abertas()) if s in self.STREAMINGS})
            if len(abertos) == 1:
                qual = abertos[0]
            else:
                def responder(resposta: str):
                    escolhido = self._servico_falado(resposta)
                    if escolhido in self.STREAMINGS:
                        self._streaming_sem_titulo(escolhido, perfil_falado, continuar)
                    else:
                        self.voz.falar("Não peguei o serviço. Não abri nada.")
                opcoes = abertos or list(self.STREAMINGS)
                self.perguntar("Em qual serviço? " + ", ".join(opcoes[:-1]) + " ou " + opcoes[-1] + "?",
                               responder, espera=15)
                return
        self._escolher_perfil(qual, perfil_falado,
                              lambda perfil, aba: self._abrir_no_perfil(qual, perfil, aba, continuar))

    def _abrir_no_perfil(self, qual: str, perfil: str | None, aba: int | None, continuar: bool) -> None:
        """Abre (ou traz para a frente) o serviço e, com a extensão, escolhe o perfil. Sem título: não toca nada."""
        dominio = self.STREAMINGS[qual][0]
        inicio = f"https://{'' if dominio.count('.') > 1 else 'www.'}{dominio}/"
        ext = self._extensao()
        if not ext:
            sistema.abrir_site(inicio)
            self.voz.falar(f"Abri {self._no(qual, '')}. " + (
                f"Sem a extensão eu não consigo conferir o perfil. Escolha o perfil {perfil} na tela." if perfil else
                "Fala o nome da série que eu procuro."))
            return
        if not aba and not sistema.JANELA_NOVA:   # já aberto: usa a aba (não recarrega o que está tocando)
            existentes = [a for a in self._abas_abertas() if _mesmo_site(a.get("url", ""), dominio)]
            aba = max(existentes, key=self._preferencia_de_aba)["id"] if existentes else None
        if aba and not sistema.JANELA_NOVA:
            abas = self._abas_abertas()
            achada = next((a for a in abas if a.get("id") == aba), None)
            if achada and sistema.MONITOR_ALVO and self._monitor_da_aba(achada, abas) != sistema.MONITOR_ALVO:
                self._mover_achado({"tipo": "aba", "aba": achada, "nome": qual},
                                   {"monitor": sistema.MONITOR_ALVO, "separar": True, "deixar": False})
            else:
                try:
                    ext.pedir("focar", aba, espera=4)
                except Exception as erro:
                    log.info("Extensao nao focou a aba do streaming: %s", erro)
        else:
            aba = self._aba_do_streaming(ext, dominio, inicio)
        self._em_segundo_plano(self._depois_de_abrir_no_perfil, ext, aba, qual, perfil, continuar)

    def _em_segundo_plano(self, funcao, *args) -> None:
        threading.Thread(target=funcao, args=args, daemon=True).start()

    def _depois_de_abrir_no_perfil(self, ext, aba, qual: str, perfil: str | None, continuar: bool) -> None:
        if perfil and not self._garantir_perfil(ext, aba, qual, perfil, self.PAUSA_STREAMING):
            return
        self.voz.falar(f"Abri {self._no(qual, '')}" + (f" no perfil {perfil}" if perfil else "") +
                       (". Fala o nome da série que eu continuo de onde parou." if continuar else
                        ". Fala o nome do que você quer assistir."))

    def _garantir_perfil(self, ext, aba, servico: str, perfil: str, pausa: float) -> str | None:
        """Na aba do serviço: tela "Quem está assistindo?" = clica no perfil pelo NOME exato ("escolhi");
        aba já confirmada nesse perfil = segue ("ja"). Não conseguiu confirmar = avisa e para (None)."""
        dominio = self._servicos_de_video()[servico][0]
        nao_achou = 0
        for _ in range(8):
            time.sleep(pausa)
            try:
                r = ext.pedir("perfil", {"aba": aba, "dominio": dominio, "nome": perfil}, espera=6)
            except Exception as erro:
                log.info("Extensao nao conferiu o perfil: %s", erro)
                r = None
            r = r if isinstance(r, dict) else {}
            aba = r.get("aba") or aba
            resultado = r.get("resultado")
            if resultado == "selecionei":
                self._lembrar_perfil(aba, servico, perfil)
                return "escolhi"
            if resultado == "nao_achei":
                nao_achou += 1
                if nao_achou >= 3:
                    self.voz.falar(f"Não achei o perfil {perfil} na tela de perfis {self._no(servico, 'd')}. "
                                   "Deixei a página aberta sem iniciar nada.")
                    return None
            sessao = self._sessoes().get(aba) or {}
            if resultado == "sem_tela" and sessao.get("servico") == servico and sessao.get("perfil") == perfil:
                return "ja"
        self.voz.falar(f"Não consegui confirmar o perfil {perfil} {self._no(servico)}. Deixei a página aberta sem "
                       "iniciar o vídeo. Se ela já estiver no perfil certo, fala o pedido de novo que eu confirmo com você.")
        return None

    def _tocar_no_streaming(self, qual: str, titulo: str, perfil: str | None = None, aba_escolhida: int | None = None,
                            continuar: bool = False) -> None:
        dominio, busca, _ = self.STREAMINGS[qual]
        url = busca.format(quote(titulo)) if "{}" in busca else busca
        ext = self._extensao()
        self.voz.falar(f"Procurando {titulo} {self._no(qual)}" + (f" no perfil {perfil}." if perfil else "."))
        if not ext:
            sistema.abrir_site(url)
            if perfil:
                self.voz.falar(f"Sem a extensão eu não consigo conferir o perfil. Confira se está no perfil {perfil}.")
            elif "{}" not in busca:
                self.voz.falar("Sem a extensão do Brave eu não consigo digitar na busca. Digite o nome lá.")
            return
        aba = None
        try:
            aba = self._aba_do_streaming(ext, dominio, url, aba_escolhida)
        except Exception as erro:
            log.info("Extensao nao abriu a busca (%s)", erro)
            sistema.abrir_site(url)
        self._em_segundo_plano(self._seguir_no_streaming, ext, aba, dominio, titulo, "{}" in busca, None,
                               perfil, url, continuar, qual)

    def _aba_do_streaming(self, ext, dominio: str, url: str, aba_escolhida: int | None = None) -> int | None:
        """Onde abrir a busca: "numa janela nova" = janela nova; a aba já escolhida (perfil confirmado), levada
        ao monitor pedido se preciso; com monitor pedido, a aba do serviço que JÁ está nesse monitor, senão a aba
        do serviço levada para lá (sozinha numa janela), senão janela nova lá; sem monitor, a aba do serviço que
        já existe (a extensão escolhe) ou uma aba nova."""
        if sistema.JANELA_NOVA:
            sistema.abrir_site(url)
            return None
        if aba_escolhida:
            abas = self._abas_abertas()
            achada = next((a for a in abas if a.get("id") == aba_escolhida), None)
            if achada and sistema.MONITOR_ALVO and self._monitor_da_aba(achada, abas) != sistema.MONITOR_ALVO:
                self._mover_achado({"tipo": "aba", "aba": achada, "nome": dominio},
                                   {"monitor": sistema.MONITOR_ALVO, "separar": True, "deixar": False})
            if achada:
                return (ext.pedir("ir", {"url": url, "dominio": dominio, "aba": aba_escolhida}, espera=6) or {}).get("id") \
                    or aba_escolhida
        if not sistema.MONITOR_ALVO:
            return (ext.pedir("ir", {"url": url, "dominio": dominio}, espera=6) or {}).get("id")
        abas = self._abas_abertas()
        do_site = [a for a in abas if _mesmo_site(a.get("url", ""), dominio)]
        ali = [a for a in do_site if self._monitor_da_aba(a, abas) == sistema.MONITOR_ALVO]
        aba = max(ali or do_site, key=self._preferencia_de_aba, default=None)
        if aba is None:
            sistema.abrir_site(url)   # não estava aberto: janela nova no monitor pedido
            return None
        if not ali:
            self._mover_achado({"tipo": "aba", "aba": aba, "nome": dominio},
                               {"monitor": sistema.MONITOR_ALVO, "separar": True, "deixar": False})
        return (ext.pedir("ir", {"url": url, "dominio": dominio, "aba": aba["id"]}, espera=6) or {}).get("id") or aba["id"]

    CONTINUAR_TEXTOS = ["continuar assistindo", "continuar", "retomar", "continue assistindo", "continue watching",
                        "resume", "continue"]

    def _seguir_no_streaming(self, ext, aba, dominio: str, titulo: str, busca_no_endereco: bool,
                             pausa: float | None = None, perfil: str | None = None, url: str = "",
                             continuar: bool = False, servico: str = "") -> None:
        """Depois de abrir o site: 0) o perfil pedido (tela "Quem está assistindo?")  1) digita o nome na busca
        2) clica no título  3) "continuar assistindo" (pedido de continuar: só isso, nunca "assistir do começo")."""
        pausa = self.PAUSA_STREAMING if pausa is None else pausa
        if perfil:
            servico = servico or next((n for n, (d, _, _) in self.STREAMINGS.items() if d == dominio), "")
            escolha = self._garantir_perfil(ext, aba, servico, perfil, pausa)
            if not escolha:
                return
            if escolha == "escolhi" and busca_no_endereco and url:   # a tela de perfis pode ter perdido a busca
                try:
                    ext.pedir("ir", {"aba": aba, "dominio": dominio, "url": url}, espera=6)
                except Exception as erro:
                    log.info("Streaming: busca depois do perfil falhou (%s)", erro)
        alvo = {"aba": aba, "dominio": dominio}

        def pedir(acao: str, **extra):
            try:
                return ext.pedir(acao, {**alvo, **extra}, espera=8)
            except Exception as erro:
                log.info("Streaming: %s falhou (%s)", acao, erro)
                return "erro"

        # 1) busca: tenta por uns 20 s (a pagina demora a montar; as vezes precisa abrir a lupa antes)
        digitou = False
        for _ in range(14):
            time.sleep(pausa)
            r = pedir("buscar", texto=titulo)
            if r in ("digitei", "ja"):
                digitou = True
                break
            if r == "sem_busca" and busca_no_endereco:
                break   # o nome ja foi no endereco: segue para o clique
        if not digitou and not busca_no_endereco:
            self.voz.falar("Abri o site mas não achei o campo de busca. Você já entrou na sua conta?")
            return
        # 2) o resultado com o nome (prefere a capa do filme/série)
        for _ in range(8):
            time.sleep(pausa)
            r = pedir("clicar", textos=[titulo], modo="titulo")
            if r not in ("nao_achei", "sem_aba", "erro"):
                break
        else:
            self.voz.falar(f"Não achei {titulo} nos resultados. Fala: clica em e o nome que aparece.")
            return
        # 3) play: "continuar assistindo" primeiro (de onde parou)
        textos = self.CONTINUAR_TEXTOS if continuar else ["continuar assistindo", "continuar", "retomar", "assistir",
                                                           "assista", "reproduzir", "play", "comecar", "resume", "watch"]
        for _ in range(6):
            time.sleep(pausa)
            r = pedir("clicar", textos=textos)
            if r not in ("nao_achei", "sem_aba", "erro"):
                return
        if continuar:
            self.voz.falar(f"Não achei de onde você parou em {titulo}. Pra começar do início fala: clica em assistir.")
            return
        self.voz.falar("Abri a página. Pra dar play fala: clica em assistir.")

    def _cmd_clicar(self, t: str) -> bool:
        """ "clica em continuar assistindo" (… "do monitor 2"): clica pelo texto que aparece na tela (extensao).
        Com várias janelas do navegador na tela, clica naquela que tem esse texto (ou pergunta qual)."""
        puro, monitor = self._monitor_da_frase(self._pedido_puro())
        achado = re.match(r"^(clica|clique|clicar|aperta|aperte)( no| na| em| o| a| nos| nas)?( botao| link| opcao| aba| icone)?"
                          r"( de| do| da| escrito| que diz| com o nome)? (.+)$", puro)
        if not achado:
            return False
        ext = self._extensao()
        if not ext:
            self.voz.falar("Pra clicar pelo nome eu preciso da extensão no Brave.")
            return True
        alvo = self._original(achado.group(5))
        monitor = monitor or sistema.MONITOR_ALVO
        sistema.MONITOR_ALVO = None
        abas = self._abas_abertas()

        def tem(aba: dict) -> float:   # quanto o texto dessa aba combina com o falado (0 = nao tem)
            try:
                r = ext.pedir("clicar", {"aba": aba["id"], "textos": [alvo], "so_ver": True}, espera=4)
            except Exception as erro:
                log.debug("Extensao nao conferiu o texto na aba %s: %s", aba.get("id"), erro)
                return 0
            return float(r.get("nota", 0)) if isinstance(r, dict) else 0

        def continuar(aba_id):
            r = ext.pedir("clicar", {"aba": aba_id, "textos": [alvo]} if aba_id else {"textos": [alvo]}, espera=6)
            if r in ("nao_achei", "sem_aba"):
                self.voz.falar(f"Não achei {alvo} na tela.")
        self._escolher_aba(self._abas_na_tela(abas), abas, alvo, monitor, continuar, tem)
        return True

    def _cmd_tocar(self, t: str) -> bool:
        """ "toca Feliz do DJ Petroski" (sem dizer onde): música vai para o Spotify (ou o YouTube, no painel)."""
        achado = re.match(r"^toca (a |o |uma |um )?(musica |playlist |album |cancao |som )?(.+)$", t)
        if not achado or re.search(r"\b(youtube|spotify)\b", t):
            return False
        onde = str((self.cfg.get("spotify") or {}).get("tocar_musica_em", "spotify"))
        if onde == "youtube":
            return self._cmd_youtube(f"toca {achado.group(3)} no youtube")
        return self._cmd_spotify(f"toca {achado.group(2) or ''}{achado.group(3)} no spotify")
