# Nota pessoal — roteiro geral após FastAPI

**Autor:** Caio ([@caiosemblano](https://github.com/caiosemblano))
**Quando:** out/2026, depois da migração Flask → FastAPI
**Escopo:** visão da minha sequência de entregas. Sem código.

Isto não substitui [`docs/proximos-passos.md`](../../proximos-passos.md) nem [`docs/responsabilidades-equipe.md`](../../responsabilidades-equipe.md). Detalhe do passo imediato em [`infra-db-models-catalogo.md`](infra-db-models-catalogo.md).

---

## Onde estamos

A stack HTTP já é FastAPI + Uvicorn. O domínio (`Usuario`, `Categoria`, `Anuncio`, `Leilao`, `Lance`) e os testes unitários estão feitos. O primeiro caso de uso (`CadastrarUsuario`) existe. CI (`Dockerfile` + `Jenkinsfile`) e `docker-compose` (PostgreSQL 16 + Redis) estão em `dev`.

Há um `create_app()` mínimo em `infra/api/app.py` (healthcheck `/` para o pipeline). Ainda **não** há persistência, repositories, rotas de catálogo nem JWT.

O gargalo do time é **schema + models SQLAlchemy + migrations Alembic**. Sem isso, casos de uso restantes, API e jobs não avançam.

O que mudou na minha frente com FastAPI:

- Sem Flask-SQLAlchemy, Flask-Migrate, Flasgger ou `flask db`.
- Models herdam de `DeclarativeBase` (SQLAlchemy 2.0).
- Migrations rodam com Alembic puro (`alembic revision` / `alembic upgrade`).
- Rotas futuras: `APIRouter` + schemas Pydantic + `Depends`; OpenAPI em `/docs`.
- Subir a API, quando existir: `uvicorn infra.api.app:create_app --factory --reload`.

---

## Minha sequência (Catálogo e Gestão de Leilões)

Ordem para desbloquear o MVP. Cada item é um PR separado, a partir de `dev`, merge em `dev`.

| # | Branch | O que entrega | O que não entra |
|---|---|---|---|
| 1 | `feature/infra-db-models-catalogo` | `Base` + models ORM + migration de `categorias`, `anuncios`, `leiloes`, `lances` | repositories, casos de uso, routers |
| 2 | `feature/adapters-repositories-catalogo` | `anuncio_repository.py`, `leilao_repository.py` (CRUD, filtros, `SELECT ... FOR UPDATE` no leilão) | HTTP, JWT |
| 3 | `feature/use-case-criar-anuncio` | `criar_anuncio.py`; depois `iniciar_leilao.py` (`AGENDADO` → `ABERTO`) | routers |
| 4 | `feature/api-routes-catalogo` | `POST /anuncios`, `GET /anuncios` + schemas Pydantic em `infra/api/` | jobs, JWT (Téo) |

Papel contínuo: **guardião do repositório** — revisar PRs antes do merge em `dev`.

O passo 1 está detalhado em [`infra-db-models-catalogo.md`](infra-db-models-catalogo.md).

---

## Dependências do time

| Quem | Próximo | Como me afeta |
|---|---|---|
| **Téo** | `feature/infra-db-model-usuario` → `feature/api-auth-jwt` | tabela `usuarios`; JWT nas rotas de anúncio |
| **Pedro Vitor** | `dar_lance` / `encerrar_leilao` / jobs / rotas de lance | consome `Leilao` + lock no repository |
| **Pedro** | handlers, histórico, revisão de migrations | revisa **todas** as migrations (guardião de banco) |

Alinhar com Pedro (e Téo) se `vendedor_id` / `comprador_id` entram como UUID sem FK agora, ou se esperamos a tabela `usuarios`. **Não** criar model de `Usuario` nas minhas PRs.

A branch remota `origin/feature/use-case-dar-lance` está desatualizada. Pedro Vitor deve abrir uma nova a partir de `dev`.

---

## Caminho mínimo do MVP (time)

```text
1. domain/ + testes unitários                         ← feito
2. infra/db/models + migration Alembic                ← agora (Téo usuário, eu catálogo)
3. adapters/repositories (leilão + usuário mínimo)
4. use_cases/dar_lance.py + encerrar_leilao.py
5. infra/api/ com POST /leiloes/{id}/lances
6. infra/jobs/ encerrando leilões expirados
```

Pode ficar depois do MVP: cadastro completo de anúncios com filtros, venda direta, status `pago`, Celery + Redis, e-mail, frontend.

---

## Convenções que não posso quebrar

- `domain/` não importa FastAPI nem SQLAlchemy.
- Casos de uso não importam FastAPI nem SQLAlchemy; recebem repositories por injeção.
- Models ORM só em `infra/db/models/`; sem métodos de negócio (`abrir`, `validar_lance`, `associar_leilao`).
- Fluxo git: branch a partir de `dev` → PR para `dev`. Eu reviso antes do merge.

Referências oficiais: [`proximos-passos.md`](../../proximos-passos.md) · [`responsabilidades-equipe.md`](../../responsabilidades-equipe.md) · [`arquitetura.md`](../../arquitetura.md) · [`estrutura-e-stack.md`](../../estrutura-e-stack.md).
