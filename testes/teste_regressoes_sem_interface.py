"""Cobertura legada recuperada sem interface, rede, áudio ou processos externos."""
from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from app import atualizar, configuracao, validacao


ROTEIRO = r'''# Roteiro
Texto solto | com barra que não é tabela

## 1. Novidades (desta leva)

### Grupo A

| Frase | O que deve acontecer | Comando esperado |
|---|---|---|
| `Mestre, que horas são` | Fala a hora | `_cmd_hora_data` |
| `Mestre, abre a|b` | Pipe dentro da crase | `_cmd_abrir` |
| `Mestre, o que é um buraco negro` | Vai pensar | (vai pensar, sem comando) |
| (painel) clique em Salvar | Salva | (painel) |
| Toque um vídeo dizendo "Mestre, ..." | NÃO executa | (ignorado, sem comando) |
| `Mestre, vou te mostrar uma nova rotina` → `Mestre, cancela a rotina` | Sai sem salvar | `_cmd_ensinar_rotina` |
| linha quebrada sem colunas

## 2. Sempre testar (regressão)

| Frase | O que deve acontecer | Comando esperado |
|:--|:--|:--|
| `Mestre, bora voltar a trabalhar` | Acorda | (acorda no ouvido, sem `_cmd_`) |
| `Mestre, abre o Gmail` | Abre o Gmail | `_cmd_abrir` \| `_cmd_sites` |
'''


