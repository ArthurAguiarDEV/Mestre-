"""Teste automatico do basico do Mestre. Rode ANTES de entregar qualquer mudanca:

    venv\\Scripts\\python -m testes.teste_basico

Trabalha numa COPIA do projeto (pasta temporaria): seu config.yaml nao e tocado
e nada abre de verdade (MESTRE_SIMULAR=1). No fim mostra OK / FALHOU para cada item.
"""
import os
import re
import shutil
import subprocess
SEM_JANELA = getattr(subprocess, "CREATE_NO_WINDOW", 0)   # teste sem janela preta de console
import sys
import tempfile
import textwrap
import zipfile
from pathlib import Path

# aceita acento na saida sem precisar de PYTHONIOENCODING=utf-8 no ambiente
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJETO = Path(__file__).resolve().parent.parent
VERSAO_ATUAL = re.search(r'VERSAO = "(\d+(?:\.\d+)*)"', (PROJETO / "app" / "versao.py").read_text(encoding="utf-8")).group(1)


def versao_anterior(versao: str) -> str:
    """Uma versao "falsa" um pouco mais velha (para o teste da atualizacao): "2.5" -> "2.4", "14" -> "13"."""
    partes = versao.split(".")
    partes[-1] = str(max(0, int(partes[-1]) - 1))
    return ".".join(partes)


VERSAO_ANTERIOR = versao_anterior(VERSAO_ATUAL)
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
    r = subprocess.run([sys.executable, str(script)], creationflags=SEM_JANELA, cwd=str(pasta), capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=espera,
                       env={**os.environ, "MESTRE_SIMULAR": "1", "PYTHONIOENCODING": "utf-8"})
    return r.returncode, (r.stdout or "") + (r.stderr or "")


_SCRIPT_OFFLINE = r"""
import socket

def _bloqueado(self, endereco):
    raise OSError("rede bloqueada no teste (simulando sem internet)")

socket.socket.connect = _bloqueado   # simula "sem internet": qualquer tentativa de rede estoura

from pathlib import Path
import yaml

cfg = yaml.safe_load(open("config.yaml", encoding="utf-8")) or {}
modelo_whisper = (cfg.get("ouvido") or {}).get("modelo_whisper", "small")

try:
    from app.audio import Transcritor
    transcritor = Transcritor(modelo=modelo_whisper, dispositivo="cpu")
    print("OK Whisper liga so com o cache local (sem internet)")
    gasto = transcritor.aquecer()
    print("OK Whisper aquece ao ligar (1 s de silencio)" if gasto > 0 else "FALHOU Whisper aquece ao ligar::aquecer devolveu 0")
except Exception as erro:
    print(f"FALHOU Whisper liga so com o cache local (sem internet)::{erro!r}")

pasta_locutor = Path("modelos") / "locutor_ecapa"
necessarios = ("hyperparams.yaml", "embedding_model.ckpt", "mean_var_norm_emb.ckpt", "classifier.ckpt",
               "label_encoder.txt")
if all((pasta_locutor / n).exists() for n in necessarios):
    try:
        from app import locutor
        import numpy as np

        extrair = locutor.carregar_modelo()
        extrair(np.zeros(16000, dtype=np.float32))
        print("OK Reconhecimento de voz (locutor) liga so com o cache local (sem internet)")
    except Exception as erro:
        print(f"FALHOU Reconhecimento de voz (locutor) liga so com o cache local (sem internet)::{erro!r}")
else:
    print("PULOU Reconhecimento de voz (locutor): modelo nao esta em modelos/locutor_ecapa nesta maquina")
"""


def _rodar_offline_no_projeto_real(espera: int = 180) -> str:
    """Roda _SCRIPT_OFFLINE dentro do projeto de verdade (nao na copia dos testes), simulando sem
    internet: confere que Whisper e o reconhecimento de voz sobem so do que ja esta baixado."""
    script = Path(tempfile.gettempdir()) / "_mestre_teste_offline.py"
    script.write_text(_SCRIPT_OFFLINE, encoding="utf-8")
    venv_python = PROJETO / "venv" / "Scripts" / "python.exe"
    python_exec = str(venv_python) if venv_python.exists() else sys.executable
    env = {**os.environ, "MESTRE_SIMULAR": "1", "PYTHONIOENCODING": "utf-8", "PYTHONPATH": str(PROJETO)}
    r = subprocess.run([python_exec, str(script)], creationflags=SEM_JANELA, cwd=str(PROJETO),
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=espera, env=env)
    return (r.stdout or "") + (r.stderr or "")


