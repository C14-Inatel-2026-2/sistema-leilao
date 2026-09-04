---
autor: "Caio"
ferramenta: cursor
data_inicio: 2026-09-04T20:47:32-03:00
conversa_id: manual-20260904204732
titulo: "primeira-tarefa-caio-must-read"
fonte: transcricao
---

## Mensagem 1 — Usuário

A partir do @docs/must-read.md o que eu, Caio Semblano, devo fazer como primeira tarefa? @docs/

## Mensagem 2 — Assistente

Vou cruzar o `must-read.md` com os docs de responsabilidades e próximos passos para identificar sua primeira tarefa.

> **Ferramenta:** `Read` — path: /home/csemblano/Dev/gh/sistema-leilao/docs/must-read.md
> **Ferramenta:** `Read` — path: /home/csemblano/Dev/gh/sistema-leilao/docs/responsabilidades-equipe.md
> **Ferramenta:** `Read` — path: /home/csemblano/Dev/gh/sistema-leilao/docs/proximos-passos.md
> **Ferramenta:** `Glob` — pattern: docs/**/*

Sua **primeira tarefa de código** é abrir a branch `feature/domain-entidades-catalogo` e implementar as entidades de domínio do seu escopo, com testes unitários.

## O que fazer

Conforme [`proximos-passos.md`](docs/proximos-passos.md) e [`responsabilidades-equipe.md`](docs/responsabilidades-equipe.md), o primeiro PR seu é:

**`feature/domain-entidades-catalogo`**
- `domain/categoria.py`
- `domain/anuncio.py`
- `domain/leilao.py` (máquina de estados e regras de criação)
- Testes em `tests/unit/` (sem Flask, sem banco)

Isso alinha com a **Fase 1** do `must-read.md`: domínio + testes unitários antes de repositórios, API ou jobs.

## Antes de codar (imediato)

1. Ambiente: `.env` a partir do `.env.example` (se ainda não estiver ok).
2. Branch a partir de `dev`: `feature/domain-entidades-catalogo`.
3. Como **Guardião do Repositório**, garantir que o fluxo `feature/* → PR → dev` esteja claro para o time.

## Ordem no time

Na sequência sugerida de PRs, o seu vem logo após o do Téo (`feature/domain-usuario`). Você pode começar o domínio de catálogo em paralelo, mas alinhe com o Pedro Vitor o contrato de `Leilao` (estados e campos), porque ele vai complementar as regras de lance em `domain/leilao.py`.

**Resumo:** primeira entrega sua = entidades `Categoria` / `Anuncio` / `Leilao` + testes unitários na branch `feature/domain-entidades-catalogo`.

## Mensagem 3 — Usuário

/exportar-conversas-ia

(Skill anexada: exportar-conversas-ia — arquiva a transcrição literal da conversa no repositório.)

## Mensagem 4 — Assistente

Para arquivar a conversa, preciso de dois dados:

1. **Autor** — Caio, Téo, Pedro Vitor ou Pedro Paiva?
2. **Escopo** — conversa atual, ou últimas N do histórico local?

## Mensagem 5 — Usuário

Caio, conversa atual

## Mensagem 6 — Assistente

Vou transcrever a sessão atual e arquivar em `docs/conversas-ia/Caio/`.

> **Ferramenta:** `Read` — path: tools/exportar-conversas/exportar_conversa.py
> **Ferramenta:** `Glob` — pattern: docs/conversas-ia/Caio/*
> **Ferramenta:** `Read` — path: docs/arquivamento-conversas-ia.md
> **Ferramenta:** `Read` — path: docs/conversas-ia/Caio/2026-09-01_1741_cursor_skill-arquivar-conversas-ia.md
> **Ferramenta:** `Grep` — pattern: modo transcrever|--corpo|--titulo
> **Ferramenta:** `Shell` — escreveu transcrição temporária e executou `exportar_conversa.py --modo transcrever`
