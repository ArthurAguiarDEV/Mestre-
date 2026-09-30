# Novo layout do Mestre — especificação de integração

Data: 30/09/2026. Responsável pelo estudo: ChatGPT/Codex.
Base examinada: `C:\Ias\Mestre-repo`, HEAD `a294459`.
Escolha do usuário: pendente, registrada em `ESCOLHA_LAYOUT.md`.

## O que foi examinado

- `app/painel.py`: 18 entradas de PAGINAS, menu de ícones com gaveta, janela inicial
  1180 × 800 e mínimo 980 × 660; páginas sob demanda e salvamento por página montada.
- `app/tema.py`: cores/fontes configuráveis, paletas atuais escuras; o nome interno
  ROSA é usado para o destaque mesmo quando a cor escolhida não é rosa.
- `app/icones.py`: ícones próprios em Pillow; não requer pacote externo de ícones.
- Painel do código atual executado em cópia temporária com configuração de exemplo,
  MESTRE_SIMULAR e perfil APPDATA isolado. Início e Áudio examinados visualmente.
  Não foi uma leitura das configurações pessoais completas do usuário.
- Prints anteriores do usuário: etapa de teste com frase/resultado esperados conflitantes
  e uma janela sem responder. A mudança visual não prova a correção desses defeitos.

O visual atual tem fonte manuscrita e navegação compacta por ícones. A tela de áudio
mistura seleção de dispositivo, calibração, gravação e reconhecimento na mesma rolagem.
O estudo propõe tipografia de leitura, rótulos visíveis, hierarquia e divulgação gradual
dos ajustes avançados.

## Três propostas, três estruturas

| Aspecto | Órbita | Aurora | Pulso |
|---|---|---|---|
| Ideia | Central de ações do dia | Espaço pessoal editorial | Estação de controle |
| Navegação | Lateral de 220 px com nomes | Horizontal, agrupada por intenção | Trilho de 94 px com legendas |
| Foco inicial | Conversa, estado, atalhos, telas | Saudação, rituais e mídia | Mapa dos monitores e próximos controles |
| Tipografia | Segoe UI | Georgia em títulos, Segoe UI no corpo | Bahnschrift em títulos, Consolas em dados, Segoe UI no corpo |
| Ícones | Linha arredondada de 1,65 px | Linha leve de 1,35 px | Linha de 2 px, cantos mais retos |
| Geometria | Cartões de 18 px | Cartões de 24 px, mais espaço | Cartões de 9 px, densidade moderada |
| Cor inicial | Verde grafite + menta | Marfim + ameixa | Azul profundo + azul elétrico |
| Tema alternativo | Claro verde | Noturno ameixa | Claro azulado |

Recomendação de design: Órbita, pelo equilíbrio entre descoberta de funções e uso
diário. Aurora privilegia leitura e Pulso privilegia controle de telas. Essa recomendação
não substitui a escolha do usuário. Pode haver combinação, desde que descrita antes
da implementação; não implementar três temas estruturais completos no app por padrão.

## Mapa completo: nenhum recurso desaparece

Os IDs abaixo são os IDs atuais de PAGINAS e SALVAR_PAGINA. Os rótulos podem mudar;
os IDs e chaves de configuração não devem ser renomeados na primeira migração.

| Página atual | Área nova (Órbita como vocabulário de referência) | Destino |
|---|---|---|
| Início | Visão geral | Status, ligar/parar/pausar/reiniciar, fila e atalhos |
| Personalidade | Ajustes | Personalidade e forma de chamar |
| Voz | Voz e escuta | Aba Voz: motor, velocidade, reserva |
| Áudio | Voz e escuta | Abas Escuta e Meu reconhecimento |
| Conversa | Conversa | Configurações do modo de conversa e IA; manter disponíveis |
| Projeto | Rotinas | Aba Projetos; conferir acesso hoje ausente de GRUPOS_MENU |
| YouTube | Mídia e telas | Serviços → YouTube; canais e perfis de streaming |
| Spotify | Mídia e telas | Serviços → Spotify; playlists e controles existentes |
| Programas e sites | Mídia e telas | Aba Programas e sites, destinos de monitor |
| Rotinas | Rotinas | Rotinas existentes, edição e comandos ensinados |
| Atalhos | Rotinas | Aba Atalhos |
| Celular | Ajustes | Conexões → Celular e Telegram |
| Histórico | Memória | Histórico e Lembranças |
| Aparência | Ajustes | Aparência: tema, fonte, texto, indicador/avatar existente |
| Melhorias | Evolução | Ideias e feedback |
| Validar atualização | Evolução | Testar versão |
| Sugestões de melhoria | Evolução | Sugestões |
| Tempos | Memória | Desempenho; sem valores inventados |

Ações de atualizar por zip, testar digitando e diagnóstico presentes no Início continuam
acessíveis na Visão geral ou em Ajustes → Diagnóstico. Avatar atual continua configurável;
desenhar um avatar novo pertence a outra etapa.

## Tokens e componentes

`app.css` é a referência visual executável, inclusive para os seis conjuntos de cores.
Tokens: --bg, --panel, --raised, --line, --text, --muted, --accent, --ink, --soft, --warn,
--radius e --font-title. Nunca substituir cores em dezenas de lugares sem um tema central.

- Espaçamento base 4/8/12/16/24/32; páginas com limite de largura.
- Títulos hierárquicos; corpo nativo entre 14 e 16 px e textos de apoio pelo menos 12 px.
  As fontes são locais do Windows com fallback. Não baixar fontes ou usar CDNs.
