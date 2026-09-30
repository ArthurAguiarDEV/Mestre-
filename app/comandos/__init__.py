"""Entende o que foi dito e executa o comando certo.

Caminho de uma frase:
  1. o Vocabulario "traduz" o jeito solto de falar  (vocabulario.yaml)
  2. cada metodo _cmd_... da lista ORDEM tenta reconhecer a frase
  3. se nenhum reconhecer e o cerebro estiver ligado, a IA interpreta

Para criar um comando novo:
  1. escreva um metodo  def _cmd_meu_comando(self, t): ...  no mixin do assunto (lista abaixo)
     (t = frase ja traduzida: sem acentos, minuscula e sem a palavra "mestre")
  2. o metodo devolve True se reconheceu a frase, ou False para passar adiante
  3. coloque o nome dele na lista ORDEM, logo abaixo

Organizacao: este arquivo e o NUCLEO (Executor.__init__, ORDEM, _executar, perguntar, falar, preencher,
_pedido_puro, _separar_monitor...). Cada assunto mora num mixin deste pacote:
  ia.py: IA: conversa livre, interpretacao de frases soltas, pensamento em segundo plano e fila
  rotinas.py: Rotinas do config.yaml e rotina ensinada falando (gravar passos, frase de chamar)
  assistente.py: Controle do proprio assistente: versao, encerrar, reiniciar, painel, ajuda, descanso,
    conversinha, atalhos ensinados e troca de voz
  feedback.py: Feedback ("isso ta errado"), agradecimento, melhorias para o Claude Code e exportar
  ditado.py: Ditado longo, revisão, destinos do projeto e área de transferência
  anotacoes.py: Historico de respostas, memoria ("lembra que..."), projetos guiados, lembretes e notas
  video.py: YouTube (pagina, canais, controle do que toca), streamings, clicar pelo texto e tocar
  midia.py: Volume (geral e por programa), teclas de midia e Spotify
  info.py: Informacoes: clima, noticias, hora e data
  janelas.py: Janelas, abas e monitores (mover, juntar, separar), tela, desligar o PC, pesquisa na
    internet e abrir programas/sites
  perfis.py: Perfis dos streamings (Arthur, Mestre...): qual perfil usar antes de buscar/tocar/continuar
  base.py: constantes e funcoes pequenas (reexportadas aqui)
"""
import logging
import queue
import random
import re
import threading
import time
from datetime import datetime
from .. import estado, memoria, personalidades, sistema
from ..config import palavras_ativacao
from ..cerebro import Cerebro
from ..config import PASTA_RESPOSTAS
from ..texto import extrair_comando, frase_de_volta, limpar_para_falar, normalizar, recuperar_original
from ..vocabulario import Vocabulario
from ..voz import Voz

# tudo da base (quem importa de app.comandos continua achando: painel, testes...)
from .base import (
    ARQUIVO_MELHORIAS, FALAS_CURTAS, ARQUIVO_REVISAO, PROMPT_MELHORIAS, DIAS, MESES, ENFEITES, CANCELAR,
    TERMINAR_DITADO, PRONTO_SOZINHO, ROTINA_VERBOS, FIM_ROTINA, CANCELA_ROTINA, NAO_GRAVA_NA_ROTINA,
    COMECO_DE_COMANDO, COMANDOS_COMUNS, LINK_PROJETO_PADRAO, CABECALHO_PROJETO, VOZES_PADRAO, FALAS_PADRAO,
    _quantos, _resumir, link_spotify, ORDINAIS, _ordinal, _host, _mesmo_site, _nome_do_canal,
    _tirar_enfeites,
)
from .ia import IAMixin
from .rotinas import RotinasMixin
from .assistente import AssistenteMixin
from .feedback import FeedbackMixin
from .ditado import DitadoMixin
from .anotacoes import AnotacoesMixin
from .video import VideoMixin
from .midia import MidiaMixin
from .info import InfoMixin
from .janelas import JanelasMixin
from .celular import CelularMixin
from .perfis import PerfisMixin

log = logging.getLogger(__name__)


def saudacao_do_horario() -> str:
    hora = datetime.now().hour
    # de madrugada (0h as 4h59) ainda e "boa noite"
    return "Boa noite" if hora < 5 else "Bom dia" if hora < 12 else "Boa tarde" if hora < 18 else "Boa noite"


