# Responsabilidades da Equipe

Distribuição de domínios, papéis e tarefas entre os integrantes do **sistema-leilao**. Cada membro atua como **Desenvolvedor Full Stack** (back-end, front-end e banco) em seu domínio principal e acumula um papel de **Guardião** transversal ao projeto.

Referências: [`proximos-passos.md`](proximos-passos.md) · [`arquitetura.md`](arquitetura.md) · [`estrutura-e-stack.md`](estrutura-e-stack.md)

---

## Visão Geral

| # | Integrante | GitHub | Domínio Principal | Papel de Guardião |
|---|------------|--------|--------------------|--------------------|
| 1 | Téo | [@TSM-05](https://github.com/TSM-05) | Identidade e Usuários | UI/UX (padronização visual) |
| 2 | Caio | [@caiosemblano](https://github.com/caiosemblano) | Catálogo e Gestão de Leilões | Repositório (branches e revisão de PRs) |
| 3 | Pedro Vitor | [@PedroVGSC](https://github.com/PedroVGSC) | Motor de Lances e Tempo Real | Arquitetura e Integração (estrutura do projeto e contratos de API) |
| 4 | Pedro | [@phpaiva05](https://github.com/phpaiva05) | Pós-Leilão, Histórico e Auditoria | Banco e Qualidade (modelagem geral e testes integrados) |

---

## 1. Téo — Identidade e Usuários

**GitHub:** [@TSM-05](https://github.com/TSM-05)

### Domínio

Responsável por todo o ciclo de vida do usuário: cadastro, autenticação, autorização e gestão de perfis (comprador/vendedor).

### Tarefas principais

| Área | Tarefa | Artefatos |
|------|--------|-----------|
| Domínio | Entidade `Usuario` (conta, credenciais, papéis) | `domain/usuario.py` |
| Adaptadores | Repository de usuários (CRUD, busca por e-mail) | `adapters/repositories/usuario_repository.py` |
| Infra / DB | Model SQLAlchemy e migration de usuários | `infra/db/models/usuario.py`, `infra/db/migrations/` |
| API | Endpoints de autenticação JWT (registro e login) | `infra/flask_app/controllers/auth_controller.py`, `infra/flask_app/routes/auth.py` |
| API | Proteção de rotas com `@jwt_required()` e claims de papel | `infra/flask_app/` |
| Testes | Testes unitários de `Usuario` e testes de integração de auth | `tests/unit/`, `tests/integration/` |

### Branches sugeridas

```text
feature/domain-usuario
feature/infra-db-model-usuario
feature/flask-auth-jwt
```

### Papel de Guardião — UI/UX

- Define e mantém o padrão visual do projeto (componentes, cores, tipografia)
- Revisa PRs que tocam em camadas de apresentação para garantir consistência
- Documenta guidelines de UI quando o front-end for implementado

---

## 2. Caio — Catálogo e Gestão de Leilões

**GitHub:** [@caiosemblano](https://github.com/caiosemblano)

### Domínio

Responsável pela criação e gestão de anúncios, categorias e pela configuração dos leilões (preço inicial, incremento mínimo, janela temporal).

### Tarefas principais

| Área | Tarefa | Artefatos |
|------|--------|-----------|
| Domínio | Entidades `Categoria`, `Anuncio` e `Leilao` (máquina de estados, regras de criação) | `domain/categoria.py`, `domain/anuncio.py`, `domain/leilao.py` |
| Adaptadores | Repositories de anúncios e leilões (CRUD, filtros por categoria/tipo/status) | `adapters/repositories/anuncio_repository.py`, `adapters/repositories/leilao_repository.py` |
| Infra / DB | Models SQLAlchemy e migrations de categorias, anúncios e leilões | `infra/db/models/` |
| Casos de uso | `CriarAnuncio` — vendedor cadastra produto (venda direta ou leilão) | `use_cases/criar_anuncio.py` |
| Casos de uso | `IniciarLeilao` — transição `agendado` → `aberto` | `use_cases/iniciar_leilao.py` |
| API | Endpoints de CRUD de anúncios e listagem com filtros | `infra/flask_app/controllers/`, `infra/flask_app/routes/` |
| Testes | Testes unitários das entidades e de integração dos casos de uso de catálogo | `tests/unit/`, `tests/integration/` |

### Branches sugeridas

```text
feature/domain-entidades-catalogo
feature/infra-db-models-catalogo
feature/adapters-repositories-catalogo
feature/use-case-criar-anuncio
feature/flask-routes-catalogo
```

### Papel de Guardião — Repositório

- Gerencia a estratégia de branches (`dev`, `feature/*`, `chore/*`, `main`)
- Revisa PRs de todos os integrantes antes do merge em `dev`
- Garante que as convenções de branch e commit são seguidas
- Resolve conflitos de merge e mantém `dev` estável

---

## 3. Pedro Vitor — Motor de Lances e Tempo Real

**GitHub:** [@PedroVGSC](https://github.com/PedroVGSC)

### Domínio

Responsável pela lógica de lances (validação, concorrência, lock transacional) e pela automação de transições temporais dos leilões (abertura e encerramento automáticos).

### Tarefas principais

| Área | Tarefa | Artefatos |
|------|--------|-----------|
| Domínio | Entidade `Lance` (valor, timestamp, validações) e regras de lance em `Leilao` | `domain/lance.py`, `domain/leilao.py` (regras de lance) |
| Adaptadores | Lock pessimista (`SELECT ... FOR UPDATE`) no repository de leilão para concorrência | `adapters/repositories/leilao_repository.py` (concorrência) |
| Casos de uso | `DarLance` — validação, persistência com lock, publicação de `LanceRealizado` | `use_cases/dar_lance.py` |
| Casos de uso | `EncerrarLeilao` — encerramento, apuração de vencedor ou cancelamento | `use_cases/encerrar_leilao.py` |
| Eventos | Publisher e evento `LanceRealizado` | `adapters/events/publisher.py` |
| Jobs | APScheduler para abrir e encerrar leilões automaticamente | `infra/jobs/encerrar_leiloes.py` |
| API | Endpoint `POST /leiloes/{id}/lances` e `GET /leiloes/{id}/lances` | `infra/flask_app/controllers/`, `infra/flask_app/routes/` |
| Testes | Testes unitários de regras de lance e testes de integração com lock | `tests/unit/`, `tests/integration/` |

### Branches sugeridas

```text
feature/domain-lance
feature/use-case-dar-lance
feature/use-case-encerrar-leilao
feature/adapters-events
feature/jobs-leilao
feature/flask-routes-lances
```

### Papel de Guardião — Arquitetura e Integração

- Mantém a integridade da arquitetura em camadas (domínio → adaptadores → infra)
- Define e documenta contratos de API (request/response, códigos de erro)
- Revisa PRs que cruzam fronteiras de camada para garantir que o domínio não depende de infra
- Mantém o `arquitetura.md` atualizado conforme o projeto evolui

---

## 4. Pedro — Pós-Leilão, Histórico e Auditoria

**GitHub:** [@phpaiva05](https://github.com/phpaiva05)

### Domínio

Responsável pelos fluxos após o encerramento do leilão: registro de histórico, auditoria de ações, e preparação para futuros fluxos de pagamento e notificação.

### Tarefas principais

| Área | Tarefa | Artefatos |
|------|--------|-----------|
| Eventos | Handlers de `LeilaoEncerrado` e `LanceRealizado` para persistir histórico | `adapters/events/handlers/` |
| Eventos | Evento `LeilaoEncerrado` e integração com publisher | `adapters/events/publisher.py` |
| Infra / DB | Models e migrations para tabelas de histórico e auditoria | `infra/db/models/`, `infra/db/migrations/` |
| API | Endpoint `GET /leiloes/{id}` (detalhe com status final e vencedor) | `infra/flask_app/controllers/`, `infra/flask_app/routes/` |
| API | Endpoints futuros de histórico e relatórios de auditoria | `infra/flask_app/` |
| Testes | Testes de integração dos handlers de eventos e fluxos pós-leilão | `tests/integration/` |

### Branches sugeridas

```text
feature/adapters-events-handlers
feature/infra-db-historico-auditoria
feature/flask-routes-historico
```

### Papel de Guardião — Banco e Qualidade

- Responsável pela modelagem geral do banco de dados (normalização, índices, constraints)
- Revisa migrations de todos os integrantes para consistência do schema
- Mantém e evolui a suíte de testes integrados
- Define metas de cobertura e configura `pytest-cov`
- Garante que o pipeline de CI (`Jenkinsfile`) executa todos os testes

---

## Matriz de Colaboração

Áreas onde os domínios se tocam e exigem comunicação entre integrantes:

| Interseção | Integrantes | O que alinhar |
|------------|-------------|---------------|
| Autenticação nos endpoints de lance | Téo + Pedro Vitor | Claims JWT necessários para identificar o usuário que dá lance |
| Criação de leilão → Motor de lances | Caio + Pedro Vitor | Contrato da entidade `Leilao` e estados iniciais |
| Encerramento → Histórico e auditoria | Pedro Vitor + Pedro | Evento `LeilaoEncerrado` — payload e handler |
| Models e migrations | Todos + Pedro (guardião) | Pedro revisa todas as migrations para consistência do schema |
| Branches e PRs | Todos + Caio (guardião) | Caio revisa e aprova PRs antes do merge em `dev` |
| Arquitetura e contratos | Todos + Pedro Vitor (guardião) | Pedro Vitor valida que as camadas estão sendo respeitadas |
| UI/UX (futuro) | Todos + Téo (guardião) | Téo define padrões visuais quando o front-end for implementado |

---

## Referências

- [Próximos passos](proximos-passos.md) — roteiro de implementação e ordem de PRs
- [Arquitetura](arquitetura.md) — camadas, domínio, eventos, concorrência
- [Estrutura e stack](estrutura-e-stack.md) — árvore de diretórios, stack e fluxo de requisição
- [README](../README.md) — visão do produto, regras de leilão e atores
