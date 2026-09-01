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
MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def clean_message_text(text: str) -> str:
    lines = [line for line in text.split("\n") if line.strip() != "[REDACTED]"]
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


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
    """Converte timestamps legíveis do Cursor para ISO-8601."""
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


def parse_jsonl_messages(path: Path) -> tuple[list[dict[str, str]], str | None, str]:
    messages: list[dict[str, str]] = []
    first_timestamp: str | None = None
    title = "conversa-ia"

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
            content_blocks = message.get("content", [])
            text_parts: list[str] = []

            for block in content_blocks:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    text = block.get("text", "").strip()
                    if text:
                        text_parts.append(text)

            if not text_parts:
                continue

            combined = "\n\n".join(text_parts)
            if role == "user":
                ts = extract_timestamp(combined)
                if ts and not first_timestamp:
                    first_timestamp = ts
                combined = extract_user_query(combined)
                if title == "conversa-ia" and combined:
                    title = slugify(combined.split("\n")[0][:80])

            combined, _ = redact_secrets(combined)
            combined = clean_message_text(combined)
            if not combined.strip():
                continue

            if messages and messages[-1]["role"] == role:
                messages[-1]["text"] += "\n\n" + combined
            else:
                messages.append({"role": role, "text": combined})

    return messages, first_timestamp, title


def parse_antigravity_markdown(path: Path) -> tuple[list[dict[str, str]], str | None, str]:
    content = path.read_text(encoding="utf-8")
    title = slugify(path.stem)
    messages = [{"role": "assistant", "text": content}]
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return messages, mtime.isoformat(), title


def build_markdown(
    autor_display: str,
    ferramenta: str,
    conversa_id: str,
    title: str,
    data_inicio: str | None,
    messages: list[dict[str, str]],
) -> str:
    if not data_inicio:
        data_inicio = datetime.now().astimezone().isoformat(timespec="seconds")

    role_labels = {"user": "Usuário", "assistant": "Assistente"}
    body_lines: list[str] = []

    for msg in messages:
        label = role_labels.get(msg["role"], msg["role"].title())
        body_lines.append(f"## {label}\n")
        body_lines.append(msg["text"])
        body_lines.append("")

    frontmatter = (
        "---\n"
        f'autor: "{autor_display}"\n'
        f"ferramenta: {ferramenta}\n"
        f"data_inicio: {data_inicio}\n"
        f"conversa_id: {conversa_id}\n"
        f'titulo: "{title.replace(chr(34), chr(39))}"\n'
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
    )

    secrets_found = "[REDACTADO" in markdown

    if data_inicio:
        try:
            dt = datetime.fromisoformat(data_inicio.replace("Z", "+00:00"))
        except ValueError:
            dt = datetime.fromtimestamp(ref.mtime, tz=timezone.utc).astimezone()
    else:
        dt = datetime.fromtimestamp(ref.mtime, tz=timezone.utc).astimezone()

    filename_base = f"{dt.strftime('%Y-%m-%d_%H%M')}_{ref.ferramenta}_{title}"
    output_dir = repo_root / "docs" / "conversas-ia" / autor_folder
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = unique_output_path(output_dir, filename_base)
    output_path.write_text(markdown, encoding="utf-8")
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
    parser.add_argument("--escopo", required=True, choices=("atual", "ultimas"))
    parser.add_argument("--n", type=int, default=1, help="Quantidade de conversas (escopo=ultimas)")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    autor_display, autor_folder = normalize_author(args.autor)

    if args.escopo == "ultimas" and args.n < 1:
        print("Erro: --n deve ser >= 1 para escopo 'ultimas'.", file=sys.stderr)
        return 1

    refs = list_transcripts(args.ferramenta, repo_root)
    selected = select_transcripts(refs, args.escopo, args.n)

    if not selected:
        print(
            f"Erro: nenhuma conversa encontrada para ferramenta '{args.ferramenta}'.",
            file=sys.stderr,
        )
        if args.ferramenta == "antigravity":
            print(
                "Para Antigravity, exporte manualmente a conversa atual em Markdown "
                "ou verifique ~/.gemini/antigravity/brain/.",
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

    print("Exportação concluída:")
    for path in exported:
        print(f"  - {path.relative_to(repo_root)}")

    if any_secrets:
        print(
            "\nAviso: possíveis segredos foram redigados. Revise os arquivos antes do commit.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