# Os comandos de cada assunto estao nos mixins (veja a lista no topo); aqui fica o nucleo.
class Executor(IAMixin, RotinasMixin, AssistenteMixin, FeedbackMixin, DitadoMixin, AnotacoesMixin,
               VideoMixin, MidiaMixin, InfoMixin, JanelasMixin, CelularMixin, PerfisMixin):
    ORDEM = [
        "_cmd_pensamento", "_cmd_parar", "_cmd_descanso", "_cmd_versao", "_cmd_conversinha", "_cmd_exportar", "_cmd_historico", "_cmd_memoria", "_cmd_ensinar_rotina", "_cmd_rotinas", "_cmd_encerrar", "_cmd_reiniciar",
        "_cmd_painel", "_cmd_ajuda", "_cmd_ditado", "_cmd_projeto", "_cmd_feedback", "_cmd_obrigado",
        "_cmd_aprender", "_cmd_atalhos", "_cmd_melhorias", "_cmd_voz",
        "_cmd_area_transferencia", "_cmd_juntar", "_cmd_mover", "_cmd_saida_som", "_cmd_volume", "_cmd_midia", "_cmd_janela",
        "_cmd_controle_video", "_cmd_youtube_controle", "_cmd_spotify", "_cmd_youtube", "_cmd_streaming", "_cmd_clicar",
        "_cmd_clima", "_cmd_noticias", "_cmd_hora_data", "_cmd_tela", "_cmd_desligar_pc",
        "_cmd_lembrete", "_cmd_notas", "_cmd_tocar", "_cmd_pesquisa", "_cmd_print_telegram", "_cmd_tocando",
        "_cmd_abrir", "_cmd_esquecer",
    ]

    def __init__(self, cfg: dict, voz: Voz, cerebro: Cerebro, vocab: Vocabulario | None = None):
        self.cfg = cfg
        self.voz = voz
        self.cerebro = cerebro
        self.vocab = vocab or Vocabulario()
        self.rodando = True
        self._frase_original = ""
        self._pendente = None          # funcao que recebe a PROXIMA frase (dialogo)
        self._pendente_espera = 12.0
        self._acabou_de_chamar = False
        self._ultimo: dict = {}
        self._foi_feedback = False
        self._pendente_ia: dict | None = None   # frase->comando da IA esperando ~30s sem correcao p/ virar memoria
        # ditado longo
        self._ditado: list[str] = []
        self._destino_ditado: str | None = None
        self._espera_ditado = 180.0
        self._ditado_ativo = False
        self._ditado_sessao = 0
        self._ditado_ultimo = 0.0
        self._texto_ditado = ""
        self._revisao_ativa = False
        self._revisao_sessao = 0
        self._tipo_registro = "comando"
        self._proj: dict = {}
        self.ultimo_comando: str | None = None
        self._rota, self._entendi = "", ""
        # pensamento da IA em segundo plano
        self._pensamentos: list[dict] = []   # FILA: cada pedido termina na sua vez (nunca descarta)
        self._fila_ia: queue.Queue = queue.Queue()
        self._trabalhador_ia: threading.Thread | None = None
        self._pensamento_id = 0
        self._trava_pensamento = threading.Lock()
        self._trava_execucao = threading.RLock()   # um comando de cada vez (voz e IA em segundo plano)
        self._descansando = False
        # rotina ensinada falando: passos sendo gravados / rotina esperando a frase de chamar
        self._gravacao: dict | None = None
        self._rotina_nova: dict | None = None
        self._n_atendidos = 0   # quantos comandos ja rodaram (para saber se uma frase virou comando)
        self._seguimento = False       # a frase veio sem a palavra (conversa): "abre" sem alvo e ignorado
        self._ignorar_seguimento = False
        a = cfg.get("assistente") or {}
        p = cfg.get("personalidade") or {}
        self.nome = a.get("nome") or "Mestre"
        self.apelido = a.get("apelido_usuario") or "chefe"
        self.palavra = palavras_ativacao(cfg)[0]
        # Frases: as do estilo; se o painel ja salvou frases (tem "estilo" no config), valem EXATAMENTE
        # as da tela (assim frase apagada nao volta). Config antigo (sem estilo): soma as duas.
        falas = {k: list(v) for k, v in personalidades.estilo(p.get("estilo"))["falas"].items()}
        for tipo, lista in (p.get("falas") or {}).items():
            minhas = [str(x) for x in lista or [] if str(x).strip()]
            if minhas:
                falas[tipo] = minhas if p.get("estilo") else list(dict.fromkeys(falas.get(tipo, []) + minhas))
        self.falas = falas
        # Frases fixas do codigo: "chefe" vira o seu apelido e {palavra} a palavra de ativacao.
        # (numa passada so: com apelido "Mestre" e palavra "assessor", voce continua sendo o Mestre)
        self.voz.trocas = [(r"\bchefe\b", self.apelido), (r"\{palavra\}", self.palavra.capitalize()),
                           (r"\{apelido\}", self.apelido), (r"\{nome\}", self.nome)]
        self.janela_conversa = float((cfg.get("conversa") or {}).get("janela_segundos", 10))
        self._aplicar_preferencias_de_voz()

    # =================================================================
    #  Entrada principal
    # =================================================================
    def executar(self, frase: str, frase_completa: str = "", seguimento: bool = False) -> float:
        """Executa e guarda o que foi feito (para o feedback "isso ta errado" e o historico)."""
        with self._trava_execucao:
            return self._executar_e_registrar(frase, frase_completa, seguimento)

    def _executar_e_registrar(self, frase: str, frase_completa: str, seguimento: bool) -> float:
        self.voz.registro = []
        self._tipo_registro = "comando"
        self._rota, self._entendi = "", ""
        gravacao, atendidos = self._gravacao, self._n_atendidos
        inicio = time.time()
        try:
            segundos = self._executar(frase, frase_completa, seguimento)
            if gravacao is not None and gravacao is self._gravacao:   # gravando uma rotina: guarda o passo
                self._proteger(self._gravar_passo, atendidos)
        finally:
            falado, self.voz.registro = self.voz.registro or [], None
            memoria.registrar_tempo("frase_para_comando", time.time() - inicio)
        if self._tipo_registro != "historico" and (normalizar(frase) or falado):
            memoria.registrar(frase_completa or frase, " ".join(falado), self._tipo_registro,
                              {"entendi": self._entendi, "rota": self._rota, "seguimento": bool(seguimento)})
        if not self._foi_feedback:
            self._ultimo = {"ouvi": frase_completa or frase, "entendi": self.vocab.traduzir(frase),
                            "respondi": estado.ler().get("ultima_resposta", "")}
        self._foi_feedback = False
        return segundos

    def _executar(self, frase: str, frase_completa: str = "", seguimento: bool = False) -> float:
        """Executa o que foi dito. Devolve por quantos segundos o Mestre deve
        continuar ouvindo SEM precisar ouvir "mestre" de novo (0 = nao espera).

        frase           = comando ja sem a palavra "mestre"
        frase_completa  = tudo que foi ouvido, com acentos
        seguimento      = a frase veio sem "mestre", durante a conversa
        """
        self._frase_original = frase_completa or frase
        log.info("Comando: %r (seguimento=%s)", frase, seguimento)

        if self._descansando:   # modo descanso: so a frase de voltar acorda
            if frase_de_volta(frase) or frase_de_volta(frase_completa):
                self._descansando = False
                estado.atualizar(descanso=False)
                self._rota = "saiu do descanso"
                self.voz.falar(self.preencher(random.choice(["Voltei {apelido}! Bora.", "Tô de volta {apelido}.",
                                                             "Acordei {apelido}. O que vamos fazer?"])))
                return self._janela()
            if re.search(r"\b(ta (ai|por ai|me ouvindo|na escuta)|cade voce|voce esta ai)\b", normalizar(frase)):
                self.voz.falar("Tô aqui descansando. Pra voltar fala: bora voltar a trabalhar.")
            self._rota = "ignorado (descansando)"
            return 0.0

        if self._gravacao is not None and self._controle_da_gravacao(frase):   # "pronto", "cancela a rotina"...
            return self._janela()

        if self._pendente:  # o Mestre tinha feito uma pergunta
            responder, self._pendente = self._pendente, None
            n = normalizar(frase)
            if responder == self._continuar_ditado:
                # No ditado so "cancela" sozinho desiste (um "nao" no meio do texto e texto)
                cancelar = re.match(r"^(cancela|cancelar)( o ditado| tudo| isso)?$", n)
            else:
                # Nestas perguntas "nada"/"nao" e resposta, nao desistencia (quem tem aceita_nao trata o "cancela")
                aceitam_nao = (self._responder_aviso_pensamento, self._proj_extra, self._proj_quer_claude)
                cancelar = (responder not in aceitam_nao and not getattr(responder, "aceita_nao", False)
                            and re.match(CANCELAR, n))
            self._rota = "resposta: " + getattr(responder, "__name__", "pergunta").strip("_")
            if cancelar:
                self._rota += " (cancelou)"
                self._ditado_ativo = False
                estado.atualizar(ditado=0, ditado_desde=0.0)
                self._fechar_revisao()
                self.falar("cancelado")
            else:
                self._proteger(responder, frase)
            return self._janela()

        if self._pendente_ia and re.match(CANCELAR, normalizar(frase)):
            # "cancela" logo depois de um comando que a IA descobriu: nao guarda na memoria
            self._cancelar_memoria_ia()
            self._rota = "cancelou memoria da ia"
            self.falar("cancelado")
            return self._janela()

        if not normalizar(frase):  # so chamaram "mestre"
            self._rota = "so chamou"
            self.falar("chamado")
            self._acabou_de_chamar = True
            return self._pendente_espera
        if self._acabou_de_chamar:  # respondeu ao "Pois nao?": nao e conversa ao redor
            self._acabou_de_chamar, seguimento = False, False

        t = self.vocab.traduzir(frase)
        if t != normalizar(frase):
            log.info("Entendi como: %r", t)
        t = self._separar_monitor(t)
        self._entendi = t
        self._seguimento, self._ignorar_seguimento = bool(seguimento), False
        try:
            atendeu = self._tentar_comandos(t)
        finally:
            self._seguimento = False
        if atendeu and self._ignorar_seguimento:   # ex.: "e colocar isso pra eu ver pelo telegram" (sem a palavra)
            self._ignorar_seguimento = False
            self._rota = "ignorado (abrir sem alvo na conversa)"
            return 0.0
        if atendeu:
            self._rota = self.ultimo_comando or "comando"
            return self._janela()

        palavras = normalizar(frase).split()
        if all(len(p) <= 2 for p in palavras) or (len(palavras) == 1 and len(palavras[0]) <= 3):
            self._rota = "ignorado (ruido)"   # "oh", "a b m": barulho, nao pergunta
            return self._janela() if not seguimento else 0.0
        if self._comando_da_memoria(frase):   # a IA ja resolveu esta frase antes: nem precisa pensar
            return self._janela()
        if self.cerebro.ligado:
            self._rota = "ia"
            self._proteger(self._interpretar_com_ia, frase)
            return self._janela()
        if seguimento:
            self._rota = "ignorado (conversa ao redor)"
            return 0.0  # provavelmente conversa ao redor; ignora em silencio
        self._rota = "nao_entendi"
        self.falar("nao_entendi")
        return self._janela()

    def _nomes_monitores(self) -> dict:
        """numero -> nomes falados. 1 = principal. Nomes extras no painel (ex.: "da tv")."""
        nomes = {1: ["principal", "primario", "primeiro", "um", "1"], 2: ["secundario", "segundo", "dois", "2"],
                 3: ["terciario", "adjacente", "terceiro", "tres", "3"], 4: ["quarto", "quatro", "4"]}
        lista = sistema.monitores()
        if len(lista) >= 2 and all("x" in m for m in lista):   # pela posicao na mesa
            por_x = sorted(lista, key=lambda m: m["x"])
            nomes.setdefault(por_x[0]["numero"], []).extend(["esquerda", "da esquerda", "do lado esquerdo"])
            nomes.setdefault(por_x[-1]["numero"], []).extend(["direita", "da direita", "do lado direito"])
            if len(por_x) == 3:
                nomes.setdefault(por_x[1]["numero"], []).extend(["meio", "do meio", "centro", "do centro"])
        for m in lista:   # "monitor LG", "monitor AOC", "monitor de 144"
            extras = [normalizar(m["marca"])] if m.get("marca") else []
            if m.get("hz"):
                extras += [f"de {m['hz']}", f"{m['hz']}", f"de {m['hz']} hertz", f"{m['hz']} hertz"]
            nomes.setdefault(m["numero"], []).extend(e for e in extras if e)
        for numero, nome in ((self.cfg.get("janelas") or {}).get("nomes_monitores") or {}).items():
            try:
                nomes.setdefault(int(numero), []).append(normalizar(str(nome)))
            except ValueError:
                continue
        return nomes

    def _separar_monitor(self, t: str) -> str:
        """"abre o youtube no monitor 2" -> abre no monitor 2 e devolve "abre o youtube"."""
        sistema.MONITOR_ALVO, sistema.JANELA_NOVA = None, False
        sistema.SEMPRE_NO_PRINCIPAL = bool((self.cfg.get("janelas") or {}).get("sempre_no_principal", True))
        sistema.SITES_NO_BRAVE = (self.cfg.get("janelas") or {}).get("navegador_sites", "brave") == "brave"
        from .. import navegador as _nav
        _nav.PERFIL_BRAVE = str((self.cfg.get("janelas") or {}).get("perfil_brave") or "")
        t = self._separar_janela_nova(t)
        resto, numero = self._extrair_monitor(t)
        if numero:
            sistema.MONITOR_ALVO = numero
            log.info("Pedido para o monitor %d", numero)
            return self._separar_janela_nova(resto)
        return t

    PADRAO_JANELA_NOVA = r"\s+(?:em|numa|na|com)\s+(?:uma\s+)?(?:janela\s+(?:nova|separada)|nova\s+janela|outra\s+janela)$"

    def _separar_janela_nova(self, t: str) -> str:
        """ "abre a Netflix numa janela nova" -> não reusa a aba que já existe e devolve "abre a netflix"."""
        achado = re.search(self.PADRAO_JANELA_NOVA, t)
        if not achado or not t[:achado.start()].strip():
            return t
        sistema.JANELA_NOVA = True
        log.info("Pedido numa janela nova")
        return t[:achado.start()].strip()

    def _tentar_comandos(self, t: str) -> bool:
        for nome in self.ORDEM:
            try:
                if getattr(self, nome)(t):
                    self._n_atendidos += 1
                    self.ultimo_comando = nome   # (teste de vocabulario e diario)
                    log.info("Comando atendido por %s", nome)
                    return True
            except Exception:
                log.exception("Erro no comando %s", nome)
                self.falar("erro")
                return True
        return False

    def _proteger(self, funcao, *args) -> None:
        try:
            funcao(*args)
        except Exception:
            log.exception("Erro em %s", getattr(funcao, "__name__", funcao))
            self.falar("erro")

    def _janela(self) -> float:
        return self._pendente_espera if self._pendente else self.janela_conversa

    # =================================================================
    #  Fala com personalidade e dialogos
    # =================================================================
    def preencher(self, texto: str) -> str:
        return (str(texto).replace("{apelido}", self.apelido).replace("{nome}", self.nome)
                .replace("{saudacao}", saudacao_do_horario()))

    def sortear(self, tipo: str) -> str:
        return self.preencher(random.choice(self.falas.get(tipo) or [""]))

    def falar(self, tipo_ou_texto: str) -> None:
        opcoes = self.falas.get(tipo_ou_texto)
        self.voz.falar(self.preencher(random.choice(opcoes)) if opcoes else self.preencher(tipo_ou_texto))

    def todas_as_falas(self) -> list[str]:
        """Tudo que e falado sempre igual: fica pronto no cache ao ligar (sai na hora)."""
        fixas = [f for lista in FALAS_CURTAS.values() for f in lista]
        return [self.preencher(f) for f in fixas] + [self.preencher(f) for lista in self.falas.values() for f in lista]

    def _aviso_curto(self, tipo: str) -> None:
        """Avisos do pensamento: meia palavra ou um bipe (painel > Conversa), para nao comer o seu tempo de falar."""
        som = str(self._cfg_cerebro().get("aviso_som", "nenhum"))
        if som == "nenhum":
            return   # so o indicador na tela (roxo = pensando, verde = pronto)
        if som == "bipe":
            self.voz.bipe(tipo)
        else:
            self.voz.falar(self.preencher(random.choice(FALAS_CURTAS[tipo])))

    def perguntar(self, pergunta: str, ao_responder, espera: float = 12.0) -> None:
        """Faz uma pergunta; a proxima frase (sem precisar de "mestre") vai para ao_responder."""
        self.voz.falar(pergunta)
        self._pendente = ao_responder
        self._pendente_espera = espera

    def _pedido_puro(self) -> str:
        """A frase falada, normalizada, sem a palavra de ativacao e SEM passar pelo vocabulario."""
        achou, comando = extrair_comando(self._frase_original, palavras_ativacao(self.cfg))
        return comando if achou else normalizar(self._frase_original)

    def _responder(self, resposta: str, pergunta: str) -> None:
        """Fala respostas curtas; respostas longas vao para um arquivo na tela."""
        limite = (self.cfg.get("cerebro") or {}).get("limite_caracteres_falados", 500)
        if len(resposta) <= limite:
            self.voz.falar(limpar_para_falar(resposta))
            return
        PASTA_RESPOSTAS.mkdir(exist_ok=True)
        arquivo = PASTA_RESPOSTAS / f"resposta_{datetime.now():%Y-%m-%d_%H-%M-%S}.txt"
        arquivo.write_text(f"PERGUNTA: {pergunta}\n\n{resposta}\n", encoding="utf-8")
        sistema.abrir_arquivo(arquivo)
        primeiro_paragrafo = limpar_para_falar(resposta.split("\n\n")[0])[:limite]
        self.voz.falar(primeiro_paragrafo + ". O resto deixei na tela.")

    def _original(self, trecho: str) -> str:
        """O trecho como foi FALADO (com acentos, cedilha, hifen), para pesquisas."""
        return recuperar_original(self._frase_original, trecho)
