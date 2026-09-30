"""Layout Aurora do painel: quais areas existem, que paginas cada uma reune e o resumo de "Seu espaco".

Sem Tk: o painel (app/painel.py) so desenha o que sai daqui e o teste confere sem abrir janela.
Os IDs das paginas (chaves de painel.PAGINAS e SALVAR_PAGINA) NAO mudam: so o agrupamento e os rotulos.
"""
from __future__ import annotations

from .texto import normalizar

# id da area, rotulo, [(pagina, rotulo na barra da area)]. A 1a pagina de cada area e a que abre ao clicar nela.
AREAS: list[tuple[str, str, list[tuple[str, str]]]] = [
    ("visao", "Visão geral", [("Início", "Início")]),
    ("conversa", "Conversa", [("Conversa", "Conversa")]),
    ("voz", "Voz e escuta", [("Áudio", "Escuta e reconhecimento"), ("Voz", "Voz")]),
    ("midias", "Mídias e telas", [("Mídias e telas", "Visão geral"), ("YouTube", "YouTube"),
                                  ("Spotify", "Spotify"), ("Programas e sites", "Programas e sites")]),
    ("rotinas", "Rotinas", [("Rotinas", "Rotinas"), ("Atalhos", "Atalhos"), ("Projeto", "Projetos")]),
    ("memoria", "Memória", [("Histórico", "Histórico e lembranças"), ("Tempos", "Desempenho")]),
    ("evolucao", "Evolução", [("Validar atualização", "Testar versão"), ("Melhorias", "Ideias"),
                              ("Sugestões de melhoria", "Sugestões")]),
    ("ajustes", "Ajustes", [("Aparência", "Aparência"), ("Personalidade", "Personalidade"),
                            ("Celular", "Conexões")]),
]

# palavras que a busca ("Buscar no Mestre", Ctrl+K) entende, alem dos rotulos
PALAVRAS = {
    "Início": "inicio visao geral ligar desligar pausar reiniciar fila comandos atualizar zip diagnostico teste",
    "Personalidade": "nome apelido palavra de ativacao estilo frases jeito de chamar",
    "Voz": "motor kokoro edge azure elevenlabs windows velocidade reserva falar",
    "Áudio": "microfone escuta calibrar ganho whisper reconhecimento minha voz detector saida de som",
    "Conversa": "ia ollama claude cidade modo conversa pensando segundo plano",
    "Projeto": "projeto projetos guiados plano claude",
    "YouTube": "canais inscricoes perfis streaming netflix disney prime hbo globoplay",
    "Spotify": "musica playlists tocar",
    "Programas e sites": "programas sites abrir monitor nomes de monitores navegador brave",
    "Mídias e telas": "servicos perfil monitores telas destinos youtube spotify netflix disney streaming",
    "Rotinas": "rotinas sequencia acoes frases",
    "Atalhos": "atalhos ensinados frases curtas",
    "Celular": "celular telegram conexoes audios pasta sincronizada avisos do pc",
    "Histórico": "historico pedidos respostas lembrancas memoria fatos ouvi entendi",
    "Aparência": "tema modo claro noturno escuro cores fonte tamanho texto indicador avatar bolinha",
    "Melhorias": "melhorias ideias feedback claude code",
    "Validar atualização": "validar testar versao roteiro etapas",
    "Sugestões de melhoria": "sugestoes melhorias diarias",
    "Tempos": "tempos desempenho medidas etapas lentidao",
}


def area_de(pagina: str) -> str:
    """O id da area que reune a pagina."""
    for area, _rotulo, paginas in AREAS:
        if any(p == pagina for p, _ in paginas):
            return area
    return AREAS[0][0]


def rotulo_area(area: str) -> str:
    return next(r for a, r, _ in AREAS if a == area)


def paginas_da_area(area: str) -> list[tuple[str, str]]:
    return next(p for a, _r, p in AREAS if a == area)


def rotulo_pagina(pagina: str) -> str:
    """Nome da pagina na barra da area (o ID interno continua o de PAGINAS)."""
    for _a, _r, paginas in AREAS:
        for p, rotulo in paginas:
            if p == pagina:
                return rotulo
    return pagina


