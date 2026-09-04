# Mini Leilão com Marketplace – Relatório de Produto, Arquitetura e Roadmap

## Summary

Este relatório define, de forma estruturada, o que deve ser construído em um mini marketplace com módulo de leilão para uma disciplina de engenharia de software, com foco em backend web. A partir de uma visão de produto, requisitos técnicos e comportamentais, o documento propõe uma arquitetura em camadas (Clean Architecture), mapeia funcionalidades essenciais, discute riscos (como concorrência em lances e fraudes) e sugere um roadmap de implementação. Em síntese:

- **Propósito e escopo:** sistema acadêmico, somente backend web, estilo marketplace simples com leilões; sem apps mobile nativos nem integrações externas reais (pagamento, redes sociais).
- **Visão de produto:** três papéis (comprador, vendedor, administrador opcional), fluxo mínimo de publicar, leiloar, dar lances, encerrar e registrar “venda simulada”; definição de um “corpus dourado” de cenários que o sistema precisa sempre atender.
- **Arquitetura técnica:** uso de Clean Architecture com camadas `domain/`, `use_cases/`, `adapters/`, `infra/`; stack em Python/Flask/PostgreSQL; tratamento explícito de race conditions em lances via transações e locks; preparação para jobs agendados e, se desejado, evolução para processamento assíncrono.
- **Funcionalidades:** cadastro e autenticação (JWT), anúncios e catálogo, leilões (estados, regras de lance, histórico), registro de “venda” e pagamento simulado, rotas administrativas de monitoramento.
- **Comportamento e UX:** análise de motivadores de compradores e vendedores, desenho dos fluxos principais (onboarding, venda, compra), foco em transparência das regras e mensagens de erro claras para construir confiança.
- **Desafios e riscos:** prevenção básica de fraudes (por exemplo, lances artificiais), latência e consistência em lances concorrentes, equilíbrio entre realismo de regras e simplicidade acadêmica, risco de overengineering.
- **Roadmap e métricas:** implementação iterativa começando pelo domínio e testes; distinção entre MVP e incrementos; métricas de sucesso centradas em cobertura de testes, aderência à arquitetura, clareza da API e atendimento ao “corpus dourado” de cenários.

---

## 1. Introdução e Escopo

### 1.1 Objetivo do projeto acadêmico (backend web-only)

O objetivo deste projeto é desenvolver um backend web de um mini marketplace com leilões, servindo como laboratório de práticas de engenharia de software. Em vez de perseguir um produto comercial completo, a ênfase está em:

- Modelar corretamente o domínio de marketplace + leilão.
- Aplicar princípios arquiteturais sólidos (Clean Architecture, separação de camadas, independência de frameworks no domínio).
- Desenvolver uma base de testes automatizados que cubra regras críticas de negócio, especialmente as que envolvem concorrência em lances.
- Experimentar automação de build e testes via CI/CD (por exemplo, Jenkins).

Trata-se de um projeto **backend-only**: a API REST será consumida por ferramentas como Swagger, Postman ou clientes web desenvolvidos à parte. Essa separação explicita o contrato entre backend e qualquer frontend, e força o grupo a pensar cuidadosamente no desenho das rotas e dos payloads de entrada/saída.

Em termos pedagógicos, isso permite que a disciplina avalie o que interessa do ponto de vista de engenharia – clareza de domínio, coesão de módulos, legibilidade de código, cobertura de testes – sem que o tempo de curso seja gasto na construção de interfaces ricas.

### 1.2 Contexto: mini marketplace estilo “classificados” com módulo de leilão

O contexto funcional é um mini marketplace de anúncios de produtos (novos ou usados), semelhante a uma aplicação de classificados on-line. Cada anúncio descreve um item, com título, descrição, categoria e um preço de referência. A diferença em relação a um marketplace puramente “compre já” é a presença de um módulo de leilão:

- Vendedores podem escolher vender diretamente ou abrir um leilão para um anúncio.
- Compradores podem disputar itens em leilões, dando lances dentro de uma janela de tempo definida.
- O sistema precisa determinar um vencedor de leilão, com base nas regras de lance, e registrar uma “venda simulada”.

Do ponto de vista de domínio, isso gera um conjunto interessante de entidades e relações: `Usuario`, `Anuncio`, `Leilao`, `Lance`, `Categoria`, `Venda`. Para a disciplina, o valor está em estruturar essas entidades e suas regras de forma consistente, isolada de detalhes de transporte HTTP ou persistência.

### 1.3 Limitações intencionais

Para manter o escopo viável no tempo da disciplina e evitar dispersão:

- Não haverá app mobile nativo. Qualquer consumo em mobile se dará via navegador sobre uma UI web ou ferramentas de teste.
- Não haverá integrações externas reais: pagamentos, notificações (e-mail/SMS), redes sociais e serviços de verificação de identidade serão simulados internamente.
- Não será implementado WebSocket ou “tempo real” pleno no MVP. Os leilões serão atualizados via chamadas HTTP normais; se desejado, notificações em “quase tempo real” podem ser simuladas como incremento posterior.
- Escala e alta disponibilidade não são objetivos primários: o projeto pode supor uma única instância da aplicação e de banco, ainda que a arquitetura seja pensada para permitir evolução.

