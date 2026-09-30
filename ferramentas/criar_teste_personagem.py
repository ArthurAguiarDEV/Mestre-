"""Cria (ou atualiza) a CÓPIA DE TESTE do personagem e o atalho "Mestre - TESTE personagem" na área de trabalho.

Igual à cópia do layout Aurora: pasta separada ao lado desta (Mestre-TESTE-personagem), que usa o venv e os modelos
DESTA pasta, com um config próprio já com o personagem ligado (avatar > modelo: "personagem" e o indicador com
balão). O config.yaml de uso NÃO é tocado. Rodar de novo atualiza só o código (app, design, ferramentas...) e mantém o
config, a memória e as escolhas feitas no painel da cópia.

Uso: venv\\Scripts\\python -m ferramentas.criar_teste_personagem   (ou ferramentas\\criar_teste_personagem.bat)
Outra cópia de teste (ex.: a do Aurora), só o código:
     venv\\Scripts\\python -m ferramentas.criar_teste_personagem --so-codigo C:\\Ias\\Mestre-TESTE-layout-aurora
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ORIGEM = Path(__file__).resolve().parents[1]
DESTINO = ORIGEM.parent / "Mestre-TESTE-personagem"
NAO_COPIAR = ("venv", "modelos", "navegador_mestre", ".git", ".claude", ".agents", ".codex", "agentes_crewai", "logs",
              "exportacoes", "arquivo_morto", "_melhorias_claude", "tarefas_ia", "__pycache__", "*.pyc")
CODIGO = ("app", "design", "ferramentas", "testes", "extensao_brave", "prompts")   # sempre atualizados
DA_COPIA = {"config.yaml", "aprendido.yaml", "vocabulario.yaml", "MELHORIAS.md"}    # arquivos que a cópia guarda
ATALHO = "Mestre - TESTE personagem.lnk"


def atualizar_codigo(destino: Path) -> None:
    """Troca só o código (app, design, ferramentas...) e os arquivos soltos da raiz; config, memória e escolhas ficam."""
    ignorar = shutil.ignore_patterns(*NAO_COPIAR)
    for pasta in CODIGO:
        if (ORIGEM / pasta).exists():
            shutil.rmtree(destino / pasta, ignore_errors=True)
            shutil.copytree(ORIGEM / pasta, destino / pasta, ignore=ignorar)
    for arq in ORIGEM.iterdir():
        if arq.is_file() and arq.name not in DA_COPIA:
            shutil.copy2(arq, destino / arq.name)


def copiar() -> bool:
    """Cria a cópia (1ª vez) ou atualiza o código. Devolve True se criou agora."""
    if not DESTINO.exists():
        shutil.copytree(ORIGEM, DESTINO, ignore=shutil.ignore_patterns(*NAO_COPIAR), symlinks=True)
        novo = True
    else:
        novo = False
        atualizar_codigo(DESTINO)
    (DESTINO / "logs").mkdir(exist_ok=True)
    modelos = DESTINO / "modelos"
    if not modelos.exists():   # junção para os modelos daqui (não copia 15 GB)
        subprocess.run(["cmd", "/c", "mklink", "/J", str(modelos), str(ORIGEM / "modelos")], capture_output=True, check=False)
    (DESTINO / "COPIA_DE_TESTE.txt").write_text(
        "TESTE do personagem 2D\r\n"
        f"Copia de {ORIGEM} (com as alteracoes nao publicadas do cartao 006).\r\n"
        "Usa o venv e os modelos da pasta de origem. Nao e a instalacao de uso diario.\r\n"
        "Feche o outro Mestre/Assessor antes de abrir este (os dois disputam o microfone).\r\n"
        "Para atualizar depois de mudancas: ferramentas\\criar_teste_personagem.bat na pasta de origem.\r\n", encoding="utf-8")
    return novo


def ligar_personagem() -> None:
    """No config da CÓPIA: indicador com balão + avatar = personagem (mantém o visual já escolhido no painel da cópia)."""
    sys.path.insert(0, str(ORIGEM))
    from app import configuracao
    from app.personagem.opcoes import escrever_config, opcoes_do_config
    arq = DESTINO / "config.yaml"
    if not arq.exists():
        shutil.copy2(ORIGEM / "config.exemplo.yaml", arq)
    y = configuracao._yaml()
    with open(arq, encoding="utf-8") as f:
        c = y.load(f)
    configuracao.secao(c, "indicador")["tipo"] = configuracao.aspas("texto_avatar")
    av = c.get("avatar") or {}
    op = opcoes_do_config(c)
    escrever_config(c, "personagem", str(av.get("jeito") or ""), str(av.get("passeio") or "personalidade"), op["perfil"])
    with open(arq, "w", encoding="utf-8") as f:
        y.dump(c, f)


def criar_atalho() -> Path:
    area = Path(os.path.join(os.environ.get("USERPROFILE", str(Path.home())), "Desktop"))
    script = (
        "$w = New-Object -ComObject WScript.Shell;"
        f"$d = [Environment]::GetFolderPath('Desktop');"
        f"$s = $w.CreateShortcut((Join-Path $d '{ATALHO}'));"
        f"$s.TargetPath = '{ORIGEM / 'venv' / 'Scripts' / 'pythonw.exe'}';"
        "$s.Arguments = '-m app.central';"
        f"$s.WorkingDirectory = '{DESTINO}';"
        f"$s.IconLocation = '{DESTINO / 'app' / 'icone.ico'}';"
        "$s.Description = 'Mestre de TESTE com o personagem 2D (copia separada)';"
        "$s.Save()")
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script], check=True, capture_output=True)
    return area / ATALHO


def main() -> int:
    if len(sys.argv) > 2 and sys.argv[1] == "--so-codigo":   # outra cópia de teste (ex.: a do Aurora): só o código
        destino = Path(sys.argv[2]).resolve()
        if destino == ORIGEM or not (destino / "COPIA_DE_TESTE.txt").exists():
            print(f"{destino} não é uma cópia de teste (falta COPIA_DE_TESTE.txt): não mexi.")
            return 1
        atualizar_codigo(destino)
        print(f"Código atualizado em {destino} (config e memória da cópia mantidos)")
        return 0
    novo = copiar()
    ligar_personagem()
    atalho = criar_atalho()
    print(("Criei" if novo else "Atualizei") + f" a cópia de teste em {DESTINO}")
    print(f"Atalho na área de trabalho: {atalho.name}")
    print("Feche o outro Mestre/Assessor antes de abrir o de teste.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
