# Projeto Mestre: instruções para o Claude Code

Assistente pessoal por voz para Windows, em Python 3.12. O dono **não é programador**:
fale com ele em português simples, explique o que mudou e o que ele precisa testar.

## Como o código está organizado

| Arquivo | O que faz |
|---|---|
| `app/main.py` | Início. `--texto` (digitar em vez de falar), `--mudo`, `--microfones` |
| `app/ouvido.py` | Laço do microfone (`_laco`/`_bloco`/`_frase`/`_tratar`, testável com blocos sintéticos): corta frases, checa "mestre", "mestre" sozinho espera o resto (`espera_apos_palavra`), frase pela metade espera a continuação (`espera_continuacao`, `termina_no_meio`), janela de conversa (congelada enquanto ele fala), descartes vão ao ouvido.jsonl com `motivo`. Blocos com eco (ele falando) vão a um 2º segmentador (`_bloco_eco`/`_frase_eco`): só vale frase que COMEÇA com a palavra; ela chama `voz.parar()` ("…, para" só para); o resto é descartado com motivo "falando". Detector local opcional (`_escutar_palavra`/`_filtrar_pelo_detector`): fora de conversa/espera/ditado/descanso, frase sem a palavra nem vai ao Whisper (motivo "sem a palavra (detector local)") |
| `app/palavra_local.py` | Detector local da palavra (`ouvido > detector_palavra`, padrão desligado; `detector_limiar` 0.5): features do openWakeWord (melspectrogram/embedding .onnx, Apache-2.0, em `modelos/palavra/`) reimplementadas com onnxruntime (`Caracteristicas`) + rede numpy `modelos/palavra/<palavra>.npz` (`Classificador`); `situacao()` p/ o painel. Treino: `ferramentas/treinar_palavra.py` (`15_treinar_palavra.bat`) |
| `app/audio.py` | Segmentador (limite de volume), ganho, normalização, Transcritor (faster-whisper, `aquecer()` ao ligar; `TRANSCREVENDO`/`esperar_whisper`: a voz natural não gera enquanto ele transcreve), diagnóstico |
| `app/locutor.py` | "Responder só à minha voz": SpeechBrain ECAPA (`modelos/locutor_ecapa`, carrega em segundo plano), impressão em `%APPDATA%\Mestre\voz_dono.json`; `Ouvido._voz_do_dono` confere antes de executar (celular/Telegram não passa por ela) |
| `app/validacao.py` | "Validar atualização" (painel > Sistema): lê `ROTEIRO_VALIDACAO.md`, casa OUVI/ENTENDI/FIZ pelo `ts` do histórico, gera relatório em `exportacoes/validacao_*.md` e FEEDBACK no MELHORIAS.md; `ultimo_relatorio()`; modo contínuo: `avaliar_continuo` (✅ avança sozinho, ❌ para com os `motivo` de descarte) |
| `app/sugestoes.py` | "Sugestões de melhoria" (painel > Sistema): 1x por dia (`sugestoes > hora`, padrão 08:00; `Agendador` numa thread do Assessor) analisa historico/ouvido.jsonl e grava `memoria/sugestoes.json` (não muda nada); o painel manda as marcadas ao Claude pelo fluxo da validação. Sugestões tipo "palavra" (Whisper escreveu a palavra de ativação errado) têm botão "Aplicar"/"Aplicar marcadas": grava o sinônimo em `aprendido.yaml` sem IA (`Vocabulario.aplicar_sinonimo`, `app/vocabulario.py`) E acrescenta a grafia em `config.yaml > assistente > variacoes_aceitas` (`configuracao.adicionar_variacao_aceita`, mesma lista que `app/ouvido.py` usa pra "acordar"), com confirmação antes, recusa trocas que quebrariam comando e some da lista (histórico p/ "Desfazer" em `sugestoes.marcar_aplicada`/`desfazer_ultima_aplicacao`, que desfaz nos dois arquivos) |
| `app/estado.py` | O que o Mestre está fazendo agora (ouvindo/gravando/...) + pausa por arquivo. Publica o essencial (só quando muda) em `logs/estado_agora.json` (`ler_de_fora`, `situacao`: o painel roda em outro processo) |
| `app/overlay.py` | "Bolinha" (tkinter, `indicador > tipo: bolinha`, ou reserva se o avatar falhar), roda na linha principal; a escuta roda numa thread |
| `app/avatar.py` + `app/avatar_janela.py` | Indicador padrão ("texto_avatar", `avatar.TIPOS`): robô animado (PySide6) num PROCESSO SEPARADO + balão de texto legível em cima ("Ouvindo…", "Pensando: <resumo>", "Falando…"...), robô ~35% menor com o balão ativo (`avatar.ESCALA_ROBO_BALAO`); opções "avatar" (só o robô) e "bolinha" no painel > Aparência. `avatar.iniciar`/`acompanhar` em `main._mostrar_avatar`; erro/sem PySide6 = bolinha; nada com MESTRE_SIMULAR. `avatar.py` sem Qt: `visual()` estado→animação, `texto_balao()` estado→texto do balão (testável sem Qt), `Animador` (quadros, `fps()` 0/20/30/60), `posicao_padrao`/`tamanho_janela` (acima do relógio, maior no modo com balão), posição em `%APPDATA%\Mestre\avatar.json`, volume da fala por UDP 127.0.0.1:47634 (`voz._tocar` → `enviar_nivel`). A janela lê `logs/estado_agora.json` só quando muda e fecha com o Assessor (`--pai`) |
| `app/painel.py` | Central + painel (customtkinter). Menu compacto só com ícones (`GRUPOS_MENU`/`PAGINAS`, ícone = nome em `app/icones.py`): `_rail` abre por cima do conteúdo com o mouse (animação só de largura), `Dica` = balão. Páginas **sob demanda** (`_garantir_pagina`, `self._montadas`; teste usa `montar_todas()`); trocar = `lift()` (nada é recriado). Salvar: cada página tem `_salvar_<página>` em `SALVAR_PAGINA` e só grava se já foi montada (rotinas sempre mesclam com o disco). Início em cartões: status/fila/últimos comandos lidos numa thread (`_coletar_inicio`) e aplicados a cada 1 s com `_por()` (só reconfigura o que mudou). Voz em abas (`_voz_campos_<motor>`, `_escolher_motor`, `_usar_reserva`). Seção = `secao(pagina, "Título", "dica")` (títulos em `RECOLHIDAS` começam fechados). `TabelaChaveValor`: páginas de 40 (◀ ▶) + busca ao digitar; aguenta milhares. Página "Tempos" (`_aba_tempos`, grupo SISTEMA): média/pior caso das últimas 50 medidas por etapa (`memoria.tempos_resumo`), lida numa thread (`_tempos_atualizar`/`_tempos_coletar_fundo`) + botão "Atualizar"; nunca trava o painel |
| `app/icones.py` | Ícones de linha desenhados com Pillow na hora (grade 24, desenha 8x e o CTkImage reduz: nítido em 125/150%); `ctk_icone(nome, cor, tam)`; `logo()` = logo "Onda" do menu; `avatar()` = rosto parado do Início |
| `app/versao.py` | `VERSAO` do projeto com ponto ("2.5", "2.6"...; suba a cada zip). O painel mostra; `atualizar.versao_atual()` lê do arquivo (texto, nunca compara como número) |
| `app/central.py` | O que o atalho "Mestre" abre: liga o Mestre (opcional) e abre o painel (uma janela só) |
| `app/iniciar_painel.py` | Abre o painel mostrando erros; porta 47631 traz para frente um painel já aberto |
| `app/bandeja.py` | Ícone perto do relógio (pystray): abrir painel, pausar, reiniciar, desligar |
| `app/atualizar.py` | Atualização por .zip (botão na Central): nunca toca config/aprendido/MELHORIAS/notas; lê OBSOLETOS.txt |
| `app/configuracao.py` | Lê/salva o config.yaml com ruamel.yaml, preservando comentários; textos sempre entre aspas |
| `app/personalidades.py` | Estilos prontos (descrição + frases por situação). Placeholders {apelido} {nome} {saudacao} |
| `app/tema.py` | Cores e fonte (config > aparencia; painel > Aparência); tema do customtkinter; logo "Onda" (`desenhar_icone`, simples até 40 px; `salvar_icones` = icone.png + icone.ico 16–256) na cor escolhida |
| `app/memoria.py` | Histórico (memoria/historico.jsonl), fatos "lembra que…" por assunto (memoria/fatos/`<assunto>`.md + `INDICE.md`; classifica por palavra-chave, migra sozinho o antigo `memoria/fatos.md` com backup em `fatos.md.antes_da_migracao`) e conversa da IA. `registrar_tempo(etapa, segundos)`/`tempos_resumo(n)`: quanto cada etapa demora (memoria/tempos.jsonl), pro painel > Sistema > Tempos; nunca pesa (só grava, `except` engole erro). Etapas gravadas hoje: `fala_para_texto` (Whisper, em `ouvido.py`), `frase_para_comando` (`comandos/__init__.py`), `ia_<id>` (um por provedor, em `cerebro.py._tentar_opcoes`) e `ate_falar` (1ª parte da voz, em `voz.py._falar_por_partes`) |
| `app/projetos.py` | Projetos guiados: pasta + PLANO.md, 3 caminhos da IA (`Cerebro.propor_opcoes`), anotações |
| `app/navegador.py` | Edge/Chrome controlado (Playwright, perfil `navegador_mestre/`) + ações do YouTube (like, chat, resultados) |
| `app/ponte.py` + `extensao_brave/` | Extensão do Brave (MV3, versão em `ponte.VERSAO_EXTENSAO` = manifest) ↔ Mestre por 127.0.0.1:47632: abas e janelas (listar, focar, separar, juntar, ir, voltar/avançar, trocar aba, clicar pelo texto) e YouTube (like, chat, resultados com canal, próximo, pausar, volume, retrato) |
| `app/exportar.py` | "Exportar para o Claude": `exportacoes/historico_para_claude_*.md` a partir de `memoria/historico.jsonl` (com `rota`/`entendi`) e `memoria/ouvido.jsonl` (tudo que o microfone transcreveu) |
| `app/revisar_ditado.py` | Janelinha do fim do ditado (processo separado), conversa com o Mestre por `logs/ditado_revisao.json` |
| `app/informacoes.py` | Clima (wttr.in) e notícias (Google Notícias RSS), grátis e sem cadastro. `o_que_esta_tocando(executor)`: Spotify (título da janela), abas do YouTube (`executor._abas_abertas`) e a janela ativa de cada monitor — usado pelo `_cmd_tocando` e pelo Telegram |
| `app/vocabulario.py` | Traduz fala solta para a forma oficial usando `vocabulario.yaml` + `aprendido.yaml` |
| `app/comandos/` | Pacote do `Executor` (`from app.comandos import Executor`): cada comando é um método `_cmd_*` listado em `Executor.ORDEM`, num mixin por assunto (a classe herda de todos) |
| `app/comandos/__init__.py` (~390) | NÚCLEO: `Executor.__init__`, `ORDEM`, `executar`/`_executar`, `_tentar_comandos`, `_separar_monitor`/`_nomes_monitores`, `preencher`/`falar`/`perguntar`, `_pedido_puro`, `_original`, `_responder`; `saudacao_do_horario` |
| `app/comandos/base.py` (~120) | Constantes (`ARQUIVO_MELHORIAS`, `PROMPT_MELHORIAS`, `LINK_PROJETO_PADRAO`, regex de ditado/rotina...) e funções pequenas (`link_spotify`, `_nome_do_canal`, `_host`...), reexportadas pelo `__init__` |
| `app/comandos/ia.py` (~355) | IA: `_interpretar_com_ia`, memória de comandos da IA, `_pensar`, fila (`_trabalhar_fila_ia`), `entregar_pensamento`, `_cmd_pensamento`, `_cmd_esquecer` |
| `app/comandos/rotinas.py` (~360) | Rotinas do config (`_cmd_rotinas`, `_executar_acao`) e ensinar rotina falando (`_cmd_ensinar_rotina`, gravação, frase de chamar) |
| `app/comandos/assistente.py` (~235) | O próprio assistente: versão, encerrar, reiniciar, painel, ajuda, descanso, conversinha, atalhos ensinados (`_cmd_aprender`/`_cmd_atalhos`) e troca de voz (`_cmd_voz`) |
| `app/comandos/feedback.py` (~135) | Feedback ("isso tá errado"), obrigado, melhorias (`_cmd_melhorias`, `_aplicar_melhorias`) e `_cmd_exportar` |
| `app/comandos/ditado.py` (~370) | Ditado (`_iniciar_ditado`…`_entregar_ditado`, destinos ipm/projeto/salvar/nota/copiar), revisão, agente IPM, área de transferência |
| `app/comandos/anotacoes.py` (~285) | Histórico de respostas, memória "lembra que…", projetos guiados (`_proj_*`), lembretes e notas |
| `app/comandos/video.py` (~590) | YouTube (página, canais, `_cmd_youtube_controle`, `_acao_youtube`), streamings (`STREAMINGS`), `_cmd_clicar`, `_cmd_tocar` |
| `app/comandos/midia.py` (~230) | Volume (geral/por programa), teclas de mídia, Spotify, saída de som (`_cmd_saida_som`: troca a caixinha/o fone pelo apelido, config `som > saidas`) |
| `app/comandos/info.py` (~60) | Clima, notícias, hora e data |
| `app/comandos/janelas.py` (~515) | Janelas e abas pelo nome/monitores (`_cmd_mover`, `_cmd_juntar`, `_escolher_aba`, `_abrir_no_monitor`), `_cmd_janela`, tela, desligar o PC, pesquisa, `_cmd_abrir` |
| `app/comandos/celular.py` | Falando no PC: `_cmd_print_telegram` ("manda um print no Telegram") e `_cmd_tocando` ("o que tá tocando"). Os outros comandos novos do Telegram (print por monitor, vídeo curto, desligar/dormir/reiniciar) só existem vindo do celular: ficam em `app/recebidos.py` (`Caixa._comando_especial`) |
| `app/cerebro.py` | IA opcional (Ollama grátis ou Claude API), interpreta frases e conversa; manda como contexto só o `INDICE.md` + os assuntos de `memoria/fatos/` ligados ao pedido (`memoria.texto_para_ia`, limite em KB de `cerebro > memoria_contexto_kb`); `sugerir_assunto` (opcional, 2ª opinião em segundo plano sobre o assunto de um fato novo). Troca de IA sozinho (`_opcoes_ia`/`_tentar_opcoes`): lista ORDENADA (`cerebro > ordem_ia`, painel > Conversa) de Ollama principal → Ollama menor (`ollama_modelo_menor`, se configurado) → Claude (se tiver `claude_chave` em segredos.json ou `ANTHROPIC_API_KEY`); quem falhar ou estourar `timeout_tentativa_seg` fica "de castigo" por `penalidade_min` minutos (não é tentada de novo até passar) |
| `app/voz.py` | Fala por motor: kokoro (`app/voz_kokoro.py`, local, modelo em `modelos/kokoro/`), natural (`app/voz_natural.py`: Chatterbox num venv SEPARADO `modelos/voz_natural/venv`, servidor `app/voz_natural_servidor.py` em 127.0.0.1:47633, fecha sozinho com o Mestre), edge, azure (`app/voz_azure.py`), elevenlabs (`app/voz_elevenlabs.py`, sem aquecer: gastaria créditos), windows; o escolhido falha → `voz > reserva` (painel > Voz > "Usar como reserva") → kokoro → edge. Cache em %TEMP%/mestre_voz. `falar` só põe na fila (`fala_em_segundo_plano`) e uma linha separada toca frase a frase; `parar()` corta a fila inteira; quem precisa que a fala termine (desligar, reiniciar, bloquear) chama `voz.esperar()` |
| `app/segredos.py` | Chaves (Azure, ElevenLabs, token do Telegram) em `%APPDATA%\Mestre\segredos.json`, FORA do projeto |
| `app/recebidos.py` | Áudios do celular: pasta sincronizada + robô do Telegram → Whisper (`Transcritor.transcrever_arquivo`) → comando (se começar com a palavra) ou destino (projeto/nota/ipm). `Caixa.avisar`: indicador azul (`estado.avisar`) + frase curta. `Caixa._comando_especial`: só do Telegram, sem a palavra de ativação — print (por monitor), "o que tá tocando", vídeo curto (`sistema.gravar_video_monitor`) e desligar/dormir/reiniciar com confirmação "sim" e aviso de 30s cancelável ("cancela"); `enviar_foto(s)`/`enviar_video` mandam pro Telegram (sendPhoto/sendMediaGroup/sendVideo) |
| `app/avisos_pc.py` | Avisos do PC pelo Telegram (`avisos_pc` no config; painel > Celular > "Avisos do PC"): janela oculta ouve `WM_QUERYENDSESSION` ("desligando"), batimento em `logs/pc_batimento.json`, ao iniciar num boot novo manda "PC ligou" ou "desligou sem avisar" (eventos 41/6008); pulso opcional ao healthchecks.io (URL em segredos.json). `recebidos.enviar_texto` manda texto ao Telegram sem precisar de `Caixa` |
| `app/sistema.py` | Ações no Windows: teclas e atalhos, mídia, volume (pycaw: por programa), janelas, print, envio ao app Claude (uiautomation). `tirar_prints_por_monitor`/`gravar_video_monitor` (Pillow/imageio, para o Telegram), `janela_ativa_por_monitor`, `suspender_pc`/`cancelar_suspensao` (dormir, cancelável). `listar_saidas_som`/`saida_som_atual`/`definir_saida_som` (pycaw + COM `IPolicyConfig` não documentado, sem baixar nada de terceiros): troca o dispositivo de reprodução padrão (console+multimídia+comunicações) casando por pedaço do nome |
| `app/youtube.py` | Último vídeo de um canal / busca, via yt-dlp |
| `config.yaml` | Configuração do usuário: **preserve os comentários** e o estilo ao editar |
| `vocabulario.yaml` | Sinônimos, enfeites ignorados e atalhos (editado à mão) |
| `aprendido.yaml` | Escrito pelo programa (atalhos e preferências ensinados por voz) |
| `MELHORIAS.md` | Ideias anotadas por voz. `- [ ]` pendente, `- [x]` feita |
| `GUIA_PASSO_A_PASSO.md` | Guia do usuário; atualize quando mudar algo que ele usa |

