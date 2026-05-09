# 🤖 AI Personal Secretary Stack

> Sistem asisten pribadi AI self-hosted yang tahu semua pekerjaan Anda — berjalan 24/7, privasi terjaga, kontrol penuh di tangan Anda.

## 📐 Architecture

```mermaid
graph TB
    User[👤 User]
    
    subgraph Interface["🖥️ USER INTERFACE"]
        TG[Telegram Bot]
    end
    
    subgraph Orchestrator["🎯 ORCHESTRATOR"]
        N8N[n8n<br/>Workflow Automation & AI Agent]
    end
    
    subgraph AIEngine["🤖 AI AGENT ENGINE"]
        OpenFang[OpenFang.sh]
        LangGraph[LangGraph]
    end
    
    subgraph Scheduling["📅 SCHEDULING"]
        CalCom[Cal.com<br/>Calendar & Appointments]
    end
    
    subgraph Knowledge["🧠 KNOWLEDGE & MEMORY"]
        Obsidian[Obsidian Notes]
        Qdrant[Qdrant<br/>Vector Memory]
    end
    
    subgraph Storage["📁 FILE STORAGE"]
        R2[Cloudflare R2<br/>S3-Compatible Object Storage]
    end
    
    subgraph External["📧 EXTERNAL SERVICES"]
        SMTP[SMTP Service<br/>SendGrid/Mailgun]
    end
    
    User --> TG
    TG --> N8N
    N8N --> OpenFang
    N8N --> LangGraph
    N8N --> CalCom
    N8N --> SMTP
    OpenFang --> Obsidian
    OpenFang --> Qdrant
    OpenFang --> R2
    LangGraph --> Obsidian
    LangGraph --> Qdrant
    LangGraph --> R2
    Obsidian --> R2
    CalCom --> SMTP
    
    classDef interfaceStyle fill:#e1f5ff,stroke:#01579b,stroke-width:2px,color:#000
    classDef orchestratorStyle fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000
    classDef aiStyle fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000
    classDef scheduleStyle fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px,color:#000
    classDef knowledgeStyle fill:#fce4ec,stroke:#880e4f,stroke-width:2px,color:#000
    classDef storageStyle fill:#fff9c4,stroke:#f57f17,stroke-width:2px,color:#000
    classDef externalStyle fill:#e0e0e0,stroke:#616161,stroke-width:2px,color:#000
    
    class TG interfaceStyle
    class N8N orchestratorStyle
    class OpenFang,LangGraph aiStyle
    class CalCom scheduleStyle
    class Obsidian,Qdrant knowledgeStyle
    class R2 storageStyle
    class SMTP externalStyle
```

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Monthly Cost Estimate](#-monthly-cost-estimate)
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

### Hardware Requirements

#### Minimum (Small Team/Personal Use)
- **CPU:** 4 cores (x86_64)
- **RAM:** 16 GB
- **Storage:** 100 GB SSD
- **Network:** 10 Mbps upload/download

#### Recommended (Production Use)
- **CPU:** 8 cores (x86_64)
- **RAM:** 32 GB
- **Storage:** 500 GB NVMe SSD
- **Network:** 50 Mbps upload/download

#### Optimal (High-Volume/Enterprise)
- **CPU:** 16 cores (x86_64)
- **RAM:** 64 GB
- **Storage:** 1 TB NVMe SSD
- **Network:** 100 Mbps upload/download

### Software Prerequisites

#### Required
- **OS:** Ubuntu 22.04 LTS / Debian 12 (recommended)
- **Docker:** 24.0.0+ with Docker Compose v2.20.0+
- **Git:** 2.34.0+
- **Python:** 3.10+ (for setup scripts)
- **Domain:** Registered domain with DNS access
- **Telegram:** Active Telegram account

#### Installation Commands

```bash
# Docker + Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Logout and login again for group changes to take effect
```

### Network & Firewall Requirements

#### Required Ports (External)
- **80/tcp** - HTTP (Caddy, auto-redirect to HTTPS)
- **443/tcp** - HTTPS (Caddy reverse proxy)

#### Internal Ports (Docker network only)
- **5678** - n8n
- **8090** - OpenFang
- **6333, 6334** - Qdrant
- **3000** - Cal.com

> **Note:** PostgreSQL menggunakan external provider (Supabase/Neon/Railway), tidak ada container lokal.
> **Note:** File storage menggunakan Cloudflare R2 (external service), tidak ada port internal.

#### Firewall Setup

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Verify
sudo ufw status
```

---

## 💰 Monthly Cost Estimate

### Scenario 1: Minimal Setup (Small Team/Personal)

**Infrastructure:**
- **VPS:** $10-20/month
  - DigitalOcean Droplet (4 cores, 16GB): $96/year = $8/month
  - Linode Dedicated 16GB: $96/month = $8/month
  - Hetzner CX31 (4 cores, 16GB): €13/month = ~$14/month
- **Domain + SSL:** $1-2/month
  - Domain (.com): ~$12/year = $1/month
  - SSL: Free (Let's Encrypt via Caddy)
- **PostgreSQL Database:** $0-10/month
  - Supabase: Free tier (500MB, 2GB bandwidth)
  - Neon: Free tier (0.5GB storage, 3GB data transfer)
  - Railway: $5/month (shared CPU, 512MB RAM)
- **Backup Storage (Optional):** $5-10/month
  - Backblaze B2: $0.005/GB = ~$5 for 1TB
  - Wasabi: $6.99/TB/month

**LLM Costs (OpenAI-compatible Provider):**
- **Light Usage:** ~$10-30/month
  - Using efficient models (gpt-3.5-turbo, claude-haiku)
  - ~1000-3000 requests/month

**Total: $26-72/month** (minimal setup, cost-optimized)

---

### Scenario 2: Production Setup (Recommended)

**Infrastructure:**
- **VPS/Dedicated Server:** $20-50/month
  - Hetzner AX41 (Ryzen 5 3600, 64GB RAM): ~€39/month (~$42)
  - Contabo VPS L (10 cores, 60GB RAM): ~€27/month (~$29)
  - OVH Advance-2 (8 cores, 32GB RAM): ~$40/month
- **Domain + SSL:** $1-2/month
- **PostgreSQL Database:** $10-25/month
  - Supabase Pro: $25/month (8GB storage, 50GB bandwidth)
  - Neon Scale: $19/month (10GB storage, autoscaling)
  - Railway Pro: $20/month (8GB RAM, shared CPU)
- **Backup Storage:** $5-10/month

**LLM Costs (OpenAI-compatible Provider):**
- **Moderate Usage:** ~$30-80/month
  - Mix of efficient and quality models
  - ~5000-10000 requests/month
  - Using gpt-4, claude-sonnet, or similar

**Total: $66-167/month** (production-ready, balanced)

---

### Scenario 3: High-Volume/Enterprise

**Infrastructure:**
- **Dedicated Server:** $50-100/month
  - Hetzner AX102 (Ryzen 9 5950X, 128GB RAM): ~€99/month (~$107)
  - OVH Scale-3 (16 cores, 64GB RAM): ~$80/month
- **Domain + SSL:** $1-2/month
- **PostgreSQL Database:** $50-200/month
  - Supabase Team: $599/month (unlimited storage, dedicated resources)
  - Neon Business: Custom pricing (dedicated compute)
  - AWS RDS: $50-200/month (db.t3.medium to db.m5.large)
- **Backup Storage:** $10-20/month

**LLM Costs (OpenAI-compatible Provider):**
- **Heavy Usage:** ~$100-300/month
  - High-quality models (gpt-4, claude-opus)
  - ~20000-50000 requests/month
  - Production workloads

**Total: $211-622/month** (enterprise-grade, high-volume)

---

### Cost Comparison Table

| Component | Scenario 1<br/>(Minimal) | Scenario 2<br/>(Production) | Scenario 3<br/>(Enterprise) |
|-----------|--------------------------|-----------------------------|-----------------------------|
| **Server/VPS** | $10-20 | $20-50 | $50-100 |
| **Domain + SSL** | $1-2 | $1-2 | $1-2 |
| **PostgreSQL Database** | $0-10 | $10-25 | $50-200 |
| **Backup Storage** | $5-10 | $5-10 | $10-20 |
| **LLM API (Provider)** | $10-30 | $30-80 | $100-300 |
| **Usage Level** | Light | Moderate | Heavy |
| **Setup Complexity** | 🔧 Low | 🔧🔧 Medium | 🔧🔧🔧 High |
| **TOTAL/month** | **$26-72** | **$66-167** | **$211-622** |

---

### Additional Optional Costs

- **Telegram Bot:** Free (unlimited messages)
- **Cal.com:** Free (self-hosted)
- **n8n:** Free (self-hosted)
- **Cloudflare R2:** Free 10GB, $0.015/GB after (S3-compatible, no egress fees)
- **Qdrant:** Free (self-hosted)
- **Monitoring (Uptime Robot):** Free tier available
- **Email Service (SMTP):**
  - SendGrid: Free (100 emails/day)
  - Mailgun: Free (5,000 emails/month)
  - SMTP2GO: Free (1,000 emails/month)

---

### PostgreSQL Provider Recommendations

#### Free Tier Options (Development/Testing)
- **Supabase:** 500MB storage, 2GB bandwidth/month
  - ✅ Generous free tier
  - ✅ Built-in auth, storage, realtime
  - ✅ Automatic backups
  - 🔗 [supabase.com](https://supabase.com)

- **Neon:** 0.5GB storage, 3GB data transfer/month
  - ✅ Serverless PostgreSQL
  - ✅ Instant branching
  - ✅ Auto-scaling
  - 🔗 [neon.tech](https://neon.tech)

- **Railway:** $5 free credit/month
  - ✅ Simple deployment
  - ✅ Built-in monitoring
  - ✅ Easy scaling
  - 🔗 [railway.app](https://railway.app)

#### Production Options
- **Supabase Pro:** $25/month
  - 8GB storage, 50GB bandwidth
  - Daily backups, point-in-time recovery
  - Dedicated resources

- **Neon Scale:** $19/month
  - 10GB storage, autoscaling compute
  - Branch protection
  - Read replicas

- **Render:** $7-25/month
  - Managed PostgreSQL
  - Automatic backups
  - Easy scaling

- **DigitalOcean Managed Database:** $15/month
  - 1GB RAM, 10GB storage
  - Automated backups
  - High availability options

#### Enterprise Options
- **AWS RDS:** $50-500+/month
  - Full control, multiple instance types
  - Multi-AZ deployment
  - Advanced monitoring

- **Google Cloud SQL:** $50-500+/month
  - Automatic replication
  - High availability
  - Integration with GCP services

- **Azure Database for PostgreSQL:** $50-500+/month
  - Enterprise-grade security
  - Built-in intelligence
  - Flexible scaling

---

### Cost Optimization Tips

1. **Start with Scenario 1** (Minimal) untuk testing, scale up sesuai kebutuhan
2. **Use free tier databases** - Supabase/Neon free tier cukup untuk development
3. **Use Hetzner Auction Server** - bisa dapat dedicated server mulai €30/month
4. **Choose efficient models** - gpt-3.5-turbo, claude-haiku untuk cost efficiency
5. **Use OpenRouter** - pay-per-use pricing, no monthly commitment
6. **Consider Groq** - free tier available for fast inference
7. **Backblaze B2 + Cloudflare** - bandwidth gratis untuk backup
8. **Annual domain purchase** - lebih murah daripada monthly
9. **Database connection pooling** - reduce database costs dengan PgBouncer
10. **Local LLM (Ollama)** - completely free if you have GPU

---

### ROI Comparison

**vs. Commercial AI Assistant Services:**
- ChatGPT Plus: $20/month (limited features)
- Claude Pro: $20/month (limited features)
- Notion AI: $10/month (limited to Notion)
- **This Stack (Scenario 1):** $26-72/month
  - ✅ Unlimited usage
  - ✅ 36+ models to choose from
  - ✅ Complete customization
  - ✅ Integration with your entire workflow
  - ✅ Self-hosted infrastructure
  - ✅ No vendor lock-in

**Break-even:** If you use >1 AI service, self-hosting provides more value and flexibility.

---

## 🤖 LLM Provider Configuration

## 🤖 LLM Provider Configuration

This project supports any **OpenAI-compatible API provider**, giving you flexibility to choose based on your needs, budget, and privacy requirements.

### Supported Providers

Any provider with OpenAI-compatible API endpoints works out of the box:

- **OpenAI** - Official GPT models (gpt-4, gpt-3.5-turbo)
- **Anthropic** - Claude models via compatibility layer
- **OpenRouter** - Access to 100+ models through single API
- **Together AI** - Open source models (Llama, Mistral, etc.)
- **Groq** - Ultra-fast inference for open models
- **Azure OpenAI** - Enterprise OpenAI deployment
- **Local (Ollama/LM Studio)** - Self-hosted for complete privacy
- **Other aggregators** - Any service with `/v1/chat/completions` endpoint

### Getting Started

1. **Choose Your Provider** and get an API key
2. **Set Environment Variables:**
   ```bash
   export LLM_API_KEY="your-api-key"
   export LLM_BASE_URL="https://api.provider.com/v1"  # Provider's base URL
   export LLM_MODEL="gpt-4"  # Your chosen model
   ```

3. **Test Connection:**
   ```bash
   curl $LLM_BASE_URL/models \
     -H "Authorization: Bearer $LLM_API_KEY"
   ```

### Provider Comparison

| Provider | Pros | Cons | Best For |
|----------|------|------|----------|
| **OpenAI** | Best quality, reliable | Most expensive | Production apps |
| **OpenRouter** | 100+ models, pay-per-use | Slight latency overhead | Experimentation |
| **Groq** | Extremely fast inference | Limited model selection | Real-time chat |
| **Together AI** | Good pricing, open models | Variable quality | Cost optimization |
| **Ollama** | Free, private, offline | Requires GPU, slower | Privacy-first |

### Configuration Examples

#### LangChain/LangGraph

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "gpt-4"),
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
    temperature=0.7,
)
```

#### n8n (HTTP Request Node)

```json
{
  "method": "POST",
  "url": "{{$env.LLM_BASE_URL}}/chat/completions",
  "headers": {
    "Authorization": "Bearer {{$env.LLM_API_KEY}}"
  },
  "body": {
    "model": "{{$env.LLM_MODEL}}",
    "messages": [{"role": "user", "content": "Your prompt"}],
    "temperature": 0.7
  }
}
```

#### OpenFang (TOML)

```toml
[llm]
provider = "openai"  # Use OpenAI-compatible mode
model = "${LLM_MODEL}"
base_url = "${LLM_BASE_URL}"
api_key = "${LLM_API_KEY}"
```

### Provider-Specific Setup

#### OpenAI
```bash
LLM_API_KEY="sk-..."
LLM_BASE_URL="https://api.openai.com/v1"
LLM_MODEL="gpt-4"
```

#### OpenRouter
```bash
LLM_API_KEY="sk-or-v1-..."
LLM_BASE_URL="https://openrouter.ai/api/v1"
LLM_MODEL="anthropic/claude-3.5-sonnet"
```

#### Groq
```bash
LLM_API_KEY="gsk_..."
LLM_BASE_URL="https://api.groq.com/openai/v1"
LLM_MODEL="llama-3.1-70b-versatile"
```

#### Together AI
```bash
LLM_API_KEY="..."
LLM_BASE_URL="https://api.together.xyz/v1"
LLM_MODEL="meta-llama/Llama-3-70b-chat-hf"
```

#### Ollama (Local)
```bash
LLM_API_KEY="ollama"  # Any value works
LLM_BASE_URL="http://localhost:11434/v1"
LLM_MODEL="llama3.1:8b"
```

---

## 🚀 Quick Start

```bash
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
```

## 🐳 Docker Compose

Buat file docker-compose.yml:

```yaml
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
      - WEBHOOK_URL=https://${N8N_HOST}/
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
      - DATABASE_URL=${DATABASE_URL}
      - NEXTAUTH_SECRET=${CALCOM_SECRET}
      - CALENDSO_ENCRYPTION_KEY=${CALCOM_ENCRYPTION_KEY}
      - NEXT_PUBLIC_WEBAPP_URL=https://${CALCOM_HOST}
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
      - R2_ENDPOINT=${R2_ENDPOINT}
      - R2_ACCESS_KEY_ID=${R2_ACCESS_KEY_ID}
      - R2_SECRET_ACCESS_KEY=${R2_SECRET_ACCESS_KEY}
      - R2_BUCKET=${R2_BUCKET}
    depends_on:
      - n8n
      - openfang
      - qdrant
    networks:
      - secretary-net

  # ============================================
  # REVERSE PROXY - Caddy
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
  qdrant_data:
  caddy_data:
  caddy_config:

networks:
  secretary-net:
    driver: bridge
```

## 🔐 Environment Variables

Buat file .env:

```bash
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
# LLM Configuration - OpenAI-Compatible Provider
# ============================================
# This project supports any OpenAI-compatible API provider
# Choose based on your needs: cost, privacy, performance

# Primary LLM Provider Configuration
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4

# Provider Examples:
# 
# OpenAI (Official):
# LLM_API_KEY=sk-...
# LLM_BASE_URL=https://api.openai.com/v1
# LLM_MODEL=gpt-4
#
# OpenRouter (100+ models):
# LLM_API_KEY=sk-or-v1-...
# LLM_BASE_URL=https://openrouter.ai/api/v1
# LLM_MODEL=anthropic/claude-3.5-sonnet
#
# Groq (Ultra-fast):
# LLM_API_KEY=gsk_...
# LLM_BASE_URL=https://api.groq.com/openai/v1
# LLM_MODEL=llama-3.1-70b-versatile
#
# Together AI (Open models):
# LLM_API_KEY=...
# LLM_BASE_URL=https://api.together.xyz/v1
# LLM_MODEL=meta-llama/Llama-3-70b-chat-hf
#
# Ollama (Local/Self-hosted):
# LLM_API_KEY=ollama
# LLM_BASE_URL=http://localhost:11434/v1
# LLM_MODEL=llama3.1:8b

# Legacy/Compatibility (for tools that expect these variable names)
LLM_PROVIDER=openai
OPENAI_API_KEY=${LLM_API_KEY}
OPENAI_API_BASE=${LLM_BASE_URL}

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
# Database - External PostgreSQL Provider
# ============================================
# Use external PostgreSQL provider (Supabase, Neon, Railway, etc.)
# Format: postgresql://username:password@host:port/database?sslmode=require
DATABASE_URL=postgresql://user:password@db.provider.com:5432/calcom?sslmode=require

# Example providers:
# - Supabase: postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
# - Neon: postgresql://[USER]:[PASSWORD]@[HOST]/[DATABASE]?sslmode=require
# - Railway: postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/railway
# - Render: postgresql://[USER]:[PASSWORD]@[HOST]/[DATABASE]

# ============================================
# Telegram
# ============================================
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ALLOWED_USERS=your_telegram_user_id

# ============================================
# External Services (Optional)
# ============================================
# SMTP for email notifications
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your_sendgrid_api_key
SMTP_FROM=secretary@yourdomain.com
```

## ⚙️ Component Setup

### 1. n8n Orchestrator

n8n berfungsi sebagai otak koordinasi yang menghubungkan semua komponen.

#### a. Daily Briefing Workflow (JSON untuk import ke n8n):

```json
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
        "url": "http://calcom:3000/api/bookings",
        "method": "GET",
        "headers": {
          "Authorization": "Bearer {{$env.CALCOM_API_KEY}}"
        },
        "qs": {
          "startTime": "{{$now.toISO()}}"
        }
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
        "model": "gpt-5.2"
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
```

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

```toml
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
provider = "openai"  # Use OpenAI-compatible mode
model = "${LLM_MODEL}"
base_url = "${LLM_BASE_URL}"
api_key = "${LLM_API_KEY}"
temperature = 0.7
max_tokens = 2048

[llm.fallback]
provider = "openai"
model = "gpt-3.5-turbo"  # Fast fallback model
api_key = "${LLM_API_KEY}"
base_url = "${LLM_BASE_URL}"

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
provider = "calcom"
api_url = "http://calcom:3000/api"
api_key = "${CALCOM_API_KEY}"

[hands.email]
provider = "smtp"
smtp_host = "${SMTP_HOST}"
smtp_port = "${SMTP_PORT}"
smtp_user = "${SMTP_USER}"
smtp_password = "${SMTP_PASSWORD}"
from_email = "${SMTP_FROM}"

[hands.storage]
provider = "s3"
endpoint = "${R2_ENDPOINT}"
access_key = "${R2_ACCESS_KEY_ID}"
secret_key = "${R2_SECRET_ACCESS_KEY}"
bucket = "${R2_BUCKET}"
region = "auto"  # Cloudflare R2 uses "auto" region

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
```
    check_interval = "5m"
    proactive_hours = { start = 7, end = 22 }

    [daemon.routines]
    morning_briefing = "0 7 * *"
    task_reminder = "0 */2 * * *"
    eod_summary = "0 21 * * *"

#### Alternatif: LangGraph Agent (langgraph/agent.py):

```python
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Qdrant
from langchain.agents import tool
from qdrant_client import QdrantClient
import requests
from datetime import datetime
import os

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
    """Ambil jadwal hari ini dari Cal.com API."""
    response = requests.get(
        "http://calcom:3000/api/bookings",
        headers={"Authorization": f"Bearer {os.getenv('CALCOM_API_KEY')}"},
        params={"startTime": datetime.now().isoformat()}
    )
    return parse_calendar_json(response.json())

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
    """Cari file di Cloudflare R2 storage."""
    import boto3
    
    s3 = boto3.client(
        's3',
        endpoint_url=os.getenv('R2_ENDPOINT'),
        aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
        region_name='auto'  # Cloudflare R2 uses "auto" region
    )
    
    response = s3.list_objects_v2(
        Bucket=os.getenv('R2_BUCKET', 'secretary-files'),
        Prefix=query
    )
    
    files = [obj['Key'] for obj in response.get('Contents', [])]
    return "\n".join(files) if files else "No files found"

# Initialize LLM
llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "gpt-4"),
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY"),
    temperature=0.7,
)

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
```

    app = workflow.compile()

---

### 3. Knowledge Base (Obsidian + Qdrant)

#### Struktur Vault Obsidian:

```plaintext
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
```
    ├── 06-Meeting-Notes/
    └── Templates/
        ├── daily-note.md
        ├── meeting-note.md
        └── project-overview.md

#### Template Daily Note (Templates/daily-note.md):

```yaml
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
```

    ## Ideas
    - 

    ## Tomorrow
    - 

#### Script Sync Obsidian ke Qdrant (scripts/sync_obsidian.py):

```python
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
embedder = SentenceTransformer(EMBEDDING_MODEL)
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
```
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

```python
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
```
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

```json
{
  "url": "https://n8n.yourdomain.com/webhook/calcom",
  "eventTriggers": ["BOOKING_CREATED", "BOOKING_CANCELLED", "BOOKING_RESCHEDULED"],
  "active": true,
  "payloadTemplate": {
    "event": "{{event}}",
    "booking": {
      "id": "{{booking.id}}",
      "title": "{{booking.title}}",
      "startTime": "{{booking.startTime}}",
      "endTime": "{{booking.endTime}}",
      "attendees": "{{booking.attendees}}"
    }
  }
}
```
```bash
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
```

Ketika ada booking baru, AI akan:
1. Sync dengan Cal.com calendar
2. Membuat preparation notes di Obsidian
3. Mengirim notifikasi ke Telegram
4. Menyimpan context ke Qdrant memory

---

### 6. Cloudflare R2 (S3 Storage)

#### Setup Guide:

1. **Create Cloudflare R2 Account:**
   - Go to https://dash.cloudflare.com
   - Navigate to R2 Object Storage
   - Create a bucket: `secretary-files`

2. **Generate API Tokens:**
   - Go to R2 → Manage R2 API Tokens
   - Create API Token with "Object Read & Write" permissions
   - Save: Access Key ID and Secret Access Key

3. **Configure Environment Variables:**
   ```bash
   R2_ACCOUNT_ID=your_account_id
   R2_ACCESS_KEY_ID=your_access_key
   R2_SECRET_ACCESS_KEY=your_secret_key
   R2_BUCKET=secretary-files
   R2_ENDPOINT=https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com
   ```

4. **Optional: Custom Domain (for public files):**
   - R2 → Settings → Custom Domains
   - Add: `files.yourdomain.com`
   - Update DNS: CNAME to R2 endpoint

#### S3 API Endpoints:

```
API Endpoint:     https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com
Bucket:           secretary-files
Region:           auto (Cloudflare R2 uses "auto")
Access Key:       ${R2_ACCESS_KEY_ID}
Secret Key:       ${R2_SECRET_ACCESS_KEY}
```

#### Python S3 Integration Example:

```python
import boto3
import os

s3 = boto3.client(
    's3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)

# Upload file
s3.upload_file('local_file.pdf', 'secretary-files', 'documents/file.pdf')

# Download file
s3.download_file('secretary-files', 'documents/file.pdf', 'downloaded.pdf')

# List files
response = s3.list_objects_v2(Bucket='secretary-files', Prefix='documents/')
for obj in response.get('Contents', []):
    print(obj['Key'])
```

---

### 7. Telegram Bot

#### Bot Code (telegram-bot/bot.py):

```python
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
    query = " ".join(context.args)
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
    """Handle file upload - simpan ke Cloudflare R2."""
    import boto3
    from io import BytesIO
    
    document = update.message.document
    file = await context.bot.get_file(document.file_id)
    file_bytes = await file.download_as_bytearray()
    
    # Upload to Cloudflare R2
    s3 = boto3.client(
        's3',
        endpoint_url=os.getenv('R2_ENDPOINT'),
        aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
        region_name='auto'
    )
    
    s3.upload_fileobj(
        BytesIO(file_bytes),
        os.getenv('R2_BUCKET', 'secretary-files'),
        f"telegram-uploads/{document.file_name}"
    )

    await update.message.reply_text(
        f"File '{document.file_name}' disimpan ke Cloudflare R2"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
```

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

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

CMD ["python", "bot.py"]
```

#### Requirements (telegram-bot/requirements.txt):

```txt
python-telegram-bot==21.0
httpx==0.27.0
```

---

## 🌐 Reverse Proxy

#### Caddyfile (caddy/Caddyfile):

```caddyfile
n8n.yourdomain.com {
    reverse_proxy n8n:5678
}

cal.yourdomain.com {
    reverse_proxy calcom:3000
}

# Cloudflare R2 (external service, no reverse proxy needed)
    header {
    }
}