Essas restrições são deliberadas. Muitos fracassos em projetos acadêmicos vêm de tentar introduzir tecnologias e integrações demais antes de estabilizar o núcleo funcional. Ao deixar claro que o objetivo não é competir com grandes plataformas, mas sim fazer um mini sistema bem modelado e bem testado, a disciplina reduz o risco de overengineering.

### 1.4 Metas de aprendizagem: arquitetura, domínio, testes e CI/CD

A partir desse contexto, as metas centrais de aprendizagem são:

**Arquitetura em camadas (Clean Architecture)**

- Domínio (`domain/`) independente de frameworks, contendo regras de negócio puras.
- Casos de uso (`use_cases/`) orquestrando ações sobre o domínio.
- Adaptadores (`adapters/`) implementando persistência e infraestrutura de eventos.
- Infraestrutura (`infra/`) expondo o domínio via HTTP, bancos de dados e jobs.

**Modelagem de domínio com estados explícitos**

- Máquina de estados de leilão clara (por exemplo, `agendado → aberto → encerrado → pago/cancelado`).
- Invariantes bem definidas (por exemplo, “só aceita lance em leilão aberto”, “o valor do lance deve ser pelo menos `lance_atual + incremento_mínimo`”).

**Teste automatizado de regras críticas**

- Testes unitários cobrindo transições de estado, validação de lances, cálculo de vencedor.
- Testes de integração de API e de concorrência (múltiplos lances simultâneos).

**Integração contínua**

- Criação de um pipeline simples (por exemplo, com Jenkins) que execute testes automaticamente a cada alteração, garantindo que regressões sejam detectadas cedo.

Essas metas alinham o projeto a boas práticas da indústria, em um domínio suficientemente rico para ser desafiador, mas suficientemente pequeno para ser dominado dentro de um semestre.

---

## 2. Visão de Produto e Domínio

### 2.1 Perfis e papéis

A plataforma terá, no mínimo, três tipos de papéis lógicos:

| Papel | Descrição resumida | Permissões principais (exemplos) |
|---|---|---|
| Comprador | Usuário que navega o catálogo e participa de leilões | Ver anúncios/leilões; dar lances; consultar histórico de lances |
| Vendedor | Usuário que oferta produtos no marketplace | Criar/editar anúncios; iniciar leilões; encerrar leilões próprios |
| Admin (opcional) | Operador responsável por monitorar e intervir no sistema | Listar todos os leilões; encerrar leilões problemáticos; consultar logs |

No modelo de domínio, isso pode ser representado por um campo `role` na entidade `Usuario`, com valores como `COMPRADOR`, `VENDEDOR`, `ADMIN` (ou combinações). As checagens de permissão não devem ficar espalhadas em `if`s na camada HTTP; o ideal é:

- Ter métodos de domínio ou casos de uso que expressem regras como “apenas o dono do anúncio pode iniciar um leilão para ele”.
- Assegurar que a camada de API apenas traduza o papel/identidade do JWT em um objeto de domínio ou contexto, repassando para o caso de uso.

Do ponto de vista de Product Management, uma definição clara de papéis ajuda a evitar ambiguidade: por exemplo, se o mesmo usuário pode ser comprador e vendedor, isso deve ficar explícito no modelo (e possivelmente refletido em permissões compostas).

Além disso, é aconselhável decidir desde cedo se o papel Admin existirá como usuário “normal com privilégios” ou se algumas operações administrativas serão expostas apenas como comandos internos (admin scripts, etc.). Para um projeto acadêmico, um papel Admin simples, autenticado via JWT como os demais, é geralmente suficiente.

### 2.2 Modelo de negócio simplificado

O modelo de negócio deste mini marketplace pode ser descrito por dois fluxos principais:

**Venda direta**

- Vendedor cria um `Anuncio` com um preço fixo.
- Comprador interessado efetua a compra “no ato” (no MVP, isso é um registro de venda simulada).
- O anúncio é marcado como vendido ou inativado.

**Venda via leilão**

- Vendedor cria um `Anuncio` e, a partir dele, inicia um `Leilao` com:
  - preço inicial;
  - incremento mínimo;
  - data/hora de início e fim.
- Compradores dão lances dentro da janela de leilão.
- Ao fim, o maior lance válido vence e gera uma “venda simulada”.

Uma decisão importante é a relação entre `Anuncio` e `Leilao`. Duas alternativas comuns:

- **1:1** – cada anúncio tem, no máximo, um leilão associado.
- **1:N** – um anúncio pode ter vários leilões em momentos diferentes (por exemplo, se um leilão falhar por falta de lances, o vendedor pode abrir outro).

Para o MVP, a abordagem **1:1** simplifica a implementação:

- O anúncio mantém um campo `leilao_atual_id`.
- O leilão referencia o anúncio via `anuncio_id`.
- Regras de domínio garantem que não existam dois leilões “ativos” para o mesmo anúncio.

A visão de produto também deve definir um “corpus mínimo de cenários” que o sistema precisa suportar ponta a ponta, algo análogo a um “golden corpus” de casos de uso. Exemplos:

