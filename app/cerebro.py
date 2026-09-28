"""Cerebro do Mestre: responde perguntas livres usando um "perfil".

Um perfil e uma pasta dentro de perfis/ com:
  instrucoes.md   -> como o assistente deve se comportar (o "prompt")
  conhecimento/   -> arquivos .md ou .txt com informacoes de apoio
"""
import json
import logging
import os
import threading
import time

from . import memoria
from .config import PASTA_PERFIS

log = logging.getLogger(__name__)

# --- Troca de IA sozinho (painel > Conversa > "Troca de IA sozinho") -----------------------
# Lista ORDENADA de opcoes de IA: se a primeira demorar (`timeout_tentativa_seg`) ou der erro,
# tenta a proxima. Quem falhar fica "de castigo" por `penalidade_min` (nao e tentada de novo ate
# passar esse tempo). Config antiga (sem essas chaves): usa os padroes abaixo.
ROTULOS_OPCOES_IA = {
    "ollama": "Ollama (modelo principal)",
    "ollama_menor": "Ollama (modelo menor)",
    "claude": "Claude API",
    "groq": "Groq (nuvem, grátis)",
    "cerebras": "Cerebras (nuvem, grátis)",
    "openrouter": "OpenRouter (nuvem, grátis)",
    "gemini": "Google Gemini (nuvem, grátis)",
}
ORDEM_IA_PADRAO = ["ollama", "ollama_menor", "claude"]
TIMEOUT_TENTATIVA_PADRAO = 30
PENALIDADE_MIN_PADRAO = 30

