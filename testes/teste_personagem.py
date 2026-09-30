"""Personagem 2D do Assessor (app/personagem), sem Qt, sem janela e sem rede: catálogo, cena, animação, passeio, opções.

O desenho na tela (Qt) e a página de teste no navegador (JavaScript) são conferidos à parte, no Windows, por
`venv\\Scripts\\python -m ferramentas.verificar_personagem` (não roda dentro da barreira dos testes seguros).
"""
import math
import re
import sys
import unittest
from pathlib import Path

from app import avatar
from app.personagem import catalogo as cat
from app.personagem import catalogo_animacao as A
from app.personagem import cena
from app.personagem.animacao import Aleatorio, Animador, arquetipo_do_estilo, visemas_do_texto
from app.personagem.opcoes import ALTURA_PADRAO_PX, dimensoes, opcoes_do_config
from app.personagem.passeio import MODOS, Passeio, do_config

RAIZ = Path(__file__).resolve().parents[1]
HEX = re.compile(r"^#[0-9A-F]{6}$")
NOS_OBRIGATORIOS = {"raiz", "perna_e", "perna_d", "torso", "capa", "cabelo_tras", "cabeca", "olho_e", "olho_d", "abertura_e", "abertura_d",
                    "iris_e", "iris_d", "sobr_e", "sobr_d", "boca", "cabelo_frente", "acessorio", "mascara_baixo", "mascara_cima",
                    "braco_e", "braco_d", "antebraco_e", "antebraco_d", "mao_e", "mao_d"}


def _ids_do_rig(no=None):
    no = no or cat.RIG
    yield no["id"]
    for f in no.get("filhos", []):
        yield from _ids_do_rig(f)


def _caminho_ok(d: str) -> bool:
    """Só M L Q C Z absolutos, com a quantidade certa de números e o primeiro comando M."""
    toks = d.split()
    if not toks or toks[0] != "M":
        return False
    i, qtd = 0, {"M": 2, "L": 2, "Q": 4, "C": 6, "Z": 0}
    while i < len(toks):
        c = toks[i]
        if c not in qtd:
            return False
        nums = toks[i + 1:i + 1 + qtd[c]]
        if len(nums) != qtd[c]:
            return False
        try:
            [float(x) for x in nums]
        except ValueError:
            return False
        i += 1 + qtd[c]
    return True


def _todas_prims(no):
    for p in no["prims"]:
        yield p
    for f in no["filhos"]:
        yield from _todas_prims(f)


