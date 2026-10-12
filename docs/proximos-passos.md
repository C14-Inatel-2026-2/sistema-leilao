# Próximos Passos

Roteiro de implementação do **sistema-leilao**. A sequência é recomendada, não obrigatória.

**Snapshot (out/2026, branch `dev`):** a fase de domínio e testes unitários está concluída. O gargalo agora é **persistência** (models SQLAlchemy, migrations e repositories). Sem isso, os casos de uso restantes, a API Flask e os jobs não avançam.

Distribuição detalhada de responsabilidades por integrante em [`responsabilidades-equipe.md`](responsabilidades-equipe.md).

Contexto arquitetural em [`arquitetura.md`](arquitetura.md). Árvore de diretórios e stack em [`estrutura-e-stack.md`](estrutura-e-stack.md).

---

## Estado atual

| Camada | Situação |
|---|---|
| `domain/` | **Feito.** Entidades `Usuario`, `Categoria`, `Anuncio`, `Leilao`, `Lance` e hierarquia `DomainError` |
| `tests/unit/` | **Feito.** Testes das entidades e de `CadastrarUsuario` |
| `use_cases/` | **Parcial.** Só `CadastrarUsuario` (+ `interfaces.py` com `UsuarioRepository` e `PasswordHasher`) |
| `adapters/` | **Vazio.** Pastas com `.gitkeep` |
| `infra/db/`, `infra/flask_app/`, `infra/jobs/` | **Vazio.** Pastas com `.gitkeep` |
| CI | **Feito.** `Dockerfile` + `Jenkinsfile` (build da imagem e `pytest` com relatórios) |
| `docker-compose.yml` | **Feito.** PostgreSQL 16 + Redis (Redis só se Celery) |

### PRs / branches já integrados em `dev`

