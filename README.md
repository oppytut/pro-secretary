# 🤖 AI Personal Secretary Stack

> Sistem asisten pribadi AI self-hosted yang tahu semua pekerjaan Anda — berjalan 24/7, privasi terjaga, kontrol penuh di tangan Anda.

> **Status (2026-05-30):** Production stack — 9 features shipped. AI engine adalah **custom LangGraph agent** di [`langgraph-agent/`](langgraph-agent/). Sumber otoritatif untuk state aktual: [`docker-compose.yml`](docker-compose.yml), [`TASK.md`](TASK.md), [`AI_AGENT_ROADMAP.md`](AI_AGENT_ROADMAP.md).

## 📐 Architecture

```mermaid
graph TB
    User[👤 User]

    subgraph Interface["🖥️ USER INTERFACE"]
        TG[Telegram Bot<br/>inbound only]
    end

    subgraph Orchestrator["🎯 ORCHESTRATOR"]
        N8N[n8n<br/>Workflows: Daily Briefing,<br/>Task Reminder, Cal.com Webhook]
    end

    subgraph AIEngine["🤖 AI AGENT ENGINE"]
        Agent[LangGraph Agent<br/>FastAPI + Qdrant + fastembed<br/>Telegram egress via /api/notify]
    end

    subgraph Scheduling["📅 SCHEDULING"]
        CalCom[Cal.com<br/>Calendar & Appointments]
    end

    subgraph Knowledge["🧠 KNOWLEDGE"]
        Obsidian[Obsidian Vault<br/>bind-mounted, auto-sync 30min]
    end

    subgraph VectorDB["💾 VECTOR DATABASE"]
        Qdrant[Qdrant Cloud<br/>384-dim all-MiniLM-L6-v2]
    end

    subgraph Storage["📁 FILE STORAGE"]
        R2[Cloudflare R2<br/>S3-compatible]
    end

    subgraph External["📧 EXTERNAL SERVICES"]
        LLM[LLM Provider<br/>OpenAI-compatible API]
        SMTP[SMTP Service<br/>SendGrid/Mailgun]
        PostgreSQL[PostgreSQL<br/>Supabase/Neon/Railway]
    end

    User --> TG
    TG --> Agent
    N8N --> Agent
    N8N --> CalCom
    CalCom --> N8N
    Agent --> LLM
    Agent --> Obsidian
    Agent --> Qdrant
    Agent --> R2
    Agent --> TG
    Obsidian --> R2
    CalCom --> SMTP
    CalCom --> PostgreSQL

    classDef interfaceStyle fill:#e1f5ff,stroke:#01579b,stroke-width:2px,color:#000
    classDef orchestratorStyle fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000
    classDef aiStyle fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000
    classDef scheduleStyle fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px,color:#000
    classDef knowledgeStyle fill:#fce4ec,stroke:#880e4f,stroke-width:2px,color:#000
    classDef storageStyle fill:#fff9c4,stroke:#f57f17,stroke-width:2px,color:#000
    classDef externalStyle fill:#e0e0e0,stroke:#616161,stroke-width:2px,color:#000
    classDef vectordbStyle fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:#000

    class TG interfaceStyle
    class N8N orchestratorStyle
    class Agent aiStyle
    class CalCom scheduleStyle
    class Obsidian knowledgeStyle
    class R2 storageStyle
    class SMTP,PostgreSQL,LLM externalStyle
    class Qdrant vectordbStyle
```

## 🔄 How It Works

### System Overview

AI Personal Secretary adalah sistem yang bekerja **24/7** untuk membantu mengelola pekerjaan, jadwal, tasks, knowledge base, dan kesehatan VPS Anda. Sistem ini menggunakan arsitektur microservices dengan 7 containers lokal dan 3 external services yang saling terintegrasi.

### Component Roles

| Component | Role | Technology | Port |
|-----------|------|------------|------|
| **Telegram Bot** | User interface | Python Telegram Bot API | External |
| **n8n** | Workflow orchestrator & router | n8n (low-code automation) | 5678 |
| **LangGraph Agent** | AI reasoning & tool execution | FastAPI + LangGraph + fastembed | 8090 |
| **Cal.com** | Calendar & appointment management | Cal.com (self-hosted) | 3000 |
| **Prometheus** | Metrics collection (multi-VPS) | Prometheus v3 + node_exporter | 9090 (internal) |
| **Alertmanager** | Alert routing → Telegram | Prometheus Alertmanager v0.28 | 9093 (internal) |
| **Caddy** | Reverse proxy + SSL termination | Caddy 2 (alpine) | 80, 443 |
| **Qdrant Cloud** | Vector database & semantic search | Qdrant (managed cloud) | External |
| **Obsidian** | Knowledge base (notes & docs) | Obsidian Markdown | - |
| **Cloudflare R2** | Object storage (files, backups) | S3-compatible storage | External |

### Data Flow Architecture

```mermaid
flowchart TD
    User[👤 USER<br/>Sends message/command<br/>via Telegram]
    
    TelegramBot[📱 TELEGRAM BOT<br/>Interface Layer<br/>━━━━━━━━━━━━━━<br/>✓ Authentication whitelist<br/>✓ Command parsing<br/>✓ Message routing]
    
    N8N[🎯 N8N<br/>Orchestration Layer<br/>━━━━━━━━━━━━━━<br/>✓ Route commands to services<br/>✓ Schedule automated tasks cron<br/>✓ Coordinate multi-service ops]
    
    AIAgent[🤖 LANGGRAPH AGENT<br/>AI Agent Layer<br/>━━━━━━━━━━━━━━<br/>✓ Understand user intent<br/>✓ Retrieve context from memory<br/>✓ Execute tools calendar, search, tasks<br/>✓ Generate natural language responses]
    
    subgraph Backend["🔧 BACKEND SERVICES (Parallel Access)"]
        Obsidian[📝 OBSIDIAN<br/>Knowledge Base<br/>━━━━━━━━<br/>• Notes<br/>• Docs<br/>• Wiki]
        
        Qdrant[💾 QDRANT CLOUD<br/>Vector DB<br/>━━━━━━━━<br/>• Memories<br/>• Tasks<br/>• Knowledge]
        
        CalCom[📅 CAL.COM<br/>Calendar<br/>━━━━━━━━<br/>• Events<br/>• Bookings]
        
        PostgreSQL[🗄️ POSTGRESQL<br/>Database<br/>━━━━━━━━<br/>• Booking data<br/>• User data<br/>• Event types]
        
        R2[📦 CLOUDFLARE R2<br/>Storage<br/>━━━━━━━━<br/>• Files<br/>• Backups<br/>• Archives]
    end
    
    User --> TelegramBot
    TelegramBot --> N8N
    N8N --> AIAgent
    AIAgent --> Obsidian
    AIAgent --> Qdrant
    AIAgent --> CalCom
    AIAgent --> R2
    Obsidian --> Qdrant
    Obsidian --> R2
    CalCom --> PostgreSQL
    
    style User fill:#e3f2fd,stroke:#1976d2,stroke-width:3px,color:#000
    style TelegramBot fill:#e1f5ff,stroke:#01579b,stroke-width:2px,color:#000
    style N8N fill:#fff3e0,stroke:#e65100,stroke-width:2px,color:#000
    style AIAgent fill:#f3e5f5,stroke:#4a148c,stroke-width:2px,color:#000
    style Backend fill:#f5f5f5,stroke:#616161,stroke-width:2px
    style Obsidian fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px,color:#000
    style Qdrant fill:#e0e0e0,stroke:#616161,stroke-width:2px,color:#000
    style CalCom fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px,color:#000
    style PostgreSQL fill:#fff9c4,stroke:#f57f17,stroke-width:2px,color:#000
    style R2 fill:#fff9c4,stroke:#f57f17,stroke-width:2px,color:#000
```

**Key Data Flows:**

1. **User Input** → Telegram Bot → n8n → AI Agent → Backend Services
2. **Proactive Tasks** → n8n (cron) → AI Agent → Backend Services → Telegram Bot → User
3. **Calendar Operations** → Cal.com ↔ PostgreSQL (persistent storage)
4. **Memory/Context** → Qdrant Cloud (vector search for relevant information)
5. **Knowledge Base** → Obsidian (notes/docs) → Qdrant Cloud (indexing) + R2 (backup)
6. **File Operations** → Cloudflare R2 (S3-compatible object storage)

---

## 📖 Workflow Examples

### Example 1: User Sends Chat Message

**User Input:** "Apa jadwal saya hari ini?"

**Flow:**

```
1. TELEGRAM BOT receives message
   ├─ Check authorization (ALLOWED_USERS)
   └─ Forward to LangGraph agent

2. LANGGRAPH AGENT processes request
   ├─ Step 1: Understand Intent
   │   └─ Detected: "check_schedule", date="today"
   │
   ├─ Step 2: Retrieve Context (Qdrant)
   │   └─ Query vector DB for relevant past conversations
   │
   ├─ Step 3: Execute Tools
   │   └─ GET http://calcom:3000/api/bookings?startTime=today
   │       Response: [
   │         { "title": "Team Standup", "time": "09:00" },
   │         { "title": "Client Meeting", "time": "14:00" }
   │       ]
   │
   ├─ Step 4: Generate Response (LLM)
   │   └─ POST https://api.openai.com/v1/chat/completions
   │       Prompt: "Format this schedule naturally: [data]"
   │       Response: "Hari ini Anda punya 2 jadwal:
   │                 1. Team Standup jam 09:00
   │                 2. Client Meeting jam 14:00"
   │
   └─ Step 5: Store Memory
       └─ Save conversation to Qdrant for future context

3. TELEGRAM BOT sends response to user
```

**Result:** User receives formatted schedule in natural language.

---

### Example 2: Command Execution (`/task`)

**User Input:** `/task Buat proposal untuk Client B`

**Flow:**

