"""Perfis dos streamings ("Arthur", "Mestre", "Magnífico"): qual perfil usar antes de buscar, tocar ou continuar.

Mixin do Executor (app/comandos/__init__.py). Três coisas diferentes, que nunca se misturam:
  - perfil do NAVEGADOR (janelas > perfil_brave): cookies e logins do Brave;
  - perfil do SERVIÇO (streaming > perfis): o perfil escolhido dentro da Netflix, Disney...;
  - sessão aberta: a aba de um serviço que o Mestre CONFIRMOU estar num perfil (só na memória).

No config ficam só nomes (streaming > perfis, perfil_padrao). A sessão guarda o mínimo (serviço, perfil,
id da aba e hora) e some quando o Mestre fecha ou a aba muda de site. Nunca senha, cookie, token, e-mail
nem endereço da página. Perfil desconhecido nunca é presumido: o Mestre pergunta.
"""
import logging
import re
import time

from .. import sistema
from ..texto import normalizar

log = logging.getLogger(__package__)

SIM = (r"^(sim|isso|isso mesmo|pode|pode sim|pode usar|usa|use|uso|confirmo|confirma|claro|com certeza|ok|"
       r"beleza|esta|ta|certo|exato|positivo|manda|vai)( sim| sim senhor| mesmo| pode)?$")
NAO = r"^(nao|nem|errado|negativo|nao e|nao esta|nao ta|outro|outra)\b"
DESISTIR = r"^(cancela|cancelar|esquece|deixa pra la|deixa|para|parar|sai|nada|nenhum|nenhuma)$"
PLANO_EXPIRA_SEG = 90   # resposta que chega depois disso não executa nada: as abas podem ter mudado
PROIBIDO_NO_NOME = re.compile(r"[@/\\:=]|senha|password|token|cookie|sessao|session", re.I)


def perfis_configurados(cfg: dict) -> list[str]:
    """Os nomes cadastrados no painel (streaming > perfis). Só nomes: nada com cara de e-mail ou senha."""
    nomes = (cfg.get("streaming") or {}).get("perfis") or []
    if isinstance(nomes, str):
        nomes = nomes.split(",")
    limpos = []
    for nome in nomes if isinstance(nomes, list) else []:
        nome = str(nome or "").strip()
        if nome and len(nome) <= 30 and not PROIBIDO_NO_NOME.search(nome) and \
                normalizar(nome) not in {normalizar(x) for x in limpos}:
            limpos.append(nome)
    return limpos[:12]


def perfil_padrao(cfg: dict) -> str:
    """O perfil padrão só vale se estiver na lista de perfis."""
    padrao = str((cfg.get("streaming") or {}).get("perfil_padrao") or "").strip()
    return achar_perfil(padrao, perfis_configurados(cfg)) or ""


def achar_perfil(falado: str, perfis: list[str]) -> str | None:
    """ "no perfil do arthur", "magnifico" -> o nome como está no cadastro ("Magnífico"). Só nome exato."""
    n = normalizar(falado or "")
    n = re.sub(r"^(e |eh |o |a |no |na |pro |pra |do |da |de |usa |use |uso |perfil |o perfil |no perfil )+", "", n)
    n = re.sub(r"\s+(por favor|ai|mesmo)$", "", n).strip()
    return next((p for p in perfis if normalizar(p) == n), None) if n else None


def sim_ou_nao(resposta: str) -> str | None:
    """ "sim" / "nao" / "desistir"; None = resposta que não dá para aceitar ("acho que sim", "talvez")."""
    n = normalizar(resposta or "")
    if re.match(DESISTIR, n):
        return "desistir"
    if re.match(SIM, n):
        return "sim"
    if re.match(NAO, n):
        return "nao"
    return None


def perfil_da_frase(puro: str) -> tuple[str, str | None]:
    """ "toca loki na disney no perfil mestre" -> ("toca loki na disney", "mestre")."""
    achado = re.search(r"\s*\b(?:(?:no|na|com o|com a|pelo|pela|usando o|usando a|em)\s+)?perfil\s+"
                       r"(?:do\s+|da\s+|de\s+)?(?P<nome>.+?)(?=\s+(?:na|no|pela|pelo|em|do|da|numa|num|pra|pro|para)\s|$)",
                       puro)
    if not achado:
        return puro, None
    resto = re.sub(r"\s+", " ", puro[:achado.start()] + " " + puro[achado.end():]).strip()
    return resto, achado.group("nome").strip()


def maiuscula(texto: str) -> str:
    """ "a Netflix" -> "A Netflix" (sem baixar o resto, como o capitalize faria)."""
    return texto[:1].upper() + texto[1:]


def lista_falada(nomes: list[str], conector: str = "ou") -> str:
    return nomes[0] if len(nomes) == 1 else ", ".join(nomes[:-1]) + f" {conector} " + nomes[-1]