- `feature/domain-usuario` — entidade `Usuario` e testes
- `feature/domain-entidades-catalogo` — `Categoria`, `Anuncio`, `Leilao`
- Extração de `Lance` e regras de lance em `Leilao`
- Unificação das exceções em `DomainError` (PRs #10–#12) — ver [`hierarquia-excecoes.md`](hierarquia-excecoes.md)
- `feature/use-case-cadastrar-usuario` — primeiro caso de uso, com testes mockados
- Testes unitários de catálogo e leilão
- `Dockerfile` / `Jenkinsfile` para build e testes

A branch remota `origin/feature/use-case-dar-lance` está **desatualizada** (sem commits à frente de `dev`). Abrir uma branch nova a partir de `dev`.

---

## O que vem agora

Ordem para desbloquear o MVP. Téo e Caio podem fazer os models em paralelo.

### 1. Models e migrations (`infra/db/`) — gargalo

Sem schema, não há persistência nem testes de integração.

| Quem | Branch | Conteúdo |
|---|---|---|
| **Téo** | `feature/infra-db-model-usuario` | Model SQLAlchemy e migration de `Usuario` |
| **Caio** | `feature/infra-db-models-catalogo` | Models e migrations de `Categoria`, `Anuncio`, `Leilao` |

Pedro ([@phpaiva05](https://github.com/phpaiva05)) revisa todas as migrations (guardião de banco).

Ordem dentro de cada PR: models → `flask db init` / `migrate` / `upgrade`.

Ao começar esta fase, copiar o ambiente local: `cp .env.example .env` e `docker compose up` (PostgreSQL).

### 2. Repositories (`adapters/repositories/`)

Interfaces (Protocols, no mesmo padrão de `use_cases/interfaces.py`) e implementações SQLAlchemy.

| Quem | Arquivo | Papel |
|---|---|---|
| **Téo** | `usuario_repository.py` | CRUD, busca por e-mail |
| **Caio** | `feature/adapters-repositories-catalogo` — `anuncio_repository.py`, `leilao_repository.py` | CRUD, filtros; **lock pessimista** (`SELECT ... FOR UPDATE`) no leilão |

O domínio não conhece a infraestrutura; os casos de uso dependem só dos contratos.

### 3. Casos de uso restantes (`use_cases/`)

Cada caso de uso recebe repositories (e publisher, quando houver eventos) por injeção. **Não** importar Flask nem SQLAlchemy.

| Quem | Arquivo | Responsabilidade |
|---|---|---|
| *(feito)* | `cadastrar_usuario.py` | Cadastro com hash e unicidade de e-mail |
| **Caio** | `criar_anuncio.py` | Vendedor cadastra produto (venda direta ou leilão) |
| **Caio** | `iniciar_leilao.py` | Transição `agendado` → `aberto` |
| **Pedro Vitor** | `dar_lance.py` | Valida domínio, persiste com lock, publica `LanceRealizado` |
| **Pedro Vitor** | `encerrar_leilao.py` | Encerra, apura vencedor ou cancela, publica `LeilaoEncerrado` |

Testes de integração em `tests/integration/` com PostgreSQL de teste, quando os repositories existirem.

### 4. API Flask (`infra/flask_app/`)

Factory `create_app`, JWT, Flasgger em `/apidocs`.

| Quem | Método | Rota | Caso de uso |
|---|---|---|---|
| **Téo** | `POST` | `/auth/register` | Cadastro |
| **Téo** | `POST` | `/auth/login` | Login → JWT |
| **Caio** | `POST` | `/anuncios` | CriarAnuncio |
| **Caio** | `GET` | `/anuncios` | Listagem com filtros |
| **Pedro Vitor** | `POST` | `/leiloes/{id}/lances` | DarLance |
| **Pedro Vitor** | `GET` | `/leiloes/{id}/lances` | Histórico de lances |
| **Pedro Vitor** / **Pedro** | `GET` | `/leiloes/{id}` | Detalhe (status, lance atual, vencedor) |

Controllers em `infra/flask_app/controllers/`; rotas em `infra/flask_app/routes/`.

A factory registra SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Flasgger e o scheduler.

### 5. Jobs (`infra/jobs/`) — **Pedro Vitor**

O job **não contém regra de negócio** — só dispara casos de uso. Detalhes em [`arquitetura.md`](arquitetura.md#jobs-e-automação).

| Job | Periodicidade | Ação |
|---|---|---|
| Abrir leilões agendados | A cada 1 min (ajustável) | `agendado` com início ≤ agora → `IniciarLeilao` |
| Encerrar leilões expirados | A cada 1 min (ajustável) | `aberto` com fim ≤ agora → `EncerrarLeilao` |

Tecnologia MVP: APScheduler no processo Flask (`pyproject.toml`). Arquivo previsto: `infra/jobs/encerrar_leiloes.py`.

### 6. Pós-leilão — **Pedro**

CI (`chore/ci-jenkinsfile`) **já está em `dev`**. Foco restante:

1. `feature/adapters-events-handlers` — handlers de `LeilaoEncerrado` e `LanceRealizado`
2. `feature/infra-db-historico-auditoria` — models e migrations de histórico
3. `feature/flask-routes-historico` — endpoints de histórico e relatórios

---

## Convenções de trabalho

| Branch | Propósito |
|---|---|
| `main` | Documentação estável e referência do projeto |
| `dev` | Integração do código em desenvolvimento |
| `feature/*` | Funcionalidade nova (domínio, API, jobs, etc.) |
| `chore/*` | Infraestrutura, CI, refatorações sem mudança de comportamento |

**Fluxo:** criar branch a partir de `dev` → implementar → abrir PR para `dev` → após estabilizar o MVP, promover `dev` → `main`.

```text
feature/infra-db-model-usuario
feature/infra-db-models-catalogo
feature/adapters-repositories-catalogo
feature/use-case-dar-lance
feature/flask-auth-jwt
```

### Ambiente (`.env`)

Necessário a partir dos models / da API. O arquivo **não** é versionado.

| Variável | Finalidade |
|---|---|
| `FLASK_APP` | Ponto de entrada (`infra.flask_app.app`) |
| `FLASK_ENV` | `development` em ambiente local |
| `SECRET_KEY` | Chave da aplicação Flask |
| `DATABASE_URL` | PostgreSQL (`postgresql://leilao:leilao@localhost:5432/leilao`) |
| `JWT_SECRET_KEY` | Assinatura dos tokens JWT |
| `REDIS_URL` | Só se adotar Celery |

---

## Domínio (concluído)

Entidades e regras puras, sem Flask ou SQLAlchemy. Detalhes em [`arquitetura.md`](arquitetura.md#modelo-de-domínio).

| Arquivo | Entidade | Responsabilidade |
|---|---|---|
| `domain/usuario.py` | **Usuario** | Conta, credenciais, papéis (comprador/vendedor) |
| `domain/categoria.py` | **Categoria** | Classificação de anúncios |
| `domain/anuncio.py` | **Anuncio** | Produto, categoria, tipo (venda direta ou leilão), status |
| `domain/leilao.py` | **Leilao** | Preço inicial, incremento mínimo, janela temporal, máquina de estados |
| `domain/lance.py` | **Lance** | Valor, usuário, timestamp; associado a um leilão |

| Regra | Onde |
|---|---|
| Máquina de estados (`agendado` → `aberto` → `encerrado` → `pago` / `cancelado`) | `domain/leilao.py` |
| Lance só com status `aberto` e dentro da janela | `domain/leilao.py` |
| Incremento mínimo: `valor >= lance_atual + incremento_minimo` | `domain/leilao.py` |
| Encerrado sem lances → `cancelado` | `domain/leilao.py` |
| Encerrado com lances → vencedor = maior lance válido | `domain/leilao.py` |

---

## Eventos de domínio (ainda não implementados)

| Evento | Quando |
|---|---|
| `LanceRealizado` | Lance aceito e persistido |
| `LeilaoEncerrado` | Leilão encerrado (manual ou job) |

`adapters/events/publisher.py` publica; `adapters/events/handlers/` consome (histórico, auditoria).

---

## CI e qualidade

O pipeline atual constrói a imagem Docker e roda `pytest` (JUnit + cobertura XML). Os testes de hoje são unitários, sem Flask nem PostgreSQL.

Quando existirem testes de integração, o stage de Test deve subir o Postgres (`docker compose`).

- Meta: **≥ 80%** em `domain/` e `use_cases/` (`pytest-cov` já está no `pyproject.toml`)
- Opcional, não bloqueante: lint (`ruff`), type check (`mypy`), `chore/pre-commit`

---

## PRs restantes por integrante

Detalhes em [`responsabilidades-equipe.md`](responsabilidades-equipe.md).

| Integrante | Domínio | Guardião |
|------------|---------|----------|
| **Téo** ([@TSM-05](https://github.com/TSM-05)) | Identidade e Usuários | UI/UX |
| **Caio** ([@caiosemblano](https://github.com/caiosemblano)) | Catálogo e Gestão de Leilões | Repositório |
| **Pedro Vitor** ([@PedroVGSC](https://github.com/PedroVGSC)) | Motor de Lances e Tempo Real | Arquitetura e Integração |
| **Pedro** ([@phpaiva05](https://github.com/phpaiva05)) | Pós-Leilão, Histórico e Auditoria | Banco e Qualidade |

**Téo** — próximo: `feature/infra-db-model-usuario`, depois `feature/flask-auth-jwt`.

**Caio** — próximo: `feature/infra-db-models-catalogo` → `feature/adapters-repositories-catalogo` → `feature/use-case-criar-anuncio` → `feature/flask-routes-catalogo`.

**Pedro Vitor** — próximo: `feature/use-case-dar-lance` (branch nova a partir de `dev`) → `feature/use-case-encerrar-leilao` → `feature/adapters-events` → `feature/jobs-leilao` → `feature/flask-routes-lances`.

**Pedro** — CI já feito; próximo: handlers, histórico/auditoria e rotas de histórico. Revisar migrations dos demais.

---

## Ordem sugerida de PRs (restantes)

Cada PR deve ser revisável e mergeável de forma independente:

1. `feature/infra-db-model-usuario` — **(Téo)** model e migration de usuário
2. `feature/infra-db-models-catalogo` — **(Caio)** models e migrations de catálogo
3. `feature/adapters-repositories-catalogo` — **(Caio)** repositories de anúncios e leilões (+ usuário, se Téo não tiver feito à parte)
4. `feature/flask-auth-jwt` — **(Téo)** registro, login e proteção de rotas
5. `feature/use-case-criar-anuncio` — **(Caio)** criação de anúncio ponta a ponta
6. `feature/use-case-dar-lance` — **(Pedro Vitor)** lance com lock e evento
7. `feature/use-case-encerrar-leilao` — **(Pedro Vitor)** encerramento e apuração
8. `feature/adapters-events` — **(Pedro Vitor)** publisher e eventos
9. `feature/adapters-events-handlers` — **(Pedro)** handlers de histórico e auditoria
10. `feature/infra-db-historico-auditoria` — **(Pedro)** models de histórico
11. `feature/flask-routes-catalogo` — **(Caio)** REST de catálogo + Flasgger
12. `feature/flask-routes-lances` — **(Pedro Vitor)** REST de lances
13. `feature/flask-routes-historico` — **(Pedro)** REST de histórico
14. `feature/jobs-leilao` — **(Pedro Vitor)** APScheduler

PRs menores (ex.: separar auth de rotas) são bem-vindos se facilitarem a revisão.

---

## Prioridade MVP enxuto

Caminho mínimo para **criar leilão → dar lance → encerrar automaticamente**:

```text
1. domain/leilao.py + domain/lance.py + testes unitários   ← feito
2. infra/db/models + migration                             ← próximo
3. adapters/repositories (leilao + usuario mínimo)
4. use_cases/dar_lance.py + use_cases/encerrar_leilao.py
5. infra/flask_app/ com POST /leiloes/{id}/lances
6. infra/jobs/ encerrando leilões expirados
```

**Pode ficar para depois do MVP:**

- Cadastro completo de anúncios com categorias e filtros
- Venda direta (sem leilão)
- Status `pago` e fluxo de pagamento
- Celery + Redis (substituir APScheduler)
- Notificações por e-mail
- Frontend
- Códigos estáveis de erro na API (`codigo` + `mensagem`) — a base `DomainError` já está unificada; ver [`hierarquia-excecoes.md`](hierarquia-excecoes.md)

Com esse recorte, valida-se lance, concorrência e encerramento automático antes de expandir o marketplace.

---

## Referências

- [Responsabilidades da equipe](responsabilidades-equipe.md) — domínios, guardiões e tarefas por integrante
- [Arquitetura](arquitetura.md) — camadas, domínio, eventos, concorrência
- [Hierarquia de exceções](hierarquia-excecoes.md) — `DomainError` unificado; códigos HTTP ainda pendentes
- [Estrutura e stack](estrutura-e-stack.md) — árvore de diretórios, stack e fluxo de requisição
- [README](../README.md) — visão do produto, regras de leilão e atores