# --- IAs gratis na nuvem (opcionais, DESLIGADAS por padrao; chave em app/segredos.py) -----
# Todas em formato de API compativel com a OpenAI (menos o Gemini, que usa a API REST propria
# do Google AI Studio). O usuario cria a chave gratis no site de cada uma (painel > Conversa).
NUVEM_URL_BASE = {
    "groq": "https://api.groq.com/openai/v1",
    "cerebras": "https://api.cerebras.ai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}
NUVEM_MODELO_PADRAO = {
    "groq": "llama-3.3-70b-versatile",
    "cerebras": "llama-3.3-70b",
    "openrouter": "meta-llama/llama-3.3-70b-instruct:free",
    "gemini": "gemini-2.5-flash",
}
NUVEM_SITE_CHAVE = {
    "groq": "https://console.groq.com/keys",
    "cerebras": "https://cloud.cerebras.ai/",
    "openrouter": "https://openrouter.ai/keys",
    "gemini": "https://aistudio.google.com/apikey",
}
GEMINI_TEXTOS_LONGOS_PADRAO = 400   # painel > Conversa: acima disso (chars), prefere o Gemini se estiver ligado

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
ESQUEMA_ASSUNTO = {
    "type": "object",
    "properties": {"assunto": {"type": "string"}},
    "required": ["assunto"],
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
        self._castigo: dict[str, float] = {}   # id da opcao -> ate quando (time.time()) fica de castigo
        self._trava_castigo = threading.Lock()
        self.ultima_ia_respondeu = ""   # qual opcao respondeu de fato pela ultima vez (log/depuracao)

    @property
    def ligado(self) -> bool:
        return self.tipo in ("ollama", "claude")

    def _limite_contexto_kb(self) -> float:
        """Tamanho maximo (fatos + indice) mandado para a IA. Config antiga sem essa chave: usa o padrao."""
        return float(self.cfg.get("memoria_contexto_kb", memoria.LIMITE_CONTEXTO_PADRAO_KB))

    # --- Troca de IA sozinho: lista ordenada + castigo ---------------------------------
    def _opcoes_ia(self) -> list[dict]:
        """Lista ordenada (painel > Conversa > ordem_ia) das opcoes de IA REALMENTE configuradas:
        Ollama menor so entra se tiver um modelo escolhido; Claude so entra se tiver chave; as IAs
        na nuvem (Groq/Cerebras/OpenRouter/Gemini) so entram se estiverem LIGADAS e com chave."""
        from . import segredos

        modelo_menor = str(self.cfg.get("ollama_modelo_menor", "")).strip()
        tem_claude = bool(segredos.ler("claude_chave")) or bool(os.environ.get("ANTHROPIC_API_KEY"))
        disponiveis = {
            "ollama": {"id": "ollama", "rotulo": ROTULOS_OPCOES_IA["ollama"], "chamar": self._ollama,
                      "modelo": self.cfg.get("ollama_modelo", "qwen2.5:7b")},
            "ollama_menor": ({"id": "ollama_menor", "rotulo": ROTULOS_OPCOES_IA["ollama_menor"],
                             "chamar": self._ollama, "modelo": modelo_menor} if modelo_menor else None),
            "claude": ({"id": "claude", "rotulo": ROTULOS_OPCOES_IA["claude"], "chamar": self._claude_api,
                       "modelo": None} if tem_claude else None),
        }
        for id_ in ("groq", "cerebras", "openrouter", "gemini"):
            ligado = bool(self.cfg.get(f"{id_}_ligado", False))
            chave = segredos.ler(f"{id_}_chave")
            chamar = ((lambda s, h, formato=None, modelo=None, timeout=None, _id=id_:
                       self._gemini(s, h, formato=formato, modelo=modelo, timeout=timeout, provedor=_id))
                      if id_ == "gemini" else
                      (lambda s, h, formato=None, modelo=None, timeout=None, _id=id_:
                       self._nuvem_openai(_id, s, h, formato=formato, modelo=modelo, timeout=timeout)))
            disponiveis[id_] = ({"id": id_, "rotulo": ROTULOS_OPCOES_IA[id_], "chamar": chamar,
                                 "modelo": self.cfg.get(f"{id_}_modelo", NUVEM_MODELO_PADRAO[id_])}
                                if (ligado and chave) else None)
        vistos: set[str] = set()
        opcoes = []
        for id_ in (self.cfg.get("ordem_ia") or ORDEM_IA_PADRAO):
            if id_ in vistos:
                continue
            vistos.add(id_)
            op = disponiveis.get(id_)
            if op:
                opcoes.append(op)
        # IAs na nuvem ligadas mas que nao estao na ordem configurada (config antiga): vao no fim.
        for id_, op in disponiveis.items():
            if op and id_ not in vistos:
                vistos.add(id_)
                opcoes.append(op)
        return opcoes

    def _tentar_opcoes(self, sistema: str, historico: list, formato: dict | None = None,
                       preferir: str | None = None) -> str:
        """Tenta cada IA da lista na ordem configurada: pula quem esta de castigo, chama com o
        tempo limite por tentativa e poe de castigo quem falhar ou estourar o tempo. Registra no
        log qual respondeu de fato. `preferir` (ex.: "gemini" em textos longos) tenta antes das outras,
        se estiver disponivel."""
        opcoes = self._opcoes_ia()
        if not opcoes:
            raise RuntimeError("Nenhuma IA configurada")
        if preferir:
            opcoes = sorted(opcoes, key=lambda o: o["id"] != preferir)
        timeout = float(self.cfg.get("timeout_tentativa_seg", TIMEOUT_TENTATIVA_PADRAO))
        penalidade_min = float(self.cfg.get("penalidade_min", PENALIDADE_MIN_PADRAO))
        agora = time.time()
        erro_final: Exception | None = None
        for op in opcoes:
            with self._trava_castigo:
                liberado_em = self._castigo.get(op["id"], 0.0)
            if liberado_em > agora:
                log.info("IA de castigo, pulando %s (libera em %ds)", op["rotulo"], int(liberado_em - agora))
                continue
            try:
                resultado = op["chamar"](sistema, historico, formato=formato, modelo=op["modelo"], timeout=timeout)
                with self._trava_castigo:
                    self._castigo.pop(op["id"], None)
                self.ultima_ia_respondeu = op["rotulo"]
                log.info("IA que respondeu: %s", op["rotulo"])
                return resultado
            except Exception as erro:
                erro_final = erro
                with self._trava_castigo:
                    self._castigo[op["id"]] = time.time() + penalidade_min * 60
                log.warning("IA falhou (de castigo por %d min): %s (%s)", penalidade_min, op["rotulo"], erro)
        raise erro_final or RuntimeError("Nenhuma IA respondeu")

    def _preferir_para(self, texto: str) -> str | None:
        """Textos longos: prefere o Gemini (se estiver ligado) antes das outras opcoes da lista."""
        limite = int(self.cfg.get("gemini_textos_longos_chars", GEMINI_TEXTOS_LONGOS_PADRAO))
        if self.cfg.get("gemini_ligado") and limite > 0 and len(texto or "") > limite:
            return "gemini"
        return None

    def perguntar(self, pergunta: str, perfil: str = "geral") -> str:
        sistema = carregar_perfil(perfil)
        if perfil == "geral":
            sistema += f"\nSua personalidade: {self.personalidade}." + memoria.texto_para_ia(
                pergunta, self._limite_contexto_kb())
        historico = self._historico.setdefault(perfil, [])
        historico.append({"role": "user", "content": pergunta})
        try:
            if self.ligado:
                resposta = self._tentar_opcoes(sistema, historico, preferir=self._preferir_para(pergunta))
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
        sistema = (INTERPRETADOR.format(personalidade=self.personalidade, comandos=comandos)
                  + memoria.texto_para_ia(frase, self._limite_contexto_kb()))
        mensagens = [{"role": "user", "content": frase}]
        try:
            bruto = self._tentar_opcoes(sistema, mensagens, formato=ESQUEMA)
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
        sistema = PROPOR + memoria.texto_para_ia(pedido, self._limite_contexto_kb())
        try:
            bruto = self._tentar_opcoes(sistema, mensagens, formato=ESQUEMA_OPCOES)
            opcoes = json.loads(bruto[bruto.find("{"):bruto.rfind("}") + 1]).get("opcoes") or []
            return [o for o in opcoes if o.get("titulo")][:3]
        except Exception:
            log.exception("A IA nao conseguiu propor opcoes")
            return []

    def sugerir_assunto(self, fato: str, assuntos: list[str]) -> str:
        """2a opiniao (opcional) sobre em qual arquivo de memoria/fatos/ um fato deve ficar: a
        classificacao por palavra-chave (memoria.classificar_assunto) ja funciona sozinha; isto so
        roda quando a IA esta ligada, em segundo plano, e pode mover o fato se discordar."""
        mensagens = [{"role": "user", "content": f'Fato: "{fato}"'}]
        sistema = ("Escolha, entre estes assuntos, o que melhor descreve o fato a seguir: "
                  + ", ".join(assuntos) + '. Responda SOMENTE com o JSON {"assunto": "<um da lista>"}.')
        try:
            bruto = self._tentar_opcoes(sistema, mensagens, formato=ESQUEMA_ASSUNTO)
            assunto = str(json.loads(bruto[bruto.find("{"):bruto.rfind("}") + 1]).get("assunto", "")).strip().lower()
            return assunto if assunto in assuntos else ""
        except Exception:
            log.exception("A IA nao conseguiu sugerir o assunto do fato")
            return ""

    def variacoes_de_frase(self, frase: str, passos: str = "", n: int = 50) -> list[str]:
        """Jeitos naturais de pedir a mesma rotina (a "rotina ensinada falando"). Falhou: lista vazia."""
        pedido = f"Frase escolhida: {frase}" + (f". O que a rotina faz: {passos}" if passos else "")
        mensagens = [{"role": "user", "content": pedido}]
        try:
            sistema = VARIACOES.format(n=n)
            bruto = self._tentar_opcoes(sistema, mensagens, formato=ESQUEMA_VARIACOES)
            frases = json.loads(bruto[bruto.find("{"):bruto.rfind("}") + 1]).get("frases") or []
            return [str(f) for f in frases if str(f).strip()]
        except Exception:
            log.exception("A IA nao conseguiu criar variacoes da frase")
            return []

    # --- Deixar a IA "quente" (o Ollama demora so na PRIMEIRA pergunta) ------
    def aquecer(self) -> None:
        """Carrega o(s) modelo(s) do Ollama na memoria ao ligar o Mestre (roda em segundo plano)."""
        if self.tipo != "ollama":
            return
        import requests

        url = self.cfg.get("ollama_url", "http://localhost:11434")
        for modelo in filter(None, (self.cfg.get("ollama_modelo", "qwen2.5:7b"),
                                    str(self.cfg.get("ollama_modelo_menor", "")).strip())):
            try:
                requests.post(f"{url}/api/generate", json={"model": modelo, "keep_alive": "60m"}, timeout=180)
                log.info("IA aquecida (modelo %s carregado)", modelo)
            except Exception as erro:
                log.warning("Nao consegui aquecer o Ollama (%s): %s", modelo, erro)

    def modelos_instalados(self) -> list[str]:
        return modelos_do_ollama(self.cfg.get("ollama_url", "http://localhost:11434"))

    # --- Ollama: IA local e gratis ---------------------------------------
    def _ollama(self, sistema: str, historico: list, formato: dict | None = None, modelo: str | None = None,
               timeout: float | None = None) -> str:
        import requests

        r = requests.post(
            f"{self.cfg.get('ollama_url', 'http://localhost:11434')}/api/chat",
            json={
                "model": modelo or self.cfg.get("ollama_modelo", "qwen2.5:7b"),
                "messages": [{"role": "system", "content": sistema}] + historico,
                "stream": False,
                "keep_alive": "60m",   # fica carregado: as proximas respostas saem mais rapido
                **({"format": formato} if formato else {}),
            },
            # depois disso desiste (por padrao) desta opcao e tenta a proxima da lista (painel > Conversa)
            timeout=float(timeout if timeout is not None else self.cfg.get("tempo_maximo", 120)),
        )
        r.raise_for_status()
        return r.json()["message"]["content"].strip()

    # --- Claude via API (pago por uso) ------------------------------------
    def _claude_api(self, sistema: str, historico: list, formato: dict | None = None, modelo: str | None = None,
                    timeout: float | None = None) -> str:
        import anthropic

        from . import segredos

        if self._claude is None:
            # A chave vem de segredos.json (painel > Conversa) ou da variavel ANTHROPIC_API_KEY (veja o guia).
            chave = segredos.ler("claude_chave")
            self._claude = anthropic.Anthropic(api_key=chave) if chave else anthropic.Anthropic()
        resposta = self._claude.beta.messages.create(
            model=modelo or self.cfg.get("claude_modelo", "claude-opus-5"),
            max_tokens=16000,
            system=sistema,
            messages=historico,
            timeout=float(timeout) if timeout is not None else anthropic.NOT_GIVEN,
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

    # --- IAs gratis na nuvem (opcionais) -----------------------------------
    def _nuvem_openai(self, provedor: str, sistema: str, historico: list, formato: dict | None = None,
                      modelo: str | None = None, timeout: float | None = None) -> str:
        """Groq, Cerebras e OpenRouter: mesmo formato de API da OpenAI (/chat/completions)."""
        import requests

        from . import segredos

        chave = segredos.ler(f"{provedor}_chave")
        if not chave:
            raise RuntimeError(f"Sem chave configurada para {provedor}")
        url = self.cfg.get(f"{provedor}_url", NUVEM_URL_BASE[provedor])
        corpo = {
            "model": modelo or self.cfg.get(f"{provedor}_modelo", NUVEM_MODELO_PADRAO[provedor]),
            "messages": [{"role": "system", "content": sistema}] + historico,
        }
        if formato:
            corpo["response_format"] = {"type": "json_object"}
        r = requests.post(f"{url}/chat/completions", headers={"Authorization": f"Bearer {chave}"}, json=corpo,
                          timeout=float(timeout) if timeout is not None else self.cfg.get("tempo_maximo", 120))
        r.raise_for_status()   # 429 (limite gratis estourado) ou outro erro: vai pra proxima opcao da lista
        return r.json()["choices"][0]["message"]["content"].strip()

    def _gemini(self, sistema: str, historico: list, formato: dict | None = None, modelo: str | None = None,
               timeout: float | None = None, provedor: str = "gemini") -> str:
        """Google Gemini (AI Studio, gratis): API REST propria (generateContent), nao e formato OpenAI."""
        import requests

        from . import segredos

        chave = segredos.ler("gemini_chave")
        if not chave:
            raise RuntimeError("Sem chave configurada para o Gemini")
        modelo = modelo or self.cfg.get("gemini_modelo", NUVEM_MODELO_PADRAO["gemini"])
        contents = [{"role": "model" if h.get("role") == "assistant" else "user",
                    "parts": [{"text": h.get("content", "")}]} for h in historico]
        corpo = {"system_instruction": {"parts": [{"text": sistema}]}, "contents": contents}
        if formato:
            corpo["generationConfig"] = {"responseMimeType": "application/json"}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
        r = requests.post(url, params={"key": chave}, json=corpo,
                          timeout=float(timeout) if timeout is not None else self.cfg.get("tempo_maximo", 120))
        r.raise_for_status()
        dados = r.json()
        candidatos = dados.get("candidates") or []
        if not candidatos:
            raise RuntimeError(f"Gemini nao respondeu: {dados.get('promptFeedback') or dados}")
        partes = candidatos[0].get("content", {}).get("parts") or []
        return "".join(p.get("text", "") for p in partes).strip()


# --- Baixar um modelo menor do Ollama (painel > Conversa > "Baixar modelo menor") -------------
MODELOS_MENORES = {"qwen3:8b": "~5 GB, bom equilíbrio", "phi4-mini": "~2,5 GB, mais leve"}


def ollama_instalado() -> bool:
    """O programa `ollama` esta no PATH do Windows (independente do servidor estar rodando)."""
    import shutil
    return shutil.which("ollama") is not None


def baixar_modelo_ollama(modelo: str, url: str = "http://localhost:11434", progresso=None) -> str:
    """Baixa um modelo do Ollama (equivalente a `ollama pull <modelo>`) usando a API HTTP dele, que
    manda o progresso linha a linha. Chame numa THREAD (pode demorar minutos). `progresso(texto)` e
    chamado a cada atualizacao. Devolve "" se deu certo, ou uma mensagem de erro."""
    import requests

    try:
        r = requests.post(f"{url}/api/pull", json={"model": modelo}, stream=True, timeout=(10, 1800))
        r.raise_for_status()
        for linha in r.iter_lines():
            if not linha:
                continue
            try:
                d = json.loads(linha)
            except ValueError:
                continue
            if d.get("error"):
                return str(d["error"])
            if progresso:
                total, completo = d.get("total"), d.get("completed")
                if total and completo:
                    progresso(f"{d.get('status', 'baixando')} ({completo / total * 100:.0f}%)")
                else:
                    progresso(str(d.get("status", "")))
        return ""
    except Exception as erro:
        return str(erro)


def modelos_do_ollama(url: str = "http://localhost:11434") -> list[str]:
    """Modelos baixados no Ollama deste PC (lista vazia se o Ollama nao estiver aberto)."""
    try:
        import requests

        r = requests.get(f"{url}/api/tags", timeout=3)
        return sorted(m["name"] for m in r.json().get("models", []))
    except Exception:
        return []
