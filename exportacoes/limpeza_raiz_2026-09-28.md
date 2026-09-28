# Limpeza da raiz do projeto — 28/09/2026

Revisão conservadora dos arquivos soltos na raiz (não mexi em `.claude/`, `.agents/`, `.codex/`,
`AGENTS.md`, nem em pastas do próprio app: `app/`, `logs/`, `memoria/`, `modelos/`, `venv/`,
`navegador_mestre/`, `perfis/`, `notas/`, `recebidos/`, `respostas/`, `testes/`, `ferramentas/`,
`extensao_brave/`). Só movi (nunca apaguei) o que tinha CERTEZA que nada usa — conferido com grep
em todo o projeto (`.py`, `.bat`, `.vbs`, `.md`, `.json`), no `INSTALAR_E_CRIAR_ATALHO.bat` e no
`atualizar.py`/`OBSOLETOS.txt`.

## Movidos para `arquivo_morto/` (nada foi apagado)

| Arquivo | Por que |
|---|---|
| `CHECKLIST_VALIDACAO.md` | O próprio `ROTEIRO_VALIDACAO.md` diz: "Este arquivo substitui o antigo CHECKLIST_VALIDACAO.md". Zero referências no resto do projeto. |
| `SKILL.md` (raiz) | Cópia antiga e desatualizada da skill `refinar-pedido`. A skill de verdade, mais nova, mora em `.claude/skills/refinar-pedido/SKILL.md` (essa eu não toquei). Nada no projeto aponta para o arquivo da raiz. |
| `config_novidades_v2.yaml` | Rascunho de "novidades do config.yaml na versão 2", já superado pelo `config.exemplo.yaml` atual (que tem os mesmos campos, ex. `conversa: janela_segundos`, com valores mais novos). Zero referências. |
| `_tmp_segredos_demo/` (pasta vazia) | Nome já diz "_tmp"/"demo"; estava vazia e sem nenhuma referência no projeto. |

Se algum desses fizer falta, está tudo em `arquivo_morto/` (não em outro lugar) e é só devolver para a raiz.

## Revisados e NÃO movidos (ficam onde estão)

| Arquivo/pasta | Por que não mexi |
|---|---|
| `config.yaml.bak` | Cópia de segurança que o próprio `app/configuracao.py` escreve sozinho a cada vez que salva o `config.yaml`. É um arquivo "vivo" (o painel usa e recria), não sobra. |
| `config.yaml.antes_do_conserto` | Idem: gerado pelo `configuracao.py` quando conserta uma seção duplicada do seu `config.yaml`. Documentado no `GUIA_PASSO_A_PASSO.md`. |
| `_melhorias_claude/` | Usado por `ferramentas/14_instalar_melhorias_claude.bat` (copia o conteúdo para dentro de `.claude/`). Ainda é o pacote de instalação. |
| `README.md`, `requirements.txt`, `INSTALAR_E_CRIAR_ATALHO.bat`, `iniciar_oculto.vbs`, `OBSOLETOS.txt` | Usados pela instalação/atualização. |
| `aprendido.yaml`, `vocabulario.yaml`, `config.yaml`, `config.exemplo.yaml` | Configuração ativa do Assessor. |
| `MELHORIAS.md`, `ROTEIRO_VALIDACAO.md`, `GUIA_PASSO_A_PASSO.md` | Documentos vivos, atualizados a cada entrega. |

## Sobre o `OBSOLETOS.txt`

Não acrescentei nada nele. Esse arquivo é o mecanismo que a ATUALIZAÇÃO POR ZIP usa para apagar
arquivos antigos na máquina de QUALQUER usuário que atualizar (ex.: os `.bat` numerados de versões
anteriores). Os 4 itens movidos acima são arquivos que sobraram só NESTE projeto (não fazem parte do
pacote que é distribuído no zip), então colocá-los no `OBSOLETOS.txt` apagaria arquivos de quem talvez
os tenha por outro motivo. Prefiro que você revise a lista acima e decida.

## Dúvida (não mexi, só listo)

Nenhum outro arquivo da raiz ficou sem explicação clara de uso — os candidatos "capengas" que eu
cheguei a considerar (os dois `config.yaml.*` de backup) são gerados pelo próprio programa e não
contam como lixo.
