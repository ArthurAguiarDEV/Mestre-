"""Coordenador inicial do Mestre: planeja uma melhoria e para antes de editar código."""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

from crewai import Agent, Crew, LLM, Process, Task


ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "prompts"
EXECUCOES = ROOT / "tarefas_ia" / "execucoes"


def ler_prompt(nome: str) -> str:
    return (PROMPTS / nome).read_text(encoding="utf-8")


def salvar_estado(pasta: Path, estado: str, dados: dict) -> None:
    registro = {
        "estado": estado,
        "momento": datetime.now().isoformat(timespec="seconds"),
        **dados,
    }
    (pasta / "estado.json").write_text(
        json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (pasta / f"{estado}.md").write_text(
        dados.get("resultado", ""), encoding="utf-8"
    )


def criar_agente(nome: str, objetivo: str, historia: str, llm: LLM) -> Agent:
    return Agent(
        role=nome,
        goal=objetivo,
        backstory=historia,
        llm=llm,
        verbose=False,
        allow_delegation=False,
    )


def executar(pedido: str) -> Path:
    identificador = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    pasta = EXECUCOES / identificador
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "pedido.md").write_text(pedido, encoding="utf-8")

    salvar_estado(pasta, "recebido", {"pedido": pedido, "resultado": pedido})

    llm = LLM(
        model="ollama/gemma3:4b",
        base_url="http://localhost:11434",
        temperature=0.2,
    )
    global_prompt = ler_prompt("00_global.md")

    refinador = criar_agente(
        "Refinador de pedidos",
        "Transformar o pedido em cartões claros e verificáveis.",
        global_prompt + "\n" + ler_prompt("01_refinador.md"),
        llm,
    )
    avaliador = criar_agente(
        "Avaliador de esforço",
        "Classificar esforço, risco, modelo e ordem de execução.",
        global_prompt + "\n" + ler_prompt("02_esforco.md"),
        llm,
    )
    planejador = criar_agente(
        "Planejador técnico",
        "Criar um plano seguro sem editar arquivos.",
        global_prompt + "\n" + ler_prompt("03_planejador.md"),
        llm,
    )

    tarefa_refino = Task(
        description=f"Pedido do usuário:\n{pedido}",
        expected_output="Texto corrigido, cartões, dúvidas e ordem sugerida.",
        agent=refinador,
    )
    tarefa_esforco = Task(
        description="Avalie cada cartão produzido e recomende esforço e modelo.",
        expected_output="Nível, modelo, pontuação e dicas para reduzir custo.",
        agent=avaliador,
    )
    tarefa_plano = Task(
        description=(
            "Com base no pedido refinado e na avaliação, crie o plano técnico. "
            "Não edite código, não faça commit e liste o teste humano."
        ),
        expected_output="Plano com arquivos, etapas, riscos e testes.",
        agent=planejador,
    )

    resultado = Crew(
        agents=[refinador, avaliador, planejador],
        tasks=[tarefa_refino, tarefa_esforco, tarefa_plano],
        process=Process.sequential,
        verbose=False,
    ).kickoff()
    texto = str(resultado)

    salvar_estado(
        pasta,
        "pronto_para_testar",
        {
            "pedido": pedido,
            "resultado": texto,
            "proximo_passo": "Revisar o plano e aprovar a implementação.",
            "publicar": False,
        },
    )
    return pasta


def main() -> None:
    pedido = " ".join(sys.argv[1:]).strip()
    if not pedido:
        print('Uso: python orquestrador.py "descreva a melhoria"')
        raise SystemExit(2)
    pasta = executar(pedido)
    print(f"Estado final: pronto_para_testar")
    print(f"Execução salva em: {pasta}")


if __name__ == "__main__":
    main()
