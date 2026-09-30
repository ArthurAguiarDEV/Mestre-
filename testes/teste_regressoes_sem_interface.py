"""Cobertura legada recuperada sem interface, rede, áudio ou processos externos."""
import ast
import hashlib
from datetime import datetime
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from types import SimpleNamespace

from app import atualizar, configuracao, validacao


def _painel_ast():
    """painel.py lido como texto (sem importar customtkinter): a classe Painel e os dicionarios de paginas."""
    origem = Path(__file__).resolve().parents[1] / "app" / "painel.py"
    arvore = ast.parse(origem.read_text(encoding="utf-8"))
    classe = next(n for n in arvore.body if isinstance(n, ast.ClassDef) and n.name == "Painel")
    return origem, arvore, classe


def _chaves_do_dicionario(no_pai, nome):
    """Chaves de um dicionario de strings: PAGINAS (modulo) ou SALVAR_PAGINA (dentro de Painel)."""
    for n in no_pai.body:
        alvo = n.targets[0] if isinstance(n, ast.Assign) else getattr(n, "target", None)
        if isinstance(alvo, ast.Name) and alvo.id == nome and isinstance(n.value, ast.Dict):
            return [k.value for k in n.value.keys]
    raise AssertionError(nome)


def _luminancia(cor):
    def canal(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(cor.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def _contraste(a, b):
    la, lb = sorted((_luminancia(a), _luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


class LayoutAuroraSemJanela(unittest.TestCase):
    """Cartao 005: navegacao por areas, busca e resumo do espaco, sem abrir nenhuma janela."""

    def test_toda_pagina_existente_continua_em_exatamente_uma_area(self):
        from app import layout
        _, arvore, classe = _painel_ast()
        paginas = _chaves_do_dicionario(arvore, "PAGINAS")
        nas_areas = [p for _a, _r, itens in layout.AREAS for p, _rot in itens]
        self.assertEqual(sorted(nas_areas), sorted(paginas))   # nenhuma sumiu, nenhuma repetida
        self.assertEqual(len(nas_areas), len(set(nas_areas)))
        for antiga in ("Início", "Personalidade", "Voz", "Áudio", "Conversa", "Projeto", "YouTube", "Spotify",
                       "Programas e sites", "Rotinas", "Atalhos", "Celular", "Histórico", "Aparência", "Melhorias",
                       "Validar atualização", "Sugestões de melhoria", "Tempos"):
            self.assertIn(antiga, nas_areas)   # os IDs internos nao foram renomeados
        salvar = _chaves_do_dicionario(classe, "SALVAR_PAGINA")
        self.assertTrue(set(salvar) <= set(paginas))
        self.assertEqual([a for a, _r, _i in layout.AREAS],
                         ["visao", "conversa", "voz", "midias", "rotinas", "memoria", "evolucao", "ajustes"])

    def test_area_de_e_rotulos(self):
        from app import layout
        self.assertEqual(layout.area_de("Tempos"), "memoria")
        self.assertEqual(layout.area_de("Spotify"), "midias")
        self.assertEqual(layout.rotulo_area("midias"), "Mídias e telas")
        self.assertEqual(layout.titulo_pagina("Mídias e telas"), "Mídias e telas")
        self.assertEqual(layout.rotulo_pagina("Celular"), "Conexões")
        self.assertEqual(layout.area_de("nao existe"), "visao")

    def test_busca_acha_por_nome_palavra_e_sem_acento(self):
        from app import layout
        self.assertEqual(layout.buscar(""), [])
        self.assertEqual(layout.buscar("microfone")[0], "Áudio")
        self.assertIn("Mídias e telas", layout.buscar("telas")[:2])
        self.assertEqual(layout.buscar("MIDIAS")[0], "Mídias e telas")
        self.assertIn("Aparência", layout.buscar("modo noturno"))
        self.assertEqual(layout.buscar("zzzz nada disso"), [])
        self.assertLessEqual(len(layout.buscar("a", limite=3)), 3)

    def test_espaco_so_mostra_o_que_existe(self):
        from app import layout
        cfg = {"canais_youtube": {"a": "@a", "b": "@b"}, "spotify": {"playlists": {"x": "u"}},
               "programas": {"calc": "calc"}, "sites": {"gmail": "u", "wa": "u"},
               "janelas": {"nomes_monitores": {"2": "tv", "x": "ruim"}}}
        d = layout.montar_espaco(cfg, [], {}, ["Netflix", "Disney"], ["Arthur"], "")
        self.assertFalse(d["monitores_lidos"])
        self.assertEqual(d["monitores"], [])   # sem leitura das telas: nada de monitor inventado
        nomes = [s["nome"] for s in d["servicos"]]
        self.assertEqual(nomes, ["YouTube", "Netflix", "Disney", "Spotify"])
        self.assertEqual(d["servicos"][0]["detalhe"], "2 canais cadastrados")
        self.assertEqual(layout.montar_espaco({"canais_youtube": {"a": "@a"}}, [], {}, [], [], "")["servicos"][0]["detalhe"],
                         "1 canal cadastrado")
        self.assertEqual(d["servicos"][1]["detalhe"], "Perfil: Arthur")
        self.assertEqual(d["servicos"][-1]["detalhe"], "1 playlist cadastrada")
        self.assertEqual((d["programas"], d["sites"]), (1, 2))
        vazio = layout.montar_espaco({}, None, None, ["Netflix"], [], "")
        self.assertEqual(vazio["servicos"][1]["detalhe"], "Nenhum perfil cadastrado")
        self.assertEqual(vazio["servicos"][0]["detalhe"], "Nenhum canal cadastrado")
        varios = layout.montar_espaco({}, None, None, ["Netflix"], ["A", "B"], "B")
        self.assertEqual(varios["servicos"][1]["detalhe"], "Perfil padrão: B")

    def test_espaco_junta_monitor_apelido_e_janela(self):
        from app import layout
        cfg = {"janelas": {"nomes_monitores": {"2": "tv"}}}
        telas = [{"numero": 1, "principal": True, "largura": 2560, "altura": 1400, "descricao": "LG 144 Hz"},
                 {"numero": 2, "principal": False, "largura": 1920, "altura": 1040, "descricao": "AOC 60 Hz"}]
        d = layout.montar_espaco(cfg, telas, {2: "YouTube - Brave"}, [], [], "")
        self.assertTrue(d["monitores_lidos"])
        self.assertEqual([(m["numero"], m["principal"], m["apelido"], m["janela"], m["resolucao"])
                          for m in d["monitores"]],
                         [(1, True, "", "", "2560×1400"), (2, False, "tv", "YouTube - Brave", "1920×1040")])

    def test_mesma_pagina_nao_e_montada_ou_selecionada_outra_vez(self):
        """mostrar_pagina da pagina que ja esta na frente nao mexe em nada (e o codigo real do painel.py)."""
        origem, _arvore, classe = _painel_ast()
        metodo = next(n for n in classe.body if isinstance(n, ast.FunctionDef) and n.name == "mostrar_pagina")
        falsa = ast.ClassDef(name="SoMostrar", bases=[], keywords=[], body=[metodo], decorator_list=[])
        modulo = ast.fix_missing_locations(ast.Module(body=[falsa], type_ignores=[]))
        contexto = {}
        exec(compile(modulo, str(origem), "exec"), contexto)
        painel = SimpleNamespace(pagina_atual="Voz")
        contexto["SoMostrar"].mostrar_pagina(painel, "Voz")   # volta antes de tocar em qualquer widget
        self.assertEqual(painel.pagina_atual, "Voz")


class TemaAuroraSemJanela(unittest.TestCase):
    def test_padrao_e_claro_e_configuracao_antiga_continua_valendo(self):
        from app import tema
        antigo = tema.paleta({"cor": "Lilás", "fundo": "Preto", "fonte": "Candara", "tamanho": "Grande"})
        self.assertEqual((antigo["MODO"], antigo["FUNDO"]), ("claro", "#F5F1E9"))   # Aurora comeca clara
        self.assertEqual((antigo["FONTE"], antigo["TAMANHO"]), ("Candara", 16))       # fonte e tamanho preservados
        noturno = tema.paleta({"cor": "Lilás", "fundo": "Preto", "modo": "escuro"})
        self.assertEqual((noturno["MODO"], noturno["FUNDO"], noturno["ROSA"]), ("escuro", "#08080a", "#C3A6F5"))
        padrao = tema.paleta({})
        self.assertEqual((padrao["MODO"], padrao["ROSA"]), ("claro", "#7654A0"))
        escuro = tema.paleta({"modo": "escuro"})
        self.assertEqual((escuro["FUNDO"], escuro["ROSA"]), ("#19171D", "#D5B7F0"))
        self.assertEqual(tema.paleta({"modo": "invalido"})["MODO"], "claro")

    def test_contraste_legivel_nos_dois_modos_e_em_todas_as_cores(self):
        from app import tema
        for modo in ("claro", "escuro"):
            for cor in list(tema.CORES) + ["#336699"]:
                for fundo in tema.FUNDOS:
                    p = tema.paleta({"modo": modo, "cor": cor, "fundo": fundo})
                    rotulo = f"{modo}/{cor}/{fundo}"
                    self.assertGreaterEqual(_contraste(p["TEXTO"], p["FUNDO"]), 7, rotulo)
                    self.assertGreaterEqual(_contraste(p["TEXTO"], p["CARTAO"]), 7, rotulo)
                    self.assertGreaterEqual(_contraste(p["TEXTO_FRACO"], p["FUNDO"]), 4.5, rotulo)
                    self.assertGreaterEqual(_contraste(p["TEXTO_FRACO"], p["CARTAO"]), 4.5, rotulo)
                    self.assertGreaterEqual(_contraste(p["ROSA"], p["ROSA_FUNDO"]), 3, rotulo)   # aba ativa
                    self.assertGreaterEqual(_contraste(p["ROSA"], p["CARTAO"]), 3, rotulo)
                    self.assertGreaterEqual(_contraste(p["TEXTO_NO_ROSA"], p["ROSA"]), 4.5, rotulo)  # botao principal
                    self.assertGreaterEqual(_contraste(p["SUCESSO"], p["CARTAO"]), 3, rotulo)
                    self.assertGreaterEqual(_contraste(p["AVISO"], p["CARTAO"]), 3, rotulo)
                    self.assertGreaterEqual(_contraste(p["TEXTO"], p["PERIGO"]), 4.5, rotulo)   # botao Desligar

    def test_indicador_e_icone_mantem_a_cor_de_sempre(self):
        from app import tema
        self.assertEqual(tema.paleta({})["COR_INDICADOR"], tema.CORES["Rosa"])
        self.assertEqual(tema.paleta({"cor": "Azul", "modo": "claro"})["COR_INDICADOR"], tema.CORES["Azul"])


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

    def test_validacao_variada_explica_avisa_e_oferece_direcionado(self):
        itens = validacao.ler_roteiro()
        for modo in validacao.MODOS:
            self.assertIn(modo, validacao.EXPLICACAO_MODOS)
        self.assertIn('quatro', validacao.EXPLICACAO_MODOS)
        self.assertNotIn('Mestre', validacao.EXPLICACAO_MODOS)
        vazio = validacao.selecionar_direcionado(itens, [], set(), 0)
        self.assertTrue(validacao.so_essenciais(vazio))
        self.assertEqual({i.id for i in vazio.itens}, set(validacao.IDS_RAPIDOS))
        self.assertIn('só nas quatro falas essenciais', validacao.descrever_escopo(vazio))
        fora = [g for g in validacao.grupos_disponiveis(itens)
                if not any(i.id in validacao.IDS_RAPIDOS for i in itens if (i.secao, i.grupo) == g)]
        a, b = fora[0], fora[-1]
        dois = validacao.selecionar_direcionado(itens, [], set(), 0, grupos_manuais=[a, b])
        ids = [i.id for i in dois.itens]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(set(validacao.IDS_RAPIDOS) <= set(ids))
        for chave in (a, b):
            self.assertTrue(any((i.secao, i.grupo) == chave and i.id not in validacao.IDS_RAPIDOS
                                for i in dois.itens))
        self.assertFalse(validacao.so_essenciais(dois))
        self.assertNotIn('só nas quatro falas essenciais', validacao.descrever_escopo(dois))
        rapido = validacao.Sessao(validacao.selecionar_modo(itens, 'Rápido').itens, 'Rápido')
        self.assertFalse(validacao.oferece_direcionado(rapido))
        rapido.indice = len(rapido.itens)
        self.assertTrue(validacao.oferece_direcionado(rapido))
        rapido.interrompida = True
        self.assertFalse(validacao.oferece_direcionado(rapido))
        self.assertFalse(validacao.oferece_direcionado(None))

    def test_ids_e_grupos_explicitos_sobrevivem_a_renomeacao(self):
        texto = ('## Novidades\n### Nome antigo\n'
                 '<!-- validacao-grupo id=grupo-fixo caminhos=app/ouvido.py rotas=_cmd_hora_data -->\n'
                 '| Frase | Ação | Esperado |\n|---|---|---|\n'
                 '| `Mestre, hora` <!-- validacao id=item-fixo --> | responde | `_cmd_hora_data` |\n')
        antes = validacao.ler_roteiro(texto=texto)[0]
        depois = validacao.ler_roteiro(texto=texto.replace('Nome antigo', 'Nome novo').replace(
            'Mestre, hora', 'Mestre, horas'))[0]
        self.assertEqual((antes.id, antes.grupo_id), (depois.id, depois.grupo_id))
        self.assertEqual(antes.caminhos, ('app/ouvido.py',))
        self.assertEqual(antes.rotas_grupo, ('_cmd_hora_data',))

    def test_git_considera_staged_e_unstaged_sem_interface(self):
        validacao.esquecer_git()
        with patch.object(validacao.subprocess, 'run', side_effect=[
            SimpleNamespace(stdout=b'a.py\0'), SimpleNamespace(stdout=b'b.py\0a.py\0'),
            SimpleNamespace(stdout=b'c.py\0')]) as comando:
            self.assertEqual(validacao.arquivos_alterados_git(Path('repositorio')), ['a.py', 'b.py', 'c.py'])
        self.assertEqual(comando.call_args_list[0].args[0],
                         ('git', 'diff', '--name-only', '--cached', '-z'))
        self.assertEqual(comando.call_args_list[1].args[0],
                         ('git', 'diff', '--name-only', '-z'))
        self.assertEqual(comando.call_args_list[2].args[0],
                         ('git', 'diff', '--name-only', '-z', '@{upstream}...HEAD'))
        validacao.esquecer_git()
        with patch.object(validacao.subprocess, 'run', return_value=SimpleNamespace(stdout=b'')):
            self.assertEqual(validacao.arquivos_alterados_git(Path('repositorio')), [])
        # a resposta fica guardada: clicar de novo no painel não roda o Git outra vez
        with patch.object(validacao.subprocess, 'run', side_effect=AssertionError('rodou o Git de novo')):
            self.assertEqual(validacao.arquivos_alterados_git(Path('repositorio')), [])
        validacao.esquecer_git()

    def test_direcionado_mapeia_arquivos_falhas_e_regressao_sem_duplicar(self):
        itens = validacao.ler_roteiro()
        grupo_janelas = next(i for i in itens if i.caminhos and 'app/comandos/janelas.py' in i.caminhos)
        falha_mesmo_grupo = grupo_janelas.id
        falha_por_rota = next(i.id for i in itens if i.grupo != grupo_janelas.grupo and
                               '_cmd_mover' in i.comandos)
        escopo = validacao.selecionar_direcionado(
            itens, ['app/comandos/janelas.py'], {falha_mesmo_grupo, falha_por_rota}, 0)
        ids = [i.id for i in escopo.itens]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(set(validacao.IDS_RAPIDOS) <= set(ids))
        self.assertIn(falha_por_rota, ids)
        self.assertIn(falha_mesmo_grupo, ids)
        self.assertIn('falha aberta', validacao.descrever_escopo(escopo))
        self.assertIn('arquivo app/comandos/janelas.py', validacao.descrever_escopo(escopo))
        self.assertEqual([i.id for i in validacao.selecionar_modo(itens, 'Rápido').itens],
                         list(validacao.IDS_RAPIDOS))
        self.assertEqual(len(validacao.selecionar_modo(itens, 'Completo').itens), len(itens))

    def test_direcionado_diff_vazio_e_arquivo_sem_mapa_usam_minimo(self):
        itens = validacao.ler_roteiro()
        falha = next(i.id for i in itens if i.id not in validacao.IDS_RAPIDOS)
        for arquivos in ([], ['arquivo/desconhecido.py']):
            escopo = validacao.selecionar_direcionado(itens, arquivos, {falha}, 2)
            self.assertEqual({i.id for i in escopo.itens}, set(validacao.IDS_RAPIDOS))
            self.assertEqual(escopo.sem_mapeamento, arquivos)
            self.assertEqual(escopo.falhas_sem_id, 2)
            self.assertIn('sem ID', validacao.descrever_escopo(escopo))
            if arquivos:
                self.assertIn('sem mapeamento', validacao.descrever_escopo(escopo))

    def test_feedback_aberto_tem_id_e_legado_fica_sem_associacao(self):
        item = validacao.ler_roteiro()[0]
        linha = validacao.linha_feedback(item, {'captura': {'ouvi': 'teste'}})
        self.assertIn(f'validacao-feedback id={item.id}', linha)
        with tempfile.TemporaryDirectory(prefix='mestre_feedback_validacao_') as tmp:
            arquivo = Path(tmp) / 'MELHORIAS.md'
            arquivo.write_text(f'- [ ] {linha}\n- [x] {linha}\n- [ ] FEEDBACK: antigo\n', encoding='utf-8')
            self.assertEqual(validacao.feedbacks_abertos(arquivo), ({item.id}, 1))

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
        with patch.object(validacao, 'arquivos_alterados_git', return_value=[]),                 patch.object(validacao, 'feedbacks_recentes', return_value=[]):
            objeto._val_atualizar_escopo()
        self.assertIn('4 itens', objeto.rot_val_escopo.texto)
        with patch.object(validacao, 'arquivos_alterados_git', return_value=['app/comandos/janelas.py']),                 patch.object(validacao, 'feedbacks_recentes', return_value=[]):
            objeto._val_atualizar_escopo()
        self.assertIn('arquivo app/comandos/janelas.py', objeto.rot_val_escopo.texto)
        self.assertFalse(objeto.lista_val_grupos.visivel)
        estado['modo'] = 'Direcionado'
        objeto.lista_val_grupos.indices = (0,)
        with patch.object(validacao, 'arquivos_alterados_git', return_value=[]):
            objeto._val_atualizar_escopo()
        self.assertTrue(objeto.lista_val_grupos.visivel)
        self.assertIn(objeto._val_grupos[0][1], objeto.rot_val_escopo.texto)
        objeto.lista_val_grupos.indices = ()
        with patch.object(validacao, 'arquivos_alterados_git', return_value=['app/comandos/janelas.py']), \
                patch.object(validacao, 'feedbacks_abertos', return_value=(set(), 0)):
            objeto._val_atualizar_escopo()
        self.assertIn('arquivo app/comandos/janelas.py', objeto.rot_val_escopo.texto)
        self.assertIn('itens', objeto.rot_val_escopo.texto)
        estado['modo'] = 'Completo'
        objeto._val_atualizar_escopo()
        self.assertIn(f'{len(validacao.ler_roteiro())} itens', objeto.rot_val_escopo.texto)

    def test_painel_monta_validacao_sem_abrir_janela(self):
        """Executa o método real com widgets falsos; detecta nomes locais que ocultam secao()."""
        origem = Path(__file__).resolve().parents[1] / 'app' / 'painel.py'
        arvore = ast.parse(origem.read_text(encoding='utf-8'))
        painel = next(n for n in arvore.body if isinstance(n, ast.ClassDef) and n.name == 'Painel')
        metodo = next(n for n in painel.body if isinstance(n, ast.FunctionDef) and n.name == '_aba_validacao')
        falsa = ast.ClassDef(name='PainelSemJanela', bases=[], keywords=[], body=[metodo], decorator_list=[])
        modulo = ast.fix_missing_locations(ast.Module(body=[falsa], type_ignores=[]))

        class WidgetFalso:
            def __init__(self, *_args, **_kwargs):
                self.linhas = []

            def pack(self, **_kwargs):
                return self

            def bind(self, *_args, **_kwargs):
                return None

            def insert(self, *_args):
                self.linhas.append(_args)

        class VariavelFalsa:
            def __init__(self, value=None):
                self.valor = value

            def get(self):
                return self.valor

        widgets = SimpleNamespace(CTkFrame=WidgetFalso, CTkLabel=WidgetFalso,
                                  CTkButton=WidgetFalso, CTkSegmentedButton=WidgetFalso,
                                  CTkCheckBox=WidgetFalso, CTkEntry=WidgetFalso)
        tema_falso = SimpleNamespace(CARTAO='cor', ROSA='cor', TEXTO='cor', TEXTO_FRACO='cor',
                                     AVISO='cor', SUCESSO='cor', fonte=lambda *_: ('fonte', 12))
        contexto = {'__name__': 'app._teste_montagem_validacao', '__package__': 'app',
                    'ctk': widgets,
                    'tk': SimpleNamespace(StringVar=VariavelFalsa, BooleanVar=VariavelFalsa,
                                          Listbox=WidgetFalso, MULTIPLE='multiple'),
                    'tema': tema_falso, 'secao': lambda *_args: WidgetFalso(),
                    'PERIGO': {}, 'SECUNDARIO': {}}
        exec(compile(modulo, str(origem), 'exec'), contexto)
        objeto = contexto['PainelSemJanela']()
        objeto.nome = objeto.palavra = 'Jarvis'
        for nome in ('_val_atualizar_botao_claude', '_val_atualizar_escopo', '_val_desenhar',
                     '_val_comecar', '_val_marcar', '_val_errado', '_val_repetir',
                     '_val_anterior', '_val_parar', '_val_confirmar_erro', '_val_ir_direcionado',
                     '_val_abrir_relatorio', '_val_mandar_claude', '_val_esperar_git'):
            setattr(objeto, nome, lambda *_: None)
        objeto._aba_validacao(WidgetFalso())
        self.assertEqual(len(objeto.lista_val_grupos.linhas), len(validacao.grupos_disponiveis(validacao.ler_roteiro())))

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

    def test_relatorio_final_consolida_sequencia_e_distingue_pendencias(self):
        roteiro = ('## Novidades\n### Falas\n| Frase | Ação | Esperado |\n|---|---|---|\n'
                   '| `Mestre, abre` → `Mestre, fecha` <!-- validacao id=sequencia --> | duas falas | `_cmd_abrir` `_cmd_fechar` |\n'
                   '| `Mestre, teste` <!-- validacao id=falha --> | funciona | `_cmd_teste` |\n'
                   '| `Mestre, pular` <!-- validacao id=pulo --> | funciona | `_cmd_pular` |\n'
                   '### Rede\n| Frase | Ação | Esperado |\n|---|---|---|\n'
                   '| Se a rede estiver ligada <!-- validacao id=condicao --> | necessária | (painel) |\n'
                   '| `Mestre, online` <!-- validacao id=dependente --> | funciona | `_cmd_online` |\n'
                   '### Conferência\n| Frase | Ação | Esperado |\n|---|---|---|\n'
                   '| (painel) Confira a tela <!-- validacao id=manual --> | aparece | (painel) |\n')
        itens = validacao.ler_roteiro(texto=roteiro)
        sessao = validacao.Sessao(itens, 'Completo')
        sessao.marcar('ok')  # primeira etapa da sequência; segunda ficou pendente
        sessao.mostrar(2)
        sessao.marcar('falha', {'ouvi': 'teste', 'rota': '_cmd_errado'}, 'falha')
        sessao.marcar('pulado')
        sessao.marcar('bloqueado')  # pré-condição bloqueia também a fala seguinte
        sessao.interrompida = True
        with tempfile.TemporaryDirectory(prefix='mestre_relatorio_final_') as tmp:
            texto = validacao.gerar_relatorio(sessao, 'Jarvis', datetime(2026, 9, 29, 3),
                                              Path(tmp)).read_text(encoding='utf-8')
        aprovados = texto.split('## Itens aprovados', 1)[1].split('## Falhas', 1)[0]
        self.assertNotIn('`sequencia`', aprovados)
        self.assertIn('`sequencia`', texto.split('## Itens não executados', 1)[1])
        self.assertIn('1 de 2 etapas aprovadas', texto)
        for secao in ('Resumo para você', 'Falhas que precisam de investigação', 'Itens bloqueados',
                      'Itens pulados', 'Itens não executados', 'Recomendações e testes físicos pendentes',
                      'Detalhes técnicos', 'Testes físicos pendentes'):
            self.assertIn(secao, texto)
        self.assertIn('Pré-condição não atendida', texto)
        self.assertIn('`manual`', texto.split('### Testes físicos pendentes', 1)[1])
        self.assertIn('**Modo:** Completo', texto)
        self.assertIn('**Itens carregados:** 6', texto)
        self.assertIn('relatório parcial', texto)
        completo = validacao.Sessao(itens[:1], 'Completo')
        completo.marcar('ok')
        completo.marcar('ok')
        with tempfile.TemporaryDirectory(prefix='mestre_sequencia_ok_') as tmp:
            aprovado = validacao.gerar_relatorio(completo, 'Jarvis', datetime(2026, 9, 29, 4),
                                                 Path(tmp)).read_text(encoding='utf-8')
        self.assertIn('`sequencia`', aprovado.split('## Itens aprovados', 1)[1].split('## Falhas', 1)[0])
        for veredito, secao in (('falha', 'Falhas que precisam de investigação'),
                                 ('bloqueado', 'Itens bloqueados'), ('pulado', 'Itens pulados')):
            with self.subTest(veredito=veredito):
                parcial = validacao.Sessao(itens[:1], 'Completo')
                parcial.marcar('ok')
                parcial.marcar(veredito)
                agrupado = validacao._itens_consolidados(parcial.lista_completa())
                self.assertEqual(agrupado[0][1], veredito)
                with tempfile.TemporaryDirectory(prefix='mestre_sequencia_estado_') as tmp:
                    texto_estado = validacao.gerar_relatorio(parcial, 'Jarvis', datetime(2026, 9, 29, 5),
                                                             Path(tmp)).read_text(encoding='utf-8')
                self.assertNotIn('`sequencia`', texto_estado.split('## Itens aprovados', 1)[1]
                                 .split('## Falhas', 1)[0])
                secao_texto = texto_estado.split('## ' + secao, 1)[1].split('## ', 1)[0]
                self.assertIn('`sequencia`', secao_texto)

    def test_feedbacks_equivalentes_nao_repetem_e_ambiguos_sao_sinalizados(self):
        item = validacao.ler_roteiro(texto=(
            '## Novidades\n### Falas\n| Frase | Ação | Esperado |\n|---|---|---|\n'
            '| `Mestre, teste` <!-- validacao id=caso --> | resposta certa | `_cmd_teste` |\n'))[0]
        sessao = validacao.Sessao([item], 'Direcionado')
        sessao.marcar('falha', {'ouvi': 'teste', 'entendi': 'teste', 'rota': '_cmd_errado',
                               'fiz': 'resposta errada', 'audio': 'primeiro.wav'}, 'falha', 'resposta certa')
        with tempfile.TemporaryDirectory(prefix='mestre_deduplicacao_') as tmp:
            arquivo = Path(tmp) / 'MELHORIAS.md'
            prefixo = '# Melhorias\n- [ ] ideia anterior sem alteração\n'
            arquivo.write_text(prefixo, encoding='utf-8')
            novas = validacao.salvar_feedbacks(sessao, arquivo, datetime(2026, 9, 29))
            self.assertEqual(len(novas), 1)
            self.assertIn('validacao-dados etapa=caso assinatura=', novas[0])
            antes = arquivo.read_bytes()
            mesma_falha = validacao.Sessao([item], 'Direcionado')
            mesma_falha.marcar('falha', {'ouvi': 'teste', 'entendi': 'teste', 'rota': '_cmd_errado',
                                       'fiz': 'resposta errada', 'audio': 'segundo.wav'},
                               'falha', 'resposta certa')
            self.assertEqual(validacao.salvar_feedbacks(mesma_falha, arquivo, datetime(2026, 9, 30)), [])
            self.assertEqual(arquivo.read_bytes(), antes)
            self.assertTrue(arquivo.read_text(encoding='utf-8').startswith(prefixo))

            diferente = validacao.Sessao([item], 'Direcionado')
            diferente.marcar('falha', {'ouvi': 'teste', 'entendi': 'teste', 'rota': '_cmd_errado',
                                     'fiz': 'outra resposta'}, 'falha', 'resposta certa')
            novas = validacao.salvar_feedbacks(diferente, arquivo, datetime(2026, 10, 1))
            self.assertEqual(len(novas), 1)
            self.assertIn('possível duplicidade', novas[0])
            self.assertEqual(arquivo.read_text(encoding='utf-8').count('FEEDBACK:'), 2)

            legado = Path(tmp) / 'LEGADO.md'
            corpo = validacao.linha_feedback(item, sessao.resultados[0])
            corpo = corpo.split(' <!-- validacao-feedback', 1)[0]
            corpo = corpo.replace(' [áudio: primeiro.wav]', '')
            legado.write_text(f'- [ ] (28/09/2026) {corpo}\n', encoding='utf-8')
            self.assertEqual(validacao.salvar_feedbacks(sessao, legado, datetime(2026, 9, 29)), [])
            self.assertEqual(legado.read_text(encoding='utf-8').count('FEEDBACK:'), 1)
            duvidoso = validacao.salvar_feedbacks(diferente, legado, datetime(2026, 10, 1))
            self.assertEqual(len(duvidoso), 1)
            self.assertIn('possível duplicidade', duvidoso[0])
            concluido = Path(tmp) / 'CONCLUIDO.md'
            concluido.write_text(f'- [x] (28/09/2026) {corpo}\n', encoding='utf-8')
            recorrente = validacao.salvar_feedbacks(sessao, concluido, datetime(2026, 10, 1))
            self.assertEqual(len(recorrente), 1)  # regressão nova não some atrás de um item já concluído
            self.assertIn('possível duplicidade', recorrente[0])


class ValidacaoCorrecoes(unittest.TestCase):
    """Cartão 20260929-195357-a641ed: etapas com o esperado certo, instruções claras, captura sem
    misturar etapas, comando feito pela IA visível e Rápido dinâmico."""
    CAB = '## Novidades\n### Grupo\n| Frase | Ação | Esperado |\n|---|---|---|\n'

    def _itens(self, *linhas):
        return validacao.ler_roteiro(texto=self.CAB + '\n'.join(linhas))

    def test_sequencia_com_um_comando_so_vale_para_a_ultima_etapa(self):
        item = self._itens('| `Mestre, que horas são` e, no meio da resposta, `Mestre, abre o Spotify` '
                           '| A fala para e o Spotify abre | `_cmd_abrir` |')[0]
        etapas = validacao.Sessao([item]).itens
        self.assertEqual([(e.tipo, e.comandos) for e in etapas], [('preparo', []), ('comando', ['_cmd_abrir'])])
        self.assertNotIn('_cmd_abrir', etapas[0].esperado)
        self.assertEqual(validacao.conferir(etapas[0], {'rota': '_cmd_hora_data'}), 'ok')
        self.assertEqual(validacao.conferir(etapas[0], {'rota': 'ignorado (ruido)'}), 'falha')
        self.assertEqual(etapas[1].instrucao, 'no meio da resposta')
        self.assertTrue(etapas[0].colada)
        self.assertIn('Mestre, abre o Spotify', etapas[0].proxima)

    def test_sequencia_com_esperado_por_etapa(self):
        item = self._itens('| `Mestre, me conta uma curiosidade` e, no meio da resposta, `Mestre, para` '
                           '| Só para | (IA) → `_cmd_parar` |')[0]
        a, b = validacao.Sessao([item]).itens
        self.assertEqual((a.tipo, a.comandos, b.tipo, b.comandos), ('ia', [], 'comando', ['_cmd_parar']))
        self.assertEqual(validacao.conferir(a, {'rota': 'ia'}), 'ok')
        # "para" durante a fala: o ouvido só cala (rota "ignorado (só parou de falar)") e isso conta
        self.assertEqual(validacao.conferir(b, {'rota': 'ignorado (só parou de falar)'}), 'ok')
        self.assertEqual(validacao.conferir(b, {'rota': '_cmd_parar'}), 'ok')

    def test_voltar_do_descanso_conta_como_descanso(self):
        item = self._itens('| `Mestre, bora voltar a trabalhar` | acorda | `_cmd_descanso` |')[0]
        self.assertEqual(validacao.conferir(item, {'rota': 'saiu do descanso'}), 'ok')

    def test_alternativas_com_ou_nao_viram_sequencia(self):
        item = self._itens('| `Mestre, volta pro fone` (ou `coloca no fone`, `agora tô usando o fone`) '
                           '| volta pro fone | `_cmd_saida_som` |')[0]
        self.assertEqual((item.tipo_item, item.falas), ('fala', ['Mestre, volta pro fone']))
        self.assertIn('coloca no fone', item.nota)

    def test_instrucoes_dizem_o_que_fazer_falar_esperar_e_observar(self):
        itens = self._itens(
            '| Desligue o Bluetooth da caixinha e fale `Mestre, coloca na caixinha` | avisa | `_cmd_saida_som` |',
            '| `Mestre, pausa o vídeo` (YouTube em 2 telas) | pausa | `_cmd_youtube_controle` |',
            '| Espere passar o tempo de castigo | volta | (IA) |',
            '| Confira o indicador | aparece | (visual) |',
            '| Se a rede estiver ligada | necessário | (painel) |',
            '| (painel) Clique em Salvar | salva | (painel) |',
            '| Rode `ferramentas\\x.bat` (responda `s`) | cria | (ferramenta) |')
        rotulos = [[r for r, _ in validacao.instrucoes(i, 'Jarvis')] for i in itens]
        self.assertEqual(itens[0].tipo_item, 'fala')   # a fala é o teste; a ação vem antes
        self.assertEqual(validacao.instrucoes(itens[0], 'Jarvis')[:2],
                         [('FAÇA ANTES', 'Desligue o Bluetooth da caixinha'), ('FALE', 'Jarvis, coloca na caixinha')])
        self.assertIn('ATENÇÃO', rotulos[1])
        self.assertEqual([r[0] for r in rotulos[2:]], ['ESPERE', 'OBSERVE', 'CONFIRA ANTES', 'FAÇA', 'FAÇA'])
        self.assertEqual(itens[6].tipo_item, 'acao_manual')   # comando de terminal nunca vai ao microfone
        for linhas in rotulos:
            self.assertIn('DEVE ACONTECER', linhas)
        self.assertNotIn('Mestre', ' '.join(t for _, t in validacao.instrucoes(itens[0], 'Jarvis')))

    def test_captura_ignora_pedido_da_etapa_anterior_que_demorou(self):
        t0 = 2_000_000.0
        ouv = [{'ts': t0 - 5, 'texto': 'Mestre, manda um print no Telegram', 'chamou': True},
               {'ts': t0 + 2, 'texto': 'Mestre, que horas são', 'chamou': True}]
        hist = [{'ts': t0 + 1, 'tipo': 'comando', 'pedido': 'Mestre, manda um print no Telegram',
                 'rota': '_cmd_print_telegram', 'resposta': 'Tirando o print.'}]
        item = self._itens('| `Mestre, que horas são` | hora | `_cmd_hora_data` |')[0]
        c = validacao.capturar(t0, hist, ouv, item)
        self.assertEqual(c['rota'], '')   # ainda não registrou a hora; o print não conta
        hist.append({'ts': t0 + 3, 'tipo': 'comando', 'pedido': 'Mestre, que horas são',
                     'rota': '_cmd_hora_data', 'resposta': 'São dez.'})
        self.assertEqual(validacao.capturar(t0, hist, ouv, item)['rota'], '_cmd_hora_data')

    def test_captura_prefere_o_pedido_parecido_com_a_frase_da_tela(self):
        t0 = 3_000_000.0
        hist = [{'ts': t0 + 2, 'tipo': 'comando', 'pedido': 'Mestre, aumenta o volume', 'rota': '_cmd_volume'},
                {'ts': t0 + 6, 'tipo': 'comando', 'pedido': 'não registrou o comando certo', 'rota': 'ia'}]
        ouv = [{'ts': t0 + 1, 'texto': 'Mestre, aumenta o volume', 'chamou': True},
               {'ts': t0 + 5, 'texto': 'não registrou o comando certo', 'conversa': True}]
        item = self._itens('| `Mestre, aumenta o volume` | sobe | `_cmd_volume` |')[0]
        c = validacao.capturar(t0, hist, ouv, item)
        self.assertEqual((c['rota'], c['ouvi'], c['outros']), ('_cmd_volume', 'Mestre, aumenta o volume', 1))
        self.assertIn('mais 1 pedido', validacao.diagnostico(c))

    def test_comando_feito_pela_ia_aparece_na_hora(self):
        t0 = 4_000_000.0
        hist = [{'ts': t0 + 1, 'tipo': 'ia executou comando', 'pedido': 'me dá uma dica de livro',
                 'rota': '_cmd_youtube', 'ia_texto': 'abre o youtube'},
                {'ts': t0 + 2, 'tipo': 'comando', 'pedido': 'Mestre, me dá uma dica de livro', 'rota': 'ia',
                 'entendi': 'me da uma dica de livro', 'resposta': 'Youtube já estava aberto.'}]
        ouv = [{'ts': t0 + 0.5, 'texto': 'Mestre, me dá uma dica de livro', 'chamou': True}]
        item = self._itens('| `Mestre, me dá uma dica de livro` | pensa | (vai pensar, sem comando) |')[0]
        c = validacao.capturar(t0, hist, ouv, item)
        self.assertEqual((c['rota'], c['ia_comando']), ('_cmd_youtube', '_cmd_youtube'))
        self.assertEqual(validacao.conferir(item, c), 'falha')
        self.assertIn('a IA a transformou em _cmd_youtube', validacao.explicar(item, c, 'falha'))
        ultimos = validacao.ultimos_comandos(5, hist, ouv)
        self.assertEqual(len(ultimos), 1)   # o registro da IA não parece um pedido repetido
        self.assertIn('ia → _cmd_youtube', ultimos[0]['entendi'])

    def test_etapa_colada_aceita_fala_antes_de_aparecer_na_tela(self):
        item = self._itens('| `Mestre, que horas são` e, no meio da resposta, `Mestre, abre o Spotify` '
                           '| abre | `_cmd_hora_data` → `_cmd_abrir` |')[0]
        sessao = validacao.Sessao([item])
        ref = 5_000_000.0
        sessao.exibida_em = ref + 100
        sessao.marcar('ok', {'rota': '_cmd_hora_data', 'ts': ref})
        self.assertAlmostEqual(sessao.exibida_em, ref + 0.01)
        r = validacao.avaliar_continuo(sessao.itens[0], ref - 1, ref + 1,
                                       [{'ts': ref, 'tipo': 'comando', 'pedido': 'Mestre, que horas são',
                                         'rota': '_cmd_hora_data'}],
                                       [{'ts': ref - 0.5, 'texto': 'Mestre, que horas são', 'chamou': True}])
        self.assertEqual((r['estado'], r['avanco']), ('ok', validacao.AVANCO_COLADO))

    def test_rapido_dinamico_usa_feedbacks_recentes_e_arquivos(self):
        itens = validacao.ler_roteiro()
        so_base = validacao.selecionar_rapido(itens, [], [])
        self.assertEqual([i.id for i in so_base.itens], list(validacao.IDS_RAPIDOS))
        self.assertIn('Nenhum arquivo alterado', validacao.descrever_escopo(so_base))
        alvo = next(i for i in itens if i.exige_microfone and i.id not in validacao.IDS_RAPIDOS)
        com_fb = validacao.selecionar_rapido(itens, [], [{'id': alvo.id, 'data': '29/09/2026'}])
        self.assertIn(alvo.id, [i.id for i in com_fb.itens])
        self.assertIn('feedback de 29/09/2026', validacao.descrever_escopo(com_fb))
        por_arquivo = validacao.selecionar_rapido(itens, ['app/ouvido.py'], [])
        extras = [i for i in por_arquivo.itens if i.id not in validacao.IDS_RAPIDOS]
        self.assertTrue(extras and len(extras) <= validacao.MAXIMO_EXTRAS_RAPIDO)
        self.assertTrue(all(i.exige_microfone for i in por_arquivo.itens))   # nada físico no Rápido
        self.assertIn('arquivo app/ouvido.py', validacao.descrever_escopo(por_arquivo))
        ids = [i.id for i in por_arquivo.itens]
        self.assertEqual(len(ids), len(set(ids)))
        # feedback antigo (sem ID) só entra se a frase E o esperado anotados batem
        antigo = validacao.selecionar_rapido(itens, [], [
            {'id': '', 'ouvi': 'Assessor, qual saída de som tá ativa?', 'esperado': '_cmd_saida_som',
             'data': '29/09/2026'},
            {'id': '', 'ouvi': 'Assessor, qual saída de som tá ativa?', 'esperado': '_cmd_abrir',
             'data': '29/09/2026'}])
        self.assertEqual([i.id for i in antigo.itens if i.id not in validacao.IDS_RAPIDOS], ['item-027'])

    def test_feedbacks_recentes_le_data_id_e_esperado(self):
        with tempfile.TemporaryDirectory(prefix='mestre_fb_recente_') as tmp:
            arquivo = Path(tmp) / 'MELHORIAS.md'
            arquivo.write_text(
                '- [ ] (29/09/2026) FEEDBACK: ouvi "Assessor, abre" · entendi "x" · respondi "y" · o certo era: z '
                '(validação: esperado _cmd_abrir) <!-- validacao-feedback id=item-9 -->\n'
                '- [ ] (20/09/2026) FEEDBACK: ouvi "velho" · o certo era: z (validação: esperado (IA))\n'
                '- [x] (29/09/2026) FEEDBACK: ouvi "feito" (validação: esperado _cmd_abrir)\n', encoding='utf-8')
            lidos = validacao.feedbacks_recentes(arquivo, 3, datetime(2026, 9, 29, 20, 0))
        self.assertEqual(lidos, [{'id': 'item-9', 'ouvi': 'Assessor, abre', 'esperado': '_cmd_abrir',
                                  'data': '29/09/2026'}])

    def test_ia_registra_na_hora_o_comando_que_rodou(self):
        from app.comandos.ia import IAMixin
        registros, agendados = [], []
        falso = SimpleNamespace(
            _frase_original='', ultimo_comando='_cmd_youtube',
            _separar_monitor=lambda t: t, vocab=SimpleNamespace(traduzir=lambda t: t),
            _tentar_comandos=lambda t: True,
            _agendar_memoria_ia=lambda *a: agendados.append(a))
        with patch('app.comandos.ia.memoria.registrar', side_effect=lambda *a, **k: registros.append(a)):
            IAMixin._usar_interpretacao(falso, {'tipo': 'comando', 'texto': 'abre o youtube'}, 'me da uma dica')
        self.assertEqual(registros, [('me da uma dica', '', 'ia executou comando',
                                      {'entendi': 'abre o youtube', 'ia_texto': 'abre o youtube',
                                       'rota': '_cmd_youtube'})])
        self.assertEqual(len(agendados), 1)   # a memória continua esperando a confirmação (~30 s)

    def test_painel_mostra_o_que_fazer_e_o_que_conferir(self):
        """Executa _val_desenhar de verdade com rótulos falsos (sem abrir janela)."""
        origem = Path(__file__).resolve().parents[1] / 'app' / 'painel.py'
        arvore = ast.parse(origem.read_text(encoding='utf-8'))
        painel = next(n for n in arvore.body if isinstance(n, ast.ClassDef) and n.name == 'Painel')
        metodos = [n for n in painel.body if isinstance(n, ast.FunctionDef)
                   and n.name in ('_val_desenhar', '_val_desenhar_continuo')]
        modulo = ast.fix_missing_locations(ast.Module(body=[ast.ClassDef(
            name='PainelSemJanela', bases=[], keywords=[], body=metodos, decorator_list=[])], type_ignores=[]))

        class Rotulo:
            texto = ''

            def configure(self, **opcoes):
                self.texto = opcoes.get('text', self.texto)

            def pack(self, **_):
                pass

            def pack_forget(self):
                pass

            def winfo_manager(self):
                return ''

        contexto = {'__name__': 'app._teste_desenho_validacao', '__package__': 'app',
                    'tema': SimpleNamespace(SUCESSO=1, AVISO=2, TEXTO_FRACO=3, fonte=lambda *_: None)}
        exec(compile(modulo, str(origem), 'exec'), contexto)
        o = contexto['PainelSemJanela']()
        o.palavra = 'Jarvis'
        for nome in ('rot_val_progresso', 'rot_val_frase', 'rot_val_esperado', 'rot_val_sugestao',
                     'bt_val_comecar', 'fr_val_destaque'):
            setattr(o, nome, Rotulo())
        o._val_botoes, o.rot_val_linhas = [], {k: Rotulo() for k in ('ouvi', 'entendi', 'fiz')}
        o.rot_val_destaque = {k: (Rotulo(), Rotulo()) for k in ('ouvi', 'entendi', 'fiz', 'descartes')}
        o._val_captura = o._val_sugestao = None
        o._val_estado, o._val_descartes = '', []
        itens = self._itens(
            '| Desligue o Bluetooth e fale `Mestre, coloca na caixinha` | avisa | `_cmd_saida_som` |',
            '| `Mestre, que horas são` e, no meio da resposta, `Mestre, abre o Spotify` | abre '
            '| `_cmd_hora_data` → `_cmd_abrir` |',
            '| (visual) confira o log | tem a linha | (visual) |')
        o._val = validacao.Sessao(itens, 'Completo')
        telas = []
        for indice in range(len(o._val.itens)):
            o._val.indice = indice
            o._val_desenhar()
            telas.append((o.rot_val_frase.texto, o.rot_val_esperado.texto))
        self.assertEqual(telas[0][0].splitlines(), ['FAÇA ANTES: Desligue o Bluetooth',
                                                    'FALE: “Jarvis, coloca na caixinha”'])
        self.assertIn('COMANDO ESPERADO: _cmd_saida_som', telas[0][1])
        self.assertIn('COMANDO ESPERADO: _cmd_hora_data', telas[1][1])
        self.assertIn('EM SEGUIDA: no meio da resposta: Jarvis, abre o Spotify', telas[1][1])
        self.assertEqual(telas[2][0].splitlines(), ['ETAPA 2 de 2', 'QUANDO: no meio da resposta',
                                                    'FALE: “Jarvis, abre o Spotify”'])
        self.assertIn('COMANDO ESPERADO: _cmd_abrir', telas[2][1])
        self.assertTrue(telas[3][0].startswith('OBSERVE: '))
        self.assertNotIn('COMANDO ESPERADO', telas[3][1])

    def test_roteiro_real_nao_tem_etapa_com_comando_de_outra(self):
        """As linhas de sequência do roteiro dizem o esperado de cada etapa (nada de "que horas são"
        esperando _cmd_abrir)."""
        roteiro = validacao.ler_roteiro()
        for item in roteiro:
            if item.tipo_item != 'sequencia' or not all(e.independente for e in item.etapas):
                continue
            self.assertNotIn('preparo', [e.tipo for e in validacao.dividir_sequencia(item)], item.id)
        hora = validacao.dividir_sequencia(next(i for i in roteiro if i.id == 'item-069'))[0]
        self.assertEqual(hora.comandos, ['_cmd_hora_data'])


class TelegramSemRede(unittest.TestCase):
    """Pedidos reais do celular (29/09) que iam pro projeto em vez de virar comando."""

    def setUp(self):
        from app import recebidos
        self.caixa = object.__new__(recebidos.Caixa)   # sem threads nem rede
        self.caixa.cfg = {"assistente": {"palavra_ativacao": "Assessor"}}
        self.caixa._energia = {}
        self.respostas, self.prints = [], []
        self.caixa.responder = lambda chat, texto: self.respostas.append(texto)
        self.caixa._telegram_print = lambda chat, monitor: self.prints.append(monitor)

    def test_mande_print_e_palavra_de_ativacao(self):
        self.assertTrue(self.caixa._comando_especial(1, "Mande print pro robô"))
        self.assertTrue(self.caixa._comando_especial(1, "Mande print do monitor 2"))
        self.assertTrue(self.caixa._comando_especial(1, "Assessor, print"))
        self.assertEqual(self.prints, [None, 2, None])

    def test_energia_com_mande_e_com_a_palavra(self):
        for pedido in ("Mande desligar", "Assessor dormir ou suspender", "suspender ou dormir"):
            self.assertTrue(self.caixa._comando_especial(1, pedido), pedido)
            self.assertIn("certeza", self.respostas[-1].lower())
            with patch("app.sistema.cancelar_desligamento"), patch("app.sistema.cancelar_suspensao"):
                self.assertTrue(self.caixa._comando_especial(1, "cancela"))

    def test_oque_junto_vira_o_que(self):
        self.assertEqual(self.caixa._pedido_do_celular("Assessor oque tá tocando"), "o que ta tocando")

    def test_texto_comum_continua_indo_pro_destino(self):
        self.assertFalse(self.caixa._comando_especial(1, "Mande uma ideia pro projeto do painel"))
        self.assertFalse(self.caixa._comando_especial(1, "Trocando o apelido não registrou"))


if __name__ == "__main__":
    unittest.main()
