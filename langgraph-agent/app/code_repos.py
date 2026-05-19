from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
import tempfile
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlparse

import yaml
from qdrant_client.http import models as qmodels

from . import config, llm, qdrant_helper
from .embedding import embed_batch

BATCH_SIZE = 64
MAX_FILE_BYTES = 500 * 1024
CHUNK_LINES = 140
CHUNK_OVERLAP = 25
MAX_CHUNK_CHARS = 8000

_CODE_NAMESPACE = uuid.UUID("4b954fb8-c92d-4d9b-8367-28b03cf733a1")
_INDEX_LOCKS: set[str] = set()

_SKIP_DIRS = {
    ".git",
    "node_modules",
    "vendor",
    "dist",
    "build",
    ".next",
    "storage",
    "coverage",
    "__pycache__",
}
_SKIP_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg", ".pdf",
    ".zip", ".gz", ".tar", ".tgz", ".rar", ".7z", ".woff", ".woff2",
    ".ttf", ".eot", ".mp4", ".mp3", ".mov", ".avi", ".lock", ".map",
}

_LANGUAGE_BY_SUFFIX = {
    ".php": "php",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "jsx",
    ".py": "python",
    ".go": "go",
    ".java": "java",
    ".cs": "csharp",
    ".rb": "ruby",
    ".vue": "vue",
    ".blade.php": "blade",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".md": "markdown",
    ".sql": "sql",
}


@dataclass(frozen=True)
class RepoConfig:
    id: str
    name: str
    provider: str
    url: str
    branch: str
    enabled: bool = True


def load_repos() -> list[RepoConfig]:
    path = config.REPOS_CONFIG_PATH
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    repos = raw.get("repos") or []
    out: list[RepoConfig] = []
    for item in repos:
        try:
            repo = RepoConfig(
                id=str(item["id"]),
                name=str(item.get("name") or item["id"]),
                provider=str(item["provider"]).lower(),
                url=str(item["url"]),
                branch=str(item.get("branch") or "main"),
                enabled=bool(item.get("enabled", True)),
            )
        except (KeyError, TypeError, ValueError):
            continue
        out.append(repo)
    return out


def get_repo(repo_id: str) -> RepoConfig | None:
    for repo in load_repos():
        if repo.enabled and repo.id == repo_id:
            return repo
    return None


def list_projects() -> list[dict[str, Any]]:
    projects: list[dict[str, Any]] = []
    for repo in load_repos():
        latest = _latest_indexed_commit(repo.id)
        try:
            chunks = qdrant_helper.count(config.COLL_CODE, {"repo_id": repo.id})
            status = "ok"
        except Exception as exc:
            chunks = 0
            status = f"qdrant_unavailable:{type(exc).__name__}"
        projects.append(
            {
                "id": repo.id,
                "name": repo.name,
                "provider": repo.provider,
                "branch": repo.branch,
                "enabled": repo.enabled,
                "indexed_commit": latest.get("commit"),
                "indexed_at": latest.get("indexed_at"),
                "chunks": chunks,
                "status": status,
            }
        )
    return projects


def index_repo(repo_id: str) -> dict[str, Any]:
    repo = get_repo(repo_id)
    if repo is None:
        known = [r.id for r in load_repos() if r.enabled]
        return {"ok": False, "error": "unknown repo", "known": known}
    if repo.id in _INDEX_LOCKS:
        return {"ok": False, "error": "index already running", "repo_id": repo.id}

    _INDEX_LOCKS.add(repo.id)
    started = time.monotonic()
    try:
        qdrant_helper.ensure_collection(config.COLL_CODE)
        repo_path = _sync_repo(repo)
        commit = _git(repo_path, ["rev-parse", "HEAD"])
        short_commit = commit[:8]
        chunks = _collect_chunks(repo, repo_path, commit)
        _upsert_chunks(chunks)
        _delete_old_commit(repo.id, commit)
        return {
            "ok": True,
            "repo_id": repo.id,
            "commit": commit,
            "short_commit": short_commit,
            "files": len({c["path"] for c in chunks}),
            "chunks": len(chunks),
            "duration_seconds": round(time.monotonic() - started, 1),
        }
    finally:
        _INDEX_LOCKS.discard(repo.id)


def search_code(query: str, repo_id: str | None = None, limit: int = 8) -> list[dict[str, Any]]:
    filters = {"repo_id": repo_id} if repo_id else None
    return qdrant_helper.search(config.COLL_CODE, query, limit=limit, filters=filters)


