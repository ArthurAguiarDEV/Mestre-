"""Entende o que foi dito e executa o comando certo.

Caminho de uma frase:
  1. o Vocabulario "traduz" o jeito solto de falar  (vocabulario.yaml)
  2. cada metodo _cmd_... da lista ORDEM tenta reconhecer a frase
  3. se nenhum reconhecer e o cerebro estiver ligado, a IA interpreta

Para criar um comando novo:
  1. escreva um metodo  def _cmd_meu_comando(self, t): ...
     (t = frase ja traduzida: sem acentos, minuscula e sem a palavra "mestre")
  2. o metodo devolve True se reconheceu a frase, ou False para passar adiante
  3. coloque o nome dele na lista ORDEM, logo abaixo
"""
import logging
import queue
import random
import re
import shutil
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, quote_plus

from . import estado, informacoes, memoria, personalidades, projetos, sistema, youtube
from .config import palavras_ativacao
from .cerebro import Cerebro
from .config import PASTA_NOTAS, PASTA_PROJETO, PASTA_RESPOSTAS
from .texto import (achar_numero, contem, extrair_comando, frase_de_volta, limpar_para_falar, melhor_correspondencia,
                    normalizar, recuperar_original)
from .vocabulario import Vocabulario, combina
from .voz import Voz

log = logging.getLogger(__name__)

ARQUIVO_MELHORIAS = PASTA_PROJETO / "MELHORIAS.md"
# Avisos curtinhos do "pensando" (ficam no cache: saem sem atraso)
FALAS_CURTAS = {"fundo": ["Segundo plano.", "Vou pensando.", "Deixa comigo."],
                "pronto": ["Pronto {apelido}.", "Pensei {apelido}.", "Tá pronto."]}
ARQUIVO_REVISAO = PASTA_PROJETO / "logs" / "ditado_revisao.json"
PROMPT_MELHORIAS = (
    "Leia o CLAUDE.md e depois o MELHORIAS.md. Para cada item pendente (- [ ]): primeiro use a skill "
    "refinar-pedido para transformar a ideia num pedido claro, me mostre e espere eu confirmar; "
    "depois implemente, rode o teste automatico (venv\\Scripts\\python -m testes.teste_basico, tudo OK) "
    "e teste no modo texto (venv\\Scripts\\python -m app.main --texto --mudo) "
    "e marque o item com [x]. No final, me explique em português simples o que mudou e o que testar falando."
)
DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]
ENFEITES = {"o", "a", "os", "as", "do", "da", "de", "dos", "das", "no", "na", "pra", "para", "pro",
            "me", "ai", "canal", "youtube", "video", "videos", "ultimo", "mais", "e", "um", "uma",
            "toca", "abre", "em", "ver", "assistir", "quero", "novo", "recente"}
CANCELAR = r"^(cancela|cancelar|deixa pra la|deixa|esquece|nada|nao|para|parar|sai)$"
# So palavras de fim bem claras: "manda" ou "envia" no meio do ditado NAO encerram
TERMINAR_DITADO = r"\b(finalizei|finalizado|terminei|acabei|fim do ditado|encerra o ditado|encerrar o ditado)$"
PRONTO_SOZINHO = r"^((e isso|ok|beleza|entao|bom)\s+)?pronto$"   # "pronto" so encerra se vier sozinho
# --- Rotina ensinada falando ("vou te mostrar uma nova rotina" ... "pronto") ---
ROTINA_VERBOS = (r"\b(mostrar|mostra|ensinar|ensina|ensinando|grava|gravar|grave|gravando|aprende|aprender|aprenda|"
                 r"cria|criar|crie|monta|montar|cadastra|cadastrar|nova)\b")
FIM_ROTINA = (r"^((e|ok|beleza|entao|bom|pode|agora)\s+)*(pronto|terminei|acabei|finalizei|e isso|e so isso|so isso|"
              r"acabou|fim)( (a|da|na) rotina)?$|\b(fim da rotina|termin(ei|ou) a rotina|acab(ei|ou) a rotina|"
              r"finaliza(r)? a rotina|salva(r)? a rotina|encerra(r)? a rotina)\b")
CANCELA_ROTINA = (r"\b(cancela|cancelar|cancele|esquece|descarta|desiste|apaga)( essa| a| esta)? (rotina|gravacao)\b|"
                  r"\b(para|pare|parar) de gravar\b|\bdesisto da rotina\b")
# Passos que nao fazem sentido repetir numa rotina (controle do proprio assistente, conversas, ditado...)
NAO_GRAVA_NA_ROTINA = {"_cmd_pensamento", "_cmd_descanso", "_cmd_versao", "_cmd_conversinha", "_cmd_exportar",
                       "_cmd_historico", "_cmd_memoria", "_cmd_ensinar_rotina", "_cmd_encerrar", "_cmd_reiniciar",
                       "_cmd_ajuda", "_cmd_ditado", "_cmd_projeto", "_cmd_feedback", "_cmd_obrigado", "_cmd_aprender",
                       "_cmd_atalhos", "_cmd_melhorias", "_cmd_esquecer", "_cmd_desligar_pc"}
# Variacao da IA que comeca assim parece comando (roubaria o "abre o gmail", o "pausa"...): fica de fora
COMECO_DE_COMANDO = (r"^(abre|abrir|abra|liga|ligar|fecha|fechar|toca|tocar|coloca|bota|pesquisa|pesquisar|procura|"
                     r"busca|aumenta|abaixa|diminui|sobe|baixa|volume|muta|desmuta|pausa|pausar|continua|proxima|"
                     r"proximo|anterior|volta|avanca|desliga|desligar|reinicia|minimiza|maximiza|joga|manda|separa|"
                     r"junta|clica|anota|me lembra|lembra|le|ler|que horas|que dia|qual|quais|como|cancela|esquece|"
                     r"repete|exporta|pode falar|pode descansar|fala|diz|muda|troca|aprende|grava|dita|ditado|valeu|"
                     r"obrigad[oa]|tudo bem|e ai|oi|ola|sim|nao|pronto|terminei|youtube|spotify|netflix)\b")
# Comandos comuns (ainda que nunca falados): uma frase de rotina nao pode aparecer dentro deles
COMANDOS_COMUNS = ["que horas sao", "que dia e hoje", "aumenta o volume", "abaixa o volume", "pausa", "continua",
                   "proxima musica", "proximo video", "tela cheia", "desliga a tela", "liga a tela",
                   "bloqueia o computador", "pode falar", "pode descansar", "bora voltar a trabalhar", "reinicia",
                   "desliga", "le minhas notas", "exporta o historico", "abre o painel", "muda a voz", "valeu"]
# "projeto Mestre" = a conversa do Claude Code onde o Mestre e feito (troque no painel > Projeto)
LINK_PROJETO_PADRAO = "https://claude.ai/code/session_01AhxUrVesiosggbqPjkkedB"
CABECALHO_PROJETO = "[Pedido ditado por voz no Mestre: corrija a transcrição e refine antes de implementar.]\n\n"

VOZES_PADRAO = ["pt-BR-AntonioNeural", "pt-BR-FranciscaNeural", "pt-BR-ThalitaMultilingualNeural",
                "en-US-AndrewMultilingualNeural", "en-US-BrianMultilingualNeural",
                "en-US-AvaMultilingualNeural", "en-US-EmmaMultilingualNeural"]

# Falas padrao = as do estilo padrao (app/personalidades.py). O config pode acrescentar mais.
FALAS_PADRAO = personalidades.estilo(None)["falas"]


def saudacao_do_horario() -> str:
    hora = datetime.now().hour
    # de madrugada (0h as 4h59) ainda e "boa noite"
    return "Boa noite" if hora < 5 else "Bom dia" if hora < 12 else "Boa tarde" if hora < 18 else "Boa noite"


def _quantos(n: int, palavra: str) -> str:
    return f"{n} {palavra}" if n == 1 else f"{n} {palavra}s"


def _resumir(nomes: list, maximo: int = 30) -> str:
    """Lista curta para o prompt da IA (1.900 canais deixariam tudo lento)."""
    texto = ", ".join(nomes[:maximo])
    return texto + (f" (e mais {len(nomes) - maximo})" if len(nomes) > maximo else "")


def link_spotify(link: str) -> str:
    """https://open.spotify.com/playlist/ID?si=... -> spotify:playlist:ID (abre direto no app)."""
    achado = re.search(r"open\.spotify\.com/(?:intl-\w+/)?(playlist|album|artist|track|show)/([A-Za-z0-9]+)", link)
    return f"spotify:{achado.group(1)}:{achado.group(2)}" if achado else link.strip()


ORDINAIS = {"primeiro": 1, "primeira": 1, "segundo": 2, "segunda": 2, "terceiro": 3, "terceira": 3,
            "quarto": 4, "quarta": 4, "quinto": 5, "quinta": 5, "sexto": 6, "sexta": 6, "setimo": 7,
            "setima": 7, "oitavo": 8, "oitava": 8, "nono": 9, "nona": 9, "decimo": 10, "decima": 10,
            "ultimo": -1}


def _ordinal(texto: str) -> int | None:
    for palavra in texto.split():
        if palavra in ORDINAIS and ORDINAIS[palavra] > 0:
            return ORDINAIS[palavra]
    return achar_numero(texto)


def _host(url: str) -> str:
    """ "https://www.netflix.com/browse" -> "netflix.com" """
    from urllib.parse import urlparse
    return urlparse(url).netloc.lower().removeprefix("www.")


def _mesmo_site(url: str, dominio: str) -> bool:
    host = _host(url)
    return host == dominio or host.endswith("." + dominio)


def _nome_do_canal(frase: str) -> str:
    """ "pesquisa pelo canal FRTT" -> "frtt" · "abre o canal do youtube do tck por favor" -> "tck" """
    achado = re.search(r"\bcanal\b(?:\s+(?:do|da|de|no))?(?:\s+youtube)?(?:\s+(?:do|da|de))?\s+(.+)$", frase)
    nome = achado.group(1) if achado else frase
    nome = re.sub(r"\b(no|do|pelo|pela|na) youtube\b|\bpor favor\b|\bai\b", " ", nome)
    return _tirar_enfeites(" ".join(nome.split())) or _tirar_enfeites(frase)


def _tirar_enfeites(t: str) -> str:
    return " ".join(p for p in t.split() if p not in ENFEITES).strip()


