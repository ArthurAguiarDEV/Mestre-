"""Constantes e funcoes pequenas usadas pelos comandos (nao dependem do Executor).

O __init__.py reexporta tudo daqui: `from app.comandos import ARQUIVO_MELHORIAS` continua valendo.
"""
import re
from .. import personalidades
from ..config import PASTA_PROJETO
from ..texto import achar_numero

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
NAO_GRAVA_NA_ROTINA = {"_cmd_pensamento", "_cmd_parar", "_cmd_descanso", "_cmd_versao", "_cmd_conversinha", "_cmd_exportar",
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
