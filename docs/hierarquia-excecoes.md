# Hierarquia de exceções de domínio

**Status:** base unificada. Todas as violações de negócio herdam de `DomainError` em `domain/exceptions.py` (PRs #10–#12). O incremento que falta é o payload HTTP `{ "codigo", "mensagem" }` quando a API existir.

Alinhado a [`must-read.md`](must-read.md) (seções 3.1, 6.1 e 6.4).

---

## Por que uma base comum

A infraestrutura (Flask) precisa distinguir **violação de regra de negócio** de **bug técnico**. Com `DomainError`, um handler HTTP pode fazer:

```python
except DomainError as exc:
    return {"codigo": ..., "mensagem": str(exc)}, 400
```

Antes da unificação, `UsuarioInvalidoError` herdava de `DomainError`, mas lance/leilão/anúncio herdavam de `ValueError`. Um `except DomainError` não cobria o núcleo do leilão.

---

## Estado atual

Todas as exceções de domínio vivem em `domain/exceptions.py` e herdam de `DomainError`. As entidades importam dali (não declaram subclasses locais de `ValueError`).

```text
DomainError
├── UsuarioInvalidoError
├── EmailJaCadastradoError
├── CategoriaInvalidaError
├── AnuncioInvalidoError
├── LeilaoInvalidoError           # dados de criação
├── EstadoLeilaoInvalidoError     # transição de estado
└── LanceInvalidoError            # valor, comprador, janela, incremento, vendedor
```

| Classe | Usada por |
|---|---|
| `UsuarioInvalidoError` | `domain/usuario.py` |
| `EmailJaCadastradoError` | `use_cases/cadastrar_usuario.py` |
| `CategoriaInvalidaError` | `domain/categoria.py` |
| `AnuncioInvalidoError` | `domain/anuncio.py` |
| `LeilaoInvalidoError` | `domain/leilao.py` (criação) |
| `EstadoLeilaoInvalidoError` | `domain/leilao.py` (abrir/encerrar/cancelar/pagar; lance com leilão não aberto) |
| `LanceInvalidoError` | `domain/lance.py` e `domain/leilao.py` (janela, incremento, vendedor) |

`AnuncioError` (local, `ValueError`) foi substituída por `AnuncioInvalidoError`.

---

## Mapeamento HTTP (quando a API existir)

Definido em [`must-read.md`](must-read.md) §6.4. A hierarquia torna o mapeamento trivial.

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

Códigos estáveis (`codigo`) ainda **não** existem — só mensagens em português. Podem entrar como incremento (atributo de classe ou tabela na camada HTTP), sem reabrir a hierarquia.

Quando existir controller de lance, um único `except DomainError` cobre incremento, janela e vendedor.

---

## O que não reabrir

- Não voltar a herdar de `ValueError` nas entidades.
- Não criar exceções de infra (HTTP, SQLAlchemy, JWT) em `domain/`.
- Não mover regras de lance de `Leilao` para `Lance`.

---

## Referências

- [`must-read.md`](must-read.md) §3.1 (domínio sem frameworks), §6.1 (domínio livre de dependências), §6.4 (padrões de erro)
- [`arquitetura.md`](arquitetura.md) — domínio isolado e testável
- [`proximos-passos.md`](proximos-passos.md) — códigos HTTP ficam depois do MVP enxuto
- Código: `domain/exceptions.py`, `domain/usuario.py`, `domain/anuncio.py`, `domain/leilao.py`, `domain/lance.py`, `domain/categoria.py`
