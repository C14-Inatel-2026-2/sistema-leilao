"""Resolução de caminhos locais de transcripts por ferramenta e SO."""

from __future__ import annotations

import os
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path


FERRAMENTAS = ("cursor", "claude", "antigravity")


@dataclass(frozen=True)
class TranscriptRef:
    path: Path
    conversa_id: str
    ferramenta: str
    mtime: float


def repo_to_slug(repo_root: Path) -> str:
    """Converte caminho do repositório no slug usado por Cursor/Claude."""
    resolved = str(repo_root.resolve())
    slug = resolved.lower()
    slug = re.sub(r"^[a-z]:", lambda m: m.group(0)[0], slug)
    slug = slug.replace("\\", "-").replace("/", "-")
    slug = re.sub(r"[^a-z0-9\-]", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def cursor_projects_dir() -> Path:
    return Path.home() / ".cursor" / "projects"


def claude_projects_dir() -> Path:
    return Path.home() / ".claude" / "projects"


def antigravity_state_db() -> Path | None:
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            candidate = Path(appdata) / "Antigravity" / "User" / "globalStorage" / "state.vscdb"
            if candidate.exists():
                return candidate
        localappdata = os.environ.get("LOCALAPPDATA")
        if localappdata:
            candidate = Path(localappdata) / "Antigravity" / "User" / "globalStorage" / "state.vscdb"
            if candidate.exists():
                return candidate
    else:
        for candidate in (
            Path.home() / "Library" / "Application Support" / "Antigravity" / "User" / "globalStorage" / "state.vscdb",
            Path.home() / ".config" / "Antigravity" / "User" / "globalStorage" / "state.vscdb",
        ):
            if candidate.exists():
                return candidate
    return None


def antigravity_brain_dir() -> Path:
    return Path.home() / ".gemini" / "antigravity" / "brain"


def find_cursor_project_dir(repo_root: Path) -> Path | None:
    slug = repo_to_slug(repo_root)
    projects = cursor_projects_dir()
    if not projects.exists():
        return None

    exact = projects / slug
    if exact.exists():
        return exact

    repo_name = repo_root.name.lower()
    for entry in projects.iterdir():
        if entry.is_dir() and entry.name.endswith(repo_name):
            return entry
    return None


def find_claude_project_dir(repo_root: Path) -> Path | None:
    slug = repo_to_slug(repo_root)
    projects = claude_projects_dir()
    if not projects.exists():
        return None

    for entry in projects.iterdir():
        if not entry.is_dir():
            continue
        if slug in entry.name.lower() or repo_root.name.lower() in entry.name.lower():
            return entry
    return None


def list_jsonl_transcripts(base_dir: Path, ferramenta: str) -> list[TranscriptRef]:
    if not base_dir or not base_dir.exists():
        return []

    refs: list[TranscriptRef] = []
    if ferramenta == "cursor":
        transcripts_dir = base_dir / "agent-transcripts"
        if not transcripts_dir.exists():
            return []
        for conv_dir in transcripts_dir.iterdir():
            if not conv_dir.is_dir():
                continue
            jsonl_files = list(conv_dir.glob("*.jsonl"))
            if not jsonl_files:
                continue
            path = jsonl_files[0]
            refs.append(
                TranscriptRef(
                    path=path,
                    conversa_id=conv_dir.name,
                    ferramenta=ferramenta,
                    mtime=path.stat().st_mtime,
                )
            )
    else:
        for path in base_dir.rglob("*.jsonl"):
            refs.append(
                TranscriptRef(
                    path=path,
                    conversa_id=path.stem,
                    ferramenta=ferramenta,
                    mtime=path.stat().st_mtime,
                )
            )

    refs.sort(key=lambda r: r.mtime, reverse=True)
    return refs


def list_antigravity_transcripts() -> list[TranscriptRef]:
    refs: list[TranscriptRef] = []
    brain = antigravity_brain_dir()
    if brain.exists():
        for path in brain.rglob("*.md"):
            refs.append(
                TranscriptRef(
                    path=path,
                    conversa_id=path.stem,
                    ferramenta="antigravity",
                    mtime=path.stat().st_mtime,
                )
            )
        refs.sort(key=lambda r: r.mtime, reverse=True)
        if refs:
            return refs

    db_path = antigravity_state_db()
    if not db_path:
        return []

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        if not tables:
            return []
    except sqlite3.Error:
        return []

    return refs


def list_transcripts(ferramenta: str, repo_root: Path) -> list[TranscriptRef]:
    if ferramenta == "cursor":
        project_dir = find_cursor_project_dir(repo_root)
        return list_jsonl_transcripts(project_dir, ferramenta)
    if ferramenta == "claude":
        project_dir = find_claude_project_dir(repo_root)
        return list_jsonl_transcripts(project_dir, ferramenta)
    if ferramenta == "antigravity":
        return list_antigravity_transcripts()
    raise ValueError(f"Ferramenta desconhecida: {ferramenta}")
