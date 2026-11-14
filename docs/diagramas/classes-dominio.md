# Classes do domínio

Como as entidades se ligam. Só o que vive em `domain/`: sem FastAPI, sem SQLAlchemy e sem os casos de uso. Setas de associação apontam para o lado que guarda o identificador.

`Anuncio.leilao_atual_id` aponta para no máximo um leilão em curso. Cada `Leilao` guarda o próprio `anuncio_id`, então o mesmo anúncio pode ter leilões anteriores. `Lance` é imutável e só existe dentro da lista do leilão. `Venda` sempre aponta para um anúncio; `leilao_id` fica preenchido quando a venda nasce de um arremate. `LanceRealizado` e `LeilaoEncerrado` são eventos publicados, não registros do agregado.

```mermaid
classDiagram
    class Email {
        <<value object>>
        +normaliza e valida
    }

    class PapelUsuario {
        <<enumeration>>
        COMPRADOR
        VENDEDOR
    }

    class Usuario {
        +UUID id
        +str nome
        +Email email
        +str senha_hash
        +PapelUsuario papel
        +bool ativo
        +validar_nome()
        +validar_senha_em_texto_puro()
        +pode_criar_anuncio() bool
        +promover_a_vendedor()
        +desativar()
    }

    class Categoria {
        +UUID id
        +str nome
        +bool ativa
        +esta_ativa() bool
        +ativar()
        +inativar()
    }

    class StatusAnuncio {
        <<enumeration>>
        ATIVO
        INATIVO
        VENDIDO
    }

    class TipoAnuncio {
        <<enumeration>>
        VENDA_DIRETA
        LEILAO
    }

    class Anuncio {
        +UUID id
        +str titulo
        +str descricao
        +Decimal preco_referencia
        +TipoAnuncio tipo
        +StatusAnuncio status
        +UUID leilao_atual_id
        +pode_iniciar_leilao() bool
        +associar_leilao()
        +pode_editar() bool
        +editar()
        +inativar()
        +marcar_vendido()
    }

    class StatusLeilao {
        <<enumeration>>
        AGENDADO
        ABERTO
        ENCERRADO
        PAGO
        CANCELADO
    }

    class Leilao {
        +UUID id
        +Decimal preco_inicial
        +Decimal incremento_minimo
        +datetime data_inicio
        +datetime data_final
        +StatusLeilao status
        +UUID vencedor_id
        +Decimal valor_arremate
        +esta_na_janela() bool
        +abrir()
        +receber_lance() Lance
        +encerrar()
        +cancelar()
        +marcar_como_pago()
    }

    class Lance {
        <<immutable>>
        +UUID id
        +Decimal valor
        +datetime criado_em
        +validar_valor()
    }

    class StatusPagamento {
        <<enumeration>>
        PENDENTE
        APROVADO
        CANCELADO
    }

    class MetodoPagamento {
        <<enumeration>>
        PIX
        CARTAO
        BOLETO
    }

    class Venda {
        +UUID id
        +Decimal valor
        +StatusPagamento status
        +MetodoPagamento metodo
        +aprovar()
        +cancelar()
    }

    class LanceRealizado {
        <<event>>
        +UUID leilao_id
        +UUID lance_id
        +UUID usuario_id
        +Decimal valor
        +datetime data_hora
    }

    class LeilaoEncerrado {
        <<event>>
        +UUID leilao_id
        +UUID vencedor_id
        +Decimal valor_final
        +datetime data_encerramento
        +str motivo
    }

    Usuario *-- Email : possui
    Usuario --> PapelUsuario
    Usuario "1" <-- "*" Anuncio : vendedor
    Usuario "1" <-- "*" Lance : comprador
    Usuario "1" <-- "*" Venda : comprador
    Categoria "1" <-- "*" Anuncio : categoria
    Anuncio --> StatusAnuncio
    Anuncio --> TipoAnuncio
    Anuncio "1" --> "0..1" Leilao : leilaoAtual
    Leilao "*" --> "1" Anuncio : anuncio
    Leilao --> StatusLeilao
    Leilao "1" *-- "*" Lance : lances
    Venda --> StatusPagamento
    Venda --> MetodoPagamento
    Venda "*" --> "1" Anuncio : anuncio
    Venda "*" --> "0..1" Leilao : leilao
```
