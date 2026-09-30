"""Roteamento seguro de streaming: serviço, título, janela/aba, monitor, perfil e ação.

Sem microfone, sem navegador e sem janela: extensão do Brave falsa (abas, tela "Quem está assistindo?" e
botões em memória), monitores falsos e voz muda. Nada abre, nada toca e nada é gravado nos arquivos do usuário.

    venv\\Scripts\\python -m unittest testes.teste_streaming_perfis
"""
import unittest
from unittest.mock import patch

from app import memoria, sistema
from app.comandos import perfis as modulo_perfis
from app.comandos.perfis import achar_perfil, perfil_da_frase, perfis_configurados, sim_ou_nao
from testes import teste_midia_escuta
from testes.teste_midia_escuta import DISNEY, NETFLIX, YT, ExtensaoFalsa, aba

PERFIS = ["Arthur", "Mestre", "Magnífico"]
PALAVRAS_DE_SEGREDO = ("senha", "password", "token", "cookie", "email", "e-mail", "sessao", "session")


class ExtensaoComPerfis(ExtensaoFalsa):
    """Extensão falsa que também sabe a tela de perfis e os botões da página."""

    def __init__(self, abas, tela=(), perfis_na_tela=PERFIS, botoes=("continuar", "assistir")):
        super().__init__(abas)
        self.tela = set(tela)            # abas mostrando "Quem está assistindo?"
        self.perfis_na_tela = list(perfis_na_tela)
        self.botoes = [b.lower() for b in botoes]
        self.escolhidos = []             # (aba, perfil) clicados na tela de perfis
        self.cliques = []                # textos de botão clicados (fora a capa do título)

    def pedir(self, acao, arg=None, espera=8.0, aba=None):
        if acao == "perfil":
            self.pedidos.append((acao, arg))
            ident = arg.get("aba") or next((a["id"] for a in self.abas if arg.get("dominio", "?") in a["url"]), 999)
            if ident not in self.tela:
                return {"resultado": "sem_tela", "tela": False, "aba": ident}
            if arg.get("so_ver"):
                return {"resultado": "tela", "tela": True, "aba": ident}
            if arg.get("nome") in self.perfis_na_tela:
                self.tela.discard(ident)
                self.escolhidos.append((ident, arg["nome"]))
                return {"resultado": "selecionei", "tela": True, "aba": ident}
            return {"resultado": "nao_achei", "tela": True, "aba": ident}
        if acao == "buscar":
            self.pedidos.append((acao, arg))
            return "digitei"
        if acao == "clicar":
            self.pedidos.append((acao, arg))
            if arg.get("modo") == "titulo":
                return "capa"
            achado = next((t for t in arg.get("textos", []) if t in self.botoes), None)
            if achado:
                self.cliques.append(achado)
                return achado
            return "nao_achei"
        return super().pedir(acao, arg, espera, aba)


class Base(unittest.TestCase):
    # o mesmo Executor com dublês dos testes de mídia (sem importar a classe: senão os testes dela rodam de novo)
    diga = teste_midia_escuta.ComandosDeVideo.diga

    def setUp(self, perfis=None, padrao=""):
        teste_midia_escuta.ComandosDeVideo.setUp(self)
        self.ex.cfg["streaming"] = {"perfis": list(PERFIS if perfis is None else perfis), "perfil_padrao": padrao}
        self.ex.PAUSA_STREAMING = 0
        self.ex._em_segundo_plano = lambda funcao, *args: funcao(*args)   # a busca no site roda na hora
        del self.ex._seguir_no_streaming   # (o ComandosDeVideo desliga; aqui o passo do perfil importa)
        self.registrados = []
        p = patch.object(memoria, "registrar", lambda *a, **k: self.registrados.append(a))
        p.start()
        self.addCleanup(p.stop)

    def com_abas(self, *abas, **extra):
        self.ext = ExtensaoComPerfis(list(abas), **extra)
        self.ex.ponte = self.ext
        return self.ext

    def acoes(self, ext):
        """O que mexeu em aba, janela ou vídeo (ler a lista de abas e conferir a tela de perfis não conta)."""
        return [(a, arg) for a, arg in ext.pedidos if a in ("ir", "focar", "separar", "juntar", "video", "buscar", "clicar")
                or (a == "perfil" and not (arg or {}).get("so_ver"))] + \
            [e for e in self.efeitos if e[0] in ("abrir_site", "mover", "midia")]

    def perguntou(self, falas, trecho):
        self.assertTrue(any(trecho in f for f in falas), f"esperava pergunta com {trecho!r}: {falas}")