```
1. TELEGRAM BOT detects command
   ├─ Parse: command="/task", args="Buat proposal untuk Client B"
   └─ Route to n8n webhook

2. N8N WORKFLOW (Message Router)
   ├─ Receive: POST http://n8n:5678/webhook/tasks
   │   Body: { "action": "create", "title": "Buat proposal..." }
   │
   ├─ Switch Node: Route based on action type
   │   └─ Branch: "create_task"
   │
   └─ Execute Task Creation
       ├─ Generate embedding for task
       └─ Store in Qdrant "tasks" collection

3. QDRANT CLOUD stores task
   └─ POST ${QDRANT_URL}/collections/tasks/points
       {
         "id": "task-uuid-456",
         "vector": [0.234, 0.567, ...],
         "payload": {
           "title": "Buat proposal untuk Client B",
           "status": "pending",
           "created_at": "2026-05-09T10:35:00"
         }
       }

4. N8N sends confirmation
   └─ Telegram: "✅ Task ditambahkan: Buat proposal untuk Client B"
```

**Result:** Task stored in vector DB, searchable by semantic similarity.

---

### Example 3: Daily Briefing (Scheduled/Proactive)

**Trigger:** Cron job at 07:00 AM every day

**Flow:**

```
1. N8N CRON TRIGGER activates
   └─ Workflow: "Daily Briefing"

2. PARALLEL DATA COLLECTION
   ├─ Fetch Today's Calendar
   │   └─ GET http://calcom:3000/api/bookings?startTime=today
   │       Response: [meetings for today]
   │
   └─ Fetch Pending Tasks
       └─ POST ${QDRANT_URL}/collections/tasks/points/scroll
           Filter: { "status": "pending" }
           Response: [pending tasks]

3. AI GENERATES BRIEFING
   └─ POST https://api.openai.com/v1/chat/completions
       Prompt: "Create morning briefing from this data:
                Calendar: [meetings]
                Tasks: [pending tasks]"
       
       Response:
       "Selamat pagi! Berikut briefing Anda hari ini:
        
        📅 JADWAL:
        - 09:00 Team Standup
        - 14:00 Client Meeting
        
        ✅ TASKS PENDING:
        - Buat proposal untuk Client B (urgent)
        - Review dokumen kontrak
        
        💡 REKOMENDASI:
        Prioritaskan proposal sebelum meeting jam 14:00."

4. SEND TO TELEGRAM
   └─ User receives briefing automatically at 07:00 AM
```

**Result:** Proactive daily briefing without user request.

---

### Example 4: Knowledge Base Search (`/cari`)

**User Input:** `/cari cara setup docker compose`

**Flow:**

```
1. TELEGRAM BOT extracts query
   └─ Query: "cara setup docker compose"

2. LANGGRAPH AGENT SEMANTIC SEARCH
   ├─ Generate embedding from query
   │   └─ Vector: [0.345, 0.678, 0.912, ...]
   │
   └─ Search in Qdrant Cloud "knowledge" collection
       └─ POST ${QDRANT_URL}/collections/knowledge/points/search
           {
             "vector": [0.345, 0.678, ...],
             "limit": 5,
             "with_payload": true
           }

3. QDRANT returns similar documents
   └─ Results: [
       {
         "score": 0.92,
         "payload": {
           "content": "Docker Compose adalah tool untuk...",
           "source_file": "DevOps/Docker-Setup.md"
         }
       },
       ...
     ]

4. FETCH FULL CONTENT (if needed)
   └─ GET https://r2.cloudflarestorage.com/secretary-files/DevOps/Docker-Setup.md

5. FORMAT AND SEND RESULTS
   └─ Telegram: "Hasil pencarian: cara setup docker compose
                 
                 1. Docker Compose adalah tool untuk define...
                    Sumber: DevOps/Docker-Setup.md
                 
                 2. Untuk setup, install dengan: apt install...
                    Sumber: DevOps/Installation-Guide.md"
```

**Result:** Semantic search finds relevant docs even with different wording.

---

### Example 5: Calendar Booking with PostgreSQL (`/jadwal`)

**User Input:** `/jadwal buat meeting dengan tim engineering besok jam 2 siang`

**Flow:**

```
1. TELEGRAM BOT parses command
   └─ Intent: create_calendar_event
   └─ Extracted data:
       - Title: "Meeting dengan tim engineering"
       - Date: tomorrow
       - Time: 14:00

2. N8N WORKFLOW processes request
   ├─ Validate date/time
   ├─ Check for conflicts
   └─ Forward to Cal.com API

3. CAL.COM API CALL
   └─ POST http://calcom:3000/api/bookings
       Headers: {
         "Authorization": "Bearer ${CALCOM_API_KEY}"
       }
       Body: {
         "eventTypeId": 123,
         "start": "2026-05-10T14:00:00Z",
         "end": "2026-05-10T15:00:00Z",
         "responses": {
           "name": "Meeting dengan tim engineering",
           "email": "user@example.com"
         }
       }

4. CAL.COM → POSTGRESQL (Database Operations)
   ├─ BEGIN TRANSACTION
   │
   ├─ INSERT INTO bookings
   │   └─ SQL: INSERT INTO "Booking" (
   │              "uid", "userId", "eventTypeId",
   │              "title", "startTime", "endTime",
   │              "status", "createdAt"
   │            ) VALUES (
   │              'booking_abc123', 1, 123,
   │              'Meeting dengan tim engineering',
   │              '2026-05-10 14:00:00', '2026-05-10 15:00:00',
   │              'ACCEPTED', NOW()
   │            )
   │
   ├─ UPDATE user availability
   │   └─ SQL: UPDATE "Availability" 
   │            SET "isBooked" = true
   │            WHERE "userId" = 1
   │            AND "startTime" = '2026-05-10 14:00:00'
   │
   ├─ INSERT INTO event_logs
   │   └─ SQL: INSERT INTO "EventLog" (
   │              "bookingId", "action", "timestamp"
   │            ) VALUES (
   │              'booking_abc123', 'CREATED', NOW()
   │            )
   │
   └─ COMMIT TRANSACTION

5. POSTGRESQL → CAL.COM (Response)
   └─ Returns: {
       "id": "booking_abc123",
       "uid": "booking_abc123",
       "title": "Meeting dengan tim engineering",
       "startTime": "2026-05-10T14:00:00Z",
       "endTime": "2026-05-10T15:00:00Z",
       "status": "ACCEPTED"
     }

6. CAL.COM → SMTP (Send Email Notification)
   └─ POST to SendGrid/Mailgun
       Subject: "Meeting Confirmed: Meeting dengan tim engineering"
       Body: "Your meeting is scheduled for May 10, 2026 at 2:00 PM"

7. N8N → QDRANT CLOUD (Store in Memory)
   └─ POST ${QDRANT_URL}/collections/agent_memory/points
       {
         "points": [{
           "id": "memory_xyz789",
           "vector": [0.123, 0.456, ...],
           "payload": {
             "type": "calendar_event",
             "booking_id": "booking_abc123",
             "title": "Meeting dengan tim engineering",
             "datetime": "2026-05-10T14:00:00Z",
             "created_via": "telegram"
           }
         }]
       }

8. TELEGRAM BOT sends confirmation
   └─ Message: "✅ Meeting berhasil dijadwalkan!
                
                📅 Meeting dengan tim engineering
                🕐 Besok, 10 Mei 2026 jam 14:00
                📧 Email konfirmasi telah dikirim
                
                Booking ID: booking_abc123"
```

**PostgreSQL Tables Involved:**

```sql
-- Cal.com uses these tables
Booking          -- Stores meeting details
Availability     -- Tracks user availability slots
EventType        -- Meeting types configuration
User             -- User information
EventLog         -- Audit trail
Attendee         -- Meeting participants
```

**Database Query Example:**

```sql
-- Check for scheduling conflicts
SELECT * FROM "Booking"
WHERE "userId" = 1
  AND "status" = 'ACCEPTED'
  AND (
    ("startTime" <= '2026-05-10 14:00:00' AND "endTime" > '2026-05-10 14:00:00')
    OR
    ("startTime" < '2026-05-10 15:00:00' AND "endTime" >= '2026-05-10 15:00:00')
  );

-- If no conflicts, proceed with booking
```

**Result:** Complete calendar booking flow with PostgreSQL transaction, email notification, and memory storage.

**Key Points:**
- ✅ **ACID Transactions** - PostgreSQL ensures data consistency
- ✅ **Conflict Detection** - Prevents double-booking
- ✅ **Audit Trail** - EventLog tracks all changes
- ✅ **External Database** - Managed by Supabase/Neon/Railway
- ✅ **Automatic Backups** - Handled by database provider

---

### Sequence Diagram: Calendar Booking Flow

Visual representation of the complete booking workflow:

```mermaid
sequenceDiagram
    participant U as 👤 User
    participant T as 📱 Telegram Bot
    participant N as 🎯 n8n
    participant C as 📅 Cal.com
    participant P as 🗄️ PostgreSQL
    participant S as 📧 SMTP
    participant Q as 🧠 Qdrant
    
    U->>T: /jadwal Meeting besok 14:00
    activate T
    T->>N: POST /webhook/calendar
    deactivate T
    
    activate N
    Note over N: Parse natural language<br/>"besok 14:00" → 2026-05-10 14:00
    N->>C: POST /api/bookings
    deactivate N
    
    activate C
    C->>P: BEGIN TRANSACTION
    activate P
    C->>P: SELECT * FROM bookings<br/>WHERE start_time = '2026-05-10 14:00'
    P-->>C: [] (no conflicts)
    C->>P: INSERT INTO bookings (...)
    P-->>C: booking_id: 123
    C->>P: COMMIT
    deactivate P
    
    C->>S: Send confirmation email
    activate S
    S-->>C: Email sent
    deactivate S
    
    C-->>N: {booking_id: 123, uid: "abc123"}
    deactivate C
    
    activate N
    N->>Q: Store booking in memory
    activate Q
    Q-->>N: Stored
    deactivate Q
    
    N->>T: Format confirmation message
    deactivate N
    
    activate T
    T->>U: ✅ Event berhasil dibuat!<br/>Meeting dengan tim engineering<br/>📅 2026-05-10 14:00-15:00<br/>🔗 cal.yourdomain.com/booking/abc123
    deactivate T
```

**Timeline:**
- **0-100ms:** Telegram → n8n (webhook)
- **100-200ms:** n8n parses natural language
- **200-500ms:** Cal.com → PostgreSQL (transaction)
- **500-800ms:** Email notification sent
- **800-900ms:** Memory storage (Qdrant)
- **900-1000ms:** Confirmation to user

