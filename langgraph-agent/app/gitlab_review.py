from __future__ import annotations

import hashlib
import hmac as _hmac
import logging
from typing import Any
from urllib.parse import quote_plus

import httpx

from . import config, llm, pr_review, telegram

logger = logging.getLogger("agent.gitlab_review")

GL_API = "https://gitlab.com/api/v4"


def verify_webhook_token(token_header: str) -> bool:
    if not config.GITLAB_WEBHOOK_SECRET:
        return True
    if not token_header:
        return False
    return _hmac.compare_digest(token_header, config.GITLAB_WEBHOOK_SECRET)


def _gl_headers() -> dict[str, str]:
    return {"PRIVATE-TOKEN": config.GITLAB_PAT}


async def fetch_mr_diff(project_id: int, mr_iid: int) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                f"{GL_API}/projects/{project_id}/merge_requests/{mr_iid}/changes",
                headers=_gl_headers(),
            )
        if r.status_code == 200:
            data = r.json()
            changes = data.get("changes", [])
            diff_parts: list[str] = []
            for change in changes:
                diff_parts.append(f"--- a/{change.get('old_path', '')}")
                diff_parts.append(f"+++ b/{change.get('new_path', '')}")
                diff_parts.append(change.get("diff", ""))
            return "\n".join(diff_parts)
    except httpx.RequestError as exc:
        logger.error("Failed to fetch MR diff for project %d MR !%d: %s", project_id, mr_iid, exc)
    return None


async def post_mr_comment(project_id: int, mr_iid: int, body: str) -> dict[str, Any] | None:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(
                f"{GL_API}/projects/{project_id}/merge_requests/{mr_iid}/notes",
                headers=_gl_headers(),
                json={"body": body},
            )
        if r.status_code in (200, 201):
            return r.json()
        logger.error("Post MR comment failed %d: %s", r.status_code, r.text[:300])
    except httpx.RequestError as exc:
        logger.error("Post MR comment request error: %s", exc)
    return None


async def handle_mr_event(payload: dict[str, Any]) -> dict[str, Any]:
    attrs = payload.get("object_attributes", {})
    action = attrs.get("action", "")
    if action not in ("open", "reopen", "update"):
        return {"skipped": True, "reason": f"action={action} not reviewable"}

    if attrs.get("work_in_progress") or attrs.get("draft"):
        return {"skipped": True, "reason": "draft MR"}

    project = payload.get("project", {})
    project_id = project.get("id", 0)
    full_name = project.get("path_with_namespace", "")
    mr_iid = attrs.get("iid", 0)
    mr_title = attrs.get("title", "")
    mr_body = attrs.get("description") or ""

    if not project_id or not mr_iid:
        return {"skipped": True, "reason": "missing project/MR info"}

    if not config.GITLAB_PAT:
        return {"skipped": True, "reason": "GITLAB_PAT not configured"}

    if not pr_review.is_repo_allowed("gitlab", full_name):
        return {"skipped": True, "reason": f"repo {full_name} not in whitelist"}

    logger.info("Reviewing MR %s!%d (%s)", full_name, mr_iid, action)

    diff = await fetch_mr_diff(project_id, mr_iid)
    if not diff:
        return {"error": "failed to fetch MR diff"}

    analysis = await pr_review.analyze_diff(diff, mr_title, mr_body)

    result = await post_mr_comment(project_id, mr_iid, analysis["body"])

    notify_text = (
        f"🔍 <b>Auto MR Review</b>\n\n"
        f"📦 {full_name}!{mr_iid}\n"
        f"📝 {mr_title}\n"
        f"🏷️ Verdict: <b>{analysis['verdict']}</b>\n"
        f"💬 {analysis['summary']}"
    )
    await telegram.send_message(notify_text, parse_mode="HTML")

    return {
        "reviewed": True,
        "repo": full_name,
        "mr": mr_iid,
        "verdict": analysis["verdict"],
        "note_id": result.get("id") if result else None,
    }


async def review_mr_on_demand(full_name: str, mr_iid: int) -> dict[str, Any]:
    if not config.GITLAB_PAT:
        return {"error": "GITLAB_PAT not configured"}

    project_id_encoded = quote_plus(full_name)

    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{GL_API}/projects/{project_id_encoded}/merge_requests/{mr_iid}",
            headers=_gl_headers(),
        )
    if r.status_code != 200:
        return {"error": f"failed to fetch MR metadata: {r.status_code}"}

    mr_data = r.json()
    project_id = mr_data.get("project_id", 0)
    mr_title = mr_data.get("title", "")
    mr_body = mr_data.get("description") or ""

    diff = await fetch_mr_diff(project_id, mr_iid)
    if not diff:
        return {"error": "failed to fetch MR diff"}

    analysis = await pr_review.analyze_diff(diff, mr_title, mr_body)

    result = await post_mr_comment(project_id, mr_iid, analysis["body"])

    notify_text = (
        f"🔍 <b>Auto MR Review (on-demand)</b>\n\n"
        f"📦 {full_name}!{mr_iid}\n"
        f"📝 {mr_title}\n"
        f"🏷️ Verdict: <b>{analysis['verdict']}</b>\n"
        f"💬 {analysis['summary']}"
    )
    await telegram.send_message(notify_text, parse_mode="HTML")

    return {
        "reviewed": True,
        "repo": full_name,
        "mr": mr_iid,
        "verdict": analysis["verdict"],
        "note_id": result.get("id") if result else None,
    }
