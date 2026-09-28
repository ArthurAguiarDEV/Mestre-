"""Ouvido do Mestre: fica escutando o microfone o tempo todo.

1. O Segmentador corta o som em frases, usando o limite de volume calibrado.
2. Cada frase e checada: chamaram "mestre"? (ou estamos no modo conversa?)
     modo_ativacao "whisper": o Whisper transcreve toda frase (mais preciso, usa mais CPU)
     modo_ativacao "vosk":    o Vosk procura so "mestre" antes (bem leve)
3. O Whisper transcreve e o comando vai para o Executor.
4. "Assessor" sozinho (ou so enchimento) NAO responde na hora: espera `espera_apos_palavra` s pelo resto
   ("Assessor... abre o YouTube" vira uma frase so). Nada vindo, responde curto e abre a conversa.
5. Toda frase descartada vai para memoria/ouvido.jsonl com o `motivo` (curta demais, transcricao vazia,
   sem a palavra, voz nao reconhecida, cortada pela voz do assistente...).
"""
import json
import logging
import queue
import time

from . import estado, locutor
from .audio import BLOCO, TAXA, Segmentador, Transcritor, aplicar_ganho, guardar_diagnostico, nivel, sugerir_limiar
from .config import caminho_do_projeto, palavras_ativacao
from .texto import extrair_comando, frase_de_volta, normalizar
from .voz import Voz

log = logging.getLogger(__name__)


