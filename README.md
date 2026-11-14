# Sistema de Leilão

Marketplace de anúncios com módulo de leilão integrado. Usuários cadastram produtos para **venda direta** ou disponibilizam em **leilão com tempo determinado**; compradores disputam lances dentro de regras claras, e o sistema encerra e apura o vencedor automaticamente.

---

## O que o sistema faz

### Para vendedores

- Criar conta e autenticar-se na plataforma
- Cadastrar anúncios de produtos com categoria e descrição
- Escolher o modo de venda: **venda direta** ou **leilão**
- Configurar leilão: preço inicial, incremento mínimo, data/hora de início e fim
- Acompanhar lances recebidos durante o leilão

### Para compradores

- Criar conta e autenticar-se
- Buscar e filtrar anúncios por categoria, tipo ou palavra-chave
- Dar lances em leilões abertos
- Consultar histórico de lances de um leilão
- Ver resultado após encerramento (vencedor ou cancelamento)

### Para o sistema (automação)

- Abrir leilões agendados no horário definido
- Encerrar leilões automaticamente ao atingir a data/hora de fim
- Definir o vencedor pelo maior lance válido
- Cancelar leilões encerrados sem nenhum lance

---

## Regras do leilão

| Regra | Comportamento |
|---|---|
| Janela temporal | Lances só são aceitos enquanto o leilão está `aberto` e dentro do prazo |
| Incremento mínimo | Cada lance deve ser pelo menos `lance_atual + incremento_minimo` |
| Concorrência | Dois lances simultâneos são tratados de forma consistente — apenas um prevalece |
| Encerramento | Ao fim do prazo, o leilão encerra sozinho; o maior lance válido vence |
| Sem lances | Leilão encerrado sem lances é marcado como `cancelado` |

### Ciclo de vida de um leilão

```text
agendado  →  aberto  →  encerrado  →  pago
                                   ↘ cancelado (sem lances)
```

---

## Requisitos

### Requisitos funcionais

| ID | Requisito |
|---|---|
| RF01 | O sistema deve permitir o cadastro de usuários com nome, e-mail único e senha |
| RF02 | O sistema deve autenticar o usuário e emitir um token de acesso com expiração |
| RF03 | O usuário autenticado deve poder consultar os próprios dados |
| RF04 | O vendedor deve poder cadastrar anúncios com título, descrição, categoria e tipo (venda direta ou leilão) |
| RF05 | O sistema deve listar anúncios com filtros por categoria, status, tipo e texto |
| RF06 | O vendedor deve poder configurar um leilão com preço inicial, incremento mínimo e data/hora de início e fim |
| RF07 | O sistema deve abrir automaticamente os leilões agendados ao chegar o horário de início |
| RF08 | O comprador deve poder dar lances em leilões abertos, respeitando a janela temporal e o incremento mínimo |
| RF09 | O sistema deve exibir o histórico de lances de um leilão em ordem cronológica reversa (do mais recente ao mais antigo) |
| RF10 | O sistema deve encerrar os leilões automaticamente ao fim do prazo, definindo como vencedor o maior lance válido ou cancelando o leilão sem lances |
| RF11 | O sistema deve registrar em auditoria os lances realizados e os encerramentos de leilão |
| RF12 | O vendedor deve poder editar e inativar os próprios anúncios |
| RF13 | O sistema deve registrar a venda e simular o pagamento após o encerramento do leilão |

### Requisitos não funcionais

