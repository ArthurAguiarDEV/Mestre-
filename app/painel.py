"""Painel de configuracoes do Mestre: tudo por cliques, sem editar o config.yaml.

Abre pelo atalho "Mestre" (app.central), pelo icone perto do relogio, pelo duplo clique no indicador ou falando
"Mestre, abre o painel".
"""
import queue
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from . import configuracao, estado, icones, personalidades, segredos, sistema, tema, youtube
from .audio import BLOCO, TAXA, Segmentador, Transcritor, aplicar_ganho, nivel, sugerir_limiar
from .config import PASTA_LOGS, PASTA_PROJETO
from .vocabulario import Vocabulario, atalhos_no_disco

ACOES_ROTINA = {
    "acordar_tela": "Ligar a tela",
    "falar": "Falar um texto",
    "data": "Falar a data de hoje",
    "clima": "Falar o clima (cidade opcional)",
    "noticias": "Ler manchetes (quantas)",
    "ler_notas": "Ler minhas anotações",
    "melhorias_pendentes": "Avisar melhorias pendentes",
    "abrir_site": "Abrir site (link ou nome)",
    "abrir_programa": "Abrir programa (nome ou caminho)",
    "abrir_pasta": "Abrir pasta",
    "youtube_ultimo_video": "Último vídeo do canal",
    "youtube_canal": "Abrir canal do YouTube",
    "volume": "Volume (aumentar/diminuir/mudo)",
    "esperar": "Esperar (segundos)",
    "desligar_tela": "Desligar a tela",
    "bloquear": "Bloquear o computador",
    "comando": "Qualquer comando falado",
}
SEM_VALOR = {"acordar_tela", "data", "ler_notas", "melhorias_pendentes", "desligar_tela", "bloquear"}
MODELOS_WHISPER = {
    "tiny": "tiny · muito rápido, erra bastante",
    "base": "base · rápido, erra um pouco",
    "small": "small · equilibrado (recomendado)",
    "medium": "medium · preciso, lento sem placa de vídeo",
    "large-v3-turbo": "large-v3-turbo · o mais preciso (ideal com placa NVIDIA)",
}
VOZES_BASICAS = ["pt-BR-AntonioNeural", "pt-BR-FranciscaNeural", "pt-BR-ThalitaMultilingualNeural",
                 "en-US-AndrewMultilingualNeural", "en-US-BrianMultilingualNeural",
                 "en-US-AvaMultilingualNeural", "en-US-EmmaMultilingualNeural",
                 "fr-FR-RemyMultilingualNeural", "it-IT-GiuseppeMultilingualNeural", "pt-PT-DuarteNeural"]


SECUNDARIO = dict(fg_color=tema.CAMPO, hover_color=tema.SECUNDARIO_HOVER, text_color=tema.TEXTO,
                  border_width=1, border_color=tema.BORDA)
PERIGO = dict(fg_color=tema.PERIGO, hover_color=tema.PERIGO_HOVER, text_color=tema.TEXTO)


def _num(texto, padrao=0) -> int:
    try:
        return int(str(texto).replace("%", "").replace("Hz", "").replace("+", ""))
    except ValueError:
        return padrao