# ======================================================================================================
#  1-4 e 8-10: serviço e perfil
# ======================================================================================================
class ServicoEPerfil(Base):
    def setUp(self):
        super().setUp(padrao="")

    # 1. serviço único identificado
    def test_servico_dito_e_perfil_dito_nao_pergunta_nada(self):
        ext = self.com_abas(aba(1, YT))
        falas = self.diga("Mestre, toca Fallout na Prime no perfil Arthur")
        self.assertEqual(self.ex.ultimo_comando, "_cmd_streaming")
        self.assertFalse(any("?" in f for f in falas), falas)
        self.assertTrue(any("Procurando Fallout no Prime Video no perfil Arthur" in f for f in falas), falas)
        busca = ext.feitos("ir")[0]
        self.assertIn("primevideo.com", busca["url"])
        self.assertIn("Fallout", busca["url"])
        self.assertNotIn("perfil", busca["url"].lower(), "o perfil não vai na busca")

    def test_minha_serie_com_um_so_servico_aberto_usa_ele(self):
        ext = self.com_abas(aba(1, YT), aba(3, DISNEY, monitor=2), tela={3})
        falas = self.diga("Mestre, abre minha série no perfil Mestre")
        self.assertFalse(any("Em qual serviço" in f for f in falas), falas)
        self.assertEqual(ext.escolhidos, [(3, "Mestre")])
        self.assertEqual(ext.feitos("buscar"), [], "sem título não procura 'minha'")
        self.assertTrue(any("Abri a Disney no perfil Mestre" in f for f in falas), falas)

    # 2. várias possibilidades geram pergunta
    def test_minha_serie_com_dois_servicos_abertos_pergunta_qual(self):
        ext = self.com_abas(aba(2, NETFLIX), aba(3, DISNEY, monitor=2))
        falas = self.diga("Mestre, abre minha série")
        self.perguntou(falas, "Em qual serviço? Disney ou Netflix?")
        self.assertEqual(self.acoes(ext), [], "nada antes da resposta")
        falas = self.diga("a Disney")
        self.perguntou(falas, "Qual perfil na Disney? Arthur, Mestre ou Magnífico?")
        self.assertEqual(self.acoes(ext), [])

    def test_continua_a_serie_sem_servico_nem_aba_pergunta_o_servico(self):
        ext = self.com_abas(aba(1, YT))
        falas = self.diga("Mestre, continua a série que eu estava vendo")
        self.perguntou(falas, "Em qual serviço?")
        self.assertEqual(self.acoes(ext), [])

    # 3. perfil explícito é respeitado
    def test_perfil_dito_e_o_que_e_escolhido_na_tela_de_perfis(self):
        self.ex.cfg["streaming"]["perfil_padrao"] = "Arthur"
        ext = self.com_abas(aba(1, YT), tela={999})   # (999 = a aba nova que a extensão abre)
        falas = self.diga("Mestre, toca Loki na Disney no perfil Mestre")
        self.assertFalse(any("?" in f for f in falas), falas)
        self.assertEqual(ext.escolhidos, [(999, "Mestre")], "nunca o padrão nem o primeiro da lista")
        self.assertEqual([b["texto"] for b in ext.feitos("buscar")], ["Loki"])

    def test_perfil_dito_diferente_do_perfil_da_aba_nao_mexe(self):
        ext = self.com_abas(aba(3, DISNEY))
        self.ex._lembrar_perfil(3, "Disney", "Arthur")
        falas = self.diga("Mestre, toca Loki na Disney no perfil Mestre")
        self.perguntou(falas, "está aberta no perfil Arthur e você pediu Mestre")
        self.assertEqual(self.acoes(ext), [])

    def test_perfil_dito_que_nao_existe_na_tela_para_sem_tocar(self):
        ext = self.com_abas(aba(1, YT), tela={999}, perfis_na_tela=["Arthur"])
        falas = self.diga("Mestre, toca Loki na Disney no perfil Mestre")
        self.perguntou(falas, "Não achei o perfil Mestre na tela de perfis da Disney")
        self.assertEqual(ext.escolhidos, [])
        self.assertEqual(ext.feitos("buscar"), [], "não busca nem dá play num perfil errado")

    def test_perfil_com_acento_casa_sem_acento(self):
        ext = self.com_abas(aba(1, YT), tela={999})
        self.diga("Mestre, toca Loki na Disney no perfil magnifico")
        self.assertEqual(ext.escolhidos, [(999, "Magnífico")])

    def test_aba_ja_confirmada_no_perfil_pedido_reusa_sem_perguntar(self):
        ext = self.com_abas(aba(2, NETFLIX))
        self.ex._lembrar_perfil(2, "Netflix", "Arthur")
        falas = self.diga("Mestre, toca Dark na Netflix no perfil Arthur")
        self.assertFalse(any("?" in f for f in falas), falas)
        self.assertEqual([p.get("aba") for p in ext.feitos("ir")], [2])

    def test_aba_aberta_sem_perfil_confirmado_pergunta_se_e_o_perfil(self):
        ext = self.com_abas(aba(2, NETFLIX))
        falas = self.diga("Mestre, toca Dark na Netflix no perfil Arthur")
        self.perguntou(falas, "A Netflix já está aberta. Ela está no perfil Arthur?")
        self.assertEqual(self.acoes(ext), [])
        self.diga("sim")
        self.assertEqual([p.get("aba") for p in ext.feitos("ir")], [2])
        # agora a sessão está confirmada: o próximo pedido não pergunta de novo
        falas = self.diga("Mestre, toca Ozark na Netflix no perfil Arthur")
        self.assertFalse(any("?" in f for f in falas), falas)

    def test_aba_na_tela_de_perfis_nao_pergunta_e_escolhe_la(self):
        ext = self.com_abas(aba(2, NETFLIX), tela={2})
        falas = self.diga("Mestre, toca Dark na Netflix no perfil Mestre")
        self.assertFalse(any("?" in f for f in falas), falas)
        self.assertEqual(ext.escolhidos, [(2, "Mestre")])

    def test_sem_tela_de_perfis_e_sem_confirmacao_nao_inicia_video(self):
        ext = self.com_abas(aba(1, YT))   # a Netflix nova já entra num perfil qualquer (sem a tela de perfis)
        falas = self.diga("Mestre, toca Dark na Netflix no perfil Arthur")
        self.perguntou(falas, "Não consegui confirmar o perfil Arthur na Netflix")
        self.assertEqual(ext.feitos("buscar") + ext.feitos("clicar"), [])

    # 4. perfil ausente com várias opções gera pergunta
    def test_sem_perfil_e_sem_padrao_pergunta_qual(self):
        ext = self.com_abas(aba(1, YT), tela={999})
        falas = self.diga("Mestre, toca Dark na Netflix")
        self.perguntou(falas, "Qual perfil na Netflix? Arthur, Mestre ou Magnífico?")
        self.assertEqual(self.acoes(ext), [])
        self.diga("o Magnífico")
        self.assertEqual(ext.escolhidos, [(999, "Magnífico")])

    def test_duas_abas_em_perfis_diferentes_pergunta_qual(self):
        ext = self.com_abas(aba(2, NETFLIX, monitor=1), aba(4, NETFLIX, monitor=2))
        self.ex._lembrar_perfil(2, "Netflix", "Arthur")
        self.ex._lembrar_perfil(4, "Netflix", "Mestre")
        falas = self.diga("Mestre, toca Dark na Netflix")
        self.perguntou(falas, "Encontrei a Netflix nos perfis Arthur e Mestre")
        self.assertEqual(self.acoes(ext), [])
        self.diga("Mestre")
        self.assertEqual([p.get("aba") for p in ext.feitos("ir")], [4])

    def test_aba_mudou_de_site_esquece_o_perfil(self):
        ext = self.com_abas(aba(2, "https://www.google.com/"))
        self.ex._lembrar_perfil(2, "Netflix", "Arthur")
        self.assertIsNone(self.ex._perfil_da_aba(ext.abas[0]))
        self.assertNotIn(2, self.ex._sessoes())

    # 8. cancelamento encerra o plano
    def test_cancela_encerra_a_pergunta_do_perfil(self):
        ext = self.com_abas(aba(1, YT), tela={999})
        self.diga("Mestre, toca Dark na Netflix")
        self.diga("cancela")
        self.assertIsNone(self.ex._pendente)
        self.assertEqual(self.acoes(ext), [])
        self.diga("Arthur")   # já não é resposta de nada
        self.assertEqual(ext.escolhidos, [])

    # 9. resposta inválida não executa
    def test_resposta_incerta_nao_executa(self):
        ext = self.com_abas(aba(2, NETFLIX))
        self.diga("Mestre, toca Dark na Netflix no perfil Arthur")
        falas = self.diga("acho que sim")
        self.perguntou(falas, "Não mexi em nada")
        self.assertEqual(self.acoes(ext), [])

    def test_perfil_que_nao_existe_na_resposta_nao_executa(self):
        ext = self.com_abas(aba(1, YT), tela={999})
        self.diga("Mestre, toca Dark na Netflix")
        falas = self.diga("Joana")
        self.perguntou(falas, "Não peguei o perfil")
        self.assertEqual(self.acoes(ext), [])

    def test_resposta_que_chega_tarde_nao_executa(self):
        ext = self.com_abas(aba(2, NETFLIX))
        self.diga("Mestre, toca Dark na Netflix no perfil Arthur")
        with patch.object(modulo_perfis, "PLANO_EXPIRA_SEG", -1):
            falas = self.diga("sim")
        self.perguntou(falas, "Fala o pedido de novo")
        self.assertEqual(self.acoes(ext), [])

    def test_nao_para_ela_esta_no_perfil_nao_mexe(self):
        ext = self.com_abas(aba(2, NETFLIX))
        self.diga("Mestre, toca Dark na Netflix no perfil Arthur")
        falas = self.diga("não")
        self.perguntou(falas, "Troque para o perfil Arthur na tela")
        self.assertEqual(self.acoes(ext), [])

    # 10. nenhuma credencial é registrada
    def test_nenhum_segredo_vai_para_extensao_config_ou_sessao(self):
        self.ex.cfg["streaming"]["perfis"] = PERFIS + ["arthur@gmail.com", "senha123", "token: abc"]
        self.assertEqual(perfis_configurados(self.ex.cfg), PERFIS)
        ext = self.com_abas(aba(2, NETFLIX), tela={2})
        self.diga("Mestre, toca Dark na Netflix no perfil Arthur")
        for acao, arg in ext.pedidos:
            texto = str(arg).lower()
            self.assertFalse(any(p in texto for p in PALAVRAS_DE_SEGREDO) or "@" in texto, (acao, arg))
            if acao == "perfil":
                self.assertLessEqual(set(arg), {"aba", "dominio", "nome", "so_ver"})
        for sessao in self.ex._sessoes().values():
            self.assertEqual(set(sessao), {"servico", "perfil", "quando"})
        self.assertFalse(any("@" in str(r) for r in self.registrados))

    def test_extensao_antiga_nao_tenta_escolher_perfil(self):
        ext = self.com_abas(aba(1, YT), tela={999})
        ext.versao = "2.4"
        falas = self.diga("Mestre, toca Dark na Netflix no perfil Arthur")
        self.perguntou(falas, "extensão do Brave precisa ser atualizada")
        self.assertEqual(self.acoes(ext), [])

    # continuar = de onde parou, nunca do começo sem confirmação
    def test_continuar_clica_em_continuar_e_nao_em_assistir(self):
        ext = self.com_abas(aba(2, NETFLIX), tela={2}, botoes=("continuar", "assistir"))
        self.diga("Mestre, continua The Office na Netflix no perfil Arthur")
        self.assertEqual(ext.cliques, ["continuar"])

    def test_continuar_sem_ponto_salvo_nao_comeca_do_inicio(self):
        ext = self.com_abas(aba(2, NETFLIX), tela={2}, botoes=("assistir", "assistir do comeco"))
        falas = self.diga("Mestre, continua The Office na Netflix no perfil Arthur")
        self.assertEqual(ext.cliques, [])
        self.perguntou(falas, "Não achei de onde você parou em The Office")


