"""Ferramentas para comparar frases faladas sem se preocupar com acentos e pontuacao."""
import difflib
import re
import unicodedata

NUMEROS = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4, "cinco": 5,
    "seis": 6, "sete": 7, "oito": 8, "nove": 9, "dez": 10, "onze": 11, "doze": 12,
    "quinze": 15, "vinte": 20, "trinta": 30, "quarenta": 40, "quarenta e cinco": 45,
    "cinquenta": 50, "sessenta": 60, "meia": 30,
}

# Palavras de "enfeite" que costumam vir junto da palavra de ativacao.
SAUDACOES = {"e", "ai", "ei", "oi", "ola", "fala", "hey", "opa", "ae", "eai", "o", "meu", "minha", "salve", "beleza",
             "ow", "ou", "po"}
# No modo descanso so estas frases acordam (com ou sem a palavra de ativacao)
VOLTAR_DO_DESCANSO = (r"\b(bora|vamos|vamo|hora de|pode) (voltar|volta) (a|pra|para o|ao)? ?(trabalhar|trabalho|ativa|ativo)\b|"
                      r"\bvolta(r)? a trabalhar\b|\bfim do descanso\b|\b(acorda|acordar|desperta)\b|\bvoltei\b|"
                      r"\bvoltamos\b|\bmodo trabalho\b|\bhora de trabalhar\b|\bpode voltar\b|^volta$|"
                      r"\b(bora|vamos|vamo) voltar$")


def frase_de_volta(texto: str) -> bool:
    return bool(re.search(VOLTAR_DO_DESCANSO, normalizar(texto)))


def normalizar(texto: str) -> str:
    """'E aí, Mestre! Bora?' -> 'e ai mestre bora'"""
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9@ ]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def parecida(palavra: str, alvos: list[str], minimo: float = 0.8) -> bool:
    return any(difflib.SequenceMatcher(None, palavra, a).ratio() >= minimo for a in alvos)


def extrair_comando(texto: str, variacoes: list[str]) -> tuple[bool, str]:
    """Procura a palavra de ativacao e devolve (achou, comando_sem_ela).

    'e ai mestre bora trabalhar' -> (True, 'bora trabalhar')
    'bora trabalhar mestre'      -> (True, 'bora trabalhar')
    """
    palavras = normalizar(texto).split()
    alvos = [normalizar(v) for v in variacoes]
    posicoes = [i for i, p in enumerate(palavras) if parecida(p, alvos)]
    if not posicoes:
        return False, ""
    i = posicoes[0]
    antes = [p for p in palavras[:i] if p not in SAUDACOES]
    depois = palavras[i + 1:]
    return True, " ".join(antes + depois).strip()


def contem(texto_normalizado: str, frase: str) -> bool:
    """Verifica se a frase aparece como palavras inteiras no texto."""
    frase = normalizar(frase)
    return re.search(rf"\b{re.escape(frase)}\b", texto_normalizado) is not None


def achar_numero(texto_normalizado: str) -> int | None:
    achado = re.search(r"\b(\d+)\b", texto_normalizado)
    if achado:
        return int(achado.group(1))
    for palavra in sorted(NUMEROS, key=len, reverse=True):
        if contem(texto_normalizado, palavra):
            return NUMEROS[palavra]
    return None


def melhor_correspondencia(nome: str, opcoes: dict, minimo: float = 0.7):
    """Acha a chave do dicionario mais parecida com o nome falado."""
    nome = normalizar(nome)
    if not nome:
        return None
    normalizadas = {normalizar(k): k for k in opcoes}
    if nome in normalizadas:
        return normalizadas[nome]
    # Varias chaves aparecem na frase? Fica com a mais longa (a mais especifica).
    contidas = [c for c in normalizadas if c and (contem(nome, c) or contem(c, nome))]
    if contidas:
        return normalizadas[max(contidas, key=len)]
    parecidas = difflib.get_close_matches(nome, list(normalizadas), n=1, cutoff=minimo)
    return normalizadas[parecidas[0]] if parecidas else None


def limpar_para_falar(texto: str) -> str:
    """Tira marcacoes de formatacao (markdown) que ficam estranhas faladas."""
    texto = re.sub(r"```.*?```", " (trecho de codigo na tela) ", texto, flags=re.S)
    texto = re.sub(r"[#*_`>|]+", " ", texto)
    texto = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", texto)
    return re.sub(r"\s+", " ", texto).strip()


def recuperar_original(original: str, trecho_normalizado: str) -> str:
    """Acha, na frase ORIGINAL, o pedaco que corresponde a um trecho normalizado.

    recuperar_original("Mestre, toca Canção Nova no YouTube!", "cancao nova") -> "Canção Nova"
    Se nao achar, devolve o proprio trecho normalizado.
    """
    alvo = normalizar(trecho_normalizado)
    if not alvo:
        return trecho_normalizado
    # Normaliza caractere a caractere, guardando de onde veio cada um
    chars, origem = [], []
    for i, c in enumerate(original):
        base = "".join(x for x in unicodedata.normalize("NFD", c.lower()) if unicodedata.category(x) != "Mn")
        for b in base or " ":
            b = b if re.match(r"[a-z0-9@]", b) else " "
            if b == " " and chars and chars[-1] == " ":
                continue
            chars.append(b)
            origem.append(i)
    texto = "".join(chars)
    achado = re.search(rf"(?<![a-z0-9@]){re.escape(alvo)}(?![a-z0-9@])", texto)
    if not achado:
        return trecho_normalizado
    inicio, fim = origem[achado.start()], origem[achado.end() - 1] + 1
    return original[inicio:fim].strip(" ,.!?;:")
