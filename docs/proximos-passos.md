# Próximos Passos

Roteiro de implementação do **sistema-leilao** após o scaffolding inicial (diretórios, Poetry, `docker-compose`, `.gitignore`). O código de negócio ainda não existe — este documento traz **sugestões** de ordem de trabalho, convenções e prioridades para o MVP. A sequência abaixo é recomendada, não obrigatória.

Distribuição detalhada de responsabilidades por integrante em [`responsabilidades-equipe.md`](responsabilidades-equipe.md).

Contexto arquitetural em [`arquitetura.md`](arquitetura.md). Árvore de diretórios e stack em [`estrutura-e-stack.md`](estrutura-e-stack.md).

---

## Imediato (antes de codar)

Itens de preparação que evitam retrabalho nas primeiras branches de código.

### Configuração do ambiente (`.env`)

1. Copiar o template: `cp .env.example .env`
2. Ajustar variáveis conforme o ambiente local:

| Variável | Finalidade |
|---|---|
| `FLASK_APP` | Ponto de entrada (`infra.flask_app.app`) |
| `FLASK_ENV` | `development` em ambiente local |
| `SECRET_KEY` | Chave da aplicação Flask |
| `DATABASE_URL` | Conexão PostgreSQL (padrão: `postgresql://leilao:leilao@localhost:5432/leilao`) |
| `JWT_SECRET_KEY` | Assinatura dos tokens JWT |
| `REDIS_URL` | Opcional no MVP; necessário apenas se adotar Celery |

O arquivo `.env` **não** deve ser versionado — já está no `.gitignore`.

### Convenções de branch

| Branch | Propósito |
|---|---|
| `main` | Documentação estável e referência do projeto |
| `dev` | Integração do código em desenvolvimento |
| `feature/*` | Funcionalidade nova (domínio, API, jobs, etc.) |
| `chore/*` | Infraestrutura, CI, refatorações sem mudança de comportamento |

**Fluxo:** criar branch a partir de `dev` → implementar → abrir PR para `dev` → após estabilizar o MVP, promover `dev` → `main`.

**Nomenclatura sugerida para branches:**

```text
feature/domain-entidades
feature/adapters-repositories
feature/use-case-dar-lance
feature/flask-auth-jwt
chore/ci-jenkinsfile
```

---

## Sugestão: Domínio (`domain/`)

