from __future__ import annotations

import json
import logging
import re
import tomllib
from pathlib import Path
from typing import Any

import httpx

from . import code_repos

logger = logging.getLogger("agent.deps_watchdog")

OSV_API_URL = "https://api.osv.dev/v1/querybatch"
GHSA_DETAIL_URL = "https://api.osv.dev/v1/vulns"

# OSV batch limit per request; conservatively chunk below 1000 to stay safe.
_BATCH_SIZE = 100
_HTTP_TIMEOUT = 30.0
_MAX_PACKAGES_PER_REPO = 500
_SEVERITY_ORDER = {"CRITICAL": 4, "HIGH": 3, "MODERATE": 2, "MEDIUM": 2, "LOW": 1, "UNKNOWN": 0}

_NPM_VERSION_CLEAN_RE = re.compile(r"^[\^~>=<]+\s*")


def _strip_npm_range(spec: str) -> str | None:
    if not spec or not isinstance(spec, str):
        return None
    spec = spec.strip()
    if spec.startswith(("git", "http", "file:", "link:", "workspace:", "npm:")):
        return None
    if "||" in spec or " - " in spec:
        return None
    cleaned = _NPM_VERSION_CLEAN_RE.sub("", spec).strip()
    if not re.match(r"^\d+\.\d+(\.\d+)?", cleaned):
        return None
    return cleaned.split()[0]


