"""Memoria do Mestre: historico de pedidos/respostas e fatos que voce pede para lembrar.

Fica na pasta memoria/ (a atualizacao pelo painel nunca mexe nela):
  memoria/historico.jsonl        -> uma linha por pedido: data, o que voce disse, o que ele respondeu
  memoria/fatos/                 -> "lembra que ..." separado por assunto (um .md por assunto, ASSUNTOS)
  memoria/fatos/INDICE.md        -> resumo de cada arquivo de assunto (o que a IA le primeiro)
  memoria/fatos.md.antes_da_migracao -> backup do fatos.md antigo (uma versao anterior guardava tudo junto)
  memoria/conversa.json          -> ultimas trocas com a IA (a conversa continua depois de reiniciar)
  memoria/ouvido.jsonl           -> tudo que o microfone transcreveu (para achar erros de reconhecimento)
  memoria/tempos.jsonl           -> quanto cada etapa demorou (painel > Tempos): fala->texto, frase->comando,
                                     IA por provedor, ate comecar a falar
"""
import json
import logging
import threading
import time
from datetime import datetime

from .config import PASTA_PROJETO
from .texto import normalizar

log = logging.getLogger(__name__)
PASTA_MEMORIA = PASTA_PROJETO / "memoria"
ARQUIVO_HISTORICO = PASTA_MEMORIA / "historico.jsonl"
ARQUIVO_FATOS = PASTA_MEMORIA / "fatos.md"                          # versao antiga (um arquivo so): so existe ate migrar
BACKUP_FATOS_ANTIGO = PASTA_MEMORIA / "fatos.md.antes_da_migracao"
PASTA_FATOS = PASTA_MEMORIA / "fatos"
ARQUIVO_INDICE = PASTA_FATOS / "INDICE.md"
ARQUIVO_CONVERSA = PASTA_MEMORIA / "conversa.json"
ARQUIVO_OUVIDO = PASTA_MEMORIA / "ouvido.jsonl"
ARQUIVO_TEMPOS = PASTA_MEMORIA / "tempos.jsonl"
MAXIMO_HISTORICO = 2000
MAXIMO_OUVIDO = 3000
MAXIMO_TEMPOS = 4000
_trava = threading.Lock()

# --- Fatos por assunto ("lembra que ...") --------------------------------------------------
ASSUNTOS = ["pessoas", "projetos", "preferencias", "casa", "trabalho", "geral"]
ASSUNTO_PADRAO = "geral"
DESCRICAO_ASSUNTO = {
    "pessoas": "nomes, aniversarios e preferencias de pessoas proximas (familia, amigos, colegas)",
    "projetos": "projetos pessoais ou de trabalho, ideias e planos",
    "preferencias": "gostos, preferencias e coisas que ele evita",
    "casa": "endereco, rede de internet de casa, animais de estimacao e coisas do dia a dia em casa",
    "trabalho": "emprego, horarios, empresa e assuntos de trabalho",
    "geral": "fatos que nao se encaixam nos outros assuntos",
}
# Palavras (ja sem acento) que classificam um fato por assunto. Ordem de checagem: PRIORIDADE_ASSUNTO.
PALAVRAS_ASSUNTO = {
    "pessoas": ["aniversario", "esposa", "marido", "namorada", "namorado", "filho", "filha", "amigo", "amiga",
                "mae", "pai", "irmao", "irma", "familia", "avo", "colega", "sobrinho", "sobrinha", "prima", "primo",
                "noiva", "noivo"],
    "trabalho": ["trabalho", "trabalha", "empresa", "escritorio", "chefe", "reuniao", "expediente", "emprego",
                 "ipm", "cliente", "horario de trabalho", "colega de trabalho"],
    "casa": ["casa", "endereco", "wifi", "roteador", "cachorro", "gato", "pet", "condominio", "aluguel", "vizinho",
             "cep", "apartamento"],
    "preferencias": ["gosto de", "gosta de", "prefiro", "prefere", "odeio", "nao gosto", "favorito", "favorita",
                     "detesto", "adoro"],
    "projetos": ["projeto", "codigo", "aplicativo", "programando", "programa que"],
}
PRIORIDADE_ASSUNTO = ["pessoas", "trabalho", "casa", "preferencias", "projetos"]
LIMITE_CONTEXTO_PADRAO_KB = 6.0   # tamanho maximo (fatos + indice) mandado a IA de uma vez