async def answer_code_question(question: str, repo_id: str | None = None) -> str:
    hits = search_code(question, repo_id=repo_id, limit=10)
    useful = [h for h in hits if float(h.get("score", 0)) >= 0.2]
    if not useful:
        target = f" di {repo_id}" if repo_id else ""
        return f"Tidak ketemu konteks kode yang cukup kuat{target}. Coba /cari dengan keyword lebih spesifik."

    context_lines: list[str] = []
    citations: list[str] = []
    for h in useful[:10]:
        p = h["payload"]
        cite = _citation(p)
        citations.append(cite)
        context_lines.append(f"[{cite}]\n{p.get('text', '')[:2500]}")

    system_prompt = (
        "Kamu menjawab pertanyaan tentang source code dari konteks yang diberikan. "
        "Jawab dalam Bahasa Indonesia ringkas. Wajib pakai citation persis dari label konteks, "
        "format repo:path:start-end@sha. Jika konteks tidak cukup, bilang tidak tahu. "
        "Jangan mengarang alasan bisnis yang tidak tertulis di kode."
    )
    user_prompt = (
        "Pertanyaan:\n"
        f"{question}\n\n"
        "Konteks kode:\n"
    )
    user_prompt += "\n\n".join(context_lines)
    user_prompt += "\n\nJawab dengan bagian: Ringkasan, Detail, Sumber."
    try:
        return await llm.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=1200,
        )
    except Exception as exc:
        sources = "\n".join(f"- {c}" for c in sorted(set(citations[:5])))
        return f"⚠️ LLM error: {exc}\n\nKonteks teratas:\n{sources}"


def format_search_results(query: str, hits: list[dict[str, Any]]) -> str:
    if not hits:
        return f"Tidak ditemukan hasil untuk: {query}"
    lines = [f"🔍 Hasil pencarian kode: {query}", ""]
    for i, h in enumerate(hits, 1):
        p = h["payload"]
        snippet = _compact(p.get("text", ""))[:260]
        lines.append(f"{i}. {snippet}...")
        lines.append(f"   📎 {_citation(p)} · score {h['score']:.3f}")
    return "\n".join(lines)


def _sync_repo(repo: RepoConfig) -> Path:
    base = config.REPO_BASE_DIR
    base.mkdir(parents=True, exist_ok=True)
    path = base / repo.id
    safe_url = _safe_url(repo.url)
    with _git_auth_env(repo) as auth_env:
        if not path.exists():
            try:
                _run_git_command(
                    ["git", "clone", "--depth", "1", "--branch", repo.branch, safe_url, str(path)],
                    cwd=base,
                    extra_env=auth_env,
                )
            finally:
                if path.exists():
                    _run_git_command(["git", "remote", "set-url", "origin", safe_url], cwd=path)
        else:
            try:
                _run_git_command(["git", "remote", "set-url", "origin", safe_url], cwd=path)
                _run_git_command(
                    ["git", "fetch", "origin", repo.branch, "--depth", "1"],
                    cwd=path,
                    extra_env=auth_env,
                )
                _run_git_command(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=path)
            finally:
                _run_git_command(["git", "remote", "set-url", "origin", safe_url], cwd=path)
    return path


def _token_for(repo: RepoConfig) -> str:
    token = config.GH_PAT if repo.provider == "github" else config.GITLAB_PAT
    if not token:
        raise RuntimeError(f"missing token for provider {repo.provider}")
    parsed = urlparse(repo.url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RuntimeError("repo url must be HTTPS in Phase 1")
    return token


def _safe_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme and parsed.hostname:
        host = parsed.hostname
        if parsed.port:
            host = f"{host}:{parsed.port}"
        return f"https://{host}{parsed.path}"
    return url


@contextmanager
def _git_auth_env(repo: RepoConfig) -> Iterator[dict[str, str]]:
    token = _token_for(repo)
    user = "x-access-token" if repo.provider == "github" else "oauth2"
    askpass_dir = Path(tempfile.mkdtemp(prefix="git-askpass-", dir=str(config.REPO_BASE_DIR)))
    try:
        os.chmod(askpass_dir, stat.S_IRWXU)
        script = askpass_dir / "askpass.sh"
        script.write_text(
            "#!/bin/sh\n"
            'case "$1" in\n'
            "  Username*) printf %s \"$GIT_ASKPASS_USER\" ;;\n"
            "  Password*) printf %s \"$GIT_ASKPASS_TOKEN\" ;;\n"
            "esac\n",
            encoding="utf-8",
        )
        os.chmod(script, stat.S_IRWXU)
        yield {
            "GIT_ASKPASS": str(script),
            "GIT_ASKPASS_USER": user,
            "GIT_ASKPASS_TOKEN": token,
            "GIT_TERMINAL_PROMPT": "0",
        }
    finally:
        try:
            for child in askpass_dir.iterdir():
                child.unlink(missing_ok=True)
            askpass_dir.rmdir()
        except OSError:
            pass


def _git(path: Path, args: list[str]) -> str:
    return _run_git_command(["git", *args], cwd=path).strip()


def _run_git_command(cmd: list[str], cwd: Path, extra_env: dict[str, str] | None = None) -> str:
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", **(extra_env or {})}
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            env=env,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(_sanitize_git_error(exc.stderr or exc.stdout)) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"git command timed out: {cmd[1] if len(cmd) > 1 else 'git'}") from exc
    return result.stdout