TITULOS = {"Mídias e telas": "Mídias e telas"}   # titulo grande da pagina quando difere do rotulo da barra


def titulo_pagina(pagina: str) -> str:
    return TITULOS.get(pagina) or rotulo_pagina(pagina)


def buscar(texto: str, limite: int = 7) -> list[str]:
    """Paginas que combinam com o texto (rotulo, area ou palavra-chave; sem acento e sem maiuscula)."""
    palavras = normalizar(texto or "").split()
    if not palavras:
        return []
    achadas: list[tuple[int, int, str]] = []
    ordem = 0
    for area, rotulo_a, paginas in AREAS:
        for pagina, rotulo in paginas:
            ordem += 1
            nome = normalizar(f"{rotulo} {pagina} {rotulo_a}")
            resto = normalizar(PALAVRAS.get(pagina, ""))
            if all(p in nome or p in resto for p in palavras):
                # rotulo que comeca com o texto vem antes; depois quem acerta no nome; depois so na palavra-chave
                peso = 0 if nome.startswith(palavras[0]) or normalizar(rotulo).startswith(palavras[0]) else \
                    1 if all(p in nome for p in palavras) else 2
                achadas.append((peso, ordem, pagina))
    return [p for _, _, p in sorted(achadas)][:limite]


# --- Seu espaco, organizado: resumo lido do config e da mesa (nada de exemplo) ---------------------------
def montar_espaco(cfg: dict, monitores: list[dict] | None, janelas_ativas: dict[int, str] | None,
                  streamings: list[str], perfis: list[str], perfil_padrao: str = "") -> dict:
    """Resumo para os cartoes "Seu espaco, organizado" e "Mídias e telas".

    `monitores` vazio/None = nao deu para ler as telas (mostra "sem dados", nunca inventa monitor).
    `perfis` sao so nomes (perfis_configurados). Nada aqui abre janela, fala ou mexe em serviço.
    """
    canais = cfg.get("canais_youtube") or {}
    playlists = (cfg.get("spotify") or {}).get("playlists") or {}
    programas = cfg.get("programas") or {}
    sites = cfg.get("sites") or {}
    nomes = {}
    for numero, nome in ((cfg.get("janelas") or {}).get("nomes_monitores") or {}).items():
        try:
            nomes[int(numero)] = str(nome)
        except (TypeError, ValueError):
            continue
    if perfis:
        detalhe_perfil = f"Perfil padrão: {perfil_padrao}" if perfil_padrao else \
            "Perfil: " + ", ".join(perfis) if len(perfis) == 1 else "Perfis: " + ", ".join(perfis)
    else:
        detalhe_perfil = "Nenhum perfil cadastrado"
    servicos = [{"nome": "YouTube", "tipo": "video",
                 "detalhe": (f"{len(canais)} canal cadastrado" if len(canais) == 1 else f"{len(canais)} canais cadastrados")
                 if canais else "Nenhum canal cadastrado"}]
    servicos += [{"nome": n, "tipo": "streaming", "detalhe": detalhe_perfil} for n in streamings]
    servicos.append({"nome": "Spotify", "tipo": "musica",
                     "detalhe": (f"{len(playlists)} playlist cadastrada" if len(playlists) == 1
                                 else f"{len(playlists)} playlists cadastradas") if playlists
                     else "Nenhuma playlist cadastrada"})
    telas = []
    for m in monitores or []:
        numero = int(m.get("numero") or len(telas) + 1)
        telas.append({
            "numero": numero, "principal": bool(m.get("principal", numero == 1)),
            "descricao": str(m.get("descricao") or "monitor"),
            "resolucao": f"{m['largura']}×{m['altura']}" if m.get("largura") and m.get("altura") else "",
            "apelido": nomes.get(numero, ""),
            "janela": str((janelas_ativas or {}).get(numero) or ""),
        })
    return {
        "servicos": servicos, "perfis": list(perfis), "perfil_padrao": perfil_padrao, "monitores": telas,
        "monitores_lidos": bool(telas),
        "programas": len(programas), "programas_amostra": [str(p) for p in list(programas)[:6]],
        "sites": len(sites), "sites_amostra": [str(s) for s in list(sites)[:6]],
    }
