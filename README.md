# 🤖 AI Personal Secretary Stack

> Sistem asisten pribadi AI self-hosted yang tahu semua pekerjaan Anda — berjalan 24/7, privasi terjaga, kontrol penuh di tangan Anda.

## 📐 Architecture

    ┌────────────────────┐
    │           USER INTERFACE            │
    │        Telegram / Matrix Bot        │
    └────────────┬────────────────────┘
                     │
    ┌────────────────▼────────────────────┐
    │            ORCHESTRATOR             │
    │          n8n (Self-hosted)          │
    │   Workflow Automation & AI Agent    │
    └───┬────────────────────────┬────┘
        │                         │
    ┌───▼────┐    ┌───────▼────┐
    │ AI AGENT ENGINE│    │  SCHEDULING  │
    │ OpenFang.sh /  │    │   Cal.com    │
    │ LangGraph      │    │              │
    └───────┬────┘    └────────────┘
            │
    ┌───────▼────────────────────────────┐
    │        KNOWLEDGE & MEMORY           │
    │  ┌────────────┐ ┌──────────────┐  │
    │  │ Obsidian +   │ │Qdrant/ChromaDB│  │
    │ Local LM    │ │(Vector Memory)│  │
    │  └──────────────┘  │
    └───────┬────────────────────────────┘
            │
    ┌───────▼────────────────────┐
    │       FILE & COMMUNICATION          │
    │           Nextcloud                  │
    │  (Email, Files, Calendar, Contacts) │
    └────────────────────────────────┘

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Docker Compose](#docker-compose)
- [Environment Variables](#environment-variables)
- [Component Setup](#component-setup)
- [Reverse Proxy](#reverse-proxy)
- [Security](#security)
- [Backup Strategy](#backup-strategy)
- [Health Monitoring](#health-monitoring)
- [Roadmap](#roadmap)

## 🔧 Prerequisites

### Hardware Minimum

| Resource | Minimum | Recommended |
|----------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 16 GB | 32 GB |
| Storage | 100 GB SD | 500 GB NVMe |
| GPU | - | NVIDIA 8GB+ (untuk local LLM) |

### Software

- Docker & Docker Compose v2+
- Git
- Domain name (untuk SSL)
- Telegram account (untuk bot)

## 🚀 Quick Start

    # 1. Clone repository
    git clone https://github.com/yourusername/ai-secretary-stack.git
    cd ai-secretary-stack

    # 2. Copy environment file
    cp .env.example .env

    # 3. Edit konfigurasi
    nano .env

    # 4. Jalankan semua services
    docker compose up -d

    # 5. Cek status
    docker compose ps

    # 6. Setup Telegram bot
    python3 scripts/setup_telegram_bot.py

## 🐳 Docker Compose

Buat file docker-compose.yml:

    version: "3.8"

    services:
      # ================================
      # ORCHESTRATOR - n8n
      # ============================================
      n8n:
        image: n8nio/n8n:latest
        container_name: n8n
        restart: always
        ports:
          - "5678:5678"
        environment:
          - N8N_BASIC_AUTH_ACTIVE=true
          - N8N_BASIC_AUTH_USER=${N8N_USER}
          - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
          - N8N_HOST=${N8N_HOST}
          - N8N_PORT=5678
          - N8N_PROTOCOL=https
          - WEBHOOK_URL=https:/${N8N_HOST}/
          - GENERIC_TIMEZONE=${TIMEZONE}
          - N8N_AI_ENABLED=true
        volumes:
          - n8n_data:/home/node/.n8n
          - ./n8n/workflows:/home/node/.n8n/workflows
        networks:
          - secretary-net

      # ============================================
      # AI AGENT ENGINE - OpenFang
      # ============================================
      openfang:
        image: ghcr.io/rightnow-ai/openfang:latest
        container_name: openfang
        restart: always
        ports:
          - "8090:8090"
        environment:
          - OPENFANG_CONFIG=/etc/openfang/secretary.toml
          - LM_PROVIDER=${LLM_PROVIDER}
          - LM_API_KEY=${LLM_API_KEY}
          - LM_MODEL=${LLM_MODEL}
        volumes:
          - ./openfang/secretary.toml:/etc/openfang/secretary.toml
          - openfang_data:/var/lib/openfang
        networks:
          - secretary-net

      # ============================================
      # LOCAL LLM - Ollama
      # ============================================
      ollama:
        image: ollama/ollama:latest
        container_name: ollama
        restart: always
        ports:
          - "11434:11434"
        volumes:
          - ollama_data:/root/.ollama
        deploy:
          resources:
            reservations:
              devices:
                - driver: nvidia
                  count: all
                capabilities: [gpu]
        networks:
          - secretary-net

      # ============================================
      # VECTOR MEMORY - Qdrant
      # ============================================
      qdrant:
        image: qdrant/qdrant:latest
        container_name: qdrant
        restart: always
        ports:
          - "6333:6333"
          - "6334:6334"
        volumes:
          - qdrant_data:/qdrant/storage
        environment:
          - QDRANT__SERVICE__API_KEY=${QDRANT_API_KEY}
        networks:
          - secretary-net

      # ============================================
      # SCHEDULING - Cal.com
      # ============================================
      calcom:
        image: calcom/cal.com:latest
        container_name: calcom
        restart: always
        ports:
          - "3000:3000"
        environment:
          - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/calcom
          - NEXTAUTH_SECRET=${CALCOM_SECRET}
          - CALENDSO_ENCRYPTION_KEY=${CALCOM_ENCRYPTION_KEY}
          - NEXT_PUBLIC_WEBAPP_URL=https://${CALCOM_HOST}
        depends_on:
          - postgres
        networks:
          - secretary-net

      # ============================================
      # NEXTCLOUD - Files, Email, Calendar
      # ============================================
      nextcloud:
        image: nextcloud:latest
        container_name: nextcloud
        restart: always
        ports:
          - "8080:80"
        environment:
          - MYSQL_HOST=mariadb
          - MYSQL_DATABASE=nextcloud
          - MYSQL_USER=${MYSQL_USER}
          - MYSQL_PASSWORD=${MYSQL_PASSWORD}
          - NEXTCLOUD_ADMIN_USER=${NC_ADMIN_USER}
          - NEXTCLOUD_ADMIN_PASSWORD=${NC_ADMIN_PASSWORD}
          - NEXTCLOUD_TRUSTED_DOMAINS=${NC_HOST}
        volumes:
          - nextcloud_data:/var/www/html
          - ./nextcloud/custom_apps:/var/www/html/custom_apps
        depends_on:
          - mariadb
        networks:
          - secretary-net

      # ============================================
      # TELEGRAM BOT
      # ============================================
      telegram-bot:
        build: ./telegram-bot
        container_name: telegram-bot
        restart: always
        environment:
          - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
          - ALLOWED_USER_IDS=${TELEGRAM_ALLOWED_USERS}
          - N8N_WEBHOOK_URL=http://n8n:5678/webhook/telegram
          - OPENFANG_URL=http://openfang:8090
          - QDRANT_URL=http://qdrant:6333
        depends_on:
          - n8n
          - openfang
          - qdrant
        networks:
          - secretary-net

      # ============================================
      # DATABASES
      # ============================================
      postgres:
        image: postgres:15
        container_name: postgres
        restart: always
        environment:
          - POSTGRES_USER=${POSTGRES_USER}
          - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
          - POSTGRES_DB=calcom
        volumes:
          - postgres_data:/var/lib/postgresql/data
        networks:
          - secretary-net

      mariadb:
        image: mariadb:10.11
        container_name: mariadb
        restart: always
        environment:
          - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
          - MYSQL_DATABASE=nextcloud
          - MYSQL_USER=${MYSQL_USER}
          - MYSQL_PASSWORD=${MYSQL_PASSWORD}
        volumes:
          - mariadb_data:/var/lib/mysql
        networks:
          - secretary-net

      # ============================================
      # REVERSE PROXY - Cady
      # ============================================
      caddy:
        image: caddy:2
        container_name: caddy
        restart: always
        ports:
          - "80:80"
          - "443:443"
        volumes:
          - ./caddy/Caddyfile:/etc/caddy/Caddyfile
          - caddy_data:/data
          - caddy_config:/config
        networks:
          - secretary-net

    volumes:
      n8n_data:
      openfang_data:
      ollama_data:
      qdrant_data:
      nextcloud_data:
      postgres_data:
      mariadb_data:
      caddy_data:
      cady_config:

    networks:
      secretary-net:
        driver: bridge

## 🔐 Environment Variables

Buat file .env:

    # ============================================
    # GENERAL
    # ============================================
    TIMEZONE=Asia/Jakarta
    DOMAIN=yourdomain.com

    # ============================================
    # n8n
    # ============================================
    N8N_USER=admin
    N8N_PASSWORD=your_secure_password_here
    N8N_HOST=n8n.yourdomain.com

    # ============================================
    # LM Configuration
    # ============================================
    LLM_PROVIDER=ollama
    LLM_API_KEY=sk-xxxxxxxx
    LLM_MODEL=llama3.1:8b
    OPENAI_API_KEY=sk-xxxxxxxxxx

    # ============================================
    # OpenFang
    # ============================================
    OPENFANG_SECRET=your_openfang_secret

    # ============================================
    # Qdrant
    # ============================================
    QDRANT_API_KEY=your_qdrant_api_key

    # ============================================
    # Cal.com
    # ============================================
    CALCOM_HOST=cal.yourdomain.com
    CALCOM_SECRET=your_calcom_secret
    CALCOM_ENCRYPTION_KEY=your_encryption_key

    # ============================================
    # Nextcloud
    # ============================================
    NC_HOST=cloud.yourdomain.com
    NC_ADMIN_USER=admin
    NC_ADMIN_PASSWORD=your_secure_password

    # ============================================
    # Database
    # ============================================
    POSTGRES_USER=calcom
    POSTGRES_PASSWORD=your_postgres_password
    MYSQL_ROOT_PASSWORD=your_mysql_root_password
    MYSQL_USER=nextcloud
    MYSQL_PASSWORD=your_mysql_password

    # ============================================
    # Telegram
    # ============================================
    TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
    TELEGRAM_ALLOWED_USERS=your_telegram_user_id

## ⚙️ Component Setup

### 1. n8n Orchestrator

n8n berfungsi sebagai otak koordinasi yang menghubungkan semua komponen.

#### a. Daily Briefing Workflow (JSON untuk import ke n8n):

    {
      "name": "Daily Briefing",
      "nodes": [
        {
          "type": "n8n-nodes-base.cron",
          "parameters": {
            "trigerTimes": {
              "item": [{ "hour": 7, "minute": 0 }]
            }
          },
          "name": "Every Morning 7AM"
        },
        {
          "type": "n8n-nodes-base.httpRequest",
          "parameters": {
            "url": "http://nextcloud:80/remote.php/dav/calendars/admin/personal",
            "method": "REPORT"
          },
          "name": "Fetch Today Calendar"
        },
        {
          "type": "n8n-nodes-base.httpRequest",
          "parameters": {
            "url": "http://qdrant:6333/collections/tasks/points/scroll",
            "method": "POST",
            "body": {
              "filter": { "must": [{ "key": "status", "match": { "value": "pending" } }] },
              "limit": 20
            }
          },
          "name": "Fetch Pending Tasks"
        },
        {
          "type": "@n8n/n8n-nodes-langchain.agent",
          "parameters": {
            "prompt": "Buatkan briefing pagi berdasarkan jadwal dan task berikut.",
            "model": "ollama/llama3.1:8b"
          },
          "name": "AI Generate Briefing"
        },
        {
          "type": "n8n-nodes-base.telegram",
          "parameters": {
            "chatId": "={{ $env.TELEGRAM_ALLOWED_USERS }}",
            "text": "={{ $json.output }"
          },
          "name": "Send to Telegram"
        }
      ]
    }

#### b. Message Router Workflow:

    {
      "name": "Telegram Message Router",
      "nodes": [
        {
          "type": "n8n-nodes-base.webhook",
          "parameters": { "path": "telegram", "method": "POST" },
          "name": "Telegram Webhook"
        },
        {
          "type": "n8n-nodes-base.switch",
          "parameters": {
            "rules": [
              { "value": "/schedule", "output": 0 },
              { "value": "/task", "output": 1 },
              { "value": "/search", "output": 2 },
              { "value": "", "output": 3, "operation": "default" }
            ]
          },
          "name": "Route by Command"
        }
      ]
    }

---

### 2. OpenFang / LangGraph

#### OpenFang Configuration (openfang/secretary.toml):

    [agent]
    name = "Secretary"
    description = "Personal AI Secretary yang tahu semua pekerjaan saya"
    mode = "daemon"
    personality = """
    Kamu adalah sekretaris pribadi AI yang sangat efisien dan proaktif.
    Kamu tahu semua jadwal, task, project, dan konteks pekerjaan saya.
    Kamu berkomunikasi dalam Bahasa Indonesia yang natural.
    Kamu memberikan reminder tanpa diminta jika ada deadline mendekat.
    """

    [llm]
    provider = "ollama"
    model = "llama3.1:8b"
    base_url = "http://ollama:11434"
    temperature = 0.7
    max_tokens = 2048

    [llm.fallback]
    provider = "openai"
    model = "gpt-4o-mini"
    api_key = "${OPENAI_API_KEY}"

    [memory]
    type = "qdrant"
    url = "http://qdrant:6333"
    collection = "agent_memory"
    api_key = "${QDRANT_API_KEY}"

    [hands]
    enabled = [
      "web_search",
      "calendar_read",
      "calendar_write",
      "file_read",
      "task_manage",
      "email_send",
      "reminder_set"
    ]

    [hands.calendar]
    provider = "caldav"
    url = "http://nextcloud:80/remote.php/dav"
    username = "${NC_ADMIN_USER}"
    password = "${NC_ADMIN_PASSWORD}"

    [hands.email]
    provider = "nextcloud"
    imap_host = "nextcloud"
    smtp_host = "nextcloud"

    [hands.tasks]
    provider = "qdrant"
    collection = "tasks"

    [channels]
    enabled = ["telegram", "webhook"]

    [channels.telegram]
    token = "${TELEGRAM_BOT_TOKEN}"
    allowed_users = ["${TELEGRAM_ALLOWED_USERS}"]

    [channels.webhook]
    port = 8090
    secret = "${OPENFANG_SECRET}"

    [daemon]
    enabled = true
    check_interval = "5m"
    proactive_hours = { start = 7, end = 22 }

    [daemon.routines]
    morning_briefing = "0 7 * *"
    task_reminder = "0 */2 * * *"
    eod_summary = "0 21 * * *"

#### Alternatif: LangGraph Agent (langgraph/agent.py):

    from langgraph.graph import StateGraph, END
    from langchain_community.llms import Ollama
    from langchain_community.vectorstores import Qdrant
    from langchain.agents import tool
    from qdrant_client import QdrantClient
    import requests
    from datetime import datetime

    # State definition
    class SecretaryState:
        messages: list
        context: str
        current_task: str
        tools_output: dict

    # Tools
    @tool
    def search_knowledge(query: str) -> str:
        """Cari informasi dari knowledge base pribadi."""
        client = QdrantClient(url="http://qdrant:6333")
        results = client.search(
            collection_name="knowledge",
            query_vector=get_embedding(query),
            limit=5
        )
        return "\n".join([r.payload["content"] for r in results])

    @tool
    def get_today_schedule() -> str:
        """Ambil jadwal hari ini dari Cal.com / Nextcloud."""
        response = requests.get(
            "http://nextcloud:80/remote.php/dav/calendars/admin/personal",
            auth=("admin", "password")
        )
        return parse_calendar(response.text)

    @tool
    def create_task(title: str, due_date: str, priority: str) -> str:
        """Buat task baru."""
        client = QdrantClient(url="http://qdrant:6333")
        client.upsert(
            collection_name="tasks",
            points=[{
                "id": generate_id(),
                "vector": get_embedding(title),
                "payload": {
                    "title": title,
                    "due_date": due_date,
                    "priority": priority,
                    "status": "pending",
                    "created_at": datetime.now().isoformat()
                }
            }]
        )
        return f"Task '{title}' berhasil dibuat (deadline: {due_date})"

    @tool
    def search_files(query: str) -> str:
        """Cari file di Nextcloud."""
        response = requests.request(
            "SEARCH",
            "http://nextcloud:80/remote.php/dav",
            auth=("admin", "password"),
            data=f"""<?xml version="1.0" encoding="UTF-8"?>
            <d:searchrequest xmlns:d="DAV:">
                <d:basicsearch>
                    <d:select><d:prop><d:displayname/></d:prop></d:select>
                    <d:from><d:scope><d:href>/files/admin</d:href></d:scope></d:from>
                    <d:where><d:like><d:prop><d:displayname/></d:prop>
                    <d:literal>%{query}%</d:literal></d:like></d:where>
                </d:basicsearch>
            </d:searchrequest>"""
        )
        return parse_search_results(response.text)

    # Build Graph
    workflow = StateGraph(SecretaryState)
    workflow.add_node("understand", understand_intent)
    workflow.add_node("retrieve_context", retrieve_context)
    workflow.add_node("execute_tools", execute_tools)
    workflow.add_node("generate_response", generate_response)

    workflow.set_entry_point("understand")
    workflow.add_edge("understand", "retrieve_context")
    workflow.add_edge("retrieve_context", "execute_tools")
    workflow.add_edge("execute_tools", "generate_response")
    workflow.add_edge("generate_response", END)

    app = workflow.compile()

---

### 3. Obsidian + Local LLM

#### Struktur Vault Obsidian:

    SecretaryVault/
    ├── 00-Inbox/              # Quick capture
    ├── 01-Projects/
    │   ├── ProjectA/
    │   │   ├── overview.md
    │   │   ├── tasks.md
    │   │   └── notes.md
    │   └── ProjectB/
    ├── 02-Areas/
    │   ├── Work/
    │   ├── Personal/
    │   └── Health/
    ├── 03-Resources/
    │   ├── People/           # Info tentang kontak/kolega
    │   ├── Procedures/       # SOP dan prosedur
    │   └── References/
    ├── 04-Archive/
    ├── 05-Daily-Notes/
    │   ├── 2026-05-08.md
    │   └── ...
    ├── 06-Meeting-Notes/
    └── Templates/
        ├── daily-note.md
        ├── meeting-note.md
        └── project-overview.md

#### Template Daily Note (Templates/daily-note.md):

    ---
    date: {{date}}
    tags: [daily-note]
    ---

    # {{date:dd, DD MMMM YYYY}}

    ## Top 3 Priorities
    1. 
    2. 
    3. 

    ## Schedule
    - 

    ## Tasks Completed
    - 

    ## Notes
    - 

    ## Ideas
    - 

    ## Tomorrow
    - 

#### Script Sync Obsidian ke Qdrant (scripts/sync_obsidian.py):

    #!/usr/bin/env python3
    """
    Sync Obsidian vault ke Qdrant vector database.
    Jalankan sebagai cron job setiap 30 menit.
    """

    import os
    import hashlib
    from pathlib import Path
    from datetime import datetime
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from sentence_transformers import SentenceTransformer

    # Configuration
    VAULT_PATH = "/path/to/SecretaryVault"
    QDRANT_URL = "http://localhost:6333"
    QDRANT_API_KEY = "your_api_key"
    COLLECTION_NAME = "knowledge"
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

    # Initialize
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    embeder = SentenceTransformer(EMBEDDING_MODEL)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n- ", "\n\n", "\n", " "]
    )

    def ensure_collection():
        """Buat collection jika belum ada."""
        collections = [c.name for c in client.get_collections().collections]
        if COLLECTION_NAME not in collections:
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=384,
                    distance=Distance.COSINE
                )
            )
            print(f"Collection '{COLLECTION_NAME}' created.")

    def get_file_hash(content: str) -> str:
        return hashlib.md5(content.encode()).hexdigest()

    def sync_vault():
        """Sync semua markdown files ke Qdrant."""
        ensure_collection()

        vault = Path(VAULT_PATH)
        md_files = list(vault.rglob("*.md"))
        points = []
        point_id = 0

        for md_file in md_files:
            if "Templates" in str(md_file):
                continue

            content = md_file.read_text(encoding="utf-8")
            relative_path = str(md_file.relative_to(vault))
            file_hash = get_file_hash(content)

            chunks = splitter.split_text(content)

            for i, chunk in enumerate(chunks):
                embedding = embedder.encode(chunk).tolist()

                points.append(PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "content": chunk,
                        "source_file": relative_path,
                "chunk_index": i,
                        "file_hash": file_hash,
                        "synced_at": datetime.now().isoformat(),
                        "folder": relative_path.split("/")[0],
                    }
                ))
                point_id += 1

        if points:
            client.delete_collection(COLLECTION_NAME)
            ensure_collection()
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i+batch_size]
                client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=batch
                )
            print(f"Synced {len(points)} chunks from {len(md_files)} files.")

    if __name__ == "__main__":
        sync_vault()

#### Cron Job untuk Auto-Sync:

    # Tambahkan ke crontab -e
    */30 * * * * cd /opt/ai-secretary && python3 scripts/sync_obsidian.py >> /var/log/obsidian-sync.log 2>&1

---

### 4. Qdrant Vector Memory

#### Inisialisasi Collections (scripts/init_qdrant.py):

    #!/usr/bin/env python3
    """Inisialisasi Qdrant collections untuk AI Secretary."""

    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams

    client = QdrantClient(url="http://localhost:6333", api_key="your_api_key")

    collections = {
        "knowledge": {
            "description": "Obsidian vault - semua knowledge dan notes",
            "size": 384,
        },
        "memory": {
            "description": "Conversation memory dan context jangka panjang",
            "size": 384,
        },
        "tasks": {
            "description": "Semua tasks dan to-do items",
            "size": 384,
        },
        "people": {
            "description": "Informasi tentang kontak dan kolega",
            "size": 384,
        },
        "decisions": {
            "description": "Log keputusan dan reasoning",
            "size": 384,
        },
    }

    for name, config in collections.items():
        try:
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=config["size"],
                    distance=Distance.COSINE
                )
            )
            print(f"Collection '{name}' created - {config['description']}")
        except Exception as e:
            print(f"Collection '{name}' already exists or error: {e}")

    print("\nAll collections initialized!")

