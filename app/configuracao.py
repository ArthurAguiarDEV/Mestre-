"""Ler e salvar o config.yaml SEM perder os comentarios (usado pelo painel)."""
import logging
import re

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.constructor import DuplicateKeyError
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

from .config import ARQUIVO_CONFIG

log = logging.getLogger(__name__)
ultimo_conserto: list[str] = []   # secoes repetidas removidas na ultima leitura (o painel avisa)


def _yaml() -> YAML:
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)
    y.representer.add_representer(type(None), lambda r, d: r.represent_scalar("tag:yaml.org,2002:null", "null"))
    return y


def aspas(valor):
    """Textos sempre entre aspas (assim "Oi!" ou "Bora?" nunca quebram o arquivo)."""
    if isinstance(valor, bool) or valor is None or isinstance(valor, (int, float)):
        return valor
    if isinstance(valor, dict):
        m = CommentedMap()
        for k, v in valor.items():
            m[str(k)] = aspas(v)
        return m
    if isinstance(valor, (list, tuple)):
        return CommentedSeq([aspas(v) for v in valor])
    return DoubleQuotedScalarString(str(valor))


def carregar() -> CommentedMap:
    try:
        with open(ARQUIVO_CONFIG, encoding="utf-8") as f:
            return _yaml().load(f) or CommentedMap()
    except DuplicateKeyError:
        ultimo_conserto[:] = consertar_secoes_repetidas()
        with open(ARQUIVO_CONFIG, encoding="utf-8") as f:
            return _yaml().load(f) or CommentedMap()


def consertar_secoes_repetidas() -> list[str]:
    """Apaga secoes repetidas do config (ex.: 'voz:' colada duas vezes).

    Fica a ULTIMA de cada uma, que e a que o Mestre ja estava usando.
    Guarda o arquivo original em config.yaml.antes_do_conserto.
    """
    linhas = ARQUIVO_CONFIG.read_text(encoding="utf-8").splitlines(keepends=True)
    # onde comeca cada secao principal (linha sem recuo do tipo "nome:")
    inicios = [(i, re.match(r"^([A-Za-z_][\w]*):", l).group(1)) for i, l in enumerate(linhas)
               if re.match(r"^([A-Za-z_][\w]*):", l)]
    ultima = {nome: i for i, nome in inicios}
    apagar = set()
    for i, nome in inicios:
        if ultima[nome] == i:
            continue
        fim = i + 1  # a secao vai ate a proxima linha sem recuo (outra secao ou comentario)
        while fim < len(linhas) and (linhas[fim].startswith((" ", "\t")) or not linhas[fim].strip()):
            fim += 1
        apagar.update(range(i, fim))
    if not apagar:
        return []
    ARQUIVO_CONFIG.with_suffix(".yaml.antes_do_conserto").write_text("".join(linhas), encoding="utf-8")
    ARQUIVO_CONFIG.write_text("".join(l for i, l in enumerate(linhas) if i not in apagar), encoding="utf-8")
    repetidas = sorted({nome for i, nome in inicios if ultima[nome] != i})
    log.warning("config.yaml: secoes repetidas removidas: %s", repetidas)
    return repetidas


def salvar(dados: CommentedMap) -> None:
    copia = ARQUIVO_CONFIG.with_suffix(".yaml.bak")
    copia.write_text(ARQUIVO_CONFIG.read_text(encoding="utf-8"), encoding="utf-8")  # backup
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
        _yaml().dump(dados, f)


def secao(dados: CommentedMap, nome: str) -> CommentedMap:
    """Devolve a secao (criando no fim do arquivo se nao existir)."""
    if not isinstance(dados.get(nome), dict):
        dados[nome] = CommentedMap()
    return dados[nome]


def trocar_mapa(dados: CommentedMap, nome: str, novo: dict) -> None:
    """Substitui o conteudo de uma secao nome->valor mantendo o comentario do topo."""
    atual = secao(dados, nome)
    # O comentario que vem DEPOIS da secao (o titulo da proxima) fica grudado no ultimo item.
    # Guardamos para colocar de volta no novo ultimo item (senao programas novos iam parar
    # embaixo do titulo "SITES").
    fim = None
    if len(atual):
        info = atual.ca.items.pop(list(atual)[-1], None)
        fim = info[2] if info and len(info) > 2 else None
    for chave in list(atual):
        if chave not in novo:
            del atual[chave]
    for chave, valor in novo.items():
        atual[str(chave)] = aspas(valor)
    if fim is not None and len(atual):   # (secao vazia: o comentario se perde, sem problema)
        atual.ca.items[list(atual)[-1]] = [None, None, fim, None]