- Criar anúncio sem leilão; venda direta simples.
- Criar anúncio, iniciar leilão, receber lances válidos; encerrar com vencedor.
- Tentar dar lance inválido (valor baixo, leilão encerrado, usuário bloqueado).
- Leilão encerrado sem lances, marcado como cancelado.

Esse conjunto de cenários é o “contrato” de produto: qualquer evolução (inclusive técnica) deve preservar seu funcionamento, e testes automatizados devem ser construídos em torno deles.

### 2.3 Estados e regras de domínio

A máquina de estados do leilão pode ser modelada como:

| Estado | Descrição |
|---|---|
| `AGENDADO` | Leilão criado, aguardando o horário de início |
| `ABERTO` | Leilão em andamento; aceita lances válidos |
| `ENCERRADO` | Janela de lances fechada; resultado ainda não consolidado em pagamento |
| `PAGO` | Venda simulada finalizada com “pagamento aprovado” |
| `CANCELADO` | Leilão encerrado sem lances válidos, ou cancelado manualmente pelo vendedor/admin |

A partir daí, regras de transição podem ser descritas de forma explícita:

- `AGENDADO → ABERTO`: quando a data/hora de início é atingida (pode ser verificado via job ou em leitura).
- `ABERTO → ENCERRADO`: ao atingir a data/hora de fim ou por encerramento manual.
- `ENCERRADO → PAGO` ou `ENCERRADO → CANCELADO`: dependendo da existência (ou não) de lance vencedor e da simulação de pagamento.

Invariantes importantes incluem:

- Leilão só aceita lance quando está em estado `ABERTO`.
- Todo lance aceito deve ter:
  - valor ≥ `lance_atual + incremento_mínimo`;
  - timestamp dentro da janela `[inicio, fim]`;
  - usuário autorizado (não bloqueado e diferente do próprio vendedor, se assim definido).

Essas regras devem viver no domínio (`Leilao` + métodos auxiliares), não em controllers; isso permite testá-las isoladamente, sem dependência de banco, HTTP ou autenticação.

Do ponto de vista de governança do produto, é útil definir quem, no grupo, será o “curador” das regras de domínio: quem valida mudanças em estados, mensagens de erro, regras de lance. Mesmo em um projeto pequeno, alguém precisa zelar pela consistência conceitual para evitar que o sistema vire uma soma de decisões locais ad hoc.

---

## 3. Arquitetura Técnica e Stack

### 3.1 Padrão arquitetural

A arquitetura proposta segue um padrão de Clean Architecture com leve inspiração em arquiteturas orientadas a eventos:

| Camada | Pasta raiz | Responsabilidade principal |
|---|---|---|
| Domínio | `domain/` | Entidades e regras de negócio puras (sem frameworks): `Usuario`, `Anuncio`, `Leilao`, etc. |
| Aplicação | `use_cases/` | Casos de uso (serviços de aplicação) que orquestram entidades, repositórios e eventos |
| Adaptadores | `adapters/` | Implementações de interfaces (repositórios, event bus, gateways se existirem) |
| Infraestrutura | `infra/` | Entrada/saída do sistema: API HTTP (Flask), ORM (SQLAlchemy), jobs (APScheduler), etc. |

A regra de dependência central é:

- O domínio não conhece as camadas externas.
- Use cases podem depender do domínio e de interfaces (repositórios, publishers), mas não de implementação concreta.
- Adaptadores e infraestrutura conhecem domínio e use cases, nunca o contrário.

Visualmente:

```text
            +------------------------+
            |        infra/          |
            | (Flask, DB, Jobs...)   |
            +-----------+------------+
                        |
                        v
              +------------------+
              |   adapters/      |
              | (repos, events)  |
              +---------+--------+
                        |
                        v
              +------------------+
              |   use_cases/     |
              +---------+--------+
                        |
                        v
              +------------------+
              |    domain/       |
              +------------------+
```

Essa estrutura permite, por exemplo, trocar o framework web (Flask por FastAPI) ou o mecanismo de persistência (SQLAlchemy por outro ORM) sem modificar as entidades de domínio ou os casos de uso.

### 3.2 Organização do repositório

A árvore de diretórios proposta é:

```text
sistema-leilao/
├── domain/
│   ├── usuario.py
│   ├── anuncio.py
│   ├── leilao.py
│   ├── lance.py
│   └── categoria.py
│
├── use_cases/
│   ├── criar_anuncio.py
│   ├── iniciar_leilao.py
│   ├── dar_lance.py
│   └── encerrar_leilao.py
│
├── adapters/
│   ├── repositories/
│   │   ├── leilao_repository.py
│   │   ├── anuncio_repository.py
│   │   └── usuario_repository.py
│   └── events/
│       ├── publisher.py
│       └── handlers/
│
├── infra/
│   ├── flask_app/
│   │   ├── app.py
│   │   ├── routes/
│   │   └── controllers/
│   ├── db/
│   │   ├── models/
│   │   └── migrations/
│   └── jobs/
│       └── encerrar_leiloes.py
│
├── tests/
│   ├── unit/
│   └── integration/
│
├── docs/
│   ├── arquitetura.md
│   └── especificacoes.md
│
├── Jenkinsfile
├── pyproject.toml
├── docker-compose.yml
└── README.md
```

