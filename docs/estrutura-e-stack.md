# Estrutura de Diretórios e Stack

Organização do repositório e tecnologias adotadas.

**Estado (out/2026):** `domain/` e testes unitários estão implementados; `use_cases/cadastrar_usuario.py` existe. `adapters/` e `infra/` ainda são scaffolding vazio. O que falta, e em que ordem, está em [`proximos-passos.md`](proximos-passos.md).

---

## Árvore de diretórios

```text
sistema-leilao/
├── domain/                     # Entidades e regras puras (Python puro)
│   ├── usuario.py
│   ├── anuncio.py
│   ├── leilao.py
│   ├── lance.py
│   ├── categoria.py
│   └── exceptions.py            # DomainError e subclasses (ver hierarquia-excecoes.md)
│
├── use_cases/                  # Casos de uso da aplicação
│   ├── interfaces.py           # Protocols (UsuarioRepository, PasswordHasher)
│   ├── cadastrar_usuario.py    # implementado
│   ├── criar_anuncio.py        # previsto
│   ├── iniciar_leilao.py       # previsto
│   ├── dar_lance.py            # previsto
│   └── encerrar_leilao.py      # previsto
│
├── adapters/
│   ├── repositories/           # Interfaces + implementações concretas
│   │   ├── leilao_repository.py
│   │   ├── anuncio_repository.py
│   │   └── usuario_repository.py
│   └── events/                 # Publisher/Subscriber de eventos
│       ├── publisher.py
│       └── handlers/
│
├── infra/
│   ├── api/                    # FastAPI: rotas, schemas, JWT, OpenAPI
│   │   ├── app.py
│   │   ├── routers/
│   │   └── schemas/
│   ├── db/                     # Models SQLAlchemy e migrations Alembic
│   │   ├── models/
│   │   └── migrations/
│   └── jobs/                   # Encerramento automático de leilões
│       └── encerrar_leiloes.py
│
├── tests/
│   ├── unit/                   # Testes de domínio (sem banco, sem framework web)
│   └── integration/            # Testes de API e persistência
│
├── docs/
│   ├── arquitetura.md
│   ├── estrutura-e-stack.md
│   └── hierarquia-excecoes.md  # DomainError unificado; códigos HTTP pendentes
│
├── Dockerfile                  # Imagem de build/teste (Poetry + pytest)
├── Jenkinsfile                 # Pipeline de CI/CD
├── pyproject.toml              # Dependências (Poetry)
├── docker-compose.yml          # PostgreSQL (+ Redis, se Celery)
└── README.md
```

### Responsabilidade por pasta

| Pasta | O que contém | Depende de |
|---|---|---|
| `domain/` | Entidades, validações, máquina de estados | Nada externo |
| `use_cases/` | Orquestração de regras de negócio | `domain/`, interfaces de `adapters/` |
| `adapters/repositories/` | Contratos e implementações de persistência | `domain/` |
| `adapters/events/` | Publicação e consumo de eventos | `domain/` |
| `infra/api/` | HTTP, autenticação, serialização | `use_cases/`, `adapters/` |
| `infra/db/` | Models ORM, migrations | `domain/` (mapeamento) |
| `infra/jobs/` | Tarefas agendadas | `use_cases/` |

---

## Stack tecnológica

| Camada / Finalidade | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ |
| Framework web | FastAPI + Uvicorn (ASGI) |
| ORM e migrations | SQLAlchemy 2.0 + Alembic |
| Autenticação | PyJWT + `OAuth2PasswordBearer` / `Depends` |
| Banco de dados | PostgreSQL (via Docker) |
| Gerenciador de dependências | Poetry |
| Testes automatizados | pytest + httpx (`TestClient`) + pytest-cov |
| Documentação da API | OpenAPI nativo do FastAPI (`/docs`, `/redoc`) |
| CI/CD | Jenkins (Jenkinsfile) |
| Jobs assíncronos (MVP) | APScheduler (lifespan do FastAPI) |
| Jobs assíncronos (evolução) | Celery + Redis |

---

## Infraestrutura local

O `docker-compose.yml` sobe os serviços de apoio:

```text
docker-compose up
     │
     ├── PostgreSQL    → persistência principal
     └── Redis         → opcional; necessário apenas se adotar Celery
```

A aplicação FastAPI roda fora do compose (ou em serviço adicional, conforme evolução do projeto):

```text
uvicorn infra.api.app:create_app --factory --reload
```

Migrations: `alembic revision --autogenerate -m "..."` e `alembic upgrade head`.

---

## Fluxo de uma requisição (exemplo: dar lance)

```text
POST /leiloes/{id}/lances
        │
        ▼
infra/api/                valida JWT, desserializa payload (Pydantic)
        │
        ▼
use_cases/dar_lance.py    orquestra a operação
        │
        ├── domain/leilao.py       valida estado, incremento, janela
        ├── adapters/repositories/ persiste com lock transacional
        └── adapters/events/       publica LanceRealizado
        │
        ▼
Resposta HTTP 201 + lance criado
```

---

## Próximos passos de implementação

1. **`domain/`** — entidades e regras de lance — **feito**
2. **`infra/db/`** — models SQLAlchemy e migrations Alembic — **próximo**
3. **`adapters/repositories/`** — interfaces e implementações SQLAlchemy
4. **`use_cases/`** — casos de uso restantes (`CriarAnuncio`, `DarLance`, `EncerrarLeilao`, …)
5. **`infra/api/`** — routers e autenticação JWT
6. **`infra/jobs/`** — encerramento automático (lifespan)
7. **`tests/integration/`** — persistência e API, depois dos repositories

Roteiro completo em [`proximos-passos.md`](proximos-passos.md). Hierarquia de exceções em [`hierarquia-excecoes.md`](hierarquia-excecoes.md). Detalhes arquiteturais em [`arquitetura.md`](arquitetura.md).
