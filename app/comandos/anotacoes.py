"""Historico de respostas, memoria ("lembra que..."), projetos guiados, lembretes e notas.

Mixin do Executor (app/comandos/__init__.py): os metodos usam self.voz, self.cfg, self.falar...
do nucleo e chamam metodos dos outros mixins pelo self.
"""
import random
import re
import threading
from datetime import datetime
from urllib.parse import quote_plus
from .. import informacoes, memoria, projetos, sistema
from ..config import PASTA_NOTAS
from ..texto import achar_numero, contem, limpar_para_falar, normalizar


class AnotacoesMixin:
    # =================================================================
    #  Historico: voltar em respostas antigas
    # =================================================================
    def _cmd_historico(self, t: str) -> bool:
        puro = self._pedido_puro()
        alvo = t + " | " + puro
        sobre = re.search(r"o que (voce|vc) (me )?(respondeu|disse|falou) (sobre|de|do|da) (.+)", puro)
        if sobre:
            self._tipo_registro = "historico"
            item = memoria.procurar(sobre.group(5))
            if item:
                self.voz.falar(f"Em {item['data']} você perguntou: {item['pedido']}. Eu respondi:")
                self._responder(item["resposta"], item["pedido"])
            else:
                self.voz.falar("Não achei nenhuma resposta sobre isso no histórico.")
            return True
        if re.search(r"\b(le|leia|fala|quais foram) (as )?(minhas )?(ultimas|ultimas tres) respostas\b", alvo):
            self._tipo_registro = "historico"
            ultimas = memoria.respostas(3)
            if not ultimas:
                self.voz.falar("O histórico ainda está vazio.")
                return True
            partes = [f"{i}: {limpar_para_falar(x['resposta'])[:140]}" for i, x in enumerate(reversed(ultimas), 1)]
            self.voz.falar("As últimas respostas. " + ". ".join(partes) + ". O histórico completo fica na Central.")
            return True
        indice = None
        if re.search(r"\b(penultima resposta|resposta de antes da ultima)\b", alvo):
            indice = -2
        elif re.search(r"\b(repete|repetir|fala de novo|diz de novo)\b.*\b(resposta|isso|o que (voce|vc) (disse|falou))\b"
                       r"|\b(resposta anterior|ultima resposta)\b", alvo) or any(
                re.fullmatch(r"(repete|repete ai|repete por favor|repita|fala de novo|diz de novo|fala denovo)", x)
                for x in (t, puro)):
            indice = -1
        if indice is None:
            return False
        self._tipo_registro = "historico"
        itens = memoria.respostas(5)
        if len(itens) < -indice:
            self.voz.falar("Não tenho essa resposta guardada.")
            return True
        self._responder(itens[indice]["resposta"], itens[indice]["pedido"])
        return True

    # =================================================================
    #  Memoria: "lembra que ..." (a IA usa nas respostas)
    # =================================================================
    def _cmd_memoria(self, t: str) -> bool:
        puro = self._pedido_puro()
        if re.search(r"\b(em \d+|daqui a|daqui|amanha as|hoje as)\b", puro):
            return False   # "me lembra que ... em 10 minutos" e lembrete
        if re.match(r"^(me )?(lembra|lembre|lembre se|guarda|grava|memoriza) (que|disso:?) ", puro):
            partes = re.split(r"(?i)\b(?:lembra|lembre(?:-se)?|guarda|grava|memoriza)\s+(?:que|disso:?)\s+",
                              self._frase_original, maxsplit=1)
            fato = (partes[1] if len(partes) > 1 else "").strip(" .,!")
            if len(fato) < 3:
                return False
            fato = fato[0].upper() + fato[1:]
            memoria.lembrar(fato)
            self.voz.falar(random.choice(["Guardado na memória.", "Pode deixar, vou lembrar.", "Anotado. Não esqueço."]))
            self._sugerir_assunto_com_ia(fato)
            return True
        if re.search(r"o que (voce|vc) (sabe|lembra) (de|sobre) mim|o que (voce|vc) lembra|minha memoria", puro):
            fatos = memoria.fatos()
            self.voz.falar("Eu lembro que: " + ". ".join(fatos[-8:]) + "." if fatos else
                           "Ainda não guardei nada. Fala: lembra que, e o que você quer.")
            return True
        esquece = re.match(r"^esquece (que|o que eu disse sobre|sobre) (.+)", puro)
        if esquece:
            apagados = memoria.esquecer(esquece.group(2))
            self.voz.falar(f"Esqueci: {apagados[0]}." if len(apagados) == 1 else
                           f"Apaguei {len(apagados)} lembranças." if apagados else "Não achei isso na memória.")
            return True
        return False

    def _sugerir_assunto_com_ia(self, fato: str) -> None:
        """O assunto por palavra-chave ja funciona sozinho: isto so pede uma 2a opiniao da IA, em
        SEGUNDO PLANO (nunca trava a escuta) - se ela discordar, move o fato pro assunto certo."""
        if not self.cerebro.ligado or not hasattr(self.cerebro, "sugerir_assunto"):
            return
        def _pensar_assunto():
            try:
                return self.cerebro.sugerir_assunto(fato, memoria.ASSUNTOS)
            except Exception:
                return ""
        self._pensar(f"assunto do fato: {fato}", _pensar_assunto,
                     lambda assunto: memoria.mover_assunto(fato, assunto) if assunto in memoria.ASSUNTOS else None,
                     imediato=True)

    # =================================================================
    #  Projetos guiados: "quero começar um novo projeto"
    # =================================================================
    def _cmd_projeto(self, t: str) -> bool:
        base = projetos.pasta_base(self.cfg)
        puro = self._pedido_puro()
        if re.search(r"\b(novo projeto|comecar (um )?projeto|criar (um )?projeto|iniciar (um )?projeto|"
                     r"projeto novo|cria (um )?projeto|montar (um )?projeto)\b", t + " | " + puro):
            self._proj = {}
            self.perguntar("Bora! Que tipo de projeto? Código, trabalho, vida pessoal, estudo ou outro?",
                           self._proj_tipo, espera=25)
            return True
        if re.search(r"\b(quais sao|lista|le) (os )?(meus )?projetos\b", t):
            lista = projetos.listar(base)
            self.voz.falar("Seus projetos: " + ", ".join(p.name for p in lista[:8]) + "." if lista else
                           "Você ainda não tem projetos. Fala: quero começar um novo projeto.")
            return True
        abre = re.match(r"^(abre|abrir|mostra) (o |a )?(pasta do )?projeto (.+)", t)
        falta = re.search(r"o que falta (no|do|pro) projeto (.+)", t)
        anota = re.match(r"^(anota|adiciona|coloca|escreve) no projeto (.+)", t)
        if not (abre or falta or anota):
            return False
        trecho = (abre or falta or anota).group((abre and 4) or 2)
        pasta = self._achar_projeto(base, trecho)
        if not pasta:
            self.voz.falar("Não achei esse projeto. Fala: quais são os meus projetos.")
            return True
        if abre:
            sistema.abrir_arquivo(pasta)
            self.voz.falar(f"Abrindo o projeto {pasta.name}.")
        elif falta:
            lista = projetos.pendentes(pasta)
            self.voz.falar(f"No {pasta.name} falta: " + ". ".join(lista[:3]) + "." if lista else
                           f"O {pasta.name} não tem passos pendentes.")
        else:
            original = re.split(re.escape(pasta.name), self._frase_original, maxsplit=1, flags=re.I)
            texto = (original[1] if len(original) > 1 else trecho).strip(" :,.-")
            if texto.lower().startswith("que "):
                texto = texto[4:]
            projetos.anotar(pasta, texto)
            self.voz.falar(f"Anotado no projeto {pasta.name}.")
        return True

    def _achar_projeto(self, base, trecho: str):
        """O projeto cujo nome aparece no comeco do trecho falado."""
        for pasta in projetos.listar(base):
            if normalizar(trecho).startswith(normalizar(pasta.name)):
                return pasta
        return projetos.achar(base, trecho)

    def _proj_tipo(self, resposta: str) -> None:
        self._proj["tipo"] = projetos.tipo_falado(resposta)
        self.perguntar("Qual o nome do projeto?", self._proj_nome, espera=25)

    def _proj_nome(self, resposta: str) -> None:
        self._proj["nome"] = (self._frase_original or resposta).strip(" .!?")
        self.perguntar("Em uma frase: qual o objetivo?", self._proj_objetivo, espera=40)

    def _proj_objetivo(self, resposta: str) -> None:
        self._proj["objetivo"] = (self._frase_original or resposta).strip()
        self.perguntar("Tem prazo ou alguma coisa já pronta? Se não tiver, fala: nada.", self._proj_extra, espera=40)

    def _proj_extra(self, resposta: str) -> None:
        extra = (self._frase_original or resposta).strip()
        self._proj["extra"] = "" if re.fullmatch(r"(nada|nao|nenhum|nenhuma|nao tem)", normalizar(extra)) else extra
        d = self._proj
        pasta = projetos.criar(projetos.pasta_base(self.cfg), d)
        self._proj["pasta"] = pasta
        self.voz.falar(f"Criei a pasta do projeto {pasta.name}.")
        if not self.cerebro.ligado:
            self.perguntar("Sem a IA ligada eu não consigo sugerir caminhos. Quer que eu mande o plano pro Claude?",
                           lambda r: self._proj_quer_claude(r), espera=20)
            return
        pedido = (f"Tipo de projeto: {d['tipo']}. Nome: {d['nome']}. Objetivo: {d['objetivo']}. "
                  f"Prazo ou o que já existe: {d.get('extra') or 'nada'}.")
        self._pensar(f"projeto {pasta.name}", lambda: self.cerebro.propor_opcoes(pedido + self._proj_pesquisar(pasta)),
                     lambda opcoes: self._proj_apresentar(pasta, opcoes or []))

    def _proj_pesquisar(self, pasta) -> str:
        """Pesquisa o objetivo na internet (roda junto com a IA, fora da escuta), grava no PLANO.md e
        devolve o resumo para a IA levar em conta nas propostas."""
        if sistema.SIMULADO or not (self.cfg.get("projetos") or {}).get("pesquisar_internet", True):
            return ""
        resultados = informacoes.pesquisar_web(self._proj.get("objetivo") or self._proj.get("nome", ""))
        projetos.gravar_pesquisa(pasta, resultados)
        if not resultados:
            return ""
        return " O que achei na internet: " + " | ".join(f"{r['titulo']}: {r['resumo']}" for r in resultados)

    def _proj_quer_claude(self, resposta: str) -> None:
        if re.search(r"\b(sim|quero|manda|pode|isso|bora)\b", normalizar(resposta)):
            self._proj_perguntar_destino()
        else:
            self.voz.falar("Beleza. O plano ficou na pasta do projeto.")

    def _proj_apresentar(self, pasta, opcoes: list) -> None:
        self._proj["pasta"], self._proj["opcoes"] = pasta, opcoes
        if not opcoes:
            self.perguntar("A IA não trouxe opções. Quer que eu mande o plano pro Claude?",
                           lambda r: self._proj_quer_claude(r), espera=20)
            return
        projetos.gravar_opcoes(pasta, opcoes)
        numeros = ["Um", "Dois", "Três"]
        falas = [f"{numeros[i]}: {o['titulo']}. {o.get('resumo', '')}" for i, o in enumerate(opcoes)]
        self.perguntar(f"Pensei em {len(opcoes)} caminhos. " + " ".join(falas) +
                       " Ou quatro: nenhum desses, mando pro Claude. Qual você quer?", self._proj_escolha, espera=60)

    def _proj_escolha(self, resposta: str) -> None:
        n = normalizar(resposta)
        opcoes = self._proj.get("opcoes") or []
        if re.search(r"\b(quatro|quarta|quarto|4|nenhum|nenhuma|nao gostei|claude|manda|outra)\b", n):
            self._proj_perguntar_destino()
            return
        indice = next((i for i, padrao in enumerate([r"\b(um|uma|primeir[oa]|1)\b", r"\b(dois|duas|segund[oa]|2)\b",
                                                      r"\b(tres|terceir[oa]|3)\b"])
                       if re.search(padrao, n) and i < len(opcoes)), None)
        if indice is None:
            indice = next((i for i, o in enumerate(opcoes) if normalizar(o["titulo"]) and contem(n, normalizar(o["titulo"]).split()[0])), None)
        if indice is None:
            self.perguntar("Não peguei. Um, dois, três ou quatro pro Claude?", self._proj_escolha, espera=40)
            return
        opcao, pasta = opcoes[indice], self._proj["pasta"]
        projetos.escolher(pasta, opcao)
        passos = opcao.get("passos") or []
        self.voz.falar(f"Fechado: {opcao['titulo']}. " + (f"Primeiro passo: {passos[0]}. " if passos else "") +
                       "Deixei tudo no plano, na pasta do projeto.")
        sistema.abrir_arquivo(pasta / "PLANO.md")
        if (self.cfg.get("projetos") or {}).get("abrir_pesquisas", True):
            for busca in (f"como começar {opcao['titulo']}", f"projetos parecidos {self._proj.get('objetivo', '')}"):
                sistema.abrir_site("https://www.google.com/search?q=" + quote_plus(busca))

    def _proj_perguntar_destino(self) -> None:
        self.perguntar("Pra onde eu mando? Claude Code ou chat novo?", self._proj_destino, espera=40)

    def _proj_destino(self, resposta: str) -> None:
        n = normalizar(resposta)
        pasta = self._proj.get("pasta")
        if pasta is None:
            return
        texto = ("Quero começar um projeto novo. Este é o plano até agora (as opções sugeridas não me agradaram; "
                 "me ajude a pensar em outros caminhos e nos primeiros passos):\n\n" + projetos.plano_em_texto(pasta))
        if re.search(r"\b(code|codigo|programar|claude code)\b", n):
            (pasta / "PEDIDO_PARA_O_CLAUDE.md").write_text(texto, encoding="utf-8")
            sistema.abrir_terminal_com('claude "Leia o PLANO.md e o PEDIDO_PARA_O_CLAUDE.md desta pasta e me ajude '
                                       'a comecar este projeto. Faca perguntas antes de criar arquivos."',
                                       pasta, f"Projeto {pasta.name}")
            self.voz.falar("Abri o Claude Code na pasta do projeto.")
        elif re.search(r"\b(chat|claude|novo|conversa)\b", n):
            self._enviar_chat_novo(texto)
        else:
            self.perguntar("Não peguei. Claude Code ou chat novo?", self._proj_destino, espera=40)

    # =================================================================
    #  Lembretes
    # =================================================================
    def _cmd_lembrete(self, t: str) -> bool:
        if not re.search(r"\b(me lembra|lembrete|timer|alarme)\b", t):
            return False
        n = achar_numero(t)
        if n is None:
            self.voz.falar("Em quanto tempo? Tipo: {palavra}, me lembra de beber água em dez minutos.")
            return True
        em_horas = re.search(r"\bhora", t) and not re.search(r"\bminuto", t)
        segundos = n * (3600 if em_horas else 60)
        assunto = re.sub(r"\b(me lembra|lembrete|timer|alarme)\b|\b(em|daqui a|daqui) (\d+|\w+) (minutos?|horas?)\b", " ", t)
        assunto = re.sub(r"^\s*(de|do|da|que)\s+", "", re.sub(r"\s+", " ", assunto)).strip() or "o seu lembrete"
        unidade = "hora" if em_horas else "minuto"
        self.voz.falar(f"Fechou! Daqui a {n} {unidade}{'s' if n > 1 else ''} eu te lembro: {assunto}.")
        aviso = threading.Timer(segundos, lambda: (sistema.acordar_tela(), self.voz.falar(f"Ô chefe, lembrete: {assunto}!")))
        aviso.daemon = True
        aviso.start()
        return True

    # =================================================================
    #  Anotacoes
    # =================================================================
    def _cmd_notas(self, t: str) -> bool:
        arquivo = PASTA_NOTAS / "notas.txt"
        if re.search(r"\b(le|leia|ler|quais sao) (as |minhas )*(notas|anotacoes)\b", t):
            if not arquivo.exists():
                self.voz.falar("Você ainda não tem anotações.")
            else:
                ultimas = arquivo.read_text(encoding="utf-8").strip().splitlines()[-5:]
                self.voz.falar("Suas últimas anotações: " + ". ".join(l.split("] ", 1)[-1] for l in ultimas))
            return True
        if re.search(r"\babre (as |minhas )*(notas|anotacoes)\b", t):
            sistema.abrir_arquivo(arquivo)
            return True
        achado = re.match(r"^anota( ai| que| isso| ai que)?\s+(.+)", t)
        if achado:
            PASTA_NOTAS.mkdir(exist_ok=True)
            with open(arquivo, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now():%d/%m/%Y %H:%M}] {achado.group(2)}\n")
            self.voz.falar(random.choice(["Anotado.", "Guardei aqui.", "Tá na lista."]))
            return True
        return False