def comando(pasta: Path, frase: str) -> str:
    r = subprocess.run([sys.executable, "-m", "app.main", "--mudo", "--comando", frase], creationflags=SEM_JANELA, cwd=str(pasta),
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

# O painel abre e guarda em memoria a lista de rotinas que tinha no config. Enquanto ele
# esta aberto, uma "outra fonte" (o Mestre rodando, ensinar rotina por voz) grava uma rotina
# nova no config.yaml. Depois o usuario apaga, NO PAINEL, uma rotina que ja existia quando ele
# abriu. Ao salvar: a rotina gravada por fora tem de sobreviver e a apagada tem de continuar apagada.
PAINEL_ROTINA_EXTERNA = r"""
from app import configuracao
import app.painel as p

pn = p.Painel(); pn.update()
pn.mostrar_pagina("Rotinas"); pn.update()

c = configuracao.carregar()
nova = configuracao.aspas({"nome": "Rotina de fora", "acoes": [{"falar": "Cheguei de fora!"}]})
nova.insert(1, "frases", configuracao.lista_em_linha(["rotina de fora"]))
c["rotinas"].append(nova)
configuracao.salvar(c)

alvo = next(i for i, r in enumerate(pn.rotinas) if r["nome"] == "Hora do cafe")
del pn.rotinas[alvo]
pn.rotina_atual = 0 if pn.rotinas else None
pn._desenhar_lista_rotinas(); pn.update()

print("SALVOU", pn.salvar())
pn.update()
pn._fechar()
"""

CONFERIR_ROTINA_EXTERNA = """
import yaml
c = yaml.safe_load(open("config.yaml", encoding="utf-8"))
print("NOMES", [r["nome"] for r in c.get("rotinas") or []])
"""


FLUXOS = r"""
import json, os, time, logging
logging.basicConfig(level=logging.WARNING)
from pathlib import Path
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

# --- Memoria de longo prazo em arquivos por assunto (memoria/fatos/) -----------------------------------
memoria.PASTA_MEMORIA.mkdir(exist_ok=True)
memoria.ARQUIVO_FATOS.write_text(
    "# fatos antigos (uma versao anterior guardava tudo num arquivo so)\n\n"
    "- Minha esposa se chama Ana e o aniversário dela é em março\n"
    "- Trabalho na IPM todo dia de manhã\n"
    "- Prefiro café sem açúcar\n"
    "- A senha do wifi de casa é segredo123\n",
    encoding="utf-8")
tinha_pasta_fatos_antes = memoria.PASTA_FATOS.exists()
fatos_migrados = memoria.fatos()   # 1a chamada: dispara a migracao
ok(not tinha_pasta_fatos_antes and not memoria.ARQUIVO_FATOS.exists() and memoria.BACKUP_FATOS_ANTIGO.exists(),
   "Migração do fatos.md antigo: gera backup (fatos.md.antes_da_migracao) e o arquivo antigo some")
ok(len(fatos_migrados) == 4, f"Migração: os 4 fatos antigos foram para memoria/fatos/ ({len(fatos_migrados)})")
ok(any("Ana" in f for f in memoria.fatos_assunto("pessoas")), "Classificação por palavra-chave: fato de pessoa foi pra pessoas.md")
ok(any("ipm" in normalizar(f) for f in memoria.fatos_assunto("trabalho")), "Classificação por palavra-chave: fato de trabalho foi pra trabalho.md")
ok(any("acucar" in normalizar(f) for f in memoria.fatos_assunto("preferencias")),
   "Classificação por palavra-chave: fato de preferência foi pra preferencias.md")
ok(any("wifi" in normalizar(f) for f in memoria.fatos_assunto("casa")), "Classificação por palavra-chave: fato de casa foi pra casa.md")
ok(memoria.ARQUIVO_INDICE.exists() and "pessoas.md" in memoria.ARQUIVO_INDICE.read_text(encoding="utf-8"),
   "INDICE.md criado com um resumo por arquivo de assunto")
memoria.fatos()   # chamar de novo nao pode migrar (nem apagar) de novo: e idempotente
ok(memoria.BACKUP_FATOS_ANTIGO.exists() and not memoria.ARQUIVO_FATOS.exists() and len(memoria.fatos()) == 4,
   "Migração roda só uma vez (idempotente): rodar de novo não duplica nem apaga nada")
contexto_trabalho = memoria.texto_para_ia("me fala sobre o meu trabalho")
ok("ipm" in normalizar(contexto_trabalho) and "ana" not in normalizar(contexto_trabalho)
   and "wifi" not in normalizar(contexto_trabalho),
   "Contexto pra IA: pergunta sobre trabalho manda só trabalho.md (+ índice), sem pessoas nem casa")

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
ok(any("ipm" in normalizar(f) for f in memoria.fatos_assunto("trabalho")),
   "“lembra que …” classifica por palavra-chave e grava no arquivo de assunto certo (trabalho.md)")
diga("esquece que prefiro cafe sem acucar", "Esquece que prefiro café sem açúcar")
ok(not any("acucar" in normalizar(f) for f in memoria.fatos_assunto("preferencias"))
   and any("ipm" in normalizar(f) for f in memoria.fatos_assunto("trabalho")),
   "“esquece que …” remove só o fato certo do arquivo de assunto certo, sem mexer nos outros")
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
# a memoria so grava depois de rodar sem correcao por uns 30s (ou na hora, se a MESMA frase repetir
# o MESMO comando antes disso): repete pra confirmar na hora, sem esperar o timer
yt.feito.clear()
diga("aquele outro la da lista", "Aquele outro lá da lista")
time.sleep(2.5)
ok(ex._pendente_ia is None, f"IA: frase repetida com o mesmo comando confirma a memória na hora ({ex._pendente_ia})")
ex.cerebro = IALenta()

# --- v13: a IA pergunta quando precisa; a resposta fala sozinha; frase ja resolvida nao passa pela IA -----
class SemIA:
    ligado = False
    def esquecer(self): pass
ex.cerebro = SemIA(); yt.feito.clear()
diga("aquele outro la da lista", "Aquele outro lá da lista")
ok(("abrir", "https://youtube.com/watch?v=3") in yt.feito and ex._rota.startswith("memoria da ia"),
   f"IA: frase que ela já resolveu roda direto da memória, sem pensar ({ex._rota})")

# --- correcao apaga a memoria da IA (sem ficar repetindo um erro pra sempre) --------------------------
ex.cerebro = IAComando(); yt.feito.clear()
diga("mais um comando novo que a ia vai inventar", "Mais um comando novo que a IA vai inventar")
time.sleep(2.5)
ok(ex._pendente_ia is not None, "IA: comando novo fica pendente de confirmação por uns 30s")
diga("isso ta errado", "Isso tá errado, era outra coisa")
ok(ex._pendente_ia is None, "IA: “isso tá errado” cancela a memória pendente (não fica preso pra sempre)")
ex.cerebro = IALenta()
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

# --- YouTube em 2 telas: "pausa"/"continua" decidem sozinhos (aba que toca / aba pausada por último) ------
class YTPausa(YTFalso):
    def __init__(self):
        super().__init__(); self.aba_alvo = None
    def pausar(self, pausar):
        self.feito.append(("pausar", self.aba_alvo, pausar)); return "ok"
yt3 = YTPausa(); ex._yt = lambda: yt3
ext3 = ExtAbas()
ext3.abas = [
    {"id": 31, "janela": 1, "titulo": "YouTube", "url": "https://www.youtube.com/watch?v=1", "ativa": True,
     "janela_x": 100, "janela_y": 0, "janela_largura": 800, "janela_altura": 600, "ultimo_acesso": 9,
     "audivel": True, "video_pausado": False, "video_pausado_em": 0},
    {"id": 32, "janela": 2, "titulo": "YouTube", "url": "https://www.youtube.com/watch?v=2", "ativa": True,
     "janela_x": 2000, "janela_y": 0, "janela_largura": 800, "janela_altura": 600, "ultimo_acesso": 5,
     "audivel": False, "video_pausado": True, "video_pausado_em": 500},
]
ex.ponte = ext3
diga("pausa o video", "Pausa o vídeo")
ok(yt3.feito[-1:] == [("pausar", 31, True)], f"“pausa” vai sozinho na aba que está tocando, sem perguntar ({yt3.feito[-1:]})")
yt3.feito.clear(); diga("continua o video", "Continua o vídeo")
ok(yt3.feito[-1:] == [("pausar", 32, False)], f"“continua” volta sozinho na aba pausada por último, sem perguntar ({yt3.feito[-1:]})")
ext3.abas[1]["audivel"] = True   # as duas tocando ao mesmo tempo
sistema.monitor_do_mouse = lambda: 3   # mouse numa 3ª tela: não desempata
yt3.feito.clear()
_, falas_p = diga("pausa o video", "Pausa o vídeo")
perguntou2 = any("monitor 1 ou no 2" in f for f in falas_p) and not yt3.feito
diga("no um", "No um")
ok(perguntou2 and yt3.feito[-1:] == [("pausar", 31, True)],
   f"Duas abas tocando ao mesmo tempo: pergunta e usa a resposta ({falas_p}, {yt3.feito[-1:]})")

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

# --- v25: novidades do Telegram (print, o que tá tocando, vídeo curto, energia com confirmação) ------------
_monitores_tg = sistema.monitores
sistema.monitores = lambda: [{"numero": 1, "x": 0, "y": 0, "largura": 1920, "altura": 1080, "marca": "", "hz": 0},
                             {"numero": 2, "x": 1920, "y": 0, "largura": 1920, "altura": 1080, "marca": "", "hz": 0}]
fotos_enviadas = []
caixa.enviar_fotos = lambda chat, itens: fotos_enviadas.append((chat, itens))
respostas_tg.clear()
caixa._mensagem_telegram({"chat": {"id": 111}, "text": "print"})
ok(fotos_enviadas and fotos_enviadas[-1][0] == 111 and len(fotos_enviadas[-1][1]) == 2,
   f"Telegram “print”: um print por monitor, sem precisar da palavra de ativação ({fotos_enviadas})")
fotos_enviadas.clear()
caixa._mensagem_telegram({"chat": {"id": 111}, "text": "print do monitor 2"})
ok(fotos_enviadas and len(fotos_enviadas[-1][1]) == 1, f"Telegram “print do monitor 2”: só o print daquele monitor ({fotos_enviadas})")

ex.caixa = caixa
fotos_enviadas.clear()
diga("manda um print no telegram", "Manda um print no Telegram")
ok(fotos_enviadas and fotos_enviadas[-1][0] == 111, f"Falando no PC “manda um print no Telegram” ({fotos_enviadas})")

_janelas_tg = sistema.janelas_abertas
sistema.janelas_abertas = lambda: [{"hwnd": 1, "titulo": "Sunset Blvd - Artista X", "exe": "spotify.exe", "monitor": 1},
                                   {"hwnd": 2, "titulo": "Editor de Código", "exe": "code.exe", "monitor": 2}]
ex._abas_abertas = lambda: [{"id": 9, "janela": 1, "titulo": "Um Vídeo - YouTube",
                             "url": "https://www.youtube.com/watch?v=9", "audivel": True, "video_pausado": None,
                             "ativa": True, "janela_x": 0, "janela_y": 0, "janela_largura": 800, "janela_altura": 600}]
respostas_tg.clear()
caixa._mensagem_telegram({"chat": {"id": 111}, "text": "o que ta tocando"})
resposta_tocando = respostas_tg[-1][1] if respostas_tg else ""
ok("Sunset Blvd" in resposta_tocando and "Um Vídeo" in resposta_tocando and "tocando" in resposta_tocando
   and "Editor de Código" in resposta_tocando,
   f"Telegram “o que tá tocando”: Spotify, YouTube e a janela ativa de cada monitor ({resposta_tocando!r})")
_, falas_toc = diga("o que ta tocando", "O que tá tocando")
ok(any("Sunset Blvd" in f for f in falas_toc), f"Falando no PC “o que tá tocando” responde falando ({falas_toc})")
sistema.janelas_abertas = _janelas_tg

videos_enviados = []
caixa.enviar_video = lambda chat, caminho, legenda="": videos_enviados.append((chat, caminho, legenda))
_gravar_video = sistema.gravar_video_monitor
sistema.gravar_video_monitor = lambda numero, segundos=15, fps=8: Path(f"video_fake_m{numero}_{segundos}s.mp4")
caixa._mensagem_telegram({"chat": {"id": 111}, "text": "grava 5 segundos do monitor 1"})
time.sleep(0.5)
ok(videos_enviados and videos_enviados[-1][1].name == "video_fake_m1_5s.mp4",
   f"Telegram “grava N segundos do monitor X”: grava e manda o vídeo ({videos_enviados})")
sistema.gravar_video_monitor = _gravar_video

comandos_energia = []
_desligar_pc, _suspender_pc, _reiniciar_pc = sistema.desligar_pc, sistema.suspender_pc, sistema.reiniciar_pc
_cancelar_desl, _cancelar_susp = sistema.cancelar_desligamento, sistema.cancelar_suspensao
sistema.desligar_pc = lambda s=30: comandos_energia.append(("desligar", s))
sistema.suspender_pc = lambda s=30: comandos_energia.append(("suspender", s))
sistema.reiniciar_pc = lambda s=30: comandos_energia.append(("reiniciar", s))
sistema.cancelar_desligamento = lambda: comandos_energia.append(("cancelar_desligamento",))
sistema.cancelar_suspensao = lambda: comandos_energia.append(("cancelar_suspensao",))
respostas_tg.clear()
caixa._mensagem_telegram({"chat": {"id": 111}, "text": "desligar"})
ok(not comandos_energia and "certeza" in respostas_tg[-1][1].lower(),
   f"Telegram “desligar”: pede confirmação antes de fazer qualquer coisa ({respostas_tg[-1:]})")
caixa._mensagem_telegram({"chat": {"id": 111}, "text": "sim"})
ok(comandos_energia == [("desligar", 30)], f"Depois do “sim”: desliga com aviso de 30 s ({comandos_energia})")
comandos_energia.clear()
caixa._mensagem_telegram({"chat": {"id": 111}, "text": "dormir"})
caixa._mensagem_telegram({"chat": {"id": 111}, "text": "cancela"})
ok(("cancelar_desligamento",) in comandos_energia and ("cancelar_suspensao",) in comandos_energia
   and not any(c[0] == "suspender" for c in comandos_energia),
   f"“cancela” antes do “sim”: cancela o pedido, nada acontece ({comandos_energia})")
sistema.desligar_pc, sistema.suspender_pc, sistema.reiniciar_pc = _desligar_pc, _suspender_pc, _reiniciar_pc
sistema.cancelar_desligamento, sistema.cancelar_suspensao = _cancelar_desl, _cancelar_susp
sistema.monitores = _monitores_tg
del ex.caixa

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

ROTINA_FALADA = r"""
import os, time, logging, yaml
logging.basicConfig(level=logging.WARNING)
from app.config import carregar_config
from app.comandos import Executor
from app.voz import Voz
from app import sistema
from app.texto import extrair_comando
from app.vocabulario import Vocabulario
ditos, abertos = [], []
class VozTeste(Voz):
    def falar(self, texto): ditos.append(texto)
class IAFalsa:
    ligado = True
    def interpretar(self, frase, comandos): return {"tipo": "resposta", "texto": "Isso é conversa."}
    def perguntar(self, frase, perfil="geral"): return "Isso é conversa."
    def esquecer(self): pass
    def variacoes_de_frase(self, frase, passos="", n=50):
        time.sleep(0.4)   # a IA demora: vai para a fila em segundo plano
        return ["Partiu modo mergulho", "partiu modo mergulho!", "bora pro modo mergulho", "Mestre, modo mergulho total",
                "modo concentração", "abre o gmail", "que horas são", "bora trabalhar", "mergulho",
                "toca a playlist foco total no spotify", "manda ver no mergulho", "pausa"]
class SemIA:
    ligado = False
    def esquecer(self): pass
sistema.abrir_site = lambda url: abertos.append(url)
sistema.abrir_programa = lambda caminho: abertos.append("programa:" + str(caminho)) or True
cfg = carregar_config()
cfg.setdefault("cerebro", {}).update(segundo_plano_seg=0.1, aviso_ao_terminar="voz")
cfg["spotify"] = {"playlists": {"Foco total": "https://open.spotify.com/playlist/37i9dQZF1DX8NTLI2TtZa6"},
                  "apertar_play": False}
ex = Executor(cfg, VozTeste(cfg, mudo=True), IAFalsa(), Vocabulario())
ex._extensao = lambda: False
def diga(completa):
    achou, cmd = extrair_comando(completa, ["mestre"])
    ditos.clear(); ex.executar(cmd if achou else completa, completa); return list(ditos)
def ok(c, nome): print(("OK " if c else "FALHOU ") + nome, flush=True)
def rotina(nome):
    c = yaml.safe_load(open("config.yaml", encoding="utf-8"))
    return next((r for r in c.get("rotinas") or [] if r["nome"] == nome), None), len(c.get("rotinas") or [])

diga("Mestre, vou te mostrar uma nova rotina")
ok(ex.ultimo_comando == "_cmd_ensinar_rotina" and ex._gravacao is not None, "Rotina falada: “vou te mostrar uma nova rotina” começa a gravar")
diga("Mestre, abre o Gmail"); diga("Mestre, abre o Claude")
falas_ia = diga("Mestre, me explica a teoria da relatividade")
diga("Mestre, toca a playlist Foco total no Spotify")
ok(abertos[:1] == ["https://mail.google.com"] and "programa:claude" in abertos and any("spotify" in a for a in abertos),
   f"Rotina falada: cada comando roda na hora ({abertos})")
ok(any("não entra na rotina" in f for f in falas_ia), f"Rotina falada: passo que foi pra IA fica de fora com aviso ({falas_ia})")
falas = diga("Mestre, pronto")
ok(any("Rotina aprendida. Qual frase eu uso para chamar?" in f for f in falas) and ex._pendente is not None,
   f"Rotina falada: “pronto” pergunta a frase ({falas})")
falas = diga("Que horas são")
ok(any("já chama outro comando" in f for f in falas) and ex._pendente is not None,
   f"Rotina falada: frase que já é de outro comando pede outra ({falas})")
diga("Modo mergulho")
fim = time.time() + 10
while time.time() < fim and ex._pensamento:
    time.sleep(0.1)
time.sleep(0.3)
r, _ = rotina("Modo mergulho")
acoes = r["acoes"] if r else []
ok(acoes == [{"abrir_site": "https://mail.google.com"}, {"abrir_programa": "claude"},
             {"comando": "toca a playlist foco total no spotify"}], f"Rotina falada: 3 passos salvos no config ({acoes})")
frases = r["frases"] if r else []
ok(frases[:1] == ["modo mergulho"] and "partiu modo mergulho" in frases and "modo concentracao" in frases
   and "bora pro modo mergulho" in frases and "modo mergulho total" in frases and len(frases) == len(set(frases)),
   f"Rotina falada: frase dita + variações da IA, sem repetidas ({frases})")
ok(not any(f in frases for f in ("abre o gmail", "que horas sao", "bora trabalhar", "mergulho", "pausa", "manda ver no mergulho",
                                 "toca a playlist foco total no spotify")),
   f"Rotina falada: variações que roubariam outros comandos ficam de fora ({frases})")
ok(any("ficou com" in f and "frases" in f for f in ditos), f"Rotina falada: confirma quantas frases ficaram ({ditos})")
texto = open("config.yaml", encoding="utf-8").read()
ok("# 1c) PERSONALIDADE" in texto and 'nome: "Modo mergulho"' in texto, "Rotina falada: config salvo com comentários e aspas")
abertos.clear()
diga("Mestre, partiu modo mergulho")
ok(ex.ultimo_comando == "_cmd_rotinas" and "https://mail.google.com" in abertos and "programa:claude" in abertos
   and any("spotify" in a for a in abertos), f"Rotina falada: a frase nova dispara a rotina ({ex.ultimo_comando} {abertos})")
ex2 = Executor(carregar_config(), VozTeste(cfg, mudo=True), SemIA(), Vocabulario())
ex2._extensao = lambda: False
ex2.executar("modo concentracao", "Mestre, modo concentração")
ok(ex2.ultimo_comando == "_cmd_rotinas", f"Rotina falada: depois de reiniciar ela continua valendo ({ex2.ultimo_comando})")
diga("Mestre, que horas são")
ok(ex.ultimo_comando == "_cmd_hora_data", "Rotina falada: “que horas são” continua sendo horas")

_, antes = rotina("x")
diga("Mestre, grava uma rotina"); diga("Mestre, abre o Gmail")
falas = diga("Mestre, cancela a rotina")
_, depois = rotina("x")
ok(ex._gravacao is None and antes == depois and not ex._pendente, f"Rotina falada: “cancela a rotina” sai sem salvar ({falas})")

ex.cerebro = SemIA()
diga("Mestre, aprende uma rotina nova"); diga("Mestre, abre o Gmail"); diga("Mestre, fala assim: Bom estudo!")
diga("Mestre, terminei"); falas = diga("Hora do estudo")
r, _ = rotina("Hora do estudo")
ok(r is not None and r["frases"][0] == "hora do estudo" and len(r["frases"]) >= 3 and {"falar": "Bom estudo!"} in r["acoes"]
   and any("É só falar" in f for f in falas), f"Rotina falada sem IA: frase dita + variações simples ({r} {falas})")
print("FIM_ROTINA_FALADA", flush=True)
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
pn._usar_reserva("natural"); pn._usar_reserva("azure"); pn.update()   # (a ativa nao vira reserva)
print("ABA_RESERVA", pn.var_reserva.get(), "Reserva: Azure" in pn.rot_voz_resumo.cget("text"),
      pn._cartoes_motor["natural"]["ativar"].cget("state"))
pn.salvar(); pn.update()
v = configuracao.carregar()["voz"]
print("SALVOU_VOZ", v["motor"], v["voz_natural"], v["voz_elevenlabs"], v["modelo_elevenlabs"], segredos.ler("elevenlabs_chave"))
print("SALVOU_RESERVA", v.get("reserva"))
print("RESERVA", Voz({"voz": {"motor": "natural"}})._motores())
vr = Voz({"voz": {"motor": "natural", "reserva": "azure"}}); vr._motor_pronto = lambda m: True
print("ORDEM_RESERVA", vr._motores())
v["motor"] = configuracao.aspas("kokoro"); d = configuracao.carregar(); d["voz"]["motor"] = configuracao.aspas("kokoro")
configuracao.salvar(d)
print("ERROS_TELA", len(erros))
for e in erros: print(e)
pn._fechar()
"""

VOZ_NATURAL_SERVIDOR = r"""
import subprocess
from app import voz_natural as vn

vn.instalado = lambda: True   # simula "ja instalada" sem precisar do venv separado de verdade

ligado = {"v": False}
def estado_falso(forcar=False):
    return {"pronto": False, "placa": "", "erro": ""} if ligado["v"] else {}
vn.estado = estado_falso

chamadas_popen = []
class ProcessoFalso:
    pid = 4242
    def poll(self):
        return None

def popen_falso(*a, **k):
    chamadas_popen.append(1)
    ligado["v"] = True   # simula o servidor abrindo a porta assim que "liga"
    return ProcessoFalso()
subprocess.Popen = popen_falso

r1 = vn.iniciar()   # nada rodando ainda: sobe UM servidor
print("PRIMEIRA", r1, len(chamadas_popen))

r2 = vn.iniciar()   # mesmo processo chamando de novo: reusa, nao sobe outro
print("SEGUNDA", r2, len(chamadas_popen))

vn._servidor = None   # simula um SEGUNDO processo (so tem a variavel em memoria zerada; a "porta" continua no ar)
r3 = vn.iniciar()
print("TERCEIRO_PROCESSO", r3, len(chamadas_popen))

print("VOZ_NATURAL_SERVIDOR_OK", r1 and r2 and r3 and len(chamadas_popen) == 1)
"""

VOZ_NATURAL_RESERVA = r"""
from pathlib import Path
from app.voz import Voz
from app import voz_natural as vn

vn.instalado = lambda: True
vn.pronta = lambda: False   # ainda carregando (nao aquecida)
vn.iniciar = lambda: True   # (nao sobe nada de verdade neste teste)

voz = Voz({"voz": {"motor": "natural"}}, mudo=True)
voz._motor_pronto = lambda m: m in ("natural", "kokoro", "edge")

tentados = []
def gerar_stub(parte, motor=None):
    motor = motor or voz.motor
    tentados.append(motor)
    if motor == "natural":
        raise RuntimeError("voz natural ainda carregando")   # e o que voz_natural.gerar() faria de verdade
    return Path("fake.wav"), True
voz._gerar = gerar_stub

arquivo, temporario = voz._gerar_com_reserva("Oi, tudo bem?")
print("MOTORES_TENTADOS", tentados)
print("VOZ_NATURAL_RESERVA_OK", tentados == ["natural", "kokoro"] and str(arquivo) == "fake.wav")
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
pn.montar_todas(); pn.update()   # (as paginas sao montadas sob demanda: aqui todas, para conferir os textos)
dados = {str(l["frame"]) for l in pn._cmd_linhas}   # (Ultimos comandos: o que VOCE falou, nao texto fixo da tela)
def textos(w):
    for filho in w.winfo_children():
        if str(filho) in dados: continue
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

VOZ_DONO = r"""
# Responder so a voz do dono: embeddings FALSOS (nada de baixar o modelo no teste)
import os, sys, tempfile, time, traceback, tkinter as tk
os.environ["MESTRE_SEGREDOS"] = tempfile.mkdtemp()
import numpy as np
from app import locutor
from app.audio import TAXA

def ok(c, nome): print(("OK " if c else "FALHOU ") + nome, flush=True)

def tom(freq, seg, fase=0.0):   # "voz" sintetica: um tom de 16 bits
    t = np.arange(int(seg * TAXA)) / TAXA
    return (np.sin(2 * np.pi * freq * t + fase) * 8000).astype(np.int16).tobytes()

rng = np.random.default_rng(7)
VOZ_A, VOZ_B = rng.normal(size=192), rng.normal(size=192)
def falso(a):   # "modelo": tom grave = dono (A), agudo = outra pessoa (B), com um pouco de ruido
    freq = np.argmax(np.abs(np.fft.rfft(a))) * TAXA / len(a)
    return (VOZ_A if freq < 250 else VOZ_B) + rng.normal(scale=0.3, size=192)

ok(locutor.opcoes({}) == (False, locutor.EXIGENCIA_PADRAO), "Voz do dono: config antigo = desligado com exigência padrão")
locutor.salvar_impressao([falso(locutor.bytes_para_float(tom(150, 2, i))) for i in range(10)])
ok(locutor.carregar_impressao() is not None and locutor.arquivo_impressao().parent == __import__("pathlib").Path(os.environ["MESTRE_SEGREDOS"]) / "Mestre",
   "Voz do dono: impressão salva fora do projeto")
v = locutor.Verificador(True, 0.4, extrair=falso)
dono, outra = tom(150, 2), tom(400, 2)
a1, n1, _ = v.verificar(dono)
a2, n2, m2 = v.verificar(outra)
ok(a1 and n1 > 0.8, f"Voz do dono: mesma voz aceita (nota {n1:.2f})")
ok(not a2 and m2 == "voz não reconhecida", f"Voz do dono: outra voz recusada (nota {n2:.2f})")
ok(locutor.Verificador(False, 0.4, extrair=falso).verificar(outra)[0], "Voz do dono: desligado aceita tudo")
ok(locutor.Verificador(True, 0.4, extrair=None).verificar(outra)[:2] == (True, None), "Voz do dono: modelo não carregado aceita")
ok(v.verificar(tom(400, 0.6), em_conversa=True)[0], "Voz do dono: frase curta na conversa passa")
ok(locutor.decidir(0.33, 0.4, 0.6)[0] and not locutor.decidir(0.33, 0.4, 2.0)[0], "Voz do dono: frase curta tem tolerância")

# No ouvido: a frase de outra voz nao e executada e vai para o historico
from app.ouvido import Ouvido
from app import memoria
o = object.__new__(Ouvido); o.verificador = v
ok(o._voz_do_dono(dono, "mestre abre o youtube", False), "Voz do dono: ouvido deixa passar o dono")
ok(not o._voz_do_dono(outra, "mestre abre o youtube", False) and memoria.historico(5)[-1].get("tipo") == "voz_nao_reconhecida",
   "Voz do dono: ouvido ignora outra voz e registra no histórico")
locutor.apagar_impressao()
ok(locutor.Verificador(True, 0.4, extrair=falso).verificar(outra)[0], "Voz do dono: sem cadastro aceita tudo")

# Painel: cadastrar (gravacao simulada), campos e salvar
erros = []
tk.Tk.report_callback_exception = lambda self, e, v, tb: erros.append("".join(traceback.format_exception(e, v, tb)))
import app.painel as p
pn = p.Painel(); pn.update()
pn.mostrar_pagina("Áudio"); pn.update()
pn._com_modelo_voz = lambda trabalho: trabalho(falso)   # (sem mainloop no teste: nada de thread)
pn._gravar_para = lambda receber: (pn.after(20, lambda: receber(tom(150, 2))), True)[1]
pn._cadastrar_voz()
fim = time.time() + 20
while time.time() < fim and not pn.var_so_minha_voz.get():
    pn.update(); time.sleep(0.05)
info = locutor.info_impressao()
ok(info.get("frases") == len(locutor.FRASES_CADASTRO) and pn.var_so_minha_voz.get(), "Voz do dono: cadastro pelo painel grava e liga a chave")
pn.var_exig_voz.set(0.55)
ok(pn.salvar(), "Voz do dono: painel salva")
import yaml
ov = yaml.safe_load(open("config.yaml", encoding="utf-8"))["ouvido"]
ok(ov.get("so_minha_voz") is True and abs(float(ov.get("exigencia_voz")) - 0.55) < 0.001, "Voz do dono: opções no config.yaml")
ok(not erros, "Voz do dono: sem erros na tela" + ("".join(erros)[-600:] if erros else ""))
ok("speechbrain" not in sys.modules and "torch" not in sys.modules, "Voz do dono: teste não carrega o modelo de verdade")
pn._fechar()
print("FIM_VOZ_DONO")
"""


CAPTACAO = r"""
# Captacao da voz: blocos sinteticos (tom = fala, zeros = silencio) no laco do Ouvido, sem microfone
import os, sys, tempfile, time
os.environ["MESTRE_SEGREDOS"] = tempfile.mkdtemp()
import numpy as np
from app import estado, locutor, memoria
from app.audio import TAXA, BLOCO, Segmentador
from app.ouvido import Ouvido, so_a_palavra, espera_apos_palavra, ESPERA_APOS_PALAVRA

def ok(c, nome): print(("OK " if c else "FALHOU ") + nome, flush=True)

def tom(seg, freq=150):
    t = np.arange(int(seg * TAXA)) / TAXA
    return (np.sin(2 * np.pi * freq * t) * 8000).astype(np.int16).tobytes()

def silencio(seg):
    return bytes(2 * int(seg * TAXA))

class Falso:   # "Whisper": devolve as frases do roteiro, na ordem
    def __init__(self, frases): self.frases = list(frases)
    def transcrever(self, audio, **k): return self.frases.pop(0) if self.frases else ""

def novo(frases, espera=ESPERA_APOS_PALAVRA, verificador=None, min_fala=0.35):
    o = object.__new__(Ouvido)
    o.ganho, o.acordar_tela, o._vigia, o.diagnostico = 1.0, False, None, False
    o.variacoes, o.espera_palavra = ["assessor"], espera
    o.verificador = verificador or locutor.Verificador(False)
    o.transcritor = Falso(frases)
    o._preparar_laco()
    chamadas = []
    def executar(comando, frase, seguimento=False):
        chamadas.append((comando, frase, seguimento)); return 8
    seg = Segmentador(500, 0.7, min_fala=min_fala)
    def tocar(audio, eco=False):
        for i in range(0, len(audio), BLOCO * 2):
            o._bloco(audio[i:i + BLOCO * 2], eco, seg, executar)
    estado.atualizar(conversa_ate=0.0, ditado_desde=0.0, descanso=False)
    return o, tocar, chamadas

def ouvidas(desde):
    return [x for x in memoria.ouvidas(300) if x.get("ts", 0) >= desde - 0.01]

ok(so_a_palavra("") and so_a_palavra("e ai") and not so_a_palavra("abre o youtube"),
   "Captação: 'Assessor' sozinho (ou só enchimento) é reconhecido")
ok(espera_apos_palavra({}) == ESPERA_APOS_PALAVRA and espera_apos_palavra({"ouvido": {"espera_apos_palavra": None}}) == ESPERA_APOS_PALAVRA,
   "Captação: config antigo usa a espera padrão")

# 1) "Assessor" + pausa de 2 s + "abre o YouTube" = uma frase so
inicio = time.time()
o, tocar, ch = novo(["Assessor.", "Abre o YouTube."])
tocar(tom(0.6)); tocar(silencio(2.0)); tocar(tom(1.2)); tocar(silencio(1.5))
ok(ch == [("abre o youtube", "Assessor. Abre o YouTube.", False)], f"Captação: palavra + pausa de 2 s + comando = uma frase só {ch}")
reg = ouvidas(inicio)
ok(any(str(r.get("motivo", "")).startswith("só a palavra") for r in reg) and any(r.get("junto_da_palavra") for r in reg),
   "Captação: ouvido.jsonl mostra a espera e a frase juntada")

# 2) "Assessor" sozinho: nao some, responde e abre a janela; o resto vem como seguimento
o, tocar, ch = novo(["Assessor.", "Abre o YouTube."])
tocar(tom(0.6)); tocar(silencio(2.0))
ok(ch == [], "Captação: durante a espera ainda não respondeu")
tocar(silencio(2.0))
ok(ch == [("", "Assessor.", False)], f"Captação: 'Assessor' sozinho não é descartado (abre a conversa) {ch}")
tocar(tom(1.2)); tocar(silencio(1.0))
ok(len(ch) == 2 and ch[1] == ("abre o youtube", "Abre o YouTube.", True), f"Captação: depois de só chamar, o resto vale sem a palavra {ch}")

# 3) espera 0 = responde na hora (jeito antigo)
o, tocar, ch = novo(["Assessor."], espera=0)
tocar(tom(0.6)); tocar(silencio(1.0))
ok(ch == [("", "Assessor.", False)], "Captação: espera 0 responde na hora")

# 4) Descartes registrados com motivo
inicio = time.time()
o, tocar, ch = novo(["", "Bom dia pessoal."])
tocar(tom(0.8)); tocar(silencio(1.0)); tocar(tom(1.0)); tocar(silencio(1.0))
reg = ouvidas(inicio)
ok(ch == [] and any(str(r.get("motivo", "")).startswith("transcrição vazia") for r in reg), "Captação: transcrição vazia fica registrada")
ok(any(r.get("motivo") == "sem a palavra de ativação" and r.get("texto") == "Bom dia pessoal." for r in reg),
   "Captação: frase sem a palavra fica registrada com o motivo")
o, tocar, ch = novo(["x"], min_fala=1.5)
tocar(tom(0.3)); tocar(silencio(1.0))
ok(any(r.get("motivo") == "curta demais" for r in ouvidas(inicio)), "Captação: trecho curto demais fica registrado")
o, tocar, ch = novo(["x"])
tocar(tom(1.2)); tocar(tom(0.3), eco=True); tocar(silencio(1.0))
ok(ch == [] and any(str(r.get("motivo", "")).startswith("cortada") for r in ouvidas(inicio)),
   "Captação: fala cortada pela voz do assistente fica registrada")

# 5) Voz do dono: "Assessor" curto + comando sao conferidos JUNTOS (mais voz para comparar)
rng = np.random.default_rng(3)
VA, VB = rng.normal(size=192), rng.normal(size=192)
def falso(a):
    freq = np.argmax(np.abs(np.fft.rfft(a))) * TAXA / len(a)
    return VA if freq < 250 else VB
locutor.salvar_impressao([falso(locutor.bytes_para_float(tom(2))) for _ in range(5)])
v = locutor.Verificador(True, 0.4, extrair=falso)
o, tocar, ch = novo(["Assessor.", "Abre o YouTube."], verificador=v)
tocar(tom(0.6)); tocar(silencio(2.0)); tocar(tom(1.2)); tocar(silencio(1.5))
ok(len(ch) == 1 and ch[0][0] == "abre o youtube", "Captação: com 'só minha voz' ligado, o dono passa")
inicio = time.time()
o, tocar, ch = novo(["Assessor, abre o YouTube."], verificador=v)
tocar(tom(1.5, freq=400)); tocar(silencio(1.0))
ok(ch == [] and any(r.get("motivo") == "voz não reconhecida" for r in ouvidas(inicio)),
   "Captação: outra voz é recusada e registrada com o motivo")
locutor.apagar_impressao()

# 6) Detector local da palavra (simulado: tom de 300 Hz = "falou a palavra")
from app import palavra_local
class DetectorFalso:
    limiar = 0.5
    def __init__(self, quebrado=False): self.quebrado, self.blocos = quebrado, 0
    def ouvir(self, bloco):
        if self.quebrado: raise RuntimeError("quebrou")
        self.blocos += 1
        a = np.frombuffer(bloco, dtype=np.int16).astype(np.float32)
        if not a.any(): return 0.0
        freq = np.argmax(np.abs(np.fft.rfft(a))) * TAXA / len(a)
        return 0.9 if 250 < freq < 350 else 0.1
def contar(o):
    o.transcricoes = 0
    orig = o.transcritor.transcrever
    def t(audio, **k):
        o.transcricoes += 1; return orig(audio, **k)
    o.transcritor.transcrever = t
inicio = time.time()
o, tocar, ch = novo(["Assessor, abre o YouTube."]); o.detector = DetectorFalso(); contar(o)
tocar(tom(1.5, freq=300)); tocar(silencio(1.0))
ok(o.transcricoes == 1 and len(ch) == 1 and ch[0][0] == "abre o youtube",
   f"Detector: ligado e ouviu a palavra -> a frase vai ao Whisper e é executada {ch}")
ok(any(r.get("nota_detector") == 0.9 for r in ouvidas(inicio)), "Detector: a nota dele fica no ouvido.jsonl")
inicio = time.time()
o, tocar, ch = novo(["Bom dia pessoal."]); o.detector = DetectorFalso(); contar(o)
tocar(tom(1.5)); tocar(silencio(1.0))
ok(o.transcricoes == 0 and ch == [] and any(r.get("motivo") == "sem a palavra (detector local)" for r in ouvidas(inicio)),
   "Detector: sem a palavra a frase nem vai ao Whisper (descarte registrado)")
o, tocar, ch = novo(["Abre o YouTube."]); o.detector = DetectorFalso(); contar(o)
estado.atualizar(conversa_ate=time.time() + 30); o._conversa_ate = time.time() + 30
tocar(tom(1.5)); tocar(silencio(1.0))
ok(o.transcricoes == 1 and len(ch) == 1, "Detector: na janela de conversa tudo vai ao Whisper (sem precisar da palavra)")
o, tocar, ch = novo(["Bora voltar a trabalhar."]); o.detector = DetectorFalso(); contar(o)
estado.atualizar(descanso=True)
tocar(tom(1.5)); tocar(silencio(1.0))
estado.atualizar(descanso=False)
ok(o.transcricoes == 1, "Detector: no modo descanso não filtra ('bora voltar a trabalhar' continua acordando)")
o, tocar, ch = novo(["Assessor.", "Abre o YouTube."]); o.detector = DetectorFalso(); contar(o)
tocar(tom(0.6, freq=300)); tocar(silencio(2.0)); tocar(tom(1.2)); tocar(silencio(1.5))
ok(ch == [("abre o youtube", "Assessor. Abre o YouTube.", False)],
   f"Detector: 'Assessor' + pausa + comando (sem a palavra) continua virando uma frase só {ch}")
o, tocar, ch = novo(["Bom dia pessoal.", "Assessor, abre o YouTube."]); o.detector = DetectorFalso(quebrado=True); contar(o)
tocar(tom(1.5)); tocar(silencio(1.0)); tocar(tom(1.5)); tocar(silencio(1.0))
ok(o.detector is None and o.transcricoes == 2 and len(ch) == 1, "Detector: se ele der erro, desliga e o Whisper ouve tudo")
# ligado sem modelo / desligado -> None (o Ouvido segue o fluxo de sempre)
d, motivo = palavra_local.carregar({"ouvido": {"detector_palavra": True, "detector_modelo": "modelos/palavra/nao_existe.npz"}})
pronto, texto = palavra_local.situacao({"ouvido": {"detector_palavra": True, "detector_modelo": "modelos/palavra/nao_existe.npz"}})
ok(d is None and not pronto and "não encontrado" in texto, f"Detector: ligado sem modelo fica indisponível e avisa ({texto[:40]})")
ok(palavra_local.carregar({})[0] is None and palavra_local.opcoes({})[0] is False and palavra_local.opcoes({})[2] == 0.5,
   "Detector: config antigo = desligado, exigência 0.5")
ok(palavra_local.nome_arquivo("Assessor") == "assessor.npz" and palavra_local.nome_arquivo("Jarvis") == "jarvis.npz",
   "Detector: o arquivo do modelo segue a palavra escolhida")
o, tocar, ch = novo(["Bom dia pessoal.", "Assessor, abre o YouTube."]); contar(o)   # (detector None = sem modelo/desligado)
tocar(tom(1.5)); tocar(silencio(1.0)); tocar(tom(1.5)); tocar(silencio(1.0))
ok(o.transcricoes == 2 and len(ch) == 1, "Detector: desligado/sem modelo = fluxo de sempre (Whisper ouve tudo)")
rng = np.random.default_rng(5)
pesos = {"media": np.zeros(1536), "desvio": np.ones(1536), "n": np.array(16), "w1": rng.normal(size=(1536, 4)),
         "b1": np.zeros(4), "w2": rng.normal(size=(4, 1)), "b2": np.zeros(1)}
notas = palavra_local.Classificador(pesos).notas(rng.normal(size=(3, 16, 96)))
ok(notas.shape == (3,) and bool(((notas >= 0) & (notas <= 1)).all()), "Detector: a rede em numpy dá notas de 0 a 1")
print("FIM_CAPTACAO")
"""


FALA_FLUIDA = r"""
# Fala em segundo plano, interromper com a palavra, frase pela metade e frase a frase.
# A voz e a de verdade (fila, linha separada, parar), mas "gerar" e "tocar" sao simulados: tocar = esperar N s.
import os, sys, tempfile, threading, time
os.environ["MESTRE_SEGREDOS"] = tempfile.mkdtemp()
from pathlib import Path
import numpy as np
from app import estado, locutor, memoria
from app.audio import TAXA, BLOCO, Segmentador
from app.ouvido import Ouvido, termina_no_meio, espera_continuacao, ESPERA_CONTINUACAO
from app.voz import Voz

def ok(c, nome): print(("OK " if c else "FALHOU ") + nome, flush=True)
def tom(seg, freq=150):
    t = np.arange(int(seg * TAXA)) / TAXA
    return (np.sin(2 * np.pi * freq * t) * 8000).astype(np.int16).tobytes()
def silencio(seg): return bytes(2 * int(seg * TAXA))
def ouvidas(desde): return [x for x in memoria.ouvidas(300) if x.get("ts", 0) >= desde - 0.01]

class Falso:   # "Whisper": devolve as frases do roteiro, na ordem
    def __init__(self, frases): self.frases = list(frases)
    def transcrever(self, audio, **k): return self.frases.pop(0) if self.frases else ""

def voz_simulada(segundos=3.0, geracao_lenta=0.0):
    # Voz de verdade (fila + linha separada + parar), sem som: "tocar" espera `segundos` (ou ate parar()).
    voz = Voz({"voz": {"motor": "kokoro"}}, mudo=False)
    voz.gerados, voz.tocados, voz.cortes = [], [], []
    def gerar(parte):
        time.sleep(geracao_lenta); voz.gerados.append((parte, time.time())); return Path("falso.wav"), False
    def tocar(arquivo):
        g = voz._geracao; voz.tocados.append(time.time()); fim = time.time() + segundos
        while time.time() < fim:
            if g != voz._geracao:
                voz.cortes.append(time.time()); return
            time.sleep(0.01)
    voz._gerar_com_reserva, voz._tocar = gerar, tocar
    return voz

def novo(frases, voz=None, falas=()):
    o = object.__new__(Ouvido)
    o.ganho, o.acordar_tela, o._vigia, o.diagnostico = 1.0, False, None, False
    o.variacoes, o.espera_palavra = ["assessor"], 2.5
    o.verificador = locutor.Verificador(False)
    o.transcritor = Falso(frases)
    o.voz = voz
    o._preparar_laco()
    falas, chamadas = list(falas), []
    def executar(comando, frase, seguimento=False):
        chamadas.append((comando, frase, seguimento))
        if voz is not None and falas:
            voz.falar(falas.pop(0))
        return 8
    seg = Segmentador(500, 0.7)
    def tocar(audio, eco=None):   # (eco=None: como o microfone de verdade, "eco" = ele estava falando)
        for i in range(0, len(audio), BLOCO * 2):
            e = eco if eco is not None else bool(voz is not None and voz.falando.is_set())
            o._bloco(audio[i:i + BLOCO * 2], e, seg, executar)
    estado.atualizar(conversa_ate=0.0, ditado_desde=0.0, descanso=False)
    return o, tocar, chamadas

# --- 1) Fala em segundo plano: o comando volta na hora e a escuta continua -------------------------
inicio = time.time()
voz = voz_simulada(3.0)
o, tocar, ch = novo(["Assessor, que horas são?", "Então tá bom, vou almoçar.", "Assessor, abre o Spotify."],
                    voz=voz, falas=["São dez horas e trinta minutos. Hora de um café."])
t0 = time.time(); tocar(tom(1.0)); tocar(silencio(1.0)); gasto = time.time() - t0
time.sleep(0.2)
ok(len(ch) == 1 and gasto < 1.0 and voz.falando.is_set() and voz.tocados,
   f"Fala em segundo plano: o comando volta na hora e a fala continua tocando ({gasto:.2f}s)")
tocar(tom(1.0), eco=True); tocar(silencio(0.8), eco=True)
reg = ouvidas(inicio)
ok(len(ch) == 1 and voz.falando.is_set() and any(r.get("motivo") == "falando" and r.get("texto", "").startswith("Então")
                                                 for r in reg),
   "Durante a fala: frase sem a palavra é descartada com o motivo 'falando' (e a escuta continua)")
# --- 2) Palavra de ativacao durante a fala: corta o som e executa ----------------------------------
t0 = time.time(); tocar(tom(1.0), eco=True); tocar(silencio(0.8), eco=True)
ok(voz.cortes and not voz.falando.is_set() and voz.cortes[0] - t0 < 0.5,
   "Interromper: 'Assessor, abre o Spotify' durante a fala corta o som na hora")
ok(len(ch) == 2 and ch[1][0] == "abre o spotify" and ch[1][2] is False, f"Interromper: e depois executa o comando {ch}")

inicio = time.time()
voz = voz_simulada(3.0)
o, tocar, ch = novo(["Assessor, que horas são?", "Assessor, para."], voz=voz, falas=["São dez horas. Bom trabalho."])
tocar(tom(1.0)); tocar(silencio(1.0)); time.sleep(0.2)
tocar(tom(0.8), eco=True); tocar(silencio(0.8), eco=True)
ok(voz.cortes and not voz.falando.is_set() and len(ch) == 1
   and any(r.get("motivo") == "interrompeu a fala" for r in ouvidas(inicio)),
   f"Interromper: 'Assessor, para' só para de falar (não vira comando) {ch}")
# a janela de conversa conta do FIM da fala (ele falou 3 s, a janela de 8 s nao pode ter corrido)
voz = voz_simulada(0.6)
o, tocar, ch = novo(["Assessor, que horas são?"], voz=voz, falas=["São dez horas."])
tocar(tom(1.0)); tocar(silencio(1.0)); resto_antes = o._conversa_ate - time.time()
time.sleep(0.4); tocar(silencio(0.2), eco=True)
ok(o._conversa_ate - time.time() >= resto_antes - 0.15, "Janela de conversa não corre enquanto ele fala")
voz.esperar(3)

# --- 3) Frase que termina no meio espera a continuacao ---------------------------------------------
ok(termina_no_meio("Assessor, abre o site do") and termina_no_meio("Eu queria...") and termina_no_meio("Porém, eu gostaria,")
   and not termina_no_meio("Abre o YouTube.") and not termina_no_meio("O que?"),
   "Frase pela metade: vírgula, reticências e 'do/que/e' no fim são reconhecidos")
ok(espera_continuacao({}) == ESPERA_CONTINUACAO and espera_continuacao({"ouvido": {"espera_continuacao": 0}}) == 0,
   "Frase pela metade: config antigo usa a espera padrão (0 desliga)")
inicio = time.time()
o, tocar, ch = novo(["Assessor, abre o site do", "YouTube."])
tocar(tom(1.0)); tocar(silencio(1.0))
ok(ch == [], "Frase terminando em 'do' ainda não foi executada (espera a continuação)")
tocar(tom(0.8)); tocar(silencio(2.0))
ok(ch == [("abre o site do youtube", "Assessor, abre o site do YouTube.", False)],
   f"Frase terminando em 'do' junta com a próxima {ch}")
ok(any(str(r.get("motivo", "")).startswith("terminou no meio") for r in ouvidas(inicio))
   and any(r.get("junto_da_anterior") for r in ouvidas(inicio)), "ouvido.jsonl mostra a espera e a frase juntada")
o, tocar, ch = novo(["Assessor, eu queria...", "que você abrisse o YouTube."])
tocar(tom(1.0)); tocar(silencio(1.5)); tocar(tom(1.2)); tocar(silencio(2.0))
ok(len(ch) == 1 and ch[0][0] == "eu queria que voce abrisse o youtube", f"'Eu queria... que você abrisse o YouTube' = uma ordem só {ch}")
o, tocar, ch = novo(["Assessor, abre o YouTube e"])
tocar(tom(1.0)); tocar(silencio(3.5))
ok(ch == [("abre o youtube e", "Assessor, abre o YouTube e", False)], f"Se a continuação não vem, vai como está {ch}")
o, tocar, ch = novo(["Assessor, abre o YouTube."])
tocar(tom(1.0)); tocar(silencio(1.0))
ok(len(ch) == 1, "Frase completa não espera nada a mais")

# --- 4) Frase a frase: a 1a toca antes de gerar todas; parar corta a fila inteira ------------------
voz = voz_simulada(0.05, geracao_lenta=0.3)
texto = ("Primeira frase bem comprida para passar de quarenta letras. Segunda frase também comprida o bastante "
         "aqui. Terceira frase comprida para fechar o teste de agora.")
voz.falar(texto); voz.esperar(10)
ok(len(voz.gerados) == 3 and voz.tocados and voz.tocados[0] < voz.gerados[-1][1],
   "Frase a frase: a 1ª frase toca antes de gerar todas")
voz = voz_simulada(2.0, geracao_lenta=0.1)
voz.falar(texto); voz.falar("Outra fala que estava na fila esperando a vez dela.")
time.sleep(0.4); voz.parar(); terminou = voz.esperar(2)
ok(terminou and not voz.falando.is_set() and len(voz.gerados) < 4 and voz.cortes,
   f"Interromper corta a fila inteira ({len(voz.gerados)} de 4 partes geradas)")
voz = Voz({"voz": {"motor": "kokoro", "frase_a_frase": False}}, mudo=True)
ok(len(voz.partes(texto)) == 1, "Frase a frase desligado: o texto sai de uma vez")
print("FIM_FALA_FLUIDA")
"""


SEGUIMENTO_ABRIR = r"""
# "abrir" sem a palavra (janela de conversa) so vale se o alvo existir
import logging
from app.config import carregar_config
from app.comandos import Executor
from app.voz import Voz
from app.vocabulario import Vocabulario
ditos = []
class VozTeste(Voz):
    def falar(self, texto): ditos.append(texto)
class SemIA:
    ligado = False
    def esquecer(self): pass
cfg = carregar_config()
ex = Executor(cfg, VozTeste(cfg, mudo=True), SemIA(), Vocabulario())
def ok(c, nome): print(("OK " if c else "FALHOU ") + nome, flush=True)
seg = ex.executar("e colocar isso pra eu ver pelo telegram", "E colocar isso pra eu ver pelo Telegram.", seguimento=True)
ok(not ditos and seg == 0.0, f"Seguimento 'e colocar isso pra eu ver pelo Telegram' sem alvo não abre nem fala nada {ditos}")
ditos.clear()
ex.executar("abre o xyzqwk", "Assessor, abre o xyzqwk")
ok(any("conheço" in d for d in ditos), "Com a palavra, 'abre' sem alvo ainda avisa que não conhece")
print("FIM_SEGUIMENTO_ABRIR")
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


VALIDACAO = r"""
# Validar atualizacao: parser do roteiro, casamento com historico simulado, relatorio e FEEDBACK
import time, traceback, tkinter as tk
from datetime import datetime
from pathlib import Path
from app import validacao as v

def ok(c, nome): print(("OK " if c else "FALHOU ") + nome, flush=True)

ROTEIRO = '''# Roteiro
Texto solto | com barra que nao e tabela

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
itens = v.ler_roteiro(texto=ROTEIRO)
print("ITENS", [(i.secao, i.tipo, i.comandos) for i in itens])
ok(len(itens) == 9, f"Validação: parser acha as 9 linhas do roteiro de teste ({len(itens)})")
ok(itens[0].comandos == ["_cmd_hora_data"] and itens[0].grupo == "Grupo A" and itens[0].secao == "novidades",
   "Validação: frase, grupo, seção e comando esperado")
ok(itens[1].falas == ["Mestre, abre a|b"], "Validação: '|' dentro da crase não quebra a coluna")
ok(itens[2].tipo == "ia" and itens[3].manual and itens[4].tipo == "ignorado", "Validação: tipos IA, painel e ignorado")
ok(itens[5].para_falar("Jarvis") == "Jarvis, vou te mostrar uma nova rotina → Jarvis, cancela a rotina",
   "Validação: várias falas e a palavra de ativação no lugar de Mestre")
ok(itens[6].o_que == "" and itens[6].comandos == [], "Validação: linha quebrada não derruba o parser")
ok(itens[7].tipo == "acordar" and itens[7].secao == "sempre" and itens[8].comandos == ["_cmd_abrir", "_cmd_sites"],
   "Validação: seção Sempre testar, acordar e dois comandos esperados")
ok(len(v.escolher(itens, "Só novidades")) == 7 and len(v.escolher(itens, "Só sempre testar")) == 2,
   "Validação: escolher só novidades / só sempre testar")
reais = v.ler_roteiro()
ok(len(reais) >= 20 and any(i.secao == "novidades" for i in reais) and any(i.secao == "sempre" for i in reais)
   and any("Validar atualização" in (i.frase + i.o_que) for i in reais),
   f"Validação: lê o ROTEIRO_VALIDACAO.md de verdade ({len(reais)} frases, com a linha deste recurso)")

# historico simulado
t0 = 1_000_000.0
hist = [
    {"ts": t0 - 50, "tipo": "comando", "pedido": "velho", "entendi": "velho", "rota": "_cmd_abrir", "resposta": "x"},
    {"ts": t0 + 3, "tipo": "comando", "pedido": "Mestre, que horas são", "entendi": "que horas sao",
     "rota": "_cmd_hora_data", "resposta": "São dez horas."},
]
ouv = [{"ts": t0 - 60, "texto": "antigo", "chamou": True},
       {"ts": t0 + 2, "texto": "Mestre, que horas são?", "chamou": True, "audio": "logs/validacao/a.wav"}]
c = v.capturar(t0, hist, ouv)
ok(c and c["ouvi"] == "Mestre, que horas são?" and c["rota"] == "_cmd_hora_data" and c["fiz"] == "São dez horas."
   and c["audio"] == "logs/validacao/a.wav", f"Validação: pega OUVI/ENTENDI/FIZ depois da frase aparecer ({c})")
ok(v.conferir(itens[0], c) == "ok", "Validação: comando certo sugere ✅")
ok(v.capturar(t0 + 10, hist, ouv) is None, "Validação: nada novo = esperando")
hist2 = hist + [{"ts": t0 + 20, "tipo": "comando", "pedido": "Mestre abre o gmail", "entendi": "abre o gmail",
                 "rota": "ia", "resposta": ""},
                {"ts": t0 + 25, "tipo": "ia virou comando", "pedido": "abre o gmail", "entendi": "abre gmail",
                 "ia_texto": "abre o gmail", "rota": "_cmd_youtube"},
                {"ts": t0 + 26, "tipo": "comando", "pedido": "isso ta errado", "rota": "_cmd_feedback", "resposta": "?"}]
c2 = v.capturar(t0 + 15, hist2, ouv + [{"ts": t0 + 19, "texto": "Mestre, abre o Gmail.", "chamou": True}])
ok(c2["rota"] == "_cmd_youtube" and "IA:" in c2["entendi"] and v.conferir(itens[8], c2) == "falha",
   f"Validação: comando errado (via IA) sugere ❌ e ignora o 'isso tá errado' ({c2})")
ok(v.conferir(itens[4], None) == "ok" and v.conferir(itens[2], {"rota": "ia"}) == "ok"
   and v.conferir(itens[7], {"rota": "saiu do descanso"}) == "ok" and v.conferir(itens[3], c) is None,
   "Validação: ignorado, IA, acordar e painel")
ok(v.conferir(itens[5], {"rota": "rotina falada: cancelou"}) == "ok", "Validação: rota equivalente (rotina falada)")
ok(v.capturar(0, [{"data": "27/09/2026 13:02", "tipo": "comando", "pedido": "x", "rota": "_cmd_abrir"}], []) is not None,
   "Validação: registro antigo (sem ts) também é lido")
ok(v.fala_nova(t0 + 18, ouv + [{"ts": t0 + 30, "texto": "Era pra abrir o Gmail", "chamou": False}])
   == "Era pra abrir o Gmail", "Validação: 'o certo era' falado")

# modo continuo (funcao pura): avanca no ✅, para no ❌, silencio, descartes com o motivo
A = v.avaliar_continuo
ok(A(itens[0], t0, t0 + 4, hist, ouv)["estado"] == "ok", "Contínuo: comando certo = ✅ (avança sozinho)")
r = A(itens[8], t0 + 15, t0 + 40, hist2, ouv + [{"ts": t0 + 19, "texto": "Mestre, abre o Gmail.", "chamou": True}])
ok(r["estado"] == "falha", f"Contínuo: comando errado = ❌ (para) ({r['estado']})")
hia = [{"ts": t0 + 3, "tipo": "comando", "pedido": "Mestre abre o gmail", "entendi": "abre o gmail", "rota": "ia"}]
ok(A(itens[8], t0, t0 + 5, hia, ouv)["estado"] == "esperando" and A(itens[8], t0, t0 + 30, hia, ouv)["estado"] == "falha",
   "Contínuo: caiu na IA espera a IA virar comando antes do ❌")
ok(A(itens[0], t0 + 100, t0 + 105, hist, ouv)["estado"] == "esperando"
   and A(itens[0], t0 + 100, t0 + 100 + v.SILENCIO_SEGUNDOS + 1, hist, ouv)["estado"] == "silencio",
   "Contínuo: nada ouvido em ~15 s = 'não ouvi nada'")
desc = [{"ts": t0 + 200, "texto": "que horas são", "chamou": False, "motivo": "sem a palavra de ativação"},
        {"ts": t0 + 201, "texto": "", "motivo": "curta demais", "descartado": True},
        {"ts": t0 + 202, "texto": "Mestre", "chamou": True, "motivo": "só a palavra: esperando o resto (3.0s)"}]
r = A(itens[0], t0 + 199, t0 + 199 + v.ESPERA_DESCARTE + 4, hist, desc)
ok(r["estado"] == "falha" and [d["motivo"] for d in r["descartes"]] == ["sem a palavra de ativação"]
   and "sem a palavra de ativação" in v.texto_descartes(r["descartes"]),
   f"Contínuo: frase descartada mostra o motivo do ouvido.jsonl ({r['estado']}, {r['descartes']})")
ok(A(itens[0], t0 + 199, t0 + 201, hist, desc)["estado"] == "esperando", "Contínuo: descarte espera um pouco (a certa pode vir)")
ign = [{"ts": t0 + 300, "texto": "Mestre, toca o vídeo", "chamou": False, "motivo": "sem a palavra de ativação"}]
ok(A(itens[4], t0 + 299, t0 + 305, [], ign)["estado"] == "ok"
   and A(itens[4], t0 + 299, t0 + 305, [{"ts": t0 + 301, "tipo": "comando", "pedido": "x", "rota": "_cmd_youtube"}],
         ign)["estado"] == "falha", "Contínuo: frase que deve ser ignorada (✅ se nada rodou, ❌ se rodou)")
um = [{"ts": t0 + 401, "tipo": "comando", "pedido": "a", "rota": "_cmd_ensinar_rotina", "resposta": "?"}]
dois = um + [{"ts": t0 + 405, "tipo": "comando", "pedido": "b", "rota": "rotina falada: cancelou", "resposta": "ok"}]
ok(A(itens[5], t0 + 400, t0 + 403, um, [])["estado"] == "esperando" and A(itens[5], t0 + 400, t0 + 407, dois, [])["estado"] == "ok",
   "Contínuo: frase em duas partes (A → B) espera a segunda")
ok(len(v.para_continuo(itens)) == len(itens) - 1 and len(v.para_continuo(itens, True)) == len(itens),
   "Contínuo: linhas (painel)/(visual) ficam fora por padrão (opção para incluir)")

# sessao, relatorio e FEEDBACK (numa copia do MELHORIAS)
s = v.Sessao(itens[:3] + [itens[8]], "Tudo")
s.marcar("ok", c, "ok")
s.marcar("pulado")
s.mostrar(1); s.marcar("ok", {"rota": "ia"}, "ok")
s.marcar("ok", {"rota": "ia"}, "ok")
s.marcar("falha", c2, "falha", "abrir o Gmail no navegador")
ok(s.acabou and len(s.resultados) == 4 and s.resultados[1]["veredito"] == "ok",
   "Validação: sessão anda, volta (Anterior) e termina")
pasta = Path("exportacoes_teste")
rel = v.gerar_relatorio(s, "Jarvis", agora=datetime(2026, 9, 27, 14, 5), pasta=pasta)
texto = rel.read_text(encoding="utf-8")
ok(rel.name == "validacao_2026-09-27_1405.md" and "**3 ok**" in texto and "**1 falhas**" in texto
   and "abrir o Gmail no navegador" in texto and "_cmd_youtube" in texto and "Mestre, abre o Gmail." in texto,
   "Validação: relatório com resumo e a falha (ouvi, entendi, fiz, esperado, o certo era)")
ok(v.ultimo_relatorio(pasta) == rel, "Validação: ultimo_relatorio() acha o relatório")
copia = Path("MELHORIAS_copia.md"); copia.write_text("# Melhorias\n- [ ] ideia velha", encoding="utf-8")
linhas = v.salvar_feedbacks(s, copia, agora=datetime(2026, 9, 27))
m = copia.read_text(encoding="utf-8")
ok(len(linhas) == 1 and "- [ ] ideia velha\n- [ ] (27/09/2026) FEEDBACK: ouvi \"Mestre, abre o Gmail.\" · entendi \"" in m
   and "· respondi \"(não falou nada)\" · o certo era: abrir o Gmail no navegador" in m,
   "Validação: cada ❌ vira FEEDBACK no MELHORIAS.md (formato do CLAUDE.md)")
s3 = v.Sessao(itens[:1]); s3.marcar("falha", c, "ok", "")
ok("[áudio: logs/validacao/a.wav]" in v.linha_feedback(itens[0], s3.resultados[0]), "Validação: FEEDBACK leva o áudio")

# audio so com a validacao ligada
v.ligar_audio(False)
ok(v.guardar_audio(b"\0\0" * 1600) == "", "Validação: sem a página aberta não guarda áudio")
v.ligar_audio(True)
cam = v.guardar_audio(b"\0\0" * 1600)
ok(cam.startswith("logs/validacao/") and Path(cam).exists(), f"Validação: com a página aberta guarda o áudio ({cam})")
v.ligar_audio(False)

# painel: a pagina abre e acompanha o historico (arquivos de memoria da copia)
erros = []
tk.Tk.report_callback_exception = lambda self, e, vv, tb: erros.append("".join(traceback.format_exception(e, vv, tb)))
from app import memoria
import app.painel as p
pn = p.Painel(); pn.update()
pn.mostrar_pagina("Melhorias"); pn.update()   # (caixa da Melhorias aberta: o FEEDBACK tem de entrar nela)
pn.mostrar_pagina("Validar atualização"); pn.update()
pn.var_val_escolha.set("Só sempre testar")
pn.var_val_continuo.set(False)   # o modo de antes (com clique) continua existindo
pn._val_comecar(); pn.update()
item = pn._val.atual
ok(pn.rot_val_frase.cget("text").startswith("Fale:") and v.ARQUIVO_ATIVA.exists(),
   "Validação: página abre e mostra a 1ª frase " + repr(pn.rot_val_frase.cget("text")))
time.sleep(0.05)
memoria.ouvido(item.para_falar("Mestre"), chamou=True)
memoria.registrar(item.para_falar("Mestre"), "Rodando a rotina.", "comando",
                  {"entendi": "bom dia", "rota": item.comandos[0] if item.comandos else "ia"})
pn._val_vigiar(); pn.update()
print("TELA", pn.rot_val_linhas["entendi"].cget("text"), "|", pn.rot_val_sugestao.cget("text"))
ok(pn._val_sugestao == "ok" and "Rodando a rotina." in pn.rot_val_linhas["fiz"].cget("text"),
   "Validação: painel mostra OUVI/ENTENDI/FIZ e sugere ✅")
pn._val_marcar("ok"); pn.update()
pn._val_errado(); pn.update()
pn.ent_val_certo.insert(0, "era outra coisa"); pn._val_confirmar_erro(); pn.update()
pn._val_repetir(); pn._val_marcar("pulado"); pn._val_anterior(); pn.update()
pn._val_parar(); pn.update()
rel = v.ultimo_relatorio()
caixa = pn.txt_melhorias.get("1.0", "end")
ok(rel is not None and "era outra coisa" in rel.read_text(encoding="utf-8") and "FEEDBACK:" in caixa
   and "era outra coisa" in caixa and "era outra coisa" in Path("MELHORIAS.md").read_text(encoding="utf-8")
   and not v.ARQUIVO_ATIVA.exists(),
   "Validação: Parar gera o relatório e o FEEDBACK (arquivo e caixa da página Melhorias)")
ok(not erros, "Validação: página sem erros na tela" + ("".join(erros)[-800:] if erros else ""))

# "Mandar para o Claude corrigir": pedido, arquivo salvo e comando (sem -p, sem flag de permissao)
ok(pn.bt_val_claude.cget("state") == "normal",
   "Validação: botão 'Mandar para o Claude corrigir' ativo (o último relatório tem falha)")
pn._val_mandar_claude(); pn.update()
pedidos = sorted(Path("exportacoes").glob("pedido_correcao_*.md"))
ok(bool(pedidos), "Validação: pedido de correção salvo em exportacoes/")
texto_pedido = pedidos[-1].read_text(encoding="utf-8") if pedidos else ""
ok(texto_pedido.startswith("Corrija as falhas do relatório de validação exportacoes/validacao_")
   and "corrigir-transcricao/refinar não são necessários" in texto_pedido and "/entregar" in texto_pedido,
   f"Validação: pedido de correção no texto certo ({texto_pedido[:90]!r})")
cmd = pn._val_ultimo_comando_claude
ok(cmd is not None and "-p" not in cmd
   and not any("--dangerously" in c or "--permission" in c for c in cmd)
   and cmd[-1].startswith("Leia o arquivo exportacoes/pedido_correcao_") and not any(ch in cmd[-1] for ch in ';"&|'),
   f"Validação: comando do Claude interativo, sem -p/flags de permissão ({cmd})")

avisos = []
p.messagebox.showinfo = lambda *a, **k: avisos.append(a)
v.comando_para_abrir_claude = lambda pedido: None
pn._val_mandar_claude(); pn.update()
ok(pn._val_ultimo_comando_claude is None and avisos,
   "Validação: Claude Code não encontrado avisa o usuário e copia o pedido")

rel_ok = v.gerar_relatorio(v.Sessao([]), "Jarvis", agora=datetime(2099, 1, 1, 0, 0), pasta=Path("exportacoes"))
ok(not v.relatorio_tem_falhas(rel_ok), "Validação: relatorio_tem_falhas() é False sem falha nenhuma")
pn._val_atualizar_botao_claude(); pn.update()
ok(pn.bt_val_claude.cget("state") == "disabled",
   "Validação: botão 'Mandar para o Claude corrigir' desativado sem falhas no relatório")


# modo continuo no painel: avanca sozinho no ✅ e para no ❌ (historico simulado)
def esperar(seg):
    fim = time.time() + seg
    while time.time() < fim:
        pn.update(); time.sleep(0.05)

v.ler_roteiro = lambda *a, **k: list(itens)
pn.var_val_escolha.set("Só novidades"); pn.var_val_continuo.set(True); pn.var_val_manuais.set(False)
pn._val_comecar(); pn.update()
ok(len(pn._val.itens) == 6 and not any(v.manual(i) for i in pn._val.itens),
   f"Contínuo (painel): começa sem as linhas de painel ({len(pn._val.itens)} frases)")
time.sleep(0.05)
memoria.ouvido("Mestre, que horas são?", chamou=True)
memoria.registrar("Mestre, que horas são?", "São dez horas.", "comando", {"entendi": "que horas sao", "rota": "_cmd_hora_data"})
pn._val_vigiar_continuo(pn._val, pn._val.atual); pn.update()
ok(pn._val_estado == "ok" and "Deu certo" in pn.rot_val_sugestao.cget("text"), "Contínuo (painel): ✅ sozinho, sem clique")
esperar(v.AVANCO_SEGUNDOS + 0.4)
ok(pn._val.indice == 1 and pn._val.resultados[0]["veredito"] == "ok", "Contínuo (painel): passou para a próxima frase sozinho")
time.sleep(0.05)
memoria.ouvido("Mestre, abre a b", chamou=True)
memoria.registrar("Mestre, abre a b", "Abrindo o YouTube.", "comando", {"entendi": "abre a b", "rota": "_cmd_youtube"})
pn._val_vigiar_continuo(pn._val, pn._val.atual); pn.update()
esperar(v.AVANCO_SEGUNDOS + 0.4)
destaque = {k: r.cget("text") for k, (_, r) in pn.rot_val_destaque.items()}
ok(pn._val_estado == "falha" and pn._val.indice == 1 and bool(pn.fr_val_destaque.winfo_manager())
   and "_cmd_youtube" in destaque["entendi"] and "abre a b" in destaque["ouvi"] and "YouTube" in destaque["fiz"],
   f"Contínuo (painel): parou no ❌ e mostra OUVI → ENTENDI → FIZ em destaque ({destaque})")
pn._val_marcar("pulado"); pn.update()
ok(pn._val.indice == 2 and not pn.fr_val_destaque.winfo_manager() and pn._val_estado in ("", "esperando"),
   "Contínuo (painel): Pular segue para a próxima e esconde o destaque")
time.sleep(0.05)
memoria.ouvido("o que é um buraco negro", chamou=False, conversa=False, motivo="sem a palavra de ativação")
pn._val.exibida_em -= v.ESPERA_DESCARTE + 1
pn._val_vigiar_continuo(pn._val, pn._val.atual); pn.update()
destaque = pn.rot_val_destaque["descartes"][1].cget("text")
ok(pn._val_estado == "falha" and "sem a palavra de ativação" in destaque,
   f"Contínuo (painel): frase descartada mostra o motivo ({pn._val_estado}, {destaque!r})")
pn._val_errado(); pn.ent_val_certo.insert(0, "era pra pensar"); pn._val_confirmar_erro(); pn.update()
ok("sem a palavra de ativação" in pn._val.resultados[2]["captura"].get("descartado", ""),
   "Contínuo (painel): o ❌ leva o motivo do descarte para o relatório")
pn._val_parar(); pn.update()
ok(pn._val is None and "Descartado pelo ouvido" in pn._val_relatorio.read_text(encoding="utf-8"),
   "Contínuo (painel): relatório com o motivo do descarte")
ok(not erros, "Contínuo (painel): sem erros na tela" + ("".join(erros)[-800:] if erros else ""))

pn._fechar()
print("FIM_VALIDACAO")
"""

AVISOS_PC = r"""
# Avisos do PC (liga/desliga pelo Telegram): logica pura de decidir a mensagem, com arquivos falsos
import os, tempfile
os.environ["MESTRE_SEGREDOS"] = tempfile.mkdtemp()
from datetime import datetime, timedelta
from app import avisos_pc as ap

def ok(c, nome): print(("OK " if c else "FALHOU ") + nome, flush=True)

agora = datetime(2026, 9, 28, 9, 0, 0)
boot_a = datetime(2026, 9, 28, 7, 0, 0)
boot_b = datetime(2026, 9, 28, 8, 30, 0)   # boot DIFERENTE (o PC religou entre os dois)

ok(ap.mesmo_boot(boot_a, boot_a + timedelta(seconds=2)), "mesmo_boot: poucos segundos de diferenca ainda conta")
ok(not ap.mesmo_boot(boot_a, boot_b), "mesmo_boot: boots bem diferentes nao contam")
ok(not ap.mesmo_boot(None, boot_a) and not ap.mesmo_boot(boot_a, None), "mesmo_boot: sem hora nenhuma = nao e o mesmo boot")

# 1) primeira vez (nunca gravou batimento): so comeca a registrar, sem avisar nada
sit, txt = ap.decidir_aviso_ligou(boot_a, {"hora": None, "boot": None}, {"boot": None, "hora": None})
ok(sit == "primeira_vez" and txt == "", f"decidir_aviso_ligou: primeira vez nao avisa nada ({sit!r})")

# 2) mesmo boot (so o Assessor reiniciou sozinho): nao avisa nada
sit, txt = ap.decidir_aviso_ligou(boot_a, {"hora": agora, "boot": boot_a}, {"boot": None, "hora": None})
ok(sit == "mesmo_boot" and txt == "", f"decidir_aviso_ligou: Assessor reiniciou sozinho nao avisa ({sit!r})")

# 3) boot novo, desligou limpo daquele boot anterior: "PC ligou"
sit, txt = ap.decidir_aviso_ligou(boot_b, {"hora": agora, "boot": boot_a}, {"boot": boot_a, "hora": agora})
ok(sit == "normal" and "PC ligou" in txt, f"decidir_aviso_ligou: desligou limpo -> PC ligou ({sit!r}, {txt!r})")

# 4) boot novo, SEM marca de desligou limpo (ou de um boot antigo demais): desligou sem avisar
sit, txt = ap.decidir_aviso_ligou(boot_b, {"hora": agora, "boot": boot_a}, {"boot": None, "hora": None})
ok(sit == "inesperado" and "sem avisar" in txt and "09:00" in txt and "28/09" in txt,
   f"decidir_aviso_ligou: sem marca -> desligou sem avisar, com o ultimo sinal ({sit!r}, {txt!r})")

# 5) boot novo, marca de um boot ANTIGO (nao do anterior): tambem e inesperado
sit, txt = ap.decidir_aviso_ligou(boot_b, {"hora": agora, "boot": boot_a},
                                   {"boot": boot_a - timedelta(days=1), "hora": agora - timedelta(days=1)})
ok(sit == "inesperado", f"decidir_aviso_ligou: marca de outro boot nao vale ({sit!r})")

# 6) mesmo com a marca certa, o Log de Eventos mostrando queda tambem vira inesperado
sit, txt = ap.decidir_aviso_ligou(boot_b, {"hora": agora, "boot": boot_a}, {"boot": boot_a, "hora": agora},
                                   houve_queda=True)
ok(sit == "inesperado", f"decidir_aviso_ligou: log com queda de energia vira inesperado mesmo com marca ({sit!r})")

# batimento e "desligou limpo": grava e le de volta (arquivos de verdade, na pasta logs/ da copia do teste)
ap.bater(boot_a)
lido = ap.ler_batimento()
ok(ap.mesmo_boot(lido["boot"], boot_a) and lido["hora"] is not None, f"bater/ler_batimento: ida e volta ({lido})")

ap.marcar_desligou_limpo(boot_a)
limpo = ap.ler_desligou_limpo()
ok(ap.mesmo_boot(limpo["boot"], boot_a) and limpo["hora"] is not None, f"marcar/ler_desligou_limpo: ida e volta ({limpo})")

# sem token/chat do Telegram: nao tenta mandar nada, nao trava, devolve False
ok(ap.avisar_telegram("teste") is False, "avisar_telegram: sem chat configurado, so devolve False (nao trava)")

# hora do boot: tem que ser no passado e perto de "agora - tempo ligado" (so confere que nao quebra)
hb = ap.hora_boot()
ok(hb < datetime.now(), f"hora_boot: devolve uma hora no passado ({hb})")

# pulso do healthchecks: desligado por padrao, e sem URL nao tenta mandar nada
ok(ap.pulso_healthchecks({}) is False, "pulso_healthchecks: desligado por padrao, nao manda nada")
ok(ap.pulso_healthchecks({"avisos_pc": {"healthchecks_ligado": True, "healthchecks_url": ""}}) is False,
   "pulso_healthchecks: ligado mas sem URL, nao manda nada")

print("FIM_AVISOS_PC")
"""

SUGESTOES = r"""
# Sugestoes de melhoria: analise com historico/ouvido sinteticos, agendamento e a pagina do painel
import json, time, traceback, tkinter as tk
from datetime import datetime, timedelta
from pathlib import Path
from app import sugestoes as sg

def ok(c, nome): print(("OK " if c else "FALHOU ") + nome, flush=True)

# agendamento
d = datetime(2026, 9, 28)
P = sg.proxima_execucao
ok(sg.hora_config("8h30") == (8, 30) and sg.hora_config("7") == (7, 0) and sg.hora_config("xx") == (8, 0)
   and sg.hora_texto("9:05") == "09:05", "Sugestões: horário do config (08:00, 8h30, inválido = 08:00)")
ok(P("08:00", (d.replace(hour=8, minute=1)).timestamp(), d.replace(hour=10)) == (d + timedelta(days=1)).replace(hour=8),
   "Sugestões: já rodou hoje = amanhã às 8h")
ok(P("08:00", (d - timedelta(days=1)).replace(hour=8, minute=5).timestamp(), d.replace(hour=7)) == d.replace(hour=8),
   "Sugestões: antes das 8h = hoje às 8h")
ok(P("08:00", (d - timedelta(days=1)).replace(hour=8, minute=5).timestamp(), d.replace(hour=9, minute=30))
   == d.replace(hour=9, minute=30), "Sugestões: PC desligado às 8h = roda na próxima abertura")
ok(P("08:00", None, d.replace(hour=7)) == d.replace(hour=7), "Sugestões: nunca rodou = roda já")
ag = sg.Agendador({"sugestoes": {"hora": "08:00"}})
hoje = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
sg.ARQUIVO_SUGESTOES.unlink(missing_ok=True)
ok(ag.passo(hoje) and not ag.passo(hoje + timedelta(hours=2)) and ag.passo(hoje + timedelta(days=1)),
   "Sugestões: agendador roda 1x por dia (e não de novo no mesmo dia)")
ok(sg.configuracao({}) == (True, "08:00"), "Sugestões: sem config = ligado às 08:00")

# analise
agora = datetime(2026, 9, 28, 9, 0).timestamp()
t = agora - 3600
ouv = [
    {"ts": agora - 90000, "texto": "", "motivo": "curta demais"},                          # antes da janela
    {"ts": t, "texto": "", "motivo": "curta demais", "descartado": True},
    {"ts": t + 5, "texto": "", "motivo": "curta demais", "descartado": True},
    {"ts": t + 9, "texto": "Assessor, abre o Spotify", "motivo": "voz não reconhecida", "voz_nao_reconhecida": 0.3},
    {"ts": t + 12, "texto": "Acessor, abre o YouTube", "chamou": False, "motivo": "sem a palavra de ativação"},
    {"ts": t + 14, "texto": "tá bom então", "chamou": False, "motivo": "sem a palavra de ativação"},
    {"ts": t + 16, "texto": "Assessor", "chamou": True, "motivo": "só a palavra: esperando o resto (3.0s)"},
]
hist = [
    {"ts": agora - 90000, "tipo": "comando", "pedido": "Assessor, bota um rock", "rota": "_cmd_spotify"},
    {"ts": t + 20, "tipo": "comando", "pedido": "Assessor, abre o bloco de notas", "entendi": "abre o bloco de notas", "rota": "ia"},
    {"ts": t + 30, "tipo": "ia virou comando", "pedido": "abre o bloco de notas", "rota": "_cmd_abrir"},
    {"ts": t + 40, "tipo": "comando", "pedido": "Assessor, o que é um buraco negro", "entendi": "o que e um buraco negro", "rota": "ia"},
    {"ts": t + 50, "tipo": "comando", "pedido": "Assessor, faz aquele negócio", "entendi": "faz aquele negocio", "rota": "nao_entendi"},
    {"ts": t + 60, "tipo": "comando", "pedido": "Assessor, toca a playlist rock", "entendi": "toca a playlist rock", "rota": "_cmd_spotify"},
    {"ts": t + 70, "tipo": "comando", "pedido": "Assessor, toca a playlist rock", "entendi": "toca a playlist rock", "rota": "_cmd_spotify"},
    {"ts": t + 200, "tipo": "comando", "pedido": "Assessor, aumenta o volume", "entendi": "aumenta o volume", "rota": "_cmd_volume"},
    {"ts": t + 205, "tipo": "comando", "pedido": "Assessor, aumenta o volume", "entendi": "aumenta o volume", "rota": "_cmd_volume"},
    {"ts": t + 300, "tipo": "comando", "pedido": "Assessor, bota um rock", "entendi": "bota um rock", "rota": "_cmd_spotify"},
    {"ts": t + 310, "tipo": "comando", "pedido": "Assessor, isso tá errado", "rota": "_cmd_feedback"},
]
lista = sg.analisar(hist, ouv, agora - 86400, "assessor", ["assessor", "assessores"], frases_conhecidas="")
ids = [x["id"] for x in lista]
print("IDS", ids)
esperados = {"descartada:curta demais", "descartada:voz nao reconhecida", "palavra:acessor", "ia:abre",
             "nao_entendi:geral", "repetido:geral", "variacao:_cmd_spotify", "variacao:_cmd_volume"}
ok(set(ids) == esperados, f"Sugestões: análise acha o esperado ({ids})")
por = {x["id"]: x for x in lista}
ok(por["descartada:curta demais"]["quantas"] == 2, "Sugestões: descartes agrupados por motivo (fora da janela não conta)")
ok("_cmd_abrir" in por["ia:abre"]["evidencias"][0]["info"] and por["ia:abre"]["quantas"] == 1,
   "Sugestões: caiu na IA com cara de comando (e o que a IA fez depois); pergunta de verdade não entra")
ok(por["repetido:geral"]["quantas"] == 1, "Sugestões: repetido logo em seguida (volume repetido é normal)")
ok([e["frase"] for e in por["variacao:_cmd_spotify"]["evidencias"]] == ["Assessor, toca a playlist rock"],
   "Sugestões: jeito novo de falar (o já visto antes não conta)")
ok(sg.analisar(hist, ouv, agora - 86400, "assessor", ["assessor"], frases_conhecidas="toca a playlist rock")
   and "variacao:_cmd_spotify" not in [x["id"] for x in sg.analisar(hist, ouv, agora - 86400, "assessor", ["assessor"],
                                                                      frases_conhecidas="Mestre, toca a playlist rock")],
   "Sugestões: frase que já está em testes/frases.py não vira sugestão")
arq = Path("memoria/sugestoes_teste.json")
dados = sg.rodar({"assistente": {"palavra_ativacao": "Assessor"}}, agora=agora, historico=hist, ouvidas=ouv, arquivo=arq)
salvo = json.loads(arq.read_text(encoding="utf-8"))
ids_salvos = {x["id"] for x in salvo["sugestoes"]}   # (o frases.py de verdade ja tem "aumenta o volume")
ok(salvo["ts"] == round(agora, 2) and ids_salvos <= esperados and len(ids_salvos) >= len(esperados) - 1 and salvo["desde"] == round(agora - 86400, 2),
   "Sugestões: grava memoria/sugestoes.json (últimas 24 h)")
dados2 = sg.rodar({}, agora=agora + 3 * 86400, historico=hist, ouvidas=ouv, arquivo=arq)
ok(dados2["desde"] == round(agora, 2), "Sugestões: PC desligado dias = olha desde a última análise")
pedido = sg.pedido_para_claude([por["ia:abre"], por["palavra:acessor"]], "28/09/2026 09:00", "Jarvis")
ok("Jarvis" in pedido and "abre o bloco de notas" in pedido and "sem a palavra de ativação" in pedido
   and "/entregar" in pedido, "Sugestões: pedido leva as marcadas com as evidências (frases, horários, motivos)")

class IAFalsa:
    tipo, ligado = "ollama", True
    def _ollama(self, sistema, mensagens, formato=None): return "Resumo: corrigir a palavra."
ok(sg.resumir_com_ia(IAFalsa(), dict(dados2, sugestoes=dados["sugestoes"]), arq) == "Resumo: corrigir a palavra."
   and sg.ler(arq)["resumo_ia"] == "Resumo: corrigir a palavra.", "Sugestões: IA ligada resume (em segundo plano)")

# Aplicar (vocabulario/sinonimo, sem IA) -----------------------------------------------
from app.vocabulario import Vocabulario
Path("aprendido.yaml").unlink(missing_ok=True)   # copia do teste: nunca mexe no aprendido.yaml de verdade

troca = sg.troca_da_sugestao(por["palavra:acessor"], "assessor")
ok(troca == ("acessor", "assessor"), f"Sugestões: troca_da_sugestao extrai (jeito, oficial) ({troca})")
ok(sg.troca_da_sugestao(por["ia:abre"], "assessor") is None,
   "Sugestões: só o tipo palavra tem troca automática (os outros continuam só pro Claude)")

v = Vocabulario()
pode, motivo = v.pode_aplicar_sinonimo("acessor", "assessor")
ok(pode and not motivo, "Vocabulário: pode aplicar uma troca válida")
ok(not v.pode_aplicar_sinonimo("", "assessor")[0], "Vocabulário: recusa palavra vazia")
ok(not v.pode_aplicar_sinonimo("ok", "assessor")[0], "Vocabulário: recusa palavra curta demais (<3 letras)")
ok(not v.pode_aplicar_sinonimo("assessor", "abre", protegidas=["assessor", "assessores"])[0],
   "Vocabulário: recusa trocar a própria palavra de ativação")
ok(not v.pode_aplicar_sinonimo("mestre", "mestre")[0], "Vocabulário: recusa trocar uma palavra por ela mesma")

aplicou, msg = v.aplicar_sinonimo("acessor", "assessor")
ok(aplicou and "acessor" in (v.aprendido.get("sinonimos") or {}).get("assessor", []),
   f"Vocabulário: Aplicar grava o sinônimo em aprendido.yaml ({msg})")
aprendido_disco = Path("aprendido.yaml").read_text(encoding="utf-8")
ok("sinonimos" in aprendido_disco and "acessor" in aprendido_disco,
   "Vocabulário: aprendido.yaml no disco tem a troca")
v2 = Vocabulario()   # recarrega do disco, como o Assessor faria
ok(v2.traduzir("acessor") == "assessor", "Vocabulário: depois de Aplicar, o vocabulário já traduz a palavra")
ok(not v2.pode_aplicar_sinonimo("acessor", "assessor")[0],
   "Vocabulário: recusa aplicar de novo uma troca que já existe")

sg._gravar(dict(dados), arq)   # dados2 (3 dias depois) tinha sobrescrito arq com uma lista vazia
sg.marcar_aplicada("palavra:acessor", "acessor", "assessor", arquivo=arq, no_config=True)
marcada = next(s for s in sg.ler(arq)["sugestoes"] if s["id"] == "palavra:acessor")
ok(marcada.get("aplicada") is True, "Sugestões: marcar_aplicada marca a sugestão no arquivo")
u = sg.ultima_aplicacao(arq)
ok(u["id"] == "palavra:acessor" and u["jeito"] == "acessor" and u["oficial"] == "assessor" and u.get("quando")
   and u.get("no_config") is True, "Sugestões: fica no histórico para o Desfazer (com no_config)")

ok(v2.desfazer_sinonimo("acessor", "assessor"), "Vocabulário: Desfazer tira o sinônimo do aprendido.yaml")
v3 = Vocabulario()
ok(v3.traduzir("acessor") == "acessor", "Vocabulário: depois de desfazer, a palavra não traduz mais")
desfeita = sg.desfazer_ultima_aplicacao(arq)
ok(desfeita["id"] == "palavra:acessor", "Sugestões: desfazer_ultima_aplicacao devolve a última aplicação")
volta = next(s for s in sg.ler(arq)["sugestoes"] if s["id"] == "palavra:acessor")
ok("aplicada" not in volta, "Sugestões: depois de desfazer, a sugestão volta a aparecer na lista")
ok(sg.desfazer_ultima_aplicacao(arq) is None, "Sugestões: sem mais nada para desfazer (histórico vazio)")

# Aplicar tambem faz ele ACORDAR com a pronuncia (config.yaml > assistente > variacoes_aceitas) --------
from app import configuracao
from app.texto import extrair_comando

variacoes_antes = sg._palavra_do_config(configuracao.carregar())[1]
ok("acesor" not in variacoes_antes, "Config: antes de aplicar, 'acesor' não está nas variações aceitas")
achou0, _ = extrair_comando("acesor, que horas sao", variacoes_antes)
ok(not achou0, "Ouvido: antes de aplicar, 'acesor, que horas são' não acorda o assistente")

ok(configuracao.adicionar_variacao_aceita("acesor"), "Config: adicionar_variacao_aceita acrescenta a grafia")
ok(not configuracao.adicionar_variacao_aceita("acesor"), "Config: não duplica se já está lá")
variacoes_depois = sg._palavra_do_config(configuracao.carregar())[1]
ok("acesor" in variacoes_depois, "Config: depois de aplicar, 'acesor' entra nas variações aceitas")
achou1, comando1 = extrair_comando("acesor, que horas sao", variacoes_depois)
ok(achou1 and comando1 == "que horas sao",
   f"Ouvido: depois de aplicar, aceita 'acesor, que horas são' ({achou1}, {comando1!r})")

ok(configuracao.remover_variacao_aceita("acesor"), "Config: remover_variacao_aceita (Desfazer) tira a grafia")
variacoes_final = sg._palavra_do_config(configuracao.carregar())[1]
ok("acesor" not in variacoes_final, "Config: depois de desfazer, 'acesor' sai das variações aceitas")
achou2, _ = extrair_comando("acesor, que horas sao", variacoes_final)
ok(not achou2, "Ouvido: depois de desfazer, 'acesor' não acorda mais o assistente")

# painel
erros = []
tk.Tk.report_callback_exception = lambda self, e, vv, tb: erros.append("".join(traceback.format_exception(e, vv, tb)))
muitas = [{"id": f"ia:v{i}", "tipo": "ia", "titulo": f"Sugestão {i}", "detalhe": "d", "quantas": 1,
           "evidencias": [{"data": "28/09 08:00", "frase": f"frase {i}", "info": "motivo x"}]} for i in range(20)]
sg._gravar({"gerado_em": "28/09/2026 08:00", "ts": 123.0, "desde_texto": "27/09/2026 08:00", "automatica": True,
            "sugestoes": muitas, "resumo_ia": ""}, sg.ARQUIVO_SUGESTOES)
import app.painel as p
pn = p.Painel(); pn.update()
pn.mostrar_pagina("Sugestões de melhoria"); pn.update()
visiveis = [l for l in pn._sug_linhas if l["frame"].winfo_manager()]
ok(len(pn._sug_linhas) == 8 and len(visiveis) == 8 and pn.rot_sug_pagina.cget("text") == "Página 1 de 3",
   f"Sugestões (painel): página abre com 20 sugestões em páginas de 8 ({pn.rot_sug_pagina.cget('text')})")
ok(pn.bt_sug_claude.cget("state") == "disabled", "Sugestões (painel): botão do Claude desativado sem nada marcado")
l0 = pn._sug_linhas[0]; l0["var"].set(True); pn._sug_alternar(l0)
pn._sug_ir(1); pn._sug_ir(1); pn.update()
l1 = pn._sug_linhas[0]; l1["var"].set(True); pn._sug_alternar(l1)
visiveis = [l for l in pn._sug_linhas if l["frame"].winfo_manager()]
ok(len(visiveis) == 4 and pn._sug_marcadas == {"ia:v0", "ia:v16"}, "Sugestões (painel): marcar em páginas diferentes")
pn._sug_mandar_claude(); pn.update()
arquivos = sorted(Path("exportacoes").glob("pedido_sugestoes_*.md"))
texto = arquivos[-1].read_text(encoding="utf-8") if arquivos else ""
cmd = pn._sug_ultimo_comando_claude
ok(arquivos and "frase 0" in texto and "frase 16" in texto and "frase 5" not in texto,
   "Sugestões (painel): pedido com as marcadas salvo em exportacoes/")
ok(cmd is None or (cmd[-1].startswith("Leia o arquivo exportacoes/pedido_sugestoes_") and "-p" not in cmd),
   f"Sugestões (painel): mesmo fluxo supervisionado do Claude, nada abre no teste ({cmd})")

# botão Aplicar (só tipo "palavra") ------------------------------------------------------
sg._gravar({"gerado_em": "28/09/2026 08:30", "ts": 456.0, "desde_texto": "27/09/2026 08:30", "automatica": True,
            "sugestoes": [
                {"id": "palavra:acesor", "tipo": "palavra",
                 "titulo": "O Whisper escreveu a palavra de ativação como “acesor” (3x)", "detalhe": "d", "quantas": 3,
                 "evidencias": [{"data": "28/09 08:00", "frase": "acesor abre o youtube",
                                "info": "sem a palavra de ativação"}]},
                {"id": "ia:v0", "tipo": "ia", "titulo": "Sugestão 0", "detalhe": "d", "quantas": 1,
                 "evidencias": [{"data": "28/09 08:00", "frase": "frase 0", "info": "motivo x"}]},
            ], "resumo_ia": ""}, sg.ARQUIVO_SUGESTOES)
pn._sug_recarregar(); pn.update()
l0, l1 = pn._sug_linhas[0], pn._sug_linhas[1]
ok(l0["id"] == "palavra:acesor" and bool(l0["aplicar"].winfo_manager()),
   "Sugestões (painel): botão Aplicar aparece na sugestão de vocabulário")
ok(l1["id"] == "ia:v0" and not l1["aplicar"].winfo_manager(),
   "Sugestões (painel): sem Aplicar nos outros tipos (continuam só indo pro Claude)")

perguntas, avisos = [], []
p.messagebox.askyesno = lambda *a, **k: perguntas.append(a) or True
p.messagebox.showwarning = lambda *a, **k: avisos.append(a)
palavra_oficial = sg.normalizar(pn.palavra)   # a palavra do config da copia de teste (ex.: "jarvis")
pn._sug_aplicar({"id": "palavra:acesor", "tipo": "palavra"}); pn.update()
ok(perguntas and "acesor" in perguntas[0][1] and palavra_oficial in perguntas[0][1],
   f"Sugestões (painel): mostra a troca exata antes de aplicar ({perguntas})")
ok("palavra:acesor" not in [l["id"] for l in pn._sug_linhas if l["frame"].winfo_manager()],
   "Sugestões (painel): depois de aplicar, some da lista")
v4 = Vocabulario()
ok(v4.traduzir("acesor") == palavra_oficial,
   "Sugestões (painel): Aplicar realmente grava no vocabulário (aprendido.yaml)")
variacoes_pos_aplicar = sg._palavra_do_config(configuracao.carregar())[1]
achou_pos, comando_pos = extrair_comando("acesor, que horas sao", variacoes_pos_aplicar)
ok("acesor" in variacoes_pos_aplicar and achou_pos and comando_pos == "que horas sao",
   "Sugestões (painel): Aplicar também acorda com essa pronúncia (config.yaml > variações aceitas)")
ok(pn.bt_sug_desfazer.cget("state") == "normal", "Sugestões (painel): Desfazer fica disponível depois de aplicar")

pn._sug_aplicar({"id": "palavra:acesor", "tipo": "palavra"}); pn.update()
ok(len(avisos) >= 1, "Sugestões (painel): aplicar de novo a mesma troca é recusado (já existe/já aplicada)")

pn._sug_desfazer(); pn.update()
v5 = Vocabulario()
ok(v5.traduzir("acesor") == "acesor", "Sugestões (painel): Desfazer tira a troca do vocabulário")
variacoes_pos_desfazer = sg._palavra_do_config(configuracao.carregar())[1]
achou_final, _ = extrair_comando("acesor, que horas sao", variacoes_pos_desfazer)
ok("acesor" not in variacoes_pos_desfazer and not achou_final,
   "Sugestões (painel): Desfazer também tira das variações aceitas (não acorda mais)")
ok(pn.bt_sug_desfazer.cget("state") == "disabled",
   "Sugestões (painel): Desfazer desativa quando não há mais nada pra desfazer")

pn._sug_analisar(); pn.update()
ok(pn._sug_dados.get("ts") != 123.0 and "Última análise" in pn.rot_sug_info.cget("text"),
   "Sugestões (painel): Analisar agora")
pn.ent_sug_hora.delete(0, "end"); pn.ent_sug_hora.insert(0, "7h30"); pn.var_sug_ligado.set(False)
ok(pn.salvar(), "Sugestões (painel): salvar")
from app import configuracao
c = configuracao.carregar()
ok(str(c["sugestoes"]["hora"]) == "07:30" and c["sugestoes"]["ligado"] is False, "Sugestões (painel): horário salvo no config")
ok(not erros, "Sugestões (painel): sem erros na tela" + ("".join(erros)[-800:] if erros else ""))
pn._fechar()
print("FIM_SUGESTOES")
"""


CEREBRO_FALLBACK = r"""
# Troca de IA sozinho (app/cerebro.py): 1a opcao lenta/com erro cai pra proxima, quem falha fica
# "de castigo" por um tempo (nao e tentada de novo ate expirar) e a ordem configurada e respeitada.
import os, tempfile, time
os.environ["MESTRE_SEGREDOS"] = tempfile.mkdtemp()
from app.cerebro import Cerebro
from app import cerebro as cerebro_modulo
from app import segredos

def ok(c, nome): print(("OK " if c else "FALHOU ") + nome, flush=True)

segredos.salvar(claude_chave="chave-de-teste-fake")
cfg = {"cerebro": {"tipo": "ollama", "ordem_ia": ["ollama", "ollama_menor", "claude"],
                   "ollama_modelo_menor": "modelo-menor", "timeout_tentativa_seg": 0.2, "penalidade_min": 0.002}}
cerebro = Cerebro(cfg)   # 0.002 min = 0.12s de castigo: da pra esperar expirar no teste

chamadas = []
def _ollama_roteado(sistema, historico, formato=None, modelo=None, timeout=None):
    if modelo == "modelo-menor":
        chamadas.append(("ollama_menor", modelo))
        return "resposta do ollama menor"
    chamadas.append(("ollama", modelo))
    time.sleep((timeout or 0) + 0.05)   # "lenta": sempre estoura o tempo por tentativa
    raise TimeoutError("Tempo esgotado (simulado)")
def _claude_ok(sistema, historico, formato=None, modelo=None, timeout=None):
    chamadas.append(("claude", modelo)); return "resposta do claude"
cerebro._ollama = _ollama_roteado
cerebro._claude_api = _claude_ok

resposta = cerebro.perguntar("oi")
ok("resposta do ollama menor" in resposta, "1ª IA lenta (estoura o tempo por tentativa): cai pra 2ª sozinho")
ok(cerebro.ultima_ia_respondeu == "Ollama (modelo menor)", "Loga qual IA respondeu de fato")
ok(chamadas == [("ollama", "qwen2.5:7b"), ("ollama_menor", "modelo-menor")], "Tenta a 1ª antes da 2ª (ordem respeitada)")

chamadas.clear()
cerebro.perguntar("oi de novo")
ok(("ollama", "qwen2.5:7b") not in chamadas, "Quem falhou fica de castigo: não é tentada de novo enquanto não expira")
ok(("ollama_menor", "modelo-menor") in chamadas, "A próxima da lista continua respondendo normalmente")

time.sleep(0.15)   # o castigo configurado (0.12s) ja expirou
chamadas.clear()
cerebro.perguntar("oi de novo")
ok(("ollama", "qwen2.5:7b") in chamadas, "Castigo expirou: a 1ª opção volta a ser tentada")

cfg2 = {"cerebro": {"tipo": "ollama", "ordem_ia": ["ollama", "ollama_menor", "claude"],
                    "ollama_modelo_menor": "modelo-menor", "timeout_tentativa_seg": 0.2, "penalidade_min": 30}}
cerebro2 = Cerebro(cfg2)
chamadas2 = []
def _ollama_falha2(sistema, historico, formato=None, modelo=None, timeout=None):
    chamadas2.append("ollama_menor" if modelo == "modelo-menor" else "ollama")
    raise RuntimeError("erro simulado")
def _claude_ok2(sistema, historico, formato=None, modelo=None, timeout=None):
    chamadas2.append("claude"); return "resposta do claude"
cerebro2._ollama = _ollama_falha2
cerebro2._claude_api = _claude_ok2
cerebro2._castigo["ollama"] = time.time() + 999   # a 1ª ja comeca de castigo
resposta3 = cerebro2.perguntar("oi")
ok("ollama" not in chamadas2, "1ª opção de castigo: nem é chamada")
ok(chamadas2 == ["ollama_menor", "claude"], "De castigo a 1ª: tenta a 2ª antes da 3ª, nunca pula a ordem")
ok("resposta do claude" in resposta3, "2ª também falhou: cai pra 3ª (Claude) da lista")

# Botão "Baixar modelo menor" (painel > Conversa): baixar_modelo_ollama le o progresso linha a linha
# da API do Ollama, modelos_do_ollama diz o que ja esta baixado e testar_modelo_ollama confirma que
# o modelo responde. Tudo sem precisar do Ollama de verdade instalado (requests trocado por um falso).
import json as _json
import requests as _requests


class _RespostaFalsaPull:
    def __init__(self, linhas):
        self._linhas = linhas
    def raise_for_status(self):
        pass
    def iter_lines(self):
        for l in self._linhas:
            yield l.encode("utf-8")


linhas_progresso = [
    _json.dumps({"status": "pulling manifest"}),
    _json.dumps({"status": "downloading", "total": 1000, "completed": 250}),
    _json.dumps({"status": "downloading", "total": 1000, "completed": 1000}),
    _json.dumps({"status": "success"}),
]
progresso_capturado = []
_requests.post = lambda url, json=None, stream=False, timeout=None: _RespostaFalsaPull(linhas_progresso)
erro_pull = cerebro_modulo.baixar_modelo_ollama("qwen3:4b", progresso=progresso_capturado.append)
ok(erro_pull == "", "Baixar modelo menor: termina sem erro quando o Ollama manda \"success\"")
ok("(25%)" in progresso_capturado[1], "Parser do progresso: 250/1000 vira 25%")
ok("(100%)" in progresso_capturado[2], "Parser do progresso: 1000/1000 vira 100%")

_requests.post = lambda url, json=None, stream=False, timeout=None: _RespostaFalsaPull(
    [_json.dumps({"error": "modelo nao existe"})])
erro_pull2 = cerebro_modulo.baixar_modelo_ollama("modelo-que-nao-existe")
ok(erro_pull2 == "modelo nao existe", "Baixar modelo menor: erro da API do Ollama aparece pro usuário")


def _post_sem_conexao(url, json=None, stream=False, timeout=None):
    raise _requests.exceptions.ConnectionError("[WinError 10061]")
_requests.post = _post_sem_conexao
erro_pull3 = cerebro_modulo.baixar_modelo_ollama("qwen3:4b")
ok("Ollama não respondeu" in erro_pull3, "Baixar modelo menor: Ollama fechado/não instalado dá erro claro (não o erro técnico)")


class _RespostaFalsaTags:
    def __init__(self, nomes):
        self._nomes = nomes
    def json(self):
        return {"models": [{"name": n} for n in self._nomes]}
_requests.get = lambda url, timeout=None: _RespostaFalsaTags(["qwen3:8b", "llama3.2:3b"])
instalados = cerebro_modulo.modelos_do_ollama()
ok(instalados == ["llama3.2:3b", "qwen3:8b"], "modelos_do_ollama: lista o que já está baixado (ordenado)")
ok("qwen3:8b" in instalados and "qwen3:4b" not in instalados,
   "Estado \"já baixado\": modelo baixado aparece na lista, o que falta baixar não")


def _get_sem_conexao(url, timeout=None):
    raise _requests.exceptions.ConnectionError("[WinError 10061]")
_requests.get = _get_sem_conexao
ok(cerebro_modulo.modelos_do_ollama() == [], "modelos_do_ollama: Ollama fechado devolve lista vazia (sem travar)")


class _RespostaFalsaChat:
    def __init__(self, texto):
        self._texto = texto
    def raise_for_status(self):
        pass
    def json(self):
        return {"message": {"content": self._texto}}
_requests.post = lambda url, json=None, timeout=None: _RespostaFalsaChat("oi! tudo bem?")
erro_testar = cerebro_modulo.testar_modelo_ollama("qwen3:4b")
ok(erro_testar == "", "Botão Testar: modelo respondendo de verdade não dá erro")

_requests.post = lambda url, json=None, timeout=None: _RespostaFalsaChat("")
erro_testar2 = cerebro_modulo.testar_modelo_ollama("qwen3:4b")
ok(erro_testar2 != "", "Botão Testar: resposta vazia do modelo é tratada como erro")

print("FIM_CEREBRO_FALLBACK")
"""


AVATAR = r"""
# Avatar robo (processo separado, PySide6) + logo "Onda"
import os, sys, json, math, time, wave, struct, tempfile, subprocess, threading, traceback, tkinter as tk
from pathlib import Path
import yaml
def ok(c, nome): print(("OK " if c else "FALHOU ") + nome, flush=True)
os.environ["MESTRE_SEGREDOS"] = tempfile.mkdtemp()
from app import avatar, tema, estado
v = avatar.visual
ok(v({"nome": "iniciando"}) == "ligando" and v({"nome": "ouvindo"}) == "idle" and v({"nome": "gravando"}) == "ouvindo"
   and v({"nome": "conversa"}) == "ouvindo" and v({"nome": "falando"}) == "falando"
   and v({"nome": "ouvindo", "pensamento": "pensando"}) == "pensando" and v({"nome": "transcrevendo"}) == "pensando"
   and v({"nome": "ouvindo", "descanso": True}) == "descansando" and v({"nome": "ouvindo"}, pausado=True) == "pausado"
   and v({"nome": "ouvindo"}, rodando=False) == "desligado" and v({"nome": "desligado"}) == "desligado",
   "Avatar: estado do assistente -> animação (ligando/ouvindo/pensando/falando/pausado/descansando/desligado)")
a = avatar.Animador()
ok(a.mudar("ligando", 0.0) == "entrar" and a.quadro(0.05)["in_op"] < 0.2 and a.quadro(0.6)["in_op"] > 0.9
   and a.quadro(2.0)["anim"] == "" and a.base == "idle", "Avatar: ligando = entra em cena e fica normal")
ok(a.fps(2.0) == 20, f"Avatar: parado no normal anima devagar (20 quadros/s) ({a.fps(2.0)})")
a.mudar("ouvindo", 3.0); q = [a.quadro(3.0 + i / 60) for i in range(60)][-1]
ok(q["ondas"] > 0.9 and q["tilt"] < -6 and q["olhos_sx"] > 1.15 and a.fps(4.0) == 60,
   "Avatar: ouvindo = atento (inclina, olhos maiores, ondas, 60 quadros/s)")
a.mudar("pensando", 5.0, fila=3); q = [a.quadro(5.0 + i / 30) for i in range(45)][-1]
ok(q["balao"] > 0.9 and q["selo"] > 0.9 and q["selo_texto"] == "3", "Avatar: pensando = balão com pontinhos + selo com a fila (3)")
a.mudar("pensando", 7.0, fila=1); q = [a.quadro(7.0 + i / 30) for i in range(45)][-1]
ok(q["selo"] < 0.1, "Avatar: fila de 1 não mostra o selo")
a.mudar("falando", 9.0)
for i in range(30):
    a.nivel(0.05, 9.0 + i / 60); q_baixo = a.quadro(9.0 + i / 60)
for i in range(30):
    a.nivel(1.0, 9.5 + i / 60); q_alto = a.quadro(9.5 + i / 60)
ok(q_alto["boca"] > 0.9 and q_alto["boca_sy"] > q_baixo["boca_sy"] + 0.5,
   f"Avatar: falando = a boca abre com o volume da fala ({q_baixo['boca_sy']:.2f} -> {q_alto['boca_sy']:.2f})")
ok(a.mudar("pausado", 11.0) == "sair" and a.visivel(11.3) and not a.visivel(12.0) and a.fps(12.0) == 0,
   "Avatar: pausado = sai de cena e para de desenhar (0 quadros/s)")
ok(a.mudar("idle", 13.0) == "voltar" and a.visivel(13.1), "Avatar: voltando = entra de novo")
a.mudar("descansando", 15.0); q = [a.quadro(15.0 + i / 20) for i in range(40)][-1]
ok(q["zzz"] > 0.9 and q["olhos_sy"] < 0.2, "Avatar: descansando = olhos fechados e zzz")
ok(a.mudar("desligado", 20.0) == "desligar" and not a.terminou(20.3) and a.terminou(21.0),
   "Avatar: desligado = despedida e fecha")
x, y = avatar.posicao_padrao((0, 0, 1920, 1032))
L, F = avatar.LADO_JANELA, avatar.FOLGA
ok(1920 - 30 <= x + L - F <= 1920 and 1032 - 20 <= y + L - F <= 1032 and x > 1700,
   f"Avatar: posição padrão logo acima do relógio ({x}, {y})")
x2, y2 = avatar.posicao_padrao((1920, 0, 3840, 1080))
ok(x2 > 3600 and y2 > 900, "Avatar: posição padrão respeita onde fica a área de trabalho")
ok(avatar.posicao_valida((x, y), [(0, 0, 1920, 1032)]) and not avatar.posicao_valida((5000, 10), [(0, 0, 1920, 1032)]),
   "Avatar: posição salva fora das telas (monitor desligado) volta ao padrão")
avatar.salvar_posicao((120, 340)); lida = avatar.ler_posicao(); avatar.salvar_posicao(None)
ok(lida == (120, 340) and avatar.ler_posicao() is None and "Mestre" in str(avatar.arquivo_posicao()),
   "Avatar: posição arrastada fica salva (APPDATA/Mestre/avatar.json)")
ok(avatar.tipo_escolhido({}) == "avatar" and avatar.tipo_escolhido({"indicador": {"tipo": "bolinha"}}) == "bolinha"
   and avatar.tipo_escolhido({"indicador": {"tipo": "xyz"}}) == "avatar", "Avatar: padrão é o avatar; bolinha é opção")
# fallback: sem PySide6 (ou no teste) nada abre e o Assessor usa a bolinha
from app import main as m
class Ex:
    rodando = True; nome = "Jarvis"; palavra = "jarvis"
ok(avatar.iniciar() is None and m._mostrar_avatar({}, Ex()) is False, "Avatar: no teste automático não aparece nada")
os.environ["MESTRE_SIMULAR"] = "0"
_pi = avatar.pyside_instalado; avatar.pyside_instalado = lambda: False
ok(avatar.iniciar() is None and m._mostrar_avatar({}, Ex()) is False, "Avatar: sem PySide6 cai para a bolinha")
avatar.pyside_instalado = _pi
os.environ["MESTRE_SIMULAR"] = "1"
ok(m._mostrar_avatar({"indicador": {"tipo": "bolinha"}}, Ex()) is False, "Avatar: escolheu bolinha = bolinha")
falha = subprocess.Popen([sys.executable, "-c", "raise SystemExit(3)"])
fechou = subprocess.Popen([sys.executable, "-c", "raise SystemExit(0)"])
rodando = [True]
threading.Timer(1.5, lambda: rodando.__setitem__(0, False)).start()
ok(avatar.acompanhar(falha, lambda: True) == "falhou" and avatar.acompanhar(fechou, lambda: rodando[0]) == "escondido",
   "Avatar: fechou com erro = bolinha; escondido pelo menu = segue sem indicador")
avatar.ATIVO = False; avatar.enviar_nivel(0.5)   # desligado: nao faz nada (nem erro)
arq = os.path.join(tempfile.mkdtemp(), "fala.wav")
with wave.open(arq, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
    w.writeframes(b"".join(struct.pack("<h", int((8000 if n < 12000 else 300) * math.sin(n / 9))) for n in range(24000)))
env = avatar.envelope(Path(arq))
ok(env and len(env) in (29, 30, 31) and avatar.nivel_no_tempo(env, 100) > 0.8 and avatar.nivel_no_tempo(env, 800) < 0.2
   and avatar.nivel_no_tempo(env, 5000) == 0.0, "Avatar: volume da fala (voz alta -> boca aberta, silêncio -> fechada)")
if avatar.pyside_instalado():
    from app import avatar_janela
    sys.argv = ["x"]
    ok(avatar_janela.main() == 0, "Avatar: a janela não abre no teste automático")
    ok(avatar_janela.tons_do_rosa("#F5A6C8") == ("#FFD0E3", "#F5A6C8", "#CF7896") and len(avatar_janela.tons_do_rosa("#8DB8F7")) == 3,
       "Avatar: cabeça rosa do protótipo (e segue a cor de destaque)")
# logo "Onda": icone.png e icone.ico em todos os tamanhos
tema.salvar_icones("#8DB8F7")
from PIL import Image
ico = Image.open("app/icone.ico")
ok(sorted(ico.info["sizes"]) == [(t, t) for t in (16, 24, 32, 48, 64, 128, 256)] and Image.open("app/icone.png").size == (256, 256),
   "Logo Onda: icone.png (256) e icone.ico (16 a 256) gerados")
import numpy as np
px = np.asarray(tema.desenhar_icone("#8DB8F7", 64).convert("RGBA")).reshape(-1, 4).astype(int)
verde = int(((px[:, 1] > 200) & (px[:, 0] < 160) & (px[:, 3] > 200)).sum())
azul = int(((px[:, 2] > 220) & (px[:, 0] < 170) & (px[:, 3] > 200)).sum())
ok(verde > 20 and azul > 100, f"Logo Onda: A na cor de destaque + onda verde ({azul} {verde})")
ok(tema.desenhar_icone(None, 16).getbbox() is not None, "Logo Onda: versão simples em 16 px")
# painel > Aparencia: Indicador avatar/bolinha salvo no config
erros = []
tk.Tk.report_callback_exception = lambda self, e, val, tb: erros.append("".join(traceback.format_exception(e, val, tb)))
import app.painel as p
pn = p.Painel(); pn.update()
pn.mostrar_pagina("Aparência"); pn.update()
ok(pn.var_indicador.get() == "Avatar robô", "Painel: Indicador começa em “Avatar robô”")
pn.var_indicador.set("Bolinha")
ok(pn.salvar(), "Painel: salvar com o indicador trocado")
c = yaml.safe_load(open("config.yaml", encoding="utf-8"))
ok(c["indicador"]["tipo"] == "bolinha" and c["aparencia"], "Painel: “Bolinha” salvo em indicador > tipo")
ok(not erros, "Avatar/painel sem erros na tela" + ("".join(erros)[-800:] if erros else ""))
pn._fechar()
print("FIM_AVATAR")
"""


PAINEL_25 = r"""
# Painel 2.5: menu de icones, paginas sob demanda, Inicio em cartoes (status, fila, ultimos comandos)
import json, os, time, traceback, tkinter as tk
def ok(c, nome): print(("OK " if c else "FALHOU ") + nome, flush=True)
from app import estado, icones, memoria, validacao
# o Assessor (outro processo) publica o estado num arquivo; o painel le
estado.definir("ouvindo")
ok(estado.ler_de_fora().get("nome") == "ouvindo", "Estado publicado para o painel (logs/estado_agora.json)")
ok(estado.situacao({"nome": "falando"}, True, False) == "falando" and estado.situacao({}, False, False) == "desligado"
   and estado.situacao({"nome": "ouvindo"}, True, True) == "pausado"
   and estado.situacao({"nome": "ouvindo", "descanso": True}, True, False) == "descansando"
   and estado.situacao({"nome": "ouvindo", "pensamento": "pensando"}, True, False) == "pensando",
   "Situação do Início: ouvindo/pensando/falando/descansando/pausado/desligado")
agora = time.time()
hist = [{"pedido": "Mestre, abre o YouTube", "entendi": "abre o youtube", "rota": "_cmd_abrir", "resposta": "Abrindo o YouTube.",
         "tipo": "comando", "ts": agora - 20},
        {"pedido": "Mestre, que horas são", "entendi": "que horas sao", "rota": "_cmd_hora_data", "resposta": "São 10h.",
         "tipo": "comando", "ts": agora - 5}]
ouv = [{"texto": "Mestre abre o iutube", "chamou": True, "ts": agora - 21}, {"texto": "blá", "ts": agora - 10},
       {"texto": "Mestre, que horas são?", "chamou": True, "ts": agora - 6}]
u = validacao.ultimos_comandos(5, hist, ouv)
ok(len(u) == 2 and u[0]["ouvi"] == "Mestre, que horas são?" and u[1]["ouvi"] == "Mestre abre o iutube"
   and "_cmd_abrir" in u[1]["entendi"] and u[1]["fiz"] == "Abrindo o YouTube.",
   f"Últimos comandos: OUVI/ENTENDI/FIZ casados, mais novo primeiro {u}")
ok(all(icones.imagem(n, "#F5A6C8").getbbox() for n in icones.DESENHOS if n != "vazio"),
   "Ícones do menu desenhados (nenhum em branco)")

erros = []
tk.Tk.report_callback_exception = lambda self, e, v, tb: erros.append("".join(traceback.format_exception(e, v, tb)))
for h in hist:
    memoria.registrar(h["pedido"], h["resposta"], "comando", {"entendi": h["entendi"], "rota": h["rota"]})
import app.painel as p
pn = p.Painel(); pn.update()
ok(pn._montadas == ["Início"], f"Páginas sob demanda: só o Início montado ao abrir {pn._montadas}")
ok(pn.status_mestre.cget("text") == "Desligado" and pn._cmd_linhas[0]["frame"].winfo_manager()
   and pn._cmd_linhas[0]["FIZ"].cget("text") == "São 10h.",
   "Início: status e últimos comandos (OUVI/ENTENDI/FIZ) na tela")
widgets = len(list(p._descendentes(pn)))
# o Assessor "liga" e comeca a pensar: o Inicio acompanha sem recriar widgets
p.sistema.mestre_ligado = lambda: True
estado.atualizar(pensamento="pensando", pensamentos_fila=1,
                 pensamentos_lista=[{"pergunta": "me explica a relatividade", "inicio": time.time() - 3, "estado": "pensando"}])
pn._aplicar_inicio(pn._coletar_inicio()); pn.update()
ok(pn.status_mestre.cget("text") == "Pensando" and pn._fila_linhas[0]["frame"].winfo_manager()
   and "relatividade" in pn._fila_linhas[0]["texto"].cget("text") and not pn.rot_fila_vazia.winfo_manager(),
   "Início: fila do pensando aparece e o status vira “Pensando”")
estado.atualizar(pensamento="", pensamentos_fila=0, pensamentos_lista=[])
estado.definir("falando")
pn._status(); fim = time.time() + 5
while time.time() < fim and pn.status_mestre.cget("text") != "Falando":
    pn.update(); time.sleep(0.05)
ok(pn.status_mestre.cget("text") == "Falando" and not pn._fila_linhas[0]["frame"].winfo_manager(),
   "Início: atualiza sozinho (leitura em segundo plano)")
ok(len(list(p._descendentes(pn))) == widgets, "Início: atualizar não cria widgets novos")
# troca de pagina: a 2a vez e so trazer para a frente
pn.mostrar_pagina("Voz"); pn.update(); pn.mostrar_pagina("Início"); pn.update()
t0 = time.time(); pn.mostrar_pagina("Voz"); pn.update(); tempo = time.time() - t0
ok(pn._montadas == ["Início", "Voz"] and tempo < 0.3, f"Voltar a uma página já aberta é rápido ({tempo:.3f}s)")
ok(pn.botoes_menu["Voz"].cget("fg_color") == p.tema.ROSA_FUNDO and pn.titulo_pagina.cget("text") == "Voz",
   "Menu: item ativo destacado e título da página")
pn._rail_ir(pn._rail_aberto); fim = time.time() + 2
while time.time() < fim and pn._rail_largura != pn._rail_aberto:
    pn.update(); time.sleep(0.01)
ok(pn._rail_largura == pn._rail_aberto, "Menu de ícones abre (mostrando os nomes)")
pn._rail_ir(pn._rail_fechado); fim = time.time() + 2
while time.time() < fim and pn._rail_largura != pn._rail_fechado:
    pn.update(); time.sleep(0.01)
ok(pn._rail_largura == pn._rail_fechado, "Menu de ícones fecha de novo")
ok(pn.salvar() and set(pn._montadas) == {"Início", "Voz"}, "Salvar com só algumas páginas abertas")
ok(not erros, "Painel 2.5 sem erros na tela" + ("".join(erros)[-800:] if erros else ""))
pn._fechar()
print("FIM_PAINEL_25")
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

        print("\n[Painel não apaga rotina]")
        cod, saida = rodar(pasta, PAINEL_ROTINA_EXTERNA)
        conferir(cod == 0 and "SALVOU True" in saida, "Painel salva com rotina gravada por fora", saida[-800:])
        cod, saida = rodar(pasta, CONFERIR_ROTINA_EXTERNA)
        conferir("Rotina de fora" in saida, "Rotina gravada por fora (enquanto o painel estava aberto) sobrevive", saida)
        conferir("Hora do cafe" not in saida, "Rotina apagada no painel continua apagada", saida)
        conferir("Bora trabalhar" in saida, "Rotina não mexida continua lá", saida)

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

        print("\n[Ensinar uma rotina falando]")
        cod, saida = rodar(pasta, ROTINA_FALADA, espera=120)
        for linha in saida.splitlines():
            if linha.startswith(("OK ", "FALHOU ")):
                conferir(linha.startswith("OK "), linha.split(" ", 1)[1].strip(), saida[-1500:])
        if "FIM_ROTINA_FALADA" not in saida:
            conferir(False, "Rotina falada: o teste rodou até o fim", saida[-1500:])

        print("\n[Vocabulário: muitos jeitos de pedir]")
        r = subprocess.run([sys.executable, "-m", "testes.frases"], creationflags=SEM_JANELA, cwd=str(pasta), capture_output=True, text=True,
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
        conferir(f"VERSAO_TELA Versão {VERSAO_ATUAL}" in saida, "Painel mostra a versão do projeto (menu lateral)", saida[-600:])
        conferir("ABRIU_SECAO True elevenlabs" in saida, "“Ativar esta voz” escolhe a voz e mostra a aba dela",
                 saida[-600:])
        conferir("SALVOU_VOZ natural francisca onwK4e9ZLuTAKqWW03F9 eleven_flash_v2_5 chave-de-teste" in saida,
                 "Voz natural e ElevenLabs salvam (chave fora do projeto)", saida[-600:])
        conferir("ABA_RESERVA azure True disabled" in saida and "SALVOU_RESERVA azure" in saida,
                 "Voz em abas: “Usar como reserva” (a ativa não vira reserva) e salva", saida[-600:])
        conferir("ORDEM_RESERVA ['natural', 'azure', 'kokoro', 'edge']" in saida,
                 "Se a voz ativa falhar, ele tenta primeiro a reserva escolhida", saida[-600:])
        conferir("RESERVA ['edge']" in saida or "RESERVA ['kokoro', 'edge']" in saida,
                 "Voz natural não instalada: ele fala com a Kokoro/Edge", saida[-600:])
        conferir("ERROS_TELA 0" in saida, "Página Voz nova sem erros na tela", saida[-1500:])

        print("\n[Voz natural: um servidor só]")
        cod, saida = rodar(pasta, VOZ_NATURAL_SERVIDOR)
        conferir("VOZ_NATURAL_SERVIDOR_OK True" in saida,
                 "Painel e Assessor chamando ao mesmo tempo não sobem dois servidores", saida[-800:])
        cod, saida = rodar(pasta, VOZ_NATURAL_RESERVA)
        conferir("VOZ_NATURAL_RESERVA_OK True" in saida,
                 "Enquanto a voz natural ainda carrega, fala com a Kokoro/Edge (sem esperar)", saida[-800:])

        print("\n[Nome e palavra novos em todo lugar]")
        cod, saida = rodar(pasta, NOMES)
        restos = [l for l in saida.splitlines() if l.startswith("COM_MESTRE")]
        conferir("NOMES_OK" in saida and not restos, "Com o nome “Jarvis”, nada na tela diz “Mestre”",
                 "\n".join(restos) or saida[-1200:])
        conferir("diga “Jarvis”" in saida, "Indicador mostra a palavra nova", saida[-600:])

        print("\n[Aparência]")
        cod, saida = rodar(pasta, APARENCIA)
        conferir("APARENCIA_OK" in saida, "Trocar cor, fonte e tamanho e salvar", saida[-800:])

        print("\n[Responder só à voz do dono]")
        cod, saida = rodar(pasta, VOZ_DONO, espera=120)
        for linha in saida.splitlines():
            if linha.startswith(("OK ", "FALHOU ")):
                conferir(linha.startswith("OK "), linha.split(" ", 1)[1].strip(), saida[-1500:])
        if "FIM_VOZ_DONO" not in saida:
            conferir(False, "Voz do dono: o teste rodou até o fim", saida[-1500:])

        print("\n[Captação da voz]")
        cod, saida = rodar(pasta, CAPTACAO, espera=120)
        for linha in saida.splitlines():
            if linha.startswith(("OK ", "FALHOU ")):
                conferir(linha.startswith("OK "), linha.split(" ", 1)[1].strip(), saida[-1500:])
        if "FIM_CAPTACAO" not in saida:
            conferir(False, "Captação: o teste rodou até o fim", saida[-1500:])

        print("\n[Fala em segundo plano, interromper e frase pela metade]")
        for trecho, fim in ((FALA_FLUIDA, "FIM_FALA_FLUIDA"), (SEGUIMENTO_ABRIR, "FIM_SEGUIMENTO_ABRIR")):
            cod, saida = rodar(pasta, trecho, espera=120)
            for linha in saida.splitlines():
                if linha.startswith(("OK ", "FALHOU ")):
                    conferir(linha.startswith("OK "), linha.split(" ", 1)[1].strip(), saida[-1500:])
            if fim not in saida:
                conferir(False, f"{fim}: o teste rodou até o fim", saida[-1500:])

        print("\n[Validar atualização]")
        cod, saida = rodar(pasta, VALIDACAO, espera=120)
        for linha in saida.splitlines():
            if linha.startswith(("OK ", "FALHOU ")):
                conferir(linha.startswith("OK "), linha.split(" ", 1)[1].strip(), saida[-1500:])
        if "FIM_VALIDACAO" not in saida:
            conferir(False, "Validação: o teste rodou até o fim", saida[-1500:])

        print("\n[Avisos do PC (liga/desliga pelo Telegram)]")
        cod, saida = rodar(pasta, AVISOS_PC, espera=60)
        for linha in saida.splitlines():
            if linha.startswith(("OK ", "FALHOU ")):
                conferir(linha.startswith("OK "), linha.split(" ", 1)[1].strip(), saida[-1500:])
        if "FIM_AVISOS_PC" not in saida:
            conferir(False, "Avisos do PC: o teste rodou até o fim", saida[-1500:])

        print("\n[Sugestões de melhoria]")
        cod, saida = rodar(pasta, SUGESTOES, espera=120)
        for linha in saida.splitlines():
            if linha.startswith(("OK ", "FALHOU ")):
                conferir(linha.startswith("OK "), linha.split(" ", 1)[1].strip(), saida[-1500:])
        if "FIM_SUGESTOES" not in saida:
            conferir(False, "Sugestões: o teste rodou até o fim", saida[-1500:])

        print("\n[Troca de IA sozinho (quando uma demora ou falha)]")
        cod, saida = rodar(pasta, CEREBRO_FALLBACK, espera=60)
        for linha in saida.splitlines():
            if linha.startswith(("OK ", "FALHOU ")):
                conferir(linha.startswith("OK "), linha.split(" ", 1)[1].strip(), saida[-1500:])
        if "FIM_CEREBRO_FALLBACK" not in saida:
            conferir(False, "Troca de IA sozinho: o teste rodou até o fim", saida[-1500:])

        print("\n[Painel 2.5: menu de ícones e Início em cartões]")
        cod, saida = rodar(pasta, PAINEL_25, espera=120)
        for linha in saida.splitlines():
            if linha.startswith(("OK ", "FALHOU ")):
                conferir(linha.startswith("OK "), linha.split(" ", 1)[1].strip(), saida[-1500:])
        if "FIM_PAINEL_25" not in saida:
            conferir(False, "Painel 2.5: o teste rodou até o fim", saida[-1500:])

        print("\n[Avatar robô e logo Onda]")
        cod, saida = rodar(pasta, AVATAR, espera=180)
        for linha in saida.splitlines():
            if linha.startswith(("OK ", "FALHOU ")):
                conferir(linha.startswith("OK "), linha.split(" ", 1)[1].strip(), saida[-1500:])
        if "FIM_AVATAR" not in saida:
            conferir(False, "Avatar: o teste rodou até o fim", saida[-1500:])

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
        (destino / "app" / "versao.py").write_text(f'VERSAO = "{VERSAO_ANTERIOR}"\n', encoding="utf-8")
        cod, saida = rodar(destino, f"""
            from pathlib import Path
            from app import atualizar
            print("VERIFICAR", repr(atualizar.verificar(r"{pacote}")))
            print(atualizar.aplicar(r"{pacote}", Path.cwd(), instalar_bibliotecas=False))
        """)
        conferir("VERIFICAR ''" in saida and "Atualizado" in saida, "Atualização aplicada", saida[-500:])
        conferir(f"da versão {VERSAO_ANTERIOR} para a {VERSAO_ATUAL}" in saida, "Atualização diz de qual versão para qual foi", saida[-500:])
        conferir((destino / "config.yaml").read_text(encoding="utf-8") == "# MEU CONFIG\n",
                 "Atualização NÃO mexe no seu config.yaml")
        conferir(not (destino / "ANTIGO.bat").exists(), "Atualização retira arquivos antigos")

        print("\n[Central e ícone]")
        cod, saida = rodar(pasta, "import app.central, app.bandeja, app.atualizar; print('IMPORTOU')")
        conferir("IMPORTOU" in saida, "Central, ícone e atualizador carregam", saida[-500:])

    print("\n[Modelos offline: liga sem internet se já baixou antes]")
    # roda no projeto DE VERDADE (nao na copia): precisa do cache do Whisper e de modelos/locutor_ecapa,
    # que a copia dos testes nao traz (pasta "modelos" e ignorada de proposito, ela e grande)
    saida = _rodar_offline_no_projeto_real()
    for linha in saida.splitlines():
        if linha.startswith("OK "):
            conferir(True, linha[3:].strip())
        elif linha.startswith("FALHOU "):
            nome, _, detalhe = linha[7:].strip().partition("::")
            conferir(False, nome, detalhe or saida[-1200:])
        elif linha.startswith("PULOU "):
            print("  PULADO  " + linha[6:].strip())
    if not any(l.startswith(("OK ", "FALHOU ", "PULOU ")) for l in saida.splitlines()):
        conferir(False, "Teste de modelos offline rodou até o fim", saida[-1200:])

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
