"""Janelas, abas e monitores (mover, juntar, separar), tela, desligar o PC, pesquisa na internet
e abrir programas/sites.

Mixin do Executor (app/comandos/__init__.py): os metodos usam self.voz, self.cfg, self.falar...
do nucleo e chamam metodos dos outros mixins pelo self.
"""
import logging
import random
import re
import time
from pathlib import Path
from urllib.parse import quote_plus
from .. import sistema
from ..texto import contem, melhor_correspondencia, normalizar
from ..vocabulario import combina

from .base import _host, _mesmo_site

log = logging.getLogger(__package__)  # "app.comandos", o mesmo logger de antes da divisao


class JanelasMixin:
    # =================================================================
    #  Janela da frente e navegador (minimizar, fechar aba...)
    # =================================================================
    def _cmd_janela(self, t: str) -> bool:
        """Janelas e navegador: age na janela que esta na frente."""
        puro = self._pedido_puro()
        fim = r"( ai| por favor)?"
        tabela = [
            (r"(fecha|feche|fechar) (essa|esta|a) janela", lambda: sistema.atalho("alt", "f4")),
            (r"(minimiza|minimizar) tudo|mostra a area de trabalho|area de trabalho", lambda: sistema.atalho("win", "d")),
            (r"(minimiza|minimizar)( essa| a| esta)?( janela)?", lambda: sistema.janela_ativa("minimizar")),
            (r"(maximiza|maximizar)( essa| a| esta)?( janela)?", lambda: sistema.janela_ativa("maximizar")),
            (r"(troca|trocar|muda|mudar) de janela|proxima janela|outra janela", lambda: sistema.atalho("alt", "tab")),
            (r"(abre )?(uma )?nova aba|abre uma aba", lambda: sistema.atalho("ctrl", "t")),
            (r"(fecha|feche|fechar) (essa |esta |a )?aba", lambda: sistema.atalho("ctrl", "w")),
            (r"(reabre|reabrir) a aba( que eu fechei)?|volta a aba que eu fechei",
             lambda: sistema.atalho("ctrl", "shift", "t")),
            (r"((vai|passa|muda|troca) (pra|para|de) )?(a )?(proxima|outra) aba|(passa|muda|troca) (de|a) aba|aba da direita",
             lambda: self._no_navegador("trocar_aba", 1, "ctrl", "tab")),
            (r"((volta|vai) (pra|para) )?(a )?aba anterior|volta (uma|a) aba|aba da esquerda",
             lambda: self._no_navegador("trocar_aba", -1, "ctrl", "shift", "tab")),
            (r"((volta|voltar|vai|ir) (pra|para|na|a) )?(a )?pagina anterior|(volta|voltar|retorna) (a |uma |pra |para |na )?pagina"
             r"( anterior)?|volta (a |uma )?pagina (pra tras|atras)",
             lambda: self._no_navegador("voltar", None, "alt", "esquerda")),
            (r"((vai|ir|passa|avanca) (pra|para) )?(a )?proxima pagina|(avanca|avancar|adianta) (a |uma )?pagina",
             lambda: self._no_navegador("avancar", None, "alt", "direita")),
            (r"(atualiza|atualizar|recarrega|recarregar)( a pagina)?", lambda: sistema.atalho("f5")),
            (r"(rola|rolar|desce|descer)( pra| para)? (baixo|a pagina)|rola|desce a tela", lambda: sistema.atalho("pgdn")),
            (r"(rola|rolar|sobe|subir)( pra| para)? (cima|a pagina)|sobe a tela", lambda: sistema.atalho("pgup")),
            (r"(vai|volta) (pro|para o) (topo|comeco)( da pagina)?", lambda: sistema.atalho("home")),
            (r"(vai|desce) (pro|para o|ate o) (final|fim)( da pagina)?", lambda: sistema.atalho("end")),
            (r"(aumenta|mais) (o )?zoom", lambda: sistema.atalho("ctrl", "mais")),
            (r"(diminui|menos|tira o) (o )?zoom", lambda: sistema.atalho("ctrl", "menos")),
            (r"zoom normal|volta o zoom", lambda: sistema.atalho("ctrl", "0")),
        ]
        mover = r"(joga|jogar|move|mover|manda|leva|levar|passa|passar|abre) (essa|esta|a) janela"
        if re.fullmatch(mover, t) or re.match(mover + r"\b", puro):
            if not sistema.MONITOR_ALVO:
                self.voz.falar("Pra qual monitor? Fala por exemplo: joga essa janela pro monitor dois.")
            else:
                sistema.mover_janela_para_monitor(sistema.janela_da_frente(), sistema.MONITOR_ALVO)
            return True
        for padrao, acao in tabela:
            if re.fullmatch(padrao + fim, t) or re.fullmatch(padrao + fim, puro):
                acao()
                return True
        if re.fullmatch(r"(tira|tirar|faz|fazer) (um )?print( da tela)?|captura (a )?tela" + fim, puro):
            arquivo = sistema.tirar_print()
            self.voz.falar("Print salvo na sua pasta de Imagens.")
            log.info("Print: %s", arquivo)
            return True
        return False

    def _no_navegador(self, acao: str, arg, *teclas: str) -> None:
        """Voltar/avançar página e trocar de aba: com o navegador na frente, pelas teclas; se você está
        em outro programa (ex.: o Brave no outro monitor), pela extensão na aba que você usou por último."""
        ext = self._extensao()
        if ext and sistema.programa_da_frente() not in sistema.NAVEGADORES:
            try:
                ext.pedir(acao, arg, espera=4)
                return
            except Exception as erro:
                log.info("Extensao nao fez %s: %s", acao, erro)
        sistema.atalho(*teclas)

    # =================================================================
    #  Janelas e abas pelo nome: "joga a Netflix pro monitor 3",
    #  "separa a Netflix pro monitor 2 e deixa o YouTube no principal"
    # =================================================================
    VERBOS_MOVER = (r"(joga|jogar|jogue|move|mover|mova|manda|mandar|mande|leva|levar|leve|passa|passar|passe|"
                    r"transfere|transferir|transfira|coloca|colocar|coloque|bota|botar|poe|por|ponha|"
                    r"separa|separar|separe|tira|tirar|tire|"
                    r"deixa|deixar|deixe|arrasta|arrastar|arraste)")
    _PREP_MONITOR = r"(?:no|na|pro|pra|para o|para a|para|ao|pro lado do|em)"
    ESTA_JANELA = {"", "janela", "essa janela", "esta janela", "ela", "isso", "essa", "esta", "aqui", "ai"}

    def _extensao(self):
        """A ponte com a extensão do Brave, se ela estiver conversando com o Mestre (senão None)."""
        ponte = getattr(self, "ponte", None)
        try:
            return ponte if ponte is not None and ponte.conectada() else None
        except Exception as erro:
            log.debug("Ponte da extensao nao respondeu se esta conectada: %s", erro)
            return None

    def _monitor_falado(self, falado: str, com_a_palavra_monitor: bool) -> int | None:
        """ "2", "secundario", "aoc", "de 144"... Sem a palavra "monitor", só nomes que não são números
        (senão "coloca o Spotify no 50" viraria monitor)."""
        falado = re.sub(r"^(meu|minha|o|a)\s+", "", falado.strip())
        falado = re.sub(r"^(monitor|tela|janela)\s+", "", falado)
        falado = re.sub(r"^(numero|n)\s+", "", falado)
        falado = re.sub(r"\s+(por favor|ai|agora)$", "", falado)
        numeros = {"um", "dois", "tres", "quatro", "primeiro", "segundo", "terceiro", "quarto"}
        for numero, nomes in self._nomes_monitores().items():
            for n in nomes:
                if not n or falado not in (n, "da " + n, "do " + n):   # exato: "... no principal e deixa ..." nao vale
                    continue
                if not com_a_palavra_monitor and (n.isdigit() or n in numeros):
                    continue
                return numero
        return None

    def _extrair_monitor(self, texto: str) -> tuple[str, int | None]:
        """Tira a parte do monitor do FIM da frase: "(no) monitor 2", "(no) monitor secundario",
        "(no) segundo monitor", "pro terciario" (o numero/nome pode vir ANTES ou DEPOIS da palavra
        "monitor", ou nem precisar dela se o nome ja for inconfundivel, tipo "secundario"/"terciario").
        A preposicao ("no"/"pro"/"para o"...) so e OPCIONAL quando a palavra "monitor" esta escrita
        (sem ambiguidade): "joga o youtube monitor 2" (fala corrida, sem "no"/"pro" no meio) vale;
        sem a palavra "monitor" a preposicao continua obrigatoria (senao "a TELA do YouTube" ou
        qualquer ultima palavra da frase virariam monitor por engano).
        Devolve (frase sem essa parte, numero) ou (frase original, None) se nao achou monitor nenhum."""
        padroes = [
            # a palavra (qualquer) vem ANTES do nome, com preposicao: "no monitor 2", "pra tela 3"
            (rf"^(.*?)\s*\b{self._PREP_MONITOR}\s+(?:meu\s+|minha\s+)?(?:monitor|tela|janela)\s+"
             r"(?:numero\s+)?(.+)$", True),
            # a palavra (qualquer) vem DEPOIS do nome, com preposicao: "pro segundo monitor"
            (rf"^(.*?)\s*\b{self._PREP_MONITOR}\s+(?:meu\s+|minha\s+)?([a-z]+)\s+(?:monitor|tela|janela)\s*$", True),
            # so "monitor" (sem ambiguidade), mesmo SEM preposicao, nome ANTES: "youtube monitor 2"
            (r"^(.*?)\s*\bmonitor\s+(?:numero\s+)?(.+)$", True),
            # so "monitor" (sem ambiguidade), mesmo SEM preposicao, nome DEPOIS: "youtube segundo monitor"
            (r"^(.*?)\s*\b([a-z]+)\s+monitor\s*$", True),
            # com preposicao mas SEM a palavra "monitor" nenhuma: "pro terciario", "no principal"
            # (nomes ambiguos como numeros/ordinais soltos exigem a palavra "monitor" acima; so nomes
            # inconfundiveis, como "secundario"/"terciario"/"aoc"/"da tv", passam por aqui)
            (rf"^(.*?)\s*\b{self._PREP_MONITOR}\s+(?:meu\s+|minha\s+)?(.+)$", False),
        ]
        for padrao, com_a_palavra_monitor in padroes:
            achado = re.match(padrao, texto)
            if not achado:
                continue
            resto, falado = achado.groups()
            numero = self._monitor_falado(falado.strip(), com_a_palavra_monitor)
            if numero:
                return resto.strip(), numero
        return texto, None

    ARTIGO_ALVO = r"(?:(?:a|o|as|os|essa|esse|esta|este|aquela|aquele|minha|meu)\s+)?"
    TIPO_ALVO = r"(?:(?:aba|janela|site|programa|app|aplicativo|guia)\s+)?"
    DE_ALVO = r"(?:(?:do|da|de|com o|com a)\s+)?"

    def _clausula_de_mover(self, parte: str) -> dict | None:
        """Uma ordem: {"verbo", "alvo", "monitor", "separar"} ou None."""
        artigo, tipo, de = self.ARTIGO_ALVO, self.TIPO_ALVO, self.DE_ALVO
        m = re.match(rf"^{self.VERBOS_MOVER}\s+{artigo}{tipo}{de}(.+)$", parte)
        if m:
            verbo, resto = m.groups()
            alvo, numero = self._extrair_monitor(resto)
            outro = re.match(rf"^(.*?)\s*\b{self._PREP_MONITOR}\s+(?:o\s+|a\s+)?(?:outro\s+monitor|outra\s+tela)$", resto)
            if not numero and outro:   # "joga a Netflix pro outro monitor": qual é o outro, decide depois
                alvo, numero = outro.group(1), "outro"
        else:   # "o YouTube deixa no principal", "a Netflix joga pro monitor 2"
            m = re.match(rf"^{artigo}{tipo}{de}(.+?)\s+{self.VERBOS_MOVER}\s+(.+)$", parte)
            if not m:
                return None
            alvo, verbo, resto = m.groups()
            _, numero = self._extrair_monitor(resto)
        if not numero:
            return None
        alvo = alvo.strip()
        separar = bool(re.match(r"(separa|tira|destaca)", verbo))
        sozinha = r"\s+(desse|deste|do|da|dessa|desta) (navegador|janela|brave|chrome)$|\s+sozinh[ao]$"
        if re.search(sozinha, alvo) or re.match(r"(so|somente|apenas) ", alvo):
            separar = True
            alvo = re.sub(sozinha, "", re.sub(r"^(so|somente|apenas) (a |o )?", "", alvo))
        return {"verbo": verbo, "alvo": alvo.strip(), "monitor": numero, "separar": separar,
                "deixar": verbo.startswith("deix")}

    def _ordens_de_mover(self, puro: str) -> list[dict] | None:
        puro = re.sub(r"^(quero que (voce|vc) |quero |por favor |da pra |consegue |pode |tem como )+", "", puro)
        uma = self._clausula_de_mover(puro)
        if uma:
            return [uma]
        # duas ordens juntas: "... pro monitor 2 e (deixa) o YouTube no principal"
        for achado in re.finditer(r"\s+(?:e|mas|,)\s+", puro):
            a, b = puro[:achado.start()], puro[achado.end():]
            primeira = self._clausula_de_mover(a)
            if primeira:
                segunda = self._clausula_de_mover(b)
                if segunda:
                    return [primeira, segunda]
        return None

    def _cmd_juntar(self, t: str) -> bool:
        """ "junta o YouTube com a Disney": a aba do YouTube vai para a janela da Disney (qualquer monitor)."""
        puro = re.sub(r"^(quero que (voce|vc) |quero |por favor |pode )+", "", self._pedido_puro())
        verbo = r"(junta|juntar|junte|une|unir|una|agrupa|agrupar|agrupe|traz|trazer|traga|coloca|coloque|poe|bota|leva|joga|manda|move|passa)"
        art = r"(?:(?:a|o|as|os)\s+)?(?:(?:janela|aba|guia)\s+)?(?:(?:do|da|de)\s+)?"
        todas = re.match(rf"^{verbo} (todas as |as |tudo |todas )?(janelas|abas|guias)( (do|da) (navegador|brave))?"
                         rf"( (em uma|numa|numa so|em uma so|na mesma) janela( so)?)?( (no|na|pro|pra) (.+))?$", puro)
        dupla = re.match(rf"^{verbo} {art}(.+?) (com|junto com|junto da|junto do|junto de|pra|para|na|dentro da|dentro do|"
                         rf"ao lado da|ao lado do|e) {art}(.+?)$", puro)
        if not (todas or dupla) or (dupla and not todas and not re.search(
                r"\b(junta|juntar|junte|une|unir|una|agrupa|agrupar|agrupe|junto|janela|guia|aba)\b", puro)):
            return False
        if dupla and not todas and (re.search(r"\b(monitor|tela)\b", dupla.group(4))
                                    or self._monitor_falado(dupla.group(4), False)):
            return False   # "manda o Spotify pra janela principal" = mudar de monitor (_cmd_mover)
        ext = self._extensao()
        if not ext:
            self.voz.falar("Pra juntar abas eu preciso da extensão no Brave. Ela não está conectada.")
            return True
        abas = self._abas_abertas()
        if todas:
            destino = next((a for a in abas if a.get("janela_em_uso") and a.get("ativa")), abas[0] if abas else None)
            if not destino:
                return True
            ext.pedir("juntar", {"abas": [a["id"] for a in abas if a["janela"] != destino["janela"]],
                                 "destino": destino["id"]}, espera=6)
            falado = todas.group(12)
            numero = self._monitor_falado(falado, False) if falado else None
            if numero:
                hwnd = sistema.janela_pelo_titulo(destino.get("titulo", ""))
                if hwnd:
                    sistema.mover_janela_para_monitor(hwnd, numero)
            self.voz.falar("Juntei tudo numa janela.")
            return True
        a_nome, b_nome = dupla.group(2), dupla.group(4)
        b_nome = re.sub(r"\s+(no|na) (monitor|tela) .+$", "", b_nome)
        a, b = self._achar_janela_ou_aba(a_nome, abas), self._achar_janela_ou_aba(b_nome, abas)
        if not (a and b and a["tipo"] == "aba" and b["tipo"] == "aba"):
            falta = a_nome if not (a and a["tipo"] == "aba") else b_nome
            self.voz.falar(f"Não achei a aba de {self._original(falta)} no Brave.")
            return True
        if a["aba"]["janela"] == b["aba"]["janela"]:
            self.voz.falar("Elas já estão na mesma janela.")
            return True
        ext.pedir("juntar", {"abas": [a["aba"]["id"]], "destino": b["aba"]["id"]}, espera=6)
        return True

    # sem monitor na frase ("separa o YouTube e a Disney", "joga a Netflix"): o Mestre pergunta o que falta
    VERBOS_SEM_MONITOR = (r"(separa|separar|separe|joga|jogar|jogue|move|mover|mova|leva|levar|leve|"
                          r"transfere|transferir|transfira)")
    SO_SEPARAR = (r"\b(so|apenas|somente) (separa|separar|separe|separando)\b|\bsem (mudar|mover|trocar)( de)?"
                  r"( monitor| tela)?\b|\bdeixa (onde|como) (esta|estao|ta|tao)\b")

    def _cmd_mover(self, t: str) -> bool:
        """Mover/separar janelas e abas. Monta a ordem INTEIRA antes de mexer: alvo que não está aberto,
        janela ambígua ou monitor que faltou = pergunta (ou avisa) e nada é feito pela metade."""
        puro = self._pedido_puro()
        ordens = self._ordens_de_mover(puro)
        abas = None
        if not ordens:
            if not re.match(rf"^(?:(?:quero que (?:voce|vc) |quero |por favor |pode )+)?{self.VERBOS_SEM_MONITOR}\s", puro):
                return False
            abas = self._abas_abertas()
            ordens = self._ordens_sem_monitor(puro, abas)
            if not ordens:
                return False
        abas = self._abas_abertas() if abas is None else abas
        opcoes = [self._janelas_do_alvo(o["alvo"], abas) for o in ordens]
        faltando = [o["alvo"] for o, op in zip(ordens, opcoes) if not op]
        if faltando:
            if len(ordens) == 1 and ordens[0]["monitor"] not in (None, "outro") and \
                    self._abrir_no_monitor(ordens[0]["alvo"], ordens[0]["monitor"]):
                return True
            nomes = " e ".join(self._original(f) for f in faltando)
            self.voz.falar(f"Não achei {nomes} aberto." + (" Não mexi em nada." if len(ordens) > 1 else ""))
            return True
        self._resolver_janelas(ordens, opcoes, abas, [], time.time())
        return True

    def _ordens_sem_monitor(self, puro: str, abas: list[dict]) -> list[dict] | None:
        """ "separa o YouTube e a Disney" -> duas ordens (monitor None = perguntar). Só vale se TODOS os alvos
        estão abertos ou são nomes conhecidos (serviço, site, programa); senão não é comigo (None)."""
        puro = re.sub(r"^(quero que (voce|vc) |quero |por favor |pode )+", "", puro)
        m = re.match(rf"^{self.VERBOS_SEM_MONITOR}\s+(.+)$", puro)
        if not m:
            return None
        verbo, resto = m.groups()
        ordens = []
        for k, pedaco in enumerate(p for p in re.split(r"\s*,\s*|\s+e\s+", resto) if p.strip()):
            if k:
                pedaco = re.sub(rf"^{self.VERBOS_MOVER}\s+", "", pedaco)
            clausula = self._clausula_de_mover(f"{verbo} {pedaco}")
            if clausula:
                ordens.append(clausula)
                continue
            alvo = re.sub(rf"^{self.ARTIGO_ALVO}{self.TIPO_ALVO}{self.DE_ALVO}", "", pedaco).strip()
            ordens.append({"verbo": verbo, "alvo": alvo, "monitor": None, "separar": verbo.startswith("separ"),
                           "deixar": False})
        conhecido = lambda alvo: bool(   # noqa: E731
            self._janelas_do_alvo(alvo, abas) or self._servico_falado(alvo) or
            melhor_correspondencia(alvo, self.cfg.get("sites") or {}) or
            melhor_correspondencia(alvo, self.cfg.get("programas") or {}))
        return ordens if ordens and all(conhecido(o["alvo"]) for o in ordens) else None

    def _resolver_janelas(self, ordens: list[dict], opcoes: list[list[dict]], abas: list[dict], achados: list[dict],
                          criado: float) -> None:
        """Resolve uma ordem de cada vez (janela ambígua = pergunta qual), depois os monitores que faltam
        (pergunta), e só então executa tudo."""
        i = len(achados)
        if i < len(ordens):
            op = opcoes[i]
            if len(op) == 1:
                self._resolver_janelas(ordens, opcoes, abas, achados + [op[0]], criado)
                return
            nome = self._original(ordens[i]["alvo"])
            por_monitor: dict = {}
            for achado in op:
                monitor = self._monitor_da_aba(achado["aba"], abas) if achado["tipo"] == "aba" else None
                por_monitor.setdefault(monitor, []).append(achado)
            telas = sorted(m for m in por_monitor if m)
            if len(telas) < 2 or None in por_monitor or any(len(por_monitor[m]) > 1 for m in telas):
                self.voz.falar(f"Tem mais de uma janela com {nome} e não sei qual. Deixe a certa na frente e fale: "
                               "joga essa janela pro monitor 2. Não mexi em nada.")
                return

            def responder(resposta: str):
                if not self._plano_valendo(criado):
                    return
                n = self._monitor_da_resposta(resposta)
                if n in por_monitor:
                    self._resolver_janelas(ordens, opcoes, abas, achados + [por_monitor[n][0]], criado)
                elif re.match(r"^(cancela|cancelar|esquece|deixa pra la|deixa|para|parar|sai|nada|nenhum|nenhuma)$",
                              normalizar(resposta)):
                    self.falar("cancelado")
                else:
                    self.voz.falar("Não peguei qual. Não mexi em nada.")
            responder.aceita_nao = True
            self.perguntar(f"Tem {nome} em mais de uma janela: no monitor " + " e no ".join(map(str, telas)) +
                           ". Qual eu uso?", responder, espera=15)
            return
        sem_monitor = [k for k, o in enumerate(ordens) if o["monitor"] is None]
        if sem_monitor:
            self._perguntar_monitores(ordens, achados, sem_monitor, criado)
            return
        self._executar_ordens(ordens, achados)

    def _perguntar_monitores(self, ordens: list[dict], achados: list[dict], sem_monitor: list[int], criado: float) -> None:
        numeros = [m["numero"] for m in sistema.monitores()]
        nomes = [self._original(ordens[k]["alvo"]) for k in sem_monitor]
        separar = all(ordens[k]["separar"] for k in sem_monitor)
        so_separar = " Ou fala: só separar." if separar else ""
        if len(sem_monitor) == 1:
            opcoes = (" O " + " ou o ".join(map(str, numeros)) + "?") if len(numeros) >= 2 else ""
            pergunta = f"Para qual monitor vai {nomes[0]}?{opcoes}{so_separar}"
        else:
            exemplo = " e ".join(f"{n} no {numeros[k % len(numeros)] if numeros else k + 1}" for k, n in enumerate(nomes))
            pergunta = (f"{'Separo' if separar else 'Movo'} {' e '.join(nomes)}. Qual monitor pra cada um? "
                        f"Fala por exemplo: {exemplo}.{so_separar}")

        def responder(resposta: str):
            if not self._plano_valendo(criado):
                return
            n = normalizar(resposta)
            if re.match(r"^(cancela|cancelar|esquece|deixa pra la|deixa|para|parar|sai|nada|nenhum|nenhuma)$", n):
                self.falar("cancelado")
                return
            if separar and re.search(self.SO_SEPARAR, n):
                escolha = [None] * len(sem_monitor)
            else:
                escolha = self._monitores_da_resposta(n, [ordens[k]["alvo"] for k in sem_monitor])
                if not escolha or any(m is None or (numeros and m not in numeros) for m in escolha):
                    self.voz.falar("Não peguei os monitores. Não mexi em nada.")
                    return
            abertas = {a.get("id") for a in self._abas_abertas()}
            if any(a["tipo"] == "aba" and a["aba"].get("id") not in abertas for a in achados):
                self.voz.falar("Uma das abas fechou. Não mexi em nada.")
                return
            novas = [dict(o) for o in ordens]
            for k, m in zip(sem_monitor, escolha):
                novas[k]["monitor"] = m
            self._executar_ordens(novas, achados)
        responder.aceita_nao = True
        self.perguntar(pergunta, responder, espera=20)

    def _monitor_da_resposta(self, resposta: str) -> int | None:
        """ "no dois", "monitor 2", "o da esquerda", "youtube no 1" (o fim da frase) -> número do monitor."""
        palavras = normalizar(resposta).split()
        for k in (3, 2, 1):
            if len(palavras) < k:
                continue
            falado = re.sub(r"^(e |eh |o |a )?(do |da |no |na |pro |pra |para o |para a |para |em |ao )", "",
                            " ".join(palavras[-k:]))
            numero = self._monitor_falado(falado, True)
            if numero:
                return numero
        return None

    def _monitores_da_resposta(self, n: str, alvos: list[str]) -> list[int | None] | None:
        """ "youtube no 1 e disney no 2" (ou "no 1 e no 2", na ordem que perguntou) -> [1, 2]."""
        if len(alvos) == 1:
            return [self._monitor_da_resposta(n)]
        pedacos = [p for p in re.split(r"\s*,\s*|\s+e\s+", n) if p.strip()]
        palavras = [[w for w in normalizar(a).split() if len(w) > 2] for a in alvos]
        escolha: list[int | None] = [None] * len(alvos)
        sem_nome = []
        for pedaco in pedacos:
            de_quem = [k for k, ws in enumerate(palavras) if ws and any(re.search(rf"\b{re.escape(w)}", pedaco) for w in ws)]
            if len(de_quem) > 1:
                return None
            if de_quem:
                escolha[de_quem[0]] = self._monitor_da_resposta(pedaco)
            else:
                sem_nome.append(self._monitor_da_resposta(pedaco))
        if all(m is None for m in escolha) and len(sem_nome) == len(alvos):
            return sem_nome   # "no 1 e no 2": na ordem em que perguntei
        return escolha if not sem_nome else None

    def _executar_ordens(self, ordens: list[dict], achados: list[dict]) -> None:
        # duas ordens para abas da MESMA janela: essa janela tem de ser separada
        if len(ordens) == 2 and all(a["tipo"] == "aba" for a in achados) and \
                achados[0]["aba"]["janela"] == achados[1]["aba"]["janela"]:
            for o in ordens:
                o["separar"] = o["separar"] or not o["deixar"]
            if all(o["deixar"] for o in ordens):
                ordens[0]["separar"] = True
        abas = None
        for ordem, achado in zip(ordens, achados):
            if ordem["monitor"] == "outro":
                abas = self._abas_abertas() if abas is None else abas
                self._mover_pro_outro_monitor(achado, ordem, abas)
                continue
            self._mover_achado(achado, ordem)

    def _mover_pro_outro_monitor(self, achado: dict, ordem: dict, abas: list[dict]) -> None:
        """ "pro outro monitor": com 2 monitores é o que ela não está; com mais, pergunta qual."""
        numeros = [m["numero"] for m in sistema.monitores()]
        if len(numeros) < 2:
            self.voz.falar("Só tem um monitor ligado.")
            return
        atual = (self._monitor_da_aba(achado["aba"], abas) if achado["tipo"] == "aba"
                 else sistema.monitor_da_janela(achado.get("hwnd") or sistema.janela_da_frente()))
        outros = [n for n in numeros if n != atual]
        if len(outros) == 1:
            self._mover_achado(achado, {**ordem, "monitor": outros[0]})
            return

        def responder(resposta: str):
            falado = re.sub(r"^(e |eh )?(o |a )?(do |da |no |na |pro |pra |para o )?(monitor |tela )?(numero )?", "",
                            normalizar(resposta))
            numero = self._monitor_falado(falado, True)
            if numero:
                self._mover_achado(achado, {**ordem, "monitor": numero})
            else:
                self.voz.falar("Não peguei o monitor. Fala de novo: joga pro monitor 2, por exemplo.")
        self.perguntar("Para qual monitor? O " + " ou o ".join(map(str, outros)) + "?", responder, espera=12)

    def _abas_abertas(self) -> list[dict]:
        ext = self._extensao()
        if not ext:
            return []
        try:
            return ext.pedir("abas", espera=4) or []
        except Exception as erro:
            log.info("Extensao nao listou as abas: %s", erro)
            return []

    # --- qual janela? (o mesmo site aberto em mais de um monitor) -------------------------------------
    def _monitor_da_frase(self, texto: str) -> tuple[str, int | None]:
        """ "abre o segundo video do monitor 2" -> ("abre o segundo video", 2). Sem monitor: (texto, None)."""
        achado = re.search(r"\s*\b(?:do|da|no|na|que (?:esta|ta) (?:no|na))\s+(?:monitor|tela)\s+(.+?)$", texto)
        if not achado:
            return texto, None
        numero = self._monitor_falado(achado.group(1), True)
        return (texto[:achado.start()].strip(), numero) if numero else (texto, None)

    def _monitor_da_aba(self, aba: dict, abas: list[dict]) -> int | None:
        """Em qual monitor esta a janela da aba: pelo titulo da janela do Windows (que mostra a aba da frente)
        ou, se nao der, pela posicao que a extensao manda."""
        frente = next((a for a in abas if a.get("janela") == aba.get("janela") and a.get("ativa")), aba)
        inicio = normalizar(frente.get("titulo", ""))[:30]
        if inicio:
            achados = {j["monitor"] for j in sistema.janelas_abertas()
                       if j["exe"] in sistema.NAVEGADORES and j.get("monitor") and normalizar(j["titulo"]).startswith(inicio)}
            if len(achados) == 1:
                return achados.pop()
        if aba.get("janela_x") is not None and aba.get("janela_largura"):
            return sistema.monitor_do_ponto(int(aba["janela_x"]) + int(aba["janela_largura"]) // 2,
                                            int(aba["janela_y"]) + int(aba.get("janela_altura") or 0) // 2)
        return None

    @staticmethod
    def _abas_na_tela(abas: list[dict], dominio: str = "") -> list[dict]:
        """As abas que voce VE: a da frente de cada janela que nao esta minimizada (so do site, se pedido)."""
        do_site = [a for a in abas if not dominio or _mesmo_site(a.get("url", ""), dominio)]
        return [a for a in do_site if a.get("ativa") and a.get("janela_estado") != "minimized"] or do_site

    def _escolher_aba(self, candidatas: list[dict], abas: list[dict], nome: str, monitor: int | None,
                      continuar, tem=None) -> None:
        """Decide em QUAL aba agir e chama continuar(id da aba). Com mais de uma na tela, nesta ordem:
        a unica que tem o que voce falou (tem), a do monitor que voce disse, a do monitor onde esta o mouse.
        Se ainda assim ficar em duvida: pergunta "No monitor 1 ou no 2?"."""
        def recente(a):
            return a.get("janela_em_uso", False), a.get("ultimo_acesso", 0)
        if not candidatas:
            continuar(None)
            return
        if tem and len(candidatas) > 1:   # tem(aba) = nota (0 = nao tem); fica so com as de nota mais alta
            notas = {a["id"]: float(tem(a) or 0) for a in candidatas}
            melhor = max(notas.values())
            com = [a for a in candidatas if melhor > 0 and notas[a["id"]] == melhor]
            if monitor is None and len(com) <= 1:   # so uma tem (ou nenhuma: quem responde e o comando)
                continuar((com[0] if com else max(candidatas, key=recente))["id"])
                return
            candidatas = com or candidatas
        if len(candidatas) == 1 and monitor is None:
            continuar(candidatas[0]["id"])
            return
        for a in candidatas:
            a["_monitor"] = self._monitor_da_aba(a, abas)
        if monitor is not None:
            ali = [a for a in candidatas if a["_monitor"] == monitor]
            if not ali and not any(a["_monitor"] for a in candidatas) and len(candidatas) == 1:
                ali = candidatas   # (nao deu para saber o monitor de nenhuma: vai na unica)
            if not ali:
                self.voz.falar(f"Não achei {nome} no monitor {monitor}.")
                return
            continuar(max(ali, key=recente)["id"])
            return
        mouse = sistema.monitor_do_mouse()
        ali = [a for a in candidatas if mouse and a["_monitor"] == mouse]
        if len(ali) == 1:
            continuar(ali[0]["id"])
            return
        telas = sorted({a["_monitor"] for a in candidatas if a["_monitor"]})
        if len(telas) >= 2:
            def responder(resposta: str, c=candidatas):
                falado = re.sub(r"^(e |eh )?(o |a )?(do |da |no |na |pro |pra )?(monitor |tela )?(numero )?", "",
                                normalizar(resposta))
                n = self._monitor_falado(falado, True)
                escolhidas = [a for a in c if n and a["_monitor"] == n]
                if escolhidas:
                    continuar(max(escolhidas, key=recente)["id"])
                else:
                    self.voz.falar("Não peguei o monitor. Fala de novo dizendo do monitor 2, por exemplo.")
            self.perguntar(f"Tem {nome} em mais de uma tela. No monitor " + " ou no ".join(map(str, telas)) + "?",
                           responder, espera=12)
            return
        continuar(max(candidatas, key=recente)["id"])

    def _dominio_do_site(self, alvo: str) -> str:
        """ "netflix" -> "netflix.com" (pelo endereco cadastrado em Programas e sites)."""
        sites = self.cfg.get("sites") or {}
        chave = melhor_correspondencia(alvo, sites)
        return _host(str(sites[chave])) if chave else ""

    def _achar_janela_ou_aba(self, alvo: str, abas: list[dict] | None = None) -> dict | None:
        """{"tipo": "frente"|"aba"|"janela", ...} para o nome falado, ou None (várias janelas: a da frente)."""
        return next(iter(self._janelas_do_alvo(alvo, abas)), None)

    def _janelas_do_alvo(self, alvo: str, abas: list[dict] | None = None) -> list[dict]:
        """Todas as janelas onde o nome falado está: uma aba por janela do navegador (a da frente dela), da
        mais provável para a menos; sem aba, a janela do programa. Mais de uma = o comando precisa perguntar."""
        alvo = normalizar(alvo)
        if alvo in self.ESTA_JANELA:
            return [{"tipo": "frente", "hwnd": sistema.janela_da_frente(), "nome": "essa janela"}]
        palavras = [w for w in alvo.split() if len(w) > 1]
        if not palavras:
            return []
        dominio = self._dominio_do_site(alvo) or ("youtube.com" if "youtube" in alvo else "")

        def combina(texto: str) -> bool:
            texto = normalizar(texto)
            return all(re.search(rf"\b{re.escape(w)}", texto) for w in palavras)

        candidatas = [aba for aba in abas or [] if (dominio and _mesmo_site(aba.get("url", ""), dominio))
                      or combina(aba.get("titulo", "")) or combina(_host(aba.get("url", "")).replace(".", " "))]
        if candidatas:   # por janela: a que esta na frente dela, depois a usada por ultimo
            por_janela: dict = {}
            for aba in sorted(candidatas, key=lambda a: (a.get("ativa", False), a.get("ultimo_acesso", 0)), reverse=True):
                por_janela.setdefault(aba.get("janela"), aba)
            return [{"tipo": "aba", "aba": aba, "nome": alvo} for aba in por_janela.values()]
        # janelas do Windows (programas; e o navegador sem a extensao, pelo titulo da aba da frente)
        programas = self.cfg.get("programas") or {}
        chave = melhor_correspondencia(alvo, programas)
        exe = Path(str(programas[chave]).strip('"')).name.lower() if chave else ""
        janelas = sistema.janelas_abertas()
        for j in janelas:
            if exe and j["exe"] == exe:
                return [{"tipo": "janela", "hwnd": j["hwnd"], "nome": alvo}]
        for j in janelas:
            if combina(j["titulo"]) or combina(j["exe"].removesuffix(".exe")):
                return [{"tipo": "janela", "hwnd": j["hwnd"], "nome": alvo}]
        return []

    def _mover_achado(self, achado: dict, ordem: dict) -> None:
        numero = ordem["monitor"]
        hwnd = achado.get("hwnd")
        if achado["tipo"] == "aba":
            ext = self._extensao()
            aba = achado["aba"]
            separar = ordem["separar"] and aba.get("abas_na_janela", 1) > 1
            try:
                r = ext.pedir("separar" if separar else "focar", aba["id"], espera=5) or {}
            except Exception as erro:
                log.warning("Extensao nao %s a aba: %s", "separou" if separar else "focou", erro)
                r = {}
            hwnd = sistema.janela_pelo_titulo(r.get("titulo") or aba.get("titulo", ""))
        if numero is None:
            return   # "só separar": fica no monitor onde está
        if not hwnd and achado["tipo"] != "frente":
            log.info("Nao achei a janela de %s", achado.get("nome"))
            return
        if ordem["deixar"] and sistema.monitor_da_janela(hwnd) == numero:
            return   # "deixa o YouTube no principal" e ele ja esta la
        sistema.mover_janela_para_monitor(hwnd, numero)

    @staticmethod
    def _preferencia_de_aba(aba: dict) -> tuple:
        """Mesma página em várias abas: a da frente, depois a que toca som, depois a usada por último."""
        return aba.get("ativa", False), aba.get("audivel", False), aba.get("ultimo_acesso", 0)

    def _site_ja_aberto(self, nome: str, url: str) -> bool:
        """ "abre a Netflix" com a Netflix já aberta numa aba: usa ela (e manda para o monitor pedido,
        sozinha numa janela) em vez de abrir outra. "... numa janela nova": abre outra, sempre."""
        if not self._extensao() or sistema.JANELA_NOVA:
            return False
        dominio = _host(str(url))
        todas = self._abas_abertas()
        abas = [a for a in todas if dominio and _mesmo_site(a.get("url", ""), dominio)]
        if not abas:
            return False
        if sistema.MONITOR_ALVO:   # já está aberto no monitor pedido: só usa essa aba
            ali = [a for a in abas if self._monitor_da_aba(a, todas) == sistema.MONITOR_ALVO]
            if ali:
                try:
                    self._extensao().pedir("focar", max(ali, key=self._preferencia_de_aba)["id"], espera=4)
                except Exception as erro:
                    log.info("Extensao nao focou a aba: %s", erro)
                    return False
                self.voz.falar(f"{nome.capitalize()} já estava aberto no monitor {sistema.MONITOR_ALVO}.")
                return True
        aba = max(abas, key=self._preferencia_de_aba)
        achado = {"tipo": "aba", "aba": aba, "nome": nome}
        if sistema.MONITOR_ALVO:
            self._mover_achado(achado, {"monitor": sistema.MONITOR_ALVO, "separar": True, "deixar": False})
            self.voz.falar(f"{nome.capitalize()} já estava aberto. Mandei pro monitor {sistema.MONITOR_ALVO}.")
        else:
            try:
                self._extensao().pedir("focar", aba["id"], espera=4)
            except Exception as erro:
                log.info("Extensao nao focou a aba: %s", erro)
                return False
            self.voz.falar(f"{nome.capitalize()} já estava aberto.")
        return True

    def _ja_aberto_vai_pro_monitor(self, nome: str, caminho: str) -> bool:
        exe = Path(str(caminho).strip('"')).name.lower()
        janela = next((j for j in sistema.janelas_abertas() if exe.endswith(".exe") and j["exe"] == exe), None)
        if not janela:
            return False
        sistema.mover_janela_para_monitor(janela["hwnd"], sistema.MONITOR_ALVO)
        return True

    def _abrir_no_monitor(self, alvo: str, numero: int) -> bool:
        """ "joga a Netflix pro monitor 3" com a Netflix fechada: abre ela lá."""
        sites = self.cfg.get("sites") or {}
        programas = self.cfg.get("programas") or {}
        chave_site, chave_prog = melhor_correspondencia(alvo, sites), melhor_correspondencia(alvo, programas)
        if not (chave_site or chave_prog):
            return False
        sistema.MONITOR_ALVO = numero
        self.voz.falar(f"{(chave_prog or chave_site).capitalize()} não estava aberto. Abrindo no monitor {numero}.")
        if chave_prog:
            sistema.abrir_programa(programas[chave_prog])
        else:
            sistema.abrir_site(sites[chave_site])
        return True

    # =================================================================
    #  Tela e computador
    # =================================================================
    def _cmd_tela(self, t: str) -> bool:
        if contem(t, "bloqueia o computador"):
            self.voz.falar("Bloqueando. Até já!")
            self.voz.esperar(6)
            sistema.bloquear()
            return True
        if contem(t, "desliga a tela"):
            self.voz.falar(random.choice(["Apagando a tela. É só me chamar.", "Luz apagada. Tô de ouvido ligado."]))
            self.voz.esperar(8)
            time.sleep(0.5)
            sistema.desligar_tela()
            return True
        if contem(t, "liga a tela"):
            sistema.acordar_tela()
            self.falar("ok")
            return True
        return False

    def _cmd_desligar_pc(self, t: str) -> bool:
        if re.search(r"\bcancela(r)? (o )?desligamento\b", t):
            sistema.cancelar_desligamento()
            self.voz.falar("Desligamento cancelado. Ufa!")
            return True
        if re.search(r"\b(desliga|desligar)\b (o )?(computador|pc)\b", t):
            self.voz.falar("Vou desligar o computador em um minuto. Se mudar de ideia, fala: {palavra}, cancela o desligamento.")
            sistema.desligar_pc(60)
            return True
        if re.search(r"\b(reinicia|reiniciar)\b (o )?(computador|pc)\b", t):
            self.voz.falar("Vou reiniciar o computador em um minuto.")
            sistema.reiniciar_pc(60)
            return True
        return False

    # =================================================================
    #  Pesquisa na internet
    # =================================================================
    def _cmd_pesquisa(self, t: str) -> bool:
        achado = re.match(r"^(pesquisa|google)( no google| na internet)?( sobre| por| em)?\s+(.+)", t)
        if not achado:
            return False
        termo = self._original(achado.group(4).replace("no google", "").replace("na internet", "").strip())
        self.voz.falar(random.choice(["Pesquisando no Google.", "Deixa eu dar um Google nisso.", "Já tô pesquisando."]))
        sistema.abrir_site("https://www.google.com/search?q=" + quote_plus(termo))
        return True

    # =================================================================
    #  Abrir programas e sites
    # =================================================================
    def _o_que_abrir(self, t: str) -> tuple[str, str | None, str | None] | None:
        """ "abre o gmail" -> (nome falado, programa cadastrado, site cadastrado). None = nao e "abre ..." """
        achado = re.match(r"^(abre|liga)\s+(o |a |os |as |meu |minha )?(site |programa |app |aplicativo )?(do |da |de )?(.+)", t)
        if not achado:
            return None
        nome = achado.group(5).strip()
        return (nome, melhor_correspondencia(nome, self.cfg.get("programas") or {}),
                melhor_correspondencia(nome, self.cfg.get("sites") or {}))

    def _cmd_abrir(self, t: str) -> bool:
        alvo = self._o_que_abrir(t)
        if not alvo:
            return False
        nome, chave_prog, chave_site = alvo
        programas = self.cfg.get("programas") or {}
        sites = self.cfg.get("sites") or {}
        if chave_prog:
            if sistema.MONITOR_ALVO and self._ja_aberto_vai_pro_monitor(chave_prog, programas[chave_prog]):
                return True
            self.voz.falar(random.choice([f"Abrindo {chave_prog}.", f"{chave_prog}, saindo!", "Na hora."]))
            if not sistema.abrir_programa(programas[chave_prog]):
                self.voz.falar(f"Não consegui abrir {chave_prog}. Confere o caminho no painel e usa o botão testar.")
        elif chave_site:
            if self._site_ja_aberto(chave_site, sites[chave_site]):
                return True
            self.voz.falar(random.choice([f"Abrindo {chave_site}.", f"Indo pro {chave_site}.", "Já é!"]))
            sistema.abrir_site(sites[chave_site])
        elif self._seguimento:
            # Sem a palavra de ativacao (conversa ao redor) e o alvo nao existe: ignora em silencio
            log.info("Seguimento com 'abre' sem alvo conhecido (%r): ignorado em silêncio", nome)
            self._ignorar_seguimento = True
        else:
            self.voz.falar(f"Não conheço {nome}. Coloca ele na lista de programas ou sites do config que eu aprendo.")
        return True
