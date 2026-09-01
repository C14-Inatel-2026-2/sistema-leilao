# Arquivamento de Conversas com IA

Este documento descreve o processo de arquivamento das conversas com ferramentas de IA no repositório do projeto, conforme exigência acadêmica definida com o professor.

---

## Motivação

Todas as interações com IA (Cursor, Antigravity e Claude Code) devem ser registradas e versionadas no GitHub. Isso garante transparência no uso de ferramentas de apoio ao desenvolvimento e permite ao professor acompanhar o histórico de decisões tomadas com auxílio de IA.

---

## Estrutura de pastas

As conversas exportadas ficam em `docs/conversas-ia/`, organizadas por integrante:

```text
docs/conversas-ia/
├── Caio/
├── Teo/
├── Pedro-Vitor/
└── Pedro-Paiva/
```

Cada integrante arquiva suas próprias conversas na pasta correspondente.

---

## Como invocar o skill

O skill `exportar-conversas-ia` está disponível em três locais do repositório (mesmo conteúdo):

| Ferramenta | Caminho do skill | Como invocar |
|---|---|---|
| **Cursor** | `.cursor/skills/exportar-conversas-ia/` | `@exportar-conversas-ia` ou mencionar "arquivar conversa com IA" |
| **Antigravity** | `.agents/skills/exportar-conversas-ia/` | Mencionar o skill ou pedir para exportar conversa |
| **Claude Code** | `.claude/skills/exportar-conversas-ia/` | `/exportar-conversas-ia` |

---

## Fluxo passo a passo

### 1. Invocar o skill

Peça para arquivar a conversa atual ou as últimas N conversas. Exemplos:

- "Arquiva esta conversa com IA"
- "Exporta as últimas 3 conversas para o GitHub"
- `/exportar-conversas-ia`

### 2. Informar o autor

O skill perguntará qual integrante é o autor:

- Caio
- Téo
- Pedro Vitor
- Pedro Paiva

### 3. Escolher o escopo

- **Conversa atual** — transcrição literal da sessão em andamento (feita pelo agente a partir do contexto)
- **Últimas N** — exportação do histórico local via `.jsonl` (pode estar incompleta)

### 4. Exportação

#### Conversa atual — transcrição literal (recomendado)

O Cursor grava arquivos `.jsonl` locais com grande parte das respostas marcadas como `[REDACTED]`. Por isso, para a conversa em andamento, o **agente deve transcrever manualmente** todo o histórico da sessão e salvar o arquivo.

Formato de cada mensagem:

```markdown
## Mensagem 1 — Usuário
<texto completo>

## Mensagem 2 — Assistente
<texto completo da resposta>
```

Depois, salve com:

```bash
python tools/exportar-conversas/exportar_conversa.py \
  --modo transcrever \
  --autor "Caio" \
  --ferramenta cursor \
  --titulo "titulo-da-conversa" \
  --corpo transcricao.md \
  --repo-root .
```

#### Últimas N — histórico local (pode ser parcial)

```bash
python tools/exportar-conversas/exportar_conversa.py \
  --modo jsonl \
  --autor "Téo" \
  --ferramenta cursor \
  --escopo ultimas \
  --n 3 \
  --repo-root .
```

O script inclui chamadas de ferramenta e marca trechos redigidos, mas **não substitui** a transcrição literal para a conversa atual.

### 5. Revisar arquivos gerados

Verifique os arquivos em `docs/conversas-ia/<autor>/`. O script avisa se detectou possíveis segredos (tokens, senhas) e os redigiu automaticamente.

### 6. Commit e push (com confirmação)

O skill pedirá confirmação antes de cada etapa:

1. **Commit** — `git add docs/conversas-ia/` + commit com mensagem padronizada
2. **Push** — `git push` na branch atual

Nenhuma ação git é executada sem sua aprovação explícita.

---

## Formato dos arquivos exportados

Cada conversa vira um arquivo Markdown com frontmatter YAML e **transcrição turno a turno**:

