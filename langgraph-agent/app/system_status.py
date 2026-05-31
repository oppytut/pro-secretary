from __future__ import annotations

import asyncio
import os
import socket
import time
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from . import config, qdrant_helper

R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_ENDPOINT = os.getenv("R2_ENDPOINT", "")
R2_BUCKET = os.getenv("R2_BUCKET", "")

DATABASE_URL = os.getenv("DATABASE_URL", "")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587") or "587")

VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "/vault")

VAULT_INTERNAL = "http://langgraph-agent:8090/health"
N8N_INTERNAL = "http://n8n:5678/healthz"
CALCOM_INTERNAL = "http://calcom:3000/"
LLM_TUNNEL_HOST = "host.docker.internal"
LLM_TUNNEL_PORT = 20128


def _now_ms() -> float:
    return time.monotonic() * 1000


async def _http_check(name: str, url: str, headers: dict | None = None, timeout: float = 8.0) -> dict:
    start = _now_ms()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url, headers=headers)
        latency = round(_now_ms() - start)
        ok = 200 <= r.status_code < 400
        return {"name": name, "ok": ok, "latency_ms": latency, "detail": f"HTTP {r.status_code}"}
    except (httpx.RequestError, httpx.HTTPError) as exc:
        latency = round(_now_ms() - start)
        return {"name": name, "ok": False, "latency_ms": latency, "detail": type(exc).__name__}


async def check_agent() -> dict:
    return await _http_check("langgraph-agent", VAULT_INTERNAL)


async def check_n8n() -> dict:
    return await _http_check("n8n", N8N_INTERNAL)


async def check_calcom() -> dict:
    return await _http_check("calcom", CALCOM_INTERNAL)


async def check_qdrant() -> dict:
    start = _now_ms()
    try:
        client = qdrant_helper.get_client()
        collections = await asyncio.to_thread(lambda: client.get_collections().collections)
        latency = round(_now_ms() - start)
        return {
            "name": "qdrant",
            "ok": True,
            "latency_ms": latency,
            "detail": f"{len(collections)} collections",
        }
    except Exception as exc:
        latency = round(_now_ms() - start)
        return {"name": "qdrant", "ok": False, "latency_ms": latency, "detail": type(exc).__name__}


async def check_llm() -> dict:
    if not config.LLM_BASE_URL or not config.LLM_API_KEY:
        return {"name": "llm", "ok": False, "latency_ms": 0, "detail": "not configured"}
    start = _now_ms()
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                f"{config.LLM_BASE_URL}/models",
                headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
            )
        latency = round(_now_ms() - start)
        ok = r.status_code == 200
        return {
            "name": "llm",
            "ok": ok,
            "latency_ms": latency,
            "detail": config.LLM_MODEL if ok else f"HTTP {r.status_code}",
        }
    except (httpx.RequestError, httpx.HTTPError) as exc:
        latency = round(_now_ms() - start)
        return {"name": "llm", "ok": False, "latency_ms": latency, "detail": type(exc).__name__}


async def check_postgres() -> dict:
    if not DATABASE_URL:
        return {"name": "postgres", "ok": False, "latency_ms": 0, "detail": "DATABASE_URL not set"}

    def _probe() -> tuple[bool, int, str]:
        start = _now_ms()
        try:
            import psycopg

            with psycopg.connect(DATABASE_URL, connect_timeout=8) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            return True, round(_now_ms() - start), "ok"
        except Exception as exc:
            return False, round(_now_ms() - start), type(exc).__name__

    ok, latency, detail = await asyncio.to_thread(_probe)
    return {"name": "postgres", "ok": ok, "latency_ms": latency, "detail": detail}


