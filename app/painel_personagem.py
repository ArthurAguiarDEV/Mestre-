"""Painel > Aparência > "Personagem": escolher o robozinho OU um personagem (homem/mulher, cabelo, roupa, fantasias de heróis,
acessórios), o jeito dele (cada personalidade se mexe e passeia de um modo) e ver a prévia.

Fica num arquivo à parte para não engordar o painel.py: ele só chama `montar(self, pagina)` ao montar a página e
`salvar(self, c)` ao salvar. A prévia é um PNG feito por `app.personagem.previa` (processo do Qt, sem janela).
"""
import json
import queue
import random
import subprocess
import tempfile
import threading
from pathlib import Path

PAGINA_TESTE = Path(__file__).resolve().parent.parent / "design" / "avatar-2026-09" / "index.html"
JEITO_AUTO = "Automático (segue a personalidade do Assessor)"


def montar(p, pagina) -> None:
    """Cria a seção "Personagem" na página Aparência. `p` é o Painel (guarda as variáveis em p.vars_pers)."""
    import tkinter as tk

    import customtkinter as ctk
    from PIL import Image

    from . import avatar, painel as P, tema
    from .config import PASTA_PROJETO
    from .personagem import catalogo as cat
    from .personagem import catalogo_animacao as A
    from .personagem.opcoes import opcoes_do_config
    from .personagem.passeio import NOMES_MODO

    op = opcoes_do_config(p.cfg)
    perfil = op["perfil"]
    av = p.cfg.get("avatar") or {}
    nomes_modelo = avatar.MODELOS
    jeito0 = str(av.get("jeito") or "").strip().lower()
    trajes = {"": "Nenhuma"}
    trajes.update({i: f"{t['universo']} · {t['nome']}" for i, t in cat.TRAJES.items()})
    jeitos = {"": JEITO_AUTO, **{k: f"{v['nome']} ({[e for e, a in A.ESTILO_PARA_ARQUETIPO.items() if a == k][0]})" for k, v in A.ARQUETIPOS.items()}}
    V = p.vars_pers = {
        "modelo": tk.StringVar(value=nomes_modelo[avatar.modelo_escolhido(p.cfg)]),
        "genero": tk.StringVar(value="Mulher" if perfil["genero"] == "f" else "Homem"),
        "pele": tk.StringVar(value=perfil["pele"]), "cabelo_cor": tk.StringVar(value=perfil["cabelo_cor"]),
        "olhos_cor": tk.StringVar(value=perfil["olhos_cor"]), "roupa_cor1": tk.StringVar(value=perfil["roupa_cor1"]),
        "roupa_cor2": tk.StringVar(value=perfil["roupa_cor2"]), "roupa_cor3": tk.StringVar(value=perfil["roupa_cor3"]),
        "cabelo": tk.StringVar(value=cat.CABELOS[perfil["cabelo"]]["nome"]), "roupa": tk.StringVar(value=cat.ROUPAS[perfil["roupa"]]["nome"]),
        "traje": tk.StringVar(value=trajes[perfil["traje"]]), "escala": tk.DoubleVar(value=round(perfil["escala"] * 100)),
        "jeito": tk.StringVar(value=jeitos.get(jeito0, JEITO_AUTO)), "passeio": tk.StringVar(value=NOMES_MODO[op["passeio"]]),
        "acessorios": {i: tk.BooleanVar(value=i in perfil["acessorios"]) for i in cat.ACESSORIOS}}
    rostos = _nomes_rosto(cat)
    V.update({opc: tk.StringVar(value=rostos[opc][perfil[opc]]) for opc in cat.ROSTO_ORDEM})
    p._pers_serie = 0
    p._pers_pendentes = 0
    p._pers_fila = queue.Queue()
    p._pers_agenda = None
    p._pers_amostras = []

    def id_de(var, tabela: dict, padrao: str) -> str:
        return next((k for k, v in tabela.items() if v == var.get()), padrao)

    def coletar() -> dict:
        return {"genero": "f" if V["genero"].get() == "Mulher" else "m", "pele": V["pele"].get(), "cabelo": id_de(V["cabelo"], {i: c["nome"] for i, c in cat.CABELOS.items()}, "curto"),
                "cabelo_cor": V["cabelo_cor"].get(), "olhos_cor": V["olhos_cor"].get(), "roupa": id_de(V["roupa"], {i: r["nome"] for i, r in cat.ROUPAS.items()}, "camiseta"),
                "roupa_cor1": V["roupa_cor1"].get(), "roupa_cor2": V["roupa_cor2"].get(), "roupa_cor3": V["roupa_cor3"].get(),
                "traje": id_de(V["traje"], trajes, ""), "acessorios": [i for i, v in V["acessorios"].items() if v.get()],
                "escala": V["escala"].get() / 100, **{opc: id_de(V[opc], rostos[opc], "") for opc in cat.ROSTO_ORDEM}}

    # --- prévia (PNG feito à parte; nunca trava o painel) ----------------------------------------------------------------
    def renderizar() -> None:
        p._pers_agenda = None
        p._pers_serie += 1
        serie = p._pers_serie
        dados = json.dumps(coletar())

        def trabalho():   # linha secundária: NADA de Tk aqui (só a fila); quem mexe na tela é colher(), na linha principal
            arq = Path(tempfile.gettempdir()) / f"mestre_previa_personagem_{serie % 4}.png"
            img = None
            try:
                subprocess.run([avatar._python_sem_janela(), "-m", "app.personagem.previa", "--perfil", dados, "--saida", str(arq), "--altura", "300"],
                               cwd=str(PASTA_PROJETO), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=40, capture_output=True, check=True)
                img = Image.open(arq).convert("RGBA")
                img.load()
            except Exception:
                img = None
            p._pers_fila.put((serie, img))

        p._pers_pendentes += 1
        threading.Thread(target=trabalho, daemon=True).start()
        if p._pers_pendentes == 1:
            colher()

    def colher() -> None:
        """Linha principal: aplica as prévias prontas e volta a olhar a fila enquanto houver alguma a caminho."""
        try:
            while True:
                serie, img = p._pers_fila.get_nowait()
                p._pers_pendentes -= 1
                aplicar(serie, img)
        except queue.Empty:
            pass
        if p._pers_pendentes > 0:
            try:
                p.after(120, colher)
            except tk.TclError:
                pass   # painel fechou

    def aplicar(serie: int, img) -> None:
        if serie != p._pers_serie:
            return   # já tem uma prévia mais nova a caminho
        try:
            if img is None:
                previa.configure(image=None, text="Prévia indisponível (precisa do PySide6).")
            else:
                p._pers_img = ctk.CTkImage(light_image=img, dark_image=img, size=(int(img.width * 0.6), int(img.height * 0.6)))
                previa.configure(image=p._pers_img, text="")
        except tk.TclError:
            pass

    def mudou(*_):
        if p._pers_agenda is not None:
            try:
                p.after_cancel(p._pers_agenda)
            except tk.TclError:
                pass
        p._pers_agenda = p.after(350, renderizar)

    # --- montagem ------------------------------------------------------------------------------------------------------
    f = P.secao(pagina, "Personagem no lugar do robozinho",
                "Troque o robozinho por um personagem de homem ou mulher, com rosto, cabelo, roupa, acessórios e fantasias. "
                "Cada personalidade do Assessor tem o seu jeito de se mexer, falar e passear pela tela. A boca acompanha a voz. "
                "Trocar entre Robozinho e Personagem vale depois de salvar e reiniciar o assistente (\"Mestre, reinicia\"). "
                "Com o personagem já na tela, visual, jeito e passeio mudam poucos segundos depois de salvar, sem reiniciar. "
                "As fantasias de heróis são versões inspiradas, só para uso pessoal.")
    P.linha_campo(f, "Avatar", lambda q: ctk.CTkSegmentedButton(q, values=list(nomes_modelo.values()), variable=V["modelo"], command=mudou), 150)
    aviso = ctk.CTkLabel(f, text="", anchor="w", text_color=tema.AVISO, wraplength=640, justify="left")

    def conferir_indicador(*_):
        """O personagem só aparece com o Indicador em "Texto + robô" ou "Só robô" (com "Bolinha" nenhum avatar abre)."""
        ind = getattr(p, "var_indicador", None)
        bolinha = ind is not None and ind.get() == avatar.TIPOS["bolinha"]
        if V["modelo"].get() == nomes_modelo["personagem"] and bolinha:
            aviso.configure(text="O Indicador (logo acima) está em \"Bolinha\": assim o personagem não aparece. "
                                 "Escolha \"Texto + robô\" ou \"Só robô\", salve e reinicie.")
            aviso.pack(fill="x", padx=(32, 18), pady=(0, 6), before=corpo)   # logo abaixo da escolha do Avatar
        else:
            aviso.pack_forget()
    V["modelo"].trace_add("write", conferir_indicador)
    if getattr(p, "var_indicador", None) is not None:
        p.var_indicador.trace_add("write", conferir_indicador)
    corpo = ctk.CTkFrame(f, fg_color="transparent")
    corpo.pack(fill="x", padx=6)
    opcoes = ctk.CTkFrame(corpo, fg_color="transparent")
    opcoes.pack(side="left", fill="both", expand=True)
    previa = ctk.CTkLabel(corpo, text="Gerando a prévia…", width=190, height=230, text_color=tema.TEXTO_FRACO)
    previa.pack(side="right", padx=(8, 16), pady=6, anchor="n")
    conferir_indicador()

    def focavel(w, acionar=None, teclas=None):
        """No Aurora só o CTkButton entra no Tab: menus, caixas de marcar e a régua do tamanho entram aqui, com anel de
        foco; Enter/Espaço aciona (abre o menu, marca a caixa) e as setas mexem na régua."""
        cv = getattr(w, "_canvas", None)
        if cv is None:
            return w
        cv.configure(takefocus=1, highlightcolor=tema.TEXTO, highlightbackground=tema.TEXTO)
        tk.Misc.bind(cv, "<FocusIn>", lambda _e: cv.configure(highlightthickness=2), "+")
        tk.Misc.bind(cv, "<FocusOut>", lambda _e: cv.configure(highlightthickness=0), "+")
        for tecla, acao in (({"<Return>": acionar, "<space>": acionar} if acionar else {}) | (teclas or {})).items():
            tk.Misc.bind(cv, tecla, lambda _e, a=acao: (a(), "break")[1], "+")
        return w

    def amostras(master, tabela, var):
        quadro = ctk.CTkFrame(master, fg_color="transparent")
        botoes = {}
        nomes = {id_: nome for id_, nome, _h in tabela}
        legenda = ctk.CTkLabel(quadro, text="", anchor="w", text_color=tema.TEXTO_FRACO)

        def pintar():
            for id_, b in botoes.items():
                escolhida = var.get() == id_
                P._estilizar(b, border_width=3 if escolhida else 1, border_color=tema.ROSA if escolhida else tema.BORDA)
            legenda.configure(text=nomes.get(var.get(), ""))   # a cor escolhida por escrito (não só pela cor)

        def escolher(id_):
            var.set(id_)
            pintar()
            mudou()
        for n, (id_, nome, hexa) in enumerate(tabela):
            b = ctk.CTkButton(quadro, text="", width=24, height=24, corner_radius=12, fg_color=hexa, hover_color=hexa,
                              border_width=1, border_color=tema.BORDA, command=lambda i=id_: escolher(i))
            b.grid(row=n // 9, column=n % 9, padx=2, pady=2)   # 9 por linha: a lista de cores não estoura a largura
            cv = getattr(b, "_canvas", None)
            if cv is not None:   # focada pelo teclado ou com o mouse em cima: diz o nome da cor
                for ev in ("<FocusIn>", "<Enter>"):
                    tk.Misc.bind(cv, ev, lambda _e, t=nome: legenda.configure(text=f"{t} (Enter escolhe)"), "+")
                for ev in ("<FocusOut>", "<Leave>"):
                    tk.Misc.bind(cv, ev, lambda _e: legenda.configure(text=nomes.get(var.get(), "")), "+")
            botoes[id_] = b
        legenda.grid(row=(len(tabela) - 1) // 9 + 1, column=0, columnspan=9, sticky="w", padx=2)
        pintar()
        p._pers_amostras.append(pintar)
        return quadro

    def menu(master, var, valores, command=None):
        m = ctk.CTkOptionMenu(master, values=valores, variable=var, width=270, command=command or mudou)
        return focavel(m, acionar=m._open_dropdown_menu)

    P.linha_campo(opcoes, "Corpo", lambda q: ctk.CTkSegmentedButton(q, values=["Homem", "Mulher"], variable=V["genero"], command=mudou), 150)
    P.linha_campo(opcoes, "Tom de pele", lambda q: amostras(q, cat.PELES, V["pele"]), 150)
    P.linha_campo(opcoes, "Cor dos olhos", lambda q: amostras(q, cat.CORES_OLHOS, V["olhos_cor"]), 150)
    for opc in cat.ROSTO_ORDEM:   # formato do rosto, olhos, sobrancelhas, nariz, bochechas
        P.linha_campo(opcoes, cat.ROSTO_ROTULOS[opc], lambda q, o=opc: menu(q, V[o], list(rostos[o].values())), 150)
    P.linha_campo(opcoes, "Cabelo", lambda q: menu(q, V["cabelo"], [c["nome"] for c in cat.CABELOS.values()]), 150)
    P.linha_campo(opcoes, "Cor do cabelo", lambda q: amostras(q, cat.CORES_CABELO, V["cabelo_cor"]), 150)

    def trocou_roupa(nome):
        rid = id_de(V["roupa"], {i: r["nome"] for i, r in cat.ROUPAS.items()}, "camiseta")
        for chave, cor in zip(("roupa_cor1", "roupa_cor2", "roupa_cor3"), cat.ROUPAS[rid]["cores"]):
            V[chave].set(cor)
        V["traje"].set(trajes[""])
        for pintar in p._pers_amostras:
            pintar()
        mudou()
    P.linha_campo(opcoes, "Roupa", lambda q: menu(q, V["roupa"], [r["nome"] for r in cat.ROUPAS.values()], trocou_roupa), 150)
    P.linha_campo(opcoes, "  peça de cima", lambda q: amostras(q, cat.CORES_ROUPA, V["roupa_cor1"]), 150)
    P.linha_campo(opcoes, "  detalhes", lambda q: amostras(q, cat.CORES_ROUPA, V["roupa_cor2"]), 150)
    P.linha_campo(opcoes, "  parte de baixo", lambda q: amostras(q, cat.CORES_ROUPA, V["roupa_cor3"]), 150)
    P.linha_campo(opcoes, "Fantasia", lambda q: menu(q, V["traje"], list(trajes.values())), 150)
    quadro_ac = P.linha_campo(opcoes, "Acessórios", lambda q: ctk.CTkFrame(q, fg_color="transparent"), 150)
    for i, (aid, ac) in enumerate(cat.ACESSORIOS.items()):
        cx = ctk.CTkCheckBox(quadro_ac, text=ac["nome"], variable=V["acessorios"][aid], command=mudou, width=140)
        cx.grid(row=i // 3, column=i % 3, sticky="w", padx=(0, 8), pady=2)
        focavel(cx, acionar=lambda c=cx: (c.toggle(),))

    def tamanho(_v=None):
        rotulo_tam.configure(text=f"{int(V['escala'].get())}%")
        mudou()

    def passo_tamanho(delta):
        V["escala"].set(max(60, min(160, V["escala"].get() + delta)))
        tamanho()
    linha_t = P.linha_campo(opcoes, "Tamanho", lambda q: ctk.CTkFrame(q, fg_color="transparent"), 150)
    focavel(ctk.CTkSlider(linha_t, from_=60, to=160, number_of_steps=20, variable=V["escala"], command=tamanho, width=220),
            teclas={"<Left>": lambda: passo_tamanho(-5), "<Right>": lambda: passo_tamanho(5),
                    "<Down>": lambda: passo_tamanho(-5), "<Up>": lambda: passo_tamanho(5)}).pack(side="left")
    rotulo_tam = ctk.CTkLabel(linha_t, text=f"{int(V['escala'].get())}%", width=50)
    rotulo_tam.pack(side="left", padx=8)
    P.linha_campo(opcoes, "Jeito", lambda q: menu(q, V["jeito"], list(jeitos.values())), 150)
    P.linha_campo(opcoes, "Passeio pela tela", lambda q: menu(q, V["passeio"], list(NOMES_MODO.values())), 150)

    def sortear():
        rnd = random.Random()
        V["genero"].set(rnd.choice(["Homem", "Mulher"]))
        for chave, tabela in (("pele", cat.PELES), ("cabelo_cor", cat.CORES_CABELO), ("olhos_cor", cat.CORES_OLHOS)):
            V[chave].set(rnd.choice(tabela)[0])
        V["cabelo"].set(rnd.choice(list(cat.CABELOS.values()))["nome"])
        for opc in cat.ROSTO_ORDEM:
            V[opc].set(rnd.choice(list(rostos[opc].values())))
        roupa = rnd.choice(list(cat.ROUPAS.values()))
        V["roupa"].set(roupa["nome"])
        for chave, cor in zip(("roupa_cor1", "roupa_cor2", "roupa_cor3"), roupa["cores"]):
            V[chave].set(rnd.choice(cat.CORES_ROUPA)[0] if rnd.random() < 0.5 else cor)
        V["traje"].set(trajes[rnd.choice(list(cat.TRAJES))] if rnd.random() < 0.3 else trajes[""])
        for aid, var in V["acessorios"].items():
            var.set(rnd.random() < 0.15)
        for pintar in p._pers_amostras:
            pintar()
        mudou()

    def abrir_teste():
        import webbrowser
        if PAGINA_TESTE.exists():
            webbrowser.open(PAGINA_TESTE.as_uri())

    botoes = ctk.CTkFrame(opcoes, fg_color="transparent")
    botoes.pack(fill="x", padx=(32, 18), pady=(10, 4))
    ctk.CTkButton(botoes, text="Sortear um visual", height=34, command=sortear).pack(side="left")
    ctk.CTkButton(botoes, text="Abrir a página de teste (no navegador)", height=34, **P.SECUNDARIO, command=abrir_teste).pack(side="left", padx=8)
    if not avatar.pyside_instalado():
        ctk.CTkLabel(f, text="O personagem precisa da biblioteca PySide6 (instale pelo INSTALAR_E_CRIAR_ATALHO.bat). Sem ela, aparece a bolinha.",
                     anchor="w", text_color=tema.AVISO, wraplength=640, justify="left").pack(fill="x", padx=(32, 18), pady=(0, 6))
    ctk.CTkLabel(f, text="Dica: clique no personagem e ele reage; arraste para mudar de lugar; botão direito: acenar, mudar o passeio, esconder.",
                 anchor="w", text_color=tema.TEXTO_FRACO, wraplength=640, justify="left").pack(fill="x", padx=(32, 18), pady=(0, 8))
    renderizar()


def salvar(p, c) -> None:
    """Grava `avatar > ...` no config. Só se a seção foi montada (o usuário abriu a página)."""
    V = getattr(p, "vars_pers", None)
    if not V:
        return
    from . import avatar
    from .personagem import catalogo as cat
    from .personagem import catalogo_animacao as A
    from .personagem.cena import normalizar
    from .personagem.opcoes import escrever_config
    from .personagem.passeio import NOMES_MODO
    trajes = {"": "Nenhuma", **{i: f"{t['universo']} · {t['nome']}" for i, t in cat.TRAJES.items()}}
    modelo = next((k for k, v in avatar.MODELOS.items() if v == V["modelo"].get()), "robo")
    jeito = next((k for k, v in A.ARQUETIPOS.items() if V["jeito"].get().startswith(v["nome"] + " (")), "")
    passeio = next((k for k, v in NOMES_MODO.items() if v == V["passeio"].get()), "personalidade")
    perfil = normalizar({
        "genero": "f" if V["genero"].get() == "Mulher" else "m", "pele": V["pele"].get(), "cabelo_cor": V["cabelo_cor"].get(), "olhos_cor": V["olhos_cor"].get(),
        "cabelo": next((i for i, x in cat.CABELOS.items() if x["nome"] == V["cabelo"].get()), "curto"),
        "roupa": next((i for i, x in cat.ROUPAS.items() if x["nome"] == V["roupa"].get()), "camiseta"),
        "roupa_cor1": V["roupa_cor1"].get(), "roupa_cor2": V["roupa_cor2"].get(), "roupa_cor3": V["roupa_cor3"].get(),
        "traje": next((i for i, n in trajes.items() if n == V["traje"].get()), ""),
        "acessorios": [i for i, v in V["acessorios"].items() if v.get()], "escala": V["escala"].get() / 100,
        **{opc: next((i for i, n in _nomes_rosto(cat)[opc].items() if n == V[opc].get()), "") for opc in cat.ROSTO_ORDEM if opc in V}})
    escrever_config(c, modelo, jeito, passeio, perfil)


def _nomes_rosto(cat) -> dict:
    """{"rosto": {"redondo": "Redondo", ...}, "olhos_estilo": {...}, ...} (id -> nome de cada opção do rosto)."""
    return {opc: {k: v["nome"] for k, v in cat.ROSTO["m"][opc].items()} for opc in cat.ROSTO_ORDEM}
