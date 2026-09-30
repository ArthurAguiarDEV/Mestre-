"""Cria tarefas e prompts copiáveis para o ChatGPT/Codex e o Claude, sem APIs pagas."""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "tarefas_ia"
FILA = BASE / "fila"
PROMPTS = BASE / "prompts_prontos"
RESULTADOS = BASE / "resultados"

# Fluxo ativo: só ChatGPT/Codex (coordena e revisa) e Claude (executa). Tudo que o
# gerador escreve (cartão, JSON, prompts, filas) sai desta definição. O Ollama continua
# sendo o motor de IA local do aplicativo e do protótipo CrewAI, não um destinatário.
AGENTES = {
    "chatgpt": {
        "rotulo": "ChatGPT/Codex",
        "funcao": "coordenação, planejamento e revisão final",
        "instrucao": "Revise o plano, confira se o escopo está claro e organize os próximos passos.",
    },
    "claude": {
        "rotulo": "Claude",
        "funcao": "implementação e revisão de código",
        "instrucao": "Leia CLAUDE.md, implemente apenas o escopo aprovado e registre os testes.",
    },
}


def classificar_esforco(pedido: str) -> tuple[str, str]:
    texto = pedido.lower()
    palavras_extra = ("repaginar", "layout", "arquitetura", "integração", "integracao", "vários", "varios")
    palavras_alto = ("painel", "função", "funcao", "automação", "automacao", "workflow", "github")
    if any(palavra in texto for palavra in palavras_extra):
        return "extra", "Opus"
    if any(palavra in texto for palavra in palavras_alto):
        return "alto", "Opus"
    return "médio", "Sonnet"


def recomendacao_modelo(agente: str, esforco: str, modelo_claude: str) -> str:
    """Sonnet/Opus só existem no Claude; o ChatGPT/Codex usa o modelo do próprio app."""
    if agente == "claude":
        modelo = f"Modelo recomendado: {modelo_claude} (Claude Code)."
    else:
        modelo = "Modelo: use o modelo configurado no seu app do ChatGPT/Codex."
    return f"Esforço recomendado: {esforco}.\n{modelo}"


def texto_prompt(identificador: str, pedido: str, agente: str, esforco: str, modelo: str) -> str:
    definicao = AGENTES[agente]
    arquivo_retorno = f"tarefas_ia/resultados/{identificador}-{agente}.md"
    return f"""# Prompt pronto — {agente}

Você é o agente de {definicao["funcao"]} do projeto Mestre.

## Pedido original

{pedido}

## Leia antes de trabalhar

1. `AGENTS.md` ou `CLAUDE.md`, conforme sua ferramenta.
2. `COORDENACAO_IA.md`.
3. `ORQUESTRACAO_IA.md`.
4. `tarefas_ia/fila/{identificador}.md`.
5. `tasks/lessons.md`.

## Sua tarefa

{definicao["instrucao"]}

{recomendacao_modelo(agente, esforco, modelo)}
Recomendação escrita aqui não muda a configuração do chat: ajuste no seletor do app.

Não faça commit, não publique no GitHub e não apague arquivos.
Se precisar de outra IA, registre a pergunta no retorno.

## Retorno obrigatório

Salve ou devolva um relatório com: o que foi analisado, decisões, arquivos envolvidos,
testes, pendências e dúvidas. O arquivo de retorno esperado é:

`{arquivo_retorno}`
"""


def atualizar_fila_agente(agente: str, identificador: str, pedido: str) -> None:
    pasta = BASE / agente
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / "hoje.md"
    bloco = f"""
## {identificador} — pendente

Pedido: {pedido}

Prompt pronto: `tarefas_ia/prompts_prontos/{identificador}-{agente}.md`
Retorno esperado: `tarefas_ia/resultados/{identificador}-{agente}.md`
"""
    with arquivo.open("a", encoding="utf-8") as destino:
        destino.write(bloco)


def criar_tarefa(pedido: str) -> Path:
    identificador = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    for pasta in (FILA, PROMPTS, RESULTADOS):
        pasta.mkdir(parents=True, exist_ok=True)
    esforco, modelo = classificar_esforco(pedido)
    convidados = "\n".join(f"- {d['rotulo']}: {d['funcao']}." for d in AGENTES.values())

    tarefa = FILA / f"{identificador}.md"
    tarefa.write_text(
        f"""# Tarefa {identificador}

Estado: `pendente`
Criada em: {datetime.now().isoformat(timespec='seconds')}

## Pedido original

{pedido}

## Agentes convidados

{convidados}

## Avaliação inicial

- Esforço: `{esforco}`
- Modelo recomendado para o Claude: `{modelo}`. O ChatGPT/Codex usa o modelo configurado no app.
- Recomendação escrita não altera a configuração do chat: ajuste no seletor do app.
- A IA executora pode corrigir essa avaliação, mas deve explicar o motivo.

## Regra de retorno

Cada agente deve salvar seu relatório em `tarefas_ia/resultados/` com o nome indicado
no prompt. O coordenador não considera a tarefa concluída enquanto o retorno não
estiver registrado.

## Aprovação humana

Depois dos retornos e dos testes, o estado deve ser `pronto_para_testar`.
Commit e GitHub só podem ocorrer depois de: `OK para publicar`.
""",
        encoding="utf-8",
    )

    for agente in AGENTES:
        prompt = PROMPTS / f"{identificador}-{agente}.md"
        prompt.write_text(texto_prompt(identificador, pedido, agente, esforco, modelo), encoding="utf-8")
        atualizar_fila_agente(agente, identificador, pedido)

    estado = {
        "id": identificador,
        "estado": "pendente",
        "pedido": pedido,
        "agentes": list(AGENTES),
        "esforco": esforco,
        "modelo": modelo,
        "modelo_vale_para": "claude",
        "sem_envio_automatico": True,
        "criado_em": datetime.now().isoformat(timespec="seconds"),
    }
    (FILA / f"{identificador}.json").write_text(
        json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return tarefa


def main() -> None:
    pedido = " ".join(sys.argv[1:]).strip()
    if not pedido:
        print('Uso: python central_tarefas.py "descreva a melhoria"')
        raise SystemExit(2)
    tarefa = criar_tarefa(pedido)
    print(f"Tarefa criada: {tarefa}")
    print(f"Prompts prontos em: {PROMPTS}")
    print(f"Filas diárias em: {BASE / '<agente>' / 'hoje.md'} (agentes: {', '.join(AGENTES)})")


if __name__ == "__main__":
    main()
