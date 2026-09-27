"""Leitura do config.yaml e caminhos do projeto."""
import logging
import sys
from pathlib import Path

import yaml

PASTA_PROJETO = Path(__file__).resolve().parent.parent
ARQUIVO_CONFIG = PASTA_PROJETO / "config.yaml"
PASTA_LOGS = PASTA_PROJETO / "logs"
PASTA_NOTAS = PASTA_PROJETO / "notas"
PASTA_RESPOSTAS = PASTA_PROJETO / "respostas"
PASTA_PERFIS = PASTA_PROJETO / "perfis"
PASTA_MODELOS = PASTA_PROJETO / "modelos"

# config.yaml e do usuario e fica fora do git: numa instalacao nova, comeca pelo exemplo
if not ARQUIVO_CONFIG.exists() and (PASTA_PROJETO / "config.exemplo.yaml").exists():
    import shutil
    shutil.copyfile(PASTA_PROJETO / "config.exemplo.yaml", ARQUIVO_CONFIG)


def carregar_config() -> dict:
    try:
        with open(ARQUIVO_CONFIG, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as erro:
        print("\n*** ERRO NO config.yaml ***")
        print("Provavelmente um TAB, recuo errado ou aspas faltando.")
        print(erro)
        sys.exit(1)


def caminho_do_projeto(relativo: str) -> Path:
    caminho = Path(relativo)
    return caminho if caminho.is_absolute() else PASTA_PROJETO / caminho


def configurar_log() -> None:
    PASTA_LOGS.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%d/%m %H:%M:%S",
        handlers=[
            logging.FileHandler(PASTA_LOGS / "mestre.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def gerar_variacoes(palavra: str) -> list[str]:
    """Jeitos parecidos de o reconhecimento escrever a palavra de ativacao.

    'mestre' -> ['mestre', 'mestres', 'mestra', 'mestri', 'mestro', 'mestr']
    """
    from .texto import normalizar

    p = normalizar(palavra).split()[-1] if normalizar(palavra) else "mestre"
    variacoes = [p, p + "s"]
    if p[-1] in "aeiou":
        variacoes += [p[:-1] + v for v in "aeio" if p[:-1] + v != p] + ([p[:-1]] if len(p) >= 5 else [])
    return list(dict.fromkeys(variacoes))


def palavras_ativacao(cfg: dict) -> list[str]:
    """A palavra de ativacao (a primeira) e suas variacoes."""
    from .texto import normalizar

    a = cfg.get("assistente") or {}
    palavra = normalizar(a.get("palavra_ativacao") or "mestre").split()[-1] if normalizar(a.get("palavra_ativacao") or "") else "mestre"
    extras = [normalizar(v) for v in (a.get("variacoes_aceitas") or []) if normalizar(v)]
    if extras and extras[0] != palavra:  # a palavra mudou: variacoes antigas nao valem mais
        extras = []
    return list(dict.fromkeys(gerar_variacoes(palavra) + extras))