class Executor:
    ORDEM = [
        "_cmd_pensamento", "_cmd_descanso", "_cmd_versao", "_cmd_conversinha", "_cmd_exportar", "_cmd_historico", "_cmd_memoria", "_cmd_ensinar_rotina", "_cmd_rotinas", "_cmd_encerrar", "_cmd_reiniciar",
        "_cmd_painel", "_cmd_ajuda", "_cmd_ditado", "_cmd_projeto", "_cmd_feedback", "_cmd_obrigado",
        "_cmd_aprender", "_cmd_atalhos", "_cmd_melhorias", "_cmd_voz",
        "_cmd_agente_ipm", "_cmd_area_transferencia", "_cmd_juntar", "_cmd_mover", "_cmd_volume", "_cmd_midia", "_cmd_janela",
        "_cmd_youtube_controle", "_cmd_spotify", "_cmd_youtube", "_cmd_streaming", "_cmd_clicar",
        "_cmd_clima", "_cmd_noticias", "_cmd_hora_data", "_cmd_tela", "_cmd_desligar_pc",
        "_cmd_lembrete", "_cmd_notas", "_cmd_tocar", "_cmd_pesquisa", "_cmd_abrir", "_cmd_esquecer",
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
        try:
            segundos = self._executar(frase, frase_completa, seguimento)
            if gravacao is not None and gravacao is self._gravacao:   # gravando uma rotina: guarda o passo
                self._proteger(self._gravar_passo, atendidos)
        finally:
            falado, self.voz.registro = self.voz.registro or [], None
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
                # Nestas perguntas "nada"/"nao" e resposta, nao desistencia
                aceitam_nao = (self._responder_aviso_pensamento, self._proj_extra, self._proj_quer_claude)
                cancelar = responder not in aceitam_nao and re.match(CANCELAR, n)
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
        if self._tentar_comandos(t):
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
        sistema.MONITOR_ALVO = None
        sistema.SEMPRE_NO_PRINCIPAL = bool((self.cfg.get("janelas") or {}).get("sempre_no_principal", True))
        sistema.SITES_NO_BRAVE = (self.cfg.get("janelas") or {}).get("navegador_sites", "brave") == "brave"
        from . import navegador as _nav
        _nav.PERFIL_BRAVE = str((self.cfg.get("janelas") or {}).get("perfil_brave") or "")
        achado = re.search(r"\s*\b(?:no|na|pro|pra|para o|para a|ao)\s+(?:meu\s+|minha\s+)?(?:monitor|tela|janela)\s+(?:numero\s+)?(.+?)$", t)
        if not achado:
            return t
        falado = achado.group(1).strip()
        for numero, nomes in self._nomes_monitores().items():
            if falado in nomes or any(n and falado.endswith(n) for n in nomes):
                sistema.MONITOR_ALVO = numero
                log.info("Pedido para o monitor %d", numero)
                return t[:achado.start()].strip()
        return t

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
        if pensando:
            estado.atualizar(pensamento="pensando", pensamento_pergunta=pensando[0]["pergunta"],
                             pensamento_desde=pensando[0]["inicio"], pensamentos_fila=len(pensando))
        else:
            estado.atualizar(pensamento="pronto" if fundo else "", pensamentos_fila=0)

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
        estado.atualizar(pensamento="", pensamentos_fila=0)

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

    def _pedido_puro(self) -> str:
        """A frase falada, normalizada, sem a palavra de ativacao e SEM passar pelo vocabulario."""
        achou, comando = extrair_comando(self._frase_original, palavras_ativacao(self.cfg))
        return comando if achou else normalizar(self._frase_original)

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

    # =================================================================
    #  Rotinas do config.yaml
    # =================================================================
    def _cmd_rotinas(self, t: str) -> bool:
        for rotina in self.cfg.get("rotinas") or []:
            frases = [self.vocab.traduzir(f) for f in rotina.get("frases", [])]
            if any(combina(t, f) for f in frases):
                log.info("Rotina: %s", rotina.get("nome"))
                for acao in rotina.get("acoes", []):
                    self._executar_acao(acao)
                return True
        return False

    def _executar_acao(self, acao: dict) -> None:
        tipo, valor = next(iter(acao.items()))
        if tipo == "falar":
            if valor in (True, None, ""):
                return
            self.voz.falar(self.preencher(valor))
        elif tipo == "acordar_tela":
            sistema.acordar_tela()
        elif tipo == "desligar_tela":
            sistema.desligar_tela()
        elif tipo == "bloquear":
            sistema.bloquear()
        elif tipo == "abrir_programa":
            sistema.abrir_programa((self.cfg.get("programas") or {}).get(valor, valor))
        elif tipo == "abrir_site":
            sistema.abrir_site((self.cfg.get("sites") or {}).get(valor, valor))
        elif tipo == "youtube_ultimo_video":
            self._abrir_ultimo_video(str(valor))
        elif tipo == "youtube_canal":
            self._abrir_canal(str(valor))
        elif tipo == "esperar":
            time.sleep(float(valor))
        elif tipo == "volume":
            sistema.volume(str(valor))
        elif tipo == "data":
            agora = datetime.now()
            self.voz.falar(f"Hoje é {DIAS[agora.weekday()]}, {agora.day} de {MESES[agora.month - 1]}.")
        elif tipo == "clima":
            self.voz.falar(informacoes.clima(str(valor) if valor not in (True, None, "") else self._cidade()))
        elif tipo == "noticias":
            self._falar_noticias(int(valor) if str(valor).isdigit() else 3)
        elif tipo == "ler_notas":
            self._cmd_notas("le minhas notas")
        elif tipo == "melhorias_pendentes":
            pendentes = self._melhorias_pendentes()
            if pendentes:
                self.voz.falar(f"Você tem {_quantos(len(pendentes), 'melhoria')} anotada pro projeto.")
        elif tipo == "abrir_pasta":
            sistema.abrir_arquivo(str(valor))
        elif tipo == "comando":
            # os comandos leem a "frase falada" (_pedido_puro): passa a ser a do passo, nao a que chamou a rotina
            original = self._frase_original
            self._frase_original = str(valor)
            try:
                self._tentar_comandos(self._separar_monitor(self.vocab.traduzir(str(valor))))
            finally:
                self._frase_original = original
            if self._pendente is not None:   # passo de rotina nao fica esperando resposta falada
                log.info("Rotina: o passo %r fez uma pergunta; ignorada", valor)
                self._pendente = None
        else:
            log.warning("Ação desconhecida na rotina: %s", tipo)

    # =================================================================
    #  Ensinar uma rotina falando: "vou te mostrar uma nova rotina", os comandos (cada um roda e fica
    #  gravado), "pronto", a frase de chamar. A IA inventa outros jeitos de pedir, em segundo plano.
    # =================================================================
    @staticmethod
    def _pede_rotina_nova(x: str) -> bool:
        return bool(re.search(r"\brotina\b", x) and re.search(ROTINA_VERBOS, x)
                    and not re.search(CANCELA_ROTINA, x) and not re.search(r"\b(roda|executa|testa)\b", x))

    def _cmd_ensinar_rotina(self, t: str) -> bool:
        """ "vou te mostrar uma nova rotina", "grava uma rotina", "aprende uma rotina nova"."""
        if not (self._pede_rotina_nova(t) or self._pede_rotina_nova(self._pedido_puro())):
            return False
        if self._gravacao is not None:
            self.voz.falar("Já estou gravando. Fala os comandos e no fim fala pronto.")
            return True
        agora = time.time()
        self._gravacao = {"passos": [], "falados": [], "ignorados": 0, "inicio": agora, "ultimo": agora}
        self._rotina_nova = None
        self.voz.falar(self.preencher(random.choice([
            "Beleza {apelido}. Fala os comandos um de cada vez. No fim fala pronto.",
            "Gravando a rotina. Pode falar os comandos e no fim diz pronto.",
            "Tô gravando. Fala os passos e quando acabar diz pronto."])))
        return True

    def _controle_da_gravacao(self, frase: str) -> bool:
        """Durante a gravacao: "pronto" termina, "cancela a rotina" desiste, "fala assim: ..." e
        "espera 5 segundos" viram passos. True = a frase era isso (nao passa para os comandos)."""
        g = self._gravacao
        if time.time() - g["ultimo"] > 900:   # 15 minutos sem nada: esqueceu que estava gravando
            log.info("Gravacao de rotina expirou (%d passos)", len(g["passos"]))
            self._gravacao = None
            return False
        n = normalizar(frase)
        if re.search(CANCELA_ROTINA, n):
            self._gravacao, self._pendente = None, None
            self._rota = "rotina falada: cancelou"
            self.voz.falar(self.preencher(random.choice(["Beleza. Cancelei a rotina.", "Rotina descartada {apelido}."])))
            return True
        if self._ditado_ativo or self._pendente:
            return False   # ditado ou pergunta em andamento: a frase e deles
        if re.search(FIM_ROTINA, n):
            self._gravacao = None
            self._rota = "rotina falada: terminou"
            if not g["passos"]:
                self.voz.falar("Não gravei nenhum passo. Rotina cancelada.")
                return True
            self._rotina_nova = {"acoes": g["passos"], "falados": g["falados"], "ignorados": g["ignorados"],
                                 "tentativas": 0}
            self.perguntar(self.preencher("Rotina aprendida. Qual frase eu uso para chamar?"), self._nomear_rotina,
                           espera=20)
            return True
        if self._anotar_fala_na_rotina(frase):
            g["ultimo"] = time.time()
            self._rota = "rotina falada: passo"
            return True
        return False

    def _anotar_fala_na_rotina(self, frase: str) -> bool:
        """ "fala assim: bom trabalho" vira um passo "falar"; "espera 5 segundos" vira "esperar"."""
        n = normalizar(frase)
        if re.match(r"^(fala|diz|diga|fale) (assim|a frase|isso) \w", n):
            achado = re.search(r"(?i)\b(?:assim|a frase|isso)\b\s*[:,]?\s*(.+)$", self._frase_original or frase)
            texto = (achado.group(1) if achado else n).strip()
            self._gravacao["passos"].append({"falar": texto})
            self._gravacao["falados"].append(normalizar(texto))
            self.voz.falar(texto)
            return True
        if re.match(r"^(espera|esperar|aguarda|aguardar) (\w+ )?segundos?$", n):
            segundos = achar_numero(n) or 1
            self._gravacao["passos"].append({"esperar": segundos})
            self.voz.falar(f"Anotei. Esperar {segundos} segundos.")
            return True
        return False

    def _gravar_passo(self, atendidos_antes: int) -> None:
        """Transforma o que acabou de rodar (a rota que vai para o historico) numa acao de rotina."""
        g = self._gravacao
        g["ultimo"] = time.time()
        rota = self._rota or ""
        if self.ultimo_comando == "_cmd_ensinar_rotina" and self._n_atendidos > atendidos_antes:
            return   # "grava uma rotina" de novo: ja respondeu que esta gravando
        if rota.startswith(("resposta", "so chamou", "ignorado", "saiu do descanso", "rotina falada")) \
                or rota == "nao_entendi":
            return   # respostas a perguntas, barulho e "nao entendi" nao viram passo
        acao = self._acao_de_rotina(atendidos_antes)
        if acao is None:
            g["ignorados"] += 1
            self.voz.falar("Esse passo não entra na rotina.")
            return
        g["passos"].append(acao)
        g["falados"].append(normalizar(self._pedido_puro()))
        log.info("Rotina falada: passo %d = %s", len(g["passos"]), acao)

    def _acao_de_rotina(self, atendidos_antes: int) -> dict | None:
        comando = self.ultimo_comando
        if self._n_atendidos <= atendidos_antes or comando in NAO_GRAVA_NA_ROTINA:
            return None   # foi para a IA (ou nem rodou), ou e controle do proprio assistente
        puro = self._pedido_puro()   # (se a IA traduziu, e o texto dela)
        if comando == "_cmd_abrir" and not sistema.MONITOR_ALVO:
            alvo = self._o_que_abrir(self._entendi or "")
            if alvo and alvo[1]:
                return {"abrir_programa": alvo[1]}
            if alvo and alvo[2]:   # o endereco (igual a rotina "Bora trabalhar")
                return {"abrir_site": str((self.cfg.get("sites") or {}).get(alvo[2]) or alvo[2])}
            return None   # "nao conheco X": nao abriu nada
        return {"comando": puro} if puro else None

    def _nomear_rotina(self, resposta: str) -> None:
        nova = self._rotina_nova
        if not nova:
            return
        frase, nome = self._frase_de_chamar(resposta)
        problema = ""
        if len(frase) < 3:
            problema = "Não peguei a frase. Fala de novo qual frase eu uso."
        elif self._frase_colide(frase, nova["falados"]):
            problema = "Essa frase já chama outro comando. Fala outra."
        if problema:
            nova["tentativas"] += 1
            if nova["tentativas"] >= 3:
                self._rotina_nova = None
                self.voz.falar("Não deu certo. Deixei essa rotina de lado.")
                return
            self.perguntar(problema, self._nomear_rotina, espera=20)
            return
        self._rotina_nova = None
        existentes = {normalizar(str(r.get("nome", ""))) for r in self.cfg.get("rotinas") or []}
        base, i = nome, 2
        while normalizar(nome) in existentes:
            nome, i = f"{base} {i}", i + 1
        frases = [frase] + self._filtrar_frases(self._variacoes_simples(frase), nova["falados"], estrito=False,
                                                ja=[frase])
        self._salvar_rotina(nome, frases, nova["acoes"])
        self._rota = "rotina falada: salvou"
        passos = _quantos(len(nova["acoes"]), "passo")
        extra = f" Deixei de fora {_quantos(nova['ignorados'], 'passo')}." if nova["ignorados"] else ""
        if not self.cerebro.ligado or not hasattr(self.cerebro, "variacoes_de_frase"):
            self.voz.falar(f"Pronto. Salvei a rotina {nome} com {passos} e {_quantos(len(frases), 'frase')}.{extra}"
                           f" É só falar: {frase}.")
            return
        self.voz.falar(f"Salvei a rotina {nome} com {passos}.{extra} Vou pensar em outros jeitos de você pedir.")
        resumo = "; ".join(str(v) for a in nova["acoes"] for v in a.values())[:400]
        falados = nova["falados"]

        def trabalho():   # na fila da IA (segundo plano): pede os jeitos e ja filtra
            variacoes = self.cerebro.variacoes_de_frase(frase, resumo, 50) or []
            return {"variacoes": variacoes, "boas": self._filtrar_frases(variacoes, falados, estrito=True,
                                                                          ja=frases, ignorar=nome)}
        self._pensar(f"jeitos de chamar a rotina {nome}", trabalho,
                     lambda r, n=nome: self._juntar_variacoes(n, r), imediato=True)

    def _frase_de_chamar(self, resposta: str) -> tuple[str, str]:
        """ "usa a frase modo foco" -> ("modo foco", "Modo foco") (o nome mantem os acentos)."""
        n = normalizar(resposta)
        sem = re.sub(r"^((pode|entao|bom|beleza|ok|ah) )*((usa|usar|use|coloca|bota|poe|quero|seria|vai ser)"
                     r"( a frase| o nome| como)?|a frase( e| vai ser| sera)?|chama( de| como| ela de)?|"
                     r"o nome( e| vai ser| sera)?)( |$)", "", n).strip()
        palavras = [p for p in re.sub(r"[\"'“”.!?,;:]", " ", resposta).split()]
        tirar = len(n.split()) - len(sem.split())
        nome = " ".join(palavras[tirar:]) if len(palavras) == len(n.split()) else sem
        return sem, (nome[:1].upper() + nome[1:]) if nome else sem

    @staticmethod
    def _variacoes_simples(frase: str) -> list[str]:
        """Sem IA: alguns jeitos obvios de pedir a mesma coisa."""
        lista = [f"rotina {frase}", f"roda a rotina {frase}"]
        achado = re.match(r"^(bora|vamos|vamo|partiu|simbora)\s+(.+)$", frase)
        if achado:
            lista += [f"{p} {achado.group(2)}" for p in ("bora", "vamos", "partiu")]
        elif frase.startswith("modo "):
            lista += [f"ativa o {frase}", f"liga o {frase}"]
        else:
            lista += [f"bora {frase}", f"{frase} agora"]
        return lista

    def _frases_de_comandos(self) -> list[str]:
        """Frases que o Executor ja mandou para outros comandos (historico real) + comandos comuns."""
        frases = list(COMANDOS_COMUNS)
        try:
            for item in memoria.historico(2000):
                rota = str(item.get("rota") or "")
                if rota.startswith("_cmd_") and rota != "_cmd_rotinas" and item.get("entendi"):
                    frases.append(normalizar(str(item["entendi"])))
        except Exception:
            log.exception("Historico para conferir a frase da rotina")
        frases += [str(c) for c in (getattr(self.vocab, "atalhos", None) or {}).values()]
        return [f for f in dict.fromkeys(frases) if f]

    def _frase_colide(self, frase: str, falados=(), estrito: bool = False, comandos=None, ignorar: str = "") -> bool:
        """A frase roubaria outro comando/rotina (ou seria pega por um comando antes da rotina)?
        estrito (variacoes da IA): tambem nada que comece como comando ("abre", "toca"...) e no minimo 2 palavras."""
        t = self.vocab.traduzir(frase)
        if not t or len(t) < 3 or self._pede_rotina_nova(t) or re.search(CANCELA_ROTINA, t) or re.search(FIM_ROTINA, t):
            return True
        if estrito and (re.match(COMECO_DE_COMANDO, t) or len(t.split()) < 2):
            return True
        for rotina in self.cfg.get("rotinas") or []:
            if ignorar and rotina.get("nome") == ignorar:
                continue
            for f in rotina.get("frases", []):
                outra = self.vocab.traduzir(str(f))
                if outra and (combina(t, outra) or combina(outra, t)):
                    return True
        for c in list(comandos if comandos is not None else self._frases_de_comandos()) + list(falados):
            if c and (combina(c, t) or c == t):   # a rotina vem ANTES dos comandos: ela roubaria "c"
                return True
        return False

    def _filtrar_frases(self, frases, falados=(), estrito: bool = True, ja=(), ignorar: str = "") -> list[str]:
        """Tira repetidas (depois do vocabulario) e as que colidem com comandos existentes."""
        comandos = self._frases_de_comandos()
        vistas = {self.vocab.traduzir(normalizar(str(f))) for f in ja}
        palavra = "|".join(re.escape(x) for x in {normalizar(self.palavra), normalizar(self.nome)} if x)
        boas = []
        for bruta in frases:
            f = normalizar(str(bruta))
            if palavra:
                f = re.sub(rf"^({palavra}) |( {palavra})$", "", f).strip()
            if not f or len(f) > 60 or len(f.split()) > 8:
                continue
            chave = self.vocab.traduzir(f)
            if chave in vistas or self._frase_colide(f, falados, estrito, comandos, ignorar):
                continue
            boas.append(f)
            vistas.add(chave)
        return boas

    def _salvar_rotina(self, nome: str, frases: list[str], acoes: list[dict] | None = None) -> int:
        """Cria a rotina (ou acrescenta frases a ela) no config.yaml, preservando os comentarios."""
        from . import configuracao
        dados = configuracao.carregar()
        lista = dados.get("rotinas")
        if not isinstance(lista, list):
            dados["rotinas"] = lista = configuracao.aspas([])
        item = next((r for r in lista if normalizar(str(r.get("nome", ""))) == normalizar(nome)), None)
        if item is None:
            item = configuracao.aspas({"nome": nome, "acoes": acoes or []})
            item.insert(1, "frases", configuracao.lista_em_linha(frases))
            lista.append(item)
        else:
            atuais = [str(f) for f in item.get("frases") or []]
            item["frases"] = configuracao.lista_em_linha(list(dict.fromkeys(atuais + list(frases))))
        configuracao.salvar(dados)
        # na memoria tambem: ja funciona sem reiniciar
        simples = {"nome": nome, "frases": [str(f) for f in item["frases"]],
                   "acoes": [{str(k): str(v) if isinstance(v, str) else v for k, v in dict(a).items()}
                             for a in item.get("acoes") or []]}
        rotinas = self.cfg.setdefault("rotinas", []) if isinstance(self.cfg.get("rotinas"), list) else None
        if rotinas is None:
            rotinas = self.cfg["rotinas"] = []
        for i, r in enumerate(rotinas):
            if normalizar(str(r.get("nome", ""))) == normalizar(nome):
                rotinas[i] = simples
                break
        else:
            rotinas.append(simples)
        log.info("Rotina falada salva: %s (%d frases, %d acoes)", nome, len(simples["frases"]), len(simples["acoes"]))
        return len(simples["frases"])

    def _juntar_variacoes(self, nome: str, resultado) -> None:
        """A IA terminou: guarda os outros jeitos de pedir (ja filtrados: sem repetidas e sem as que roubariam
        comandos)."""
        resultado = resultado if isinstance(resultado, dict) else {}
        variacoes, novas = resultado.get("variacoes") or [], resultado.get("boas") or []
        atual = next((r for r in self.cfg.get("rotinas") or [] if r.get("nome") == nome), {})
        total = self._salvar_rotina(nome, novas) if novas else len(atual.get("frases", []))
        log.info("Rotina falada %s: a IA mandou %d jeitos, entraram %d", nome, len(variacoes or []), len(novas))
        if not variacoes:
            self.voz.falar(f"A IA não mandou outros jeitos. A rotina {nome} ficou com {_quantos(total, 'frase')}.")
        else:
            self.voz.falar(f"Pronto. A rotina {nome} ficou com {_quantos(total, 'frase')} para chamar.")

    # =================================================================
    #  Controle do proprio Mestre
    # =================================================================
    def _cmd_versao(self, t: str) -> bool:
        """ "qual a sua versão?", "em que versão você está?" """
        if not re.search(r"\b(qual|que|em que) (e )?(a )?(sua |tua )?versao\b|\bversao (do|da) (projeto|assistente|mestre)\b|"
                         r"\b(sua|tua) versao\b", t):
            return False
        from .atualizar import versao_atual
        self.voz.falar(f"Estou na versão {versao_atual()}.")
        return True

    def _cmd_encerrar(self, t: str) -> bool:
        """ "desliga", "pode desligar", "desliga o Assessor", "se desliga", "encerra você"."""
        nomes = "|".join(sorted({"assistente", "mestre", re.escape(normalizar(self.nome)), re.escape(normalizar(self.palavra))} - {""}))
        puro = self._pedido_puro()
        sozinho = r"^(pode |ja pode |agora |entao )?(se )?(desliga|desligar|desligue|encerra|encerrar|encerre)( ai| agora| voce| tudo| por hoje| o programa)?( por favor)?$"
        com_nome = rf"\b(fecha|fechar|desliga|desligar|desligue|encerra|encerrar)( o| a)? ({nomes})\b"
        if not (re.search(sozinho, t) or re.search(sozinho, puro) or re.search(com_nome, t) or re.search(com_nome, puro)):
            return False
        self.falar("despedida")
        self.rodando = False
        return True

    def _cmd_reiniciar(self, t: str) -> bool:
        if not re.search(r"\b(reinicia|reiniciar|recarrega|recarregar|atualiza|atualizar) (o |a |as )?(assistente|mestre|configuracao|configuracoes|vocabulario)\b|\breinicia(r)? voce\b|^(se )?(reinicia|reiniciar|reinicia ai)$", t):
            return False
        if "--texto" in sys.argv:  # no modo texto, so recarrega o vocabulario
            self.vocab.recarregar()
            self.voz.falar("Recarreguei o vocabulário. Mudanças no código ou no config pedem fechar e abrir de novo.")
            return True
        self.voz.falar("Reiniciando! Volto em alguns segundos.")
        sistema.reiniciar_mestre()
        return True

    def _cmd_painel(self, t: str) -> bool:
        if re.search(r"\babre (o |as |a )?(painel|configuracoes|configuracao|ajustes)\b", t) and not re.search(r"\bwindows\b", t):
            self.voz.falar(random.choice(["Abrindo o painel.", "Painel na tela!"]))
            sistema.abrir_painel()
            return True
        return False

    # =================================================================
    #  Feedback: "isso ta errado" guarda o erro para o Claude Code corrigir
    # =================================================================
    def _cmd_feedback(self, t: str) -> bool:
        achado = re.search(r"\b(isso (ta|esta) errado|ta errado|voce errou|errou|nao era isso|nao foi isso|"
                           r"entendeu errado|feedback)\b", t)
        if not achado:
            return False
        self._foi_feedback = True
        self._cancelar_memoria_ia()   # FEEDBACK/"nao era isso": nao guarda (e apaga se ja tinha guardado)
        if not self._ultimo:
            self.voz.falar("Ainda não fiz nada pra você corrigir.")
            return True
        correcao = re.split(r"(?i)\b(feedback|errado|errou|isso|era|foi)\b[\s,:.]*", self._frase_original)[-1].strip(" ,.")
        if len(correcao) < 3:
            self.perguntar("Poxa. O que era pra eu ter feito?", self._salvar_feedback, espera=20)
        else:
            self._salvar_feedback(correcao)
        return True

    def _salvar_feedback(self, correcao: str) -> None:
        self._foi_feedback = True
        u = self._ultimo
        audio = estado.ler().get("audio_anterior") or b""
        anexo = ""
        if audio:
            from .audio import salvar_wav

            pasta = PASTA_PROJETO / "logs" / "feedback"
            pasta.mkdir(parents=True, exist_ok=True)
            arquivo = pasta / f"{datetime.now():%Y%m%d_%H%M%S}.wav"
            salvar_wav(audio, arquivo)
            anexo = f" [áudio: logs/feedback/{arquivo.name}]"
        self._salvar_melhoria(
            f"FEEDBACK: ouvi \"{u.get('ouvi', '')}\" · entendi \"{u.get('entendi', '')}\" · "
            f"respondi \"{u.get('respondi', '')}\" · o certo era: {correcao.strip()}{anexo}")

    def _cmd_obrigado(self, t: str) -> bool:
        if re.fullmatch(r"(muito )?(obrigado|obrigada|brigado|brigada|valeu|vlw|agradecido|thanks)( (demais|mesmo|cara|mano))?", t):
            self.falar("obrigado")
            return True
        return False

    def _cmd_esquecer(self, t: str) -> bool:
        if re.fullmatch(r"(esquece a conversa|nova conversa|limpa a conversa|esquece tudo)", t):
            self.cerebro.esquecer()
            self.voz.falar("Pronto, página em branco. Conversa nova.")
            return True
        return False

    def _cmd_ajuda(self, t: str) -> bool:
        if not re.search(r"(o que voce (sabe|consegue|pode) fazer|quais (sao )?(os )?(seus )?comandos|\bajuda\b|me ajuda)", t):
            return False
        self.voz.falar(
            "Eu rodo suas rotinas, tipo bora trabalhar. Abro programas, sites e o último vídeo "
            "de um canal do YouTube. Falo a hora, mexo no volume, apago e acendo a tela. "
            "Faço lembretes e anotações. Mando perguntas e ditados pro seu agente IPM. "
            "E você pode me ensinar atalhos, trocar minha voz e ditar melhorias longas. "
            "É só falar: quero ditar melhorias. E no fim: finalizei."
        )
        return True

    # =================================================================
    #  Ensinar atalhos por voz
    # =================================================================
    def _cmd_aprender(self, t: str) -> bool:
        # Tudo numa frase so: "Quando eu falar bora codar, abre o VS Code"
        if re.match(r"^quando eu (falar|disser|dizer|pedir)\b", t):
            achado = re.search(r"(?i)quando eu (falar|disser|dizer|pedir)\s+(.+)", self._frase_original)
            resto = achado.group(2) if achado else ""
            if "," in resto:
                gatilho, comando = resto.split(",", 1)
                self._salvar_atalho(gatilho, comando)
            else:
                self.voz.falar("Fala com uma pausa entre as partes, ou fala: {palavra}, aprende um atalho.")
            return True
        if not re.search(r"\b(aprende|aprenda|aprender|cria|criar|ensinar|te ensinar|novo) (um |uma )?(atalho|comando|frase)\b", t):
            return False
        self.perguntar("Bora! Qual frase você vai falar?", self._aprender_passo_2)
        return True

    def _aprender_passo_2(self, gatilho: str) -> None:
        gatilho = gatilho.strip(" ,.!?")
        self.perguntar(f"Beleza. E quando você falar {gatilho}, o que eu faço?",
                       lambda comando: self._salvar_atalho(gatilho, comando), espera=15)

    def _salvar_atalho(self, gatilho: str, comando: str) -> None:
        falado = comando.strip(" ,.!?")
        gatilho, comando = normalizar(gatilho), normalizar(comando)
        if not gatilho or not comando:
            self.voz.falar("Faltou uma parte. Tenta de novo: {palavra}, aprende um atalho.")
            return
        self.vocab.aprender_atalho(gatilho, comando)
        self.voz.falar(f"Aprendido! Quando você falar {gatilho}, eu faço: {falado}.")

    def _cmd_atalhos(self, t: str) -> bool:
        achado = re.match(r"^(esquece|apaga|remove|deleta) (o )?(atalho|comando) (.+)", t)
        if achado:
            if self.vocab.esquecer_atalho(achado.group(4)):
                self.voz.falar(f"Pronto, esqueci o atalho {achado.group(4)}.")
            else:
                self.voz.falar("Não achei esse atalho entre os que você me ensinou.")
            return True
        if re.search(r"\b(quais|lista|listar|fala) (sao )?(os |meus |seus )?atalhos\b", t):
            atalhos = self.vocab.atalhos
            if not atalhos:
                self.voz.falar("Ainda não tenho nenhum atalho.")
            else:
                lista = ". ".join(f"{k}: {v}" for k, v in list(atalhos.items())[:8])
                self.voz.falar(f"Tenho {_quantos(len(atalhos), 'atalho')}. {lista}.")
            return True
        return False

    # =================================================================
    #  Melhorias: anote por voz, o Claude Code implementa
    # =================================================================
    def _cmd_melhorias(self, t: str) -> bool:
        if re.search(r"\b(aplica|aplicar|implementa|implementar|trabalha|faz|fazer|executa)\b.*\b(melhorias|ideias|sugestoes)\b", t):
            self._aplicar_melhorias()
            return True
        if re.search(r"\b(le|quais sao|lista|fala) (as )?(minhas )?(melhorias|ideias)\b", t):
            pendentes = self._melhorias_pendentes()
            if not pendentes:
                self.voz.falar("Não tem nenhuma melhoria pendente.")
            else:
                self.voz.falar(f"{_quantos(len(pendentes), 'pendente')}: " + ". ".join(pendentes[:5]))
            return True
        achado = re.search(r"\b(anota|registra|tenho|nova|anotar|salva) (uma |a )?(melhoria|ideia|sugestao)( (pra|para|pro) (voce|o mestre|mestre))?\b", t)
        if not achado:
            return False
        # Pega o texto depois de "melhoria"/"ideia" na frase original (com acentos)
        partes = re.split(r"(?i)melhoria|ideia|ideia|sugest[aã]o", self._frase_original, maxsplit=1)
        ideia = re.sub(r"^[\s,:;.!-]*((pra|para|pro)\s+(você|voce|o mestre|mestre)\b)?[\s,:;.!-]*", "",
                       partes[1] if len(partes) > 1 else "", flags=re.I).strip()
        if len(ideia) < 4:
            self.perguntar("Manda a ideia, tô anotando.", self._salvar_melhoria, espera=20)
        else:
            self._salvar_melhoria(ideia)
        return True

    def _salvar_melhoria(self, ideia: str, falar: bool = True) -> None:
        if not ARQUIVO_MELHORIAS.exists():
            ARQUIVO_MELHORIAS.write_text(
                "# Melhorias para o Mestre\n\n"
                "Ideias anotadas por voz. O Claude Code implementa as pendentes (- [ ]).\n\n",
                encoding="utf-8")
        linhas = [x.strip() for x in ideia.strip().splitlines() if x.strip()] or [""]
        with open(ARQUIVO_MELHORIAS, "a", encoding="utf-8") as f:
            f.write(f"- [ ] ({datetime.now():%d/%m/%Y}) {linhas[0]}\n")
            for continuacao in linhas[1:]:   # ditado longo: o resto fica recuado, no mesmo item
                f.write(f"      {continuacao}\n")
        if falar:
            self.voz.falar(random.choice(["Anotado na lista de melhorias!", "Ideia guardada!",
                                          "Boa! Anotei na lista."]))

    def _melhorias_pendentes(self) -> list[str]:
        if not ARQUIVO_MELHORIAS.exists():
            return []
        return [re.sub(r"^- \[ \] (\(.*?\) )?", "", linha).strip()
                for linha in ARQUIVO_MELHORIAS.read_text(encoding="utf-8").splitlines()
                if linha.startswith("- [ ]")]

    def _aplicar_melhorias(self) -> None:
        pendentes = self._melhorias_pendentes()
        if not pendentes:
            self.voz.falar("A lista de melhorias está vazia. Me fala uma ideia primeiro.")
            return
        if not shutil.which("claude"):
            self.voz.falar("Pra isso eu preciso do Claude Code instalado. Abri a lista de melhorias; "
                           "o passo a passo está no guia, na etapa 14.")
            sistema.abrir_arquivo(ARQUIVO_MELHORIAS)
            return
        self.voz.falar(f"Chamando o Claude Code pra trabalhar em {_quantos(len(pendentes), 'melhoria')}. "
                       "Acompanha na janela que vai abrir. Quando terminar, fala: {palavra}, reinicia.")
        sistema.abrir_terminal_com(f'claude "{PROMPT_MELHORIAS}"', PASTA_PROJETO, "Mestre - melhorias")

    # =================================================================
    #  Voz: trocar, acelerar, engrossar
    # =================================================================
    def _aplicar_preferencias_de_voz(self) -> None:
        p = self.vocab.preferencia
        self.voz.configurar(voz=p("voz"), velocidade=p("velocidade"), tom=p("tom"))

    def _vozes_favoritas(self) -> list[str]:
        if self.voz.motor == "kokoro":
            from .voz_kokoro import VOZES
            return list(VOZES)
        return (self.cfg.get("voz") or {}).get("vozes_favoritas") or VOZES_PADRAO

    def _voz_atual(self) -> str:
        return self.voz.voz_kokoro if self.voz.motor == "kokoro" else self.voz.voz_edge

    @staticmethod
    def _nome_da_voz(v: str) -> str:
        from .voz_kokoro import VOZES
        if v in VOZES:
            return VOZES[v].split(" ")[0]
        partes = v.split("-")
        return (partes[2] if len(partes) > 2 else v).replace("Neural", "").replace("Multilingual", "")

    def _cmd_voz(self, t: str) -> bool:
        if not re.search(r"\b(voz|vozes|fala|falar|fale)\b", t):
            return False
        if re.search(r"\b(apresenta|mostra|abre|testa|quais) (as )?(suas )?vozes\b|\bvozes disponiveis\b", t):
            self._apresentar_vozes()
            return True
        if re.search(r"\b(muda|troca|trocar|mudar|outra) (a |de )?voz\b|\boutra voz\b|\bproxima voz\b", t):
            favoritas = self._vozes_favoritas()
            atual = self._voz_atual()
            nova = favoritas[(favoritas.index(atual) + 1) % len(favoritas)] if atual in favoritas else favoritas[0]
            self._trocar_voz(nova)
            return True
        achado = re.search(r"\b(usa|use|coloca|abre|quero) a voz (do |da |de )?(.+)", t)
        if achado:
            nome = achado.group(3).replace(" ", "")
            nova = next((v for v in self._vozes_favoritas()
                         if nome in normalizar(v + self._nome_da_voz(v)).replace(" ", "")), None)
            if nova:
                self._trocar_voz(nova)
            else:
                self.voz.falar(f"Não achei a voz {achado.group(3)} nas favoritas. Olha a lista no config.")
            return True
        ajustes = [
            (r"mais rapido|mais depressa|acelera", "velocidade", 10),
            (r"mais devagar|mais lento|com calma", "velocidade", -10),
            (r"mais grave|mais grosso|voz grossa", "tom", -5),
            (r"mais agudo|mais fino|voz fina", "tom", 5),
        ]
        for padrao, campo, passo in ajustes:
            if re.search(padrao, t):
                atual = self.vocab.preferencia(campo) or ("+10%" if campo == "velocidade" else "+0Hz")
                numero = int(re.sub(r"[^\d-]", "", atual) or 0) + passo
                valor = f"{numero:+d}%" if campo == "velocidade" else f"{numero:+d}Hz"
                self.vocab.salvar_preferencia(campo, valor)
                self._aplicar_preferencias_de_voz()
                self.voz.falar("Assim tá melhor?")
                return True
        if re.search(r"\b(volta|voltar) (a )?voz (ao|pro) normal\b|\bvoz normal\b", t):
            for campo in ("voz", "velocidade", "tom"):
                self.vocab.salvar_preferencia(campo, None)
            self.voz.configurar(**{k: (self.cfg.get("voz") or {}).get(c) for k, c in
                                   (("voz", "voz_edge"), ("velocidade", "velocidade"), ("tom", "tom"))})
            self.voz.falar("Voltei pra voz original.")
            return True
        return False

    def _trocar_voz(self, nova: str) -> None:
        self.vocab.salvar_preferencia("voz", nova)
        self._aplicar_preferencias_de_voz()
        self.voz.falar(f"E aí, chefe! Essa é a voz {self._nome_da_voz(nova)}. Curtiu?")

    def _apresentar_vozes(self) -> None:
        original = self._voz_atual()
        vozes = self._vozes_favoritas()
        for i, v in enumerate(vozes, 1):
            self.voz.configurar(voz=v)
            self.voz.falar(f"Voz número {i}: {self._nome_da_voz(v)}. Fala, chefe! Bora trabalhar?")
        self.voz.configurar(voz=original)
        self.voz.falar(f"Pra escolher, fala por exemplo: {{palavra}}, usa a voz do {self._nome_da_voz(vozes[-1])}.")

    # =================================================================
    #  Agente IPM
    # =================================================================
    def _cfg_ipm(self) -> dict:
        return self.cfg.get("agente_ipm") or {}

    def _cmd_agente_ipm(self, t: str) -> bool:
        if not contem(t, "agente ipm"):
            return False
        if re.search(r"\b(copiei|copiado|area de transferencia|o que ta copiado|o que esta copiado)\b", t):
            return False  # tratado em _cmd_area_transferencia
        if re.search(r"\babre\b", t) and re.fullmatch(r"(abre )?(o |a )?(meu )?agente ipm( no claude)?", t):
            sistema.abrir_site(self._cfg_ipm().get("link_projeto", "https://claude.ai/projects"))
            self.voz.falar("Abri seu agente IPM no Claude.")
            return True
        pergunta = self._texto_depois_de("agente ipm")
        if re.search(r"\b(ditado|ditar|vou ditar|vou falar|caso longo)\b", t) or len(pergunta) < 4:
            self._iniciar_ditado("ipm")
            return True
        self._enviar_ao_agente(pergunta)
        return True

    def _original(self, trecho: str) -> str:
        """O trecho como foi FALADO (com acentos, cedilha, hifen), para pesquisas."""
        return recuperar_original(self._frase_original, trecho)

    def _texto_depois_de(self, gatilho: str) -> str:
        """Pega, na frase ORIGINAL (com acentos), o que vem depois do gatilho ou de um sinonimo dele."""
        for jeito in self.vocab.jeitos_de(gatilho):
            padrao = r"[\W_]+".join(re.escape(p) for p in jeito.split())
            partes = re.split(padrao, self._frase_original, maxsplit=1, flags=re.IGNORECASE)
            if len(partes) > 1:
                return re.sub(r"^[\s,:;.!?-]*(sobre\s+)?", "", partes[1]).strip()
        return ""

    # =================================================================
    #  Ditado longo: fale o quanto quiser, com pausas; termine com "finalizei"
    # =================================================================
    def _quer_ditar_melhorias(self) -> bool:
        """Palavras-chave: "melhoria/melhorar/ideia/ajuste/feedback" + um verbo de intencao ou "projeto/Mestre".

        Ex.: "quero melhorar uma coisa no projeto", "tenho umas ideias pra voce", "modo melhorias".
        """
        puro = self._pedido_puro()
        if not re.search(r"\b(melhorias?|melhorar|melhora|ideias?|sugestao|sugestoes|ajustes?|feedback)\b", puro):
            return False
        if re.search(r"\b(le|leia|lista|listar|quais|aplica|aplicar|implementa|implementar|minhas melhorias)\b", puro):
            return False   # "le minhas melhorias", "aplica as melhorias"
        # "anota uma melhoria: deixar o painel azul" (a ideia ja veio junto) -> anotacao rapida
        direto = re.search(r"\b(anota|registra|salva|nova) (uma |a )?(melhoria|ideia|sugestao)\b(.*)", puro)
        if direto and len(direto.group(4).split()) >= 4:
            return False
        nomes = {normalizar(self.nome), self.palavra, "mestre"}
        alvo = re.search(r"\b(projeto|voce|assistente|sistema|app|programa)\b", puro) or any(
            n and contem(puro, n) for n in nomes)
        verbo = re.search(r"\b(quero|queria|vou|vamos|bora|tenho|preciso|posso|deixa|modo|registrar|anotar|"
                          r"passar|criar|fazer|dar|ditar|mandar|falar)\b", puro)
        if not re.search(r"\b(melhorias?|melhorar|melhora|ajustes?|feedback)\b", puro):
            return bool(alvo)   # so "ideia"/"sugestao": precisa falar do projeto ("quero uma sugestao de filme" nao e)
        return bool(alvo or verbo)

    def _cmd_ditado(self, t: str) -> bool:
        if self._quer_ditar_melhorias():
            self._iniciar_ditado("projeto")
            return True
        if not re.search(r"\b(vou ditar|quero ditar|modo ditado|ditado|ditar|pedido longo|texto longo)\b", t):
            return False
        if contem(t, "agente ipm"):
            return False  # tratado em _cmd_agente_ipm
        destino = ("projeto" if re.search(r"\b(melhorias?|ideias?|sugestao|sugestoes|projeto|claude code)\b", t) else
                   "nota" if re.search(r"\b(nota|notas|anotacao)\b", t) else None)
        self._iniciar_ditado(destino)
        return True

    def _silencio_ditado(self) -> float:
        return float((self.cfg.get("ouvido") or {}).get("ditado_silencio_max") or 180)

    def _iniciar_ditado(self, destino: str | None = "ipm") -> None:
        self._ditado = []
        self._destino_ditado = destino
        self._espera_ditado = self._silencio_ditado()
        self._ditado_ativo = True
        self._ditado_sessao += 1
        self._ditado_ultimo = time.time()
        estado.atualizar(ditado=0, ditado_desde=time.time(), ditado_contexto="")
        self.perguntar("Pode falar. Pode pausar pra pensar. Quando acabar, diga: finalizei.",
                       self._continuar_ditado, espera=self._espera_ditado)
        threading.Thread(target=self._vigiar_ditado, args=(self._ditado_sessao,), daemon=True).start()

    def _vigiar_ditado(self, sessao: int) -> None:
        """Fecha o ditado sozinho depois de muito tempo em silencio (sem perder o que foi dito)."""
        while self._ditado_ativo and self._ditado_sessao == sessao:
            time.sleep(1)
            if estado.ler()["nome"] in ("gravando", "transcrevendo"):
                continue
            if self._ditado_ativo and time.time() - self._ditado_ultimo > self._espera_ditado:
                if self._pendente == self._continuar_ditado:
                    self._pendente = None
                if self._ditado:
                    self.voz.falar("Fiquei muito tempo sem ouvir nada, então fechei o ditado.")
                self._finalizar_ditado()
                return

    def _continuar_ditado(self, trecho: str) -> None:
        # Guarda a frase COMO FOI FALADA (com acentos e pontuacao), nao a versao "limpa" do comando
        trecho = self._frase_original or trecho
        n = normalizar(trecho)
        self._ditado_ultimo = time.time()
        if re.search(r"^(apaga|corta|tira) (a |o )?(ultima|ultimo)", n):
            if self._ditado:
                self._ditado.pop()
            estado.atualizar(ditado=len(self._ditado))
            self.perguntar("Apaguei o último trecho.", self._continuar_ditado, espera=self._espera_ditado)
            return
        if re.search(TERMINAR_DITADO, n) or re.match(PRONTO_SOZINHO, n):
            # "…e é isso. Finalizei" -> guarda o que veio antes da palavra de fim
            resto = re.split(r"(?i)[,.!\s]*(pronto|finalizei|finalizado|terminei|acabei|"
                             r"fim do ditado|encerra o ditado|encerrar o ditado)[.!\s]*$", trecho)[0].strip()
            if re.match(PRONTO_SOZINHO, normalizar(resto + " pronto")) and len(normalizar(resto).split()) <= 2:
                resto = ""   # era só "ok, pronto"
            if resto:
                self._ditado.append(resto)
            self._finalizar_ditado()
            return
        # Trecho normal: guarda em silencio (o indicador mostra o tempo)
        self._ditado.append(trecho.strip())
        estado.atualizar(ditado=len(self._ditado), ditado_contexto=" ".join(self._ditado)[-300:])
        self._pendente = self._continuar_ditado
        self._pendente_espera = self._espera_ditado

    def _finalizar_ditado(self) -> None:
        self._ditado_ativo = False
        estado.atualizar(ditado=0, ditado_desde=0.0)
        if not self._ditado:
            self.voz.falar("Não anotei nada.")
            return
        texto = "\n".join(self._ditado)
        self._texto_ditado = texto
        destino = self._destino_ditado
        revisar = bool((self.cfg.get("ditado") or {}).get("revisar_na_janela", True))
        trechos = _quantos(len(self._ditado), "trecho")
        if destino and not revisar:
            self._entregar_ditado(texto, destino)
            return
        if revisar:
            self._abrir_revisao(texto, destino)
        if destino:
            pergunta = (f"Anotei {trechos}. Confere na janela e fala manda que eu levo pro "
                        f"{self._nome_do_destino(destino)}.")
        else:
            pergunta = (f"Anotei {trechos}. Mando pro agente IPM ou pro projeto {self.nome}?"
                        + (" Se quiser, corrige o texto na janela." if revisar else ""))
        self.perguntar(pergunta, self._responder_destino, espera=90)

    def _nome_do_destino(self, destino: str) -> str:
        return {"ipm": "agente IPM", "projeto": f"projeto {self.nome}", "salvar": "lista de melhorias",
                "nota": "bloco de notas", "copiar": "Control C"}.get(destino, destino)

    def _qual_destino(self, resposta: str) -> str | None:
        """Para onde vai o ditado. 'projeto' = esta conversa do Claude Code (+ MELHORIAS.md)."""
        d = normalizar(resposta)
        original = normalizar(self._frase_original or resposta)
        if re.search(r"\b(copia|copiar|area de transferencia)\b", d):
            return "copiar"
        if re.search(r"\b(so salva|so salvar|salva so|so guarda|so guardar|so anota|so na lista)\b", d):
            return "salvar"
        if re.search(r"\b(nota|notas|anotacao|bloco de notas)\b", d):
            return "nota"
        if re.search(r"\b(chat novo|novo chat|conversa nova|nova conversa)\b", d):
            return "chat"
        nomes = {normalizar(self.nome), self.palavra, "mestre"}
        if (re.search(r"\b(projeto|claude code|code|codigo|melhorias?|conversa|assistente)\b", d)
                or any(n and contem(d, n) for n in nomes)
                or any(n and re.search(rf"\b(pro|pra|para|para o|no|ao)\s+{re.escape(n)}\b", original) for n in nomes)):
            return "projeto"
        if re.search(r"\b(ipm|agente|trabalho|atende)\b", d):
            return "ipm"
        if re.search(r"\bclaude\b", d):
            return "?"   # "manda pro Claude": pode ser qualquer um dos dois
        return None

    def _responder_destino(self, resposta: str) -> None:
        texto = self._texto_revisado()
        destino = self._qual_destino(resposta)
        if destino is None and self._destino_ditado and re.search(
                r"\b(manda|pode mandar|envia|pode enviar|sim|isso|pode|ok|beleza|confirma|leva|bora)\b",
                normalizar(resposta)):
            destino = self._destino_ditado
        if destino == "?":
            self.perguntar(f"Pro agente IPM ou pro projeto {self.nome}?", self._responder_destino, espera=60)
            return
        if destino is None:
            self.perguntar(f"Não peguei. Agente IPM, projeto {self.nome}, só salvar ou copiar?",
                           self._responder_destino, espera=60)
            return
        self._fechar_revisao()
        self._entregar_ditado(texto, destino)

    def _entregar_ditado(self, texto: str, destino: str) -> None:
        if not texto.strip():
            self.voz.falar("O texto ficou vazio, então não mandei nada.")
            return
        if destino == "ipm":
            self._enviar_ao_agente(texto)
        elif destino == "projeto":
            self._enviar_ao_projeto(texto)
        elif destino == "salvar":
            self._salvar_melhoria(texto)
        elif destino == "chat":
            self._enviar_chat_novo(texto)
        elif destino == "nota":
            PASTA_NOTAS.mkdir(exist_ok=True)
            with open(PASTA_NOTAS / "notas.txt", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now():%d/%m/%Y %H:%M}] {texto.replace(chr(10), ' ')}\n")
            self.falar("ok")
        else:
            sistema.copiar(texto)
            self.voz.falar("Copiado! É só colar onde quiser com Control V.")

    # --- janela de revisao (processo separado: app/revisar_ditado.py) -------------------
    def _abrir_revisao(self, texto: str, destino: str | None) -> None:
        import json

        ARQUIVO_REVISAO.parent.mkdir(exist_ok=True)
        ARQUIVO_REVISAO.write_text(json.dumps({"texto": texto, "sugerido": destino or "", "estado": "aberto",
                                               "nome": self.nome}, ensure_ascii=False), encoding="utf-8")
        self._revisao_ativa = True
        self._revisao_sessao += 1
        sistema.abrir_revisao_ditado()
        threading.Thread(target=self._vigiar_revisao, args=(self._revisao_sessao,), daemon=True).start()

    def _ler_revisao(self) -> dict:
        import json

        try:
            return json.loads(ARQUIVO_REVISAO.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _texto_revisado(self) -> str:
        """O texto como ficou na janela (voce pode ter corrigido), ou o ditado original."""
        if self._revisao_ativa:
            return self._ler_revisao().get("texto") or self._texto_ditado
        return self._texto_ditado

    def _fechar_revisao(self) -> None:
        if not self._revisao_ativa:
            return
        self._revisao_ativa = False
        dados = self._ler_revisao()
        if dados:
            dados["estado"] = "fechar"
            import json
            ARQUIVO_REVISAO.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    def _vigiar_revisao(self, sessao: int) -> None:
        """Se voce clicar num botao da janela, o Mestre envia (e esquece a pergunta falada)."""
        while self._revisao_ativa and self._revisao_sessao == sessao:
            time.sleep(0.4)
            dados = self._ler_revisao()
            situacao = dados.get("estado")
            if situacao not in ("escolhido", "cancelado", "fechado"):
                continue
            self._revisao_ativa = False
            if situacao == "fechado":
                return   # fechou no X: a pergunta falada continua valendo
            if self._pendente == self._responder_destino:
                self._pendente = None
            if situacao == "cancelado":
                self.falar("cancelado")
            else:
                self._proteger(self._entregar_ditado, dados.get("texto", ""), dados.get("destino", "copiar"))
            return

    # --- destinos -----------------------------------------------------------------------
    def _enviar_ao_projeto(self, texto: str) -> None:
        """Salva no MELHORIAS.md e cola na conversa do Claude Code do projeto (link no painel)."""
        self._salvar_melhoria(texto, falar=False)
        c = self.cfg.get("projeto_mestre") or {}
        link = str(c.get("link") or LINK_PROJETO_PADRAO).strip()
        if not link:
            self.voz.falar("Salvei na lista de melhorias. Coloca o link da conversa do Claude Code no painel "
                           "que da próxima vez eu mando direto.")
            return
        modo = str(c.get("modo") or "app")
        enviar = c.get("enviar_automaticamente", True)
        altura = int(c.get("altura_caixa", 90))
        mensagem = CABECALHO_PROJETO + texto
        self.voz.falar(random.choice([f"Levando pro projeto {self.nome}.", "Mandando pro Claude.",
                                      "Deixa comigo, já mando pro projeto."]))
        if modo == "terminal":
            sistema.enviar_para_claude_terminal(mensagem)
            self.voz.falar("Abri o Claude Code no terminal com o seu pedido. Ficou salvo também na lista de melhorias.")
            return
        if modo == "app":
            if sistema.enviar_para_app_claude(mensagem, enviar=enviar, altura_caixa=altura, posicao=c.get("posicao_caixa")):
                self.voz.falar("Mandei pro app do Claude. Se não aparecer lá, é só dar Control V: o texto está copiado.")
                return
            self.voz.falar("Não achei o app do Claude, então vou pelo navegador.")
        sistema.abrir_site(link)
        time.sleep(float(c.get("segundos_para_carregar", 8)))
        sistema.clicar_e_colar_na_janela_ativa(mensagem, enviar=enviar, altura_caixa=altura)
        self.voz.falar("Enviado! Se não aparecer, é só dar Control V: o texto está copiado. "
                       "Ficou salvo também na lista de melhorias.")

    def _enviar_chat_novo(self, texto: str) -> None:
        """Abre uma conversa nova no claude.ai ja com o texto (e envia)."""
        sistema.copiar(texto)
        self.voz.falar("Abrindo um chat novo no Claude.")
        if len(texto) < 1800:
            sistema.abrir_site("https://claude.ai/new?q=" + quote(texto))
            time.sleep(float((self.cfg.get("projeto_mestre") or {}).get("segundos_para_carregar", 8)))
            if (self.cfg.get("projeto_mestre") or {}).get("enviar_automaticamente", True):
                sistema.apertar_enter()
        else:
            sistema.abrir_site("https://claude.ai/new")
            time.sleep(float((self.cfg.get("projeto_mestre") or {}).get("segundos_para_carregar", 8)))
            sistema.clicar_e_colar_na_janela_ativa(texto)
        self.voz.falar("Pronto. Se o texto não aparecer, é só dar Control V.")

    def _enviar_ao_agente(self, texto: str) -> None:
        c = self._cfg_ipm()
        if c.get("modo", "site") == "cerebro":
            self._conversar(texto, perfil="agente_ipm")
            return
        sistema.abrir_site(c.get("link_projeto", "https://claude.ai/projects"))
        self.voz.falar(random.choice(["Mandando pro agente IPM.", "Levando isso pro agente IPM.",
                                      "Deixa comigo, já mando pro agente."]))
        time.sleep(float(c.get("segundos_para_carregar", 7)))
        sistema.colar_e_enviar(texto, enviar=c.get("enviar_automaticamente", True))
        self.voz.falar("Enviado! Quando a resposta chegar, clica em copiar e fala: {palavra}, lê pra mim.")

    # =================================================================
    #  Area de transferencia (o que voce copiou com Ctrl+C)
    # =================================================================
    def _cmd_area_transferencia(self, t: str) -> bool:
        copiou = re.search(r"\b(copiei|copiado|area de transferencia|ta copiado|esta copiado)\b", t)
        # (o "pra mim" de "le pra mim" ja foi tirado pelo vocabulario)
        ler = re.fullmatch(r"(le|leia|ler)( isso| a resposta| o texto| ai)?", t)
        if not copiou and not ler:
            return False
        texto = sistema.ler_area_transferencia()
        if not texto.strip():
            self.voz.falar("A área de transferência está vazia. Copia o texto com Ctrl C primeiro.")
            return True
        if contem(t, "agente ipm"):
            # "manda o que eu copiei pro agente IPM e pergunta como resolver" -> "pergunta como resolver"
            instrucao = re.sub(r"^(e|,)\s+", "", self._texto_depois_de("agente ipm"), flags=re.I).strip()
            self._enviar_ao_agente(f"{instrucao}\n\n{texto}" if len(instrucao) > 3 else texto)
            return True
        self._responder(texto, "Texto copiado")
        return True

    # =================================================================
    #  YouTube
    # =================================================================
    #  Historico: voltar em respostas antigas
    # =================================================================
    def _cmd_descanso(self, t: str) -> bool:
        """ "pode descansar": fica quieto (ouve so "bora voltar a trabalhar")."""
        puro = self._pedido_puro()
        if not re.search(r"^(pode |vai |agora |ja pode )?(descansar|descansa|descanse|dormir|dorme|durma|relaxar um pouco)"
                         r"( um pouco| agora| ai| por enquanto)?$|\bmodo descanso\b|\b(da|de) um tempo\b|"
                         r"\bfica (quieto|quietinho|em silencio|de boa)\b|\b(stand ?by|standby|modo espera)\b", puro):
            return False
        self._descansando = True
        estado.atualizar(descanso=True)
        self.voz.falar(self.preencher(random.choice(["Beleza {apelido}. Vou descansar. Pra voltar fala: bora voltar a trabalhar.",
                                                     "Tô descansando {apelido}. Quando quiser fala: bora voltar a trabalhar."])))
        return True

    def _cmd_conversinha(self, t: str) -> bool:
        """Cumprimento ("e aí", "tá por aí?") e despedida ("tchau"): resposta curta, sem IA."""
        puro = self._pedido_puro()
        if re.fullmatch(r"((e ai|oi|ola|fala|opa|salve|beleza|tudo bem|tudo certo|ta ai|ta por ai|ta me ouvindo|"
                        r"na escuta|presente|cade voce|voce ta ai|voce esta ai|ta aqui|ta on)\s*)+"
                        r"( (meu )?(parceiro|mano|cara|amigo|brother))?", puro):
            self.falar("chamado")
            self._acabou_de_chamar = True
            return True
        if re.fullmatch(r"((tchau|bye|falou|flw|ate mais|ate logo|ate depois|ate amanha|fui|valeu tchau)\s*)+", puro):
            self.voz.falar(self.preencher(random.choice(["Até mais {apelido}.", "Falou {apelido}!", "Tchau {apelido}. Tô por aqui."])))
            return True
        return False

    def _cmd_exportar(self, t: str) -> bool:
        """ "exporta o histórico": arquivo para o Claude analisar o que deu errado (app/exportar.py)."""
        puro = self._pedido_puro()
        if not re.search(r"\b(exporta|exportar|exporte|gera|gerar|salva|manda|mandar|passa)\b.*\b(historico|"
                         r"relatorio (dos|de) testes?|frases? (dos|de) testes?)\b", puro):
            return False
        from . import exportar
        periodo = ("hoje" if re.search(r"\bhoje\b", puro) else "tudo" if re.search(r"\b(tudo|todo|completo|inteiro)\b", puro)
                   else "30 dias" if re.search(r"\b(mes|30 dias)\b", puro) else "7 dias")
        arquivo = exportar.gerar(self.cfg, periodo)
        sistema.mostrar_na_pasta(arquivo)
        self.voz.falar(f"Histórico de {periodo} exportado. A pasta abriu com o arquivo marcado: é só arrastar pro Claude.")
        return True

    def _cmd_historico(self, t: str) -> bool:
        puro = self._pedido_puro()
        alvo = t + " | " + puro
        sobre = re.search(r"o que (voce|vc) (me )?(respondeu|disse|falou) (sobre|de|do|da) (.+)", puro)
        if sobre:
            self._tipo_registro = "historico"
            item = memoria.procurar(sobre.group(5))
            if item:
                self.voz.falar(f"Em {item['data']} você perguntou: {item['pedido']}. Eu respondi:")
                self._responder(item["resposta"], item["pedido"])
            else:
                self.voz.falar("Não achei nenhuma resposta sobre isso no histórico.")
            return True
        if re.search(r"\b(le|leia|fala|quais foram) (as )?(minhas )?(ultimas|ultimas tres) respostas\b", alvo):
            self._tipo_registro = "historico"
            ultimas = memoria.respostas(3)
            if not ultimas:
                self.voz.falar("O histórico ainda está vazio.")
                return True
            partes = [f"{i}: {limpar_para_falar(x['resposta'])[:140]}" for i, x in enumerate(reversed(ultimas), 1)]
            self.voz.falar("As últimas respostas. " + ". ".join(partes) + ". O histórico completo fica na Central.")
            return True
        indice = None
        if re.search(r"\b(penultima resposta|resposta de antes da ultima)\b", alvo):
            indice = -2
        elif re.search(r"\b(repete|repetir|fala de novo|diz de novo)\b.*\b(resposta|isso|o que (voce|vc) (disse|falou))\b"
                       r"|\b(resposta anterior|ultima resposta)\b", alvo) or any(
                re.fullmatch(r"(repete|repete ai|repete por favor|repita|fala de novo|diz de novo|fala denovo)", x)
                for x in (t, puro)):
            indice = -1
        if indice is None:
            return False
        self._tipo_registro = "historico"
        itens = memoria.respostas(5)
        if len(itens) < -indice:
            self.voz.falar("Não tenho essa resposta guardada.")
            return True
        self._responder(itens[indice]["resposta"], itens[indice]["pedido"])
        return True

    # =================================================================
    #  Memoria: "lembra que ..." (a IA usa nas respostas)
    # =================================================================
    def _cmd_memoria(self, t: str) -> bool:
        puro = self._pedido_puro()
        if re.search(r"\b(em \d+|daqui a|daqui|amanha as|hoje as)\b", puro):
            return False   # "me lembra que ... em 10 minutos" e lembrete
        if re.match(r"^(me )?(lembra|lembre|lembre se|guarda|grava|memoriza) (que|disso:?) ", puro):
            partes = re.split(r"(?i)\b(?:lembra|lembre(?:-se)?|guarda|grava|memoriza)\s+(?:que|disso:?)\s+",
                              self._frase_original, maxsplit=1)
            fato = (partes[1] if len(partes) > 1 else "").strip(" .,!")
            if len(fato) < 3:
                return False
            memoria.lembrar(fato[0].upper() + fato[1:])
            self.voz.falar(random.choice(["Guardado na memória.", "Pode deixar, vou lembrar.", "Anotado. Não esqueço."]))
            return True
        if re.search(r"o que (voce|vc) (sabe|lembra) (de|sobre) mim|o que (voce|vc) lembra|minha memoria", puro):
            fatos = memoria.fatos()
            self.voz.falar("Eu lembro que: " + ". ".join(fatos[-8:]) + "." if fatos else
                           "Ainda não guardei nada. Fala: lembra que, e o que você quer.")
            return True
        esquece = re.match(r"^esquece (que|o que eu disse sobre|sobre) (.+)", puro)
        if esquece:
            apagados = memoria.esquecer(esquece.group(2))
            self.voz.falar(f"Esqueci: {apagados[0]}." if len(apagados) == 1 else
                           f"Apaguei {len(apagados)} lembranças." if apagados else "Não achei isso na memória.")
            return True
        return False

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
    #  Projetos guiados: "quero começar um novo projeto"
    # =================================================================
    def _cmd_projeto(self, t: str) -> bool:
        base = projetos.pasta_base(self.cfg)
        puro = self._pedido_puro()
        if re.search(r"\b(novo projeto|comecar (um )?projeto|criar (um )?projeto|iniciar (um )?projeto|"
                     r"projeto novo|cria (um )?projeto|montar (um )?projeto)\b", t + " | " + puro):
            self._proj = {}
            self.perguntar("Bora! Que tipo de projeto? Código, trabalho, vida pessoal, estudo ou outro?",
                           self._proj_tipo, espera=25)
            return True
        if re.search(r"\b(quais sao|lista|le) (os )?(meus )?projetos\b", t):
            lista = projetos.listar(base)
            self.voz.falar("Seus projetos: " + ", ".join(p.name for p in lista[:8]) + "." if lista else
                           "Você ainda não tem projetos. Fala: quero começar um novo projeto.")
            return True
        abre = re.match(r"^(abre|abrir|mostra) (o |a )?(pasta do )?projeto (.+)", t)
        falta = re.search(r"o que falta (no|do|pro) projeto (.+)", t)
        anota = re.match(r"^(anota|adiciona|coloca|escreve) no projeto (.+)", t)
        if not (abre or falta or anota):
            return False
        trecho = (abre or falta or anota).group((abre and 4) or 2)
        pasta = self._achar_projeto(base, trecho)
        if not pasta:
            self.voz.falar("Não achei esse projeto. Fala: quais são os meus projetos.")
            return True
        if abre:
            sistema.abrir_arquivo(pasta)
            self.voz.falar(f"Abrindo o projeto {pasta.name}.")
        elif falta:
            lista = projetos.pendentes(pasta)
            self.voz.falar(f"No {pasta.name} falta: " + ". ".join(lista[:3]) + "." if lista else
                           f"O {pasta.name} não tem passos pendentes.")
        else:
            original = re.split(re.escape(pasta.name), self._frase_original, maxsplit=1, flags=re.I)
            texto = (original[1] if len(original) > 1 else trecho).strip(" :,.-")
            if texto.lower().startswith("que "):
                texto = texto[4:]
            projetos.anotar(pasta, texto)
            self.voz.falar(f"Anotado no projeto {pasta.name}.")
        return True

    def _achar_projeto(self, base, trecho: str):
        """O projeto cujo nome aparece no comeco do trecho falado."""
        for pasta in projetos.listar(base):
            if normalizar(trecho).startswith(normalizar(pasta.name)):
                return pasta
        return projetos.achar(base, trecho)

    def _proj_tipo(self, resposta: str) -> None:
        self._proj["tipo"] = projetos.tipo_falado(resposta)
        self.perguntar("Qual o nome do projeto?", self._proj_nome, espera=25)

    def _proj_nome(self, resposta: str) -> None:
        self._proj["nome"] = (self._frase_original or resposta).strip(" .!?")
        self.perguntar("Em uma frase: qual o objetivo?", self._proj_objetivo, espera=40)

    def _proj_objetivo(self, resposta: str) -> None:
        self._proj["objetivo"] = (self._frase_original or resposta).strip()
        self.perguntar("Tem prazo ou alguma coisa já pronta? Se não tiver, fala: nada.", self._proj_extra, espera=40)

    def _proj_extra(self, resposta: str) -> None:
        extra = (self._frase_original or resposta).strip()
        self._proj["extra"] = "" if re.fullmatch(r"(nada|nao|nenhum|nenhuma|nao tem)", normalizar(extra)) else extra
        d = self._proj
        pasta = projetos.criar(projetos.pasta_base(self.cfg), d)
        self._proj["pasta"] = pasta
        self.voz.falar(f"Criei a pasta do projeto {pasta.name}.")
        if not self.cerebro.ligado:
            self.perguntar("Sem a IA ligada eu não consigo sugerir caminhos. Quer que eu mande o plano pro Claude?",
                           lambda r: self._proj_quer_claude(r), espera=20)
            return
        pedido = (f"Tipo de projeto: {d['tipo']}. Nome: {d['nome']}. Objetivo: {d['objetivo']}. "
                  f"Prazo ou o que já existe: {d.get('extra') or 'nada'}.")
        self._pensar(f"projeto {pasta.name}", lambda: self.cerebro.propor_opcoes(pedido + self._proj_pesquisar(pasta)),
                     lambda opcoes: self._proj_apresentar(pasta, opcoes or []))

    def _proj_pesquisar(self, pasta) -> str:
        """Pesquisa o objetivo na internet (roda junto com a IA, fora da escuta), grava no PLANO.md e
        devolve o resumo para a IA levar em conta nas propostas."""
        if sistema.SIMULADO or not (self.cfg.get("projetos") or {}).get("pesquisar_internet", True):
            return ""
        resultados = informacoes.pesquisar_web(self._proj.get("objetivo") or self._proj.get("nome", ""))
        projetos.gravar_pesquisa(pasta, resultados)
        if not resultados:
            return ""
        return " O que achei na internet: " + " | ".join(f"{r['titulo']}: {r['resumo']}" for r in resultados)

    def _proj_quer_claude(self, resposta: str) -> None:
        if re.search(r"\b(sim|quero|manda|pode|isso|bora)\b", normalizar(resposta)):
            self._proj_perguntar_destino()
        else:
            self.voz.falar("Beleza. O plano ficou na pasta do projeto.")

    def _proj_apresentar(self, pasta, opcoes: list) -> None:
        self._proj["pasta"], self._proj["opcoes"] = pasta, opcoes
        if not opcoes:
            self.perguntar("A IA não trouxe opções. Quer que eu mande o plano pro Claude?",
                           lambda r: self._proj_quer_claude(r), espera=20)
            return
        projetos.gravar_opcoes(pasta, opcoes)
        numeros = ["Um", "Dois", "Três"]
        falas = [f"{numeros[i]}: {o['titulo']}. {o.get('resumo', '')}" for i, o in enumerate(opcoes)]
        self.perguntar(f"Pensei em {len(opcoes)} caminhos. " + " ".join(falas) +
                       " Ou quatro: nenhum desses, mando pro Claude. Qual você quer?", self._proj_escolha, espera=60)

    def _proj_escolha(self, resposta: str) -> None:
        n = normalizar(resposta)
        opcoes = self._proj.get("opcoes") or []
        if re.search(r"\b(quatro|quarta|quarto|4|nenhum|nenhuma|nao gostei|claude|manda|outra)\b", n):
            self._proj_perguntar_destino()
            return
        indice = next((i for i, padrao in enumerate([r"\b(um|uma|primeir[oa]|1)\b", r"\b(dois|duas|segund[oa]|2)\b",
                                                      r"\b(tres|terceir[oa]|3)\b"])
                       if re.search(padrao, n) and i < len(opcoes)), None)
        if indice is None:
            indice = next((i for i, o in enumerate(opcoes) if normalizar(o["titulo"]) and contem(n, normalizar(o["titulo"]).split()[0])), None)
        if indice is None:
            self.perguntar("Não peguei. Um, dois, três ou quatro pro Claude?", self._proj_escolha, espera=40)
            return
        opcao, pasta = opcoes[indice], self._proj["pasta"]
        projetos.escolher(pasta, opcao)
        passos = opcao.get("passos") or []
        self.voz.falar(f"Fechado: {opcao['titulo']}. " + (f"Primeiro passo: {passos[0]}. " if passos else "") +
                       "Deixei tudo no plano, na pasta do projeto.")
        sistema.abrir_arquivo(pasta / "PLANO.md")
        if (self.cfg.get("projetos") or {}).get("abrir_pesquisas", True):
            for busca in (f"como começar {opcao['titulo']}", f"projetos parecidos {self._proj.get('objetivo', '')}"):
                sistema.abrir_site("https://www.google.com/search?q=" + quote_plus(busca))

    def _proj_perguntar_destino(self) -> None:
        self.perguntar("Pra onde eu mando? Claude Code, agente IPM ou chat novo?", self._proj_destino, espera=40)

    def _proj_destino(self, resposta: str) -> None:
        n = normalizar(resposta)
        pasta = self._proj.get("pasta")
        if pasta is None:
            return
        texto = ("Quero começar um projeto novo. Este é o plano até agora (as opções sugeridas não me agradaram; "
                 "me ajude a pensar em outros caminhos e nos primeiros passos):\n\n" + projetos.plano_em_texto(pasta))
        if re.search(r"\b(code|codigo|programar|claude code)\b", n):
            (pasta / "PEDIDO_PARA_O_CLAUDE.md").write_text(texto, encoding="utf-8")
            sistema.abrir_terminal_com('claude "Leia o PLANO.md e o PEDIDO_PARA_O_CLAUDE.md desta pasta e me ajude '
                                       'a comecar este projeto. Faca perguntas antes de criar arquivos."',
                                       pasta, f"Projeto {pasta.name}")
            self.voz.falar("Abri o Claude Code na pasta do projeto.")
        elif re.search(r"\b(agente|ipm)\b", n):
            self._enviar_ao_agente(texto)
        elif re.search(r"\b(chat|claude|novo|conversa)\b", n):
            self._enviar_chat_novo(texto)
        else:
            self.perguntar("Não peguei. Claude Code, agente IPM ou chat novo?", self._proj_destino, espera=40)

    # =================================================================
    #  YouTube "vendo" a pagina (janela do navegador controlada pelo Mestre)
    # =================================================================
    def _yt(self):
        """O YouTube controlado (ou None, se desligado no painel ou sem a biblioteca)."""
        if not (self.cfg.get("youtube") or {}).get("navegador_mestre", True):
            return None
        if getattr(self, "_youtube", None) is None:
            from .navegador import (Navegador, YouTube, YouTubeNoBraveComExtensao, YouTubeNoNavegadorNormal,
                                    caminho_do_brave)
            c = self.cfg.get("youtube") or {}
            canal = str(c.get("navegador", "brave"))
            modo = str(c.get("modo") or "extensao")
            if modo == "extensao":   # o SEU Brave + a extensao do Mestre (recomendado)
                if getattr(self, "ponte", None) is None:
                    from .ponte import Ponte
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
        yt = self._yt()
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
            from .ponte import desatualizada
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

    def _cmd_streaming(self, t: str) -> bool:
        puro = self._pedido_puro()
        qual = next((nome for nome, (_, _, jeitos) in self.STREAMINGS.items()
                     if re.search(rf"\b(na|no|pela|pelo|da|do|em) ({jeitos})\b", puro)), None)
        tem_tipo = re.search(rf"\b{self.TIPOS_DE_VIDEO}\b", puro)
        if not re.search(rf"\b{self.VERBOS_ASSISTIR}\b", t + " " + puro) or not (qual or tem_tipo):
            return False
        titulo = puro
        if qual:
            titulo = re.sub(rf"\b(na|no|pela|pelo|da|do|em) ({self.STREAMINGS[qual][2]})\b( que (esta|ta) )?"
                            r"( aberta| aberto)?( (na|no) (janela|monitor|tela) \w+)?", " ", titulo)
        titulo = re.sub(rf"\b(quero |eu quero |pode )?{self.VERBOS_ASSISTIR}\b|\b{self.TIPOS_DE_VIDEO}\b|"
                        r"\b(de onde parei|do comeco|agora|pra mim|por favor|ai|tocar|assistindo)\b", " ", titulo)
        palavras = titulo.split()
        while palavras and palavras[0] in ("a", "o", "as", "os", "de", "do", "da", "e", "que"):   # so nas pontas
            palavras.pop(0)
        while palavras and palavras[-1] in ("a", "o", "as", "os", "de", "do", "da", "e", "que"):
            palavras.pop()
        titulo = " ".join(palavras)
        if not titulo:
            return False
        titulo = self._original(titulo)
        if not qual:
            self.perguntar(f"Em qual? Netflix, Disney, Prime, HBO ou Globoplay?",
                           lambda r, tt=titulo: self._responder_streaming(r, tt), espera=15)
            return True
        self._tocar_no_streaming(qual, titulo)
        return True

    def _responder_streaming(self, resposta: str, titulo: str) -> None:
        n = normalizar(resposta)
        qual = next((nome for nome, (_, _, jeitos) in self.STREAMINGS.items() if re.search(rf"\b({jeitos})\b", n)), None)
        if qual:
            self._tocar_no_streaming(qual, titulo)
        else:
            self.voz.falar("Não peguei o streaming. Fala de novo: toca a série na Disney, por exemplo.")

    def _tocar_no_streaming(self, qual: str, titulo: str) -> None:
        dominio, busca, _ = self.STREAMINGS[qual]
        url = busca.format(quote(titulo)) if "{}" in busca else busca
        ext = self._extensao()
        self.voz.falar(f"Procurando {titulo} na {qual}.")
        if not ext:
            sistema.abrir_site(url)
            if "{}" not in busca:
                self.voz.falar("Sem a extensão do Brave eu não consigo digitar na busca. Digite o nome lá.")
            return
        aba = None
        if sistema.MONITOR_ALVO:
            sistema.abrir_site(url)   # janela nova no monitor pedido
        else:
            try:
                aba = (ext.pedir("ir", {"url": url, "dominio": dominio}, espera=6) or {}).get("id")
            except Exception as erro:
                log.info("Extensao nao abriu a busca (%s)", erro)
                sistema.abrir_site(url)
        threading.Thread(target=self._seguir_no_streaming, args=(ext, aba, dominio, titulo, "{}" in busca),
                         daemon=True).start()

    def _seguir_no_streaming(self, ext, aba, dominio: str, titulo: str, busca_no_endereco: bool,
                             pausa: float = 1.5) -> None:
        """Depois de abrir o site: 1) digita o nome na busca  2) clica no título  3) "continuar assistindo"."""
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
        for _ in range(6):
            time.sleep(pausa)
            r = pedir("clicar", textos=["continuar assistindo", "continuar", "retomar", "assistir", "assista",
                                         "reproduzir", "play", "comecar", "resume", "watch"])
            if r not in ("nao_achei", "sem_aba", "erro"):
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
            except Exception:
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

    def _cmd_janela(self, t: str) -> bool:
        """Janelas e navegador: age na janela que esta na frente."""
        puro = self._pedido_puro()
        fim = r"( ai| por favor)?"
        tabela = [
            (r"(fecha|feche|fechar) (essa|esta|a) janela", lambda: sistema.atalho("alt", "f4")),
            (r"(minimiza|minimizar) tudo|mostra a area de trabalho|area de trabalho", lambda: sistema.atalho("win", "d")),
            (r"(minimiza|minimizar)( essa| a| esta)?( janela)?", lambda: sistema.janela_ativa("minimizar")),
            (r"(maximiza|maximizar)( essa| a| esta)?( janela)?", lambda: sistema.janela_ativa("maximizar")),
            (r"(troca|trocar|muda|mudar) de janela|proxima janela|outra janela", lambda: sistema.atalho("alt", "tab")),
            (r"(abre )?(uma )?nova aba|abre uma aba", lambda: sistema.atalho("ctrl", "t")),
            (r"(fecha|feche|fechar) (essa |esta |a )?aba", lambda: sistema.atalho("ctrl", "w")),
            (r"(reabre|reabrir) a aba( que eu fechei)?|volta a aba que eu fechei",
             lambda: sistema.atalho("ctrl", "shift", "t")),
            (r"((vai|passa|muda|troca) (pra|para|de) )?(a )?(proxima|outra) aba|(passa|muda|troca) (de|a) aba|aba da direita",
             lambda: self._no_navegador("trocar_aba", 1, "ctrl", "tab")),
            (r"((volta|vai) (pra|para) )?(a )?aba anterior|volta (uma|a) aba|aba da esquerda",
             lambda: self._no_navegador("trocar_aba", -1, "ctrl", "shift", "tab")),
            (r"((volta|voltar|vai|ir) (pra|para|na|a) )?(a )?pagina anterior|(volta|voltar|retorna) (a |uma |pra |para |na )?pagina"
             r"( anterior)?|volta (a |uma )?pagina (pra tras|atras)",
             lambda: self._no_navegador("voltar", None, "alt", "esquerda")),
            (r"((vai|ir|passa|avanca) (pra|para) )?(a )?proxima pagina|(avanca|avancar|adianta) (a |uma )?pagina",
             lambda: self._no_navegador("avancar", None, "alt", "direita")),
            (r"(atualiza|atualizar|recarrega|recarregar)( a pagina)?", lambda: sistema.atalho("f5")),
            (r"(rola|rolar|desce|descer)( pra| para)? (baixo|a pagina)|rola|desce a tela", lambda: sistema.atalho("pgdn")),
            (r"(rola|rolar|sobe|subir)( pra| para)? (cima|a pagina)|sobe a tela", lambda: sistema.atalho("pgup")),
            (r"(vai|volta) (pro|para o) (topo|comeco)( da pagina)?", lambda: sistema.atalho("home")),
            (r"(vai|desce) (pro|para o|ate o) (final|fim)( da pagina)?", lambda: sistema.atalho("end")),
            (r"(aumenta|mais) (o )?zoom", lambda: sistema.atalho("ctrl", "mais")),
            (r"(diminui|menos|tira o) (o )?zoom", lambda: sistema.atalho("ctrl", "menos")),
            (r"zoom normal|volta o zoom", lambda: sistema.atalho("ctrl", "0")),
        ]
        mover = r"(joga|jogar|move|mover|manda|leva|levar|passa|passar|abre) (essa|esta|a) janela"
        if re.fullmatch(mover, t) or re.match(mover + r"\b", puro):
            if not sistema.MONITOR_ALVO:
                self.voz.falar("Pra qual monitor? Fala por exemplo: joga essa janela pro monitor dois.")
            else:
                sistema.mover_janela_para_monitor(sistema.janela_da_frente(), sistema.MONITOR_ALVO)
            return True
        for padrao, acao in tabela:
            if re.fullmatch(padrao + fim, t) or re.fullmatch(padrao + fim, puro):
                acao()
                return True
        if re.fullmatch(r"(tira|tirar|faz|fazer) (um )?print( da tela)?|captura (a )?tela" + fim, puro):
            arquivo = sistema.tirar_print()
            self.voz.falar("Print salvo na sua pasta de Imagens.")
            log.info("Print: %s", arquivo)
            return True
        return False

    def _no_navegador(self, acao: str, arg, *teclas: str) -> None:
        """Voltar/avançar página e trocar de aba: com o navegador na frente, pelas teclas; se você está
        em outro programa (ex.: o Brave no outro monitor), pela extensão na aba que você usou por último."""
        ext = self._extensao()
        if ext and sistema.programa_da_frente() not in sistema.NAVEGADORES:
            try:
                ext.pedir(acao, arg, espera=4)
                return
            except Exception as erro:
                log.info("Extensao nao fez %s: %s", acao, erro)
        sistema.atalho(*teclas)

    # =================================================================
    #  Janelas e abas pelo nome: "joga a Netflix pro monitor 3",
    #  "separa a Netflix pro monitor 2 e deixa o YouTube no principal"
    # =================================================================
    VERBOS_MOVER = (r"(joga|jogar|jogue|move|mover|mova|manda|mandar|mande|leva|levar|leve|passa|passar|passe|"
                    r"coloca|colocar|coloque|bota|botar|poe|por|ponha|separa|separar|separe|tira|tirar|tire|"
                    r"deixa|deixar|deixe|arrasta|arrastar|arraste)")
    ESTA_JANELA = {"", "janela", "essa janela", "esta janela", "ela", "isso", "essa", "esta", "aqui", "ai"}

    def _extensao(self):
        """A ponte com a extensão do Brave, se ela estiver conversando com o Mestre (senão None)."""
        ponte = getattr(self, "ponte", None)
        try:
            return ponte if ponte is not None and ponte.conectada() else None
        except Exception:
            return None

    def _monitor_falado(self, falado: str, com_a_palavra_monitor: bool) -> int | None:
        """ "2", "secundario", "aoc", "de 144"... Sem a palavra "monitor", só nomes que não são números
        (senão "coloca o Spotify no 50" viraria monitor)."""
        falado = re.sub(r"^(meu|minha|o|a)\s+", "", falado.strip())
        falado = re.sub(r"^(monitor|tela|janela)\s+", "", falado)
        falado = re.sub(r"^(numero|n)\s+", "", falado)
        falado = re.sub(r"\s+(por favor|ai|agora)$", "", falado)
        numeros = {"um", "dois", "tres", "quatro", "primeiro", "segundo", "terceiro", "quarto"}
        for numero, nomes in self._nomes_monitores().items():
            for n in nomes:
                if not n or falado not in (n, "da " + n, "do " + n):   # exato: "... no principal e deixa ..." nao vale
                    continue
                if not com_a_palavra_monitor and (n.isdigit() or n in numeros):
                    continue
                return numero
        return None

    def _clausula_de_mover(self, parte: str) -> dict | None:
        """Uma ordem: {"verbo", "alvo", "monitor", "separar"} ou None."""
        artigo = r"(?:(?:a|o|as|os|essa|esse|esta|este|aquela|aquele|minha|meu)\s+)?"
        tipo = r"(?:(?:aba|janela|site|programa|app|aplicativo|guia)\s+)?"
        de = r"(?:(?:do|da|de|com o|com a)\s+)?"
        prep = r"\s+(?:no|na|pro|pra|para o|para a|para|ao|pro lado do|em)\s+"
        mon = r"(monitor\s+|tela\s+|janela\s+)?(.+)"
        m = re.match(rf"^{self.VERBOS_MOVER}\s+{artigo}{tipo}{de}(.*?){prep}{mon}$", parte)
        if m:
            verbo, alvo, palavra_mon, falado = m.groups()
        else:   # "o YouTube deixa no principal", "a Netflix joga pro monitor 2"
            m = re.match(rf"^{artigo}{tipo}{de}(.+?)\s+{self.VERBOS_MOVER}{prep}{mon}$", parte)
            if not m:
                return None
            alvo, verbo, palavra_mon, falado = m.groups()
        numero = self._monitor_falado(falado, bool(palavra_mon))
        if not numero:
            return None
        separar = bool(re.match(r"(separa|tira|destaca)", verbo))
        sozinha = r"\s+(desse|deste|do|da|dessa|desta) (navegador|janela|brave|chrome)$|\s+sozinh[ao]$"
        if re.search(sozinha, alvo) or re.match(r"(so|somente|apenas) ", alvo):
            separar = True
            alvo = re.sub(sozinha, "", re.sub(r"^(so|somente|apenas) (a |o )?", "", alvo))
        return {"verbo": verbo, "alvo": alvo.strip(), "monitor": numero, "separar": separar,
                "deixar": verbo.startswith("deix")}

    def _ordens_de_mover(self, puro: str) -> list[dict] | None:
        puro = re.sub(r"^(quero que (voce|vc) |quero |por favor |da pra |consegue |pode |tem como )+", "", puro)
        uma = self._clausula_de_mover(puro)
        if uma:
            return [uma]
        # duas ordens juntas: "... pro monitor 2 e (deixa) o YouTube no principal"
        for achado in re.finditer(r"\s+(?:e|mas|,)\s+", puro):
            a, b = puro[:achado.start()], puro[achado.end():]
            primeira = self._clausula_de_mover(a)
            if primeira:
                segunda = self._clausula_de_mover(b)
                if segunda:
                    return [primeira, segunda]
        return None

    def _cmd_juntar(self, t: str) -> bool:
        """ "junta o YouTube com a Disney": a aba do YouTube vai para a janela da Disney (qualquer monitor)."""
        puro = re.sub(r"^(quero que (voce|vc) |quero |por favor |pode )+", "", self._pedido_puro())
        verbo = r"(junta|juntar|junte|une|unir|una|agrupa|agrupar|agrupe|traz|trazer|traga|coloca|coloque|poe|bota|leva|joga|manda|move|passa)"
        art = r"(?:(?:a|o|as|os)\s+)?(?:(?:janela|aba|guia)\s+)?(?:(?:do|da|de)\s+)?"
        todas = re.match(rf"^{verbo} (todas as |as |tudo |todas )?(janelas|abas|guias)( (do|da) (navegador|brave))?"
                         rf"( (em uma|numa|numa so|em uma so|na mesma) janela( so)?)?( (no|na|pro|pra) (.+))?$", puro)
        dupla = re.match(rf"^{verbo} {art}(.+?) (com|junto com|junto da|junto do|junto de|pra|para|na|dentro da|dentro do|"
                         rf"ao lado da|ao lado do|e) {art}(.+?)$", puro)
        if not (todas or dupla) or (dupla and not todas and not re.search(
                r"\b(junta|juntar|junte|une|unir|una|agrupa|agrupar|agrupe|junto|janela|guia|aba)\b", puro)):
            return False
        if dupla and not todas and (re.search(r"\b(monitor|tela)\b", dupla.group(4))
                                    or self._monitor_falado(dupla.group(4), False)):
            return False   # "manda o Spotify pra janela principal" = mudar de monitor (_cmd_mover)
        ext = self._extensao()
        if not ext:
            self.voz.falar("Pra juntar abas eu preciso da extensão no Brave. Ela não está conectada.")
            return True
        abas = self._abas_abertas()
        if todas:
            destino = next((a for a in abas if a.get("janela_em_uso") and a.get("ativa")), abas[0] if abas else None)
            if not destino:
                return True
            ext.pedir("juntar", {"abas": [a["id"] for a in abas if a["janela"] != destino["janela"]],
                                 "destino": destino["id"]}, espera=6)
            falado = todas.group(12)
            numero = self._monitor_falado(falado, False) if falado else None
            if numero:
                hwnd = sistema.janela_pelo_titulo(destino.get("titulo", ""))
                if hwnd:
                    sistema.mover_janela_para_monitor(hwnd, numero)
            self.voz.falar("Juntei tudo numa janela.")
            return True
        a_nome, b_nome = dupla.group(2), dupla.group(4)
        b_nome = re.sub(r"\s+(no|na) (monitor|tela) .+$", "", b_nome)
        a, b = self._achar_janela_ou_aba(a_nome, abas), self._achar_janela_ou_aba(b_nome, abas)
        if not (a and b and a["tipo"] == "aba" and b["tipo"] == "aba"):
            falta = a_nome if not (a and a["tipo"] == "aba") else b_nome
            self.voz.falar(f"Não achei a aba de {self._original(falta)} no Brave.")
            return True
        if a["aba"]["janela"] == b["aba"]["janela"]:
            self.voz.falar("Elas já estão na mesma janela.")
            return True
        ext.pedir("juntar", {"abas": [a["aba"]["id"]], "destino": b["aba"]["id"]}, espera=6)
        return True

    def _cmd_mover(self, t: str) -> bool:
        ordens = self._ordens_de_mover(self._pedido_puro())
        if not ordens:
            return False
        abas = self._abas_abertas()
        achados = [self._achar_janela_ou_aba(o["alvo"], abas) for o in ordens]
        # duas ordens para abas da MESMA janela: essa janela tem de ser separada
        if len(ordens) == 2 and all(a and a["tipo"] == "aba" for a in achados) and \
                achados[0]["aba"]["janela"] == achados[1]["aba"]["janela"]:
            for o in ordens:
                o["separar"] = o["separar"] or not o["deixar"]
            if all(o["deixar"] for o in ordens):
                ordens[0]["separar"] = True
        falhas = []
        for ordem, achado in zip(ordens, achados):
            if not achado:
                falhas.append(ordem["alvo"])
                continue
            self._mover_achado(achado, ordem)
        if falhas:
            nomes = " e ".join(self._original(f) for f in falhas)
            if len(ordens) == 1 and self._abrir_no_monitor(ordens[0]["alvo"], ordens[0]["monitor"]):
                return True
            self.voz.falar(f"Não achei {nomes} aberto.")
        return True

    def _abas_abertas(self) -> list[dict]:
        ext = self._extensao()
        if not ext:
            return []
        try:
            return ext.pedir("abas", espera=4) or []
        except Exception as erro:
            log.info("Extensao nao listou as abas: %s", erro)
            return []

    # --- qual janela? (o mesmo site aberto em mais de um monitor) -------------------------------------
    def _monitor_da_frase(self, texto: str) -> tuple[str, int | None]:
        """ "abre o segundo video do monitor 2" -> ("abre o segundo video", 2). Sem monitor: (texto, None)."""
        achado = re.search(r"\s*\b(?:do|da|no|na|que (?:esta|ta) (?:no|na))\s+(?:monitor|tela)\s+(.+?)$", texto)
        if not achado:
            return texto, None
        numero = self._monitor_falado(achado.group(1), True)
        return (texto[:achado.start()].strip(), numero) if numero else (texto, None)

    def _monitor_da_aba(self, aba: dict, abas: list[dict]) -> int | None:
        """Em qual monitor esta a janela da aba: pelo titulo da janela do Windows (que mostra a aba da frente)
        ou, se nao der, pela posicao que a extensao manda."""
        frente = next((a for a in abas if a.get("janela") == aba.get("janela") and a.get("ativa")), aba)
        inicio = normalizar(frente.get("titulo", ""))[:30]
        if inicio:
            achados = {j["monitor"] for j in sistema.janelas_abertas()
                       if j["exe"] in sistema.NAVEGADORES and j.get("monitor") and normalizar(j["titulo"]).startswith(inicio)}
            if len(achados) == 1:
                return achados.pop()
        if aba.get("janela_x") is not None and aba.get("janela_largura"):
            return sistema.monitor_do_ponto(int(aba["janela_x"]) + int(aba["janela_largura"]) // 2,
                                            int(aba["janela_y"]) + int(aba.get("janela_altura") or 0) // 2)
        return None

    @staticmethod
    def _abas_na_tela(abas: list[dict], dominio: str = "") -> list[dict]:
        """As abas que voce VE: a da frente de cada janela que nao esta minimizada (so do site, se pedido)."""
        do_site = [a for a in abas if not dominio or _mesmo_site(a.get("url", ""), dominio)]
        return [a for a in do_site if a.get("ativa") and a.get("janela_estado") != "minimized"] or do_site

    def _escolher_aba(self, candidatas: list[dict], abas: list[dict], nome: str, monitor: int | None,
                      continuar, tem=None) -> None:
        """Decide em QUAL aba agir e chama continuar(id da aba). Com mais de uma na tela, nesta ordem:
        a unica que tem o que voce falou (tem), a do monitor que voce disse, a do monitor onde esta o mouse.
        Se ainda assim ficar em duvida: pergunta "No monitor 1 ou no 2?"."""
        def recente(a):
            return a.get("janela_em_uso", False), a.get("ultimo_acesso", 0)
        if not candidatas:
            continuar(None)
            return
        if tem and len(candidatas) > 1:   # tem(aba) = nota (0 = nao tem); fica so com as de nota mais alta
            notas = {a["id"]: float(tem(a) or 0) for a in candidatas}
            melhor = max(notas.values())
            com = [a for a in candidatas if melhor > 0 and notas[a["id"]] == melhor]
            if monitor is None and len(com) <= 1:   # so uma tem (ou nenhuma: quem responde e o comando)
                continuar((com[0] if com else max(candidatas, key=recente))["id"])
                return
            candidatas = com or candidatas
        if len(candidatas) == 1 and monitor is None:
            continuar(candidatas[0]["id"])
            return
        for a in candidatas:
            a["_monitor"] = self._monitor_da_aba(a, abas)
        if monitor is not None:
            ali = [a for a in candidatas if a["_monitor"] == monitor]
            if not ali and not any(a["_monitor"] for a in candidatas) and len(candidatas) == 1:
                ali = candidatas   # (nao deu para saber o monitor de nenhuma: vai na unica)
            if not ali:
                self.voz.falar(f"Não achei {nome} no monitor {monitor}.")
                return
            continuar(max(ali, key=recente)["id"])
            return
        mouse = sistema.monitor_do_mouse()
        ali = [a for a in candidatas if mouse and a["_monitor"] == mouse]
        if len(ali) == 1:
            continuar(ali[0]["id"])
            return
        telas = sorted({a["_monitor"] for a in candidatas if a["_monitor"]})
        if len(telas) >= 2:
            def responder(resposta: str, c=candidatas):
                falado = re.sub(r"^(e |eh )?(o |a )?(do |da |no |na |pro |pra )?(monitor |tela )?(numero )?", "",
                                normalizar(resposta))
                n = self._monitor_falado(falado, True)
                escolhidas = [a for a in c if n and a["_monitor"] == n]
                if escolhidas:
                    continuar(max(escolhidas, key=recente)["id"])
                else:
                    self.voz.falar("Não peguei o monitor. Fala de novo dizendo do monitor 2, por exemplo.")
            self.perguntar(f"Tem {nome} em mais de uma tela. No monitor " + " ou no ".join(map(str, telas)) + "?",
                           responder, espera=12)
            return
        continuar(max(candidatas, key=recente)["id"])

    def _dominio_do_site(self, alvo: str) -> str:
        """ "netflix" -> "netflix.com" (pelo endereco cadastrado em Programas e sites)."""
        sites = self.cfg.get("sites") or {}
        chave = melhor_correspondencia(alvo, sites)
        return _host(str(sites[chave])) if chave else ""

    def _achar_janela_ou_aba(self, alvo: str, abas: list[dict] | None = None) -> dict | None:
        """{"tipo": "frente"|"aba"|"janela", ...} para o nome falado, ou None."""
        alvo = normalizar(alvo)
        if alvo in self.ESTA_JANELA:
            return {"tipo": "frente", "hwnd": sistema.janela_da_frente(), "nome": "essa janela"}
        palavras = [w for w in alvo.split() if len(w) > 1]
        if not palavras:
            return None
        dominio = self._dominio_do_site(alvo) or ("youtube.com" if "youtube" in alvo else "")

        def combina(texto: str) -> bool:
            texto = normalizar(texto)
            return all(re.search(rf"\b{re.escape(w)}", texto) for w in palavras)

        candidatas = [aba for aba in abas or [] if (dominio and _mesmo_site(aba.get("url", ""), dominio))
                      or combina(aba.get("titulo", "")) or combina(_host(aba.get("url", "")).replace(".", " "))]
        if candidatas:   # a que esta na frente da janela, depois a usada por ultimo
            aba = max(candidatas, key=lambda a: (a.get("ativa", False), a.get("ultimo_acesso", 0)))
            return {"tipo": "aba", "aba": aba, "nome": alvo}
        # janelas do Windows (programas; e o navegador sem a extensao, pelo titulo da aba da frente)
        programas = self.cfg.get("programas") or {}
        chave = melhor_correspondencia(alvo, programas)
        exe = Path(str(programas[chave]).strip('"')).name.lower() if chave else ""
        janelas = sistema.janelas_abertas()
        for j in janelas:
            if exe and j["exe"] == exe:
                return {"tipo": "janela", "hwnd": j["hwnd"], "nome": alvo}
        for j in janelas:
            if combina(j["titulo"]) or combina(j["exe"].removesuffix(".exe")):
                return {"tipo": "janela", "hwnd": j["hwnd"], "nome": alvo}
        return None

    def _mover_achado(self, achado: dict, ordem: dict) -> None:
        numero = ordem["monitor"]
        hwnd = achado.get("hwnd")
        if achado["tipo"] == "aba":
            ext = self._extensao()
            aba = achado["aba"]
            separar = ordem["separar"] and aba.get("abas_na_janela", 1) > 1
            try:
                r = ext.pedir("separar" if separar else "focar", aba["id"], espera=5) or {}
            except Exception as erro:
                log.warning("Extensao nao %s a aba: %s", "separou" if separar else "focou", erro)
                r = {}
            hwnd = sistema.janela_pelo_titulo(r.get("titulo") or aba.get("titulo", ""))
        if not hwnd and achado["tipo"] != "frente":
            log.info("Nao achei a janela de %s", achado.get("nome"))
            return
        if ordem["deixar"] and sistema.monitor_da_janela(hwnd) == numero:
            return   # "deixa o YouTube no principal" e ele ja esta la
        sistema.mover_janela_para_monitor(hwnd, numero)

    def _site_ja_aberto(self, nome: str, url: str) -> bool:
        """ "abre a Netflix" com a Netflix já aberta numa aba: usa ela (e manda para o monitor pedido,
        sozinha numa janela) em vez de abrir outra."""
        if not self._extensao():
            return False
        dominio = _host(str(url))
        abas = [a for a in self._abas_abertas() if dominio and _mesmo_site(a.get("url", ""), dominio)]
        if not abas:
            return False
        aba = max(abas, key=lambda a: (a.get("ativa", False), a.get("ultimo_acesso", 0)))
        achado = {"tipo": "aba", "aba": aba, "nome": nome}
        if sistema.MONITOR_ALVO:
            self._mover_achado(achado, {"monitor": sistema.MONITOR_ALVO, "separar": True, "deixar": False})
            self.voz.falar(f"{nome.capitalize()} já estava aberto. Mandei pro monitor {sistema.MONITOR_ALVO}.")
        else:
            try:
                self._extensao().pedir("focar", aba["id"], espera=4)
            except Exception as erro:
                log.info("Extensao nao focou a aba: %s", erro)
                return False
            self.voz.falar(f"{nome.capitalize()} já estava aberto.")
        return True

    def _ja_aberto_vai_pro_monitor(self, nome: str, caminho: str) -> bool:
        exe = Path(str(caminho).strip('"')).name.lower()
        janela = next((j for j in sistema.janelas_abertas() if exe.endswith(".exe") and j["exe"] == exe), None)
        if not janela:
            return False
        sistema.mover_janela_para_monitor(janela["hwnd"], sistema.MONITOR_ALVO)
        return True

    def _abrir_no_monitor(self, alvo: str, numero: int) -> bool:
        """ "joga a Netflix pro monitor 3" com a Netflix fechada: abre ela lá."""
        sites = self.cfg.get("sites") or {}
        programas = self.cfg.get("programas") or {}
        chave_site, chave_prog = melhor_correspondencia(alvo, sites), melhor_correspondencia(alvo, programas)
        if not (chave_site or chave_prog):
            return False
        sistema.MONITOR_ALVO = numero
        self.voz.falar(f"{(chave_prog or chave_site).capitalize()} não estava aberto. Abrindo no monitor {numero}.")
        if chave_prog:
            sistema.abrir_programa(programas[chave_prog])
        else:
            sistema.abrir_site(sites[chave_site])
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

    # =================================================================
    #  Tela e computador
    # =================================================================
    def _cmd_tela(self, t: str) -> bool:
        if contem(t, "bloqueia o computador"):
            self.voz.falar("Bloqueando. Até já!")
            sistema.bloquear()
            return True
        if contem(t, "desliga a tela"):
            self.voz.falar(random.choice(["Apagando a tela. É só me chamar.", "Luz apagada. Tô de ouvido ligado."]))
            time.sleep(1)
            sistema.desligar_tela()
            return True
        if contem(t, "liga a tela"):
            sistema.acordar_tela()
            self.falar("ok")
            return True
        return False

    def _cmd_desligar_pc(self, t: str) -> bool:
        if re.search(r"\bcancela(r)? (o )?desligamento\b", t):
            sistema.cancelar_desligamento()
            self.voz.falar("Desligamento cancelado. Ufa!")
            return True
        if re.search(r"\b(desliga|desligar)\b (o )?(computador|pc)\b", t):
            self.voz.falar("Vou desligar o computador em um minuto. Se mudar de ideia, fala: {palavra}, cancela o desligamento.")
            sistema.desligar_pc(60)
            return True
        if re.search(r"\b(reinicia|reiniciar)\b (o )?(computador|pc)\b", t):
            self.voz.falar("Vou reiniciar o computador em um minuto.")
            sistema.reiniciar_pc(60)
            return True
        return False

    # =================================================================
    #  Lembretes
    # =================================================================
    def _cmd_lembrete(self, t: str) -> bool:
        if not re.search(r"\b(me lembra|lembrete|timer|alarme)\b", t):
            return False
        n = achar_numero(t)
        if n is None:
            self.voz.falar("Em quanto tempo? Tipo: {palavra}, me lembra de beber água em dez minutos.")
            return True
        em_horas = re.search(r"\bhora", t) and not re.search(r"\bminuto", t)
        segundos = n * (3600 if em_horas else 60)
        assunto = re.sub(r"\b(me lembra|lembrete|timer|alarme)\b|\b(em|daqui a|daqui) (\d+|\w+) (minutos?|horas?)\b", " ", t)
        assunto = re.sub(r"^\s*(de|do|da|que)\s+", "", re.sub(r"\s+", " ", assunto)).strip() or "o seu lembrete"
        unidade = "hora" if em_horas else "minuto"
        self.voz.falar(f"Fechou! Daqui a {n} {unidade}{'s' if n > 1 else ''} eu te lembro: {assunto}.")
        aviso = threading.Timer(segundos, lambda: (sistema.acordar_tela(), self.voz.falar(f"Ô chefe, lembrete: {assunto}!")))
        aviso.daemon = True
        aviso.start()
        return True

    # =================================================================
    #  Anotacoes
    # =================================================================
    def _cmd_notas(self, t: str) -> bool:
        arquivo = PASTA_NOTAS / "notas.txt"
        if re.search(r"\b(le|leia|ler|quais sao) (as |minhas )*(notas|anotacoes)\b", t):
            if not arquivo.exists():
                self.voz.falar("Você ainda não tem anotações.")
            else:
                ultimas = arquivo.read_text(encoding="utf-8").strip().splitlines()[-5:]
                self.voz.falar("Suas últimas anotações: " + ". ".join(l.split("] ", 1)[-1] for l in ultimas))
            return True
        if re.search(r"\babre (as |minhas )*(notas|anotacoes)\b", t):
            sistema.abrir_arquivo(arquivo)
            return True
        achado = re.match(r"^anota( ai| que| isso| ai que)?\s+(.+)", t)
        if achado:
            PASTA_NOTAS.mkdir(exist_ok=True)
            with open(arquivo, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now():%d/%m/%Y %H:%M}] {achado.group(2)}\n")
            self.voz.falar(random.choice(["Anotado.", "Guardei aqui.", "Tá na lista."]))
            return True
        return False

    # =================================================================
    #  Pesquisa na internet
    # =================================================================
    def _cmd_pesquisa(self, t: str) -> bool:
        achado = re.match(r"^(pesquisa|google)( no google| na internet)?( sobre| por| em)?\s+(.+)", t)
        if not achado:
            return False
        termo = self._original(achado.group(4).replace("no google", "").replace("na internet", "").strip())
        self.voz.falar(random.choice(["Pesquisando no Google.", "Deixa eu dar um Google nisso.", "Já tô pesquisando."]))
        sistema.abrir_site("https://www.google.com/search?q=" + quote_plus(termo))
        return True

    # =================================================================
    #  Abrir programas e sites
    # =================================================================
    def _o_que_abrir(self, t: str) -> tuple[str, str | None, str | None] | None:
        """ "abre o gmail" -> (nome falado, programa cadastrado, site cadastrado). None = nao e "abre ..." """
        achado = re.match(r"^(abre|liga)\s+(o |a |os |as |meu |minha )?(site |programa |app |aplicativo )?(do |da |de )?(.+)", t)
        if not achado:
            return None
        nome = achado.group(5).strip()
        return (nome, melhor_correspondencia(nome, self.cfg.get("programas") or {}),
                melhor_correspondencia(nome, self.cfg.get("sites") or {}))

    def _cmd_abrir(self, t: str) -> bool:
        alvo = self._o_que_abrir(t)
        if not alvo:
            return False
        nome, chave_prog, chave_site = alvo
        programas = self.cfg.get("programas") or {}
        sites = self.cfg.get("sites") or {}
        if chave_prog:
            if sistema.MONITOR_ALVO and self._ja_aberto_vai_pro_monitor(chave_prog, programas[chave_prog]):
                return True
            self.voz.falar(random.choice([f"Abrindo {chave_prog}.", f"{chave_prog}, saindo!", "Na hora."]))
            if not sistema.abrir_programa(programas[chave_prog]):
                self.voz.falar(f"Não consegui abrir {chave_prog}. Confere o caminho no painel e usa o botão testar.")
        elif chave_site:
            if self._site_ja_aberto(chave_site, sites[chave_site]):
                return True
            self.voz.falar(random.choice([f"Abrindo {chave_site}.", f"Indo pro {chave_site}.", "Já é!"]))
            sistema.abrir_site(sites[chave_site])
        else:
            self.voz.falar(f"Não conheço {nome}. Coloca ele na lista de programas ou sites do config que eu aprendo.")
        return True
