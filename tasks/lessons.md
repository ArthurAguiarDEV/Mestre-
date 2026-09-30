# Lições aprendidas

Uma linha por correção do dono: `erro → regra`. Máximo ~30 linhas (junte ou apague as antigas).
Quem trabalha no projeto (Claude e ChatGPT/Codex) lê este arquivo no começo da sessão.

<!-- exemplo: - Chamei o Ollama direto na escuta → sempre passar por self._pensar(...). -->

- Usei `secao` como variável de laço na montagem de uma página → não sombrear funções locais usadas no mesmo método; testar a montagem da página sem abrir janela.
- Gerador de tarefas mandava prompt para Manus/Ollama e sugeria Sonnet/Opus ao ChatGPT → só ChatGPT/Codex e Claude recebem tarefas; Ollama é o motor de IA local do app/CrewAI, não destinatário; Sonnet/Opus são do Claude e o ChatGPT usa o modelo do app (texto de prompt não muda o seletor).
- Cor fixa com sufixo (`"#3B2F38-"`) saiu inválida no desenho do personagem → toda cor do catálogo passa por `arte.resolver_cor` (aceita `#hex` ou `$ficha` com `+`/`-`); o teste confere que TODA cor resolvida é `#RRGGBB`. Depois de mexer em `app/personagem/` ou em `design/avatar-2026-09/`, rode `ferramentas.gerar_demo_personagem` (a página de teste é gerada do catálogo).
- Abri várias janelas Qt no mesmo processo de verificação e o Python caiu (segfault) → uma janela por processo, como no uso real; e `after()` do Tk chamado de thread só funciona com o `mainloop` rodando (em teste, use `mainloop` com `after(..., quit)`).
- Instrução de repasse mandava commit/push por conta própria → o repasse é local, por arquivos, e commit/push só com autorização específica para aquela entrega (OK para publicar).
- Entreguei o personagem só com a página no navegador e o dono não achou como abrir no programa (o config dele usa a bolinha e o personagem estava escondido em Aparência) → entrega visual para validar vem com cópia de teste + atalho próprio na área de trabalho (`ferramentas/criar_teste_personagem.bat`, igual ao do Aurora), sem tocar o config de uso.
- Animação "travada": a página pintava a 24 quadros/s parada e cada ponto-chave parava seco (suavização por trecho); o antebraço direito girava ao contrário (herdava o espelho) → curva contínua (monotônica) entre pontos, molas de inércia nos braços/cabelo/capa, `inv` nos nós filhos de nó espelhado e conferir poses em imagem (`previa_personagem --animar`) antes de entregar.
