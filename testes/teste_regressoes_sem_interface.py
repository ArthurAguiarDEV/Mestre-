"""Cobertura legada recuperada sem interface, rede, áudio ou processos externos."""
import ast
import hashlib
from datetime import datetime
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from types import SimpleNamespace

from app import atualizar, configuracao, validacao


def metodos_menu_sem_janela():
    """Carrega os metodos reais sem importar customtkinter ou iniciar a interface."""
    origem = Path(__file__).resolve().parents[1] / "app" / "painel.py"
    arvore = ast.parse(origem.read_text(encoding="utf-8"))
    classe = next(n for n in arvore.body if isinstance(n, ast.ClassDef) and n.name == "Painel")
    movimento = next(n for n in arvore.body if isinstance(n, ast.ClassDef) and n.name == "MovimentoGaveta")
    metodos = [n for n in classe.body if isinstance(n, ast.FunctionDef)
               and n.name in {"_rail_aplicar", "_rail_alternar", "_rail_esc", "_escolher_menu",
                              "_rail_montar_pendente", "_marcar_item", "mostrar_pagina"}]
    classe_falsa = ast.ClassDef(name="MenuSemInterface", bases=[], keywords=[], body=metodos, decorator_list=[])
    modulo = ast.fix_missing_locations(ast.Module(body=[movimento, classe_falsa], type_ignores=[]))
    contexto = {"math": math}
    exec(compile(modulo, str(origem), "exec"), contexto)
    return contexto["MenuSemInterface"], contexto["MovimentoGaveta"]


def percorrer(mov, t, ate, no_trilho, na_gaveta=False, passo=0.016):
    """Anda o relogio de t ate `ate` em quadros de ~16 ms; devolve (t, [p de cada quadro])."""
    ps = []
    while t < ate - 1e-9:
        t += passo
        ps.append(mov.passo(t, no_trilho, na_gaveta))
    return t, ps