---

### 5. Cal.com Scheduling

#### Webhook Integration dengan n8n:

    # Setelah Cal.com running, setup webhook:
    curl -X POST https://cal.yourdomain.com/api/v1/webhooks \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer YOUR_CALCOM_API_KEY" \
      -d '{
        "subscriberUrl": "https://n8n.yourdomain.com/webhook/calcom-events",
        "eventTriggers": [
          "BOOKING_CREATED",
          "BOOKING_CANCELLED",
          "BOOKING_RESCHEDULED"
        ],
        "active": true
      }'

Ketika ada booking baru, AI akan:
1. Menambahkan ke Nextcloud Calendar
2. Membuat preparation notes di Obsidian
3. Mengirim notifikasi ke Telegram
4. Menyimpan context ke Qdrant memory

---

### 6. Nextcloud

#### Post-Installation Setup:

    # Install apps yang dibutuhkan
    docker exec -u www-data nextcloud php occ app:install calendar
    docker exec -u www-data nextcloud php occ app:install contacts
    docker exec -u www-data nextcloud php occ app:install mail
    docker exec -u www-data nextcloud php occ app:install tasks
    docker exec -u www-data nextcloud php occ app:install notes
    docker exec -u www-data nextcloud php occ app:install deck

    # Setup external storage untuk Obsidian vault
    docker exec -u www-data nextcloud php occ app:install files_external

