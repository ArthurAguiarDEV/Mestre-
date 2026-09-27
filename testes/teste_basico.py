"""Teste automatico do basico do Mestre. Rode ANTES de entregar qualquer mudanca:

    venv\\Scripts\\python -m testes.teste_basico

Trabalha numa COPIA do projeto (pasta temporaria): seu config.yaml nao e tocado
e nada abre de verdade (MESTRE_SIMULAR=1). No fim mostra OK / FALHOU para cada item.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import zipfile
from pathlib import Path

PROJETO = Path(__file__).resolve().parent.parent
IGNORAR = shutil.ignore_patterns("venv", "modelos", "logs", "*.zip", "__pycache__", ".git", "mestre.pid",
                                 "notas", "respostas")
resultados: list[tuple[bool, str, str]] = []


def conferir(ok: bool, nome: str, detalhe: str = "") -> None:
    resultados.append((bool(ok), nome, detalhe))
    print(("  OK      " if ok else "  FALHOU  ") + nome + (f"  ({detalhe})" if detalhe and not ok else ""), flush=True)


def rodar(pasta: Path, codigo: str, espera: int = 300) -> tuple[int, str]:
    """Roda um trecho de Python dentro da copia do projeto."""
    # (em arquivo: pelo "-c" o trecho grande passa do limite de linha de comando do Windows)
    script = pasta / "_trecho_teste.py"
    script.write_text(textwrap.dedent(codigo), encoding="utf-8")
    r = subprocess.run([sys.executable, str(script)], cwd=str(pasta), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=espera,
                       env={**os.environ, "MESTRE_SIMULAR": "1", "PYTHONIOENCODING": "utf-8"})
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def comando(pasta: Path, frase: str) -> str:
    r = subprocess.run([sys.executable, "-m", "app.main", "--mudo", "--comando", frase], cwd=str(pasta),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
                       env={**os.environ, "MESTRE_SIMULAR": "1", "PYTHONIOENCODING": "utf-8"})
    return (r.stdout or "") + (r.stderr or "")


def copiar_projeto(destino: Path) -> Path:
    pasta = destino / "mestre"
    shutil.copytree(PROJETO, pasta, ignore=IGNORAR)
    (pasta / "logs").mkdir(exist_ok=True)
    # Os testes falam "mestre ...": a cópia usa essa palavra, seja qual for a escolhida pelo usuário
    cfg = pasta / "config.yaml"
    if (pasta / "config.exemplo.yaml").exists():  # testes nao dependem do config do usuario
        shutil.copyfile(pasta / "config.exemplo.yaml", cfg)
    if cfg.exists():
        texto = cfg.read_text(encoding="utf-8")
        cfg.write_text(re.sub(r'(?m)^(\s*palavra_ativacao:\s*).*$', r'\1"mestre"', texto), encoding="utf-8")
    return pasta


# ---------------------------------------------------------------------------
PREPARAR = """
from app import configuracao
c = configuracao.carregar()
canais = {f"Canal de teste {i}": f"https://www.youtube.com/channel/UC{i:020d}" for i in range(2000)}
canais["Spotify"] = "@spotify"           # canal com o MESMO nome de um programa
canais["Manual do Mundo"] = "@manualdomundo"
configuracao.trocar_mapa(c, "canais_youtube", canais)
configuracao.salvar(c)
print("preparado")
"""

PAINEL = r"""
import sys, time, traceback, tkinter as tk
erros = []
tk.Tk.report_callback_exception = lambda self, e, v, tb: erros.append("".join(traceback.format_exception(e, v, tb)))
inicio = time.time()
import app.painel as p
pn = p.Painel()
pn.update()
print("TEMPO_ABRIR", round(time.time() - inicio, 1))

# busca de canais
pn.mostrar_pagina("YouTube"); pn.update()
pn.tab_canais.var_busca.set("manual do"); pn.tab_canais._buscar(); pn.update()
print("BUSCA", len(pn.tab_canais.visiveis), pn.tab_canais.visiveis[0][1].get() if pn.tab_canais.visiveis else "")
pn.tab_canais.var_busca.set(""); pn.tab_canais._buscar()
time.sleep(0.4); pn.update()          # (deixa a busca "ao digitar" terminar)
t = pn.tab_canais
t.ir_para(10); pn.update()
pag10 = t.visiveis[0][1].get()
t.ir_para(999); pn.update()
ultima = t.nav_topo[2].cget("text")
t0 = time.time(); t.ir_para(0); pn.update(); tempo_pagina = time.time() - t0
print("PAGINAS", pag10 != t.visiveis[0][1].get(), ultima, len(t.visiveis))
print("TEMPO_PAGINA", round(tempo_pagina, 3))
t.adicionar(); pn.update()
pn.tab_canais.visiveis[0][1].insert(0, "Canal novo do teste"); pn.tab_canais.visiveis[0][2].insert(0, "@canalnovo")
# apagar um canal pela busca
pn.tab_canais.var_busca.set("Canal de teste 1999"); pn.tab_canais._buscar(); pn.update()
pn.tab_canais._remover(pn.tab_canais.visiveis[0][3]); pn.update()

# programa e site novos
pn.mostrar_pagina("Programas e sites"); pn.update()
pn.tab_prog.adicionar(); pn.update()
ek, ev = pn.tab_prog.visiveis[0][1:3]
ek.insert(0, "spotify"); ev.insert(0, '"' + sys.executable + '"')   # com aspas, como o "Copiar como caminho"
pn.tab_sites.adicionar(); pn.update()
pn.tab_sites.visiveis[0][1].insert(0, "site do teste"); pn.tab_sites.visiveis[0][2].insert(0, "https://exemplo.com")

# rotina nova com 3 acoes
pn.mostrar_pagina("Rotinas"); pn.update()
pn._nova_rotina(); pn.update()
pn.ent_rot_nome.delete(0, "end"); pn.ent_rot_nome.insert(0, "Rotina do teste")
pn.ent_rot_frases.delete(0, "end"); pn.ent_rot_frases.insert(0, "rotina do teste, testa a rotina")
pn._adicionar_acao(); pn.update()
var, ent = pn.linhas_acoes[-1]; var.set(p.ACOES_ROTINA["abrir_programa"]); ent.insert(0, "spotify")
pn._adicionar_acao(); pn.update()
var, ent = pn.linhas_acoes[-1]; var.set(p.ACOES_ROTINA["abrir_site"]); ent.insert(0, "site do teste")
pn._mover_acao(2, -1); pn.update()          # mexe na ordem e volta
pn._mover_acao(1, 1); pn.update()
print("SALVOU", pn.salvar())
pn.update()
print("ERROS_TELA", len(erros))
for e in erros: print(e)
pn._fechar()
"""

CONFERIR_CONFIG = """
import yaml
c = yaml.safe_load(open("config.yaml", encoding="utf-8"))
print("PROGRAMA", c["programas"].get("spotify"))
print("SITE", c["sites"].get("site do teste"))
print("CANAIS", len(c["canais_youtube"]), "Canal novo do teste" in c["canais_youtube"], "Canal de teste 1999" in c["canais_youtube"])
r = [x for x in c["rotinas"] if x["nome"] == "Rotina do teste"]
print("ROTINA", r[0]["frases"] if r else None, [list(a)[0] for a in r[0]["acoes"]] if r else None)
texto = open("config.yaml", encoding="utf-8").read()
print("ORDEM_OK", texto.index("spotify:") < texto.index("# 8) SITES") if "# 8) SITES" in texto else True)
"""


FLUXOS = r"""
import json, os, time, logging
logging.basicConfig(level=logging.WARNING)
from app.config import carregar_config
from app.comandos import Executor, ARQUIVO_MELHORIAS, ARQUIVO_REVISAO
from app.voz import Voz
from app import estado, sistema
from app.vocabulario import Vocabulario
from app.texto import normalizar
ditos, colados, abertos = [], [], []
class VozTeste(Voz):
    def falar(self, texto):
        ditos.append(texto); estado.atualizar(ultima_resposta=texto)