class ConfiguracaoSemInterface(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mestre_config_")
        self.config = Path(self.tmp.name) / "config.yaml"
        exemplo = Path(__file__).resolve().parents[1] / "config.exemplo.yaml"
        self.config.write_text(exemplo.read_text(encoding="utf-8"), encoding="utf-8")
        self.patcher = patch.object(configuracao, "ARQUIVO_CONFIG", self.config)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.tmp.cleanup()

    def test_salvar_mapa_preserva_comentarios_ordem_e_backup(self):
        original = self.config.read_text(encoding="utf-8")
        dados = configuracao.carregar()
        configuracao.trocar_mapa(dados, "programas", {"spotify": '"C:/Spotify.exe"'})
        configuracao.trocar_mapa(dados, "sites", {"site do teste": "https://exemplo.com"})
        configuracao.trocar_mapa(dados, "canais_youtube", {"Manual do Mundo": "@manualdomundo"})
        configuracao.salvar(dados)

        salvo = configuracao.carregar()
        texto = self.config.read_text(encoding="utf-8")
        self.assertEqual(salvo["programas"]["spotify"], '"C:/Spotify.exe"')
        self.assertEqual(salvo["sites"]["site do teste"], "https://exemplo.com")
        self.assertEqual(salvo["canais_youtube"]["Manual do Mundo"], "@manualdomundo")
        self.assertIn("# 8) SITES", texto)
        self.assertLess(texto.index("spotify:"), texto.index("# 8) SITES"))
        self.assertEqual(self.config.with_suffix(".yaml.bak").read_text(encoding="utf-8"), original)

    def test_mesclar_lista_preserva_nova_de_fora_e_respeita_exclusao(self):
        iniciais = {"hora do cafe", "bora trabalhar"}
        disco = [{"nome": "Hora do cafe"}, {"nome": "Bora trabalhar"}, {"nome": "Rotina de fora"}]
        editado = [{"nome": "Bora trabalhar", "acoes": [{"falar": "vamos"}]}]
        resultado = configuracao.mesclar_novas_por_nome(disco, iniciais, editado)
        self.assertEqual([r["nome"] for r in resultado], ["Bora trabalhar", "Rotina de fora"])

    def test_consertar_secoes_repetidas_mantem_a_ultima(self):
        texto = "assistente:\n  nome: \"Antigo\"\nvoz:\n  motor: \"edge\"\nassistente:\n  nome: \"Novo\"\n"
        self.config.write_text(texto, encoding="utf-8")
        dados = configuracao.carregar()
        self.assertEqual(dados["assistente"]["nome"], "Novo")
        self.assertEqual(dados["voz"]["motor"], "edge")
        self.assertEqual(configuracao.ultimo_conserto, ["assistente"])
        self.assertEqual(self.config.with_suffix(".yaml.antes_do_conserto").read_text(encoding="utf-8"), texto)

    def test_migracao_preserva_dados_e_aplica_todas_as_versoes(self):
        dados = configuracao.carregar()
        dados["versao_config"] = 9
        assistente = configuracao.secao(dados, "assistente")
        assistente["nome"] = configuracao.aspas("Mestre")
        assistente["apelido_usuario"] = configuracao.aspas("Mestre")
        assistente["palavra_ativacao"] = configuracao.aspas("assessor")
        configuracao.secao(dados, "sites")["meu portal"] = configuracao.aspas("https://interno.test")
        cerebro = configuracao.secao(dados, "cerebro")
        cerebro["aviso_som"] = configuracao.aspas("voz")
        cerebro["aviso_ao_terminar"] = configuracao.aspas("voz")
        configuracao.secao(dados, "voz")["motor"] = configuracao.aspas("edge")
        configuracao.salvar(dados)

        self.assertTrue(configuracao.migrar())
        migrado = configuracao.carregar()
        self.assertEqual(migrado["versao_config"], configuracao.VERSAO_CONFIG)
        self.assertEqual(migrado["assistente"]["nome"], "Assessor")
        self.assertEqual(migrado["assistente"]["apelido_usuario"], "Mestre")
        self.assertEqual(migrado["cerebro"]["aviso_som"], "nenhum")
        self.assertEqual(migrado["cerebro"]["aviso_ao_terminar"], "falar_direto")
        self.assertEqual(migrado["voz"]["motor"], "kokoro")
        self.assertEqual(migrado["voz"]["voz_kokoro"], "pm_alex")
        self.assertEqual(migrado["sites"]["meu portal"], "https://interno.test")
        self.assertIn("netflix", migrado["sites"])
        self.assertFalse(configuracao.migrar())

    def test_variacoes_aceitas_sem_duplicar_e_com_desfazer(self):
        self.assertTrue(configuracao.adicionar_variacao_aceita("mestri"))
        self.assertFalse(configuracao.adicionar_variacao_aceita("MÉSTRI"))
        self.assertIn("mestri", configuracao.carregar()["assistente"]["variacoes_aceitas"])
        self.assertTrue(configuracao.remover_variacao_aceita("mestri"))
        self.assertFalse(configuracao.remover_variacao_aceita("mestri"))


class AtualizacaoSemInterface(unittest.TestCase):
    def test_zip_atualiza_codigo_preserva_dados_e_remove_obsoleto(self):
        with tempfile.TemporaryDirectory(prefix="mestre_atualizar_") as tmp:
            raiz = Path(tmp)
            destino, pacote = raiz / "instalado", raiz / "pacote.zip"
            (destino / "app").mkdir(parents=True)
            (destino / "app" / "main.py").write_text("antigo", encoding="utf-8")
            (destino / "app" / "versao.py").write_text('VERSAO = "2.5"\n', encoding="utf-8")
            (destino / "config.yaml").write_text("# MEU CONFIG\n", encoding="utf-8")
            (destino / "aprendido.yaml").write_text("meu: dado\n", encoding="utf-8")
            (destino / "MELHORIAS.md").write_text("minhas ideias\n", encoding="utf-8")
            (destino / "notas").mkdir()
            (destino / "notas" / "minha.txt").write_text("não tocar", encoding="utf-8")
            (destino / "perfis").mkdir()
            (destino / "perfis" / "meu.md").write_text("personalizado", encoding="utf-8")
            (destino / "ANTIGO.bat").write_text("velho", encoding="utf-8")

            with zipfile.ZipFile(pacote, "w") as z:
                z.writestr("mestre/app/main.py", "novo")
                z.writestr("mestre/app/versao.py", 'VERSAO = "2.6"\n')
                z.writestr("mestre/config.yaml", "sobrescrito")
                z.writestr("mestre/aprendido.yaml", "sobrescrito")
                z.writestr("mestre/MELHORIAS.md", "sobrescrito")
                z.writestr("mestre/notas/minha.txt", "sobrescrito")
                z.writestr("mestre/perfis/meu.md", "sobrescrito")
                z.writestr("mestre/perfis/novo.md", "novo perfil")
                z.writestr("mestre/OBSOLETOS.txt", "ANTIGO.bat\nconfig.yaml\n../fora.txt\n")

            self.assertEqual(atualizar.verificar(pacote), "")
            resumo = atualizar.aplicar(pacote, destino, instalar_bibliotecas=False)
            self.assertIn("da versão 2.5 para a 2.6", resumo)
            self.assertEqual((destino / "app" / "main.py").read_text(encoding="utf-8"), "novo")
            self.assertEqual((destino / "config.yaml").read_text(encoding="utf-8"), "# MEU CONFIG\n")
            self.assertEqual((destino / "aprendido.yaml").read_text(encoding="utf-8"), "meu: dado\n")
            self.assertEqual((destino / "MELHORIAS.md").read_text(encoding="utf-8"), "minhas ideias\n")
            self.assertEqual((destino / "notas" / "minha.txt").read_text(encoding="utf-8"), "não tocar")
            self.assertEqual((destino / "perfis" / "meu.md").read_text(encoding="utf-8"), "personalizado")
            self.assertEqual((destino / "perfis" / "novo.md").read_text(encoding="utf-8"), "novo perfil")
            self.assertFalse((destino / "ANTIGO.bat").exists())
            reservas = list((destino / "logs").glob("antes_da_atualizacao_*.zip"))
            self.assertEqual(len(reservas), 1)
            with zipfile.ZipFile(reservas[0]) as reserva:
                self.assertEqual(reserva.read("app/main.py"), b"antigo")
                self.assertEqual(reserva.read("ANTIGO.bat"), b"velho")

    def test_verificacao_versoes_e_zip_invalido(self):
        with tempfile.TemporaryDirectory(prefix="mestre_zip_") as tmp:
            pasta = Path(tmp)
            invalido, valido = pasta / "invalido.zip", pasta / "valido.zip"
            with zipfile.ZipFile(invalido, "w") as z:
                z.writestr("qualquer.txt", "x")
            with zipfile.ZipFile(valido, "w") as z:
                z.writestr("app/main.py", "x")
                z.writestr("app/versao.py", 'VERSAO = "10.2"\n')
            self.assertIn("não parece", atualizar.verificar(invalido))
            self.assertEqual(atualizar.verificar(valido), "")
            self.assertEqual(atualizar.versao_do_zip(valido), "10.2")
            self.assertEqual(atualizar.versao_do_zip(invalido), "?")


class ValidacaoSemInterface(unittest.TestCase):
    def setUp(self):
        self.itens = validacao.ler_roteiro(texto=ROTEIRO)
        self.t0 = 1_000_000.0
        self.hist = [
            {"ts": self.t0 - 50, "tipo": "comando", "pedido": "velho", "rota": "_cmd_abrir", "resposta": "x"},
            {"ts": self.t0 + 3, "tipo": "comando", "pedido": "Mestre, que horas são",
             "entendi": "que horas sao", "rota": "_cmd_hora_data", "resposta": "São dez horas."},
        ]
        self.ouv = [
            {"ts": self.t0 - 60, "texto": "antigo", "chamou": True},
            {"ts": self.t0 + 2, "texto": "Mestre, que horas são?", "chamou": True,
             "audio": "logs/validacao/a.wav"},
        ]

    def test_parser_secoes_tipos_pipes_e_multiplas_falas(self):
        itens = self.itens
        self.assertEqual(len(itens), 9)
        self.assertEqual((itens[0].secao, itens[0].grupo, itens[0].comandos),
                         ("novidades", "Grupo A", ["_cmd_hora_data"]))
        self.assertEqual(itens[1].falas, ["Mestre, abre a|b"])
        self.assertEqual((itens[2].tipo, itens[3].manual, itens[4].tipo), ("ia", True, "ignorado"))
        self.assertEqual(itens[5].para_falar("Jarvis"),
                         "Jarvis, vou te mostrar uma nova rotina → Jarvis, cancela a rotina")
        self.assertEqual((itens[6].o_que, itens[6].comandos), ("", []))
        self.assertEqual((itens[7].tipo, itens[7].secao, itens[8].comandos),
                         ("acordar", "sempre", ["_cmd_abrir", "_cmd_sites"]))
        self.assertEqual((len(validacao.escolher(itens, "Só novidades")),
                          len(validacao.escolher(itens, "Só sempre testar"))), (7, 2))

    def test_captura_e_conferencia_de_rotas(self):
        captura = validacao.capturar(self.t0, self.hist, self.ouv)
        self.assertEqual((captura["ouvi"], captura["rota"], captura["fiz"], captura["audio"]),
                         ("Mestre, que horas são?", "_cmd_hora_data", "São dez horas.", "logs/validacao/a.wav"))
        self.assertEqual(validacao.conferir(self.itens[0], captura), "ok")
        self.assertIsNone(validacao.capturar(self.t0 + 10, self.hist, self.ouv))

        hist2 = self.hist + [
            {"ts": self.t0 + 20, "tipo": "comando", "pedido": "Mestre abre o gmail",
             "entendi": "abre o gmail", "rota": "ia", "resposta": ""},
            {"ts": self.t0 + 25, "tipo": "ia virou comando", "pedido": "abre o gmail",
             "ia_texto": "abre o gmail", "rota": "_cmd_youtube"},
            {"ts": self.t0 + 26, "tipo": "comando", "pedido": "isso ta errado",
             "rota": "_cmd_feedback", "resposta": "?"},
        ]
        c2 = validacao.capturar(self.t0 + 15, hist2,
                                self.ouv + [{"ts": self.t0 + 19, "texto": "Mestre, abre o Gmail.", "chamou": True}])
        self.assertEqual(c2["rota"], "_cmd_youtube")
        self.assertIn("IA:", c2["entendi"])
        self.assertEqual(validacao.conferir(self.itens[8], c2), "falha")
        self.assertEqual(validacao.conferir(self.itens[4], None), "ok")
        self.assertEqual(validacao.conferir(self.itens[2], {"rota": "ia"}), "ok")
        self.assertEqual(validacao.conferir(self.itens[7], {"rota": "saiu do descanso"}), "ok")
        self.assertIsNone(validacao.conferir(self.itens[3], captura))
        self.assertEqual(validacao.conferir(self.itens[5], {"rota": "rotina falada: cancelou"}), "ok")

    def test_registro_antigo_e_fala_nova(self):
        antigo = [{"data": "27/09/2026 13:02", "tipo": "comando", "pedido": "x", "rota": "_cmd_abrir"}]
        self.assertIsNotNone(validacao.capturar(0, antigo, []))
        ouvidas = self.ouv + [{"ts": self.t0 + 30, "texto": "Era pra abrir o Gmail", "chamou": False}]
        self.assertEqual(validacao.fala_nova(self.t0 + 18, ouvidas), "Era pra abrir o Gmail")

    def test_modo_continuo_ok_falha_ia_silencio_e_descarte(self):
        avaliar = validacao.avaliar_continuo
        self.assertEqual(avaliar(self.itens[0], self.t0, self.t0 + 4, self.hist, self.ouv)["estado"], "ok")
        hia = [{"ts": self.t0 + 3, "tipo": "comando", "pedido": "Mestre abre o gmail",
                "entendi": "abre o gmail", "rota": "ia"}]
        self.assertEqual(avaliar(self.itens[8], self.t0, self.t0 + 5, hia, self.ouv)["estado"], "esperando")
        self.assertEqual(avaliar(self.itens[8], self.t0, self.t0 + 30, hia, self.ouv)["estado"], "falha")
        self.assertEqual(avaliar(self.itens[0], self.t0 + 100, self.t0 + 105, self.hist, self.ouv)["estado"], "esperando")
        self.assertEqual(avaliar(self.itens[0], self.t0 + 100,
                                 self.t0 + 101 + validacao.SILENCIO_SEGUNDOS, self.hist, self.ouv)["estado"], "silencio")
        desc = [
            {"ts": self.t0 + 200, "texto": "que horas são", "chamou": False,
             "motivo": "sem a palavra de ativação"},
            {"ts": self.t0 + 201, "texto": "", "motivo": "curta demais", "descartado": True},
            {"ts": self.t0 + 202, "texto": "Mestre", "chamou": True,
             "motivo": "só a palavra: esperando o resto (3.0s)"},
        ]
        resultado = avaliar(self.itens[0], self.t0 + 199,
                            self.t0 + 203 + validacao.ESPERA_DESCARTE, self.hist, desc)
        self.assertEqual(resultado["estado"], "falha")
        self.assertEqual([d["motivo"] for d in resultado["descartes"]], ["sem a palavra de ativação"])
        self.assertIn("sem a palavra de ativação", validacao.texto_descartes(resultado["descartes"]))

    def test_modo_continuo_ignorado_multiplas_falas_e_filtro_manual(self):
        ignorada = [{"ts": self.t0 + 300, "texto": "Mestre, toca o vídeo", "chamou": False,
                     "motivo": "sem a palavra de ativação"}]
        avaliar = validacao.avaliar_continuo
        self.assertEqual(avaliar(self.itens[4], self.t0 + 299, self.t0 + 305, [], ignorada)["estado"], "ok")
        executou = [{"ts": self.t0 + 301, "tipo": "comando", "pedido": "x", "rota": "_cmd_youtube"}]
        self.assertEqual(avaliar(self.itens[4], self.t0 + 299, self.t0 + 305, executou, ignorada)["estado"], "falha")
        uma = [{"ts": self.t0 + 401, "tipo": "comando", "pedido": "a",
                "rota": "_cmd_ensinar_rotina", "resposta": "?"}]
        duas = uma + [{"ts": self.t0 + 405, "tipo": "comando", "pedido": "b",
                       "rota": "rotina falada: cancelou", "resposta": "ok"}]
        self.assertEqual(avaliar(self.itens[5], self.t0 + 400, self.t0 + 403, uma, [])["estado"], "esperando")
        self.assertEqual(avaliar(self.itens[5], self.t0 + 400, self.t0 + 407, duas, [])["estado"], "ok")
        self.assertEqual(len(validacao.para_continuo(self.itens)), len(self.itens) - 1)
        self.assertEqual(len(validacao.para_continuo(self.itens, True)), len(self.itens))

    def test_sessao_relatorio_feedback_e_pedido_de_correcao(self):
        captura = validacao.capturar(self.t0, self.hist, self.ouv)
        sessao = validacao.Sessao(self.itens[:3] + [self.itens[8]], "Tudo")
        sessao.marcar("ok", captura, "ok")
        sessao.marcar("pulado")
        sessao.mostrar(1)
        sessao.marcar("ok", {"rota": "ia"}, "ok")
        sessao.marcar("ok", {"rota": "ia"}, "ok")
        c2 = {"ouvi": "Mestre, abre o Gmail.", "entendi": "abre o gmail",
              "rota": "_cmd_youtube", "fiz": "(não falou nada)"}
        sessao.marcar("falha", c2, "falha", "abrir o Gmail no navegador")
        self.assertTrue(sessao.acabou)
        self.assertEqual(sessao.resultados[1]["veredito"], "ok")

        with tempfile.TemporaryDirectory(prefix="mestre_validacao_") as tmp:
            pasta = Path(tmp)
            relatorio = validacao.gerar_relatorio(sessao, "Jarvis", datetime(2026, 9, 27, 14, 5), pasta)
            texto = relatorio.read_text(encoding="utf-8")
            self.assertEqual(relatorio.name, "validacao_2026-09-27_1405.md")
            self.assertIn("**3 ok**", texto)
            self.assertIn("**1 falhas**", texto)
            self.assertIn("abrir o Gmail no navegador", texto)
            self.assertTrue(validacao.relatorio_tem_falhas(relatorio))
            self.assertEqual(validacao.ultimo_relatorio(pasta), relatorio)

            melhorias = pasta / "MELHORIAS.md"
            melhorias.write_text("# Melhorias\n- [ ] ideia velha", encoding="utf-8")
            linhas = validacao.salvar_feedbacks(sessao, melhorias, datetime(2026, 9, 27))
            self.assertEqual(len(linhas), 1)
            self.assertIn("- [ ] ideia velha\n- [ ] (27/09/2026) FEEDBACK:",
                          melhorias.read_text(encoding="utf-8"))

            pedido = validacao.pedido_de_correcao(relatorio)
            arquivo = validacao.salvar_pedido_correcao(pedido, datetime(2026, 9, 27, 14, 6), pasta)
            self.assertIn("Corrija as falhas", arquivo.read_text(encoding="utf-8"))
            curto = validacao.prompt_curto(arquivo)
            self.assertTrue(curto.startswith("Leia o arquivo "))
            self.assertFalse(any(c in curto for c in ';"&|'))

    def test_feedback_inclui_audio_e_relatorio_sem_falha(self):
        captura = validacao.capturar(self.t0, self.hist, self.ouv)
        sessao = validacao.Sessao(self.itens[:1])
        sessao.marcar("falha", captura, "ok", "")
        self.assertIn("[áudio: logs/validacao/a.wav]", validacao.linha_feedback(self.itens[0], sessao.resultados[0]))
        with tempfile.TemporaryDirectory(prefix="mestre_validacao_ok_") as tmp:
            relatorio = validacao.gerar_relatorio(validacao.Sessao([]), "Jarvis",
                                                   datetime(2099, 1, 1), Path(tmp))
            self.assertFalse(validacao.relatorio_tem_falhas(relatorio))


if __name__ == "__main__":
    unittest.main()
