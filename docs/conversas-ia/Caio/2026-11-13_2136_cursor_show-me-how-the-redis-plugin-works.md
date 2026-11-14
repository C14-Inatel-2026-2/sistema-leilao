---
autor: "Caio"
ferramenta: cursor
data_inicio: 2026-11-13T21:36:00-03:00
conversa_id: 3490e669-b277-4f10-99ef-f7ba577baa2f
titulo: "show-me-how-the-redis-plugin-works"
fonte: jsonl
---

> **Nota:** exportação a partir do arquivo local `.jsonl`. Trechos marcados como redigidos não estão disponíveis no disco. Para transcrição literal da conversa atual, use o modo `transcrever`.

## Mensagem 1 — Usuário

Show me how the Redis plugin works

## Mensagem 1 — Assistente

The Redis plugin adds Redis development guidance that I apply automatically while you work, plus a skill you can call directly.

## Skill

**redis-development** covers performance and best practices for:

- Data structures and when to use each one
- Redis Query Engine (indexes, field types, query syntax)
- Vector search with RedisVL (HNSW vs FLAT, hybrid search, RAG)
- Semantic caching with LangCache
- Connection handling, memory limits, TTLs, and observability

Invoke it with `/redis-development`, or I will use it on my own when the task involves Redis.

## Rules (applied automatically)

These kick in whenever Redis work shows up in the conversation. You do not need to turn them on.

| Area | What it enforces |
|---|---|
| **Connections** | Pooling, pipelining, timeouts, client-side caching, avoiding slow commands in production |
| **Data** | Right structure for the job, consistent key names, `INCR` for counters, transactions, hash field expiry |
| **JSON** | JSON vs Hash vs String, partial updates via JSON paths |
| **Memory** | TTLs on cache keys, memory limits and eviction policies |
| **Query Engine** | Index only queried fields, correct field types, DIALECT 2, efficient queries, zero-downtime index updates |
| **Vectors** | Index setup, HNSW vs FLAT, hybrid search, RAG pattern |
| **Semantic cache** | LangCache usage and cache configuration |
| **Streams** | Streams vs Pub/Sub |
| **Cluster** | Hash tags for multi-key ops, read replicas for read-heavy loads |
| **Security** | Authentication, ACLs, network access |
| **Observability** | Key metrics and debug commands |

There are no extra slash commands or hooks in this plugin. The skill is the entry point; the rules shape how Redis code is written once the work starts.
