# 🚀 Low-Resource Deployment Guide

> Deployment guide for servers with **4 cores / 8GB RAM** (minimum spec)

## 📋 Overview

This guide helps you deploy AI Personal Secretary Stack on budget VPS. All heavy stateful services (Qdrant, PostgreSQL) run externally as managed cloud services.

**What runs locally (5 containers):**
1. n8n (workflow orchestrator)
2. OpenFang (AI agent)
3. Cal.com (calendar app)
4. Telegram Bot (interface)
5. Caddy (reverse proxy)

**What runs externally:**
- PostgreSQL (Supabase/Neon/Railway)
- Qdrant (Qdrant Cloud)
- Cloudflare R2 (file storage)
- LLM Provider (OpenAI/Groq/etc)

---

## 🎯 Prerequisites

### Hardware Requirements
- **CPU:** 4 cores (x86_64)
- **RAM:** 8 GB
- **Storage:** 100 GB SSD
- **Network:** 10 Mbps upload/download
- **Swap:** 8 GB (CRITICAL - see setup below)

### Software Requirements
- Ubuntu 22.04 LTS / Debian 12
- Docker 24.0.0+ with Docker Compose v2.20.0+
- Git 2.34.0+
- Domain with DNS access

### External Services (Required)
1. **Qdrant Cloud** - Free tier (1GB, 1M vectors)
2. **PostgreSQL** - Supabase/Neon free tier
3. **Cloudflare R2** - Free tier (10GB)
4. **LLM Provider** - OpenAI/Groq/OpenRouter
5. **Telegram Bot** - Free

---

## 📝 Step-by-Step Setup

### Step 1: Enable Swap Space (CRITICAL)

8GB RAM is tight. Swap prevents OOM crashes during vector indexing and LLM inference.

```bash
# Create 8GB swap file
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify
free -h
# Should show 8GB swap
```

**Swap Configuration (Optional but Recommended):**
```bash
# Reduce swappiness (use swap only when necessary)
sudo sysctl vm.swappiness=10
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf

# Increase cache pressure (free up memory faster)
sudo sysctl vm.vfs_cache_pressure=50
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf
```

---

### Step 2: Sign Up for Qdrant Cloud

1. **Go to:** https://cloud.qdrant.io
2. **Sign up** (free tier available)
3. **Create cluster:**
   - Name: `ai-secretary`
   - Region: Choose closest to your VPS
   - Plan: Free (1GB storage, 1M vectors)
4. **Get credentials:**
   - Cluster URL: `https://xyz-abc-123.qdrant.io:6333`
   - API Key: `qdrant_api_key_here`

**Free Tier Limits:**
- Storage: 1 GB
- Vectors: 1 million
- Requests: Unlimited
- Sufficient for: Personal use, 10k-50k notes/documents

---

### Step 3: Clone Repository

```bash
cd /opt
sudo git clone https://github.com/yourusername/ai-secretary-stack.git
cd ai-secretary-stack
```

---

### Step 4: Configure Environment Variables

```bash
# Copy example
cp .env.example .env

# Edit configuration
nano .env
```

**Critical Variables:**

```bash
# Qdrant Cloud (from Step 2)
QDRANT_URL=https://your-cluster-id.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_cloud_api_key

# PostgreSQL (Supabase free tier)
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# LLM Provider (choose one)
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-3.5-turbo  # Use efficient model for cost savings

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ALLOWED_USERS=your_telegram_user_id

# Domains
DOMAIN=yourdomain.com
N8N_HOST=n8n.yourdomain.com
CALCOM_HOST=cal.yourdomain.com
```

---

### Step 5: Create Required Directories

```bash
# Create directories for volumes
mkdir -p n8n/workflows
mkdir -p openfang
mkdir -p caddy
mkdir -p telegram-bot

# Set permissions
sudo chown -R $USER:$USER .
```

---

### Step 6: Create Minimal Telegram Bot

```bash
# Create Dockerfile
cat > telegram-bot/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir python-telegram-bot requests

COPY bot.py .

CMD ["python", "bot.py"]
EOF

# Create bot script
cat > telegram-bot/bot.py << 'EOF'
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
ALLOWED_USERS = [int(uid) for uid in os.getenv('TELEGRAM_ALLOWED_USERS', '').split(',')]
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        await update.message.reply_text("Unauthorized")
        return
    await update.message.reply_text("AI Secretary Bot is running!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS:
        return
    await update.message.reply_text(f"Received: {update.message.text}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Bot started")
    app.run_polling()

if __name__ == '__main__':
    main()
EOF
```

---

### Step 7: Create Caddyfile

```bash
cat > caddy/Caddyfile << 'EOF'
{
    email admin@yourdomain.com
}

n8n.yourdomain.com {
    reverse_proxy n8n:5678
}

cal.yourdomain.com {
    reverse_proxy calcom:3000
}
EOF
```

---

### Step 8: Deploy Stack

```bash
# Start services
docker compose up -d

# Check status
docker compose ps

# Monitor logs
docker compose logs -f

# Check resource usage
docker stats
```

