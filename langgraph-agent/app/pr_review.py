from __future__ import annotations

import hashlib
import hmac as _hmac
import json
import logging
from pathlib import Path
from typing import Any

import httpx

from . import config, llm, telegram

logger = logging.getLogger("agent.pr_review")

GH_API = "https://api.github.com"
_WHITELIST_FILE = Path("/app/state/review_repos.json")

_REVIEW_SYSTEM_PROMPT = (
    "You are a senior code reviewer. Analyze the PR diff below and provide a concise review.\n\n"
    "Focus on:\n"
    "1. Bugs or logic errors\n"
    "2. Security issues (injection, auth bypass, secrets exposure)\n"
    "3. Performance anti-patterns (N+1 queries, unnecessary allocations)\n"
    "4. Missing error handling\n"
    "5. Code style issues only if severe\n\n"
    "Rules:\n"
    "- Be concise. No praise, no filler.\n"
    "- If the change is clean and minor, say so in one sentence.\n"
    "- For each finding, state: file, issue, suggestion.\n"
    "- End with a verdict: APPROVE (clean), COMMENT (minor notes), or REQUEST_CHANGES (bugs/security).\n"
    "- Output format:\n"
    "  FINDINGS:\n"
    "  - [file.py] issue description → suggestion\n"
    "  VERDICT: APPROVE|COMMENT|REQUEST_CHANGES\n"
    "  SUMMARY: one-line summary for the review body"
)

_MAX_DIFF_CHARS = 12000


def get_whitelist() -> list[str]:
    if _WHITELIST_FILE.exists():
        try:
            return json.loads(_WHITELIST_FILE.read_text())
        except Exception:
            pass
    return []


def set_whitelist(repos: list[str]) -> None:
    _WHITELIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    _WHITELIST_FILE.write_text(json.dumps(repos, indent=2))


def is_repo_allowed(platform: str, full_name: str) -> bool:
    whitelist = get_whitelist()
    if not whitelist:
        return True
    key = f"{platform}:{full_name}"
    return key in whitelist


def verify_webhook_signature(payload_body: bytes, signature_header: str) -> bool:
    if not config.GH_WEBHOOK_SECRET:
        return True
    if not signature_header:
        return False
    expected = "sha256=" + _hmac.new(
        config.GH_WEBHOOK_SECRET.encode(), payload_body, hashlib.sha256
    ).hexdigest()
    return _hmac.compare_digest(expected, signature_header)


def _gh_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {config.GH_PAT}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def fetch_pr_diff(owner: str, repo: str, pr_number: int) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                f"{GH_API}/repos/{owner}/{repo}/pulls/{pr_number}",
                headers={
                    "Authorization": f"Bearer {config.GH_PAT}",
                    "Accept": "application/vnd.github.diff",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
            )
        if r.status_code == 200:
            return r.text
    except httpx.RequestError as exc:
        logger.error("Failed to fetch diff for %s/%s#%d: %s", owner, repo, pr_number, exc)
    return None