class IALenta:
    ligado, atraso = True, 2.5
    def interpretar(self, frase, comandos):
        time.sleep(self.atraso); return {"tipo": "resposta", "texto": f"Resposta pensada sobre {frase}"}
    def perguntar(self, frase, perfil="geral"):
        time.sleep(self.atraso); return f"Conversa sobre {frase}"
    def propor_opcoes(self, pedido):
        time.sleep(0.2)
        return [{"titulo": f"Caminho {n}", "resumo": f"Resumo {n}", "passos": [f"Passo {n}.1", f"Passo {n}.2"]}
                for n in ("simples", "medio", "ousado")]
    def esquecer(self): pass
sistema.colar_e_enviar = lambda texto, enviar=True: colados.append(texto)
sistema.enviar_para_app_claude = lambda texto, enviar=True, altura_caixa=90, **kw: colados.append(texto) or True
sistema.clicar_e_colar_na_janela_ativa = lambda texto, enviar=True, altura_caixa=90: colados.append(texto)
sistema.abrir_terminal_com = lambda linha, pasta, titulo: abertos.append(f"terminal:{pasta}:{linha}")
sistema.abrir_site = lambda url: abertos.append(url)
cfg = carregar_config()
cfg.setdefault("cerebro", {}).update(segundo_plano_seg=1, aviso_ao_terminar="voz")
import tempfile, pathlib
PASTA_PROJ = pathlib.Path(tempfile.mkdtemp())
cfg["projetos"] = {"pasta": str(PASTA_PROJ), "abrir_pesquisas": True}
cfg["spotify"] = {"playlists": {"Foco total": "https://open.spotify.com/playlist/37i9dQZF1DX8NTLI2TtZa6?si=abc"},
                  "apertar_play": False}
from app import memoria
cfg.setdefault("projeto_mestre", {}).update(segundos_para_carregar=0)
cfg.setdefault("agente_ipm", {}).update(segundos_para_carregar=0, modo="site")
ex = Executor(cfg, VozTeste(cfg, mudo=True), IALenta(), Vocabulario())
def diga(frase, completa=None):
    ditos.clear(); t0 = time.time(); ex.executar(frase, completa or frase); return time.time() - t0, list(ditos)
def ok(c, nome): print(("OK " if c else "FALHOU ") + nome, flush=True)

tempo, _ = diga("me explica a teoria da relatividade")
ok(tempo < 2 and estado.ler()["pensamento"] == "pensando", "IA demorou: vai para segundo plano (bolinha roxa)")
tempo, falas = diga("que horas sao")
ok(tempo < 1 and bool(falas), "Comando simples funciona enquanto a IA pensa")
time.sleep(2.8)
ok(estado.ler()["pensamento"] == "pronto", "Terminou: bolinha verde")
ok(not any("Resposta pensada" in f for f in ditos), "Não fala a resposta sem você pedir")
diga("", "Mestre")          # voce so chamou "Mestre" (o caso que perdia a resposta)
_, falas = diga("falar", "Mestre, pode falar")   # o vocabulario tira o "pode": chega "falar"
ok(any("Resposta pensada sobre me explica" in f for f in falas), "“Mestre” e depois “pode falar” entrega a resposta")
_, falas = diga("repete a resposta", "Repete a resposta")
ok(any("Resposta pensada sobre me explica" in f for f in falas), "“repete a resposta” (histórico)")
_, falas = diga("o que voce respondeu sobre relatividade", "O que você respondeu sobre relatividade?")
ok(any("Resposta pensada sobre me explica" in f for f in falas), "“o que você respondeu sobre …” acha no histórico")
diga("me lembra que eu trabalho na ipm de manha", "Lembra que eu trabalho na IPM de manhã")
ok(any("IPM de manhã" in f for f in memoria.fatos()) and "IPM de manhã" in memoria.texto_para_ia(),
   "“lembra que …” guarda na memória (e a IA usa)")
abertos.clear()
diga("toca a playlist foco total no spotify", "Toca a playlist foco total no Spotify")
ok(abertos and abertos[-1] == "spotify:playlist:37i9dQZF1DX8NTLI2TtZa6", "Spotify: playlist cadastrada abre no app")
diga("toca legiao urbana no spotify", "Toca Legião Urbana no Spotify")
ok(abertos and abertos[-1].startswith("spotify:search:Legi"), "Spotify: nome desconhecido abre a busca")

diga("quero comecar um novo projeto", "Quero começar um novo projeto")
diga("codigo", "Código")
diga("app de receitas", "App de Receitas")
diga("organizar minhas receitas", "Organizar minhas receitas da família.")
_, falas = diga("nada", "Nada.")
time.sleep(1.5)
pasta = PASTA_PROJ / "App de Receitas"
ok((pasta / "PLANO.md").exists() and (pasta / "codigo").is_dir(), "Novo projeto: pasta e PLANO.md criados")
ok(any("Pensei em 3 caminhos" in f and "quatro" in f.lower() for f in ditos), "IA traz 3 caminhos + a 4ª (mandar pro Claude)")
abertos.clear()
diga("dois", "Dois")
plano = (pasta / "PLANO.md").read_text(encoding="utf-8")
ok("Caminho medio" in plano.split("## Caminho escolhido")[1] and "- [ ] Passo medio.1" in plano, "Escolher o caminho grava os passos")
_, falas = diga("o que falta no projeto app de receitas", "O que falta no projeto App de Receitas?")
ok(any("Passo medio.1" in f for f in falas), "“o que falta no projeto …”")
ex._proj = {"pasta": pasta, "opcoes": ex._proj.get("opcoes")}
ex.perguntar("?", ex._proj_escolha)
diga("nenhum manda pro claude", "Nenhum, manda pro Claude")
abertos.clear()
diga("chat novo", "Chat novo")
ok(any(a.startswith("https://claude.ai/new?q=") for a in abertos), "4ª opção → chat novo no Claude com o plano")

diga("me conta uma historia longa"); _, falas = diga("cancela"); time.sleep(3)
ok(not any("historia" in f for f in ditos) and estado.ler()["pensamento"] == "", "“cancela” descarta o pensamento")

ARQUIVO_MELHORIAS.unlink(missing_ok=True)
diga("quero ditar melhorias")
diga("quero que o painel tenha modo claro", "Quero que o painel tenha modo claro.")
diga("e que ele manda um aviso", "E que ele manda um aviso.")
ok(ex._ditado_ativo, "“manda” no meio do ditado não encerra")
_, falas = diga("finalizei", "Finalizei.")
ok(json.loads(ARQUIVO_REVISAO.read_text(encoding="utf-8"))["estado"] == "aberto", "Janela de revisão no fim do ditado")
diga("manda")
m = ARQUIVO_MELHORIAS.read_text(encoding="utf-8") if ARQUIVO_MELHORIAS.exists() else ""
ok("Quero que o painel tenha modo claro." in m, "Ditado salvo COM acentos no MELHORIAS.md")
ok(bool(colados) and "modo claro" in colados[-1] and colados[-1].startswith("[Pedido ditado"),
   "Ditado de melhorias vai para o app Claude (com o aviso de corrigir e refinar)")
