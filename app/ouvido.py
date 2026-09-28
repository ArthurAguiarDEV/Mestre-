"""Ouvido do Mestre: fica escutando o microfone o tempo todo.

1. O Segmentador corta o som em frases, usando o limite de volume calibrado.
2. Cada frase e checada: chamaram "mestre"? (ou estamos no modo conversa?)
     modo_ativacao "whisper": o Whisper transcreve toda frase (mais preciso, usa mais CPU)
     modo_ativacao "vosk":    o Vosk procura so "mestre" antes (bem leve)
3. O Whisper transcreve e o comando vai para o Executor.
4. "Assessor" sozinho (ou so enchimento) NAO responde na hora: espera `espera_apos_palavra` s pelo resto
   ("Assessor... abre o YouTube" vira uma frase so). Nada vindo, responde curto e abre a conversa.
5. Frase que termina no meio (virgula, reticencias, "do", "que", "e"...) espera `espera_continuacao` s pela
   continuacao e junta as duas (a fala comprida nao vira 5 comandos).
6. Enquanto ele FALA (a fala toca em segundo plano), o microfone continua ouvindo, mas so vale frase que
   COMECA com a palavra de ativacao (o resto e o eco da propria voz: descartado com motivo "falando").
   Essa frase corta a fala na hora: "Assessor, para" so para; "Assessor, abre o Spotify" para e executa.
7. Detector local da palavra (opcional, `ouvido > detector_palavra`, app/palavra_local.py): ouve cada bloco e, fora
   da conversa/espera/ditado/descanso, so manda ao Whisper a frase em que ele ouviu a palavra (o resto e
   descartado com motivo "sem a palavra (detector local)", sem gastar o Whisper). Sem modelo: fluxo de sempre.
8. Toda frase descartada vai para memoria/ouvido.jsonl com o `motivo` (curta demais, transcricao vazia,
   sem a palavra, voz nao reconhecida, cortada pela voz do assistente, falando...).
"""
import json
import logging
import queue
import re
import threading
import time
from collections import deque

from . import estado, locutor, palavra_local
from .audio import BLOCO, TAXA, Segmentador, Transcritor, aplicar_ganho, guardar_diagnostico, nivel, sugerir_limiar
from .config import caminho_do_projeto, palavras_ativacao
from .texto import extrair_comando, frase_de_volta, normalizar, parecida
from .voz import Voz

log = logging.getLogger(__name__)


