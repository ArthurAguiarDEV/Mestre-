"""Projetos guiados: "Mestre, quero começar um novo projeto".

Cada projeto vira uma pasta (padrao: Documentos/Projetos/<nome>) com um PLANO.md:
respostas da conversa, os 3 caminhos que a IA sugeriu, o caminho escolhido (com os
passos como caixinhas - [ ]) e as anotacoes feitas por voz.
"""
import re
from datetime import datetime
from pathlib import Path

from .texto import melhor_correspondencia, normalizar

TIPOS = {  # tipo: (nome falado, subpastas)
    "codigo": ("de código", ["codigo", "ideias", "referencias"]),
    "trabalho": ("de trabalho", ["documentos", "reunioes", "entregas"]),
    "vida": ("da vida pessoal", ["ideias", "planos", "arquivos"]),
    "estudo": ("de estudo", ["materiais", "resumos", "exercicios"]),
    "outro": ("", ["ideias", "arquivos"]),
}


def tipo_falado(frase: str) -> str:
    n = normalizar(frase)
    for tipo, palavras in (("codigo", r"codigo|programa|app|aplicativo|site|software|sistema"),
                           ("trabalho", r"trabalho|empresa|servico|ipm|cliente"),
                           ("vida", r"vida|pessoal|casa|familia|saude|viagem"),
                           ("estudo", r"estudo|estudar|curso|faculdade|aprender|prova")):
        if re.search(rf"\b({palavras})\b", n):
            return tipo
    return "outro"


def pasta_base(cfg: dict) -> Path:
    escolhida = str((cfg.get("projetos") or {}).get("pasta") or "").strip()
    if escolhida:
        return Path(escolhida).expanduser()
    documentos = Path.home() / "Documents"
    return (documentos if documentos.exists() else Path.home()) / "Projetos"


def _nome_de_pasta(nome: str) -> str:
    limpo = re.sub(r'[<>:"/\\|?*]+', "", nome).strip().strip(".")
    return limpo[:60] or f"Projeto {datetime.now():%Y-%m-%d}"


def criar(base: Path, dados: dict) -> Path:
    """dados: nome, tipo, objetivo, extra. Devolve a pasta criada."""
    pasta = base / _nome_de_pasta(dados["nome"])
    n = 2
    while (pasta / "PLANO.md").exists():
        pasta = base / f"{_nome_de_pasta(dados['nome'])} ({n})"
        n += 1
    for sub in TIPOS.get(dados["tipo"], TIPOS["outro"])[1]:
        (pasta / sub).mkdir(parents=True, exist_ok=True)
    (pasta / "PLANO.md").write_text(
        f"# {dados['nome']}\n\n"
        f"- **Tipo:** {dados['tipo']}\n"
        f"- **Criado em:** {datetime.now():%d/%m/%Y %H:%M}\n"
        f"- **Objetivo:** {dados['objetivo']}\n"
        f"- **Prazo / o que já existe:** {dados.get('extra') or '-'}\n\n"
        "## Caminhos sugeridos\n\n(a IA ainda não sugeriu)\n\n"
        "## Caminho escolhido\n\n(ainda não escolhido)\n\n"
        "## Anotações\n\n", encoding="utf-8")
    return pasta


def _trocar_secao(texto: str, titulo: str, corpo: str) -> str:
    padrao = rf"(## {re.escape(titulo)}\n\n)(.*?)(?=\n## |\Z)"
    return re.sub(padrao, lambda m: m.group(1) + corpo.rstrip() + "\n", texto, count=1, flags=re.S)


def gravar_pesquisa(pasta: Path, resultados: list[dict]) -> None:
    plano = pasta / "PLANO.md"
    corpo = "".join(f"- [{r['titulo']}]({r['link']}): {r.get('resumo', '')}\n" for r in resultados) or "(nada encontrado)"
    texto = plano.read_text(encoding="utf-8")
    if "## Pesquisa na internet" not in texto:   # a secao entra antes dos caminhos
        texto = texto.replace("## Caminhos sugeridos", "## Pesquisa na internet\n\n\n## Caminhos sugeridos", 1)
    plano.write_text(_trocar_secao(texto, "Pesquisa na internet", corpo), encoding="utf-8")


def gravar_opcoes(pasta: Path, opcoes: list[dict]) -> None:
    plano = pasta / "PLANO.md"
    corpo = ""
    for i, o in enumerate(opcoes, 1):
        corpo += f"### {i}. {o['titulo']}\n{o.get('resumo', '')}\n\n"
        corpo += "".join(f"- {p}\n" for p in o.get("passos", [])) + "\n"
    plano.write_text(_trocar_secao(plano.read_text(encoding="utf-8"), "Caminhos sugeridos", corpo), encoding="utf-8")


def escolher(pasta: Path, opcao: dict) -> None:
    plano = pasta / "PLANO.md"
    corpo = f"**{opcao['titulo']}**: {opcao.get('resumo', '')}\n\n" + "".join(
        f"- [ ] {p}\n" for p in opcao.get("passos", []))
    plano.write_text(_trocar_secao(plano.read_text(encoding="utf-8"), "Caminho escolhido", corpo), encoding="utf-8")


def anotar(pasta: Path, texto: str) -> None:
    with open(pasta / "PLANO.md", "a", encoding="utf-8") as f:
        f.write(f"- ({datetime.now():%d/%m %H:%M}) {texto.strip()}\n")


def pendentes(pasta: Path) -> list[str]:
    plano = pasta / "PLANO.md"
    if not plano.exists():
        return []
    return [l[6:].strip() for l in plano.read_text(encoding="utf-8").splitlines() if l.startswith("- [ ] ")]


def listar(base: Path) -> list[Path]:
    if not base.exists():
        return []
    return sorted((p for p in base.iterdir() if (p / "PLANO.md").exists()), key=lambda p: p.stat().st_mtime,
                  reverse=True)


def achar(base: Path, nome_falado: str) -> Path | None:
    projetos = {p.name: p for p in listar(base)}
    chave = melhor_correspondencia(nome_falado, projetos)
    return projetos[chave] if chave else None


def plano_em_texto(pasta: Path) -> str:
    return (pasta / "PLANO.md").read_text(encoding="utf-8")