Base de tudo: entidades e regras puras, sem Flask ou SQLAlchemy. Detalhes do modelo em [`arquitetura.md`](arquitetura.md#modelo-de-domínio).

### Entidades a implementar

| Arquivo | Entidade | Responsabilidade |
|---|---|---|
| `domain/usuario.py` | **Usuario** | Conta, credenciais, papéis (comprador/vendedor) |
| `domain/categoria.py` | **Categoria** | Classificação de anúncios |
| `domain/anuncio.py` | **Anuncio** | Produto, categoria, tipo (venda direta ou leilão), status |
| `domain/leilao.py` | **Leilao** | Preço inicial, incremento mínimo, janela temporal, máquina de estados |
| `domain/lance.py` | **Lance** | Valor, usuário, timestamp; associado a um leilão |

### Regras críticas (implementar no domínio)

| Regra | Onde validar |
|---|---|
| Máquina de estados do leilão (`agendado` → `aberto` → `encerrado` → `pago` / `cancelado`) | `domain/leilao.py` |
| Lance só aceito com status `aberto` e dentro da janela temporal | `domain/leilao.py` |
| Incremento mínimo: `valor >= lance_atual + incremento_minimo` | `domain/leilao.py` |
| Encerrado sem lances → `cancelado` | `domain/leilao.py` |
| Encerrado com lances → vencedor = maior lance válido | `domain/leilao.py` |

### Testes unitários

Criar em `tests/unit/` — sem banco, sem Flask:

- Transições válidas e inválidas de estado do leilão
- Rejeição de lance abaixo do incremento mínimo
- Rejeição de lance fora da janela temporal
- Apuração de vencedor e cancelamento sem lances

Meta: cobertura alta em `domain/` antes de avançar para adaptadores.

---

## Sugestão: Adaptadores (`adapters/`)

Contratos de persistência e eventos. A infraestrutura conhece o domínio; o domínio não conhece a infraestrutura.

### Repositories (`adapters/repositories/`)

| Arquivo | Interface + implementação |
|---|---|
| `usuario_repository.py` | CRUD de usuários, busca por e-mail |
| `anuncio_repository.py` | CRUD de anúncios, filtros por categoria/tipo |
| `leilao_repository.py` | CRUD de leilões, busca por status e janela temporal |

**Pontos de atenção:**

- Definir **interfaces** (protocolos ou classes abstratas) consumidas pelos casos de uso
- Implementação concreta com SQLAlchemy em `infra/db/`
- Lock pessimista (`SELECT ... FOR UPDATE`) no repositório de leilão para lances concorrentes — ver [`arquitetura.md`](arquitetura.md#concorrência-em-lances)

### Eventos (`adapters/events/`)

| Componente | Responsabilidade |
|---|---|
| `publisher.py` | Publicação de eventos de domínio |
| `handlers/` | Consumidores independentes (histórico, auditoria, notificações futuras) |

Eventos previstos:

| Evento | Quando |
|---|---|
| `LanceRealizado` | Lance aceito e persistido |
| `LeilaoEncerrado` | Leilão encerrado (manual ou job) |

### Models e migrations (`infra/db/`)

| Pasta | Conteúdo |
|---|---|
| `infra/db/models/` | Models SQLAlchemy mapeando entidades de domínio |
| `infra/db/migrations/` | Migrations via Flask-Migrate (`flask db init`, `migrate`, `upgrade`) |

Ordem sugerida: models → migration inicial → implementações concretas dos repositories.

---

## Sugestão: Casos de uso (`use_cases/`)

Orquestração de regras de negócio. Cada caso de uso recebe repositories e publisher por injeção de dependência.

| Arquivo | Caso de uso | Responsabilidade |
|---|---|---|
| `criar_anuncio.py` | **CriarAnuncio** | Vendedor cadastra produto (venda direta ou leilão) |
| `iniciar_leilao.py` | **IniciarLeilao** | Transição `agendado` → `aberto` no horário de início |
| `dar_lance.py` | **DarLance** | Valida regras de domínio, persiste com lock, publica `LanceRealizado` |
| `encerrar_leilao.py` | **EncerrarLeilao** | Encerra leilão, define vencedor ou cancela, publica `LeilaoEncerrado` |

**Regra:** casos de uso **não** importam Flask nem SQLAlchemy diretamente — apenas interfaces de `adapters/`.

Testes de integração em `tests/integration/` podem cobrir cada caso de uso com banco real (PostgreSQL de teste).

---

## Sugestão: API Flask (`infra/flask_app/`)

Camada HTTP: autenticação, rotas, serialização e documentação Swagger.

### App factory (`app.py`)

- Factory pattern (`create_app`) com configuração via variáveis de ambiente
- Registro de extensões: SQLAlchemy, Flask-Migrate, Flask-JWT-Extended, Flasgger
- Inicialização do scheduler (`infra/jobs/`) no contexto da aplicação

### Autenticação (JWT)

- Registro e login de usuário (endpoints públicos)
- Proteção de rotas com `@jwt_required()`
- Claims com identificação do usuário e papel (comprador/vendedor)

### Rotas previstas (MVP)

| Método | Rota | Caso de uso |
|---|---|---|
| `POST` | `/auth/register` | Cadastro de usuário |
| `POST` | `/auth/login` | Login → token JWT |
| `POST` | `/anuncios` | CriarAnuncio |
| `GET` | `/anuncios` | Listagem com filtros |
| `POST` | `/leiloes/{id}/lances` | DarLance |
| `GET` | `/leiloes/{id}/lances` | Histórico de lances |
| `GET` | `/leiloes/{id}` | Detalhe do leilão (status, lance atual) |

Controllers em `infra/flask_app/controllers/`; rotas em `infra/flask_app/routes/`.

### Flasgger (Swagger)

- Documentação OpenAPI em `/apidocs`
- Anotar endpoints com schemas de request/response
- Incluir exemplos de payloads e códigos de erro (400, 401, 404, 409)

---

## Sugestão: Jobs (`infra/jobs/`)

Encerramento (e abertura) automática de leilões sem depender de requisição HTTP. Detalhes em [`arquitetura.md`](arquitetura.md#jobs-e-automação).

| Job | Periodicidade | Ação |
|---|---|---|
| Abrir leilões agendados | A cada 1 min (ajustável) | Busca `agendado` com `data_hora_inicio <= agora` → `IniciarLeilao` |
| Encerrar leilões expirados | A cada 1 min (ajustável) | Busca `aberto` com `data_hora_fim <= agora` → `EncerrarLeilao` |

**Tecnologia MVP:** APScheduler embutido no processo Flask (já listado no `pyproject.toml`).

**Regra:** o job **não contém regra de negócio** — apenas dispara casos de uso já definidos.

Arquivo previsto: `infra/jobs/encerrar_leiloes.py` (pode incluir também a lógica de abertura ou separar em módulo dedicado).

---

## Sugestão: CI/CD e qualidade

Automação de build, testes e cobertura antes de merge em `dev`.

### Jenkinsfile

Pipeline mínimo sugerido:

```text
checkout → poetry install → docker compose up (postgres) → pytest --cov → relatório
```

Etapas opcionais: lint (`ruff` ou `flake8`), type check (`mypy`).

### Cobertura de testes

- `pytest-cov` já configurado no `pyproject.toml`
- Meta inicial: **≥ 80%** em `domain/` e `use_cases/`
- Relatório HTML ou XML para o Jenkins

### Pre-commit (opcional)

Hooks sugeridos para `chore/pre-commit`:

- Formatação (`black` ou `ruff format`)
- Lint (`ruff check`)
- Verificação de arquivos grandes e trailing whitespace

Não é bloqueante para o MVP, mas reduz ruído em PRs.

---

## Distribuição de Responsabilidades

Cada integrante atua como **Desenvolvedor Full Stack** em seu domínio e acumula um papel de **Guardião** transversal. Detalhes completos em [`responsabilidades-equipe.md`](responsabilidades-equipe.md).

| Integrante | Domínio | Guardião |
|------------|---------|----------|
| **Téo** ([@TSM-05](https://github.com/TSM-05)) | Identidade e Usuários | UI/UX (padronização visual) |
| **Caio** ([@caiosemblano](https://github.com/caiosemblano)) | Catálogo e Gestão de Leilões | Repositório (branches e revisão de PRs) |
| **Pedro Vitor** ([@PedroVGSC](https://github.com/PedroVGSC)) | Motor de Lances e Tempo Real | Arquitetura e Integração (contratos de API) |
| **Pedro** ([@phpaiva05](https://github.com/phpaiva05)) | Pós-Leilão, Histórico e Auditoria | Banco e Qualidade (modelagem e testes) |

### PRs por integrante

**Téo — Identidade e Usuários:**
1. `feature/domain-usuario` — entidade `Usuario` e testes unitários
2. `feature/infra-db-model-usuario` — model SQLAlchemy e migration
3. `feature/flask-auth-jwt` — registro, login, JWT e proteção de rotas

**Caio — Catálogo e Gestão de Leilões:**
1. `feature/domain-entidades-catalogo` — entidades `Categoria`, `Anuncio`, `Leilao` e testes
2. `feature/infra-db-models-catalogo` — models e migrations de catálogo
3. `feature/adapters-repositories-catalogo` — repositories de anúncios e leilões
4. `feature/use-case-criar-anuncio` — caso de uso de criação de anúncio
5. `feature/flask-routes-catalogo` — endpoints REST de catálogo

**Pedro Vitor — Motor de Lances e Tempo Real:**
1. `feature/domain-lance` — entidade `Lance` e regras de lance em `Leilao`
2. `feature/use-case-dar-lance` — lance com lock transacional e evento `LanceRealizado`
3. `feature/use-case-encerrar-leilao` — encerramento, apuração e evento `LeilaoEncerrado`
4. `feature/adapters-events` — publisher e eventos de domínio
5. `feature/jobs-leilao` — APScheduler para abrir/encerrar leilões
6. `feature/flask-routes-lances` — endpoints REST de lances

**Pedro — Pós-Leilão, Histórico e Auditoria:**
1. `feature/adapters-events-handlers` — handlers de `LeilaoEncerrado` e `LanceRealizado`
2. `feature/infra-db-historico-auditoria` — models e migrations de histórico/auditoria
3. `feature/flask-routes-historico` — endpoints de histórico e relatórios
4. `chore/ci-jenkinsfile` — pipeline de CI com testes e cobertura

---

## Ordem sugerida de PRs

Branches `feature/*` e `chore/*` em sequência lógica — cada PR deve ser revisável e mergeável de forma independente:

1. `feature/domain-usuario` — **(Téo)** entidade `Usuario` e testes unitários
2. `feature/domain-entidades-catalogo` — **(Caio)** entidades de catálogo e testes
3. `feature/domain-lance` — **(Pedro Vitor)** entidade `Lance` e regras de lance
4. `feature/infra-db-model-usuario` — **(Téo)** model SQLAlchemy e migration de usuário
5. `feature/infra-db-models-catalogo` — **(Caio)** models e migrations de catálogo
6. `feature/adapters-repositories-catalogo` — **(Caio)** repositories de anúncios e leilões
7. `feature/flask-auth-jwt` — **(Téo)** registro, login e proteção de rotas JWT
8. `feature/use-case-criar-anuncio` — **(Caio)** primeiro caso de uso ponta a ponta
9. `feature/use-case-dar-lance` — **(Pedro Vitor)** lance com lock transacional e evento
10. `feature/use-case-encerrar-leilao` — **(Pedro Vitor)** encerramento e apuração
11. `feature/adapters-events` — **(Pedro Vitor)** publisher e eventos de domínio
12. `feature/adapters-events-handlers` — **(Pedro)** handlers para histórico e auditoria
13. `feature/infra-db-historico-auditoria` — **(Pedro)** models de histórico
14. `feature/flask-routes-catalogo` — **(Caio)** endpoints REST de catálogo + Flasgger
15. `feature/flask-routes-lances` — **(Pedro Vitor)** endpoints REST de lances
16. `feature/flask-routes-historico` — **(Pedro)** endpoints de histórico
17. `feature/jobs-leilao` — **(Pedro Vitor)** APScheduler para abrir/encerrar leilões
18. `chore/ci-jenkinsfile` — **(Pedro)** pipeline de CI com testes e cobertura

PRs menores (ex.: separar auth de rotas) são bem-vindos se facilitarem a revisão.

---

## Prioridade MVP enxuto

Caminho mínimo para demonstrar o fluxo completo **criar leilão → dar lance → encerrar automaticamente**:

```text
1. domain/leilao.py + domain/lance.py + testes unitários
2. infra/db/models + migration
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

Com esse recorte, é possível validar as regras críticas de lance, concorrência e encerramento automático antes de expandir o marketplace.

---

## Referências

- [Responsabilidades da equipe](responsabilidades-equipe.md) — domínios, guardiões e tarefas por integrante
- [Arquitetura](arquitetura.md) — camadas, domínio, eventos, concorrência
- [Estrutura e stack](estrutura-e-stack.md) — árvore de diretórios, stack e fluxo de requisição
- [README](../README.md) — visão do produto, regras de leilão e atores