```markdown
---
autor: "Caio"
ferramenta: cursor
data_inicio: 2026-09-01T17:08:00-03:00
conversa_id: 8c1dd47f-a95b-424d-8c38-cd1aa40eba5a
titulo: "Skill arquivar conversas IA"
fonte: transcricao
---

## Mensagem 1 — Usuário
<texto completo da mensagem>

## Mensagem 2 — Assistente
<texto completo da resposta>

## Mensagem 3 — Usuário
...
```

O campo `fonte` indica a origem:

| Valor | Significado |
|---|---|
| `transcricao` | Transcrição literal feita pelo agente (completa) |
| `jsonl` | Lida do arquivo local (pode ter trechos redigidos) |

### Convenção de nomes de arquivo

```
YYYY-MM-DD_HHmm_<ferramenta>_<slug-titulo>.md
```

Exemplo: `2026-09-01_1708_cursor_skill-arquivar-conversas-ia.md`

Se já existir um arquivo com o mesmo nome, o script adiciona sufixo `-2`, `-3`, etc.

---

## Template manual (fallback)

Use este template quando o script não conseguir ler o histórico local (comum no Antigravity):

```markdown
---
autor: "<nome>"
ferramenta: antigravity
data_inicio: <ISO-8601>
conversa_id: manual-<timestamp>
titulo: "<titulo-da-conversa>"
---

## Usuário
<mensagens do usuário>

## Assistente
<respostas do assistente>
```

Salve em `docs/conversas-ia/<pasta-do-autor>/` seguindo a convenção de nomes acima.

---

## Onde cada ferramenta armazena conversas

| Ferramenta | Local (Windows) | Formato |
|---|---|---|
| Cursor | `%USERPROFILE%\.cursor\projects\<projeto>\agent-transcripts\` | `.jsonl` |
| Claude Code | `%USERPROFILE%\.claude\projects\` | `.jsonl` |
| Antigravity | `%APPDATA%\Antigravity\` + `~/.gemini/antigravity/brain/` | SQLite / artefatos |

O script tenta localizar automaticamente os transcripts do projeto atual comparando o caminho do repositório.

---

## Troubleshooting

### "Nenhuma conversa encontrada"

- Confirme que a ferramenta está aberta no diretório correto do projeto
- Para Cursor, verifique se existe pasta em `%USERPROFILE%\.cursor\projects\`
- Use o fallback manual descrito acima

### Antigravity não exporta automaticamente

O Antigravity armazena dados em formatos menos padronizados. Nesse caso:

1. O agente reconstrói a conversa atual a partir do contexto da sessão
2. Salva manualmente usando o template acima

### Exportação incompleta / trechos redigidos

O Cursor salva transcripts locais com `[REDACTED]` no lugar das respostas completas. Se o arquivo exportado parece um resumo em vez de uma transcrição:

1. Use o modo `transcrever` (conversa atual)
2. Peça ao agente para reescrever a conversa **na íntegra**, mensagem por mensagem
3. Não use `--modo jsonl --escopo atual` esperando transcrição completa

O script redige automaticamente padrões como `api_key=...`, tokens `sk-...`, `ghp_...` e chaves AWS. Revise o arquivo antes do commit e remova manualmente qualquer dado sensível restante.

### Arquivo com nome duplicado

O script adiciona sufixo numérico (`-2`, `-3`) automaticamente. Não é necessário renomear manualmente.

---

## Componentes do sistema

```text
.cursor/skills/exportar-conversas-ia/SKILL.md    # Skill Cursor
.agents/skills/exportar-conversas-ia/SKILL.md   # Skill Antigravity
.claude/skills/exportar-conversas-ia/SKILL.md   # Skill Claude Code
tools/exportar-conversas/exportar_conversa.py   # Script de exportação
tools/exportar-conversas/paths.py               # Resolução de caminhos locais
docs/conversas-ia/                              # Arquivo das conversas
```

Os três arquivos `SKILL.md` são idênticos e seguem o padrão aberto [Agent Skills](https://agentskills.io), compatível com Cursor, Antigravity e Claude Code.

---

## Boas práticas

1. Arquive ao final de cada sessão produtiva com IA
2. Revise o conteúdo exportado antes de confirmar o commit
3. Nunca commite arquivos `.env`, credenciais ou tokens
4. Use a branch de trabalho atual; o push publica na branch em que você está
5. Prefira exportar a conversa atual imediatamente após concluir uma tarefa
