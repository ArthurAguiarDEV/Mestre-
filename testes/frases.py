"""Teste de vocabulario: muitas jeitos de pedir a mesma coisa -> qual comando atende.

    venv\\Scripts\\python -m testes.frases

Roda so em texto (nada abre de verdade). Cada linha: (frase falada, comando que deve atender).
"""
FRASES = [
    # --- ditar melhorias (projeto) ---
    ("Mestre, quero ditar melhorias", "_cmd_ditado"),
    ("Mestre, quero melhorar uma coisa no projeto", "_cmd_ditado"),
    ("Mestre, quero melhorar isso aqui no meu projeto", "_cmd_ditado"),
    ("Mestre, quero criar novas melhorias", "_cmd_ditado"),
    ("Mestre, tenho uma ideia pro projeto", "_cmd_ditado"),
    ("Mestre, tenho umas ideias pra você", "_cmd_ditado"),
    ("Mestre, tenho algumas sugestões de melhoria", "_cmd_ditado"),
    ("Mestre, bora anotar umas melhorias", "_cmd_ditado"),
    ("Mestre, quero passar umas melhorias", "_cmd_ditado"),
    ("Mestre, quero fazer uns ajustes no projeto", "_cmd_ditado"),
    ("Mestre, quero dar um feedback do projeto", "_cmd_ditado"),
    ("Mestre, vamos melhorar o Mestre", "_cmd_ditado"),
    ("Mestre, quero registrar melhorias", "_cmd_ditado"),
    ("Mestre, modo melhorias", "_cmd_ditado"),
    ("Mestre, vou ditar", "_cmd_ditado"),
    ("Mestre, vou falar um texto longo", "_cmd_ditado"),
    ("Mestre, lê minhas melhorias", "_cmd_melhorias"),
    ("Mestre, quais são as melhorias", "_cmd_melhorias"),
    ("Mestre, aplica as melhorias", "_cmd_melhorias"),
    # --- agente IPM ---
    ("Mestre, pergunta pro agente IPM como abrir um chamado", "_cmd_agente_ipm"),
    ("Mestre, abre o agente IPM", "_cmd_agente_ipm"),
    ("Mestre, ditado pro agente IPM", "_cmd_agente_ipm"),
    # --- projetos ---
    ("Mestre, quero começar um novo projeto", "_cmd_projeto"),
    ("Mestre, cria um projeto novo", "_cmd_projeto"),
    ("Mestre, bora iniciar um projeto", "_cmd_projeto"),
    ("Mestre, quais são os meus projetos", "_cmd_projeto"),
    # --- exportar o historico para o Claude ---
    ("Mestre, exporta o histórico", "_cmd_exportar"),
    ("Mestre, exporta o histórico de hoje", "_cmd_exportar"),
    ("Mestre, manda o histórico pro Claude", "_cmd_exportar"),
    ("Mestre, gera o relatório dos testes", "_cmd_exportar"),
    # --- historico e memoria ---
    ("Mestre, repete a resposta", "_cmd_historico"),
    ("Mestre, repete", "_cmd_historico"),
    ("Mestre, fala de novo", "_cmd_historico"),
    ("Mestre, qual foi a última resposta", "_cmd_historico"),
    ("Mestre, lê as últimas respostas", "_cmd_historico"),
    ("Mestre, o que você respondeu sobre relatividade", "_cmd_historico"),
    ("Mestre, lembra que eu trabalho de manhã", "_cmd_memoria"),
    ("Mestre, guarda que meu aniversário é em maio", "_cmd_memoria"),
    ("Mestre, o que você lembra de mim", "_cmd_memoria"),
    # --- musica ---
    ("Mestre, pausa", "_cmd_midia"),
    ("Mestre, pausa a música", "_cmd_midia"),
    ("Mestre, pausa o Spotify", "_cmd_midia"),
    ("Mestre, despausa", "_cmd_midia"),
    ("Mestre, continua a música", "_cmd_midia"),
    ("Mestre, volta a tocar", "_cmd_midia"),
    ("Mestre, próxima música", "_cmd_midia"),
    ("Mestre, pula essa", "_cmd_midia"),
    ("Mestre, próxima", "_cmd_midia"),
    ("Mestre, música anterior", "_cmd_midia"),
    ("Mestre, volta a música", "_cmd_midia"),
    ("Mestre, para a música", "_cmd_midia"),
    # --- saida de som (troca a caixinha/o fone) ---
    ("Mestre, coloca na caixinha de som", "_cmd_saida_som"),
    ("Mestre, ativa a caixinha", "_cmd_saida_som"),
    ("Mestre, joga o som pra caixinha", "_cmd_saida_som"),
    ("Mestre, troca pra caixinha", "_cmd_saida_som"),
    ("Mestre, volta pro fone", "_cmd_saida_som"),
    ("Mestre, coloca no fone", "_cmd_saida_som"),
    ("Mestre, agora tô usando o fone", "_cmd_saida_som"),
    ("Mestre, som no fone", "_cmd_saida_som"),
    ("Mestre, troca a saída de som", "_cmd_saida_som"),
    ("Mestre, qual saída de som tá ativa", "_cmd_saida_som"),
    ("Mestre, qual a saída de som", "_cmd_saida_som"),
    # armadilhas: volume continua sendo volume, não troca de dispositivo
    ("Mestre, abaixa o som", "_cmd_volume"),
    ("Mestre, aumenta o volume do fone", "_cmd_volume"),
    # --- volume ---
    ("Mestre, aumenta o volume", "_cmd_volume"),
    ("Mestre, diminui o volume", "_cmd_volume"),
    ("Mestre, sobe o volume um pouco", "_cmd_volume"),
    ("Mestre, volume no 30", "_cmd_volume"),
    ("Mestre, volume máximo", "_cmd_volume"),
    ("Mestre, muta", "_cmd_volume"),
    ("Mestre, tira do mudo", "_cmd_volume"),
    ("Mestre, aumenta o volume do Spotify", "_cmd_volume"),
    ("Mestre, diminui o Spotify", "_cmd_volume"),
    ("Mestre, abaixa o Spotify", "_cmd_volume"),
    ("Mestre, coloca o Spotify no máximo", "_cmd_volume"),
    ("Mestre, coloque no volume máximo do Spotify", "_cmd_volume"),
    ("Mestre, Spotify no 50", "_cmd_volume"),
    ("Mestre, muta o Spotify", "_cmd_volume"),
    ("Mestre, tira o som do Spotify", "_cmd_volume"),
    ("Mestre, volta o som do Spotify", "_cmd_volume"),
    ("Mestre, Spotify mais alto", "_cmd_volume"),
    ("Mestre, abaixa o áudio do navegador em 30%", "_cmd_volume"),
    ("Mestre, aumenta o Spotify pra 50", "_cmd_volume"),
    ("Mestre, muta o Brave", "_cmd_volume"),
    ("Mestre, volume do Chrome no 20", "_cmd_volume"),
    ("Mestre, abaixa o volume do navegador", "_cmd_volume"),
    ("Mestre, aumenta o volume do Edge", "_cmd_volume"),
    ("Mestre, coloca o navegador no máximo", "_cmd_volume"),
    ("Mestre, desmuta o Chrome", "_cmd_volume"),
    # armadilha: sem programa nenhum, continua sendo o volume geral
    ("Mestre, abaixa o volume", "_cmd_volume"),
    # --- spotify (abrir) ---
    ("Mestre, toca a playlist Foco no Spotify", "_cmd_spotify"),
    ("Mestre, toca Legião Urbana no Spotify", "_cmd_spotify"),
    ("Mestre, bota Coldplay no Spotify", "_cmd_spotify"),
    # --- janelas ---
    ("Mestre, fecha essa janela", "_cmd_janela"),
    ("Mestre, minimiza", "_cmd_janela"),
    ("Mestre, minimiza essa janela", "_cmd_janela"),
    ("Mestre, maximiza a janela", "_cmd_janela"),
    ("Mestre, minimiza tudo", "_cmd_janela"),
    ("Mestre, mostra a área de trabalho", "_cmd_janela"),
    ("Mestre, troca de janela", "_cmd_janela"),
    ("Mestre, nova aba", "_cmd_janela"),
    ("Mestre, abre uma nova aba", "_cmd_janela"),
    ("Mestre, fecha a aba", "_cmd_janela"),
    ("Mestre, reabre a aba", "_cmd_janela"),
    ("Mestre, volta a página", "_cmd_janela"),
    ("Mestre, página anterior", "_cmd_janela"),
    ("Mestre, atualiza a página", "_cmd_janela"),
    ("Mestre, recarrega", "_cmd_janela"),
    ("Mestre, rola pra baixo", "_cmd_janela"),
    ("Mestre, desce a página", "_cmd_janela"),
    ("Mestre, rola pra cima", "_cmd_janela"),
    ("Mestre, vai pro topo", "_cmd_janela"),
    ("Mestre, aumenta o zoom", "_cmd_janela"),
    ("Mestre, diminui o zoom", "_cmd_janela"),
    ("Mestre, tira um print", "_cmd_janela"),
    ("Mestre, joga essa janela pro monitor 2", "_cmd_mover"),
    ("Mestre, manda essa janela pro monitor secundário", "_cmd_mover"),
    ("Mestre, leva essa janela pra tela 3", "_cmd_mover"),
    ("Mestre, vai para a próxima página", "_cmd_janela"),
    ("Mestre, volta pra página anterior", "_cmd_janela"),
    ("Mestre, avança a página", "_cmd_janela"),
    ("Mestre, próxima aba", "_cmd_janela"),
    ("Mestre, vai pra próxima aba", "_cmd_janela"),
    ("Mestre, aba anterior", "_cmd_janela"),
    ("Mestre, volta uma aba", "_cmd_janela"),
    # --- janelas e abas pelo nome (monitores) ---
    ("Mestre, joga a Netflix pro monitor 3", "_cmd_mover"),
    ("Mestre, manda o Spotify pro monitor secundário", "_cmd_mover"),
    ("Mestre, leva o YouTube pro terciário", "_cmd_mover"),
    ("Mestre, passa a janela da Netflix pra tela 2", "_cmd_mover"),
    ("Mestre, separa a Netflix pro monitor 2 e deixa o YouTube no principal", "_cmd_mover"),
    ("Mestre, quero que você jogue a Netflix desse navegador para o monitor 2 e o YouTube deixe no meu principal",
     "_cmd_mover"),
    ("Mestre, coloca o Spotify no monitor principal", "_cmd_mover"),
    # --- mover janela: sem preposição antes do "monitor" (fala corrida) ---
    ("Mestre, joga o YouTube monitor 2", "_cmd_mover"),
    ("Mestre, mover YouTube monitor 2", "_cmd_mover"),
    ("Mestre, transfere a janela do YouTube pro monitor secundário", "_cmd_mover"),
    ("Mestre, transfere a tela do YouTube para o segundo monitor", "_cmd_mover"),
    ("Mestre, passa a janela do YouTube pro monitor secundário", "_cmd_mover"),
    # --- mover janela: "segundo/terceiro monitor" (o número/nome vem ANTES da palavra monitor) ---
    ("Mestre, joga o YouTube pro segundo monitor", "_cmd_mover"),
    ("Mestre, manda a Netflix pro terceiro monitor", "_cmd_mover"),
    # --- armadilha: "abre" com monitor continua ABRINDO, não movendo ---
    ("Mestre, abre o YouTube no monitor 2", "_cmd_youtube"),
    ("Mestre, abre a Netflix no monitor 3", "_cmd_abrir"),
    # --- YouTube (controle) ---
    ("Mestre, tela cheia", "_cmd_youtube_controle"),
    ("Mestre, coloca em tela cheia", "_cmd_youtube_controle"),
    ("Mestre, deixa em tela cheia", "_cmd_youtube_controle"),
    ("Mestre, sai da tela cheia", "_cmd_youtube_controle"),
    ("Mestre, tira da tela cheia", "_cmd_youtube_controle"),
    ("Mestre, tela cheia com chat", "_cmd_youtube_controle"),
    ("Mestre, modo cinema", "_cmd_youtube_controle"),
    ("Mestre, liga a legenda", "_cmd_youtube_controle"),
    ("Mestre, dá um like", "_cmd_youtube_controle"),
    ("Mestre, dá like", "_cmd_youtube_controle"),
    ("Mestre, curte esse vídeo", "_cmd_youtube_controle"),
    ("Mestre, deixa um gostei", "_cmd_youtube_controle"),
    ("Mestre, se inscreve no canal", "_cmd_youtube_controle"),
    ("Mestre, inscreve", "_cmd_youtube_controle"),
    ("Mestre, fecha o chat", "_cmd_youtube_controle"),
    ("Mestre, esconde o chat", "_cmd_youtube_controle"),
    ("Mestre, abre o chat", "_cmd_youtube_controle"),
    ("Mestre, lê os títulos", "_cmd_youtube_controle"),
    ("Mestre, quais são os vídeos", "_cmd_youtube_controle"),
    ("Mestre, abre o terceiro vídeo", "_cmd_youtube_controle"),
    ("Mestre, clica no segundo vídeo", "_cmd_youtube_controle"),
    ("Mestre, abre o primeiro resultado", "_cmd_youtube_controle"),
    ("Mestre, quero o quarto vídeo", "_cmd_youtube_controle"),
    ("Mestre, abre o vídeo do Manual do Mundo", "_cmd_youtube"),   # (YouTube fechado: último vídeo do canal)
    ("Mestre, avança 30 segundos", "_cmd_youtube_controle"),
    ("Mestre, volta 10 segundos", "_cmd_youtube_controle"),
    ("Mestre, avança 2 minutos", "_cmd_youtube_controle"),
    ("Mestre, próximo vídeo", "_cmd_youtube_controle"),
    ("Mestre, vai pro próximo vídeo", "_cmd_youtube_controle"),
    ("Mestre, pula esse vídeo", "_cmd_youtube_controle"),
    ("Mestre, vídeo anterior", "_cmd_youtube_controle"),
    ("Mestre, pausa o vídeo", "_cmd_youtube_controle"),
    ("Mestre, para o vídeo", "_cmd_youtube_controle"),
    ("Mestre, continua o vídeo", "_cmd_youtube_controle"),
    ("Mestre, despausa o vídeo", "_cmd_youtube_controle"),
    ("Mestre, dá play no vídeo", "_cmd_youtube_controle"),
    ("Mestre, vai pras inscrições", "_cmd_youtube_controle"),
    ("Mestre, abre o assistir mais tarde", "_cmd_youtube_controle"),
    ("Mestre, abre os shorts", "_cmd_youtube_controle"),
    ("Mestre, abre o histórico do YouTube", "_cmd_youtube_controle"),
    ("Mestre, mostra os vídeos que eu gostei", "_cmd_youtube_controle"),
    ("Mestre, próximo", "_cmd_midia"),
    # --- YouTube (abrir) ---
    ("Mestre, abre o YouTube", "_cmd_youtube"),
    ("Mestre, abre o último vídeo do Manual do Mundo", "_cmd_youtube"),
    ("Mestre, pesquisa receita de pão no YouTube", "_cmd_youtube"),
    ("Mestre, toca Legião Urbana no YouTube", "_cmd_youtube"),
    ("Mestre, abre o canal Manual do Mundo", "_cmd_youtube"),
    ("Mestre, abre o YouTube no monitor 2", "_cmd_youtube"),
    # --- sites e programas ---
    ("Mestre, abre a Netflix", "_cmd_abrir"),
    ("Mestre, abre o ChatGPT", "_cmd_abrir"),
    ("Mestre, abre o Gemini", "_cmd_abrir"),
    ("Mestre, abre o Mercado Livre", "_cmd_abrir"),
    ("Mestre, abre a Shopee", "_cmd_abrir"),
    ("Mestre, abre o TikTok", "_cmd_abrir"),
    ("Mestre, abre a Twitch", "_cmd_abrir"),
    ("Mestre, abre o Prime Video", "_cmd_abrir"),
    ("Mestre, abre a Disney", "_cmd_abrir"),
    ("Mestre, abre o Gmail", "_cmd_abrir"),
    ("Mestre, entra no Perplexity", "_cmd_abrir"),
    ("Mestre, abre a calculadora", "_cmd_abrir"),
    ("Mestre, abre a Netflix no monitor 3", "_cmd_abrir"),
    ("Mestre, abre o ChatGPT no monitor terciário", "_cmd_abrir"),
    # --- armadilhas: NAO podem virar ditado de melhorias ---
    ("Mestre, quero uma sugestão de filme", None),
    ("Mestre, me dá uma ideia de receita", None),
    ("Mestre, anota uma melhoria deixar o painel azul com letras maiores", "_cmd_melhorias"),
    # --- frases reais do historico exportado (25/09) ---
    ("Meu Mestre, coloque em tela cheia", "_cmd_youtube_controle"),
    ("Fala, meu Mestre. Abre o canal do FRTT.", "_cmd_youtube"),
    ("Mestre, pesquise pelo canal FRTT", "_cmd_youtube"),
    ("Mestre, e aí", "_cmd_conversinha"),
    ("E aí, meu Mestre, tá por aí?", "_cmd_conversinha"),
    ("Mestre, tchau tchau", "_cmd_conversinha"),
    ("Mestre, bye", "_cmd_conversinha"),
    ("Mestre, descansar", "_cmd_descanso"),
    ("Mestre, pode descansar", "_cmd_descanso"),
    ("Mestre, fica quieto", "_cmd_descanso"),
    ("Mestre, modo descanso", "_cmd_descanso"),
    ("Mestre, volte na página anterior", "_cmd_janela"),
    ("Mestre, se inscreva nesse canal", "_cmd_youtube_controle"),
    ("Mestre, pause Spotify", "_cmd_midia"),
    ("Mestre, pula essa música do Spotify", "_cmd_midia"),
    ("Mestre, continua Spotify", "_cmd_midia"),
    ("Mestre, multa o Spotify", "_cmd_volume"),
    ("Mestre, diminui o Spotify em 20%", "_cmd_volume"),
    ("Mestre, tirar o vídeo do YouTube do mudo", "_cmd_volume"),
    ("Mestre, aumentar o volume do YouTube", "_cmd_volume"),
    ("Mestre, abre a Netflix na janela principal", "_cmd_abrir"),
    ("Mestre, o segundo vídeo da janela", "_cmd_youtube_controle"),
    ("Mestre, selecione o primeiro vídeo com o nome I hate how much I love Jumanji", "_cmd_youtube_controle"),
    ("Mestre, tocar os terceiros vídeos dessa lista", "_cmd_youtube_controle"),
    ("Mestre, selecione o canal do primeiro vídeo", "_cmd_youtube_controle"),
    ("Mestre, reproduz o último vídeo desse canal", "_cmd_youtube"),
    ("Mestre, tocar Feliz do DJ Petroski", "_cmd_tocar"),
    ("Mestre, toca Agentes da Shield na Disney", "_cmd_streaming"),
    ("Mestre, reproduzir na Disney aberta na janela principal o seriado Agentes da Shield", "_cmd_streaming"),
    ("Mestre, quero continuar assistindo a série Agentes da Shield", "_cmd_streaming"),
    ("Mestre, assiste Stranger Things na Netflix", "_cmd_streaming"),
    ("Mestre, junta o YouTube com a Disney", "_cmd_juntar"),
    ("Mestre, juntar a janela do HBO Max com a do Disney", "_cmd_juntar"),
    ("Mestre, traz o YouTube pra janela da Disney", "_cmd_juntar"),
    ("Mestre, junta todas as janelas no principal", "_cmd_juntar"),
    ("Mestre, manda o Spotify pra janela principal", "_cmd_mover"),
    ("Mestre, clica em continuar assistindo", "_cmd_clicar"),
    # --- outros ---
    ("Mestre, que horas são", "_cmd_hora_data"),
    ("Mestre, que dia é hoje", "_cmd_hora_data"),
    ("Mestre, bora trabalhar", "_cmd_rotinas"),
    ("Mestre, bom dia", "_cmd_rotinas"),
    # --- ensinar uma rotina falando ---
    ("Mestre, vou te mostrar uma nova rotina", "_cmd_ensinar_rotina"),
    ("Mestre, grava uma rotina", "_cmd_ensinar_rotina"),
    ("Mestre, aprende uma rotina nova", "_cmd_ensinar_rotina"),
    ("Mestre, quero te ensinar uma rotina", "_cmd_ensinar_rotina"),
    ("Mestre, vamos criar uma rotina", "_cmd_ensinar_rotina"),
    ("Mestre, desliga a tela", "_cmd_tela"),
    ("Mestre, bloqueia o computador", "_cmd_tela"),
    ("Mestre, isso tá errado, era outra coisa", "_cmd_feedback"),
    ("Mestre, valeu", "_cmd_obrigado"),
    ("Mestre, abre o painel", "_cmd_painel"),
    ("Mestre, me lembra de beber água em 10 minutos", "_cmd_lembrete"),
    ("Mestre, anota comprar pão", "_cmd_notas"),
    # --- v13: desligar sem dizer o nome; escolher a tela; clicar ---
    ("Mestre, qual é a sua versão?", "_cmd_versao"),
    ("Mestre, em que versão você está", "_cmd_versao"),
    ("Mestre, desliga", "_cmd_encerrar"),
    ("Mestre, pode desligar", "_cmd_encerrar"),
    ("Mestre, pode se desligar", "_cmd_encerrar"),
    ("Mestre, desliga o Mestre", "_cmd_encerrar"),
    ("Mestre, encerra por hoje", "_cmd_encerrar"),
    ("Mestre, desliga a tela", "_cmd_tela"),
    ("Mestre, desliga o PC", "_cmd_desligar_pc"),
    ("Mestre, abre o segundo vídeo do monitor 2", "_cmd_youtube_controle"),
    ("Mestre, o terceiro vídeo da tela 2", "_cmd_youtube_controle"),
    ("Mestre, pausa o vídeo do monitor 2", "_cmd_youtube_controle"),
    ("Mestre, abre o vídeo com o nome Como seria o GTA 6 no monitor 2", "_cmd_youtube_controle"),
    ("Mestre, clica em continuar assistindo do monitor 3", "_cmd_clicar"),
    # --- v25: novidades do Telegram (print, o que tá tocando) pedidas falando no PC ---
    ("Mestre, manda um print no Telegram", "_cmd_print_telegram"),
    ("Mestre, manda um print da tela pro Telegram", "_cmd_print_telegram"),
    ("Mestre, o que tá tocando", "_cmd_tocando"),
    ("Mestre, o que está tocando agora", "_cmd_tocando"),
]


