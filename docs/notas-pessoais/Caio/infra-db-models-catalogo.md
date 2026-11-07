# Nota pessoal — próximo passo imediato: `feature/infra-db-models-catalogo`

**Autor:** Caio ([@caiosemblano](https://github.com/caiosemblano))
**Branch:** `feature/infra-db-models-catalogo` (recriar a partir de `origin/dev`)
**Escopo:** guia da primeira entrega de persistência do catálogo. Sem código pronto.

Visão da sequência completa em [`roteiro-geral-pos-fastapi.md`](roteiro-geral-pos-fastapi.md). Isto não substitui [`docs/proximos-passos.md`](../../proximos-passos.md).

A stack HTTP passou de Flask para FastAPI: **não** há Flask-Migrate nem `flask db`. Models herdam de uma `DeclarativeBase` do SQLAlchemy 2.0; migrations rodam com Alembic puro. **Não** é preciso subir a app FastAPI para migrar.

---

## Estado local a conferir antes de começar

No checkout recente (out/2026):

- Branch local errada: `feature/infra-db-model-usuario` (tarefa do **Téo**).
- `infra/db/models/categoria.py` existe, mas está vazio.
- `infra/db/models/.gitkeep` foi removido (ainda não commitado).
- `origin/feature/infra-db-models-catalogo` está **atrás** de `dev` — não reutilizar sem atualizar.

Corrigir o git **antes** de escrever models:

```text
git fetch origin
git switch -c feature/infra-db-models-catalogo origin/dev
# se a branch local já existir desatualizada, recriar a partir de origin/dev
cp .env.example .env
docker compose up -d
```

Levar o `categoria.py` vazio só se ainda fizer sentido na branch certa; senão descartar e recriar no Passo 3.

---

## O que esta PR é (e o que não é)

**É:** `Base` + models ORM + uma migration Alembic das tabelas de catálogo.

**Não é:** repositories, casos de uso, routers FastAPI, JWT, jobs, model de `Usuario`.

Já existe `infra/api/app.py` com healthcheck para o pipeline. Não mexer nisso nesta PR.

Regra de camadas: dataclasses em `domain/` **não** ganham SQLAlchemy. Models em `infra/db/models/` só espelham colunas. O domínio não importa FastAPI nem SQLAlchemy.

---

## Passo 0 — ambiente, `Base` e Alembic

Dependências já no `pyproject.toml`: `sqlalchemy`, `alembic`, `psycopg2-binary`.

`DATABASE_URL` do `.env.example`: `postgresql://leilao:leilao@localhost:5432/leilao` (Postgres 16 no compose).

Criar a base do SQLAlchemy (ex.: `infra/db/session.py` ou `infra/db/base.py`):

- `class Base(DeclarativeBase): pass`
- `create_engine(DATABASE_URL)`
- `sessionmaker(...)` (`autoflush=False`, `autocommit=False`) — a sessão será usada depois no `Depends(get_db)` do FastAPI; nesta PR basta existir para o Alembic e para os models herdarem `Base`.

Inicializar o Alembic **uma vez**:

```text
poetry run alembic init infra/db/migrations
```

Gera `alembic.ini` e `infra/db/migrations/env.py`. No `env.py`:

- Ler `DATABASE_URL` do ambiente e configurar `sqlalchemy.url`.
- `target_metadata = Base.metadata`.
- **Importar todos os models** antes do autogenerate (senão a revision sai vazia).

---

## Passo 1 — inventário das colunas (ler `domain/`, não inventar)

Anotar **campo → tipo Python → nullable?** a partir das dataclasses.

### `categorias` ← `domain/categoria.py`

| Campo | Tipo no domínio | Nullable |
|---|---|---|
| `id` | `UUID` | não (PK, default `uuid4`) |
| `nome` | `str` | não |
| `ativa` | `bool` | não (default `True`) |
| `criado_em` | `datetime` (UTC) | não |

### `anuncios` ← `domain/anuncio.py`

Enums: `StatusAnuncio` (`ATIVO`, `INATIVO`, `VENDIDO`) e `TipoAnuncio` (`VENDA_DIRETA`, `LEILAO`).

| Campo | Tipo no domínio | Nullable |
|---|---|---|
| `id` | `UUID` | não (PK) |
| `titulo` | `str` | não |
| `descricao` | `str` | não |
| `preco_referencia` | `Decimal` | não |
| `categoria_id` | `UUID` | não → `categorias.id` |
| `vendedor_id` | `UUID` | não → usuários (ver Passo 2) |
| `tipo` | `TipoAnuncio` | não (default `VENDA_DIRETA`) |
| `status` | `StatusAnuncio` | não (default `ATIVO`) |
| `leilao_atual_id` | `UUID \| None` | sim → `leiloes.id` (ciclo) |
| `criado_em` | `datetime` (UTC) | não |

### `leiloes` ← `domain/leilao.py`

Enum: `StatusLeilao` (`AGENDADO`, `ABERTO`, `ENCERRADO`, `PAGO`, `CANCELADO`).

| Campo | Tipo no domínio | Nullable |
|---|---|---|
| `id` | `UUID` | não (PK) |
| `anuncio_id` | `UUID` | não → `anuncios.id` |
| `vendedor_id` | `UUID` | não → usuários (ver Passo 2) |
| `preco_inicial` | `Decimal` | não |
| `incremento_minimo` | `Decimal` | não |
| `data_inicio` | `datetime` | não |
| `data_final` | `datetime` | não |
| `status` | `StatusLeilao` | não (default `AGENDADO`) |
| `vencedor_id` | `UUID \| None` | sim |
| `valor_arremate` | `Decimal \| None` | sim |
| `criado_em` | `datetime` (UTC) | não |
| `lances` | `list[Lance]` | não é coluna — tabela `lances` |

### `lances` ← `domain/lance.py`

| Campo | Tipo no domínio | Nullable |
|---|---|---|
| `id` | `UUID` | não (PK) |
| `leilao_id` | `UUID` | não → `leiloes.id` |
| `comprador_id` | `UUID` | não → usuários (ver Passo 2) |
| `valor` | `Decimal` | não |
| `criado_em` | `datetime` (UTC, com tzinfo) | não |

Tipos SQLAlchemy 2.0 para procurar:

| No domínio | No model |
|---|---|
| `UUID` | `Uuid` / `mapped_column` PostgreSQL UUID |
| `Decimal` (dinheiro) | `Numeric` — **nunca** `Float` |
| `datetime` com fuso | `DateTime(timezone=True)` |
| `str, Enum` | `Enum` do SQLAlchemy **ou** gravar o valor string |
| `bool` | `Boolean` |

Manter aberto: [`docs/arquitetura.md`](../../arquitetura.md) e [`docs/estrutura-e-stack.md`](../../estrutura-e-stack.md).

---

## Passo 2 — desenhar o schema antes de escrever classes

1. **Tabelas:** `categorias`, `anuncios`, `leiloes`, `lances`. Sem `lances` não dá para persistir o histórico do leilão depois.

2. **FKs que o domínio já declara**
   - `Anuncio.categoria_id` → `categorias`
   - `Anuncio.vendedor_id` e `Leilao.vendedor_id` → usuários
   - `Leilao.anuncio_id` → `anuncios`
   - `Anuncio.leilao_atual_id` → `leiloes` (**ciclo** anúncio ↔ leilão)
   - `Lance.leilao_id` / `comprador_id`

3. **Usuário ainda não existe** (PR do Téo: `feature/infra-db-model-usuario`). Decidir com Pedro (guardião de banco): coluna UUID sem FK agora, ou esperar a tabela dele. **Não** criar `Usuario` nesta PR.

4. **Ciclo anúncio ↔ leilão** — procurar `SQLAlchemy circular foreign key use_alter` ou `ForeignKeyConstraint`. `leilao_atual_id` precisa de `use_alter=True` (ou equivalente).

5. **Índices** — `leiloes.status` (job vai buscar “aberto + fim ≤ agora”), `anuncios.categoria_id`, `vendedor_id`.

6. **MVP 1:1** — [`docs/must-read.md`](../../must-read.md) §2.2: um anúncio, no máximo um leilão ativo, via `leilao_atual_id`.

7. **`ondelete` / nullable:** anúncio sem categoria inválido; leilão sem anúncio inválido; `leilao_atual_id` opcional.

---

## Passo 3 — escrever os models

Arquivos em `infra/db/models/`. Herdar de `infra.db.session.Base` (ou o módulo que o Passo 0 criar) — **não** `db.Model` do Flask-SQLAlchemy.

Procurar: SQLAlchemy 2.0 `DeclarativeBase` / `Mapped` / `mapped_column` / `relationship()`.

Esboço do mapeamento (confirmar tipos no Passo 1):

- `categoria.py` — `__tablename__ = "categorias"`
- `anuncio.py` — `__tablename__ = "anuncios"`; `preco_referencia` como `Numeric`; `leilao_atual_id` com FK circular
- `leilao.py` — `__tablename__ = "leiloes"`; `preco_inicial` / `incremento_minimo` / `valor_arremate` como `Numeric`; `relationship` 1:N para lances
- `lance.py` — `__tablename__ = "lances"`; `valor` como `Numeric`

Critérios:

- Sem métodos de negócio (`abrir`, `validar_lance`, `associar_leilao`) nas classes ORM. Isso fica em `domain/`.
- Enums de domínio podem ser reutilizados **pelos nomes**; evitar importar **entidades** de domínio nos models.
- `__tablename__` no plural, em português, como na lista do Passo 2.

---

## Passo 4 — gerar e aplicar a migration

Ordem: models → importar no `env.py` → autogenerate → upgrade.

```text
poetry run alembic revision --autogenerate -m "create catalogo tables"
poetry run alembic upgrade head
```

Checar:

- `DATABASE_URL` aponta para o Postgres do compose.
- Models **importados** em `env.py` (senão a revision sai vazia).
- `\dt` no `psql` (localhost:5432): esperar `categorias`, `anuncios`, `leiloes`, `lances` e as FKs do Passo 2.

---

## Passo 5 — critério de pronto desta PR

- `domain/` intacto (sem SQLAlchemy lá); `poetry run pytest` nos unitários atuais continua passando.
- Models só em `infra/db/models/`, herdando `Base`.
- Uma revision Alembic criando as tabelas de catálogo.
- `alembic upgrade head` ok contra o Postgres do compose.
- Sem routers, sem repositories, sem `criar_anuncio`, sem model de `Usuario`.

Pedro ([@phpaiva05](https://github.com/phpaiva05)) revisa a migration. Se a tabela de usuário do Téo entrar antes, pode ser preciso uma revision seguinte só para as FKs.

---

## Depois desta PR (não fazer agora)

Sequência completa em [`roteiro-geral-pos-fastapi.md`](roteiro-geral-pos-fastapi.md). Em resumo:

1. `feature/adapters-repositories-catalogo`
2. `feature/use-case-criar-anuncio` (+ `iniciar_leilao.py`)
3. `feature/api-routes-catalogo`

Papel contínuo: guardião do repositório — revisar PRs antes do merge em `dev`.