## Como adicionar um comando

1. Crie `def _cmd_nome(self, t: str) -> bool` no mixin do assunto em `app/comandos/` (YouTube/streaming →
   `video.py`, janelas/abas/abrir → `janelas.py`, volume/Spotify → `midia.py`, clima/hora → `info.py`, notas/projetos →
   `anotacoes.py`, ditado/IPM → `ditado.py`, IA → `ia.py`, rotinas → `rotinas.py`, feedback/melhorias → `feedback.py`,
   o próprio assistente → `assistente.py`). Assunto novo = arquivo novo com `class XMixin:` + incluir na herança
   do `Executor` em `__init__.py`. Constante compartilhada vai em `base.py`. `t` já vem
   normalizado (minúsculo, sem acentos, sem "mestre") e traduzido pelo vocabulário.
2. Devolva `True` se reconheceu (e executou), `False` para passar adiante.
3. Coloque o nome em `Executor.ORDEM` (a ordem importa: os mais específicos vêm antes).
4. Novos jeitos de falar entram em `vocabulario.yaml` (sinônimos), não em regex gigantes.
5. Para perguntar algo de volta ao usuário, use `self.perguntar(texto, funcao_resposta)`.

## Pedidos do usuário (TODA mensagem nova com um pedido)

Os pedidos chegam falados, longos e com várias ideias juntas (às vezes com o cabeçalho
`[Pedido ditado por voz no Mestre...]`, colado pelo próprio Mestre). Sempre, nesta ordem:

