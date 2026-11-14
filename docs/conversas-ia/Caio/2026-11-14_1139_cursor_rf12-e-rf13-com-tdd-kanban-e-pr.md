---
autor: "Caio"
ferramenta: cursor
data_inicio: 2026-11-14T11:39:52-03:00
conversa_id: manual-20261114113952
titulo: "RF12 e RF13 com TDD, kanban e PR"
fonte: transcricao
---

## Mensagem 1 — Usuário

o app está pronto?

## Mensagem 2 — Assistente

Vou conferir o estado do projeto — o que já está implementado e o que ainda falta — para responder se o app está pronto.

> **Ferramenta:** `Read` — path: README.md

> **Ferramenta:** `Glob` — arquivos de documentação e de código do repositório

## Mensagem 3 — Assistente

A documentação de próximos passos está desatualizada em relação ao código. Vou cruzar os requisitos com o que as rotas, casos de uso e jobs realmente fazem.

> **Ferramenta:** `Read` — infra/api/app.py, infra/api/routers/anuncios.py, infra/api/routers/leiloes.py, infra/api/routers/auth.py, infra/jobs/leiloes.py

## Mensagem 4 — Assistente

O fluxo principal da API está pronto. O que o README descreve como produto — cadastro, login, anúncio, lance, histórico e abertura/encerramento automático — está implementado e coberto por testes. Não há interface gráfica: o README define o sistema como API REST, com contrato em `/docs`.

| Requisito | Estado |
|---|---|
| RF01–RF03 cadastro, login JWT e `/auth/me` | Pronto |
| RF04–RF06 criar e listar anúncios, com leilão | Pronto (`POST` e `GET /anuncios`) |
| RF07 abrir leilões no horário | Pronto (job a cada 1 min) |
| RF08–RF09 dar lance e ver histórico | Pronto |
| RF10 encerrar e apurar vencedor, ou cancelar sem lances | Pronto |
| RF11 auditoria de lance e encerramento | Pronto |
| RF12 editar e inativar o próprio anúncio | Só no domínio (`Anuncio.editar` / `inativar`); não há rota |
| RF13 venda e pagamento simulado (`pago`) | Só no domínio (`Leilao.marcar_como_pago`); não há caso de uso nem rota |

Dois furos no que já existe: `POST /anuncios` não exige login e aceita o `vendedor_id` no corpo da requisição; a listagem de lances também é pública.

`docs/proximos-passos.md` está desatualizado: ainda marca jobs, `EncerrarLeilao` e histórico como pendentes, e isso já está no código.

## Mensagem 5 — Usuário

Implemente ambos que faltam, com TDD

## Mensagem 6 — Assistente

Os dois requisitos que faltam são editar/inativar anúncio e registrar a venda com pagamento simulado. Vou olhar o domínio e o padrão dos casos de uso existentes para planejar a implementação com TDD.

> **Ferramenta:** `Read` — domain/anuncio.py, domain/leilao.py, docs/must-read.md (seção 4.4), use_cases/interfaces.py, use_cases/encerrar_leilao.py

## Mensagem 7 — Usuário

Implemente ambos que faltam, com TDD e documentando no gh projects via CLI

## Mensagem 8 — Assistente

O pedido agora inclui o quadro no GitHub Projects. Vou ver como o repositório organiza issues e o padrão dos testes, para o plano cobrir TDD e o registro no board.

> **Ferramenta:** `Read` — domain/exceptions.py, tests/integration/test_api_anuncios.py, infra/db/models/leilao.py, tests/unit/test_leilao.py

## Mensagem 9 — Assistente

Plano apresentado para confirmação. Branch sugerida, a partir de `dev`: `feature/rf12-rf13-anuncio-e-venda`.

Quadro no GitHub, antes do código, no repositório `C14-Inatel-2026-2/sistema-leilao`:

- Listar o project da org (`gh project list --owner C14-Inatel-2026-2`). Se não houver um do sistema de leilão, criar um.
- Abrir duas issues, com critérios de aceite, e adicioná-las ao project (`gh issue create`, `gh project item-add`).
- Mover cada item para In Progress ao começar o ciclo e para Done quando os testes da fatia ficarem verdes (`gh project field-list` + `gh project item-edit`).

Issues:

- RF12 — vendedor autenticado edita e inativa só o próprio anúncio.
- RF13 — ao encerrar com vencedor o sistema registra a venda `PENDENTE`; o vencedor simula o pagamento (`APROVADO`) ou cancela (`CANCELADO`).

RF12 — editar e inativar. Regras já em `domain/anuncio.py`: `editar` só com anúncio `ATIVO` e sem lances; `inativar` recusa `VENDIDO`. O caso de uso só acrescenta dono e persistência.

- Novas exceções em `domain/exceptions.py`: `AnuncioNaoEncontradoError` (404) e `AcessoNegadoError` (403).
- `EditarAnuncio` e `InativarAnuncio` em `use_cases/`, dependendo de `AnuncioRepository` e `LeilaoRepository`. O vendedor vem do JWT, não do corpo. `leilao_com_lances` sai de `bool(leilao.lances)`.
- Rotas em `infra/api/routers/anuncios.py`, com `get_current_user`: `PATCH /anuncios/{id}` (título, descrição, preço de referência) e `POST /anuncios/{id}/inativar`.

