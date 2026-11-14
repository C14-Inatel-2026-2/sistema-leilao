# Collection Postman

Collection para apresentar o fluxo no Postman. A API não tem tela. O encerramento não tem rota: o job em `infra/jobs/leiloes.py` fecha o leilão a cada um minuto.

Arquivos desta pasta:

- `sistema-leilao.postman_collection.json`
- `local.postman_environment.json`

## Antes de importar

Copie o ambiente, suba o banco, aplique as migrations e suba a API. `DATABASE_URL` precisa existir. Sem ela o job não inicia e a pasta 02 nunca vê o leilão `ENCERRADO`.

```text
cp .env.example .env
poetry run task db-up
poetry run task migrate
poetry run task api
```

## Categoria

Não há endpoint de categoria. Insira uma e copie o `id` para a variável `categoriaId` do environment.

```text
docker compose exec postgres psql -U leilao -d leilao -c \
  "INSERT INTO categorias (id, nome, ativa, criado_em) VALUES (gen_random_uuid(), 'Eletronicos', true, now()) RETURNING id;"
```

## Importar

No Postman, importe os dois JSON e selecione o environment `local`. `baseUrl` já vem `http://127.0.0.1:8000`. `senha` é `DemoLeilao123`, só para esta demonstração.

Não preencha e-mail nem token à mão. O pré-request de cada cadastro grava um e-mail com `Date.now()`, e o teste do login grava o token na collection.

## Ordem

1. Rode as pastas **00 Setup** e **01 Fluxo do leilão**.
2. Pare. O `data_final` desse leilão fica cerca de 3 minutos à frente da criação. Depois disso, espere até mais um minuto pela próxima execução do job.
3. Rode a pasta **02 Encerramento pelo job**. Se o teste disser que o leilão ainda está `ABERTO`, rode a pasta de novo.
4. A pasta **03 Anúncio sem lances** é opcional. Rode depois da 00, com o mesmo `vendedorId` e `categoriaId`. Ela não faz parte da sequência que paga.

A última request da pasta 02 chama `postman.setNextRequest(null)`. O runner para antes de **Cancelar venda**. Essa request só serve no lugar de **Simular pagamento**, enquanto a venda está `PENDENTE`.

## O que cada pasta prova

- **00 Setup** cria vendedor e comprador e guarda os dois tokens.
- **01 Fluxo do leilão** abre o leilão na criação, aceita os lances de 550 e 600, recusa 560 e o lance do vendedor, e mostra o histórico com 600 primeiro.
- **02 Encerramento pelo job** mostra leilão `ENCERRADO`, venda `PENDENTE`, pagamento `PIX`, leilão `PAGO` e anúncio `VENDIDO`.
- **03 Anúncio sem lances** cria um leilão `AGENDADO`, edita o anúncio e inativa.

## Se falhar

E-mail duplicado não deve ocorrer: cada cadastro usa um sufixo novo. 401 num lance em geral é o token do outro ator, ou um token da execução anterior. Leilão que continua `ABERTO` na pasta 02 é espera do job, não defeito da request. Confira se a API subiu com `DATABASE_URL`.
