"""Janelinha que aparece no fim do ditado: ler, corrigir e escolher para onde vai.

O Mestre escreve o texto em logs/ditado_revisao.json e abre esta janela. Ela grava as
correcoes no mesmo arquivo; o botao escolhido vira "estado": "escolhido" e o Mestre envia.
Se voce responder por voz, o Mestre muda o estado para "fechar" e a janela some sozinha.
"""
import json
import sys

import customtkinter as ctk

from . import tema
from .config import PASTA_LOGS

ARQUIVO = PASTA_LOGS / "ditado_revisao.json"


def ler() -> dict:
    try:
        return json.loads(ARQUIVO.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def gravar(dados: dict) -> None:
    ARQUIVO.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")


class Revisao(ctk.CTk):
    def __init__(self):
        tema.aplicar()
        super().__init__()
        self.dados = ler()
        nome = self.dados.get("nome") or "Mestre"
        self.title(f"{nome} · Revisar o ditado")
        largura, altura = 920, 540
        x, y = tema.posicao_janela((self.winfo_screenwidth() - largura) // 2,
                                    max(0, (self.winfo_screenheight() - altura) // 2 - 40))
        self.geometry(f"{largura}x{altura}+{x}+{y}")
        self.minsize(560, 380)
        self.attributes("-topmost", True)
        self.after(1500, lambda: self.attributes("-topmost", False))
        self.fonte = ctk.CTkFont(family=tema.FONTE, size=tema.TAMANHO)

        ctk.CTkLabel(self, text="Confira o que eu anotei", anchor="w", text_color=tema.ROSA,
                     font=ctk.CTkFont(family=tema.FONTE, size=tema.TAMANHO + 6, weight="bold")).pack(fill="x", padx=20, pady=(16, 0))
        ctk.CTkLabel(self, text="Corrija o que precisar. Depois clique no destino, ou fale (ex.: “manda pro projeto”).",
                     anchor="w", text_color=tema.TEXTO_FRACO).pack(fill="x", padx=20, pady=(0, 8))
        self.caixa = ctk.CTkTextbox(self, wrap="word", font=self.fonte)
        self.caixa.pack(fill="both", expand=True, padx=20)
        self.caixa.insert("1.0", self.dados.get("texto", ""))
        self.caixa.bind("<KeyRelease>", lambda e: self._agendar_gravar())
        self._espera = None

        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.pack(fill="x", padx=20, pady=14, before=self.caixa)
        self.caixa.pack_forget()
        self.caixa.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        sugerido = self.dados.get("sugerido") or ""
        secundario = dict(fg_color=tema.SECUNDARIO, hover_color=tema.SECUNDARIO_HOVER, text_color=tema.TEXTO)
        for destino, texto in (("projeto", f"Projeto {nome} (Claude Code)"),
                               ("salvar", "Só salvar nas melhorias"), ("copiar", "Copiar")):
            estilo = {} if destino == sugerido or (not sugerido and destino == "projeto") else secundario
            ctk.CTkButton(botoes, text=texto, height=38, **estilo,
                          command=lambda d=destino: self._escolher(d)).pack(side="left", padx=(0, 8))
        ctk.CTkButton(botoes, text="Cancelar", height=38, fg_color=tema.PERIGO, hover_color=tema.PERIGO_HOVER,
                      text_color=tema.TEXTO, command=lambda: self._terminar("cancelado")).pack(side="right")
        self.protocol("WM_DELETE_WINDOW", lambda: self._terminar("fechado"))
        self.after(400, self._vigiar)

    def _texto(self) -> str:
        return self.caixa.get("1.0", "end").strip()

    def _agendar_gravar(self):
        if self._espera:
            self.after_cancel(self._espera)
        self._espera = self.after(400, self._gravar_texto)

    def _gravar_texto(self):
        self._espera = None
        dados = ler() or self.dados
        if dados.get("estado") == "aberto":
            dados["texto"] = self._texto()
            gravar(dados)

    def _escolher(self, destino: str):
        dados = ler() or self.dados
        dados.update(texto=self._texto(), destino=destino, estado="escolhido")
        gravar(dados)
        self.destroy()

    def _terminar(self, situacao: str):
        dados = ler() or self.dados
        if dados.get("estado") == "aberto":
            dados.update(texto=self._texto(), estado=situacao)
            gravar(dados)
        self.destroy()

    def _vigiar(self):
        """O Mestre recebeu a resposta por voz: fecha sozinha."""
        if ler().get("estado") != "aberto":
            self.destroy()
            return
        self.after(400, self._vigiar)


def main() -> None:
    if not ARQUIVO.exists():
        sys.exit(0)
    tema.definir_icone_da_barra()
    Revisao().mainloop()


if __name__ == "__main__":
    main()