TDD, um comportamento por vez: teste unitário com mock falhando, implementação mínima, teste de API em `tests/integration/test_api_anuncios.py` (dono, outro usuário 403, anúncio inexistente 404, edição com lances 400, inativar vendido 400). Commit quando a fatia estiver verde.

RF13 — venda e pagamento simulado. Modelo da seção 4.4 de `docs/must-read.md`, só para leilão encerrado com vencedor. Venda direta fica de fora: `POST /anuncios` hoje sempre cria leilão.

- Entidade `Venda` em `domain/venda.py`: `PENDENTE`, `APROVADO`, `CANCELADO`; método simulado (`PIX`, `CARTAO`, `BOLETO`); `aprovar` e `cancelar` só a partir de `PENDENTE`.
- `RegistrarVenda`: leilão `ENCERRADO` com `vencedor_id`; idempotente por leilão. O job em `infra/jobs/leiloes.py` chama esse caso de uso depois de `EncerrarLeilao` quando houver vencedor. `EncerrarLeilao` não muda.
- `SimularPagamento`: só o vencedor; grava o método, aprova a venda, `leilao.marcar_como_pago()` e `anuncio.marcar_vendido()` na mesma transação.
- `CancelarVenda`: só o vencedor, enquanto `PENDENTE`. Leilão permanece `ENCERRADO` e anúncio `ATIVO`.
- Persistência: `VendaModel`, registro em `infra/db/models/__init__.py`, migration Alembic com `down_revision = b3d5f8e12a40`, `VendaRepository` no protocolo de `use_cases/interfaces.py`.
- Rotas: `GET /leiloes/{id}/venda` (vendedor ou vencedor), `POST /vendas/{id}/pagamento`, `POST /vendas/{id}/cancelar`.

TDD na mesma ordem: testes de domínio da `Venda`, testes unitários dos três casos de uso, teste do job em `tests/integration/test_job_leiloes.py` (encerrar com lance cria venda `PENDENTE`; sem lance não cria), testes de API, depois o código que faz cada um passar. Commit separado desta fatia.

Fora deste trabalho: não alterar o contrato de `POST /anuncios` nem o de `EncerrarLeilao`. Não atualizar `docs/proximos-passos.md`. Não fazer push.

## Mensagem 10 — Usuário

RF12 e RF13 com TDD e GitHub Projects

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

## Mensagem 11 — Assistente

Vou começar pelo quadro no GitHub e pela branch, e em seguida implementar RF12 e RF13 em ciclos de TDD.

> **Ferramenta:** `Shell` — git status, gh auth status, gh project list

## Mensagem 12 — Assistente

O login do GitHub funciona fora do sandbox, mas o token não tem permissão de Projects. Vou pedir esse escopo e, em paralelo, ver como a API traduz erros de domínio.

> **Ferramenta:** `Shell` — gh auth refresh -h github.com -s project

## Mensagem 13 — Assistente

A permissão de Projects foi concedida. Vou localizar o quadro e abrir as duas issues.

O quadro usado foi o project 6 da organização, `@caiosemblano's SL kanban`. Foram criadas e colocadas em In progress:

- https://github.com/C14-Inatel-2026-2/sistema-leilao/issues/86 — RF12: editar e inativar o próprio anúncio
- https://github.com/C14-Inatel-2026-2/sistema-leilao/issues/87 — RF13: registrar a venda e simular o pagamento

## Mensagem 14 — Assistente

As issues #86 e #87 estão em progresso no kanban. O próximo passo é o teste que ainda não tem implementação, para o RF12.

Branch criada: `feature/rf12-rf13-anuncio-e-venda`.

O teste `tests/unit/test_editar_inativar_anuncio.py` falhou na coleta, como esperado: `ImportError: cannot import name 'AcessoNegadoError'`.

## Mensagem 15 — Assistente

O teste falhou na importação, como esperado. Vou implementar as exceções e os dois casos de uso até ele passar.

Foram acrescentados `AnuncioNaoEncontradoError` e `AcessoNegadoError`, os casos de uso `EditarAnuncio` e `InativarAnuncio`, e os oito testes unitários passaram.

Em seguida os testes de API foram escritos e falharam. As rotas `PATCH /anuncios/{id}` e `POST /anuncios/{id}/inativar` foram implementadas, com o handler HTTP traduzindo 404 e 403. Os testes de anúncio passaram (23). Commit:

`feat: permite ao vendedor editar e inativar o próprio anúncio.`

## Mensagem 16 — Assistente

RF12 já está no histórico. Agora o ciclo da venda começa pelo teste de domínio, antes de existir a entidade.

`tests/unit/test_venda.py` falhou na coleta (`VendaInvalidaError` inexistente) e, depois da entidade `Venda`, passou (7 testes).

