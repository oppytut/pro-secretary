import logging
import os
from pathlib import Path

QDRANT_URL = os.getenv("QDRANT_URL", "").rstrip("/")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

if LLM_BASE_URL and not LLM_BASE_URL.startswith(("https://", "http://localhost", "http://127.")):
    logging.getLogger("agent").warning(
        "LLM_BASE_URL=%s is not HTTPS and not loopback; API key will transit in cleartext",
        LLM_BASE_URL,
    )

CALCOM_API_KEY = os.getenv("CALCOM_API_KEY", "")
CALCOM_BASE_URL = os.getenv("CALCOM_BASE_URL", "http://calcom:3000").rstrip("/")

AGENT_SECRET = os.getenv("AGENT_SECRET", "")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Jakarta")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ALLOWED_USERS = [
    x.strip() for x in os.getenv("TELEGRAM_ALLOWED_USERS", "").split(",") if x.strip()
]

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DIM = 384

# Collection names must match scripts/init_qdrant.py and scripts/sync_obsidian.py.
# Drift here silently corrupts queries (writes succeed, search misses).
COLL_KNOWLEDGE = "knowledge"
COLL_MEMORY = "agent_memory"
COLL_TASKS = "tasks"
COLL_PEOPLE = "people"
COLL_DECISIONS = "decisions"
COLL_CODE = "code_chunks"

GH_PAT = os.getenv("GH_PAT", "")
GITLAB_PAT = os.getenv("GITLAB_PAT", "")
REPO_BASE_DIR = Path(os.getenv("REPO_BASE_DIR", "/repos"))
REPOS_CONFIG_PATH = Path(os.getenv("REPOS_CONFIG_PATH", "/app/repos.yml"))

RESOURCE_ALERT_STATE_FILE = Path(
    os.getenv("RESOURCE_ALERT_STATE_FILE", "/app/state/resource-alert-state.json")
)
RESOURCE_DISK_WARN_PCT = float(os.getenv("RESOURCE_DISK_WARN_PCT", "80"))
RESOURCE_DISK_CRIT_PCT = float(os.getenv("RESOURCE_DISK_CRIT_PCT", "90"))
RESOURCE_MEM_WARN_PCT = float(os.getenv("RESOURCE_MEM_WARN_PCT", "85"))
RESOURCE_MEM_CRIT_PCT = float(os.getenv("RESOURCE_MEM_CRIT_PCT", "92"))
RESOURCE_MEM_SUSTAINED_MINUTES = int(os.getenv("RESOURCE_MEM_SUSTAINED_MINUTES", "30"))
RESOURCE_SWAP_WARN_PCT = float(os.getenv("RESOURCE_SWAP_WARN_PCT", "50"))
RESOURCE_SWAP_CRIT_PCT = float(os.getenv("RESOURCE_SWAP_CRIT_PCT", "70"))
RESOURCE_QDRANT_WARN_POINTS = int(os.getenv("RESOURCE_QDRANT_WARN_POINTS", "800000"))
RESOURCE_QDRANT_CRIT_POINTS = int(os.getenv("RESOURCE_QDRANT_CRIT_POINTS", "950000"))
RESOURCE_POSTGRES_CONNECT_TIMEOUT_SEC = int(os.getenv("RESOURCE_POSTGRES_CONNECT_TIMEOUT_SEC", "5"))


def assert_ready() -> list[str]:
    missing = []
    if not QDRANT_URL:
        missing.append("QDRANT_URL")
    if not QDRANT_API_KEY:
        missing.append("QDRANT_API_KEY")
    if not LLM_API_KEY:
        missing.append("LLM_API_KEY")
    if not AGENT_SECRET:
        missing.append("AGENT_SECRET")
    return missing