class CatalogoDoPersonagem(unittest.TestCase):
    def test_quantidades_pedidas(self):
        # 2ª rodada (30/09): o dono pediu "mais cabelo, mais cabeça, mais fantasia, mais tudo"
        self.assertGreaterEqual(len(cat.CABELOS), 20)
        self.assertGreaterEqual(len(cat.ROUPAS), 16)
        self.assertGreaterEqual(len(cat.ACESSORIOS), 25)
        self.assertGreaterEqual(len(cat.CORES_CABELO), 15)
        self.assertGreaterEqual(len(cat.PELES), 8)
        marvel = [t for t in cat.TRAJES.values() if t["universo"] == "Marvel"]
        dc = [t for t in cat.TRAJES.values() if t["universo"] == "DC"]
        classicas = [t for t in cat.TRAJES.values() if t["universo"] == "Clássicas"]
        self.assertGreaterEqual(len(marvel), 20)
        self.assertGreaterEqual(len(dc), 18)
        self.assertGreaterEqual(len(classicas), 10)
        self.assertEqual({t["universo"] for t in cat.TRAJES.values()}, set(cat.UNIVERSOS))
        for opc in cat.ROSTO_ORDEM:
            self.assertGreaterEqual(len(cat.ROSTO["m"][opc]), 4, opc)
            self.assertEqual(cat.ROSTO["m"][opc].keys(), cat.ROSTO["f"][opc].keys())
            self.assertIn(cena.PERFIL_PADRAO[opc], cat.ROSTO["m"][opc])
        for nome in ("Homem de Ferro", "Homem-Aranha", "Super-Homem", "Batman", "Flash"):   # os que o dono citou
            self.assertIn(nome, [t["nome"] for t in cat.TRAJES.values()])
        for t in cat.TRAJES.values():
            self.assertTrue(t["nome"] and set(t["pecas"]) == {"m", "f"})
        for r in cat.ROUPAS.values():
            self.assertTrue(r["nome"] and len(r["cores"]) == 3 and set(r["pecas"]) == {"m", "f"})

    def test_toda_primitiva_e_valida(self):
        tem_fantasia = [""] + list(cat.TRAJES)
        for g in "mf":
            for tid in tem_fantasia:
                sc = cena.montar({"genero": g, "traje": tid, "acessorios": list(cat.ACESSORIOS)})
                for no in cena.nos(sc):
                    for p in no["prims"]:
                        self.assertIn(p["t"], ("el", "rr", "pa"), (tid, no["id"]))
                        if p["t"] == "pa":
                            self.assertTrue(_caminho_ok(p["d"]), (tid, no["id"], p["d"][:60]))
                        elif p["t"] == "el":
                            self.assertTrue(all(k in p for k in ("x", "y", "rx", "ry")))
                        else:
                            self.assertTrue(all(k in p for k in ("x", "y", "w", "h", "r")))
                        self.assertTrue(0 <= p.get("o", 1) <= 1 and p.get("lw", 0) >= 0)
                        for k in ("f", "s"):
                            v = p.get(k)
                            for c in (v[1:] if isinstance(v, list) else ([v] if v else [])):
                                self.assertRegex(c, HEX, (tid, no["id"], k))

    def test_montar_todas_as_combinacoes(self):
        for g in "mf":
            for cab in cat.CABELOS:
                for rou in cat.ROUPAS:
                    sc = cena.montar({"genero": g, "cabelo": cab, "roupa": rou})
                    ids = [n["id"] for n in cena.nos(sc)]
                    self.assertEqual(len(ids), len(set(ids)))
                    self.assertTrue(NOS_OBRIGATORIOS <= set(ids), NOS_OBRIGATORIOS - set(ids))
            for tid in cat.TRAJES:
                sc = cena.montar({"genero": g, "traje": tid})
                self.assertGreater(len(list(_todas_prims(sc["raiz"]))), 30, tid)
                self.assertTrue(sc["sombra"])

    def test_esqueleto_e_o_mesmo_id_do_catalogo(self):
        ids = list(_ids_do_rig())
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(NOS_OBRIGATORIOS <= set(ids))

    def test_fantasia_manda_no_cabelo_e_na_pele(self):
        batman = cena.montar({"traje": "batman", "cabelo": "longo"})
        nos = {n["id"]: n for n in cena.nos(batman)}
        self.assertEqual(nos["cabelo_frente"]["prims"], [])   # capuz cobre o cabelo
        thor = {n["id"]: n for n in cena.nos(cena.montar({"traje": "thor", "cabelo": "curto"}))}
        self.assertTrue(thor["cabelo_tras"]["prims"])          # Thor é sempre de cabelo comprido
        hulk = cena.montar({"traje": "hulk", "pele": "clara"})
        cores = {p["f"][1] for n in cena.nos(hulk) if n["id"] == "cabeca" for p in n["prims"] if isinstance(p.get("f"), list)}
        from app.personagem.arte import resolver_cor
        self.assertIn(resolver_cor("$pele+", {"pele": "#6FBF4A"}), cores)   # rosto verde, não o tom de pele escolhido
        sem_ac = {n["id"]: n for n in cena.nos(cena.montar({"traje": "homem_de_ferro", "acessorios": ["oculos", "barba"]}))}
        self.assertEqual(sem_ac["acessorio"]["prims"], [])     # capacete esconde acessório do rosto

    def test_roupa_e_cores_do_usuario(self):
        a = cena.montar({"roupa": "camiseta", "roupa_cor1": "vermelho"})
        b = cena.montar({"roupa": "camiseta", "roupa_cor1": "verde"})
        self.assertNotEqual(a["raiz"], b["raiz"])
        c = {n["id"]: n for n in cena.nos(cena.montar({"roupa": "moletom", "genero": "m"}))}
        d = {n["id"]: n for n in cena.nos(cena.montar({"roupa": "moletom", "genero": "f"}))}
        self.assertNotEqual(c["torso"]["prims"], d["torso"]["prims"])   # torso feminino é outro desenho

    def test_normalizar_perfil_velho_ou_com_lixo(self):
        p = cena.normalizar(None)
        self.assertEqual(p, cena.PERFIL_PADRAO | {"acessorios": []})
        p = cena.normalizar({"genero": "Feminino", "cabelo": "inexistente", "roupa": "xxx", "traje": "nada", "escala": "9", "acessorios": ["oculos", "oculos", "lixo"],
                             "pele": "#abcdef", "coisa_nova": 1})
        self.assertEqual((p["genero"], p["cabelo"], p["roupa"], p["traje"], p["escala"]), ("f", "longo", "camiseta", "", 1.6))
        self.assertEqual(p["acessorios"], ["oculos"])
        self.assertNotIn("coisa_nova", p)
        self.assertEqual(cena.normalizar({"escala": "abc"})["escala"], 1.0)
        self.assertEqual(cena.normalizar({"escala": 0.1})["escala"], 0.6)
        sc = cena.montar({"pele": "#123456", "olhos_cor": "cor-que-nao-existe"})   # cor inválida cai no padrão, sem erro
        self.assertTrue(sc["raiz"]["prims"] is not None)
        p = cena.normalizar({"rosto": "triangular", "nariz": 3, "olhos_estilo": "grande"})
        self.assertEqual((p["rosto"], p["nariz"], p["olhos_estilo"]), ("redondo", "botao", "grande"))

    def test_json_do_catalogo_e_pequeno_e_serializavel(self):
        import json
        texto = json.dumps(cat.como_dados())
        self.assertLess(len(texto), 1_200_000)   # entra inteiro na página de teste (um arquivo só)
        self.assertEqual(json.loads(texto)["trajes"].keys(), cat.TRAJES.keys())

    def test_cada_opcao_do_rosto_muda_o_desenho(self):
        def slots(perfil):
            return {n["id"]: n["prims"] for n in cena.nos(cena.montar(perfil))}
        base = slots({})
        for opc in cat.ROSTO_ORDEM:
            for val in cat.ROSTO["m"][opc]:
                if val != cena.PERFIL_PADRAO[opc]:
                    self.assertNotEqual(slots({opc: val}), base, (opc, val))
        # com fantasia: cabeça redonda (as máscaras foram desenhadas nela); olho da máscara manda, senão fica o escolhido
        self.assertEqual(slots({"traje": "robin", "rosto": "oval"})["cabeca"], slots({"traje": "robin"})["cabeca"])
        self.assertEqual(slots({"traje": "homem_aranha", "olhos_estilo": "pontinho"})["iris_e"], slots({"traje": "homem_aranha"})["iris_e"])
        self.assertNotEqual(slots({"traje": "robin", "olhos_estilo": "pontinho"})["iris_e"], slots({"traje": "robin"})["iris_e"])

    def test_braco_sem_emenda_e_lado_direito_espelhado(self):
        nos = {n["id"]: n for n in cena.nos(cena.montar({}))}
        self.assertTrue(nos["braco_e"].get("contorno") and nos["braco_d"].get("contorno"))
        self.assertTrue(nos["antebraco_d"].get("inv") and nos["mao_d"].get("inv"))    # giro positivo fecha para dentro nos dois lados
        self.assertFalse(nos["antebraco_e"].get("inv"))
        for no in ("braco_e", "antebraco_e"):
            contornos = [p for p in nos[no]["prims"] if p.get("c")]
            self.assertTrue(contornos and all(not p.get("f") and p.get("s") for p in contornos), no)
        mangas = {n["id"]: n for n in cena.nos(cena.montar({"roupa": "moletom"}))}
        self.assertGreaterEqual(sum(1 for p in mangas["antebraco_e"]["prims"] if p.get("c")), 2)   # pele + manga

    def test_cabelo_comprido_balanca_mais(self):
        self.assertGreater(cena.montar({"cabelo": "longo"})["balanco"], cena.montar({"cabelo": "curto"})["balanco"])
        self.assertEqual(cena.montar({"traje": "homem_aranha", "cabelo": "longo"})["balanco"], 0.0)   # sem cabelo à vista