| ID | Categoria | Requisito | Como é garantido |
|---|---|---|---|
| RNF01 | Segurança | Senhas nunca armazenadas em texto puro | Hash com bcrypt (`adapters/security/password_hasher.py`) |
| RNF02 | Segurança | Rotas protegidas exigem token válido e expirável | JWT assinado, validado em `get_current_user`; resposta 401 |
| RNF03 | Segurança | O login não revela se um e-mail está cadastrado | Mesma mensagem de erro para e-mail inexistente, senha errada ou conta inativa |
| RNF04 | Segurança | Dependências e imagem sem vulnerabilidades conhecidas corrigíveis | Trivy e Grype no pipeline |
| RNF05 | Consistência | Lances simultâneos no mesmo leilão não podem corromper o estado | Lock pessimista (`SELECT ... FOR UPDATE`) no repositório de leilão |
| RNF06 | Manutenibilidade | Regras de negócio independentes de framework e banco | Clean Architecture: `domain` e `use_cases` não importam FastAPI nem SQLAlchemy |
| RNF07 | Qualidade | Código testado e padronizado | Testes unitários e de integração (pytest), cobertura mínima de 70% no pipeline e Ruff |
| RNF08 | Integração contínua | Toda mudança passa por verificação automática antes do merge | Jenkins: Hadolint, Ruff, build, testes, security scan e publicação da imagem |
| RNF09 | Usabilidade da API | Contrato da API documentado e testável | OpenAPI gerado pelo FastAPI em `/docs` e `/redoc` |
| RNF10 | Portabilidade | Mesmo ambiente em desenvolvimento, CI e produção | Imagem Docker; PostgreSQL via `docker compose` |
| RNF11 | Consistência de dados | Esquema do banco versionado | Migrations com Alembic |

---

## Atores

| Ator | Papel |
|---|---|
| **Vendedor** | Cadastra produtos, configura leilões, acompanha disputas |
| **Comprador** | Busca anúncios, dá lances, consulta histórico |
| **Sistema** | Abre/fecha leilões no horário, apura vencedor, publica eventos |

---

## Exemplos de uso

1. **Vendedor cria leilão** — cadastra um notebook com preço inicial R$ 500, incremento mínimo R$ 50, encerramento em 24 h.
2. **Comprador dá lance** — oferece R$ 550; o lance é aceito e registrado no histórico.
3. **Lance inválido rejeitado** — tentativa de R$ 520 (abaixo do mínimo) retorna erro.
4. **Encerramento automático** — ao fim das 24 h, o sistema define o maior lance como vencedor.
5. **Consulta de histórico** — qualquer usuário autenticado vê todos os lances de um leilão encerrado.

---

## Como consumir a API

A aplicação é uma **API REST** (sem interface gráfica). Endpoints documentados via **Swagger/OpenAPI** gerado pelo FastAPI — acessível em `/docs` (ReDoc em `/redoc`) quando a aplicação estiver rodando.

Ferramentas sugeridas para teste manual: Postman, Insomnia ou `curl`.

---

## Desenvolvimento

Os comandos do dia a dia estão no taskipy (`pyproject.toml`). Depois de `poetry install`:

```text
poetry run task --list
```

| Tarefa | O que faz |
|---|---|
| `lint` | `ruff check` e `ruff format --check` |
| `format` | aplica formatação e correções do ruff |
| `test` | suite do pytest |
| `coverage` | testes com cobertura, no mesmo formato do CI |
| `check` | `lint` e `test` |
| `api` | sobe a API (`uvicorn` com reload) |
| `db-up` / `db-down` | sobe ou derruba o PostgreSQL (`docker compose`) |
| `migrate` | `alembic upgrade head` |
| `revision` | gera uma migration; argumentos extras vão depois de `--` |

```text
poetry run task check
poetry run task api
poetry run task revision -- -m "create catalogo tables"
```

Antes da API e das migrations, copie o ambiente (`cp .env.example .env`) e suba o banco (`poetry run task db-up`).

---

## Documentação técnica

- [Arquitetura](docs/arquitetura.md) — camadas, domínio, eventos, concorrência
- [Hierarquia de exceções](docs/hierarquia-excecoes.md) — `DomainError` unificado e mapeamento para HTTP (400 validação, 401 credenciais/token, 409 e-mail duplicado)
- [Estrutura e stack](docs/estrutura-e-stack.md) — árvore de diretórios e tecnologias
- [Próximos passos](docs/proximos-passos.md) — estado atual e ordem de PRs
- [Arquivamento de conversas com IA](docs/arquivamento-conversas-ia.md) — exportação e publicação de chats com IA