# =====================================================================
#  Pecas reutilizaveis
# =====================================================================
class TabelaChaveValor(ctk.CTkFrame):
    """Lista editavel de pares (ex.: nome falado -> link).

    Aguenta milhares de itens: os dados ficam numa lista e a tela mostra uma
    PAGINA de LIMITE linhas por vez (setas para passar; a busca filtra ao digitar).
    """

    LIMITE = 40

    def __init__(self, master, dados: dict, rotulo_chave: str, rotulo_valor: str, largura_valor=420,
                 testar=None, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self.itens: list[list] = [[str(k), str(v)] for k, v in (dados or {}).items()]
        self.largura_valor = largura_valor
        self.testar = testar          # funcao(chave, valor) do botao "Testar" (opcional)
        self.visiveis: list[tuple] = []
        self._novos: list[int] = []   # adicionados agora: aparecem primeiro
        self.pagina = 0
        self._pool: list[dict] = []   # linhas da tela, reaproveitadas

        busca = ctk.CTkFrame(self, fg_color="transparent")
        busca.pack(fill="x", pady=(0, 4))
        self.var_busca = tk.StringVar()
        ctk.CTkLabel(busca, text="Buscar:", text_color=tema.TEXTO_FRACO).pack(side="left", padx=(4, 2))
        ctk.CTkEntry(busca, textvariable=self.var_busca, width=240,
                     placeholder_text="filtra enquanto você digita").pack(side="left", padx=4)
        ctk.CTkButton(busca, text="✕ Limpar", width=80, **SECUNDARIO,
                      command=lambda: self.var_busca.set("")).pack(side="left", padx=4)
        self.rot_contagem = ctk.CTkLabel(busca, text="", anchor="w", text_color=tema.TEXTO_FRACO)
        self.rot_contagem.pack(side="left", padx=8)
        self.nav_topo = self._navegacao()
        self._espera = None
        self.var_busca.trace_add("write", lambda *_: self._agendar_busca())

        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x")
        self._cabecalho = topo
        ctk.CTkLabel(topo, text=rotulo_chave, width=240, anchor="w", font=tema.fonte(14, True)).pack(side="left", padx=4)
        ctk.CTkLabel(topo, text=rotulo_valor, anchor="w", font=tema.fonte(14, True)).pack(side="left", padx=4)
        self.lista = ctk.CTkFrame(self, fg_color="transparent")
        self.lista.pack(fill="both", expand=True, pady=4)
        self.nav_baixo = self._navegacao()
        self._desenhar()

    def _navegacao(self):
        """◀ Anterior · Página 3 de 48 · Próxima ▶"""
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", pady=2)
        anterior = ctk.CTkButton(barra, text="◀ Anterior", width=100, **SECUNDARIO, command=lambda: self.ir_para(self.pagina - 1))
        anterior.pack(side="left", padx=4)
        rotulo = ctk.CTkLabel(barra, text="", text_color=tema.TEXTO_FRACO)
        rotulo.pack(side="left", padx=8)
        proxima = ctk.CTkButton(barra, text="Próxima ▶", width=100, **SECUNDARIO, command=lambda: self.ir_para(self.pagina + 1))
        proxima.pack(side="left", padx=4)
        return barra, anterior, rotulo, proxima

    def ir_para(self, pagina: int) -> None:
        self._guardar_visiveis()
        self.pagina = pagina
        self._desenhar()
        w = self.master   # volta a rolagem da pagina para o topo da lista
        while w is not None:
            if hasattr(w, "_parent_canvas"):
                w._parent_canvas.yview_moveto(0)
                break
            w = getattr(w, "master", None)

    # --- dados --------------------------------------------------------------
    def _guardar_visiveis(self) -> None:
        """Copia o que foi digitado nas linhas da tela para a lista de dados."""
        for _, ek, ev, i in self.visiveis:
            if self.itens[i] is not None:
                self.itens[i] = [ek.get(), ev.get()]

    def valores(self) -> dict:
        self._guardar_visiveis()
        return {k.strip(): v.strip() for k, v in (x for x in self.itens if x) if k.strip()}

    def quantidade(self) -> int:
        return sum(1 for x in self.itens if x and x[0].strip())

    def adicionar(self, chave: str = "", valor: str = "") -> None:
        """Botao "+ Adicionar": linha nova no topo, com o cursor nela."""
        self._guardar_visiveis()
        self.itens.append([chave, valor])
        self._novos.append(len(self.itens) - 1)
        self.var_busca.set("")          # (a busca redesenha sozinha)
        self.pagina = 0
        self._desenhar()
        if self.visiveis:
            self.visiveis[0][1].focus_set()

    def adicionar_varios(self, novos: dict) -> int:
        """Importacao: junta muitos de uma vez (sem repetir nomes). Devolve quantos entraram."""
        self._guardar_visiveis()
        existentes = {k.strip().lower() for k, _ in (x for x in self.itens if x)}
        n = 0
        for k, v in novos.items():
            if k.strip() and k.strip().lower() not in existentes:
                self.itens.append([k, v])
                existentes.add(k.strip().lower())
                n += 1
        self._desenhar()
        return n

    def apagar_todos(self) -> None:
        self.itens = []
        self._novos = []
        self.visiveis = []
        self.pagina = 0
        self._desenhar()

    def _remover(self, i: int) -> None:
        self._guardar_visiveis()
        self.itens[i] = None
        self._desenhar()

    # --- tela ---------------------------------------------------------------
    def _agendar_busca(self) -> None:
        if self._espera:
            self.after_cancel(self._espera)
        self._espera = self.after(250, self._buscar)

    def _buscar(self) -> None:
        self._espera = None
        self._guardar_visiveis()
        self.pagina = 0
        self._desenhar(guardar=False)

    def _desenhar(self, guardar: bool = False) -> None:
        from .texto import normalizar

        if guardar:
            self._guardar_visiveis()
        self.visiveis = []
        termo = normalizar(self.var_busca.get())
        vivos = [i for i, x in enumerate(self.itens) if x is not None]
        if termo:
            achados = [i for i in vivos if termo in normalizar(self.itens[i][0] + " " + self.itens[i][1])]
        else:
            novos = [i for i in reversed(self._novos) if self.itens[i] is not None]
            achados = novos + [i for i in vivos if i not in set(novos)]
        paginas = max(1, -(-len(achados) // self.LIMITE))
        self.pagina = max(0, min(self.pagina, paginas - 1))
        inicio = self.pagina * self.LIMITE
        mostrar = achados[inicio:inicio + self.LIMITE]
        for k, i in enumerate(mostrar):
            self._linha(k, i)
        for r in self._pool[len(mostrar):]:   # linhas que sobraram nesta pagina: escondidas
            r["frame"].pack_forget()
        total = len(vivos)
        self.rot_contagem.configure(text=f"{len(achados)} encontrado(s) de {total}" if termo else f"{total} item(ns)")
        for barra, anterior, rotulo, proxima in (self.nav_topo, self.nav_baixo):
            if paginas > 1:
                if not barra.winfo_manager():   # estava escondida (lista cabia numa pagina)
                    if barra is self.nav_topo[0]:
                        barra.pack(fill="x", pady=2, before=self._cabecalho)
                    else:
                        barra.pack(fill="x", pady=2)
                rotulo.configure(text=f"Página {self.pagina + 1} de {paginas}")
                anterior.configure(state="normal" if self.pagina > 0 else "disabled")
                proxima.configure(state="normal" if self.pagina < paginas - 1 else "disabled")
            else:
                barra.pack_forget()

    def _linha(self, k: int, i: int) -> None:
        """Mostra o item i na linha k da tela. As linhas sao REAPROVEITADAS (trocar de pagina nao pisca)."""
        if k >= len(self._pool):
            r = {"i": i}
            r["frame"] = ctk.CTkFrame(self.lista, fg_color="transparent")
            r["ek"] = ctk.CTkEntry(r["frame"], width=240)
            r["ek"].pack(side="left", padx=4)
            r["ev"] = ctk.CTkEntry(r["frame"], width=self.largura_valor)
            r["ev"].pack(side="left", padx=4)
            if self.testar:
                ctk.CTkButton(r["frame"], text="Testar", width=64, **SECUNDARIO,
                              command=lambda: self.testar(r["ek"].get().strip(), r["ev"].get().strip())).pack(side="left", padx=4)
            ctk.CTkButton(r["frame"], text="✕", width=32, **PERIGO,
                          command=lambda: self._remover(r["i"])).pack(side="left", padx=4)
            self._pool.append(r)
        r = self._pool[k]
        r["i"] = i
        chave, valor = self.itens[i]
        for campo, texto in ((r["ek"], chave), (r["ev"], valor)):
            if campo.get() != texto:
                campo.delete(0, "end")
                campo.insert(0, texto)
        if not r["frame"].winfo_manager():
            r["frame"].pack(fill="x", pady=2)
        self.visiveis.append((r["frame"], r["ek"], r["ev"], i))


# Secoes "avancadas": comecam fechadas (clique no titulo para abrir). Menos coisa jogada na tela.
RECOLHIDAS = {"Jeitos de chamar", "Atalhos úteis", "Ajustes de captação", "Reconhecimento de voz (Whisper)",
              "Descrição", "Frases", "Projetos guiados", "Vocabulário avançado", "Memória"}


def _dividir_dica(dica: str) -> tuple[str, str]:
    """Explicacao longa: a 1a frase aparece; o resto fica no "mais"."""
    if len(dica) <= 120:
        return dica, ""
    for fim in (". ", ": ", "? "):
        corte = dica.find(fim, 40)
        if 0 < corte < 170:
            return dica[:corte + 1].strip(), dica[corte + 1:].strip()
    return dica, ""


def secao(pagina, texto: str, dica: str = "", recolhida: bool | None = None):
    """Um CARTAO na pagina: titulo, explicacao curta (o resto em "mais ›") e o conteudo.

    Devolve o frame onde os campos da secao entram. As avancadas (RECOLHIDAS) comecam fechadas.
    """
    if recolhida is None:
        recolhida = texto in RECOLHIDAS
    cartao = ctk.CTkFrame(pagina, fg_color=tema.CARTAO, corner_radius=14, border_width=1, border_color=tema.BORDA)
    cartao.pack(fill="x", padx=(4, 10), pady=7)
    topo = ctk.CTkFrame(cartao, fg_color="transparent")
    topo.pack(fill="x", padx=18, pady=(14, 14 if recolhida and not dica else 2))
    ctk.CTkFrame(topo, width=4, height=18, fg_color=tema.ROSA, corner_radius=2).pack(side="left", padx=(0, 10))
    rotulo = ctk.CTkLabel(topo, text=texto, anchor="w", font=tema.fonte(16, True))
    rotulo.pack(side="left")
    corpo = ctk.CTkFrame(cartao, fg_color="transparent")
    if dica:
        curta, resto = _dividir_dica(dica)
        explica = ctk.CTkLabel(cartao, text=curta + ("   mais ›" if resto else ""), anchor="w", justify="left",
                               text_color=tema.TEXTO_FRACO, font=tema.fonte(12), wraplength=780)
        explica.pack(fill="x", padx=(32, 18), pady=(0, 12 if recolhida else 4))
        if resto:
            aberta = [False]

            def mais(_=None):
                aberta[0] = not aberta[0]
                explica.configure(text=dica + "   ‹ menos" if aberta[0] else curta + "   mais ›")
            explica.configure(cursor="hand2")
            explica.bind("<Button-1>", mais)
    aberto = [not recolhida]

    def alternar(_=None):
        aberto[0] = not aberto[0]
        if aberto[0]:
            corpo.pack(fill="x", padx=3, pady=(2, 12))
        else:
            corpo.pack_forget()
        botao.configure(text="Esconder ▴" if aberto[0] else "Mostrar ▾")
    botao = ctk.CTkButton(topo, text="Esconder ▴" if aberto[0] else "Mostrar ▾", width=96, height=28,
                          font=tema.fonte(12), command=alternar, **SECUNDARIO)
    if recolhida:   # (so as avancadas mostram o botao; as outras ficam sempre abertas)
        botao.pack(side="right")
        for w in (topo, rotulo):
            w.configure(cursor="hand2")
            w.bind("<Button-1>", alternar)
    else:   # (padx: o conteudo nao cobre a borda do cartao)
        corpo.pack(fill="x", padx=3, pady=(2, 12))
    corpo.alternar = alternar
    corpo.esta_aberta = lambda: aberto[0]
    return corpo


def titulo(master, texto: str, dica: str = ""):   # (nome antigo)
    return secao(master, texto, dica)


def linha_campo(master, rotulo: str, widget_fabrica, largura_rotulo=230):
    f = ctk.CTkFrame(master, fg_color="transparent")
    f.pack(fill="x", pady=4, padx=(32, 18))
    ctk.CTkLabel(f, text=rotulo, width=largura_rotulo, anchor="w").pack(side="left")
    w = widget_fabrica(f)
    w.pack(side="left", fill="x", expand=True)
    return w


RAIL = 68            # menu lateral fechado: so os icones
RAIL_ABERTO = 236    # com o mouse em cima: icones + nomes
LILAS = "#C3A6F5"
COR_SITUACAO = {"ouvindo": tema.SUCESSO, "pensando": LILAS, "falando": tema.ROSA, "descansando": tema.TEXTO_FRACO,
                "pausado": tema.AVISO, "desligado": tema.TEXTO_FRACO}
ROTULOS_COMANDO = (("OUVI", "#26324a", "#8DB8F7"), ("ENTENDI", "#352a4a", LILAS), ("FIZ", "#1a2a24", tema.SUCESSO))


def _descendentes(w):
    yield w
    for filho in w.winfo_children():
        yield from _descendentes(filho)


def _ligar_eventos(w, **eventos) -> None:
    """Liga eventos no widget e em tudo dentro dele (os do customtkinter tem canvas/rotulo por dentro)."""
    for x in _descendentes(w):
        for sequencia, funcao in eventos.items():
            tk.Misc.bind(x, f"<{sequencia}>", funcao, "+")


def cartao(master, titulo: str, icone: str = "", sub: str = ""):
    """Cartao do Inicio (como os do prototipo): titulo com icone, explicacao curta e o corpo (devolvido)."""
    c = ctk.CTkFrame(master, fg_color=tema.CARTAO, corner_radius=16, border_width=1, border_color=tema.BORDA)
    topo = ctk.CTkFrame(c, fg_color="transparent")
    topo.pack(fill="x", padx=18, pady=(16, 2 if sub else 8))
    if icone:
        ctk.CTkLabel(topo, text="", image=icones.ctk_icone(icone, tema.ROSA, 18), width=20).pack(side="left", padx=(0, 8))
    ctk.CTkLabel(topo, text=titulo, anchor="w", font=tema.fonte(15, True)).pack(side="left")
    if sub:
        ctk.CTkLabel(c, text=sub, anchor="w", justify="left", wraplength=420, text_color=tema.TEXTO_FRACO,
                     font=tema.fonte(12)).pack(fill="x", padx=18, pady=(0, 8))
    corpo = ctk.CTkFrame(c, fg_color="transparent")
    corpo.pack(fill="both", expand=True, padx=18, pady=(0, 16))
    c.corpo = corpo
    return c


class Dica:
    """Balaozinho ao lado do menu (nome e o que tem na pagina). Uma janelinha so, reaproveitada."""

    def __init__(self, raiz):
        self.raiz, self.janela, self._agendado = raiz, None, None

    def agendar(self, onde, titulo: str, texto: str) -> None:
        self.cancelar()
        if tema.testando():
            return   # (teste automatico: nenhuma janela aparece)
        self._agendado = self.raiz.after(650, lambda: self._mostrar(onde(), titulo, texto))

    def _mostrar(self, onde, titulo, texto) -> None:
        self._agendado = None
        try:
            if self.janela is None:
                self.janela = tk.Toplevel(self.raiz)
                self.janela.overrideredirect(True)
                self.janela.attributes("-topmost", True)
                self.janela.configure(bg=tema.BORDA)
                corpo = tk.Frame(self.janela, bg=tema.CAMPO)
                corpo.pack(padx=1, pady=1)
                self._t = tk.Label(corpo, bg=tema.CAMPO, fg=tema.TEXTO, anchor="w", justify="left",
                                   font=(tema.FONTE, 10 + tema.TAMANHO - 14, "bold"))
                self._t.pack(fill="x", padx=10, pady=(7, 0))
                self._x = tk.Label(corpo, bg=tema.CAMPO, fg=tema.TEXTO_FRACO, anchor="w", justify="left", wraplength=260,
                                   font=(tema.FONTE, 9 + tema.TAMANHO - 14))
                self._x.pack(fill="x", padx=10, pady=(1, 8))
            self._t.configure(text=titulo)
            self._x.configure(text=texto)
            self.janela.geometry(f"+{onde[0]}+{onde[1]}")
            self.janela.deiconify()
            self.janela.lift()
        except tk.TclError:
            pass

    def cancelar(self) -> None:
        if self._agendado:
            self.raiz.after_cancel(self._agendado)
            self._agendado = None
        if self.janela is not None:
            try:
                self.janela.withdraw()
            except tk.TclError:
                pass


# =====================================================================
#  Painel
# =====================================================================
class Painel(ctk.CTk):
    def __init__(self):
        tema.aplicar()
        super().__init__()
        largura, altura = 1180, 800
        x = max(0, (self.winfo_screenwidth() - largura) // 2)   # centralizado no monitor principal
        y = max(0, (self.winfo_screenheight() - altura) // 2 - 20)
        x, y = tema.posicao_janela(x, y)
        self.geometry(f"{largura}x{altura}+{x}+{y}")
        self.minsize(980, 660)
        configuracao.migrar()
        self.cfg = configuracao.carregar()
        a = self.cfg.get("assistente") or {}
        self.nome = str(a.get("nome") or "Mestre")
        from .config import palavras_ativacao
        self.palavra = palavras_ativacao(self.cfg)[0].capitalize()   # o que voce FALA para chamar
        self.title(f"{self.nome} · Central")
        self._colocar_icone()
        carregando = ctk.CTkLabel(self, text=f"Abrindo o painel do {self.nome}...", text_color=tema.ROSA,
                                  font=tema.fonte(20, True))
        carregando.place(relx=0.5, rely=0.5, anchor="center")
        self.update()   # a janela aparece JA, com o aviso; o resto e montado em seguida
        self.vocab = Vocabulario()
        self._stream = None
        self._fila_audio: queue.Queue = queue.Queue()
        self._niveis: list[float] = []
        self._gravacao: bytes | None = None
        self._gravando = False
        self._ao_gravar = None        # (cadastro/teste da voz: quem recebe a proxima frase gravada)
        self._voz_extrair = None      # (modelo de reconhecimento da voz, carregado so quando precisa)
        self._cad_frases: list[str] | None = None
        self._transcritores: dict = {}
        self._ultimos_valores: dict = {}   # (_por: so reconfigura widget quando o valor muda)
        self._inicio_novo = None
        self._coletando = False
        self._marca_hist = None
        self._comandos_cache: list[dict] = []
        # nomes das rotinas de quando o painel abriu (ver _salvar_rotinas / configuracao.mesclar_novas_por_nome)
        self._rotinas_iniciais = {str((r or {}).get("nome", "")).strip().lower() for r in (self.cfg.get("rotinas") or [])}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._montar_lateral()
        self._montar_conteudo()
        if configuracao.ultimo_conserto:
            self.aviso.configure(text_color=tema.AVISO, text=(
                "Consertei o config.yaml: a seção " + ", ".join(configuracao.ultimo_conserto) +
                " estava repetida (fiquei com a última). Original em config.yaml.antes_do_conserto."))
        carregando.destroy()
        # paginas sob demanda: cada uma e montada na 1a vez que aparece e depois so troca (instantaneo)
        self.paginas = {nome: (None, info[1]) for nome, info in PAGINAS.items()}
        self._montadas: list[str] = []
        self.mostrar_pagina("Início")
        self._rail.lift()
        self.protocol("WM_DELETE_WINDOW", self._fechar)
        self.after(100, self._atualizar_medidor)
        self.after(1000, self._tique_status)
        escutar_chamados(self)

    def _colocar_icone(self):
        try:
            if sistema.EH_WINDOWS:
                self.iconbitmap(str(Path(__file__).with_name("icone.ico")))
            else:
                self._foto_icone = tk.PhotoImage(file=str(Path(__file__).with_name("icone.png")))
                self.iconphoto(True, self._foto_icone)
        except Exception:
            pass  # sem icone, sem problema

    def trazer_para_frente(self):
        """Outro clique no atalho com o painel ja aberto: so mostra este."""
        self.deiconify()
        self.lift()
        self.attributes("-topmost", True)
        self.after(300, lambda: self.attributes("-topmost", False))
        self.focus_force()

    def _por(self, w, **opcoes) -> None:
        """configure() so quando muda (o Inicio atualiza a cada segundo sem redesenhar nada a toa)."""
        if self._ultimos_valores.get(id(w)) != opcoes:
            w.configure(**opcoes)
            self._ultimos_valores[id(w)] = opcoes

    # --- menu lateral compacto (so icones; abre com o mouse em cima) ------------
    def _montar_lateral(self):
        from .atualizar import versao_atual
        from .ponte import VERSAO_EXTENSAO
        self.versao = versao_atual()
        escala = ctk.ScalingTracker.get_widget_scaling(self)
        self._rail_fechado, self._rail_aberto = round(RAIL * escala), round(RAIL_ABERTO * escala)
        self._rail_largura = self._rail_alvo = self._rail_fechado
        self._rail_anim = self._rail_abrir = self._rail_vigia = None
        self._dica = Dica(self)
        # o espaco do menu fechado fica reservado; o menu aberto passa POR CIMA do conteudo (nada se mexe)
        tk.Frame(self, width=self._rail_fechado, bg=tema.LATERAL, highlightthickness=0, bd=0).grid(
            row=0, column=0, sticky="ns")
        self._rail = tk.Frame(self, bg=tema.LATERAL, highlightthickness=0, bd=0)
        self._rail.place(x=0, y=0, relheight=1, width=self._rail_fechado)
        dentro = tk.Frame(self._rail, bg=tema.LATERAL, highlightthickness=0, bd=0)
        dentro.place(x=0, y=0, relheight=1, width=self._rail_aberto)   # largura fixa: o menu so "recorta"
        tk.Frame(self._rail, bg=tema.BORDA, width=1, highlightthickness=0, bd=0).place(
            relx=1, x=-1, y=0, relheight=1, width=1)
        # marca (icone do programa + nome); o nome comeca depois da parte visivel do menu fechado
        marca = ctk.CTkFrame(dentro, fg_color="transparent")
        marca.pack(fill="x", pady=(16, 8))
        self._logo = ctk.CTkImage(icones.logo(tema.ROSA, 128), size=(36, 36))
        ctk.CTkLabel(marca, text="", image=self._logo, width=48).pack(side="left", padx=(10, 0))
        ctk.CTkLabel(marca, text=self.nome, anchor="w", font=tema.fonte(17, True)).pack(side="left", padx=(16, 0))
        # rodape: versao do projeto e da extensao
        pe = ctk.CTkFrame(dentro, fg_color="transparent")
        pe.pack(side="bottom", fill="x", pady=(6, 14))
        ctk.CTkLabel(pe, text=self.versao, width=48, height=22, corner_radius=11, fg_color=tema.ROSA_FUNDO,
                     text_color=tema.ROSA, font=tema.fonte(11, True)).pack(side="left", padx=(10, 0))
        self.rot_versao = ctk.CTkLabel(pe, text=f"Versão {self.versao} · extensão {VERSAO_EXTENSAO}", anchor="w",
                                       text_color=tema.TEXTO_FRACO, font=tema.fonte(11))
        self.rot_versao.pack(side="left", padx=(16, 0))
        menu = ctk.CTkScrollableFrame(dentro, fg_color=tema.LATERAL, corner_radius=0,
                                      scrollbar_button_color=tema.LATERAL,
                                      scrollbar_button_hover_color=tema.SECUNDARIO_HOVER)
        menu.pack(fill="both", expand=True)
        self.botoes_menu, self._rotulos_menu = {}, {}
        for grupo, nomes in GRUPOS_MENU:
            g = ctk.CTkFrame(menu, fg_color="transparent", height=22)
            g.pack(fill="x", pady=(8, 1))
            ctk.CTkFrame(g, width=20, height=2, corner_radius=1, fg_color=tema.BORDA).pack(side="left", padx=(24, 0))
            ctk.CTkLabel(g, text=grupo, anchor="w", height=18, text_color=tema.TEXTO_FRACO,
                         font=tema.fonte(10, True)).pack(side="left", padx=(28, 0))
            for nome in nomes:
                self._item_menu(menu, nome)
        _ligar_eventos(self._rail, Enter=self._rail_entrou)

    def _item_menu(self, menu, nome: str):
        icone, descricao = PAGINAS[nome][0], PAGINAS[nome][1]
        linha = ctk.CTkFrame(menu, fg_color="transparent")
        linha.pack(fill="x", pady=1)
        bt = ctk.CTkButton(linha, text="", image=icones.ctk_icone(icone, tema.TEXTO_FRACO, 21), width=48, height=40,
                           corner_radius=12, fg_color="transparent", hover_color=tema.CARTAO,
                           command=lambda: self.mostrar_pagina(nome))
        bt.pack(side="left", padx=(10, 0))
        rot = ctk.CTkLabel(linha, text=nome, anchor="w", text_color=tema.TEXTO_FRACO, font=tema.fonte(13), cursor="hand2")
        rot.pack(side="left", fill="x", expand=True, padx=(16, 0))
        self.botoes_menu[nome], self._rotulos_menu[nome] = bt, rot

        def entrar(_=None):
            if nome != getattr(self, "pagina_atual", None):
                self._por(bt, fg_color=tema.CARTAO)
                self._por(rot, text_color=tema.TEXTO)
            self._dica.agendar(lambda: (self._rail.winfo_rootx() + self._rail_largura + 8, linha.winfo_rooty()),
                               nome, descricao)

        def sair(_=None):
            if nome != getattr(self, "pagina_atual", None):
                self._por(bt, fg_color="transparent")
                self._por(rot, text_color=tema.TEXTO_FRACO)
            self._dica.cancelar()
        _ligar_eventos(linha, Enter=entrar, Leave=sair)
        for w in (linha, rot):   # (o botao do icone ja tem o command)
            _ligar_eventos(w, **{"Button-1": lambda _=None: self.mostrar_pagina(nome)})

    def _marcar_item(self, nome: str, ativo: bool):
        cor = tema.ROSA if ativo else tema.TEXTO_FRACO
        self._por(self.botoes_menu[nome], fg_color=tema.ROSA_FUNDO if ativo else "transparent",
                  hover_color=tema.ROSA_FUNDO if ativo else tema.CARTAO,
                  image=icones.ctk_icone(PAGINAS[nome][0], cor, 21))
        self._por(self._rotulos_menu[nome], text_color=cor, font=tema.fonte(13, ativo))

    def _rail_entrou(self, _=None):
        if self._rail_alvo != self._rail_aberto and self._rail_abrir is None:
            self._rail_abrir = self.after(90, self._rail_expandir)   # (passar rapido por cima nao abre)
        if self._rail_vigia is None:
            self._rail_vigia = self.after(100, self._vigiar_rail)

    def _rail_expandir(self):
        self._rail_abrir = None
        self._rail_ir(self._rail_aberto)

    def _ponteiro_no_rail(self) -> bool:
        try:
            x, y = self.winfo_pointerxy()
            rx, ry = self._rail.winfo_rootx(), self._rail.winfo_rooty()
            return rx <= x < rx + self._rail_largura and ry <= y < ry + self._rail.winfo_height()
        except tk.TclError:
            return False

    def _vigiar_rail(self):
        """Enquanto o mouse esta no menu, confere a cada 0,1 s; saiu = fecha (so roda nesse tempo)."""
        if self._ponteiro_no_rail():
            self._rail_vigia = self.after(100, self._vigiar_rail)
            return
        self._rail_vigia = None
        if self._rail_abrir is not None:
            self.after_cancel(self._rail_abrir)
            self._rail_abrir = None
        self._dica.cancelar()
        self._rail_ir(self._rail_fechado)

    def _rail_ir(self, alvo: int):
        self._rail_alvo = alvo
        if alvo == self._rail_aberto:
            self._rail.lift()
        if self._rail_anim is None:
            self._rail_passo()

    def _rail_passo(self):
        """Animacao curta (~0,1 s): so muda a largura de UM quadro; o conteudo do menu nao e redesenhado."""
        falta = self._rail_alvo - self._rail_largura
        if abs(falta) <= 3:
            self._rail_largura = self._rail_alvo
        else:
            self._rail_largura += int(falta * 0.5)
        self._rail.place_configure(width=self._rail_largura)
        self._rail_anim = self.after(12, self._rail_passo) if self._rail_largura != self._rail_alvo else None

    # --- conteudo: cabecalho, pagina e rodape ------------------------------------
    def _montar_conteudo(self):
        conteudo = ctk.CTkFrame(self, fg_color=tema.FUNDO, corner_radius=0)
        conteudo.grid(row=0, column=1, sticky="nsew")
        conteudo.grid_columnconfigure(0, weight=1)
        conteudo.grid_rowconfigure(1, weight=1)
        self._conteudo = conteudo
        cabecalho = ctk.CTkFrame(conteudo, fg_color="transparent")
        cabecalho.grid(row=0, column=0, sticky="ew", padx=28, pady=(20, 8))
        direita = ctk.CTkFrame(cabecalho, fg_color="transparent")
        direita.pack(side="right", anchor="n", pady=6)
        self.status_lateral = ctk.CTkLabel(direita, text="", anchor="e", font=tema.fonte(12))
        self.status_lateral.pack(side="left", padx=(0, 12))
        ctk.CTkLabel(direita, text=f"v{self.versao}", width=54, height=26, corner_radius=13, fg_color=tema.ROSA_FUNDO,
                     text_color=tema.ROSA, font=tema.fonte(12, True)).pack(side="left")
        caixa = ctk.CTkFrame(cabecalho, width=46, height=46, corner_radius=13, fg_color=tema.ROSA_FUNDO)
        caixa.pack(side="left", padx=(0, 14))
        caixa.pack_propagate(False)
        self.icone_pagina = ctk.CTkLabel(caixa, text="", image=icones.ctk_icone("casa", tema.ROSA, 22))
        self.icone_pagina.pack(expand=True)
        textos = ctk.CTkFrame(cabecalho, fg_color="transparent")
        textos.pack(side="left", fill="x", expand=True)
        self.titulo_pagina = ctk.CTkLabel(textos, text="", anchor="w", height=30, font=tema.fonte(22, True))
        self.titulo_pagina.pack(fill="x")
        self.subtitulo_pagina = ctk.CTkLabel(textos, text="", anchor="w", height=18, text_color=tema.TEXTO_FRACO,
                                             font=tema.fonte(13))
        self.subtitulo_pagina.pack(fill="x")

        rodape = ctk.CTkFrame(conteudo, fg_color=tema.LATERAL, corner_radius=0, height=64)
        rodape.grid(row=2, column=0, sticky="ew")
        self.aviso = ctk.CTkLabel(rodape, text="As mudanças só valem depois de salvar.", text_color=tema.TEXTO_FRACO)
        self.aviso.pack(side="left", padx=24, pady=16)
        ctk.CTkButton(rodape, text=f"✓  Salvar e reiniciar o {self.nome}", height=40, width=240, corner_radius=20,
                      font=tema.fonte(14, True),
                      command=lambda: self.salvar(reiniciar=True)).pack(side="right", padx=(6, 24), pady=12)
        ctk.CTkButton(rodape, text="Salvar", height=40, width=110, corner_radius=20, **SECUNDARIO,
                      command=self.salvar).pack(side="right", padx=6, pady=12)

    def _garantir_pagina(self, nome: str):
        """Monta a pagina na primeira vez (sob demanda) e guarda: nas proximas vezes so troca."""
        frame, descricao = self.paginas[nome]
        if frame is None:
            frame = ctk.CTkScrollableFrame(self._conteudo, fg_color="transparent")
            PAGINAS[nome][2](self, frame)
            self.paginas[nome] = (frame, descricao)
            self._montadas.append(nome)
        return frame

    def montar_todas(self):
        """Monta todas as paginas (o teste automatico usa para conferir todos os textos)."""
        for nome in PAGINAS:
            self._garantir_pagina(nome)

    def mostrar_pagina(self, nome: str):
        anterior = getattr(self, "pagina_atual", None)
        if anterior and anterior != nome:
            self._marcar_item(anterior, False)
        if self.paginas[nome][0] is None and hasattr(self, "titulo_pagina"):
            # 1a vez: o menu e o titulo respondem ja; a pagina e montada logo em seguida
            self._marcar_item(nome, True)
            self._por(self.titulo_pagina, text=nome)
            self._por(self.subtitulo_pagina, text="Abrindo...")
            self.update_idletasks()
        frame = self._garantir_pagina(nome)
        # as paginas ja montadas ficam todas no mesmo lugar, uma em cima da outra: trocar e so trazer a
        # escolhida para a frente (esconder/mostrar faria o customtkinter redesenhar a pagina inteira)
        if not frame.grid_info():
            frame.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 8))
        frame.lift()
        self._marcar_item(nome, True)
        self.pagina_atual = nome
        icone, descricao = PAGINAS[nome][0], PAGINAS[nome][1]
        self._por(self.icone_pagina, image=icones.ctk_icone(icone, tema.ROSA, 22))
        self._por(self.titulo_pagina, text=nome)
        self._por(self.subtitulo_pagina, text=descricao)
        if nome == "Sugestões de melhoria" and hasattr(self, "_sug_linhas"):
            self._sug_recarregar()

    def _sec(self, nome: str) -> dict:
        return self.cfg.get(nome) or {}

    # -----------------------------------------------------------------
    #  Inicio: cartoes (status + avatar, fila do pensando, atalhos, ultimos comandos)
    # -----------------------------------------------------------------
    def _aba_inicio(self, pagina):
        grade = ctk.CTkFrame(pagina, fg_color="transparent")
        grade.pack(fill="x", padx=(4, 10), pady=(4, 0))
        grade.grid_columnconfigure((0, 1), weight=1, uniform="inicio")
        self._cartao_status(grade).grid(row=0, column=0, columnspan=2, sticky="nsew", pady=(0, 7))
        self._cartao_fila(grade).grid(row=1, column=0, sticky="nsew", padx=(0, 7), pady=7)
        self._cartao_atalhos(grade).grid(row=1, column=1, sticky="nsew", padx=(7, 0), pady=7)
        self._cartao_comandos(grade).grid(row=2, column=0, columnspan=2, sticky="nsew", pady=7)
        self._inicio_novidades(pagina)
        self._inicio_jeitos_de_chamar(pagina)
        self._inicio_atalhos_uteis(pagina)
        self._aplicar_inicio(self._coletar_inicio())   # (a 1a vez aqui mesmo: a pagina ja abre preenchida)

    def _cartao_status(self, master):
        c = ctk.CTkFrame(master, fg_color=tema.CARTAO, corner_radius=16, border_width=1, border_color=tema.BORDA)
        linha = ctk.CTkFrame(c, fg_color="transparent")
        linha.pack(fill="x", padx=20, pady=(18, 6))
        # lugar do avatar: por enquanto um desenho parado (o robo animado entra aqui depois)
        self.avatar_area = ctk.CTkFrame(linha, width=150, height=150, fg_color="transparent")
        self.avatar_area.pack(side="left", anchor="n")
        self.avatar_area.pack_propagate(False)
        self._avatar_img = ctk.CTkImage(icones.avatar(tema.ROSA), size=(140, 140))
        ctk.CTkLabel(self.avatar_area, text="", image=self._avatar_img).pack(expand=True)
        lado = ctk.CTkFrame(linha, fg_color="transparent")
        lado.pack(side="left", fill="both", expand=True, padx=(20, 0))
        self.status_mestre = ctk.CTkLabel(lado, text="", anchor="w", font=tema.fonte(26, True))
        self.status_mestre.pack(fill="x", pady=(8, 0))
        self.status_detalhe = ctk.CTkLabel(lado, text="", anchor="w", justify="left", wraplength=600,
                                           text_color=tema.TEXTO_FRACO)
        self.status_detalhe.pack(fill="x")
        botoes = ctk.CTkFrame(lado, fg_color="transparent")
        botoes.pack(fill="x", pady=(14, 4))
        grande = dict(height=42, width=140, corner_radius=12, font=tema.fonte(14, True), compound="left")
        self.bt_ligar = ctk.CTkButton(botoes, text=" Ligar", image=icones.ctk_icone("play", tema.TEXTO_NO_ROSA, 16),
                                      command=self._ligar_mestre, **grande)
        self.bt_ligar.pack(side="left")
        ctk.CTkButton(botoes, text=" Desligar", image=icones.ctk_icone("parar", tema.TEXTO, 16), **PERIGO, **grande,
                      command=self._desligar_mestre).pack(side="left", padx=(8, 0))
        from .versao import DATA
        ctk.CTkLabel(botoes, text=f"Versão {self.versao} ({DATA})", text_color=tema.TEXTO_FRACO,
                     font=tema.fonte(12)).pack(side="left", padx=14)
        self.var_ligar_ao_abrir = tk.BooleanVar(value=bool(self._sec("central").get("ligar_mestre_ao_abrir", True)))
        ctk.CTkSwitch(lado, text=f"Ligar o {self.nome} sozinho quando eu abrir a Central (atalho da área de trabalho)",
                      variable=self.var_ligar_ao_abrir).pack(anchor="w", pady=(6, 0))
        ctk.CTkLabel(c, text=f"Mudou alguma configuração? Clique em “Salvar e reiniciar o {self.nome}” (embaixo). "
                             "O config.yaml é atualizado sozinho, com cópia de segurança (config.yaml.bak).",
                     anchor="w", justify="left", wraplength=820, text_color=tema.TEXTO_FRACO,
                     font=tema.fonte(12)).pack(fill="x", padx=20, pady=(4, 16))
        return c

    def _cartao_fila(self, master):
        c = cartao(master, "Fila do pensando", "brilho", "Pedidos que a IA está resolvendo em segundo plano.")
        self._fila_linhas = []
        for _ in range(4):   # (no maximo 4 na tela; o resto vira "+ N na fila")
            fr = ctk.CTkFrame(c.corpo, fg_color="transparent")
            topo = ctk.CTkFrame(fr, fg_color="transparent")
            topo.pack(fill="x")
            chip = ctk.CTkLabel(topo, text="", width=78, height=22, corner_radius=11, font=tema.fonte(11, True))
            chip.pack(side="right", padx=(8, 0))
            texto = ctk.CTkLabel(topo, text="", anchor="w", justify="left", wraplength=300)
            texto.pack(side="left", fill="x", expand=True)
            barra = ctk.CTkProgressBar(fr, height=5, progress_color=LILAS)
            barra.pack(fill="x", pady=(5, 8))
            self._fila_linhas.append({"frame": fr, "texto": texto, "chip": chip, "barra": barra})
        self.rot_fila_vazia = ctk.CTkLabel(c.corpo, text="Nada na fila agora. Quando a IA demorar, o pedido aparece aqui.",
                                           anchor="w", justify="left", wraplength=380, text_color=tema.TEXTO_FRACO)
        self.rot_fila_mais = ctk.CTkLabel(c.corpo, text="", anchor="w", text_color=tema.TEXTO_FRACO, font=tema.fonte(12))
        return c

    def _cartao_atalhos(self, master):
        c = cartao(master, "Atalhos rápidos", "atalho")
        grade = ctk.CTkFrame(c.corpo, fg_color="transparent")
        grade.pack(fill="both", expand=True)
        grade.grid_columnconfigure((0, 1, 2), weight=1, uniform="atalho")
        estilo = dict(height=70, corner_radius=14, compound="top", fg_color=tema.CAMPO, border_width=1,
                      border_color=tema.BORDA, hover_color=tema.SECUNDARIO_HOVER, text_color=tema.TEXTO,
                      font=tema.fonte(12))
        itens = [("Reiniciar", "reiniciar", self._reiniciar_mestre),
                 ("Pausar", "pausa", self._alternar_pausa),
                 ("Validar atualização", "check", lambda: self.mostrar_pagina("Validar atualização")),
                 ("Sugestões", "brilho", lambda: self.mostrar_pagina("Sugestões de melhoria")),
                 ("Testar digitando", "teclado", self._testar_por_texto),
                 ("Teste automático", "chip", self._teste_automatico),
                 ("Atualizar (.zip)", "baixar", self._atualizar_por_zip),
                 ("Ouvir a voz", "alto", lambda: self.mostrar_pagina("Voz")),
                 ("Microfone", "mic", lambda: self.mostrar_pagina("Áudio"))]
        for i, (texto, icone, cmd) in enumerate(itens):
            b = ctk.CTkButton(grade, text=texto, image=icones.ctk_icone(icone, tema.ROSA, 22), command=cmd, **estilo)
            b.grid(row=i // 3, column=i % 3, sticky="nsew", padx=4, pady=4)
            if icone == "pausa":
                self.bt_pausa = b
        return c

    def _cartao_comandos(self, master):
        c = cartao(master, "Últimos comandos", "historico", "O que ele ouviu, entendeu e fez (os mais novos em cima).")
        self._cmd_linhas = []
        for i in range(5):   # (5 linhas fixas: so o texto muda)
            fr = ctk.CTkFrame(c.corpo, fg_color="transparent")
            if i:
                ctk.CTkFrame(fr, height=1, fg_color=tema.BORDA).pack(fill="x", pady=(0, 8))
            hora = ctk.CTkLabel(fr, text="", width=52, anchor="ne", text_color=tema.TEXTO_FRACO, font=tema.fonte(12))
            hora.pack(side="right", anchor="n")
            textos = {}
            for rotulo, fundo, cor in ROTULOS_COMANDO:
                l = ctk.CTkFrame(fr, fg_color="transparent")
                l.pack(fill="x", pady=1)
                ctk.CTkLabel(l, text=rotulo, width=70, height=20, corner_radius=6, fg_color=fundo, text_color=cor,
                             font=tema.fonte(10, True)).pack(side="left", anchor="n", pady=1)
                t = ctk.CTkLabel(l, text="", anchor="w", justify="left", wraplength=720)
                t.pack(side="left", fill="x", expand=True, padx=(10, 0))
                textos[rotulo] = t
            self._cmd_linhas.append({"frame": fr, "hora": hora, **textos})
        self.rot_cmd_vazio = ctk.CTkLabel(c.corpo, text="Ainda não tem comandos. Fale com ele e eles aparecem aqui.",
                                          anchor="w", text_color=tema.TEXTO_FRACO)
        ctk.CTkButton(c.corpo, text="Ver o histórico completo", width=190, height=30, **SECUNDARIO,
                      command=lambda: self.mostrar_pagina("Histórico")).pack(side="bottom", anchor="w", pady=(10, 0))
        return c

    def _inicio_novidades(self, pagina):
        f = secao(pagina, f"Novidades da versão {self.versao}", "O que mudou no painel:")
        dicas = [("Menu com ícones", "passe o mouse na barra da esquerda: ela abre mostrando os nomes"),
                 ("Início em cartões", "o que ele está fazendo agora, a fila do pensando e os últimos comandos"),
                 ("Últimos comandos", "OUVI / ENTENDI / FIZ de cada pedido, atualizando sozinho"),
                 ("Voz em abas", "uma aba por voz: Ativar esta voz, Testar e Usar como reserva"),
                 ("Voz reserva", "se a voz ativa falhar, ele fala com a reserva que você escolheu"),
                 ("Painel mais leve", "cada página só é montada quando você abre; trocar de página é na hora")]
        for frase, explica in dicas:
            linha = ctk.CTkFrame(f, fg_color="transparent")
            linha.pack(fill="x", padx=(32, 18), pady=2)
            ctk.CTkLabel(linha, text=frase, anchor="w", width=200, text_color=tema.ROSA,
                         font=tema.fonte(13, True)).pack(side="left")
            ctk.CTkLabel(linha, text=explica, anchor="w", text_color=tema.TEXTO_FRACO).pack(side="left")

    def _inicio_jeitos_de_chamar(self, pagina):
        w = self.palavra
        f = secao(pagina, "Jeitos de chamar", "Todos funcionam. Os da direita também tiram do modo descanso "
                                              f"(“{w}, pode descansar”).")
        chamar = [f"{w}", f"E aí, {w}", f"Fala, {w}", f"Ô {w}", f"Oi, {w}", f"Meu {w}", f"Fala, meu {w}",
                  f"E aí, meu {w}, tá por aí?", f"{w}, tá aí?", f"{w}, tá me ouvindo?", f"Salve, {w}", f"Opa, {w}",
                  f"Beleza, {w}?", f"{w}, na escuta?", f"{w}, presente?", f"{w}, bora", f"{w}, preciso de você",
                  f"{w}, me ajuda", f"{w}, cadê você?", f"{w}, bom dia", f"{w}, bora trabalhar"]
        voltar = [f"{w}, volta", "Bora voltar a trabalhar", "Bora voltar", f"{w}, voltei", f"{w}, fim do descanso",
                  f"{w}, hora de trabalhar", f"{w}, acorda", f"{w}, modo trabalho", f"{w}, voltamos"]
        grade = ctk.CTkFrame(f, fg_color="transparent")
        grade.pack(fill="x", padx=(32, 18))
        for i, frase in enumerate(chamar):
            ctk.CTkLabel(grade, text=f"{i + 1}. {frase}", anchor="w", text_color=tema.TEXTO).grid(
                row=i % 11, column=i // 11, sticky="w", padx=(0, 24))
        for j, frase in enumerate(voltar):
            ctk.CTkLabel(grade, text=f"{len(chamar) + j + 1}. {frase}", anchor="w", text_color=tema.ROSA).grid(
                row=j, column=2, sticky="w")

    def _inicio_atalhos_uteis(self, pagina):
        f = secao(pagina, "Atalhos úteis")
        util = ctk.CTkFrame(f, fg_color="transparent")
        util.pack(fill="x", padx=(32, 18))
        for texto, alvo in [("Abrir o guia", PASTA_PROJETO / "GUIA_PASSO_A_PASSO.md"),
                            ("Ver o diário (log)", PASTA_LOGS / "mestre.log"),
                            ("Áudios de diagnóstico", PASTA_LOGS / "audios"),
                            ("Áudios de feedback", PASTA_LOGS / "feedback"),
                            (f"Pasta do {self.nome}", PASTA_PROJETO)]:
            ctk.CTkButton(util, text=texto, **SECUNDARIO,
                          command=lambda a=alvo: sistema.abrir_arquivo(a) if Path(a).exists()
                          else messagebox.showinfo(self.nome, "Ainda não existe.")).pack(side="left", padx=(0, 8))

    # --- status: le em segundo plano, aplica na tela sem recriar nada -------------
    def _coletar_inicio(self) -> dict:
        """Roda FORA da linha do tkinter (menos a 1a vez): arquivos do Assessor, nada de widget aqui."""
        from . import memoria, validacao

        rodando = sistema.mestre_ligado()
        pausado = estado.pausado()
        agora = estado.ler_de_fora() if rodando else {}

        def mudou_em(arquivo):
            try:
                return arquivo.stat().st_mtime
            except OSError:
                return 0.0
        marca = (mudou_em(memoria.ARQUIVO_HISTORICO), mudou_em(memoria.ARQUIVO_OUVIDO))
        if marca != self._marca_hist:   # so rele o historico quando ele muda
            self._comandos_cache = validacao.ultimos_comandos(5)
            self._marca_hist = marca
        return {"rodando": rodando, "pausado": pausado, "agora": agora, "comandos": self._comandos_cache,
                "situacao": estado.situacao(agora, rodando, pausado)}

    def _coletar_em_fundo(self):
        try:
            self._inicio_novo = self._coletar_inicio()
        except Exception:
            pass
        finally:
            self._coletando = False

    def _aplicar_se_novo(self):
        novo, self._inicio_novo = self._inicio_novo, None
        if novo is not None:
            self._aplicar_inicio(novo)

    def _status(self):
        """Pede uma leitura agora (depois de ligar, pausar...) e mostra em seguida."""
        if not self._coletando:
            self._coletando = True
            threading.Thread(target=self._coletar_em_fundo, daemon=True).start()
        self.after(200, self._aplicar_se_novo)

    def _tique_status(self):
        """A cada ~1 s: o Inicio e a bolinha do topo acompanham o Assessor sozinhos."""
        try:
            self._aplicar_se_novo()
            self._status()
        finally:
            self.after(1000, self._tique_status)

    def _aplicar_inicio(self, d: dict):
        situacao, rodando, pausado = d["situacao"], d["rodando"], d["pausado"]
        titulo, detalhe = estado.SITUACOES[situacao]
        cor = COR_SITUACAO[situacao]
        self._por(self.status_lateral, text=f"●  {titulo}", text_color=cor)
        if not hasattr(self, "status_mestre"):
            return   # (o Inicio ainda nao foi montado)
        agora = d["agora"]
        lista = list(agora.get("pensamentos_lista") or [])
        if situacao == "ouvindo":
            detalhe = f"Pode falar: diga “{self.palavra}” e o pedido."
        elif situacao == "pensando":
            n = sum(1 for p in lista if p.get("estado") == "pensando") or 1
            detalhe = f"A IA está trabalhando em {n} pedido{'s' if n > 1 else ''} (fila abaixo)."
        elif situacao == "falando" and agora.get("ultima_resposta"):
            detalhe = f"“{str(agora['ultima_resposta'])[:140]}”"
        elif situacao == "desligado":
            detalhe = ("Clique em “Ligar” para ele começar a ouvir. Ligado, ele também aparece perto do relógio "
                       "do Windows.")
        self._por(self.status_mestre, text=titulo, text_color=cor)
        self._por(self.status_detalhe, text=detalhe)
        self._por(self.bt_ligar, state="disabled" if rodando else "normal")
        self._por(self.bt_pausa, text="Retomar" if pausado else "Pausar", state="normal" if rodando else "disabled",
                  image=icones.ctk_icone("play" if pausado else "pausa", tema.ROSA, 22))
        self._aplicar_fila(lista)
        self._aplicar_comandos(d["comandos"])

    def _aplicar_fila(self, lista: list[dict]):
        agora = time.time()
        for i, linha in enumerate(self._fila_linhas):
            if i < len(lista):
                p = lista[i]
                pensando = p.get("estado") == "pensando"
                segundos = max(0, int(agora - float(p.get("inicio") or agora)))
                self._por(linha["texto"], text=f"“{str(p.get('pergunta') or '')[:120]}”")
                self._por(linha["chip"], text=f"pensando {segundos}s" if pensando else "pronto",
                          fg_color=tema.ROSA_FUNDO if pensando else "#1a2a24",
                          text_color=LILAS if pensando else tema.SUCESSO)
                self._por(linha["barra"], progress_color=LILAS if pensando else tema.SUCESSO)
                linha["barra"].set(min(0.95, segundos / 120) if pensando else 1.0)
                if not linha["frame"].winfo_manager():
                    depois = [w for w in (self.rot_fila_vazia, self.rot_fila_mais) if w.winfo_manager()]
                    linha["frame"].pack(fill="x", **({"before": depois[0]} if depois else {}))
            elif linha["frame"].winfo_manager():
                linha["frame"].pack_forget()
        vazia = not lista
        if vazia and not self.rot_fila_vazia.winfo_manager():
            self.rot_fila_vazia.pack(fill="x")
        elif not vazia and self.rot_fila_vazia.winfo_manager():
            self.rot_fila_vazia.pack_forget()
        mais = len(lista) - len(self._fila_linhas)
        self._por(self.rot_fila_mais, text=f"+ {mais} na fila" if mais > 0 else "")
        if mais > 0 and not self.rot_fila_mais.winfo_manager():
            self.rot_fila_mais.pack(fill="x")
        elif mais <= 0 and self.rot_fila_mais.winfo_manager():
            self.rot_fila_mais.pack_forget()

    def _aplicar_comandos(self, comandos: list[dict]):
        for i, linha in enumerate(self._cmd_linhas):
            if i < len(comandos):
                c = comandos[i]
                self._por(linha["hora"], text=c["hora"])
                for rotulo, chave in (("OUVI", "ouvi"), ("ENTENDI", "entendi"), ("FIZ", "fiz")):
                    self._por(linha[rotulo], text=str(c[chave])[:200])
                if not linha["frame"].winfo_manager():
                    linha["frame"].pack(fill="x", pady=(0, 8),
                                        **({"before": self.rot_cmd_vazio} if self.rot_cmd_vazio.winfo_manager() else {}))
            elif linha["frame"].winfo_manager():
                linha["frame"].pack_forget()
        if comandos and self.rot_cmd_vazio.winfo_manager():
            self.rot_cmd_vazio.pack_forget()
        elif not comandos and not self.rot_cmd_vazio.winfo_manager():
            self.rot_cmd_vazio.pack(fill="x")

    def _ligar_mestre(self):
        if not sistema.mestre_ligado():
            estado.pausar(False)
            sistema.iniciar_mestre()
        self.aviso.configure(text="Ligando... A primeira fala dele avisa que está pronto.", text_color=tema.TEXTO_FRACO)
        self.after(2500, self._status)

    def _reiniciar_mestre(self):
        sistema.reiniciar_mestre()
        self.after(2500, self._status)

    def _desligar_mestre(self):
        sistema.parar_mestre()
        self.after(500, self._status)

    def _alternar_pausa(self):
        estado.pausar(not estado.pausado())
        self._status()

    def _testar_por_texto(self):
        python = PASTA_PROJETO / "venv" / "Scripts" / "python.exe"
        sistema.abrir_terminal_com(f'"{python}" -m app.main --texto', PASTA_PROJETO, f"{self.nome} - testar digitando")

    def _teste_automatico(self):
        python = PASTA_PROJETO / "venv" / "Scripts" / "python.exe"
        sistema.abrir_terminal_com(f'"{python}" -m testes.teste_basico', PASTA_PROJETO, f"{self.nome} - teste automatico")

    def _atualizar_por_zip(self):
        from . import atualizar

        zip_ = filedialog.askopenfilename(title=f"Escolha o arquivo de atualização do {self.nome}",
                                          filetypes=[("Atualização do Mestre", "*.zip")])
        if not zip_:
            return
        problema = atualizar.verificar(zip_)
        if problema:
            messagebox.showerror(self.nome, problema)
            return
        if not messagebox.askyesno(self.nome, "Atualizar agora?\n\nSuas configurações, notas e melhorias ficam "
                                             f"como estão. O {self.nome} e esta janela vão reiniciar sozinhos."):
            return
        self.aviso.configure(text="Atualizando... (pode levar 1 ou 2 minutos se tiver biblioteca nova)",
                             text_color=tema.AVISO)
        estava_ligado = sistema.mestre_ligado()

        def trabalho():
            try:
                resumo = atualizar.aplicar(zip_)
            except Exception as erro:
                self.after(0, lambda e=erro: messagebox.showerror(self.nome, f"A atualização falhou:\n{e}"))
                return
            self.after(0, lambda: self._depois_de_atualizar(resumo, estava_ligado))
        threading.Thread(target=trabalho, daemon=True).start()

    def _depois_de_atualizar(self, resumo: str, estava_ligado: bool):
        messagebox.showinfo(self.nome, resumo + "\n\nA Central vai reabrir agora.")
        if estava_ligado:
            sistema.reiniciar_mestre()
        self._fechar()
        sistema.abrir_painel()

    # -----------------------------------------------------------------
    def _aba_audio(self, pagina):
        f = pagina   # (cada secao abaixo troca f pelo cartao dela)
        o = self._sec("ouvido")
        f = secao(pagina, "Microfone")
        try:
            from .ouvido import listar_microfones
            mics = [f"{i} · {n}" for i, n in listar_microfones()]
        except Exception:
            mics = []
        opcoes = ["Padrão do Windows"] + mics
        atual = next((m for m in mics if m.split(" · ")[0] == str(o.get("microfone"))), "Padrão do Windows")
        self.var_mic = tk.StringVar(value=atual)
        linha_campo(f, "Microfone", lambda p: ctk.CTkOptionMenu(p, values=opcoes, variable=self.var_mic, width=520))

        f = secao(pagina, "Teste e calibração",
               "1) Clique em “Ligar teste”. A barra mostra o volume que chega ao microfone; a linha branca é o limite "
               "(abaixo dela é tratado como silêncio). 2) Fique em silêncio e clique em “Medir ruído”: o limite é "
               "ajustado sozinho. 3) Clique em “Gravar frase” e fale como falaria com ele. Depois ouça a "
               "gravação e veja o que o Whisper entendeu. Enquanto o teste está ligado, a escuta dele fica em pausa.")
        medidor = ctk.CTkFrame(f)
        medidor.pack(fill="x", padx=(28, 18), pady=4)
        self.canvas_nivel = tk.Canvas(medidor, height=26, bg="#1d2029", highlightthickness=0)
        self.canvas_nivel.pack(fill="x", padx=10, pady=(10, 4))
        self.rotulo_nivel = ctk.CTkLabel(medidor, text="Teste desligado", anchor="w")
        self.rotulo_nivel.pack(fill="x", padx=10, pady=(0, 8))
        bts = ctk.CTkFrame(f, fg_color="transparent")
        bts.pack(fill="x", padx=(28, 18), pady=4)
        self.bt_teste = ctk.CTkButton(bts, text="▶ Ligar teste", command=self._alternar_teste)
        self.bt_teste.pack(side="left", padx=4)
        ctk.CTkButton(bts, text="Medir ruído (3s de silêncio)", **SECUNDARIO, command=self._medir_ruido).pack(side="left", padx=4)
        ctk.CTkButton(bts, text="● Gravar frase", **PERIGO,
                      command=self._gravar_frase).pack(side="left", padx=4)
        ctk.CTkButton(bts, text="Ouvir gravação", **SECUNDARIO, command=self._ouvir_gravacao).pack(side="left", padx=4)
        ctk.CTkButton(bts, text="Transcrever", **SECUNDARIO, command=self._transcrever_teste).pack(side="left", padx=4)
        self.resultado_teste = ctk.CTkTextbox(f, height=90)
        self.resultado_teste.pack(fill="x", padx=(28, 18), pady=4)
        self.resultado_teste.insert("1.0", "O resultado do teste aparece aqui.")

        f = secao(pagina, "Minha voz",
                  f"Para o {self.nome} obedecer só a você, e não a um vídeo tocando na caixa de som ou a outra pessoa. "
                  "1) Clique em “Cadastrar minha voz” e leia em voz alta as frases que aparecem, uma de cada vez, do "
                  "seu jeito normal (a gravação passa sozinha para a próxima quando você faz uma pausa). "
                  "2) A chave “Responder só à minha voz” liga sozinha no fim. 3) Clique em “Testar” e fale uma frase: "
                  "aparece a nota de 0 a 1 (quanto mais perto de 1, mais parecida com a sua voz). "
                  "A régua “Quão exigente” é a nota mínima: mais para a direita, mais rígido. "
                  "Tudo roda no seu PC, grátis. Salve e reinicie para valer.")
        from . import locutor
        ligado, exigencia = locutor.opcoes(self.cfg)
        self.var_so_minha_voz = tk.BooleanVar(value=ligado)
        linha_campo(f, "Responder só à minha voz", lambda p: ctk.CTkSwitch(
            p, text="ignorar vozes que não são a minha (vídeos, outras pessoas)", variable=self.var_so_minha_voz,
            command=self._mostrar_situacao_voz))
        self.var_exig_voz = tk.DoubleVar(value=exigencia)
        linha_campo(f, "Quão exigente", lambda p: ctk.CTkSlider(
            p, from_=0.2, to=0.7, number_of_steps=50, variable=self.var_exig_voz,
            command=lambda v: self._mostrar_situacao_voz()))
        bts = ctk.CTkFrame(f, fg_color="transparent")
        bts.pack(fill="x", padx=(28, 18), pady=4)
        self.bt_cadastrar_voz = ctk.CTkButton(bts, text="● Cadastrar minha voz", command=self._cadastrar_voz)
        self.bt_cadastrar_voz.pack(side="left", padx=4)
        ctk.CTkButton(bts, text="Testar", **SECUNDARIO, command=self._testar_voz).pack(side="left", padx=4)
        ctk.CTkButton(bts, text="Apagar cadastro", **SECUNDARIO, command=self._apagar_voz).pack(side="left", padx=4)
        self.rot_situacao_voz = ctk.CTkLabel(f, text="", anchor="w", justify="left", text_color=tema.TEXTO_FRACO)
        self.rot_situacao_voz.pack(fill="x", padx=(32, 18))
        self.txt_voz = ctk.CTkTextbox(f, height=80, wrap="word")
        self.txt_voz.pack(fill="x", padx=(28, 18), pady=4)
        self._voz_msg("Aqui aparecem a frase para ler no cadastro e a nota do teste.")
        self._mostrar_situacao_voz()

        f = secao(pagina, "Ajustes de captação")
        self.var_auto = tk.BooleanVar(value=not o.get("limiar_volume"))
        linha_campo(f, "Limite automático ao ligar", lambda p: ctk.CTkSwitch(p, text="medir o ruído sozinho toda vez que ele liga",
                                                                            variable=self.var_auto))
        self.var_limiar = tk.DoubleVar(value=float(o.get("limiar_volume") or 400))
        self.rot_limiar = linha_campo(f, "Limite de volume (fixo)", lambda p: ctk.CTkSlider(
            p, from_=50, to=3000, variable=self.var_limiar, command=lambda v: self._desenhar_nivel()))
        self.var_ganho = tk.DoubleVar(value=float(o.get("ganho") or 1.0))
        linha_campo(f, "Ganho (aumenta o volume do mic)", lambda p: ctk.CTkSlider(p, from_=0.5, to=4, variable=self.var_ganho))
        self.var_silencio = tk.DoubleVar(value=float(o.get("silencio_fim") or 0.8))
        linha_campo(f, "Pausa que encerra a frase (s)", lambda p: ctk.CTkSlider(p, from_=0.4, to=2.0, variable=self.var_silencio))
        from .ouvido import espera_apos_palavra
        self.var_espera_palavra = tk.DoubleVar(value=espera_apos_palavra(self.cfg))
        linha_campo(f, f"Espera depois de só “{self.palavra}” (s)", lambda p: ctk.CTkSlider(
            p, from_=0, to=5, number_of_steps=20, variable=self.var_espera_palavra))
        from .ouvido import espera_continuacao
        self.var_espera_cont = tk.DoubleVar(value=espera_continuacao(self.cfg))
        linha_campo(f, "Espera se a frase parar no meio (s)", lambda p: ctk.CTkSlider(
            p, from_=0, to=3, number_of_steps=12, variable=self.var_espera_cont))
        ctk.CTkLabel(f, text="Frase que termina em vírgula, reticências ou “do”, “que”, “e”, “pra”... espera a "
                            "continuação e junta as duas numa ordem só (0 = desligado).",
                     anchor="w", justify="left", wraplength=620, text_color=tema.TEXTO_FRACO).pack(fill="x", padx=(32, 18))
        sv = self._sec("voz")
        self.var_fala_fundo = tk.BooleanVar(value=bool(sv.get("fala_em_segundo_plano", True)))
        linha_campo(f, "Ouvir enquanto fala", lambda p: ctk.CTkSwitch(
            p, text=f"a escuta continua enquanto ele fala (só vale frase que começa com “{self.palavra}”)",
            variable=self.var_fala_fundo))
        self.var_interromper = tk.BooleanVar(value=bool(sv.get("interromper_com_palavra", True)))
        linha_campo(f, f"Interromper com “{self.palavra}”", lambda p: ctk.CTkSwitch(
            p, text=f"“{self.palavra}, para” corta a fala na hora; “{self.palavra}, abre...” corta e executa",
            variable=self.var_interromper))
        self.var_frase_a_frase = tk.BooleanVar(value=bool(sv.get("frase_a_frase", True)))
        linha_campo(f, "Fala frase a frase", lambda p: ctk.CTkSwitch(
            p, text="resposta longa começa a tocar na 1ª frase enquanto prepara as outras",
            variable=self.var_frase_a_frase))
        self.var_max = tk.IntVar(value=int(o.get("max_frase") or 60))
        linha_campo(f, "Tamanho máximo de uma frase (s)", lambda p: ctk.CTkSlider(p, from_=15, to=180, number_of_steps=33,
                                                                                variable=self.var_max))
        self.var_espera_ditado = tk.IntVar(value=int(o.get("ditado_silencio_max") or 180))
        linha_campo(f, "Silêncio que fecha o ditado (s)", lambda p: ctk.CTkSlider(p, from_=30, to=600, number_of_steps=19,
                                                                                variable=self.var_espera_ditado))
        self.var_revisar = tk.BooleanVar(value=bool(self._sec("ditado").get("revisar_na_janela", True)))
        linha_campo(f, "Revisar o ditado", lambda p: ctk.CTkSwitch(
            p, text="no fim do ditado, abrir uma janela para ler, corrigir e escolher o destino", variable=self.var_revisar))
        from .ouvido import PALAVRAS_PADRAO
        self.ent_palavras = linha_campo(f, "Palavras que ele deve conhecer", lambda p: ctk.CTkEntry(p))
        self.ent_palavras.insert(0, ", ".join(str(x) for x in (o.get("palavras_conhecidas") or PALAVRAS_PADRAO)))
        ctk.CTkLabel(f, text="Separe por vírgula. O reconhecimento de voz erra menos essas palavras "
                            "(nomes do trabalho, programas, gírias). Vale depois de reiniciar.",
                     anchor="w", text_color=tema.TEXTO_FRACO).pack(fill="x", padx=(32, 18))
        self.rotulo_valores = ctk.CTkLabel(f, text="", anchor="w", text_color=tema.TEXTO_FRACO)
        self.rotulo_valores.pack(fill="x")

        f = secao(pagina, "Reconhecimento de voz (Whisper)")
        self.var_modo = tk.StringVar(value={"vosk": f"Leve (Vosk procura “{self.palavra}”)"}.get(o.get("modo_ativacao"),
                                                                                      "Preciso (Whisper ouve tudo)"))
        linha_campo(f, f"Como detectar “{self.palavra}”", lambda p: ctk.CTkSegmentedButton(
            p, values=["Preciso (Whisper ouve tudo)", f"Leve (Vosk procura “{self.palavra}”)"], variable=self.var_modo))
        from . import palavra_local
        det_ligado, _, det_limiar = palavra_local.opcoes(self.cfg)
        self.var_detector = tk.BooleanVar(value=det_ligado)
        linha_campo(f, "Detector local da palavra", lambda p: ctk.CTkSwitch(
            p, text=f"um ouvido leve procura só “{self.palavra}” antes do Whisper (menos processador, menos disparo com vídeo)",
            variable=self.var_detector))
        self.var_detector_limiar = tk.DoubleVar(value=det_limiar)
        linha_campo(f, "Exigência do detector", lambda p: ctk.CTkSlider(
            p, from_=0.1, to=0.9, number_of_steps=16, variable=self.var_detector_limiar))
        _, texto_det = palavra_local.situacao(self.cfg)
        self.rot_detector = ctk.CTkLabel(f, text=texto_det, anchor="w", justify="left", wraplength=620,
                                         text_color=tema.TEXTO_FRACO)
        self.rot_detector.pack(fill="x", padx=(32, 18))
        self.var_modelo = tk.StringVar(value=MODELOS_WHISPER.get(o.get("modelo_whisper", "small"), MODELOS_WHISPER["small"]))
        linha_campo(f, "Modelo", lambda p: ctk.CTkOptionMenu(p, values=list(MODELOS_WHISPER.values()), variable=self.var_modelo))
        self.var_precisao = tk.StringVar(value=o.get("precisao", "equilibrado"))
        linha_campo(f, "Capricho", lambda p: ctk.CTkSegmentedButton(p, values=["rapido", "equilibrado", "preciso"],
                                                                    variable=self.var_precisao))
        self.var_disp = tk.StringVar(value={"cpu": "Processador", "gpu": "Placa de vídeo"}.get(o.get("dispositivo"), "Automático"))
        linha_campo(f, "Onde rodar o Whisper", lambda p: ctk.CTkSegmentedButton(
            p, values=["Automático", "Processador", "Placa de vídeo"], variable=self.var_disp))
        self.rot_gpu = ctk.CTkLabel(f, text="Verificando a placa de vídeo...", anchor="w", text_color=tema.TEXTO_FRACO)
        self.rot_gpu.pack(fill="x")
        # so depois que a janela abriu (responder antes disso da erro no tkinter)
        self.after(300, lambda: threading.Thread(target=self._verificar_gpu, daemon=True).start())
        self.var_diag = tk.BooleanVar(value=bool(o.get("gravar_diagnostico", False)))
        linha_campo(f, "Guardar áudios ouvidos", lambda p: ctk.CTkSwitch(
            p, text="salva as últimas 30 frases em logs/audios (para ouvir o que chegou)", variable=self.var_diag))

        f = secao(pagina, "Saída de som",
                  f"Por onde o som sai (a caixinha de som, o fone...). Dê um apelido pra cada dispositivo "
                  f"(a palavra que você fala, tipo “caixinha” ou “fone”) e Salve, pra falar “{self.palavra}, "
                  "coloca na caixinha” ou “troca pra fone”. “Usar agora” troca na hora, sem precisar salvar.")
        from . import sistema as _sistema
        from .comandos.midia import SAIDAS_SOM_PADRAO
        from .texto import normalizar as _normalizar
        apelidos_cfg = dict(SAIDAS_SOM_PADRAO)
        apelidos_cfg.update(configuracao.secao(self.cfg, "som").get("saidas") or {})

        def _apelido_do_dispositivo(nome: str) -> str:
            n = _normalizar(nome).replace(" ", "").replace("-", "")
            for apelido, pedaco in apelidos_cfg.items():
                p = _normalizar(pedaco).replace(" ", "").replace("-", "")
                if p and p in n:
                    return apelido
            return ""

        dispositivos = _sistema.listar_saidas_som()
        self._saida_som_linhas: list[tuple[str, str, ctk.CTkEntry]] = []   # (nome, apelido ao abrir, campo)
        if not dispositivos:
            ctk.CTkLabel(f, text=f"Não consegui ver os dispositivos de som agora (abra o painel de novo se acabou "
                                 f"de ligar o Bluetooth, ou reinicie o {self.nome}).",
                        anchor="w", text_color=tema.TEXTO_FRACO).pack(fill="x", padx=(32, 18))
        for d in dispositivos[:15]:
            linha = ctk.CTkFrame(f, fg_color="transparent")
            linha.pack(fill="x", padx=(28, 18), pady=3)
            texto_nome = d["nome"] + ("  (em uso agora)" if d["padrao"] else "")
            ctk.CTkLabel(linha, text=texto_nome, anchor="w", width=360, wraplength=360).pack(side="left", padx=(0, 8))
            apelido_atual = _apelido_do_dispositivo(d["nome"])
            ent = ctk.CTkEntry(linha, placeholder_text="apelido (ex.: caixinha)", width=160)
            ent.insert(0, apelido_atual)
            ent.pack(side="left", padx=4)
            ctk.CTkButton(linha, text="Usar agora", **SECUNDARIO,
                         command=lambda dev=d: self._usar_saida_som_agora(dev)).pack(side="left", padx=8)
            self._saida_som_linhas.append((d["nome"], apelido_atual, ent))

    def _usar_saida_som_agora(self, dispositivo: dict):
        from . import sistema as _sistema
        motivo = _sistema.definir_saida_som(dispositivo["id"])
        if motivo:
            messagebox.showerror(self.nome, f"Não consegui trocar pra {dispositivo['nome']}:\n{motivo}")
        else:
            messagebox.showinfo(self.nome, f"Som na {dispositivo['nome']}.")

    def _dispositivo(self) -> str:
        return {"Processador": "cpu", "Placa de vídeo": "gpu"}.get(self.var_disp.get(), "auto")

    def _verificar_gpu(self):
        from .audio import gpu_disponivel, tem_placa_nvidia
        if gpu_disponivel():
            texto = "✔ Placa NVIDIA pronta: o Whisper fica bem mais rápido (use o modelo large-v3-turbo)."
        elif tem_placa_nvidia():
            texto = ("Placa NVIDIA encontrada, mas faltam as bibliotecas dela: o reconhecimento usa o processador. "
                     "Para ativar a placa, rode o ferramentas\\11_ativar_placa_de_video.bat.")
        else:
            texto = "Sem placa NVIDIA: o Whisper roda no processador (use small ou medium)."
        try:
            self.after(0, lambda: self.rot_gpu.configure(text=texto))
        except RuntimeError:
            pass  # o painel fechou antes da checagem terminar

    def _mic_escolhido(self):
        v = self.var_mic.get()
        return None if v.startswith("Padrão") else int(v.split(" · ")[0])

    def _alternar_teste(self):
        if self._stream:
            self._parar_teste()
            return
        import sounddevice as sd

        def recebe(dados, frames, tempo, status):
            self._fila_audio.put(bytes(dados))

        try:
            self._stream = sd.RawInputStream(samplerate=TAXA, blocksize=BLOCO, device=self._mic_escolhido(),
                                             dtype="int16", channels=1, callback=recebe)
            self._stream.start()
        except Exception as erro:
            self._stream = None
            messagebox.showerror(self.nome, f"Não consegui abrir o microfone:\n{erro}")
            return
        estado.pausar(True)
        self.bt_teste.configure(text="■ Desligar teste")

    def _parar_teste(self):
        if not hasattr(self, "bt_teste"):
            return   # (a pagina Audio nem foi aberta: nenhum teste ligado)
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        estado.pausar(False)
        self.bt_teste.configure(text="▶ Ligar teste")
        self.rotulo_nivel.configure(text="Teste desligado")

    def _atualizar_medidor(self):
        if "Áudio" not in self._montadas:   # (pagina ainda fechada: nada para medir nem desenhar)
            self.after(250, self._atualizar_medidor)
            return
        blocos = []
        while not self._fila_audio.empty():
            blocos.append(aplicar_ganho(self._fila_audio.get_nowait(), self.var_ganho.get()))
        for b in blocos:
            v = nivel(b)
            self._niveis.append(v)
            self._nivel_atual = v
            if self._gravando:
                frase = self._seg.processar(b)
                self._tempo_gravado += BLOCO / TAXA
                if frase or self._tempo_gravado > 12:
                    self._gravando = False
                    self._gravacao = frase or b"".join(self._seg._frase)
                    self._mostrar(f"Gravado: {len(self._gravacao) / (TAXA * 2):.1f}s de áudio. "
                                  "Clique em “Ouvir gravação” ou “Transcrever”.")
                    if self._ao_gravar:
                        entregar, self._ao_gravar = self._ao_gravar, None
                        entregar(self._gravacao)
        self._niveis = self._niveis[-60:]
        if getattr(self, "pagina_atual", None) != "Áudio":   # escondida: nao redesenha (o painel fica leve)
            self.after(120, self._atualizar_medidor)
            return
        self._desenhar_nivel()
        self._por(
            self.rotulo_valores,
            text=f"Limite: {'automático' if self.var_auto.get() else round(self.var_limiar.get())} · "
                 f"Ganho: {self.var_ganho.get():.1f}x · Pausa: {self.var_silencio.get():.1f}s · "
                 f"Frase até {self.var_max.get()}s · Ditado fecha após {self.var_espera_ditado.get()}s de silêncio")
        self.after(80, self._atualizar_medidor)

    def _desenhar_nivel(self):
        c = self.canvas_nivel
        largura = max(c.winfo_width(), 200)
        c.delete("all")
        limiar = self.var_limiar.get()
        escala = max(limiar * 3, 600)
        v = getattr(self, "_nivel_atual", 0) if self._stream else 0
        cor = "#ff5c5c" if self._gravando else ("#3ecf8e" if v >= limiar else "#4b5563")
        c.create_rectangle(0, 4, min(1, v / escala) * largura, 22, fill=cor, outline="")
        x = largura / 3
        c.create_line(x, 0, x, 26, fill="#eceae4", width=2)
        if self._stream:
            estado_voz = "FALA detectada" if v >= limiar else "silêncio/ruído"
            self.rotulo_nivel.configure(text=f"Volume agora: {v:.0f}   ·   limite: {limiar:.0f}   ·   {estado_voz}")

    def _medir_ruido(self):
        if not self._stream:
            self._alternar_teste()
        self._mostrar("Fique em silêncio por 3 segundos...")
        self._niveis.clear()

        def concluir():
            limiar = sugerir_limiar(self._niveis[-30:])
            self.var_limiar.set(limiar)
            self.var_auto.set(False)
            self._mostrar(f"Ruído medido. Limite ajustado para {limiar:.0f}. Agora grave uma frase para testar.")
        self.after(3000, concluir)

    def _gravar_frase(self):
        if not self._stream:
            self._alternar_teste()
        self._seg = Segmentador(self.var_limiar.get(), self.var_silencio.get())
        self._tempo_gravado = 0.0
        self._gravando = True
        self._mostrar(f"Gravando... fale agora (ex.: “E aí {self.palavra}, abre o último vídeo do Manual do Mundo”). "
                      "A gravação para sozinha quando você fizer uma pausa.")

    def _ouvir_gravacao(self):
        if not self._gravacao:
            self._mostrar("Grave uma frase primeiro.")
            return
        import numpy as np
        import sounddevice as sd

        sd.play(np.frombuffer(self._gravacao, dtype=np.int16), TAXA)

    def _transcrever_teste(self):
        if not self._gravacao:
            self._mostrar("Grave uma frase primeiro.")
            return
        modelo = next(k for k, v in MODELOS_WHISPER.items() if v == self.var_modelo.get())
        chave = (modelo, self.var_precisao.get(), self._dispositivo())
        self._mostrar(f"Transcrevendo com o modelo {modelo} (na primeira vez ele é baixado e carregado, pode demorar)...")

        def trabalho():
            try:
                if chave not in self._transcritores:
                    self._transcritores[chave] = Transcritor(modelo, chave[1], chave[2])
                inicio = time.time()
                texto = self._transcritores[chave].transcrever(self._gravacao)
                onde = "placa de vídeo" if self._transcritores[chave].dispositivo == "cuda" else "processador"
                msg = (f"O {self.nome} entendeu: “{texto}”\n"
                       f"(modelo {modelo}, no {onde}, {time.time() - inicio:.1f}s para transcrever)")
            except Exception as erro:
                msg = f"Erro ao transcrever: {erro}"
            self.after(0, lambda: self._mostrar(msg))
        threading.Thread(target=trabalho, daemon=True).start()

    # --- Minha voz (responder só ao dono) ---------------------------------
    def _voz_msg(self, texto: str):
        self.txt_voz.delete("1.0", "end")
        self.txt_voz.insert("1.0", texto)

    def _mostrar_situacao_voz(self):
        from . import locutor
        info = locutor.info_impressao()
        cad = (f"Voz cadastrada em {info.get('data', '?')} ({info.get('frases', '?')} frases)." if info.get("impressao")
               else "Voz ainda não cadastrada.")
        if self.var_so_minha_voz.get() and not info.get("impressao"):
            cad += " A chave está ligada, mas sem cadastro ele continua obedecendo a qualquer voz."
        self.rot_situacao_voz.configure(text=f"{cad}   Exigência: {self.var_exig_voz.get():.2f}")

    def _gravar_para(self, receber) -> bool:
        """Grava UMA frase pelo teste do microfone e entrega o audio a receber(audio)."""
        if not self._stream:
            self._alternar_teste()
            if not self._stream:
                return False
        self._seg = Segmentador(self.var_limiar.get(), self.var_silencio.get())
        self._tempo_gravado = 0.0
        self._ao_gravar = receber
        self._gravando = True
        return True

    def _com_modelo_voz(self, trabalho):
        """Roda trabalho(extrair) numa thread, carregando o modelo antes (só na 1a vez)."""
        from . import locutor

        def rodar():
            try:
                if self._voz_extrair is None:
                    self.after(0, lambda: self._voz_msg("Carregando o reconhecimento de voz (na primeira vez baixa "
                                                         "uns 85 MB, pode demorar um pouco)..."))
                    self._voz_extrair = locutor.carregar_modelo()
                trabalho(self._voz_extrair)
            except Exception as erro:
                self.after(0, lambda e=erro: self._voz_msg(f"Não consegui usar o reconhecimento de voz: {e}"))
        threading.Thread(target=rodar, daemon=True).start()

    def _cadastrar_voz(self):
        from . import locutor
        if self._cad_frases is not None:   # clicou de novo: cancela
            self._cad_frases = None
            self._ao_gravar = None
            self._gravando = False
            self.bt_cadastrar_voz.configure(text="● Cadastrar minha voz")
            self._parar_teste()
            self._voz_msg("Cadastro cancelado. Nada foi salvo.")
            return
        self._cad_frases = [fr.format(palavra=self.palavra.capitalize()) for fr in locutor.FRASES_CADASTRO]
        self._cad_audios: list[bytes] = []
        self.bt_cadastrar_voz.configure(text="■ Parar cadastro")
        self._proxima_frase_voz()

    def _proxima_frase_voz(self):
        if self._cad_frases is None:
            return
        i = len(self._cad_audios)
        if i >= len(self._cad_frases):
            self._concluir_cadastro_voz()
            return
        self._voz_msg(f"Frase {i + 1} de {len(self._cad_frases)}. Fale agora, do seu jeito normal:\n\n"
                      f"“{self._cad_frases[i]}”")
        if not self._gravar_para(self._frase_voz_gravada):
            self._cad_frases = None
            self.bt_cadastrar_voz.configure(text="● Cadastrar minha voz")

    def _frase_voz_gravada(self, audio: bytes):
        if self._cad_frases is None:
            return
        if len(audio) < TAXA * 2 * 0.7:   # menos de 0,7 s: não ouviu direito
            self._voz_msg("Não ouvi direito. Vamos repetir a mesma frase...")
            self.after(1200, self._proxima_frase_voz)
            return
        self._cad_audios.append(audio)
        self.after(500, self._proxima_frase_voz)

    def _concluir_cadastro_voz(self):
        from . import locutor
        audios = list(self._cad_audios)
        self._cad_frases = None
        self.bt_cadastrar_voz.configure(text="● Cadastrar minha voz")
        self._parar_teste()
        self._voz_msg(f"Gravei {len(audios)} frases. Gerando a sua impressão de voz...")

        def trabalho(extrair):
            embs = [extrair(locutor.bytes_para_float(a)) for a in audios]
            locutor.salvar_impressao(embs)
            info = locutor.info_impressao()

            def pronto():
                self.var_so_minha_voz.set(True)
                self._mostrar_situacao_voz()
                self._voz_msg(f"Pronto! Sua voz foi cadastrada ({len(audios)} frases). A chave “Responder só à "
                              f"minha voz” foi ligada. Agora clique em “Testar” e fale uma frase para ver a nota. "
                              f"Depois clique em Salvar e reinicie o {self.nome} para valer. "
                              f"(nota mínima entre as frases do cadastro: {info.get('nota_minima_cadastro', '?')})")
            self.after(0, pronto)
        self._com_modelo_voz(trabalho)

    def _testar_voz(self):
        from . import locutor
        if self._cad_frases is not None:
            return
        if locutor.carregar_impressao() is None:
            self._voz_msg("Cadastre sua voz primeiro (botão “Cadastrar minha voz”).")
            return
        if self._voz_extrair is None:   # (carrega enquanto você fala)
            self._com_modelo_voz(lambda extrair: None)
        self._voz_msg(f"Fale uma frase agora (ex.: “{self.palavra.capitalize()}, abre o YouTube”). "
                      "Dica: teste também com um vídeo tocando na caixa de som.")
        self._gravar_para(self._voz_teste_gravado)

    def _voz_teste_gravado(self, audio: bytes):
        from . import locutor
        self._parar_teste()
        if len(audio) < TAXA * 2 * 0.3:
            self._voz_msg("Não ouvi nada. Clique em “Testar” de novo e fale um pouco mais alto.")
            return
        self._voz_msg("Comparando com a sua voz...")

        def trabalho(extrair):
            nota = locutor.cosseno(extrair(locutor.bytes_para_float(audio)), locutor.carregar_impressao())
            exig = self.var_exig_voz.get()
            aceita, _ = locutor.decidir(nota, exig, len(audio) / (TAXA * 2))
            veredito = ("✔ reconhecida: ele obedeceria." if aceita
                        else "✖ não reconhecida: ele ignoraria esta frase.")
            self.after(0, lambda: self._voz_msg(
                f"Nota desta frase: {nota:.2f} (exigência atual {exig:.2f}) → {veredito}\n"
                "Sua voz dá nota alta? Um vídeo ou outra pessoa dá nota baixa? Então está bom. Se a sua voz for "
                "recusada, diminua a exigência; se o vídeo passar, aumente."))
        self._com_modelo_voz(trabalho)

    def _apagar_voz(self):
        from . import locutor
        if locutor.carregar_impressao() is None:
            self._voz_msg("Não há voz cadastrada.")
            return
        if not messagebox.askyesno(self.nome, "Apagar o cadastro da sua voz? Ele volta a obedecer a qualquer voz."):
            return
        locutor.apagar_impressao()
        self.var_so_minha_voz.set(False)
        self._mostrar_situacao_voz()
        self._voz_msg("Cadastro apagado. Salve para valer.")

    def _mostrar(self, texto: str):
        self.resultado_teste.delete("1.0", "end")
        self.resultado_teste.insert("1.0", texto)

    # -----------------------------------------------------------------
    #  Voz: uma aba por motor (so o essencial dele) + "Ativar", "Testar" e "Usar como reserva"
    # -----------------------------------------------------------------
    # chave: (titulo, selo, texto curto, icone)
    MOTORES_INFO = {
        "kokoro": ("Kokoro", "GRÁTIS · NO SEU PC", "Rápida e natural. Funciona sem internet.", "pc"),
        "natural": ("Natural", "GRÁTIS · PLACA DE VÍDEO", "A mais humana das grátis. Pesada (6 GB).", "chip"),
        "edge": ("Edge", "GRÁTIS · INTERNET", "Vozes da Microsoft pela internet. A voz de antes.", "nuvem"),
        "azure": ("Azure", "GRÁTIS ATÉ 8 H/MÊS · CHAVE", "Vozes da Microsoft, mais estáveis.", "chave"),
        "elevenlabs": ("ElevenLabs", "PAGA · TEM PLANO GRÁTIS", "A mais natural de todas.", "estrela"),
        "windows": ("Windows", "SEMPRE FUNCIONA", "A voz que já vem no Windows. Sem internet, robótica.", "pc"),
    }

    class _AbaMotor:
        """O que o resto do painel (e o teste) usa de cada aba: esta aberta? / abrir."""

        def __init__(self, painel, chave):
            self.painel, self.chave = painel, chave

        def esta_aberta(self) -> bool:
            return getattr(self.painel, "_aba_voz_atual", None) == self.chave

        def alternar(self, _=None):
            self.painel._mostrar_aba_motor(self.chave)

    def _aba_voz(self, pagina):
        v = self._sec("voz")
        motor = str(v.get("motor", "kokoro"))
        motor = motor if motor in self.MOTORES_INFO else "kokoro"
        self.MOTORES = {k: info[0] for k, info in self.MOTORES_INFO.items()}
        self.var_motor = tk.StringVar(value=self.MOTORES[motor])
        reserva = str(v.get("reserva") or "kokoro")
        if reserva not in self.MOTORES_INFO or reserva == motor:
            reserva = "edge" if motor != "edge" else "kokoro"
        self.var_reserva = tk.StringVar(value=reserva)
        self._voz_resumo(pagina)
        self._voz_barra_abas(pagina)
        self._voz_area = ctk.CTkFrame(pagina, fg_color="transparent")
        self._voz_area.pack(fill="x", padx=(4, 10))
        self.secoes_motor, self._cartoes_motor, self._rot_teste_motor = {}, {}, {}
        for chave in self.MOTORES_INFO:
            corpo = self._voz_cartao_motor(chave)
            getattr(self, f"_voz_campos_{chave}")(corpo, v)
            self.secoes_motor[chave] = self._AbaMotor(self, chave)
        self._voz_ajustes(pagina, v)
        self._aba_voz_atual = None
        self._mostrar_aba_motor(motor)
        self._voz_atualizar_marcas()

    def _voz_resumo(self, pagina):
        faixa = ctk.CTkFrame(pagina, fg_color=tema.ROSA_FUNDO, corner_radius=16, border_width=1,
                             border_color=tema.misturar(tema.ROSA_FUNDO, tema.ROSA, 0.25))
        faixa.pack(fill="x", padx=(4, 10), pady=(4, 10))
        ctk.CTkLabel(faixa, text="", image=icones.ctk_icone("alto", tema.ROSA, 20)).pack(side="left", padx=(16, 8), pady=12)
        self.rot_voz_resumo = ctk.CTkLabel(faixa, text="", anchor="w", font=tema.fonte(14, True))
        self.rot_voz_resumo.pack(side="left")
        ctk.CTkLabel(faixa, text="Se a ativa falhar, ele usa a reserva sozinho", height=24, corner_radius=12,
                     fg_color=tema.CAMPO, text_color=tema.TEXTO_FRACO, font=tema.fonte(11)).pack(side="right", padx=14)

    def _voz_barra_abas(self, pagina):
        barra = ctk.CTkFrame(pagina, fg_color=tema.CAMPO, corner_radius=14, border_width=1, border_color=tema.BORDA)
        barra.pack(fill="x", padx=(4, 10), pady=(0, 10))
        self._botoes_aba_motor = {}
        for chave, (nome, *_) in self.MOTORES_INFO.items():
            b = ctk.CTkButton(barra, text=nome, width=96, height=34, corner_radius=10, compound="left",
                              image=icones.ctk_icone("vazio", "#000000", 9), fg_color="transparent",
                              hover_color=tema.SECUNDARIO_HOVER, text_color=tema.TEXTO_FRACO, font=tema.fonte(13),
                              command=lambda c=chave: self._mostrar_aba_motor(c))
            b.pack(side="left", padx=(4 if not self._botoes_aba_motor else 2, 2), pady=4)
            self._botoes_aba_motor[chave] = b

    def _voz_cartao_motor(self, chave: str):
        """O cartao da aba: cabecalho, situacao, campos (devolvidos) e os 3 botoes."""
        nome, selo, texto, icone = self.MOTORES_INFO[chave]
        c = ctk.CTkFrame(self._voz_area, fg_color=tema.CARTAO, corner_radius=16, border_width=1, border_color=tema.BORDA)
        topo = ctk.CTkFrame(c, fg_color="transparent")
        topo.pack(fill="x", padx=18, pady=(16, 2))
        ctk.CTkLabel(topo, text="", image=icones.ctk_icone(icone, tema.ROSA, 20)).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(topo, text=nome, anchor="w", font=tema.fonte(16, True)).pack(side="left")
        ctk.CTkLabel(topo, text=selo, text_color=tema.ROSA if chave in ("elevenlabs", "azure") else tema.SUCESSO,
                     font=tema.fonte(10, True)).pack(side="left", padx=12)
        situacao = ctk.CTkLabel(topo, text="", height=22, corner_radius=11, font=tema.fonte(11, True))
        situacao.pack(side="right")
        ctk.CTkLabel(c, text=texto, anchor="w", justify="left", wraplength=780, text_color=tema.TEXTO_FRACO,
                     font=tema.fonte(12)).pack(fill="x", padx=18, pady=(0, 8))
        corpo = ctk.CTkFrame(c, fg_color="transparent")
        corpo.pack(fill="x", padx=3)
        botoes = ctk.CTkFrame(c, fg_color="transparent")
        botoes.pack(fill="x", padx=18, pady=(10, 4))
        ativar = ctk.CTkButton(botoes, text=" Ativar esta voz", image=icones.ctk_icone("check", tema.TEXTO_NO_ROSA, 16),
                               compound="left", width=170, command=lambda: self._escolher_motor(chave))
        ativar.pack(side="left")
        ctk.CTkButton(botoes, text=" Testar", image=icones.ctk_icone("play", tema.TEXTO, 14), compound="left", width=110,
                      **SECUNDARIO, command=lambda: self._ouvir_voz(chave)).pack(side="left", padx=8)
        reserva = ctk.CTkButton(botoes, text="Usar como reserva", width=160, **SECUNDARIO,
                                command=lambda: self._usar_reserva(chave))
        reserva.pack(side="left")
        rot = ctk.CTkLabel(c, text="", anchor="w", justify="left", wraplength=780, text_color=tema.TEXTO_FRACO)
        rot.pack(fill="x", padx=18, pady=(2, 14))
        self._rot_teste_motor[chave] = rot
        self._cartoes_motor[chave] = {"cartao": c, "situacao": situacao, "ativar": ativar, "reserva": reserva}
        return corpo

    def _voz_campos_kokoro(self, f, v):
        from . import voz_kokoro
        self.var_voz_kokoro = tk.StringVar(value=voz_kokoro.VOZES.get(str(v.get("voz_kokoro", "pm_alex")),
                                                                      voz_kokoro.VOZES["pm_alex"]))
        linha_campo(f, "Voz Kokoro", lambda p: ctk.CTkSegmentedButton(
            p, values=list(voz_kokoro.VOZES.values()), variable=self.var_voz_kokoro))
        linha_k = ctk.CTkFrame(f, fg_color="transparent")
        linha_k.pack(fill="x", padx=(32, 18), pady=4)
        self.bt_kokoro = ctk.CTkButton(linha_k, text="⇩  Baixar a voz Kokoro (330 MB)", width=260,
                                       command=self._baixar_kokoro)
        self.bt_kokoro.pack(side="left")
        self.rot_kokoro = ctk.CTkLabel(linha_k, text="", anchor="w", text_color=tema.TEXTO_FRACO)
        self.rot_kokoro.pack(side="left", padx=10)
        self._estado_kokoro()

    def _voz_campos_natural(self, f, v):
        from . import voz_natural
        ctk.CTkLabel(f, text="Chatterbox, que fala português: imita o timbre de um áudio de uns 10 segundos (a voz da "
                             "Microsoft ou um áudio seu). Precisa de placa NVIDIA para ficar rápida e instala num canto "
                             f"separado (uns 6 GB), sem mexer no resto do {self.nome}. Enquanto ela carrega, ele fala "
                             "com a reserva.", anchor="w", justify="left", wraplength=760, text_color=tema.TEXTO_FRACO,
                     font=tema.fonte(12)).pack(fill="x", padx=(32, 18), pady=(0, 6))
        self.var_voz_natural = tk.StringVar(value=voz_natural.VOZES.get(str(v.get("voz_natural", "antonio")),
                                                                        voz_natural.VOZES["antonio"]))
        linha_campo(f, "Timbre", lambda p: ctk.CTkOptionMenu(p, values=list(voz_natural.VOZES.values()),
                                                             variable=self.var_voz_natural, width=360))
        linha_n = ctk.CTkFrame(f, fg_color="transparent")
        linha_n.pack(fill="x", padx=(32, 18), pady=4)
        self.bt_natural = ctk.CTkButton(linha_n, text="⇩  Instalar a voz natural", width=220, command=self._instalar_natural)
        self.bt_natural.pack(side="left")
        ctk.CTkButton(linha_n, text="Usar um áudio meu...", **SECUNDARIO, command=self._audio_natural).pack(side="left", padx=8)
        self.rot_natural = ctk.CTkLabel(f, text="", anchor="w", justify="left", wraplength=760, text_color=tema.TEXTO_FRACO)
        self.rot_natural.pack(fill="x", padx=(32, 18))
        self._estado_natural()

    def _voz_campos_edge(self, f, v):
        pref = self.vocab.preferencia
        ctk.CTkLabel(f, text="As marcadas com ★ são “Multilingual”: mais expressivas (com um leve sotaque).", anchor="w",
                     text_color=tema.TEXTO_FRACO, font=tema.fonte(12)).pack(fill="x", padx=(32, 18), pady=(0, 6))
        todas = list(dict.fromkeys(list(v.get("vozes_favoritas") or []) + VOZES_BASICAS))
        self.vozes = sorted(todas, key=lambda n: ("Multilingual" not in n, n))
        self.var_voz = tk.StringVar(value=pref("voz") or v.get("voz_edge", "pt-BR-AntonioNeural"))
        self.menu_voz = linha_campo(f, "Voz Edge", lambda p: ctk.CTkOptionMenu(
            p, values=[self._rotulo_voz(n) for n in self.vozes], width=420,
            command=lambda r: self.var_voz.set(r.replace("★ ", "").split(" · ")[0])))
        self.menu_voz.set(self._rotulo_voz(self.var_voz.get()))
        linha_v = ctk.CTkFrame(f, fg_color="transparent")
        linha_v.pack(fill="x", padx=(32, 18), pady=4)
        ctk.CTkButton(linha_v, text="Carregar todas as vozes da Microsoft", **SECUNDARIO,
                      command=self._carregar_vozes).pack(side="left")

    def _voz_campos_azure(self, f, v):
        from . import voz_azure
        ctk.CTkLabel(f, text="Crie um recurso “Speech” no portal da Azure (plano grátis F0) e cole a chave e a região. "
                             "A chave fica no seu usuário do Windows, fora do projeto. Passo a passo no guia (Etapa 30).",
                     anchor="w", justify="left", wraplength=760, text_color=tema.TEXTO_FRACO,
                     font=tema.fonte(12)).pack(fill="x", padx=(32, 18), pady=(0, 6))
        self.var_voz_azure = tk.StringVar(value=str(v.get("voz_azure", "pt-BR-AntonioNeural")))
        linha_campo(f, "Voz Azure", lambda p: ctk.CTkComboBox(p, values=voz_azure.VOZES, variable=self.var_voz_azure,
                                                              width=420))
        self.ent_azure_chave = linha_campo(f, "Chave (KEY 1)", lambda p: ctk.CTkEntry(p, height=36, show="•"))
        self.ent_azure_chave.insert(0, segredos.ler("azure_chave"))
        self.ent_azure_regiao = linha_campo(f, "Região", lambda p: ctk.CTkEntry(p, height=36))
        self.ent_azure_regiao.insert(0, segredos.ler("azure_regiao", "brazilsouth"))
        linha_a = ctk.CTkFrame(f, fg_color="transparent")
        linha_a.pack(fill="x", padx=(32, 18), pady=4)
        ctk.CTkButton(linha_a, text="Salvar chave e testar", width=200, command=self._testar_azure).pack(side="left")
        ctk.CTkButton(linha_a, text="Abrir o portal da Azure", **SECUNDARIO,
                      command=lambda: webbrowser.open("https://portal.azure.com/#create/Microsoft.CognitiveServicesSpeechServices")
                      ).pack(side="left", padx=8)
        self.rot_azure = ctk.CTkLabel(f, text="", anchor="w", justify="left", wraplength=760, text_color=tema.TEXTO_FRACO)
        self.rot_azure.pack(fill="x", padx=(32, 18))

    def _voz_campos_elevenlabs(self, f, v):
        from . import voz_elevenlabs
        ctk.CTkLabel(f, text="Crie uma conta em elevenlabs.io, vá em Developers > API Keys, crie uma chave e cole aqui. "
                             "O plano grátis dá uns 10 mil caracteres por mês; as frases fixas ficam guardadas (só gastam "
                             "na primeira vez). A chave fica no seu usuário do Windows, fora do projeto.",
                     anchor="w", justify="left", wraplength=760, text_color=tema.TEXTO_FRACO,
                     font=tema.fonte(12)).pack(fill="x", padx=(32, 18), pady=(0, 6))
        self.ent_eleven_chave = linha_campo(f, "Chave da API", lambda p: ctk.CTkEntry(p, height=36, show="•"))
        self.ent_eleven_chave.insert(0, segredos.ler("elevenlabs_chave"))
        self.vozes_eleven = dict(voz_elevenlabs.VOZES)
        atual = str(v.get("voz_elevenlabs", voz_elevenlabs.VOZ_PADRAO))
        self.vozes_eleven.setdefault(atual, atual)
        self.var_voz_eleven = tk.StringVar(value=self.vozes_eleven[atual])
        self.menu_eleven = linha_campo(f, "Voz", lambda p: ctk.CTkOptionMenu(
            p, values=list(self.vozes_eleven.values()), variable=self.var_voz_eleven, width=360))
        self.var_modelo_eleven = tk.StringVar(value=voz_elevenlabs.MODELOS.get(
            str(v.get("modelo_elevenlabs", voz_elevenlabs.MODELO_PADRAO)), voz_elevenlabs.MODELOS[voz_elevenlabs.MODELO_PADRAO]))
        linha_campo(f, "Modelo", lambda p: ctk.CTkSegmentedButton(p, values=list(voz_elevenlabs.MODELOS.values()),
                                                                  variable=self.var_modelo_eleven))
        linha_e = ctk.CTkFrame(f, fg_color="transparent")
        linha_e.pack(fill="x", padx=(32, 18), pady=4)
        ctk.CTkButton(linha_e, text="Salvar chave e testar", width=200, command=self._testar_eleven).pack(side="left")
        ctk.CTkButton(linha_e, text="Abrir o site", **SECUNDARIO,
                      command=lambda: webbrowser.open("https://elevenlabs.io/app/developers/api-keys")).pack(side="left", padx=8)
        self.rot_eleven = ctk.CTkLabel(f, text="", anchor="w", justify="left", wraplength=760, text_color=tema.TEXTO_FRACO)
        self.rot_eleven.pack(fill="x", padx=(32, 18))

    def _voz_campos_windows(self, f, v):
        ctk.CTkLabel(f, text="Não tem nada para configurar: é a voz instalada no Windows. Boa como última reserva "
                             "(funciona sem internet e sem baixar nada).", anchor="w", justify="left", wraplength=760,
                     text_color=tema.TEXTO_FRACO, font=tema.fonte(12)).pack(fill="x", padx=(32, 18), pady=(0, 4))

    def _voz_ajustes(self, pagina, v):
        pref = self.vocab.preferencia
        f = secao(pagina, "Frase de teste e ajustes", "Valem para todas as vozes. “Ouvir” fala com a voz ativa e mostra "
                                                      "em quantos segundos ela começou a falar.")
        self.texto_voz = ctk.CTkEntry(f, height=36)
        self.texto_voz.insert(0, "Fala, chefe! Beleza, já abri o YouTube, e o clima hoje, olha, tá ótimo.")
        self.texto_voz.pack(fill="x", padx=(32, 18), pady=4)
        b = ctk.CTkFrame(f, fg_color="transparent")
        b.pack(fill="x", padx=(32, 18), pady=(2, 6))
        ctk.CTkButton(b, text="▶  Ouvir", width=120, command=self._ouvir_voz).pack(side="left", padx=(0, 10))
        self.rot_voz = ctk.CTkLabel(b, text="", anchor="w", text_color=tema.TEXTO_FRACO)
        self.rot_voz.pack(side="left")
        self.var_vel = tk.IntVar(value=_num(pref("velocidade") or v.get("velocidade", "+10%")))
        linha_campo(f, "Velocidade", lambda p: ctk.CTkSlider(p, from_=-50, to=50, number_of_steps=20, variable=self.var_vel))
        self.var_tom = tk.IntVar(value=_num(pref("tom") or v.get("tom", "+0Hz")))
        linha_campo(f, "Tom (grave ↔ agudo)", lambda p: ctk.CTkSlider(p, from_=-20, to=20, number_of_steps=40, variable=self.var_tom))
        self.var_fluida = tk.BooleanVar(value=bool(v.get("fluida", True)))
        linha_campo(f, "Fala fluida", lambda p: ctk.CTkSwitch(
            p, text="tira as vírgulas que viram pausas “de robô”", variable=self.var_fluida))
        self.rot_ajustes = ctk.CTkLabel(f, text="", anchor="w", text_color=tema.TEXTO_FRACO, font=tema.fonte(12))
        self.rot_ajustes.pack(fill="x", padx=(32, 18))

        def mostrar(*_):
            self.rot_ajustes.configure(text=f"Velocidade {self.var_vel.get():+d}% · Tom {self.var_tom.get():+d}Hz "
                                            "(o tom só vale para Edge e Azure)")
        self.var_vel.trace_add("write", mostrar)
        self.var_tom.trace_add("write", mostrar)
        mostrar()

    def _mostrar_aba_motor(self, chave: str):
        """Troca a aba (so esconde uma e mostra a outra: nada e recriado)."""
        if chave == getattr(self, "_aba_voz_atual", None):
            return
        anterior = self._aba_voz_atual
        if anterior:
            self._cartoes_motor[anterior]["cartao"].pack_forget()
            self._por(self._botoes_aba_motor[anterior], fg_color="transparent", text_color=tema.TEXTO_FRACO)
        self._cartoes_motor[chave]["cartao"].pack(fill="x", pady=(0, 7))
        self._por(self._botoes_aba_motor[chave], fg_color=tema.CARTAO, text_color=tema.TEXTO)
        self._aba_voz_atual = chave

    def _voz_atualizar_marcas(self):
        """Resumo do topo, bolinhas das abas (verde = ativa, amarela = reserva) e os botoes de cada aba."""
        ativa, reserva = self._motor_escolhido(), self.var_reserva.get()
        self.rot_voz_resumo.configure(text=f"Voz ativa: {self.MOTORES[ativa]}   ·   Reserva: {self.MOTORES.get(reserva, reserva)}")
        for chave, b in self._botoes_aba_motor.items():
            cor = tema.SUCESSO if chave == ativa else tema.AVISO if chave == reserva else None
            self._por(b, image=icones.ctk_icone("ponto", cor, 9) if cor else icones.ctk_icone("vazio", "#000000", 9))
            partes = self._cartoes_motor[chave]
            if chave == ativa:
                self._por(partes["situacao"], text="  ✓ Voz ativa  ", fg_color="#1a2a24", text_color=tema.SUCESSO)
            elif chave == reserva:
                self._por(partes["situacao"], text="  Reserva  ", fg_color="#2a2419", text_color=tema.AVISO)
            else:
                self._por(partes["situacao"], text="", fg_color="transparent", text_color=tema.TEXTO_FRACO)
            self._por(partes["ativar"], state="disabled" if chave == ativa else "normal",
                      text=" Esta é a voz ativa" if chave == ativa else " Ativar esta voz")
            self._por(partes["reserva"], state="disabled" if chave in (ativa, reserva) else "normal",
                      text="É a reserva" if chave == reserva else "Usar como reserva")

    def _escolher_motor(self, chave: str, abrir: bool = True):
        """“Ativar esta voz”: ela passa a ser a voz ativa (e a aba dela aparece)."""
        self.var_motor.set(self.MOTORES.get(chave, self.MOTORES["kokoro"]))
        if self.var_reserva.get() == chave:   # a reserva nunca e a propria ativa
            self.var_reserva.set("edge" if chave != "edge" else "kokoro")
        self._voz_atualizar_marcas()
        if abrir:
            self._mostrar_aba_motor(chave)

    def _usar_reserva(self, chave: str):
        if chave == self._motor_escolhido():
            return
        self.var_reserva.set(chave)
        self._voz_atualizar_marcas()
        self._rot_teste_motor[chave].configure(text=f"✓ {self.MOTORES[chave]} é a reserva agora (salve para valer).",
                                               text_color=tema.SUCESSO)

    @staticmethod
    def _rotulo_voz(nome: str) -> str:
        partes = nome.split("-")
        curto = partes[2].replace("MultilingualNeural", "").replace("Neural", "") if len(partes) > 2 else nome
        return f"{'★ ' if 'Multilingual' in nome else ''}{nome} · {curto}"

    def _motor_escolhido(self) -> str:
        return next((k for k, r in self.MOTORES.items() if r == self.var_motor.get()), "kokoro")

    def _voz_kokoro_escolhida(self) -> str:
        from .voz_kokoro import VOZES
        return next((k for k, r in VOZES.items() if r == self.var_voz_kokoro.get()), "pm_alex")

    def _voz_natural_escolhida(self) -> str:
        from .voz_natural import VOZES
        return next((k for k, r in VOZES.items() if r == self.var_voz_natural.get()), "antonio")

    def _voz_eleven_escolhida(self) -> str:
        return next((k for k, r in self.vozes_eleven.items() if r == self.var_voz_eleven.get()), "pNInz6obpgDQGcFmaJgB")

    def _modelo_eleven_escolhido(self) -> str:
        from .voz_elevenlabs import MODELO_PADRAO, MODELOS
        return next((k for k, r in MODELOS.items() if r == self.var_modelo_eleven.get()), MODELO_PADRAO)

    def _estado_natural(self, texto: str = ""):
        from . import voz_natural
        placa = ("Placa NVIDIA encontrada ✓" if voz_natural.tem_placa_nvidia()
                 else "Não achei placa NVIDIA: ela vai rodar no processador (fica bem devagar)")
        if voz_natural.instalado():
            e = voz_natural.estado(forcar=True)
            situacao = ("✓ Instalada e ligada " + ("na placa de vídeo" if e.get("placa") == "cuda" else "no processador")
                        if e.get("pronto") else f"✓ Instalada. Liga sozinha com o {self.nome} quando ela for a escolhida."
                        if not e.get("erro") else f"Instalada, mas deu erro: {e['erro']}")
            self.bt_natural.configure(text="Reinstalar")
        else:
            situacao = "Ainda não instalada. O botão baixa tudo (uns 6 GB, de 10 a 40 minutos)."
        self.rot_natural.configure(text=(texto + "\n" if texto else "") + f"{situacao}  ·  {placa}")

    def _instalar_natural(self):
        from . import voz_natural
        if not messagebox.askyesno(self.nome, "Vai baixar uns 6 GB (PyTorch + a voz) e pode levar de 10 a 40 minutos. "
                                              "Pode continuar usando o PC. Instalar agora?"):
            return
        self.bt_natural.configure(state="disabled")

        def progresso(texto):
            try:
                self.after(0, lambda: self.rot_natural.configure(text=texto))
            except RuntimeError:
                pass

        def trabalho():
            erro = voz_natural.instalar(progresso)
            try:
                self.after(0, lambda: (self.bt_natural.configure(state="normal"),
                                       self._estado_natural(f"Erro: {erro}" if erro else
                                                            "Pronto! Escolha o cartão “Natural” e salve.")))
            except RuntimeError:
                pass
        threading.Thread(target=trabalho, daemon=True).start()

    def _audio_natural(self):
        from . import voz_natural
        arquivo = filedialog.askopenfilename(title="Um áudio de uns 10 segundos com a voz que ele deve imitar",
                                             filetypes=[("Áudio", "*.wav *.mp3 *.ogg *.m4a *.flac"), ("Todos", "*.*")])
        if arquivo:
            voz_natural.usar_meu_audio(arquivo)
            self.var_voz_natural.set(voz_natural.VOZES["meu_audio"])
            self._estado_natural("✓ Áudio guardado: o timbre “Um áudio meu” vai imitar essa voz.")

    def _testar_eleven(self):
        from . import voz_elevenlabs
        segredos.salvar(elevenlabs_chave=self.ent_eleven_chave.get())
        self.rot_eleven.configure(text="Testando...", text_color=tema.TEXTO_FRACO)

        def trabalho():
            import tempfile
            destino = Path(tempfile.gettempdir()) / "mestre_teste_eleven.mp3"
            try:
                vozes = voz_elevenlabs.minhas_vozes()
                inicio = time.time()
                voz_elevenlabs.gerar(f"Oi! Essa é a voz da ElevenLabs no {self.nome}.", self._voz_eleven_escolhida(),
                                     self._modelo_eleven_escolhido(), "+0%", destino)
                texto, cor = (f"✓ Funcionando ({time.time() - inicio:.1f} s). {len(vozes)} vozes na sua conta, "
                              "já estão na lista. Escolha o cartão “ElevenLabs” e salve."), tema.SUCESSO
                from .voz import Voz
                Voz({"voz": {"motor": "edge"}})._tocar(destino)
            except Exception as erro:
                vozes = {}
                texto, cor = f"Não funcionou: {erro}. Confira a chave em elevenlabs.io > Developers > API Keys.", tema.AVISO

            def mostrar():
                self.rot_eleven.configure(text=texto, text_color=cor)
                if vozes:
                    self.vozes_eleven.update(vozes)
                    self.menu_eleven.configure(values=list(self.vozes_eleven.values()))
            try:
                self.after(0, mostrar)
            except RuntimeError:
                pass
        threading.Thread(target=trabalho, daemon=True).start()

    def _ouvir_voz(self, motor: str | None = None):
        """Fala a frase de teste: com a voz ativa (botao "Ouvir") ou com a da aba ("Testar")."""
        from .voz import Voz
        from .voz_natural import pronta as voz_natural_pronta
        rotulo = self._rot_teste_motor[motor] if motor else self.rot_voz
        motor = motor or self._motor_escolhido()
        rotulo.configure(text="Falando...", text_color=tema.TEXTO_FRACO)

        def falar():
            inicio = time.time()
            voz = Voz({"voz": {"motor": motor, "reserva": self.var_reserva.get(), "voz_edge": self.var_voz.get(),
                               "voz_kokoro": self._voz_kokoro_escolhida(), "voz_azure": self.var_voz_azure.get(),
                               "voz_natural": self._voz_natural_escolhida(), "voz_elevenlabs": self._voz_eleven_escolhida(),
                               "modelo_elevenlabs": self._modelo_eleven_escolhido(),
                               "velocidade": f"{self.var_vel.get():+d}%", "tom": f"{self.var_tom.get():+d}Hz"}})
            voz.fluida = bool(self.var_fluida.get())
            primeira = []
            voz._tocar_original, voz._tocar = voz._tocar, lambda a: (primeira or primeira.append(time.time() - inicio),
                                                                     voz._tocar_original(a))
            voz.falar(self.texto_voz.get())
            voz.esperar(120)   # (a fala toca em segundo plano: espera terminar para medir)
            usada = next(iter(voz._motores()), "windows")
            if motor == "natural" and not voz_natural_pronta():
                usada = f"{voz._motores()[1] if len(voz._motores()) > 1 else 'edge'} (a natural ainda está carregando)"
            elif usada != motor and motor != "windows":
                usada = f"{usada} (a {self.MOTORES.get(motor, motor)} não está pronta: falou a reserva)"
            texto = f"Voz {usada}: começou a falar em {primeira[0]:.1f} s." if primeira else "Não consegui falar."
            try:
                self.after(0, lambda: rotulo.configure(text=texto))
            except RuntimeError:
                pass
        threading.Thread(target=falar, daemon=True).start()

    def _estado_kokoro(self):
        from . import voz_kokoro
        if not voz_kokoro.biblioteca_instalada():
            texto = "Falta a biblioteca: use o botão de atualizar (.zip) na Central (ela instala)."
        elif voz_kokoro.baixado():
            texto = "✓ Voz Kokoro pronta neste PC."
            self.bt_kokoro.configure(state="disabled")
        else:
            texto = "Ainda não baixada. (Se “Kokoro” estiver escolhido, ele baixa sozinho ao ligar.)"
        self.rot_kokoro.configure(text=texto)

    def _baixar_kokoro(self):
        from . import voz_kokoro
        self.bt_kokoro.configure(state="disabled")

        def progresso(x):
            try:
                self.after(0, lambda: self.rot_kokoro.configure(text=f"Baixando... {x * 100:.0f}%"))
            except RuntimeError:
                pass

        def trabalho():
            erro = voz_kokoro.baixar(progresso)
            try:
                self.after(0, lambda: (self.rot_kokoro.configure(text=f"Erro: {erro}") if erro else self._estado_kokoro(),
                                       erro and self.bt_kokoro.configure(state="normal")))
            except RuntimeError:
                pass
        threading.Thread(target=trabalho, daemon=True).start()

    def _testar_azure(self):
        from . import voz_azure
        segredos.salvar(azure_chave=self.ent_azure_chave.get(), azure_regiao=self.ent_azure_regiao.get() or "brazilsouth")
        self.rot_azure.configure(text="Testando...", text_color=tema.TEXTO_FRACO)

        def trabalho():
            import tempfile
            destino = Path(tempfile.gettempdir()) / "mestre_teste_azure.mp3"
            try:
                inicio = time.time()
                voz_azure.gerar("Oi Mestre. Essa é a voz da Azure.", self.var_voz_azure.get(), "+0%", "+0Hz", destino)
                texto, cor = f"✓ Azure funcionando ({time.time() - inicio:.1f} s). Escolha “Azure (chave)” e salve.", tema.SUCESSO
                from .voz import Voz
                Voz({"voz": {"motor": "edge"}})._tocar(destino)
            except Exception as erro:
                texto, cor = (f"Não funcionou: {erro}. Confira a chave (KEY 1) e a região (ex.: brazilsouth, eastus) "
                              "no portal da Azure > seu recurso Speech > Chaves e ponto de extremidade."), tema.AVISO
            try:
                self.after(0, lambda: self.rot_azure.configure(text=texto, text_color=cor))
            except RuntimeError:
                pass
        threading.Thread(target=trabalho, daemon=True).start()

    def _carregar_vozes(self):
        def trabalho():
            try:
                from .vozes import vozes_disponiveis
                nomes = [v["ShortName"] for v in vozes_disponiveis()]
                self.vozes = sorted(dict.fromkeys(self.vozes + nomes), key=lambda n: ("Multilingual" not in n, n))
                self.after(0, lambda: (self.menu_voz.configure(values=[self._rotulo_voz(n) for n in self.vozes]),
                                       self.rot_voz.configure(text=f"{len(nomes)} vozes carregadas.")))
            except Exception as erro:
                self.after(0, lambda e=erro: self.rot_voz.configure(text=f"Não consegui carregar: {e}"))
        threading.Thread(target=trabalho, daemon=True).start()

    def _linha_ia_nuvem(self, f, id_: str, nome: str, cb: dict, modelo_padrao: str, site_chave: str):
        """Um cartao de IA na nuvem (Groq/Cerebras/OpenRouter/Gemini): ligar, chave, modelo, testar."""
        cartao = ctk.CTkFrame(f, fg_color=tema.CAMPO, corner_radius=10)
        cartao.pack(fill="x", padx=(32, 18), pady=6)
        topo = ctk.CTkFrame(cartao, fg_color="transparent")
        topo.pack(fill="x", padx=12, pady=(10, 4))
        var_ligado = tk.BooleanVar(value=bool(cb.get(f"{id_}_ligado", False)))
        ctk.CTkSwitch(topo, text=nome, variable=var_ligado, font=tema.fonte(14, "bold")).pack(side="left")
        ctk.CTkButton(topo, text="Criar chave grátis", **SECUNDARIO, width=160,
                      command=lambda: webbrowser.open(site_chave)).pack(side="right")
        corpo = ctk.CTkFrame(cartao, fg_color="transparent")
        corpo.pack(fill="x", padx=12, pady=(0, 10))
        ent_chave = linha_campo(corpo, "Chave da API", lambda p: ctk.CTkEntry(p, height=36, show="•"), largura_rotulo=140)
        ent_chave.insert(0, segredos.ler(f"{id_}_chave"))
        ent_modelo = linha_campo(corpo, "Modelo", lambda p: ctk.CTkEntry(p, height=36), largura_rotulo=140)
        ent_modelo.insert(0, str(cb.get(f"{id_}_modelo", modelo_padrao)))
        linha_botao = ctk.CTkFrame(corpo, fg_color="transparent")
        linha_botao.pack(fill="x", pady=4)
        rot = ctk.CTkLabel(corpo, text="", anchor="w", justify="left", wraplength=740, text_color=tema.TEXTO_FRACO)
        ctk.CTkButton(linha_botao, text="Testar", width=120,
                      command=lambda: self._testar_ia_nuvem(id_, ent_chave, ent_modelo, rot)).pack(side="left")
        rot.pack(fill="x", pady=(2, 0))
        self._nuvem_ia[id_] = {"ligado": var_ligado, "chave": ent_chave, "modelo": ent_modelo}

    def _testar_ia_nuvem(self, id_: str, ent_chave, ent_modelo, rot):
        from . import cerebro
        chave, modelo = ent_chave.get().strip(), (ent_modelo.get().strip() or None)
        if not chave:
            rot.configure(text="Cole a chave da API antes de testar.", text_color=tema.AVISO)
            return
        segredos.salvar(**{f"{id_}_chave": chave})
        rot.configure(text="Testando...", text_color=tema.TEXTO_FRACO)

        def trabalho():
            inicio = time.time()
            try:
                c = cerebro.Cerebro({"cerebro": {"tipo": "ollama"}})
                if id_ == "gemini":
                    resposta = c._gemini("Responda so 'ok'.", [{"role": "user", "content": "oi"}], modelo=modelo, timeout=30)
                else:
                    resposta = c._nuvem_openai(id_, "Responda so 'ok'.", [{"role": "user", "content": "oi"}],
                                               modelo=modelo, timeout=30)
                demora = time.time() - inicio
                texto, cor = f"✓ Respondeu em {demora:.1f} s: “{resposta[:60]}”", tema.SUCESSO
            except Exception as erro:
                texto, cor = f"Não funcionou: {erro}", tema.AVISO
            try:
                self.after(0, lambda: rot.configure(text=texto, text_color=cor))
            except RuntimeError:
                pass
        threading.Thread(target=trabalho, daemon=True).start()

    # -----------------------------------------------------------------
    def _aba_conversa(self, pagina):
        from . import memoria
        from .cerebro import ORDEM_IA_PADRAO, PENALIDADE_MIN_PADRAO, ROTULOS_OPCOES_IA, TIMEOUT_TENTATIVA_PADRAO
        f = pagina   # (cada secao abaixo troca f pelo cartao dela)
        f = secao(pagina, "Modo conversa", "Depois de responder, ele fica ouvindo sem precisar da palavra de ativação por este "
                                   "tempo. 0 desliga. Se a TV atrapalhar, diminua.")
        self.var_janela = tk.IntVar(value=int(self._sec("conversa").get("janela_segundos", 10)))
        rot = ctk.CTkLabel(f, text="", anchor="w", text_color=tema.TEXTO_FRACO)
        linha_campo(f, "Segundos", lambda p: ctk.CTkSlider(p, from_=0, to=30, number_of_steps=30, variable=self.var_janela,
                                                           command=lambda v: rot.configure(text=f"{int(v)} segundos")))
        rot.pack(fill="x", padx=(32, 18))
        rot.configure(text=f"{self.var_janela.get()} segundos")
        cb = self._sec("cerebro")
        f = secao(pagina, "Quando a IA demora (Ollama)",
               "Se a IA passar do tempo abaixo, ela continua pensando em SEGUNDO PLANO: você volta a dar "
               "comandos e o indicador ganha uma bolinha roxa “Pensando”. Quando fica verde, diga “pode falar” "
               "ou “qual a resposta?”. “Cancela” descarta.")
        self.var_fundo = tk.IntVar(value=int(cb.get("segundo_plano_seg", 3)))
        self.var_maximo = tk.IntVar(value=int(cb.get("tempo_maximo", 120)))
        rot_ia = ctk.CTkLabel(f, text="", anchor="w", text_color=tema.TEXTO_FRACO)

        def mostrar_ia(*_):
            rot_ia.configure(text=f"Vai para segundo plano depois de {self.var_fundo.get()} s · "
                                  f"desiste depois de {self.var_maximo.get()} s")
        linha_campo(f, "Segundo plano depois de (s)", lambda p: ctk.CTkSlider(
            p, from_=1, to=30, number_of_steps=29, variable=self.var_fundo, command=mostrar_ia))
        linha_campo(f, "Desistir depois de (s)", lambda p: ctk.CTkSlider(
            p, from_=30, to=300, number_of_steps=27, variable=self.var_maximo, command=mostrar_ia))
        rot_ia.pack(fill="x", padx=(32, 18))
        mostrar_ia()
        self.AVISOS = {"tela": "Só mudar a cor no indicador", "voz": "Avisar e esperar eu pedir",
                       "falar_direto": "Falar a resposta direto"}
        self.var_aviso = tk.StringVar(value=self.AVISOS.get(cb.get("aviso_ao_terminar", "falar_direto"),
                                                            self.AVISOS["falar_direto"]))
        linha_campo(f, "Quando terminar", lambda p: ctk.CTkSegmentedButton(p, values=list(self.AVISOS.values()),
                                                                          variable=self.var_aviso))
        self.SONS_AVISO = {"nenhum": "Silêncio (só o indicador)", "bipe": "Bipe curtinho", "voz": "Voz curta"}
        self.var_bipe = tk.StringVar(value=self.SONS_AVISO.get(str(cb.get("aviso_som", "nenhum")), self.SONS_AVISO["nenhum"]))
        linha_campo(f, "Aviso do pensando", lambda p: ctk.CTkSegmentedButton(
            p, values=list(self.SONS_AVISO.values()), variable=self.var_bipe))
        self.var_contexto_kb = tk.IntVar(value=int(cb.get("memoria_contexto_kb", memoria.LIMITE_CONTEXTO_PADRAO_KB)))
        rot_ctx = ctk.CTkLabel(f, text="", anchor="w", text_color=tema.TEXTO_FRACO)
        linha_campo(f, "Memória mandada pra IA (KB)", lambda p: ctk.CTkSlider(
            p, from_=2, to=20, number_of_steps=18, variable=self.var_contexto_kb,
            command=lambda v: rot_ctx.configure(text=f"{int(v)} KB de fatos por pergunta (o índice sempre vai inteiro)")))
        rot_ctx.pack(fill="x", padx=(32, 18))
        rot_ctx.configure(text=f"{self.var_contexto_kb.get()} KB de fatos por pergunta (o índice sempre vai inteiro)")
        self.var_modelo_ia = tk.StringVar(value=str(cb.get("ollama_modelo", "qwen2.5:7b")))
        self.ent_modelo_ia = linha_campo(f, "Modelo do Ollama", lambda p: ctk.CTkComboBox(
            p, variable=self.var_modelo_ia, values=[self.var_modelo_ia.get()]))
        self.rot_ollama = ctk.CTkLabel(f, text="Procurando os modelos instalados no Ollama...", anchor="w", justify="left",
                                       wraplength=820, text_color=tema.TEXTO_FRACO)
        self.rot_ollama.pack(fill="x", padx=(32, 18))
        linha = ctk.CTkFrame(f, fg_color="transparent")
        linha.pack(fill="x", padx=(32, 18), pady=4)
        for modelo, dica in (("llama3.2:3b", "leve e rápido"), ("gemma3:4b", "bom em português")):
            ctk.CTkButton(linha, text=f"Baixar {modelo} ({dica})", **SECUNDARIO,
                          command=lambda m=modelo: sistema.abrir_terminal_com(
                              f"ollama pull {m}", PASTA_PROJETO, f"Baixando {m}")).pack(side="left", padx=(0, 8))
        ctk.CTkButton(linha, text="Atualizar o Ollama (site)", **SECUNDARIO,
                      command=lambda: webbrowser.open("https://ollama.com/download")).pack(side="left")
        self.after(500, self._procurar_modelos_ollama)

        from .cerebro import MODELOS_MENORES
        self._modelos_instalados_ollama: list[str] = []
        linha_menor = ctk.CTkFrame(f, fg_color="transparent")
        linha_menor.pack(fill="x", padx=(32, 18), pady=(8, 4))
        self.var_menor_escolha = tk.StringVar(value="qwen3:8b")

        def escolher_menor(v):
            self.var_menor_escolha.set(v.split(" (")[0])
            self._atualizar_status_menor()
        ctk.CTkOptionMenu(linha_menor, values=[f"{m} ({d})" for m, d in MODELOS_MENORES.items()],
                          command=escolher_menor, width=260).pack(side="left")
        self.btn_baixar_menor = ctk.CTkButton(linha_menor, text="Baixar modelo menor", width=180,
                                              command=self._baixar_modelo_menor)
        self.btn_baixar_menor.pack(side="left", padx=8)
        self.btn_testar_menor = ctk.CTkButton(linha_menor, text="Testar", width=90, state="disabled",
                                              **SECUNDARIO, command=self._testar_modelo_menor)
        self.btn_testar_menor.pack(side="left")
        self.rot_menor = ctk.CTkLabel(f, text="", anchor="w", justify="left", wraplength=820, text_color=tema.TEXTO_FRACO)
        self.rot_menor.pack(fill="x", padx=(32, 18))

        self.ROTULOS_IA = dict(ROTULOS_OPCOES_IA)
        f = secao(pagina, "Troca de IA sozinho (se uma demorar ou falhar)",
               "Se a 1ª opção passar do “tempo por tentativa” ou der erro, ele tenta a próxima da lista sozinho, "
               "na hora, sem travar a escuta. Quem falhar fica “de castigo” (não é tentada de novo por um "
               "tempo). Deixe o modelo do Ollama menor em branco para não usar uma 2ª opção do Ollama.")
        ordem_cfg = [i for i in (cb.get("ordem_ia") or ORDEM_IA_PADRAO) if i in self.ROTULOS_IA]
        ordem_cfg += [i for i in ORDEM_IA_PADRAO if i not in ordem_cfg]
        valores_ordem = list(self.ROTULOS_IA.values())
        self.var_ordem1 = tk.StringVar(value=self.ROTULOS_IA[ordem_cfg[0]])
        self.var_ordem2 = tk.StringVar(value=self.ROTULOS_IA[ordem_cfg[1]])
        self.var_ordem3 = tk.StringVar(value=self.ROTULOS_IA[ordem_cfg[2]])
        linha_campo(f, "1ª opção", lambda p: ctk.CTkOptionMenu(p, values=valores_ordem, variable=self.var_ordem1))
        linha_campo(f, "2ª opção", lambda p: ctk.CTkOptionMenu(p, values=valores_ordem, variable=self.var_ordem2))
        linha_campo(f, "3ª opção", lambda p: ctk.CTkOptionMenu(p, values=valores_ordem, variable=self.var_ordem3))
        self.var_modelo_menor = tk.StringVar(value=str(cb.get("ollama_modelo_menor", "")))
        self.ent_modelo_menor = linha_campo(f, "Modelo do Ollama menor (opcional)", lambda p: ctk.CTkComboBox(
            p, variable=self.var_modelo_menor, values=[self.var_modelo_menor.get() or "(nenhum)"]))
        self.var_timeout_tentativa = tk.IntVar(value=int(cb.get("timeout_tentativa_seg", TIMEOUT_TENTATIVA_PADRAO)))
        rot_tent = ctk.CTkLabel(f, text="", anchor="w", text_color=tema.TEXTO_FRACO)
        linha_campo(f, "Tempo por tentativa (s)", lambda p: ctk.CTkSlider(
            p, from_=5, to=90, number_of_steps=17, variable=self.var_timeout_tentativa,
            command=lambda v: rot_tent.configure(text=f"{int(v)} segundos e passa pra próxima opção")))
        rot_tent.pack(fill="x", padx=(32, 18))
        rot_tent.configure(text=f"{self.var_timeout_tentativa.get()} segundos e passa pra próxima opção")
        self.var_penalidade = tk.IntVar(value=int(cb.get("penalidade_min", PENALIDADE_MIN_PADRAO)))
        rot_pen = ctk.CTkLabel(f, text="", anchor="w", text_color=tema.TEXTO_FRACO)
        linha_campo(f, "Tempo de castigo (min)", lambda p: ctk.CTkSlider(
            p, from_=5, to=120, number_of_steps=23, variable=self.var_penalidade,
            command=lambda v: rot_pen.configure(text=f"{int(v)} minutos sem tentar de novo depois de falhar")))
        rot_pen.pack(fill="x", padx=(32, 18))
        rot_pen.configure(text=f"{self.var_penalidade.get()} minutos sem tentar de novo depois de falhar")
        self.ent_claude_chave = linha_campo(f, "Chave da API do Claude (opcional)",
                                            lambda p: ctk.CTkEntry(p, height=36, show="*"))
        self.ent_claude_chave.insert(0, segredos.ler("claude_chave"))

        from .cerebro import GEMINI_TEXTOS_LONGOS_PADRAO, NUVEM_MODELO_PADRAO, NUVEM_SITE_CHAVE
        f = secao(pagina, "IAs grátis na nuvem (opcionais)",
               "Mais opções pra “Troca de IA sozinho” acima: crie uma chave grátis (link abaixo de cada uma) "
               "e ligue a que quiser. Todas DESLIGADAS por padrão. Aviso: na nuvem, suas frases saem do seu PC "
               "e vão pro servidor da empresa escolhida (ao contrário do Ollama, que fica só no seu PC).",
               recolhida=True)
        self._nuvem_ia = {}
        cb = self._sec("cerebro")
        for id_, nome in (("groq", "Groq"), ("cerebras", "Cerebras"), ("openrouter", "OpenRouter"),
                          ("gemini", "Google Gemini")):
            self._linha_ia_nuvem(f, id_, nome, cb, NUVEM_MODELO_PADRAO[id_], NUVEM_SITE_CHAVE[id_])
        self.var_gemini_longos = tk.IntVar(value=int(cb.get("gemini_textos_longos_chars", GEMINI_TEXTOS_LONGOS_PADRAO)))
        rot_longos = ctk.CTkLabel(f, text="", anchor="w", text_color=tema.TEXTO_FRACO)
        linha_campo(f, "Preferir Gemini em textos longos (acima de)", lambda p: ctk.CTkSlider(
            p, from_=0, to=2000, number_of_steps=40, variable=self.var_gemini_longos,
            command=lambda v: rot_longos.configure(
                text="Desligado (nunca prefere)" if int(v) == 0 else f"{int(v)} caracteres no pedido (só se o Gemini estiver ligado)")))
        rot_longos.pack(fill="x", padx=(32, 18))
        rot_longos.configure(text="Desligado (nunca prefere)" if self.var_gemini_longos.get() == 0 else
                             f"{self.var_gemini_longos.get()} caracteres no pedido (só se o Gemini estiver ligado)")

        f = secao(pagina, "Sua cidade", "Usada no clima (“vai chover?”).")
        self.ent_cidade = ctk.CTkEntry(f, height=36)
        self.ent_cidade.insert(0, self._sec("assistente").get("cidade", "São Paulo"))
        self.ent_cidade.pack(fill="x", padx=(32, 18))

    def _ensinar_caixa(self):
        """5 s para parar o mouse em cima da caixa de mensagem do app Claude (ja maximizado)."""
        def trabalho():
            if not sistema.preparar_janela_do_claude():
                self.after(0, lambda: self.rot_envio.configure(text="Não achei o app Claude. Abra o app e tente de novo.",
                                                               text_color=tema.AVISO))
                return
            for n in range(5, 0, -1):
                self.after(0, lambda n=n: self.rot_envio.configure(
                    text=f"Pare o mouse EM CIMA da caixa de mensagem do Claude... {n}", text_color=tema.AVISO))
                time.sleep(1)
            pos = sistema.posicao_do_mouse_no_claude()
            if pos:
                self._posicao_caixa = pos
                texto, cor = (f"Aprendi! ({int(pos[0] * 100)}% da largura, {int(pos[1] * 100)}% da altura). "
                              "Clique em Salvar para guardar.", tema.SUCESSO)
            else:
                texto, cor = "O mouse não estava em cima da janela do Claude. Tente de novo.", tema.AVISO
            self.after(0, lambda: (self.rot_envio.configure(text=texto, text_color=cor), self.lift()))
        threading.Thread(target=trabalho, daemon=True).start()

    def _testar_envio(self):
        """Manda uma mensagem de teste para a conversa aberta no app Claude e mostra o resultado."""
        self.rot_envio.configure(text="Testando... não mexa no mouse por uns segundos.", text_color=tema.AVISO)

        def trabalho():
            ok = sistema.enviar_para_app_claude(
                "Teste do Mestre: se você está lendo isto, o envio automático funciona (pode ignorar).",
                enviar=bool(self.var_enviar_projeto.get()), altura_caixa=int(self.var_altura_caixa.get()),
                posicao=self._posicao_caixa or self._sec("projeto_mestre").get("posicao_caixa"))
            texto = ("Enviado. Confira no app Claude se a mensagem apareceu. Se não apareceu, mande para o Claude "
                     "o último print da pasta logs\\diagnostico." if ok else
                     "Não achei o app Claude (claude.exe). Ele está instalado? Abra o app e tente de novo.")
            try:
                self.after(0, lambda: (self.rot_envio.configure(text=texto, text_color=tema.SUCESSO if ok else tema.AVISO),
                                       self.lift()))
            except RuntimeError:
                pass
        threading.Thread(target=trabalho, daemon=True).start()

    def _atualizar_status_menor(self):
        """Mostra se o modelo escolhido na lista de sugeridos ja esta baixado e liga/desliga o botao Testar."""
        modelo = self.var_menor_escolha.get()
        ja_baixado = modelo in self._modelos_instalados_ollama
        self.btn_testar_menor.configure(state="normal" if ja_baixado else "disabled")
        if ja_baixado:
            self.rot_menor.configure(text=f"✓ {modelo} já está baixado neste PC.", text_color=tema.SUCESSO)
        else:
            self.rot_menor.configure(text=f"{modelo} ainda não foi baixado.", text_color=tema.TEXTO_FRACO)

    def _baixar_modelo_menor(self):
        from .cerebro import baixar_modelo_ollama, ollama_instalado
        if not ollama_instalado():
            self.rot_menor.configure(text="O Ollama não está instalado neste PC. Baixe em ollama.com/download e "
                                          "tente de novo.", text_color=tema.AVISO)
            return
        modelo = self.var_menor_escolha.get()
        self.btn_baixar_menor.configure(state="disabled")
        self.btn_testar_menor.configure(state="disabled")
        self.rot_menor.configure(text=f"Baixando {modelo}... isso pode demorar vários minutos.", text_color=tema.TEXTO_FRACO)

        def progresso(texto):
            try:
                self.after(0, lambda: self.rot_menor.configure(text=f"Baixando {modelo}: {texto}"))
            except RuntimeError:
                pass

        def trabalho():
            url = str(self._sec("cerebro").get("ollama_url", "http://localhost:11434"))
            erro = baixar_modelo_ollama(modelo, url, progresso)

            def terminou():
                self.btn_baixar_menor.configure(state="normal")
                if erro:
                    self.rot_menor.configure(text=f"Não consegui baixar {modelo}: {erro}", text_color=tema.AVISO)
                    return
                self.var_modelo_menor.set(modelo)
                valores = list(dict.fromkeys([modelo] + list(self.ent_modelo_menor.cget("values") or [])))
                self.ent_modelo_menor.configure(values=valores)
                if modelo not in self._modelos_instalados_ollama:
                    self._modelos_instalados_ollama.append(modelo)
                self.salvar()   # ja preenche e grava "ollama_modelo_menor" sozinho, sem precisar clicar em Salvar
                self.rot_menor.configure(text=f"✓ {modelo} baixado e salvo como “Modelo do Ollama menor”! "
                                              "Já pode usar na troca de IA sozinho.", text_color=tema.SUCESSO)
                self._atualizar_status_menor()
            try:
                self.after(0, terminou)
            except RuntimeError:
                pass
        threading.Thread(target=trabalho, daemon=True).start()

    def _testar_modelo_menor(self):
        from .cerebro import testar_modelo_ollama
        modelo = self.var_menor_escolha.get()
        self.btn_testar_menor.configure(state="disabled")
        self.rot_menor.configure(text=f"Testando {modelo}...", text_color=tema.TEXTO_FRACO)

        def trabalho():
            url = str(self._sec("cerebro").get("ollama_url", "http://localhost:11434"))
            erro = testar_modelo_ollama(modelo, url)

            def terminou():
                self.btn_testar_menor.configure(state="normal")
                if erro:
                    self.rot_menor.configure(text=f"{modelo} não respondeu: {erro}", text_color=tema.AVISO)
                else:
                    self.rot_menor.configure(text=f"✓ {modelo} respondeu certinho.", text_color=tema.SUCESSO)
            try:
                self.after(0, terminou)
            except RuntimeError:
                pass
        threading.Thread(target=trabalho, daemon=True).start()

    def _procurar_modelos_ollama(self):
        def trabalho():
            from .cerebro import modelos_do_ollama
            url = str(self._sec("cerebro").get("ollama_url", "http://localhost:11434"))
            modelos = modelos_do_ollama(url)
            texto = (f"{len(modelos)} modelo(s) instalado(s) no Ollama: escolha na lista. Mais leves respondem mais rápido."
                     if modelos else "O Ollama não respondeu (está fechado ou não instalado). Abra o Ollama e reabra esta página.")

            def terminou():
                self._modelos_instalados_ollama = modelos
                self.ent_modelo_ia.configure(values=modelos or [self.var_modelo_ia.get()])
                self.ent_modelo_menor.configure(
                    values=[""] + modelos if modelos else [self.var_modelo_menor.get() or "(nenhum)"])
                self.rot_ollama.configure(text=texto)
                self._atualizar_status_menor()
            try:
                self.after(0, terminou)
            except RuntimeError:
                pass
        threading.Thread(target=trabalho, daemon=True).start()

    def _aba_personalidade(self, pagina):
        f = pagina   # (cada secao abaixo troca f pelo cartao dela)
        a = self._sec("assistente")
        p = self._sec("personalidade")
        f = secao(pagina, "Nomes", "Como ele se chama, como ele te chama e a palavra que acorda ele. "
                           "A palavra de ativação deve ser UMA palavra fácil de pronunciar e pouco comum "
                           "(ex.: mestre, jarvis, luna). Os jeitos parecidos são gerados sozinhos.")
        self.ent_nome = linha_campo(f, "Nome DELE (o assistente)", lambda q: ctk.CTkEntry(q, height=36))
        self.ent_nome.insert(0, a.get("nome") or "Mestre")
        self.ent_apelido = linha_campo(f, "Como ele chama VOCÊ", lambda q: ctk.CTkEntry(q, height=36))
        self.ent_apelido.insert(0, a.get("apelido_usuario") or "chefe")
        self.ent_palavra = linha_campo(f, "Palavra que acorda ele", lambda q: ctk.CTkEntry(q, height=36))
        self.ent_palavra.insert(0, a.get("palavra_ativacao") or "mestre")
        rot_nomes = ctk.CTkLabel(f, text="", anchor="w", justify="left", wraplength=820, text_color=tema.TEXTO_FRACO)
        rot_nomes.pack(fill="x", padx=(32, 18))

        def exemplo_nomes(*_):
            nome = self.ent_nome.get().strip() or "Mestre"
            apelido = self.ent_apelido.get().strip() or "chefe"
            palavra = self.ent_palavra.get().strip() or "mestre"
            texto = f"Exemplo: você diz “E aí {palavra}” e ele responde “Opa {apelido}, manda ver!”. Ele se apresenta como {nome}."
            if nome.lower() == apelido.lower():
                texto += "  ⚠ O nome dele e o seu estão iguais: ele vai parecer que fala sozinho."
            rot_nomes.configure(text=texto, text_color=tema.AVISO if nome.lower() == apelido.lower() else tema.TEXTO_FRACO)
        for campo in (self.ent_nome, self.ent_apelido, self.ent_palavra):
            campo.bind("<KeyRelease>", exemplo_nomes)
        exemplo_nomes()

        f = secao(pagina, "Estilo", "Escolha um estilo e clique em “Aplicar”: a descrição e as frases abaixo são trocadas "
                            "pelas do estilo. Depois ajuste do seu jeito.")
        self.var_estilo = tk.StringVar(value=p.get("estilo") or personalidades.ESTILO_PADRAO)
        linha = ctk.CTkFrame(f, fg_color="transparent")
        linha.pack(fill="x", padx=(32, 18), pady=4)
        ctk.CTkOptionMenu(linha, values=list(personalidades.ESTILOS), variable=self.var_estilo, width=260).pack(side="left")
        ctk.CTkButton(linha, text="Aplicar estilo", width=140, command=self._aplicar_estilo).pack(side="left", padx=8)

        f = secao(pagina, "Descrição", "Como ele conversa quando a IA (cérebro) está ligada. {nome} e {apelido} são trocados sozinhos.")
        self.txt_desc = ctk.CTkTextbox(f, height=90, wrap="word")
        self.txt_desc.insert("1.0", personalidades.descricao_efetiva(p))
        self.txt_desc.pack(fill="x", padx=(32, 18))

        f = secao(pagina, "Frases", "Uma frase por linha; ele sorteia uma a cada vez. Pode usar {apelido}, {nome} e {saudacao}. "
                            "Dica: poucas vírgulas deixam a voz mais natural.")
        self.txt_falas = {}
        falas_estilo = personalidades.estilo(p.get("estilo"))["falas"]
        falas = p.get("falas") or {}
        for chave, nome in personalidades.SITUACOES.items():
            ctk.CTkLabel(f, text=nome, anchor="w", font=tema.fonte(13, True)).pack(
                fill="x", padx=(32, 18), pady=(10, 2))
            caixa = ctk.CTkTextbox(f, height=96, wrap="word")
            lista = list(dict.fromkeys(list(falas_estilo.get(chave, [])) + [str(x) for x in falas.get(chave) or []]))
            caixa.insert("1.0", "\n".join(lista))
            caixa.pack(fill="x", padx=(32, 18))
            self.txt_falas[chave] = caixa

    def _aplicar_estilo(self):
        e = personalidades.estilo(self.var_estilo.get())
        self.txt_desc.delete("1.0", "end")
        self.txt_desc.insert("1.0", e["descricao"])
        for chave, caixa in self.txt_falas.items():
            caixa.delete("1.0", "end")
            caixa.insert("1.0", "\n".join(e["falas"].get(chave, [])))
        self.aviso.configure(text=f"Estilo “{self.var_estilo.get()}” aplicado. Clique em Salvar.", text_color=tema.ROSA)

    # -----------------------------------------------------------------
    def _aba_ipm(self, pagina):
        f = pagina   # (cada secao abaixo troca f pelo cartao dela)
        c = self._sec("agente_ipm")
        f = secao(pagina, "Seu agente IPM no Claude")
        self.var_ipm_modo = tk.StringVar(value=c.get("modo", "site"))
        linha_campo(f, "Modo", lambda p: ctk.CTkSegmentedButton(p, values=["site", "cerebro"], variable=self.var_ipm_modo))
        ctk.CTkLabel(f, text="site = abre seu projeto no claude.ai e envia (grátis, Claude de verdade) · "
                            "cerebro = responde por voz com a IA local", anchor="w", text_color=tema.TEXTO_FRACO).pack(fill="x")
        self.ent_link = linha_campo(f, "Link do projeto", lambda p: ctk.CTkEntry(p))
        self.ent_link.insert(0, c.get("link_projeto", "https://claude.ai/projects"))
        self.var_seg = tk.IntVar(value=int(c.get("segundos_para_carregar", 7)))
        rot = ctk.CTkLabel(f, text=f"{self.var_seg.get()} s para a página carregar", anchor="w")
        linha_campo(f, "Espera antes de colar", lambda p: ctk.CTkSlider(p, from_=2, to=20, number_of_steps=18, variable=self.var_seg,
                                                                        command=lambda v: rot.configure(text=f"{int(v)} s para a página carregar")))
        rot.pack(fill="x")
        self.var_enviar = tk.BooleanVar(value=bool(c.get("enviar_automaticamente", True)))
        linha_campo(f, "Enviar sozinho", lambda p: ctk.CTkSwitch(p, text="apertar Enter depois de colar", variable=self.var_enviar))
        ctk.CTkButton(f, text="Testar: abrir o projeto", command=lambda: webbrowser.open(self.ent_link.get())).pack(anchor="w", pady=8)

        from .comandos import LINK_PROJETO_PADRAO
        pm = self._sec("projeto_mestre")
        f = secao(pagina, f"Projeto {self.nome} (Claude Code)",
               f"Para onde vão as melhorias ditadas (“{self.palavra}, quero ditar melhorias” … “finalizei”). "
               "Ele salva no MELHORIAS.md e manda o texto para o Claude (app do PC, terminal ou navegador; escolha abaixo). "
               "O link só é usado no modo Navegador.")
        self.ent_link_projeto = linha_campo(f, "Link da conversa", lambda p: ctk.CTkEntry(p))
        self.ent_link_projeto.insert(0, str(pm.get("link") or LINK_PROJETO_PADRAO))
        self.var_seg_projeto = tk.IntVar(value=int(pm.get("segundos_para_carregar", 8)))
        rot_p = ctk.CTkLabel(f, text=f"{self.var_seg_projeto.get()} s para a página carregar", anchor="w")
        linha_campo(f, "Espera antes de colar", lambda p: ctk.CTkSlider(
            p, from_=2, to=20, number_of_steps=18, variable=self.var_seg_projeto,
            command=lambda v: rot_p.configure(text=f"{int(v)} s para a página carregar")))
        rot_p.pack(fill="x", padx=(32, 18))
        self.MODOS_PROJETO = {"app": "App Claude do PC", "terminal": "Claude Code no terminal", "navegador": "Navegador"}
        self.var_modo_projeto = tk.StringVar(value=self.MODOS_PROJETO.get(pm.get("modo", "app"), self.MODOS_PROJETO["app"]))
        linha_campo(f, "Mandar por", lambda p: ctk.CTkSegmentedButton(p, values=list(self.MODOS_PROJETO.values()),
                                                                     variable=self.var_modo_projeto))
        ctk.CTkLabel(f, text=f"App Claude: cola na conversa que estiver ABERTA no app (deixe o app nesta conversa). "
                            f"Terminal: abre o Claude Code na pasta do {self.nome} (conversa nova, o mais garantido).",
                     anchor="w", justify="left", wraplength=820, text_color=tema.TEXTO_FRACO).pack(fill="x", padx=(32, 18))
        self.var_altura_caixa = tk.IntVar(value=int(pm.get("altura_caixa", 90)))
        rot_alt = ctk.CTkLabel(f, text=f"Clica {self.var_altura_caixa.get()} pixels acima do rodapé da janela "
                                       "(se ele clicar no lugar errado, ajuste aqui)", anchor="w", text_color=tema.TEXTO_FRACO)
        linha_campo(f, "Onde fica a caixa de texto", lambda p: ctk.CTkSlider(
            p, from_=40, to=220, number_of_steps=18, variable=self.var_altura_caixa,
            command=lambda v: rot_alt.configure(text=f"Clica {int(v)} pixels acima do rodapé da janela "
                                                     "(se ele clicar no lugar errado, ajuste aqui)")))
        rot_alt.pack(fill="x", padx=(32, 18))
        self.var_enviar_projeto = tk.BooleanVar(value=bool(pm.get("enviar_automaticamente", True)))
        linha_campo(f, "Enviar sozinho", lambda p: ctk.CTkSwitch(p, text="apertar Enter depois de colar",
                                                                 variable=self.var_enviar_projeto))
        botoes_teste = ctk.CTkFrame(f, fg_color="transparent")
        botoes_teste.pack(fill="x", padx=(32, 18), pady=8)
        ctk.CTkButton(botoes_teste, text="Testar envio para o app Claude", command=self._testar_envio).pack(side="left")
        ctk.CTkButton(botoes_teste, text="Ensinar onde fica a caixa", **SECUNDARIO,
                      command=self._ensinar_caixa).pack(side="left", padx=(8, 0))
        self._posicao_caixa = None
        pos = pm.get("posicao_caixa")
        ctk.CTkButton(botoes_teste, text="Abrir a conversa no navegador", **SECUNDARIO,
                      command=lambda: webbrowser.open(self.ent_link_projeto.get())).pack(side="left", padx=8)
        self.rot_envio = ctk.CTkLabel(f, text="", anchor="w", justify="left", wraplength=820, text_color=tema.TEXTO_FRACO)
        self.rot_envio.pack(fill="x", padx=(32, 18))
        if pos:
            self.rot_envio.configure(text=f"Posição ensinada: {int(float(pos[0]) * 100)}% da largura, "
                                          f"{int(float(pos[1]) * 100)}% da altura da janela do Claude.")

        from . import projetos
        pj = self._sec("projetos")
        f = secao(pagina, "Projetos guiados", f"“{self.palavra}, quero começar um novo projeto”: ele pergunta o tipo, o nome e o "
                                      "objetivo, cria a pasta com um PLANO.md e a IA sugere 3 caminhos (ou o 4º: mandar pro Claude).")
        linha = linha_campo(f, "Pasta dos projetos", lambda p: ctk.CTkFrame(p, fg_color="transparent"))
        self.ent_pasta_projetos = ctk.CTkEntry(linha, placeholder_text=str(projetos.pasta_base({})))
        if pj.get("pasta"):
            self.ent_pasta_projetos.insert(0, str(pj["pasta"]))
        self.ent_pasta_projetos.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(linha, text="Escolher...", width=100, **SECUNDARIO, command=lambda: (
            lambda d: (self.ent_pasta_projetos.delete(0, "end"), self.ent_pasta_projetos.insert(0, d)) if d else None)(
            filedialog.askdirectory(title="Pasta dos projetos"))).pack(side="left", padx=6)
        ctk.CTkButton(linha, text="Abrir", width=70, **SECUNDARIO, command=lambda: sistema.abrir_arquivo(
            projetos.pasta_base({"projetos": {"pasta": self.ent_pasta_projetos.get()}}))).pack(side="left")
        self.var_pesquisas = tk.BooleanVar(value=bool(pj.get("abrir_pesquisas", True)))
        linha_campo(f, "Pesquisas", lambda p: ctk.CTkSwitch(
            p, text="abrir pesquisas no navegador depois de escolher o caminho", variable=self.var_pesquisas))
        self.var_pesquisar_web = tk.BooleanVar(value=bool(pj.get("pesquisar_internet", True)))
        linha_campo(f, "Pesquisa automática", lambda p: ctk.CTkSwitch(
            p, text="pesquisar o objetivo na internet antes da IA sugerir os caminhos", variable=self.var_pesquisar_web))

    # -----------------------------------------------------------------
    def _aba_youtube(self, pagina):
        f = pagina   # (cada secao abaixo troca f pelo cartao dela)
        f = secao(pagina, "Canais do YouTube",
               f"Nome que você fala → @ do canal (ou link). Diga: “{self.palavra}, abre o último vídeo do <nome>”. "
               "Para trazer TODAS as suas inscrições de uma vez, use um dos botões de importar.")
        b = ctk.CTkFrame(f, fg_color="transparent")
        b.pack(fill="x", padx=(28, 18), pady=4)
        ctk.CTkButton(b, text="Importar do Google Takeout (.csv)", command=self._importar_takeout).pack(side="left", padx=4)
        ctk.CTkButton(b, text="Importar do Firefox", **SECUNDARIO, command=lambda: self._importar_navegador("firefox")).pack(side="left", padx=4)
        ctk.CTkButton(b, text="Importar arquivo OPML/XML", **SECUNDARIO, command=self._importar_opml).pack(side="left", padx=4)
        ctk.CTkButton(b, text="Como exportar do Takeout?", **SECUNDARIO, command=self._ajuda_takeout).pack(side="left", padx=4)
        self.rot_yt = ctk.CTkLabel(f, text="", anchor="w", text_color=tema.TEXTO_FRACO)
        self.rot_yt.pack(fill="x")
        yt = self._sec("youtube")
        f = secao(pagina, "Controlar o YouTube por voz",
               "Fale com o YouTube aberto: “tela cheia”, “dá like”, “se inscreve”, “fecha o chat”, "
               "“abre o terceiro vídeo”, “lê os títulos”, “avança 30 segundos”…")
        self.var_yt_nav = tk.BooleanVar(value=bool(yt.get("navegador_mestre", True)))
        linha_campo(f, "Comandos de voz", lambda p: ctk.CTkSwitch(
            p, text="ligados (desligado: o YouTube abre no navegador padrão, sem comandos)", variable=self.var_yt_nav))
        self.NAVEGADORES = {"brave": "Brave", "msedge": "Edge", "chrome": "Chrome"}
        self.var_yt_canal = tk.StringVar(value=self.NAVEGADORES.get(yt.get("navegador", "brave"), "Brave"))
        linha_campo(f, "Navegador", lambda p: ctk.CTkSegmentedButton(p, values=list(self.NAVEGADORES.values()),
                                                                     variable=self.var_yt_canal))
        self.MODOS_YT = {"extensao": "Meu Brave + extensão (recomendado)", "controlado": "Janela controlada",
                         "normal": "Meu Brave (só teclas)"}
        self.var_yt_modo = tk.StringVar(value=self.MODOS_YT.get(yt.get("modo", "extensao"), self.MODOS_YT["extensao"]))
        linha_campo(f, "Modo", lambda p: ctk.CTkSegmentedButton(p, values=list(self.MODOS_YT.values()), variable=self.var_yt_modo))
        ctk.CTkLabel(f, text="Meu Brave + extensão: o seu Brave de sempre (com seus logins) e TODOS os comandos. "
                            "Instale a extensão uma vez: brave://extensions > ligue o Modo de desenvolvedor > "
                            "“Carregar sem compactação” > escolha a pasta extensao_brave (botão abaixo abre a pasta). "
                            "Depois recarregue o YouTube (F5). Depois de cada atualização pela Central, clique na setinha redonda "
                            "da extensão em brave://extensions. Ela também deixa separar abas e mandar para outro "
                            "monitor (“separa a Netflix pro monitor 2”).", anchor="w", justify="left", wraplength=820,
                     text_color=tema.TEXTO_FRACO).pack(fill="x", padx=(32, 18))
        linha_ext = ctk.CTkFrame(f, fg_color="transparent")
        linha_ext.pack(fill="x", padx=(32, 18), pady=4)
        ctk.CTkButton(linha_ext, text="Abrir a pasta da extensão", **SECUNDARIO,
                      command=lambda: sistema.abrir_arquivo(PASTA_PROJETO / "extensao_brave")).pack(side="left")
        self.rot_ext = ctk.CTkLabel(linha_ext, text="", anchor="w")
        self.rot_ext.pack(side="left", padx=10)
        self.after(1500, self._ver_extensao)
        ctk.CTkButton(f, text="Só no modo Janela controlada: entrar na minha conta", **SECUNDARIO,
                      command=self._abrir_janela_youtube).pack(anchor="w", padx=(32, 18), pady=(4, 12))
        self.tab_canais = TabelaChaveValor(f, self.cfg.get("canais_youtube") or {}, "Nome falado", "@ do canal ou link",
                                           testar=lambda k, v: webbrowser.open(youtube.url_canal(v)) if v else None)
        b2 = ctk.CTkFrame(f, fg_color="transparent")
        b2.pack(fill="x", pady=(8, 4))
        ctk.CTkButton(b2, text="+ Adicionar canal", command=lambda: self.tab_canais.adicionar()).pack(side="left", padx=4)
        ctk.CTkButton(b2, text="Apagar todos os canais", **PERIGO, command=self._apagar_canais).pack(side="right", padx=4)
        self.tab_canais.pack(fill="both", expand=True, padx=(24, 14))

    def _ver_extensao(self):
        def trabalho():
            from .ponte import VERSAO_EXTENSAO, desatualizada, versao_da_extensao
            versao = versao_da_extensao()
            if not versao:
                texto, cor = (f"○ extensão ainda não conectou (o {self.nome} está ligado? o Brave está aberto? "
                              "recarregou a extensão?)", tema.TEXTO_FRACO)
            elif desatualizada(versao):
                texto, cor = (f"⚠ extensão conectada, mas na versão {versao} (a nova é a {VERSAO_EXTENSAO}): "
                              "brave://extensions > setinha redonda no cartão dela > F5 no YouTube", tema.AVISO)
            else:
                texto, cor = f"● extensão conectada (versão {versao})", tema.SUCESSO
            try:
                self.after(0, lambda: self.rot_ext.configure(text=texto, text_color=cor))
                self.after(5000, self._ver_extensao)
            except RuntimeError:
                pass
        threading.Thread(target=trabalho, daemon=True).start()

    def _abrir_janela_youtube(self):
        """Abre o navegador do Mestre no YouTube (pelo proprio Mestre, para usar o mesmo perfil)."""
        from .navegador import Navegador
        if not Navegador.disponivel():
            messagebox.showinfo(self.nome, "Falta a biblioteca do navegador. Use Atualizar o Mestre (.zip) ou rode "
                                           "o INSTALAR_E_CRIAR_ATALHO.bat.")
            return
        canal = next(k for k, v in self.NAVEGADORES.items() if v == self.var_yt_canal.get())
        threading.Thread(target=lambda: Navegador(canal).abrir("https://accounts.google.com/ServiceLogin?service=youtube"),
                         daemon=True).start()
        messagebox.showinfo(self.nome, "Entre na sua conta do Google nessa janela e depois feche-a. "
                                       "O login fica guardado para os comandos de voz.")

    def _apagar_canais(self):
        n = self.tab_canais.quantidade()
        if n and messagebox.askyesno(self.nome, f"Apagar os {n} canais da lista?\n(Só vale depois de Salvar.)"):
            self.tab_canais.apagar_todos()
            self.rot_yt.configure(text="Lista vazia. Clique em Salvar para confirmar.")

    def _juntar_canais(self, novos: dict):
        n = self.tab_canais.adicionar_varios(novos)
        self.rot_yt.configure(text=f"{n} canais novos importados ({len(novos)} encontrados). Clique em Salvar.")

    def _importar_takeout(self):
        caminho = filedialog.askopenfilename(title="Arquivo de inscrições do Takeout",
                                             filetypes=[("Planilha CSV", "*.csv"), ("Todos", "*.*")])
        if caminho:
            try:
                self._juntar_canais(youtube.importar_takeout_csv(caminho))
            except Exception as erro:
                messagebox.showerror(self.nome, f"Não consegui ler o arquivo:\n{erro}")

    def _importar_opml(self):
        caminho = filedialog.askopenfilename(filetypes=[("OPML/XML", "*.opml *.xml"), ("Todos", "*.*")])
        if caminho:
            try:
                self._juntar_canais(youtube.importar_opml(caminho))
            except Exception as erro:
                messagebox.showerror(self.nome, f"Não consegui ler o arquivo:\n{erro}")

    def _importar_navegador(self, navegador: str):
        self.rot_yt.configure(text=f"Lendo suas inscrições pelo {navegador}... (feche o navegador antes)")

        def trabalho():
            try:
                canais = youtube.importar_do_navegador(navegador)
                self.after(0, lambda: self._juntar_canais(canais))
            except Exception as erro:
                self.after(0, lambda e=erro: self.rot_yt.configure(
                    text=f"Não deu pelo {navegador} ({str(e)[:90]}). Use o Google Takeout."))
        threading.Thread(target=trabalho, daemon=True).start()

    def _ajuda_takeout(self):
        messagebox.showinfo("Exportar inscrições do YouTube", (
            "1. Abra takeout.google.com (vou abrir para você).\n"
            "2. Clique em “Desmarcar tudo”. Desça até “YouTube e YouTube Music” e marque.\n"
            "3. Clique em “Todos os dados do YouTube incluídos”, desmarque tudo e deixe só “inscrições”.\n"
            "4. Próxima etapa > Criar exportação. O Google manda um e-mail com o link (leva alguns minutos).\n"
            "5. Baixe o .zip, extraia e procure o arquivo inscricoes.csv (ou subscriptions.csv).\n"
            "6. Volte aqui e clique em “Importar do Google Takeout”."))
        webbrowser.open("https://takeout.google.com/")

    # -----------------------------------------------------------------
    def _aba_programas(self, pagina):
        f = pagina   # (cada secao abaixo troca f pelo cartao dela)
        f = secao(pagina, "Programas", "Nome que você fala → programa (nome curto como notepad, ou caminho do .exe).")
        self.tab_prog = TabelaChaveValor(f, self.cfg.get("programas") or {}, "Nome falado", "Programa",
                                         testar=self._testar_programa)
        self.tab_prog.pack(fill="x", padx=(24, 14))
        b = ctk.CTkFrame(f, fg_color="transparent")
        b.pack(fill="x", padx=(28, 18), pady=4)
        ctk.CTkButton(b, text="+ Adicionar", command=lambda: self.tab_prog.adicionar()).pack(side="left", padx=4)
        ctk.CTkButton(b, text="Procurar programa no PC...", **SECUNDARIO, command=self._procurar_programa).pack(side="left", padx=4)
        f = secao(pagina, "Sites", "Nome que você fala → endereço.")
        self.tab_sites = TabelaChaveValor(f, self.cfg.get("sites") or {}, "Nome falado", "Endereço (https://...)",
                                          testar=lambda k, v: sistema.abrir_site(v) if v else None)
        self.tab_sites.pack(fill="x", padx=(24, 14))
        ctk.CTkButton(f, text="+ Adicionar site", command=lambda: self.tab_sites.adicionar()).pack(anchor="w", pady=4)
        self.var_sites_brave = tk.BooleanVar(value=(self._sec("janelas").get("navegador_sites", "brave") == "brave"))
        linha_campo(f, "Navegador dos sites", lambda p: ctk.CTkSwitch(
            p, text="abrir os sites no Brave (onde estão os meus logins), mesmo que o padrão do Windows seja outro",
            variable=self.var_sites_brave))
        self.ent_perfil_brave = linha_campo(f, "Perfil do Brave", lambda p: ctk.CTkEntry(
            p, placeholder_text="vazio = o último que você usou (ex.: Profile 1)"))
        if self._sec("janelas").get("perfil_brave"):
            self.ent_perfil_brave.insert(0, str(self._sec("janelas").get("perfil_brave")))
        self._secao_monitores(pagina)

    def _secao_monitores(self, pagina):
        jn = self._sec("janelas")
        lista = sistema.monitores()
        f = secao(pagina, "Monitores", f"Fale “… no monitor 2” (ou o nome abaixo) para abrir lá. “Joga essa janela pro monitor 3” "
                               f"move a janela da frente. 1 = principal; depois os de mais Hz (dá para falar a marca: “monitor AOC”, "
                               f"ou os Hz: “monitor de 144”). "
                               f"Monitores encontrados: {len(lista) or '?'}.")
        self.var_principal = tk.BooleanVar(value=bool(jn.get("sempre_no_principal", True)))
        linha_campo(f, "Padrão", lambda p: ctk.CTkSwitch(
            p, text="abrir sempre no monitor principal (quando eu não disser outro)", variable=self.var_principal))
        nomes = jn.get("nomes_monitores") or {}
        self.ent_monitores = {}
        for n in range(1, max(3, len(lista)) + 1):
            info = next((m for m in lista if m["numero"] == n), None)
            rotulo = f"Monitor {n}" + (f" ({info['descricao']})" if info else "")
            e = linha_campo(f, rotulo, lambda p: ctk.CTkEntry(
                p, placeholder_text={1: "ex.: principal", 2: "ex.: da esquerda", 3: "ex.: da TV"}.get(n, "")))
            if nomes.get(str(n)) or nomes.get(n):
                e.insert(0, str(nomes.get(str(n)) or nomes.get(n)))
            self.ent_monitores[n] = e
        ctk.CTkButton(f, text="Identificar monitores", **SECUNDARIO, command=self._identificar_monitores).pack(
            anchor="w", padx=(32, 18), pady=6)

    def _identificar_monitores(self):
        """Mostra um numero grande em cada monitor por 3 segundos."""
        lista = sistema.monitores()
        if not lista:
            messagebox.showinfo(self.nome, "Não consegui ler os monitores deste PC.")
            return
        for m in lista:
            janela = ctk.CTkToplevel(self)
            janela.overrideredirect(True)
            janela.attributes("-topmost", True)
            x, y = tema.posicao_janela(m['x'] + m['largura'] // 2 - 130, m['y'] + m['altura'] // 2 - 130)
            janela.geometry(f"260x260+{x}+{y}")
            ctk.CTkLabel(janela, text=str(m["numero"]), text_color=tema.ROSA, font=tema.fonte(130, True)).pack(expand=True)
            ctk.CTkLabel(janela, text=m.get("descricao", ""), font=tema.fonte(16, True)).pack(pady=(0, 16))
            janela.after(3000, janela.destroy)

    def _testar_programa(self, nome: str, alvo: str):
        if not alvo:
            messagebox.showinfo(self.nome, "Escreva o programa (nome curto ou caminho) antes de testar.")
            return
        problema = sistema.problema_no_programa(alvo)
        if problema:
            messagebox.showwarning(self.nome, problema)
            return
        sistema.abrir_programa(alvo)
        self.aviso.configure(text=f"Abrindo {nome or alvo}... Se não abriu, confira o caminho.", text_color=tema.TEXTO_FRACO)

    def _procurar_programa(self):
        caminho = filedialog.askopenfilename(title="Escolha o programa",
                                             filetypes=[("Programas e atalhos", "*.exe *.lnk"), ("Todos", "*.*")])
        if caminho:
            self.tab_prog.adicionar(Path(caminho).stem.lower(), caminho.replace("/", "\\"))

    # -----------------------------------------------------------------
    def _aba_rotinas(self, pagina):
        f = pagina   # (cada secao abaixo troca f pelo cartao dela)
        f = secao(pagina, "Rotinas", "Uma frase dispara várias ações em sequência. Escolha a rotina à esquerda e edite à direita.")
        self.rotinas = [dict(nome=r.get("nome", ""), frases=list(r.get("frases", [])),
                             acoes=[dict(a) for a in r.get("acoes", [])]) for r in (self.cfg.get("rotinas") or [])]
        # nomes de quando o painel abriu: uma rotina ensinada por voz DEPOIS disso (nome novo no
        # arquivo) precisa sobreviver ao salvar; ver configuracao.mesclar_novas_por_nome
        self._rotinas_iniciais = {str(r["nome"]).strip().lower() for r in self.rotinas}
        corpo = ctk.CTkFrame(f, fg_color="transparent")
        corpo.pack(fill="both", expand=True)
        self.lista_rotinas = ctk.CTkFrame(corpo, width=220)
        self.lista_rotinas.pack(side="left", fill="y", padx=(0, 10))
        self.editor = ctk.CTkFrame(corpo)
        self.editor.pack(side="left", fill="both", expand=True)
        self.rotina_atual = 0 if self.rotinas else None
        self._desenhar_lista_rotinas()
        self._desenhar_editor()

    def _desenhar_lista_rotinas(self):
        for w in self.lista_rotinas.winfo_children():
            w.destroy()
        for i, r in enumerate(self.rotinas):
            ctk.CTkButton(self.lista_rotinas, text=r["nome"] or "(sem nome)", anchor="w",
                          **(dict(fg_color=tema.ROSA_FUNDO, text_color=tema.ROSA, hover_color=tema.ROSA_FUNDO) if i == self.rotina_atual else SECUNDARIO),
                          command=lambda i=i: self._escolher_rotina(i)).pack(fill="x", pady=2, padx=6)
        ctk.CTkButton(self.lista_rotinas, text="+ Nova rotina",
                      command=self._nova_rotina).pack(fill="x", pady=(12, 2), padx=6)

    def _guardar_editor(self):
        if self.rotina_atual is None or not hasattr(self, "ent_rot_nome"):
            return
        r = self.rotinas[self.rotina_atual]
        r["nome"] = self.ent_rot_nome.get().strip()
        r["frases"] = [x.strip() for x in self.ent_rot_frases.get().split(",") if x.strip()]
        acoes = []
        for tipo_var, ent in self.linhas_acoes:
            tipo = next(k for k, v in ACOES_ROTINA.items() if v == tipo_var.get())
            valor = ent.get().strip() if ent else True
            if isinstance(valor, str) and valor.replace(".", "", 1).isdigit():
                valor = float(valor) if "." in valor else int(valor)   # "3" -> 3
            if tipo == "esperar" and valor in ("", True):
                valor = 1
            acoes.append({tipo: valor if valor != "" else True})
        r["acoes"] = acoes

    def _escolher_rotina(self, i):
        self._guardar_editor()
        self.rotina_atual = i
        self._desenhar_lista_rotinas()
        self._desenhar_editor()

    def _nova_rotina(self):
        self._guardar_editor()
        self.rotinas.append(dict(nome="Nova rotina", frases=["minha frase"], acoes=[{"falar": "Olá!"}]))
        self.rotina_atual = len(self.rotinas) - 1
        self._desenhar_lista_rotinas()
        self._desenhar_editor()

    def _desenhar_editor(self):
        for w in self.editor.winfo_children():
            w.destroy()
        self.linhas_acoes = []
        if self.rotina_atual is None:
            ctk.CTkLabel(self.editor, text="Nenhuma rotina. Clique em “+ Nova rotina”.").pack(pady=20)
            return
        r = self.rotinas[self.rotina_atual]
        self.ent_rot_nome = linha_campo(self.editor, "Nome", lambda p: ctk.CTkEntry(p), 140)
        self.ent_rot_nome.insert(0, r["nome"])
        self.ent_rot_frases = linha_campo(self.editor, "Frases (separe por vírgula)", lambda p: ctk.CTkEntry(p), 140)
        self.ent_rot_frases.insert(0, ", ".join(r["frases"]))
        ctk.CTkLabel(self.editor, text="Ações (na ordem):", anchor="w", font=tema.fonte(14, True)).pack(fill="x", padx=8, pady=(8, 2))
        for i, acao in enumerate(r["acoes"]):
            tipo, valor = next(iter(acao.items()))
            linha = ctk.CTkFrame(self.editor, fg_color="transparent")
            linha.pack(fill="x", padx=8, pady=2)
            var = tk.StringVar(value=ACOES_ROTINA.get(tipo, ACOES_ROTINA["comando"]))
            ctk.CTkOptionMenu(linha, values=list(ACOES_ROTINA.values()), variable=var, width=250, dynamic_resizing=False,
                              command=lambda v: (self._guardar_editor(), self._desenhar_editor())).pack(side="left")
            ent = None
            if tipo not in SEM_VALOR:
                ent = ctk.CTkEntry(linha, width=330)
                ent.insert(0, "" if valor is True else str(valor))
                ent.pack(side="left", padx=4)
            else:  # espaco vazio para as setas ficarem alinhadas
                ctk.CTkFrame(linha, width=338, height=1, fg_color="transparent").pack(side="left")
            for txt, cmd in (("↑", lambda i=i: self._mover_acao(i, -1)), ("↓", lambda i=i: self._mover_acao(i, 1)),
                             ("✕", lambda i=i: self._remover_acao(i))):
                ctk.CTkButton(linha, text=txt, width=30, **(SECUNDARIO if txt != "✕" else PERIGO),
                              command=cmd).pack(side="left", padx=2)
            self.linhas_acoes.append((var, ent))
        b = ctk.CTkFrame(self.editor, fg_color="transparent")
        b.pack(fill="x", padx=8, pady=8)
        ctk.CTkButton(b, text="+ Adicionar ação", command=self._adicionar_acao).pack(side="left", padx=4)
        ctk.CTkButton(b, text="▶ Salvar e testar", **SECUNDARIO, command=self._testar_rotina).pack(side="left", padx=4)
        ctk.CTkButton(b, text="Apagar esta rotina", **PERIGO,
                      command=self._apagar_rotina).pack(side="right", padx=4)

    def _testar_rotina(self):
        """Salva e roda a rotina pela PRIMEIRA frase dela, igual a quando você fala."""
        self._guardar_editor()
        r = self.rotinas[self.rotina_atual]
        if not r["frases"]:
            messagebox.showinfo(self.nome, "Escreva pelo menos uma frase para esta rotina.")
            return
        if not self.salvar():
            return
        frase = r["frases"][0]
        self.aviso.configure(text=f"Testando: “{frase}”...", text_color=tema.TEXTO_FRACO)

        def trabalho():
            saida = sistema.rodar_comando(frase)
            if f"Rotina: {r['nome']}" in saida:
                texto, cor = f"A rotina “{r['nome']}” rodou pela frase “{frase}”.", tema.SUCESSO
            else:
                import re
                outra = re.search(r"Rotina: (.+)", saida)
                texto = (f"A frase “{frase}” disparou OUTRA rotina: {outra.group(1)}. Mude a frase." if outra else
                         f"A frase “{frase}” não disparou a rotina. Veja o diário (log).")
                cor = tema.AVISO
            self.after(0, lambda: self.aviso.configure(text=texto, text_color=cor))
        threading.Thread(target=trabalho, daemon=True).start()

    def _mover_acao(self, i, passo):
        self._guardar_editor()
        acoes = self.rotinas[self.rotina_atual]["acoes"]
        j = i + passo
        if 0 <= j < len(acoes):
            acoes[i], acoes[j] = acoes[j], acoes[i]
        self._desenhar_editor()

    def _remover_acao(self, i):
        self._guardar_editor()
        del self.rotinas[self.rotina_atual]["acoes"][i]
        self._desenhar_editor()

    def _adicionar_acao(self):
        self._guardar_editor()
        self.rotinas[self.rotina_atual]["acoes"].append({"falar": ""})
        self._desenhar_editor()

    def _apagar_rotina(self):
        if messagebox.askyesno(self.nome, "Apagar esta rotina?"):
            del self.rotinas[self.rotina_atual]
            self.rotina_atual = 0 if self.rotinas else None
            self._desenhar_lista_rotinas()
            self._desenhar_editor()

    # -----------------------------------------------------------------
    def _aba_spotify(self, pagina):
        f = pagina   # (cada secao abaixo troca f pelo cartao dela)
        sp = self._sec("spotify")
        f = secao(pagina, "Playlists do Spotify",
               f"Nome que você fala → link da playlist (no Spotify: ··· > Compartilhar > Copiar link). Diga: "
               f"“{self.palavra}, toca a playlist <nome> no Spotify”. Sem playlist cadastrada, ele abre a busca do app.")
        from .comandos import link_spotify
        self.tab_playlists = TabelaChaveValor(f, sp.get("playlists") or {}, "Nome falado", "Link da playlist",
                                              testar=lambda k, v: sistema.abrir_site(link_spotify(v)) if v else None)
        ctk.CTkButton(f, text="+ Adicionar playlist", command=lambda: self.tab_playlists.adicionar()).pack(anchor="w", pady=4)
        self.tab_playlists.pack(fill="x", padx=(24, 14))
        linha_sp = ctk.CTkFrame(f, fg_color="transparent")
        linha_sp.pack(fill="x", padx=(32, 18), pady=6)
        ctk.CTkButton(linha_sp, text="Testar volume só do Spotify", **SECUNDARIO,
                      command=self._testar_volume_spotify).pack(side="left")
        self.rot_vol_sp = ctk.CTkLabel(linha_sp, text="(deixe uma música tocando)", text_color=tema.TEXTO_FRACO)
        self.rot_vol_sp.pack(side="left", padx=10)
        self.var_tocar_em = tk.StringVar(value="YouTube" if sp.get("tocar_musica_em") == "youtube" else "Spotify")
        linha_campo(f, "“toca …” sem dizer onde", lambda p: ctk.CTkSegmentedButton(
            p, values=["Spotify", "YouTube"], variable=self.var_tocar_em))
        self.var_play = tk.BooleanVar(value=bool(sp.get("apertar_play", True)))
        linha_campo(f, "Começar a tocar", lambda p: ctk.CTkSwitch(
            p, text="apertar Play sozinho depois de abrir a playlist (se o Spotify ignorar, é um clique)",
            variable=self.var_play))

    def _testar_volume_spotify(self):
        def trabalho():
            r = sistema.volume_do_programa("Spotify.exe", "diminuir", 0.3)
            if not r:
                time.sleep(1.5)
                sistema.volume_do_programa("Spotify.exe", "aumentar", 0.3)
            texto = {"": "OK: o Spotify abaixou e voltou, sem mexer no volume do computador.",
                     "nao_tocando": "Não achei o Spotify tocando. Dê play numa música e teste de novo.",
                     "sem_biblioteca": "Falta a biblioteca (pycaw). Use Atualizar o Mestre (.zip) na Central."}.get(r, f"Erro: {r}")
            try:
                self.after(0, lambda: self.rot_vol_sp.configure(text=texto, text_color=tema.SUCESSO if not r else tema.AVISO))
            except RuntimeError:
                pass
        threading.Thread(target=trabalho, daemon=True).start()

    # -----------------------------------------------------------------
    def _aba_celular(self, pagina):
        f = pagina   # (cada secao abaixo troca f pelo cartao dela)
        from . import recebidos
        rc = self._sec("recebidos")
        f = secao(pagina, "O que ele faz com o áudio", f"Começou com “{self.palavra}, …”? Ele executa como comando "
                                               f"(ex.: “{self.palavra.capitalize()}, abre o YouTube”). Senão, vai para o destino abaixo. "
                                               "O texto fica guardado na pasta recebidos.")
        self.DESTINOS_CELULAR = {"projeto": "Projeto no app do Claude", "nota": "Minhas notas", "ipm": "Agente IPM"}
        self.var_destino_cel = tk.StringVar(value=self.DESTINOS_CELULAR.get(str(rc.get("destino", "projeto")),
                                                                            self.DESTINOS_CELULAR["projeto"]))
        linha_campo(f, "Destino", lambda p: ctk.CTkSegmentedButton(p, values=list(self.DESTINOS_CELULAR.values()),
                                                                     variable=self.var_destino_cel))
        self.AVISOS_CELULAR = {"tela_e_voz": "Tela e voz", "tela": "Só na tela", "voz": "Só a frase", "nenhum": "Nenhum"}
        self.var_aviso_cel = tk.StringVar(value=self.AVISOS_CELULAR.get(str(rc.get("aviso", "tela_e_voz")),
                                                                        self.AVISOS_CELULAR["tela_e_voz"]))
        linha_campo(f, "Aviso quando chega", lambda p: ctk.CTkSegmentedButton(p, values=list(self.AVISOS_CELULAR.values()),
                                                                                variable=self.var_aviso_cel))
        self.ent_frase_telegram = linha_campo(f, "Frase do Telegram", lambda p: ctk.CTkEntry(p, height=36))
        self.ent_frase_telegram.insert(0, str(rc.get("frase_telegram") or "Mensagem do Telegram."))
        self.ent_frase_pasta = linha_campo(f, "Frase da pasta", lambda p: ctk.CTkEntry(p, height=36))
        self.ent_frase_pasta.insert(0, str(rc.get("frase_pasta") or "Áudio do celular."))

        f = secao(pagina, "1. Pasta sincronizada (o mais simples)",
               "No celular: no áudio do WhatsApp (ou do gravador) toque em Compartilhar > Drive (ou OneDrive) e salve "
               "na pasta abaixo. No PC, a mesma pasta precisa aparecer (Google Drive para computador ou OneDrive). "
               "Ele transcreve em poucos segundos e move o áudio para a subpasta “lidos”. Passo a passo: guia, Etapa 30.")
        self.var_pasta_audios = tk.BooleanVar(value=bool(rc.get("pasta_ligada", True)))
        linha_campo(f, "Vigiar a pasta", lambda p: ctk.CTkSwitch(p, text="ligado", variable=self.var_pasta_audios))
        self.ent_pasta_audios = linha_campo(f, "Pasta dos áudios", lambda p: ctk.CTkEntry(p, height=36))
        self.ent_pasta_audios.insert(0, str(rc.get("pasta") or ""))
        self.ent_pasta_audios.configure(placeholder_text=str(recebidos.pasta_padrao()))
        linha = ctk.CTkFrame(f, fg_color="transparent")
        linha.pack(fill="x", padx=(32, 18), pady=4)

        def escolher():
            pasta = filedialog.askdirectory(title="Pasta onde os áudios do celular chegam")
            if pasta:
                self.ent_pasta_audios.delete(0, "end")
                self.ent_pasta_audios.insert(0, pasta)

        def abrir():
            pasta = Path(self.ent_pasta_audios.get().strip() or recebidos.pasta_padrao())
            pasta.mkdir(parents=True, exist_ok=True)
            sistema.abrir_arquivo(pasta)
        ctk.CTkButton(linha, text="Escolher pasta...", **SECUNDARIO, command=escolher).pack(side="left")
        ctk.CTkButton(linha, text="Abrir a pasta", **SECUNDARIO, command=abrir).pack(side="left", padx=8)

        f = secao(pagina, "2. Telegram (de qualquer lugar)",
               "No Telegram, fale com @BotFather > /newbot > dê um nome > copie o TOKEN e cole aqui. Depois mande "
               "“oi” para o seu robô: a primeira conversa vira a sua (só ela é atendida). O token fica no seu usuário "
               "do Windows, fora da pasta do projeto.")
        self.var_telegram = tk.BooleanVar(value=bool(rc.get("telegram_ligado", True)))
        linha_campo(f, "Telegram", lambda p: ctk.CTkSwitch(p, text="ligado", variable=self.var_telegram))
        self.ent_telegram = linha_campo(f, "Token do robô", lambda p: ctk.CTkEntry(p, height=36, show="•"))
        self.ent_telegram.insert(0, segredos.ler("telegram_token"))
        linha_t = ctk.CTkFrame(f, fg_color="transparent")
        linha_t.pack(fill="x", padx=(32, 18), pady=4)
        ctk.CTkButton(linha_t, text="Salvar token e testar", width=200, command=self._testar_telegram).pack(side="left")
        ctk.CTkButton(linha_t, text="Esquecer o meu chat", **SECUNDARIO,
                      command=lambda: (segredos.salvar(telegram_chat="", telegram_nome=""), self._estado_telegram())
                      ).pack(side="left", padx=8)
        self.rot_telegram = ctk.CTkLabel(f, text="", anchor="w", justify="left", wraplength=820, text_color=tema.TEXTO_FRACO)
        self.rot_telegram.pack(fill="x", padx=(32, 18))
        self._estado_telegram()

        f = secao(pagina, "3. Avisos do PC",
               "Manda uma mensagem no Telegram acima quando o PC desliga/reinicia e quando liga de novo "
               "(e avisa se o desligamento anterior foi uma queda de energia ou travou). Guia, Etapa 35.")
        ap = self._sec("avisos_pc")
        self.var_avisos_pc = tk.BooleanVar(value=bool(ap.get("ligado", True)))
        linha_campo(f, "Avisar “PC ligou” / “PC desligando”", lambda p: ctk.CTkSwitch(
            p, text="ligado", variable=self.var_avisos_pc))
        self.var_healthchecks = tk.BooleanVar(value=bool(ap.get("healthchecks_ligado", False)))
        linha_campo(f, "Pulso pro healthchecks.io", lambda p: ctk.CTkSwitch(
            p, text="ligado (avisa NA HORA se faltar energia)", variable=self.var_healthchecks))
        self.ent_healthchecks = linha_campo(f, "URL do ping", lambda p: ctk.CTkEntry(p, height=36))
        self.ent_healthchecks.insert(0, segredos.ler("healthchecks_url"))
        self.ent_healthchecks.configure(placeholder_text="https://hc-ping.com/xxxxxxxx-xxxx-...")
        linha_hc = ctk.CTkFrame(f, fg_color="transparent")
        linha_hc.pack(fill="x", padx=(32, 18), pady=4)
        ctk.CTkButton(linha_hc, text="Testar pulso", **SECUNDARIO, command=self._testar_healthchecks).pack(side="left")
        self.rot_healthchecks = ctk.CTkLabel(linha_hc, text="", text_color=tema.TEXTO_FRACO)
        self.rot_healthchecks.pack(side="left", padx=10)

    def _testar_healthchecks(self):
        from . import avisos_pc
        url = self.ent_healthchecks.get().strip()
        segredos.salvar(healthchecks_url=url)

        def trabalho():
            if not url:
                texto, cor = "Cole a URL do ping primeiro.", tema.AVISO
            else:
                ok = avisos_pc.pulso_healthchecks({"avisos_pc": {"healthchecks_ligado": True,
                                                                  "healthchecks_url": url}})
                texto = "✓ Pulso enviado." if ok else "Não consegui mandar o pulso (confira a URL)."
                cor = tema.SUCESSO if ok else tema.AVISO
            try:
                self.after(0, lambda: self.rot_healthchecks.configure(text=texto, text_color=cor))
            except RuntimeError:
                pass
        threading.Thread(target=trabalho, daemon=True).start()

    def _estado_telegram(self, texto: str = ""):
        chat = segredos.ler("telegram_nome") or segredos.ler("telegram_chat")
        base = (f"Conectado com o chat de {chat}." if chat else
                f"Nenhum chat ainda: mande “oi” para o seu robô com o {self.nome} ligado.") if segredos.ler("telegram_token") \
            else "Sem token ainda."
        self.rot_telegram.configure(text=(texto + "  " if texto else "") + base + f" (Reinicie o {self.nome} depois de mudar.)")

    def _testar_telegram(self):
        from . import recebidos
        token = self.ent_telegram.get().strip()
        segredos.salvar(telegram_token=token)

        def trabalho():
            try:
                texto = f"✓ Token certo: seu robô é {recebidos.testar_telegram(token)}."
            except Exception as erro:
                texto = f"Token não funcionou: {erro}"
            try:
                self.after(0, lambda: self._estado_telegram(texto))
            except RuntimeError:
                pass
        threading.Thread(target=trabalho, daemon=True).start()

    # -----------------------------------------------------------------
    def _aba_historico(self, pagina):
        f = pagina   # (cada secao abaixo troca f pelo cartao dela)
        from . import memoria
        f = secao(pagina, "Histórico", "Tudo que você pediu e o que ele respondeu (os mais novos em cima). Por voz: "
                               "“repete a resposta”, “lê as últimas respostas”, “o que você respondeu sobre …”.")
        barra = ctk.CTkFrame(f, fg_color="transparent")
        barra.pack(fill="x", padx=(32, 18))
        self.var_busca_hist = tk.StringVar()
        ctk.CTkLabel(barra, text="Buscar:", text_color=tema.TEXTO_FRACO).pack(side="left")
        ctk.CTkEntry(barra, textvariable=self.var_busca_hist, width=260).pack(side="left", padx=6)
        ctk.CTkButton(barra, text="Atualizar", width=90, **SECUNDARIO, command=self._mostrar_historico).pack(side="left")
        self.var_busca_hist.trace_add("write", lambda *_: self._mostrar_historico())
        self.txt_hist = ctk.CTkTextbox(f, height=330, wrap="word")
        self.txt_hist.pack(fill="x", padx=(32, 18), pady=6)
        self._mostrar_historico()
        f = secao(pagina, "Exportar para o Claude", "Gera um arquivo com tudo que foi falado nos testes: o que ele ouviu, "
                                            "o que entendeu, qual comando atendeu e o que foi para a IA. Arraste o "
                                            "arquivo para a conversa com o Claude para ele achar os erros. "
                                            f"Por voz: “{self.palavra}, exporta o histórico”.")
        from .exportar import PERIODOS
        linha = ctk.CTkFrame(f, fg_color="transparent")
        linha.pack(fill="x", padx=(32, 18), pady=4)
        self.var_periodo_exp = tk.StringVar(value="7 dias")
        ctk.CTkSegmentedButton(linha, values=list(PERIODOS), variable=self.var_periodo_exp).pack(side="left")
        ctk.CTkButton(linha, text="⇪  Exportar para o Claude", width=210, command=self._exportar_historico).pack(side="left", padx=10)
        self.rot_exportar = ctk.CTkLabel(f, text="", anchor="w", justify="left", wraplength=820, text_color=tema.TEXTO_FRACO)
        self.rot_exportar.pack(fill="x", padx=(32, 18))
        f = secao(pagina, "Memória", f"Fatos que ele guarda para a IA usar (“{self.palavra}, lembra que …”), "
                             "organizados por assunto. Um por linha em cada caixa: edite ou apague e clique em Salvar.")
        self.txt_fatos_assunto = {}
        self._fatos_iniciais_assunto = {}
        for assunto in memoria.ASSUNTOS:
            ctk.CTkLabel(f, text=f"{assunto.capitalize()} — {memoria.DESCRICAO_ASSUNTO.get(assunto, '')}",
                        anchor="w", text_color=tema.TEXTO_FRACO).pack(fill="x", padx=(32, 18), pady=(8, 0))
            caixa = ctk.CTkTextbox(f, height=70, wrap="word")
            iniciais = memoria.fatos_assunto(assunto)
            caixa.insert("1.0", "\n".join(iniciais))
            caixa.pack(fill="x", padx=(32, 18), pady=(2, 4))
            self.txt_fatos_assunto[assunto] = caixa
            self._fatos_iniciais_assunto[assunto] = iniciais

    def _exportar_historico(self):
        from . import exportar
        try:
            arquivo = exportar.gerar(self.cfg, self.var_periodo_exp.get())
        except Exception as erro:
            self.rot_exportar.configure(text=f"Não consegui exportar: {erro}", text_color=tema.AVISO)
            return
        sistema.mostrar_na_pasta(arquivo)
        self.rot_exportar.configure(text=f"✓ Pronto: {arquivo.name} (a pasta abriu com ele marcado). "
                                         "Arraste para a conversa com o Claude.", text_color=tema.SUCESSO)

    def _mostrar_historico(self):
        from . import memoria
        from .texto import normalizar
        termo = normalizar(self.var_busca_hist.get())
        itens = [i for i in reversed(memoria.historico(400))
                 if not termo or termo in normalizar(i.get("pedido", "") + " " + i.get("resposta", ""))]
        self.txt_hist.configure(state="normal")
        self.txt_hist.delete("1.0", "end")
        self.txt_hist.insert("1.0", "\n\n".join(
            f"{i['data']} · você: {i.get('pedido', '')}\n        {self.nome}: {i.get('resposta') or '(sem resposta falada)'}"
            for i in itens[:150]) or "(nada ainda)")
        self.txt_hist.configure(state="disabled")

    # -----------------------------------------------------------------
    def _aba_aparencia(self, pagina):
        f = pagina   # (cada secao abaixo troca f pelo cartao dela)
        atual = {**tema.PADRAO, **{k: str(v) for k, v in self._sec("aparencia").items() if v}}
        self.vars_aparencia = {k: tk.StringVar(value=atual[k]) for k in ("cor", "fundo", "fonte", "tamanho")}
        v = self.vars_aparencia
        f = secao(pagina, "Cores e fonte", "Escolha e veja a prévia ao lado. “Aplicar” salva e reabre a Central com o visual "
                                   "novo. A cor de destaque vale também para o indicador e o ícone perto do relógio.")
        corpo = ctk.CTkFrame(f, fg_color="transparent")
        corpo.pack(fill="x", padx=12)
        opcoes = ctk.CTkFrame(corpo, fg_color="transparent")
        opcoes.pack(side="left", fill="both", expand=True)
        nomes_cor = list(tema.CORES)
        linha = linha_campo(opcoes, "Cor de destaque", lambda p: ctk.CTkFrame(p, fg_color="transparent"), 150)
        self.menu_cor = ctk.CTkOptionMenu(linha, values=nomes_cor + ["Personalizada"], width=170,
                                          command=lambda c: self._escolher_cor() if c == "Personalizada" else self._previa())
        self.menu_cor.set(v["cor"].get() if v["cor"].get() in nomes_cor else "Personalizada")
        self.menu_cor.pack(side="left")
        ctk.CTkButton(linha, text="Escolher cor...", width=120, **SECUNDARIO,
                      command=self._escolher_cor).pack(side="left", padx=6)
        linha_campo(opcoes, "Fundo", lambda p: ctk.CTkOptionMenu(p, values=list(tema.FUNDOS), variable=v["fundo"],
                                                                 command=lambda _: self._previa()), 150)
        import tkinter.font as tkfont
        instaladas = set(tkfont.families(self))
        self._fontes_comuns = [x for x in tema.FONTES if x in instaladas] or tema.FONTES
        self._fontes_todas = sorted(x for x in instaladas if not x.startswith("@"))
        linha_f = linha_campo(opcoes, "Fonte", lambda p: ctk.CTkFrame(p, fg_color="transparent"), 150)
        self.menu_fonte = ctk.CTkComboBox(linha_f, values=self._fontes_comuns, variable=v["fonte"], width=230,
                                          command=lambda _: self._previa())
        self.menu_fonte.pack(side="left")
        self.var_todas_fontes = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(linha_f, text=f"todas do PC ({len(self._fontes_todas)})", variable=self.var_todas_fontes,
                        command=lambda: self.menu_fonte.configure(
                            values=self._fontes_todas if self.var_todas_fontes.get() else self._fontes_comuns)
                        ).pack(side="left", padx=8)
        linha_campo(opcoes, "Tamanho do texto", lambda p: ctk.CTkSegmentedButton(
            p, values=list(tema.TAMANHOS), variable=v["tamanho"], command=lambda _: self._previa()), 150)
        botoes = ctk.CTkFrame(opcoes, fg_color="transparent")
        botoes.pack(fill="x", padx=(32, 18), pady=12)
        ctk.CTkButton(botoes, text="Aplicar (reabre a Central)", height=38, command=self._aplicar_aparencia).pack(side="left")
        ctk.CTkButton(botoes, text="Voltar ao padrão", height=38, **SECUNDARIO,
                      command=self._aparencia_padrao).pack(side="left", padx=8)

        # previa: um "painel em miniatura" pintado com as cores escolhidas
        self.previa = ctk.CTkFrame(corpo, width=330, height=250, corner_radius=14, border_width=1)
        self.previa.pack(side="right", padx=(12, 12), pady=8)
        self.previa.pack_propagate(False)
        self.pv_lateral = ctk.CTkFrame(self.previa, width=110, corner_radius=0)
        self.pv_lateral.pack(side="left", fill="y")
        self.pv_marca = ctk.CTkLabel(self.pv_lateral, text=f"● {self.nome}")
        self.pv_marca.pack(anchor="w", padx=10, pady=(14, 8))
        self.pv_item = ctk.CTkLabel(self.pv_lateral, text="  ⌂  Início", anchor="w", corner_radius=8)
        self.pv_item.pack(fill="x", padx=6)
        self.pv_item2 = ctk.CTkLabel(self.pv_lateral, text="  ♪  Voz", anchor="w")
        self.pv_item2.pack(fill="x", padx=6, pady=2)
        self.pv_conteudo = ctk.CTkFrame(self.previa, corner_radius=0)
        self.pv_conteudo.pack(side="left", fill="both", expand=True)
        self.pv_titulo = ctk.CTkLabel(self.pv_conteudo, text="Início", anchor="w")
        self.pv_titulo.pack(fill="x", padx=12, pady=(14, 0))
        self.pv_texto = ctk.CTkLabel(self.pv_conteudo, text="Assim fica o texto.", anchor="w")
        self.pv_texto.pack(fill="x", padx=12)
        self.pv_cartao = ctk.CTkFrame(self.pv_conteudo, corner_radius=10)
        self.pv_cartao.pack(fill="x", padx=12, pady=10)
        self.pv_botao = ctk.CTkButton(self.pv_cartao, text="▶ Ligar", width=90, hover=False)
        self.pv_botao.pack(side="left", padx=8, pady=10)
        self.pv_botao2 = ctk.CTkButton(self.pv_cartao, text="Reiniciar", width=80, hover=False)
        self.pv_botao2.pack(side="left", pady=10)
        self.pv_campo = ctk.CTkLabel(self.pv_conteudo, text="  campo de texto", anchor="w", corner_radius=6)
        self.pv_campo.pack(fill="x", padx=12)
        self._previa()

        # indicador na tela: avatar robô (padrão) ou a bolinha de antes
        from . import avatar
        f = secao(pagina, "Indicador na tela", "O que fica perto do relógio mostrando se ele está ouvindo, pensando "
                                               "ou falando. Vale depois de reiniciar o assistente.")
        tipo = avatar.tipo_escolhido(self.cfg)
        self.var_indicador = tk.StringVar(value=avatar.TIPOS[tipo])
        linha_campo(f, "Indicador", lambda p: ctk.CTkSegmentedButton(p, values=list(avatar.TIPOS.values()),
                                                                     variable=self.var_indicador), 150)
        if not avatar.pyside_instalado():
            ctk.CTkLabel(f, text="O avatar precisa da biblioteca PySide6 (instale pelo INSTALAR_E_CRIAR_ATALHO.bat). "
                                 "Sem ela, aparece a bolinha.", anchor="w", text_color=tema.AVISO,
                         wraplength=640, justify="left").pack(fill="x", padx=(32, 18), pady=(0, 6))
        ctk.CTkLabel(f, text="Avatar: arraste para mudar de lugar · duplo clique abre o painel · botão direito: pausar, "
                             "voltar ao lugar padrão ou esconder.", anchor="w", text_color=tema.TEXTO_FRACO,
                     wraplength=640, justify="left").pack(fill="x", padx=(32, 18), pady=(0, 8))

    def _escolher_cor(self):
        from tkinter import colorchooser

        atual = tema.paleta({k: x.get() for k, x in self.vars_aparencia.items()})["ROSA"]
        escolhida = colorchooser.askcolor(color=atual, title="Cor de destaque", parent=self)[1]
        if escolhida:
            self.vars_aparencia["cor"].set(escolhida.upper())
            self.menu_cor.set("Personalizada")
        elif self.vars_aparencia["cor"].get() in tema.CORES:
            self.menu_cor.set(self.vars_aparencia["cor"].get())
        self._previa()

    def _previa(self):
        v = self.vars_aparencia
        if self.menu_cor.get() in tema.CORES:
            v["cor"].set(self.menu_cor.get())
        c = tema.paleta({k: x.get() for k, x in v.items()})
        delta = c["TAMANHO"] - 14
        f = lambda n, b=False: ctk.CTkFont(family=c["FONTE"], size=n + delta, weight="bold" if b else "normal")  # noqa: E731
        self.previa.configure(fg_color=c["FUNDO"], border_color=c["BORDA"])
        self.pv_lateral.configure(fg_color=c["LATERAL"])
        self.pv_marca.configure(text_color=c["ROSA"], font=f(15, True))
        self.pv_item.configure(fg_color=c["ROSA_FUNDO"], text_color=c["ROSA"], font=f(12))
        self.pv_item2.configure(text_color=tema.TEXTO, font=f(12))
        self.pv_conteudo.configure(fg_color=c["FUNDO"])
        self.pv_titulo.configure(text_color=tema.TEXTO, font=f(17, True))
        self.pv_texto.configure(text_color=tema.TEXTO_FRACO, font=f(11))
        self.pv_cartao.configure(fg_color=c["CARTAO"])
        self.pv_botao.configure(fg_color=c["ROSA"], text_color=c["TEXTO_NO_ROSA"], font=f(12, True))
        self.pv_botao2.configure(fg_color=c["SECUNDARIO"], text_color=tema.TEXTO, font=f(12))
        self.pv_campo.configure(fg_color=c["CAMPO"], text_color=tema.TEXTO_FRACO, font=f(11))

    def _aparencia_padrao(self):
        for k, x in self.vars_aparencia.items():
            x.set(tema.PADRAO[k])
        self.menu_cor.set(tema.PADRAO["cor"])
        self._previa()

    def _aplicar_aparencia(self):
        if not self.salvar():
            return
        try:
            tema.salvar_icones(tema.paleta({k: x.get() for k, x in self.vars_aparencia.items()})["ROSA"])
        except Exception:
            pass   # sem Pillow o icone fica como estava
        self._fechar()
        sistema.abrir_painel()

    # -----------------------------------------------------------------
    def _aba_atalhos(self, pagina):
        f = pagina   # (cada secao abaixo troca f pelo cartao dela)
        f = secao(pagina, "Atalhos ensinados", "Frase curta → comando completo. (Os que você ensina por voz aparecem aqui.)")
        self.tab_atalhos = TabelaChaveValor(f, self.vocab.aprendido.get("atalhos") or {}, "Quando eu falar", f"O {self.nome} faz")
        self.tab_atalhos.pack(fill="x", padx=(24, 14))
        # frases de quando o painel abriu: um atalho ensinado por voz DEPOIS disso precisa sobreviver ao salvar
        self._atalhos_iniciais = {str(k).strip().lower() for k in (self.vocab.aprendido.get("atalhos") or {})}
        ctk.CTkButton(f, text="+ Adicionar atalho", command=lambda: self.tab_atalhos.adicionar()).pack(anchor="w", pady=4)
        f = secao(pagina, "Vocabulário avançado", "Sinônimos e palavras ignoradas ficam no vocabulario.yaml.")
        ctk.CTkButton(f, text="Abrir vocabulario.yaml", **SECUNDARIO,
                      command=lambda: sistema.abrir_arquivo(PASTA_PROJETO / "vocabulario.yaml")).pack(anchor="w")

    # -----------------------------------------------------------------
    def _aba_melhorias(self, pagina):
        f = pagina   # (cada secao abaixo troca f pelo cartao dela)
        from .comandos import ARQUIVO_MELHORIAS
        f = secao(pagina, "Lista de melhorias", "As ideias que você anota por voz. Pode escrever aqui também, uma por linha "
                                        "no formato: - [ ] minha ideia")
        self.txt_melhorias = ctk.CTkTextbox(f, height=320)
        self.txt_melhorias.insert("1.0", ARQUIVO_MELHORIAS.read_text(encoding="utf-8") if ARQUIVO_MELHORIAS.exists()
                                  else "# Melhorias para o Mestre\n\n")
        self.txt_melhorias.pack(fill="both", expand=True)
        ctk.CTkButton(f, text="Refinar e aplicar com o Claude Code",
                      command=self._aplicar_melhorias).pack(anchor="w", pady=6)

    def _aplicar_melhorias(self):
        self._salvar_melhorias()
        from .comandos import PROMPT_MELHORIAS
        sistema.abrir_terminal_com(f'claude "{PROMPT_MELHORIAS}"', PASTA_PROJETO, f"{self.nome} - melhorias")

    def _salvar_melhorias(self):
        from .comandos import ARQUIVO_MELHORIAS
        ARQUIVO_MELHORIAS.write_text(self.txt_melhorias.get("1.0", "end").rstrip() + "\n", encoding="utf-8")

    # -----------------------------------------------------------------
    #  Validar atualizacao (frases do ROTEIRO_VALIDACAO.md, uma por vez)
    # -----------------------------------------------------------------
    def _aba_validacao(self, pagina):
        from . import validacao
        self._val = None            # validacao.Sessao em andamento
        self._val_captura = None    # o que o assistente registrou para a frase da tela
        self._val_sugestao = None
        self._val_errado_desde = 0.0   # clicou ❌: a proxima frase ouvida vira "o certo era"
        self._val_ultimo_comando_claude = None   # "Mandar para o Claude corrigir" (para o teste automatico)
        self._val_estado = ""        # modo continuo: esperando | ok | falha | conferir | silencio
        self._val_descartes = []     # frases que o ouvido jogou fora (com o motivo)
        self._val_avanco = None      # after() que passa para a proxima frase depois do ✅
        f = secao(pagina, "Validar atualização",
                  f"Depois de atualizar, fale as frases do roteiro uma por vez ao {self.nome} (ligado, como sempre). "
                  "Para cada frase o painel mostra o que ele OUVIU, o que ENTENDEU (e qual comando atendeu) e o que "
                  "FEZ, compara com o esperado e sugere ✅ ou ❌. Você confirma. No fim sai um relatório em "
                  "exportacoes/ e cada ❌ vira um FEEDBACK na lista de melhorias.")
        linha = ctk.CTkFrame(f, fg_color="transparent")
        linha.pack(fill="x", padx=(32, 18), pady=4)
        self.var_val_escolha = tk.StringVar(value="Só novidades")
        ctk.CTkSegmentedButton(linha, values=list(validacao.ESCOLHAS), variable=self.var_val_escolha).pack(side="left")
        self.bt_val_comecar = ctk.CTkButton(linha, text="▶  Começar", width=130, command=self._val_comecar)
        self.bt_val_comecar.pack(side="left", padx=10)
        opcoes = ctk.CTkFrame(f, fg_color="transparent")
        opcoes.pack(fill="x", padx=(32, 18), pady=(2, 0))
        self.var_val_continuo = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(opcoes, text="Modo contínuo (passa sozinho quando dá certo, só para no ❌)",
                        variable=self.var_val_continuo).pack(side="left")
        self.var_val_manuais = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(opcoes, text="Incluir linhas de painel/visual", variable=self.var_val_manuais).pack(side="left",
                                                                                                        padx=14)
        self.rot_val_progresso = ctk.CTkLabel(f, text="", anchor="w", text_color=tema.TEXTO_FRACO)
        self.rot_val_progresso.pack(fill="x", padx=(32, 18), pady=(6, 0))
        self.rot_val_frase = ctk.CTkLabel(f, text="", anchor="w", justify="left", wraplength=800,
                                          font=tema.fonte(18, True), text_color=tema.ROSA)
        self.rot_val_frase.pack(fill="x", padx=(32, 18), pady=(2, 0))
        self.rot_val_esperado = ctk.CTkLabel(f, text="", anchor="w", justify="left", wraplength=800,
                                             text_color=tema.TEXTO_FRACO)
        self.rot_val_esperado.pack(fill="x", padx=(32, 18), pady=(0, 6))
        self.rot_val_linhas = {}
        for chave, rotulo in (("ouvi", "OUVI"), ("entendi", "ENTENDI"), ("fiz", "FIZ")):
            lf = ctk.CTkFrame(f, fg_color="transparent")
            lf.pack(fill="x", padx=(32, 18), pady=1)
            ctk.CTkLabel(lf, text=rotulo, width=80, anchor="w", font=tema.fonte(13, True)).pack(side="left")
            valor = ctk.CTkLabel(lf, text="-", anchor="w", justify="left", wraplength=700)
            valor.pack(side="left", fill="x", expand=True)
            self.rot_val_linhas[chave] = valor
        self.rot_val_sugestao = ctk.CTkLabel(f, text="", anchor="w", justify="left", wraplength=800,
                                             font=tema.fonte(14, True))
        self.rot_val_sugestao.pack(fill="x", padx=(32, 18), pady=(6, 2))
        # destaque do ❌ no modo continuo: OUVI → ENTENDI → FIZ grandes + por que o ouvido descartou
        self.fr_val_destaque = ctk.CTkFrame(f, fg_color=tema.CARTAO, corner_radius=12, border_width=2,
                                            border_color=tema.AVISO)
        self.rot_val_destaque = {}
        for chave, rotulo, tamanho, cor in (("ouvi", "OUVI", 20, tema.TEXTO), ("entendi", "ENTENDI", 20, tema.ROSA),
                                            ("fiz", "FIZ", 18, tema.AVISO), ("descartes", "DESCARTEI", 16, tema.AVISO)):
            lf = ctk.CTkFrame(self.fr_val_destaque, fg_color="transparent")
            lf.pack(fill="x", padx=14, pady=3)
            ctk.CTkLabel(lf, text=rotulo, width=120, anchor="nw", font=tema.fonte(15, True),
                         text_color=tema.TEXTO_FRACO).pack(side="left", anchor="n")
            valor = ctk.CTkLabel(lf, text="-", anchor="w", justify="left", wraplength=640,
                                 font=tema.fonte(tamanho, True), text_color=cor)
            valor.pack(side="left", fill="x", expand=True)
            self.rot_val_destaque[chave] = (lf, valor)
        botoes = ctk.CTkFrame(f, fg_color="transparent")
        botoes.pack(fill="x", padx=(32, 18), pady=4)
        self.bt_val_ok = ctk.CTkButton(botoes, text="✅  Deu certo", width=130, command=lambda: self._val_marcar("ok"))
        self.bt_val_ok.pack(side="left", padx=(0, 6))
        self.bt_val_erro = ctk.CTkButton(botoes, text="❌  Deu errado", width=130, **PERIGO, command=self._val_errado)
        self.bt_val_erro.pack(side="left", padx=6)
        self._val_botoes = [self.bt_val_ok, self.bt_val_erro]
        for texto, acao in (("Pular", lambda: self._val_marcar("pulado")), ("Repetir", self._val_repetir),
                            ("◀ Anterior", self._val_anterior), ("■ Parar", self._val_parar)):
            b = ctk.CTkButton(botoes, text=texto, width=96, **SECUNDARIO, command=acao)
            b.pack(side="left", padx=4)
            self._val_botoes.append(b)
        # "o certo era..." (so aparece depois do ❌)
        self.fr_val_certo = ctk.CTkFrame(f, fg_color="transparent")
        ctk.CTkLabel(self.fr_val_certo, text="O certo era:", width=100, anchor="w").pack(side="left")
        self.ent_val_certo = ctk.CTkEntry(self.fr_val_certo, width=420,
                                          placeholder_text=f"digite, ou fale sem chamar o {self.nome}")
        self.ent_val_certo.pack(side="left", padx=4, fill="x", expand=True)
        ctk.CTkButton(self.fr_val_certo, text="Salvar ❌ e seguir", width=150, **PERIGO,
                      command=self._val_confirmar_erro).pack(side="left", padx=4)
        self.rot_val_resultado = ctk.CTkLabel(f, text="", anchor="w", justify="left", wraplength=800,
                                              text_color=tema.TEXTO_FRACO)
        self.rot_val_resultado.pack(fill="x", padx=(32, 18), pady=(6, 0))
        fr_val_pos = ctk.CTkFrame(f, fg_color="transparent")
        fr_val_pos.pack(fill="x", padx=(32, 18), pady=4)
        self.bt_val_relatorio = ctk.CTkButton(fr_val_pos, text="Abrir o relatório", width=150, **SECUNDARIO,
                                              command=self._val_abrir_relatorio)
        self.bt_val_claude = ctk.CTkButton(fr_val_pos, text="🛠  Mandar para o Claude corrigir", width=240,
                                           **SECUNDARIO, command=self._val_mandar_claude)
        self.bt_val_claude.pack(side="left", padx=(0, 8))
        self._val_atualizar_botao_claude()
        self._val_desenhar()

    def _val_atualizar_botao_claude(self):
        from . import validacao
        relatorio = validacao.ultimo_relatorio()
        ativo = validacao.relatorio_tem_falhas(relatorio)
        self.bt_val_claude.configure(state="normal" if ativo else "disabled")

    def _val_mandar_claude(self):
        from . import validacao
        relatorio = validacao.ultimo_relatorio()
        if not validacao.relatorio_tem_falhas(relatorio):
            return
        pedido = validacao.pedido_de_correcao(relatorio)
        arquivo = validacao.salvar_pedido_correcao(pedido)
        comando = validacao.comando_para_abrir_claude(validacao.prompt_curto(arquivo))
        self._val_ultimo_comando_claude = comando   # para o teste automatico conferir
        if sistema.abrir_com_comando(comando, PASTA_PROJETO):
            return
        sistema.copiar(pedido)
        messagebox.showinfo(self.nome, "Não encontrei o Claude Code instalado (comando \"claude\"). "
                                       "Copiei o pedido para a área de transferência: abra um terminal na "
                                       "pasta do projeto, rode \"claude\" e cole (Ctrl+V).")

    def _val_comecar(self):
        from . import validacao
        itens = validacao.escolher(validacao.ler_roteiro(), self.var_val_escolha.get())
        continuo = bool(self.var_val_continuo.get())
        if continuo:
            itens = validacao.para_continuo(itens, bool(self.var_val_manuais.get()))
        if not itens:
            self.rot_val_resultado.configure(text="Não achei frases no ROTEIRO_VALIDACAO.md para essa escolha.",
                                             text_color=tema.AVISO)
            return
        self._val = validacao.Sessao(itens, self.var_val_escolha.get())
        self._val.continuo = continuo
        validacao.ligar_audio(True)   # o ouvido guarda o audio de cada frase (para o relatorio)
        self.rot_val_resultado.configure(text="")
        self.bt_val_relatorio.pack_forget()
        self._val_nova_frase()
        self._val_vigiar()

    def _val_nova_frase(self):
        self._val_captura, self._val_sugestao, self._val_errado_desde = None, None, 0.0
        self._val_cancelar_avanco()
        self._val_estado, self._val_descartes = "", []
        self.fr_val_certo.pack_forget()
        self.ent_val_certo.delete(0, "end")
        if self._val and self._val.acabou:
            self._val_parar()
            return
        self._val_desenhar()

    def _val_desenhar(self):
        from . import validacao
        s = self._val
        ativo = s is not None and s.atual is not None
        for b in self._val_botoes:
            b.configure(state="normal" if ativo else "disabled")
        self.bt_val_comecar.configure(text="↺  Recomeçar" if ativo else "▶  Começar")
        if not ativo:
            self.rot_val_progresso.configure(text="Escolha quais frases e clique em Começar.")
            self.rot_val_frase.configure(text="")
            self.rot_val_esperado.configure(text="")
            self.rot_val_sugestao.configure(text="")
            for rot in self.rot_val_linhas.values():
                rot.configure(text="-")
            return
        item = s.atual
        self.rot_val_progresso.configure(
            text=f"Frase {s.indice + 1} de {len(s.itens)} · {validacao.NOMES_SECAO.get(item.secao, '')} › {item.grupo}")
        continuo = getattr(s, "continuo", False)
        self.rot_val_frase.configure(font=tema.fonte(26 if continuo else 18, True))
        if item.manual:
            self.rot_val_frase.configure(text=f"Faça: {item.para_falar(self.palavra)}")
        else:
            self.rot_val_frase.configure(text=f"Fale: “{item.para_falar(self.palavra)}”")
        comando = ", ".join(item.comandos) or item.esperado
        self.rot_val_esperado.configure(text=f"O que deve acontecer: {item.o_que}   ·   esperado: {comando}")
        c = self._val_captura or {}
        entendi = c.get("entendi") or ""
        if c.get("rota"):
            entendi = f"{entendi}   →   {c['rota']}" if entendi else c["rota"]
        for chave, texto in (("ouvi", c.get("ouvi")), ("entendi", entendi), ("fiz", c.get("fiz"))):
            self.rot_val_linhas[chave].configure(text=texto or "-")
        sug = self._val_sugestao
        marca = {"ok": "Sugestão: ✅  ", "falha": "Sugestão: ❌  "}.get(sug, "")
        cor = {"ok": tema.SUCESSO, "falha": tema.AVISO}.get(sug, tema.TEXTO_FRACO)
        self.rot_val_sugestao.configure(text=marca + validacao.explicar(item, self._val_captura, sug), text_color=cor)
        if continuo:
            self._val_desenhar_continuo(item, entendi)
        else:
            self.fr_val_destaque.pack_forget()

    def _val_desenhar_continuo(self, item, entendi: str):
        """Modo continuo: a situacao em uma frase e, no ❌, OUVI → ENTENDI → FIZ em destaque."""
        from . import validacao
        estado, c = self._val_estado, self._val_captura or {}
        esperado = ", ".join(item.comandos) or item.esperado or "?"
        falando = ("🎙  Pode falar. Quando der certo passa sozinho para a próxima.", tema.TEXTO_FRACO)
        textos = {
            "ok": ("✅  Deu certo! Indo para a próxima...", tema.SUCESSO),
            "falha": (f"❌  Não bateu (esperado {esperado}, atendeu {c.get('rota') or 'nada'}). "
                      "Veja abaixo o que ele entendeu: ❌ Deu errado para anotar, Repetir ou Pular.", tema.AVISO),
            "conferir": ("Não dá para conferir sozinho: marque ✅ Deu certo ou ❌ Deu errado.", tema.AVISO),
            "silencio": ("🔇  Não ouvi nada — fale de novo ou Pular.", tema.AVISO),
        }
        texto, cor = textos.get(estado, falando)
        self.rot_val_sugestao.configure(text=texto, text_color=cor)
        mostrar = estado in ("falha", "conferir") or (estado == "silencio" and self._val_descartes)
        if not mostrar:
            self.fr_val_destaque.pack_forget()
            return
        valores = {"ouvi": f"“{c['ouvi']}”" if c.get("ouvi") else "(nada chegou ao comando)",
                   "entendi": entendi or "(nada)", "fiz": c.get("fiz") or "(nada)",
                   "descartes": validacao.texto_descartes(self._val_descartes)}
        for chave, (linha, rotulo) in self.rot_val_destaque.items():
            rotulo.configure(text=valores[chave] or "-")
            if chave == "descartes" and not valores[chave]:
                linha.pack_forget()
            elif not linha.winfo_manager():
                linha.pack(fill="x", padx=14, pady=3)
        self.fr_val_destaque.pack(fill="x", padx=(32, 18), pady=6, after=self.rot_val_sugestao)

    def _val_cancelar_avanco(self):
        if self._val_avanco is not None:
            try:
                self.after_cancel(self._val_avanco)
            except Exception:
                pass
            self._val_avanco = None

    def _val_avancar(self, indice: int):
        """Chamado AVANCO_SEGUNDOS depois do ✅ no modo continuo."""
        self._val_avanco = None
        if self._val is not None and self._val.indice == indice and self._val_estado == "ok":
            self._val_marcar("ok")

    def _val_vigiar_continuo(self, s, item):
        from . import validacao
        if self._val_estado in ("ok", "falha", "conferir"):
            return   # ja decidiu: esperando o avanco ou o clique
        r = validacao.avaliar_continuo(item, s.exibida_em)
        mudou = (r["estado"], r["captura"], r["descartes"]) != (self._val_estado, self._val_captura,
                                                                 self._val_descartes)
        self._val_estado, self._val_captura, self._val_descartes = r["estado"], r["captura"], r["descartes"]
        self._val_sugestao = r["sugestao"] or validacao.conferir(item, r["captura"])
        if r["estado"] == "ok":
            indice = s.indice
            self._val_avanco = self.after(int(validacao.AVANCO_SEGUNDOS * 1000), lambda: self._val_avancar(indice))
        if mudou:
            self._val_desenhar()

    def _val_vigiar(self):
        """Uma vez por segundo: o que o assistente registrou desde que a frase apareceu."""
        from . import validacao
        s = self._val
        if s is None or s.atual is None:
            return
        try:
            item = s.atual
            if self._val_errado_desde:   # esperando o "o certo era..." falado
                fala = validacao.fala_nova(self._val_errado_desde)
                if fala and not self.ent_val_certo.get().strip():
                    self.ent_val_certo.insert(0, fala)
            elif getattr(s, "continuo", False):
                self._val_vigiar_continuo(s, item)
            elif not item.manual:
                captura = validacao.capturar(s.exibida_em)
                if captura != self._val_captura:
                    self._val_captura = captura
                    self._val_sugestao = validacao.conferir(item, captura)
                    self._val_desenhar()
        except Exception as erro:   # (arquivo sendo escrito pelo outro processo etc.: tenta de novo)
            self.rot_val_resultado.configure(text=f"Não consegui ler o histórico agora: {erro}", text_color=tema.AVISO)
        self.after(500 if getattr(s, "continuo", False) else 1000, self._val_vigiar)

    def _val_marcar(self, veredito: str, certo_era: str = ""):
        if not self._val or self._val.atual is None:
            return
        captura = self._val_captura
        if self._val_descartes and veredito == "falha":   # o relatorio leva o motivo do descarte
            from . import validacao
            texto = validacao.texto_descartes(self._val_descartes).replace("\n", " · ")
            captura = dict(captura or {}, descartado=texto)
        self._val.marcar(veredito, captura, self._val_sugestao, certo_era)
        self._val_nova_frase()

    def _val_errado(self):
        self._val_errado_desde = time.time()
        self.fr_val_certo.pack(fill="x", padx=(32, 18), pady=4, after=self.rot_val_sugestao)
        self.ent_val_certo.focus_set()

    def _val_confirmar_erro(self):
        self._val_marcar("falha", self.ent_val_certo.get())

    def _val_repetir(self):
        if self._val:
            self._val.mostrar()
            self._val_nova_frase()

    def _val_anterior(self):
        if self._val and self._val.indice > 0:
            self._val.mostrar(self._val.indice - 1)
            self._val_nova_frase()

    def _val_parar(self):
        """Fecha a validacao: relatorio + FEEDBACK no MELHORIAS.md (tambem na caixa da pagina Melhorias)."""
        from . import validacao
        s, self._val = self._val, None
        validacao.ligar_audio(False)
        self._val_cancelar_avanco()
        self._val_estado, self._val_descartes = "", []
        self.fr_val_destaque.pack_forget()
        self.fr_val_certo.pack_forget()
        self._val_desenhar()
        if s is None or not s.resultados:
            self.rot_val_resultado.configure(text="Validação parada (nenhuma frase conferida).",
                                             text_color=tema.TEXTO_FRACO)
            return
        try:
            self._val_relatorio = validacao.gerar_relatorio(s, self.nome)
            self._val_relatorio_feedbacks(s)
        except Exception as erro:
            self.rot_val_resultado.configure(text=f"Não consegui gerar o relatório: {erro}", text_color=tema.AVISO)
            return
        lista = s.lista()
        oks = sum(1 for _, r in lista if r["veredito"] == "ok")
        falhas = sum(1 for _, r in lista if r["veredito"] == "falha")
        extra = f" {falhas} FEEDBACK(s) entraram na lista de melhorias." if falhas else ""
        self.rot_val_resultado.configure(
            text=f"✓ {oks} ok · {falhas} falhas. Relatório: exportacoes/{self._val_relatorio.name}.{extra}",
            text_color=tema.SUCESSO if not falhas else tema.AVISO)
        self.bt_val_relatorio.pack(side="left", padx=(0, 8))
        self._val_atualizar_botao_claude()

    def _val_relatorio_feedbacks(self, s) -> list[str]:
        from . import validacao
        from .comandos import ARQUIVO_MELHORIAS
        linhas = validacao.salvar_feedbacks(s, ARQUIVO_MELHORIAS)
        caixa = getattr(self, "txt_melhorias", None)
        if linhas and caixa is not None:   # o "Salvar" grava a caixa por cima do arquivo: ela precisa ter as linhas
            atual = caixa.get("1.0", "end").rstrip()
            caixa.delete("1.0", "end")
            caixa.insert("1.0", atual + "\n" + "\n".join(linhas) + "\n")
        return linhas

    def _val_abrir_relatorio(self):
        from . import validacao
        arquivo = validacao.ultimo_relatorio()
        if arquivo:
            sistema.abrir_arquivo(arquivo)

    # -----------------------------------------------------------------
    #  Sugestoes de melhoria (app/sugestoes.py: 1x por dia, so gera a lista)
    # -----------------------------------------------------------------
    SUG_POR_PAGINA = 8

    def _aba_sugestoes(self, pagina):
        from . import sugestoes
        self._sug_dados = sugestoes.ler()
        self._sug_marcadas: set[str] = set()
        self._sug_pagina = 0
        self._sug_ultimo_comando_claude = None   # para o teste automatico conferir
        self._sug_ultimo_pedido = ""
        cfg_sug = self._sec("sugestoes")
        f = secao(pagina, "Análise diária",
                  f"Todo dia, no horário escolhido, o {self.nome} olha o que aconteceu desde a última análise: "
                  "frases jogadas fora pelo ouvido (e o motivo), frases com cara de comando que caíram na IA, "
                  "\"não entendi\", pedidos repetidos logo em seguida e jeitos novos de falar que funcionaram. "
                  "Ele NÃO muda nada sozinho: só monta a lista abaixo. Se o computador estava desligado no "
                  "horário, a análise roda quando ele ligar.")
        self.var_sug_ligado = tk.BooleanVar(value=bool(cfg_sug.get("ligado", True)))
        linha_campo(f, "Analisar todo dia", lambda m: ctk.CTkCheckBox(m, text="ligado", variable=self.var_sug_ligado))
        self.ent_sug_hora = linha_campo(f, "Horário (HH:MM)", lambda m: ctk.CTkEntry(m, width=90))
        self.ent_sug_hora.insert(0, sugestoes.hora_texto(cfg_sug.get("hora", sugestoes.HORA_PADRAO)))
        f = secao(pagina, "Sugestões", "Marque as que valem a pena e mande para o Claude Code: ele recebe as "
                                      "sugestões com as frases, os horários e os motivos, e você acompanha no terminal.")
        topo = ctk.CTkFrame(f, fg_color="transparent")
        topo.pack(fill="x", padx=(32, 18), pady=4)
        ctk.CTkButton(topo, text="🔍  Analisar agora", width=150, command=self._sug_analisar).pack(side="left")
        self.rot_sug_info = ctk.CTkLabel(topo, text="", anchor="w", text_color=tema.TEXTO_FRACO)
        self.rot_sug_info.pack(side="left", padx=12, fill="x", expand=True)
        self.rot_sug_resumo = ctk.CTkLabel(f, text="", anchor="w", justify="left", wraplength=800)
        self.rot_sug_resumo.pack(fill="x", padx=(32, 18), pady=(2, 4))
        # um numero FIXO de linhas (a lista pode crescer: nada de um widget por sugestao)
        self._sug_linhas = []
        for _ in range(self.SUG_POR_PAGINA):
            linha = ctk.CTkFrame(f, fg_color=tema.CAMPO, corner_radius=10)
            var = tk.BooleanVar(value=False)
            caixa = ctk.CTkCheckBox(linha, text="", width=28, variable=var)
            caixa.pack(side="left", anchor="n", padx=(10, 4), pady=10)
            textos = ctk.CTkFrame(linha, fg_color="transparent")
            textos.pack(side="left", fill="x", expand=True, padx=(0, 10), pady=6)
            titulo_sug = ctk.CTkLabel(textos, text="", anchor="w", justify="left", wraplength=720,
                                      font=tema.fonte(14, True))
            titulo_sug.pack(fill="x")
            detalhe = ctk.CTkLabel(textos, text="", anchor="w", justify="left", wraplength=720,
                                   text_color=tema.TEXTO_FRACO, font=tema.fonte(12))
            detalhe.pack(fill="x")
            aplicar = ctk.CTkButton(linha, text="✓ Aplicar", width=100, **SECUNDARIO)
            self._sug_linhas.append({"frame": linha, "var": var, "caixa": caixa, "titulo": titulo_sug,
                                     "detalhe": detalhe, "aplicar": aplicar, "id": None})
        self.rot_sug_vazia = ctk.CTkLabel(f, text="", anchor="w", text_color=tema.TEXTO_FRACO)
        nav = ctk.CTkFrame(f, fg_color="transparent")
        nav.pack(fill="x", padx=(32, 18), pady=4)
        self._sug_nav = nav
        self.bt_sug_antes = ctk.CTkButton(nav, text="◀", width=40, **SECUNDARIO, command=lambda: self._sug_ir(-1))
        self.bt_sug_antes.pack(side="left")
        self.rot_sug_pagina = ctk.CTkLabel(nav, text="", width=140)
        self.rot_sug_pagina.pack(side="left", padx=6)
        self.bt_sug_depois = ctk.CTkButton(nav, text="▶", width=40, **SECUNDARIO, command=lambda: self._sug_ir(1))
        self.bt_sug_depois.pack(side="left")
        ctk.CTkButton(nav, text="Marcar todas", width=120, **SECUNDARIO,
                      command=lambda: self._sug_marcar_todas(True)).pack(side="left", padx=(16, 4))
        ctk.CTkButton(nav, text="Desmarcar", width=100, **SECUNDARIO,
                      command=lambda: self._sug_marcar_todas(False)).pack(side="left", padx=4)
        fim = ctk.CTkFrame(f, fg_color="transparent")
        fim.pack(fill="x", padx=(32, 18), pady=(4, 8))
        self.bt_sug_claude = ctk.CTkButton(fim, text="🛠  Mandar marcadas para o Claude", width=260,
                                           command=self._sug_mandar_claude)
        self.bt_sug_claude.pack(side="left")
        self.bt_sug_aplicar_marcadas = ctk.CTkButton(fim, text="✓ Aplicar marcadas", width=170, **SECUNDARIO,
                                                     command=self._sug_aplicar_marcadas)
        self.bt_sug_aplicar_marcadas.pack(side="left", padx=(8, 0))
        self.bt_sug_desfazer = ctk.CTkButton(fim, text="↩ Desfazer última aplicação", width=200, **SECUNDARIO,
                                             command=self._sug_desfazer)
        self.bt_sug_desfazer.pack(side="left", padx=(8, 0))
        self.rot_sug_status = ctk.CTkLabel(f, text="", anchor="w", justify="left", wraplength=800,
                                           text_color=tema.TEXTO_FRACO)
        self.rot_sug_status.pack(fill="x", padx=(32, 18), pady=(0, 8))
        self._sug_desenhar()

    def _sug_lista(self) -> list[dict]:
        return [s for s in (self._sug_dados or {}).get("sugestoes") or [] if not s.get("aplicada")]

    def _sug_recarregar(self):
        """Ao abrir a página: pega a análise mais nova (o Assessor pode ter rodado a das 8h)."""
        from . import sugestoes
        novos = sugestoes.ler()
        if novos.get("ts") != (self._sug_dados or {}).get("ts"):
            self._sug_dados, self._sug_marcadas, self._sug_pagina = novos, set(), 0
        self._sug_desenhar()

    def _sug_desenhar(self):
        lista = self._sug_lista()
        dados = self._sug_dados or {}
        if dados.get("gerado_em"):
            quem = "automática" if dados.get("automatica") else "feita por você"
            self.rot_sug_info.configure(text=f"Última análise: {dados['gerado_em']} ({quem}), olhando desde "
                                             f"{dados.get('desde_texto', '?')} · {len(lista)} sugestão(ões)")
        else:
            self.rot_sug_info.configure(text="Ainda não teve análise. Clique em Analisar agora.")
        resumo = str(dados.get("resumo_ia") or "").strip()
        self.rot_sug_resumo.configure(text=f"Resumo da IA: {resumo}" if resumo else "")
        paginas = max(1, -(-len(lista) // self.SUG_POR_PAGINA))
        self._sug_pagina = max(0, min(self._sug_pagina, paginas - 1))
        inicio = self._sug_pagina * self.SUG_POR_PAGINA
        for i, linha in enumerate(self._sug_linhas):
            linha["frame"].pack_forget()
        for i, linha in enumerate(self._sug_linhas):
            if inicio + i >= len(lista):
                linha["id"] = None
                continue
            sug = lista[inicio + i]
            linha["id"] = sug.get("id")
            linha["var"].set(sug.get("id") in self._sug_marcadas)
            linha["caixa"].configure(command=lambda l=linha: self._sug_alternar(l))
            evid = sug.get("evidencias") or []
            exemplos = [f"{e.get('data')} “{e.get('frase')}” ({e.get('info')})" for e in evid[-3:]]
            mais = f"\n… e mais {len(evid) - 3}" if len(evid) > 3 else ""
            linha["titulo"].configure(text=str(sug.get("titulo") or ""))
            linha["detalhe"].configure(text=str(sug.get("detalhe") or "") + ("\n• " + "\n• ".join(exemplos)
                                                                           if exemplos else "") + mais)
            if sug.get("tipo") == "palavra":
                linha["aplicar"].configure(command=lambda s=sug: self._sug_aplicar(s))
                linha["aplicar"].pack(side="right", anchor="n", padx=(0, 10), pady=10)
            else:
                linha["aplicar"].pack_forget()
            linha["frame"].pack(fill="x", padx=(32, 18), pady=3, before=self._sug_nav)
        if lista:
            self.rot_sug_vazia.pack_forget()
        else:
            self.rot_sug_vazia.configure(text="Nenhuma sugestão por enquanto." if dados.get("gerado_em") else "")
            self.rot_sug_vazia.pack(fill="x", padx=(32, 18), pady=4, before=self._sug_nav)
        self.rot_sug_pagina.configure(text=f"Página {self._sug_pagina + 1} de {paginas}")
        self.bt_sug_antes.configure(state="normal" if self._sug_pagina > 0 else "disabled")
        self.bt_sug_depois.configure(state="normal" if self._sug_pagina < paginas - 1 else "disabled")
        n = len(self._sug_marcadas)
        self.bt_sug_claude.configure(state="normal" if n else "disabled",
                                     text=f"🛠  Mandar marcadas para o Claude ({n})" if n
                                     else "🛠  Mandar marcadas para o Claude")
        from . import sugestoes
        self.bt_sug_desfazer.configure(state="normal" if sugestoes.ultima_aplicacao() else "disabled")

    def _sug_alternar(self, linha):
        if not linha["id"]:
            return
        if linha["var"].get():
            self._sug_marcadas.add(linha["id"])
        else:
            self._sug_marcadas.discard(linha["id"])
        self._sug_desenhar()

    def _sug_marcar_todas(self, sim: bool):
        self._sug_marcadas = {s.get("id") for s in self._sug_lista()} if sim else set()
        self._sug_desenhar()

    def _sug_ir(self, passo: int):
        self._sug_pagina += passo
        self._sug_desenhar()

    def _sug_analisar(self):
        from . import sugestoes
        try:
            self._sug_dados = sugestoes.rodar(self.cfg)
        except Exception as erro:
            self.rot_sug_status.configure(text=f"Não consegui analisar: {erro}", text_color=tema.AVISO)
            return
        self._sug_marcadas, self._sug_pagina = set(), 0
        self.rot_sug_status.configure(text=f"✓ Análise pronta: {len(self._sug_lista())} sugestão(ões).",
                                      text_color=tema.SUCESSO)
        self._sug_desenhar()

    def _sug_mandar_claude(self):
        """Mesmo fluxo supervisionado da validação: salva o pedido e abre o Claude Code interativo."""
        from . import sugestoes, validacao
        marcadas = [s for s in self._sug_lista() if s.get("id") in self._sug_marcadas]
        if not marcadas:
            self.rot_sug_status.configure(text="Marque pelo menos uma sugestão.", text_color=tema.AVISO)
            return
        pedido = sugestoes.pedido_para_claude(marcadas, (self._sug_dados or {}).get("gerado_em", ""), self.nome)
        arquivo = validacao.salvar_pedido_correcao(pedido, prefixo="pedido_sugestoes")
        comando = validacao.comando_para_abrir_claude(validacao.prompt_curto(arquivo))
        self._sug_ultimo_pedido, self._sug_ultimo_comando_claude = pedido, comando
        if sistema.abrir_com_comando(comando, PASTA_PROJETO):
            self.rot_sug_status.configure(text=f"✓ Mandei {len(marcadas)} sugestão(ões) para o Claude "
                                               f"(pedido em exportacoes/{arquivo.name}).", text_color=tema.SUCESSO)
            return
        sistema.copiar(pedido)
        messagebox.showinfo(self.nome, "Não encontrei o Claude Code instalado (comando \"claude\"). "
                                       "Copiei o pedido para a área de transferência: abra um terminal na "
                                       "pasta do projeto, rode \"claude\" e cole (Ctrl+V).")

    # -----------------------------------------------------------------
    #  Aplicar (so tipo "palavra": Whisper ouviu a palavra de ativação errado). Grava sem IA,
    #  direto no vocabulário (aprendido.yaml) E nas variações aceitas da palavra de ativação
    #  (config.yaml, o mesmo que app/ouvido.py usa pra "acordar"), com confirmação antes.
    # -----------------------------------------------------------------
    def _sug_confirmar_e_aplicar(self, sug: dict) -> bool:
        from . import sugestoes, configuracao
        from .config import palavras_ativacao
        troca = sugestoes.troca_da_sugestao(sug, self.palavra)
        if not troca:
            return False
        jeito, oficial = troca
        pode, motivo = self.vocab.pode_aplicar_sinonimo(jeito, oficial, palavras_ativacao(self.cfg))
        if not pode:
            messagebox.showwarning(self.nome, f"Não posso aplicar: {motivo}")
            return False
        if not messagebox.askyesno(self.nome, f"Vai trocar “{jeito}” por “{oficial}” no vocabulário e o "
                                              f"{self.nome} passa a ACORDAR também quando ouvir “{jeito}” "
                                              f"(gravado em aprendido.yaml e no config.yaml). Confirma?"):
            return False
        aplicou, msg = self.vocab.aplicar_sinonimo(jeito, oficial, palavras_ativacao(self.cfg))
        if not aplicou:
            messagebox.showwarning(self.nome, f"Não posso aplicar: {msg}")
            return False
        entrou_config = configuracao.adicionar_variacao_aceita(jeito)
        sugestoes.marcar_aplicada(sug.get("id"), jeito, oficial, no_config=entrou_config)
        for s in (self._sug_dados or {}).get("sugestoes") or []:
            if s.get("id") == sug.get("id"):
                s["aplicada"] = True
        self._sug_marcadas.discard(sug.get("id"))
        return True

    def _sug_aplicar(self, sug: dict):
        if self._sug_confirmar_e_aplicar(sug):
            self.rot_sug_status.configure(text=f"✓ Aplicada: {sug.get('titulo')}", text_color=tema.SUCESSO)
        self._sug_desenhar()

    def _sug_aplicar_marcadas(self):
        from . import sugestoes
        marcadas = [s for s in self._sug_lista() if s.get("id") in self._sug_marcadas]
        aplicaveis = [s for s in marcadas if s.get("tipo") == "palavra"]
        if not aplicaveis:
            self.rot_sug_status.configure(
                text="Nenhuma marcada é do tipo vocabulário (só essas têm “Aplicar”; as outras vão para o Claude).",
                text_color=tema.AVISO)
            return
        aplicadas = sum(1 for s in aplicaveis if self._sug_confirmar_e_aplicar(s))
        if aplicadas:
            self.rot_sug_status.configure(text=f"✓ {aplicadas} de {len(aplicaveis)} aplicada(s).",
                                          text_color=tema.SUCESSO)
        self._sug_desenhar()

    def _sug_desfazer(self):
        from . import sugestoes, configuracao
        ultima = sugestoes.desfazer_ultima_aplicacao()
        if not ultima:
            self.rot_sug_status.configure(text="Nenhuma aplicação para desfazer.", text_color=tema.AVISO)
            return
        self.vocab.desfazer_sinonimo(ultima.get("jeito", ""), ultima.get("oficial", ""))
        if ultima.get("no_config"):
            configuracao.remover_variacao_aceita(ultima.get("jeito", ""))
        for s in (self._sug_dados or {}).get("sugestoes") or []:
            if s.get("id") == ultima.get("id"):
                s.pop("aplicada", None)
        self.rot_sug_status.configure(
            text=f"↩ Desfeito: “{ultima.get('jeito')}” não vira mais “{ultima.get('oficial')}” "
                 f"(e não acorda mais com essa pronúncia).",
            text_color=tema.SUCESSO)
        self._sug_desenhar()

    # =================================================================
    #  Salvar
    # =================================================================
    # -----------------------------------------------------------------
    #  Salvar: cada pagina grava so o que e dela (e so se ja foi aberta; as outras ficam como estao)
    # -----------------------------------------------------------------
    SALVAR_PAGINA = {
        "Início": "_salvar_inicio", "Personalidade": "_salvar_personalidade", "Voz": "_salvar_voz",
        "Áudio": "_salvar_audio", "Conversa": "_salvar_conversa", "IPM e projetos": "_salvar_ipm",
        "YouTube": "_salvar_youtube", "Programas e sites": "_salvar_programas", "Spotify": "_salvar_spotify",
        "Celular": "_salvar_celular", "Histórico": "_salvar_historico", "Aparência": "_salvar_aparencia",
        "Sugestões de melhoria": "_salvar_sugestoes",
    }

    def salvar(self, reiniciar: bool = False):
        try:
            self.vocab.recarregar()   # (o Assessor pode ter aprendido algo por voz com o painel aberto)
            c = self.cfg
            for nome in PAGINAS:
                if nome in self._montadas and nome in self.SALVAR_PAGINA:
                    getattr(self, self.SALVAR_PAGINA[nome])(c)
            self._salvar_rotinas(c)
            configuracao.salvar(c)
            if "Atalhos" in self._montadas:
                self._salvar_atalhos()
            if "Melhorias" in self._montadas:
                self._salvar_melhorias()
        except Exception as erro:
            messagebox.showerror(self.nome, f"Não consegui salvar:\n{erro}")
            return False
        self.aviso.configure(text=f"Salvo às {time.strftime('%H:%M:%S')}.", text_color=tema.SUCESSO)
        if reiniciar:
            self._reiniciar_mestre()
            self.aviso.configure(text=f"Salvo! O {self.nome} está reiniciando com as novidades.")
        return True

    def _salvar_inicio(self, c):
        configuracao.secao(c, "central")["ligar_mestre_ao_abrir"] = bool(self.var_ligar_ao_abrir.get())

    def _salvar_audio(self, c):
        o = configuracao.secao(c, "ouvido")
        o["microfone"] = self._mic_escolhido()
        o["modo_ativacao"] = "vosk" if self.var_modo.get().startswith("Leve") else "whisper"
        o["detector_palavra"] = bool(self.var_detector.get())
        o["detector_limiar"] = round(float(self.var_detector_limiar.get()), 2)
        o["modelo_whisper"] = configuracao.aspas(next(k for k, v in MODELOS_WHISPER.items() if v == self.var_modelo.get()))
        o["precisao"] = self.var_precisao.get()
        o["limiar_volume"] = 0 if self.var_auto.get() else int(self.var_limiar.get())
        o["ganho"] = round(self.var_ganho.get(), 1)
        o["silencio_fim"] = round(self.var_silencio.get(), 1)
        o["espera_apos_palavra"] = round(float(self.var_espera_palavra.get()), 1)
        o["espera_continuacao"] = round(float(self.var_espera_cont.get()), 2)
        o["gravar_diagnostico"] = bool(self.var_diag.get())
        o["so_minha_voz"] = bool(self.var_so_minha_voz.get())
        o["exigencia_voz"] = round(float(self.var_exig_voz.get()), 2)
        o["max_frase"] = int(self.var_max.get())
        o["ditado_silencio_max"] = int(self.var_espera_ditado.get())
        configuracao.secao(c, "ditado")["revisar_na_janela"] = bool(self.var_revisar.get())
        o["palavras_conhecidas"] = configuracao.lista_em_linha(
            [x.strip() for x in self.ent_palavras.get().split(",") if x.strip()])
        o["dispositivo"] = configuracao.aspas(self._dispositivo())
        v = configuracao.secao(c, "voz")   # (estas chaves da voz ficam na pagina Audio)
        v["fala_em_segundo_plano"] = bool(self.var_fala_fundo.get())
        v["interromper_com_palavra"] = bool(self.var_interromper.get())
        v["frase_a_frase"] = bool(self.var_frase_a_frase.get())
        saidas = dict(configuracao.secao(c, "som").get("saidas") or {})   # preserva quem nao esta na tela agora
        for nome, apelido_ao_abrir, ent in getattr(self, "_saida_som_linhas", []):
            novo = ent.get().strip().lower()
            if apelido_ao_abrir and apelido_ao_abrir != novo:
                saidas.pop(apelido_ao_abrir, None)
            if novo:
                saidas[novo] = configuracao.aspas(nome)
        if saidas:
            configuracao.secao(c, "som")["saidas"] = configuracao.aspas(saidas)

    def _salvar_voz(self, c):
        v = configuracao.secao(c, "voz")
        v["motor"] = configuracao.aspas(self._motor_escolhido())
        v["reserva"] = configuracao.aspas(self.var_reserva.get())
        v["fluida"] = bool(self.var_fluida.get())
        v["voz_edge"] = configuracao.aspas(str(self.var_voz.get()))
        v["voz_kokoro"] = configuracao.aspas(self._voz_kokoro_escolhida())
        v["voz_azure"] = configuracao.aspas(str(self.var_voz_azure.get()).strip() or "pt-BR-AntonioNeural")
        v["voz_natural"] = configuracao.aspas(self._voz_natural_escolhida())
        v["voz_elevenlabs"] = configuracao.aspas(self._voz_eleven_escolhida())
        v["modelo_elevenlabs"] = configuracao.aspas(self._modelo_eleven_escolhido())
        if self.ent_eleven_chave.get().strip():
            segredos.salvar(elevenlabs_chave=self.ent_eleven_chave.get())
        if self.ent_azure_chave.get().strip():
            segredos.salvar(azure_chave=self.ent_azure_chave.get(), azure_regiao=self.ent_azure_regiao.get() or "brazilsouth")
        v["velocidade"] = configuracao.aspas(f"{self.var_vel.get():+d}%")
        v["tom"] = configuracao.aspas(f"{self.var_tom.get():+d}Hz")
        for campo, valor in (("voz", v["voz_edge"]), ("velocidade", v["velocidade"]), ("tom", v["tom"])):  # noqa
            self.vocab.salvar_preferencia(campo, str(valor))   # a voz escolhida por voz tambem muda

    def _salvar_conversa(self, c):
        configuracao.secao(c, "conversa")["janela_segundos"] = int(self.var_janela.get())
        cb = configuracao.secao(c, "cerebro")
        cb["segundo_plano_seg"] = int(self.var_fundo.get())
        cb["tempo_maximo"] = int(self.var_maximo.get())
        cb["aviso_som"] = configuracao.aspas(next((k for k, v in self.SONS_AVISO.items() if v == self.var_bipe.get()), "nenhum"))
        cb["aviso_ao_terminar"] = configuracao.aspas(
            next(k for k, v in self.AVISOS.items() if v == self.var_aviso.get()))
        cb["ollama_modelo"] = configuracao.aspas(self.var_modelo_ia.get().strip() or "qwen2.5:7b")
        cb["memoria_contexto_kb"] = int(self.var_contexto_kb.get())
        ids_ordem = []
        for var in (self.var_ordem1, self.var_ordem2, self.var_ordem3):
            id_ = next((k for k, v in self.ROTULOS_IA.items() if v == var.get()), None)
            if id_ and id_ not in ids_ordem:
                ids_ordem.append(id_)
        cb["ordem_ia"] = configuracao.lista_em_linha(ids_ordem)
        cb["ollama_modelo_menor"] = configuracao.aspas(self.var_modelo_menor.get().strip())
        cb["timeout_tentativa_seg"] = int(self.var_timeout_tentativa.get())
        cb["penalidade_min"] = int(self.var_penalidade.get())
        if self.ent_claude_chave.get().strip():
            segredos.salvar(claude_chave=self.ent_claude_chave.get().strip())
        for id_, campos in self._nuvem_ia.items():
            cb[f"{id_}_ligado"] = bool(campos["ligado"].get())
            cb[f"{id_}_modelo"] = configuracao.aspas(campos["modelo"].get().strip())
            if campos["chave"].get().strip():
                segredos.salvar(**{f"{id_}_chave": campos["chave"].get().strip()})
        cb["gemini_textos_longos_chars"] = int(self.var_gemini_longos.get())
        configuracao.secao(c, "assistente")["cidade"] = configuracao.aspas(self.ent_cidade.get().strip() or "São Paulo")

    def _salvar_ipm(self, c):
        pm = configuracao.secao(c, "projeto_mestre")
        pm["link"] = configuracao.aspas(self.ent_link_projeto.get().strip())
        pm["segundos_para_carregar"] = int(self.var_seg_projeto.get())
        pm["enviar_automaticamente"] = bool(self.var_enviar_projeto.get())
        pm["modo"] = configuracao.aspas(next(k for k, v in self.MODOS_PROJETO.items() if v == self.var_modo_projeto.get()))
        pm["altura_caixa"] = int(self.var_altura_caixa.get())
        if self._posicao_caixa is not None:
            pm["posicao_caixa"] = configuracao.lista_em_linha(self._posicao_caixa)
        pj = configuracao.secao(c, "projetos")
        pj["pasta"] = configuracao.aspas(self.ent_pasta_projetos.get().strip())
        pj["abrir_pesquisas"] = bool(self.var_pesquisas.get())
        pj["pesquisar_internet"] = bool(self.var_pesquisar_web.get())
        ipm = configuracao.secao(c, "agente_ipm")
        ipm["modo"] = self.var_ipm_modo.get()
        ipm["link_projeto"] = configuracao.aspas(self.ent_link.get().strip())
        ipm["segundos_para_carregar"] = int(self.var_seg.get())
        ipm["enviar_automaticamente"] = bool(self.var_enviar.get())

    def _salvar_spotify(self, c):
        sp = configuracao.secao(c, "spotify")
        sp["apertar_play"] = bool(self.var_play.get())
        sp["tocar_musica_em"] = configuracao.aspas("youtube" if self.var_tocar_em.get() == "YouTube" else "spotify")
        configuracao.trocar_mapa(sp, "playlists", self.tab_playlists.valores())

    def _salvar_celular(self, c):
        rc = configuracao.secao(c, "recebidos")
        rc["pasta"] = configuracao.aspas(self.ent_pasta_audios.get().strip())
        rc["pasta_ligada"] = bool(self.var_pasta_audios.get())
        rc["telegram_ligado"] = bool(self.var_telegram.get())
        rc["destino"] = configuracao.aspas(next(k for k, v in self.DESTINOS_CELULAR.items() if v == self.var_destino_cel.get()))
        rc["aviso"] = configuracao.aspas(next((k for k, v in self.AVISOS_CELULAR.items() if v == self.var_aviso_cel.get()),
                                              "tela_e_voz"))
        rc["frase_telegram"] = configuracao.aspas(self.ent_frase_telegram.get().strip())
        rc["frase_pasta"] = configuracao.aspas(self.ent_frase_pasta.get().strip())
        ap = configuracao.secao(c, "avisos_pc")
        ap["ligado"] = bool(self.var_avisos_pc.get())
        ap["healthchecks_ligado"] = bool(self.var_healthchecks.get())
        segredos.salvar(healthchecks_url=self.ent_healthchecks.get().strip())

    def _salvar_historico(self, c):
        from . import memoria
        for assunto, caixa in self.txt_fatos_assunto.items():
            novos = [x.strip() for x in caixa.get("1.0", "end").splitlines() if x.strip() and not x.startswith("#")]
            if novos != self._fatos_iniciais_assunto.get(assunto):   # so grava se voce mexeu (o Mestre tambem grava)
                memoria.salvar_fatos_assunto(assunto, novos)
                self._fatos_iniciais_assunto[assunto] = novos

    def _salvar_aparencia(self, c):
        ap = configuracao.secao(c, "aparencia")
        for chave, var in self.vars_aparencia.items():
            ap[chave] = configuracao.aspas(var.get())
        if hasattr(self, "var_indicador"):
            from . import avatar
            tipo = next((k for k, v in avatar.TIPOS.items() if v == self.var_indicador.get()), "avatar")
            configuracao.secao(c, "indicador")["tipo"] = configuracao.aspas(tipo)

    def _salvar_sugestoes(self, c):
        from . import sugestoes
        sg = configuracao.secao(c, "sugestoes")
        sg["ligado"] = bool(self.var_sug_ligado.get())
        sg["hora"] = configuracao.aspas(sugestoes.hora_texto(self.ent_sug_hora.get()))

    def _salvar_personalidade(self, c):
        from .config import gerar_variacoes
        from .texto import normalizar
        assist = configuracao.secao(c, "assistente")
        palavra = (normalizar(self.ent_palavra.get()).split() or ["mestre"])[-1]
        assist["nome"] = configuracao.aspas(self.ent_nome.get().strip() or "Mestre")
        assist["apelido_usuario"] = configuracao.aspas(self.ent_apelido.get().strip() or "chefe")
        assist["palavra_ativacao"] = configuracao.aspas(palavra)
        assist["variacoes_aceitas"] = configuracao.lista_em_linha(gerar_variacoes(palavra))
        p = configuracao.secao(c, "personalidade")
        p["estilo"] = configuracao.aspas(self.var_estilo.get())
        p["descricao"] = configuracao.aspas(self.txt_desc.get("1.0", "end").strip())
        falas = configuracao.secao(p, "falas")
        for chave, caixa in self.txt_falas.items():
            linhas = [x.strip() for x in caixa.get("1.0", "end").splitlines() if x.strip()]
            if linhas:
                falas[chave] = configuracao.lista_em_linha(linhas)

    def _salvar_youtube(self, c):
        ytc = configuracao.secao(c, "youtube")
        ytc["navegador_mestre"] = bool(self.var_yt_nav.get())
        ytc["navegador"] = configuracao.aspas(next(k for k, v in self.NAVEGADORES.items() if v == self.var_yt_canal.get()))
        ytc["modo"] = configuracao.aspas(next(k for k, v in self.MODOS_YT.items() if v == self.var_yt_modo.get()))
        configuracao.trocar_mapa(c, "canais_youtube", self.tab_canais.valores())

    def _salvar_programas(self, c):
        jn = configuracao.secao(c, "janelas")
        jn["sempre_no_principal"] = bool(self.var_principal.get())
        jn["navegador_sites"] = configuracao.aspas("brave" if self.var_sites_brave.get() else "padrao")
        jn["perfil_brave"] = configuracao.aspas(self.ent_perfil_brave.get().strip())
        configuracao.trocar_mapa(jn, "nomes_monitores",
                                 {str(n): e.get().strip() for n, e in self.ent_monitores.items() if e.get().strip()})
        configuracao.trocar_mapa(c, "programas", self.tab_prog.valores())
        configuracao.trocar_mapa(c, "sites", self.tab_sites.valores())

    def _salvar_rotinas(self, c):
        """Sempre (mesmo com a pagina Rotinas fechada): a rotina ensinada por voz com o painel aberto nao se perde."""
        if "Rotinas" in self._montadas:
            self._guardar_editor()
            rotinas = []
            for r in self.rotinas:
                item = configuracao.aspas({"nome": r["nome"], "acoes": r["acoes"]})
                item.insert(1, "frases", configuracao.lista_em_linha(r["frases"]))
                rotinas.append(item)
        else:
            rotinas = list(c.get("rotinas") or [])
        # releia o disco: uma rotina ensinada por voz enquanto o painel estava aberto nao pode
        # se perder quando o painel salva por cima do que tinha em memoria
        rotinas_no_disco = configuracao.carregar().get("rotinas") or []
        c["rotinas"] = configuracao.mesclar_novas_por_nome(rotinas_no_disco, self._rotinas_iniciais, rotinas)

    def _salvar_atalhos(self):
        atalhos_editados = {str(k): str(x) for k, x in self.tab_atalhos.valores().items()}
        # releia o disco: um atalho ensinado por voz enquanto o painel estava aberto nao pode
        # se perder quando o painel salva por cima do que tinha em memoria
        chaves_editadas = {k.strip().lower() for k in atalhos_editados}
        novos = {k: v for k, v in atalhos_no_disco().items()
                 if k.strip().lower() not in self._atalhos_iniciais and k.strip().lower() not in chaves_editadas}
        self.vocab.aprendido["atalhos"] = {**atalhos_editados, **novos}
        self.vocab.salvar_aprendido()

    def _fechar(self):
        self._parar_teste()
        if getattr(self, "_val", None) is not None:   # validacao aberta: o ouvido para de guardar audio
            from . import validacao
            validacao.ligar_audio(False)
            self._val = None   # para o laco _val_vigiar nao mexer em widgets ja destruidos
            self._val_cancelar_avanco()
        servidor = getattr(self, "_servidor", None)
        if servidor:   # libera a porta ja (para um painel novo conseguir abrir logo em seguida)
            try:
                servidor.close()
            except OSError:
                pass
        self.destroy()


def escutar_chamados(janela) -> None:
    """Deixa o painel aberto atender o "me mostra" de um segundo clique no atalho."""
    import socket

    from .iniciar_painel import PORTA_PAINEL

    try:
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.bind(("127.0.0.1", PORTA_PAINEL))
        servidor.listen(2)
    except OSError:
        return  # porta ocupada: sem problema, so abre outro painel
    janela._servidor = servidor

    def atender():
        while True:
            try:
                conexao, _ = servidor.accept()
                conexao.close()
                janela.after(0, janela.trazer_para_frente)
            except Exception:
                return
    threading.Thread(target=atender, daemon=True).start()


PAGINAS = {
    #  nome:              (icone de app/icones.py, descricao, montar)
    "Início":            ("casa", "Ligar, desligar, pausar, testar e atualizar.", Painel._aba_inicio),
    "Personalidade":     ("rosto", "Nome, como ele te chama, palavra de ativação, estilo e frases.", Painel._aba_personalidade),
    "Voz":               ("voz", "Qual voz, velocidade, tom e fala fluida.", Painel._aba_voz),
    "Áudio":             ("mic", "Microfone, calibração, reconhecimento de voz e frases longas.", Painel._aba_audio),
    "Conversa":          ("conversa", "Modo conversa, IA que demora (segundo plano) e sua cidade.", Painel._aba_conversa),
    "IPM e projetos":    ("maleta", "Agente IPM, projeto Mestre (Claude) e projetos guiados.", Painel._aba_ipm),
    "YouTube":           ("youtube", "Canais e importação das suas inscrições.", Painel._aba_youtube),
    "Programas e sites": ("janelas", "O que ele abre quando você pede e em qual monitor.", Painel._aba_programas),
    "Spotify":           ("musica", "Playlists para tocar por voz.", Painel._aba_spotify),
    "Rotinas":           ("rotina", "Uma frase, várias ações em sequência.", Painel._aba_rotinas),
    "Atalhos":           ("atalho", "Frases curtas que você ensinou.", Painel._aba_atalhos),
    "Celular":           ("celular", "Áudios do celular: pasta sincronizada e Telegram.", Painel._aba_celular),
    "Histórico":         ("historico", "Pedidos, respostas e o que ele lembra de você.", Painel._aba_historico),
    "Aparência":         ("paleta", "Cores, fonte e tamanho do texto.", Painel._aba_aparencia),
    "Melhorias":         ("lampada", "Ideias e feedbacks para o Claude Code implementar.", Painel._aba_melhorias),
    "Validar atualização": ("check", "Fale as frases do roteiro e confira o que ele ouviu, entendeu e fez.",
                            Painel._aba_validacao),
    "Sugestões de melhoria": ("brilho", "Todo dia ele olha o que deu errado e sugere melhorias para o Claude.",
                              Painel._aba_sugestoes),
}


GRUPOS_MENU = [
    ("ASSISTENTE", ["Início", "Personalidade", "Conversa"]),
    ("VOZ E OUVIDO", ["Voz", "Áudio"]),
    ("APPS E SITES", ["YouTube", "Spotify", "Programas e sites", "Rotinas", "Atalhos"]),
    ("INTEGRAÇÕES", ["IPM e projetos", "Celular"]),
    ("SISTEMA", ["Histórico", "Melhorias", "Validar atualização", "Sugestões de melhoria", "Aparência"]),
]


def main():
    Painel().mainloop()


if __name__ == "__main__":
    main()
