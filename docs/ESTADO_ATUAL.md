# Estado verificado do Mestre — 30/09/2026

## Qual é a versão atual?

O código mais recente está em **C:\Ias\Mestre-repo**: layout Aurora e personagem opcional, incluindo a integração 007. É uma versão candidata, com testes automáticos aprovados e aceite físico pendente. A versão interna ainda é 2.6; não foi gerado um novo pacote de atualização.

Para conferir Aurora e personagem juntos, use **Mestre - TESTE personagem**, em **C:\Ias\Mestre-TESTE-personagem**. Feche o outro Assessor antes, pois compartilham microfone e portas. A comparação inicial encontrou os mesmos 163 arquivos em `app`, `testes`, `ferramentas`, `design` e `extensao_brave` nas duas cópias de teste e no repositório.

O atalho **Assessor** abre `C:\Ias\mestre\mestre`, uma linha mais antiga. **Mestre** e **Assessor - Validacao nova** abrem `Mestre-repo`. **Assessor - Teste B1+B2** abre a integração separada. Os alvos foram lidos dos atalhos reais; não foram alterados.

## Testes: fatos desta auditoria

| Verificação | Resultado | O que prova |
|---|---|---|
| Suíte segura atual, `python -m testes.teste_basico` | 195 testes OK; 302/302 frases | Lógica e regressões cobertas, sem efeitos físicos |
| Arquivos selecionados para commit, em cópia isolada sem dados pessoais | 195 testes OK; 302/302 frases | A candidata também passa usando somente os arquivos da publicação e o ambiente Python existente |
| `python -m ferramentas.verificar_personagem` | TUDO CERTO | Renderização Qt sem tela, estados e equivalência JS/Python; não prova voz real |
| Suíte da integração B1+B2 em 1fe641b | 84 testes, 7 falhas | Essa cópia não está pronta para incorporar |
| Módulo B1+B2 executado isoladamente | 30 testes, mesmas 7 falhas | Falhas reproduzidas fora da suíte completa |
| Duas cópias de teste versus código atual | 0 divergências em 163 arquivos | Código das cópias sincronizado na auditoria |
| Arquivamento | 41 itens, hashes e diretórios conferidos | Conteúdo preservado nos movimentos |

Além dos 41 itens da raiz, cinco retornos históricos foram preservados por hash em `tarefas_ia/arquivo/resultados`. O mapa adicional está em `auditoria-2026-09-30/movimentacoes-internas.json`. Não foi uma nova instalação das dependências: a cópia isolada usou o ambiente existente no PC.

As sete falhas B1+B2 estão nos cenários de parada e eco de `testes.teste_comandos_noite.ParaNaoVaiParaIA`. A causa ainda precisa de investigação; falha de teste não identifica sozinha uma falha do microfone. A execução parou antes das frases: não se declara aprovação das frases dessa cópia.

O último relatório físico localizado em `Mestre-repo/exportacoes/validacao_2026-09-29_2359.md` é anterior ao código visual atual e identifica o commit **63a77f2**: **7 itens aprovados e 5 com falha** (17 etapas: 11 aprovadas e 6 falhas). Falhas: saída de som, volume/transcrição, fala de fundo/Telegram, cancelamento do pensamento e retorno do descanso. O texto “nenhum teste físico pendente” dentro desse relatório vale para aquele roteiro executado, não para as funcionalidades acrescentadas depois.

## O que aconteceu

1. Pacotes iniciais e atualizações v2–v13: evolução por ZIP. O Diário PDF documenta até v10; não representa o estado atual.
2. 28–29/09: reorganização inicial, painel, métricas e isolamento dos testes; o bloco gráfico legado foi desativado e parte da cobertura recuperada sem efeitos reais.
3. 29/09: validação por modos e cartão 001, com `fe65b4b`; o trabalho paralelo B1+B2 chegou a `53087e6`, depois integração `f65fb1c` e ajuste `1fe641b`.
4. GitHub consultado nesta auditoria: `main` e `entrega/001-validacao-variada` apontavam para **a294459**. O `main` local estava atrasado; não era a fonte do estado remoto.
5. 30/09: organização inicial 003, revisão 004, Aurora 005, personagem 006 e integração 007; os últimos trabalhos estavam no disco, sem commit.
6. Auditoria 008: consulta real ao Claude Code em leitura, inventário, reserva, testes independentes, arquivamento e documentação corrigida. Branch desta entrega: `revisao/auditoria-2026-09-30`.