**Total Response Time:** ~1 second

---

### Database Schema: PostgreSQL ERD

Entity Relationship Diagram showing Cal.com database structure:

```mermaid
erDiagram
    USERS ||--o{ BOOKINGS : creates
    USERS ||--o{ EVENT_TYPES : owns
    EVENT_TYPES ||--o{ BOOKINGS : "has type"
    BOOKINGS ||--o{ EVENT_LOGS : tracks
    
    USERS {
        int id PK
        string email UK
        string name
        string timezone
        timestamp created_at
    }
    
    EVENT_TYPES {
        int id PK
        int user_id FK
        string title
        int duration_minutes
        string description
        boolean active
    }
    
    BOOKINGS {
        int id PK
        string uid UK
        string title
        text description
        timestamp start_time
        timestamp end_time
        int user_id FK
        int event_type_id FK
        string status
        timestamp created_at
    }
    
    EVENT_LOGS {
        int id PK
        int booking_id FK
        string action
        text metadata
        timestamp created_at
    }
```

**Table Relationships:**
- **USERS** → **BOOKINGS**: One user can create many bookings
- **USERS** → **EVENT_TYPES**: One user can define many event types
- **EVENT_TYPES** → **BOOKINGS**: One event type can have many bookings
- **BOOKINGS** → **EVENT_LOGS**: One booking can have many audit log entries

**Key Constraints:**
- `USERS.email` - Unique constraint (UK)
- `BOOKINGS.uid` - Unique identifier for external references
- Foreign keys ensure referential integrity
- `EVENT_LOGS` provides complete audit trail

### Example 6: Knowledge Retrieval from Obsidian (`/tanya`)

**User Input:** `/tanya Apa yang sudah kita diskusikan tentang project Alpha minggu lalu?`

**Flow:**

```
1. TELEGRAM BOT receives question
   └─ Intent: knowledge_retrieval
   └─ Query: "diskusi project Alpha minggu lalu"

2. LANGGRAPH AGENT processes request
   ├─ Step 1: Generate Query Embedding
   │   └─ POST to LLM embedding endpoint
   │       Input: "diskusi project Alpha minggu lalu"
   │       Output: vector [0.234, 0.567, 0.891, ...]
   │
   ├─ Step 2: Search Qdrant Cloud (Indexed Obsidian Content)
   │   └─ POST ${QDRANT_URL}/collections/knowledge/points/search
   │       {
   │         "vector": [0.234, 0.567, ...],
   │         "limit": 5,
   │         "filter": {
   │           "must": [
   │             { "key": "source", "match": { "value": "obsidian" } },
   │             { "key": "created_at", "range": { "gte": "2026-05-04" } }
   │           ]
   │         }
   │       }
   │
   │       Response: [
   │         {
   │           "score": 0.94,
   │           "payload": {
   │             "title": "Project Alpha - Weekly Sync",
   │             "file_path": "Projects/Alpha/2026-05-05-weekly-sync.md",
   │             "content": "Discussed timeline delays...",
   │             "tags": ["project-alpha", "meeting-notes"],
   │             "created_at": "2026-05-05T10:00:00Z"
   │           }
   │         },
   │         {
   │           "score": 0.87,
   │           "payload": {
   │             "title": "Alpha - Technical Decisions",
   │             "file_path": "Projects/Alpha/technical-decisions.md",
   │             "content": "Decided to use PostgreSQL...",
   │             "tags": ["project-alpha", "architecture"],
   │             "created_at": "2026-05-06T14:30:00Z"
   │           }
   │         }
   │       ]
   │
   └─ Step 3: Fetch Full Content from Obsidian/R2
       ├─ Option A: Read from local Obsidian vault
       │   └─ File: /vault/Projects/Alpha/2026-05-05-weekly-sync.md
       │
       └─ Option B: Fetch from R2 backup
           └─ GET https://r2.cloudflarestorage.com/secretary-files/
                   obsidian/Projects/Alpha/2026-05-05-weekly-sync.md

3. AI SYNTHESIZES ANSWER
   └─ POST https://api.openai.com/v1/chat/completions
       System: "You are a personal secretary. Summarize these notes."
       Context: [Full content from Obsidian notes]
       User Query: "Apa yang sudah kita diskusikan tentang project Alpha?"
       
       Response:
       "Berdasarkan notes minggu lalu tentang Project Alpha:
        
        📝 WEEKLY SYNC (5 Mei):
        - Timeline mengalami delay 2 minggu karena dependency issue
        - Tim engineering butuh tambahan resource
        - Client sudah informed dan setuju dengan revised timeline
        
        🏗️ TECHNICAL DECISIONS (6 Mei):
        - Memutuskan pakai PostgreSQL untuk database
        - Architecture: microservices dengan n8n orchestration
        - Deployment: Docker Compose di VPS
        
        📎 Sumber: Projects/Alpha/2026-05-05-weekly-sync.md"

4. TELEGRAM BOT sends synthesized answer
   └─ User receives contextual answer with source references
```

**Result:** AI retrieves and synthesizes information from Obsidian notes with source attribution.

**Key Points:**
- ✅ **Semantic Search** - Finds relevant notes even with different wording
- ✅ **Source Attribution** - Shows which Obsidian files were used
- ✅ **Time Filtering** - Can filter by date range
- ✅ **Tag Support** - Leverages Obsidian tags for better filtering
- ✅ **Dual Storage** - Reads from local vault or R2 backup

---

### Example 7: Meeting Preparation with Obsidian Context

**User Input:** `/siapkan meeting dengan Client B besok`

**Flow:**

```
1. TELEGRAM BOT parses command
   └─ Intent: meeting_preparation
   └─ Entity: "Client B", date: "tomorrow"

2. LANGGRAPH AGENT orchestrates preparation
   ├─ PARALLEL DATA COLLECTION (4 sources)
   │
   ├─ [1] Fetch Calendar Info
   │   └─ GET http://calcom:3000/api/bookings?client=Client+B
   │       Response: {
   │         "title": "Client B - Q2 Review",
   │         "time": "2026-05-12T10:00:00Z",
   │         "duration": "60 minutes"
   │       }
   │
   ├─ [2] Search Obsidian for Client B History
   │   └─ POST ${QDRANT_URL}/collections/knowledge/points/search
   │       Filter: tags contains "client-b"
   │       Response: [
   │         "Clients/Client-B/profile.md",
   │         "Clients/Client-B/2026-Q1-review.md",
   │         "Clients/Client-B/contract-details.md"
   │       ]
   │
   ├─ [3] Search Past Meeting Notes
   │   └─ POST ${QDRANT_URL}/collections/knowledge/points/search
   │       Filter: tags contains "client-b" AND "meeting-notes"
   │       Response: [
   │         "Meetings/2026-02-15-client-b-kickoff.md",
   │         "Meetings/2026-03-20-client-b-progress.md"
   │       ]
   │
   └─ [4] Search Pending Tasks Related to Client B
       └─ POST ${QDRANT_URL}/collections/tasks/points/search
           Filter: payload.client = "Client B" AND status = "pending"
           Response: [
             { "title": "Finalize Q2 report for Client B", "status": "pending" },
             { "title": "Prepare demo environment", "status": "in_progress" }
           ]

3. FETCH FULL CONTENT FROM OBSIDIAN
   ├─ Read: Clients/Client-B/profile.md
   │   Content:
   │   ---
   │   # Client B Profile
   │   - Industry: FinTech
   │   - Contact: John Doe (CTO)
   │   - Contract: $50k/year, expires Dec 2026
   │   - Pain Points: Legacy system migration
   │   - Tech Stack: Java, PostgreSQL, AWS
   │   ---
   │
   ├─ Read: Clients/Client-B/2026-Q1-review.md
   │   Content:
   │   ---
   │   # Q1 Review - Client B
   │   - Delivered: API integration module
   │   - Feedback: Very satisfied with performance
   │   - Concerns: Timeline for Phase 2
   │   - Next Steps: Discuss Q2 roadmap
   │   ---
   │
   └─ Read: Meetings/2026-03-20-client-b-progress.md
       Content:
       ---
       # Progress Meeting - Client B
       - Discussed: Phase 1 completion
       - Action Items: Prepare Phase 2 proposal
       - Client requested: Cost breakdown for scaling
       ---

4. AI GENERATES MEETING BRIEF
   └─ POST https://api.openai.com/v1/chat/completions
       System: "You are a personal secretary preparing a meeting brief."
       Context: [All fetched Obsidian content + calendar + tasks]
       
       Response:
       "📋 MEETING PREPARATION: Client B - Q2 Review
        
        🗓️ MEETING DETAILS:
        - Date: Besok, 12 Mei 2026
        - Time: 10:00 AM
        - Duration: 60 minutes
        - Topic: Q2 Review
        
        👤 CLIENT PROFILE:
        - Company: Client B (FinTech)
        - Contact: John Doe (CTO)
        - Contract: $50k/year (expires Dec 2026)
        - Tech Stack: Java, PostgreSQL, AWS
        
        📊 Q1 RECAP:
        - ✅ Delivered: API integration module
        - 😊 Feedback: Very satisfied with performance
        - ⚠️ Concern: Timeline for Phase 2
        
        📝 LAST MEETING (20 Mar):
        - Discussed Phase 1 completion
        - Client requested cost breakdown for scaling
        
        ✅ PENDING TASKS:
        - [ ] Finalize Q2 report for Client B
        - [⏳] Prepare demo environment (in progress)
        
        💡 TALKING POINTS:
        1. Present Q2 roadmap
        2. Address Phase 2 timeline concerns
        3. Provide scaling cost breakdown (from last meeting)
        4. Discuss contract renewal (expires Dec 2026)
        
        📎 Reference Files:
        - Clients/Client-B/profile.md
        - Clients/Client-B/2026-Q1-review.md
        - Meetings/2026-03-20-client-b-progress.md"

5. CREATE PREPARATION NOTE IN OBSIDIAN
   └─ Write new file: Meetings/2026-05-12-client-b-prep.md
       Content: [Generated meeting brief above]
       
   └─ Sync to R2 for backup
       └─ PUT https://r2.cloudflarestorage.com/secretary-files/
               obsidian/Meetings/2026-05-12-client-b-prep.md

6. INDEX NEW NOTE TO QDRANT
   └─ POST ${QDRANT_URL}/collections/knowledge/points
       {
         "points": [{
           "id": "note_prep_client_b_20260512",
           "vector": [0.345, 0.678, ...],
           "payload": {
             "title": "Meeting Prep: Client B Q2 Review",
             "file_path": "Meetings/2026-05-12-client-b-prep.md",
             "tags": ["client-b", "meeting-prep", "q2-review"],
             "created_at": "2026-05-11T15:30:00Z",
             "source": "obsidian"
           }
         }]
       }

7. TELEGRAM BOT sends preparation brief
   └─ Message: [Full meeting brief with formatting]
   └─ Attachment: Link to Obsidian note
```

