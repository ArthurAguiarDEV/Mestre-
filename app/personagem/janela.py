"""Janela do PERSONAGEM (PROCESSO SEPARADO, PySide6): faz o papel do robô em app/avatar_janela.py, opcional.

    pythonw -m app.personagem.janela --pai <pid do Assessor> --nome Assessor --palavra assessor --tipo texto_avatar

- Sem fundo, sempre por cima, sem botão na barra de tarefas. Arraste para mudar de lugar (o mesmo arquivo do robô:
  %APPDATA%\\Mestre\\personagem.json, separado do robô). Duplo clique: painel. Um clique: ele reage. Botão direito: menu.
- Lê logs/estado_agora.json (só quando muda) e o volume da fala por UDP (app.avatar): a boca e os gestos seguem a voz.
- Aparência, jeito e passeio vêm do config.yaml (`avatar > personagem`, `avatar > jeito`, `avatar > passeio`) e valem NA HORA:
  o config é relido em segundo plano quando muda (mexeu no painel, o personagem muda sem reiniciar).
- Código de saída 0 = fechou normal/escondido; outro = erro (o Assessor volta ao robô/bolinha).
- `--estado arquivo.json --pai 0` serve para testar sem o Assessor.
"""
import argparse
import json
import math
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import yaml
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (QAction, QColor, QCursor, QFont, QFontMetrics, QGuiApplication, QPainter, QPen,
                           QRadialGradient)
from PySide6.QtWidgets import QApplication, QMenu, QWidget

from .. import avatar, estado, tema
from ..config import ARQUIVO_CONFIG, PASTA_PROJETO
from . import catalogo_animacao as A
from . import catalogo as cat
from .animacao import Animador
from .cena import montar
from .opcoes import ALTURA_BALAO, FOLGA, VAO_BALAO, dimensoes, opcoes_do_config  # noqa: F401
from .passeio import MODOS, NOMES_MODO, do_config
from .render_qt import Desenhista

POSICAO = "personagem"   # lugar salvo em %APPDATA%\Mestre\personagem.json (o robô, de outro tamanho, usa avatar.json)

VERDE = "#7DE3B8"
ESCURO = "#1C1418"
COR_PENSANDO_TXT, COR_FALANDO_TXT, COR_NEUTRA_TXT = "#b388ff", "#4fd1c5", "#8a8f99"
CORES_BALAO = {"ligando": VERDE, "idle": VERDE, "ouvindo": VERDE, "pensando": COR_PENSANDO_TXT, "falando": COR_FALANDO_TXT,
               "pausado": COR_NEUTRA_TXT, "descansando": COR_NEUTRA_TXT, "desligado": COR_NEUTRA_TXT}
ESTADOS_JANELA = {"idle": "idle", "ouvindo": "ouvindo", "pensando": "pensando", "falando": "falando", "descansando": "descansando"}


def _cor(hexa: str, alfa: float = 1.0) -> QColor:
    c = QColor(hexa)
    c.setAlphaF(max(0.0, min(1.0, alfa)))
    return c


def ler_config() -> dict:
    try:
        return yaml.safe_load(ARQUIVO_CONFIG.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}