class PerfilPadrao(Base):
    def setUp(self):
        super().setUp(padrao="Arthur")

    def test_continuar_a_serie_na_disney_confirma_o_perfil_padrao(self):
        ext = self.com_abas(aba(1, YT), tela={999})
        falas = self.diga("Mestre, continua a série na Disney")
        self.perguntou(falas, "Devo usar o perfil Arthur na Disney?")
        self.assertEqual(self.acoes(ext), [])
        self.diga("sim")
        self.assertEqual(ext.escolhidos, [(999, "Arthur")])

    def test_nao_ao_padrao_pergunta_os_outros(self):
        ext = self.com_abas(aba(1, YT), tela={999})
        self.diga("Mestre, continua a série na Disney")
        falas = self.diga("não")
        self.perguntou(falas, "Então Qual perfil na Disney? Mestre ou Magnífico?")
        self.assertEqual(self.acoes(ext), [])
        self.diga("Mestre")
        self.assertEqual(ext.escolhidos, [(999, "Mestre")])

    def test_padrao_com_aba_aberta_faz_uma_pergunta_so(self):
        ext = self.com_abas(aba(3, DISNEY))
        falas = self.diga("Mestre, toca Loki na Disney")
        self.perguntou(falas, "A Disney já está aberta. Ela está no perfil Arthur?")
        self.diga("isso")
        self.assertEqual([p.get("aba") for p in ext.feitos("ir")], [3])

    def test_continua_o_filme_com_a_disney_tocando_so_retoma_o_video(self):
        ext = self.com_abas(aba(3, DISNEY, audivel=False))
        falas = self.diga("Mestre, continua o filme na Disney")
        self.assertEqual(self.ex.ultimo_comando, "_cmd_controle_video")
        self.assertEqual(ext.feitos("video"), [{"aba": 3, "dominio": "disneyplus.com", "pausar": False}])
        self.assertFalse(any("perfil" in f for f in falas), falas)


