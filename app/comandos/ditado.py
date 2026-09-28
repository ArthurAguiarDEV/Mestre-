"""Ditado longo (destinos ipm/projeto/salvar/nota/copiar), revisao, agente IPM e area de transferencia.

Mixin do Executor (app/comandos/__init__.py): os metodos usam self.voz, self.cfg, self.falar...
do nucleo e chamam metodos dos outros mixins pelo self.
"""
import random
import re
import threading
import time
from datetime import datetime
from urllib.parse import quote
from .. import estado, sistema
from ..config import PASTA_NOTAS
from ..texto import contem, normalizar

from .base import (
    ARQUIVO_REVISAO, TERMINAR_DITADO, PRONTO_SOZINHO, LINK_PROJETO_PADRAO, CABECALHO_PROJETO, _quantos,
)


class DitadoMixin:
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
