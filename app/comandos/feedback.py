"""Feedback ("isso ta errado"), agradecimento, melhorias para o Claude Code e exportar.

Mixin do Executor (app/comandos/__init__.py): os metodos usam self.voz, self.cfg, self.falar...
do nucleo e chamam metodos dos outros mixins pelo self.
"""
import random
import re
import shutil
from datetime import datetime
from .. import estado, sistema
from ..config import PASTA_PROJETO

from .base import ARQUIVO_MELHORIAS, PROMPT_MELHORIAS, _quantos


class FeedbackMixin:
    # =================================================================
    #  Feedback: "isso ta errado" guarda o erro para o Claude Code corrigir
    # =================================================================
    def _cmd_feedback(self, t: str) -> bool:
        achado = re.search(r"\b(isso (ta|esta) errado|ta errado|voce errou|errou|nao era isso|nao foi isso|"
                           r"entendeu errado|feedback)\b", t)
        if not achado:
            return False
        self._foi_feedback = True
        self._cancelar_memoria_ia()   # FEEDBACK/"nao era isso": nao guarda (e apaga se ja tinha guardado)
        if not self._ultimo:
            self.voz.falar("Ainda não fiz nada pra você corrigir.")
            return True
        correcao = re.split(r"(?i)\b(feedback|errado|errou|isso|era|foi)\b[\s,:.]*", self._frase_original)[-1].strip(" ,.")
        if len(correcao) < 3:
            self.perguntar("Poxa. O que era pra eu ter feito?", self._salvar_feedback, espera=20)
        else:
            self._salvar_feedback(correcao)
        return True

    def _salvar_feedback(self, correcao: str) -> None:
        self._foi_feedback = True
        u = self._ultimo
        audio = estado.ler().get("audio_anterior") or b""
        anexo = ""
        if audio:
            from ..audio import salvar_wav

            pasta = PASTA_PROJETO / "logs" / "feedback"
            pasta.mkdir(parents=True, exist_ok=True)
            arquivo = pasta / f"{datetime.now():%Y%m%d_%H%M%S}.wav"
            salvar_wav(audio, arquivo)
            anexo = f" [áudio: logs/feedback/{arquivo.name}]"
        self._salvar_melhoria(
            f"FEEDBACK: ouvi \"{u.get('ouvi', '')}\" · entendi \"{u.get('entendi', '')}\" · "
            f"respondi \"{u.get('respondi', '')}\" · o certo era: {correcao.strip()}{anexo}")

    def _cmd_obrigado(self, t: str) -> bool:
        if re.fullmatch(r"(muito )?(obrigado|obrigada|brigado|brigada|valeu|vlw|agradecido|thanks)( (demais|mesmo|cara|mano))?", t):
            self.falar("obrigado")
            return True
        return False

    # =================================================================
    #  Melhorias: anote por voz, o Claude Code implementa
    # =================================================================
    def _cmd_melhorias(self, t: str) -> bool:
        if re.search(r"\b(aplica|aplicar|implementa|implementar|trabalha|faz|fazer|executa)\b.*\b(melhorias|ideias|sugestoes)\b", t):
            self._aplicar_melhorias()
            return True
        if re.search(r"\b(le|quais sao|lista|fala) (as )?(minhas )?(melhorias|ideias)\b", t):
            pendentes = self._melhorias_pendentes()
            if not pendentes:
                self.voz.falar("Não tem nenhuma melhoria pendente.")
            else:
                self.voz.falar(f"{_quantos(len(pendentes), 'pendente')}: " + ". ".join(pendentes[:5]))
            return True
        achado = re.search(r"\b(anota|registra|tenho|nova|anotar|salva) (uma |a )?(melhoria|ideia|sugestao)( (pra|para|pro) (voce|o mestre|mestre))?\b", t)
        if not achado:
            return False
        # Pega o texto depois de "melhoria"/"ideia" na frase original (com acentos)
        partes = re.split(r"(?i)melhoria|ideia|ideia|sugest[aã]o", self._frase_original, maxsplit=1)
        ideia = re.sub(r"^[\s,:;.!-]*((pra|para|pro)\s+(você|voce|o mestre|mestre)\b)?[\s,:;.!-]*", "",
                       partes[1] if len(partes) > 1 else "", flags=re.I).strip()
        if len(ideia) < 4:
            self.perguntar("Manda a ideia, tô anotando.", self._salvar_melhoria, espera=20)
        else:
            self._salvar_melhoria(ideia)
        return True

    def _salvar_melhoria(self, ideia: str, falar: bool = True) -> None:
        if not ARQUIVO_MELHORIAS.exists():
            ARQUIVO_MELHORIAS.write_text(
                "# Melhorias para o Mestre\n\n"
                "Ideias anotadas por voz. O Claude Code implementa as pendentes (- [ ]).\n\n",
                encoding="utf-8")
        linhas = [x.strip() for x in ideia.strip().splitlines() if x.strip()] or [""]
        with open(ARQUIVO_MELHORIAS, "a", encoding="utf-8") as f:
            f.write(f"- [ ] ({datetime.now():%d/%m/%Y}) {linhas[0]}\n")
            for continuacao in linhas[1:]:   # ditado longo: o resto fica recuado, no mesmo item
                f.write(f"      {continuacao}\n")
        if falar:
            self.voz.falar(random.choice(["Anotado na lista de melhorias!", "Ideia guardada!",
                                          "Boa! Anotei na lista."]))

    def _melhorias_pendentes(self) -> list[str]:
        if not ARQUIVO_MELHORIAS.exists():
            return []
        return [re.sub(r"^- \[ \] (\(.*?\) )?", "", linha).strip()
                for linha in ARQUIVO_MELHORIAS.read_text(encoding="utf-8").splitlines()
                if linha.startswith("- [ ]")]

    def _aplicar_melhorias(self) -> None:
        pendentes = self._melhorias_pendentes()
        if not pendentes:
            self.voz.falar("A lista de melhorias está vazia. Me fala uma ideia primeiro.")
            return
        if not shutil.which("claude"):
            self.voz.falar("Pra isso eu preciso do Claude Code instalado. Abri a lista de melhorias; "
                           "o passo a passo está no guia, na etapa 14.")
            sistema.abrir_arquivo(ARQUIVO_MELHORIAS)
            return
        self.voz.falar(f"Chamando o Claude Code pra trabalhar em {_quantos(len(pendentes), 'melhoria')}. "
                       "Acompanha na janela que vai abrir. Quando terminar, fala: {palavra}, reinicia.")
        sistema.abrir_terminal_com(f'claude "{PROMPT_MELHORIAS}"', PASTA_PROJETO, "Mestre - melhorias")

    def _cmd_exportar(self, t: str) -> bool:
        """ "exporta o histórico": arquivo para o Claude analisar o que deu errado (app/exportar.py)."""
        puro = self._pedido_puro()
        if not re.search(r"\b(exporta|exportar|exporte|gera|gerar|salva|manda|mandar|passa)\b.*\b(historico|"
                         r"relatorio (dos|de) testes?|frases? (dos|de) testes?)\b", puro):
            return False
        from .. import exportar
        periodo = ("hoje" if re.search(r"\bhoje\b", puro) else "tudo" if re.search(r"\b(tudo|todo|completo|inteiro)\b", puro)
                   else "30 dias" if re.search(r"\b(mes|30 dias)\b", puro) else "7 dias")
        arquivo = exportar.gerar(self.cfg, periodo)
        sistema.mostrar_na_pasta(arquivo)
        self.voz.falar(f"Histórico de {periodo} exportado. A pasta abriu com o arquivo marcado: é só arrastar pro Claude.")
        return True
