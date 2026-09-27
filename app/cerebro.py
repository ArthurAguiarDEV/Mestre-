"""Cerebro do Mestre: responde perguntas livres usando um "perfil".

Um perfil e uma pasta dentro de perfis/ com:
  instrucoes.md   -> como o assistente deve se comportar (o "prompt")
  conhecimento/   -> arquivos .md ou .txt com informacoes de apoio
"""
import json
import logging

from . import memoria
from .config import PASTA_PERFIS

log = logging.getLogger(__name__)

ORIENTACAO_VOZ = (
    "\n\n# Forma de responder\n"
    "Voce esta sendo usado por VOZ em um assistente pessoal no Windows. "
    "Responda sempre em portugues do Brasil. Comece com a resposta direta em uma ou duas "
    "frases curtas, faceis de ouvir. Se precisar de detalhes (listas, passos, textos de "
    "chamado), coloque depois: eles serao mostrados na tela."
)

MAX_TURNOS_MEMORIA = 6


INTERPRETADOR = (
    "Voce e o interpretador de comandos de um assistente de voz no Windows. "
    "O usuario fala de um jeito solto e informal; a transcricao pode ter erros. "
    "Decida entre tres saidas:\n"
    '1. Se for um PEDIDO DE ACAO que algum comando da lista faz: {{"tipo": "comando", "texto": "<o comando, no formato da lista>"}}\n'
    "   Prefira SEMPRE esta saida quando der para entender a acao, mesmo com erros de transcricao.\n"
    '2. So se for uma acao da lista mas faltar algo ESSENCIAL (qual de dois alvos, por exemplo) ou for arriscada '
    '(desligar o PC, fechar tudo, apagar): {{"tipo": "pergunta", "texto": "<pergunta curta para o usuario>"}}\n'
    '3. Se for conversa ou pergunta: {{"tipo": "resposta", "texto": "<resposta curta, falada, com esta personalidade: {personalidade}>"}}\n'
    "Responda SOMENTE com o JSON.\n\n{comandos}"
)
ESQUEMA = {
    "type": "object",
    "properties": {"tipo": {"type": "string", "enum": ["comando", "pergunta", "resposta"]}, "texto": {"type": "string"}},
    "required": ["tipo", "texto"],
    "additionalProperties": False,
}
ESQUEMA_OPCOES = {
    "type": "object",
    "properties": {"opcoes": {"type": "array", "items": {
        "type": "object",
        "properties": {"titulo": {"type": "string"}, "resumo": {"type": "string"},
                       "passos": {"type": "array", "items": {"type": "string"}}},
        "required": ["titulo", "resumo", "passos"], "additionalProperties": False}}},
    "required": ["opcoes"],
    "additionalProperties": False,
}
PROPOR = (
    "Voce ajuda o usuario a comecar um projeto novo. Com base nas respostas dele, proponha EXATAMENTE 3 "
    "caminhos diferentes (do mais simples ao mais ambicioso). Para cada um: um titulo curto (ate 6 palavras), "
    "um resumo de uma frase e de 3 a 5 primeiros passos praticos. Portugues do Brasil, linguagem simples. "
    "Responda SOMENTE com o JSON."
)
VARIACOES = (
    "Voce ajuda um assistente de voz brasileiro. O usuario gravou uma ROTINA (uma sequencia de comandos) e escolheu "
    "uma frase para chamar. Escreva {n} jeitos DIFERENTES e naturais de pedir essa mesma rotina FALANDO, em portugues "
    "do Brasil informal: girias ('bora', 'partiu', 'manda ver', 'solta'), jeitos de pedir ('pode', 'quero', 'vamos'), "
    "com e sem artigo. Frases curtas (2 a 6 palavras), sem pontuacao, sem o nome do assistente. Mantenha o sentido da "
    "frase e NAO descreva os passos (nada de 'abre o X' ou 'toca Y'). Responda SOMENTE com o JSON."
)
ESQUEMA_VARIACOES = {
    "type": "object",
    "properties": {"frases": {"type": "array", "items": {"type": "string"}}},
    "required": ["frases"],
    "additionalProperties": False,
}
PERSONALIDADE_PADRAO = ("parceiro brasileiro, bem-humorado e informal; fala curto, "
                        "usa girias leves como 'beleza', 'ja e', 'bora' e chama o usuario de {apelido}")