1. **corrigir-transcricao** (`.claude/skills/corrigir-transcricao/`): mostre "Entendi assim:" com o
   texto corrigido (Ollama, IPM, Claude Code... veja o glossário da skill).
2. **refinar-pedido** (`.claude/skills/refinar-pedido/`): cartões + ordem sugerida.
3. **Espere o "ok"** antes de implementar. Se ele acrescentar algo, junte ao cartão certo.

Palavra nova que o Whisper errou e ele corrigiu? Acrescente no glossário da corrigir-transcricao.

## Itens "FEEDBACK:" no MELHORIAS.md

São erros relatados por voz: `ouvi "..." · entendi "..." · respondi "..." · o certo era: ...`, às vezes com
`[áudio: logs/feedback/x.wav]`. "ouvi" é o que o Whisper transcreveu; "entendi" é o texto depois do
vocabulário. Descubra onde o erro nasceu (transcrição, vocabulário, regex de comando ou resposta) e corrija
na camada certa: erro de transcrição costuma se resolver com vocabulário/sinônimo ou prompt do Whisper
(`Transcritor.PROMPT` em `app/audio.py`), não com regex.

## Regras

- Frases FALADAS (`self.voz.falar`) com acentos corretos e POUCAS vírgulas (a voz pausa em cada uma).
- Não escreva "chefe" nem "Mestre" fixos em frases novas: use `self.falar("<situação>")`,
  `self.preencher("... {apelido} ...")` ou os marcadores `{palavra}` (o que ele fala para chamar), `{apelido}`
  (o usuário) e `{nome}` (o assistente) direto em `self.voz.falar`. `voz.trocas` aplica tudo numa passada só:
  o usuário pode se chamar "Mestre" (apelido) e o assistente "Assessor"; nunca troque "Mestre" por regex.
  Varie as respostas com `random.choice` ou `self.falar("ok")` (falas da personalidade).