class PerfisMixin:
    # --- sessão: qual aba o Mestre já confirmou em qual perfil (só na memória) ------------------------
    def _sessoes(self) -> dict:
        if not hasattr(self, "_sessoes_streaming"):
            self._sessoes_streaming = {}   # id da aba -> {"servico", "perfil", "quando"}
        return self._sessoes_streaming

    def _lembrar_perfil(self, aba_id, servico: str, perfil: str) -> None:
        if aba_id:
            self._sessoes()[aba_id] = {"servico": servico, "perfil": perfil, "quando": time.time()}

    def _perfil_da_aba(self, aba: dict) -> str | None:
        """O perfil confirmado desta aba, se ela ainda é do mesmo serviço (mudou de site: esquece)."""
        sessao = self._sessoes().get(aba.get("id"))
        if not sessao:
            return None
        if self._servico_da_aba(aba) != sessao["servico"]:
            self._sessoes().pop(aba.get("id"), None)
            return None
        return sessao["perfil"]

    def _limpar_sessoes(self, abas: list[dict]) -> None:
        abertas = {a.get("id") for a in abas}
        for aba_id in [i for i in self._sessoes() if i not in abertas]:
            self._sessoes().pop(aba_id, None)

    def _na_tela_de_perfis(self, aba: dict, servico: str) -> bool:
        """A aba está mostrando "Quem está assistindo?" (a extensão confere, sem clicar em nada)."""
        try:
            r = self._extensao().pedir("perfil", {"aba": aba["id"], "dominio": self._servicos_de_video()[servico][0],
                                                  "so_ver": True}, espera=4)
        except Exception as erro:
            log.info("Extensao nao conferiu a tela de perfis: %s", erro)
            return False
        return isinstance(r, dict) and bool(r.get("tela"))

    # --- decidir o perfil ----------------------------------------------------------------------------
    def _escolher_perfil(self, servico: str, falado: str | None, seguir) -> None:
        """Decide o perfil (e a aba) ANTES de buscar/tocar/continuar e chama seguir(perfil, id_da_aba).
        perfil None = nenhum perfil cadastrado e nenhum falado (o jeito de antes). Na dúvida, pergunta."""
        perfis = perfis_configurados(self.cfg)
        padrao = perfil_padrao(self.cfg)
        ext = self._extensao()
        if (falado or perfis) and ext:
            from ..ponte import desatualizada
            if desatualizada(getattr(ext, "versao", "")):
                self.voz.falar("Pra escolher o perfil a extensão do Brave precisa ser atualizada. Recarregue ela: "
                               "o passo a passo está no painel, na página YouTube.")
                return
        abas = self._abas_abertas()
        self._limpar_sessoes(abas)
        do_servico = [a for a in abas if self._servico_da_aba(a) == servico]
        if falado:
            nome = achar_perfil(falado, perfis) if perfis else self._original(falado).strip().title()
            if not nome:
                self._perguntar_qual_perfil(servico, perfis, seguir,
                                            f"Não conheço o perfil {self._original(falado)}. ")
                return
            self._conferir_aba(servico, nome, do_servico, abas, seguir)
            return
        if not perfis:
            seguir(None, None)
            return
        confirmados = sorted({p for p in map(self._perfil_da_aba, do_servico) if p})
        if len(confirmados) > 1:
            self._perguntar_qual_perfil(servico, confirmados, seguir,
                                        f"Encontrei {self._no(servico, '')} nos perfis {lista_falada(confirmados, 'e')}. ")
            return
        if confirmados:
            p = confirmados[0]
            if p == padrao or len(perfis) == 1:
                self._conferir_aba(servico, p, do_servico, abas, seguir)
            else:
                self._confirmar_perfil(servico, p, [x for x in perfis if x != p], seguir,
                                       f"{maiuscula(self._no(servico, ''))} está no perfil {p}. Uso ele?")
            return
        if len(perfis) == 1:
            self._conferir_aba(servico, perfis[0], do_servico, abas, seguir)
            return
        if padrao:
            desconhecida = self._aba_do_perfil(do_servico, abas)
            if desconhecida and not self._na_tela_de_perfis(desconhecida, servico):
                # a pergunta "ela está no perfil Arthur?" já confirma o padrão (uma pergunta só)
                self._conferir_aba(servico, padrao, do_servico, abas, seguir)
                return
            self._confirmar_perfil(servico, padrao, [x for x in perfis if x != padrao], seguir,
                                   f"Devo usar o perfil {padrao} {self._no(servico)}?")
            return
        self._perguntar_qual_perfil(servico, perfis, seguir)

    def _aba_do_perfil(self, candidatas: list[dict], abas: list[dict]) -> dict | None:
        """Entre as abas do serviço (sem perfil confirmado), a que seria usada: a do monitor pedido, senão
        a da frente / que toca / usada por último."""
        candidatas = [a for a in candidatas if not self._perfil_da_aba(a)]
        if sistema.MONITOR_ALVO:
            ali = [a for a in candidatas if self._monitor_da_aba(a, abas) == sistema.MONITOR_ALVO]
            candidatas = ali or candidatas
        return max(candidatas, key=self._preferencia_de_aba, default=None)

    def _conferir_aba(self, servico: str, perfil: str, do_servico: list[dict], abas: list[dict], seguir) -> None:
        """Com o perfil decidido: usa a aba já confirmada nele; aba em outro perfil = não mexe; aba sem
        perfil confirmado = pergunta (ou deixa a tela "Quem está assistindo?" escolher)."""
        if sistema.JANELA_NOVA or not self._extensao():
            seguir(perfil, None)
            return
        mesmo = [a for a in do_servico if self._perfil_da_aba(a) == perfil]
        if mesmo:
            ali = [a for a in mesmo if not sistema.MONITOR_ALVO or self._monitor_da_aba(a, abas) == sistema.MONITOR_ALVO]
            seguir(perfil, max(ali or mesmo, key=self._preferencia_de_aba)["id"])
            return
        aba = self._aba_do_perfil(do_servico, abas)
        if aba is None:
            if do_servico:   # todas as abas do serviço estão confirmadas em OUTRO perfil
                outro = self._perfil_da_aba(do_servico[0])
                self.voz.falar(f"{maiuscula(self._no(servico, ''))} está aberta no perfil {outro} e você pediu "
                               f"{perfil}. Troque o perfil na tela e fale de novo. Não mexi em nada.")
                return
            seguir(perfil, None)   # nada aberto: abre e escolhe na tela "Quem está assistindo?"
            return
        if self._na_tela_de_perfis(aba, servico):
            seguir(perfil, aba["id"])
            return
        onde = ""
        if len(do_servico) > 1:
            monitor = self._monitor_da_aba(aba, abas)
            onde = f" do monitor {monitor}" if monitor else ""
        criado = time.time()

        def responder(resposta: str):
            decisao = sim_ou_nao(resposta)
            if not self._plano_valendo(criado):
                return
            if decisao == "sim":
                if aba["id"] not in {a.get("id") for a in self._abas_abertas()}:
                    self.voz.falar(f"A aba {self._no(servico, 'd')} fechou. Não mexi em nada.")
                    return
                self._lembrar_perfil(aba["id"], servico, perfil)
                seguir(perfil, aba["id"])
            elif decisao == "nao":
                self.voz.falar(f"Tá bom. Troque para o perfil {perfil} na tela e fale de novo. Não mexi em nada.")
            elif decisao == "desistir":
                self.falar("cancelado")
            else:
                self.voz.falar("Não entendi se é sim ou não. Não mexi em nada.")
        responder.aceita_nao = True
        self.perguntar(f"{maiuscula(self._no(servico, ''))}{onde} já está aberta. Ela está no perfil {perfil}?",
                       responder, espera=15)

    def _plano_valendo(self, criado: float) -> bool:
        if time.time() - criado <= PLANO_EXPIRA_SEG:
            return True
        self.voz.falar("Demorou um pouco e as janelas podem ter mudado. Fala o pedido de novo. Não mexi em nada.")
        return False

    def _perguntar_qual_perfil(self, servico: str, opcoes: list[str], seguir, antes: str = "") -> None:
        criado = time.time()

        def responder(resposta: str):
            resposta = resposta or self._frase_original   # respondeu só "Mestre" (= a palavra de ativação)
            if not self._plano_valendo(criado):
                return
            escolhido = achar_perfil(resposta, opcoes)
            if escolhido:
                self._escolher_perfil(servico, escolhido, seguir)   # confere a aba de novo, com o que está aberto agora
            elif sim_ou_nao(resposta) == "desistir":
                self.falar("cancelado")
            else:
                self.voz.falar("Não peguei o perfil. Não mexi em nada. Fala de novo dizendo no perfil "
                               f"{opcoes[0]}, por exemplo.")
        responder.aceita_nao = True
        self.perguntar(f"{antes}Qual perfil {self._no(servico)}? {lista_falada(opcoes)}?", responder, espera=15)

    def _confirmar_perfil(self, servico: str, perfil: str, outros: list[str], seguir, pergunta: str) -> None:
        criado = time.time()

        def responder(resposta: str):
            resposta = resposta or self._frase_original   # respondeu só "Mestre" (= a palavra de ativação)
            decisao = sim_ou_nao(resposta)
            escolhido = achar_perfil(resposta, [perfil] + outros)
            if not self._plano_valendo(criado):
                return
            if decisao == "sim" or escolhido == perfil:
                self._escolher_perfil(servico, perfil, seguir)
            elif escolhido:
                self._escolher_perfil(servico, escolhido, seguir)
            elif decisao == "nao" and outros:
                self._perguntar_qual_perfil(servico, outros, seguir, "Então ")
            elif decisao in ("nao", "desistir"):
                self.falar("cancelado")
            else:
                self.voz.falar("Não entendi se é sim ou não. Não mexi em nada.")
        responder.aceita_nao = True
        self.perguntar(pergunta, responder, espera=15)