**Result:** Comprehensive meeting preparation by aggregating data from Obsidian, calendar, and tasks.

**Obsidian Workflow:**
```
Obsidian Vault → Qdrant (search) → AI (synthesize) → New Note → Obsidian → R2 (backup)
     ↓                                                                ↓
  (read)                                                          (write)
```

**Key Points:**
- ✅ **Context Aggregation** - Pulls from multiple Obsidian notes
- ✅ **Automatic Note Creation** - Saves preparation brief back to Obsidian
- ✅ **Bidirectional Sync** - Reads from and writes to Obsidian
- ✅ **Tag-Based Filtering** - Uses Obsidian tags for precise search
- ✅ **Source Tracking** - Shows which notes were referenced
- ✅ **Backup Integration** - Auto-syncs new notes to R2

---

## 🔄 Key Features & Workflows

### 1. **Context-Aware Conversations**

Setiap percakapan disimpan di Qdrant sebagai vector embeddings. Ketika user bertanya, sistem:
- Retrieve 5 percakapan paling relevan dari history
- Gunakan sebagai context untuk LLM
- Generate response yang aware terhadap percakapan sebelumnya

**Example:**
```
User: "Kapan meeting dengan Client A?"
Bot: "Meeting dengan Client A dijadwalkan jam 14:00 hari ini."

[2 hours later]
User: "Apa yang perlu saya siapkan?"
Bot: "Untuk meeting Client A jam 14:00, saya sarankan:
      - Review proposal yang sudah dibuat
      - Siapkan demo produk
      - Bawa kontrak untuk ditandatangani"
```

Bot ingat context "meeting Client A" dari percakapan sebelumnya.

---

### 2. **Proactive Reminders**

LangGraph agent expose scheduled endpoints yang dipanggil n8n setiap 5 menit via workflow scheduler (Daily Briefing 07:00, Task Reminder 09/13/17 weekday):

```toml
[daemon]
enabled = true
check_interval = "5m"
proactive_hours = { start = 7, end = 22 }

[daemon.routines]
morning_briefing = "0 7 * * *"      # 07:00 daily
task_reminder = "0 */2 * * *"       # Every 2 hours
eod_summary = "0 21 * * *"          # 21:00 daily
```

**Reminder Logic:**
- 1 hour before meeting → Send reminder + preparation suggestions
- Task deadline approaching → Notify with priority level
- End of day → Summary of completed/pending tasks

---

### 3. **Multi-Tool Orchestration**

Single user query dapat trigger multiple tools secara parallel:

**User:** "Siapkan meeting dengan Client B minggu depan"

**AI Agent executes:**
```python
# Parallel execution
results = await asyncio.gather(
    check_calendar(next_week),           # Cal.com API
    search_client_info("Client B"),      # Qdrant search
    get_previous_meetings("Client B"),   # Qdrant history
    create_task("Prepare meeting agenda") # Qdrant tasks
)

# Generate response with all context
response = llm.generate(
    f"Schedule meeting considering: {results}"
)
```

**Result:** AI suggests optimal time slot based on calendar availability, previous meeting notes, and creates preparation tasks automatically.

---

### 4. **Knowledge Base Auto-Sync**

Cron job runs every 30 minutes to sync Obsidian vault:

```bash
# scripts/sync_obsidian.py
*/30 * * * * python3 /opt/ai-secretary/scripts/sync_obsidian.py
```

**Sync Process:**
1. Scan Obsidian vault for new/modified `.md` files
2. Extract text content and metadata
3. Generate embeddings using LLM
4. Upsert to Qdrant "knowledge" collection
5. Upload original files to Cloudflare R2 for backup

**Result:** Knowledge base always up-to-date, searchable by semantic similarity.

---

### 5. **Self-Improving Skills**

User dapat menyimpan prosedur/pattern yang sering dipakai ke Qdrant `skills` collection, lalu recall via semantic search.

**Simpan skill:**
```
/skill log deploy-bot | Build image, push main, CI auto-deploy, verify docker ps
```

**Recall skill:**
```
/skill deploy
→ 🧠 Skills matching "deploy":
  1. deploy-bot (score: 0.43)
     Build image, push main, CI auto-deploy, verify docker ps
     • git push main
     • wait CI green
     • docker ps verify
```

**How it works:**
1. `/skill log <name> | <description>` → embed name+description → store in Qdrant `skills` collection
2. `/skill <query>` → embed query → cosine similarity search → return top-5 matches
3. Semantic search means "cara deploy" or "push production" juga match "deploy-bot"

**Payload schema:**
```json
{
  "name": "deploy-bot",
  "description": "Build image, push main, CI auto-deploy, verify docker ps",
  "steps": ["git push main", "wait CI green", "docker ps verify"],
  "tags": ["ops", "deploy"],
  "user_id": "561827493"
}
```

**Result:** Personal knowledge base of procedures that grows over time, searchable by meaning not just keywords.

---

## 🔐 Security & Authentication Flow

### Layer 1: User Authentication
```
Telegram Bot
├─ Whitelist: ALLOWED_USER_IDS=[123456789, 987654321]
└─ Reject: Any user not in whitelist
```

### Layer 2: Service-to-Service Auth
```
Internal Services (Docker Network)
├─ n8n → langgraph-agent: No auth (isolated network)

External Services
├─ Agent → Qdrant Cloud: API Key (QDRANT_API_KEY)
├─ Agent → Cal.com: Bearer Token (CALCOM_API_KEY)
├─ Agent → R2: AWS Signature V4 (R2_ACCESS_KEY_ID + SECRET)
├─ LLM Provider: Bearer Token (LLM_API_KEY)
└─ SMTP: Username/Password (SMTP_USER + PASSWORD)
```

### Layer 3: Network Security
```
Caddy Reverse Proxy (HTTPS/TLS)
├─ n8n.yourdomain.com → http://n8n:5678
├─ cal.yourdomain.com → http://calcom:3000
└─ All traffic encrypted with Let's Encrypt SSL
```

---

## 📊 Monitoring & Health Checks

Health check script runs every 5 minutes via cron:

```bash
# scripts/health_check.sh
*/5 * * * * /opt/ai-secretary/scripts/health_check.sh
```

**Checks:**
```bash
# Check each service
curl -f http://localhost:5678/healthz    # n8n
curl -f http://localhost:3000/api/health # Cal.com
curl -f http://localhost:8090/health     # langgraph-agent

# Check external services
curl -f "${QDRANT_URL}/healthz" -H "api-key: ${QDRANT_API_KEY}"  # Qdrant Cloud

# If any fails
if [ $? -ne 0 ]; then
    # Send alert to Telegram
    curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
         -d "chat_id=$ADMIN_ID" \
         -d "text=⚠️ Service DOWN: $service_name"
fi
```

**Result:** Immediate notification if any service goes down.

---

## 📡 Multi-VPS Monitoring (Prometheus + Alertmanager)

Selain health check internal di atas, stack juga punya **Prometheus + Alertmanager** untuk monitor banyak VPS sekaligus dengan alert ke Telegram.

### Components

| Service | Role |
|---|---|
| `node_exporter` | Per-VPS metrics agent (CPU, RAM, disk, network) — listen di port 19100 |
| `prometheus` | Scrape semua node_exporter setiap 30 detik, retain 30 hari |
| `alertmanager` | Group + dedup + route alert → Telegram |
| Telegram Bot | `/monitor` command untuk query Prometheus dari chat |

### Pipeline

```
node_exporter (each VPS:19100)
   → Prometheus (scrape, evaluate alert rules)
   → Alertmanager (group, dedup, route)
   → Telegram (using same bot_token + chat_id)
```

### Telegram Commands

- `/monitor` — list semua VPS dengan status up/down + CPU/RAM/disk %, plus active alerts
- `/monitor <name>` — detail untuk satu VPS (CPU, load, RAM, swap, disk, uptime, alerts)
- `/vps` — local pro-secretary detail (existing, via agent `/api/vps_status`)

### Alert Rules

10 rule di [`prometheus/alert_rules.yml`](prometheus/alert_rules.yml):

| Rule | Trigger | Severity |
|---|---|---|
| `InstanceDown` | `up == 0` for 2m | critical |
| `HighCPU` | > 85% for 5m | warning |
| `HighMemory` | > 85% for 5m | warning |
| `CriticalMemory` | > 92% for 2m | critical |
| `DiskWarning` | > 80% for 5m | warning |
| `DiskCritical` | > 90% for 2m | critical |
| `DiskFillPrediction` | predict_linear < 0 in 24h | warning |
| `HighSwap` | > 50% for 10m | warning |
| `HighLoad` | load5 > 2× CPU cores for 10m | warning |
| `NetworkErrors` | err rate > 10/s for 5m | warning |

### Adding a New VPS Target

1. **Install node_exporter** di target VPS, listen on port `19100` (non-standard, lihat "Why port 19100" di bawah):
   ```bash
   sudo apt install -y prometheus-node-exporter
   echo 'ARGS="--web.listen-address=:19100"' | sudo tee /etc/default/prometheus-node-exporter
   sudo systemctl enable --now prometheus-node-exporter
   sudo systemctl restart prometheus-node-exporter
   ```