Essa organização explicita as responsabilidades:

- `domain/`: foco em regra de negócio.
- `use_cases/`: foco em fluxos de aplicação (orquestração).
- `adapters/`: foco em integração com recursos externos internos ao processo (banco, fila, logs).
- `infra/`: foco em tecnologias de borda (HTTP, DB, agendadores).
- `tests/`: espelha as camadas, com testes unitários para domínio/use_cases e de integração para adapters/infra.

### 3.3 Stack tecnológica

A stack base recomendada é:

| Camada / Finalidade | Tecnologia (sugestão) |
|---|---|
| Linguagem | Python 3.11+ |
| Framework web | Flask (+ extensões REST) |
| ORM e migrations | SQLAlchemy + Flask-Migrate |
| Banco de dados | PostgreSQL |
| Autenticação | JWT (biblioteca para Flask) |
| Gerenciamento de dependências | Poetry |
| Testes | pytest (+ extensões) |
| Documentação de API | Swagger/OpenAPI (por ex., Flasgger) |
| CI/CD | Jenkins (via Jenkinsfile) |
| Jobs agendados | APScheduler (MVP) |

Essa combinação equilibra simplicidade e realismo: todas são tecnologias amplamente usadas, com boa documentação e tooling em torno.

### 3.4 Concorrência e transações

Um dos pontos mais críticos do sistema é garantir a consistência dos lances em cenários onde vários usuários podem tentar dar lance ao mesmo tempo. Em uma plataforma de leilão real, essa é uma exigência central: pequenas discrepâncias de ordem ou valor podem gerar injustiças percebidas pelos usuários e até disputas legais (*A Framework for Realtime Online Auctions*).

Para o projeto acadêmico, uma estratégia recomendada é:

**Ao registrar um lance:**

1. Iniciar uma transação no banco.
2. Carregar o registro do leilão (e/ou o “estado atual” – último lance) com lock pessimista (`SELECT ... FOR UPDATE`).
3. Verificar, dentro da transação:
   - se o leilão ainda está `ABERTO`;
   - se o horário atual está dentro `[inicio, fim]`;
   - se o valor do lance é ≥ `último_lance + incremento_mínimo`.
4. Se as condições forem satisfeitas:
   - inserir o novo lance;
   - atualizar o “lance atual” no leilão;
   - commitar a transação.
5. Em caso de falha em qualquer validação:
   - abortar a transação;
   - retornar erro significativo na API.

Essa abordagem garante que dois lances concorrentes sejam serializados em relação ao mesmo leilão, evitando que ambos sejam aceitos em condições que deveriam rejeitar um deles. É mais simples de implementar do que arquiteturas com filas dedicadas ou partições temporais, e suficiente para o volume esperado em ambiente acadêmico.

Além de implementar a lógica, é essencial escrever testes específicos de concorrência, mesmo que simulando paralelismo com threads ou processos em um ambiente de teste controlado.

### 3.5 Eventos de domínio e notificações internas

Embora o sistema não vá integrar notificações externas reais no MVP, é desejável pensar em termos de eventos de domínio:

- `LanceRealizado`: publicado quando um lance é aceito.
- `LeilaoEncerrado`: publicado quando um leilão muda para estado `ENCERRADO`.
- `VendaRegistrada`: publicado quando uma venda simulada é criada.

Esses eventos podem ser representados por classes simples no domínio e publicados por meio de uma interface em `adapters/events/publisher.py`. Inicialmente, um publisher simples (que apenas registra eventos em log ou em uma tabela de auditoria) é suficiente. Se, futuramente, quiserem experimentar notificações em tempo quase real (por exemplo, via WebSockets), bastará adicionar um novo handler para os mesmos eventos, sem alterar os casos de uso que os emitem.

Em ambientes de produção, recomenda-se que canais de tempo real (como WebSockets) apliquem boas práticas de segurança – autenticação por token, uso de TLS (`wss://`), validação do cabeçalho de origem, rate limiting e renovação de sessão (*WebSocket Security Cheat Sheet*). Mesmo que o projeto acadêmico não implemente WebSockets, entender essas práticas ajuda a projetar uma arquitetura que possa evoluir nessa direção.

---

## 4. Funcionalidades Essenciais

### 4.1 Usuários e autenticação

A base de qualquer marketplace é a gestão de usuários. O sistema deve prover:

**Cadastro de usuários com:**

- e-mail único;
- senha (armazenada com hash seguro);
- nome;
- papel inicial (comprador, vendedor ou ambos).

**Login:**

- endpoint que recebe credenciais;
- valida credenciais no domínio;
- emite um JWT com claims como:
  - `sub` (ID do usuário);
  - `role`;
  - `exp` (expiração).

**Gestão de perfil:**

- endpoint autenticado para consultar dados básicos;
- opcionalmente, endpoint para atualizar dados não sensíveis (por exemplo, nome, telefone).

Para reforço de segurança (mesmo em ambiente acadêmico), é interessante discutir:

