# Personagem do Assessor — por onde começar

## Ver agora (1 minuto)

1. Abra **`index.html`** (duplo clique). Ele funciona sozinho, sem internet (só a fonte do título vem da internet; sem ela usa outra).
   Também está publicado como link privado (o endereço está no retorno `tarefas_ia/resultados/006-avatar-personagem-claude.md`).
2. O boneco aparece no **canto de baixo da tela**. **Arraste** para onde quiser; **clique** nele e ele reage.
3. Abas: **Corpo**, **Cabelo**, **Roupa**, **Fantasia** (Marvel e DC), **Extras**, **Jeito**. Ao lado: estados
   (ouvindo, pensando, falando, descansando), **Fazer falar** (usa a voz do navegador, se houver em português), gestos, passear sozinho.
4. O quadro **Para usar no Assessor** mostra o trecho do `config.yaml` com o que você montou (botão Copiar).

Imagens prontas para olhar sem abrir nada: `imagens/` (fantasias, cabelos, roupas, acessórios, poses de fala/reverência/pulo).

## Usar no Assessor

Painel > **Aparência** > **Personagem no lugar do robozinho** > Avatar = **Personagem** > salvar > `Mestre, reinicia`.
Voltar ao robozinho: Avatar = Robozinho. Se o personagem der erro, o robozinho aparece sozinho.

## Arquivos

| Arquivo | Para que serve |
|---|---|
| `index.html` / `artefato.html` | A página de teste pronta (gerada; `artefato.html` é a mesma sem `<html>`, para publicar como Artefato) |
| `modelo.html`, `demo.js`, `personagem.js` | Fonte da página (visual, interface, desenhista/animador em Canvas) |
| `imagens/` | Folhas de contato geradas pelo Qt (`ferramentas/previa_personagem.py`) |

Depois de mexer no catálogo (`app/personagem/catalogo_*.py`) ou nesta pasta, regenere:

```powershell
venv\Scripts\python -m ferramentas.gerar_demo_personagem
```

O teste automático (`testes/teste_personagem.py`) avisa se `index.html`/`artefato.html` ficaram desatualizados.

## Acrescentar coisas

- **Herói novo:** escreva `_meu_heroi(g)` em `app/personagem/catalogo_trajes.py` (Marvel) ou `catalogo_trajes_dc.py` (DC) usando as
  peças prontas (`capa`, `bota_alta`, `luva`, `cinto`, `estrela`, `raio`, `capuz`, `cabeca_cheia`...) e registre na tabela do fim do arquivo.
- **Cabelo:** uma entrada em `catalogo_cabelos.py` (`tras` fica atrás do corpo, `frente` cobre a testa).
- **Gesto/jeito:** clipe em `catalogo_animacao.py` (`CLIPES`) e, para um jeito, a lista `idle` de `ARQUETIPOS`.
- Depois: regenerar a página e rodar `venv\Scripts\python -m testes.teste_basico`.

As fantasias são versões inspiradas (cores e formas simples, sem logotipos oficiais), para uso pessoal.