for resposta, esperado in [("manda pro claude code", "projeto"), ("manda pro agente ipm", "ipm"), ("pro projeto", "projeto")]:
    ex._frase_original = resposta
    ok(ex._qual_destino(resposta) == esperado, f"“{resposta}” vai para {esperado}")

# --- musica, volume, janelas e YouTube -------------------------------------------------
feitos = []
sistema.midia = lambda acao: feitos.append(("midia", acao))
sistema.volume = lambda acao, vezes=5: feitos.append(("volume", acao))
sistema.volume_do_pc = lambda n: feitos.append(("volume_pc", n))
sistema.volume_do_programa = lambda proc, acao, q=0.1: feitos.append(("volume_app", proc, acao, round(q, 2))) or ""
sistema.atalho = lambda *teclas: feitos.append(("atalho", "+".join(teclas)))
sistema.janela_ativa = lambda acao: feitos.append(("janela", acao))
casos = [("Pausa o Spotify", ("midia", "tocar_pausar")), ("Pausa a música do Spotify", ("midia", "tocar_pausar")),
         ("Despausa", ("midia", "tocar_pausar")), ("Volta a tocar", ("midia", "tocar_pausar")),
         ("Próxima música", ("midia", "proxima")), ("Pula essa", ("midia", "proxima")),
         ("Música anterior", ("midia", "anterior")),
         ("Diminui o volume", ("volume", "diminuir")), ("Aumenta o volume", ("volume", "aumentar")),
         ("Volume no 30", ("volume_pc", 30)),
         ("Aumenta o volume do Spotify", ("volume_app", "Spotify.exe", "aumentar", 0.1)),
         ("Spotify no volume 40", ("volume_app", "Spotify.exe", "definir", 0.4)),
         ("Fecha essa aba", ("atalho", "ctrl+w")), ("Nova aba", ("atalho", "ctrl+t")),
         ("Minimiza essa janela", ("janela", "minimizar")), ("Rola pra baixo", ("atalho", "pgdn")),
         ("Volta a página", ("atalho", "alt+esquerda")), ("Troca de janela", ("atalho", "alt+tab"))]
for falado, esperado in casos:
    feitos.clear()
    diga(normalizar(falado), falado)
    ok(feitos[:1] == [esperado], f"“{falado}” → {esperado[0]} {esperado[1]}")

class YTFalso:
    def __init__(self): self.feito = []
    def na_pagina_do_youtube(self): return True
    def resultados(self): return [{"titulo": f"Video {n} de teste", "link": f"https://youtube.com/watch?v={n}"} for n in range(1, 6)]
    def __getattr__(self, nome): return lambda *a: self.feito.append((nome,) + a) or "ok"
yt = YTFalso(); ex._yt = lambda: yt
for falado, esperado in [("Tela cheia", "tela_cheia"), ("Dá um like", "like"), ("Se inscreve no canal", "inscrever"),
                         ("Fecha o chat", "chat"), ("Tela cheia com chat", "tela_cheia_com_chat"),
                         ("Avança 30 segundos", "pular"), ("Abre o terceiro vídeo", "abrir")]:
    yt.feito.clear(); diga(normalizar(falado), falado)
    ok(bool(yt.feito) and yt.feito[0][0] == esperado, f"YouTube: “{falado}”")
ok(yt.feito[0] == ("abrir", "https://youtube.com/watch?v=3"), "YouTube: “abre o terceiro vídeo” abre o 3º resultado")
# --- monitores ------------------------------------------------------------------------
movidos = []
sistema.mover_janela_para_monitor = lambda hwnd, n, maximizar=True: movidos.append(n) or True
ex.cfg["janelas"] = {"nomes_monitores": {"2": "da tv"}, "sempre_no_principal": True}
diga("abre o youtube no monitor 2", "Abre o YouTube no monitor 2")
ok(sistema.MONITOR_ALVO == 2 and yt.feito and yt.feito[-1][0] == "abrir", "“abre o YouTube no monitor 2”")
diga("abre o youtube no monitor da tv", "Abre o YouTube no monitor da TV")
ok(sistema.MONITOR_ALVO == 2, "Monitor pelo nome (“da TV”)")
diga("joga essa janela pro monitor tres", "Joga essa janela pro monitor três")
ok(movidos[-1:] == [3], "“joga essa janela pro monitor 3”")
diga("que horas sao", "Que horas são")
ok(sistema.MONITOR_ALVO is None, "Sem pedir monitor: volta ao padrão (principal)")

# --- volume so do Spotify -----------------------------------------------------------------
for falado, esperado in [("Muta o Spotify", ("volume_app", "Spotify.exe", "mudo", 0)),
                         ("Tira o som do Spotify", ("volume_app", "Spotify.exe", "mudo", 0)),
                         ("Volta o som do Spotify", ("volume_app", "Spotify.exe", "som", 0)),
                         ("Diminui o volume do Spotfy", ("volume_app", "Spotify.exe", "diminuir", 0.1))]:
    feitos.clear(); diga(normalizar(falado), falado)
    ok(feitos[:1] == [esperado] and not any(f[0] == "volume" for f in feitos), f"“{falado}” mexe SÓ no Spotify")

# --- YouTube no navegador normal (so teclas) ---------------------------------------------------
from app.navegador import YouTubeNoNavegadorNormal
normal = YouTubeNoNavegadorNormal(None); normal.na_pagina_do_youtube = lambda: True
ex._yt = lambda: normal
_, falas = diga("da um like", "Dá um like")
ok(any("teclas" in f for f in falas), "Brave normal: like explica que precisa da janela controlada")
teclas = []
sistema.tecla_letra = lambda l: teclas.append(l)
diga("tela cheia", "Tela cheia")
ok(teclas == ["f"], "Brave normal: “tela cheia” aperta F")

# --- Spotify no maximo (e ele fala o nivel) ------------------------------------------------
def vol_prog(proc, acao, q=0.1):
    feitos.append(("volume_app", proc, acao, round(q, 2)))
    sistema.ULTIMO_NIVEL = q if acao == "definir" else 0.6
    return ""
sistema.volume_do_programa = vol_prog
feitos.clear(); _, falas = diga("abre no volume maximo do spotify", "Coloque no volume máximo do Spotify")
ok(feitos[:1] == [("volume_app", "Spotify.exe", "definir", 1.0)] and any("100 por cento" in f for f in falas),
   "“volume máximo do Spotify” → Spotify em 100% (e ele confirma falando)")

# --- monitores pela marca e pelos Hz -----------------------------------------------------
sistema.monitores = lambda: [{"numero": 1, "marca": "LG", "hz": 240}, {"numero": 2, "marca": "AOC", "hz": 240},
                             {"numero": 3, "marca": "", "hz": 144}]
for falado, n in [("no monitor AOC", 2), ("no monitor LG", 1), ("no monitor de 144", 3), ("no monitor terciário", 3),
                  ("no monitor primário", 1), ("no monitor secundário", 2)]:
    diga(normalizar("abre o youtube " + falado), "Abre o YouTube " + falado)
    ok(sistema.MONITOR_ALVO == n, f"“abre o YouTube {falado}” → monitor {n}")

# --- ponte da extensao do Brave (sem navegador: um cliente falso faz o papel da extensao) ---
import json as _json, threading as _th, urllib.request as _u
from app.ponte import Ponte
ponte = Ponte(porta=47699); ponte.iniciar()
def extensao_falsa():
    r = _u.urlopen("http://127.0.0.1:47699/proximo", timeout=25); pedido = _json.loads(r.read())
    corpo = _json.dumps({"id": pedido["id"], "resultado": "ok:" + pedido["acao"]}).encode()
    _u.urlopen(_u.Request("http://127.0.0.1:47699/resposta", data=corpo, headers={"Content-Type": "application/json"}))