- **Estados de usuário:** ativo, bloqueado, pendente.
- Usuários podem ser bloqueados, por exemplo, após muitas tentativas de login falhas ou por suspeita de abuso (como comportamento de fraude em lances).
- **Autenticação multifator (MFA) opcional:**
  - Ainda que não seja implementada na íntegra, pode-se modelar um campo “MFA habilitado” e definir pontos de integração futura (por exemplo, exigência de código adicional em operações sensíveis como encerrar leilão ou registrar venda).

Essas escolhas ajudam a criar um modelo mental de segurança em camadas: mesmo que o MVP implemente apenas senha + JWT, o domínio já está pensado para suportar mecanismos mais fortes em incrementos futuros.

### 4.2 Anúncios e catálogo

O módulo de anúncios e catálogo é responsável por:

**CRUD de `Anuncio`:**

- criar novo anúncio (vendedor autenticado);
- editar anúncio (somente o dono, enquanto não houver venda/leilão ativo);
- inativar anúncio (por exemplo, após venda ou por opção do vendedor).

**Atributos de `Anuncio`:**

- título, descrição, categoria;
- preço de referência;
- status (`ATIVO`, `INATIVO`, talvez `VENDIDO`);
- indicação se há leilão associado.

**Filtros para listagem:**

- por categoria;
- por faixa de preço;
- por vendedor;
- por status (por exemplo, “com leilão aberto”).

Do ponto de vista de API, é importante:

- Projetar endpoints de listagem com paginação (mesmo que o volume de dados seja pequeno), pois essa é a prática em aplicações reais.
- Definir ordenação padrão (por exemplo, anúncios mais recentes primeiro) e permitir ordenação por preço ou data, se fizer sentido.

O domínio deve conter regras básicas, como:

- Não permitir que um anúncio inativo seja usado para criar novos leilões.
- Não permitir edição de campos críticos (por exemplo, descrição, preço de referência) depois que um leilão associado tenha recebido lances, para evitar “mudanças de escopo” durante uma disputa.

### 4.3 Leilões e lances

O núcleo funcional do projeto está aqui. As principais operações são:

**Criação/agendamento de leilão:**

- Vendedor seleciona um anúncio elegível.
- Informa preço inicial, incremento mínimo, datas de início e fim.
- O domínio valida:
  - que não há outro leilão `AGENDADO`/`ABERTO` para o mesmo anúncio;
  - que a data/hora de início é antes da de fim;
  - que os valores de preço inicial e incremento mínimo são positivos.

**Abertura de leilão:**

- Pode ser interpretada como um estado derivado (se `agora ≥ início`) ou como uma transição explícita (por um job que marca `AGENDADO → ABERTO`).

**Recebimento de lances:**

- Endpoint autenticado de lance: `POST /leiloes/{id}/lances`.
- Corpo com valor do lance e, opcionalmente, comentários.
- Domínio verifica as invariantes explicadas na Seção 2.3.
- Em caso de aceitação, é criado um `Lance` e atualizado o “lance atual” do leilão.

**Histórico de lances e auditoria:**

- Endpoint de leitura autenticado ou público (dependendo da política) para listar lances de um leilão, em ordem cronológica.
- Isso reforça a percepção de justiça e permite depuração de problemas.

**Encerramento de leilão:**

- Pode ocorrer de forma:
  - automática (job verifica fim da janela e executa caso de uso `EncerrarLeilao`);
  - manual (vendedor ou admin aciona endpoint de encerramento antecipado, respeitando regras).
- O domínio decide:
  - se houve lance vencedor;
  - quem é o usuário vencedor e qual o valor final;
  - para qual estado o leilão vai (`ENCERRADO` com vencedor, ou `CANCELADO` sem lances).

Pesquisas sobre sistemas de leilão on-line destacam que a implementação correta do mecanismo de lance e do critério de vencedor é essencial para a credibilidade da plataforma, e que problemas de concorrência podem levar a disputas e assimetria de informação entre participantes (*A Framework for Realtime Online Auctions*). Mesmo em escala acadêmica, tratar esses detalhes com rigor prepara o grupo para desafios similares em ambientes reais.

### 4.4 “Venda” e pagamento simulado

Depois que um leilão é encerrado com vencedor, ou que uma venda direta é acionada, o sistema deve:

- Criar uma entidade de `Venda` ou `Pedido`, associando:
  - anúncio;
  - comprador;
  - valor final (no caso de leilão, valor do lance vencedor; em venda direta, preço fixo);
  - data de criação;
  - método de pagamento simulado;
  - status de pagamento.
- Tratar o pagamento como simulado, com estados como:
  - `PENDENTE`: assim que a venda é registrada;
  - `APROVADO`: quando um endpoint interno é chamado para “simular” aprovação;
  - `CANCELADO`: se a venda é cancelada (por exemplo, por desistência).

O objetivo aqui não é reproduzir fluxos complexos de gateway de pagamento, mas modelar os estados de uma transação financeira de forma suficientemente realista para permitir discussões sobre consistência de dados e casos de falha (como cancelamento). Isso também permite conectar o estado `PAGO` do `Leilao` ao estado da venda.

### 4.5 Administração e monitoramento (opcional)

Funcionalidades administrativas podem incluir:

**Console de leilões:**

- Listar todos os leilões `ABERTOS`, `AGENDADOS`, `ENCERRADOS`, `CANCELADOS`.
- Filtros por vendedor, categoria, intervalo de datas.