def main() -> int:
    import logging
    import os
    import shutil
    import sys
    import tempfile
    from pathlib import Path

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # aceita acento sem PYTHONIOENCODING
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ["MESTRE_SIMULAR"] = "1"
    logging.basicConfig(level=logging.ERROR)
    projeto = Path(__file__).resolve().parent.parent
    pasta = Path(tempfile.mkdtemp(prefix="mestre_frases_")) / "mestre"
    shutil.copytree(projeto, pasta, ignore=shutil.ignore_patterns("venv", "modelos", "logs", "*.zip", "__pycache__",
                                                                   "memoria", "navegador_mestre"))
    (pasta / "logs").mkdir(exist_ok=True)
    sys.path.insert(0, str(pasta))
    for mod in [m for m in sys.modules if m == "app" or m.startswith("app.")]:
        del sys.modules[mod]
    from app import configuracao, sistema
    from app.config import carregar_config, palavras_ativacao
    from app.comandos import Executor
    from app.texto import extrair_comando
    from app.vocabulario import Vocabulario
    from app.voz import Voz
    configuracao.migrar()
    cfg = carregar_config()
    # As frases de teste começam com "Mestre": não depender da palavra que o usuário escolheu
    cfg.setdefault("assistente", {})["palavra_ativacao"] = "mestre"
    cfg["rotinas"] = list(cfg.get("rotinas") or []) + [{"nome": "Bom dia", "frases": ["bom dia"], "acoes": []}]
    cfg["canais_youtube"] = {"Manual do Mundo": "@manualdomundo"}
    cfg["spotify"] = {"playlists": {"Foco": "https://open.spotify.com/playlist/x"}, "apertar_play": False}
    for nome in ("abrir_site", "abrir_programa", "abrir_arquivo", "midia", "volume", "volume_do_pc", "atalho",
                 "janela_ativa", "tirar_print", "mover_janela_para_monitor", "desligar_tela", "bloquear",
                 "abrir_terminal_com", "copiar", "colar_e_enviar", "acordar_tela", "tecla_letra", "abrir_revisao_ditado",
                 "abrir_painel", "reiniciar_mestre", "parar_mestre", "iniciar_mestre", "play_pause"):
        setattr(sistema, nome, lambda *a, **k: True)
    sistema.volume_do_programa = lambda *a, **k: ""

    class SemIA:
        ligado = False

        def esquecer(self):
            pass

    ex = Executor(cfg, Voz(cfg, mudo=True), SemIA(), Vocabulario())
    ex._yt = lambda: None
    variacoes = palavras_ativacao(cfg)
    falhas = []
    for frase, esperado in FRASES:
        ex._pendente, ex._ditado_ativo, ex.ultimo_comando, ex._descansando = None, False, None, False
        ex._gravacao = None
        achou, comando = extrair_comando(frase, variacoes)
        try:
            ex.executar(comando if achou else frase, frase)
        except Exception as erro:
            falhas.append((frase, esperado, f"ERRO {erro}"))
            continue
        if ex.ultimo_comando != esperado:
            falhas.append((frase, esperado, ex.ultimo_comando))
    print(f"\nVOCABULARIO: {len(FRASES) - len(falhas)} de {len(FRASES)} frases foram para o comando certo.")
    for frase, esperado, veio in falhas:
        print(f"  FALHOU  {frase!r}: esperado {esperado}, veio {veio}")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
