from __future__ import annotations

import logging
import re
from typing import Any

from . import gitlab_review, llm, pr_review

logger = logging.getLogger(__name__)

_DOCS_SYSTEM_PROMPT = (
    "You are a documentation reviewer. Given a code diff, decide whether documentation "
    "needs updating, and suggest concrete edits.\n\n"
    "Check for:\n"
    "1. New / changed public API endpoints (path, method, request/response).\n"
    "2. New / changed CLI commands or environment variables.\n"
    "3. New / removed configuration options.\n"
    "4. Breaking changes that need a CHANGELOG entry.\n"
    "5. New features that warrant a README mention.\n\n"
    "Rules:\n"
    "- Be specific. Cite file paths from the diff.\n"
    "- Suggest concrete edits, not vague directions.\n"
    "- If no docs need updating, say so in one line.\n"
    "- Output format (no markdown, no preamble):\n\n"
    "VERDICT: NEEDS_DOCS | NO_DOCS_NEEDED\n"
    "AFFECTED_AREAS:\n"
    "- area name (e.g. README, CHANGELOG, api-docs.md)\n"
    "SUGGESTIONS:\n"
    "- [target file] specific edit description\n"
    "- [target file] specific edit description\n"
    "SUMMARY: one-line summary"
)

_MAX_DIFF_CHARS = 12000

_DOC_FILE_RE = re.compile(
    r"^(README|CHANGELOG|CONTRIBUTING|HISTORY|UPGRADING|MIGRATION|RELEASE_NOTES)",
    re.IGNORECASE,
)
_DOC_DIR_HINTS = ("docs/", "doc/", "documentation/", ".github/")
_DOC_EXT = (".md", ".mdx", ".rst", ".adoc", ".txt")
_API_HINT_RE = re.compile(r"@app\.(get|post|put|delete|patch)|router\.(get|post|put|delete|patch)|\bapi\.add_resource", re.IGNORECASE)
_ENV_HINT_RE = re.compile(r"os\.getenv|os\.environ|process\.env\.", re.IGNORECASE)
_CMD_HINT_RE = re.compile(r"CommandHandler\(\"|argparse\.|click\.command|@app\.command", re.IGNORECASE)


def _diff_changed_files(diff: str) -> list[str]:
    files: list[str] = []
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split(" b/")
            if len(parts) == 2:
                files.append(parts[1])
        elif line.startswith("+++ b/"):
            files.append(line[6:])
    seen: set[str] = set()
    out: list[str] = []
    for f in files:
        if f and f not in seen:
            seen.add(f)
            out.append(f)
    return out