#### WebDAV Endpoints (untuk integrasi):

    Calendar:  http://nextcloud:80/remote.php/dav/calendars/{user}/
    Contacts:  http://nextcloud:80/remote.php/dav/addressbooks/users/{user}/
    Files:     http://nextcloud:80/remote.php/dav/files/{user}/
    Tasks:     http://nextcloud:80/remote.php/dav/calendars/{user}/tasks/

---

### 7. Telegram Bot

#### Bot Code (telegram-bot/bot.py):

    #!/usr/bin/env python3
    """
    AI Secretary Telegram Bot
    Interface utama untuk berkomunikasi dengan AI Secretary.
    """

    import os
    import logging
    import httpx
    from telegram import Update, BotCommand
    from telegram.ext import (
        Application, CommandHandler, MessageHandler,
        filters, ContextTypes
    )

    # Config
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    ALLOWED_USERS = [int(x) for x in os.getenv("ALLOWED_USER_IDS", "").split(",")]
    N8N_WEBHOOK = os.getenv("N8N_WEBHOOK_URL")
    OPENFANG_URL = os.getenv("OPENFANG_URL")

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Security: hanya user yang dizinkan
    def authorized(func):
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
            if update.effective_user.id not in ALLOWED_USERS:
                await update.message.reply_text("Unauthorized.")
                return
            return await func(update, context)
        return wrapper

    @authorized
    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "AI Secretary Active\n\n"
            "Saya siap membantu. Berikut yang bisa saya lakukan:\n\n"
            "/jadwal - Lihat jadwal hari ini\n"
            "/task - Kelola tasks\n"
            "/cari [query] - Cari di knowledge base\n"
            "/catat [note] - Catat sesuatu\n"
            "/status - Status semua projects\n"
            "/briefing - Daily briefing\n"
            "/remind [waktu] [pesan] - Set reminder\n\n"
            "Atau langsung kirim pesan biasa untuk chat."
        )

    @authorized
    async def cmd_jadwal(update: Update, context: ContextTypes.DEFAULT_TYPE):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{N8N_WEBHOOK}/schedule",
                json={"user_id": update.effective_user.id, "action": "today"}
            )
        await update.message.reply_text(response.json().get("message", "Tidak ada jadwal."))

    @authorized
    async def cmd_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        if not args:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{N8N_WEBHOOK}/tasks",
                    json={"action": "list", "status": "pending"}
                )
            await update.message.reply_text(response.json().get("message"))
        else:
            task_text = " ".join(args)
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{N8N_WEBHOOK}/tasks",
                    json={"action": "create", "title": task_text}
                )
            await update.message.reply_text(f"Task ditambahkan: {task_text}")

    @authorized
    async def cmd_cari(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = ".join(context.args)
        if not query:
            await update.message.reply_text("Gunakan: /cari [kata kunci]")
            return

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OPENFANG_URL}/api/search",
                json={"query": query, "collection": "knowledge", "limit": 5}
            )

        results = response.json().get("results", [])
        if results:
            text = f"Hasil pencarian: {query}\n\n"
            for i, r in enumerate(results, 1):
                text += f"{i}. {r['content'][:200]}...\n"
                text += f"   Sumber: {r['source_file']}\n\n"
            await update.message.reply_text(text)
        else:
            await update.message.reply_text("Tidak ditemukan hasil.")

    @authorized
    async def cmd_catat(update: Update, context: ContextTypes.DEFAULT_TYPE):
        note = " ".join(context.args)
        if not note:
            await update.message.reply_text("Gunakan: /catat [isi catan]")
            return
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{N8N_WEBHOOK}/note",
                json={"content": note, "source": "telegram"}
            )
        await update.message.reply_text(f"Dicatat: {note}")

    @authorized
    async def cmd_briefing(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Menyiapkan briefing...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{N8N_WEBHOOK}/briefing",
                json={"user_id": update.effective_user.id}
            )
        await update.message.reply_text(response.json().get("message"))

    @authorized
    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle pesan biasa - kirim ke AI agent."""
        user_message = update.message.text
        await update.message.reply_chat_action("typing")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OPENFANG_URL}/api/chat",
                json={
                    "message": user_message,
                    "user_id": str(update.effective_user.id),
                    "context": {
                        "platform": "telegram",
                        "timestamp": update.message.date.isoformat()
                    }
                }
            )

        reply = response.json().get("response", "Maf, terjadi kesalahan.")
        await update.message.reply_text(reply)

    @authorized
    async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle file upload - simpan ke Nextcloud."""
        document = update.message.document
        file = await context.bot.get_file(document.file_id)
        file_bytes = await file.download_as_bytearray()

        async with httpx.AsyncClient() as client:
            await client.put(
                f"http://nextcloud:80/remote.php/dav/files/admin/Inbox/{document.file_name}",
                content=file_bytes,
                auth=("admin", os.getenv("NC_ADMIN_PASSWORD"))
            )

        await update.message.reply_text(
            f"File '{document.file_name}' disimpan ke Nextcloud/Inbox/"
        )

    def main():
        app = Application.builder().token(BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", cmd_start))
        app.add_handler(CommandHandler("jadwal", cmd_jadwal))
        app.add_handler(CommandHandler("task", cmd_task))
        app.add_handler(CommandHandler("cari", cmd_cari))
        app.add_handler(CommandHandler("catat", cmd_catat))
        app.add_handler(CommandHandler("briefing", cmd_briefing))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

        logger.info("Secretary Bot started!")
        app.run_polling()

    if __name__ == "__main__":
        main()

#### Dockerfile (telegram-bot/Dockerfile):

    FROM python:3.11-slim

    WORKDIR /app

    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    COPY bot.py .

    CMD ["python", "bot.py"]

#### Requirements (telegram-bot/requirements.txt):

    python-telegram-bot==21.0
    httpx==0.27.0

---

## 🌐 Reverse Proxy

#### Caddyfile (cady/Caddyfile):

    n8n.yourdomain.com {
        reverse_proxy n8n:5678
    }

    cal.yourdomain.com {
        reverse_proxy calcom:3000
    }

    cloud.yourdomain.com {
        reverse_proxy nextcloud:80
        header {
            Strict-Transport-Security "max-age=31536000;"
        }
        redir /.well-known/carddav /remote.php/dav 301
        redir /.well-known/caldav /remote.php/dav 301
    }

    qdrant.yourdomain.com {
        reverse_proxy qdrant:6333
        @blocked not remote_ip 127.0.0.1 YOUR_IP_HERE
        respond @blocked 403
    }

---

## 🔒 Security

### Checklist Keamanan:

- Semua service di belakang reverse proxy dengan SSL
- Qdrant API key di-set dan tidak exposed ke public
- Telegram bot hanya menerima dari ALLOWED_USER_IDS
- n8n menggunakan basic auth
- Nextcloud 2FA enabled
- Docker network isolated (secretary-net)
- Regular security updates (watchtower)
- Firewall: hanya port 80, 443 yang terbuka
- Backup encrypted
- Audit log enabled di semua services

### Auto-Update dengan Watchtower (tambahkan ke docker-compose.yml):

    watchtower:
      image: containrrr/watchtower
      container_name: watchtower
      restart: always
      volumes:
        - /var/run/docker.sock:/var/run/docker.sock
      environment:
        - WATCHTOWER_CLEANUP=true
        - WATCHTOWER_SCHEDULE=0 0 4 * * *
        - WATCHTOWER_NOTIFICATIONS=shoutrrr
        - WATCHTOWER_NOTIFICATION_URL=telegram:/${TELEGRAM_BOT_TOKEN}@telegram?channels=${TELEGRAM_ALLOWED_USERS}

---

## 💾 Backup Strategy

#### Backup Script (scripts/backup.sh):

    #!/bin/bash
    # Daily backup script untuk AI Secretary Stack

    BACKUP_DIR="/backups/ai-secretary"
    DATE=$(date +%Y-%m-%d_%H%M)
    RETENTION_DAYS=30

    mkdir -p $BACKUP_DIR/$DATE

    echo "Starting backup: $DATE"

    # 1. n8n workflows dan credentials
    docker exec n8n n8n export:workflow --all --output=/tmp/workflows.json
    docker cp n8n:/tmp/workflows.json $BACKUP_DIR/$DATE/n8n-workflows.json
    docker run --rm -v n8n_data:/data -v $BACKUP_DIR/$DATE:/backup alpine \
        tar czf /backup/n8n-data.tar.gz /data

    # 2. Qdrant snapshots
    for collection in knowledge memory tasks people decisions; do
        curl -X POST "http://localhost:6333/collections/$collection/snapshots" \
            -H "api-key: $QDRANT_API_KEY"
    done
    docker run --rm -v qdrant_data:/data -v $BACKUP_DIR/$DATE:/backup alpine \
        tar czf /backup/qdrant-data.tar.gz /data

    # 3. Nextcloud
    docker exec -u www-data nextcloud php occ maintenance:mode --on
    docker run --rm -v nextcloud_data:/data -v $BACKUP_DIR/$DATE:/backup alpine \
        tar czf /backup/nextcloud-data.tar.gz /data
    docker exec -u www-data nextcloud php occ maintenance:mode --off

    # 4. Databases
    docker exec postgres pg_dump -U calcom calcom > $BACKUP_DIR/$DATE/postgres-calcom.sql
    docker exec mariadb mysqldump -u root -p$MYSQL_ROOT_PASSWORD nextcloud > $BACKUP_DIR/$DATE/mariadb-nextcloud.sql

    # 5. Obsidian vault
    tar czf $BACKUP_DIR/$DATE/obsidian-vault.tar.gz /path/to/SecretaryVault

    # 6. Config files
    tar czf $BACKUP_DIR/$DATE/configs.tar.gz \
        docker-compose.yml .env \
        openfang/ cady/ telegram-bot/

    # Encrypt backup
    tar czf - $BACKUP_DIR/$DATE | gpg --symmetric --cipher-algo AES256 \
        --passphrase-file /root/.backup-passphrase \
        -o $BACKUP_DIR/$DATE.tar.gz.gpg

    # Cleanup unencrypted
    rm -rf $BACKUP_DIR/$DATE

    # Remove old backups
    find $BACKUP_DIR -name "*.tar.gz.gpg" -mtime +$RETENTION_DAYS -delete

    echo "Backup completed: $BACKUP_DIR/$DATE.tar.gz.gpg"

    # Notify via Telegram
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d chat_id="$TELEGRAM_ALLOWED_USERS" \
        -d text="Backup selesai: $DATE"

#### Cron:

    0 2 * * * /opt/ai-secretary/scripts/backup.sh >> /var/log/backup.log 2>&1

---

## 🏥 Health Monitoring

#### Health Check Script (scripts/health_check.sh):

    #!/bin/bash
    # Health check untuk semua services

    SERVICES=(
        "n8n|http://localhost:5678/healthz|200"
        "qdrant|http://localhost:6333/healthz|200"
        "nextcloud|http://localhost:8080/status.php|200"
        "ollama|http://localhost:11434/api/tags|200"
        "calcom|http://localhost:3000/api/health|200"
        "openfang|http://localhost:8090/health|200"
    )

    ALERT=""

    for service_info in "${SERVICES[@]}"; do
        IFS='|' read -r name url expected_code <<< "$service_info"

        status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url")

        if [ "$status_code" != "$expected_code" ]; then
            ALERT+="$name DOWN (got $status_code, expected $expected_code)\n"
        fi
    done

    if [ -n "$ALERT" ]; then
        curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
            -d chat_id="$TELEGRAM_ALLOWED_USERS" \
            -d text="HEALTH ALERT:\n$ALERT"
    fi

#### Cron (setiap 5 menit):

    */5 * * * /opt/ai-secretary/scripts/health_check.sh

---

## 🚀 Post-Installation

Setelah semua service running:

    # 1. Pull model LM
    docker exec ollama ollama pull llama3.1:8b
    docker exec ollama ollama pull nomic-embed-text

    # 2. Inisialisasi Qdrant collections
    python3 scripts/init_qdrant.py

    # 3. Sync Obsidian vault pertama kali
    python3 scripts/sync_obsidian.py

    # 4. Test Telegram bot
    # Buka Telegram, cari bot Anda, kirim /start

    # 5. Setup n8n workflows
    # Buka https://n8n.yourdomain.com
    # Import workflow dari n8n/workflows/

    # 6. Verifikasi semua koneksi
    bash scripts/health_check.sh

---

## 🗺️ Roadmap

- Basic setup dan deployment (done)
- Telegram bot interface (done)
- Knowledge base sync (done)
- Voice message support (Whisper ST)
- Proactive reminders dan suggestions
- Email auto-categorization dan drafting
- Meeting notes auto-generation
- Multi-language support
- Mobile app (React Native)
- Browser extension for web capture
- Integration dengan WhatsApp Business API
- Fine-tuned local model untuk personal style

---

## 📝 License

MIT License - Gunakan dan modifikasi sesuka hati.

---

## 🙏 Credits

- n8n (https://n8n.io) - Workflow Automation
- OpenFang (https://openfang.sh) - Agent OS
- Qdrant (https://qdrant.tech) - Vector Database
- Ollama (https://ollama.ai) - Local LLM
- Cal.com (https://cal.com) - Scheduling
- Nextcloud (https://nextcloud.com) - Cloud Platform
- Obsidian (https://obsidian.md) - Knowledge Management

---

"Sekretaris terbaik adalah yang tahu apa yang Anda butuhkan sebelum Anda memintanya."