async def check_r2() -> dict:
    if not all([R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_ENDPOINT, R2_BUCKET]):
        return {"name": "r2", "ok": False, "latency_ms": 0, "detail": "not configured"}

    def _probe() -> tuple[bool, int, str]:
        start = _now_ms()
        try:
            import boto3
            from botocore.config import Config

            s3 = boto3.client(
                "s3",
                endpoint_url=R2_ENDPOINT,
                aws_access_key_id=R2_ACCESS_KEY_ID,
                aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                region_name="auto",
                config=Config(connect_timeout=5, read_timeout=8, retries={"max_attempts": 1}),
            )
            s3.head_bucket(Bucket=R2_BUCKET)
            return True, round(_now_ms() - start), R2_BUCKET
        except Exception as exc:
            return False, round(_now_ms() - start), type(exc).__name__

    ok, latency, detail = await asyncio.to_thread(_probe)
    return {"name": "r2", "ok": ok, "latency_ms": latency, "detail": detail}


async def check_smtp() -> dict:
    if not SMTP_HOST:
        return {"name": "smtp", "ok": False, "latency_ms": 0, "detail": "SMTP_HOST not set"}

    def _probe() -> tuple[bool, int, str]:
        start = _now_ms()
        try:
            with socket.create_connection((SMTP_HOST, SMTP_PORT), timeout=5):
                return True, round(_now_ms() - start), f"{SMTP_HOST}:{SMTP_PORT}"
        except OSError as exc:
            return False, round(_now_ms() - start), type(exc).__name__

    ok, latency, detail = await asyncio.to_thread(_probe)
    return {"name": "smtp", "ok": ok, "latency_ms": latency, "detail": detail}


async def check_llm_tunnel() -> dict:
    start = _now_ms()
    try:
        await asyncio.to_thread(
            lambda: socket.create_connection((LLM_TUNNEL_HOST, LLM_TUNNEL_PORT), timeout=5).close()
        )
        latency = round(_now_ms() - start)
        return {
            "name": "llm-tunnel",
            "ok": True,
            "latency_ms": latency,
            "detail": f"{LLM_TUNNEL_HOST}:{LLM_TUNNEL_PORT}",
        }
    except OSError as exc:
        latency = round(_now_ms() - start)
        return {"name": "llm-tunnel", "ok": False, "latency_ms": latency, "detail": type(exc).__name__}


async def check_obsidian() -> dict:
    def _probe() -> tuple[bool, int, str]:
        start = _now_ms()
        try:
            from pathlib import Path

            root = Path(VAULT_PATH)
            if not root.exists():
                return False, 0, "vault path missing"
            files = [f for f in root.rglob("*.md") if "Templates" not in f.parts]
            return True, round(_now_ms() - start), f"{len(files)} files"
        except Exception as exc:
            return False, 0, type(exc).__name__

    ok, latency, detail = await asyncio.to_thread(_probe)

    last_sync = "unknown"
    try:
        client = qdrant_helper.get_client()
        from qdrant_client.http import models as qmodels

        points, _ = await asyncio.to_thread(
            lambda: client.scroll(
                collection_name=config.COLL_KNOWLEDGE,
                scroll_filter=qmodels.Filter(
                    must=[
                        qmodels.FieldCondition(
                            key="source", match=qmodels.MatchValue(value="obsidian")
                        )
                    ]
                ),
                limit=1,
                with_payload=True,
            )
        )
        if points:
            last_sync = points[0].payload.get("synced_at", "unknown")
            if last_sync != "unknown":
                try:
                    dt = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
                    last_sync = dt.astimezone(ZoneInfo(config.TIMEZONE)).strftime(
                        "%H:%M %Z"
                    )
                except (ValueError, TypeError):
                    last_sync = last_sync.split("T")[1][:5] + " UTC"
    except Exception:
        pass

    full_detail = detail if not ok else f"{detail}, last sync {last_sync}"
    return {"name": "obsidian", "ok": ok, "latency_ms": latency, "detail": full_detail}


async def collect_all() -> dict[str, Any]:
    checks = await asyncio.gather(
        check_agent(),
        check_n8n(),
        check_calcom(),
        check_qdrant(),
        check_llm(),
        check_llm_tunnel(),
        check_postgres(),
        check_r2(),
        check_smtp(),
        check_obsidian(),
        return_exceptions=False,
    )
    failed = sum(1 for c in checks if not c["ok"])
    return {
        "ok": failed == 0,
        "total": len(checks),
        "failed": failed,
        "checks": checks,
    }
