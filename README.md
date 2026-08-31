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

A aplicação é uma **API REST** (sem interface gráfica). Endpoints documentados via **Swagger/OpenAPI** — acessível em `/apidocs` quando a aplicação estiver rodando.

Ferramentas sugeridas para teste manual: Postman, Insomnia ou `curl`.

---

## Documentação técnica

- [Arquitetura](docs/arquitetura.md) — camadas, domínio, eventos, concorrência
- [Estrutura e stack](docs/estrutura-e-stack.md) — árvore de diretórios e tecnologias

Documentos de entrega acadêmica (Projeto C14): [`Projeto-C14/docs/`](Projeto-C14/docs/EntregaInicial/).