class Ouvido:
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

        self.transcritor = Transcritor(o.get("modelo_whisper", "small"), o.get("precisao", "equilibrado"),
                                       o.get("dispositivo", "auto"), palavras_de_dica(cfg), palavra=self.variacoes[0])

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
        # no ditado longo), e a voz dele mesmo continua ignorada.
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
        self._pendente: dict | None = None   # "Assessor" sozinho: esperando o resto da frase
        self._blocos = 0                     # relogio do audio (1 bloco = 0,1 s)

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

    def _bloco(self, bruto: bytes, eco: bool, seg: Segmentador, ao_ouvir_comando) -> None:
        self._blocos += 1
        bloco = aplicar_ganho(bruto, self.ganho)
        estado.atualizar(nivel=nivel(bloco))
        # O executor pode abrir a janela de conversa (ex.: "terminei de pensar, quer ouvir?")
        self._conversa_ate = max(self._conversa_ate, estado.ler()["conversa_ate"])
        # Ignora o microfone enquanto o Mestre fala (e logo depois), ou em pausa.
        if eco or estado.pausado():
            if eco and seg.falando and seg.duracao_atual >= 0.8:   # voce falava e ele comecou a falar por cima
                self._descartar("cortada: o assistente começou a falar", audio_seg=round(seg.duracao_atual, 1))
            seg.reiniciar()
            if estado.pausado() and estado.ler()["nome"] != "pausado":
                estado.definir("pausado")
            return
        if estado.ler()["nome"] == "pausado":
            estado.definir("ouvindo")

        em_conversa = time.time() < self._conversa_ate or self._pendente is not None
        estava_falando = seg.falando
        audio = seg.processar(bloco)
        if seg.descartada:
            self._descartar("curta demais", audio_seg=round(seg.descartada, 1))
            seg.descartada = 0.0
        if seg.falando and not estava_falando:
            estado.definir("gravando")
        if audio is None:
            if not seg.falando and estado.ler()["nome"] == "gravando":
                estado.definir("conversa" if em_conversa else "ouvindo")
            self._vencer_espera(seg, ao_ouvir_comando)
            return
        self._frase(audio, seg, ao_ouvir_comando)

    def _vencer_espera(self, seg: Segmentador, ao_ouvir_comando, sem_audio: bool = False) -> None:
        """"Assessor" sozinho e nada mais veio na espera: responde curto e abre a janela de conversa."""
        p = self._pendente
        if not p or seg.falando:
            return
        if sem_audio:   # (microfone parado: vale o relogio de verdade)
            venceu = time.time() - p["quando"] >= self.espera_palavra + 1
        else:
            venceu = (self._blocos - p["bloco"]) * BLOCO / TAXA >= self.espera_palavra
        if not venceu:
            return
        self._pendente = None
        log.info("Só chamou (esperei %.1fs e não veio o resto): %r", self.espera_palavra, p["frase"])
        self._entregar("", p["frase"], p["audio"], True, p["em_conversa"], seg, ao_ouvir_comando)

    def _frase(self, audio: bytes, seg: Segmentador, ao_ouvir_comando) -> None:
        """Uma frase completa saiu do Segmentador: transcreve, decide e entrega (ou registra o descarte)."""
        from . import memoria, validacao

        duracao = len(audio) / (TAXA * 2)
        p = self._pendente
        # comecou dentro da janela de conversa (ou logo depois de "Assessor" sozinho)?
        em_conversa = p["em_conversa"] if p else time.time() - duracao < self._conversa_ate
        if self._vigia and not em_conversa and not p and not self._chamou_mestre_vosk(audio):
            self._descartar("sem a palavra de ativação (Vosk)", audio_seg=round(duracao, 1))
            estado.definir("ouvindo")
            return

        estado.definir("transcrevendo")
        inicio = time.time()
        e = estado.ler()
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
        volta = "conversa" if em_conversa else "ouvindo"
        if not frase:
            self._descartar("transcrição vazia (barulho?)", audio_seg=round(duracao, 1))
            if p:   # depois de "Assessor": continua esperando o resto
                p["bloco"], p["quando"] = self._blocos, time.time()
            estado.definir(volta)
            return

        achou, comando = extrair_comando(frase, self.variacoes)
        if not achou and not em_conversa and e.get("descanso") and frase_de_volta(frase):
            achou, comando = True, normalizar(frase)   # descansando: "bora voltar a trabalhar" acorda
        extra = {}
        so_chamou = achou and not p and not ditado and self.espera_palavra > 0 and so_a_palavra(comando)
        if p:   # "Assessor… abre o YouTube": as duas partes viram uma frase so
            self._pendente = None
            if not achou:
                comando = normalizar(frase)
            achou, frase, audio = True, f"{p['frase']} {frase}", p["audio"] + audio
            extra["junto_da_palavra"] = True
        elif so_chamou:
            extra["motivo"] = f"só a palavra: esperando o resto ({self.espera_palavra:.1f}s)"
        elif not achou and not em_conversa:
            extra["motivo"] = "sem a palavra de ativação"
        arquivo_audio = validacao.guardar_audio(audio)   # so com a validacao aberta no painel
        if arquivo_audio:
            extra["audio"] = arquivo_audio
        memoria.ouvido(frase, chamou=achou, conversa=em_conversa, ditado=ditado,
                       audio_seg=round(len(audio) / (TAXA * 2), 1), transcricao_seg=gasto, **extra)

        if so_chamou:
            self._pendente = {"frase": frase, "audio": audio, "em_conversa": em_conversa,
                              "bloco": self._blocos, "quando": time.time()}
            log.info("Só a palavra (%r): esperando o resto da frase por até %.1fs", frase, self.espera_palavra)
            estado.definir("conversa", "pode falar...")
            return
        if not achou and not em_conversa:
            estado.definir(volta)
            return
        self._entregar(comando if achou else normalizar(frase), frase, audio, achou, em_conversa, seg,
                       ao_ouvir_comando)

    def _entregar(self, comando: str, frase: str, audio: bytes, achou: bool, em_conversa: bool,
                  seg: Segmentador, ao_ouvir_comando) -> None:
        if not self._voz_do_dono(audio, frase, em_conversa):
            estado.definir("conversa" if em_conversa else "ouvindo")
            return
        if achou and self.acordar_tela:
            from . import sistema
            sistema.acordar_tela()

        estado.atualizar(ultima_frase=frase, audio_anterior=estado.ler()["ultimo_audio"], ultimo_audio=audio)
        estado.definir("trabalhando", frase)
        segundos = ao_ouvir_comando(comando, frase, seguimento=not achou) or 0
        self._conversa_ate = time.time() + segundos
        estado.atualizar(conversa_ate=self._conversa_ate)
        estado.definir("conversa" if segundos else "ouvindo")
        seg.reiniciar()
        # (o que voce falou enquanto ele trabalhava continua na fila e e ouvido agora)


# "Assessor, é..." / "E aí, Assessor, hum": so enchimento depois da palavra = so chamou
ENCHIMENTO = {"e", "eh", "ah", "ahn", "an", "hum", "hm", "humm", "uhm", "entao", "tipo", "ai", "oi", "ei", "ne",
              "pois", "assim", "o", "a", "ta", "bom", "olha"}
ESPERA_APOS_PALAVRA = 2.5   # s: depois de "Assessor" sozinho, espera o resto da frase antes de responder


def so_a_palavra(comando: str) -> bool:
    """O que sobrou depois da palavra de ativação é vazio ou só enchimento?"""
    return all(p in ENCHIMENTO for p in normalizar(comando).split())


def espera_apos_palavra(cfg: dict) -> float:
    """Segundos de espera depois de "Assessor" sozinho (0 = responde na hora). Config antigo: padrão."""
    o = (cfg or {}).get("ouvido") or {}
    try:
        v = float(o.get("espera_apos_palavra", ESPERA_APOS_PALAVRA))
    except (TypeError, ValueError):
        v = ESPERA_APOS_PALAVRA
    return min(6.0, max(0.0, v))


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