_th.Thread(target=extensao_falsa, daemon=True).start()
time.sleep(0.3)
ok(ponte.pedir("like", espera=5) == "ok:like" and ponte.conectada(), "Ponte da extensão do Brave: pedido e resposta")

# --- nomes: ele = Assessor, voce = Mestre (uma troca nao desfaz a outra) -------------------
v = Voz(cfg, mudo=True)
v.trocas = [(r"\bchefe\b", "Mestre"), (r"\{palavra\}", "Assessor"), (r"\{apelido\}", "Mestre"), (r"\{nome\}", "Assessor")]
ok(v.trocar("Pronto chefe. Fala: {palavra}, reinicia.") == "Pronto Mestre. Fala: Assessor, reinicia.",
   "Nomes: chama você de Mestre e ensina a chamar o Assessor (sem virar “Assessor” no seu lugar)")

# --- pensando em silencio ------------------------------------------------------------------
ex.cfg["cerebro"]["aviso_som"] = "nenhum"; ditos.clear(); ex._aviso_curto("fundo"); ex._aviso_curto("pronto")
ok(not ditos, "Pensando em silêncio: só o indicador, sem frases")

# --- abas e janelas pelo nome (extensao falsa do Brave) ------------------------------------
class ExtFalsa:
    def __init__(self):
        self.pedidos = []
        self.abas = [{"id": 1, "janela": 10, "titulo": "Netflix", "url": "https://www.netflix.com/browse", "ativa": False,
                      "abas_na_janela": 2, "ultimo_acesso": 5},
                     {"id": 2, "janela": 10, "titulo": "YouTube", "url": "https://www.youtube.com/", "ativa": True,
                      "abas_na_janela": 2, "ultimo_acesso": 9},
                     {"id": 3, "janela": 11, "titulo": "Caixa de entrada - Gmail", "url": "https://mail.google.com/mail",
                      "ativa": True, "abas_na_janela": 1, "ultimo_acesso": 7}]
    def conectada(self): return True
    def pedir(self, acao, arg=None, espera=8):
        self.pedidos.append((acao, arg))
        if acao == "abas": return self.abas
        return {"titulo": next((a["titulo"] for a in self.abas if a["id"] == arg), "")}
ext = ExtFalsa(); ex.ponte = ext
janelas_brave = {"Netflix": 101, "YouTube": 102, "Caixa de entrada - Gmail": 103}
sistema.janela_pelo_titulo = lambda titulo, exe="brave.exe", espera=2.5: janelas_brave.get(titulo)
sistema.monitor_da_janela = lambda h: 1
sistema.janelas_abertas = lambda: [{"hwnd": 55, "titulo": "Spotify Premium", "exe": "spotify.exe", "monitor": 1}]
def mover(falado):
    ext.pedidos.clear(); movidos.clear(); abertos.clear(); diga(normalizar(falado), falado)
    return [p for p in ext.pedidos if p[0] != "abas"], list(movidos)
ped, mov = mover("Joga a Netflix pro monitor 3")
ok(ped == [("focar", 1)] and mov == [3], f"“Joga a Netflix pro monitor 3”: leva a janela dela, sem abrir outra ({ped} {mov})")
ped, mov = mover("Separa a Netflix pro monitor 2 e deixa o YouTube no principal")
ok(("separar", 1) in ped and ("focar", 2) in ped and mov == [2],
   f"“Separa a Netflix pro monitor 2 e deixa o YouTube no principal” ({ped} {mov})")
ped, mov = mover("Quero que você jogue a Netflix desse navegador para o monitor 2 e o YouTube deixe no meu principal")
ok(("separar", 1) in ped and mov == [2], f"Mesma ordem falada do jeito solto ({ped} {mov})")
ped, mov = mover("Abre a Netflix no monitor 2")
ok(("separar", 1) in ped and mov == [2] and not abertos, f"“Abre a Netflix no monitor 2” com ela aberta: usa a aba que já existe ({ped} {mov} {abertos})")
ped, mov = mover("Abre o Gmail")
ok(ped == [("focar", 3)] and not abertos, "“Abre o Gmail” com ele aberto: traz a aba para a frente")
ped, mov = mover("Manda o Spotify pro monitor AOC")
ok(mov == [2], f"“Manda o Spotify pro monitor AOC”: janela de programa pelo nome ({mov})")
ped, mov = mover("Coloca o Spotify no máximo")
ok(not mov, "“Coloca o Spotify no máximo” continua sendo volume (não é monitor)")
del ex.ponte

# --- YouTube: o video certo da tela pelo canal ou pelo titulo -------------------------------
tela = [{"titulo": "Receita de pão caseiro", "canal": "Ana Maria", "link": "L1"},
        {"titulo": "Como seria o GTA 6 feito pela Ubisoft", "canal": "David Jones", "link": "L2"},
        {"titulo": "GTA 5 ao vivo", "canal": "Gameplay J", "link": "L3"}]
achar = lambda f: (ex._video_na_tela(normalizar(f), tela) or {}).get("link")
ok(achar("david jones que está na tela do youtube") == "L2" and achar("GTA 6") == "L2" and achar("gameplay j") == "L3"
   and achar("receita de pão") == "L1" and achar("xuxa") is None, "YouTube: acha o vídeo da tela pelo canal ou pelo título")
class YTTela(YTFalso):
    def resultados(self): return tela
yt = YTTela(); ex._yt = lambda: yt
diga(normalizar("Quero ver o vídeo do David Jones que está na tela do YouTube"), "Quero ver o vídeo do David Jones que está na tela do YouTube")
ok(("abrir", "L2") in yt.feito, "“Quero ver o vídeo do David Jones” abre o vídeo dele")
for falado, esperado in [("Pausa o vídeo", ("pausar", True)), ("Continua o vídeo", ("pausar", False)),
                         ("Próximo vídeo", ("proximo",)), ("Vai pras inscrições", ("abrir", "https://www.youtube.com/feed/subscriptions")),
                         ("Abre o assistir mais tarde", ("abrir", "https://www.youtube.com/playlist?list=WL"))]:
    yt.feito.clear(); diga(normalizar(falado), falado)
    ok(yt.feito[:1] == [esperado], f"YouTube: “{falado}” ({yt.feito[:1]})")

# --- exportar o historico para o Claude ------------------------------------------------------
memoria.ouvido("a mestri abre o youtube", chamou=False, conversa=False, audio_seg=1.2, transcricao_seg=0.8)
from app import exportar
arq = exportar.gerar(ex.cfg, "tudo")
txt = arq.read_text(encoding="utf-8")
ok(arq.exists() and "## Resumo" in txt and "_cmd_mover" in txt and "Joga a Netflix pro monitor 3" in txt
   and "a mestri abre o youtube" in txt.split("## Frases ignoradas")[1].split("## Feedbacks")[0],
   "Exportar o histórico: arquivo com resumo, comandos e frases mal ouvidas")
_, falas = diga("exporta o historico de hoje", "Exporta o histórico de hoje")
ok(any("exportado" in f for f in falas), "“Exporta o histórico de hoje” por voz")

