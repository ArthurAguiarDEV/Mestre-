"""Mídia e vídeo sem navegador real: qual serviço, aba, janela e monitor; e a escuta enquanto o Mestre fala.

Tudo com dublês: extensão do Brave falsa (abas em memória), monitores falsos, voz muda, Whisper falso.
Nada abre, nada toca, nada é gravado nos arquivos do usuário (memória e estado ficam em dublês).

    venv\\Scripts\\python -m unittest testes.teste_midia_escuta
"""
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import yaml

from app import estado, memoria, sistema, validacao
from app.ponte import VERSAO_EXTENSAO

PROJETO = Path(__file__).resolve().parents[1]
MONITORES_2 = [{"numero": 1, "x": 0, "y": 0, "largura": 1920, "altura": 1040, "marca": "", "hz": 0},
               {"numero": 2, "x": 1920, "y": 0, "largura": 1920, "altura": 1040, "marca": "", "hz": 0}]
MONITORES_3 = MONITORES_2 + [{"numero": 3, "x": 3840, "y": 0, "largura": 1920, "altura": 1040, "marca": "", "hz": 0}]


def isolar_arquivos(teste: unittest.TestCase) -> None:
    """Memória e estado apontam para uma pasta temporária: nenhum teste escreve em memoria/ nem em logs/."""
    pasta = tempfile.TemporaryDirectory(prefix="mestre_midia_")
    teste.addCleanup(pasta.cleanup)
    raiz, projeto = Path(pasta.name), memoria.PASTA_MEMORIA.parent
    for nome in [n for n in vars(memoria) if n.startswith(("ARQUIVO_", "PASTA_", "BACKUP_"))]:
        p = patch.object(memoria, nome, raiz / Path(getattr(memoria, nome)).relative_to(projeto))
        p.start()
        teste.addCleanup(p.stop)
    for alvo, nome in ((estado, "_publicar"), (memoria, "registrar_tempo")):
        p = patch.object(alvo, nome, lambda *a, **k: None)
        p.start()
        teste.addCleanup(p.stop)


def aba(ident, url, monitor=1, audivel=False, ativa=True, janela=None, acesso=0, abas_na_janela=1):
    """Uma aba como a extensão manda (a posição da janela diz o monitor)."""
    return {"id": ident, "janela": janela or ident, "titulo": f"aba {ident}", "url": url, "ativa": ativa,
            "audivel": audivel, "ultimo_acesso": acesso, "abas_na_janela": abas_na_janela,
            "janela_x": 1920 * (monitor - 1) + 100, "janela_y": 0, "janela_largura": 800, "janela_altura": 600,
            "janela_estado": "normal", "video_pausado": None, "video_pausado_em": 0}


YT, NETFLIX, DISNEY = "https://www.youtube.com/watch?v=1", "https://www.netflix.com/watch/2", "https://www.disneyplus.com/play/3"


class ExtensaoFalsa:
    versao = VERSAO_EXTENSAO   # a extensão atual (a velha é testada à parte)

    def __init__(self, abas):
        self.abas = abas
        self.pedidos = []

    def conectada(self):
        return True

    def pedir(self, acao, arg=None, espera=8.0, aba=None):
        self.pedidos.append((acao, arg))
        if acao == "abas":
            return self.abas
        if acao == "video":
            return "ok"
        if acao == "ir":
            return {"id": (arg or {}).get("aba") or 999}
        if acao in ("focar", "separar"):
            return {"titulo": "aba"}
        return None

    def feitos(self, acao):
        return [arg for a, arg in self.pedidos if a == acao]


class VozFalsa:
    motor = "edge"

    def __init__(self):
        self.ditos, self.trocas, self.registro = [], [], None

    def falar(self, texto, *a, **k):
        self.ditos.append(str(texto))

    def configurar(self, **k):
        pass


class SemIA:
    ligado = False

    def esquecer(self):
        pass


