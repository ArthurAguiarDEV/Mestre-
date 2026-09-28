"""Ponto de partida do Mestre.

  python -m app.main               -> modo voz (normal), com o indicador na tela
  python -m app.main --texto       -> digita os comandos (bom para testar)
  python -m app.main --microfones  -> lista os microfones
  python -m app.main --sem-indicador -> modo voz sem o indicador na tela
  python -m app.main --comando "bora trabalhar" -> executa UM comando e sai (botao "Testar" das rotinas)
"""
import argparse
import logging
import os

import threading
import time

from . import estado, sistema
from .cerebro import Cerebro
from .comandos import Executor
from .config import PASTA_PROJETO, carregar_config, configurar_log, palavras_ativacao
from .texto import extrair_comando
from .vocabulario import Vocabulario
from .voz import Voz

log = logging.getLogger("mestre")
ARQUIVO_PID = PASTA_PROJETO / "mestre.pid"


def modo_texto(executor: Executor, variacoes: list[str]) -> None:
    print("\nMODO TEXTO: digite o que voce falaria (ex.: 'e ai mestre, que horas sao?').")
    print("Pode digitar com ou sem a palavra 'mestre'. Para sair, digite: sair\n")
    while executor.rodando:
        try:
            frase = input("VOCE: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if frase.lower() in ("sair", "exit", "quit"):
            break
        achou, comando = extrair_comando(frase, variacoes)
        segundos = executor.executar(comando if achou else frase, frase)
        if segundos and executor._pendente:
            print("   (o Mestre esta esperando sua resposta; pode digitar sem 'mestre')")


def escutar(cfg: dict, voz: Voz, executor: Executor) -> None:
    from .ouvido import Ouvido

    try:
        # Cumprimenta NA HORA; o ouvido (Whisper) carrega enquanto isso
        estado.definir("iniciando", "carregando o ouvido...")
        # A IA (Ollama) demora so na primeira pergunta: carrega o modelo ja, em segundo plano
        threading.Thread(target=executor.cerebro.aquecer, daemon=True).start()
        voz.falar_em_segundo_plano(executor.sortear("inicio"))
        ouvido = Ouvido(cfg, voz)
        from .recebidos import Caixa   # audios do celular (pasta sincronizada e Telegram)
        executor.caixa = Caixa(cfg, executor, ouvido.transcritor)
        executor.caixa.iniciar()
        voz.aquecer(executor.todas_as_falas())  # falas fixas ficam prontas (saem na hora)
        from . import voz_kokoro
        if voz.motor == "kokoro" and voz_kokoro.biblioteca_instalada() and not voz_kokoro.baixado():
            def baixar_kokoro():   # primeira vez: baixa a voz nova (enquanto isso fala com a Edge)
                if not voz_kokoro.baixar():
                    voz.aquecer(executor.todas_as_falas())
            threading.Thread(target=baixar_kokoro, daemon=True).start()
        ouvido.escutar_para_sempre(executor.executar, lambda: executor.rodando)
    except Exception:
        log.exception("O Mestre parou por causa de um erro")
        estado.definir("pausado", "erro: veja logs/mestre.log")
        executor.rodando = False


def main() -> None:
    parser = argparse.ArgumentParser(description="Mestre - assistente pessoal por voz")
    parser.add_argument("--texto", action="store_true", help="digitar em vez de falar")
    parser.add_argument("--mudo", action="store_true", help="nao falar em voz alta")
    parser.add_argument("--microfones", action="store_true", help="listar microfones e sair")
    parser.add_argument("--sem-indicador", action="store_true", help="nao mostrar o indicador na tela")
    parser.add_argument("--comando", help="executa um comando (como se tivesse falado) e sai")
    args = parser.parse_args()

    if args.microfones:
        from .ouvido import imprimir_microfones
        imprimir_microfones()
        return

    configurar_log()
    try:   # novidades de versao entram no config UMA vez (ex.: sites padrao)
        from . import configuracao
        configuracao.migrar()
    except Exception:
        log.exception("Migracao do config falhou (seguindo mesmo assim)")
    cfg = carregar_config()
    variacoes = palavras_ativacao(cfg)
    voz = Voz(cfg, mudo=args.mudo)
    executor = Executor(cfg, voz, Cerebro(cfg), Vocabulario())

    if args.texto:
        modo_texto(executor, variacoes)
        return
    if args.comando:
        achou, comando = extrair_comando(args.comando, variacoes)
        executor.executar(comando if achou else args.comando, args.comando)
        os._exit(0)

    ARQUIVO_PID.write_text(str(os.getpid()))
    estado.pausar(False)

    def vigiar_desligar():   # "desliga": o indicador fecha sozinho; se algo segurar (microfone, rede), sai assim mesmo
        while executor.rodando:
            time.sleep(0.2)
        time.sleep(1.5)
        log.info("Desligando (saida garantida)")
        if ARQUIVO_PID.exists() and ARQUIVO_PID.read_text().strip() == str(os.getpid()):
            ARQUIVO_PID.unlink()
        os._exit(0)
    threading.Thread(target=vigiar_desligar, daemon=True).start()
    from .ponte import Ponte
    executor.ponte = Ponte()   # a extensao do Brave conversa com o Mestre por aqui (abas, janelas e YouTube)
    executor.ponte.iniciar()
    try:   # "Sugestões de melhoria": 1x por dia (sugestoes > hora), so gera a lista em memoria/sugestoes.json
        from . import sugestoes
        sugestoes.iniciar_agendador(cfg, executor.cerebro, lambda: executor.rodando)
    except Exception:
        log.exception("Nao consegui ligar as sugestoes de melhoria (seguindo mesmo assim)")
    from . import bandeja

    icone = bandeja.iniciar(sistema.abrir_painel, sistema.reiniciar_mestre,
                            lambda: setattr(executor, "rodando", False),
                            (cfg.get("assistente") or {}).get("nome") or "Mestre")
    try:
        mostrar = not args.sem_indicador and (cfg.get("indicador") or {}).get("mostrar", True)
        if mostrar:
            # A escuta roda em segundo plano; o indicador fica na "linha principal" (exigencia do Windows)
            threading.Thread(target=escutar, args=(cfg, voz, executor), daemon=True).start()
            import tkinter as tk
            from .overlay import Indicador

            raiz = tk.Tk()
            raiz.title("Mestre")
            Indicador(raiz, executor, sistema.abrir_painel, sistema.reiniciar_mestre)
            raiz.mainloop()
            executor.rodando = False
        else:
            escutar(cfg, voz, executor)
    except KeyboardInterrupt:
        pass
    finally:
        if icone:
            try:
                icone.stop()
            except Exception:
                pass
        # So apaga se o arquivo ainda for deste processo (ao reiniciar, o novo ja escreveu o dele)
        if ARQUIVO_PID.exists() and ARQUIVO_PID.read_text().strip() == str(os.getpid()):
            ARQUIVO_PID.unlink()
        log.info("Mestre encerrado.")
    os._exit(0)  # encerra tambem timers de lembrete pendentes


if __name__ == "__main__":
    main()
