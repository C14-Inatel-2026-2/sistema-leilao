---
name: exportar-conversas-ia
description: >-
  Exporta conversas com IA para docs/conversas-ia/ e publica no GitHub.
  Use quando o usuário pedir para arquivar, exportar ou publicar conversas
  com IA, ou invocar /exportar-conversas-ia.
disable-model-invocation: true
---

# Exportar Conversas com IA

Arquiva a **transcrição literal** da conversa no repositório, conforme exigência acadêmica.

## Regra principal

O objetivo é uma **transcrição completa**: cada mensagem do usuário e cada resposta do assistente, **na íntegra**, na ordem em que ocorreram.

O arquivo `.jsonl` local do Cursor **não contém** as respostas completas — o Cursor grava `[REDACTED]` no disco. Por isso:

| Escopo | Método |
|---|---|
| **Conversa atual** | Agente transcreve do contexto da sessão (obrigatório) |
| **Últimas N** | Script lê `.jsonl` local (pode estar incompleto; avisar o usuário) |

## Checklist de execução

```
- [ ] 1. Perguntar autor
- [ ] 2. Perguntar escopo (atual ou últimas N)
- [ ] 3. Detectar ferramenta
- [ ] 4. Exportar transcrição literal
- [ ] 5. Mostrar resumo dos arquivos criados
- [ ] 6. Confirmar commit (se usuário aceitar)
- [ ] 7. Confirmar push (se usuário aceitar)
```

## Passo 1 — Identificar o autor

Pergunte sempre qual integrante é o autor:

- Caio
- Téo
- Pedro Vitor
- Pedro Paiva

## Passo 2 — Definir escopo

- **Conversa atual** — transcrever toda a sessão em andamento
- **Últimas N** — exportar N conversas do histórico local (pode ser parcial)

## Passo 3 — Detectar ferramenta

| Ferramenta | Como detectar |
|---|---|
| Cursor | Sessão no Cursor IDE |
| Antigravity | Sessão no Google Antigravity |
| Claude Code | Sessão no Claude Code |

## Passo 4 — Exportar transcrição literal

### Conversa atual (método principal)

1. Revise **todo** o histórico da sessão no seu contexto
2. Escreva a transcrição completa em um arquivo temporário, seguindo o formato abaixo
3. Salve com o script:

```bash
python tools/exportar-conversas/exportar_conversa.py \
  --modo transcrever \
  --autor "<nome>" \
  --ferramenta <cursor|claude|antigravity> \
  --titulo "<titulo-resumido-da-conversa>" \
  --corpo /caminho/para/transcricao.md \
  --repo-root .
```

**Alternativa:** escreva o arquivo final diretamente em `docs/conversas-ia/<pasta-do-autor>/` com frontmatter + corpo.

#### Formato obrigatório da transcrição

Cada troca de mensagem vira uma seção numerada. Inclua **todo o texto** que o usuário enviou e **todo o texto** que você respondeu — sem resumir, sem omitir.

```markdown
## Mensagem 1 — Usuário

<texto completo da primeira mensagem do usuário>

## Mensagem 2 — Assistente

<texto completo da sua primeira resposta, incluindo explicações, código citado e conclusões>

## Mensagem 3 — Usuário

<texto completo da segunda mensagem do usuário>

## Mensagem 4 — Assistente

<texto completo da sua segunda resposta>
```

Regras da transcrição:

- **Não resuma** — copie o conteúdo integral de cada turno
- **Não omita** respostas intermediárias — cada resposta sua é uma seção
- Ações de ferramenta podem aparecer como bloco dentro da mensagem do assistente:
  `> **Ferramenta:** \`Read\` — path: src/foo.py`
- Não inclua tokens, senhas ou conteúdo de `.env`

### Últimas N conversas (histórico local)

```bash
python tools/exportar-conversas/exportar_conversa.py \
  --modo jsonl \
  --autor "<nome>" \
  --ferramenta <cursor|claude|antigravity> \
  --escopo ultimas \
  --n <N> \
  --repo-root .
```

Avise o usuário que conversas antigas exportadas via `.jsonl` podem ter trechos redigidos pelo Cursor.

## Passo 5 — Resumo

Informe:

- Quantos arquivos foram criados
- Caminho em `docs/conversas-ia/<autor>/`
- Se a exportação é transcrição literal ou parcial (jsonl)

## Passo 6 — Commit (com confirmação)

**Nunca faça commit sem confirmação explícita.**

```bash
git add docs/conversas-ia/
git commit -m "docs: arquiva conversa(s) IA de <autor> (<ferramenta>)"
```

## Passo 7 — Push (com confirmação)

**Nunca faça push sem confirmação explícita.**

```bash
git push
```

## Mapeamento autor → pasta

| Autor | Pasta |
|---|---|
| Caio | `docs/conversas-ia/Caio/` |
| Téo | `docs/conversas-ia/Teo/` |
| Pedro Vitor | `docs/conversas-ia/Pedro-Vitor/` |
| Pedro Paiva | `docs/conversas-ia/Pedro-Paiva/` |

## Referência

Documentação completa em [docs/arquivamento-conversas-ia.md](../../docs/arquivamento-conversas-ia.md).
