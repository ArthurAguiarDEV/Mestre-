"""Indicador na tela: uma "pilula" pequena, sempre por cima, mostrando o estado do Mestre.

- Arraste com o botao esquerdo para mudar de lugar (a posicao fica salva).
- Passe o mouse por cima para ver a ultima frase ouvida e a ultima resposta.
- Duplo clique abre o painel de configuracoes.
- Botao direito: menu (painel, pausar escuta, reiniciar, sair).
- Quando a IA pensa em segundo plano, abre uma segunda "pilula" ao lado:
  roxa = pensando, verde = resposta pronta (clique nela ou diga "pode falar").
"""
import sys
import time
import tkinter as tk

from . import estado, tema

FUNDO = "#171a22"
TEXTO = "#eceae4"
TEXTO_FRACO = "#9aa0ad"
TRANSPARENTE = "#010203"   # cor "magica" que o Windows torna invisivel (cantos arredondados)
LARGURA, ALTURA, ALTURA_ABERTA = 320, 40, 104
VAO, LARGURA_PENSAMENTO = 8, 220          # segunda pilula (pensamento em segundo plano)
COR_PENSANDO, COR_PRONTO = "#b388ff", "#3ecf8e"
COR_AVISO = "#29a9eb"   # azul do Telegram: chegou algo do celular

ESTADOS = {
    #  nome:          (cor da bolinha, texto)
    "iniciando":     ("#8a8f99", "Carregando o ouvido..."),
    "ouvindo":       ("#3ecf8e", "Ouvindo · diga “{palavra}”"),
    "gravando":      ("#ff5c5c", "Gravando sua voz..."),
    "transcrevendo": ("#f2a541", "Entendendo..."),
    "trabalhando":   ("#5b9cff", "Fazendo..."),
    "pensando":      ("#b388ff", "Pensando..."),
    "falando":       ("#4fd1c5", "Falando..."),
    "conversa":      ("#3ecf8e", "Pode falar sem “{palavra}”"),
    "pausado":       ("#8a8f99", "Pausado (botão direito)"),
}