**Histórico de ações:**

- Expor, de forma controlada, entradas de log relevantes (por exemplo, criação de leilões, encerramentos, lances rejeitados por motivo X).

**Operações de correção:**

- Encerrar manualmente um leilão em estado problemático.
- Marcar uma venda como `CANCELADA` em cenários de disputa (por exemplo, se algo deu errado no fluxo).

Essas rotas não são estritamente necessárias para o MVP, mas são um excelente campo de prática para controle de acesso baseado em papel, além de facilitar a própria depuração do sistema durante a disciplina.

---

## 5. Aspectos Comportamentais e UX

### 5.1 Perfis de comportamento

Compreender como compradores e vendedores tendem a se comportar em plataformas de leilão ajuda a construir um produto mais coerente, mesmo em escala acadêmica.

**Vendedor:**

- Quer equilibrar preço e rapidez:
  - se acredita que o item é muito desejado ou raro, tende a preferir leilão;
  - se quer liquidez imediata, prefere venda direta.
- Valoriza a simplicidade para publicar e acompanhar seus anúncios/leilões.
- Tem receio de fraudes (por exemplo, comprador vencedor que não paga) e valoriza alguma visibilidade do histórico de compradores.

**Comprador:**

- Busca barganha e oportunidade de pagar abaixo do valor de mercado.
- Gosta da “emoção da disputa”, especialmente perto do fim do leilão.
- Valoriza confiança no mecanismo: regras claras, histórico de lances transparente, ausência de lances artificiais óbvios.

Estudos sobre *shill bidding* (lances falsos, frequentemente dados pelo próprio vendedor ou por cúmplices para elevar artificialmente o preço) indicam que usuários tendem a se tornar mais céticos e a evitar leilões em que percebem padrões estranhos de lance, o que afeta engajamento e reputação da plataforma (*Shill bidding in online platforms*). Mesmo que o projeto não implemente mecanismos sofisticados de detecção, é útil ter consciência desses riscos ao desenhar logs e controles.

### 5.2 Fluxos principais

Três fluxos de UX são centrais:

**Onboarding:**

- Fluxo: cadastro → login → obtenção de token JWT.
- Experiência desejada:
  - Erros claros em caso de e-mail já existente, senha fraca, etc.
  - Possível confirmação de cadastro (simulada) para reforçar padrões mentais de “conta verificada”.

**Fluxo de venda (pelo vendedor):**

- Cadastro/login;
- Criação de anúncio;
- Decisão de abrir leilão ou não;
- Acompanhamento do leilão (listagem de lances, status do leilão);
- Encerramento (manual ou automático);
- Visualização de resultado (vencedor/valor).

**Fluxo de compra (pelo comprador):**

- Cadastro/login;
- Navegação pelo catálogo (busca por categoria, preço, etc.);
- Entrada na página de um leilão específico;
- Dar lances (com feedback imediato de aceitação/rejeição);
- Acompanha resultado (ganhou/perdeu).

Ao documentar e testar esses fluxos ponta a ponta, o grupo constrói o tal “corpus dourado” de cenários essenciais de produto, que devem ser protegidos contra regressões.

### 5.3 Confiança e transparência

A confiança do usuário depende fortemente de três fatores:

**Transparência de regras:**

- Incremento mínimo de lances é explicitado e retornado pela API junto com os dados do leilão.
- Critérios de desempate são claros (por exemplo, em caso de lances com mesmo valor, vence o mais antigo).
- Janelas de tempo são consistentemente aplicadas.

**Histórico e visibilidade:**

- Histórico de lances, com timestamps, valor e um identificador de usuário (que pode ser parcialmente anonimizado).
- Possibilidade de o usuário ver os lances que fez e seus resultados passados (ganhou/perdeu).

**Mensagens de erro significativas:**

- Não basta retornar HTTP 400; a mensagem precisa dizer por que o lance foi rejeitado: “lance abaixo do incremento mínimo”, “leilão não está aberto”, etc.
- Mensagens consistentes em toda a API ajudam tanto desenvolvedores de UI quanto usuários finais.

A literatura sobre fraudes em leilões on-line destaca que a falta de transparência em lances e resultados é um dos fatores que mais corroem a confiança, incentivando o abandono da plataforma e reclamações formais (*Auction Fraud: What It Is and How to Prevent It*).

### 5.4 Experiência de uso via Web

Embora o projeto não inclua frontend, é importante desenhar a API pensando em UIs web que serão construídas sobre ela:

**Rotas “amigas de tela”:**

- Um endpoint para detalhar um leilão deve retornar:
  - dados do anúncio;
  - estado atual do leilão (incluindo tempo restante);
  - valor do lance atual;
  - resumo de histórico (por exemplo, últimos N lances).
- Isso evita que uma página precise disparar muitas chamadas sequenciais para montar a tela.

**Latência percebida:**

- A cada lance, o cliente deve obter resposta rápida, com confirmação clara.
- Em contextos reais, canais em tempo real (WebSockets) são usados para atualizar todos os participantes simultaneamente; aqui, isso pode ser parcialmente simulado com polling periódico ou recarga manual, mas a API deve ser capaz de servir múltiplas leituras em sequência com consistência.