class MenuSemJanela(unittest.TestCase):
    def test_passar_rapido_nao_abre_e_parar_abre_suave(self):
        _, Movimento = metodos_menu_sem_janela()
        mov = Movimento()
        mov.acordar(0.0)
        t, ps = percorrer(mov, 0.0, Movimento.ESPERA * 0.6, no_trilho=True)
        t, ps2 = percorrer(mov, t, t + 0.3, no_trilho=False)
        self.assertEqual(set(ps + ps2), {0.0})   # so passou por cima: continua fechado
        t, ps = percorrer(mov, t, t + Movimento.ESPERA + 0.4, no_trilho=True)
        self.assertEqual(ps[-1], 1.0)
        self.assertEqual(ps, sorted(ps))   # so anda para frente
        self.assertLess(max(b - a for a, b in zip(ps, ps[1:])), 0.35)   # em varios quadros, sem salto

    def test_sair_fecha_e_voltar_no_meio_inverte_sem_salto(self):
        _, Movimento = metodos_menu_sem_janela()
        mov = Movimento()
        mov.acordar(0.0)
        t, _ = percorrer(mov, 0.0, 1.0, no_trilho=True)
        self.assertEqual(mov.p, 1.0)
        t, ps = percorrer(mov, t, t + 0.05, no_trilho=False)
        meio = ps[-1]
        self.assertTrue(0 < meio < 1)
        # o mouse volta para a parte da gaveta ainda visivel: abre de novo a partir de onde estava
        t, ps = percorrer(mov, t, t + 0.4, no_trilho=False, na_gaveta=True)
        self.assertGreater(ps[0], meio)
        self.assertLess(ps[0] - meio, 0.35)
        self.assertEqual(ps[-1], 1.0)
        t, ps = percorrer(mov, t, t + 0.5, no_trilho=False)
        self.assertEqual(ps[-1], 0.0)
        self.assertEqual(ps, sorted(ps, reverse=True))

    def test_tela_travada_nao_faz_a_gaveta_saltar(self):
        _, Movimento = metodos_menu_sem_janela()
        mov = Movimento()
        mov.abrir()
        mov.acordar(0.0)
        mov.passo(0.016, True, False)
        antes = mov.p
        mov.passo(2.0, True, False)   # 2 s sem quadro (pagina montando)
        self.assertLess(mov.p - antes, 1 - math.exp(-Movimento.PASSO_MAX / Movimento.TAU) + 1e-9)

    def test_depois_do_clique_fica_fechado_ate_o_mouse_sair(self):
        _, Movimento = metodos_menu_sem_janela()
        mov = Movimento()
        mov.acordar(0.0)
        t, _ = percorrer(mov, 0.0, 1.0, no_trilho=True)
        mov.fechar()
        t, ps = percorrer(mov, t, t + 1.5, no_trilho=True)
        self.assertEqual(ps[-1], 0.0)   # mouse parado no trilho nao reabre
        t, _ = percorrer(mov, t, t + 0.1, no_trilho=False)
        self.assertFalse(mov.segurar)
        t, ps = percorrer(mov, t, t + Movimento.ESPERA + 0.4, no_trilho=True)
        self.assertEqual(ps[-1], 1.0)   # saiu e voltou: abre de novo

    def test_abrir_e_fechar_so_move_a_gaveta(self):
        Painel, Movimento = metodos_menu_sem_janela()
        espaco, conteudo, gaveta, trilho, borda = (unittest.mock.Mock() for _ in range(5))
        pintados = []
        painel = SimpleNamespace(
            _rail_fechado=68, _gaveta_largura=212, _rail_desloc=0, _rail_espaco=espaco, _conteudo=conteudo,
            _gaveta=gaveta, _trilho=trilho, _trilho_borda=borda, _dica=unittest.mock.Mock(),
            _rail_marcados={"Voz"}, _rail_foco=None, _rail_pintar=pintados.append,
        )
        mov = Movimento()
        mov.acordar(0.0)
        t = 0.0
        for _ in range(10):   # abrir e fechar dez vezes
            t, ps = percorrer(mov, t, t + 1.0, no_trilho=True)
            t, ps2 = percorrer(mov, t, t + 1.0, no_trilho=False)
            for p in ps + ps2:
                Painel._rail_aplicar(painel, p)
        self.assertEqual(espaco.mock_calls, [])
        self.assertEqual(conteudo.mock_calls, [])
        chamadas = gaveta.place_configure.call_args_list
        self.assertTrue(chamadas)
        self.assertTrue(all(c.args == () and set(c.kwargs) == {"x"} for c in chamadas))
        xs = [c.kwargs["x"] for c in chamadas]
        self.assertEqual((min(xs), max(xs), xs[-1]), (68 - 212, 68, 68 - 212))
        self.assertFalse(trilho.place_configure.called)
        self.assertEqual(pintados.count("Voz"), 20)   # pilula do trilho troca de forma so ao abrir/fechar

    def test_clique_em_pagina_montada_abre_na_hora_e_uma_vez(self):
        Painel, Movimento = metodos_menu_sem_janela()
        mostradas = []
        painel = SimpleNamespace(
            _rail_mov=Movimento(), _rail_desloc=212, _rail_depois=None, _rail_montar_id=None,
            paginas={"Voz": ("montada", "")}, _rail_acordar=lambda: None,
            mostrar_pagina=mostradas.append,
        )
        Painel._escolher_menu(painel, "Voz")
        self.assertEqual(mostradas, ["Voz"])
        self.assertTrue(painel._rail_mov.segurar)
        self.assertEqual(painel._rail_mov.alvo, 0)

    def test_pagina_nova_monta_depois_que_a_gaveta_fecha(self):
        Painel, Movimento = metodos_menu_sem_janela()
        mostradas, cancelados = [], []
        painel = SimpleNamespace(
            _rail_mov=Movimento(), _rail_desloc=212, _rail_depois=None, _rail_montar_id=None,
            _rail_marcados={"Início"}, pagina_atual="Início", _rail_pintar=lambda _n: None,
            paginas={"Voz": (None, ""), "Áudio": (None, ""), "Início": ("montada", "")},
            _rail_acordar=lambda: None, after_cancel=cancelados.append, mostrar_pagina=mostradas.append,
        )
        painel._marcar_item = lambda nome, ativo: Painel._marcar_item(painel, nome, ativo)
        Painel._escolher_menu(painel, "Voz")
        self.assertEqual((mostradas, painel._rail_depois, painel._rail_marcados), ([], "Voz", {"Voz"}))
        painel._rail_montar_id = "agendado"
        Painel._escolher_menu(painel, "Áudio")   # mudou de ideia antes de montar
        self.assertEqual((cancelados, painel._rail_depois, painel._rail_marcados), (["agendado"], "Áudio", {"Áudio"}))
        Painel._rail_montar_pendente(painel)
        Painel._rail_montar_pendente(painel)
        self.assertEqual(mostradas, ["Áudio"])

    def test_logo_e_esc(self):
        Painel, Movimento = metodos_menu_sem_janela()
        painel = SimpleNamespace(_rail_mov=Movimento(), _rail_acordar=lambda: None)
        Painel._rail_alternar(painel)
        self.assertEqual((painel._rail_mov.alvo, painel._rail_mov.segurar), (1, False))
        Painel._rail_esc(painel)
        self.assertEqual((painel._rail_mov.alvo, painel._rail_mov.segurar), (0, True))

    def test_mesma_pagina_nao_e_montada_ou_selecionada_outra_vez(self):
        Painel, _ = metodos_menu_sem_janela()

        painel = SimpleNamespace(pagina_atual="Voz")
        Painel.mostrar_pagina(painel, "Voz")


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

    def test_tipos_ids_etapas_e_instrucoes_fora_do_microfone(self):
        linhas = [
            '| `Mestre, oi` <!-- validacao id=voz-1 tipo=fala --> | responde | `_cmd_oi` |',
            '| `Mestre, abre` → `Mestre, fecha` | duas etapas | `_cmd_abrir` `_cmd_fechar` |',
            '| (painel) Clique em Salvar | salva | (painel) |',
            '| Confira o indicador | aparece | (visual) |',
            '| Se a rede estiver ligada | necessário | (painel) |',
            '| Espere 5 segundos | termina | (visual) |',
            '| (automático) rode o teste | passou | (teste) |',
            '| Fale qualquer pedido e espere | confira | (visual) |',
        ]
        cabecalho = '## Novidades\n### Grupo\n| Frase | Ação | Esperado |\n|---|---|---|\n'
        itens = validacao.ler_roteiro(texto=cabecalho + '\n'.join(linhas))
        self.assertEqual([i.tipo_item for i in itens],
                         ['fala', 'sequencia', 'acao_manual', 'observacao', 'pre_condicao',
                          'espera', 'teste_automatico', 'acao_manual'])
        self.assertEqual(itens[0].id, 'voz-1')
        self.assertEqual(itens[1].etapas[0].id, itens[1].id + '-1')
        self.assertTrue(all(e.independente for e in itens[1].etapas))
        self.assertEqual({i.id for i in itens}, {i.id for i in validacao.ler_roteiro(
            texto=cabecalho + '\n'.join(reversed(linhas)))})
        self.assertTrue(all(i.para_falar('Jarvis') == '' for i in itens[2:]))
        self.assertEqual(itens[0].para_falar('Jarvis'), 'Jarvis, oi')
        self.assertIsNone(validacao.conferir(itens[2], {'rota': '_cmd_oi'}))
        self.assertEqual(validacao.avaliar_continuo(itens[2], 0, 20, [], [])['estado'], 'conferir')

    def test_relatorio_parcial_proveniencia_bloqueios_e_etapas(self):
        roteiro = ('## Novidades\n### Grupo\n| Frase | Ação | Esperado |\n|---|---|---|\n'
                   '| `Mestre, abre` → `Mestre, fecha` | duas etapas | `_cmd_abrir` `_cmd_fechar` |\n'
                   '| Se a rede estiver ligada | necessário | (painel) |\n'
                   '| (painel) Clique em Salvar | salva | (painel) |\n')
        itens = validacao.ler_roteiro(texto=roteiro)
        sessao = validacao.Sessao(itens[:2], 'Só novidades', excluidos=itens[2:])
        self.assertEqual((sessao.itens_carregados, len(sessao.itens)), (3, 3))
        self.assertEqual([i.id for i in sessao.itens[:2]],
                         [itens[0].id + '-1', itens[0].id + '-2'])
        self.assertEqual([i.comandos for i in sessao.itens[:2]], [['_cmd_abrir'], ['_cmd_fechar']])
        sessao.marcar('ok', {'rota': '_cmd_abrir'})
        sessao.marcar('bloqueado')
        sessao.interrompida = True
        with tempfile.TemporaryDirectory(prefix='mestre_parcial_') as tmp:
            pasta = Path(tmp)
            relatorio = validacao.gerar_relatorio(sessao, 'Jarvis', datetime(2026, 9, 29, 2, 0), pasta)
            texto = relatorio.read_text(encoding='utf-8')
            outro = validacao.gerar_relatorio(sessao, 'Jarvis', datetime(2026, 9, 29, 2, 0), pasta)
            self.assertNotEqual(relatorio, outro)
            self.assertEqual(validacao.ultimo_relatorio(pasta), outro)
            etapas = validacao.gerar_relatorio(validacao.Sessao([itens[0]]), 'Jarvis',
                                               datetime(2026, 9, 29, 2, 1), pasta).read_text(encoding='utf-8')
            self.assertIn('0 de 2 etapas conferidas', etapas)
            self.assertIn('**Itens carregados:** 1', etapas)
        self.assertIn('relatório parcial', texto)
        self.assertIn('**Itens carregados:** 3', texto)
        self.assertIn(sessao.commit, texto)
        self.assertIn(sessao.versao, texto)
        self.assertIn(hashlib.sha256(validacao.ARQUIVO_ROTEIRO.read_bytes()).hexdigest(), texto)
        self.assertIn('## Pré-condições', texto)
        self.assertIn('## Itens bloqueados', texto)
        self.assertIn('## Itens não executados', texto)
        self.assertIn(itens[0].id + '-2', texto)
        self.assertIn(itens[2].id, texto)

    def test_modos_selecionam_escopo_e_descrevem_antes_de_iniciar(self):
        itens = validacao.ler_roteiro()
        rapido = validacao.selecionar_modo(itens, 'Rápido')
        self.assertEqual([i.id for i in rapido.itens], list(validacao.IDS_RAPIDOS))
        self.assertTrue(all(i.exige_microfone and i.tipo_item == 'fala' for i in rapido.itens))
        self.assertEqual(rapido.etapas, len(rapido.itens))
        self.assertIn('4 itens (4 etapas)', validacao.descrever_escopo(rapido))
        self.assertIn('sem tarefas físicas longas', validacao.descrever_escopo(rapido))

        grupos = validacao.grupos_disponiveis(itens)
        escolhidos = [grupos[2], grupos[-1]]
        direcionado = validacao.selecionar_modo(itens, 'Direcionado', escolhidos)
        self.assertEqual(direcionado.itens,
                         [i for i in itens if (i.secao, i.grupo) in escolhidos])
        self.assertEqual(direcionado.grupos, escolhidos)
        self.assertIn(escolhidos[0][1], validacao.descrever_escopo(direcionado))
        self.assertEqual(validacao.descrever_escopo(validacao.selecionar_modo(itens, 'Direcionado')),
                         'Selecione pelo menos um grupo para validar.')

        completo = validacao.selecionar_modo(itens, 'Completo')
        self.assertEqual(completo.itens, itens)
        self.assertTrue(any(i.tipo_item == 'pre_condicao' for i in completo.itens))
        self.assertTrue(any(i.tipo_item == 'observacao' for i in completo.itens))
        self.assertTrue(any(i.tipo_item == 'espera' for i in completo.itens))
        self.assertIn(f'{len(itens)} itens', validacao.descrever_escopo(completo))
        self.assertIn('não serão enviados ao microfone', validacao.descrever_escopo(completo))
        self.assertEqual([i.id for i in validacao.selecionar_modo(list(reversed(itens)), 'Rápido').itens],
                         list(validacao.IDS_RAPIDOS))

    def test_pre_condicao_bloqueia_grupo_sem_registrar_falha(self):
        roteiro = ('## Novidades\n### Grupo A\n| Frase | Ação | Esperado |\n|---|---|---|\n'
                   '| Se a rede estiver ligada | necessária | (painel) |\n'
                   '| `Mestre, abre o site` | abre | `_cmd_abrir` |\n'
                   '### Grupo B\n| Frase | Ação | Esperado |\n|---|---|---|\n'
                   '| `Mestre, que horas são` | responde | `_cmd_hora_data` |\n')
        sessao = validacao.Sessao(validacao.selecionar_modo(validacao.ler_roteiro(texto=roteiro),
                                                           'Completo').itens, 'Completo')
        sessao.marcar('falha')
        self.assertEqual([r['veredito'] for _, r in sessao.lista_completa()],
                         ['bloqueado', 'bloqueado', 'nao_executado'])
        self.assertEqual(sessao.atual.grupo, 'Grupo B')
        with tempfile.TemporaryDirectory(prefix='mestre_precondicao_') as tmp:
            relatorio = validacao.gerar_relatorio(sessao, 'Jarvis', datetime(2026, 9, 29, 2, 1), Path(tmp))
            texto = relatorio.read_text(encoding='utf-8')
        self.assertIn('**Modo:** Completo', texto)
        self.assertIn('Pré-condição não atendida', texto)
        self.assertIn('**0 falhas**', texto)

    def test_painel_descreve_modo_sem_abrir_janela(self):
        origem = Path(__file__).resolve().parents[1] / 'app' / 'painel.py'
        arvore = ast.parse(origem.read_text(encoding='utf-8'))
        painel = next(n for n in arvore.body if isinstance(n, ast.ClassDef) and n.name == 'Painel')
        metodos = [n for n in painel.body if isinstance(n, ast.FunctionDef)
                   and n.name in {'_val_escopo', '_val_atualizar_escopo'}]
        falsa = ast.ClassDef(name='PainelSemJanela', bases=[], keywords=[], body=metodos, decorator_list=[])
        modulo = ast.fix_missing_locations(ast.Module(body=[falsa], type_ignores=[]))
        contexto = {'__name__': 'app._teste_painel_validacao', '__package__': 'app'}
        exec(compile(modulo, str(origem), 'exec'), contexto)

        class ListaFalsa:
            def __init__(self):
                self.indices = ()
                self.visivel = False

            def curselection(self):
                return self.indices

            def pack(self, **_):
                self.visivel = True

            def pack_forget(self):
                self.visivel = False

        class RotuloFalso:
            def __init__(self):
                self.texto = ''

            def configure(self, **opcoes):
                self.texto = opcoes['text']

        classe = contexto['PainelSemJanela']
        objeto = classe()
        estado = {'modo': 'Rápido'}
        objeto.var_val_modo = SimpleNamespace(get=lambda: estado['modo'])
        objeto._val_grupos = validacao.grupos_disponiveis(validacao.ler_roteiro())
        objeto.lista_val_grupos = ListaFalsa()
        objeto.rot_val_escopo = RotuloFalso()
        objeto._val_atualizar_escopo()
        self.assertIn('4 itens', objeto.rot_val_escopo.texto)
        self.assertFalse(objeto.lista_val_grupos.visivel)
        estado['modo'] = 'Direcionado'
        objeto.lista_val_grupos.indices = (0,)
        objeto._val_atualizar_escopo()
        self.assertTrue(objeto.lista_val_grupos.visivel)
        self.assertIn(objeto._val_grupos[0][1], objeto.rot_val_escopo.texto)
        estado['modo'] = 'Completo'
        objeto._val_atualizar_escopo()
        self.assertIn(f'{len(validacao.ler_roteiro())} itens', objeto.rot_val_escopo.texto)

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
        self.assertIsNone(validacao.conferir(self.itens[4], None))  # tocar vídeo é ação manual
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
        self.assertEqual(avaliar(self.itens[4], self.t0 + 299, self.t0 + 305, [], ignorada)["estado"], "conferir")
        executou = [{"ts": self.t0 + 301, "tipo": "comando", "pedido": "x", "rota": "_cmd_youtube"}]
        self.assertEqual(avaliar(self.itens[4], self.t0 + 299, self.t0 + 305, executou, ignorada)["estado"], "conferir")
        uma = [{"ts": self.t0 + 401, "tipo": "comando", "pedido": "a",
                "rota": "_cmd_ensinar_rotina", "resposta": "?"}]
        duas = uma + [{"ts": self.t0 + 405, "tipo": "comando", "pedido": "b",
                       "rota": "rotina falada: cancelou", "resposta": "ok"}]
        self.assertEqual(avaliar(self.itens[5], self.t0 + 400, self.t0 + 403, uma, [])["estado"], "esperando")
        self.assertEqual(avaliar(self.itens[5], self.t0 + 400, self.t0 + 407, duas, [])["estado"], "ok")
        self.assertEqual(validacao.para_continuo(self.itens), [i for i in self.itens if i.exige_microfone])
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