# --- Historico ------------------------------------------------------------------------
def registrar(pedido: str, resposta: str, tipo: str = "comando", extra: dict | None = None) -> None:
    """extra (para a exportacao): "entendi" (a frase depois do vocabulario) e "rota" (qual comando
    atendeu, "ia", "nao_entendi"...). "ts" (segundos) serve para a validacao achar o pedido certo."""
    if not (pedido or "").strip() and not (resposta or "").strip():
        return
    item = {"data": datetime.now().strftime("%d/%m/%Y %H:%M"), "pedido": pedido.strip(),
            "resposta": (resposta or "").strip(), "tipo": tipo, "ts": round(time.time(), 2), **(extra or {})}
    _acrescentar(ARQUIVO_HISTORICO, item, MAXIMO_HISTORICO)


def ouvido(texto: str, **dados) -> None:
    """Toda frase transcrita pelo microfone, inclusive as ignoradas (sem a palavra de ativacao).
    Serve para descobrir onde o reconhecimento de fala erra (painel > Histórico > Exportar)."""
    item = {"data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"), "texto": (texto or "").strip(),
            "ts": round(time.time(), 2), **dados}
    _acrescentar(ARQUIVO_OUVIDO, item, MAXIMO_OUVIDO)


def registrar_tempo(etapa: str, segundos: float) -> None:
    """Quanto uma etapa demorou (painel > Sistema > Tempos), para achar o que esta lento: "fala_para_texto"
    (Whisper), "frase_para_comando" (achar e rodar o comando), "ia_<id>" (cada provedor de IA) e
    "ate_falar" (da decisao ate o audio comecar a tocar). Nunca atrapalha quem chamou: so registra."""
    try:
        if segundos is None or segundos < 0:
            return
        item = {"ts": round(time.time(), 2), "etapa": str(etapa), "segundos": round(float(segundos), 3)}
        _acrescentar(ARQUIVO_TEMPOS, item, MAXIMO_TEMPOS)
    except Exception:
        log.warning("Nao consegui guardar o tempo da etapa %s", etapa, exc_info=True)


def tempos_resumo(n: int = 50) -> dict[str, dict]:
    """Media e pior caso das ultimas `n` medidas de cada etapa (memoria/tempos.jsonl).
    Devolve {etapa: {"media": s, "pior": s, "n": quantas}}."""
    if not ARQUIVO_TEMPOS.exists():
        return {}
    por_etapa: dict[str, list[float]] = {}
    try:
        linhas = ARQUIVO_TEMPOS.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}
    for linha in linhas:
        try:
            d = json.loads(linha)
            por_etapa.setdefault(str(d["etapa"]), []).append(float(d["segundos"]))
        except (ValueError, KeyError, TypeError):
            continue
    resumo = {}
    for etapa, valores in por_etapa.items():
        ultimos = valores[-n:]
        if not ultimos:
            continue
        resumo[etapa] = {"media": round(sum(ultimos) / len(ultimos), 2), "pior": round(max(ultimos), 2),
                          "n": len(ultimos)}
    return resumo


def _acrescentar(arquivo, item: dict, maximo: int) -> None:
    with _trava:
        try:
            PASTA_MEMORIA.mkdir(exist_ok=True)
            with open(arquivo, "a", encoding="utf-8") as f:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
            _enxugar(arquivo, maximo)
        except OSError as erro:
            log.warning("Nao consegui guardar em %s: %s", arquivo.name, erro)


def _enxugar(arquivo, maximo: int) -> None:
    linhas = arquivo.read_text(encoding="utf-8").splitlines()
    if len(linhas) > maximo * 1.2:
        arquivo.write_text("\n".join(linhas[-maximo:]) + "\n", encoding="utf-8")


def _ler(arquivo, limite: int) -> list[dict]:
    if not arquivo.exists():
        return []
    itens = []
    for linha in arquivo.read_text(encoding="utf-8").splitlines()[-limite:]:
        try:
            itens.append(json.loads(linha))
        except ValueError:
            continue
    return itens