# --- v12: descanso ------------------------------------------------------------------------------
abertos.clear()
diga("pode descansar", "Pode descansar")
_, falas_d = diga("abre o youtube", "Abre o YouTube")
dormiu = ex._descansando and not abertos and not falas_d
_, falas_v = diga("bora voltar a trabalhar", "Bora voltar a trabalhar")
ok(dormiu and not ex._descansando and falas_v, "Descanso: ignora tudo e volta com “bora voltar a trabalhar”")

# --- v12: comando que a IA descobriu roda sozinho (sem "pode falar") e com a frase certa ---------------
class IAComando(IALenta):
    atraso = 1.6
    def interpretar(self, frase, comandos):
        time.sleep(self.atraso); return {"tipo": "comando", "texto": "abre o terceiro video"}
yt = YTFalso(); ex._yt = lambda: yt
ex.cerebro = IAComando()
ex.cfg["cerebro"]["segundo_plano_seg"] = 1
diga("aquele outro la da lista", "Aquele outro lá da lista")
time.sleep(2.5)
ok(("abrir", "https://youtube.com/watch?v=3") in yt.feito and not ex._pensamento,
   f"IA: comando em segundo plano roda sozinho e abre o 3º vídeo ({yt.feito})")
ex.cerebro = IALenta()

# --- v13: a IA pergunta quando precisa; a resposta fala sozinha; frase ja resolvida nao passa pela IA -----
class SemIA:
    ligado = False
    def esquecer(self): pass
ex.cerebro = SemIA(); yt.feito.clear()
diga("aquele outro la da lista", "Aquele outro lá da lista")
ok(("abrir", "https://youtube.com/watch?v=3") in yt.feito and ex._rota.startswith("memoria da ia"),
   f"IA: frase que ela já resolveu roda direto da memória, sem pensar ({ex._rota})")
class IAPergunta(IALenta):
    atraso = 1.4
    def interpretar(self, frase, comandos):
        time.sleep(self.atraso)
        if "respondeu" in frase:
            return {"tipo": "comando", "texto": "abre o segundo video"}
        return {"tipo": "pergunta", "texto": "Qual deles, o do monitor 1 ou o do 2?"}
ex.cerebro = IAPergunta(); yt.feito.clear()
diga("faz aquilo de antes com aquele negocio", "Faz aquilo de antes com aquele negócio")
time.sleep(2.2)
pergunta_feita = any("Qual deles" in f for f in ditos) and ex._pendente is not None
diga("o dois", "O dois")
time.sleep(2.2)
ok(pergunta_feita and ("abrir", "https://youtube.com/watch?v=2") in yt.feito,
   f"IA: pergunta sozinha quando precisa (sem “pode falar”) e executa com a resposta ({yt.feito})")
ex.cerebro = IALenta(); ex.cfg["cerebro"]["aviso_ao_terminar"] = "falar_direto"
diga("me conta uma curiosidade", "Me conta uma curiosidade")
time.sleep(3.2)
ok(any("Resposta pensada sobre me conta" in f for f in ditos) and not ex._pensamento,
   "IA: terminou de pensar → já fala a resposta (padrão novo)")
ex.cfg["cerebro"]["aviso_ao_terminar"] = "voz"

# --- v12: volume relativo, conversa curta, canal pelo nome falado --------------------------------------
feitos.clear(); diga("abaixa o spotify em 20", "Diminui o Spotify em 20%")
ok(feitos[:1] == [("volume_app", "Spotify.exe", "diminuir", 0.2)], f"“Diminui o Spotify em 20%” baixa 20 (não vai PARA 20) {feitos[:1]}")
_, falas_c = diga("e ai", "E aí")
ok(ex.ultimo_comando == "_cmd_conversinha" and falas_c, "“E aí” responde na hora (sem IA)")
from app.comandos import _nome_do_canal
ok(_nome_do_canal("pesquisa pelo canal frtt") == "frtt" and _nome_do_canal("abre o canal do youtube do tck por favor") == "tck",
   "Nome do canal: “pesquise pelo canal FRTT” procura FRTT")
from app import comandos as _c
import datetime as _dt
_real = _c.datetime
class _Madrugada(_dt.datetime):
    @classmethod
    def now(cls, tz=None): return _dt.datetime(2026, 9, 25, 3, 33)
_c.datetime = _Madrugada
ok(_c.saudacao_do_horario() == "Boa noite", "Às 3h33 ele diz “boa noite” (não “bom dia”)")
_c.datetime = _real

# --- v12: juntar abas, streaming e clicar pelo texto (extensao falsa) ---------------------------------
ext = ExtFalsa(); ex.ponte = ext
ext.abas.append({"id": 4, "janela": 12, "titulo": "Disney+", "url": "https://www.disneyplus.com/home", "ativa": True,
                 "abas_na_janela": 1, "ultimo_acesso": 3})
ext.pedidos.clear(); diga("junta o youtube com a disney", "Junta o YouTube com a Disney")
ok(("juntar", {"abas": [2], "destino": 4}) in ext.pedidos, f"“Junta o YouTube com a Disney” ({ext.pedidos[-1:]})")
ext.pedidos.clear(); diga("toca agentes da shield na disney", "Toca Agentes da Shield na Disney")
time.sleep(1.8)
ok(any(p[0] == "ir" and p[1]["url"] == "https://www.disneyplus.com/" for p in ext.pedidos) and
   any(p[0] == "buscar" and p[1]["texto"] == "Agentes da Shield" for p in ext.pedidos),
   f"Streaming: abre a Disney e digita o nome certo na busca ({ext.pedidos[:2]})")
ext.pedidos.clear(); diga("clica em continuar assistindo", "Clica em continuar assistindo")
cliques = [p for p in ext.pedidos if p[0] == "clicar" and not p[1].get("so_ver")]
ok(len(cliques) == 1 and cliques[0][1]["textos"] == ["continuar assistindo"], f"“Clica em …” pela extensão ({cliques})")

# --- v13: qual janela? YouTube aberto no monitor 1 e no 2 ------------------------------------------------
class ExtAbas:
    def __init__(self):
        self.pedidos = []
        self.abas = [{"id": 21, "janela": 1, "titulo": "YouTube", "url": "https://www.youtube.com/", "ativa": True,
                      "janela_x": 100, "janela_y": 0, "janela_largura": 800, "janela_altura": 600, "ultimo_acesso": 9},
                     {"id": 22, "janela": 2, "titulo": "Inscrições - YouTube", "url": "https://www.youtube.com/feed/subscriptions",
                      "ativa": True, "janela_x": 2000, "janela_y": 0, "janela_largura": 800, "janela_altura": 600, "ultimo_acesso": 5},
                     {"id": 23, "janela": 3, "titulo": "Disney+", "url": "https://www.disneyplus.com/browse/x", "ativa": True,
                      "janela_x": 4000, "janela_y": 0, "janela_largura": 800, "janela_altura": 600, "ultimo_acesso": 3}]
    def conectada(self): return True
    def pedir(self, acao, arg=None, espera=8, aba=None):
        self.pedidos.append((acao, arg, aba))
        if acao == "abas": return self.abas
        if acao == "resultados":
            n = aba or 0
            return [{"titulo": f"Video {i} da aba {n}" + (" Como seria o GTA 6" if (n, i) == (22, 4) else ""),
                     "canal": "David Jones" if (n, i) == (22, 4) else "Outro", "link": f"https://youtube.com/watch?v={n}{i}"}
                    for i in range(1, 6)]
        if acao == "clicar" and arg.get("so_ver"):
            return {"nota": 4 if arg.get("aba") == 23 else 0, "texto": "x"}
        return "ok"