## Escopo do produto

Assistente pessoal Windows em Python: palavra de ativação → áudio/transcrição → vocabulário/roteamento → comando ou IA → resposta por voz e indicador. Inclui programas/janelas/mídia, ditado, memória, rotinas, painel de configuração, validação e feedback. Ollama é motor local; Claude é colaborador de desenvolvimento e uma integração opcional já existente. O protótipo CrewAI não é necessário para executar o assistente.

Prioridade: comandos de voz confiáveis, interrupção previsível e configurações preservadas. Aurora e personagem são apresentação da mesma base. Não ampliar funções enquanto o comportamento básico ainda tem falhas sem diagnóstico.

## Organização e dependências

| Local | Papel | Decisão |
|---|---|---|
| `C:\Ias\01_ATUAL` | Entrada de leitura para o trabalho atual | Índice; não duplica código |
| `C:\Ias\02_EM_VALIDACAO` | Entrada de leitura para testes e pendências | Índice; sem pacote chamado estável |
| `C:\Ias\Mestre-repo` | Fonte de desenvolvimento atual | Mantida no caminho original |
| `C:\Ias\Mestre-TESTE-personagem` e `Mestre-TESTE-layout-aurora` | Cópias de avaliação | Mantidas; configurações próprias |
| `C:\Ias\mestre\mestre` | Código antigo, dados e ambiente compartilhado | Não é lixo: sustenta venv e modelos |
| `C:\Ias\mestre\integracao_b1_b2` | Experimento integrado de voz | Bloqueado por sete falhas atuais |
| `C:\Ias\mestre\noite_claude` e `review_card_001` | Worktrees de implementação/revisão | Preservados com Git e alterações locais |
| `C:\Ias\03_ARQUIVO` | ZIPs antigos e versões extraídas | Arquivados sem apagar |
| `C:\Ias\04_REFERENCIAS` | PDFs, guias antigos, vídeos, pesquisas e skills exportadas | Histórico, não instrução atual |
| `C:\Ias\auditoria-2026-09-30` | Inventário, hashes, logs, consulta e reserva local | Material local; não publicar a reserva |

`Mestre-repo/venv` e `modelos` são junções para `mestre/mestre`. As cópias de teste também usam os modelos compartilhados. Não mover esses caminhos sem um plano de migração dos ambientes, atalhos e worktrees. As instruções exportadas em `04_REFERENCIAS/skills-exportadas` são cópias; as habilidades instaladas ficam no perfil do usuário.

Dentro do repositório, `app`, `testes`, `ferramentas`, `extensao_brave` e `perfis` permanecem nos caminhos usados pelo programa. `design` guarda estudos e demonstrações; `tarefas_ia` guarda o fluxo Codex/Claude; `agentes_crewai` é protótipo. `arquivo_morto` e `tarefas_ia/arquivo` preservam histórico. `_melhorias_claude`, `.agents` e `.codex` não foram classificados como descartáveis.

## Propostas em ordem de valor

