---
name: exportar-conversas-ia
description: >-
  Exporta conversas com IA para docs/conversas-ia/ e publica no GitHub.
  Use quando o usuário pedir para arquivar, exportar ou publicar conversas
  com IA, ou invocar /exportar-conversas-ia.
disable-model-invocation: true
---

# Exportar Conversas com IA

Arquiva conversas com IA no repositório, conforme exigência acadêmica do projeto.

## Quando usar

- Usuário pede para arquivar, exportar ou publicar conversa(s) com IA
- Usuário invoca `/exportar-conversas-ia` ou `@exportar-conversas-ia`

## Checklist de execução

```
- [ ] 1. Perguntar autor
- [ ] 2. Perguntar escopo (atual ou últimas N)
- [ ] 3. Detectar ferramenta
- [ ] 4. Executar script de exportação
- [ ] 5. Mostrar resumo dos arquivos criados
- [ ] 6. Confirmar commit (se usuário aceitar)
- [ ] 7. Confirmar push (se usuário aceitar)
```

## Passo 1 — Identificar o autor

Pergunte sempre qual integrante é o autor da conversa:

- Caio
- Téo
- Pedro Vitor
- Pedro Paiva

## Passo 2 — Definir escopo

Pergunte o escopo:

- **Conversa atual** — exporta apenas a sessão mais recente
- **Últimas N** — exporta as N conversas mais recentes (pedir o valor de N)

## Passo 3 — Detectar ferramenta

Identifique a ferramenta ativa:

| Ferramenta | Como detectar |
|---|---|
| Cursor | Sessão no Cursor IDE |
| Antigravity | Sessão no Google Antigravity |
| Claude Code | Sessão no Claude Code (CLI ou extensão) |

Se não for possível detectar, pergunte ao usuário.

## Passo 4 — Executar exportação

Na raiz do repositório, execute:

```bash
python tools/exportar-conversas/exportar_conversa.py \
  --autor "<nome>" \
  --ferramenta <cursor|claude|antigravity> \
  --escopo atual \
  --repo-root .
```

Para últimas N conversas:

```bash
python tools/exportar-conversas/exportar_conversa.py \
  --autor "<nome>" \
  --ferramenta <cursor|claude|antigravity> \
  --escopo ultimas \
  --n <N> \
  --repo-root .
```

### Fallback Antigravity

Se o script não encontrar conversas do Antigravity:

1. Reconstrua a conversa atual manualmente em Markdown
2. Use o template em [docs/arquivamento-conversas-ia.md](../../docs/arquivamento-conversas-ia.md)
3. Salve em `docs/conversas-ia/<pasta-do-autor>/` com o padrão de nome:
   `YYYY-MM-DD_HHmm_antigravity_<slug-titulo>.md`

### Fallback sem transcript local

Se nenhum arquivo local for encontrado, exporte a conversa atual do contexto da sessão usando o mesmo template Markdown.

## Passo 5 — Resumo

Informe ao usuário:

- Quantos arquivos foram criados
- Caminho de cada arquivo em `docs/conversas-ia/<autor>/`
- Se houve redação de possíveis segredos (revisar antes do commit)

## Passo 6 — Commit (com confirmação)

**Nunca faça commit sem confirmação explícita.**

Pergunte: "Deseja criar o commit com os arquivos exportados?"

Se sim:

```bash
git add docs/conversas-ia/
git commit -m "docs: arquiva conversa(s) IA de <autor> (<ferramenta>)"
```

## Passo 7 — Push (com confirmação)

**Nunca faça push sem confirmação explícita.**

Pergunte: "Deseja fazer push para o GitHub?"

Se sim:

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