class ComandosDeVideo(unittest.TestCase):
    """Comandos ambíguos: o Mestre pergunta; comando claro: executa sem perguntar."""

    def setUp(self):
        from app.comandos import Executor
        from app.vocabulario import Vocabulario
        cfg = yaml.safe_load((PROJETO / "config.exemplo.yaml").read_text(encoding="utf-8")) or {}
        cfg.setdefault("assistente", {})["palavra_ativacao"] = "mestre"
        cfg["sites"] = {"netflix": "https://www.netflix.com", "disney": "https://www.disneyplus.com"}
        cfg["janelas"] = {"sempre_no_principal": True}
        isolar_arquivos(self)
        self.efeitos = []   # (o que o Mestre fez no Windows)
        for alvo, nome, valor in (
                (memoria, "registrar", lambda *a, **k: None), (memoria, "registrar_tempo", lambda *a, **k: None),
                (memoria, "ouvido", lambda *a, **k: None),
                (estado, "atualizar", lambda *a, **k: None), (estado, "definir", lambda *a, **k: None),
                (sistema, "monitores", lambda: MONITORES_2), (sistema, "janelas_abertas", lambda: []),
                (sistema, "monitor_do_mouse", lambda: None), (sistema, "janela_pelo_titulo", lambda *a, **k: 77),
                (sistema, "monitor_da_janela", lambda hwnd: 1),
                (sistema, "midia", lambda acao: self.efeitos.append(("midia", acao))),
                (sistema, "abrir_site", lambda url: self.efeitos.append(
                    ("abrir_site", url, sistema.MONITOR_ALVO, sistema.JANELA_NOVA))),
                (sistema, "mover_janela_para_monitor", lambda hwnd, n, *a, **k: self.efeitos.append(("mover", hwnd, n)))):
            p = patch.object(alvo, nome, valor)
            p.start()
            self.addCleanup(p.stop)
        self.voz = VozFalsa()
        self.ex = Executor(cfg, self.voz, SemIA(), Vocabulario())
        self.ex._yt = lambda: None
        self.ex._seguir_no_streaming = lambda *a, **k: None   # (a busca/clique no site roda numa linha separada)
        self.ext = None

    def com_abas(self, *abas):
        self.ext = ExtensaoFalsa(list(abas))
        self.ex.ponte = self.ext
        return self.ext

    def diga(self, frase):
        """Como o ouvido entrega: comando sem a palavra + a frase inteira. Devolve o que ele falou."""
        from app.config import palavras_ativacao
        from app.texto import extrair_comando
        antes = len(self.voz.ditos)
        self.ex.ultimo_comando = None
        achou, comando = extrair_comando(frase, palavras_ativacao(self.ex.cfg))
        self.ex._executar(comando if achou else frase, frase)
        return self.voz.ditos[antes:]

    # --- pausar: qual serviço -----------------------------------------------------------------------
    def test_pausa_o_video_com_dois_servicos_tocando_pergunta_qual(self):
        ext = self.com_abas(aba(1, YT, audivel=True), aba(2, NETFLIX, monitor=2, audivel=True))
        falas = self.diga("Mestre, pausa o vídeo")
        self.assertTrue(any("no YouTube e na Netflix" in f and "Qual você quer pausar" in f for f in falas), falas)
        self.assertEqual(ext.feitos("video"), [], "não pode pausar nada antes da resposta")
        self.assertEqual(self.efeitos, [], "nem a tecla de mídia geral")
        self.diga("a Netflix")
        self.assertEqual(ext.feitos("video"), [{"aba": 2, "dominio": "netflix.com", "pausar": True}])

    def test_pausa_o_video_da_netflix_age_na_netflix_sem_perguntar(self):
        ext = self.com_abas(aba(1, YT, audivel=True), aba(2, NETFLIX, monitor=2, audivel=True))
        falas = self.diga("Mestre, pausa o vídeo da Netflix")
        self.assertEqual(self.ex.ultimo_comando, "_cmd_controle_video")
        self.assertEqual(ext.feitos("video"), [{"aba": 2, "dominio": "netflix.com", "pausar": True}])
        self.assertFalse(any("?" in f for f in falas), falas)

    def test_pausa_a_disney_e_continua_o_filme_na_disney(self):
        ext = self.com_abas(aba(3, DISNEY, audivel=True))
        self.diga("Mestre, pausa a Disney")
        self.diga("Mestre, continua o filme na Disney")
        self.assertEqual(ext.feitos("video"), [{"aba": 3, "dominio": "disneyplus.com", "pausar": True},
                                               {"aba": 3, "dominio": "disneyplus.com", "pausar": False}])

    def test_unico_video_tocando_pausa_sem_perguntar(self):
        ext = self.com_abas(aba(1, YT, audivel=False), aba(2, NETFLIX, monitor=2, audivel=True))
        falas = self.diga("Mestre, pausa o vídeo")
        self.assertEqual(ext.feitos("video"), [{"aba": 2, "dominio": "netflix.com", "pausar": True}])
        self.assertFalse(any("?" in f for f in falas), falas)

    def test_so_youtube_continua_com_o_comando_do_youtube(self):
        self.com_abas(aba(1, YT, audivel=True))
        self.diga("Mestre, pausa o vídeo")
        self.assertEqual(self.ex.ultimo_comando, "_cmd_youtube_controle")
        self.diga("Mestre, pausa o vídeo do YouTube")
        self.assertEqual(self.ex.ultimo_comando, "_cmd_youtube_controle")

    def test_mesmo_servico_em_duas_telas_pergunta_o_monitor(self):
        ext = self.com_abas(aba(4, DISNEY, monitor=1, audivel=True), aba(5, DISNEY, monitor=2, audivel=True))
        falas = self.diga("Mestre, pausa a Disney")
        self.assertTrue(any("No monitor 1 ou no 2" in f for f in falas), falas)
        self.assertEqual(ext.feitos("video"), [])
        self.diga("no dois")
        self.assertEqual([p["aba"] for p in ext.feitos("video")], [5])

    def test_disse_o_monitor_nao_pergunta(self):
        ext = self.com_abas(aba(4, DISNEY, monitor=1, audivel=True), aba(5, DISNEY, monitor=2, audivel=True))
        falas = self.diga("Mestre, pausa a Disney do monitor 2")
        self.assertEqual([p["aba"] for p in ext.feitos("video")], [5])
        self.assertFalse(any("?" in f for f in falas), falas)

    def test_nenhum_video_aberto_pergunta_antes_do_pause_geral(self):
        self.com_abas(aba(1, "https://www.google.com/"))
        falas = self.diga("Mestre, pausa o vídeo")
        self.assertTrue(any("pause geral" in f for f in falas), falas)
        self.assertEqual(self.efeitos, [])
        self.diga("sim")
        self.assertEqual(self.efeitos, [("midia", "tocar_pausar")])

    def test_nenhum_video_aberto_e_resposta_nao_nao_mexe_em_nada(self):
        self.com_abas(aba(1, "https://www.google.com/"))
        self.diga("Mestre, pausa o vídeo")
        self.diga("não")
        self.assertEqual(self.efeitos, [])

    def test_servico_dito_sem_aba_avisa(self):
        ext = self.com_abas(aba(1, YT, audivel=True))
        falas = self.diga("Mestre, pausa a Netflix")
        self.assertTrue(any("Não achei aba da Netflix" in f for f in falas), falas)
        self.assertEqual(ext.feitos("video"), [])

    def test_extensao_desatualizada_avisa_em_vez_de_falhar_calada(self):
        ext = self.com_abas(aba(2, NETFLIX, audivel=True))
        ext.versao = "2.3"
        falas = self.diga("Mestre, pausa a Netflix")
        self.assertTrue(any("desatualizada" in f for f in falas), falas)
        self.assertEqual(ext.feitos("video"), [])

    # --- abrir / tocar: qual serviço, reutilizar ou abrir, qual monitor ------------------------------
    def test_quero_assistir_sem_servico_pergunta_o_servico(self):
        falas = self.diga("Mestre, quero assistir Fallout")
        self.assertEqual(self.ex.ultimo_comando, "_cmd_streaming")
        self.assertTrue(any("Em qual serviço" in f and "YouTube" in f for f in falas), falas)
        self.assertEqual(self.efeitos, [], "não escolhe serviço sozinho")
        self.diga("na Prime")
        self.assertEqual(len(self.efeitos), 1)
        self.assertIn("primevideo.com", self.efeitos[0][1])
        self.assertIn("Fallout", self.efeitos[0][1])

    def test_quero_assistir_resposta_youtube_busca_no_youtube(self):
        from app import youtube
        with patch.object(youtube, "buscar_video", lambda termo: "https://www.youtube.com/watch?v=fallout"):
            self.diga("Mestre, quero assistir Fallout")
            self.diga("no YouTube")
        self.assertEqual([e[1] for e in self.efeitos], ["https://www.youtube.com/watch?v=fallout"])

    def test_toca_na_disney_no_monitor_2_reusa_a_aba_que_ja_esta_la(self):
        ext = self.com_abas(aba(1, YT, monitor=1), aba(6, DISNEY, monitor=2))
        self.diga("Mestre, toca Loki na Disney no monitor 2")
        self.assertEqual([p.get("aba") for p in ext.feitos("ir")], [6])
        self.assertEqual([e for e in self.efeitos if e[0] in ("abrir_site", "mover")], [])

    def test_toca_na_disney_no_monitor_2_leva_a_aba_de_outro_monitor(self):
        ext = self.com_abas(aba(6, DISNEY, monitor=1, abas_na_janela=3))
        self.diga("Mestre, toca Loki na Disney no monitor 2")
        self.assertEqual(ext.feitos("separar"), [6], "tira a aba da janela que tem outras abas")
        self.assertIn(("mover", 77, 2), self.efeitos)
        self.assertEqual([p.get("aba") for p in ext.feitos("ir")], [6])
        self.assertFalse([e for e in self.efeitos if e[0] == "abrir_site"], "não abre outra Disney")

    def test_toca_na_disney_no_monitor_2_sem_disney_aberta_abre_janela_la(self):
        ext = self.com_abas(aba(1, YT))
        self.diga("Mestre, toca Loki na Disney no monitor 2")
        self.assertEqual([(e[0], e[2]) for e in self.efeitos], [("abrir_site", 2)])
        self.assertEqual(ext.feitos("ir"), [])

    def test_toca_na_netflix_numa_janela_nova_nao_reusa(self):
        ext = self.com_abas(aba(2, NETFLIX))
        self.diga("Mestre, toca Dark na Netflix numa janela nova")
        self.assertEqual(self.ex.ultimo_comando, "_cmd_streaming")
        self.assertEqual([(e[0], e[3]) for e in self.efeitos], [("abrir_site", True)])
        self.assertEqual(ext.feitos("ir"), [])

    def test_abre_a_netflix_ja_aberta_no_monitor_pedido_so_usa(self):
        ext = self.com_abas(aba(2, NETFLIX, monitor=2))
        falas = self.diga("Mestre, abre a Netflix no monitor 2")
        self.assertEqual(ext.feitos("focar"), [2])
        self.assertTrue(any("já estava aberto no monitor 2" in f for f in falas), falas)
        self.assertEqual([e for e in self.efeitos if e[0] in ("abrir_site", "mover")], [])

    def test_abre_a_netflix_ja_aberta_sem_monitor_reusa_a_aba(self):
        ext = self.com_abas(aba(2, NETFLIX))
        self.diga("Mestre, abre a Netflix")
        self.assertEqual(ext.feitos("focar"), [2])
        self.assertEqual(self.efeitos, [])

    def test_abre_a_netflix_numa_janela_nova_abre_outra(self):
        ext = self.com_abas(aba(2, NETFLIX))
        self.diga("Mestre, abre a Netflix numa janela nova")
        self.assertEqual(self.ex.ultimo_comando, "_cmd_abrir")
        self.assertEqual(ext.feitos("focar"), [])
        self.assertEqual([(e[0], e[3]) for e in self.efeitos], [("abrir_site", True)])

    def test_abre_o_youtube_numa_janela_nova_abre_outra(self):
        self.com_abas(aba(1, YT))
        self.diga("Mestre, abre o YouTube numa janela nova no monitor 2")
        self.assertEqual(self.ex.ultimo_comando, "_cmd_youtube")
        self.assertEqual([(e[0], e[2], e[3]) for e in self.efeitos], [("abrir_site", 2, True)])

    def test_janela_nova_nao_vaza_para_o_proximo_comando(self):
        self.com_abas(aba(2, NETFLIX))
        self.diga("Mestre, abre a Netflix numa janela nova")
        self.diga("Mestre, abre a Netflix")
        self.assertFalse(sistema.JANELA_NOVA)

    def test_joga_pro_outro_monitor_com_dois_monitores_nao_pergunta(self):
        self.com_abas(aba(2, NETFLIX, monitor=1))
        falas = self.diga("Mestre, joga a Netflix pro outro monitor")
        self.assertEqual(self.ex.ultimo_comando, "_cmd_mover")
        self.assertIn(("mover", 77, 2), self.efeitos)
        self.assertFalse(any("?" in f for f in falas), falas)

    def test_joga_pro_outro_monitor_com_tres_monitores_pergunta_qual(self):
        with patch.object(sistema, "monitores", lambda: MONITORES_3):
            self.com_abas(aba(2, NETFLIX, monitor=1))
            falas = self.diga("Mestre, joga a Netflix pro outro monitor")
            self.assertTrue(any("Para qual monitor" in f and "2 ou o 3" in f for f in falas), falas)
            self.assertFalse([e for e in self.efeitos if e[0] == "mover"])
            self.diga("o três")
        self.assertIn(("mover", 77, 3), self.efeitos)