class YTAba(YTFalso):
    def __init__(self):
        super().__init__(); self.aba_alvo = None
    def resultados(self): return ex._resultados_da_aba(self.aba_alvo)
    def abrir(self, link, monitor=None): self.feito.append(("abrir", self.aba_alvo, link))
_monitores, _janelas, _mouse = sistema.monitores, sistema.janelas_abertas, sistema.monitor_do_mouse
sistema.monitores = lambda: [{"numero": 1, "x": 0, "y": 0, "largura": 1920, "altura": 1040, "marca": "", "hz": 0},
                             {"numero": 2, "x": 1920, "y": 0, "largura": 1920, "altura": 1040, "marca": "", "hz": 0},
                             {"numero": 3, "x": 3840, "y": 0, "largura": 1920, "altura": 1040, "marca": "", "hz": 0}]
sistema.janelas_abertas = lambda: []
ext2 = ExtAbas(); ex.ponte = ext2; yt2 = YTAba(); ex._yt = lambda: yt2
diga("abre o segundo video do monitor 2", "Abre o segundo vídeo do monitor 2")
ok(yt2.feito[-1:] == [("abrir", 22, "https://youtube.com/watch?v=222")], f"“Abre o segundo vídeo do monitor 2” ({yt2.feito[-1:]})")
sistema.monitor_do_mouse = lambda: 1; yt2.feito.clear()
diga("abre o terceiro video", "Abre o terceiro vídeo")
ok(yt2.feito[-1:] == [("abrir", 21, "https://youtube.com/watch?v=213")], f"Sem dizer o monitor: o do mouse ({yt2.feito[-1:]})")
sistema.monitor_do_mouse = lambda: 3; yt2.feito.clear()
_, falas_q = diga("abre o primeiro video", "Abre o primeiro vídeo")
perguntou = any("monitor 1 ou no 2" in f for f in falas_q) and not yt2.feito
diga("no dois", "No dois")
ok(perguntou and yt2.feito[-1:] == [("abrir", 22, "https://youtube.com/watch?v=221")],
   f"Mouse em outra tela: pergunta “No monitor 1 ou no 2?” e usa a resposta ({falas_q}, {yt2.feito[-1:]})")
yt2.feito.clear()
diga("abre o video com o nome como seria o gta 6", "Abre o vídeo com o nome Como seria o GTA 6")
ok(yt2.feito[-1:] == [("abrir", 22, "https://youtube.com/watch?v=224")], f"Vídeo pelo nome: acha em qual tela ele está ({yt2.feito[-1:]})")
ext2.pedidos.clear(); diga("clica em continuar assistindo", "Clica em continuar assistindo")
cliques = [p for p in ext2.pedidos if p[0] == "clicar" and not p[1].get("so_ver")]
ok(cliques and cliques[0][1].get("aba") == 23, f"“Clica em …” vai na janela que tem esse botão ({cliques})")
sistema.monitores, sistema.janelas_abertas, sistema.monitor_do_mouse = _monitores, _janelas, _mouse
ex._yt = lambda: yt
del ex.ponte

# --- v12: audio do celular (pasta e Telegram) --------------------------------------------------------
import tempfile as _tf, pathlib as _pl
os.environ["MESTRE_SEGREDOS"] = _tf.mkdtemp()
from app import recebidos, segredos
class TranscritorFalso:
    def transcrever_arquivo(self, caminho): return _pl.Path(caminho).read_text(encoding="utf-8")
pasta_cel = _pl.Path(_tf.mkdtemp())
ex.cfg["recebidos"] = {"pasta": str(pasta_cel), "destino": "projeto"}
caixa = recebidos.Caixa(ex.cfg, ex, TranscritorFalso())
(pasta_cel / "audio1.ogg").write_text("Quero que o painel tenha um botão novo", encoding="utf-8")
colados.clear()
caixa._processar_arquivo(pasta_cel / "audio1.ogg", pasta_cel / "lidos")
ok(any("botão novo" in c and "Áudio do celular" in c for c in colados) and list((pasta_cel / "lidos").iterdir()),
   "Pasta do celular: transcreve, manda pro projeto e move o áudio para “lidos”")
respostas_tg = []
caixa.responder = lambda chat, texto: respostas_tg.append((chat, texto))
caixa._mensagem_telegram({"chat": {"id": 111}, "from": {"first_name": "Arthur"}, "text": "/start"})
yt.feito.clear()
ditos.clear()
caixa._mensagem_telegram({"chat": {"id": 111}, "text": "Mestre, abre o terceiro vídeo"})
ok("Mensagem do Telegram." in ditos and "Telegram" in estado.ler()["aviso"] and estado.ler()["aviso_ate"] > time.time(),
   f"Telegram: avisa na tela e fala “Mensagem do Telegram.” ({ditos[:2]}, {estado.ler()['aviso']})")
caixa._mensagem_telegram({"chat": {"id": 999}, "text": "Mestre, abre o primeiro vídeo"})
ok(segredos.ler("telegram_chat") == "111" and ("abrir", "https://youtube.com/watch?v=3") in yt.feito
   and not any(c == 999 for c, _ in respostas_tg), "Telegram: o 1º chat vira o seu, executa comando e ignora estranhos")

# --- fila do "pensando": 3 pedidos seguidos para a IA lenta + comando simples no meio, nada trava ---------
class IAFila(IALenta):
    atraso = 1.2
    def interpretar(self, frase, comandos):
        time.sleep(self.atraso)
        if "terceiro" in frase:
            return {"tipo": "comando", "texto": "abre o terceiro video"}
        return {"tipo": "resposta", "texto": f"Resposta pensada sobre {frase}"}
ex.cerebro = IAFila(); yt.feito.clear(); ditos.clear()
ex.cfg["cerebro"]["aviso_ao_terminar"] = "falar_direto"; ex.cfg["cerebro"]["segundo_plano_seg"] = 0.5
tempos = [diga(f, f)[0] for f in ("fila pedido um", "fila pedido dois")]
t_simples, falas_s = diga("que horas sao", "Que horas são")
tempos.append(diga("fila abre o terceiro la", "Fila abre o terceiro lá")[0])
fila_roxa = estado.ler()["pensamento"] == "pensando" and estado.ler().get("pensamentos_fila", 0) >= 2
fim = time.time() + 15
while time.time() < fim and ex._pensamento:
    time.sleep(0.1)
ordem = [f for f in ditos if "Resposta pensada sobre fila" in f]
ok(max(tempos) < 1.5 and t_simples < 1 and bool(falas_s) and fila_roxa and not ex._pensamento
   and ordem == ["Resposta pensada sobre fila pedido um", "Resposta pensada sobre fila pedido dois"]
   and ("abrir", "https://youtube.com/watch?v=3") in yt.feito and estado.ler()["pensamento"] == "",
   f"Fila do pensando: 3 pedidos + comando simples no meio, cada um na sua vez, sem travar ({ordem}, {yt.feito})")
t_depois, falas_d = diga("que horas sao", "Que horas são")
ok(t_depois < 1 and bool(falas_d), "Depois da fila o Assessor continua respondendo")
ex.cerebro = IALenta(); ex.cfg["cerebro"]["aviso_ao_terminar"] = "voz"; ex.cfg["cerebro"]["segundo_plano_seg"] = 1

