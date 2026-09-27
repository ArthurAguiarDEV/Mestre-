"""Ouvido do Mestre: fica escutando o microfone o tempo todo.

1. O Segmentador corta o som em frases, usando o limite de volume calibrado.
2. Cada frase e checada: chamaram "mestre"? (ou estamos no modo conversa?)
     modo_ativacao "whisper": o Whisper transcreve toda frase (mais preciso, usa mais CPU)
     modo_ativacao "vosk":    o Vosk procura so "mestre" antes (bem leve)
3. O Whisper transcreve e o comando vai para o Executor.
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
        memoria.ouvido(frase, voz_nao_reconhecida=round(nota, 2))
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

        conversa_ate = 0.0
        with sd.RawInputStream(samplerate=TAXA, blocksize=BLOCO, device=self.microfone,
                               dtype="int16", channels=1, callback=recebe_audio):
            limiar = self.limiar or self._calibrar(fila)
            seg = Segmentador(limiar, self.silencio_fim, max_fala=self.max_frase)
            estado.atualizar(limiar=limiar)
            estado.definir("ouvindo")
            log.info("Ouvindo (modo %s, limiar %.0f)... diga '%s'.", self.modo, limiar, self.variacoes[0])
            while deve_continuar():
                try:
                    bruto, eco = fila.get(timeout=0.5)
                except queue.Empty:
                    continue
                bloco = aplicar_ganho(bruto, self.ganho)
                estado.atualizar(nivel=nivel(bloco))
                # O executor pode abrir a janela de conversa (ex.: "terminei de pensar, quer ouvir?")
                conversa_ate = max(conversa_ate, estado.ler()["conversa_ate"])
                # Ignora o microfone enquanto o Mestre fala (e logo depois), ou em pausa.
                if eco or estado.pausado():
                    seg.reiniciar()
                    if estado.pausado() and estado.ler()["nome"] != "pausado":
                        estado.definir("pausado")
                    continue
                if estado.ler()["nome"] == "pausado":
                    estado.definir("ouvindo")

                em_conversa = time.time() < conversa_ate
                estava_falando = seg.falando
                audio = seg.processar(bloco)
                if seg.falando and not estava_falando:
                    estado.definir("gravando")
                if audio is None:
                    if not seg.falando and estado.ler()["nome"] == "gravando":
                        estado.definir("conversa" if em_conversa else "ouvindo")
                    continue

                duracao = len(audio) / (TAXA * 2)
                em_conversa = time.time() - duracao < conversa_ate  # comecou dentro da janela
                if self._vigia and not em_conversa and not self._chamou_mestre_vosk(audio):
                    estado.definir("ouvindo")
                    continue

                estado.definir("transcrevendo")
                inicio = time.time()
                e = estado.ler()
                if e.get("ditado_desde"):   # ditado: modo caprichado (mais preciso, com o texto anterior de contexto)
                    log.info("Transcrevendo no modo caprichado (ditado)")
                    try:
                        frase = self.transcritor.transcrever(audio, caprichado=True, contexto=e.get("ditado_contexto", ""))
                    except TypeError:   # transcritor antigo/simulado
                        frase = self.transcritor.transcrever(audio)
                else:
                    frase = self.transcritor.transcrever(audio)
                log.info("Ouvi (%.1fs de áudio, %.1fs para transcrever): %r",
                         duracao, time.time() - inicio, frase)
                if self.diagnostico:
                    guardar_diagnostico(audio, frase)
                achou, comando = extrair_comando(frase, self.variacoes) if frase else (False, "")
                if frase:   # (exportacao do historico: inclusive o que foi ignorado)
                    from . import memoria
                    memoria.ouvido(frase, chamou=achou, conversa=em_conversa, ditado=bool(e.get("ditado_desde")),
                                   audio_seg=round(duracao, 1), transcricao_seg=round(time.time() - inicio, 1))
                if frase and not achou and not em_conversa and e.get("descanso") and frase_de_volta(frase):
                    achou, comando = True, normalizar(frase)   # descansando: "bora voltar a trabalhar" acorda
                if not frase or (not achou and not em_conversa):
                    estado.definir("conversa" if em_conversa else "ouvindo")
                    continue
                if not self._voz_do_dono(audio, frase, em_conversa):
                    estado.definir("conversa" if em_conversa else "ouvindo")
                    continue
                if achou and self.acordar_tela:
                    from . import sistema
                    sistema.acordar_tela()

                estado.atualizar(ultima_frase=frase, audio_anterior=estado.ler()["ultimo_audio"], ultimo_audio=audio)
                estado.definir("trabalhando", frase)
                segundos = ao_ouvir_comando(comando if achou else normalizar(frase), frase,
                                            seguimento=not achou) or 0
                conversa_ate = time.time() + segundos
                estado.atualizar(conversa_ate=conversa_ate)
                estado.definir("conversa" if segundos else "ouvindo")
                seg.reiniciar()
                # (o que voce falou enquanto ele trabalhava continua na fila e e ouvido agora)


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
