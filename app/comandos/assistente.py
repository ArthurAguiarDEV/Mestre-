"""Controle do proprio assistente: versao, encerrar, reiniciar, painel, ajuda, descanso, conversinha, atalhos ensinados e troca de voz.

Mixin do Executor (app/comandos/__init__.py): os metodos usam self.voz, self.cfg, self.falar...
do nucleo e chamam metodos dos outros mixins pelo self.
"""
import random
import re
import sys
from .. import estado, sistema
from ..texto import normalizar

from .base import VOZES_PADRAO, _quantos


class AssistenteMixin:
    # =================================================================
    #  Controle do proprio Mestre
    # =================================================================
    def _cmd_versao(self, t: str) -> bool:
        """ "qual a sua versão?", "em que versão você está?" """
        if not re.search(r"\b(qual|que|em que) (e )?(a )?(sua |tua )?versao\b|\bversao (do|da) (projeto|assistente|mestre)\b|"
                         r"\b(sua|tua) versao\b", t):
            return False
        from ..atualizar import versao_atual
        self.voz.falar(f"Estou na versão {versao_atual()}.")
        return True

    def _cmd_encerrar(self, t: str) -> bool:
        """ "desliga", "pode desligar", "desliga o Assessor", "se desliga", "encerra você"."""
        nomes = "|".join(sorted({"assistente", "mestre", re.escape(normalizar(self.nome)), re.escape(normalizar(self.palavra))} - {""}))
        puro = self._pedido_puro()
        sozinho = r"^(pode |ja pode |agora |entao )?(se )?(desliga|desligar|desligue|encerra|encerrar|encerre)( ai| agora| voce| tudo| por hoje| o programa)?( por favor)?$"
        com_nome = rf"\b(fecha|fechar|desliga|desligar|desligue|encerra|encerrar)( o| a)? ({nomes})\b"
        if not (re.search(sozinho, t) or re.search(sozinho, puro) or re.search(com_nome, t) or re.search(com_nome, puro)):
            return False
        self.falar("despedida")
        self.voz.esperar(10)   # (a despedida termina de tocar antes de desligar)
        self.rodando = False
        return True

    def _cmd_reiniciar(self, t: str) -> bool:
        if not re.search(r"\b(reinicia|reiniciar|recarrega|recarregar|atualiza|atualizar) (o |a |as )?(assistente|mestre|configuracao|configuracoes|vocabulario)\b|\breinicia(r)? voce\b|^(se )?(reinicia|reiniciar|reinicia ai)$", t):
            return False
        if "--texto" in sys.argv:  # no modo texto, so recarrega o vocabulario
            self.vocab.recarregar()
            self.voz.falar("Recarreguei o vocabulário. Mudanças no código ou no config pedem fechar e abrir de novo.")
            return True
        self.voz.falar("Reiniciando! Volto em alguns segundos.")
        self.voz.esperar(8)   # (a fala termina antes de o processo fechar)
        sistema.reiniciar_mestre()
        return True

    def _cmd_painel(self, t: str) -> bool:
        if re.search(r"\babre (o |as |a )?(painel|configuracoes|configuracao|ajustes)\b", t) and not re.search(r"\bwindows\b", t):
            self.voz.falar(random.choice(["Abrindo o painel.", "Painel na tela!"]))
            sistema.abrir_painel()
            return True
        return False

    def _cmd_ajuda(self, t: str) -> bool:
        if not re.search(r"(o que voce (sabe|consegue|pode) fazer|quais (sao )?(os )?(seus )?comandos|\bajuda\b|me ajuda)", t):
            return False
        self.voz.falar(
            "Eu rodo suas rotinas, tipo bora trabalhar. Abro programas, sites e o último vídeo "
            "de um canal do YouTube. Falo a hora, mexo no volume, apago e acendo a tela. "
            "Faço lembretes e anotações. Mando perguntas e ditados pro seu agente IPM. "
            "E você pode me ensinar atalhos, trocar minha voz e ditar melhorias longas. "
            "É só falar: quero ditar melhorias. E no fim: finalizei."
        )
        return True

    # =================================================================
    #  Ensinar atalhos por voz
    # =================================================================
    def _cmd_aprender(self, t: str) -> bool:
        # Tudo numa frase so: "Quando eu falar bora codar, abre o VS Code"
        if re.match(r"^quando eu (falar|disser|dizer|pedir)\b", t):
            achado = re.search(r"(?i)quando eu (falar|disser|dizer|pedir)\s+(.+)", self._frase_original)
            resto = achado.group(2) if achado else ""
            if "," in resto:
                gatilho, comando = resto.split(",", 1)
                self._salvar_atalho(gatilho, comando)
            else:
                self.voz.falar("Fala com uma pausa entre as partes, ou fala: {palavra}, aprende um atalho.")
            return True
        if not re.search(r"\b(aprende|aprenda|aprender|cria|criar|ensinar|te ensinar|novo) (um |uma )?(atalho|comando|frase)\b", t):
            return False
        self.perguntar("Bora! Qual frase você vai falar?", self._aprender_passo_2)
        return True

    def _aprender_passo_2(self, gatilho: str) -> None:
        gatilho = gatilho.strip(" ,.!?")
        self.perguntar(f"Beleza. E quando você falar {gatilho}, o que eu faço?",
                       lambda comando: self._salvar_atalho(gatilho, comando), espera=15)

    def _salvar_atalho(self, gatilho: str, comando: str) -> None:
        falado = comando.strip(" ,.!?")
        gatilho, comando = normalizar(gatilho), normalizar(comando)
        if not gatilho or not comando:
            self.voz.falar("Faltou uma parte. Tenta de novo: {palavra}, aprende um atalho.")
            return
        self.vocab.aprender_atalho(gatilho, comando)
        self.voz.falar(f"Aprendido! Quando você falar {gatilho}, eu faço: {falado}.")

    def _cmd_atalhos(self, t: str) -> bool:
        achado = re.match(r"^(esquece|apaga|remove|deleta) (o )?(atalho|comando) (.+)", t)
        if achado:
            if self.vocab.esquecer_atalho(achado.group(4)):
                self.voz.falar(f"Pronto, esqueci o atalho {achado.group(4)}.")
            else:
                self.voz.falar("Não achei esse atalho entre os que você me ensinou.")
            return True
        if re.search(r"\b(quais|lista|listar|fala) (sao )?(os |meus |seus )?atalhos\b", t):
            atalhos = self.vocab.atalhos
            if not atalhos:
                self.voz.falar("Ainda não tenho nenhum atalho.")
            else:
                lista = ". ".join(f"{k}: {v}" for k, v in list(atalhos.items())[:8])
                self.voz.falar(f"Tenho {_quantos(len(atalhos), 'atalho')}. {lista}.")
            return True
        return False

    # =================================================================
    #  Voz: trocar, acelerar, engrossar
    # =================================================================
    def _aplicar_preferencias_de_voz(self) -> None:
        p = self.vocab.preferencia
        self.voz.configurar(voz=p("voz"), velocidade=p("velocidade"), tom=p("tom"))

    def _vozes_favoritas(self) -> list[str]:
        if self.voz.motor == "kokoro":
            from ..voz_kokoro import VOZES
            return list(VOZES)
        return (self.cfg.get("voz") or {}).get("vozes_favoritas") or VOZES_PADRAO

    def _voz_atual(self) -> str:
        return self.voz.voz_kokoro if self.voz.motor == "kokoro" else self.voz.voz_edge

    @staticmethod
    def _nome_da_voz(v: str) -> str:
        from ..voz_kokoro import VOZES
        if v in VOZES:
            return VOZES[v].split(" ")[0]
        partes = v.split("-")
        return (partes[2] if len(partes) > 2 else v).replace("Neural", "").replace("Multilingual", "")

    def _cmd_voz(self, t: str) -> bool:
        if not re.search(r"\b(voz|vozes|fala|falar|fale)\b", t):
            return False
        if re.search(r"\b(apresenta|mostra|abre|testa|quais) (as )?(suas )?vozes\b|\bvozes disponiveis\b", t):
            self._apresentar_vozes()
            return True
        if re.search(r"\b(muda|troca|trocar|mudar|outra) (a |de )?voz\b|\boutra voz\b|\bproxima voz\b", t):
            favoritas = self._vozes_favoritas()
            atual = self._voz_atual()
            nova = favoritas[(favoritas.index(atual) + 1) % len(favoritas)] if atual in favoritas else favoritas[0]
            self._trocar_voz(nova)
            return True
        achado = re.search(r"\b(usa|use|coloca|abre|quero) a voz (do |da |de )?(.+)", t)
        if achado:
            nome = achado.group(3).replace(" ", "")
            nova = next((v for v in self._vozes_favoritas()
                         if nome in normalizar(v + self._nome_da_voz(v)).replace(" ", "")), None)
            if nova:
                self._trocar_voz(nova)
            else:
                self.voz.falar(f"Não achei a voz {achado.group(3)} nas favoritas. Olha a lista no config.")
            return True
        ajustes = [
            (r"mais rapido|mais depressa|acelera", "velocidade", 10),
            (r"mais devagar|mais lento|com calma", "velocidade", -10),
            (r"mais grave|mais grosso|voz grossa", "tom", -5),
            (r"mais agudo|mais fino|voz fina", "tom", 5),
        ]
        for padrao, campo, passo in ajustes:
            if re.search(padrao, t):
                atual = self.vocab.preferencia(campo) or ("+10%" if campo == "velocidade" else "+0Hz")
                numero = int(re.sub(r"[^\d-]", "", atual) or 0) + passo
                valor = f"{numero:+d}%" if campo == "velocidade" else f"{numero:+d}Hz"
                self.vocab.salvar_preferencia(campo, valor)
                self._aplicar_preferencias_de_voz()
                self.voz.falar("Assim tá melhor?")
                return True
        if re.search(r"\b(volta|voltar) (a )?voz (ao|pro) normal\b|\bvoz normal\b", t):
            for campo in ("voz", "velocidade", "tom"):
                self.vocab.salvar_preferencia(campo, None)
            self.voz.configurar(**{k: (self.cfg.get("voz") or {}).get(c) for k, c in
                                   (("voz", "voz_edge"), ("velocidade", "velocidade"), ("tom", "tom"))})
            self.voz.falar("Voltei pra voz original.")
            return True
        return False

    def _trocar_voz(self, nova: str) -> None:
        self.vocab.salvar_preferencia("voz", nova)
        self._aplicar_preferencias_de_voz()
        self.voz.falar(f"E aí, chefe! Essa é a voz {self._nome_da_voz(nova)}. Curtiu?")

    def _apresentar_vozes(self) -> None:
        original = self._voz_atual()
        vozes = self._vozes_favoritas()
        for i, v in enumerate(vozes, 1):
            self.voz.configurar(voz=v)
            self.voz.falar(f"Voz número {i}: {self._nome_da_voz(v)}. Fala, chefe! Bora trabalhar?")
            self.voz.esperar(30)   # (a fala e em segundo plano: so troca a voz depois de ela tocar)
        self.voz.configurar(voz=original)
        self.voz.falar(f"Pra escolher, fala por exemplo: {{palavra}}, usa a voz do {self._nome_da_voz(vozes[-1])}.")

    # =================================================================
    #  Descanso ("pode descansar") e conversinha
    # =================================================================
    def _cmd_descanso(self, t: str) -> bool:
        """ "pode descansar": fica quieto (ouve so "bora voltar a trabalhar")."""
        puro = self._pedido_puro()
        if not re.search(r"^(pode |vai |agora |ja pode )?(descansar|descansa|descanse|dormir|dorme|durma|relaxar um pouco)"
                         r"( um pouco| agora| ai| por enquanto)?$|\bmodo descanso\b|\b(da|de) um tempo\b|"
                         r"\bfica (quieto|quietinho|em silencio|de boa)\b|\b(stand ?by|standby|modo espera)\b", puro):
            return False
        self._descansando = True
        estado.atualizar(descanso=True)
        self.voz.falar(self.preencher(random.choice(["Beleza {apelido}. Vou descansar. Pra voltar fala: bora voltar a trabalhar.",
                                                     "Tô descansando {apelido}. Quando quiser fala: bora voltar a trabalhar."])))
        return True

    def _cmd_conversinha(self, t: str) -> bool:
        """Cumprimento ("e aí", "tá por aí?") e despedida ("tchau"): resposta curta, sem IA."""
        puro = self._pedido_puro()
        if re.fullmatch(r"((e ai|oi|ola|fala|opa|salve|beleza|tudo bem|tudo certo|ta ai|ta por ai|ta me ouvindo|"
                        r"na escuta|presente|cade voce|voce ta ai|voce esta ai|ta aqui|ta on)\s*)+"
                        r"( (meu )?(parceiro|mano|cara|amigo|brother))?", puro):
            self.falar("chamado")
            self._acabou_de_chamar = True
            return True
        if re.fullmatch(r"((tchau|bye|falou|flw|ate mais|ate logo|ate depois|ate amanha|fui|valeu tchau)\s*)+", puro):
            self.voz.falar(self.preencher(random.choice(["Até mais {apelido}.", "Falou {apelido}!", "Tchau {apelido}. Tô por aqui."])))
            return True
        return False