2. **Restrict port 19100** ke pro-secretary IP only (jangan expose ke public):
   ```bash
   # If VPS uses UFW (Ubuntu default):
   sudo ufw allow proto tcp from <PRO_SECRETARY_IP> to any port 19100 comment 'prometheus pro-secretary'
   sudo ufw reload

   # If VPS uses raw iptables:
   sudo iptables -I INPUT -p tcp --dport 19100 -s <PRO_SECRETARY_IP> -j ACCEPT
   sudo iptables -A INPUT -p tcp --dport 19100 -j DROP
   sudo apt install iptables-persistent
   sudo netfilter-persistent save
   ```

3. **Tambah target** di [`prometheus/prometheus.yml`](prometheus/prometheus.yml) — append ke existing `node` job, jangan buat job baru:
   ```yaml
   - targets: ["<IP>:19100"]
     labels:
       instance_name: "<short-name>"
       provider: "<digitalocean|hetzner|biznet|...>"
   ```

4. **Push** ke main → CI auto-deploy. Deploy step `docker compose up -d --force-recreate prometheus alertmanager` memastikan config bind-mount picked up (no manual reload needed).

### Why port 19100 (NOT 9100)

Onboarding VPS pertama dari Biznet Indonesia (erpstg) → DO Singapore (pro-secretary) menemukan: SYN ke `:9100` silently dropped in transit. Source IP sama, dest IP sama, tapi `:22`/`:443`/`:3270` reachable. Kemungkinan ISP-level filter pada well-known Prometheus port. Switch ke `:19100` immediate fix. Standard ini diadopsi untuk semua VPS supaya tidak ulang debug.

Bonus: avoids opportunistic port scans for `:9100`.

5. **Verify**:
   ```bash
   docker exec prometheus wget -qO- 'http://localhost:9090/api/v1/targets'
   ```
   Atau via Telegram: `/monitor`.

### Why Prometheus over Grafana?

Stack sengaja **tidak** include Grafana. Reasoning:

- **Goal utama** = "alert kalau VPS sakit" → ter-solve dengan Prometheus + Alertmanager + Telegram
- Grafana = +1 service to maintain, butuh auth, butuh dashboard provisioning
- Prometheus retain 30 hari → data history sudah ada saat Grafana ditambahkan nanti
- Tunggu sampai user actually butuh trend visualization, baru attach Grafana

Untuk attach Grafana nanti, tinggal tambah container Grafana yang point ke `http://prometheus:9090` sebagai data source.

### Why bot_token diinjeksi via entrypoint script?

Alertmanager tidak support `${ENV_VAR}` substitution di config natively. Solusi:

- [`prometheus/alertmanager.yml`](prometheus/alertmanager.yml) berisi placeholder: `PLACEHOLDER_BOT_TOKEN`, `PLACEHOLDER_CHAT_ID`
- [`prometheus/alertmanager-entrypoint.sh`](prometheus/alertmanager-entrypoint.sh) jalan saat container start, sed-substitute placeholder dari env var ke config file aktual
- Container reuse `TELEGRAM_BOT_TOKEN` + `TELEGRAM_ALLOWED_USERS` dari `.env` — no extra secrets needed

---

## 🎯 Use Case Examples

### Personal Assistant
- "Apa yang harus saya kerjakan hari ini?"
- "Ingatkan saya 1 jam sebelum meeting"
- "Cari notes tentang project X"
- "Buatkan summary dari meeting kemarin"

### Project Management
- "Buat task: Review PR #123"
- "Apa status project Alpha?"
- "Siapa yang handle feature authentication?"
- "Deadline apa yang mendekat minggu ini?"

### Knowledge Management
- "Cari dokumentasi tentang API integration"
- "Bagaimana cara setup CI/CD pipeline?"
- "Apa yang kita diskusikan tentang database migration?"
- "Simpan notes ini ke project Beta"

### Calendar Management
- "Jadwalkan meeting dengan tim engineering"
- "Reschedule meeting Client A ke besok"
- "Apa jadwal saya minggu depan?"
- "Block calendar saya untuk focus time"

### Skills & Procedures
- `/skill log deploy-bot | Build image, push main, CI auto-deploy, verify docker ps`
- `/skill log fix-retrieval | Cek path_terms, expand irrelevant filter, test ulang`
- `/skill deploy` — recall prosedur deploy via semantic search
- `/skill tunnel` — recall prosedur setup SSH tunnel

---

## 📋 Table of Contents