def _parse_package_json(path: Path) -> list[dict[str, str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    pkgs: list[dict[str, str]] = []
    for section in ("dependencies", "devDependencies", "optionalDependencies"):
        deps = data.get(section) or {}
        if not isinstance(deps, dict):
            continue
        for name, spec in deps.items():
            version = _strip_npm_range(str(spec))
            if not version:
                continue
            pkgs.append({"name": name, "version": version, "ecosystem": "npm"})
    return pkgs


def _parse_package_lock(path: Path) -> list[dict[str, str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    pkgs: list[dict[str, str]] = []
    # npm lockfile v2/v3 uses "packages" with empty key for root.
    packages = data.get("packages") or {}
    if isinstance(packages, dict) and packages:
        for key, info in packages.items():
            if not key or not isinstance(info, dict):
                continue
            name = info.get("name")
            if not name:
                # Path key like "node_modules/foo" -> derive name.
                parts = key.split("node_modules/")
                if len(parts) > 1:
                    name = parts[-1]
            version = info.get("version")
            if name and version and isinstance(version, str):
                pkgs.append({"name": name, "version": version, "ecosystem": "npm"})
        return pkgs
    deps = data.get("dependencies") or {}
    if isinstance(deps, dict):
        for name, info in deps.items():
            if isinstance(info, dict) and info.get("version"):
                pkgs.append({"name": name, "version": info["version"], "ecosystem": "npm"})
    return pkgs


_PIP_LINE_RE = re.compile(r"^([A-Za-z0-9_.\-\[\]]+)\s*==\s*([A-Za-z0-9_.+\-]+)")


def _parse_requirements_txt(path: Path) -> list[dict[str, str]]:
    pkgs: list[dict[str, str]] = []
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line or line.startswith("-"):
                continue
            m = _PIP_LINE_RE.match(line)
            if not m:
                continue
            name = m.group(1).split("[")[0].strip()
            version = m.group(2).strip()
            pkgs.append({"name": name, "version": version, "ecosystem": "PyPI"})
    except Exception:
        return []
    return pkgs


def _parse_pyproject(path: Path) -> list[dict[str, str]]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    pkgs: list[dict[str, str]] = []
    poetry = (data.get("tool") or {}).get("poetry") or {}
    for section in ("dependencies", "dev-dependencies"):
        deps = poetry.get(section) or {}
        if not isinstance(deps, dict):
            continue
        for name, spec in deps.items():
            if name.lower() == "python":
                continue
            version = spec if isinstance(spec, str) else (spec.get("version") if isinstance(spec, dict) else None)
            cleaned = _strip_npm_range(str(version)) if version else None
            if cleaned:
                pkgs.append({"name": name, "version": cleaned, "ecosystem": "PyPI"})
    return pkgs


def _parse_composer_lock(path: Path) -> list[dict[str, str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    pkgs: list[dict[str, str]] = []
    for section in ("packages", "packages-dev"):
        for entry in data.get(section) or []:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name")
            version = entry.get("version")
            if name and version and isinstance(version, str):
                clean = version.lstrip("v")
                pkgs.append({"name": name, "version": clean, "ecosystem": "Packagist"})
    return pkgs


def _parse_go_mod(path: Path) -> list[dict[str, str]]:
    pkgs: list[dict[str, str]] = []
    try:
        in_require = False
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if line.startswith("require ("):
                in_require = True
                continue
            if in_require and line == ")":
                in_require = False
                continue
            if in_require or line.startswith("require "):
                clean = line.removeprefix("require ").strip()
                if not clean or clean.startswith("//"):
                    continue
                parts = clean.split()
                if len(parts) >= 2:
                    pkgs.append({"name": parts[0], "version": parts[1].lstrip("v"), "ecosystem": "Go"})
    except Exception:
        return []
    return pkgs


_PARSERS: dict[str, Any] = {
    "package-lock.json": _parse_package_lock,
    "package.json": _parse_package_json,
    "requirements.txt": _parse_requirements_txt,
    "pyproject.toml": _parse_pyproject,
    "composer.lock": _parse_composer_lock,
    "go.mod": _parse_go_mod,
}

_SCAN_SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", "__pycache__", ".venv", "venv"}


def _collect_manifests(repo_path: Path) -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    seen_dirs_with_lock: set[Path] = set()
    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SCAN_SKIP_DIRS for part in path.parts):
            continue
        if path.name in _PARSERS:
            found.append((path.name, path))
            if path.name == "package-lock.json":
                seen_dirs_with_lock.add(path.parent)
    # Prefer lockfile over manifest for npm; drop package.json if sibling lock exists.
    return [(name, p) for name, p in found if not (name == "package.json" and p.parent in seen_dirs_with_lock)]


def _dedupe(pkgs: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    out: list[dict[str, str]] = []
    for p in pkgs:
        key = (p["ecosystem"], p["name"], p["version"])
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


async def _query_osv_batch(packages: list[dict[str, str]]) -> list[list[dict[str, Any]]]:
    queries = [
        {"package": {"name": p["name"], "ecosystem": p["ecosystem"]}, "version": p["version"]}
        for p in packages
    ]
    async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
        r = await client.post(OSV_API_URL, json={"queries": queries})
    r.raise_for_status()
    data = r.json()
    raw_results = data.get("results") or []
    out: list[list[dict[str, Any]]] = []
    for item in raw_results:
        if isinstance(item, dict) and isinstance(item.get("vulns"), list):
            out.append(item["vulns"])
        else:
            out.append([])
    while len(out) < len(packages):
        out.append([])
    return out


async def _fetch_vuln_detail(vuln_id: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            r = await client.get(f"{GHSA_DETAIL_URL}/{vuln_id}")
        if r.status_code == 200:
            return r.json()
    except Exception:
        logger.warning("vuln detail fetch failed for %s", vuln_id)
    return {}


def _severity_from_detail(detail: dict[str, Any]) -> str:
    db_specific = detail.get("database_specific") or {}
    if isinstance(db_specific, dict) and db_specific.get("severity"):
        return str(db_specific["severity"]).upper()
    severities = detail.get("severity") or []
    if isinstance(severities, list):
        for s in severities:
            if isinstance(s, dict) and s.get("score"):
                score = str(s["score"])
                if score.startswith("CVSS:") or "/" in score:
                    return "HIGH"  # heuristic; real parse needs CVSS lib.
                return score.upper()
    return "UNKNOWN"


async def scan_packages(packages: list[dict[str, str]]) -> list[dict[str, Any]]:
    if not packages:
        return []
    findings: list[dict[str, Any]] = []
    seen_vuln_ids: set[str] = set()

    for i in range(0, len(packages), _BATCH_SIZE):
        batch = packages[i : i + _BATCH_SIZE]
        try:
            results = await _query_osv_batch(batch)
        except Exception:
            logger.exception("OSV batch query failed (offset=%d)", i)
            continue

        for pkg, vulns in zip(batch, results, strict=False):
            for v in vulns:
                vuln_id = v.get("id")
                if not vuln_id or vuln_id in seen_vuln_ids:
                    continue
                seen_vuln_ids.add(vuln_id)
                findings.append(
                    {
                        "vuln_id": vuln_id,
                        "package": pkg["name"],
                        "ecosystem": pkg["ecosystem"],
                        "version": pkg["version"],
                        "severity": "UNKNOWN",
                        "summary": "",
                    }
                )

    # Enrich with severity + summary (only for first 30 to avoid rate limits).
    for finding in findings[:30]:
        detail = await _fetch_vuln_detail(finding["vuln_id"])
        if detail:
            finding["severity"] = _severity_from_detail(detail)
            finding["summary"] = (detail.get("summary") or "")[:200]

    findings.sort(
        key=lambda f: (-_SEVERITY_ORDER.get(f["severity"], 0), f["package"]),
    )
    return findings


def collect_packages_from_repo(repo_path: Path) -> list[dict[str, str]]:
    all_pkgs: list[dict[str, str]] = []
    for filename, path in _collect_manifests(repo_path):
        parser = _PARSERS[filename]
        try:
            all_pkgs.extend(parser(path))
        except Exception:
            logger.exception("parser failed for %s", path)
        if len(all_pkgs) >= _MAX_PACKAGES_PER_REPO:
            break
    return _dedupe(all_pkgs)[:_MAX_PACKAGES_PER_REPO]


async def scan_repo(repo_id: str) -> dict[str, Any]:
    repo = code_repos.get_repo(repo_id)
    if repo is None:
        return {"ok": False, "error": "unknown repo", "repo_id": repo_id}

    try:
        repo_path = code_repos._sync_repo(repo)
    except Exception as exc:
        logger.exception("repo sync failed")
        return {"ok": False, "error": f"sync failed: {exc}", "repo_id": repo_id}

    packages = collect_packages_from_repo(repo_path)
    findings = await scan_packages(packages)

    by_severity: dict[str, int] = {}
    for f in findings:
        by_severity[f["severity"]] = by_severity.get(f["severity"], 0) + 1

    return {
        "ok": True,
        "repo_id": repo.id,
        "repo_name": repo.name,
        "packages_scanned": len(packages),
        "vulns_found": len(findings),
        "by_severity": by_severity,
        "findings": findings[:50],
    }


async def scan_all_repos() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for repo in code_repos.load_repos():
        if not repo.enabled:
            continue
        try:
            result = await scan_repo(repo.id)
        except Exception as exc:
            logger.exception("scan_repo failed for %s", repo.id)
            result = {"ok": False, "repo_id": repo.id, "error": str(exc)}
        results.append(result)
    return results


def format_report(results: list[dict[str, Any]]) -> str:
    lines: list[str] = ["🛡️ <b>Dependency Watchdog</b>", ""]
    total_vulns = 0
    total_repos = 0
    repos_with_issues: list[dict[str, Any]] = []

    for r in results:
        if not r.get("ok"):
            lines.append(f"⚠️ {r.get('repo_id')}: {r.get('error', 'failed')}")
            continue
        total_repos += 1
        total_vulns += r.get("vulns_found", 0)
        if r.get("vulns_found", 0) > 0:
            repos_with_issues.append(r)

    lines.append(f"📊 Scanned: {total_repos} repo, {total_vulns} vuln total")
    lines.append("")

    if not repos_with_issues:
        lines.append("✅ Tidak ada vulnerability terdeteksi.")
        return "\n".join(lines)

    for r in repos_with_issues:
        sev_str = " · ".join(f"{k}:{v}" for k, v in sorted(r["by_severity"].items()))
        lines.append(f"📦 <b>{r['repo_name']}</b> — {r['packages_scanned']} pkg, {r['vulns_found']} vuln")
        lines.append(f"   {sev_str}")
        for f in r["findings"][:5]:
            sev = f["severity"]
            badge = {"CRITICAL": "🔴", "HIGH": "🟠", "MODERATE": "🟡", "MEDIUM": "🟡", "LOW": "🟢"}.get(sev, "⚪")
            lines.append(f"   {badge} [{sev}] {f['package']}@{f['version']} → {f['vuln_id']}")
            if f.get("summary"):
                lines.append(f"      {f['summary'][:120]}")
        if len(r["findings"]) > 5:
            lines.append(f"   ... +{len(r['findings']) - 5} more")
        lines.append("")

    return "\n".join(lines).strip()