class Ouvido:
    # (padroes na classe: o teste automatico monta o Ouvido sem o __init__)
    voz = None
    interromper = True
    espera_cont = 1.5
    detector = None              # palavra_local.Detector (opcional): None = Whisper ouve tudo, como sempre

    def __init__(self, cfg: dict, voz: Voz):
        self.cfg = cfg
        self.voz = voz
        o = cfg.get("ouvido") or {}
        a = cfg.get("assistente") or {}
        self.microfone = o.get("microfone")
        self.variacoes = palavras_ativacao(cfg)
        self.acordar_tela = a.get("acordar_tela_ao_ouvir", True)
        self.modo = o.get("modo_ativacao", "whisper")
        self.limiar = float(o.get("limiar_volume") or 0)      # 0 = calibrar ao ligar
        self.ganho = float(o.get("ganho") or 1.0)
        self.silencio_fim = float(o.get("silencio_fim") or 0.8)
        self.max_frase = float(o.get("max_frase") or 60)
        self.diagnostico = bool(o.get("gravar_diagnostico", False))
        self.espera_palavra = espera_apos_palavra(cfg)
        self.espera_cont = espera_continuacao(cfg)
        self.interromper = bool(getattr(voz, "interromper", True))
        self._preparar_laco()

        self._vigia = None
        if self.modo == "vosk":
            from vosk import KaldiRecognizer, Model, SetLogLevel

            SetLogLevel(-1)
            pasta = caminho_do_projeto(o.get("modelo_vosk", "modelos/vosk-model-small-pt-0.3"))
            if not pasta.exists():
                raise SystemExit(f"Modelo Vosk nao encontrado em {pasta}. Rode o INSTALAR_E_CRIAR_ATALHO.bat de novo.")
            gramatica = json.dumps(sorted({normalizar(v) for v in self.variacoes}) + ["[unk]"])
            self._vigia = (KaldiRecognizer, Model(str(pasta)), gramatica)

        # Responder so a voz do dono (painel > Audio > Minha voz). Carrega em segundo plano.
        self.verificador = locutor.Verificador.do_config(cfg)

        # Detector local da palavra (painel > Audio). Desligado/sem modelo: None (fluxo de sempre).
        try:
            self.detector, self.detector_motivo = palavra_local.carregar(cfg)
        except Exception as erro:
            log.warning("Detector da palavra indisponível (%s)", erro)
            self.detector, self.detector_motivo = None, str(erro)

        self.transcritor = Transcritor(o.get("modelo_whisper", "small"), o.get("precisao", "equilibrado"),
                                       o.get("dispositivo", "auto"), palavras_de_dica(cfg), palavra=self.variacoes[0])
        # Aquece o Whisper (1 s de silencio) enquanto mede o ruido: a 1a frase nao demora mais que as outras
        threading.Thread(target=self.transcritor.aquecer, name="aquecer_whisper", daemon=True).start()

    # -----------------------------------------------------------------
    def _chamou_mestre_vosk(self, audio: bytes) -> bool:
        KaldiRecognizer, modelo, gramatica = self._vigia
        rec = KaldiRecognizer(modelo, TAXA, gramatica)
        rec.AcceptWaveform(audio)
        texto = json.loads(rec.FinalResult()).get("text", "")
        return any(p != "[unk]" for p in texto.split())

    def _voz_do_dono(self, audio: bytes, frase: str, em_conversa: bool) -> bool:
        """A frase ia ser executada: e a voz do dono? (desligado/sem cadastro/modelo carregando: sim)."""
        aceita, nota, motivo = self.verificador.verificar(audio, em_conversa=em_conversa)
        if nota is not None:
            log.info("Voz: nota %.2f (exigência %.2f) -> %s", nota, self.verificador.exigencia, motivo)
        if aceita:
            return True
        from . import memoria
        memoria.registrar(frase, f"(ignorado: voz não reconhecida, nota {nota:.2f})", tipo="voz_nao_reconhecida",
                          extra={"nota_voz": round(nota, 2), "exigencia_voz": round(self.verificador.exigencia, 2)})
        memoria.ouvido(frase, voz_nao_reconhecida=round(nota, 2), motivo="voz não reconhecida")
        return False

    def _calibrar(self, fila: queue.Queue) -> float:
        estado.definir("iniciando", "medindo o ruído do ambiente...")
        niveis, fim = [], time.time() + 1.5
        while time.time() < fim:
            try:
                niveis.append(nivel(aplicar_ganho(fila.get(timeout=0.5)[0], self.ganho)))
            except queue.Empty:
                pass
        limiar = sugerir_limiar(niveis)
        log.info("Limiar de volume calibrado automaticamente: %.0f", limiar)
        return limiar

    def escutar_para_sempre(self, ao_ouvir_comando, deve_continuar) -> None:
        """Chama ao_ouvir_comando(comando, frase_completa, seguimento=...) quando falam com o Mestre.

        ao_ouvir_comando devolve por quantos segundos continuar ouvindo SEM "mestre".
        """
        import sounddevice as sd

        # Cada bloco vai com a marca "o Mestre estava falando quando isto foi gravado?".
        # Assim nada do que VOCE fala se perde enquanto ele transcreve ou trabalha (importante
        # no ditado longo), e a voz dele mesmo so vale se comecar com a palavra de ativacao.
        fila: queue.Queue[tuple[bytes, bool]] = queue.Queue()

        def recebe_audio(dados, frames, tempo, status):
            eco = self.voz.falando.is_set() or time.time() - self.voz.terminou_em < 0.3
            fila.put((bytes(dados), eco))

        self._preparar_laco()
        with sd.RawInputStream(samplerate=TAXA, blocksize=BLOCO, device=self.microfone,
                               dtype="int16", channels=1, callback=recebe_audio):
            limiar = self.limiar or self._calibrar(fila)
            seg = Segmentador(limiar, self.silencio_fim, max_fala=self.max_frase)
            estado.atualizar(limiar=limiar)
            estado.definir("ouvindo")
            log.info("Ouvindo (modo %s, limiar %.0f)... diga '%s'.", self.modo, limiar, self.variacoes[0])
            self._laco(fila, seg, ao_ouvir_comando, deve_continuar)

    # --- O laco (separado do microfone: o teste automatico alimenta blocos sinteticos) -------------
    def _preparar_laco(self) -> None:
        self._conversa_ate = 0.0
        self._pendente: dict | None = None   # esperando o resto: "Assessor" sozinho ou frase que terminou no meio
        self._blocos = 0                     # relogio do audio (1 bloco = 0,1 s)
        self._seg_eco: Segmentador | None = None   # frases gravadas enquanto ELE fala
        self._resto_conversa: float | None = None  # janela de conversa congelada enquanto ele fala
        self._notas: deque = deque(maxlen=1200)   # nota do detector da palavra por bloco (ultimos 120 s)
        self._inicio_frase = 0                     # bloco em que a frase atual comecou

    def _laco(self, fila: queue.Queue, seg: Segmentador, ao_ouvir_comando, deve_continuar) -> None:
        while deve_continuar():
            try:
                bruto, eco = fila.get(timeout=0.5)
            except queue.Empty:
                self._vencer_espera(seg, ao_ouvir_comando, sem_audio=True)
                continue
            self._bloco(bruto, eco, seg, ao_ouvir_comando)

    def _descartar(self, motivo: str, texto: str = "", **dados) -> None:
        """Nenhuma frase some sem registro: vai para memoria/ouvido.jsonl com o motivo."""
        from . import memoria
        log.info("Descartado (%s): %r", motivo, texto)
        memoria.ouvido(texto, descartado=True, motivo=motivo, **dados)

    def _falando(self) -> bool:
        return bool(self.voz is not None and self.voz.falando.is_set())

    def _voltar(self, nome: str, detalhe: str = "") -> None:
        """Volta o indicador para ouvindo/conversa, sem apagar o "falando" enquanto a fala toca."""
        if self._falando() and estado.ler()["nome"] == "falando":
            return
        estado.definir(nome, detalhe)

    def _bloco(self, bruto: bytes, eco: bool, seg: Segmentador, ao_ouvir_comando) -> None:
        self._blocos += 1
        bloco = aplicar_ganho(bruto, self.ganho)
        estado.atualizar(nivel=nivel(bloco))
        # O executor pode abrir a janela de conversa (ex.: "terminei de pensar, quer ouvir?")
        self._conversa_ate = max(self._conversa_ate, estado.ler()["conversa_ate"])
        # Em pausa: ignora o microfone.
        if estado.pausado():
            seg.reiniciar()
            self._seg_eco = None
            if estado.ler()["nome"] != "pausado":
                estado.definir("pausado")
            return
        self._escutar_palavra(bloco)
        if eco:   # ele esta falando (ou acabou de falar)
            if seg.falando and seg.duracao_atual >= 0.8:   # voce falava e ele comecou a falar por cima
                self._descartar("cortada: o assistente começou a falar", audio_seg=round(seg.duracao_atual, 1))
            seg.reiniciar()
            self._segurar_conversa()
            if self.interromper:
                self._bloco_eco(bloco, seg, ao_ouvir_comando)
            return
        self._resto_conversa = None
        if self._seg_eco is not None and self._seg_eco.falando:   # a fala dele acabou no meio de uma frase sua
            audio = self._seg_eco.fechar(minimo=0.5)
            if audio:
                self._frase_eco(audio, seg, ao_ouvir_comando)
        if estado.ler()["nome"] == "pausado":
            estado.definir("ouvindo")

        em_conversa = time.time() < self._conversa_ate or self._pendente is not None
        estava_falando = seg.falando
        audio = seg.processar(bloco)
        if seg.descartada:
            self._descartar("curta demais", audio_seg=round(seg.descartada, 1))
            seg.descartada = 0.0
        if seg.falando and not estava_falando:
            self._inicio_frase = self._blocos
            estado.definir("gravando")
        if audio is None:
            if not seg.falando and estado.ler()["nome"] == "gravando":
                estado.definir("conversa" if em_conversa else "ouvindo")
            self._vencer_espera(seg, ao_ouvir_comando)
            return
        self._frase(audio, seg, ao_ouvir_comando)

    # --- Detector local da palavra (opcional) ------------------------------------------------------
    def _escutar_palavra(self, bloco: bytes) -> None:
        """Passa o bloco ao detector (se houver) e guarda a nota. Erro no detector = desliga e segue sem ele."""
        if self.detector is None:
            return
        try:
            nota = float(self.detector.ouvir(bloco))
        except Exception as erro:
            log.warning("Detector da palavra falhou (%s): desligado até reiniciar, o Whisper ouve tudo", erro)
            self.detector = None
            return
        self._notas.append((self._blocos, nota))

    def _nota_da_frase(self, audio: bytes) -> float:
        """Maior nota do detector desde um pouco antes do comeco da frase (a fala pre-gravada) ate agora."""
        inicio = min(self._inicio_frase, self._blocos - len(audio) // (BLOCO * 2)) - MARGEM_DETECTOR
        return max((n for b, n in self._notas if b >= inicio), default=0.0)

    def _filtrar_pelo_detector(self, audio: bytes, em_conversa: bool, pendente: bool, e: dict) -> dict | None:
        """None = pode seguir para o Whisper; dict = descartar (com os dados do registro).
        So filtra fora da conversa, sem espera pendente, fora do ditado e do descanso ("bora voltar" acorda)."""
        if self.detector is None or em_conversa or pendente or e.get("ditado_desde") or e.get("descanso"):
            return None
        nota = self._nota_da_frase(audio)
        if nota >= self.detector.limiar:
            self._nota_detector = nota
            return None
        return {"nota_detector": round(nota, 2)}

    def _segurar_conversa(self) -> None:
        """Enquanto ele fala, a janela de conversa nao corre: ela conta a partir do fim da fala."""
        agora = time.time()
        resto = max(0.0, self._conversa_ate - agora)
        if self._resto_conversa is not None and self._resto_conversa > resto:
            self._conversa_ate = agora + self._resto_conversa
            estado.atualizar(conversa_ate=self._conversa_ate)
        else:
            self._resto_conversa = resto

    # --- Enquanto ele fala: so frase que comeca com a palavra de ativacao (e ela corta a fala) -----
    def _bloco_eco(self, bloco: bytes, seg: Segmentador, ao_ouvir_comando) -> None:
        if self._seg_eco is None or self._seg_eco.limiar != seg.limiar:
            self._seg_eco = Segmentador(seg.limiar, SILENCIO_ECO, max_fala=MAX_FRASE_ECO)
        audio = self._seg_eco.processar(bloco)
        self._seg_eco.descartada = 0.0
        if audio:
            self._frase_eco(audio, seg, ao_ouvir_comando)

    def _chamou_no_inicio(self, frase: str) -> bool:
        """A palavra de ativacao esta no comeco da frase? ("Assessor, para", "ô Assessor, abre...")"""
        alvos = [normalizar(v) for v in self.variacoes]
        return any(parecida(p, alvos) for p in normalizar(frase).split()[:3])

    def _e_eco(self, comando: str) -> bool:
        """O que veio depois da palavra e o que ELE esta falando (o nome dele na propria fala)?"""
        falando = normalizar(self.voz.texto_falando()) if self.voz is not None and hasattr(self.voz, "texto_falando") else ""
        palavras = normalizar(comando).split()[:3]
        return bool(falando) and len(palavras) >= 2 and " ".join(palavras) in falando

    def _frase_eco(self, audio: bytes, seg: Segmentador, ao_ouvir_comando) -> None:
        from . import memoria

        duracao = round(len(audio) / (TAXA * 2), 1)
        if self._vigia and not self._chamou_mestre_vosk(audio):   # (modo leve: nem transcreve)
            self._descartar("falando", audio_seg=duracao)
            return
        inicio = time.time()
        frase = self.transcritor.transcrever(audio)
        gasto = round(time.time() - inicio, 1)
        log.info("Ouvi enquanto falava (%.1fs de áudio, %.1fs para transcrever): %r", duracao, gasto, frase)
        if not frase or not self._chamou_no_inicio(frase):
            self._descartar("falando", frase or "", audio_seg=duracao, transcricao_seg=gasto)
            return
        _, comando = extrair_comando(frase, self.variacoes)
        so_parar = bool(re.fullmatch(PARAR, normalizar(comando)))
        if not so_parar and not so_a_palavra(comando) and self._e_eco(comando):
            self._descartar("falando: eco da própria voz", frase, audio_seg=duracao, transcricao_seg=gasto)
            return
        if not self._voz_do_dono(audio, frase, em_conversa=False):
            return
        parou = self.voz.parar() if self.voz is not None and hasattr(self.voz, "parar") else False
        log.info("Interrompeu a fala (%s): %r", "parou" if parou else "já tinha terminado", frase)
        if so_parar:   # "Assessor, para": so para
            memoria.ouvido(frase, chamou=True, interrompeu=True, motivo="interrompeu a fala",
                           audio_seg=duracao, transcricao_seg=gasto)
            memoria.registrar(frase, "(parei de falar)", "comando", {"entendi": normalizar(comando),
                                                                       "rota": "ignorado (só parou de falar)"})
            estado.definir("conversa" if time.time() < self._conversa_ate else "ouvindo")
            return
        e = estado.ler()
        self._tratar(frase, audio, gasto, False, bool(e.get("ditado_desde")), e, seg, ao_ouvir_comando,
                     extra={"interrompeu": True}, verificada=True)

    # --- Esperas: "Assessor" sozinho e frase que terminou no meio ----------------------------------
    def _vencer_espera(self, seg: Segmentador, ao_ouvir_comando, sem_audio: bool = False) -> None:
        """Nada mais veio na espera: "Assessor" sozinho responde curto (abre a conversa); a frase que
        terminou no meio vai como esta."""
        p = self._pendente
        if not p or seg.falando:
            return
        espera = p.get("espera", self.espera_palavra)
        if sem_audio:   # (microfone parado: vale o relogio de verdade)
            venceu = time.time() - p["quando"] >= espera + 1
        else:
            venceu = (self._blocos - p["bloco"]) * BLOCO / TAXA >= espera
        if not venceu:
            return
        self._pendente = None
        if p.get("tipo") == "continuacao":
            log.info("A continuação não veio (esperei %.1fs): %r", espera, p["frase"])
            self._entregar(p["comando"], p["frase"], p["audio"], p["achou"], p["em_conversa"], seg, ao_ouvir_comando)
            return
        log.info("Só chamou (esperei %.1fs e não veio o resto): %r", espera, p["frase"])
        self._entregar("", p["frase"], p["audio"], True, p["em_conversa"], seg, ao_ouvir_comando)

    def _frase(self, audio: bytes, seg: Segmentador, ao_ouvir_comando) -> None:
        """Uma frase completa saiu do Segmentador: transcreve, decide e entrega (ou registra o descarte)."""
        duracao = len(audio) / (TAXA * 2)
        p = self._pendente
        # comecou dentro da janela de conversa (ou logo depois de "Assessor" sozinho)?
        em_conversa = p["em_conversa"] if p else time.time() - duracao < self._conversa_ate
        e = estado.ler()
        self._nota_detector = None
        barrado = self._filtrar_pelo_detector(audio, em_conversa, bool(p), e)
        if barrado is not None:   # (nem chega ao Whisper: e o que economiza processador/placa)
            self._descartar("sem a palavra (detector local)", audio_seg=round(duracao, 1), **barrado)
            estado.definir("ouvindo")
            return
        if self._vigia and not em_conversa and not p and not self._chamou_mestre_vosk(audio):
            self._descartar("sem a palavra de ativação (Vosk)", audio_seg=round(duracao, 1))
            estado.definir("ouvindo")
            return

        estado.definir("transcrevendo")
        inicio = time.time()
        ditado = bool(e.get("ditado_desde"))
        if ditado:   # ditado: modo caprichado (mais preciso, com o texto anterior de contexto)
            log.info("Transcrevendo no modo caprichado (ditado)")
            try:
                frase = self.transcritor.transcrever(audio, caprichado=True, contexto=e.get("ditado_contexto", ""))
            except TypeError:   # transcritor antigo/simulado
                frase = self.transcritor.transcrever(audio)
        else:
            frase = self.transcritor.transcrever(audio)
        gasto = round(time.time() - inicio, 1)
        log.info("Ouvi (%.1fs de áudio, %.1fs para transcrever): %r", duracao, gasto, frase)
        if self.diagnostico:
            guardar_diagnostico(audio, frase)
        if not frase:
            self._descartar("transcrição vazia (barulho?)", audio_seg=round(duracao, 1))
            if p:   # depois de "Assessor" (ou de uma frase pela metade): continua esperando o resto
                p["bloco"], p["quando"] = self._blocos, time.time()
            estado.definir("conversa" if em_conversa else "ouvindo")
            return
        extra = {"nota_detector": round(self._nota_detector, 2)} if self._nota_detector is not None else None
        self._tratar(frase, audio, gasto, em_conversa, ditado, e, seg, ao_ouvir_comando, extra=extra)

    def _tratar(self, frase: str, audio: bytes, gasto: float, em_conversa: bool, ditado: bool, e: dict,
                seg: Segmentador, ao_ouvir_comando, extra: dict | None = None, verificada: bool = False) -> None:
        """Frase ja transcrita: junta com a espera, decide se espera mais, registra e entrega."""
        from . import memoria, validacao

        p = self._pendente
        if p:
            em_conversa = p["em_conversa"]
        volta = "conversa" if em_conversa else "ouvindo"
        achou, comando = extrair_comando(frase, self.variacoes)
        if not achou and not em_conversa and e.get("descanso") and frase_de_volta(frase):
            achou, comando = True, normalizar(frase)   # descansando: "bora voltar a trabalhar" acorda
        extra = dict(extra or {})
        so_chamou = achou and not p and not ditado and self.espera_palavra > 0 and so_a_palavra(comando)
        partes = 1
        if p:   # "Assessor… abre o YouTube" / "eu queria… que abrisse o YouTube": as partes viram uma frase so
            self._pendente = None
            verificada = False   # (a voz e conferida de novo com o audio todo)
            if p.get("tipo") == "continuacao":
                resto = comando if achou else normalizar(frase)
                comando, achou = f"{p['comando']} {resto}".strip(), p["achou"]
                extra["junto_da_anterior"] = True
            else:
                if not achou:
                    comando = normalizar(frase)
                achou = True
                extra["junto_da_palavra"] = True
            frase, audio, partes = f"{p['frase']} {frase}", p["audio"] + audio, p.get("partes", 1) + 1
        elif not achou:
            comando = normalizar(frase)
        continua = (not so_chamou and not ditado and self.espera_cont > 0 and (achou or em_conversa)
                    and partes < MAX_PARTES and termina_no_meio(frase) and not so_a_palavra(comando))
        if so_chamou:
            extra["motivo"] = f"só a palavra: esperando o resto ({self.espera_palavra:.1f}s)"
        elif continua:
            extra["motivo"] = f"terminou no meio: esperando a continuação ({self.espera_cont:.1f}s)"
        elif not achou and not em_conversa:
            extra["motivo"] = "sem a palavra de ativação"
        arquivo_audio = validacao.guardar_audio(audio)   # so com a validacao aberta no painel
        if arquivo_audio:
            extra["audio"] = arquivo_audio
        memoria.ouvido(frase, chamou=achou, conversa=em_conversa, ditado=ditado,
                       audio_seg=round(len(audio) / (TAXA * 2), 1), transcricao_seg=gasto, **extra)

        if so_chamou or continua:
            self._pendente = {"tipo": "palavra" if so_chamou else "continuacao", "frase": frase, "audio": audio,
                              "em_conversa": em_conversa, "bloco": self._blocos, "quando": time.time(),
                              "comando": comando, "achou": achou, "partes": partes,
                              "espera": self.espera_palavra if so_chamou else self.espera_cont}
            if so_chamou:
                log.info("Só a palavra (%r): esperando o resto da frase por até %.1fs", frase, self.espera_palavra)
                estado.definir("conversa", "pode falar...")
            else:
                log.info("Frase terminou no meio (%r): esperando a continuação por até %.1fs", frase, self.espera_cont)
                estado.definir("conversa", "continua...")
            return
        if not achou and not em_conversa:
            estado.definir(volta)
            return
        self._entregar(comando, frase, audio, achou, em_conversa, seg, ao_ouvir_comando, verificada=verificada)

    def _entregar(self, comando: str, frase: str, audio: bytes, achou: bool, em_conversa: bool,
                  seg: Segmentador, ao_ouvir_comando, verificada: bool = False) -> None:
        if not verificada and not self._voz_do_dono(audio, frase, em_conversa):
            estado.definir("conversa" if em_conversa else "ouvindo")
            return
        if achou and self.acordar_tela:
            from . import sistema
            sistema.acordar_tela()

        estado.atualizar(ultima_frase=frase, audio_anterior=estado.ler()["ultimo_audio"], ultimo_audio=audio)
        estado.definir("trabalhando", frase)
        segundos = ao_ouvir_comando(comando, frase, seguimento=not achou) or 0
        self._conversa_ate = time.time() + segundos
        # a resposta dele ainda esta tocando: a janela so comeca a correr quando ele terminar de falar
        self._resto_conversa = float(segundos) if self._falando() else None
        estado.atualizar(conversa_ate=self._conversa_ate)
        self._voltar("conversa" if segundos else "ouvindo")
        seg.reiniciar()
        # (o que voce falou enquanto ele trabalhava continua na fila e e ouvido agora)


# "Assessor, é..." / "E aí, Assessor, hum": so enchimento depois da palavra = so chamou
ENCHIMENTO = {"e", "eh", "ah", "ahn", "an", "hum", "hm", "humm", "uhm", "entao", "tipo", "ai", "oi", "ei", "ne",
              "pois", "assim", "o", "a", "ta", "bom", "olha"}
ESPERA_APOS_PALAVRA = 2.5   # s: depois de "Assessor" sozinho, espera o resto da frase antes de responder
ESPERA_CONTINUACAO = 1.5    # s: frase que terminou no meio espera a continuacao mais este tanto
MAX_PARTES = 6              # (no maximo tantas partes juntadas numa frase so)
SILENCIO_ECO = 0.6          # s: pausa que fecha uma frase gravada enquanto ele fala
MARGEM_DETECTOR = 6         # blocos (0,6 s) antes do comeco da frase que ainda contam para o detector
MAX_FRASE_ECO = 6.0         # s: enquanto ele fala, confere a cada 6 s no maximo (o eco da voz nao tem pausa)
# Palavras que deixam a frase "pela metade": "abre o site do...", "eu queria que", "pesquisa sobre o, "
CONECTIVOS = {"do", "da", "dos", "das", "de", "que", "e", "pra", "pro", "pras", "pros", "para", "com", "mas",
              "porem", "tipo", "ou", "porque", "no", "na", "nos", "nas", "em", "num", "numa", "um", "uma",
              "o", "a", "os", "as", "ao", "aos", "sobre"}
# "Assessor, para" (durante a fala): so para de falar, nao vira comando
PARAR = (r"(ei |ah |o )?(para|pare|parar|para de falar|pode parar|para ai|chega|silencio|cala (a )?boca|quieto|"
         r"fica quieto|psiu|shh+|stop|espera|ok|ta bom|ta|beleza|obrigado|valeu|entendi|ja entendi)"
         r"( ai| por favor| agora)?")


def so_a_palavra(comando: str) -> bool:
    """O que sobrou depois da palavra de ativação é vazio ou só enchimento?"""
    return all(p in ENCHIMENTO for p in normalizar(comando).split())


def termina_no_meio(frase: str) -> bool:
    """A frase acabou "pela metade"? (vírgula, reticências ou palavra de ligação no fim: do, que, e, pra...)"""
    t = (frase or "").strip()
    if not t or t.endswith(("?", "!")):
        return False
    if t.endswith(("...", "…", ",", ";", ":")):
        return True
    palavras = normalizar(t).split()
    return bool(palavras) and palavras[-1] in CONECTIVOS


def _segundos(cfg: dict, chave: str, padrao: float, maximo: float) -> float:
    o = (cfg or {}).get("ouvido") or {}
    try:
        v = float(o.get(chave, padrao))
    except (TypeError, ValueError):
        v = padrao
    return min(maximo, max(0.0, v))


def espera_apos_palavra(cfg: dict) -> float:
    """Segundos de espera depois de "Assessor" sozinho (0 = responde na hora). Config antigo: padrão."""
    return _segundos(cfg, "espera_apos_palavra", ESPERA_APOS_PALAVRA, 6.0)


def espera_continuacao(cfg: dict) -> float:
    """Segundos a mais que a frase "pela metade" espera a continuação (0 = desligado). Config antigo: padrão."""
    return _segundos(cfg, "espera_continuacao", ESPERA_CONTINUACAO, 4.0)


def listar_microfones() -> list[tuple[int, str]]:
    import sounddevice as sd

    return [(i, d["name"]) for i, d in enumerate(sd.query_devices()) if d["max_input_channels"] > 0]


def imprimir_microfones() -> None:
    import sounddevice as sd

    print("\nMICROFONES ENCONTRADOS (use o numero no painel ou no config.yaml):\n")
    for i, nome in listar_microfones():
        print(f"  {i:>3}  ->  {nome}")
    print(f"\nMicrofone padrao do Windows: {sd.default.device[0]}\n")


PALAVRAS_PADRAO = ["Ollama", "IPM", "Atende.Net", "Claude", "Claude Code", "skill", "prompt", "Spotify",
                   "YouTube", "playlist", "painel", "melhorias", "finalizei"]


def palavras_de_dica(cfg: dict) -> list[str]:
    """Nomes que o Whisper deve "esperar" ouvir: programas, sites e frases de rotina.

    Canais so entram se forem poucos (com 1.900 inscricoes, 40 nomes sorteados
    atrapalhariam mais do que ajudariam).
    """
    o = cfg.get("ouvido") or {}
    nomes = [str(x) for x in (o.get("palavras_conhecidas") or PALAVRAS_PADRAO)]   # primeiro: as do projeto
    nomes += list(((cfg.get("spotify") or {}).get("playlists") or {}))
    nomes += list(cfg.get("programas") or {}) + list(cfg.get("sites") or {})
    nomes += [f for r in (cfg.get("rotinas") or []) for f in (r.get("frases") or [])[:1]]
    canais = list(cfg.get("canais_youtube") or {})
    if len(canais) <= 30:
        nomes += canais
    return [str(n) for n in nomes]