**Comunicação de regras:**

- Além de estar em `docs/`, as regras essenciais podem ser retornadas junto com os dados de leilão (por exemplo, campo `explicacao_regra_incremento`), o que facilita exibi-las diretamente na UI.

Nesse sentido, a API não é apenas uma camada técnica; ela é parte do design de UX, pois define o que é fácil (ou não) construir nas interfaces de usuário.

---

## 6. Críticas, Desafios e Recomendações

### 6.1 Desafios técnicos

Alguns desafios técnicos relevantes para o projeto:

**Concorrência em lances:**

- Mesmo em um ambiente acadêmico com poucos usuários simultâneos, é fundamental lidar corretamente com race conditions em lances, como descrito na Seção 3.4. Plataformas reais relatam explicitamente que ordenar e processar lances na sequência correta é um dos requisitos mais críticos para a integridade do sistema (*Real-Time Bidding and Auctions*).

**Domínio livre de dependências:**

- É tentador, por conveniência, importar objetos de ORM ou detalhes de HTTP dentro de entidades de domínio. Essa prática compromete a testabilidade e a clareza da arquitetura. Garantir que o domínio dependa apenas de tipos primitivos ou objetos de valor próprios é um desafio de disciplina de equipe, não técnico.

**Logging e observabilidade:**

- Decidir “quanto logar” e “como logar” é delicado: logs demais geram ruído; logs de menos atrapalham a depuração. Para o projeto:
  - Logar sempre que um leilão muda de estado.
  - Logar tentativas de lance e o motivo de rejeição (quando houver).
  - Logar operações administrativas sensíveis (encerramento manual, cancelamento de venda).

**Manter a API coerente:**

- Ao evoluir o sistema, é fácil quebrar contratos de API (nomes de campos, formatos) sem perceber, principalmente em ambientes sem front acoplado. É recomendável usar a especificação OpenAPI como “fonte da verdade” e manter uma verificação de compatibilidade mínima.

### 6.2 Desafios funcionais

**Modelagem precisa de estados:**

- Erros comuns incluem:
  - estados implícitos (por exemplo, “código 3 quer dizer ‘bloqueado automaticamente’” sem documentação);
  - transições não tratadas (por exemplo, o que acontece se o job de encerramento falhar temporariamente?).
- A robustez do sistema depende de estados bem nomeados e documentados, acompanhados de testes de transição.

**Políticas de encerramento:**

- É preciso decidir:
  - se o vendedor pode encerrar um leilão antecipadamente;
  - se isso pode ocorrer após existirem lances;
  - quais são as consequências para compradores que já tinham dado lance.
- Para um MVP acadêmico, uma política simples poderia ser: o leilão só é encerrado automaticamente na data/hora de fim; o encerramento manual é permitido apenas enquanto não houver lances. Mas essas escolhas precisam ser explicitadas.

**Equilíbrio entre realismo e simplicidade:**

- Cada nova regra (por exemplo, extensão automática de tempo se houver lances nos últimos X segundos – “anti-sniping”) traz valor, mas aumenta a complexidade. Em projetos reais, mecanismos anti-“sniping” e de extensão de tempo são comuns (*Building a Real-Time Auction Platform*); aqui, é preciso avaliar se isso cabe no escopo acadêmico ou se deve ser tratado como incremento opcional.

### 6.3 Críticas ao escopo e trade-offs

Alguns trade-offs a considerar:

**Complexidade vs. aprendizado:**

- Introduzir filas, workers assíncronos, ou microserviços pode ser didático, mas corre o risco de diluir o tempo sobre o núcleo de leilão e marketplace.
- Por outro lado, restringir tudo a um único script Flask “monolítico” reduz a exposição a boas práticas arquiteturais.
- A proposta de clean architecture modularizado atinge um bom ponto intermediário: mantém um único deploy (monolito) mas com separação interna.

**Simulação de pagamento vs. realismo de checkout:**

- Simular pagamentos simplifica o projeto e evita lidar com regulatórios, segurança de cartões, etc.
- Isso sacrifica a oportunidade de exercitar integrações externas – algo que poderia ser abordado em outro trabalho ou disciplina.

**Antifraude:**

- Sistemas reais lidam com uma gama de fraudes: não entrega, não pagamento, chargebacks, uso de dados roubados de cartão, entre outros (*How to safely use online auction sites*).
- No projeto acadêmico, é suficiente concentrar-se em prevenção de abusos dentro da plataforma (por exemplo, impedir lances repetitivos suspeitos ou uso de múltiplas contas pelo mesmo usuário), deixando modelos de detecção automatizada (como machine learning) fora de escopo.

### 6.4 Recomendações de design

Com base no exposto, algumas recomendações práticas:

**Centralizar regras críticas no domínio:**

- Toda lógica de aceitação/rejeição de lance deve estar em `Leilao` ou em serviços de domínio auxiliares, não em controllers.
- Transições de estado (inclusive de `Venda`) também devem ser métodos de domínio.

**Especificar features com “mini-specs” antes de codar:**

- Para cada caso de uso relevante (por ex., “Dar lance”, “Encerrar leilão”), escrever uma pequena especificação com:
  - objetivo;
  - pré-condições;
  - fluxos felizes e de erro;
  - impacto em estados.
