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
│   ├── flask_app/              # Rotas, controllers, serialização, JWT
│   │   ├── app.py
│   │   ├── routes/
│   │   └── controllers/
│   ├── db/                     # Models SQLAlchemy e migrations
│   │   ├── models/
│   │   └── migrations/
│   └── jobs/                   # Encerramento automático de leilões
│       └── encerrar_leiloes.py
│
├── tests/
│   ├── unit/                   # Testes de domínio (sem banco, sem Flask)
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
| `infra/flask_app/` | HTTP, autenticação, serialização | `use_cases/`, `adapters/` |
| `infra/db/` | Models ORM, migrations | `domain/` (mapeamento) |
| `infra/jobs/` | Tarefas agendadas | `use_cases/` |

---

## Stack tecnológica

| Camada / Finalidade | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ |
| Framework web | Flask + Flask-RESTful |
| ORM e migrations | SQLAlchemy + Flask-Migrate |
| Autenticação | Flask-JWT-Extended |
| Banco de dados | PostgreSQL (via Docker) |
| Gerenciador de dependências | Poetry |
| Testes automatizados | pytest + pytest-flask + pytest-cov |
| Documentação da API | Swagger / OpenAPI (Flasgger) |
| CI/CD | Jenkins (Jenkinsfile) |
| Jobs assíncronos (MVP) | APScheduler |
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

A aplicação Flask roda fora do compose (ou em serviço adicional, conforme evolução do projeto).

---

## Fluxo de uma requisição (exemplo: dar lance)

```text
POST /leiloes/{id}/lances
        │
        ▼
infra/flask_app/          valida JWT, desserializa payload
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
2. **`infra/db/`** — models SQLAlchemy e migrations — **próximo**
3. **`adapters/repositories/`** — interfaces e implementações SQLAlchemy
4. **`use_cases/`** — casos de uso restantes (`CriarAnuncio`, `DarLance`, `EncerrarLeilao`, …)
5. **`infra/flask_app/`** — rotas e autenticação
6. **`infra/jobs/`** — encerramento automático
7. **`tests/integration/`** — persistência e API, depois dos repositories

Roteiro completo em [`proximos-passos.md`](proximos-passos.md). Hierarquia de exceções em [`hierarquia-excecoes.md`](hierarquia-excecoes.md). Detalhes arquiteturais em [`arquitetura.md`](arquitetura.md).
