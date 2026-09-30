import sys
from pathlib import Path

from crewai import Agent, Crew, LLM, Process, Task


def criar_fluxo(pedido: str) -> Crew:
    modelo_local = LLM(
        model="ollama/gemma3:4b",
        base_url="http://localhost:11434",
        temperature=0.2,
    )

    pesquisador = Agent(
        role="Organizador de pedidos",
        goal="Entender o pedido e separar objetivo, contexto e restrições.",
        backstory="Você é cuidadoso e não inventa requisitos.",
        llm=modelo_local,
        verbose=False,
    )

    analista = Agent(
        role="Analista de soluções",
        goal="Transformar o pedido em um plano simples, seguro e executável.",
        backstory="Você prioriza passos pequenos e verificáveis.",
        llm=modelo_local,
        verbose=False,
    )

    revisor = Agent(
        role="Revisor de qualidade",
        goal="Encontrar ambiguidades, riscos e melhorias antes da entrega.",
        backstory="Você revisa com objetividade e propõe correções práticas.",
        llm=modelo_local,
        verbose=False,
    )

    tarefa_pesquisa = Task(
        description=f"""
        Analise este pedido do projeto Mestre:
        {pedido}

        Entregue: objetivo principal, informações conhecidas, dúvidas e critérios de sucesso.
        """,
        expected_output="Resumo estruturado do pedido, sem inventar informações.",
        agent=pesquisador,
    )

    tarefa_analise = Task(
        description="Com base na análise anterior, crie um plano em passos curtos e ordenados.",
        expected_output="Plano prático com etapas, dependências e validações.",
        agent=analista,
    )

    tarefa_revisao = Task(
        description="Revise o resumo e o plano. Aponte riscos, lacunas e entregue uma versão final clara.",
        expected_output="Resultado final revisado, com próximos passos e critérios de conclusão.",
        agent=revisor,
    )

    return Crew(
        agents=[pesquisador, analista, revisor],
        tasks=[tarefa_pesquisa, tarefa_analise, tarefa_revisao],
        process=Process.sequential,
        verbose=False,
    )


def main() -> None:
    pedido = " ".join(sys.argv[1:]).strip()
    if not pedido:
        pedido = "Organizar a próxima melhoria do Mestre"

    resultado = criar_fluxo(pedido).kickoff()
    destino = Path(__file__).with_name("resultado.md")
    destino.write_text(str(resultado), encoding="utf-8")
    print(f"Resultado salvo em: {destino}")


if __name__ == "__main__":
    main()
