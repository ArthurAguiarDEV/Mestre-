"""Rotinas do config.yaml e rotina ensinada falando (gravar passos, frase de chamar).

Mixin do Executor (app/comandos/__init__.py): os metodos usam self.voz, self.cfg, self.falar...
do nucleo e chamam metodos dos outros mixins pelo self.
"""
import logging
import random
import re
import time
from datetime import datetime
from .. import informacoes, memoria, sistema
from ..texto import achar_numero, normalizar
from ..vocabulario import combina

from .base import (
    DIAS, MESES, ROTINA_VERBOS, FIM_ROTINA, CANCELA_ROTINA, NAO_GRAVA_NA_ROTINA, COMECO_DE_COMANDO,
    COMANDOS_COMUNS, _quantos,
)

log = logging.getLogger(__package__)  # "app.comandos", o mesmo logger de antes da divisao


class RotinasMixin:
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
        from .. import configuracao
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