- Tudo tem de continuar **grátis**. Não adicione serviço pago sem perguntar.
- Arquivos `.bat` e `.vbs` usam quebra de linha CRLF e texto sem acentos.
- Não guarde senhas nem chaves em arquivos do projeto.
- Toda opção nova de configuração precisa de um valor padrão no código (o config.yaml do usuário
  pode ser antigo) e de um campo no painel (`app/painel.py`), para ele não precisar editar YAML.
- Interface: nada de janela nova fora do painel, do indicador e da revisão do ditado sem perguntar.
- Nova biblioteca? Coloque em `requirements.txt` (a atualização pela Central e o `INSTALAR_E_CRIAR_ATALHO.bat` instalam).
- Os `.bat` ficam em `ferramentas/` e começam com `cd /d "%~dp0.."`. O usuário usa o atalho **Mestre** (Central).
- Tela com lista que pode crescer (canais, programas...) nunca cria um widget por item sem limite.
- Em `except ... as erro:` com `lambda` dentro, use `lambda e=erro:` (o Python apaga `erro` no fim do except).
- Textos na tela e falas usam o nome e a palavra escolhidos (`self.nome`, `self.palavra`), nunca "Mestre" fixo.
  O teste automático confere isso com o nome "Jarvis".
- Chamada à IA (Ollama/Claude) passa por `self._pensar(...)`: nunca travar a escuta esperando a IA.
- O vocabulário tira palavras como "pode" ("pode falar" vira "falar"). Comando que depende da frase exata
  usa `self._pedido_puro()` (a frase falada, sem a palavra de ativação e sem o vocabulário).
