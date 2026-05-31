from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

import httpx

from . import config, llm, telegram

logger = logging.getLogger(__name__)

GH_API = "https://api.github.com"
_WHITELIST_FILE = Path("/app/state/coverage_repos.json")

COVERAGE_TARGET = float(os.getenv("COVERAGE_TARGET", "80"))
COVERAGE_MIN_LINES = int(os.getenv("COVERAGE_MIN_LINES", "10"))
COVERAGE_MAX_LINES = int(os.getenv("COVERAGE_MAX_LINES", "400"))
COVERAGE_SCAN_TIMEOUT = int(os.getenv("COVERAGE_SCAN_TIMEOUT_SEC", "300"))
COVERAGE_PYTEST_CMD = os.getenv("COVERAGE_PYTEST_CMD", "python3 -m pytest --cov --cov-report=json")

_GENERATE_TESTS_SYSTEM_PROMPT = (
    "You are a senior Python test engineer. Given a source file with low coverage and "
    "a list of uncovered line numbers, write a single pytest test module that covers "
    "the missing lines.\n\n"
    "Rules:\n"
    "- Match the existing test style shown in the sample tests.\n"
    "- Use pytest fixtures, monkeypatch, tmp_path where appropriate.\n"
    "- Mock external I/O (network, subprocess, filesystem outside tmp_path).\n"
    "- Test only the public surface unless private functions are critical.\n"
    "- One test class per logical unit. Tests must be deterministic.\n"
    "- Output ONLY a complete Python test module. No explanations, no markdown fences.\n"
    "- Start with: from __future__ import annotations\n"
    "- Import the module under test by relative path (will be wired by caller).\n"
    "- All tests must pass when the source file is unchanged."
)

_MAX_SOURCE_CHARS = 6000
_MAX_SAMPLE_CHARS = 3000


def get_whitelist() -> list[str]:
    if _WHITELIST_FILE.exists():
        try:
            data = json.loads(_WHITELIST_FILE.read_text())
            if isinstance(data, list):
                return [str(item) for item in data]
        except Exception:
            pass
    return []


def set_whitelist(repos: list[str]) -> None:
    _WHITELIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    _WHITELIST_FILE.write_text(json.dumps(repos, indent=2))


def is_repo_allowed(full_name: str) -> bool:
    whitelist = get_whitelist()
    if not whitelist:
        return False
    return full_name in whitelist


async def _run(cmd: list[str], cwd: str | None = None, timeout: int = 60) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return 124, "", f"timeout after {timeout}s"
    return proc.returncode or 0, stdout.decode(errors="replace"), stderr.decode(errors="replace")


async def clone_repo(full_name: str, dest: str, branch: str = "main") -> bool:
    if not config.GH_PAT:
        logger.error("GH_PAT not set, cannot clone")
        return False
    url = f"https://x-access-token:{config.GH_PAT}@github.com/{full_name}.git"
    rc, _, stderr = await _run(
        ["git", "clone", "--depth", "1", "--branch", branch, url, dest],
        timeout=120,
    )
    if rc != 0:
        logger.error("Clone %s failed: %s", full_name, stderr[:300])
        return False
    return True


async def run_coverage(repo_dir: str) -> dict[str, Any] | None:
    cmd = COVERAGE_PYTEST_CMD.split() + ["--cov-report=json:coverage.json"]
    rc, stdout, stderr = await _run(
        cmd,
        cwd=repo_dir,
        timeout=COVERAGE_SCAN_TIMEOUT,
    )
    cov_path = Path(repo_dir) / "coverage.json"
    if not cov_path.exists():
        logger.error("coverage.json not produced (rc=%d): %s", rc, (stderr or stdout)[:300])
        return None
    try:
        result: dict[str, Any] = json.loads(cov_path.read_text())
        return result
    except Exception as exc:
        logger.error("Failed to parse coverage.json: %s", exc)
        return None


def pick_lowest_coverage_file(coverage_data: dict[str, Any]) -> dict[str, Any] | None:
    files = coverage_data.get("files", {})
    candidates: list[dict[str, Any]] = []
    for path, entry in files.items():
        summary = entry.get("summary", {})
        num_statements = summary.get("num_statements", 0)
        if num_statements < COVERAGE_MIN_LINES or num_statements > COVERAGE_MAX_LINES:
            continue
        percent = summary.get("percent_covered", 100.0)
        if percent >= COVERAGE_TARGET:
            continue
        if "/test" in path or path.startswith("test") or "conftest" in path:
            continue
        missing = entry.get("missing_lines", [])
        candidates.append({
            "path": path,
            "percent": percent,
            "num_statements": num_statements,
            "missing_lines": missing,
        })
    if not candidates:
        return None
    candidates.sort(key=lambda c: (c["percent"], -c["num_statements"]))
    return candidates[0]