`tests/unit/test_registrar_venda.py` falhou na coleta (`use_cases.cancelar_venda` inexistente). Depois de `RegistrarVenda`, `SimularPagamento` e `CancelarVenda`, domínio e casos de uso passaram (16 testes).

## Mensagem 17 — Assistente

Os testes de persistência falham porque ainda não há repositório de venda. Vou criar o modelo, a migration, o job e as rotas.

Foram criados `VendaModel`, a migration `c4e8a1b27d50_create_vendas_table` (revisa `b3d5f8e12a40`), `SQLAlchemyVendaRepository`, o registro da venda no job depois do encerramento com vencedor, e as rotas `GET /leiloes/{id}/venda`, `POST /vendas/{id}/pagamento` e `POST /vendas/{id}/cancelar`.

A suíte completa ficou em 203 testes passando e 1 ignorado. Commit:

`feat: registra a venda ao encerrar o leilão e simula o pagamento.`

As issues #86 e #87 foram movidas para Done e fechadas.

## Mensagem 18 — Assistente

RF12 e RF13 estão implementados na branch `feature/rf12-rf13-anuncio-e-venda`, com os testes verdes (203 passaram). As duas issues estão em Done no kanban [@caiosemblano's SL kanban](https://github.com/orgs/C14-Inatel-2026-2/projects/6).

**RF12.** O vendedor autenticado edita e inativa só o próprio anúncio.

- `PATCH /anuncios/{id}` altera título, descrição e preço de referência.
- `POST /anuncios/{id}/inativar` marca o anúncio como `INATIVO`.
- Outro usuário recebe 403, anúncio inexistente recebe 404, e a edição é recusada se o leilão já tem lances ou se o anúncio está vendido.

**RF13.** Depois do encerramento com vencedor, o job cria uma venda `PENDENTE`. Sem lances, não há venda.

- `GET /leiloes/{id}/venda` fica visível para o vendedor ou o vencedor.
- `POST /vendas/{id}/pagamento` só o vencedor: método `PIX`, `CARTAO` ou `BOLETO`, venda `APROVADO`, leilão `PAGO` e anúncio `VENDIDO`.
- `POST /vendas/{id}/cancelar` só o vencedor, enquanto `PENDENTE`. O leilão continua `ENCERRADO` e o anúncio `ATIVO`.

Issues: #86 e #87. A branch ainda não foi enviada ao remoto.

## Mensagem 19 — Usuário

Progresso do progeto está atualizado no kanban? Faça um scan

## Mensagem 20 — Assistente

Vou comparar o kanban com o que já está no repositório: issues, status dos cards e o que o código realmente entrega.

> **Ferramenta:** `Shell` — gh project item-list 6 --owner C14-Inatel-2026-2

## Mensagem 21 — Assistente

O quadro tem cards fora de Done. Vou cruzar esses itens com o estado real das issues e com o que já entrou na `dev`.

## Mensagem 22 — Assistente

O kanban não está alinhado com o código. No quadro [@caiosemblano's SL kanban](https://github.com/orgs/C14-Inatel-2026-2/projects/6) há 68 cards: 59 em Done, 4 em In progress, 3 em In review e 2 em Ready. Nove cards antigos continuam abertos apesar de o trabalho já estar na `dev`, e os dois de hoje estão em Done sem terem entrado na `dev`.

Estes nove ainda aparecem como pendentes, mas o pull request que os entrega já foi mergeado:

| Card no quadro | Status no kanban | O que já está na `dev` |
|---|---|---|
| #32 US02, e as tarefas #34, #35 e #36 | In progress | #57, #58 e #59, todos Done |
| #27 US03 lance | Ready | #49 e #76, Done |
| #29 US04 abertura e encerramento | Ready | #77, Done |
| #28 US05, e as tarefas #41 e #42 | In review | #72 e #73, Done |

No sentido contrário, #86 (RF12) e #87 (RF13) estão em Done e fechadas, mas os dois commits existem só na branch local `feature/rf12-rf13-anuncio-e-venda`. Eles não foram enviados e não há pull request.

## Mensagem 23 — Usuário

Atuealize-os

## Mensagem 24 — Assistente

O quadro está atrás do que já entrou na `dev` e à frente do RF12/RF13, que ainda não saíram da máquina. Vou alinhar os cards a esse estado.

> **Ferramenta:** `Shell` — gh project item-edit e gh issue close/reopen

## Mensagem 25 — Assistente

O kanban [@caiosemblano's SL kanban](https://github.com/orgs/C14-Inatel-2026-2/projects/6) agora acompanha o repositório.

Nove cards que já estavam na `dev` foram para Done e as issues fecharam:

- #27 US03, pelo #49 e pelo #76
- #29 US04, pelo #77
- #32 US02, com #34, #35 e #36, pelos #57, #58 e #59
- #28 US05, com #41 e #42, pelos #72 e #73

#86 e #87 voltaram para In progress. O código continua só na branch local `feature/rf12-rf13-anuncio-e-venda`, sem pull request.

## Mensagem 26 — Usuário

arquive a conversa /exportar-conversas-ia e abra o PR
