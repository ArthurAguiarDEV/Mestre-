# Primeiro fluxo do Mestre com CrewAI

Este exemplo cria uma pequena equipe de agentes:

1. Pesquisador: organiza o pedido recebido.
2. Analista: transforma a pesquisa em um plano.
3. Revisor: verifica clareza, riscos e próximos passos.

## 1. Instalar

Abra o PowerShell nesta pasta e execute:

```powershell
..\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 2. Executar

Este exemplo usa o Ollama local com o modelo `gemma3:4b`. Não precisa de chave da
OpenAI nem de pagamento por uso. Verifique se o Ollama está aberto e se o modelo
aparece em `ollama list`.

```powershell
$env:PYTHONIOENCODING = "utf-8"
..\venv\Scripts\python.exe crew.py "Organizar a próxima melhoria do Mestre"
```

O resultado será salvo em `resultado.md`.

Para usar outro modelo já instalado, altere `ollama/gemma3:4b` em `crew.py`.

## Como o fluxo funciona

O CrewAI reúne agentes, tarefas e um processo. Neste primeiro exemplo o processo é
sequencial: a saída do pesquisador passa para o analista e depois para o revisor.

Depois que este teste funcionar, o fluxo pode ser ligado ao painel do Mestre.

## Coordenador seguro

Para executar a nova etapa, abra o PowerShell e rode:

```powershell
cd C:\Ias\Mestre-repo\agentes_crewai
$env:PYTHONIOENCODING = "utf-8"
..\venv\Scripts\python.exe orquestrador.py "Criar uma tela para mostrar as tarefas do dia"
```

O coordenador executa o refinamento, a avaliação de esforço e o planejamento.
Ele salva uma pasta em `tarefas_ia\execucoes\` e termina em
`pronto_para_testar`. Nesta primeira versão ele não edita o código e não faz
commit: você revisa o plano antes da próxima etapa.

## Gerador de tarefas para as IAs

O `central_tarefas.py` cria um cartão, um JSON, os prompts e as filas de uma tarefa nova,
**somente para o ChatGPT/Codex e o Claude** (a lista está em `AGENTES` no próprio arquivo).
Ele não usa rede, API nem o Ollama: só escreve arquivos em `tarefas_ia/`.

```powershell
cd C:\Ias\Mestre-repo\agentes_crewai
..\venv\Scripts\python.exe central_tarefas.py "Descreva aqui a melhoria desejada"
```

Sonnet/Opus aparecem só na recomendação do Claude; no prompt do ChatGPT/Codex vale o modelo
do app. O Ollama acima é o motor de IA local do exemplo (`crew.py`) e do coordenador
(`orquestrador.py`); ele não recebe tarefas do gerador. Manus está desativado.