- [Architecture](#-architecture)
- [How It Works](#-how-it-works)
- [AI Agent Engine](#-ai-agent-engine)
- [LLM Provider Configuration](#-llm-provider-configuration)
- [Prerequisites](#-prerequisites)
- [Monthly Cost Estimate](#-monthly-cost-estimate)
- [Quick Start](#-quick-start)
- [Docker Compose](#-docker-compose)
- [Environment Variables](#-environment-variables)
- [Component Setup](#-component-setup)
- [Reverse Proxy](#-reverse-proxy)
- [Security](#-security)
- [Backup Strategy](#-backup-strategy)
- [Health Monitoring](#-health-monitoring)
- [Troubleshooting](#-troubleshooting)
- [Post-Installation](#-post-installation)
- [Roadmap](#-roadmap)
- [License](#-license)
- [Credits](#-credits)

## 🔧 Prerequisites

### Hardware Requirements

> **Important:** PostgreSQL, Qdrant, dan Cloudflare R2 adalah external services yang TIDAK berjalan di server Anda. Resource requirements di bawah hanya untuk 7 containers lokal: n8n, langgraph-agent, Cal.com, Telegram Bot, Prometheus, Alertmanager, dan Caddy.

#### Minimum (Personal Use - Single User)
- **CPU:** 4 cores (x86_64)
- **RAM:** 8 GB
- **Storage:** 100 GB SSD
- **Network:** 10 Mbps upload/download
- **Swap:** 8 GB (for OOM protection)
- **Disk I/O:** 1000+ IOPS, 50+ MB/s throughput

**Why these specs:**
- 8GB RAM sufficient since Qdrant runs externally (saves 3-5 GB)
- 100GB storage sufficient (no local vector data)
- 4 cores handles concurrent AI operations with external services
- SSD recommended for Cal.com and n8n performance

#### Recommended (Production Use - Small Team)
- **CPU:** 6 cores (x86_64)
- **RAM:** 16 GB
- **Storage:** 200 GB SSD
- **Network:** 25 Mbps upload/download
- **Swap:** 8 GB
- **Disk I/O:** 3000+ IOPS, 100+ MB/s throughput

#### Optimal (High-Volume/Enterprise)
- **CPU:** 8 cores (x86_64)
- **RAM:** 32 GB
- **Storage:** 500 GB SSD
- **Network:** 100 Mbps upload/download
- **Swap:** 16 GB
- **Disk I/O:** 5000+ IOPS, 200+ MB/s throughput

#### Resource Breakdown (Minimum Tier)

**What runs on YOUR server (7 containers):**
- n8n: ~1.5-2 GB RAM, 1 core
- Cal.com: ~1-1.5 GB RAM, 0.5-1 core (app only, database is external)
- langgraph-agent: ~1-2 GB RAM, 1 core
- Telegram Bot: ~0.3-0.5 GB RAM, negligible CPU
- Prometheus: ~0.3-1 GB RAM, 0.2 core (multi-VPS scrape, 30d retention)
- Alertmanager: ~50-100 MB RAM, negligible CPU
- Caddy: ~0.2-0.3 GB RAM, negligible CPU
- OS + Docker: ~2-3 GB RAM, 0.5-1 core

**Total baseline:** 6-9 GB RAM, spikes to 10-12 GB during LLM inference

**What runs EXTERNALLY (not on your server):**
- PostgreSQL: Hosted by Supabase/Neon/Railway (only network bandwidth)
- Qdrant: Hosted by Qdrant Cloud (only network bandwidth)
- Cloudflare R2: Object storage (only network bandwidth)
- LLM Provider: API calls to OpenAI/Groq/etc (only network bandwidth)

#### Important Notes

- **SSD recommended** (NVMe not required since Qdrant runs externally)
- **Enable swap space** to prevent OOM crashes during LLM inference:
  ```bash
  sudo fallocate -l 8G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  ```
- **Plan for 20-30% headroom** - LLM inference causes 2-3x CPU/RAM spikes
- **Storage grows over time:** Plan for 20-50 GB growth per year (logs, backups)

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
- **8090** - langgraph-agent
- **3000** - Cal.com

> **Note:** PostgreSQL menggunakan external provider (Supabase/Neon/Railway), tidak ada container lokal.
> **Note:** Qdrant menggunakan Qdrant Cloud (external service), tidak ada container lokal.
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

### Scenario 1: Minimal Setup (Personal Use - Single User)

> **Note:** Hardware requirements: 4 cores, 8GB RAM, 100GB storage. All heavy services (Qdrant, PostgreSQL) run externally.

**Infrastructure:**
- **VPS:** $8-15/month
  - Hetzner CX21 (4 cores, 8GB): €9/month = ~$10/month ← **Recommended** (matches minimum spec)
  - Contabo VPS S (4 cores, 8GB): €7/month = ~$8/month ← **Budget option**
  - OVH Starter (4 cores, 8GB): ~$12/month ← **Alternative**
  
- **Domain + SSL:** $1-2/month
  - Domain (.com): ~$12/year = $1/month
  - SSL: Free (Let's Encrypt via Caddy)
  
- **PostgreSQL Database (External):** $0-10/month
  - Supabase: Free tier (500MB, 2GB bandwidth) ← **Sufficient for personal use**
  - Neon: Free tier (0.5GB storage, 3GB data transfer)
  - Railway: $5/month (shared CPU, 512MB RAM)
  - **Note:** Database runs on provider, NOT on your VPS
  
- **Qdrant Cloud (External):** $0/month
  - Free tier: 1GB storage, 1M vectors ← **Sufficient for personal use**
  - **Note:** Vector database runs on Qdrant Cloud, NOT on your VPS
  
- **Cloudflare R2 (External):** $0-5/month
  - Free tier: 10GB storage, unlimited egress
  - Paid: $0.015/GB/month beyond 10GB
  - **Note:** File storage runs on Cloudflare, NOT on your VPS
  
- **Backup Storage (Optional):** $1-5/month
  - Backblaze B2: $0.005/GB = ~$1.25 for 250GB
  - Wasabi: $6.99/TB/month (minimum, overkill for this tier)

**LLM Costs (OpenAI-compatible Provider):**
- **Light Usage:** ~$10-30/month
  - Using efficient models (gpt-3.5-turbo, claude-haiku)
  - ~1000-3000 requests/month

**Total: $19-52/month** (personal use, cost-optimized)

---

### Scenario 2: Production Setup (Small Team)

**Infrastructure:**
- **VPS/Dedicated Server:** $15-30/month
  - Hetzner CX31 (6 cores, 16GB): €15/month = ~$16/month ← **Recommended**
  - Contabo VPS M (6 cores, 16GB): €12/month = ~$13/month ← **Budget option**
  - OVH Advance-1 (6 cores, 16GB): ~$25/month ← **Alternative**
  
- **Domain + SSL:** $1-2/month

- **PostgreSQL Database (External):** $10-25/month
  - Supabase Pro: $25/month (8GB storage, 50GB bandwidth)
  - Neon Scale: $19/month (10GB storage, autoscaling)
  - Railway Pro: $20/month (8GB RAM, shared CPU)
  - **Note:** Database runs on provider, NOT on your VPS
  
- **Qdrant Cloud (External):** $0-25/month
  - Free tier: 1GB storage, 1M vectors
  - Starter: $25/month (5GB storage, 5M vectors)
  - **Note:** Vector database runs on Qdrant Cloud, NOT on your VPS
  
- **Cloudflare R2 (External):** $5-15/month
  - Free tier: 10GB storage
  - Typical usage: 50-100GB = $0.75-1.50/month
  - **Note:** File storage runs on Cloudflare, NOT on your VPS
  
- **Backup Storage:** $2-7/month
  - Backblaze B2: $0.005/GB = ~$2.50 for 500GB
  - Wasabi: $6.99/TB/month

**LLM Costs (OpenAI-compatible Provider):**
- **Moderate Usage:** ~$30-80/month
  - Mix of efficient and quality models
  - ~5000-10000 requests/month
  - Using gpt-4, claude-sonnet, or similar

**Total: $58-172/month** (production-ready, small team)

---

### Scenario 3: High-Volume/Enterprise

**Infrastructure:**
- **Dedicated Server:** $40-80/month
  - Hetzner AX41 (Ryzen 5 3600, 32GB RAM): ~€39/month (~$42) ← **Recommended**
  - OVH Scale-2 (8 cores, 32GB RAM): ~$60/month ← **Alternative**
  - Hetzner AX61 (Ryzen 7 3700X, 64GB RAM): ~€59/month (~$64) ← **High headroom**
  
- **Domain + SSL:** $1-2/month

- **PostgreSQL Database (External):** $50-200/month
  - Supabase Team: $599/month (unlimited storage, dedicated resources) ← **Overkill for most**
  - Neon Business: Custom pricing (dedicated compute)
  - AWS RDS: $50-200/month (db.t3.medium to db.m5.large)
  - Supabase Pro: $25/month (often sufficient for enterprise)
  - **Note:** Database runs on provider, NOT on your VPS
  
- **Qdrant Cloud (External):** $25-95/month
  - Starter: $25/month (5GB storage, 5M vectors)
  - Standard: $95/month (20GB storage, 20M vectors)
  - **Note:** Vector database runs on Qdrant Cloud, NOT on your VPS
  
- **Cloudflare R2 (External):** $10-30/month
  - Typical usage: 500GB-1TB = $7.50-15/month
  - **Note:** File storage runs on Cloudflare, NOT on your VPS
  
- **Backup Storage:** $5-15/month
  - Backblaze B2: $0.005/GB = ~$5 for 1TB
  - Wasabi: $6.99/TB/month (flat rate)

**LLM Costs (OpenAI-compatible Provider):**
- **Heavy Usage:** ~$100-300/month
  - High-quality models (gpt-4, claude-opus)
  - ~20000-50000 requests/month
  - Production workloads

**Total: $230-620/month** (enterprise-grade, high-volume)

---

### Cost Comparison Table

| Component | Scenario 1<br/>(Personal) | Scenario 2<br/>(Small Team) | Scenario 3<br/>(Enterprise) |
|-----------|--------------------------|-----------------------------|-----------------------------|
| **Server/VPS** | $8-15 | $15-30 | $40-80 |
| **Domain + SSL** | $1-2 | $1-2 | $1-2 |
| **PostgreSQL (External)** | $0-10 | $10-25 | $50-200 |
| **Qdrant Cloud (External)** | $0 | $0-25 | $25-95 |
| **Cloudflare R2 (External)** | $0-5 | $5-15 | $10-30 |
| **Backup Storage** | $1-5 | $2-7 | $5-15 |
| **LLM API (Provider)** | $10-30 | $30-80 | $100-300 |
| **Usage Level** | Light | Moderate | Heavy |
| **Setup Complexity** | 🔧 Low | 🔧🔧 Medium | 🔧🔧🔧 High |
| **TOTAL/month** | **$19-52** | **$58-172** | **$230-620** |

---

### Additional Optional Costs

- **Telegram Bot:** Free (unlimited messages)
- **Cal.com:** Free (self-hosted)
- **n8n:** Free (self-hosted)
- **Qdrant Cloud:** Free tier (1GB storage, 1M vectors)
- **Cloudflare R2:** Free 10GB, $0.015/GB after (S3-compatible, no egress fees)
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

### Qdrant Cloud Provider Recommendations

#### Free Tier (Development/Personal Use)
- **Qdrant Cloud Free:** 1GB storage, 1M vectors
  - ✅ Generous free tier for personal use
  - ✅ Fully managed, no maintenance
  - ✅ Automatic backups and updates
  - ✅ Multiple regions available
  - 🔗 [cloud.qdrant.io](https://cloud.qdrant.io)

#### Production Options
- **Qdrant Cloud Starter:** $25/month
  - 5GB storage, 5M vectors
  - Dedicated resources
  - Priority support

- **Qdrant Cloud Standard:** $95/month
  - 20GB storage, 20M vectors
  - High availability
  - Advanced monitoring

#### Enterprise Options
- **Qdrant Cloud Enterprise:** Custom pricing
  - Unlimited storage
  - Dedicated cluster
  - SLA guarantees
  - Custom configurations

#### Alternative Providers
- **Pinecone:** $70+/month (serverless vector DB)
  - ✅ Serverless, auto-scaling
  - ❌ Different API (not Qdrant-compatible)
  
- **Weaviate Cloud:** $25+/month
  - ✅ Managed vector DB
  - ❌ Different API (not Qdrant-compatible)

> **Recommendation:** Use **Qdrant Cloud** for direct compatibility with this project. Free tier is sufficient for personal use (10k-50k documents).

---

### Cost Optimization Tips

1. **Start with Scenario 1** (Minimal) untuk testing, scale up sesuai kebutuhan
2. **Use free tier services** - Supabase/Neon + Qdrant Cloud free tier cukup untuk development
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
- **This Stack (Scenario 1):** $19-52/month
  - ✅ Unlimited usage
  - ✅ 36+ models to choose from
  - ✅ Complete customization
  - ✅ Integration with your entire workflow
  - ✅ Self-hosted infrastructure
  - ✅ No vendor lock-in

**Break-even:** If you use >1 AI service, self-hosting provides more value and flexibility.

---

## 🤖 AI Agent Engine

Stack menggunakan **custom LangGraph agent** yang dibangun di [`langgraph-agent/`](langgraph-agent/). Implementasinya adalah FastAPI + LangGraph StateGraph + fastembed ONNX (384-dim, model `sentence-transformers/all-MiniLM-L6-v2`), di-containerize dan di-deploy via docker-compose.

**Kenapa LangGraph?** State machine eksplisit yang mudah di-extend (tambah node untuk intent baru), sementara sisi produksinya tetap ringan (satu container, memory limit 1 GB, cold start <10 detik). Workflow: `understand → retrieve context → generate response`. HTTP endpoint dipanggil dari n8n dan Telegram bot (`/api/chat`, `/api/search`, `/api/task`, `/api/notify`, `/api/briefing`, `/api/meeting_notes`, `/api/deps/scan`, `/api/sync_vault`, dll).

Detail teknis lihat [`langgraph-agent/app/workflow.py`](langgraph-agent/app/workflow.py) dan [`langgraph-agent/app/main.py`](langgraph-agent/app/main.py).

---

## 🧠 LLM Provider Configuration

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

#### LangGraph Agent (docker-compose)

Current stack. See [`docker-compose.yml`](docker-compose.yml) for the authoritative definition. Agent reads LLM credentials from the environment:

```yaml
  langgraph-agent:
    build: ./langgraph-agent
    environment:
      - LLM_API_KEY=${LLM_API_KEY}
      - LLM_BASE_URL=${LLM_BASE_URL}
      - LLM_MODEL=${LLM_MODEL}
      - QDRANT_URL=${QDRANT_URL}
      - QDRANT_API_KEY=${QDRANT_API_KEY}
      - AGENT_SECRET=${AGENT_SECRET}
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

### Setup (4 cores / 8GB RAM minimum)

Stack terdiri dari 7 container lokal (n8n, langgraph-agent, calcom, telegram-bot, prometheus, alertmanager, caddy). Heavy services (Qdrant, PostgreSQL) run externally untuk menghemat resource.

```bash
# 1. Clone repository
git clone https://github.com/yourusername/ai-secretary-stack.git
cd ai-secretary-stack

# 2. Setup swap space (recommended for 8GB RAM)
chmod +x scripts/setup_swap.sh
sudo ./scripts/setup_swap.sh 8G

# 3. Sign up for external services (free tiers available)
# - Qdrant Cloud: https://cloud.qdrant.io (1GB free)
# - PostgreSQL: https://supabase.com or https://neon.tech (free tier)
# - Cloudflare R2: https://dash.cloudflare.com (10GB free)

# 4. Copy and configure environment
cp .env.example .env
nano .env
# Set QDRANT_URL, QDRANT_API_KEY, DATABASE_URL from providers above

# 5. Deploy stack
docker compose up -d

# 6. Check status
docker compose ps
docker stats

# 7. Verify resource usage (should be under 6GB)
free -h
```

**See detailed guide:** [DEPLOYMENT_LOW_RESOURCE.md](DEPLOYMENT_LOW_RESOURCE.md)

**Cost:** $19-52/month (VPS + free tier services)

---

### Which VPS Should I Choose?

| Your Budget | Recommended VPS | Why |
|-------------|----------------|-----|
| **$8-10/month** | Hetzner CX21 (4 cores, 8GB) | Minimum spec, works with swap |
| **$13-16/month** | Hetzner CX31 (6 cores, 16GB) | Comfortable headroom |
| **$25-45/month** | Hetzner AX41 (dedicated, 32GB) | Production-grade, high throughput |

---

## 🛠️ Local Development

Setup minimum untuk reproduce CI gates lokal sebelum push.

### Prerequisites

- Python 3.11 (CI authoritative; py3.12 jalan tapi versi resmi 3.11)
- `pip`, `git`, `gh` CLI

### One-time setup

```bash
git clone <repo>
cd pro-secretary

# Install runtime + test deps
pip install -r telegram-bot/requirements.txt
pip install -r langgraph-agent/requirements.txt
pip install pytest pytest-cov ruff mypy pre-commit

# Optional: enable pre-commit hooks (mirror CI lint locally)
pre-commit install --hook-type pre-commit --hook-type pre-push
```

### Run all CI gates locally

```bash
# 1. Compile (catches syntax errors)
python3 -m compileall -q telegram-bot langgraph-agent

# 2. Pyflakes-class lint (catches undefined names, unused imports)
python3 -m ruff check --select=F telegram-bot langgraph-agent tests

# 3. Type check (lenient, whole package)
python3 -m mypy --config-file=mypy.ini telegram-bot langgraph-agent

# 4. Type check (strict, whitelisted modules only)
python3 -m mypy --strict \
  langgraph-agent/app/embedding.py \
  langgraph-agent/app/journal.py \
  langgraph-agent/app/telegram.py

# 5. Orphan-reference checks (handler/scheduler refs resolved)
python3 scripts/lint_orphan_refs.py

# 6. Tests + coverage floor
python3 -m pytest -q
```

Or run the same set via pre-commit:

```bash
pre-commit run --all-files                            # ruff + actionlint + compileall + orphan-refs
pre-commit run --all-files --hook-stage pre-push      # adds mypy lenient + strict
```

### Local feedback loop

```bash
# Fast iterate (single test file)
python3 -m pytest tests/test_journal.py -v

# Coverage report (per-module)
python3 -m pytest --cov=bot --cov=app --cov-report=term-missing -q

# Skip a hook for one commit
SKIP=mypy git commit -m "..."
```

### Coverage floor

`pytest.ini` enforces a project-wide coverage floor (`--cov-fail-under=23` as of 2026-05-31). Tests fail if coverage drops below the floor; bump only after adding new tests.

### Tightening type safety

Lenient mypy is the baseline (whole package). The strict gate covers a whitelist of well-typed modules in `.github/workflows/deploy.yml` (mypy strict step). To add a new module to the strict whitelist:

1. Run `mypy --strict path/to/module.py` until it passes
2. Add the path to the strict step in `.github/workflows/deploy.yml`
3. Add the path to the `mypy-strict` hook in `.pre-commit-config.yaml`

---

## 🐳 Docker Compose

Definisi service yang authoritative ada di [`docker-compose.yml`](docker-compose.yml) di root repo. Stack terdiri dari 7 container lokal:

| Service | Image | Memory limit | Role |
|---|---|---|---|
| `n8n` | `n8nio/n8n:latest` | 1.5 GB | Workflow orchestrator |
| `langgraph-agent` | built from `./langgraph-agent/` | 1 GB | AI reasoning + Telegram egress |
| `calcom` | `calcom/cal.com:latest` | 1.5 GB | Calendar |
| `telegram-bot` | built from `./telegram-bot/` | 512 MB | Telegram inbound |
| `prometheus` | `prom/prometheus:v3.4.0` | 1 GB | Multi-VPS metrics scrape |
| `alertmanager` | `prom/alertmanager:v0.28.1` | 256 MB | Alert routing → Telegram |
| `caddy` | `caddy:2-alpine` | 256 MB | HTTPS reverse proxy |

External services (tidak di-container-kan): Qdrant Cloud, PostgreSQL (Supabase/Neon/Railway), Cloudflare R2, LLM Provider.

Deploy via CI: push ke `main` → GitHub Actions run [`deploy.yml`](.github/workflows/deploy.yml) → SSH ke VPS → `docker compose up -d`. Untuk ngelihat state live di VPS, jalankan `docker compose ps`.

---

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
# LangGraph Agent
# ============================================
AGENT_SECRET=your_agent_secret_here  # openssl rand -hex 32

# ============================================
# Qdrant - Vector Database (External Provider)
# ============================================
# Use Qdrant Cloud (managed vector database)
# Sign up: https://cloud.qdrant.io
QDRANT_URL=https://your-cluster-id.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_cloud_api_key

# Provider tiers:
# - Free: 1GB storage, 1M vectors (sufficient for personal use)
# - Starter: $25/month (5GB storage, 5M vectors)
# - Standard: $95/month (20GB storage, 20M vectors)

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
        "url": "${QDRANT_URL}/collections/tasks/points/scroll",
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

### 2. LangGraph Agent

Implementation lengkap ada di [`langgraph-agent/`](langgraph-agent/). Struktur:

- `app/main.py` — FastAPI app dengan endpoints `/api/chat`, `/api/search`, `/api/task`, `/api/tasks`, `/api/note`, `/api/schedule`, `/api/briefing`, `/api/sync_vault`, `/api/notify`, `/health`
- `app/workflow.py` — LangGraph StateGraph: `understand → retrieve_context → generate_response`
- `app/tools.py` — Qdrant CRUD + Cal.com API + memory helpers
- `app/embedding.py` — fastembed ONNX wrapper (384-dim, `all-MiniLM-L6-v2`)
- `app/sync.py` — Obsidian vault → Qdrant upsert dengan orphan sweep
- `app/telegram.py` — Telegram Bot API sendMessage wrapper (single egress)
- `Dockerfile` — Python 3.11-slim, pre-cache ONNX model saat build

Agent di-auth dengan `AGENT_SECRET` via header `X-Agent-Secret`. Bot dan n8n workflow sama-sama pakai shared secret ini.

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

## Ideas
- 

## Tomorrow
- 
```

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
QDRANT_URL = os.getenv("QDRANT_URL", "https://your-cluster-id.qdrant.io:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "your_api_key")
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

client = QdrantClient(url=os.getenv("QDRANT_URL", "https://your-cluster-id.qdrant.io:6333"), api_key=os.getenv("QDRANT_API_KEY", "your_api_key"))

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
AGENT_URL = os.getenv("AGENT_URL")

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
            f"{AGENT_URL}/api/search",
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
            f"{AGENT_URL}/api/chat",
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
# Qdrant Cloud (external service, no reverse proxy needed)
```

---

## 🔒 Security

### Checklist Keamanan:

- Semua service di belakang reverse proxy dengan SSL
- Qdrant Cloud API key secured (never exposed to public)
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

# 2. Qdrant Cloud snapshots (managed by provider)
# Qdrant Cloud handles backups automatically
# Manual snapshot (if needed):
for collection in knowledge memory tasks people decisions; do
    curl -X POST "${QDRANT_URL}/collections/$collection/snapshots" \
        -H "api-key: $QDRANT_API_KEY"
done

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
    langgraph-agent/ caddy/ telegram-bot/ systemd/

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

### Testing Backup & Recovery

#### Verify Backup Integrity

```bash
# Check backup file exists and is not corrupted
BACKUP_FILE="$BACKUP_DIR/2026-05-09.tar.gz.gpg"

# Test decryption
gpg --decrypt $BACKUP_FILE > /dev/null 2>&1 && echo "✅ Backup decryption OK" || echo "❌ Backup corrupted"

# List contents without extracting
gpg --decrypt $BACKUP_FILE | tar -tzf - | head -20

# Check backup size (should be > 100MB for full backup)
du -h $BACKUP_FILE
```

#### Restore from Backup

**⚠️ WARNING:** This will overwrite current data. Test in staging environment first.

```bash
# 1. Stop all services
docker compose down

# 2. Decrypt and extract backup
RESTORE_DIR="/tmp/restore-$(date +%Y%m%d)"
mkdir -p $RESTORE_DIR

gpg --decrypt $BACKUP_FILE | tar -xzf - -C $RESTORE_DIR

# 3. Restore n8n data
docker volume create n8n_data
docker run --rm \
  -v n8n_data:/data \
  -v $RESTORE_DIR/n8n:/backup \
  alpine sh -c "rm -rf /data/* && cp -r /backup/* /data/"

# 4. Restore langgraph-agent volume
docker volume create langgraph_cache
docker run --rm \
  -v langgraph_cache:/data \
  -v $RESTORE_DIR/langgraph_cache:/backup \
  alpine sh -c "rm -rf /data/* && cp -r /backup/* /data/"

# 5. Restore Qdrant Cloud (if needed)
# Qdrant Cloud handles backups automatically
# For manual restore, use Qdrant Cloud dashboard or API snapshots

# 6. Restore database (if using self-hosted PostgreSQL)
# Skip if using external provider (Supabase/Neon)
psql $DATABASE_URL < $RESTORE_DIR/postgres-calcom.sql

# 7. Restore Obsidian vault
tar -xzf $RESTORE_DIR/obsidian-vault.tar.gz -C /path/to/SecretaryVault

# 8. Restore configuration files
cp $RESTORE_DIR/configs/.env .env
cp $RESTORE_DIR/configs/docker-compose.yml docker-compose.yml

# 9. Start services
docker compose up -d

# 10. Verify restoration
docker compose ps
bash scripts/health_check.sh

# 11. Test functionality
# Send test message to Telegram bot
# Verify n8n workflows are present
# Check Qdrant collections exist
```

#### Automated Restore Script

```bash
# scripts/restore.sh
#!/bin/bash
set -e

BACKUP_FILE=$1
RESTORE_DIR="/tmp/restore-$(date +%Y%m%d)"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup-file.tar.gz.gpg>"
    exit 1
fi

echo "🔄 Starting restore from: $BACKUP_FILE"

# Stop services
echo "⏸️  Stopping services..."
docker compose down

# Extract backup
echo "📦 Extracting backup..."
mkdir -p $RESTORE_DIR
gpg --decrypt $BACKUP_FILE | tar -xzf - -C $RESTORE_DIR

# Restore volumes
echo "💾 Restoring volumes..."
for volume in n8n_data langgraph_cache; do
    echo "  - Restoring $volume..."
    docker volume create $volume
    docker run --rm \
      -v $volume:/data \
      -v $RESTORE_DIR/${volume%_data}:/backup \
      alpine sh -c "rm -rf /data/* && cp -r /backup/* /data/"
done

# Start services
echo "🚀 Starting services..."
docker compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services..."
sleep 30

# Verify
echo "✅ Verifying restoration..."
docker compose ps
bash scripts/health_check.sh

echo "✅ Restore completed successfully!"
echo "📝 Restored from: $BACKUP_FILE"
echo "📁 Temporary files in: $RESTORE_DIR"
echo "🗑️  Clean up: rm -rf $RESTORE_DIR"
```

#### Recovery Time Objective (RTO)

| Component | Restore Time | Data Loss (RPO) |
|-----------|--------------|-----------------|
| n8n workflows | 5 minutes | Last backup (daily) |
| Qdrant Cloud | 0 minutes (managed) | Automatic (provider) |
| langgraph-agent| 5 minutes | Last backup (daily) |
| Database | 15 minutes | Last backup (daily) |
| Obsidian vault | 5 minutes | Last backup (daily) |
| **Total RTO** | **~30 minutes** | **24 hours** |

**Recommendation:** For production, reduce RPO to 1 hour by increasing backup frequency.
```

---

## 🏥 Health Monitoring

#### Health Check Script (scripts/health_check.sh):

    #!/bin/bash
    # Health check untuk semua services

    SERVICES=(
        "n8n|http://localhost:5678/healthz|200"
        "calcom|http://localhost:3000/api/health|200"
        "langgraph-agent|container:langgraph-agent:http://localhost:8090/health|200"
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

```bash
# 0. Verify all services are running
docker compose ps
# All services should show "Up" status

# 1. Inisialisasi Qdrant Cloud collections
python3 scripts/init_qdrant.py

# 2. Sync Obsidian vault pertama kali
python3 scripts/sync_obsidian.py

# 3. Setup external PostgreSQL database
# Test connection
psql $DATABASE_URL -c "SELECT 1"

# Create database if not exists
psql $DATABASE_URL -c "CREATE DATABASE IF NOT EXISTS calcom"

# Run Cal.com migrations
docker exec calcom npm run db:migrate

# 4. Test Telegram bot
# Buka Telegram, cari bot Anda, kirim /start
# Bot should respond with welcome message

# 5. Setup n8n workflows
# Buka https://n8n.yourdomain.com
# Login with N8N_USER and N8N_PASSWORD
# Import workflow dari n8n/workflows/

# 6. Verifikasi semua koneksi
bash scripts/health_check.sh

# 7. Test end-to-end flow
# Send message to Telegram bot: "Apa jadwal saya hari ini?"
# Bot should query Cal.com and respond
```

### Verification Checklist

After post-installation, verify:

- [ ] All Docker containers running (`docker compose ps`)
- [ ] n8n accessible at configured URL
- [ ] Qdrant Cloud connection working (`curl ${QDRANT_URL}/collections -H "api-key: ${QDRANT_API_KEY}"`)
- [ ] Cal.com accessible at `http://localhost:3000`
- [ ] Telegram bot responds to `/start` command
- [ ] Database migrations completed successfully
- [ ] Health check script passes all tests
- [ ] End-to-end message flow works (Telegram → n8n → langgraph-agent → Response)

---

## 🔧 Troubleshooting

### Docker Compose Won't Start

**Symptom:** `docker compose up -d` fails with port conflicts

**Solution:**
```bash
# Check if ports are already in use
netstat -tulpn | grep -E '5678|8090|6333|3000'

# If ports are in use, either:
# 1. Stop the conflicting service
# 2. Change ports in docker-compose.yml

# Check Docker daemon status
systemctl status docker

# View detailed logs
docker compose logs
```

---

### Qdrant Cloud Connection Issues

**Symptom:** `Connection refused` or timeout errors to Qdrant Cloud

**Solution:**
```bash
# 1. Verify credentials
echo $QDRANT_URL
echo $QDRANT_API_KEY

# 2. Test connection
curl -X GET "${QDRANT_URL}/collections" \
  -H "api-key: ${QDRANT_API_KEY}"

# 3. Check firewall (ensure your VPS can reach external HTTPS)
curl -I https://cloud.qdrant.io

# 4. Verify cluster is active on Qdrant Cloud dashboard
# Visit: https://cloud.qdrant.io

# 5. Restart langgraph-agent
docker compose restart langgraph-agent
```

---

### Telegram Bot Not Responding

**Symptom:** Bot doesn't reply to messages

**Solution:**
```bash
# 1. Verify bot token is valid
curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe

# 2. Check if your user ID is in whitelist
echo $TELEGRAM_ALLOWED_USERS
# Should contain your Telegram user ID

# 3. Get your Telegram user ID
# Send message to @userinfobot on Telegram

# 4. Check bot logs
docker logs telegram-bot

# 5. Verify webhook is set correctly
curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getWebhookInfo
```

---

### Cal.com API Authentication Fails

**Symptom:** `401 Unauthorized` when calling Cal.com API

**Solution:**
```bash
# 1. Verify CALCOM_API_KEY is set (NOT CALCOM_SECRET)
echo $CALCOM_API_KEY

# 2. Get API key from Cal.com
# Login to Cal.com → Settings → API Keys → Create New API Key

# 3. Test API key
curl -H "Authorization: Bearer $CALCOM_API_KEY" \
     http://localhost:3000/api/bookings

# 4. Check Cal.com logs
docker logs calcom
```

---

### LLM API Rate Limits

**Symptom:** `429 Too Many Requests` from LLM provider

**Solution:**
```bash
# 1. Check your provider's rate limits
# OpenAI: 3 RPM (free tier), 60 RPM (paid)
# OpenRouter: varies by model

# 2. Implement exponential backoff in code
# 3. Use fallback model (gpt-3.5-turbo)
# 4. Reduce request frequency

# 5. Monitor usage
# OpenAI: https://platform.openai.com/usage
# OpenRouter: https://openrouter.ai/activity
```

---

### Database Connection Failed

**Symptom:** Cal.com can't connect to PostgreSQL

**Solution:**
```bash
# 1. Test DATABASE_URL
psql $DATABASE_URL -c "SELECT 1"

# 2. Verify database exists
psql $DATABASE_URL -c "\l"

# 3. Run migrations
docker exec calcom npm run db:migrate

# 4. Check PostgreSQL provider status
# Supabase: https://app.supabase.com/project/_/settings/database
# Neon: https://console.neon.tech/
```

---

## 🗺️ Roadmap

### Shipped Features

| # | Feature | Trigger | Command |
|---|---|---|---|
| 1 | Multi-VPS Monitoring | Push (Prometheus) + 5 min health check | `/monitor`, `/vps` |
| 2 | Knowledge Base Sync | Auto every 30 min | `/sync`, `/cari` |
| 3 | Voice Message Support | On voice message | (auto via Whisper) |
| 4 | Multi-Repo Code Q&A | On demand | `/tanya`, `/index` |
| 5 | Self-Improving Skills | Passive logging | `/skill` |
| 6 | Resource Alerts | Threshold trigger | (auto Telegram) |
| 7 | Morning Standup Brief | 07:00 WIB daily | `/briefing` |
| 8 | Incident Auto-Responder | Every 5 min | (auto-fix) |
| 9 | Config Drift Detector | 02:00 WIB daily | `/drift` |
| 10 | SSL/Domain Watchdog | 02:05 WIB daily | `/ssl add/del/list` |
| 11 | Capacity Planning | 02:10 WIB daily | `/capacity` |
| 12 | Auto PR/MR Review (GitHub + GitLab) | Webhook event | `/review owner/repo#123` |
| 13 | Meeting Notes → Action Items | Voice ≥500 chars OR `/meeting` | `/meeting <transkrip>` |
| 14 | Dependency Watchdog | 03:00 WIB daily | `/deps [repo_id]` |
| 15 | Documentation Sync | On demand | `/docsync owner/repo#123` |

Detail per fitur + roadmap lanjutan: [`AI_AGENT_ROADMAP.md`](AI_AGENT_ROADMAP.md).

### On the Horizon

- **Documentation Sync** — auto-update API docs/README/changelog from PR diff
- **Spec-to-Implementation** — kirim spec, agent breakdown + implement + PR
- **Dependency Watchdog Phase 2** — auto-PR untuk patch versions setelah dogfood Phase 1 validate noise level
- **Email auto-categorization + drafting** — IMAP integration, agent triage inbox
- **Mobile app (React Native)** — companion app untuk on-the-go interactions
- **Browser extension** — quick capture web content ke knowledge base
- **WhatsApp Business API integration** — second messaging channel
- **Fine-tuned local model** — personal style + on-device privacy
- **Grafana dashboard** (deferred — Prometheus retain 30d, attach saat butuh trend visualization)

---

## 📝 License

MIT License - Gunakan dan modifikasi sesuka hati.

---

## 🙏 Credits

- n8n (https://n8n.io) - Workflow Automation
- LangGraph (https://github.com/langchain-ai/langgraph) - Agent workflow framework
- Qdrant (https://qdrant.tech) - Vector Database
- Cal.com (https://cal.com) - Scheduling
- Cloudflare R2 (https://www.cloudflare.com/products/r2/) - S3-Compatible Object Storage
- Obsidian (https://obsidian.md) - Knowledge Management
- OpenAI, Anthropic, and other LLM providers - AI Models

---

"Sekretaris terbaik adalah yang tahu apa yang Anda butuhkan sebelum Anda memintanya."