def carregar_perfil(nome: str) -> str:
    pasta = PASTA_PERFIS / nome
    partes = []
    instrucoes = pasta / "instrucoes.md"
    if instrucoes.exists():
        partes.append(instrucoes.read_text(encoding="utf-8"))
    conhecimento = pasta / "conhecimento"
    if conhecimento.exists():
        for arquivo in sorted(conhecimento.iterdir()):
            if arquivo.suffix.lower() in (".md", ".txt"):
                partes.append(f"\n\n# Conhecimento: {arquivo.name}\n" + arquivo.read_text(encoding="utf-8"))
    return "\n".join(partes) + ORIENTACAO_VOZ


class Cerebro:
    def __init__(self, cfg: dict):
        c = cfg.get("cerebro", {})
        self.tipo = c.get("tipo", "nenhum")
        self.cfg = c
        from .personalidades import descricao_efetiva

        p = cfg.get("personalidade") or {}
        a = cfg.get("assistente") or {}
        descricao = descricao_efetiva(p)
        nome, apelido = a.get("nome") or "Mestre", a.get("apelido_usuario") or "chefe"
        # Deixa claro quem e quem (ex.: ele = "Assessor", voce = "Mestre": ele nao pode se chamar de Mestre)
        self.personalidade = (str(descricao).replace("{nome}", nome).replace("{apelido}", apelido)
                              + f". Seu nome e {nome}. O usuario (a pessoa que fala com voce) se chama {apelido}"
                              + (f": chame o usuario de {apelido}, nunca de {nome}" if nome.lower() != apelido.lower() else ""))
        # A conversa continua depois de reiniciar (memoria/conversa.json)
        self._historico: dict[str, list] = memoria.carregar_conversa()
        self._claude = None

    @property
    def ligado(self) -> bool:
        return self.tipo in ("ollama", "claude")

    def perguntar(self, pergunta: str, perfil: str = "geral") -> str:
        sistema = carregar_perfil(perfil)
        if perfil == "geral":
            sistema += f"\nSua personalidade: {self.personalidade}." + memoria.texto_para_ia()
        historico = self._historico.setdefault(perfil, [])
        historico.append({"role": "user", "content": pergunta})
        try:
            if self.tipo == "ollama":
                resposta = self._ollama(sistema, historico)
            elif self.tipo == "claude":
                resposta = self._claude_api(sistema, historico)
            else:
                resposta = "Meu cerebro esta desligado. Ative no arquivo de configuracao."
        except Exception as erro:
            historico.pop()
            log.exception("Erro no cerebro")
            return f"Tive um problema para pensar na resposta: {erro}"
        historico.append({"role": "assistant", "content": resposta})
        del historico[:-MAX_TURNOS_MEMORIA * 2]
        memoria.salvar_conversa(self._historico)
        return resposta

    def interpretar(self, frase: str, comandos: str) -> dict:
        """Transforma uma frase solta em {"tipo": "comando"|"pergunta"|"resposta", "texto": ...}."""
        sistema = INTERPRETADOR.format(personalidade=self.personalidade, comandos=comandos) + memoria.texto_para_ia()
        mensagens = [{"role": "user", "content": frase}]
        try:
            if self.tipo == "ollama":
                bruto = self._ollama(sistema, mensagens, formato=ESQUEMA)
            else:
                bruto = self._claude_api(sistema, mensagens, formato=ESQUEMA)
            decisao = json.loads(bruto[bruto.find("{"):bruto.rfind("}") + 1])
            if decisao.get("tipo") in ("comando", "pergunta", "resposta"):
                return decisao
        except Exception:
            log.exception("A IA nao conseguiu interpretar")
        return {"tipo": "resposta", "texto": ""}

    def esquecer(self) -> None:
        self._historico.clear()
        memoria.salvar_conversa({})

    def propor_opcoes(self, pedido: str) -> list[dict]:
        """3 caminhos para um projeto: [{"titulo", "resumo", "passos": [...]}, ...]"""
        mensagens = [{"role": "user", "content": pedido}]
        try:
            if self.tipo == "ollama":
                bruto = self._ollama(PROPOR + memoria.texto_para_ia(), mensagens, formato=ESQUEMA_OPCOES)
            else:
                bruto = self._claude_api(PROPOR, mensagens, formato=ESQUEMA_OPCOES)
            opcoes = json.loads(bruto[bruto.find("{"):bruto.rfind("}") + 1]).get("opcoes") or []
            return [o for o in opcoes if o.get("titulo")][:3]
        except Exception:
            log.exception("A IA nao conseguiu propor opcoes")
            return []

    def variacoes_de_frase(self, frase: str, passos: str = "", n: int = 50) -> list[str]:
        """Jeitos naturais de pedir a mesma rotina (a "rotina ensinada falando"). Falhou: lista vazia."""
        pedido = f"Frase escolhida: {frase}" + (f". O que a rotina faz: {passos}" if passos else "")
        mensagens = [{"role": "user", "content": pedido}]
        try:
            sistema = VARIACOES.format(n=n)
            if self.tipo == "ollama":
                bruto = self._ollama(sistema, mensagens, formato=ESQUEMA_VARIACOES)
            else:
                bruto = self._claude_api(sistema, mensagens, formato=ESQUEMA_VARIACOES)
            frases = json.loads(bruto[bruto.find("{"):bruto.rfind("}") + 1]).get("frases") or []
            return [str(f) for f in frases if str(f).strip()]
        except Exception:
            log.exception("A IA nao conseguiu criar variacoes da frase")
            return []

    # --- Deixar a IA "quente" (o Ollama demora so na PRIMEIRA pergunta) ------
    def aquecer(self) -> None:
        """Carrega o modelo do Ollama na memoria ao ligar o Mestre (roda em segundo plano)."""
        if self.tipo != "ollama":
            return
        try:
            import requests

            requests.post(f"{self.cfg.get('ollama_url', 'http://localhost:11434')}/api/generate",
                          json={"model": self.cfg.get("ollama_modelo", "qwen2.5:7b"), "keep_alive": "60m"},
                          timeout=180)
            log.info("IA aquecida (modelo carregado)")
        except Exception as erro:
            log.warning("Nao consegui aquecer o Ollama: %s", erro)

    def modelos_instalados(self) -> list[str]:
        return modelos_do_ollama(self.cfg.get("ollama_url", "http://localhost:11434"))

    # --- Ollama: IA local e gratis ---------------------------------------
    def _ollama(self, sistema: str, historico: list, formato: dict | None = None) -> str:
        import requests

        r = requests.post(
            f"{self.cfg.get('ollama_url', 'http://localhost:11434')}/api/chat",
            json={
                "model": self.cfg.get("ollama_modelo", "qwen2.5:7b"),
                "messages": [{"role": "system", "content": sistema}] + historico,
                "stream": False,
                "keep_alive": "60m",   # fica carregado: as proximas respostas saem mais rapido
                **({"format": formato} if formato else {}),
            },
            timeout=float(self.cfg.get("tempo_maximo", 120)),   # depois disso desiste (painel > Conversa)
        )
        r.raise_for_status()
        return r.json()["message"]["content"].strip()

    # --- Claude via API (pago por uso) ------------------------------------
    def _claude_api(self, sistema: str, historico: list, formato: dict | None = None) -> str:
        import anthropic

        if self._claude is None:
            # A chave vem da variavel de ambiente ANTHROPIC_API_KEY (veja o guia).
            self._claude = anthropic.Anthropic()
        resposta = self._claude.beta.messages.create(
            model=self.cfg.get("claude_modelo", "claude-opus-5"),
            max_tokens=16000,
            system=sistema,
            messages=historico,
            output_config={
                "effort": self.cfg.get("claude_esforco", "low"),
                **({"format": {"type": "json_schema", "schema": formato}} if formato else {}),
            },
            # Se o modelo principal recusar, o servidor tenta outro modelo automaticamente.
            betas=["server-side-fallback-2026-07-01"],
            extra_body={"fallbacks": "default"},
        )
        if resposta.stop_reason == "refusal":
            return "O Claude preferiu nao responder a essa pergunta."
        return "".join(b.text for b in resposta.content if b.type == "text").strip()


def modelos_do_ollama(url: str = "http://localhost:11434") -> list[str]:
    """Modelos baixados no Ollama deste PC (lista vazia se o Ollama nao estiver aberto)."""
    try:
        import requests

        r = requests.get(f"{url}/api/tags", timeout=3)
        return sorted(m["name"] for m in r.json().get("models", []))
    except Exception:
        return []
