"""Janela do avatar robô (PROCESSO SEPARADO, PySide6). O Assessor abre com `app.avatar.iniciar()`.

    pythonw -m app.avatar_janela --pai <pid do Assessor> --nome Assessor --palavra assessor

- Sem fundo (transparência por pixel), sempre por cima, sem botão na barra de tarefas.
- Lê o estado de logs/estado_agora.json (só quando o arquivo muda) e o volume da fala por UDP (app.avatar).
- Arraste para mudar de lugar (fica salvo em %APPDATA%\\Mestre\\avatar.json). Duplo clique: painel.
  Botão direito: Pausar/Retomar, Abrir painel, Voltar ao lugar padrão, Esconder avatar.
- Fecha sozinho quando o Assessor fecha. Código de saída 0 = fechou normal/escondido; outro = erro (o Assessor
  volta para a bolinha).
- `--estado arquivo.json --pai 0` serve para testar sem o Assessor (medir consumo, ver as animações).
"""
import argparse
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (QAction, QBrush, QColor, QFont, QGuiApplication, QLinearGradient, QPainter,
                           QPainterPath, QPen, QRadialGradient)
from PySide6.QtWidgets import QApplication, QMenu, QWidget

from . import avatar, estado, tema
from .config import PASTA_PROJETO

VERDE = "#7DE3B8"
VISOR = ("#2E2229", "#120C0F")
BALAO = "#2A1F25"
ESCURO = "#1C1418"
LILAS_ZZZ = "#E7C6F0"
SELO = "#FF5C8A"


def tons_do_rosa(cor: str) -> tuple[str, str, str]:
    """(claro, meio, escuro) da cabeça. Rosa padrão = cores exatas do protótipo; outra cor = misturas."""
    if cor.upper() == "#F5A6C8":
        return "#FFD0E3", "#F5A6C8", "#CF7896"
    return tema.misturar(cor, "#FFFFFF", 0.45), cor, tema.misturar(cor, "#5A1030", 0.28)


def _cor(hexa: str, alfa: float = 1.0) -> QColor:
    c = QColor(hexa)
    c.setAlphaF(max(0.0, min(1.0, alfa)))
    return c


