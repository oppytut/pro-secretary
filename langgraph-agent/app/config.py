import os

QDRANT_URL = os.getenv("QDRANT_URL", "").rstrip("/")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

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


def assert_ready() -> list[str]:
    missing = []
    if not QDRANT_URL:
        missing.append("QDRANT_URL")
    if not QDRANT_API_KEY:
        missing.append("QDRANT_API_KEY")
    if not LLM_API_KEY:
        missing.append("LLM_API_KEY")
    return missing
