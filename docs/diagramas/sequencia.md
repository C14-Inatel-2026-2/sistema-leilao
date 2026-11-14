# Sequência

Em que ordem as coisas acontecem. Os dois fluxos que uma classe não mostra: o lance com lock e o job que abre, encerra e registra a venda. O pagamento entra no fim porque é o comprador, não o job, quem o dispara.

`LeilaoEncerrado` não cria a venda. O handler desse evento só grava auditoria. A venda `PENDENTE` nasce numa passagem seguinte do mesmo job, para leilão `ENCERRADO` com vencedor e ainda sem venda.

## Dar lance

`POST /leiloes/{leilao_id}/lances`. O lock pessimista segura o leilão até o commit. A regra (aberto, janela, incremento, vendedor fora) roda dentro dessa transação, em `Leilao.receber_lance`. O evento sai só depois do commit: um rollback não vira lance auditado.

```mermaid
sequenceDiagram
    actor Comprador
    participant API as POST /leiloes/id/lances
    participant DarLance
    participant Repo as LeilaoRepository
    participant Leilao
    participant Bus as publish
    participant Auditoria as handle_lance_realizado

    Comprador->>API: valor
    API->>DarLance: executar
    DarLance->>Repo: buscar_com_lock
    Note over Repo: SELECT FOR UPDATE
    Repo-->>DarLance: leilao
    DarLance->>Leilao: receber_lance
    Note over Leilao: aberto, janela, incremento, nao e o vendedor
    Leilao-->>DarLance: lance
    DarLance->>Repo: salvar
    DarLance->>DarLance: confirmar commit
    DarLance->>Bus: LanceRealizado
    Bus->>Auditoria: salvar_lance
    DarLance-->>API: lance
    API-->>Comprador: lance aceito
```

Se o leilão não existe, `DarLance` levanta `LeilaoNaoEncontradoError` antes de chamar o domínio. Se o lance fere a regra, `receber_lance` levanta `LanceInvalidoError` ou `EstadoLeilaoInvalidoError` e nada é commitado.

## Job de leilões

O APScheduler chama `processar_leiloes` a cada minuto. Cada leilão abre ou encerra na própria transação: a falha de um não impede os outros. `IniciarLeilao` não publica evento. `EncerrarLeilao` publica `LeilaoEncerrado` depois do commit, e o handler grava a auditoria. Sem lances, o leilão vai para `CANCELADO` e o motivo do evento é `sem_lances`.

```mermaid
sequenceDiagram
    participant Job as APScheduler
    participant Iniciar as IniciarLeilao
    participant Encerrar as EncerrarLeilao
    participant Repo as LeilaoRepository
    participant Leilao
    participant Bus as publish
    participant Auditoria as handle_leilao_encerrado
    participant Registrar as RegistrarVenda
    participant Vendas as VendaRepository

    Job->>Repo: listar AGENDADO na janela
    loop cada leilao a abrir
        Job->>Iniciar: executar
        Iniciar->>Leilao: abrir
        Iniciar->>Repo: salvar e commit
    end

    Job->>Repo: listar ABERTO com data_final no passado
    loop cada leilao a encerrar
        Job->>Encerrar: executar
        Encerrar->>Repo: buscar_com_lock
        Encerrar->>Leilao: encerrar
        alt ha lance
            Note over Leilao: ENCERRADO, vencedor e valor
        else sem lance
            Note over Leilao: CANCELADO
        end
        Encerrar->>Repo: salvar
        Encerrar->>Repo: confirmar commit
        Encerrar->>Bus: LeilaoEncerrado
        Bus->>Auditoria: salvar_encerramento
    end

    Job->>Repo: listar ENCERRADO com vencedor e sem venda
    loop cada leilao a registrar
        Job->>Registrar: executar
        Registrar->>Vendas: salvar Venda PENDENTE
        Registrar->>Vendas: commit
    end
```

## Pagamento e cancelamento

`POST /vendas/{venda_id}/pagamento` e `POST /vendas/{venda_id}/cancelar`. Só o comprador gravado na venda pode as duas ações, e só enquanto ela está `PENDENTE`.

Aprovar o pagamento muda três agregados na mesma transação: venda `APROVADO`, leilão `PAGO`, anúncio `VENDIDO`. Cancelar muda só a venda. O leilão permanece `ENCERRADO`.

```mermaid
sequenceDiagram
    actor Comprador
    participant API as POST /vendas/id
    participant Pagar as SimularPagamento
    participant Cancelar as CancelarVenda
    participant Venda
    participant Leilao
    participant Anuncio

    alt simular pagamento
        Comprador->>API: metodo PIX CARTAO ou BOLETO
        API->>Pagar: executar
        Pagar->>Venda: aprovar
        Pagar->>Leilao: marcar_como_pago
        Pagar->>Anuncio: marcar_vendido
        Pagar->>Pagar: commit
        Pagar-->>Comprador: venda APROVADA
    else cancelar venda
        Comprador->>API: cancelar
        API->>Cancelar: executar
        Cancelar->>Venda: cancelar
        Cancelar->>Cancelar: commit
        Cancelar-->>Comprador: venda CANCELADA
    end
```