def find_sample_tests(repo_dir: str, limit: int = 2) -> str:
    samples: list[str] = []
    test_dir = Path(repo_dir) / "tests"
    if not test_dir.is_dir():
        test_dir = Path(repo_dir)
    for test_file in sorted(test_dir.rglob("test_*.py")):
        try:
            content = test_file.read_text(errors="replace")
        except Exception:
            continue
        if len(content) < 200 or len(content) > _MAX_SAMPLE_CHARS:
            continue
        samples.append(f"# --- {test_file.relative_to(repo_dir)} ---\n{content}")
        if len(samples) >= limit:
            break
    return "\n\n".join(samples)


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        first_nl = text.find("\n")
        if first_nl != -1:
            text = text[first_nl + 1 :]
        if text.endswith("```"):
            text = text[: -3]
    return text.strip()


async def generate_tests(
    source_path: str,
    source_content: str,
    missing_lines: list[int],
    sample_tests: str,
) -> str:
    truncated_source = source_content[:_MAX_SOURCE_CHARS]
    user_message = (
        f"SOURCE FILE: {source_path}\n"
        f"UNCOVERED LINES: {missing_lines[:60]}\n\n"
        f"SOURCE:\n```python\n{truncated_source}\n```\n\n"
        f"SAMPLE EXISTING TESTS (match this style):\n{sample_tests[:_MAX_SAMPLE_CHARS]}\n\n"
        f"Write a complete pytest test module covering the uncovered lines."
    )
    response = await llm.chat_completion(
        messages=[
            {"role": "system", "content": _GENERATE_TESTS_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=4000,
    )
    return _strip_code_fences(response)


async def verify_tests(repo_dir: str, test_file_rel: str) -> tuple[bool, str]:
    rc, stdout, stderr = await _run(
        ["python3", "-m", "pytest", "-q", "--no-cov", test_file_rel],
        cwd=repo_dir,
        timeout=120,
    )
    if rc == 0:
        return True, stdout[-500:]
    return False, (stderr or stdout)[-500:]


async def _gh_post(path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any] | None]:
    headers = {
        "Authorization": f"Bearer {config.GH_PAT}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{GH_API}{path}", headers=headers, json=payload)
        if r.status_code in (200, 201):
            return r.status_code, r.json()
        logger.error("gh POST %s failed %d: %s", path, r.status_code, r.text[:200])
        return r.status_code, None
    except httpx.RequestError as exc:
        logger.error("gh POST %s request error: %s", path, exc)
        return 0, None


async def open_pr(
    full_name: str,
    repo_dir: str,
    test_file_rel: str,
    target_path: str,
    coverage_pct: float,
    base: str = "main",
) -> dict[str, Any]:
    slug = re.sub(r"[^a-z0-9]+", "-", target_path.lower()).strip("-")[:50]
    branch = f"coverage/{slug}-{int(time.time())}"

    rc, _, stderr = await _run(
        ["git", "checkout", "-b", branch], cwd=repo_dir, timeout=30
    )
    if rc != 0:
        return {"ok": False, "error": f"checkout failed: {stderr[:200]}"}

    rc, _, stderr = await _run(
        ["git", "config", "user.email", "coverage-bot@pro-secretary"],
        cwd=repo_dir,
        timeout=10,
    )
    rc, _, stderr = await _run(
        ["git", "config", "user.name", "Coverage Bot"], cwd=repo_dir, timeout=10
    )

    rc, _, stderr = await _run(
        ["git", "add", test_file_rel], cwd=repo_dir, timeout=15
    )
    if rc != 0:
        return {"ok": False, "error": f"git add failed: {stderr[:200]}"}

    msg = f"test: add coverage tests for {target_path} ({coverage_pct:.0f}% covered)"
    rc, _, stderr = await _run(
        ["git", "commit", "-m", msg], cwd=repo_dir, timeout=15
    )
    if rc != 0:
        return {"ok": False, "error": f"git commit failed: {stderr[:200]}"}

    rc, _, stderr = await _run(
        ["git", "push", "-u", "origin", branch], cwd=repo_dir, timeout=60
    )
    if rc != 0:
        return {"ok": False, "error": f"git push failed: {stderr[:200]}"}

    title = f"test: coverage tests for {target_path}"
    body = (
        f"Auto-generated tests for `{target_path}` "
        f"(currently {coverage_pct:.1f}% covered).\n\n"
        f"Generated by pro-secretary Test Coverage Agent. "
        f"Tests verified locally before opening this PR.\n\n"
        f"Review carefully — LLM-generated tests may need cleanup."
    )
    status, data = await _gh_post(
        f"/repos/{full_name}/pulls",
        {"title": title, "body": body, "head": branch, "base": base},
    )
    if status not in (200, 201) or not data:
        return {"ok": False, "error": f"create PR failed: HTTP {status}"}
    return {"ok": True, "pr_url": data.get("html_url"), "pr_number": data.get("number"), "branch": branch}


async def has_open_coverage_pr(full_name: str, target_path: str) -> bool:
    headers = {
        "Authorization": f"Bearer {config.GH_PAT}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(
                f"{GH_API}/repos/{full_name}/pulls?state=open&per_page=30",
                headers=headers,
            )
        if r.status_code != 200:
            return False
        prs = r.json()
        if not isinstance(prs, list):
            return False
        slug = target_path.lower()
        for pr in prs:
            title = (pr.get("title") or "").lower()
            head_ref = ((pr.get("head") or {}).get("ref") or "").lower()
            if slug in title or slug.replace("/", "-") in head_ref:
                return True
        return False
    except httpx.RequestError:
        return False


async def scan_and_pr(full_name: str, branch: str = "main", min_coverage: float | None = None) -> dict[str, Any]:
    if not is_repo_allowed(full_name):
        return {"ok": False, "error": f"repo {full_name} not in coverage whitelist"}

    target_pct = min_coverage if min_coverage is not None else COVERAGE_TARGET

    workdir = tempfile.mkdtemp(prefix="cov_")
    try:
        if not await clone_repo(full_name, workdir, branch=branch):
            return {"ok": False, "error": "clone failed"}

        coverage_data = await run_coverage(workdir)
        if not coverage_data:
            return {"ok": False, "error": "coverage scan failed"}

        original_target = COVERAGE_TARGET
        try:
            globals()["COVERAGE_TARGET"] = target_pct
            picked = pick_lowest_coverage_file(coverage_data)
        finally:
            globals()["COVERAGE_TARGET"] = original_target

        if not picked:
            return {"ok": True, "skipped": True, "reason": "no files below threshold"}

        target_path = picked["path"]

        if await has_open_coverage_pr(full_name, target_path):
            return {
                "ok": True,
                "skipped": True,
                "reason": f"open coverage PR already exists for {target_path}",
                "lowest": target_path,
                "coverage": picked["percent"],
            }

        source_file = Path(workdir) / target_path
        if not source_file.exists():
            return {"ok": False, "error": f"source file {target_path} not found"}
        source_content = source_file.read_text(errors="replace")

        sample_tests = find_sample_tests(workdir)
        test_code = await generate_tests(
            target_path,
            source_content,
            picked["missing_lines"],
            sample_tests,
        )

        if not test_code or "def test_" not in test_code:
            return {"ok": False, "error": "LLM produced no valid test code"}

        basename = Path(target_path).stem
        tests_dir = Path(workdir) / "tests"
        tests_dir.mkdir(exist_ok=True)
        test_file = tests_dir / f"test_{basename}_coverage.py"
        test_file.write_text(test_code)
        test_file_rel = str(test_file.relative_to(workdir))

        ok, output = await verify_tests(workdir, test_file_rel)
        if not ok:
            logger.warning("Generated tests failed: %s", output)
            return {"ok": False, "error": f"generated tests failed verification: {output[:200]}"}

        pr_result = await open_pr(
            full_name, workdir, test_file_rel, target_path, picked["percent"], base=branch
        )
        if not pr_result["ok"]:
            return {"ok": False, "error": pr_result["error"], "lowest": target_path}

        notify = (
            f"📊 <b>Coverage Agent</b>\n\n"
            f"📦 {full_name}\n"
            f"🎯 {target_path} ({picked['percent']:.1f}%)\n"
            f"🔧 PR #{pr_result['pr_number']}: {pr_result['pr_url']}"
        )
        await telegram.send_message(notify, parse_mode="HTML")

        return {
            "ok": True,
            "scanned": True,
            "lowest": target_path,
            "coverage": picked["percent"],
            "pr_url": pr_result["pr_url"],
            "pr_number": pr_result["pr_number"],
            "branch": pr_result["branch"],
        }
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