class Personagem(QWidget):
    def __init__(self, args):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.tipo = args.tipo if args.tipo in avatar.TIPOS else "texto_avatar"
        self.balao_on = self.tipo == "texto_avatar"
        self.pai = args.pai
        self.nome, self.palavra = args.nome, args.palavra.capitalize()
        self.arq_estado = Path(args.estado) if args.estado else estado.ARQUIVO_AGORA
        self.ciclo = avatar.Animador()          # entrar / voltar / sair / desligar e visibilidade
        self.dados: dict = {}
        self.balao_texto = ""
        self._mtime = None
        self._ultimo_pai = 0.0
        self._arrasto = None
        self._arrastou = False
        self._dica = ""
        self._q = None
        self._p = None
        self._sock = None
        self._tenta_porta = 0.0
        self._cfg_mtime = None
        self._cfg_novo = None
        self._cfg_ativo = True
        self._chegada = None
        self._pos_passeio = None
        self.op = None
        self.pers = None
        self.desenho = None
        self.passeio = None
        self.aplicar_opcoes(opcoes_do_config(ler_config()), primeira=True)
        threading.Thread(target=self._vigiar_config, daemon=True).start()
        self.tempo = QTimer(self)
        self.tempo.setTimerType(Qt.PreciseTimer)
        self.tempo.timeout.connect(self._tick)
        self.vigia = QTimer(self)
        self.vigia.timeout.connect(self._vigiar)
        self.vigia.start(150)
        self._vigiar()

    # --- configuração ao vivo ---------------------------------------------------------------------------
    def _vigiar_config(self) -> None:
        while self._cfg_ativo:
            try:
                m = ARQUIVO_CONFIG.stat().st_mtime
            except OSError:
                m = None
            if m != self._cfg_mtime:
                primeiro = self._cfg_mtime is None
                self._cfg_mtime = m
                if not primeiro:
                    self._cfg_novo = ler_config()
            time.sleep(2.0)

    def aplicar_opcoes(self, op: dict, primeira: bool = False) -> None:
        """Perfil, jeito e passeio (na largada e sempre que o painel salvar algo)."""
        antigo = self.op
        self.op = op
        if antigo is None or antigo["perfil"] != op["perfil"]:
            self.desenho = Desenhista(montar(op["perfil"]))
            self.dim = dimensoes(op["perfil"]["escala"], self.balao_on)
            self.setFixedSize(self.dim["largura"], self.dim["altura"])
            self.largura, self.altura = self.dim["largura"], self.dim["altura"]
            if antigo is not None:
                self._reposicionar()
        if antigo is None or antigo["arquetipo"] != op["arquetipo"] or antigo["perfil"]["traje"] != op["perfil"]["traje"]:
            expr = cat.TRAJES.get(op["perfil"]["traje"], {}).get("expressao")
            novo = Animador(op["arquetipo"], expr, int(time.time()) & 0xFFFF)
            if self.pers is not None:
                novo.mudar(self.pers.estado, time.monotonic())
            self.pers = novo
        self.pers.balanco = self.desenho.cena.get("balanco", 1.0)   # cabelo comprido balança mais
        if antigo is None or (antigo["passeio"], antigo["arquetipo"], antigo["perfil"]["escala"]) != (op["passeio"], op["arquetipo"], op["perfil"]["escala"]):
            self.passeio = do_config(op["passeio"], A.ARQUETIPOS[op["arquetipo"]], op["perfil"]["escala"])
            self._pos_passeio = None
        if primeira:
            self.ir_para(self._posicao_inicial())

    def _reposicionar(self) -> None:
        self.ir_para(self._padrao() if not avatar.ler_posicao(POSICAO) else self._posicao_inicial())

    # --- posição --------------------------------------------------------------------------------------------
    def _telas(self) -> list:
        return [(g.x(), g.y(), g.x() + g.width(), g.y() + g.height())
                for g in (s.availableGeometry() for s in QGuiApplication.screens())]

    def _padrao(self) -> tuple[int, int]:
        g = QGuiApplication.primaryScreen().availableGeometry()
        return avatar.posicao_padrao((g.x(), g.y(), g.x() + g.width(), g.y() + g.height()), folga=FOLGA,
                                     largura=self.largura, altura=self.altura)

    def _centro(self, x: float, y: float) -> tuple[float, float]:
        d = self.dim
        return x + self.largura - FOLGA - d["larg_personagem"] / 2, y + self.altura - FOLGA - d["altura_px"] / 2

    def _posicao_valida(self, pos) -> bool:
        try:
            cx, cy = self._centro(int(pos[0]), int(pos[1]))
        except (TypeError, ValueError, IndexError):
            return False
        return any(e <= cx < d and t <= cy < b for e, t, d, b in self._telas())

    def _posicao_inicial(self) -> tuple[int, int]:
        pos = avatar.ler_posicao(POSICAO)
        return pos if pos and self._posicao_valida(pos) else self._padrao()

    def ir_para(self, pos) -> None:
        self.move(int(pos[0]), int(pos[1]))

    def voltar_ao_padrao(self) -> None:
        avatar.salvar_posicao(None, POSICAO)
        self.ir_para(self._padrao())
        self.passeio.novo_lugar(*self._ref())

    def _tela_atual(self) -> tuple:
        cx, cy = self._centro(self.x(), self.y())
        for t in self._telas():
            if t[0] <= cx < t[2] and t[1] <= cy < t[3]:
                return t
        return self._telas()[0]

    def _ref(self) -> tuple[float, float]:
        """Ponto que o passeio controla: esquerda do corpo do personagem e topo da janela."""
        return self.x() + self.largura - FOLGA - self.dim["larg_personagem"], float(self.y())

    # --- estado ----------------------------------------------------------------------------------------------
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
                pass

    def _pai_vivo(self, agora: float) -> bool:
        if self.pai <= 0:
            return True
        if agora - self._ultimo_pai > 1.0:
            self._ultimo_pai = agora
            self._pai_ok = avatar.processo_vivo(self.pai)
        return getattr(self, "_pai_ok", True)

    def _vigiar(self) -> None:
        agora = time.monotonic()
        novo_cfg, self._cfg_novo = self._cfg_novo, None
        if novo_cfg is not None:
            self.aplicar_opcoes(opcoes_do_config(novo_cfg))
        self._ler()
        vivo = self._pai_vivo(agora)
        dados = self.dados
        if self.pai > 0 and dados.get("pid") != self.pai:
            dados = {"nome": "iniciando"}
        novo = avatar.visual(dados, rodando=vivo, pausado=estado.pausado())
        fila = int(self.dados.get("pensamentos_fila") or 0)
        pronto = self.dados.get("pensamento") == "pronto"
        anim = self.ciclo.mudar(novo, agora, fila, pronto)
        if anim == "entrar":
            self._chegada = agora + 1.5
        self.pers.mudar(ESTADOS_JANELA.get(self.ciclo.base, "idle"), agora)
        if self.balao_on:
            self.balao_texto = avatar.texto_balao(dados, rodando=vivo, pausado=estado.pausado())
        self._receber_nivel(agora)
        self._atualizar_dica()
        if self.ciclo.terminou(agora) and self.ciclo.base == "desligado":
            QApplication.instance().exit(0)
            return
        self._acordar(agora)

    def _acordar(self, agora: float) -> None:
        fps = self.ciclo.fps(agora)
        if fps:
            fps = max(fps, self.pers.fps(agora) if self.ciclo.base not in ("pausado", "desligado") else fps)
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
        self._q = self.ciclo.quadro(agora)
        if self._chegada is not None and agora >= self._chegada and self.ciclo.base == "idle":
            self._chegada = None
            self.pers.gesto(self.pers.arq["chegada"], agora)
        self._passear(agora)
        self._olhar()
        self._p = self.pers.quadro(agora)
        self.update()
        self._acordar(agora)

    def _passear(self, agora: float) -> None:
        if self._arrasto is not None or not self.ciclo.visivel(agora) or self.ciclo.anim:
            self.pers.andar(0)
            return
        area = self._tela_atual()
        x, y = self._ref()
        ocupado = self.pers.estado != "idle" or self.pers.overlay is not None or self.ciclo.base != "idle"
        nx, ny, direcao = self.passeio.atualizar(agora, x, y, area, ocupado, self.dim["larg_personagem"])
        if (nx, ny) != (x, y):
            self.move(int(round(nx - (self.largura - FOLGA - self.dim["larg_personagem"]))), int(round(ny)))
        self.pers.andar(direcao, self.passeio.vel / 70.0)

    def _olhar(self) -> None:
        """Os olhos seguem o mouse (a personalidade decide o quanto)."""
        cx, cy = self._centro(self.x(), self.y())
        m = QCursor.pos()
        self.pers.olhar((m.x() - cx) / 500.0, (m.y() - (cy - self.dim["altura_px"] * 0.2)) / 320.0)

    def _receber_nivel(self, agora: float) -> None:
        if self._sock is None and agora >= self._tenta_porta:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.bind(("127.0.0.1", avatar.PORTA_NIVEL))
                s.setblocking(False)
                self._sock = s
            except OSError:
                self._tenta_porta = agora + 5
        if self._sock is None:
            return
        ultimo = None
        while True:
            try:
                ultimo = self._sock.recv(256)
            except (BlockingIOError, OSError):
                break
            texto = ultimo.decode("utf-8", "ignore")
            if texto.startswith("t:"):   # a frase que vai ser falada: vogais para a boca
                self.pers.texto(texto[2:])
                ultimo = None
        if ultimo:
            try:
                v = float(ultimo.decode())
            except ValueError:
                return
            self.ciclo.nivel(v, agora)
            self.pers.nivel(v, agora)

    def _atualizar_dica(self) -> None:
        d = self.dados
        textos = {"idle": f"Ouvindo · diga “{self.palavra}”", "ouvindo": "Ouvindo você...", "pensando": "Pensando...",
                  "falando": "Falando...", "descansando": "Descansando · diga “bora voltar”", "pausado": "Pausado",
                  "desligado": "Desligado"}
        linha = textos.get(self.ciclo.base, self.nome)
        if self.ciclo.fila > 1 and self.ciclo.base == "pensando":
            linha += f" ({self.ciclo.fila} na fila)"
        if self.ciclo.pronto:
            linha += " · resposta pronta: diga “pode falar”"
        dica = (f"{self.nome}: {linha}\nOuvi: {(d.get('ultima_frase') or '(nada ainda)')[:60]}\n"
                f"Disse: {(d.get('ultima_resposta') or '(nada ainda)')[:60]}\nDuplo clique: painel · Botão direito: menu")
        if dica != self._dica:
            self._dica = dica
            self.setToolTip(dica)

    # --- mouse ---------------------------------------------------------------------------------------------------
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
        if e.button() == Qt.LeftButton:
            if self._arrastou:
                avatar.salvar_posicao((self.x(), self.y()), POSICAO)
                self.passeio.novo_lugar(*self._ref())
            elif not self.pers.ocupado():
                self.pers.gesto(self.pers.rng.escolher([["surpresa", 2], ["acenar", 2], ["pular", 1]]), time.monotonic())
        self._arrasto = None

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            abrir_painel()

    def contextMenuEvent(self, e):
        menu = QMenu(self)
        pausado = estado.pausado()
        acoes = [("Retomar a escuta" if pausado else "Pausar a escuta", lambda: estado.pausar(not pausado)),
                 ("Abrir painel", abrir_painel), None,
                 ("Acenar", lambda: self.pers.gesto("acenar", time.monotonic())),
                 ("Fazer uma gracinha", lambda: self.pers.gesto(self.pers.rng.escolher(self.pers.arq["idle"]), time.monotonic())), None]
        for item in acoes:
            if item is None:
                menu.addSeparator()
                continue
            acao = QAction(item[0], menu)
            acao.triggered.connect(item[1])
            menu.addAction(acao)
        sub = menu.addMenu("Passeio")
        for modo in ("personalidade", *MODOS):
            a = QAction(NOMES_MODO[modo], sub, checkable=True, checked=self.op["passeio"] == modo)
            a.triggered.connect(lambda _c=False, m=modo: self._trocar_passeio(m))
            sub.addAction(a)
        menu.addSeparator()
        for txt, fn in (("Voltar ao lugar padrão", self.voltar_ao_padrao), ("Esconder o personagem (volta ao reiniciar)", lambda: QApplication.instance().exit(0))):
            a = QAction(txt, menu)
            a.triggered.connect(fn)
            menu.addAction(a)
        menu.exec(e.globalPos())
        QTimer.singleShot(50, self._vigiar)

    def _trocar_passeio(self, modo: str) -> None:
        """Escolha pelo menu do personagem: vale agora e fica salvo no config."""
        op = dict(self.op, passeio=modo)
        self.aplicar_opcoes(op)
        try:
            from .. import configuracao
            cfg = configuracao.carregar()
            configuracao.secao(cfg, "avatar")["passeio"] = configuracao.aspas(modo)
            configuracao.salvar(cfg)
        except Exception:   # sem o ruamel/painel aberto escrevendo: vale só até fechar
            pass

    # --- desenho ---------------------------------------------------------------------------------------------------
    def paintEvent(self, _e):
        q, pq = self._q, self._p
        if not q or not pq or not q["visivel"]:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        d = self.dim
        es = d["escala"]
        fx = self.largura - FOLGA - d["larg_personagem"] / 2      # pés (centro), em px da janela
        fy = self.altura - FOLGA - 4
        p.save()
        p.translate(fx, fy)
        p.scale(es, es)
        p.setOpacity(q["in_op"])
        p.translate(0, q["in_dy"] * 0.9)
        p.scale(q["in_sx"], q["in_sy"])
        self._aura(p, pq)
        self.desenho.desenhar(p, pq["pose"])
        self._extras(p, pq["extras"], time.monotonic(), q)
        if q["flash_op"] > 0:
            p.setPen(QPen(_cor(VERDE, q["flash_op"]), 3 / es))
            p.setBrush(Qt.NoBrush)
            r = 80 * q["flash_esc"]
            p.drawEllipse(QPointF(0, -100), r, r)
        p.restore()
        if self.balao_on and self.balao_texto:
            self._balao(p)
        p.end()

    def _aura(self, p: QPainter, pq: dict) -> None:
        cor = pq["extras"].get("aura")
        if not cor:
            return
        t = time.monotonic()
        g = QRadialGradient(QPointF(0, -105), 120)
        g.setColorAt(0, _cor(cor, 0.22 + 0.06 * math.sin(t * 2.2)))
        g.setColorAt(1, _cor(cor, 0.0))
        p.setPen(Qt.NoPen)
        p.setBrush(g)
        p.drawEllipse(QPointF(0, -105), 120, 120)

    def _extras(self, p: QPainter, ex: dict, t: float, q: dict) -> None:
        """Enfeites em unidades do personagem (pés em 0,0): ondas de voz, balão de pensar, zzz, notas, holograma, selo."""
        base = p.opacity()
        p.setPen(Qt.NoPen)
        if ex["ondas"] > 0.01:
            p.setOpacity(base * ex["ondas"])
            p.setBrush(_cor(VERDE))
            amp = ex["amp"]
            for i, (x, alt) in enumerate(((70, 26), (82, 40), (94, 22))):
                h = alt * (0.35 + 0.65 * (amp if self.pers.estado == "falando" else 0.5 + 0.5 * math.sin(t * 7 + i * 2)))
                p.drawRoundedRect(QRectF(x, -150 - h / 2, 6, h), 3, 3)
        if ex["pensando"] > 0.01:
            p.save()
            p.setOpacity(base * ex["pensando"])
            k = 0.4 + 0.6 * ex["pensando"]
            p.translate(-70, -218)
            p.scale(k, k)
            p.setBrush(_cor("#2A1F25"))
            p.setPen(QPen(_cor(COR_PENSANDO_TXT, 0.8), 2))
            p.drawRoundedRect(QRectF(-34, -18, 68, 32), 16, 16)
            p.drawEllipse(QPointF(24, 22), 5.5, 5)
            p.drawEllipse(QPointF(32, 32), 3.4, 3)
            p.setPen(Qt.NoPen)
            for i, x in enumerate((-16, 0, 16)):
                f = ((t - i * 0.15) / 1.1) % 1.0
                salto = -5 * (math.sin(math.pi * f / 0.6) if f < 0.6 else 0.0)
                p.setBrush(_cor(COR_PENSANDO_TXT, 0.55 + 0.45 * (salto / -5)))
                p.drawEllipse(QPointF(x, -2 + salto), 4.4, 4.4)
            p.restore()
        if ex["zzz"] > 0.01:
            p.setPen(_cor("#E7C6F0"))
            for i in range(3):
                f = ((t - i) / 3.0) % 1.0
                op = f / 0.25 if f < 0.25 else 1 - (f - 0.25) / 0.75
                p.setOpacity(base * ex["zzz"] * max(0.0, op))
                fonte = QFont(tema.FONTE)
                fonte.setPixelSize(int(18 + 8 * f))
                fonte.setWeight(QFont.ExtraBold)
                p.setFont(fonte)
                p.drawText(QPointF(64 + 12 * f, -178 - 40 * f), "z")
        if ex["notas"] > 0.01:
            p.setPen(_cor("#7DE3B8"))
            for i in range(3):
                f = ((t - i * 0.5) / 1.6) % 1.0
                p.setOpacity(base * ex["notas"] * (1 - f))
                fonte = QFont(tema.FONTE)
                fonte.setPixelSize(20)
                p.setFont(fonte)
                p.drawText(QPointF(64 + 10 * math.sin(f * 6 + i), -150 - 50 * f), "♪")
        if ex["holo"] > 0.01:
            p.setOpacity(base * ex["holo"])
            cor = ex["aura"] or "#5AD7FF"
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(_cor(cor, 0.85), 2))
            gira = t * 40
            for i, r in enumerate((26, 18)):
                p.save()
                p.translate(-86, -104)
                p.rotate(gira * (1 if i == 0 else -1.6))
                p.setPen(QPen(_cor(cor, 0.8), 2, Qt.DashLine))
                p.drawEllipse(QPointF(0, 0), r, r * 0.55)
                p.restore()
            p.setPen(Qt.NoPen)
            p.setBrush(_cor(cor, 0.16))
            p.drawRoundedRect(QRectF(-112, -134 + 3 * math.sin(t * 3), 52, 34), 6, 6)
        p.setOpacity(base)
        if q["selo"] > 0.01:
            p.save()
            p.setOpacity(base * q["selo"])
            pronto = q["selo_texto"] == "✓"
            p.translate(-56, -200)
            p.setBrush(_cor(VERDE if pronto else "#FF5C8A"))
            p.setPen(QPen(_cor(ESCURO), 3))
            p.drawEllipse(QPointF(0, 0), 13, 13)
            fonte = QFont(tema.FONTE)
            fonte.setPixelSize(15)
            fonte.setWeight(QFont.ExtraBold)
            p.setFont(fonte)
            p.setPen(_cor(ESCURO if pronto else "#FFFFFF"))
            p.drawText(QRectF(-13, -13, 26, 26), Qt.AlignCenter, q["selo_texto"][:2])
            p.restore()

    def _balao(self, p: QPainter) -> None:
        """Etiqueta de texto legível em cima do personagem (igual à do robô)."""
        texto = self.balao_texto
        fonte = QFont(tema.FONTE)
        fonte.setPixelSize(17)
        fonte.setWeight(QFont.DemiBold)
        p.setFont(fonte)
        m = QFontMetrics(fonte)
        pad_esq, pad_dir = 26, 14
        disponivel = self.largura - 2 * FOLGA - pad_esq - pad_dir
        if m.horizontalAdvance(texto) > disponivel:
            texto = m.elidedText(texto, Qt.ElideRight, disponivel)
        largura = max(70, min(self.largura - 2 * FOLGA, m.horizontalAdvance(texto) + pad_esq + pad_dir))
        altura = ALTURA_BALAO - 8
        x1, y1 = self.largura - FOLGA - largura, 6
        cor = CORES_BALAO.get(self.ciclo.base, VERDE)
        p.setPen(QPen(_cor(cor, 0.85), 1.4))
        p.setBrush(_cor(ESCURO, 0.92))
        p.drawRoundedRect(QRectF(x1, y1, largura, altura), altura / 2, altura / 2)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(cor))
        p.drawEllipse(QPointF(x1 + 14, y1 + altura / 2), 5, 5)
        p.setPen(QColor("#F5F5F7"))
        p.drawText(QRectF(x1 + pad_esq, y1, largura - pad_esq - 8, altura), Qt.AlignVCenter | Qt.AlignLeft, texto)

    def fechar(self) -> None:
        self._cfg_ativo = False


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
    parser.add_argument("--tipo", default="texto_avatar")
    args = parser.parse_args()
    if tema.testando():
        return 0   # teste automático: nada aparece na tela
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Assessor.Personagem")
    except Exception:
        pass
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv[:1])
    app.setQuitOnLastWindowClosed(False)
    janela = Personagem(args)
    codigo = app.exec()
    janela.fechar()
    del janela
    return codigo


if __name__ == "__main__":
    sys.exit(main())
