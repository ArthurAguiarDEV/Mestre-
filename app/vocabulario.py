"""Traduz o jeito solto de falar para a forma que os comandos entendem.

Le vocabulario.yaml (editado por voce) e aprendido.yaml (escrito pelo Mestre
quando voce ensina algo por voz).
"""
import difflib
import logging
import re

import yaml

from .config import PASTA_PROJETO
from .texto import normalizar

log = logging.getLogger(__name__)

ARQUIVO_VOCABULARIO = PASTA_PROJETO / "vocabulario.yaml"
ARQUIVO_APRENDIDO = PASTA_PROJETO / "aprendido.yaml"


# Formas de verbo que o Whisper escreve (imperativo, infinitivo...). Valem mesmo com um vocabulario.yaml
# antigo; o do arquivo vem por cima.
SINONIMOS_EMBUTIDOS = {
    "abre": ["abra", "abrir", "abri", "selecione", "seleciona", "selecionar", "escolha", "escolhe", "escolher"],
    "volta": ["volte", "voltar", "retorne", "retorna", "retornar"],
    "avanca": ["avance", "avancar"],
    "pausa": ["pause", "pausar", "pausa ai"],
    "continua": ["continue", "continuar"],
    "inscreve": ["inscreva", "inscrever"],
    "toca": ["tocar", "toque", "reproduz", "reproduza", "reproduzir"],
    "muta": ["mute", "mutar"],
    "desmuta": ["desmute", "desmutar"],
    "pula": ["pule", "pular"],
    "clica": ["clique", "clicar", "aperta em", "aperte em"],
}


