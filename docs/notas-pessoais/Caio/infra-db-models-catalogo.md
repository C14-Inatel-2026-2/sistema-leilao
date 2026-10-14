# Nota pessoal — `feature/infra-db-models-catalogo`

**Autor:** Caio ([@caiosemblano](https://github.com/caiosemblano))
**Branch:** `feature/infra-db-models-catalogo` (a partir de `origin/dev`)
**Escopo:** guia de trabalho, **sem código de models pronto**. Procurar e implementar.

Isto não substitui [`docs/proximos-passos.md`](../../proximos-passos.md) nem [`docs/responsabilidades-equipe.md`](../../responsabilidades-equipe.md). É o roteiro da primeira entrega de persistência do catálogo.

A stack HTTP passou de Flask para FastAPI: **não** há Flask-Migrate nem `flask db`. Models herdam `infra.db.session.Base`; migrations rodam com Alembic puro.

---

## O que esta PR é (e o que não é)

**É:** schema + models ORM + migration das tabelas de catálogo.

**Não é:** repositories, casos de uso, routers FastAPI, JWT, jobs.

Pastas à espera: `infra/db/models/` (vazia). Já existem `infra/db/session.py`, `alembic.ini` e `infra/db/migrations/env.py`.

Regra de camadas: dataclasses em `domain/` **não** ganham SQLAlchemy. Models em `infra/db/models/` só espelham colunas. O domínio não importa FastAPI nem SQLAlchemy.

---

## Passo 0 — sessão e Alembic (já no repositório)

Não é preciso criar app HTTP para migrar. Conferir:

- `infra/db/session.py` — `engine`, `SessionLocal`, `class Base(DeclarativeBase)`, `get_db()`
- `infra/config.py` — `DATABASE_URL` via pydantic-settings
- `alembic.ini` — `script_location = infra/db/migrations`
- `infra/db/migrations/env.py` — usa `Base.metadata` e `settings.DATABASE_URL`

Quando os models existirem, **importá-los** em `env.py` (há um comentário no arquivo). Sem isso o autogenerate emite revision vazia.

Comandos:

```text
alembic revision --autogenerate -m "catalogo inicial"
alembic upgrade head
```

Conferir no `pyproject.toml` que `alembic` e `sqlalchemy` estão nas dependências.

---

## Passo 1 — inventário das colunas (ler, não inventar)

Abrir e anotar **campo → tipo Python → nullable?**

| Arquivo | O que extrair |
|---|---|
| `domain/categoria.py` | campos da dataclass |
| `domain/anuncio.py` | campos + enums `StatusAnuncio` e `TipoAnuncio` |
| `domain/leilao.py` | campos + enum `StatusLeilao` |
| `domain/lance.py` | campos; `Leilao` já tem `lances: list[Lance]` |

Tipos SQLAlchemy 2.0 para procurar:

| No domínio | Procurar |
|---|---|
| `UUID` | `SqlAlchemy Uuid mapped_column postgresql` |
| `Decimal` | `Numeric` vs `Float` (**não** usar Float para dinheiro) |
| `datetime` com fuso | `DateTime(timezone=True)` |
| `str, Enum` | `SQLAlchemy Enum` vs gravar o valor string |
| `bool` | `Boolean` |

Manter aberto: `docs/arquitetura.md` (camadas) e `docs/estrutura-e-stack.md` (`infra/db/models/`).

---

## Passo 2 — desenhar o schema antes de escrever classes

Responder isto no papel:

1. **Tabelas** — `categorias`, `anuncios`, `leiloes`, e provavelmente `lances`. Sem `lances` não dá para persistir o histórico do leilão depois.

2. **FKs que o domínio já declara**
   - `Anuncio.categoria_id` → categorias
   - `Anuncio.vendedor_id` e `Leilao.vendedor_id` → usuários
   - `Leilao.anuncio_id` → anúncios
   - `Anuncio.leilao_atual_id` → leilões (**ciclo** anúncio ↔ leilão)
   - `Lance.leilao_id` / `comprador_id`

3. **Usuário ainda não existe** (PR do Téo: `feature/infra-db-model-usuario`). Decidir com Pedro (guardião de banco): coluna UUID sem FK agora, ou esperar a tabela dele. **Não** criar `Usuario` nesta PR.

4. **Ciclo anúncio ↔ leilão** — procurar `SQLAlchemy circular foreign key use_alter` ou `ForeignKeyConstraint`.

5. **Índices** — status do leilão (job vai buscar “aberto + fim ≤ agora”), `categoria_id`, `vendedor_id`.

6. **MVP 1:1** — `docs/must-read.md` §2.2: um anúncio, no máximo um leilão ativo, via `leilao_atual_id`.

---

## Passo 3 — escrever os models

Arquivos em `infra/db/models/` (a pasta já existe vazia).

Procurar:

- SQLAlchemy 2.0 `DeclarativeBase` / `Mapped` / `mapped_column`
- Herdar de `infra.db.session.Base` (**não** `db.Model` do Flask-SQLAlchemy)
- `relationship()` one-to-many (`Leilao` → `Lance`)

Critérios:

- Sem métodos de negócio (`abrir`, `validar_lance`, `associar_leilao`) nas classes ORM. Isso fica em `domain/`.
- Enums de domínio podem ser reutilizados pelos nomes; evitar importar **entidades** de domínio nos models.
- `ondelete` / `nullable`: anúncio sem categoria inválido; leilão sem anúncio inválido; `leilao_atual_id` opcional.

---

## Passo 4 — gerar e aplicar a migration

Ordem: models → importar no `env.py` → `alembic revision --autogenerate` → `alembic upgrade head`.

Checar:

- `DATABASE_URL` = `postgresql://leilao:leilao@localhost:5432/leilao`
- models **importados** em `env.py` (senão a revision sai vazia)

Conferir: `\dt` no `psql` (localhost:5432). Esperar as tabelas e FKs desenhados no passo 2.

---

## Passo 5 — critério de pronto desta PR

- `domain/` intacto (sem SQLAlchemy lá)
- models só em `infra/db/models/`, herdando `Base`
- uma revision Alembic criando as tabelas de catálogo
- `alembic upgrade head` ok contra o Postgres do compose
- sem routers, sem repositories, sem `criar_anuncio`

Pedro revisa a migration. Se a tabela de usuário do Téo entrar antes, pode ser preciso uma revision seguinte só para as FKs.

---

## Depois desta PR (não fazer agora)

1. `feature/adapters-repositories-catalogo` — `anuncio_repository.py`, `leilao_repository.py` (CRUD, filtros, `SELECT ... FOR UPDATE` no leilão)
2. `feature/use-case-criar-anuncio` — `criar_anuncio.py`, depois `iniciar_leilao.py`
3. `feature/api-routes-catalogo` — `POST /anuncios`, `GET /anuncios` + schemas Pydantic

Papel contínuo: guardião do repositório — revisar PRs antes do merge em `dev`.

---

## Ambiente local

```text
git fetch origin
checkout a partir de origin/dev → feature/infra-db-models-catalogo
cp .env.example .env
docker compose up
```

Próximo ato: inventário no papel (passo 1) e models herdando `Base` (passo 3).