def ouvidas(limite: int = 5000) -> list[dict]:
    return _ler(ARQUIVO_OUVIDO, limite)


def historico(limite: int = 200) -> list[dict]:
    """Mais recentes por ultimo."""
    return _ler(ARQUIVO_HISTORICO, limite)


def comando_ja_descoberto(pedido: str) -> str:
    """A IA ja transformou esta frase (ou uma quase igual) em comando antes? Devolve o comando (ou "").
    Assim a mesma frase nao precisa esperar a IA de novo."""
    from difflib import SequenceMatcher

    alvo = normalizar(pedido)
    if len(alvo) < 4:
        return ""
    melhor, nota_melhor = "", 0.0
    for item in historico(4000):
        if item.get("tipo") != "ia virou comando":
            continue
        comando = str(item.get("ia_texto") or item.get("entendi") or "")
        visto = normalizar(item.get("pedido", ""))
        if not comando or not visto:
            continue
        nota = 1.0 if visto == alvo else SequenceMatcher(None, visto, alvo).ratio()
        if nota >= nota_melhor:   # o mais recente ganha no empate
            melhor, nota_melhor = comando, nota
    return melhor if nota_melhor >= 0.9 else ""


def confirmar_comando_ia(pedido: str, texto_ia: str, comando: str, rota: str) -> None:
    """Grava frase->comando na memoria (`comando_ja_descoberto` usa depois). So chame isto depois de
    confirmado: o comando rodou sem correcao por uns 30s, ou a mesma frase repetiu o mesmo comando."""
    registrar(pedido, "", "ia virou comando", {"entendi": comando, "ia_texto": texto_ia, "rota": rota})


def esquecer_comando_ia(pedido: str) -> list[dict]:
    """Apaga do historico as vezes que a IA transformou uma frase parecida com `pedido` em comando.
    Usado quando o usuario corrige (FEEDBACK, "nao era isso", cancelar): a lembranca errada some.
    Devolve os itens apagados."""
    from difflib import SequenceMatcher

    alvo = normalizar(pedido)
    if len(alvo) < 4:
        return []
    todos = _ler(ARQUIVO_HISTORICO, MAXIMO_HISTORICO * 2)
    mantidos, apagados = [], []
    for item in todos:
        if item.get("tipo") == "ia virou comando":
            visto = normalizar(item.get("pedido", ""))
            nota = 1.0 if visto == alvo else SequenceMatcher(None, visto, alvo).ratio()
            if visto and nota >= 0.9:
                apagados.append(item)
                continue
        mantidos.append(item)
    if apagados:
        with _trava:
            try:
                PASTA_MEMORIA.mkdir(exist_ok=True)
                corpo = "".join(json.dumps(i, ensure_ascii=False) + "\n" for i in mantidos)
                ARQUIVO_HISTORICO.write_text(corpo, encoding="utf-8")
            except OSError as erro:
                log.warning("Nao consegui apagar memoria da IA: %s", erro)
    return apagados


def respostas(limite: int = 50) -> list[dict]:
    """So os itens que tiveram resposta falada (mais recentes por ultimo)."""
    return [i for i in historico(limite * 4) if i.get("resposta")][-limite:]