def lista_em_linha(itens: list) -> CommentedSeq:
    """Lista no estilo ["a", "b"] (igual ao resto do arquivo)."""
    seq = CommentedSeq([aspas(i) for i in itens])
    seq.fa.set_flow_style()
    return seq


# --- Migracoes: novidades de cada versao que precisam entrar no config do usuario ---------
SITES_PADRAO = {
    # streaming
    "netflix": "https://www.netflix.com", "prime video": "https://www.primevideo.com",
    "disney": "https://www.disneyplus.com", "hbo max": "https://www.hbomax.com",
    "globoplay": "https://globoplay.globo.com", "twitch": "https://www.twitch.tv",
    # compras
    "amazon": "https://www.amazon.com.br", "mercado livre": "https://www.mercadolivre.com.br",
    "shopee": "https://shopee.com.br",
    # redes
    "tiktok": "https://www.tiktok.com", "instagram": "https://www.instagram.com",
    "whatsapp": "https://web.whatsapp.com", "gmail": "https://mail.google.com",
    # IAs
    "chatgpt": "https://chatgpt.com", "gemini": "https://gemini.google.com", "claude site": "https://claude.ai",
    "copilot": "https://copilot.microsoft.com", "perplexity": "https://www.perplexity.ai",
    "deepseek": "https://chat.deepseek.com", "grok": "https://grok.com",
}
VERSAO_CONFIG = 13


def migrar() -> bool:
    """Acrescenta ao config as novidades (sites padrao etc.) UMA vez, sem apagar nada seu.

    Devolve True se mudou algo. Chamado ao ligar o Mestre e ao abrir o painel.
    """
    try:
        dados = carregar()
    except Exception as erro:
        log.warning("Migracao do config pulada: %s", erro)
        return False
    versao = int(dados.get("versao_config") or 0)
    if versao >= VERSAO_CONFIG:
        return False
    if versao < 10:   # v10: sites padrao (streaming, compras, IAs)
        sites = secao(dados, "sites")
        existentes = {str(k).strip().lower() for k in sites}
        for nome, link in SITES_PADRAO.items():
            if nome not in existentes:
                sites[nome] = aspas(link)
    if versao < 11:
        # v11: o "pensando" fica em silencio (so o indicador na tela)
        cb = secao(dados, "cerebro")
        cb["aviso_som"] = aspas("nenhum")
        if str(cb.get("aviso_ao_terminar", "voz")) == "voz":
            cb["aviso_ao_terminar"] = aspas("tela")
        # v11: quem e quem. Palavra "assessor" + nome ainda "Mestre" (ou igual ao seu apelido) = ele se
        # chamava de Mestre. O nome dele passa a ser a palavra de ativacao.
        a = secao(dados, "assistente")
        palavra = (str(a.get("palavra_ativacao") or "mestre").split() or ["mestre"])[-1].strip(",.!")
        nome = str(a.get("nome") or "Mestre").strip()
        apelido = str(a.get("apelido_usuario") or "chefe").strip()
        if palavra and palavra.lower() != nome.lower() and (nome.lower() in ("mestre", apelido.lower())):
            a["nome"] = aspas(palavra.capitalize())
    if versao < 12:
        # v12: voz Kokoro (no PC) passa a ser a padrao; se falhar, ele usa a Edge sozinho
        v = secao(dados, "voz")
        if str(v.get("motor", "edge")) == "edge":
            v["motor"] = aspas("kokoro")
        v.setdefault("voz_kokoro", aspas("pm_alex"))
    if versao < 13:
        # v13: a IA terminou de pensar? Ela ja fala a resposta (so pergunta quando precisa de voce)
        cb = secao(dados, "cerebro")
        if str(cb.get("aviso_ao_terminar", "tela")) == "tela":
            cb["aviso_ao_terminar"] = aspas("falar_direto")
    dados["versao_config"] = VERSAO_CONFIG
    salvar(dados)
    log.info("config.yaml atualizado da versao %d para a %d", versao, VERSAO_CONFIG)
    return True
