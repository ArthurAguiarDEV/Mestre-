"""Memoria do Mestre: historico de pedidos/respostas e fatos que voce pede para lembrar.

Fica na pasta memoria/ (a atualizacao pelo painel nunca mexe nela):
  memoria/historico.jsonl  -> uma linha por pedido: data, o que voce disse, o que ele respondeu
  memoria/fatos.md         -> "lembra que ..." (uma linha por fato; a IA usa nas respostas)
  memoria/conversa.json    -> ultimas trocas com a IA (a conversa continua depois de reiniciar)
  memoria/ouvido.jsonl     -> tudo que o microfone transcreveu (para achar erros de reconhecimento)
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
ARQUIVO_FATOS = PASTA_MEMORIA / "fatos.md"
ARQUIVO_CONVERSA = PASTA_MEMORIA / "conversa.json"
ARQUIVO_OUVIDO = PASTA_MEMORIA / "ouvido.jsonl"
MAXIMO_HISTORICO = 2000
MAXIMO_OUVIDO = 3000
_trava = threading.Lock()


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
def fatos() -> list[str]:
    if not ARQUIVO_FATOS.exists():
        return []
    return [l[2:].strip() for l in ARQUIVO_FATOS.read_text(encoding="utf-8").splitlines() if l.startswith("- ")]


def salvar_fatos(lista: list[str]) -> None:
    PASTA_MEMORIA.mkdir(exist_ok=True)
    corpo = "".join(f"- {f.strip()}\n" for f in lista if f.strip())
    ARQUIVO_FATOS.write_text("# O que o Mestre sabe sobre voce (edite a vontade: um fato por linha)\n\n" + corpo,
                             encoding="utf-8")


def lembrar(fato: str) -> None:
    atual = fatos()
    if normalizar(fato) not in {normalizar(f) for f in atual}:
        salvar_fatos(atual + [fato])


def esquecer(trecho: str) -> list[str]:
    """Apaga os fatos que contem o trecho. Devolve os apagados."""
    alvo = normalizar(trecho)
    atual = fatos()
    apagados = [f for f in atual if alvo and alvo in normalizar(f)]
    if apagados:
        salvar_fatos([f for f in atual if f not in apagados])
    return apagados


def texto_para_ia() -> str:
    lista = fatos()
    return ("\nCoisas que o usuario pediu para voce lembrar:\n" + "\n".join(f"- {f}" for f in lista)) if lista else ""


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