- "… no monitor 2" é tirado da frase por `_separar_monitor` (vira `sistema.MONITOR_ALVO`); quem abre janelas
  chama `sistema.depois_de_abrir(antes)` para posicionar. pycaw/uiautomation fora da linha principal precisam
  de `comtypes.CoInitialize()` / `UIAutomationInitializerInThread()`.
- Em perguntas onde "nada"/"não" é resposta válida, ponha o método em `aceitam_nao` (senão vira "cancelar").
- Janelas e abas pelo nome (`_cmd_mover`): "joga X pro monitor N" move a janela onde X está; "separa X" (ou
  duas ordens para abas da mesma janela) tira a aba para uma janela só dela pela extensão. `abrir_site` com
  monitor pedido abre `--new-window` (nunca arrastar a janela que já existia). Site já aberto numa aba = usar a aba.
- Mudou a extensão? Suba a versão no `manifest.json` E em `ponte.VERSAO_EXTENSAO` (o painel avisa quem está com a velha).
- Modo descanso (`_cmd_descanso`, `Executor._descansando`, `estado.descanso`): só `texto.frase_de_volta` acorda.
- Comando que a IA descobre em segundo plano roda sozinho (`_pensamento_terminou`), com `_frase_original` = texto da IA.
- Mesmo site em mais de uma tela: `_escolher_aba(candidatas, abas, nome, monitor, continuar, tem)` decide a aba
  (a que `tem` o texto falado > "do monitor N" (`_monitor_da_frase`) > monitor do mouse > pergunta "No monitor 1 ou no 2?").
  As ações do YouTube vão para a aba escolhida por `YouTubeNoBraveComExtensao.aba_alvo` (→ `ponte.pedir(..., aba=)`).