# ======================================================================================================
#  Escuta enquanto o Mestre fala (sem microfone: o que o Whisper "ouviu" é escrito no teste)
# ======================================================================================================
class VozFalando:
    """A voz no meio de uma resposta."""

    def __init__(self, texto=""):
        import threading
        self.falando = threading.Event()
        self.falando.set()
        self.terminou_em = 0.0
        self.texto = texto
        self.paradas = 0

    def texto_falando(self):
        return self.texto

    def parar(self):
        self.paradas += 1
        return True


class WhisperFalso:
    def __init__(self, *frases):
        self.frases = list(frases)
        self.pedidos = 0

    def transcrever(self, audio):
        self.pedidos += 1
        return self.frases.pop(0) if self.frases else ""


class DonoSempre:
    exigencia = 0.5

    def verificar(self, audio, em_conversa=False):
        return True, None, ""


class SegFalso:
    falando = False
    limiar = 500.0

    def reiniciar(self):
        pass


class EscutaDuranteAResposta(unittest.TestCase):
    """O que ele faz com o que ouve enquanto ELE está falando (caminho `_frase_eco`)."""

    def setUp(self):
        from app.ouvido import Ouvido
        isolar_arquivos(self)
        self.descartes, self.historico = [], []
        for alvo, nome, valor in (
                (memoria, "ouvido", lambda texto="", **k: self.descartes.append((texto, k.get("motivo")))),
                (memoria, "registrar", lambda *a, **k: self.historico.append((a, k))),
                (estado, "definir", lambda *a, **k: None), (estado, "atualizar", lambda *a, **k: None),
                (estado, "pausado", lambda: False), (validacao, "guardar_audio", lambda audio: None)):
            p = patch.object(alvo, nome, valor)
            p.start()
            self.addCleanup(p.stop)
        o = Ouvido.__new__(Ouvido)
        o.cfg, o.variacoes, o._vigia, o.detector = {}, ["assessor"], None, None
        o.verificador, o.acordar_tela, o.interromper = DonoSempre(), False, True
        o.espera_palavra, o.espera_cont, o.ganho, o.diagnostico = 0.0, 0.0, 1.0, False
        o._preparar_laco()
        self.o = o
        self.entregues = []

    def ouvir_falando(self, transcricao, tts="Agora são oito e meia da noite."):
        self.o.voz = VozFalando(tts)
        self.o.transcritor = WhisperFalso(transcricao)
        self.o._frase_eco(b"\x00\x00" * 16000, SegFalso(),
                          lambda comando, frase, seguimento=False: self.entregues.append(comando) or 0)
        return self.o.voz

    def motivos(self):
        return [m for _, m in self.descartes]

    def test_mestre_falando_e_voce_calado_nao_vira_comando(self):
        voz = self.ouvir_falando("")
        self.assertEqual(self.entregues, [])
        self.assertEqual(voz.paradas, 0)
        self.assertEqual(self.motivos(), ["falando"])

    def test_eco_da_propria_resposta_sem_a_palavra_e_descartado(self):
        voz = self.ouvir_falando("pausar vídeo", tts="Vou pausar vídeo agora.")
        self.assertEqual(self.entregues, [])
        self.assertEqual(voz.paradas, 0)
        self.assertEqual(self.motivos(), ["falando"])

    def test_para_so_interrompe_a_fala(self):
        voz = self.ouvir_falando("Assessor, para.")
        self.assertEqual(voz.paradas, 1)
        self.assertEqual(self.entregues, [], "“para” não executa mídia nenhuma")
        self.assertEqual(self.motivos(), ["interrompeu a fala"])
        rota = self.historico[-1][0][3]["rota"]
        self.assertEqual(rota, "ignorado (só parou de falar)")

    def test_pausa_o_video_durante_a_fala_interrompe_e_entrega_o_comando(self):
        voz = self.ouvir_falando("Assessor, pausa o vídeo.")
        self.assertEqual(voz.paradas, 1)
        self.assertEqual(self.entregues, ["pausa o video"])

    def test_pausa_o_video_sem_a_palavra_durante_a_fala_e_descartado(self):
        voz = self.ouvir_falando("pausa o vídeo")
        self.assertEqual((self.entregues, voz.paradas), ([], 0))
        self.assertEqual(self.motivos(), ["falando"])

    def test_palavra_seguida_do_texto_que_ele_mesmo_fala_e_eco(self):
        voz = self.ouvir_falando("Assessor pausa o vídeo", tts="Pra parar diga: Assessor, pausa o vídeo.")
        self.assertEqual((self.entregues, voz.paradas), ([], 0))
        self.assertEqual(self.motivos(), ["falando: eco da própria voz"])

    def test_blocos_gravados_com_ele_falando_passam_pelo_segundo_segmentador(self):
        """Ponta a ponta pelo `_bloco`: fala alta de 1 s + silêncio, tudo marcado como eco."""
        from app.audio import BLOCO, Segmentador
        self.o.voz = VozFalando("Resposta longa.")
        self.o.transcritor = WhisperFalso("Assessor, pausa o vídeo.")
        seg = Segmentador(500.0)
        alto = struct.pack(f"<{BLOCO}h", *([8000, -8000] * (BLOCO // 2)))
        silencio = b"\x00\x00" * BLOCO
        entregar = lambda comando, frase, seguimento=False: self.entregues.append(comando) or 0   # noqa: E731
        for bloco in [alto] * 10 + [silencio] * 10:
            self.o._bloco(bloco, True, seg, entregar)
        self.assertEqual(self.o.transcritor.pedidos, 1)
        self.assertEqual(self.entregues, ["pausa o video"])
        self.assertEqual(self.o.voz.paradas, 1)

    def test_fala_normal_nao_passa_pelo_caminho_do_eco(self):
        """Sem ele falando (eco=False) o bloco vai pelo segmentador normal, não pelo de eco."""
        from app.audio import BLOCO, Segmentador
        self.o.voz = VozFalando("")
        self.o.voz.falando.clear()
        self.o.transcritor = WhisperFalso("Assessor, pausa o vídeo.")
        seg = Segmentador(500.0)
        alto = struct.pack(f"<{BLOCO}h", *([8000, -8000] * (BLOCO // 2)))
        entregar = lambda comando, frase, seguimento=False: self.entregues.append(comando) or 0   # noqa: E731
        for bloco in [alto] * 10 + [b"\x00\x00" * BLOCO] * 12:
            self.o._bloco(bloco, False, seg, entregar)
        self.assertIsNone(self.o._seg_eco)
        self.assertEqual(self.entregues, ["pausa o video"])
        self.assertEqual(self.o.voz.paradas, 0)


if __name__ == "__main__":
    unittest.main()
