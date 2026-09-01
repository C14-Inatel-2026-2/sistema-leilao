#!/usr/bin/env python3
"""Exporta conversas com IA para Markdown em docs/conversas-ia/."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from paths import FERRAMENTAS, TranscriptRef, list_transcripts

AUTHOR_ALIASES: dict[str, tuple[str, str]] = {
    "caio": ("Caio", "Caio"),
    "teo": ("Téo", "Teo"),
    "téo": ("Téo", "Teo"),
    "pedro vitor": ("Pedro Vitor", "Pedro-Vitor"),
    "pedro-vitor": ("Pedro Vitor", "Pedro-Vitor"),
    "pedro paiva": ("Pedro Paiva", "Pedro-Paiva"),
    "pedro-paiva": ("Pedro Paiva", "Pedro-Paiva"),
}

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password|passwd)\s*[:=]\s*\S+"),
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r"(?i)sk-[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"(?i)AKIA[0-9A-Z]{16}"),
]

TIMESTAMP_RE = re.compile(r"<timestamp>(.*?)</timestamp>", re.DOTALL)
USER_QUERY_RE = re.compile(r"<user_query>(.*?)</user_query>", re.DOTALL)
REDACTED_NOTE = "*(conteúdo redigido pelo Cursor no arquivo local)*"
MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def normalize_author(author: str) -> tuple[str, str]:
    key = author.strip().lower()
    if key not in AUTHOR_ALIASES:
        valid = ", ".join(sorted({v[0] for v in AUTHOR_ALIASES.values()}))
        raise ValueError(f"Autor inválido: {author!r}. Opções: {valid}")
    return AUTHOR_ALIASES[key]


def slugify(text: str, max_len: int = 60) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:max_len] or "conversa"


def redact_secrets(text: str) -> tuple[str, bool]:
    redacted = text
    found = False
    for pattern in SECRET_PATTERNS:
        if pattern.search(redacted):
            found = True
            redacted = pattern.sub("[REDACTADO: possível segredo detectado]", redacted)
    return redacted, found


def extract_timestamp(text: str) -> str | None:
    match = TIMESTAMP_RE.search(text)
    if not match:
        return None
    raw = match.group(1).strip()
    return parse_human_timestamp(raw) or raw


def parse_human_timestamp(raw: str) -> str | None:
    match = re.match(
        r"\w+,\s+(\w+)\s+(\d{1,2}),\s+(\d{4}),\s+(\d{1,2}):(\d{2})\s+(AM|PM)\s+\(UTC([+-]\d+)\)",
        raw,
        re.IGNORECASE,
    )
    if not match:
        return None
    month_str, day, year, hour, minute, ampm, tz_offset = match.groups()
    month = MONTH_MAP.get(month_str[:3].lower())
    if not month:
        return None
    hour_int = int(hour) % 12
    if ampm.upper() == "PM":
        hour_int += 12
    sign = tz_offset[0]
    hours = tz_offset[1:].zfill(2)
    tz = f"{sign}{hours}:00"
    try:
        dt = datetime(int(year), month, int(day), hour_int, int(minute))
        return f"{dt.isoformat(timespec='seconds')}{tz}"
    except ValueError:
        return None


def extract_user_query(text: str) -> str:
    match = USER_QUERY_RE.search(text)
    if match:
        return match.group(1).strip()
    cleaned = TIMESTAMP_RE.sub("", text).strip()
    return cleaned


def format_tool_use(block: dict) -> str:
    name = block.get("name") or block.get("tool_name") or "ferramenta"
    tool_input = block.get("input") or block.get("arguments") or {}
    if isinstance(tool_input, dict):
        summary_parts = []
        for key in ("command", "path", "pattern", "description", "query", "search_term"):
            if key in tool_input and tool_input[key]:
                summary_parts.append(f"{key}: {tool_input[key]}")
        if not summary_parts:
            summary_parts.append(json.dumps(tool_input, ensure_ascii=False)[:500])
        detail = "; ".join(summary_parts)
    else:
        detail = str(tool_input)[:500]
    return f"> **Ferramenta:** `{name}` — {detail}"


def format_text_block(text: str) -> str:
    text = text.strip()
    if text == "[REDACTED]":
        return REDACTED_NOTE
    if "[REDACTED]" in text:
        visible = text.replace("[REDACTED]", "").strip()
        parts = [part for part in (visible, REDACTED_NOTE) if part]
        return "\n\n".join(parts)
    return text


def parse_content_blocks(content_blocks: list) -> str:
    parts: list[str] = []
    for block in content_blocks:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type == "text":
            text = format_text_block(block.get("text", ""))
            if text:
                parts.append(text)
        elif block_type in ("tool_use", "tool-call", "tool_call"):
            parts.append(format_tool_use(block))
        elif block_type == "tool_result":
            result = block.get("content") or block.get("output") or ""
            if isinstance(result, list):
                result = "\n".join(
                    item.get("text", str(item)) if isinstance(item, dict) else str(item)
                    for item in result
                )
            result = str(result).strip()
            if result:
                parts.append(f"> **Resultado:**\n>\n> {result[:2000].replace(chr(10), chr(10) + '> ')}")
    return "\n\n".join(parts).strip()


def parse_jsonl_messages(path: Path) -> tuple[list[dict[str, str]], str | None, str]:
    messages: list[dict[str, str]] = []
    first_timestamp: str | None = None
    title = "conversa-ia"
    turn = 0

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            if record.get("type") == "turn_ended":
                continue

            role = record.get("role")
            if role not in ("user", "assistant"):
                continue

            message = record.get("message", {})
            combined = parse_content_blocks(message.get("content", []))
            if not combined:
                continue

            if role == "user":
                turn += 1
                ts = extract_timestamp(combined)
                if ts and not first_timestamp:
                    first_timestamp = ts
                combined = extract_user_query(combined)
                if title == "conversa-ia" and combined:
                    title = slugify(combined.split("\n")[0][:80])

            combined, _ = redact_secrets(combined)
            if not combined.strip():
                continue

            role_label = "Usuário" if role == "user" else "Assistente"
            messages.append({
                "role": role,
                "turn": turn if role == "user" else turn,
                "heading": f"## Mensagem {turn} — {role_label}",
                "text": combined,
            })

    return messages, first_timestamp, title


def parse_antigravity_markdown(path: Path) -> tuple[list[dict[str, str]], str | None, str]:
    content = path.read_text(encoding="utf-8")
    title = slugify(path.stem)
    messages = [{
        "role": "assistant",
        "turn": 1,
        "heading": "## Mensagem 1 — Assistente",
        "text": content,
    }]
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return messages, mtime.isoformat(), title


def build_markdown(
    autor_display: str,
    ferramenta: str,
    conversa_id: str,
    title: str,
    data_inicio: str | None,
    messages: list[dict[str, str]],
    fonte: str = "jsonl",
) -> str:
    if not data_inicio:
        data_inicio = datetime.now().astimezone().isoformat(timespec="seconds")

    body_lines: list[str] = []
    if fonte == "jsonl":
        body_lines.append(
            "> **Nota:** exportação a partir do arquivo local `.jsonl`. "
            "Trechos marcados como redigidos não estão disponíveis no disco. "
            "Para transcrição literal da conversa atual, use o modo `transcrever`.\n"
        )

    for msg in messages:
        heading = msg.get("heading")
        if not heading:
            role_label = "Usuário" if msg["role"] == "user" else "Assistente"
            turn = msg.get("turn", "?")
            heading = f"## Mensagem {turn} — {role_label}"
        body_lines.append(heading)
        body_lines.append("")
        body_lines.append(msg["text"])
        body_lines.append("")

    frontmatter = (
        "---\n"
        f'autor: "{autor_display}"\n'
        f"ferramenta: {ferramenta}\n"
        f"data_inicio: {data_inicio}\n"
        f"conversa_id: {conversa_id}\n"
        f'titulo: "{title.replace(chr(34), chr(39))}"\n'
        f"fonte: {fonte}\n"
        "---\n"
    )
    return frontmatter + "\n" + "\n".join(body_lines).rstrip() + "\n"


def unique_output_path(output_dir: Path, base_name: str) -> Path:
    candidate = output_dir / f"{base_name}.md"
    if not candidate.exists():
        return candidate
    counter = 2
    while True:
        candidate = output_dir / f"{base_name}-{counter}.md"
        if not candidate.exists():
            return candidate
        counter += 1


def save_markdown(
    markdown: str,
    autor_folder: str,
    ferramenta: str,
    title: str,
    repo_root: Path,
    mtime: float | None = None,
) -> Path:
    if mtime is None:
        dt = datetime.now().astimezone()
    else:
        dt = datetime.fromtimestamp(mtime, tz=timezone.utc).astimezone()

    filename_base = f"{dt.strftime('%Y-%m-%d_%H%M')}_{ferramenta}_{slugify(title)}"
    output_dir = repo_root / "docs" / "conversas-ia" / autor_folder
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = unique_output_path(output_dir, filename_base)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def export_transcript(
    ref: TranscriptRef,
    autor_display: str,
    autor_folder: str,
    repo_root: Path,
) -> tuple[Path, bool]:
    if ref.ferramenta == "antigravity" and ref.path.suffix == ".md":
        messages, data_inicio, title = parse_antigravity_markdown(ref.path)
    else:
        messages, data_inicio, title = parse_jsonl_messages(ref.path)

    if not messages:
        raise ValueError(f"Nenhuma mensagem encontrada em {ref.path}")

    markdown = build_markdown(
        autor_display=autor_display,
        ferramenta=ref.ferramenta,
        conversa_id=ref.conversa_id,
        title=title,
        data_inicio=data_inicio,
        messages=messages,
        fonte="jsonl",
    )

    secrets_found = "[REDACTADO" in markdown
    output_path = save_markdown(
        markdown, autor_folder, ref.ferramenta, title, repo_root, ref.mtime
    )
    return output_path, secrets_found


def save_transcription(
    corpo: str,
    autor_display: str,
    autor_folder: str,
    ferramenta: str,
    repo_root: Path,
    titulo: str,
    conversa_id: str | None = None,
    data_inicio: str | None = None,
) -> tuple[Path, bool]:
    corpo = corpo.strip()
    if not corpo:
        raise ValueError("Corpo da transcrição vazio.")

    corpo, secrets_found = redact_secrets(corpo)
    title = titulo or slugify(corpo.split("\n", 1)[0][:80])
    if title.startswith("mensagem"):
        title = "conversa-ia"

    if not data_inicio:
        data_inicio = datetime.now().astimezone().isoformat(timespec="seconds")

    frontmatter = (
        "---\n"
        f'autor: "{autor_display}"\n'
        f"ferramenta: {ferramenta}\n"
        f"data_inicio: {data_inicio}\n"
        f"conversa_id: {conversa_id or f'manual-{datetime.now().strftime('%Y%m%d%H%M%S')}'}\n"
        f'titulo: "{title.replace(chr(34), chr(39))}"\n'
        "fonte: transcricao\n"
        "---\n"
    )
    markdown = frontmatter + "\n" + corpo + "\n"
    output_path = save_markdown(markdown, autor_folder, ferramenta, title, repo_root)
    return output_path, secrets_found


def select_transcripts(refs: list[TranscriptRef], escopo: str, n: int) -> list[TranscriptRef]:
    if not refs:
        return []
    if escopo == "atual":
        return [refs[0]]
    return refs[:n]


def main() -> int:
    parser = argparse.ArgumentParser(description="Exporta conversas com IA para docs/conversas-ia/")
    parser.add_argument("--autor", required=True, help="Caio, Téo, Pedro Vitor ou Pedro Paiva")
    parser.add_argument("--ferramenta", required=True, choices=FERRAMENTAS)
    parser.add_argument(
        "--modo",
        choices=("jsonl", "transcrever"),
        default="jsonl",
        help="jsonl=lê arquivo local; transcrever=salva corpo fornecido pelo agente",
    )
    parser.add_argument("--escopo", choices=("atual", "ultimas"), default="atual")
    parser.add_argument("--n", type=int, default=1, help="Quantidade de conversas (escopo=ultimas)")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--corpo", type=Path, help="Arquivo com transcrição literal (modo transcrever)")
    parser.add_argument("--titulo", default="", help="Título da conversa")
    parser.add_argument("--conversa-id", default="", help="ID da conversa")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    autor_display, autor_folder = normalize_author(args.autor)

    if args.modo == "transcrever":
        if not args.corpo:
            print(
                "Erro: modo transcrever exige --corpo <arquivo.md> com a transcrição literal.",
                file=sys.stderr,
            )
            return 1
        corpo = args.corpo.read_text(encoding="utf-8")
        try:
            path, secrets = save_transcription(
                corpo=corpo,
                autor_display=autor_display,
                autor_folder=autor_folder,
                ferramenta=args.ferramenta,
                repo_root=repo_root,
                titulo=args.titulo,
                conversa_id=args.conversa_id or None,
            )
        except ValueError as exc:
            print(f"Erro: {exc}", file=sys.stderr)
            return 1
        print("Transcrição salva:")
        print(f"  - {path.relative_to(repo_root)}")
        if secrets:
            print("\nAviso: possíveis segredos foram redigidos.", file=sys.stderr)
        return 0

    if args.escopo == "ultimas" and args.n < 1:
        print("Erro: --n deve ser >= 1 para escopo 'ultimas'.", file=sys.stderr)
        return 1

    if args.escopo == "atual":
        print(
            "Aviso: o arquivo .jsonl local do Cursor redige grande parte das respostas.\n"
            "Para transcrição literal da conversa atual, o agente deve usar --modo transcrever.\n",
            file=sys.stderr,
        )

    refs = list_transcripts(args.ferramenta, repo_root)
    selected = select_transcripts(refs, args.escopo, args.n)

    if not selected:
        print(
            f"Erro: nenhuma conversa encontrada para ferramenta '{args.ferramenta}'.",
            file=sys.stderr,
        )
        return 1

    exported: list[Path] = []
    any_secrets = False

    for ref in selected:
        try:
            path, secrets = export_transcript(ref, autor_display, autor_folder, repo_root)
            exported.append(path)
            any_secrets = any_secrets or secrets
        except ValueError as exc:
            print(f"Aviso: {exc}", file=sys.stderr)

    if not exported:
        print("Erro: nenhum arquivo foi exportado.", file=sys.stderr)
        return 1

    print("Exportação concluída (parcial — ver nota sobre redação no arquivo):")
    for path in exported:
        print(f"  - {path.relative_to(repo_root)}")

    if any_secrets:
        print("\nAviso: possíveis segredos foram redigidos.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