def _sanitize_git_error(text: str) -> str:
    text = re.sub(r"https://[^\s:@]+:[^\s@]+@", "https://***:***@", text)
    return text.strip()[-500:] or "git command failed"


def _collect_chunks(repo: RepoConfig, repo_path: Path, commit: str) -> list[dict[str, Any]]:
    listed = _git(repo_path, ["ls-files", "--cached", "--others", "--exclude-standard"])
    now = datetime.now(timezone.utc).isoformat()
    chunks: list[dict[str, Any]] = []
    for rel in listed.splitlines():
        path = repo_path / rel
        if not path.is_file() or _skip_path(rel, path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if "\x00" in text:
            continue
        file_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
        language = _language_for(rel)
        for idx, chunk in enumerate(_line_chunks(text)):
            point_key = f"{repo.id}:{commit}:{rel}:{chunk['start_line']}-{chunk['end_line']}"
            chunks.append(
                {
                    "id": str(uuid.uuid5(_CODE_NAMESPACE, point_key)),
                    "text": chunk["text"],
                    "repo_id": repo.id,
                    "repo_name": repo.name,
                    "provider": repo.provider,
                    "branch": repo.branch,
                    "commit": commit,
                    "path": rel,
                    "language": language,
                    "chunk_index": idx,
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "file_hash": file_hash,
                    "indexed_at": now,
                }
            )
    return chunks


def _skip_path(rel: str, path: Path) -> bool:
    parts = set(Path(rel).parts)
    if parts & _SKIP_DIRS:
        return True
    lower = rel.lower()
    if lower.endswith(".min.js") or any(lower.endswith(s) for s in _SKIP_SUFFIXES):
        return True
    try:
        return path.stat().st_size > MAX_FILE_BYTES
    except OSError:
        return True


def _language_for(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".blade.php"):
        return "blade"
    suffix = Path(lower).suffix
    return _LANGUAGE_BY_SUFFIX.get(suffix, suffix.lstrip(".") or "text")


def _line_chunks(text: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    if not lines:
        return []
    if len(lines) <= 100 and len(text) <= MAX_CHUNK_CHARS:
        return [{"start_line": 1, "end_line": len(lines), "text": text.strip()}]

    chunks: list[dict[str, Any]] = []
    start = 0
    while start < len(lines):
        end = min(len(lines), start + CHUNK_LINES)
        chunk_lines = lines[start:end]
        chunk_text = "\n".join(chunk_lines).strip()
        if len(chunk_text) > MAX_CHUNK_CHARS:
            chunk_text = chunk_text[:MAX_CHUNK_CHARS]
        if chunk_text:
            chunks.append({"start_line": start + 1, "end_line": end, "text": chunk_text})
        if end == len(lines):
            break
        start = max(end - CHUNK_OVERLAP, start + 1)
    return chunks


def _upsert_chunks(chunks: list[dict[str, Any]]) -> None:
    client = qdrant_helper.get_client()
    for offset in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[offset : offset + BATCH_SIZE]
        vectors = embed_batch(c["text"] for c in batch)
        points = [
            qmodels.PointStruct(id=c["id"], vector=v, payload={k: val for k, val in c.items() if k != "id"})
            for c, v in zip(batch, vectors)
        ]
        client.upsert(collection_name=config.COLL_CODE, points=points, wait=True)


def _delete_old_commit(repo_id: str, commit: str) -> None:
    client = qdrant_helper.get_client()
    offset = None
    old_ids: list[str] = []
    while True:
        points, offset = client.scroll(
            collection_name=config.COLL_CODE,
            scroll_filter=qmodels.Filter(
                must=[qmodels.FieldCondition(key="repo_id", match=qmodels.MatchValue(value=repo_id))]
            ),
            limit=256,
            offset=offset,
            with_payload=True,
        )
        old_ids.extend(str(p.id) for p in points if (p.payload or {}).get("commit") != commit)
        if len(old_ids) >= 512:
            qdrant_helper.delete_points(config.COLL_CODE, old_ids)
            old_ids.clear()
        if offset is None:
            break
    if old_ids:
        qdrant_helper.delete_points(config.COLL_CODE, old_ids)


def _latest_indexed_commit(repo_id: str) -> dict[str, Any]:
    try:
        hits = qdrant_helper.scroll(config.COLL_CODE, filters={"repo_id": repo_id}, limit=1)
    except Exception:
        return {}
    if not hits:
        return {}
    payload = hits[0].get("payload", {})
    return {"commit": payload.get("commit"), "indexed_at": payload.get("indexed_at")}


def _citation(payload: dict[str, Any]) -> str:
    sha = str(payload.get("commit") or "")[:8]
    return (
        f"{payload.get('repo_id')}:{payload.get('path')}:"
        f"{payload.get('start_line')}-{payload.get('end_line')}@{sha}"
    )


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