todas = ex.todas_as_falas()
ok(all(ex.preencher(f) in todas for f in ("Segundo plano.", "Pronto {apelido}.")), "Avisos curtos do pensando ficam no cache")
print("FIM_FLUXOS", flush=True)  # os._exit nao esvazia o buffer
os._exit(0)
"""

VOZES_PAINEL = r"""
import os, tempfile, tkinter as tk, traceback
os.environ["MESTRE_SEGREDOS"] = tempfile.mkdtemp()
erros = []
tk.Tk.report_callback_exception = lambda self, e, v, tb: erros.append("".join(traceback.format_exception(e, v, tb)))
import app.painel as p
from app import configuracao, segredos
from app.voz import Voz
pn = p.Painel(); pn.update()
print("VERSAO_TELA", pn.rot_versao.cget("text"))
pn.mostrar_pagina("Voz"); pn.update()
fechada = not pn.secoes_motor["elevenlabs"].esta_aberta()
pn._escolher_motor("elevenlabs"); pn.update()
print("ABRIU_SECAO", fechada and pn.secoes_motor["elevenlabs"].esta_aberta(), pn._motor_escolhido())
pn.ent_eleven_chave.insert(0, "chave-de-teste")
pn.var_voz_eleven.set(pn.vozes_eleven["onwK4e9ZLuTAKqWW03F9"])
pn._escolher_motor("natural"); pn.update()
pn.var_voz_natural.set("Francisca (timbre da voz da Microsoft)")
pn.salvar(); pn.update()
v = configuracao.carregar()["voz"]
print("SALVOU_VOZ", v["motor"], v["voz_natural"], v["voz_elevenlabs"], v["modelo_elevenlabs"], segredos.ler("elevenlabs_chave"))
print("RESERVA", Voz({"voz": {"motor": "natural"}})._motores())
v["motor"] = configuracao.aspas("kokoro"); d = configuracao.carregar(); d["voz"]["motor"] = configuracao.aspas("kokoro")
configuracao.salvar(d)
print("ERROS_TELA", len(erros))
for e in erros: print(e)
pn._fechar()
"""

MIGRACAO_NOMES = r"""
from app import configuracao
d = configuracao.carregar()
a = configuracao.secao(d, "assistente")
a["nome"] = configuracao.aspas("Mestre"); a["apelido_usuario"] = configuracao.aspas("Mestre")
a["palavra_ativacao"] = configuracao.aspas("assessor")
cb = configuracao.secao(d, "cerebro"); cb["aviso_som"] = configuracao.aspas("voz"); cb["aviso_ao_terminar"] = configuracao.aspas("voz")
d["versao_config"] = 10; configuracao.salvar(d)
configuracao.migrar()
d = configuracao.carregar(); a = d["assistente"]; cb = d["cerebro"]
print(a["nome"], a["apelido_usuario"], cb["aviso_som"], cb["aviso_ao_terminar"])
if (a["nome"], a["apelido_usuario"], cb["aviso_som"], cb["aviso_ao_terminar"]) == ("Assessor", "Mestre", "nenhum", "falar_direto"):
    print("MIGRACAO_NOMES_OK")
a["nome"] = configuracao.aspas("Mestre"); a["apelido_usuario"] = configuracao.aspas("chefe")
a["palavra_ativacao"] = configuracao.aspas("mestre"); configuracao.salvar(d)   # (os proximos testes usam o padrao)
"""

NOMES = r"""
import yaml, tkinter as tk
c = yaml.safe_load(open("config.yaml", encoding="utf-8"))
from app import configuracao
d = configuracao.carregar(); a = configuracao.secao(d, "assistente")
a["nome"] = configuracao.aspas("Jarvis"); a["palavra_ativacao"] = configuracao.aspas("jarvis")
a["variacoes_aceitas"] = configuracao.lista_em_linha(["jarvis", "jarvis"]); configuracao.salvar(d)
import app.painel as p
pn = p.Painel(); pn.update()
def textos(w):
    for filho in w.winfo_children():
        for opcao in ("text", "label"):
            try:
                t = filho.cget(opcao)
                if isinstance(t, str) and t: yield t
            except Exception: pass
        yield from textos(filho)
for t in list(textos(pn)) + [pn.title()]:
    if "Mestre" in t: print("COM_MESTRE", repr(t[:90]))
pn._fechar()
from app.overlay import Indicador
class Vocab:
    def preferencia(self, k): return None
    def salvar_preferencia(self, *a): pass
class Ex: rodando, nome, palavra, vocab = True, "Jarvis", "jarvis", Vocab()
from app import estado
estado.definir("ouvindo")
raiz = tk.Tk(); ind = Indicador(raiz, Ex(), lambda: None, lambda: None); raiz.update()
itens = [ind.tela.itemcget(i, "text") for i in ind.tela.find_all() if ind.tela.type(i) == "text"]
menu = [ind.menu.entrycget(i, "label") for i in range(ind.menu.index("end") + 1) if ind.menu.type(i) == "command"]
for t in itens + menu:
    if "Mestre" in t: print("COM_MESTRE", repr(t))
print("INDICADOR", itens[0] if itens else "")
raiz.destroy()
print("NOMES_OK")
"""

APARENCIA = r"""
import yaml
import app.painel as p
pn = p.Painel(); pn.update()
pn.mostrar_pagina("Aparência"); pn.update()
pn.menu_cor.set("Azul"); pn.vars_aparencia["fonte"].set("Calibri"); pn.vars_aparencia["tamanho"].set("Grande")
pn._previa(); pn.update()
ok = pn.salvar()
pn._fechar()
ap = yaml.safe_load(open("config.yaml", encoding="utf-8"))["aparencia"]
from app import tema
cor = tema.paleta(ap)["ROSA"]
print("APARENCIA", ok, ap, cor)
if ok and ap["cor"] == "Azul" and ap["fonte"] == "Calibri" and ap["tamanho"] == "Grande" and cor == tema.CORES["Azul"]:
    print("APARENCIA_OK")
