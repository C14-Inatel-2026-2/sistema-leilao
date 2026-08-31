# Arquitetura Técnica

API REST de marketplace (estilo OLX) com módulo de leilão. A aplicação é **somente backend** — consumível via Swagger, Postman ou testes automatizados, sem frontend acoplado.

O foco arquitetural está em **camadas bem definidas, desacoplamento e consistência sob concorrência**, não em complexidade artificial de regra de negócio.

---

## Padrão arquitetural

O sistema adota **Clean Architecture** combinada com **Event-Driven Architecture**.

```text
domain/          → Entidades e regras puras (Usuario, Anuncio, Leilao, Lance, Categoria)
                   Sem dependência de Flask ou SQLAlchemy — 100% testável isoladamente

use_cases/       → Casos de uso (CriarAnuncio, IniciarLeilao, DarLance, EncerrarLeilao)

adapters/
  repositories/  → Interfaces + implementações concretas (ex.: SQLAlchemyLeilaoRepository)
  events/        → Publisher/Subscriber de eventos de domínio

infra/
  flask_app/     → Rotas, controllers, serialização, autenticação (JWT)
  db/            → Models SQLAlchemy, migrations (Flask-Migrate)
  jobs/          → Jobs agendados de encerramento automático
```

### Regra de dependência

O domínio reside no centro e **não conhece nenhuma camada externa**:

```text
[Dominio do Leilao] <----- [Casos de Uso]
       ^                          ^
       |                          |
[Eventos/Jobs]           [Infraestrutura e Rotas]
```

A infraestrutura e os adaptadores conhecem o domínio; o domínio nunca importa Flask, SQLAlchemy ou Celery.

---

## Modelo de domínio

### Entidades principais

| Entidade | Responsabilidade |
|---|---|
| **Usuario** | Conta, credenciais e papéis (comprador/vendedor) |
| **Anuncio** | Produto, categoria, tipo (venda direta ou leilão), status |
| **Leilao** | Vinculado a um anúncio; preço inicial, incremento mínimo, janela temporal, status |
| **Lance** | Valor, usuário, timestamp; associado a um leilão |
| **Categoria** | Classificação e organização de anúncios |

### Máquina de estados do leilão

```text
agendado → aberto → encerrado → pago
                              ↘ cancelado
```

| Estado | Descrição |
|---|---|
| `agendado` | Leilão criado, aguardando horário de abertura |
| `aberto` | Em andamento; aceita lances válidos |
| `encerrado` | Período de lances finalizado; apura-se o maior lance |
| `pago` | Arrematante efetuou o pagamento |
| `cancelado` | Encerrado sem lances válidos ou interrompido |

**Regras de transição:**

- Só aceita lance quando o status é `aberto`
- Encerramento automático ao atingir `data_hora_fim` (job agendado)
- Encerrado sem lances → status `cancelado`
- Encerrado com lances → vencedor definido pelo maior lance válido

---

## Concorrência em lances

Dois lances quase simultâneos exigem tratamento real de condição de corrida. A estratégia adotada:

1. Transação de banco com **lock pessimista** (`SELECT ... FOR UPDATE`) no registro do leilão
2. Validação de incremento mínimo e janela temporal **dentro da transação**
3. Persistência do lance e atualização do lance atual em operação atômica

O domínio define *quando* um lance é válido; a infraestrutura garante *atomicidade* na persistência.

---

## Eventos de domínio

Transições relevantes publicam eventos desacoplados, consumidos por handlers independentes:

| Evento | Quando é publicado | Consumidores típicos |
|---|---|---|
| `LanceRealizado` | Lance aceito e persistido | Histórico de lances, notificações |
| `LeilaoEncerrado` | Job ou ação manual encerra o leilão | Apuração de vencedor, auditoria |

O event bus interno permite adicionar novos handlers (ex.: e-mail, log de auditoria) sem alterar o caso de uso que originou o evento.

---

## Jobs e automação

O encerramento automático de leilões não pode depender de requisição HTTP. Um job periódico verifica leilões com status `aberto` cuja `data_hora_fim` já passou e dispara o caso de uso `EncerrarLeilao`.

```text
Job agendado
     │
     ▼
Busca leilões abertos com fim <= agora
     │
     ▼
EncerrarLeilao (caso de uso)
     │
     ▼
Publica LeilaoEncerrado
```

**Escolha de tecnologia:**

- **APScheduler** (MVP): scheduler embutido no processo Flask; setup simples, suficiente para encerramento periódico
- **Celery + Redis** (evolução): fila de tarefas com worker separado; indicado se o volume de jobs, retries ou notificações crescer

Em ambos os casos, o job **não contém regra de negócio** — apenas dispara casos de uso já definidos no domínio.

---

## Decisões-chave

- **Domínio isolado** permite trocar a camada de persistência sem alterar regra de negócio
- **Repository pattern** desacopla casos de uso das implementações concretas de banco
- **Eventos de domínio** permitem estender o sistema (notificações, histórico) sem acoplar módulos
- **Testes de domínio puros** (sem banco, sem Flask) garantem cobertura das regras críticas de lance e transição de estado

---
