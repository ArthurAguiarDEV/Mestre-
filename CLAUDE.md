# Projeto Mestre: instruções para o Claude Code

Assistente pessoal por voz para Windows, em Python 3.12. O dono **não é programador**:
fale com ele em português simples, explique o que mudou e o que ele precisa testar.

## Como o código está organizado

| Arquivo | O que faz |
|---|---|
| `app/main.py` | Início. `--texto` (digitar em vez de falar), `--mudo`, `--microfones` |
| `app/ouvido.py` | Laço do microfone: corta frases, checa "mestre", janela de conversa, atualiza o estado |
| `app/audio.py` | Segmentador (limite de volume), ganho, normalização, Transcritor (faster-whisper), diagnóstico |
| `app/locutor.py` | "Responder só à minha voz": SpeechBrain ECAPA (`modelos/locutor_ecapa`, carrega em segundo plano), impressão em `%APPDATA%\Mestre\voz_dono.json`; `Ouvido._voz_do_dono` confere antes de executar (celular/Telegram não passa por ela) |
| `app/validacao.py` | "Validar atualização" (painel > Sistema): lê `ROTEIRO_VALIDACAO.md`, casa OUVI/ENTENDI/FIZ pelo `ts` do histórico, gera relatório em `exportacoes/validacao_*.md` e FEEDBACK no MELHORIAS.md; `ultimo_relatorio()` |
| `app/estado.py` | O que o Mestre está fazendo agora (ouvindo/gravando/...) + pausa por arquivo |
| `app/overlay.py` | Indicador na tela (tkinter), roda na linha principal; a escuta roda numa thread |
| `app/painel.py` | Central + painel (customtkinter). Menu lateral em grupos (`GRUPOS_MENU`); cada seção é um cartão: `f = secao(pagina, "Título", "dica")` (dica longa vira "mais ›"; títulos em `RECOLHIDAS` começam fechados). `TabelaChaveValor`: páginas de 40 (◀ ▶) + busca ao digitar; aguenta milhares |
| `app/versao.py` | `VERSAO` do projeto (suba a cada zip). O painel mostra; `atualizar.versao_atual()` lê do arquivo |
| `app/central.py` | O que o atalho "Mestre" abre: liga o Mestre (opcional) e abre o painel (uma janela só) |
| `app/iniciar_painel.py` | Abre o painel mostrando erros; porta 47631 traz para frente um painel já aberto |
| `app/bandeja.py` | Ícone perto do relógio (pystray): abrir painel, pausar, reiniciar, desligar |
| `app/atualizar.py` | Atualização por .zip (botão na Central): nunca toca config/aprendido/MELHORIAS/notas; lê OBSOLETOS.txt |
| `app/configuracao.py` | Lê/salva o config.yaml com ruamel.yaml, preservando comentários; textos sempre entre aspas |
| `app/personalidades.py` | Estilos prontos (descrição + frases por situação). Placeholders {apelido} {nome} {saudacao} |
| `app/tema.py` | Cores e fonte (config > aparencia; painel > Aparência); tema do customtkinter e ícone na cor escolhida |
| `app/memoria.py` | Histórico (memoria/historico.jsonl), fatos "lembra que…" (memoria/fatos.md) e conversa da IA |
| `app/projetos.py` | Projetos guiados: pasta + PLANO.md, 3 caminhos da IA (`Cerebro.propor_opcoes`), anotações |
| `app/navegador.py` | Edge/Chrome controlado (Playwright, perfil `navegador_mestre/`) + ações do YouTube (like, chat, resultados) |
| `app/ponte.py` + `extensao_brave/` | Extensão do Brave (MV3, versão em `ponte.VERSAO_EXTENSAO` = manifest) ↔ Mestre por 127.0.0.1:47632: abas e janelas (listar, focar, separar, juntar, ir, voltar/avançar, trocar aba, clicar pelo texto) e YouTube (like, chat, resultados com canal, próximo, pausar, volume, retrato) |
| `app/exportar.py` | "Exportar para o Claude": `exportacoes/historico_para_claude_*.md` a partir de `memoria/historico.jsonl` (com `rota`/`entendi`) e `memoria/ouvido.jsonl` (tudo que o microfone transcreveu) |
| `app/revisar_ditado.py` | Janelinha do fim do ditado (processo separado), conversa com o Mestre por `logs/ditado_revisao.json` |
| `app/informacoes.py` | Clima (wttr.in) e notícias (Google Notícias RSS), grátis e sem cadastro |
| `app/vocabulario.py` | Traduz fala solta para a forma oficial usando `vocabulario.yaml` + `aprendido.yaml` |
| `app/comandos.py` | `Executor`: cada comando é um método `_cmd_*` listado em `Executor.ORDEM`. Ditado (`_iniciar_ditado`…`_entregar_ditado`, destinos ipm/projeto/salvar/nota/copiar) e IA em segundo plano (`_pensar`, `entregar_pensamento`) |
| `app/cerebro.py` | IA opcional (Ollama grátis ou Claude API), interpreta frases e conversa |
| `app/voz.py` | Fala por motor: kokoro (`app/voz_kokoro.py`, local, modelo em `modelos/kokoro/`), natural (`app/voz_natural.py`: Chatterbox num venv SEPARADO `modelos/voz_natural/venv`, servidor `app/voz_natural_servidor.py` em 127.0.0.1:47633, fecha sozinho com o Mestre), edge, azure (`app/voz_azure.py`), elevenlabs (`app/voz_elevenlabs.py`, sem aquecer: gastaria créditos), windows; o escolhido falha → kokoro → edge. Cache em %TEMP%/mestre_voz |
| `app/segredos.py` | Chaves (Azure, ElevenLabs, token do Telegram) em `%APPDATA%\Mestre\segredos.json`, FORA do projeto |
| `app/recebidos.py` | Áudios do celular: pasta sincronizada + robô do Telegram → Whisper (`Transcritor.transcrever_arquivo`) → comando (se começar com a palavra) ou destino (projeto/nota/ipm). `Caixa.avisar`: indicador azul (`estado.avisar`) + frase curta |
| `app/sistema.py` | Ações no Windows: teclas e atalhos, mídia, volume (pycaw: por programa), janelas, print, envio ao app Claude (uiautomation) |
| `app/youtube.py` | Último vídeo de um canal / busca, via yt-dlp |
| `config.yaml` | Configuração do usuário: **preserve os comentários** e o estilo ao editar |
| `vocabulario.yaml` | Sinônimos, enfeites ignorados e atalhos (editado à mão) |
| `aprendido.yaml` | Escrito pelo programa (atalhos e preferências ensinados por voz) |
| `MELHORIAS.md` | Ideias anotadas por voz. `- [ ]` pendente, `- [x]` feita |
| `GUIA_PASSO_A_PASSO.md` | Guia do usuário; atualize quando mudar algo que ele usa |

## Como adicionar um comando

1. Crie `def _cmd_nome(self, t: str) -> bool` em `app/comandos.py`. `t` já vem
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
  `aviso_ao_terminar: falar_direto`). Frase que virou comando fica na memória (`memoria.comando_ja_descoberto`): sem IA na próxima.
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