Documentos de entrega acadêmica (Projeto C14): [`Projeto-C14/docs/`](Projeto-C14/docs/EntregaInicial/).

---

## Branches

| Branch | Propósito |
|---|---|
| `main` | Documentação estável e referência do projeto |
| `dev` | Integração do código em desenvolvimento |
| `feature/*`, `chore/*` | Trabalho isolado; merge em `dev` via pull request |
| `refactor/*` | Refatorações sem mudança de comportamento externo; merge em `dev` via pull request |
| `fix/*` | Correções (bugs, vulnerabilidades); merge em `dev` via pull request |
| `docs/*` | Documentação; merge em `dev` via pull request |

---

## Refactorings

Refactorings aplicados no projeto. Cada um passou pelo pipeline (lint, testes e security scan) verde antes e depois da mudança.

| Autor | Smell | Refactoring aplicado | Por quê | PR |
|---|---|---|---|---|
| Téo ([@TSM-05](https://github.com/TSM-05)) | Validação fora de ordem: `CadastrarUsuario` gerava o hash da senha antes de validar nome e e-mail | Validar os dados de entrada antes do hash e expor `validar_nome` no domínio | Evita processar bcrypt (operação cara) com dados que seriam recusados e mantém a regra no domínio | [#55](https://github.com/C14-Inatel-2026-2/sistema-leilao/pull/55) |
| Téo ([@TSM-05](https://github.com/TSM-05)) | Primitive Obsession: e-mail como `str` solta, sem normalização (permitia contas duplicadas por diferença de maiúsculas) | Replace Primitive with Object: Value Object `Email` | A regra de e-mail fica num lugar só e acabam as contas duplicadas | [#65](https://github.com/C14-Inatel-2026-2/sistema-leilao/pull/65) |
| Pedro ([@phpaiva05](https://github.com/phpaiva05)) | Global Mutable State / Handlers Duplication: `register_auditoria_handlers` usava `append` em dicionário global, duplicando gravações caso chamada múltiplas vezes | Idempotent Event Registration: registro idempotente de handlers no barramento de eventos | Evita gravações duplicadas de auditoria e garante isolamento nos testes e inicialização segura | [#70](https://github.com/C14-Inatel-2026-2/sistema-leilao/pull/70) |
| Pedro ([@phpaiva05](https://github.com/phpaiva05)) | Middle Man / Lazy Module: `adapters/events/publisher.py` apenas reexportava símbolos do `__init__.py` sem adicionar comportamento | Inline Module / Remove Middle Man: remoção do módulo redundante e importação direta de `adapters.events` | Elimina código morto, simplifica a arquitetura e reduz complexidade acidental | [#70](https://github.com/C14-Inatel-2026-2/sistema-leilao/pull/70) |
| Pedro Vitor ([@PedroVGSC](https://github.com/PedroVGSC)) | Duplicated Code: a regra da janela temporal (`momento < data_inicio or momento >= data_final`) estava repetida em `Leilao.abrir` e `Leilao.validar_lance` | Extract Method: `Leilao._dentro_da_janela(momento)` | A regra da janela fica num lugar só: abertura e lance não podem divergir se o limite mudar | [#75](https://github.com/C14-Inatel-2026-2/sistema-leilao/pull/75) |
| Pedro Vitor ([@PedroVGSC](https://github.com/PedroVGSC)) | Duplicate Query: `valor_minimo_proximo_lance` chamava `maior_lance()` duas vezes, percorrendo a lista de lances duas vezes | Extract Variable: guarda o maior lance numa variável local | Uma passada só pela lista de lances a cada validação e código mais legível | [#75](https://github.com/C14-Inatel-2026-2/sistema-leilao/pull/75) |