class SemPerfisCadastrados(Base):
    """11. Quem não cadastrou perfis continua com o comportamento de antes."""

    def setUp(self):
        super().setUp(perfis=[])

    def test_toca_na_disney_como_antes(self):
        ext = self.com_abas(aba(1, YT))
        falas = self.diga("Mestre, toca Agentes da Shield na Disney")
        self.assertFalse(any("?" in f for f in falas), falas)
        self.assertEqual([p for p in ext.pedidos if p[0] == "perfil"], [])
        self.assertEqual([b["texto"] for b in ext.feitos("buscar")], ["Agentes da Shield"])

    def test_perfil_dito_sem_cadastro_vale_como_foi_falado(self):
        ext = self.com_abas(aba(1, YT), tela={999}, perfis_na_tela=["Joana"])
        self.diga("Mestre, toca Loki na Disney no perfil Joana")
        self.assertEqual(ext.escolhidos, [(999, "Joana")])


# ======================================================================================================
#  5-7: janela, monitor e comando composto
# ======================================================================================================
class JanelasEMonitores(Base):
    # 5. janela ambígua gera pergunta
    def test_youtube_em_duas_janelas_pergunta_qual_antes_de_mover(self):
        ext = self.com_abas(aba(1, YT, monitor=1), aba(5, YT, monitor=2))
        falas = self.diga("Mestre, separa o YouTube pro monitor 2")
        self.perguntou(falas, "Tem YouTube em mais de uma janela: no monitor 1 e no 2. Qual eu uso?")
        self.assertEqual(self.acoes(ext), [])
        self.diga("o do monitor 1")
        self.assertEqual(ext.feitos("focar") + ext.feitos("separar"), [1])
        self.assertIn(("mover", 77, 2), self.efeitos)

    def test_duas_janelas_no_mesmo_monitor_nao_escolhe_sozinho(self):
        ext = self.com_abas(aba(1, YT, monitor=1), aba(5, YT, monitor=1))
        falas = self.diga("Mestre, joga o YouTube pro monitor 2")
        self.perguntou(falas, "Tem mais de uma janela com YouTube e não sei qual")
        self.assertEqual(self.acoes(ext), [])

    # 6. monitor ausente gera pergunta
    def test_joga_a_netflix_sem_monitor_pergunta_o_monitor(self):
        ext = self.com_abas(aba(2, NETFLIX, monitor=1))
        falas = self.diga("Mestre, joga a Netflix")
        self.assertEqual(self.ex.ultimo_comando, "_cmd_mover")
        self.perguntou(falas, "Para qual monitor vai Netflix? O 1 ou o 2?")
        self.assertEqual(self.acoes(ext), [])
        self.diga("no dois")
        self.assertIn(("mover", 77, 2), self.efeitos)

    # 7. comando composto não executa parcialmente
    def test_separa_youtube_e_disney_pergunta_antes_de_mexer(self):
        ext = self.com_abas(aba(1, YT, monitor=1, janela=10, abas_na_janela=2),
                            aba(3, DISNEY, monitor=1, janela=10, abas_na_janela=2))
        falas = self.diga("Mestre, separa o YouTube e a Disney")
        self.assertEqual(self.ex.ultimo_comando, "_cmd_mover")
        self.perguntou(falas, "Qual monitor pra cada um?")
        self.assertEqual(self.acoes(ext), [], "nem a primeira parte antes de resolver tudo")
        self.diga("YouTube no 1 e Disney no 2")
        self.assertEqual(ext.feitos("separar"), [1, 3])
        self.assertEqual([e for e in self.efeitos if e[0] == "mover"], [("mover", 77, 1), ("mover", 77, 2)])

    def test_separa_youtube_e_disney_so_separar(self):
        ext = self.com_abas(aba(1, YT, janela=10, abas_na_janela=2), aba(3, DISNEY, janela=10, abas_na_janela=2))
        self.diga("Mestre, separa o YouTube e a Disney")
        self.diga("só separar")
        self.assertEqual(ext.feitos("separar"), [1, 3])
        self.assertEqual([e for e in self.efeitos if e[0] == "mover"], [])

    def test_composto_com_um_alvo_fechado_nao_faz_nada(self):
        ext = self.com_abas(aba(1, YT, monitor=1))
        falas = self.diga("Mestre, separa o YouTube pro monitor 2 e a Netflix pro monitor 1")
        self.perguntou(falas, "Não achei Netflix aberto. Não mexi em nada.")
        self.assertEqual(self.acoes(ext), [])

    def test_composto_com_segundo_monitor_faltando_pergunta_so_ele(self):
        ext = self.com_abas(aba(1, YT, monitor=1), aba(3, DISNEY, monitor=1))
        falas = self.diga("Mestre, separa o YouTube pro monitor 2 e a Disney")
        self.perguntou(falas, "Para qual monitor vai Disney?")
        self.assertEqual(self.acoes(ext), [])
        self.diga("monitor 1")
        self.assertEqual([e for e in self.efeitos if e[0] == "mover"], [("mover", 77, 2), ("mover", 77, 1)])

    # 8 e 9 nas janelas
    def test_cancela_o_composto(self):
        ext = self.com_abas(aba(1, YT), aba(3, DISNEY))
        self.diga("Mestre, separa o YouTube e a Disney")
        self.diga("cancela")
        self.assertIsNone(self.ex._pendente)
        self.assertEqual(self.acoes(ext), [])

    def test_resposta_de_monitor_invalida_nao_executa(self):
        ext = self.com_abas(aba(1, YT), aba(3, DISNEY))
        self.diga("Mestre, separa o YouTube e a Disney")
        falas = self.diga("banana")
        self.perguntou(falas, "Não peguei os monitores. Não mexi em nada.")
        self.assertEqual(self.acoes(ext), [])

    def test_monitor_que_nao_existe_nao_executa(self):
        ext = self.com_abas(aba(2, NETFLIX))
        self.diga("Mestre, joga a Netflix")
        self.diga("monitor 3")
        self.assertEqual(self.acoes(ext), [])

    def test_alvo_desconhecido_nao_e_do_mover(self):
        self.com_abas(aba(1, YT))
        self.diga("Mestre, leva o lixo pra fora")
        self.assertNotEqual(self.ex.ultimo_comando, "_cmd_mover")