"""


def main() -> int:
    print("\nTESTE AUTOMATICO DO MESTRE (numa copia; seu config nao e tocado)\n")
    with tempfile.TemporaryDirectory(prefix="mestre_teste_") as tmp:
        pasta = copiar_projeto(Path(tmp))

        cod, saida = rodar(pasta, PREPARAR)
        conferir(cod == 0 and "preparado" in saida, "Config com 2.000 canais do YouTube", saida[-300:])

        print("\n[Painel]")
        cod, saida = rodar(pasta, PAINEL)
        valores = dict(l.split(" ", 1) for l in saida.splitlines() if l.split(" ")[0].isupper() and " " in l)
        tempo = float(valores.get("TEMPO_ABRIR", "999"))
        conferir(cod == 0 and tempo < 15, f"Painel abre rápido com 2.000 canais ({tempo:.1f}s)", saida[-800:])
        conferir("Manual do Mundo" in valores.get("BUSCA", ""), "Busca de canais", valores.get("BUSCA", ""))
        conferir(valores.get("SALVOU") == "True", "Salvar", saida[-800:])
        conferir(valores.get("ERROS_TELA") == "0", "Nenhum erro escondido nos botões", saida[-1500:])
        conferir(valores.get("PAGINAS", "").startswith("True Página 51 de 51 40"), "Passar páginas (◀ ▶) na lista",
                 valores.get("PAGINAS", ""))
        conferir(float(valores.get("TEMPO_PAGINA", "9")) < 0.5,
                 f"Trocar de página é rápido ({valores.get('TEMPO_PAGINA', '?')}s)", valores.get("TEMPO_PAGINA", ""))

        cod, saida = rodar(pasta, CONFERIR_CONFIG)
        v = dict(l.split(" ", 1) for l in saida.splitlines() if " " in l)
        conferir(v.get("PROGRAMA", "").endswith("python.exe") or "python" in v.get("PROGRAMA", ""),
                 "Programa novo salvo", saida[-500:])
        conferir(v.get("ORDEM_OK") == "True", "Programa salvo no lugar certo do arquivo", saida[-300:])
        conferir(v.get("SITE") == "https://exemplo.com", "Site novo salvo", saida[-300:])
        conferir(v.get("CANAIS") == "2002 True False", "Canal adicionado e canal apagado", v.get("CANAIS", ""))
        conferir("abrir_programa" in v.get("ROTINA", "") and "abrir_site" in v.get("ROTINA", ""),
                 "Rotina nova salva com as ações", v.get("ROTINA", ""))

        cod, saida = rodar(pasta, "import app.painel as p; pn = p.Painel(); pn.update(); print('REABRIU'); pn._fechar()")
        conferir("REABRIU" in saida, "Painel reabre depois de salvar", saida[-800:])

        print("\n[Comandos, como se você falasse]")
        s = comando(pasta, "mestre abre o spotify")
        conferir("Abrindo programa" in s and "Abrindo site" not in s,
                 "“abre o spotify” abre o PROGRAMA (e não o canal de mesmo nome)", s[-600:])
        s = comando(pasta, "mestre testa a rotina")
        conferir("Rotina: Rotina do teste" in s and "Abrindo programa" in s and "Abrindo site: https://exemplo.com" in s,
                 "Rotina nova roda pela frase", s[-800:])
        s = comando(pasta, "mestre abre o site do teste")
        conferir("Abrindo site: https://exemplo.com" in s, "Site novo abre", s[-600:])
        s = comando(pasta, "mestre abre o canal manual do mundo")
        conferir(("youtube.com/@manualdomundo" in s or "Abrindo o canal Manual do Mundo" in s) and "Traceback" not in s,
                 "Canal do YouTube abre", s[-600:])
        s = comando(pasta, "mestre que horas são")
        conferir("Falando:" in s and "Traceback" not in s, "Pergunta simples (horas)", s[-600:])

        print("\n[Ditado e pensamento em segundo plano]")
        cod, saida = rodar(pasta, FLUXOS, espera=120)
        for linha in saida.splitlines():
            if linha.startswith(("OK ", "FALHOU ")):
                conferir(linha.startswith("OK "), linha.split(" ", 1)[1].strip(), saida[-1200:])
        if "FIM_FLUXOS" not in saida:
            conferir(False, "Fluxos de ditado/pensamento rodaram até o fim", saida[-1500:])

        print("\n[Vocabulário: muitos jeitos de pedir]")
        r = subprocess.run([sys.executable, "-m", "testes.frases"], cwd=str(pasta), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=300,
                           env={**os.environ, "MESTRE_SIMULAR": "1", "PYTHONIOENCODING": "utf-8"})
        resumo = next((l for l in r.stdout.splitlines() if l.startswith("VOCABULARIO")), r.stdout[-300:] + r.stderr[-500:])
        conferir(r.returncode == 0, resumo.strip(), "\n".join(l for l in r.stdout.splitlines() if "FALHOU" in l))
        cod, saida = rodar(pasta, "from app import configuracao; import yaml; print('MIGROU', configuracao.migrar(), "
                                  "'netflix' in yaml.safe_load(open('config.yaml', encoding='utf-8'))['sites'])")
        conferir(re.search(r"MIGROU (True|False) True", saida) is not None,
                 "Sites padrão entram no config (Netflix, ChatGPT...)", saida[-400:])
        cod, saida = rodar(pasta, MIGRACAO_NOMES)
        conferir("MIGRACAO_NOMES_OK" in saida, "Config antigo: ele vira “Assessor”, você fica “Mestre”, pensando em silêncio",
                 saida[-600:])

        print("\n[Painel novo: versão e vozes]")
        cod, saida = rodar(pasta, VOZES_PAINEL)
        conferir("VERSAO_TELA Versão 13" in saida, "Painel mostra a versão do projeto (menu lateral)", saida[-600:])
        conferir("ABRIU_SECAO True elevenlabs" in saida, "Clicar no cartão da voz escolhe e abre a configuração dela",
                 saida[-600:])
        conferir("SALVOU_VOZ natural francisca onwK4e9ZLuTAKqWW03F9 eleven_flash_v2_5 chave-de-teste" in saida,
                 "Voz natural e ElevenLabs salvam (chave fora do projeto)", saida[-600:])
        conferir("RESERVA ['edge']" in saida or "RESERVA ['kokoro', 'edge']" in saida,
                 "Voz natural não instalada: ele fala com a Kokoro/Edge", saida[-600:])
        conferir("ERROS_TELA 0" in saida, "Página Voz nova sem erros na tela", saida[-1500:])

        print("\n[Nome e palavra novos em todo lugar]")
        cod, saida = rodar(pasta, NOMES)
        restos = [l for l in saida.splitlines() if l.startswith("COM_MESTRE")]
        conferir("NOMES_OK" in saida and not restos, "Com o nome “Jarvis”, nada na tela diz “Mestre”",
                 "\n".join(restos) or saida[-1200:])
        conferir("diga “Jarvis”" in saida, "Indicador mostra a palavra nova", saida[-600:])

        print("\n[Aparência]")
        cod, saida = rodar(pasta, APARENCIA)
        conferir("APARENCIA_OK" in saida, "Trocar cor, fonte e tamanho e salvar", saida[-800:])

        print("\n[Atualização por .zip]")
        destino = copiar_projeto(Path(tmp) / "outra")
        (destino / "config.yaml").write_text("# MEU CONFIG\n", encoding="utf-8")
        (destino / "ANTIGO.bat").write_text("velho", encoding="utf-8")
        pacote = Path(tmp) / "atualizacao.zip"
        with zipfile.ZipFile(pacote, "w") as z:
            for arq in (pasta / "app").rglob("*.py"):
                z.write(arq, "mestre/" + arq.relative_to(pasta).as_posix())
            z.writestr("mestre/config.yaml", "sobrescrito!")
            z.writestr("mestre/OBSOLETOS.txt", "ANTIGO.bat\nconfig.yaml\n")
        (destino / "app" / "versao.py").write_text('VERSAO = "12"\n', encoding="utf-8")
        cod, saida = rodar(destino, f"""
            from pathlib import Path
            from app import atualizar
            print("VERIFICAR", repr(atualizar.verificar(r"{pacote}")))
            print(atualizar.aplicar(r"{pacote}", Path.cwd(), instalar_bibliotecas=False))
        """)
        conferir("VERIFICAR ''" in saida and "Atualizado" in saida, "Atualização aplicada", saida[-500:])
        conferir("da versão 12 para a 13" in saida, "Atualização diz de qual versão para qual foi", saida[-500:])
        conferir((destino / "config.yaml").read_text(encoding="utf-8") == "# MEU CONFIG\n",
                 "Atualização NÃO mexe no seu config.yaml")
        conferir(not (destino / "ANTIGO.bat").exists(), "Atualização retira arquivos antigos")

        print("\n[Central e ícone]")
        cod, saida = rodar(pasta, "import app.central, app.bandeja, app.atualizar; print('IMPORTOU')")
        conferir("IMPORTOU" in saida, "Central, ícone e atualizador carregam", saida[-500:])

    falhas = [r for r in resultados if not r[0]]
    print("\n" + "=" * 60)
    if falhas:
        print(f"  {len(falhas)} de {len(resultados)} itens FALHARAM:")
        for _, nome, detalhe in falhas:
            print(f"\n--- {nome}\n{detalhe}")
    else:
        print(f"  TUDO CERTO: {len(resultados)} de {len(resultados)} itens passaram.")
    print("=" * 60)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