def _is_doc_file(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    if _DOC_FILE_RE.match(name):
        return True
    if any(path.startswith(d) for d in _DOC_DIR_HINTS):
        return True
    return path.lower().endswith(_DOC_EXT)


def _classify_diff(diff: str) -> dict[str, Any]:
    files = _diff_changed_files(diff)
    code_files = [f for f in files if not _is_doc_file(f)]
    doc_files = [f for f in files if _is_doc_file(f)]

    has_api = bool(_API_HINT_RE.search(diff))
    has_env = bool(_ENV_HINT_RE.search(diff))
    has_cmd = bool(_CMD_HINT_RE.search(diff))

    return {
        "files_changed": files,
        "code_files": code_files,
        "doc_files": doc_files,
        "signals": {
            "has_api_change": has_api,
            "has_env_change": has_env,
            "has_command_change": has_cmd,
        },
    }


def _parse_llm_response(response: str) -> dict[str, Any]:
    section = None
    affected: list[str] = []
    suggestions: list[str] = []
    verdict = "NO_DOCS_NEEDED"
    summary = ""

    for raw_line in response.splitlines():
        stripped = raw_line.strip()
        upper = stripped.upper()

        if upper.startswith("VERDICT:"):
            v = stripped[len("VERDICT:"):].strip().upper()
            if "NEEDS_DOCS" in v:
                verdict = "NEEDS_DOCS"
            else:
                verdict = "NO_DOCS_NEEDED"
            continue
        if upper.startswith("AFFECTED_AREAS"):
            section = "areas"
            continue
        if upper.startswith("SUGGESTIONS"):
            section = "suggestions"
            continue
        if upper.startswith("SUMMARY:"):
            summary = stripped[len("SUMMARY:"):].strip()
            section = None
            continue

        if not stripped or stripped == "-" or stripped.lower() == "- (none)":
            continue

        if section == "areas":
            text = stripped.lstrip("-").strip()
            if text and text.lower() != "(none)":
                affected.append(text)
        elif section == "suggestions":
            text = stripped.lstrip("-").strip()
            if text and text.lower() != "(none)":
                suggestions.append(text)

    return {
        "verdict": verdict,
        "affected_areas": affected,
        "suggestions": suggestions,
        "summary": summary,
    }


async def analyze(diff: str, pr_title: str, pr_body: str | None = None) -> dict[str, Any]:
    if not diff or not diff.strip():
        return {
            "verdict": "NO_DOCS_NEEDED",
            "affected_areas": [],
            "suggestions": [],
            "summary": "diff kosong",
            "classification": {"files_changed": [], "code_files": [], "doc_files": [], "signals": {}},
        }

    classification = _classify_diff(diff)

    truncated = diff[:_MAX_DIFF_CHARS]
    was_truncated = len(diff) > _MAX_DIFF_CHARS
    if was_truncated:
        truncated += f"\n\n... (truncated, {len(diff)} total chars)"

    user_content = f"PR Title: {pr_title}\n"
    if pr_body:
        user_content += f"PR Description: {pr_body[:500]}\n"
    sig = classification["signals"]
    hints: list[str] = []
    if sig.get("has_api_change"):
        hints.append("API endpoints changed")
    if sig.get("has_env_change"):
        hints.append("env vars referenced")
    if sig.get("has_command_change"):
        hints.append("CLI/command handlers changed")
    if classification["doc_files"]:
        hints.append(f"{len(classification['doc_files'])} doc files already updated")
    if hints:
        user_content += "\nSignal hints: " + ", ".join(hints) + "\n"
    user_content += f"\nDiff:\n```\n{truncated}\n```"

    response = await llm.chat_completion(
        messages=[
            {"role": "system", "content": _DOCS_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        max_tokens=1200,
    )

    parsed = _parse_llm_response(response)
    parsed["classification"] = classification
    parsed["truncated"] = was_truncated
    parsed["raw"] = response
    return parsed


async def analyze_github_pr(owner: str, repo: str, pr_number: int, pr_title: str = "", pr_body: str | None = None) -> dict[str, Any]:
    diff = await pr_review.fetch_pr_diff(owner, repo, pr_number)
    if diff is None:
        return {"ok": False, "error": "could not fetch diff", "platform": "github", "ref": f"{owner}/{repo}#{pr_number}"}
    if not pr_title:
        pr_title = f"{owner}/{repo}#{pr_number}"
    result = await analyze(diff, pr_title, pr_body)
    result["ok"] = True
    result["platform"] = "github"
    result["ref"] = f"{owner}/{repo}#{pr_number}"
    return result


async def analyze_gitlab_mr(project_id: int | str, mr_iid: int, mr_title: str = "", mr_body: str | None = None) -> dict[str, Any]:
    try:
        pid_int = int(project_id)
    except (TypeError, ValueError):
        return {"ok": False, "error": f"invalid GitLab project_id: {project_id!r}", "platform": "gitlab"}
    diff = await gitlab_review.fetch_mr_diff(pid_int, mr_iid)
    if diff is None:
        return {"ok": False, "error": "could not fetch diff", "platform": "gitlab", "ref": f"{project_id}!{mr_iid}"}
    if not mr_title:
        mr_title = f"{project_id}!{mr_iid}"
    result = await analyze(diff, mr_title, mr_body)
    result["ok"] = True
    result["platform"] = "gitlab"
    result["ref"] = f"{project_id}!{mr_iid}"
    return result


def format_for_telegram(result: dict[str, Any]) -> str:
    if not result.get("ok", True):
        return f"⚠️ Docs sync failed: {result.get('error', 'unknown')} ({result.get('ref', '')})"

    verdict = result.get("verdict", "NO_DOCS_NEEDED")
    icon = "📝" if verdict == "NEEDS_DOCS" else "✅"
    badge = "Needs Docs Update" if verdict == "NEEDS_DOCS" else "Docs Look Synced"

    ref = result.get("ref", "")
    lines = [f"{icon} <b>Docs Sync — {badge}</b>"]
    if ref:
        lines.append(f"<code>{ref}</code>")
    if result.get("summary"):
        lines.append("")
        lines.append(result["summary"])

    affected = result.get("affected_areas") or []
    if affected:
        lines.append("")
        lines.append("📂 <b>Affected Areas</b>")
        for a in affected[:10]:
            lines.append(f"• {a}")

    suggestions = result.get("suggestions") or []
    if suggestions:
        lines.append("")
        lines.append(f"💡 <b>Suggestions ({len(suggestions)})</b>")
        for s in suggestions[:8]:
            lines.append(f"• {s}")
        if len(suggestions) > 8:
            lines.append(f"... +{len(suggestions) - 8} more")

    classification = result.get("classification") or {}
    code_files = classification.get("code_files") or []
    doc_files = classification.get("doc_files") or []
    if code_files or doc_files:
        lines.append("")
        lines.append(f"📊 {len(code_files)} code file(s), {len(doc_files)} doc file(s) changed")

    if result.get("truncated"):
        lines.append("")
        lines.append("⚠️ <i>Diff terlalu panjang, sebagian dipotong.</i>")

    return "\n".join(lines).strip()