- Streaming: `STREAMINGS` com "{}" busca pelo endereço; sem "{}" abre o site e a extensão DIGITA na busca (`buscar`).
- IA: saídas "comando" (roda na hora), "pergunta" (pergunta e pensa de novo com a resposta) e "resposta" (fala direto,
  `aviso_ao_terminar: falar_direto`). Frase que virou comando só entra na memória (`memoria.comando_ja_descoberto`,
  sem IA na próxima) depois de rodar ~30s sem correção (`Executor._agendar_memoria_ia`/`_pendente_ia`) ou se a
  mesma frase repetir o mesmo comando antes disso; FEEDBACK/"não era isso"/cancelar apagam a memória pendente
  (ou já gravada) daquela frase (`Executor._cancelar_memoria_ia`, `memoria.esquecer_comando_ia`).
- Comandos de YouTube/navegador ficam fora da IA: frase nova do usuário que caiu na IA ("rota": "ia" no
  histórico exportado) vira regex no comando certo + linha em `testes/frases.py`.

## Como testar (sempre, depois de cada mudança)

1. **Teste automático (obrigatório antes de entregar):**
   ```
   venv\Scripts\python -m testes.teste_basico
   ```
   Roda numa cópia do projeto (painel com 2.000 canais, adicionar programa/site/canal/rotina, salvar,
   comandos e atualização por zip). Tudo precisa dar OK. Mudou algo do painel ou dos comandos?
   Acrescente um item em `testes/teste_basico.py`.
   Inclui `testes/frases.py`: 150+ jeitos de falar → qual `_cmd_*` deve atender. Comando novo ou frase nova
   que ele usa? Acrescente lá (e as "armadilhas" que NÃO podem cair no comando).
2. Um comando só: `venv\Scripts\python -m app.main --mudo --comando "mestre bora trabalhar"`
   (com `MESTRE_SIMULAR=1` nada abre de verdade).
3. Conversa digitada:
   ```
   venv\Scripts\python -m app.main --texto --mudo
   ```
Digite frases como o usuário falaria (ex.: `po mestre, bota o youtube ai`) e confira no
terminal a linha `Entendi como: ...` e a ação executada. O microfone não dá para testar
aqui: diga ao usuário quais frases ele deve testar falando, depois de `Mestre, reinicia`.

## Roteiro de validação

`ROTEIRO_VALIDACAO.md` (raiz) tem as frases que o usuário deve testar falando: "Novidades" (desta
entrega) e "Sempre testar" (regressão fixa do dia a dia). O `/entregar` atualiza a seção Novidades.

## Ao terminar os itens do MELHORIAS.md

- Marque cada item feito com `[x]`.
- Explique ao usuário, em linguagem simples, o que mudou e como testar.
- Se algo não for possível (ex.: limite do Windows), explique o motivo e sugira alternativa.