def procurar(assunto: str) -> dict | None:
    """A resposta mais recente cujo pedido ou resposta fala do assunto."""
    palavras = [p for p in normalizar(assunto).split() if len(p) > 2]
    if not palavras:
        return None
    melhor, pontos_melhor = None, 0
    for item in reversed(respostas(500)):
        texto = normalizar(item.get("pedido", "") + " " + item.get("resposta", ""))
        pontos = sum(1 for p in palavras if p in texto)
        if pontos > pontos_melhor:
            melhor, pontos_melhor = item, pontos
    return melhor if pontos_melhor >= max(1, len(palavras) // 2) else None


# --- Fatos ("lembra que ...") ------------------------------------------------------------
def classificar_assunto(fato: str) -> str:
    """So por palavras-chave, funciona 100% sem IA (a IA pode sugerir depois, em segundo plano)."""
    alvo = normalizar(fato)
    for assunto in PRIORIDADE_ASSUNTO:
        if any(normalizar(p) in alvo for p in PALAVRAS_ASSUNTO.get(assunto, [])):
            return assunto
    return ASSUNTO_PADRAO


def _arquivo_assunto(assunto: str):
    return PASTA_FATOS / f"{assunto}.md"


def fatos_assunto(assunto: str) -> list[str]:
    arquivo = _arquivo_assunto(assunto)
    if not arquivo.exists():
        return []
    return [l[2:].strip() for l in arquivo.read_text(encoding="utf-8").splitlines() if l.startswith("- ")]


def salvar_fatos_assunto(assunto: str, lista: list[str]) -> None:
    if assunto not in ASSUNTOS:
        assunto = ASSUNTO_PADRAO
    PASTA_FATOS.mkdir(parents=True, exist_ok=True)
    corpo = "".join(f"- {f.strip()}\n" for f in lista if f.strip())
    cabecalho = f"# {assunto.capitalize()} ({DESCRICAO_ASSUNTO.get(assunto, '')})\nEdite a vontade: um fato por linha.\n\n"
    _arquivo_assunto(assunto).write_text(cabecalho + corpo, encoding="utf-8")
    _atualizar_indice()


def _atualizar_indice() -> None:
    """Uma linha por arquivo de assunto, com resumo curto do TIPO de conteudo (nunca os fatos em si: o
    indice vai inteiro pra IA junto com qualquer pergunta, entao nao pode vazar assunto que nao veio ao caso).
    E o que a IA le primeiro (texto_para_ia)."""
    linhas = ["# Indice dos assuntos (memoria de longo prazo)", ""]
    for assunto in ASSUNTOS:
        n = len(fatos_assunto(assunto))
        resumo = DESCRICAO_ASSUNTO.get(assunto, "")
        linhas.append(f"- {assunto}.md — {resumo} ({n} fato(s))" if n else f"- {assunto}.md — {resumo} (vazio)")
    PASTA_FATOS.mkdir(parents=True, exist_ok=True)
    ARQUIVO_INDICE.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def _migrar_se_preciso() -> None:
    """1a vez com esta versao: se memoria/fatos.md (tudo junto) ainda existir, separa por assunto,
    gera o INDICE.md e guarda o original em fatos.md.antes_da_migracao (nunca apaga). So roda uma vez:
    depois da migracao o fatos.md antigo nao existe mais, entao a proxima chamada nem entra aqui."""
    if not ARQUIVO_FATOS.exists():
        return
    with _trava:
        if not ARQUIVO_FATOS.exists():
            return   # outra thread migrou enquanto esperava a trava
        ja_tem_fatos_por_assunto = PASTA_FATOS.exists() and any(fatos_assunto(a) for a in ASSUNTOS)
        if not ja_tem_fatos_por_assunto:
            try:
                antigos = [l[2:].strip() for l in ARQUIVO_FATOS.read_text(encoding="utf-8").splitlines()
                          if l.startswith("- ")]
            except OSError as erro:
                log.warning("Nao consegui ler o fatos.md antigo para migrar: %s", erro)
                return
            PASTA_FATOS.mkdir(parents=True, exist_ok=True)
            for fato in antigos:
                assunto = classificar_assunto(fato)
                salvar_fatos_assunto(assunto, fatos_assunto(assunto) + [fato])
            _atualizar_indice()
            log.info("Memoria migrada: %d fato(s) de fatos.md para memoria/fatos/", len(antigos))
        try:
            ARQUIVO_FATOS.replace(BACKUP_FATOS_ANTIGO)
        except OSError as erro:
            log.warning("Nao consegui guardar o backup do fatos.md antigo: %s", erro)


def fatos() -> list[str]:
    """Todos os fatos, de todos os assuntos (compatibilidade: quem so quer a lista toda)."""
    _migrar_se_preciso()
    return [f for assunto in ASSUNTOS for f in fatos_assunto(assunto)]


def lembrar(fato: str, assunto: str | None = None) -> str:
    """Classifica por palavra-chave (a menos que `assunto` ja venha decidido) e grava no arquivo certo.
    Devolve o assunto usado (`_cmd_memoria` usa para, se a IA estiver ligada, pedir uma 2a opiniao em
    segundo plano e mover com `mover_assunto` se ela discordar - sem travar a escuta)."""
    _migrar_se_preciso()
    if normalizar(fato) in {normalizar(f) for f in fatos()}:
        return assunto if assunto in ASSUNTOS else classificar_assunto(fato)
    alvo = assunto if assunto in ASSUNTOS else classificar_assunto(fato)
    salvar_fatos_assunto(alvo, fatos_assunto(alvo) + [fato])
    return alvo


def mover_assunto(fato: str, novo_assunto: str) -> bool:
    """Move um fato ja gravado para outro arquivo de assunto (sugestao da IA em segundo plano)."""
    if novo_assunto not in ASSUNTOS:
        return False
    alvo = normalizar(fato)
    with _trava:
        for assunto in ASSUNTOS:
            if assunto == novo_assunto:
                continue
            atual = fatos_assunto(assunto)
            achado = next((f for f in atual if normalizar(f) == alvo), None)
            if achado:
                salvar_fatos_assunto(assunto, [f for f in atual if f != achado])
                salvar_fatos_assunto(novo_assunto, fatos_assunto(novo_assunto) + [achado])
                return True
    return False


def esquecer(trecho: str) -> list[str]:
    """Apaga (em todos os assuntos) os fatos que contem o trecho. Devolve os apagados."""
    _migrar_se_preciso()
    alvo = normalizar(trecho)
    apagados: list[str] = []
    if not alvo:
        return apagados
    for assunto in ASSUNTOS:
        atual = fatos_assunto(assunto)
        achados = [f for f in atual if alvo in normalizar(f)]
        if achados:
            salvar_fatos_assunto(assunto, [f for f in atual if f not in achados])
            apagados.extend(achados)
    return apagados


def _assuntos_relevantes(pergunta: str) -> list[str]:
    """Assuntos ligados as palavras da pergunta (mesma logica da classificacao). Sem pista nenhuma: todos
    (o limite de tamanho em texto_para_ia corta se precisar)."""
    alvo = normalizar(pergunta)
    achados = [a for a in PRIORIDADE_ASSUNTO
              if a in alvo or any(normalizar(p) in alvo for p in PALAVRAS_ASSUNTO.get(a, []))]
    if ASSUNTO_PADRAO in alvo and ASSUNTO_PADRAO not in achados:
        achados.append(ASSUNTO_PADRAO)
    if not achados:
        return list(ASSUNTOS)
    if ASSUNTO_PADRAO not in achados:
        achados.append(ASSUNTO_PADRAO)   # o fallback sempre entra: pode ter algo que nao bateu palavra-chave
    return achados


def texto_para_ia(pergunta: str = "", limite_kb: float = LIMITE_CONTEXTO_PADRAO_KB) -> str:
    """O que mandar para a IA: o INDICE.md inteiro + so os arquivos de assunto relevantes a pergunta (ou
    todos, sem pergunta), ate o limite de tamanho (nao estoura o prompt). `pergunta` = a frase do usuario
    (ou o pedido) que vai motivar a resposta."""
    _migrar_se_preciso()
    if not any(fatos_assunto(a) for a in ASSUNTOS):
        return ""
    indice = ARQUIVO_INDICE.read_text(encoding="utf-8") if ARQUIVO_INDICE.exists() else ""
    partes = [f"\nMemoria de longo prazo (fatos que o usuario pediu para voce lembrar, por assunto). "
              f"Indice dos assuntos:\n{indice}"]
    limite_bytes = max(1024, int(float(limite_kb) * 1024))
    usado = len(partes[0].encode("utf-8"))
    for assunto in _assuntos_relevantes(pergunta):
        lista = fatos_assunto(assunto)
        if not lista:
            continue
        bloco = f"\n## {assunto}.md\n" + "\n".join(f"- {f}" for f in lista)
        if usado + len(bloco.encode("utf-8")) > limite_bytes:
            break
        partes.append(bloco)
        usado += len(bloco.encode("utf-8"))
    return "".join(partes)


# --- Conversa com a IA (continua depois de reiniciar) -------------------------------------
def carregar_conversa() -> dict:
    try:
        return json.loads(ARQUIVO_CONVERSA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def salvar_conversa(historicos: dict) -> None:
    try:
        PASTA_MEMORIA.mkdir(exist_ok=True)
        ARQUIVO_CONVERSA.write_text(json.dumps(historicos, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