qdrant.yourdomain.com {
    reverse_proxy qdrant:6333
    @blocked not remote_ip 127.0.0.1 YOUR_IP_HERE
    respond @blocked 403
}
```

---

## 🔒 Security

### Checklist Keamanan:

- Semua service di belakang reverse proxy dengan SSL
- Qdrant API key di-set dan tidak exposed ke public
- Telegram bot hanya menerima dari ALLOWED_USER_IDS
- n8n menggunakan basic auth
- Cloudflare R2 bucket policies configured
- Docker network isolated (secretary-net)
- Regular security updates (watchtower)
- Firewall: hanya port 80, 443 yang terbuka
- Backup encrypted
- Audit log enabled di semua services

### Auto-Update dengan Watchtower (tambahkan ke docker-compose.yml):

```yaml
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
```

---

## 💾 Backup Strategy

#### Backup Script (scripts/backup.sh):

```bash
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

# 3. Cloudflare R2 (external backup via rclone)

# 4. Database (External PostgreSQL - use provider's backup tools)
# For Supabase: Automatic daily backups included
# For Neon: Point-in-time restore available
# For Railway/Render: Use their backup features
# Manual backup (if needed):
# pg_dump $DATABASE_URL > $BACKUP_DIR/$DATE/postgres-calcom.sql