- Ações principais de 44 px ou mais no app; alvos de toque 44 px quando aplicável.
- Ícone sempre acompanhado de rótulo nas funções importantes; tooltip nos utilitários.
- Estados: disponível, ocupado, pausado, desligado, sem dados e erro com próxima ação.
- Indicadores não dependem só de cor. Mensagens de erro explicam como continuar.
- Tab percorre em ordem lógica; foco visível; Esc fecha gaveta/busca/dialog.
- Preferência de movimento reduzido desliga animações; ondas são decorativas.

## Adaptação do tamanho

O HTML foi feito para avaliação de layout, inclusive em 390 px. Isso não cria um aplicativo
de celular nem converte o projeto desktop em site. No aplicativo nativo, adaptar ao tamanho
da janela e à escala do Windows é a prioridade.

- ≥ 1280 px: navegação completa, cartões em duas/três colunas.
- 980–1279 px: conteúdo condensado com títulos legíveis.
- 800–979 px: uma coluna principal; navegação compacta ou gaveta com rótulos.
- Protótipo de 390 px: referência para empilhamento e menus; não prometer esse mínimo
  no CustomTkinter antes de validar os controles existentes.
- Conferir 100%, 125% e 150% de escala, texto maior, arraste entre três monitores,
  maximizar/restaurar e nenhuma janela fora da área visível.

## O que o protótipo faz e o que ainda é conceito

Funciona na demonstração: navegação de oito áreas/subabas, claro/escuro, busca local,
tecla Ctrl+K, pausar o estado visual, campos/controles, conversa fictícia, quatro etapas
de teste com resultados e nova rodada, baixar opinião e relatório demonstrativo.

Não há integração com microfone, APIs, streaming, configurações reais, arquivos pessoais
ou execução de comandos. O protótipo identifica dados ilustrativos. Nomes/perfil usados
vêm do pedido do usuário. Cenários e atividades não são histórico real.

Cuidados ao integrar:

- A conversa digitável no protótipo é uma hipótese visual. A página Conversa atual é de
  configuração. Só ativar o envio real se houver adaptador existente e revisado; caso
  contrário, manter configurações e criar cartão próprio para essa funcionalidade.
- O mapa de monitores deve ler dados existentes em segundo plano; mostrar “sem dados”
  se a ponte não estiver disponível. Não criar comandos de janelas ou assumir três telas.
- Exemplos de rotinas não devem ser gravados na configuração do usuário.
- O nome, apelido e palavra de ativação vêm da configuração na versão integrada.
- Botões de mídia usam apenas ações existentes após resolver serviço/perfil/destino.
  A frase “O que deseja assistir?” não comprova implementação de regra nova de perfil.

## Validação e feedback fáceis

Uma tela mostra: preparo necessário, uma fala/ação, resultado observável, três respostas
(funcionou / deu problema / não consegui testar) e comentário opcional. Detalhes técnicos
ficam recolhidos. Falha fica registrada; resultado não testado nunca conta como aprovado.

No protótipo, quatro exemplos variam dentro de um conjunto local. Na versão real, manter
IDs, proveniência, cobertura por arquivos alterados, falhas recentes e regressões essenciais
do mecanismo existente em `app/validacao.py`. Diversidade de frases é complementar;
sortear perguntas isoladamente não garante teste relevante.

Ao concluir: resumo legível e ação explícita para preparar o retorno da IA. Não dizer
“enviado ao Claude” quando apenas salvou um arquivo. Encaminhamento continua conforme
o fluxo do 004. Não publicar, mandar mensagens ou fechar feedback automaticamente.

## Fatias de implementação

1. **Estrutura e tema:** extrair componentes visuais para módulo pequeno; tokens claro/escuro,
   fontes e tamanhos, usando CustomTkinter. Não reescrever `painel.py` inteiro nem trocar toolkit.
2. **Navegação e Visão geral:** aplicar a estrutura escolhida, nomes, busca de funções e
   estado real. Preservar páginas existentes e IDs. Reorganização que precisa mudar a regra
   antiga de trilho fixo deve ser documentada nas instruções como parte do layout escolhido.
3. **Agrupamento:** hospedar páginas existentes nas novas áreas e preservar suas funções
   `_salvar_*`, `_montadas`, `_garantir_pagina` e trabalho de coleta em threads.
4. **Evolução:** simplificar apresentação de instruções e retorno sem alterar indevidamente
   seleção, captura ou critério de aprovação dos testes.
5. **Acabamento:** ícones nativos, foco, espaçamento, erros, vazio, desempenho e escala.

Para cada fatia: testes apropriados; uma execução final da suíte do projeto; inspeção
visual. Não executar rotinas reais, downloads de modelos ou comandos de desligamento
para verificar aparência. Processamento pesado continua fora da thread da interface.

## Entrega ao usuário

Criar cópia de validação e atalho com nome inequívoco, por exemplo
`Mestre — TESTE layout [modelo]`. Conferir TargetPath, Arguments e WorkingDirectory.
Não prometer atalho existente antes de criá-lo e verificá-lo. Registrar a base, limitações,
resultado dos testes e caminho da cópia. Manter o atalho de uso diário.

Teste humano da interface escolhida: abrir; achar microfone e mídia; alternar tema;
redimensionar; realizar uma validação curta; fechar/reabrir e conferir preferências.
Voz/monitores são testes funcionais separados. Publicação só após a autorização da entrega.

## Reprodução da prévia

Abrir `index.html` no navegador, diretamente no PC. Não precisa instalar nada.
`app.html?modelo=orbita|aurora|pulso` identifica a proposta; `tema=light|dark` escolhe tema.
`verificar_ui.cjs` usa uma instalação existente de Playwright; variáveis opcionais:
PLAYWRIGHT_MODULE (caminho do módulo) e BROWSER_CHANNEL (nesta máquina, msedge).
As capturas e `verificacao-ui.json` são saídas geradas dessa verificação.