class AnimacaoDoPersonagem(unittest.TestCase):
    def test_sorteio_igual_ao_do_javascript(self):
        r = Aleatorio(1)
        self.assertEqual([r.prox() for _ in range(4)], [0.6270739405881613, 0.002735721180215478, 0.5274470399599522, 0.9810509674716741])
        r = Aleatorio(12345)
        self.assertEqual([round(r.prox(), 10) for _ in range(3)], [0.9797282678, 0.3067522645, 0.4842054215])

    def test_estilos_da_personalidade_viram_jeitos(self):
        from app import personalidades
        self.assertEqual(set(A.ESTILO_PARA_ARQUETIPO), set(personalidades.ESTILOS))   # nenhum estilo ficou sem jeito
        for estilo, arq in A.ESTILO_PARA_ARQUETIPO.items():
            self.assertEqual(arquetipo_do_estilo(estilo), arq)
        self.assertEqual(arquetipo_do_estilo("Estilo inventado"), "parceiro")
        self.assertEqual(arquetipo_do_estilo("Sério e direto", "coach"), "coach")     # o dono pode forçar outro jeito
        self.assertEqual(arquetipo_do_estilo("Sério e direto", "xxx"), "serio")

    def test_canais_dos_clipes_existem_no_esqueleto(self):
        nos = set(_ids_do_rig()) | {"sombra", "boca", "olhos"}
        for nome, c in A.CLIPES.items():
            self.assertGreater(c["dur"], 0, nome)
            for canal, spec in c["trilhas"].items():
                no, _, prop = canal.partition(".")
                self.assertIn(no, nos, (nome, canal))
                self.assertIn(prop, ("x", "y", "r", "sx", "sy", "o"), (nome, canal))
                if "seno" in spec:
                    self.assertEqual(spec["seno"][2], int(spec["seno"][2]), (nome, canal))   # ciclos inteiros: o clipe emenda
                else:
                    ts = [t for t, _v in spec["k"]]
                    self.assertEqual(ts, sorted(ts), (nome, canal))
                    self.assertTrue(0 <= ts[0] and ts[-1] <= 1)
        for arq in A.ARQUETIPOS.values():
            for est, (clipe, expr) in arq["estado"].items():
                self.assertIn(clipe, A.CLIPES)
                self.assertIn(expr, A.EXPRESSOES)
            for g, peso in arq["idle"]:
                self.assertFalse(A.CLIPES[g]["loop"] and g != "parado")
                self.assertGreater(peso, 0)
            for extra in arq["base"]:
                self.assertIn(extra, A.CLIPES)
            self.assertIn(arq["chegada"], A.CLIPES)
            self.assertIn(arq["passeio"]["modo"], MODOS)
        for c in A.CLIPES.values():
            if c.get("expr"):
                self.assertIn(c["expr"], A.EXPRESSOES)

    def test_todos_os_jeitos_e_estados_geram_poses_finitas(self):
        for arq in A.ARQUETIPOS:
            for est in ("idle", "ouvindo", "pensando", "falando", "descansando"):
                an = Animador(arq, None, 3)
                an.mudar(est, 0.0)
                for i in range(240):
                    t = i / 60
                    if est == "falando":
                        an.nivel(0.5 + 0.5 * math.sin(t * 9), t)
                    q = an.quadro(t)
                    for canal, v in q["pose"].items():
                        if canal != "boca.v":
                            self.assertTrue(math.isfinite(v), (arq, est, canal))
                    self.assertIn(q["pose"]["boca.v"], {p["v"] for p in cat.CORPO["m"]["boca"]})
                    for k, v in q["extras"].items():
                        if k not in ("aura",):
                            self.assertTrue(math.isfinite(v))

    def test_cada_gesto_toca_por_inteiro_e_termina(self):
        for nome, c in A.CLIPES.items():
            if c["loop"]:
                continue
            an = Animador("parceiro", None, 2)
            an.quadro(0.0)
            self.assertTrue(an.gesto(nome, 0.0), nome)
            achou = False
            for i in range(int((c["dur"] + 1.5) * 60)):
                q = an.quadro(i / 60)
                achou = achou or q["gesto"] == nome
                self.assertTrue(all(math.isfinite(v) for k, v in q["pose"].items() if k != "boca.v"))
            self.assertTrue(achou, nome)
            self.assertIsNone(an.overlay, nome)   # acabou sozinho
        self.assertFalse(Animador().gesto("parado", 0.0))       # clipe que repete não é gesto avulso
        self.assertFalse(Animador().gesto("nao_existe", 0.0))

    def test_piscar_de_tempos_em_tempos(self):
        an = Animador("parceiro", None, 9)
        minimo, vezes, abaixo, abertos = 1.0, 0, False, 0
        for i in range(60 * 40):
            q = an.quadro(i / 60)
            a = q["pose"]["abertura_e.sy"]
            minimo = min(minimo, a)
            if a < 0.3 and not abaixo:
                vezes += 1
            abaixo = a < 0.3
            abertos += a > 0.5
        self.assertLess(minimo, 0.1)
        self.assertGreaterEqual(vezes, 5)     # em 40 s
        self.assertGreater(abertos, 60 * 40 * 0.6)   # de olho aberto quase o tempo todo (gesto sorridente fecha)

    def test_boca_segue_o_volume_e_as_vogais_do_texto(self):
        self.assertEqual(visemas_do_texto("Beleza, deixa comigo"), ["E", "E", "A", "E", "I", "A", "O", "M", "I", "O"])
        self.assertEqual(visemas_do_texto(""), [])
        an = Animador("parceiro", None, 1)
        an.mudar("falando", 0.0)
        an.texto("Ola pessoal")
        vistos, abertos = [], 0
        for i in range(60 * 6):
            t = i / 60
            an.nivel(0.15 + 0.85 * abs(math.sin(t * 7)), t)     # sílabas: o volume sobe e desce
            q = an.quadro(t)
            v = q["pose"]["boca.v"]
            if not vistos or vistos[-1] != v:
                vistos.append(v)
            abertos += v in ("A", "E", "I", "O", "U")
        self.assertGreater(len(set(vistos)), 3)               # muda de forma ao longo da fala
        self.assertGreater(abertos, 60)                       # e abre de verdade
        self.assertIn(vistos[0], ("A", "E", "I", "O", "U", "M", "sorriso"))
        calado = Animador("parceiro", None, 1)
        calado.mudar("falando", 0.0)
        calado.nivel(0.0, 0.0)
        for i in range(90):
            calado.nivel(0.0, i / 60)
            q = calado.quadro(i / 60)
        self.assertNotIn(q["pose"]["boca.v"], ("A", "E", "I", "O", "U"))   # sem volume, a boca não abre

    def test_cada_personalidade_tem_seus_proprios_gestos(self):
        escolhidos = {}
        for arq in A.ARQUETIPOS:
            an = Animador(arq, None, 11)
            vistos = set()
            for i in range(60 * 60 * 5):          # 5 minutos parado
                if i % 2:
                    continue
                q = an.quadro(i / 60)
                if q["gesto"]:
                    vistos.add(q["gesto"])
            escolhidos[arq] = vistos
            self.assertTrue(vistos, arq)
            permitidos = {g for g, _p in A.ARQUETIPOS[arq]["idle"]} | {A.ARQUETIPOS[arq]["chegada"]}
            self.assertTrue(vistos <= permitidos, (arq, vistos - permitidos))
        self.assertNotIn("punho", escolhidos["mordomo"])
        self.assertIn("reverencia", escolhidos["mordomo"])
        self.assertIn("cruzar_bracos", escolhidos["serio"])
        self.assertIn("escanear", escolhidos["jarvis"])
        self.assertTrue({"punho", "pular"} & escolhidos["coach"])
        self.assertEqual(len({frozenset(v) for v in escolhidos.values()}), len(escolhidos))   # nenhum é igual ao outro

    def test_jarvis_flutua_e_coach_quica(self):
        def altura(arq):
            an = Animador(arq, None, 5)
            ys = [an.quadro(i / 60)["pose"].get("raiz.y", 0.0) for i in range(300) if not an.overlay]
            return min(ys), max(ys)
        jmin, jmax = altura("jarvis")
        self.assertLess(jmax, -3)                            # levita: nunca encosta no chão
        self.assertEqual(Animador("jarvis").quadro(0.0)["extras"]["aura"], "#5AD7FF")
        self.assertEqual(Animador("serio").quadro(0.0)["extras"]["aura"], "")

    def test_trocar_de_estado_nao_da_tranco(self):
        an = Animador("serio", None, 4)     # parado: sem gesto sorteado nos primeiros segundos
        an.mudar("idle", 0.0)
        ant = an.quadro(0.0)["pose"]
        pior = 0.0
        for i in range(1, 120):
            t = i / 60
            if i == 60:
                an.mudar("pensando", t)
            pose = an.quadro(t)["pose"]
            for c in ("braco_d.r", "antebraco_d.r", "cabeca.r", "torso.r"):
                pior = max(pior, abs(pose.get(c, 0.0) - ant.get(c, 0.0)))
            ant = pose
        self.assertLess(pior, 12.0)     # graus de um quadro para o outro (a mistura leva ~0,28 s)

    def test_fps_economiza_quando_parado(self):
        an = Animador("serio", None, 1)
        an.quadro(0.0)
        self.assertLessEqual(an.fps(20.0), 30)
        an.mudar("falando", 21.0)
        self.assertEqual(an.fps(21.1), 60)
        an.mudar("descansando", 22.0)
        self.assertEqual(an.fps(30.0), 15)

    def test_dados_de_inercia_e_fala_existem(self):
        nos = set(_ids_do_rig())
        for tabela in (A.MOLAS, A.INERCIA, A.VIDA, *A.POSES_FALA.values()):
            for canal in tabela:
                self.assertIn(canal.partition(".")[0], nos, canal)
        self.assertTrue(set(A.INERCIA) <= set(A.MOLAS))
        for arq in A.ARQUETIPOS.values():
            self.assertTrue(arq["fala"])
            for nome, peso in arq["fala"]:
                self.assertIn(nome, A.POSES_FALA)
                self.assertGreater(peso, 0)

    def test_curva_continua_sem_passar_do_ponto(self):
        from app.personagem.animacao import avaliar
        trilha = {"k": [[0, 0], [0.3, 10], [0.6, 20], [0.8, 20], [1, 0]]}
        vals = [avaliar(trilha, i / 1000) for i in range(1001)]
        self.assertTrue(all(-1e-9 <= v <= 20 + 1e-9 for v in vals))                     # nunca passa de um ponto
        self.assertGreater(vals[310] - vals[290], 0.4)                                 # não para no ponto do meio da subida
        self.assertAlmostEqual(vals[700], 20, places=6)                               # segura onde os pontos são iguais
        self.assertEqual((avaliar(trilha, 0), avaliar(trilha, 1)), (0, 0))

    def test_molas_tiram_o_tranco_e_assentam(self):
        an = Animador("parceiro", None, 3)
        for i in range(60):
            an.quadro(i / 60)
        ant = an.quadro(1.0)["pose"]
        an.gesto("acenar", 1.0)
        pior = 0.0
        for i in range(1, 60 * 5):
            pose = an.quadro(1.0 + i / 60)["pose"]
            pior = max(pior, abs(pose["braco_d.r"] - ant["braco_d.r"]), abs(pose["antebraco_d.r"] - ant["antebraco_d.r"]))
            ant = pose
        self.assertLess(pior, 20.0)          # graus por quadro a 60 quadros/s: sobe o braço rápido (0,3 s), mas sem pulo
        self.assertIsNone(an.overlay)
        self.assertLess(abs(ant["braco_d.r"] - (-7)), 12)   # voltou para perto do repouso do "parado"

    def test_fala_mexe_os_bracos_e_cada_jeito_do_seu_modo(self):
        def faixa(arq):
            an = Animador(arq, None, 5)
            an.mudar("falando", 0.0)
            vistos = []
            for i in range(60 * 10):
                t = i / 60
                an.nivel(0.55 + 0.4 * math.sin(t * 9), t)
                q = an.quadro(t)["pose"]
                vistos.append((q["braco_e.r"], q["braco_d.r"], q["antebraco_d.r"]))
            return max(max(v) - min(v) for v in zip(*vistos)), an
        parceiro, an = faixa("parceiro")
        serio, _ = faixa("serio")
        self.assertGreater(parceiro, 30)     # gesticula de verdade
        self.assertGreater(parceiro, serio)  # o sério fala mais contido

    def test_capa_fica_para_tras_ao_andar(self):
        for dirc in (1, -1):
            an = Animador("parceiro", None, 2)
            an.andar(dirc, 1.0)
            vals = [an.quadro(i / 60)["pose"]["capa.r"] for i in range(120)]
            media = sum(vals[60:]) / 60
            self.assertGreater(media * dirc, 3, dirc)   # andando para a direita, a capa vai para a esquerda (e vice-versa)

    def test_mesma_semente_mesmo_resultado(self):
        def roda(seed):
            an = Animador("parceiro", None, seed)
            return [round(an.quadro(i / 60)["pose"]["braco_d.r"], 6) for i in range(0, 3000, 7)]
        self.assertEqual(roda(21), roda(21))
        self.assertNotEqual(roda(21), roda(22))