# 5. Obsidian vault
tar czf $BACKUP_DIR/$DATE/obsidian-vault.tar.gz /path/to/SecretaryVault

# 6. Config files
tar czf $BACKUP_DIR/$DATE/configs.tar.gz \
    docker-compose.yml .env \
    openfang/ caddy/ telegram-bot/

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
```

#### Cron:

```bash
0 2 * * * /opt/ai-secretary/scripts/backup.sh >> /var/log/backup.log 2>&1
```

---

## 🏥 Health Monitoring

#### Health Check Script (scripts/health_check.sh):

    #!/bin/bash
    # Health check untuk semua services

    SERVICES=(
        "n8n|http://localhost:5678/healthz|200"
        "qdrant|http://localhost:6333/healthz|200"
        
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

    # 1. Inisialisasi Qdrant collections
    python3 scripts/init_qdrant.py

    # 2. Sync Obsidian vault pertama kali
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
- Cal.com (https://cal.com) - Scheduling
- Cloudflare R2 (https://www.cloudflare.com/products/r2/) - S3-Compatible Object Storage
- Obsidian (https://obsidian.md) - Knowledge Management
- OpenAI, Anthropic, and other LLM providers - AI Models

---

"Sekretaris terbaik adalah yang tahu apa yang Anda butuhkan sebelum Anda memintanya."
