# Testes seguros do Mestre

Base da correção: `5317745`.

Execute, na raiz do projeto:

```powershell
venv\Scripts\python -m testes.teste_basico
```

Essa entrada executa os testes de isolamento/comportamento, as regressões sem
interface recuperadas da suíte antiga e as 277 frases de regressão. Também é
possível executar apenas `-m testes.teste_seguranca`,
`-m testes.teste_regressoes_sem_interface` ou `-m testes.frases`. Use essas
entradas por módulo, em um processo Python novo.

A classificação completa da cobertura antiga está em `COBERTURA_LEGADA.md`.

`testes/__init__.py` instala a barreira antes do aplicativo e define
`MESTRE_SIMULAR=1`. Processos filhos, navegador padrão, Tk (inclusive janelas
transparentes), Qt, áudio, automação de mouse/teclado, DLLs nativas e conexões de
rede são bloqueados. Uma tentativa levanta `EfeitoRealBloqueado`, inclusive nos
caminhos que normalmente capturam `Exception` para tentar outro método. O registro
de tentativas também detecta violações ocorridas em threads.

Os testes de produção substituem as saídas por doubles **antes** de desativar a
simulação naquele teste. Não invocam APIs de monitores ou janelas físicas.
As consultas do YouTube/clima/notícias no teste de frases usam dados fixos; a voz
é muda. Configuração, aprendizado e histórico ficam numa cópia temporária com
configuração de exemplo. Os arquivos do usuário não são alterados.

## Inventário revisado

`saidas_reais.json` registra as chamadas Python diretas encontradas. O teste
compara esse inventário com o código e exige revisão quando uma saída muda.

| Caminho | Saída real | Proteção nos testes |
|---|---|---|
| `app/sistema.py`: `abrir_site` | Brave por Popen, navegador padrão e URI Spotify | Retorno em simulação em qualquer plataforma; barreira de processos/navegador |
| `app/sistema.py`: programas, arquivos, Explorer, app Claude, terminais | startfile e Popen | Retorno antes da saída; doubles nos testes do ramo real |
| `app/sistema.py`: painel, revisão, iniciar/reiniciar, comando em processo separado, parar PID, desligar PC | Popen/run, taskkill, shutdown | Simulação; bloqueio global de processos e de os._exit/os.kill |
| `app/navegador.py`: YouTube normal e Brave com extensão | Popen e fallback abrir_site | Retorno antes de ler janela ativa ou iniciar processo |
| `app/navegador.py`: navegador controlado | Playwright visível, goto, bring_to_front, teclado, JavaScript e CDP | Nenhuma thread/callback/instância Playwright em simulação; import bloqueado na barreira |
| `app/ponte.py` | Servidor local e pedidos à extensão | Sem servidor, consulta ou enfileiramento em simulação; sockets bloqueados |
| `extensao_brave/background.js` e `conteudo.js` | tabs.create, windows.create/update, foco e reprodução de vídeo | Sem pedidos pela ponte; extensão não é executada pelos testes |
| `app/painel.py` | 8 chamadas webbrowser: Azure, ElevenLabs, chave de IA, Ollama, projetos, canais e Takeout | webbrowser bloqueado; suíte não constrói painel |
| `app/avatar.py` e `avatar_janela.py` | Processo do avatar e abertura do painel | Avatar respeita simulação; Popen/Qt bloqueados |
| `app/personagem/janela.py` | Processo do painel (duplo clique no personagem) | Qt e Popen bloqueados; a janela só abre fora dos testes (`ferramentas/verificar_personagem.py` roda no Windows) |
| `app/painel_personagem.py` | `subprocess.run` da prévia (PNG feito por `app.personagem.previa`) e `webbrowser.open` da página de teste local | A suíte não constrói o painel; processo e navegador bloqueados |
| `app/atualizar.py` | pip por subprocess.run | Processo bloqueado; instalação não executada |
| `app/avisos_pc.py` | PowerShell e janela de eventos Windows | Processo/DLL bloqueados; integração não executada |
| `app/voz_natural.py` | nvidia-smi, instalação, servidor de voz e taskkill | Processos e áudio bloqueados; código de voz não alterado |
| `testes/teste_basico.py` (trechos legados) | Processos Python, Tk, testes de voz/avatar | Entrada antiga desativada; a entrada padrão roda a suíte segura |

As consultas de monitores/janelas/mouse em `sistema` devolvem valores vazios na
simulação. As ações de foco, posicionamento, teclas e área de transferência não
chegam às APIs do Windows.

## Limitações deliberadas

- A suíte antiga de painel/avatar criava janelas transparentes, ainda reais.
  Foi preservada como referência, mas sua função de execução recusa rodar.
  Nenhum resultado da suíte gráfica, dos modelos de voz ou das instalações é
  declarado como validado por esta entrega. Migrar esses casos exige doubles.
- Não há teste físico de monitores, foco, áudio, teclado ou mouse; a comprovação
  é feita nos pontos de saída e nas chamadas esperadas com substitutos em memória.
- A barreira pertence aos testes e não afeta o processo de uso normal do Mestre.
  `MESTRE_SIMULAR=1` sozinho, fora das entradas de teste, não equivale à barreira:
  outros módulos legados, como painel e voz, continuam exigindo isolamento.
- A barreira não é uma sandbox contra código hostil ou uma futura biblioteca
  nativa desconhecida. Novas integrações exigem revisão do inventário e testes.
- Na entrega original de isolamento, o visual não mudou. Desde então, Aurora e
  personagem alteraram interface e emissão de texto para o avatar. Telegram e extensão
  continuam exigindo validação própria; estado verificado em `../docs/ESTADO_ATUAL.md`.