- Isso reduz retrabalho e facilita o uso de IA como auxílio à codificação.

**Definir padrões de erro desde o início:**

- Códigos HTTP consistentes (400 para erros de validação, 401 para não autenticado, 403 para não autorizado, etc.).
- Formato fixo de payload de erro (por exemplo, `{ "codigo": "ERRO_INCREMENTO_MINIMO", "mensagem": "..." }`).

**Planejar desde cedo como evoluir segurança:**

- Ainda que MFA, KYC/KYB (verificação de identidade de usuários) e antifraude sofisticado não sejam implementados, o modelo de dados e domínio podem reservar espaço para estados e campos que permitam essa expansão futura, sem reescrever o núcleo do sistema.

---

## 7. Roadmap, Backlog e Métricas Acadêmicas

### 7.1 Roadmap de implementação

Um roadmap iterativo razoável é:

| Fase | Foco principal | Entregáveis |
|---|---|---|
| 1 | Domínio e testes unitários | Entidades, estados de leilão, regras de lance + testes |
| 2 | Repositórios e banco de dados | Interfaces de repositório, modelos ORM, migrations |
| 3 | Casos de uso | `CriarAnuncio`, `IniciarLeilao`, `DarLance`, `EncerrarLeilao` com testes de orquestração |
| 4 | API REST | Rotas Flask, autenticação JWT, documentação via OpenAPI |
| 5 | Jobs de encerramento | Job com APScheduler para encerrar leilões automaticamente |
| 6 | Testes de integração e hardening | Testes de API, testes de concorrência em lances, ajustes de logging e erros |

Cada fase deve incluir uma pequena revisão técnica e, quando possível, uma demonstração para a turma/professor, reforçando o ciclo de feedback rápido.

### 7.2 Backlog: MVP vs incrementos

Podemos dividir o backlog em dois níveis:

**MVP (mínimo necessário para a disciplina)**

- Cadastro/login de usuários, com JWT.
- CRUD de anúncios.
- Criação/agendamento de leilões.
- Registro de lances com validação correta.
- Encerramento de leilões (manual e/ou automático via job).
- Registro de venda simulada básica.
- Documentação de API e testes unitários/integrados básicos.

**Incrementos possíveis**

- Avaliação mútua de compradores e vendedores.
- Filtros de catálogo mais avançados (por exemplo, busca textual).
- Histórico enriquecido de lances (comentários, estatísticas).
- Simulação de notificações (por exemplo, registro de “mensagens” a serem mostradas em uma UI).
- Mecanismos simples de mitigação de fraude (por exemplo, limitação de tentativas de lance por minuto, detecção de padrões suspeitos básicos).

Essa organização permite que o grupo garanta a entrega de um núcleo funcional robusto, adicionando incrementos apenas se houver tempo e capacidade.

### 7.3 Métricas de sucesso

Para avaliar o sucesso do projeto no contexto acadêmico, algumas métricas (quantitativas e qualitativas) podem ser consideradas:

**Cobertura de testes:**

- Percentual geral de linhas cobertas.
- Cobertura específica de módulos críticos (`leilao.py`, `lance.py`, casos de uso de lances e encerramento).

**Aderência à arquitetura planejada:**

- Verificação se o código respeita a separação `domain` / `use_cases` / `adapters` / `infra`.
- Ausência de dependências indevidas (por exemplo, `domain` importando Flask ou SQLAlchemy).

**Clareza da API:**

- Facilidade em executar os fluxos do “corpus dourado” via Swagger ou Postman.
- Consistência de códigos e formatos de resposta.

**Estabilidade em cenários de concorrência simulada:**

- Testes de múltiplos lances concorrentes executando sem produzir estados inconsistentes.

**Feedback qualitativo:**

- Impressões da turma e do professor sobre clareza de documentação, previsibilidade de comportamento e facilidade de manutenção.

Essas métricas ajudam não só na nota final, mas também na reflexão do grupo sobre o próprio processo de desenvolvimento.

---

## Conclusão

O mini marketplace com módulo de leilão proposto oferece um terreno ideal para exercitar engenharia de software de verdade em um contexto controlado. Ele combina:

- um domínio interessante (marketplace + leilões), com estados e invariantes claros;
- desafios técnicos relevantes (concorrência em lances, modelagem de estados, logging e testes);
- e espaço para decisões de produto (regras de negócio, papéis de usuário, escopo de MVP vs incrementos).

A mensagem central deste relatório é que a qualidade do projeto não será medida pela quantidade de features, mas pela qualidade da modelagem de domínio, da arquitetura em camadas e dos testes automatizados. Construir um sistema em que:

- os estados de leilão são bem definidos;
- os lances são processados de forma atômica e auditável;
- as regras são explícitas e cobertas por testes;

ensina mais – e prepara melhor para a prática profissional – do que tentar replicar a complexidade de grandes plataformas.

Com um roadmap iterativo, um backlog bem priorizado e métricas de sucesso alinhadas à disciplina, o grupo pode entregar um backend de leilão e marketplace que seja, ao mesmo tempo, didático, robusto e extensível.