class Avatar(QWidget):
    def __init__(self, args):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(avatar.LADO_JANELA, avatar.LADO_JANELA)
        self.pai = args.pai
        self.nome, self.palavra = args.nome, args.palavra.capitalize()
        self.arq_estado = Path(args.estado) if args.estado else estado.ARQUIVO_AGORA
        self.claro, self.meio, self.escuro = tons_do_rosa(tema.ROSA)
        self.anim = avatar.Animador()
        self.dados: dict = {}
        self._mtime = None
        self._ultimo_pai = 0.0
        self._arrasto = None
        self._arrastou = False
        self._dica = ""
        self._q = None
        self._sock = None
        self._tenta_porta = 0.0
        self.ir_para(self._posicao_inicial())

        self.tempo = QTimer(self)                  # animação: só roda quando há algo mexendo
        self.tempo.setTimerType(Qt.PreciseTimer)
        self.tempo.timeout.connect(self._tick)
        self.vigia = QTimer(self)                  # estado do Assessor: leve (olha a data do arquivo)
        self.vigia.timeout.connect(self._vigiar)
        self.vigia.start(150)
        self._vigiar()

    # --- posição ----------------------------------------------------------------------------
    def _telas(self) -> list:
        return [(g.x(), g.y(), g.x() + g.width(), g.y() + g.height())
                for g in (s.availableGeometry() for s in QGuiApplication.screens())]

    def _padrao(self) -> tuple[int, int]:
        g = QGuiApplication.primaryScreen().availableGeometry()
        return avatar.posicao_padrao((g.x(), g.y(), g.x() + g.width(), g.y() + g.height()))

    def _posicao_inicial(self) -> tuple[int, int]:
        pos = avatar.ler_posicao()
        return pos if pos and avatar.posicao_valida(pos, self._telas()) else self._padrao()

    def ir_para(self, pos) -> None:
        self.move(int(pos[0]), int(pos[1]))

    def voltar_ao_padrao(self) -> None:
        avatar.salvar_posicao(None)
        self.ir_para(self._padrao())

    # --- estado -------------------------------------------------------------------------------
    def _ler(self) -> None:
        try:
            mtime = self.arq_estado.stat().st_mtime
        except OSError:
            mtime = None
        if mtime != self._mtime:
            self._mtime = mtime
            try:
                self.dados = json.loads(self.arq_estado.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                pass   # (o Assessor gravando agora: lê na próxima volta)

    def _pai_vivo(self, agora: float) -> bool:
        if self.pai <= 0:
            return True
        if agora - self._ultimo_pai > 1.0:
            self._ultimo_pai = agora
            self._pai_ok = avatar.processo_vivo(self.pai)
        return getattr(self, "_pai_ok", True)

    def _vigiar(self) -> None:
        agora = time.monotonic()
        self._ler()
        vivo = self._pai_vivo(agora)
        dados = self.dados
        if self.pai > 0 and dados.get("pid") != self.pai:
            dados = {"nome": "iniciando"}   # arquivo ainda é do Assessor anterior: espera o novo publicar
        novo = avatar.visual(dados, rodando=vivo, pausado=estado.pausado())
        fila = int(self.dados.get("pensamentos_fila") or 0)
        pronto = self.dados.get("pensamento") == "pronto"
        self.anim.mudar(novo, agora, fila, pronto)
        self._receber_nivel(agora)
        self._atualizar_dica()
        if self.anim.terminou(agora) and self.anim.base == "desligado":
            QApplication.instance().exit(0)
            return
        self._acordar(agora)

    def _acordar(self, agora: float) -> None:
        fps = self.anim.fps(agora)
        if fps and not self.isVisible():
            self.show()
        if fps:
            intervalo = int(1000 / fps)
            if not self.tempo.isActive() or self.tempo.interval() != intervalo:
                self.tempo.start(intervalo)
        else:
            self.tempo.stop()
            if self.isVisible():
                self.hide()

    def _tick(self) -> None:
        agora = time.monotonic()
        self._receber_nivel(agora)
        self._q = self.anim.quadro(agora)
        self.update()
        self._acordar(agora)

    def _receber_nivel(self, agora: float) -> None:
        if self._sock is None and agora >= self._tenta_porta:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.bind(("127.0.0.1", avatar.PORTA_NIVEL))
                s.setblocking(False)
                self._sock = s
            except OSError:
                self._tenta_porta = agora + 5   # porta ocupada (outro avatar fechando): tenta de novo depois
        if self._sock is None:
            return
        ultimo = None
        while True:
            try:
                ultimo = self._sock.recv(32)
            except (BlockingIOError, OSError):
                break
        if ultimo:
            try:
                self.anim.nivel(float(ultimo.decode()), agora)
            except ValueError:
                pass

    def _atualizar_dica(self) -> None:
        d = self.dados
        textos = {"idle": f"Ouvindo · diga “{self.palavra}”", "ouvindo": "Ouvindo você...", "pensando": "Pensando...",
                  "falando": "Falando...", "descansando": "Descansando · diga “bora voltar”", "pausado": "Pausado",
                  "desligado": "Desligado"}
        linha = textos.get(self.anim.base, self.nome)
        if self.anim.fila > 1 and self.anim.base == "pensando":
            linha += f" ({self.anim.fila} na fila)"
        if self.anim.pronto:
            linha += " · resposta pronta: diga “pode falar”"
        dica = (f"{self.nome}: {linha}\nOuvi: {(d.get('ultima_frase') or '(nada ainda)')[:60]}\n"
                f"Disse: {(d.get('ultima_resposta') or '(nada ainda)')[:60]}\nDuplo clique: painel · Botão direito: menu")
        if dica != self._dica:
            self._dica = dica
            self.setToolTip(dica)

    # --- mouse --------------------------------------------------------------------------------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._arrasto = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._arrastou = False

    def mouseMoveEvent(self, e):
        if self._arrasto is not None and e.buttons() & Qt.LeftButton:
            novo = e.globalPosition().toPoint() - self._arrasto
            if self._arrastou or (novo - self.pos()).manhattanLength() > 3:
                self._arrastou = True
                self.move(novo)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self._arrastou:
            avatar.salvar_posicao((self.x(), self.y()))
        self._arrasto = None

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            abrir_painel()

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        pausado = estado.pausado()
        acoes = [("Retomar a escuta" if pausado else "Pausar a escuta", lambda: estado.pausar(not pausado)),
                 ("Abrir painel", abrir_painel), None,
                 ("Voltar ao lugar padrão", self.voltar_ao_padrao),
                 ("Esconder avatar (volta ao reiniciar)", lambda: QApplication.instance().exit(0))]
        for item in acoes:
            if item is None:
                menu.addSeparator()
                continue
            acao = QAction(item[0], menu)
            acao.triggered.connect(item[1])
            menu.addAction(acao)
        menu.exec(e.globalPos())
        QTimer.singleShot(50, self._vigiar)

    # --- desenho ------------------------------------------------------------------------------
    def paintEvent(self, _e):
        q = self._q
        if not q or not q["visivel"]:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        esc = avatar.TAMANHO / 200
        p.translate(avatar.FOLGA, avatar.FOLGA)
        p.scale(esc, esc)
        # caixa inteira (entrar/voltar/sair): origem no centro
        p.save()
        p.setOpacity(q["in_op"])
        p.translate(100, 100 + q["in_dy"])
        p.scale(q["in_sx"], q["in_sy"])
        p.translate(-100, -100)
        self._desenhar_robo(p, q)
        self._desenhar_extras(p, q)
        if q["flash_op"] > 0:   # anel verde da entrada
            p.setPen(QPen(_cor(VERDE, q["flash_op"]), 3 / esc))
            p.setBrush(Qt.NoBrush)
            r = 70 * q["flash_esc"]
            p.drawEllipse(QPointF(100, 110), r, r)
        p.restore()
        p.end()

    def _grad(self, y0, y1, cores):
        g = QLinearGradient(0, y0, 0, y1)
        for pos, cor in cores:
            g.setColorAt(pos, QColor(cor))
        return QBrush(g)

    def _desenhar_robo(self, p: QPainter, q: dict) -> None:
        rosa = lambda y0, y1: self._grad(y0, y1, [(0, self.claro), (0.55, self.meio), (1, self.escuro)])  # noqa: E731
        # sombra
        p.save()
        p.translate(100, 190)
        p.scale(q["sombra_sx"], 1)
        p.setPen(Qt.NoPen)
        p.setBrush(_cor("#000000", q["sombra_op"]))
        p.drawEllipse(QPointF(0, 0), 52, 7)
        p.restore()
        # corpo (balanço + inclinação; origem embaixo, no meio)
        p.save()
        p.translate(100, 180)
        p.translate(0, q["rig_dy"])
        p.scale(q["rig_sx"], q["rig_sy"])
        p.rotate(q["tilt"])
        p.translate(-100, -180)
        p.setPen(Qt.NoPen)
        p.setBrush(rosa(146, 180))
        p.drawRoundedRect(QRectF(72, 146, 56, 34), 15, 15)
        p.setBrush(_cor(VERDE, q["brilho"]))
        p.drawEllipse(QPointF(100, 162), 5, 5)
        p.setPen(QPen(QColor(self.escuro), 5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(100, 50), QPointF(100, 30))
        p.setPen(Qt.NoPen)
        brilho = QRadialGradient(QPointF(100, 25), 14)
        brilho.setColorAt(0, _cor(VERDE, 0.9))
        brilho.setColorAt(1, _cor(VERDE, 0))
        p.setOpacity(p.opacity() * q["brilho"])
        p.setBrush(QBrush(brilho))
        p.drawEllipse(QPointF(100, 25), 14, 14)
        p.setOpacity(q["in_op"])
        p.setBrush(_cor(VERDE, 0.35 + 0.65 * q["luz"]))
        p.drawEllipse(QPointF(100, 25), 7, 7)
        p.setBrush(QColor(self.escuro))
        p.drawRoundedRect(QRectF(27, 84, 16, 34), 8, 8)
        p.drawRoundedRect(QRectF(157, 84, 16, 34), 8, 8)
        p.setBrush(rosa(46, 150))
        p.drawRoundedRect(QRectF(38, 46, 124, 104), 40, 40)
        p.save()   # brilho da cabeça
        p.translate(74, 60)
        p.rotate(-12)
        p.setBrush(_cor("#FFFFFF", 0.4))
        p.drawEllipse(QPointF(0, 0), 24, 7)
        p.restore()
        p.setBrush(self._grad(68, 130, [(0, VISOR[0]), (1, VISOR[1])]))
        p.drawRoundedRect(QRectF(52, 68, 96, 62), 26, 26)
        p.setBrush(_cor("#FFFFFF", 0.06))
        p.drawRoundedRect(QRectF(58, 72, 60, 8), 4, 4)
        # olhos de LED (olhar, escala, piscar)
        p.save()
        p.translate(q["look_x"], q["look_y"])
        p.translate(100, 93)
        p.scale(q["olhos_sx"], max(0.02, q["olhos_sy"]))
        p.translate(-100, -93)
        cor_olho = QColor(VERDE) if q["luz"] > 0.98 else _cor(tema.misturar(VISOR[0], VERDE, 0.2 + 0.8 * q["luz"]))
        p.setBrush(cor_olho)
        p.drawRoundedRect(QRectF(69, 82, 17, 22), 8.5, 8.5)
        p.drawRoundedRect(QRectF(114, 82, 17, 22), 8.5, 8.5)
        p.restore()
        # boca: sorriso <-> boca aberta que segue o volume da fala
        if q["boca"] < 0.99:
            p.setOpacity(q["in_op"] * (1 - q["boca"]))
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(QColor(VERDE), 4, Qt.SolidLine, Qt.RoundCap))
            caminho = QPainterPath(QPointF(89, 113))
            caminho.quadTo(QPointF(100, 121), QPointF(111, 113))
            p.drawPath(caminho)
        if q["boca"] > 0.01:
            p.setOpacity(q["in_op"] * q["boca"])
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(VERDE))
            p.drawEllipse(QPointF(100, 116), 9 * q["boca_sx"], 7 * q["boca_sy"])
        p.setOpacity(q["in_op"])
        p.restore()

    def _desenhar_extras(self, p: QPainter, q: dict) -> None:
        base = q["in_op"]
        p.setPen(Qt.NoPen)
        if q["ondas"] > 0.01:   # ondas de voz ao lado
            p.setOpacity(base * q["ondas"])
            p.setBrush(QColor(VERDE))
            for (x, y, h), esc in zip(((178, 97, 26), (187, 90, 40), (196, 99, 22)), q["barras"]):
                meio, alt = y + h / 2, h * esc
                p.drawRoundedRect(QRectF(x, meio - alt / 2, 6, alt), 3, 3)
        if q["balao"] > 0.01:   # balão com os pontinhos
            p.save()
            p.setOpacity(base * q["balao"])
            k = 0.4 + 0.6 * q["balao"]
            p.translate(161, 24)
            p.scale(k, k)
            p.translate(-161, -24)
            p.setBrush(QColor(BALAO))
            p.setPen(QPen(_cor(VERDE, 0.55), 2))
            p.drawRoundedRect(QRectF(134, 4, 56, 28), 14, 14)
            p.setPen(QPen(_cor(VERDE, 0.55), 1.5))
            p.drawEllipse(QPointF(132, 40), 5, 4.5)
            p.setPen(Qt.NoPen)
            for x, (dy, op) in zip((150, 162, 174), q["pontos"]):
                p.setBrush(_cor(VERDE, op))
                p.drawEllipse(QPointF(x, 18 + dy), 4.2, 4.2)
            p.restore()
        if q["zzz"] > 0.01:   # zzz dormindo
            p.setPen(QColor(LILAS_ZZZ))
            for (x, y, tam), (dx, dy, esc, op) in zip(((160, 58, 22), (152, 66, 16), (168, 52, 13)), q["zs"]):
                p.save()
                p.setOpacity(base * q["zzz"] * op)
                p.translate(x + dx + tam * 0.25, y + dy - tam * 0.35)
                p.scale(esc, esc)
                f = QFont(tema.FONTE)
                f.setPixelSize(tam)
                f.setWeight(QFont.ExtraBold)
                p.setFont(f)
                p.drawText(QPointF(-tam * 0.25, tam * 0.35), "z")
                p.restore()
        if q["selo"] > 0.01:   # selo: quantos na fila do pensando (ou resposta pronta)
            p.save()
            p.setOpacity(base * q["selo"])
            k = 0.4 + 0.6 * q["selo"]
            p.translate(40, 38)
            p.scale(k, k)
            pronto = q["selo_texto"] == "✓"
            p.setBrush(QColor(VERDE if pronto else SELO))
            p.setPen(QPen(QColor(ESCURO), 3))
            p.drawEllipse(QPointF(0, 0), 14, 14)
            f = QFont(tema.FONTE)
            f.setPixelSize(16)
            f.setWeight(QFont.ExtraBold)
            p.setFont(f)
            p.setPen(QColor(ESCURO if pronto else "#FFFFFF"))
            p.drawText(QRectF(-14, -14, 28, 28), Qt.AlignCenter, q["selo_texto"][:2])
            p.restore()


def abrir_painel() -> None:
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    try:
        subprocess.Popen([str(pythonw if pythonw.exists() else sys.executable), "-m", "app.iniciar_painel"],
                         cwd=str(PASTA_PROJETO), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except OSError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pai", type=int, default=0)
    parser.add_argument("--nome", default="Assessor")
    parser.add_argument("--palavra", default="assessor")
    parser.add_argument("--estado", default="")
    args = parser.parse_args()
    if tema.testando():
        return 0   # teste automático: nada aparece na tela
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Assessor.Avatar")
    except Exception:
        pass
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv[:1])
    app.setQuitOnLastWindowClosed(False)
    janela = Avatar(args)   # (guardar a referência: senão o Python apaga a janela)
    codigo = app.exec()
    del janela
    return codigo


if __name__ == "__main__":
    sys.exit(main())