**Expected Resource Usage:**
```
CONTAINER     CPU %    MEM USAGE / LIMIT     MEM %
n8n           5-15%    1.2GB / 2GB          60%
openfang      5-10%    800MB / 2GB          40%
calcom        3-8%     900MB / 1.5GB        60%
telegram-bot  1-2%     200MB / 512MB        39%
caddy         1-2%     100MB / 256MB        39%
─────────────────────────────────────────────────
TOTAL         15-37%   3.2GB / 6.25GB       51%
```

**With OS overhead: ~4-5 GB total usage (fits in 8GB with swap)**

---

### Step 9: Verify Deployment

```bash
# Check all containers running
docker compose ps
# All should show "Up"

# Test n8n
curl http://localhost:5678/healthz

# Test Cal.com
curl http://localhost:3000/api/health

# Test Qdrant Cloud connection
curl -X GET "https://your-cluster-id.qdrant.io:6333/collections" \
  -H "api-key: your_qdrant_api_key"
```

---

## 🔍 Monitoring & Maintenance

### Monitor Resource Usage

```bash
# Real-time monitoring
docker stats

# Check swap usage
free -h

# Check disk usage
df -h
```

### Log Management

```bash
# View logs
docker compose logs -f [service_name]

# Limit log size (add to docker-compose.yml)
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart n8n

# Rebuild after changes
docker compose up -d --build
```

---

## ⚠️ Troubleshooting

### OOM (Out of Memory) Errors

**Symptoms:**
- Containers randomly stopping
- `docker compose ps` shows "Exited (137)"
- System becomes unresponsive

**Solutions:**
```bash
# 1. Check swap is enabled
free -h

# 2. Increase swap if needed
sudo swapoff /swapfile
sudo fallocate -l 12G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 3. Reduce container limits
# Edit docker-compose.yml, reduce memory limits by 20%

# 4. Restart services
docker compose restart
```

### High CPU Usage

**Symptoms:**
- CPU constantly at 90-100%
- Slow response times

**Solutions:**
```bash
# 1. Check which container is consuming CPU
docker stats

# 2. Reduce concurrent operations
# Edit .env, reduce n8n concurrent executions

# 3. Use more efficient LLM model
# Edit .env:
LLM_MODEL=gpt-3.5-turbo  # Instead of gpt-4
```

### Qdrant Cloud Connection Issues

**Symptoms:**
- "Connection refused" errors
- Vector search not working

**Solutions:**
```bash
# 1. Verify credentials
echo $QDRANT_URL
echo $QDRANT_API_KEY

# 2. Test connection
curl -X GET "$QDRANT_URL/collections" \
  -H "api-key: $QDRANT_API_KEY"

# 3. Check firewall (Qdrant uses port 6333)
# Ensure your VPS can reach external HTTPS

# 4. Restart OpenFang
docker compose restart openfang
```

---

## 💰 Cost Estimate (4 Cores / 8GB RAM)

```
VPS (4 cores, 8GB):        $8-15/month
  - Hetzner CX21:          €9/month (~$10)
  - Contabo VPS S:         €7/month (~$8)

PostgreSQL (Supabase):     $0/month (free tier)
Qdrant Cloud:              $0/month (free tier, 1GB)
Cloudflare R2:             $0-2/month (free 10GB)
LLM API (light usage):     $10-30/month
Domain:                    $1/month
Backup (Backblaze B2):     $0.50/month (100GB)

TOTAL:                     $19.50-48.50/month
```

---

## 🔄 Upgrade Path

When you outgrow 4 cores / 8GB RAM:

### Option 1: Upgrade VPS
- Move to 6 cores / 16GB RAM
- More headroom for concurrent operations
- Cost: $15-30/month

### Option 2: Upgrade External Services
- Upgrade to Qdrant Cloud Starter ($25/month)
- Upgrade to Supabase Pro ($25/month)
- Keep current VPS
- Cost: $58-83/month

### Option 3: Full Cloud
- Move n8n to n8n Cloud ($20/month)
- Keep Qdrant Cloud
- Minimal VPS for Cal.com + Telegram
- Cost: $48-93/month

---

## 📚 Additional Resources

- **Qdrant Cloud Docs:** https://qdrant.tech/documentation/cloud/
- **Docker Resource Limits:** https://docs.docker.com/config/containers/resource_constraints/
- **Swap Configuration:** https://www.digitalocean.com/community/tutorials/how-to-add-swap-space-on-ubuntu-22-04
- **n8n Self-Hosting:** https://docs.n8n.io/hosting/
- **Cal.com Self-Hosting:** https://cal.com/docs/self-hosting

---

## ✅ Success Checklist

- [ ] Swap space enabled (8GB)
- [ ] Qdrant Cloud cluster created
- [ ] All environment variables configured
- [ ] Docker Compose deployed successfully
- [ ] All 5 containers running
- [ ] Resource usage under 6GB RAM
- [ ] Telegram bot responding
- [ ] n8n accessible via domain
- [ ] Cal.com accessible via domain
- [ ] Qdrant Cloud connection working

---

**Need help?** Check the main README.md or open an issue on GitHub.