class PasseioDoPersonagem(unittest.TestCase):
    AREA = (0.0, 0.0, 1920.0, 1032.0)

    def _roda(self, p, segundos=900, ocupado_ate=0.0, fps=30):
        x, y = 1500.0, 900.0
        p.novo_lugar(x, y)
        minx = maxx = x
        miny = maxy = y
        andou = 0
        for i in range(int(segundos * fps)):
            t = i / fps
            x, y, d = p.atualizar(t, x, y, self.AREA, t < ocupado_ate, 150.0)
            minx, maxx, miny, maxy = min(minx, x), max(maxx, x), min(miny, y), max(maxy, y)
            andou += d != 0
            self.assertTrue(self.AREA[0] <= x <= self.AREA[2] - 150.0 + 1e-6, (i, x))
            self.assertTrue(self.AREA[1] <= y <= self.AREA[3] + 1e-6, (i, y))
        return (minx, maxx, miny, maxy), andou

    def test_fixo_nunca_sai_do_lugar(self):
        (minx, maxx, miny, maxy), andou = self._roda(Passeio("fixo"))
        self.assertEqual((minx, maxx, miny, maxy, andou), (1500.0, 1500.0, 900.0, 900.0, 0))

    def test_curto_anda_perto_e_so_na_horizontal(self):
        (minx, maxx, miny, maxy), andou = self._roda(Passeio("curto", 280, 70, (4, 8)))
        self.assertGreater(andou, 30)
        self.assertGreaterEqual(minx, 1500 - 280 - 1)
        self.assertEqual((miny, maxy), (900.0, 900.0))

    def test_tela_cobre_a_borda_de_baixo_toda(self):
        (minx, maxx, miny, maxy), _ = self._roda(Passeio("tela", 900, 130, (2, 5)), 1500)
        self.assertLess(minx, 500)
        self.assertGreater(maxx, 1200)
        self.assertEqual((miny, maxy), (900.0, 900.0))

    def test_livre_flutua_para_cima_mas_nunca_para_fora(self):
        (minx, maxx, miny, maxy), _ = self._roda(Passeio("livre", 380, 46, (3, 6)), 1500)
        self.assertLess(miny, 850)
        self.assertLessEqual(maxy, 900.0 + 1e-6)

    def test_para_quando_ocupado_e_volta_depois(self):
        p = Passeio("curto", 280, 70, (1, 2))
        x, y = 1000.0, 900.0
        p.novo_lugar(x, y)
        parou_em, direcoes = None, []
        for i in range(30 * 120):
            t = i / 30
            ocupado = 20 <= t < 60
            nx, ny, d = p.atualizar(t, x, y, self.AREA, ocupado, 150.0)
            if ocupado:
                self.assertEqual(d, 0)
                if parou_em is None:
                    parou_em = (nx, ny)
                self.assertEqual((nx, ny), parou_em)   # falando/pensando: fica onde está
            else:
                direcoes.append(d)
            x, y = nx, ny
        self.assertTrue(any(d for d in direcoes))

    def test_arrastar_muda_a_casa(self):
        p = Passeio("curto", 200, 70, (1, 2))
        p.novo_lugar(300.0, 900.0)
        x, y = 300.0, 900.0
        for i in range(30 * 20):
            x, y, _ = p.atualizar(i / 30, x, y, self.AREA, False, 150.0)
        x, y = 1600.0, 900.0
        p.novo_lugar(x, y)   # o usuário arrastou
        for i in range(30 * 20, 30 * 400):
            x, y, _ = p.atualizar(i / 30, x, y, self.AREA, False, 150.0)
            self.assertGreaterEqual(x, 1600 - 200 - 1e-6)

    def test_modo_do_config(self):
        arq = A.ARQUETIPOS["jarvis"]
        self.assertEqual(do_config("personalidade", arq).modo, "livre")
        self.assertEqual(do_config("", arq).modo, "livre")
        self.assertEqual(do_config("fixo", arq).modo, "fixo")
        self.assertEqual(do_config("lixo", arq).modo, "fixo")
        self.assertEqual({k: A.ARQUETIPOS[k]["passeio"]["modo"] for k in A.ARQUETIPOS},
                         {"parceiro": "curto", "mordomo": "curto", "jarvis": "livre", "coach": "tela", "serio": "fixo"})