class PainelSemJanela(unittest.TestCase):
    """O campo "Perfis dos streamings" (painel > YouTube): monta e salva sem abrir janela nem customtkinter."""

    @staticmethod
    def metodos():
        import ast
        import re
        from pathlib import Path
        from types import SimpleNamespace
        from app import configuracao

        class Campo:
            def __init__(self, master=None, placeholder_text=""):
                self.texto = ""

            def insert(self, _pos, texto):
                self.texto = texto + self.texto

            def get(self):
                return self.texto

        origem = Path(__file__).resolve().parents[1] / "app" / "painel.py"
        classe = next(n for n in ast.parse(origem.read_text(encoding="utf-8")).body
                      if isinstance(n, ast.ClassDef) and n.name == "Painel")
        metodos = [n for n in classe.body if isinstance(n, ast.FunctionDef)
                   and n.name in {"_secao_perfis_streaming", "_salvar_youtube"}]
        falsa = ast.ClassDef(name="PainelFalso", bases=[], keywords=[], body=metodos, decorator_list=[])
        contexto = {"re": re, "configuracao": configuracao, "ctk": SimpleNamespace(CTkEntry=Campo),
                    "secao": lambda pagina, titulo, dica="": titulo,
                    "linha_campo": lambda f, rotulo, fabrica: fabrica(f)}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[falsa], type_ignores=[])), str(origem), "exec"), contexto)
        return contexto["PainelFalso"]

    def painel(self, cfg):
        from types import SimpleNamespace
        Painel = self.metodos()
        p = Painel()
        p.cfg, p.palavra, p.nome = cfg, "mestre", "Mestre"
        p._sec = lambda nome: cfg.get(nome) or {}
        p.var_yt_nav = p.var_yt_canal = p.var_yt_modo = SimpleNamespace(get=lambda: "Brave")
        p.NAVEGADORES, p.MODOS_YT = {"brave": "Brave"}, {"extensao": "Brave"}
        p.tab_canais = SimpleNamespace(valores=lambda: {})
        p._secao_perfis_streaming(None)
        return p

    def test_monta_com_o_que_esta_no_config(self):
        p = self.painel({"streaming": {"perfis": ["Arthur", "Magnífico"], "perfil_padrao": "Arthur"}})
        self.assertEqual(p.ent_perfis_streaming.get(), "Arthur, Magnífico")
        self.assertEqual(p.ent_perfil_padrao.get(), "Arthur")

    def test_salva_so_nomes(self):
        import io
        from ruamel.yaml.comments import CommentedMap
        from app import configuracao
        p = self.painel({})
        p.ent_perfis_streaming.insert(0, "Arthur, Mestre, arthur@gmail.com, minha senha, Magnífico, Arthur")
        p.ent_perfil_padrao.insert(0, "Arthur")
        c = CommentedMap()
        p._salvar_youtube(c)
        self.assertEqual(list(c["streaming"]["perfis"]), ["Arthur", "Mestre", "Magnífico"])
        self.assertEqual(str(c["streaming"]["perfil_padrao"]), "Arthur")
        saida = io.StringIO()
        configuracao._yaml().dump(c, saida)
        self.assertNotIn("@", saida.getvalue())
        self.assertNotIn("senha", saida.getvalue())