class Indicador:
    def __init__(self, raiz: tk.Tk, executor, abrir_painel, reiniciar):
        self.raiz = raiz
        self.executor = executor
        self.abrir_painel = abrir_painel
        self.reiniciar = reiniciar
        self.aberto = False
        self._pulso = 0
        self.nome = getattr(executor, "nome", "Mestre")
        self.palavra = str(getattr(executor, "palavra", "mestre")).capitalize()
        self.borda = tema.misturar("#2a2f3b", tema.ROSA, 0.45)   # contorno na cor de destaque
        self._largura = LARGURA

        raiz.overrideredirect(True)
        raiz.attributes("-topmost", True)
        try:
            raiz.attributes("-alpha", 0.94)
        except tk.TclError:
            pass
        self.cantos_redondos = sys.platform == "win32"
        fundo_janela = TRANSPARENTE if self.cantos_redondos else FUNDO
        raiz.configure(bg=fundo_janela)
        if self.cantos_redondos:
            raiz.attributes("-transparentcolor", TRANSPARENTE)

        x, y = self._posicao_salva()
        x, y = tema.posicao_janela(x, y)
        raiz.geometry(f"{LARGURA}x{ALTURA}+{x}+{y}")
        self.tela = tk.Canvas(raiz, width=LARGURA, height=ALTURA_ABERTA, bg=fundo_janela,
                              highlightthickness=0, bd=0)
        self.tela.pack(fill="both", expand=True)

        self.menu = tk.Menu(raiz, tearoff=0)
        self.menu.add_command(label="Abrir painel de configurações", command=self.abrir_painel)
        self.menu.add_command(label="Pausar / retomar a escuta", command=self._alternar_pausa)
        self.menu.add_separator()
        self.menu.add_command(label="Ouvir a resposta pensada", command=self._clique_pensamento)
        self.menu.add_command(label="Descartar a resposta pensada", command=self._descartar_pensamento)
        self.menu.add_separator()
        self.menu.add_command(label=f"Reiniciar o {self.nome}", command=self.reiniciar)
        self.menu.add_command(label=f"Desligar o {self.nome}", command=self._sair)

        for alvo in (self.tela,):
            alvo.bind("<ButtonPress-1>", self._comeca_arrastar)
            alvo.bind("<ButtonRelease-1>", self._clique_ou_solta, add="+")
            alvo.bind("<B1-Motion>", self._arrastando)
            alvo.bind("<Double-Button-1>", lambda e: self.abrir_painel())
            alvo.bind("<Button-3>", lambda e: self.menu.tk_popup(e.x_root, e.y_root))
            alvo.bind("<Enter>", lambda e: self._abrir(True))
            alvo.bind("<Leave>", lambda e: self._abrir(False))
        self._atualizar()

    # --- posicao ---------------------------------------------------------
    def _posicao_salva(self) -> tuple[int, int]:
        pos = self.executor.vocab.preferencia("indicador_posicao")
        if pos and len(pos) == 2:
            return int(pos[0]), int(pos[1])
        return (self.raiz.winfo_screenwidth() - LARGURA) // 2, 6

    def _comeca_arrastar(self, e):
        self._arraste = (e.x, e.y)
        self._arrastou = False

    def _arrastando(self, e):
        x = self.raiz.winfo_x() + e.x - self._arraste[0]
        y = self.raiz.winfo_y() + e.y - self._arraste[1]
        self.raiz.geometry(f"+{x}+{y}")
        self._arrastou = True

    def _clique_ou_solta(self, e):
        if getattr(self, "_arrastou", False):
            self.executor.vocab.salvar_preferencia("indicador_posicao", [self.raiz.winfo_x(), self.raiz.winfo_y()])
        elif e.x > LARGURA:   # clicou na pilula do pensamento
            self._clique_pensamento()

    def _clique_pensamento(self):
        if estado.ler().get("pensamento"):
            import threading
            threading.Thread(target=self.executor.entregar_pensamento, daemon=True).start()

    def _descartar_pensamento(self):
        if estado.ler().get("pensamento"):
            self.executor.cancelar_pensamento()

    def _abrir(self, sim: bool):
        self.aberto = sim
        self._redimensionar()

    def _redimensionar(self):
        altura = ALTURA_ABERTA if self.aberto else ALTURA
        self.raiz.geometry(f"{self._largura}x{altura}+{self.raiz.winfo_x()}+{self.raiz.winfo_y()}")

    # --- acoes do menu ------------------------------------------------------
    def _alternar_pausa(self):
        estado.pausar(not estado.pausado())
        if not estado.pausado():
            estado.definir("ouvindo")

    def _sair(self):
        self.executor.rodando = False

    # --- desenho --------------------------------------------------------------
    def _retangulo_redondo(self, x1, y1, x2, y2, r, **kw):
        pontos = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
                  x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        return self.tela.create_polygon(pontos, smooth=True, **kw)

    def _atualizar(self):
        if not self.executor.rodando:
            self.raiz.destroy()
            return
        e = estado.ler()
        nome = e["nome"]
        cor, texto = ESTADOS.get(nome, ESTADOS["ouvindo"])
        texto = texto.format(palavra=self.palavra)
        if e.get("aviso") and time.time() < e.get("aviso_ate", 0) and nome != "gravando":
            cor, texto = COR_AVISO, e["aviso"]
        elif e.get("descanso") and nome in ("conversa", "ouvindo", "gravando", "transcrevendo"):
            cor, texto = "#8a8f99", "Descansando · diga “bora voltar”"
        elif e.get("ditado_desde") and nome in ("conversa", "ouvindo", "gravando", "transcrevendo"):
            segundos = int(time.time() - e["ditado_desde"])
            texto = f"Ditando {segundos // 60}:{segundos % 60:02d} · diga “finalizei”"
        elif nome == "conversa":
            restam = max(0, int(e["conversa_ate"] - time.time()))
            texto = (f"Pode falar sem “{self.palavra}” ({restam}s)" if restam
                     else ESTADOS["ouvindo"][1].format(palavra=self.palavra))
        elif nome in ("trabalhando", "falando") and e["detalhe"]:
            texto = ("Fazendo: " if nome == "trabalhando" else "") + e["detalhe"]
        texto = texto if len(texto) <= 32 else texto[:31] + "…"

        altura = ALTURA_ABERTA if self.aberto else ALTURA
        pensamento = e.get("pensamento") or ""
        largura = LARGURA + (VAO + LARGURA_PENSAMENTO if pensamento else 0)
        if largura != self._largura:
            self._largura = largura
            self._redimensionar()
        t = self.tela
        t.delete("all")
        self._retangulo_redondo(1, 1, LARGURA - 1, altura - 1, 18 if self.cantos_redondos else 0,
                                fill=FUNDO, outline=self.borda)
        if pensamento:
            self._desenhar_pensamento(e, pensamento)
        # bolinha (pisca enquanto grava)
        self._pulso = (self._pulso + 1) % 10
        raio = 6 + (2 if nome == "gravando" and self._pulso < 5 else 0)
        t.create_oval(18 - raio, 20 - raio, 18 + raio, 20 + raio, fill=cor, outline="")
        t.create_text(34, 20, text=texto, anchor="w", fill=TEXTO, font=(tema.FONTE, 10, "bold"))
        # medidor do microfone: barra fina embaixo, com a marca do limiar
        if nome in ("ouvindo", "gravando", "conversa") and e["limiar"]:
            escala = max(e["limiar"] * 3, 1)
            largura_barra = LARGURA - 48
            nivel_px = min(1.0, e["nivel"] / escala) * largura_barra
            t.create_rectangle(34, 32, 34 + largura_barra, 34, fill="#2a2f3b", outline="")
            t.create_rectangle(34, 32, 34 + nivel_px, 34, fill=cor, outline="")
            limiar_px = 34 + largura_barra / 3
            t.create_line(limiar_px, 30, limiar_px, 36, fill=TEXTO_FRACO)
        if self.aberto:
            ouvi = e["ultima_frase"] or "(nada ainda)"
            disse = e["ultima_resposta"] or "(nada ainda)"
            t.create_text(18, 52, text=f"Ouvi: {ouvi[:40]}", anchor="w", fill=TEXTO_FRACO, font=(tema.FONTE, 9))
            t.create_text(18, 72, text=f"Disse: {disse[:39]}", anchor="w", fill=TEXTO_FRACO, font=(tema.FONTE, 9))
            t.create_text(18, 91, text="Duplo clique: painel · Botão direito: menu", anchor="w",
                          fill="#6b7280", font=(tema.FONTE, 8))
        self.raiz.after(100, self._atualizar)

    def _desenhar_pensamento(self, e: dict, pensamento: str):
        """Segunda pilula: roxa enquanto a IA pensa, verde quando a resposta fica pronta."""
        t = self.tela
        x0 = LARGURA + VAO
        pronto = pensamento == "pronto"
        cor = COR_PRONTO if pronto else COR_PENSANDO
        self._retangulo_redondo(x0 + 1, 1, x0 + LARGURA_PENSAMENTO - 1, ALTURA - 1, 18 if self.cantos_redondos else 0,
                                fill=FUNDO, outline=cor)
        if pronto:
            texto = "Concluído · “pode falar”"
        else:
            segundos = int(time.time() - (e.get("pensamento_desde") or time.time()))
            texto = f"Pensando… {segundos}s"
        raio = 6 + (1 if not pronto and self._pulso < 5 else 0)
        t.create_oval(x0 + 18 - raio, 20 - raio, x0 + 18 + raio, 20 + raio, fill=cor, outline="")
        t.create_text(x0 + 32, 20, text=texto, anchor="w", fill=TEXTO, font=(tema.FONTE, 9, "bold"))
        if self.aberto:
            pergunta = (e.get("pensamento_pergunta") or "")[:26]
            t.create_text(x0 + 12, 52, text=f"Pergunta: {pergunta}", anchor="w", fill=TEXTO_FRACO, font=(tema.FONTE, 9))
            t.create_text(x0 + 12, 72, text="Clique: ouvir · Botão dir.: descartar" if pronto else "Pode dar outros comandos",
                          anchor="w", fill=TEXTO_FRACO, font=(tema.FONTE, 8))