async def analyze_diff(diff: str, pr_title: str, pr_body: str | None = None) -> dict[str, str]:
    truncated = diff[:_MAX_DIFF_CHARS]
    if len(diff) > _MAX_DIFF_CHARS:
        truncated += f"\n\n... (truncated, {len(diff)} total chars)"

    user_content = f"PR Title: {pr_title}\n"
    if pr_body:
        user_content += f"PR Description: {pr_body[:500]}\n"
    user_content += f"\nDiff:\n```\n{truncated}\n```"

    response = await llm.chat_completion(
        messages=[
            {"role": "system", "content": _REVIEW_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        max_tokens=1500,
    )

    verdict = "COMMENT"
    summary = response
    for line in response.splitlines():
        stripped = line.strip().upper()
        if stripped.startswith("VERDICT:"):
            v = stripped.replace("VERDICT:", "").strip()
            if "APPROVE" in v:
                verdict = "APPROVE"
            elif "REQUEST_CHANGES" in v:
                verdict = "REQUEST_CHANGES"
            else:
                verdict = "COMMENT"
        if line.strip().upper().startswith("SUMMARY:"):
            summary = line.strip()[len("SUMMARY:"):].strip()

    return {"verdict": verdict, "body": response, "summary": summary}


async def post_review(
    owner: str, repo: str, pr_number: int, commit_sha: str, body: str, event: str
) -> dict[str, Any] | None:
    payload: dict[str, Any] = {
        "commit_id": commit_sha,
        "body": body,
        "event": event,
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                f"{GH_API}/repos/{owner}/{repo}/pulls/{pr_number}/reviews",
                headers=_gh_headers(),
                json=payload,
            )
        if r.status_code in (200, 201):
            return r.json()
        logger.error("Post review failed %d: %s", r.status_code, r.text[:300])
    except httpx.RequestError as exc:
        logger.error("Post review request error: %s", exc)
    return None


async def handle_pr_event(payload: dict[str, Any]) -> dict[str, Any]:
    action = payload.get("action", "")
    if action not in ("opened", "synchronize", "reopened", "ready_for_review"):
        return {"skipped": True, "reason": f"action={action} not reviewable"}

    pr = payload.get("pull_request", {})
    if pr.get("draft"):
        return {"skipped": True, "reason": "draft PR"}

    repo_data = payload.get("repository", {})
    full_name = repo_data.get("full_name", "")
    owner, repo = full_name.split("/", 1) if "/" in full_name else ("", "")
    pr_number = pr.get("number", 0)
    pr_title = pr.get("title", "")
    pr_body = pr.get("body") or ""
    head_sha = pr.get("head", {}).get("sha", "")

    if not owner or not repo or not pr_number:
        return {"skipped": True, "reason": "missing repo/PR info"}

    if not config.GH_PAT:
        return {"skipped": True, "reason": "GH_PAT not configured"}

    if not is_repo_allowed("github", full_name):
        return {"skipped": True, "reason": f"repo {full_name} not in whitelist"}

    logger.info("Reviewing PR %s/%s#%d (%s)", owner, repo, pr_number, action)

    diff = await fetch_pr_diff(owner, repo, pr_number)
    if not diff:
        return {"error": "failed to fetch diff"}

    analysis = await analyze_diff(diff, pr_title, pr_body)

    result = await post_review(
        owner, repo, pr_number, head_sha, analysis["body"], analysis["verdict"]
    )

    notify_text = (
        f"🔍 <b>Auto PR Review</b>\n\n"
        f"📦 {full_name}#{pr_number}\n"
        f"📝 {pr_title}\n"
        f"🏷️ Verdict: <b>{analysis['verdict']}</b>\n"
        f"💬 {analysis['summary']}"
    )
    await telegram.send_message(notify_text, parse_mode="HTML")

    return {
        "reviewed": True,
        "repo": full_name,
        "pr": pr_number,
        "verdict": analysis["verdict"],
        "review_id": result.get("id") if result else None,
    }


async def review_pr_on_demand(platform: str, full_name: str, pr_number: int) -> dict[str, Any]:
    owner, repo = full_name.split("/", 1) if "/" in full_name else ("", "")
    if not owner or not repo:
        return {"error": "invalid repo format, expected owner/repo"}

    if platform == "github":
        if not config.GH_PAT:
            return {"error": "GH_PAT not configured"}

        diff = await fetch_pr_diff(owner, repo, pr_number)
        if not diff:
            return {"error": "failed to fetch diff"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(
                f"{GH_API}/repos/{owner}/{repo}/pulls/{pr_number}",
                headers=_gh_headers(),
            )
        pr_title = ""
        pr_body = ""
        head_sha = ""
        if r.status_code == 200:
            pr_data = r.json()
            pr_title = pr_data.get("title", "")
            pr_body = pr_data.get("body") or ""
            head_sha = pr_data.get("head", {}).get("sha", "")

        analysis = await analyze_diff(diff, pr_title, pr_body)

        result = None
        if head_sha:
            result = await post_review(
                owner, repo, pr_number, head_sha, analysis["body"], analysis["verdict"]
            )

        notify_text = (
            f"🔍 <b>Auto PR Review (on-demand)</b>\n\n"
            f"📦 {full_name}#{pr_number}\n"
            f"📝 {pr_title}\n"
            f"🏷️ Verdict: <b>{analysis['verdict']}</b>\n"
            f"💬 {analysis['summary']}"
        )
        await telegram.send_message(notify_text, parse_mode="HTML")

        return {
            "reviewed": True,
            "repo": full_name,
            "pr": pr_number,
            "verdict": analysis["verdict"],
            "review_id": result.get("id") if result else None,
        }

    elif platform == "gitlab":
        from . import gitlab_review
        return await gitlab_review.review_mr_on_demand(full_name, pr_number)

    return {"error": f"unsupported platform: {platform}"}
