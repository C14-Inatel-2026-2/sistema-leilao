---
autor: "Caio"
ferramenta: cursor
data_inicio: 2026-09-14T21:26:06-03:00
conversa_id: manual-20260914212606
titulo: "proxima-entrega-e-implementacao-categoria"
fonte: transcricao
---

## Mensagem 1 — Usuário

[Imagem anexada: requisitos da entrega acadêmica de testes unitários]

Texto visível na imagem:
- Cada membro do grupo deve realizar, no mínimo, 4 testes unitários, sendo 2 com mock e 2 sem mock, e um dos casos de teste sendo um teste negativo. Lembre-se de testar classes e seus métodos, e seguir boas práticas para criar esses testes
- Os testes unitários devem englobar tanto back-end quanto front-end (se tiver um), e para isso cabe o framework de escolha do grupo
- Toda trabalho feito deve ser commitado e seguindo...

Based on what I have done and what I'm planned to do in this project @docs/conversas-ia/Caio/ @docs/must-read.md @docs/proximos-passos.md .

What do I need to do for the next deliver?

## Mensagem 2 — Assistente

I'll read the project docs, your conversation notes, and the current code so I can map what's already done to the next deliverable.

> **Ferramenta:** `Read` — path: /home/csemblano/Dev/gh/sistema-leilao/docs/must-read.md
> **Ferramenta:** `Read` — path: /home/csemblano/Dev/gh/sistema-leilao/docs/proximos-passos.md
> **Ferramenta:** `Glob` — pattern: docs/conversas-ia/Caio/**
> **Ferramenta:** `Read` — path: .../assets/image-0c6cee2d-f1a0-43e1-a805-2fae67558cc8.png
> **Ferramenta:** `Glob` — pattern: docs/**/*.md
> **Ferramenta:** `Read` — docs/conversas-ia/Caio/2026-09-04_2047_cursor_primeira-tarefa-caio-must-read.md
> **Ferramenta:** `Read` — docs/responsabilidades-equipe.md
> **Ferramenta:** `Read` — domain/leilao.py, domain/anuncio.py, domain/categoria.py
> **Ferramenta:** `Read` — README.md, domain/usuario.py, domain/exceptions.py, docs/estrutura-e-stack.md, docs/arquitetura.md, pyproject.toml
> **Ferramenta:** `Grep` / agent transcripts — passo 1, testes, mock

The next course deliverable is **unit tests**, not models, API, or the next PR in `proximos-passos.md`. The screenshot sets the bar; your catalog domain is the code those tests should hit.

## What this deliverable requires (you)

Each member, independently:

| Requirement | What it means for you |
|---|---|
| **≥ 4 unit tests** | Yours, on *your* classes/methods |
| **2 without mock** | Direct tests on `Anuncio` / `Leilao` / `Categoria` |
| **2 with mock** | `unittest.mock` (`patch` / `MagicMock`) |
| **≥ 1 negative** | A case that must fail (`pytest.raises`) |
| **Backend + frontend** | Backend only — this project has no UI |
| **Commit** | On a feature branch, following the repo conventions |

pytest is already in `pyproject.toml`. There is still **no** `tests/unit/test_*.py` in the tree.

## What you already have vs what is missing

**Done (your catalog slice):**

- `domain/anuncio.py` — creation, 1:1 auction link, edit/inactivate/sold
- `domain/leilao.py` — states plus `abrir` / `receber_lance` / `encerrar` / `marcar_como_pago`
- Téo’s `Usuario` exists; scaffolding (`use_cases/`, `adapters/`) is empty
- Passo 1 was planned as `feature/domain-entidades-catalogo` (entities + unit tests)

**Not done (blocks this deliverable):**

- `domain/categoria.py` is **empty**
- Unit tests were written in a previous session (37 passing, no mocks) and **are not in the repo now** — they were never committed
- Nothing here uses a collaborator yet, so you still have **zero mocked tests**
- `use_cases/criar_anuncio.py` and repositories do not exist (those are later PRs)

Do **not** start `feature/infra-db-models-catalogo` for this hand-in. That is the PR *after* this one.

## What to implement

**1. Finish `Categoria`**
Name required, `ativa`, `inativar()` / `ativar()`. `Anuncio` already depends on `categoria_id`.

**2. Four tests that match the rubric** (you can add more)

Without mock (pure domain):

1. **Happy:** `Anuncio.associar_leilao` on an active listing with no auction
2. **Happy:** `Leilao.abrir` inside the time window → `ABERTO`
3. **Negative:** empty title → `AnuncioError`, or bid below increment → `LanceInvalidoError`

With mock (clock — these entities have no repos yet):

4. `patch` `datetime.now` so `abrir` is called *before* `data_inicio` → `EstadoLeilaoInvalidoError`
5. `patch` `datetime.now` so `receber_lance` runs *after* `data_final` → `LanceInvalidoError`

That is 2+ without mock, 2 with mock, and at least one negative. Test **methods**, not only constructors.

If you want mocks that look more like production (better for the course than only freezing time), add a thin `CriarAnuncio` that takes a repository `Protocol` and mock `save` / `get`. That is optional for the rubric and is already your later PR `feature/use-case-criar-anuncio`.

**3. Do not test frontend**
`docs/arquitetura.md` is API-only. Backend coverage is enough.

**4. Commit on `feature/domain-entidades-catalogo`**
From `dev`, include entities + tests + the 9 Sep conversation archive if you still want it. Flow: `feature/*` → PR → `dev`.

## Keep out of this hand-in

- SQLAlchemy models / migrations
- Flask routes
- Jobs, JWT, Jenkins
- Duplicating Pedro Vitor’s lance PR as a separate feature — your `Leilao` already has bid logic; **test it**, and align with him so you do not fight over `domain/leilao.py`

`proximos-passos.md` after this: `feature/infra-db-models-catalogo` → repositories → `CriarAnuncio` → catalog HTTP routes.

Run with:

```bash
poetry run pytest tests/unit -q
```

I’m in Ask mode, so I can’t add the files. Switch to Agent mode if you want this implemented on the branch.

## Mensagem 3 — Usuário

Implement categoria.py, do not create tests yet! Let's move slowly

## Mensagem 4 — Assistente

I'll implement `Categoria` to match the existing domain style, and leave tests out of this step.

> **Ferramenta:** `Read` — domain/categoria.py, domain/anuncio.py, domain/exceptions.py, domain/leilao.py (início)
> **Ferramenta:** `Grep` — Categoria
> **Ferramenta:** `Read` — docs/arquitetura.md (modelo de domínio)
> **Ferramenta:** `Write` — domain/categoria.py
> **Ferramenta:** `ReadLints` — domain/categoria.py (sem erros)

`domain/categoria.py` is in place, following the same shape as `Anuncio`.

**Fields:** `nome` (required), `ativa` (starts `True`), `id` (UUID), `criado_em`.

**Rules:** empty or whitespace-only name raises `CategoriaError`; the name is trimmed. `Anuncio` still only holds `categoria_id` — it does not import this class.

**Methods:** `esta_ativa()`, `inativar()`, `ativar()`.

No tests were added. Say when you want the next piece.

## Mensagem 5 — Usuário

/exportar-conversas-ia

(Skill anexada: exportar-conversas-ia — arquiva a transcrição literal da conversa no repositório.)

## Mensagem 6 — Assistente

To archive this chat I need two things:

1. **Author** — Caio, Téo, Pedro Vitor, or Pedro Paiva?
2. **Scope** — this conversation only, or the last N chats from local history?

## Mensagem 7 — Usuário

Caio