| Prioridade | Proposta | Aceite e motivo | Custo relativo |
|---|---|---|---|
| P0 | Diagnosticar as 7 falhas B1+B2 antes de integrar | Suíte isolada e completa verdes; conferir diferenças entre B1+B2 e a linha atual | Médio |
| P0 | Resolver as cinco falhas reais por camada | Comparar OUVI/ENTENDI/FIZ; áudio ruim no reconhecimento, roteamento no comando, cancelamento no estado; teste de regressão para cada correção | Alto |
| P0 | Separar versão de uso, candidata e histórico | Um atalho de uso após aceite; identificação clara de branch/build; evitar testar código antigo por engano | Médio |
| P1 | Rever interrupção e retomada como estados explícitos | “Assessor, para” interrompe; “pode falar” retoma somente a resposta guardada; TV sem ativação ignorada | Alto |
| P1 | Completar acessibilidade do Aurora | Menus, caixas e réguas de todas as páginas acessíveis por teclado, com foco real | Médio |
| P1 | Identificar a versão em cada evidência | Relatório registra commit, alterações locais e hashes, sem depender apenas do número 2.6 | Pequeno |
| P1 | Painel de testes usar a palavra configurada | Roteiro mostra Assessor/Jarvis conforme configuração, sem confundir nome do usuário com ativação | Pequeno |
| P1 | Consolidar fila em uma fonte de estado | Índices gerados a partir do cartão; não repetir tarefa já implementada | Médio |
| P2 | Migrar gradualmente o legado gráfico para testes isolados | Cobertura documentada em `testes/COBERTURA_LEGADA.md`, sem voltar a criar efeitos reais na suíte segura | Alto |
| P2 | Conjunto local de áudios consentidos para regressão | Amostras com transcrição esperada e métricas por cenário; armazenamento local e descarte definido | Médio |
| P2 | Desacoplar ambiente/modelos da cópia antiga | Plano de migração e reversão; só depois arquivar a antiga instalação | Alto |

Alternativa de arquitetura: manter o monólito modular e extrair apenas estado de conversa e lógica de interface que precisem de testes. Reescrever tudo ou acrescentar mais agentes agora aumentaria o custo sem resolver as falhas observadas. Ajuste fino de modelos, novas vozes e mais fantasias ficam depois das métricas do reconhecimento, latência e interrupção. Publicação como produto exige revisão própria das referências visuais de terceiros; esta auditoria não fez análise jurídica.

## O que funcionou e o que falhou no processo

Funcionou: barreira contra efeitos reais, testes de frases, estados gráficos comparados em Python/JS, retornos em arquivo e cópias isoladas para avaliação. Falhou: índices atrasados, mudanças simultâneas no painel citadas pelo Claude, nomes de versão iguais para códigos distintos, dados de uso rastreados pelo Git e falta de uma evidência física ligada à candidata atual.

Nesta entrega, `aprendido.yaml` e `MELHORIAS.md` foram retirados do rastreamento nos próximos commits, mantendo os arquivos locais. Filas e prompts gerados, execuções e histórico local das IAs ficaram fora da publicação. Isso não remove dados de commits antigos: o histórico Git não foi reescrito. A reserva local contém dados pessoais e não deve ser enviada ao GitHub.

O gerador de tarefas foi conferido em diretório temporário: dois pedidos produziram duas tarefas e quatro prompts, somente para Codex e Claude, sem criar filas Manus/Ollama.

Manus permanece apenas no histórico. A consulta desta auditoria foi uma nova execução do Claude Code, autenticada na instalação existente, com ferramentas de leitura. Não foi continuação nem leitura automática de todos os chats antigos. O retorno está na pasta local de auditoria.

## Limites e próxima decisão

A auditoria percorreu as 47 entradas originais da raiz, inventariou arquivos próprios, comparou 14 cópias de código, inspecionou os 18 ZIPs e extraiu os dois PDFs. Ambientes de terceiros, modelos, caches e objetos internos do Git foram identificados, mas não auditados arquivo a arquivo. Vídeos/áudios foram preservados e inventariados; não foram todos transcritos ou assistidos. Não é uma certificação de todo o código, hardware ou histórico de conversas.

A candidata pode ser revisada visualmente. Ainda não está comprovada a experiência completa de voz, foco real do teclado, escala de tela e uso prolongado. Os resultados de teste, mesmo verdes, não substituem essa evidência.

Próxima etapa de implementação proposta: diagnosticar B1+B2 e corrigir as falhas reais na linha candidata, com testes antes de qualquer promoção a versão de uso. A organização e a preservação do histórico são uma entrega separada dessa correção funcional.
