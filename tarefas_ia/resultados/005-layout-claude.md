# Retorno do cartão 005 — Aurora no painel nativo

**Estado: `pronto_para_testar`** · Executor: Claude Code (Sonnet 5.5, esforço médio) · 30/09/2026
Sem commit, sem push. Branch `entrega/001-validacao-variada`, HEAD `a294459` (mudanças locais anteriores preservadas).

## Confirmações de partida
- Aurora está registrada em `design/layout-2026-09/ESCOLHA_LAYOUT.md`; a revisão do 004 existe (`resultados/004-revisao-codex.md`).
- Seguido: `GUIA_IMPLEMENTACAO.md` e o protótipo (`app.js`/`app.css`) como referência visual. Sem Electron, web, React ou dependência nova.

## O que foi feito (fatias do guia)
1. **Estrutura e tema** — `app/tema.py`: paletas Aurora clara (padrão) e noturna, `config.yaml > aparencia > modo`, títulos em Georgia (`fonte_titulo`). A configuração pessoal (cor, fundo, fonte, tamanho) continua valendo: o fundo escolhido vale no modo noturno; cores personalizadas são ajustadas para ficar legíveis. Avatar, bolinha e ícone mantêm a cor de sempre (`COR_INDICADOR`). Cores fixas do painel viraram tokens.
2. **Navegação e Visão geral** — o trilho/gaveta lateral saiu; entrou cabeçalho com marca, estado, busca (Ctrl+K) e botão Modo noturno/claro, mais 8 áreas no topo (Visão geral, Conversa, Voz e escuta, Mídias e telas, Rotinas, Memória, Evolução, Ajustes). Início ganhou **“Seu espaço, organizado”**.
3. **Agrupamento** — as 18 páginas antigas viraram botões sob o título da área; **IDs de `PAGINAS`/`SALVAR_PAGINA`, `_garantir_pagina`, `_montadas`, salvamento parcial e coletas em thread não mudaram**. Nova página **“Mídias e telas”** (suas telas, perfil, serviços, programas/sites e apelidos de monitor, com atalhos para YouTube, Spotify e Programas e sites).
4. **Evolução** — só apresentação: Validar atualização virou “Testar versão”, Melhorias “Ideias”. `app/validacao.py` e seus critérios não foram tocados.
5. **Acabamento** — ícones novos (lupa, sol, lua, seta, perfil), Tab/Enter/Espaço em todo botão com anel de foco e rolagem até o foco, barra do topo que encolhe em janela estreita.

Dados reais, sem demonstração: telas, janela em destaque, perfil (`Arthur Magnifico`, sem acento como está no seu config), canais, playlists, programas e sites vêm do Windows/config, lidos numa thread. Sem leitura de monitores aparece “Sem dados das telas”. Só leitura: nada move janela, fala ou mexe em serviço. Sem função nova (a conversa digitável do protótipo NÃO foi implementada; a página Conversa segue de configuração).

## Arquivos
- Novo: `app/layout.py` (áreas, busca e resumo do espaço, sem Tk).
- Alterados: `app/painel.py`, `app/tema.py`, `app/icones.py`, `app/avatar_janela.py` e `app/overlay.py` (só a cor do indicador), `testes/teste_regressoes_sem_interface.py` (testes do menu de gaveta trocados por 9 da navegação, busca, resumo do espaço, paleta e contraste), `testes/teste_basico.py` (trechos do bloco legado desativado), `ROTEIRO_VALIDACAO.md` (itens 001–009 e 057–060 reescritos para o layout novo, IDs mantidos), `GUIA_PASSO_A_PASSO.md` (seção 32.1), `CLAUDE.md` e `AGENTS.md` (linhas de painel/tema/layout; a regra do trilho fixo foi substituída pela do layout Aurora).
- Pequeno acréscimo: se existir `COPIA_DE_TESTE.txt` na pasta do projeto, a 1ª linha aparece no título e no cabeçalho.
- Versão do projeto **não** foi alterada (`app/versao.py`).