class OpcoesEIntegracao(unittest.TestCase):
    def test_config_antigo_sem_avatar_segue_o_robo_e_o_padrao(self):
        self.assertEqual(avatar.modelo_escolhido({}), "robo")
        self.assertEqual(avatar.modelo_escolhido({"avatar": {"modelo": "xyz"}}), "robo")
        self.assertEqual(avatar.modelo_escolhido({"avatar": {"modelo": "Personagem"}}), "personagem")
        self.assertEqual(avatar.modulo_da_janela("robo"), "app.avatar_janela")
        self.assertEqual(avatar.modulo_da_janela("personagem"), "app.personagem.janela")
        o = opcoes_do_config({})
        self.assertEqual(o["perfil"], cena.normalizar(None))
        self.assertEqual((o["arquetipo"], o["passeio"]), ("parceiro", "personalidade"))

    def test_opcoes_do_config(self):
        cfg = {"personalidade": {"estilo": "Mordomo elegante"}, "avatar": {"jeito": "COACH", "passeio": "tela", "personagem": {"genero": "f", "traje": "batman", "escala": 1.3}}}
        o = opcoes_do_config(cfg)
        self.assertEqual((o["arquetipo"], o["passeio"], o["perfil"]["genero"], o["perfil"]["traje"], o["perfil"]["escala"]), ("coach", "tela", "f", "batman", 1.3))
        cfg["avatar"]["jeito"] = ""
        self.assertEqual(opcoes_do_config(cfg)["arquetipo"], "mordomo")     # sem jeito: segue a personalidade
        self.assertEqual(opcoes_do_config({"avatar": {"passeio": "voando"}})["passeio"], "personalidade")
        self.assertEqual(opcoes_do_config({"avatar": None, "personalidade": None})["arquetipo"], "parceiro")

    def test_tamanho_da_janela(self):
        d = dimensoes(1.0, True)
        self.assertEqual(d["altura_px"], ALTURA_PADRAO_PX)                 # 176 px: o triplo do bonequinho do jogo (~55 px)
        self.assertGreaterEqual(ALTURA_PADRAO_PX, 3 * 55)
        self.assertGreaterEqual(d["largura"], avatar.LARGURA_BALAO_MAX)   # cabe o balão de texto
        self.assertGreater(d["altura"], dimensoes(1.0, False)["altura"])
        self.assertLess(dimensoes(0.6, False)["largura"], dimensoes(1.6, False)["largura"])
        self.assertGreater(dimensoes(1.6, True)["altura"], dimensoes(0.6, True)["altura"])

    def test_gravar_no_config_mantem_comentarios_e_volta_igual(self):
        import io

        import yaml
        from ruamel.yaml import YAML
        y = YAML()
        c = y.load('aparencia:\n  cor: "Rosa"  # meu comentario\n')
        perfil = cena.normalizar({"genero": "f", "traje": "mulher_maravilha", "acessorios": ["oculos", "brincos"], "escala": 1.25, "cabelo": "chiquinha"})
        from app.personagem.opcoes import escrever_config
        escrever_config(c, "personagem", "coach", "tela", perfil)
        buf = io.StringIO()
        y.dump(c, buf)
        self.assertIn("# meu comentario", buf.getvalue())
        cfg = yaml.safe_load(buf.getvalue())
        o = opcoes_do_config(cfg)
        self.assertEqual(o["perfil"], perfil)
        self.assertEqual((o["arquetipo"], o["passeio"], avatar.modelo_escolhido(cfg)), ("coach", "tela", "personagem"))
        escrever_config(c, "xyz", "abc", "voando", perfil)      # valor inválido cai no padrão, sem quebrar o arquivo
        buf = io.StringIO()
        y.dump(c, buf)
        cfg = yaml.safe_load(buf.getvalue())
        self.assertEqual((avatar.modelo_escolhido(cfg), cfg["avatar"]["jeito"], cfg["avatar"]["passeio"]), ("robo", "", "personalidade"))

    def test_painel_chama_a_secao_do_personagem(self):
        texto = (RAIZ / "app" / "painel.py").read_text(encoding="utf-8")
        self.assertIn("painel_personagem.montar(self, pagina)", texto)
        self.assertIn("painel_personagem.salvar(self, c)", texto)
        self.assertTrue((RAIZ / "app" / "painel_personagem.py").exists())
        import importlib
        importlib.import_module("app.painel_personagem")            # importar não abre nada (o Tk só entra dentro de montar)

    def test_previa_do_painel_nao_mexe_no_tk_fora_da_linha_principal(self):
        import ast
        arvore = ast.parse((RAIZ / "app" / "painel_personagem.py").read_text(encoding="utf-8"))
        trabalho = next(n for n in ast.walk(arvore) if isinstance(n, ast.FunctionDef) and n.name == "trabalho")
        chamadas = {n.func.attr for n in ast.walk(trabalho) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        self.assertFalse(chamadas & {"after", "configure", "set", "pack", "grid", "update"}, chamadas)   # só a fila
        self.assertIn("put", chamadas)

    def test_lugar_do_personagem_separado_do_robo(self):
        import os
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as pasta, patch.dict(os.environ, {"MESTRE_SEGREDOS": pasta}):
            avatar.salvar_posicao((1998, 38))                       # robô arrastado lá para cima
            self.assertIsNone(avatar.ler_posicao("personagem"))     # o personagem não herda: nasce no lugar padrão
            avatar.salvar_posicao((500, 900), "personagem")
            self.assertEqual((avatar.ler_posicao(), avatar.ler_posicao("personagem")), ((1998, 38), (500, 900)))
            avatar.salvar_posicao(None, "personagem")               # "Voltar ao lugar padrão" do personagem não apaga o do robô
            self.assertEqual((avatar.ler_posicao(), avatar.ler_posicao("personagem")), ((1998, 38), None))
        texto = (RAIZ / "app" / "personagem" / "janela.py").read_text(encoding="utf-8")
        self.assertNotRegex(texto, r"avatar\.(ler|salvar)_posicao\((None|\(self\.x\(\), self\.y\(\)\))?\)")   # sempre com POSICAO

    def test_se_o_personagem_falha_volta_o_robo_e_depois_a_bolinha(self):
        from types import SimpleNamespace
        from unittest.mock import patch

        from app import main as m
        ex = SimpleNamespace(nome="Assessor", palavra="assessor", rodando=True)
        chamadas = []

        def iniciar(nome, palavra, tipo, modelo="robo"):
            chamadas.append(modelo)
            return object()
        with patch.object(avatar, "iniciar", iniciar), patch.object(avatar, "acompanhar", side_effect=["falhou", "desligou"]):
            self.assertTrue(m._mostrar_avatar({"avatar": {"modelo": "personagem"}}, ex))
        self.assertEqual(chamadas, ["personagem", "robo"])          # o personagem caiu: o robozinho assume
        chamadas.clear()
        with patch.object(avatar, "iniciar", iniciar), patch.object(avatar, "acompanhar", side_effect=["falhou"]):
            self.assertFalse(m._mostrar_avatar({}, ex))              # robô que falha = bolinha, como sempre
        self.assertEqual(chamadas, ["robo"])
        chamadas.clear()
        with patch.object(avatar, "iniciar", iniciar), patch.object(avatar, "acompanhar", side_effect=["falhou", "falhou"]):
            self.assertFalse(m._mostrar_avatar({"avatar": {"modelo": "personagem"}}, ex))
        self.assertEqual(chamadas, ["personagem", "robo"])

    def test_arquivos_com_qt_compilam_sem_importar_qt(self):
        for nome in ("render_qt.py", "janela.py", "previa.py"):
            origem = (RAIZ / "app" / "personagem" / nome).read_text(encoding="utf-8")
            compile(origem, nome, "exec")                            # erro de sintaxe aparece aqui (o Qt é bloqueado nos testes)
        js = (RAIZ / "design" / "avatar-2026-09" / "personagem.js").read_text(encoding="utf-8")
        self.assertIn("Personagem = {", js)

    def test_texto_da_fala_so_vai_com_o_avatar_ligado(self):
        avatar.ATIVO = False
        avatar._sock = None
        avatar.enviar_texto("oi")
        self.assertIsNone(avatar._sock)      # avatar desligado: nada de socket

    def test_config_exemplo_traz_o_personagem(self):
        import yaml
        cfg = yaml.safe_load((RAIZ / "config.exemplo.yaml").read_text(encoding="utf-8"))
        av = cfg["avatar"]
        self.assertEqual(av["modelo"], "robo")                              # o robô continua o padrão até o dono aprovar
        self.assertEqual(cena.normalizar(av["personagem"]), cena.normalizar(None))
        self.assertEqual(opcoes_do_config(cfg)["passeio"], "personalidade")

    def test_pagina_de_teste_esta_em_dia(self):
        from ferramentas import gerar_demo_personagem as g
        frag, completo = g.montar()
        pasta = RAIZ / "design" / "avatar-2026-09"
        self.assertEqual((pasta / "artefato.html").read_text(encoding="utf-8"), frag, "rode: venv\\Scripts\\python -m ferramentas.gerar_demo_personagem")
        self.assertEqual((pasta / "index.html").read_text(encoding="utf-8"), completo)
        for marca in ("__DADOS_JSON__", "__PERSONAGEM_JS__", "__DEMO_JS__"):
            self.assertNotIn(marca, frag)
        self.assertIn("<title>Personagem do Assessor</title>", frag)
        self.assertNotIn("http://", frag.replace("http://www.w3.org", ""))    # nada de recurso de fora fora da lista do Artefato

    def test_nada_do_personagem_sem_janela_importa_qt(self):
        antes = {m for m in sys.modules if m.startswith("PySide6")}
        import importlib
        for nome in ("arte", "catalogo", "cena", "animacao", "passeio", "opcoes"):
            importlib.import_module("app.personagem." + nome)
        self.assertEqual({m for m in sys.modules if m.startswith("PySide6")}, antes)


if __name__ == "__main__":
    unittest.main()