def _ler_yaml(caminho) -> dict:
    if not caminho.exists():
        return {}
    try:
        with open(caminho, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as erro:
        log.error("Erro em %s (TAB ou recuo errado?): %s", caminho.name, erro)
        return {}


def _alternativas(frases) -> str:
    """Monta um "ou" de frases inteiras, da mais longa para a mais curta."""
    unicas = sorted({normalizar(f) for f in frases if normalizar(f)}, key=len, reverse=True)
    return "|".join(re.escape(f) for f in unicas)


class Vocabulario:
    def __init__(self):
        self.recarregar()

    def recarregar(self) -> None:
        v = _ler_yaml(ARQUIVO_VOCABULARIO)
        self.aprendido = _ler_yaml(ARQUIVO_APRENDIDO)

        inicio = _alternativas(v.get("ignorar_no_inicio") or [])
        self._re_inicio = re.compile(rf"^(?:{inicio})\b\s*") if inicio else None
        qualquer = _alternativas(v.get("ignorar_em_qualquer_lugar") or [])
        self._re_qualquer = re.compile(rf"\b(?:{qualquer})\b") if qualquer else None

        # Cada jeito de falar aponta para a forma "oficial" (inclusive ela mesma).
        # aprendido.yaml tambem pode ter "sinonimos" (ex.: aplicados pelo botao "Aplicar" das
        # sugestoes de melhoria, painel > Sistema): mesmo formato do vocabulario.yaml, escrito pelo programa.
        self._troca: dict[str, str] = {}
        for oficial, jeitos in list(SINONIMOS_EMBUTIDOS.items()) + list((v.get("sinonimos") or {}).items()) \
                + list((self.aprendido.get("sinonimos") or {}).items()):
            for jeito in [oficial] + list(jeitos or []):
                self._troca[normalizar(jeito)] = normalizar(oficial)
        alternativas = _alternativas(self._troca)
        self._re_sinonimos = re.compile(rf"\b(?:{alternativas})\b") if alternativas else None

        atalhos = dict(v.get("atalhos") or {})
        atalhos.update(self.aprendido.get("atalhos") or {})
        self.atalhos = {self._traduzir_sem_atalho(k): normalizar(c) for k, c in atalhos.items()}

    # -----------------------------------------------------------------
    def _traduzir_sem_atalho(self, frase: str) -> str:
        t = normalizar(frase)
        if self._re_qualquer:
            t = self._re_qualquer.sub(" ", t)
        t = re.sub(r"\s+", " ", t).strip()
        if self._re_inicio:
            anterior = None
            while anterior != t:  # tira varios enfeites seguidos
                anterior = t
                t = self._re_inicio.sub("", t).strip()
        if self._re_sinonimos:
            t = self._re_sinonimos.sub(lambda m: self._troca[m.group(0)], t)
        return re.sub(r"\s+", " ", t).strip()

    def traduzir(self, frase: str) -> str:
        """'po, bota ai o youtube pra mim' -> 'abre o youtube'"""
        t = self._traduzir_sem_atalho(frase)
        if t in self.atalhos:
            return self.atalhos[t]
        parecido = difflib.get_close_matches(t, list(self.atalhos), n=1, cutoff=0.85)
        return self.atalhos[parecido[0]] if parecido else t

    def jeitos_de(self, oficial: str) -> list[str]:
        """Todos os jeitos de falar uma forma oficial, do mais longo ao mais curto."""
        oficial = normalizar(oficial)
        jeitos = [j for j, o in self._troca.items() if o == oficial] or [oficial]
        return sorted(jeitos, key=len, reverse=True)

    # --- O que o Mestre aprende por voz ----------------------------------
    def aprender_atalho(self, frase: str, comando: str) -> None:
        self.aprendido.setdefault("atalhos", {})[normalizar(frase)] = normalizar(comando)
        self.salvar_aprendido()

    def esquecer_atalho(self, frase: str) -> bool:
        atalhos = self.aprendido.get("atalhos") or {}
        chave = difflib.get_close_matches(normalizar(frase), list(atalhos), n=1, cutoff=0.75)
        if not chave:
            return False
        del atalhos[chave[0]]
        self.salvar_aprendido()
        return True

    # --- Botao "Aplicar" das sugestoes de melhoria (vocabulario/sinonimo, sem IA) -----------
    def pode_aplicar_sinonimo(self, jeito: str, oficial: str, protegidas=()) -> tuple[bool, str]:
        """Confere se da para trocar "jeito" por "oficial" sem quebrar comandos. Nao muda nada."""
        jeito, oficial = normalizar(jeito), normalizar(oficial)
        if not jeito or not oficial:
            return False, "Palavra vazia: não dá para aplicar."
        if len(jeito) < 3:
            return False, f"“{jeito}” é curta demais (menos de 3 letras): poderia trocar palavras demais sem querer."
        if jeito == oficial:
            return False, "Já é a própria palavra: não há troca para fazer."
        if jeito in {normalizar(p) for p in protegidas}:
            return False, f"“{jeito}” é a palavra de ativação: não posso trocar o que ela significa."
        if jeito in self._troca:
            atual = self._troca[jeito]
            if atual == oficial:
                return False, "Essa troca já existe no vocabulário."
            return False, f"“{jeito}” já é sinônimo de “{atual}”: apague essa troca antes, se quiser mudar."
        return True, ""

    def aplicar_sinonimo(self, jeito: str, oficial: str, protegidas=()) -> tuple[bool, str]:
        """Grava "jeito" como sinonimo de "oficial" em aprendido.yaml (escrito pelo programa).

        Confere antes com pode_aplicar_sinonimo; devolve (aplicou, mensagem)."""
        pode, motivo = self.pode_aplicar_sinonimo(jeito, oficial, protegidas)
        if not pode:
            return False, motivo
        jeito, oficial = normalizar(jeito), normalizar(oficial)
        lista = self.aprendido.setdefault("sinonimos", {}).setdefault(oficial, [])
        if jeito not in lista:
            lista.append(jeito)
        self.salvar_aprendido()
        return True, f"“{jeito}” agora vira “{oficial}”."

    def desfazer_sinonimo(self, jeito: str, oficial: str) -> bool:
        """Desfaz um aplicar_sinonimo (tira "jeito" da lista de "oficial" em aprendido.yaml)."""
        jeito, oficial = normalizar(jeito), normalizar(oficial)
        lista = (self.aprendido.get("sinonimos") or {}).get(oficial)
        if not lista or jeito not in lista:
            return False
        lista.remove(jeito)
        if not lista:
            del self.aprendido["sinonimos"][oficial]
        self.salvar_aprendido()
        return True

    def preferencia(self, nome: str, padrao=None):
        return (self.aprendido.get("preferencias") or {}).get(nome, padrao)

    def salvar_preferencia(self, nome: str, valor) -> None:
        self.aprendido.setdefault("preferencias", {})[nome] = valor
        self.salvar_aprendido()

    def salvar_aprendido(self) -> None:
        with open(ARQUIVO_APRENDIDO, "w", encoding="utf-8") as f:
            f.write("# Escrito pelo Mestre quando voce ensina algo por voz.\n"
                    "# Pode editar ou apagar linhas; para zerar tudo, apague o arquivo.\n")
            yaml.safe_dump(self.aprendido, f, allow_unicode=True, sort_keys=True)
        self.recarregar()


def atalhos_no_disco() -> dict:
    """So os atalhos aprendidos gravados AGORA no aprendido.yaml (sem instanciar Vocabulario).

    Usado pelo painel ao salvar, pra nao apagar um atalho que voce ensinou por voz enquanto
    o painel estava aberto (o painel so tinha, em memoria, a foto de quando abriu).
    """
    return dict(_ler_yaml(ARQUIVO_APRENDIDO).get("atalhos") or {})


def combina(texto: str, frase: str, minimo: float = 0.8) -> bool:
    """A frase aparece no texto, mesmo com pequenas diferencas de pronuncia?

    'bora trabalhar agora' combina com 'bora trabalhar'
    'bora trabalha'        combina com 'bora trabalhar'
    """
    t, f = normalizar(texto), normalizar(frase)
    if not f:
        return False
    if re.search(rf"\b{re.escape(f)}\b", t):
        return True
    if len(f) < 8:  # frases curtas: so vale igualzinho (evita "dia" parecer "da")
        return False
    palavras_t = t.split()
    palavras_f = f.split()
    n = len(palavras_f)
    for i in range(len(palavras_t) - n + 1):
        trecho = " ".join(palavras_t[i:i + n])
        if difflib.SequenceMatcher(None, trecho, f).ratio() >= minimo:
            return True
    return False