## Testes reais
- `venv\Scripts\python -m testes.teste_basico`: **147 testes OK** (mesmo total da base; 9 do menu antigo trocados por 9 novos) e **302 de 302 frases OK**, saída 0. Roda antes e depois de todas as mudanças.
- O bloco “legado” de `teste_basico.py` (janelas reais) continua desativado no projeto; não conta como cobertura.
- Contraste (WCAG) testado em claro/noturno para todas as cores e fundos: texto ≥ 7:1, texto de apoio ≥ 4,5:1, botão principal ≥ 4,5:1.
- Painel real aberto em cópia isolada (config real copiada para a caixa de areia, MESTRE_SIMULAR): 19 verificações OK — sem monitor inventado quando não há leitura, perfil vindo do config, Ctrl+K/Enter/Esc, Alt+1..8, Tab chega às 8 áreas, anel de foco, Enter/Espaço, reabrir área na página anterior, salvar parcial, botão de modo grava `modo: "escuro"` e reabre.
- Leitura real dos monitores (só leitura, fora da simulação): 3 telas detectadas em 0,01 s.
- Capturas conferidas: claro e noturno, 1180×800, 980×660 com texto “Maior”, página alta de Início e Mídias e telas. Cópia de teste aberta pelo caminho real (`app.iniciar_painel`) por ~14 s: abriu sem erro, título “· TESTE layout Aurora”.

## Cópia de teste e atalho
- Cópia: `C:\Ias\Mestre-TESTE-layout-aurora` (código + config real + memória; `modelos` é uma **junção** para `C:\Ias\Mestre-repo\modelos`, e usa o venv do repositório). Conferida por hash: idêntica ao repositório (exceto o trabalho de personagem de outra IA, abaixo).
- Atalho novo na Área de Trabalho: `Mestre - TESTE layout Aurora.lnk` → alvo `C:\Ias\Mestre-repo\venv\Scripts\pythonw.exe`, argumentos `-m app.central`, pasta `C:\Ias\Mestre-TESTE-layout-aurora` (os três conferidos lendo o atalho de volta).
- Atalhos de uso diário **não foram alterados**: `Assessor.lnk` (→ `C:\Ias\mestre\mestre`) e `Mestre.lnk` (→ `C:\Ias\Mestre-repo`). **Atenção:** `Mestre.lnk` roda o próprio repositório, que agora contém o layout Aurora; ele já vai abrir com o visual novo.
- Para apagar a cópia: remova antes a junção (`cmd /c rmdir C:\Ias\Mestre-TESTE-layout-aurora\modelos`), depois a pasta. Nunca apague com a junção dentro.

## Limitações e pontos de atenção
- Trocar o modo salva o que estiver editado e reabre a Central (o mesmo caminho do “Aplicar” da Aparência); não é troca instantânea.
- Tab chega em todos os botões; menus de escolha (OptionMenu/ComboBox), interruptores e caixas seguem só com o mouse.
- Não testado: escala 125/150% do Windows (só texto Grande/Maior), arraste entre três monitores, leitores de tela. Voz e monitores reais dependem do seu teste.
- Diagnóstico não virou item próprio: Atualizar .zip, Testar digitando e Teste automático ficam nos Atalhos rápidos da Visão geral.
- **Outra IA está editando em paralelo** (`app/personagem/` e `ferramentas/previa_personagem.py`, avatares, ainda sem commit, e uma sessão avisou que tocará em `painel.py`). Não mexi nisso e excluí da cópia de teste. Convém integrar as duas frentes em sequência para não haver conflito em `painel.py`/`tema.py`.
- Fechar o painel diário antes: a porta 47631 faz o painel já aberto ir para a frente em vez de abrir o de teste; e, ao testar voz, desligue o assistente diário (microfone).

## Roteiro humano curto (ver também ROTEIRO_VALIDACAO, itens 001–009 e 057–060)
1. Feche o painel e o assistente diários; abra `Mestre - TESTE layout Aurora`. Confira: título “TESTE layout Aurora”, visual claro, 8 áreas no topo.
2. Visão geral: veja “Seu espaço, organizado” com seus 3 monitores e o perfil; clique em “Abrir detalhes”.
3. Mídias e telas: telas, perfil, serviços e os botões YouTube, Spotify, Programas e sites.
4. Ctrl+K, digite “microfone”, Enter; depois Tab e Enter em um botão.
5. Clique em Modo noturno; reabre escuro; volte ao claro.
6. Arraste a janela até o tamanho mínimo e mude o texto para Maior (Ajustes > Aparência): nada cortado.
7. Ligue o assistente e fale um comando simples; faça uma etapa em Evolução > Testar versão.
8. Feche e reabra: o modo e as preferências continuam.
