# Hierarquia de exceções de domínio

**Status:** dívida técnica conhecida. Documentar agora; unificar depois, em um PR dedicado, sem misturar com features.

Este documento descreve o estado atual das exceções em `domain/`, o alvo alinhado a [`must-read.md`](must-read.md) (seções 3.1, 6.1 e 6.4) e o checklist da correção.

---

## Por que unificar

A infraestrutura (Flask) precisa distinguir **violação de regra de negócio** de **bug técnico**. Com uma base comum (`DomainError`), um handler HTTP pode fazer:

```python
except DomainError as exc:
    return {"codigo": ..., "mensagem": str(exc)}, 400
```

Hoje isso não funciona de ponta a ponta: `UsuarioInvalidoError` herda de `DomainError`, mas `LanceInvalidoError`, `LeilaoInvalidoError`, `EstadoLeilaoInvalidoError` e `AnuncioError` herdam de `ValueError`. Um `except DomainError` não pega lance/leilão/anúncio.

O relatório de produto também pede payload de erro estável (`codigo` + `mensagem`). Sem hierarquia comum, cada controller tende a mapear exceções ad hoc.

---

## Estado atual (as-is)

Duas convenções convivem.

### 1. Base compartilhada em `domain/exceptions.py`

| Classe | Base | Usada por |
|---|---|---|
| `DomainError` | `Exception` | (base) |
| `UsuarioInvalidoError` | `DomainError` | `domain/usuario.py` |
| `AnuncioInvalidoError` | `DomainError` | **ninguém** — definida, não levantada |
| `CategoriaInvalidaError` | `DomainError` | **ninguém** — `domain/categoria.py` ainda vazio |

### 2. Exceções locais, ao lado da entidade, herdando `ValueError`

| Classe | Arquivo | Base | Papel |
|---|---|---|---|
| `AnuncioError` | `domain/anuncio.py` | `ValueError` | Validação e transições de anúncio |
| `LanceInvalidoError` | `domain/lance.py` | `ValueError` | Lance inválido por si só **e** regras de lance em `Leilao` (janela, incremento, vendedor) |
| `LeilaoInvalidoError` | `domain/leilao.py` | `ValueError` | Dados de criação inválidos (preço, incremento, datas) |
| `EstadoLeilaoInvalidoError` | `domain/leilao.py` | `ValueError` | Transição de estado proibida (abrir/encerrar/cancelar/pagar no status errado; lance com leilão não aberto) |

`Leilao` importa `LanceInvalidoError` de `domain/lance.py` e a usa nas regras de lance. Isso é aceitável (a exceção acompanha o conceito), mas a **base** deveria ser `DomainError`, não `ValueError`.

### Problemas concretos

1. **Bases diferentes** — `except DomainError` não cobre o núcleo do leilão.
2. **Dois nomes para anúncio** — `AnuncioInvalidoError` (morta) vs `AnuncioError` (viva).
3. **Sem códigos estáveis** — só mensagens em português; a API ainda não tem `codigo` (`ERRO_INCREMENTO_MINIMO`, etc.).
4. **`ValueError` é genérico** — na infra, mistura regra de negócio com erro de programação (`int("abc")` também é `ValueError`).

---

## Alvo (to-be)

Uma árvore só. Todas as violações de negócio herdam de `DomainError`.

```text
DomainError
├── UsuarioInvalidoError
├── CategoriaInvalidaError
├── AnuncioInvalidoError          # unificar com AnuncioError (renomear)
├── LeilaoInvalidoError           # dados de criação
├── EstadoLeilaoInvalidoError     # transição de estado
└── LanceInvalidoError            # valor, comprador, janela, incremento, vendedor
```

### Onde declarar

Manter **duas camadas**, sem espalhar bases novas:

| O quê | Onde |
|---|---|
| `DomainError` e exceções usadas por mais de um módulo | `domain/exceptions.py` |
| Exceção que só a entidade (e quem a orquestra) levanta | pode continuar no arquivo da entidade, **desde que herde `DomainError`** |

`LanceInvalidoError` pode permanecer em `domain/lance.py` (já é importada por `Leilao`). O que precisa mudar é a classe-base.

`AnuncioError` deve convergir para o nome já previsto em `exceptions.py`: `AnuncioInvalidoError`. Um alias temporário (`AnuncioError = AnuncioInvalidoError`) é opcional se houver testes/imports no meio da migração.

### Mapeamento HTTP (quando a API existir)

Definido em [`must-read.md`](must-read.md) §6.4; a hierarquia só torna o mapeamento trivial.

| Situação | HTTP | Exceção típica |
|---|---|---|
| Dados ou regra de negócio violada | 400 | qualquer `DomainError` |
| Não autenticado | 401 | (infra/JWT, não domínio) |
| Autenticado sem permissão | 403 | (caso de uso / papel; pode virar `DomainError` específica depois) |
| Recurso inexistente | 404 | (repositório / caso de uso) |

Payload alvo:

```json
{ "codigo": "ERRO_INCREMENTO_MINIMO", "mensagem": "..." }
```

Códigos estáveis (`codigo`) **não** precisam entrar neste PR de hierarquia. Primeiro unificar a base; códigos podem ser um incremento (atributo de classe ou tabela na camada HTTP).

---

## O que não misturar nesta correção

- Não alterar mensagens de erro nem as regras que as disparam.
- Não mover regras de lance de `Leilao` para `Lance`.
- Não criar exceções de infra (HTTP, SQLAlchemy, JWT) em `domain/`.
- Não implementar o handler Flask neste PR — só deixar o `except DomainError` possível.

---

## Checklist do PR futuro

Sugestão de branch: `chore/domain-exception-hierarchy`.

1. Fazer `LanceInvalidoError`, `LeilaoInvalidoError`, `EstadoLeilaoInvalidoError` e a exceção de anúncio herdarem `DomainError`.
2. Unificar `AnuncioError` → `AnuncioInvalidoError`; atualizar `domain/anuncio.py`.
3. Remover a classe duplicada/morta em `exceptions.py` se o nome canônico passar a viver na entidade — **ou** o contrário: mover todas para `exceptions.py`. Escolher um lado e aplicar em todos os arquivos.
4. Garantir que `CategoriaInvalidaError` seja a exceção usada quando `categoria.py` for preenchido.
5. Teste unitário mínimo: `isinstance(LanceInvalidoError(), DomainError)` (e o equivalente para leilão/anúncio).
6. Quando existir controller de lance: um único `except DomainError` cobre incremento, janela e vendedor.

---

## Referências

- [`must-read.md`](must-read.md) §3.1 (domínio sem frameworks), §6.1 (domínio livre de dependências), §6.4 (padrões de erro)
- [`arquitetura.md`](arquitetura.md) — domínio isolado e testável
- Código: `domain/exceptions.py`, `domain/usuario.py`, `domain/anuncio.py`, `domain/leilao.py`, `domain/lance.py`