class FuncoesPuras(unittest.TestCase):
    def test_perfil_da_frase(self):
        self.assertEqual(perfil_da_frase("toca loki na disney no perfil mestre"), ("toca loki na disney", "mestre"))
        self.assertEqual(perfil_da_frase("continua a serie no perfil do arthur na netflix"),
                         ("continua a serie na netflix", "arthur"))
        self.assertEqual(perfil_da_frase("toca loki na disney"), ("toca loki na disney", None))

    def test_achar_perfil_so_nome_exato(self):
        self.assertEqual(achar_perfil("no perfil magnifico", PERFIS), "Magnífico")
        self.assertEqual(achar_perfil("Arthur", PERFIS), "Arthur")
        self.assertIsNone(achar_perfil("art", PERFIS))
        self.assertIsNone(achar_perfil("", PERFIS))

    def test_sim_ou_nao(self):
        self.assertEqual(sim_ou_nao("sim"), "sim")
        self.assertEqual(sim_ou_nao("isso mesmo"), "sim")
        self.assertEqual(sim_ou_nao("não"), "nao")
        self.assertEqual(sim_ou_nao("cancela"), "desistir")
        self.assertIsNone(sim_ou_nao("acho que sim"))
        self.assertIsNone(sim_ou_nao("talvez"))

    def test_perfis_do_config_so_nomes(self):
        cfg = {"streaming": {"perfis": ["Arthur", "arthur", "x@y.com", "minha senha", " Mestre "]}}
        self.assertEqual(perfis_configurados(cfg), ["Arthur", "Mestre"])
        self.assertEqual(perfis_configurados({}), [])
        self.assertEqual(perfis_configurados({"streaming": {"perfis": "Arthur, Mestre"}}), ["Arthur", "Mestre"])


if __name__ == "__main__":
    unittest.main()
