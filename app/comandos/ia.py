"""IA: conversa livre, interpretacao de frases soltas, pensamento em segundo plano e fila.

Mixin do Executor (app/comandos/__init__.py): os metodos usam self.voz, self.cfg, self.falar...
do nucleo e chamam metodos dos outros mixins pelo self.
"""
import logging
import re
import threading
import time
from .. import estado, memoria
from ..texto import normalizar

from .base import _resumir

log = logging.getLogger(__package__)  # "app.comandos", o mesmo logger de antes da divisao


class IAMixin:
    # =================================================================
    #  IA: conversa livre e interpretacao de frases soltas
    # =================================================================
    def _interpretar_com_ia(self, frase: str) -> None:
        resumo = self._resumo_de_comandos()
        self._pensar(frase, lambda: self.cerebro.interpretar(frase, resumo),
                     lambda decisao: self._usar_interpretacao(decisao, frase))

    def _comando_da_memoria(self, frase: str) -> bool:
        """Frase que a IA ja transformou em comando antes (memoria/historico): executa direto, sem IA."""
        try:
            texto_ia = memoria.comando_ja_descoberto(frase)
        except Exception:
            log.exception("Memoria de comandos da IA")
            return False
        if not texto_ia:
            return False
        original = self._frase_original
        self._frase_original = texto_ia
        comando = self._separar_monitor(self.vocab.traduzir(texto_ia))
        if comando and self._tentar_comandos(comando):
            self._rota = f"memoria da ia: {self.ultimo_comando}"
            self._entendi = comando
            log.info("Comando que a IA ja tinha descoberto: %r -> %r", frase, texto_ia)
            return True
        self._frase_original = original
        return False

    def _usar_interpretacao(self, decisao: dict | None, frase: str) -> None:
        decisao = decisao or {}
        if decisao.get("tipo") == "comando":
            texto_ia = str(decisao.get("texto", ""))
            # os comandos leem a "frase falada": passa a ser a frase da IA (e nao o "pode falar" de agora)
            self._frase_original = texto_ia
            comando = self._separar_monitor(self.vocab.traduzir(texto_ia))
            log.info("IA entendeu como comando: %r", comando)
            if comando and self._tentar_comandos(comando):
                # (na exportacao: frases que a IA transformou em comando = comandos que faltam no vocabulario)
                # e a "memoria": so grava depois de ~30s sem correcao (ou na hora, se repetir igual),
                # senao um erro da IA (tipo "dica de livro" virar "abre o youtube") fica preso pra sempre
                self._agendar_memoria_ia(frase, texto_ia, comando, self.ultimo_comando)
                return
        if decisao.get("tipo") == "pergunta" and decisao.get("texto"):
            # a IA precisa de uma decisao sua (qual dos dois? tem certeza?): pergunta e pensa de novo com a resposta
            pergunta = str(decisao["texto"])
            self.perguntar(pergunta, lambda resposta, f=frase, p=pergunta: self._interpretar_com_ia(
                f"{f} (eu perguntei: {p} e o usuario respondeu: {resposta})"), espera=15)
            return
        self._responder(decisao.get("texto") or self.sortear("nao_entendi"), frase)

    def _agendar_memoria_ia(self, frase: str, texto_ia: str, comando: str, rota: str) -> None:
        """So grava frase->comando na memoria (`memoria.comando_ja_descoberto`) depois de rodar sem
        correcao por ~30s; se a mesma frase virar o mesmo comando de novo antes disso, confirma na hora."""
        alvo = normalizar(frase)
        anterior = self._pendente_ia
        if anterior and normalizar(anterior["frase"]) == alvo and anterior["comando"] == comando:
            anterior["timer"].cancel()
            memoria.confirmar_comando_ia(frase, texto_ia, comando, rota)
            self._pendente_ia = None
            return
        pendente: dict = {"frase": frase, "ia_texto": texto_ia, "comando": comando, "rota": rota}

        def _confirmar() -> None:
            if self._pendente_ia is pendente:
                self._pendente_ia = None
            memoria.confirmar_comando_ia(frase, texto_ia, comando, rota)

        timer = threading.Timer(30.0, _confirmar)
        timer.daemon = True
        pendente["timer"] = timer
        self._pendente_ia = pendente
        timer.start()

    def _cancelar_memoria_ia(self, frase: str = "") -> None:
        """FEEDBACK / "nao era isso" / cancelar logo depois: nao deixa a IA memorizar (nem usar)
        esta frase como comando, e apaga da memoria se ja tinha ficado gravada antes."""
        pendente = self._pendente_ia
        if pendente:
            pendente["timer"].cancel()
            self._pendente_ia = None
        alvo = frase or (pendente["frase"] if pendente else self._ultimo.get("ouvi", ""))
        if alvo:
            apagados = memoria.esquecer_comando_ia(alvo)
            if apagados:
                log.info("Memoria da IA apagada por correcao: %r (%d entrada(s))", alvo, len(apagados))

    def _resumo_de_comandos(self) -> str:
        c = self.cfg
        rotinas = [f for r in (c.get("rotinas") or []) for f in r.get("frases", [])[:1]]
        return (
            "Comandos que existem (use EXATAMENTE este formato):\n"
            "- abre <programa ou site>. Programas: " + ", ".join(c.get("programas") or {}) + ". "
            "Sites: " + ", ".join(c.get("sites") or {}) + "\n"
            "- abre o ultimo video do <canal>. Canais: " + _resumir(list(c.get("canais_youtube") or {})) + "\n"
            "- abre o canal <canal> | toca <musica> no youtube | pesquisa <termo> no youtube\n"
            "- rotinas: " + ", ".join(rotinas) + "\n"
            "- que horas sao | que dia e hoje | aumenta o volume | abaixa o volume | muta\n"
            "- pausa | desliga a tela | liga a tela | bloqueia o computador\n"
            "- me lembra de <assunto> em <N> minutos | anota <texto> | le minhas notas\n"
            "- pesquisa <termo> (Google) | agente ipm <pergunta> | le o que eu copiei\n"
            "- muda a voz | fala mais rapido | fala mais devagar | aprende um atalho\n"
            "- anota uma melhoria <ideia> | aplica as melhorias\n"
            "- spotify: toca a playlist <nome> no spotify | toca <musica> no spotify | pausa | continua | proxima musica | "
            "aumenta o volume do spotify | spotify no 50 | muta o spotify\n"
            "- youtube aberto: proximo video | pausa o video | continua o video | tela cheia | da like | se inscreve | "
            "abre o terceiro video | abre o video do <canal ou titulo> | le os titulos | vai pras inscricoes "
            "(com YouTube em mais de uma tela: acrescente 'do monitor <N>')\n"
            "- navegador: volta a pagina | avanca a pagina | proxima aba | fecha a aba | clica em <texto na tela> "
            "(opcional: 'do monitor <N>')\n"
            "- desliga (o assistente) | reinicia\n"
            "- janelas: joga a <janela> pro monitor <1, 2, 3, principal> | separa a <aba> pro monitor 2 | "
            "junta o <aba> com a <aba> | minimiza | maximiza\n"
            "- streaming: toca <serie ou filme> na <netflix, disney, prime video, hbo max, globoplay>\n"
            "- pode descansar | exporta o historico\n"
            "Se nao for nenhum destes, responda como conversa (tipo resposta). Nunca invente um comando fora da lista."
        )

    def _conversar(self, frase: str, perfil: str = "geral") -> None:
        if not self.cerebro.ligado:
            self.falar("nao_entendi")
            return
        self._pensar(frase, lambda: self.cerebro.perguntar(frase, perfil),
                     lambda resposta: self._responder(resposta or self.sortear("nao_entendi"), frase))

    # =================================================================
    #  Pensamento em segundo plano: a IA demorou? O Mestre volta a ouvir, guarda a
    #  resposta e so fala quando voce pedir ("pode falar", "qual a resposta?")
    # =================================================================
    def _cfg_cerebro(self) -> dict:
        return self.cfg.get("cerebro") or {}

    def _pensar(self, frase: str, trabalho, entregar, imediato: bool = False) -> None:
        """Coloca o pedido na FILA da IA (um de cada vez, na ordem). Nunca descarta o anterior.
        Espera no maximo `segundo_plano_seg` (so se for o unico da fila); depois volta a ouvir.
        imediato: terminou em segundo plano? Entrega na hora (tarefa interna, nao espera o "pode falar")."""
        limite = float(self._cfg_cerebro().get("segundo_plano_seg", 3))
        with self._trava_pensamento:
            self._pensamento_id += 1
            meu = self._pensamento_id
            na_frente = sum(1 for x in self._pensamentos if x["estado"] == "pensando")
            p = {"id": meu, "pergunta": frase, "estado": "pensando", "inicio": time.time(), "resultado": None,
                 "fundo": False, "entregar": entregar, "trabalho": trabalho, "pronto": threading.Event(),
                 "imediato": imediato}
            self._pensamentos.append(p)
            if self._trabalhador_ia is None or not self._trabalhador_ia.is_alive():
                self._trabalhador_ia = threading.Thread(target=self._trabalhar_fila_ia, daemon=True, name="fila-ia")
                self._trabalhador_ia.start()
            # atras de outro na fila (ou pedido feito pela propria fila): nem espera, ja vai para segundo plano
            ja_fundo = na_frente > 0 or threading.current_thread() is self._trabalhador_ia
            p["fundo"] = ja_fundo
        if na_frente:
            log.info("Pensamento na fila (%d na frente): %r", na_frente, frase)
        self._fila_ia.put(p)
        estado.definir("pensando", frase)
        if ja_fundo:
            self._atualizar_indicador()
            self._aviso_curto("fundo")
            return
        if str(self._cfg_cerebro().get("aviso_som", "nenhum")) != "nenhum":
            self.voz.falar_em_segundo_plano(self.sortear("pensando"))
        if not p["pronto"].wait(limite):
            with self._trava_pensamento:
                fundo = p["estado"] == "pensando" and p in self._pensamentos
                if fundo:
                    p["fundo"] = True
            if fundo:   # demorou: vai para segundo plano e o Mestre volta a ouvir
                self._atualizar_indicador()
                self._aviso_curto("fundo")
                return
        self._entregar_se_pronto(meu)

    def _trabalhar_fila_ia(self) -> None:
        """Uma thread so: a IA pensa um pedido de cada vez (Ollama e historico da conversa nao se misturam)."""
        while True:
            p = self._fila_ia.get()
            with self._trava_pensamento:
                cancelado = p not in self._pensamentos
            if cancelado:
                p["pronto"].set()
                continue
            try:
                resultado = p["trabalho"]()
            except Exception:
                log.exception("A IA falhou")
                resultado = None
            try:
                self._pensamento_terminou(p["id"], resultado)
            except Exception:
                log.exception("Erro entregando o pensamento")
            finally:
                p["pronto"].set()

    def _atualizar_indicador(self) -> None:
        """Bolinha: roxa se algum pedido (em segundo plano) ainda pensa, verde se tem resposta guardada."""
        with self._trava_pensamento:
            fundo = [x for x in self._pensamentos if x["fundo"]]
        pensando = [x for x in fundo if x["estado"] == "pensando"]
        lista = [{"pergunta": str(x["pergunta"])[:160], "inicio": x["inicio"], "estado": x["estado"]} for x in fundo]
        if pensando:
            estado.atualizar(pensamento="pensando", pensamento_pergunta=pensando[0]["pergunta"],
                             pensamento_desde=pensando[0]["inicio"], pensamentos_fila=len(pensando),
                             pensamentos_lista=lista)
        else:
            estado.atualizar(pensamento="pronto" if fundo else "", pensamentos_fila=0, pensamentos_lista=lista)

    def _achar_pensamento(self, meu: int) -> dict | None:
        return next((x for x in self._pensamentos if x["id"] == meu), None)

    def _pensamento_terminou(self, meu: int, resultado) -> None:
        with self._trava_pensamento:
            p = self._achar_pensamento(meu)
            if not p:
                return   # cancelado
            p["resultado"] = resultado
            p["estado"] = "pronto" if resultado else "falhou"
            fundo = p["fundo"]
        if not fundo:
            return   # quem esta esperando (sem segundo plano) entrega
        if self._descansando:   # descansando: nao fala nada; fica guardado (verde)
            self._atualizar_indicador()
            return
        if p["estado"] == "falhou":
            with self._trava_pensamento:
                if p in self._pensamentos:
                    self._pensamentos.remove(p)
            self._atualizar_indicador()
            self.voz.falar("A IA não conseguiu responder aquela pergunta. Tenta de novo daqui a pouco.")
            return
        if p.get("imediato") or isinstance(resultado, dict) and resultado.get("tipo") in ("comando", "pergunta"):
            # A IA descobriu que era um COMANDO (ou precisa perguntar algo): faz na hora, sem esperar "pode falar"
            log.info("IA terminou em segundo plano com %s: executando", resultado.get("tipo"))
            self._esperar_voce_parar_de_falar()
            with self._trava_execucao:
                self._entregar_se_pronto(meu)
            return
        self._atualizar_indicador()
        texto = resultado if isinstance(resultado, str) else (resultado or {}).get("texto", "") \
            if isinstance(resultado, dict) else ""
        if texto:   # guarda ja no historico: mesmo que se perca, "repete a resposta" acha
            memoria.registrar(p["pergunta"], texto, "ia (guardada)")
        aviso = str(self._cfg_cerebro().get("aviso_ao_terminar", "falar_direto"))
        if aviso == "falar_direto" and not self._ditado_ativo:   # no ditado: fica guardada (indicador verde)
            self._esperar_voce_parar_de_falar()
            with self._trava_execucao:
                self._entregar_se_pronto(meu)
            return
        if aviso == "voz" and not self._ditado_ativo:
            self._aviso_curto("pronto")
            if self._pendente is None:
                self._pendente = self._responder_aviso_pensamento
                self._pendente_espera = 12.0
                estado.atualizar(conversa_ate=time.time() + 12)

    @staticmethod
    def _esperar_voce_parar_de_falar(limite: float = 10.0) -> None:
        """Nao fala por cima de voce: espera o microfone terminar a frase (no maximo alguns segundos)."""
        fim = time.time() + limite
        while time.time() < fim and estado.ler()["nome"] in ("gravando", "transcrevendo"):
            time.sleep(0.2)

    def _entregar_se_pronto(self, meu: int) -> None:
        with self._trava_pensamento:
            p = self._achar_pensamento(meu)
            if not p or p["estado"] == "pensando":
                return
            self._pensamentos.remove(p)
        self._atualizar_indicador()
        if p["estado"] == "falhou":
            self.falar("erro")
            return
        p["entregar"](p["resultado"])

    @property
    def _pensamento(self) -> dict | None:
        """O pedido mais antigo da fila (compatibilidade: "tem pensamento?")."""
        with self._trava_pensamento:
            return self._pensamentos[0] if self._pensamentos else None

    def entregar_pensamento(self) -> bool:
        """Fala a resposta guardada mais antiga (ou avisa que ainda esta pensando). Tambem pelo clique no indicador."""
        with self._trava_pensamento:
            prontos = [x for x in self._pensamentos if x["estado"] != "pensando"]
            pensando = [x for x in self._pensamentos if x["estado"] == "pensando"]
        if prontos:
            self._entregar_se_pronto(prontos[0]["id"])
            return True
        if not pensando:
            self.voz.falar("Não tem nenhuma resposta guardada.")
            return False
        extra = f" Tem {len(pensando)} pedidos na fila." if len(pensando) > 1 else ""
        self.voz.falar(f"Ainda tô pensando. Faz {int(time.time() - pensando[0]['inicio'])} segundos.{extra}")
        return True

    def cancelar_pensamento(self) -> None:
        """Descarta tudo que esta na fila da IA (o que ja esta rodando termina e e ignorado)."""
        with self._trava_pensamento:
            self._pensamentos.clear()
        estado.atualizar(pensamento="", pensamentos_fila=0, pensamentos_lista=[])

    def _responder_aviso_pensamento(self, resposta: str) -> None:
        n = normalizar(resposta)
        if re.search(r"\b(cancela|esquece|descarta|joga fora|deixa pra la)\b", n):
            self.cancelar_pensamento()
            self.voz.falar("Beleza, deixei pra lá.")
        elif re.search(r"\b(espera|depois|agora nao|mais tarde|segura|guarda|nao)\b", n):
            self.voz.falar("Beleza. Fica guardado. Quando quiser, fala: qual a resposta.")
        elif re.search(r"\b(sim|pode|fala|manda|quero|bora|claro|ok|beleza|vai|diz|conta)\b", n):
            self.entregar_pensamento()
        else:   # era outro pedido: a resposta continua guardada
            self._executar(resposta, self._frase_original)

    def _cmd_pensamento(self, t: str) -> bool:
        if not self._pensamento:
            return False
        puro = self._pedido_puro()
        if re.fullmatch(r"(pode )?(fala|falar|fala ai|diz|dizer|conta|contar)( ai)?", puro) or re.fullmatch(
                r"(fala|falar|diz|conta)", t):
            self.entregar_pensamento()
            return True
        if re.fullmatch(r"(cancela|esquece|deixa pra la|esquece isso)", t) or re.search(
                r"\b(para de pensar|cancela (o |esse )?pensamento|esquece (o |esse )?pensamento|"
                r"descarta (a resposta|o pensamento))\b", t):
            self.cancelar_pensamento()
            self.voz.falar("Beleza, deixei pra lá.")
            return True
        if re.search(r"\b(pode falar|fala o pensamento|qual (foi |e )?a resposta|o que voce pensou|"
                     r"fala a resposta|terminou de pensar|ja pensou|pode dizer|manda a resposta|"
                     r"e a resposta|resultado do pensamento)\b", t + " | " + puro):
            self.entregar_pensamento()
            return True
        return False

    def _cmd_esquecer(self, t: str) -> bool:
        if re.fullmatch(r"(esquece a conversa|nova conversa|limpa a conversa|esquece tudo)", t):
            self.cerebro.esquecer()
            self.voz.falar("Pronto, página em branco. Conversa nova.")
            return True
        return False
