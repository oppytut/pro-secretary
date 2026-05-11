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
        PostgreSQL[PostgreSQL<br/>Supabase/Neon/Railway]
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
    CalCom --> PostgreSQL
    
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
    class SMTP,PostgreSQL externalStyle
```

## 🔄 How It Works

### System Overview

AI Personal Secretary adalah sistem yang bekerja **24/7** untuk membantu mengelola pekerjaan, jadwal, tasks, dan knowledge base Anda. Sistem ini menggunakan arsitektur microservices dengan 7 komponen utama yang saling terintegrasi.

### Component Roles

| Component | Role | Technology | Port |
|-----------|------|------------|------|
| **Telegram Bot** | User interface | Python Telegram Bot API | External |
| **n8n** | Workflow orchestrator & router | n8n (low-code automation) | 5678 |
| **OpenFang/LangGraph** | AI reasoning & decision making | OpenFang.sh / LangGraph | 8090 |
| **Cal.com** | Calendar & appointment management | Cal.com (self-hosted) | 3000 |
| **Qdrant** | Vector database & semantic search | Qdrant | 6333, 6334 |
| **Obsidian** | Knowledge base (notes & docs) | Obsidian Markdown | - |
| **Cloudflare R2** | Object storage (files, backups) | S3-compatible storage | External |

### Data Flow Architecture

```mermaid
flowchart TD
    User[👤 USER<br/>Sends message/command<br/>via Telegram]
    
    TelegramBot[📱 TELEGRAM BOT<br/>Interface Layer<br/>━━━━━━━━━━━━━━<br/>✓ Authentication whitelist<br/>✓ Command parsing<br/>✓ Message routing]
    
    N8N[🎯 N8N<br/>Orchestration Layer<br/>━━━━━━━━━━━━━━<br/>✓ Route commands to services<br/>✓ Schedule automated tasks cron<br/>✓ Coordinate multi-service ops]
    
    AIAgent[🤖 OPENFANG / LANGGRAPH<br/>AI Agent Layer<br/>━━━━━━━━━━━━━━<br/>✓ Understand user intent<br/>✓ Retrieve context from memory<br/>✓ Execute tools calendar, search, tasks<br/>✓ Generate natural language responses]
    
    subgraph Backend["🔧 BACKEND SERVICES (Parallel Access)"]
        Obsidian[📝 OBSIDIAN<br/>Knowledge Base<br/>━━━━━━━━<br/>• Notes<br/>• Docs<br/>• Wiki]
        
        Qdrant[💾 QDRANT<br/>Vector DB<br/>━━━━━━━━<br/>• Memories<br/>• Tasks<br/>• Knowledge]
        
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
    style Qdrant fill:#fce4ec,stroke:#880e4f,stroke-width:2px,color:#000
    style CalCom fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px,color:#000
    style PostgreSQL fill:#fff9c4,stroke:#f57f17,stroke-width:2px,color:#000
    style R2 fill:#fff9c4,stroke:#f57f17,stroke-width:2px,color:#000
```

**Key Data Flows:**

1. **User Input** → Telegram Bot → n8n → AI Agent → Backend Services
2. **Proactive Tasks** → n8n (cron) → AI Agent → Backend Services → Telegram Bot → User
3. **Calendar Operations** → Cal.com ↔ PostgreSQL (persistent storage)
4. **Memory/Context** → Qdrant (vector search for relevant information)
5. **Knowledge Base** → Obsidian (notes/docs) → Qdrant (indexing) + R2 (backup)
6. **File Operations** → Cloudflare R2 (S3-compatible object storage)

---

## 📖 Workflow Examples

### Example 1: User Sends Chat Message

**User Input:** "Apa jadwal saya hari ini?"

**Flow:**

```
1. TELEGRAM BOT receives message
   ├─ Check authorization (ALLOWED_USERS)
   └─ Forward to OpenFang AI Agent

2. OPENFANG AI AGENT processes request
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

3. QDRANT stores task
   └─ POST http://qdrant:6333/collections/tasks/points
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
       └─ POST http://qdrant:6333/collections/tasks/points/scroll
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

2. OPENFANG SEMANTIC SEARCH
   ├─ Generate embedding from query
   │   └─ Vector: [0.345, 0.678, 0.912, ...]
   │
   └─ Search in Qdrant "knowledge" collection
       └─ POST http://qdrant:6333/collections/knowledge/points/search
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

7. N8N → QDRANT (Store in Memory)
   └─ POST http://qdrant:6333/collections/agent_memory/points
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

2. OPENFANG AI AGENT processes request
   ├─ Step 1: Generate Query Embedding
   │   └─ POST to LLM embedding endpoint
   │       Input: "diskusi project Alpha minggu lalu"
   │       Output: vector [0.234, 0.567, 0.891, ...]
   │
   ├─ Step 2: Search Qdrant (Indexed Obsidian Content)
   │   └─ POST http://qdrant:6333/collections/knowledge/points/search
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

2. OPENFANG AI AGENT orchestrates preparation
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
   │   └─ POST http://qdrant:6333/collections/knowledge/points/search
   │       Filter: tags contains "client-b"
   │       Response: [
   │         "Clients/Client-B/profile.md",
   │         "Clients/Client-B/2026-Q1-review.md",
   │         "Clients/Client-B/contract-details.md"
   │       ]
   │
   ├─ [3] Search Past Meeting Notes
   │   └─ POST http://qdrant:6333/collections/knowledge/points/search
   │       Filter: tags contains "client-b" AND "meeting-notes"
   │       Response: [
   │         "Meetings/2026-02-15-client-b-kickoff.md",
   │         "Meetings/2026-03-20-client-b-progress.md"
   │       ]
   │
   └─ [4] Search Pending Tasks Related to Client B
       └─ POST http://qdrant:6333/collections/tasks/points/search
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
   └─ POST http://qdrant:6333/collections/knowledge/points
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

OpenFang berjalan dalam **daemon mode**, checking deadlines setiap 5 menit:

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
├─ n8n → OpenFang: No auth (isolated network)
├─ OpenFang → Qdrant: API Key (QDRANT_API_KEY)
├─ OpenFang → Cal.com: Bearer Token (CALCOM_API_KEY)
└─ OpenFang → R2: AWS Signature V4 (R2_ACCESS_KEY_ID + SECRET)

External Services
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
curl -f http://localhost:6333/healthz    # Qdrant
curl -f http://localhost:3000/api/health # Cal.com
curl -f http://localhost:8090/health     # OpenFang

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

---

## 📋 Table of Contents

- [Architecture](#-architecture)
- [How It Works](#-how-it-works)
- [AI Agent Engine: OpenFang vs LangGraph](#-ai-agent-engine-openfang-vs-langgraph)
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

> **Important:** PostgreSQL dan Cloudflare R2 adalah external services yang TIDAK berjalan di server Anda. Resource requirements di bawah hanya untuk 6 containers lokal: n8n, OpenFang, Qdrant, Cal.com, Telegram Bot, dan Caddy.

#### Minimum (Personal Use - Single User)
- **CPU:** 6 cores (x86_64)
- **RAM:** 24 GB
- **Storage:** 250 GB NVMe SSD
- **Network:** 10 Mbps upload/download
- **Swap:** 16 GB (for OOM protection)
- **Disk I/O:** 3000+ IOPS, 100+ MB/s throughput

**Why these specs:**
- 16GB RAM causes OOM during Qdrant vector indexing
- 100GB storage fills up in 2-3 months (logs + vectors + backups)
- 4 cores bottleneck during concurrent AI operations
- NVMe required for Qdrant performance (SATA too slow)

#### Recommended (Production Use - Small Team)
- **CPU:** 8 cores (x86_64)
- **RAM:** 32 GB
- **Storage:** 500 GB NVMe SSD
- **Network:** 25 Mbps upload/download
- **Swap:** 16 GB
- **Disk I/O:** 5000+ IOPS, 200+ MB/s throughput

#### Optimal (High-Volume/Enterprise)
- **CPU:** 16 cores (x86_64)
- **RAM:** 64 GB
- **Storage:** 1 TB NVMe SSD
- **Network:** 100 Mbps upload/download
- **Swap:** 32 GB
- **Disk I/O:** 10000+ IOPS, 500+ MB/s throughput

#### Resource Breakdown (Minimum Tier)

**What runs on YOUR server (6 containers):**
- n8n: ~1.5-2 GB RAM, 1 core
- Qdrant: ~3-5 GB RAM, 1-2 cores (vector database - biggest consumer)
- Cal.com: ~1-1.5 GB RAM, 0.5-1 core (app only, database is external)
- OpenFang: ~1-2 GB RAM, 1 core
- Telegram Bot: ~0.3-0.5 GB RAM, negligible CPU
- Caddy: ~0.2-0.3 GB RAM, negligible CPU
- OS + Docker: ~2-3 GB RAM, 0.5-1 core

**Total baseline:** 10-14 GB RAM, spikes to 16-18 GB during vector indexing/LLM inference

**What runs EXTERNALLY (not on your server):**
- PostgreSQL: Hosted by Supabase/Neon/Railway (only network bandwidth)
- Cloudflare R2: Object storage (only network bandwidth)
- LLM Provider: API calls to OpenAI/Groq/etc (only network bandwidth)

#### Important Notes

- **NVMe SSD required** (not SATA) - Qdrant + Cal.com are I/O-intensive
- **Enable swap space** to prevent OOM crashes during vector indexing:
  ```bash
  sudo fallocate -l 16G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  ```
- **Allocate 8GB minimum to Qdrant container** for 100k+ vector collections
- **Plan for 20-30% headroom** - LLM inference and vector indexing cause 2-3x CPU/RAM spikes
- **Storage grows over time:** Plan for 50-100 GB growth per year (logs, vectors, backups)

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

### Scenario 1: Minimal Setup (Personal Use - Single User)

> **Note:** Hardware requirements updated to 6 cores, 24GB RAM, 250GB storage. VPS pricing below reflects OLD specs (4 cores, 16GB). See updated recommendations in comments.

**Infrastructure:**
- **VPS:** $15-25/month
  - Hetzner CX41 (8 cores, 32GB): €25/month = ~$27/month ← **Recommended** (exceeds minimum for headroom)
  - Contabo VPS M (6 cores, 16GB): €12/month = ~$13/month ← **Tight but workable**
  - OVH Essential (4 cores, 16GB): ~$18/month ← **Below minimum, not recommended**
  
- **Domain + SSL:** $1-2/month
  - Domain (.com): ~$12/year = $1/month
  - SSL: Free (Let's Encrypt via Caddy)
  
- **PostgreSQL Database (External):** $0-10/month
  - Supabase: Free tier (500MB, 2GB bandwidth) ← **Sufficient for personal use**
  - Neon: Free tier (0.5GB storage, 3GB data transfer)
  - Railway: $5/month (shared CPU, 512MB RAM)
  - **Note:** Database runs on provider, NOT on your VPS
  
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

**Total: $27-72/month** (personal use, cost-optimized)

---

### Scenario 2: Production Setup (Small Team)

**Infrastructure:**
- **VPS/Dedicated Server:** $25-45/month
  - Hetzner AX41 (Ryzen 5 3600, 64GB RAM): ~€39/month (~$42) ← **Exceeds spec (64GB vs 32GB), but good value**
  - OVH Advance-2 (8 cores, 32GB RAM): ~$40/month ← **Matches spec exactly**
  - Contabo VPS L (10 cores, 60GB RAM): ~€27/month (~$29) ← **Exceeds spec, best value**
  
- **Domain + SSL:** $1-2/month

- **PostgreSQL Database (External):** $10-25/month
  - Supabase Pro: $25/month (8GB storage, 50GB bandwidth)
  - Neon Scale: $19/month (10GB storage, autoscaling)
  - Railway Pro: $20/month (8GB RAM, shared CPU)
  - **Note:** Database runs on provider, NOT on your VPS
  
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

**Total: $73-174/month** (production-ready, small team)

---

### Scenario 3: High-Volume/Enterprise

**Infrastructure:**
- **Dedicated Server:** $80-110/month
  - Hetzner AX102 (Ryzen 9 5950X, 128GB RAM): ~€99/month (~$107) ← **Exceeds spec (128GB vs 64GB)**
  - OVH Scale-3 (16 cores, 64GB RAM): ~$80/month ← **Matches spec exactly**
  - Hetzner AX61 (Ryzen 7 3700X, 64GB RAM): ~€59/month (~$64) ← **Matches spec, best value**
  
- **Domain + SSL:** $1-2/month

- **PostgreSQL Database (External):** $50-200/month
  - Supabase Team: $599/month (unlimited storage, dedicated resources) ← **Overkill for most**
  - Neon Business: Custom pricing (dedicated compute)
  - AWS RDS: $50-200/month (db.t3.medium to db.m5.large)
  - Supabase Pro: $25/month (often sufficient for enterprise)
  - **Note:** Database runs on provider, NOT on your VPS
  
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

**Total: $246-657/month** (enterprise-grade, high-volume)

---

### Cost Comparison Table

| Component | Scenario 1<br/>(Personal) | Scenario 2<br/>(Small Team) | Scenario 3<br/>(Enterprise) |
|-----------|--------------------------|-----------------------------|-----------------------------|
| **Server/VPS** | $15-25 | $25-45 | $80-110 |
| **Domain + SSL** | $1-2 | $1-2 | $1-2 |
| **PostgreSQL (External)** | $0-10 | $10-25 | $50-200 |
| **Cloudflare R2 (External)** | $0-5 | $5-15 | $10-30 |
| **Backup Storage** | $1-5 | $2-7 | $5-15 |
| **LLM API (Provider)** | $10-30 | $30-80 | $100-300 |
| **Usage Level** | Light | Moderate | Heavy |
| **Setup Complexity** | 🔧 Low | 🔧🔧 Medium | 🔧🔧🔧 High |
| **TOTAL/month** | **$27-77** | **$73-174** | **$246-657** |

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

## 🤖 AI Agent Engine: OpenFang vs LangGraph

This project supports two AI agent engines with different approaches. Understanding the differences helps you choose the right one for your needs.

### Overview

Both **OpenFang.sh** and **LangGraph** serve as the "brain" of the AI Personal Secretary, but with different philosophies:

| Aspect | OpenFang.sh | LangGraph |
|--------|-------------|-----------|
| **Approach** | Configuration-based (TOML) | Code-based (Python) |
| **Setup Complexity** | Low (edit config file) | Medium-High (write code) |
| **Flexibility** | Medium (limited by config options) | High (full control over logic) |
| **Production Ready** | ✅ Yes (built-in features) | ⚠️ Depends (need to build features) |
| **Daemon Mode** | ✅ Built-in (24/7 background service) | ❌ Need to implement |
| **Proactive Features** | ✅ Built-in (cron, reminders) | ❌ Need to implement |
| **Multi-channel** | ✅ Built-in (Telegram, webhook, HTTP) | ❌ Need to implement |
| **Pre-built Tools** | ✅ Calendar, email, tasks, search | ❌ Need to implement each tool |
| **Monitoring** | ✅ Built-in health checks | ❌ Need to implement |
| **Learning Curve** | Low (just configuration) | Medium (Python skills required) |
| **Maintenance** | Low (update config) | High (maintain code) |
| **Best For** | Production, MVP, Quick deploy | Custom logic, Prototyping, R&D |

---

### AI Agent Workflow State Machine

Both OpenFang and LangGraph follow a similar state-based workflow for processing user requests:

```mermaid
stateDiagram-v2
    [*] --> Understand: User message received
    
    Understand --> RetrieveContext: Intent extracted
    note right of Understand
        • Parse user intent
        • Extract entities
        • Classify task type
    end note
    
    RetrieveContext --> ExecuteTools: Context loaded
    note right of RetrieveContext
        • Query Qdrant vector DB
        • Get conversation history
        • Load relevant memories
    end note
    
    ExecuteTools --> GenerateResponse: Tools executed
    note right of ExecuteTools
        • Call calendar API
        • Search knowledge base
        • Create/update tasks
        • Upload/retrieve files
    end note
    
    GenerateResponse --> StoreMemory: Response generated
    note right of GenerateResponse
        • Format with LLM
        • Natural language output
        • Bahasa Indonesia
    end note
    
    StoreMemory --> [*]: Complete
    note right of StoreMemory
        • Save to Qdrant
        • Update context
        • Log interaction
    end note
    
    ExecuteTools --> ExecuteTools: Multiple tools needed
    Understand --> [*]: Invalid/unclear intent
```

**State Transitions:**
- **Understand** → **RetrieveContext**: Intent successfully parsed
- **RetrieveContext** → **ExecuteTools**: Relevant context retrieved
- **ExecuteTools** → **ExecuteTools**: Multiple tools need to be called sequentially
- **ExecuteTools** → **GenerateResponse**: All tools executed successfully
- **GenerateResponse** → **StoreMemory**: Response formatted
- **StoreMemory** → **[*]**: Interaction complete
- **Understand** → **[*]**: Invalid intent (error handling)

---

### OpenFang.sh - Configuration-Based Agent

**Type:** Production-ready AI Agent OS (Operating System for AI Agents)

**Philosophy:** Configure, don't code. Define agent behavior through declarative configuration.

#### Key Features

✅ **Daemon Mode** - Runs 24/7 as background service, proactively checking for tasks
✅ **Built-in Tools** - Calendar, email, file management, task tracking out-of-the-box
✅ **Multi-channel** - Telegram, webhook, HTTP API support included
✅ **Proactive Reminders** - Automatically sends reminders based on schedule
✅ **Production Ready** - Auth, rate limiting, monitoring built-in

#### Configuration Example

```toml
# openfang/secretary.toml

[agent]
name = "Secretary"
description = "Personal AI Secretary yang tahu semua pekerjaan saya"
mode = "daemon"  # Runs continuously in background
personality = """
Kamu adalah sekretaris pribadi AI yang sangat efisien dan proaktif.
Kamu tahu semua jadwal, task, project, dan konteks pekerjaan saya.
Kamu berkomunikasi dalam Bahasa Indonesia yang natural.
Kamu memberikan reminder tanpa diminta jika ada deadline mendekat.
"""

[llm]
provider = "openai"
model = "${LLM_MODEL}"
base_url = "${LLM_BASE_URL}"
api_key = "${LLM_API_KEY}"
temperature = 0.7
max_tokens = 2048

[llm.fallback]
provider = "openai"
model = "gpt-3.5-turbo"  # Fast fallback for simple queries
api_key = "${LLM_API_KEY}"
base_url = "${LLM_BASE_URL}"

[memory]
type = "qdrant"
url = "http://qdrant:6333"
collection = "agent_memory"
api_key = "${QDRANT_API_KEY}"

[hands]  # Built-in tools - just enable them
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
region = "auto"

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

[daemon]  # Proactive features
enabled = true
check_interval = "5m"  # Check for tasks every 5 minutes
proactive_hours = { start = 7, end = 22 }  # Active hours

[daemon.routines]
morning_briefing = "0 7 * * *"      # 07:00 daily
task_reminder = "0 */2 * * *"       # Every 2 hours
eod_summary = "0 21 * * *"          # 21:00 daily
```

#### Workflow

```
User Message
    ↓
OpenFang Daemon (always running)
    ↓
[agent] → Apply personality & mode
    ↓
[llm] → Call LLM for reasoning
    ↓
[memory] → Retrieve context from Qdrant
    ↓
[hands] → Execute tools (calendar, email, etc.)
    ↓
Response to User
    ↓
[daemon] → Check for proactive tasks (reminders, briefings)
```

**Everything is handled automatically based on configuration.**

#### When to Use OpenFang

✅ **Production deployment** - Need stable, reliable agent
✅ **Quick MVP** - Want to deploy fast without writing code
✅ **Proactive assistant** - Need automatic reminders and briefings
✅ **Standard workflows** - Common use cases (calendar, tasks, email)
✅ **Low maintenance** - Prefer configuration over code maintenance

---

### LangGraph - Code-Based Agent

**Type:** Python framework for building custom AI agents with graph-based workflows

**Philosophy:** Code everything. Full control over agent behavior through Python.

#### Key Features

✅ **Full Customization** - Control every detail of agent behavior
✅ **Graph-Based Workflow** - Define agent as state machine with nodes and edges
✅ **Flexible Logic** - Implement complex decision trees and conditional routing
✅ **Easy Testing** - Test each node independently
✅ **Visual Workflow** - Graph structure is easy to understand and debug

#### Prerequisites

Before implementing LangGraph agent, ensure you have:

**System Requirements:**
- Python 3.9 or higher
- pip package manager
- Virtual environment (recommended)

**Installation:**

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install langchain==0.1.0 \
            langgraph==0.0.20 \
            qdrant-client==1.7.0 \
            langchain-openai==0.0.5 \
            langchain-community==0.0.10 \
            requests==2.31.0 \
            boto3==1.34.0 \
            sentence-transformers==2.2.2

# Verify installation
python -c "import langgraph; print(f'LangGraph version: {langgraph.__version__}')"
python -c "import langchain; print(f'LangChain version: {langchain.__version__}')"
```

**Docker Setup (Alternative):**

```dockerfile
# langgraph/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent.py .

CMD ["python", "agent.py"]
```

```txt
# langgraph/requirements.txt
langchain==0.1.0
langgraph==0.0.20
qdrant-client==1.7.0
langchain-openai==0.0.5
langchain-community==0.0.10
requests==2.31.0
boto3==1.34.0
sentence-transformers==2.2.2
```

#### Implementation Example

> **📖 Full Implementation:** For complete LangGraph agent code with all tools and workflow nodes, see [Component Setup → LangGraph Agent](#alternatif-langgraph-agent-langgraphagentpy) section below.

**Quick Overview - Workflow Structure:**

```python
from langgraph.graph import StateGraph, END

# 1. Define state
class SecretaryState:
    messages: list
    context: str
    current_task: str
    tools_output: dict

# 2. Build workflow graph
workflow = StateGraph(SecretaryState)
workflow.add_node("understand", understand_intent)
workflow.add_node("retrieve_context", retrieve_context)
workflow.add_node("execute_tools", execute_tools)
workflow.add_node("generate_response", generate_response)

# 3. Define flow
workflow.set_entry_point("understand")
workflow.add_edge("understand", "retrieve_context")
workflow.add_edge("retrieve_context", "execute_tools")
workflow.add_edge("execute_tools", "generate_response")
workflow.add_edge("generate_response", END)

# 4. Compile and use
app = workflow.compile()
result = app.invoke({"messages": ["Apa jadwal saya hari ini?"]})
```

**Key Components:**
- **State Management:** SecretaryState tracks conversation flow
- **Tools:** search_knowledge, get_today_schedule, create_task, search_files
- **Workflow Nodes:** understand → retrieve_context → execute_tools → generate_response
- **Graph-Based:** Each node is independently testable

See full implementation with error handling, tool definitions, and deployment instructions in Component Setup section.

#### Workflow

```python
User Message
    ↓
app.invoke({"messages": [user_message]})
    ↓
understand_intent(state)      # ← You implement this
    ↓
retrieve_context(state)       # ← You implement this
    ↓
execute_tools(state)          # ← You implement this
    ↓
generate_response(state)      # ← You implement this
    ↓
Response to User
```

**Every step must be manually implemented in Python code.**

#### When to Use LangGraph

✅ **Custom workflows** - Need very specific agent behavior
✅ **Complex logic** - Conditional routing, multi-step reasoning
✅ **Prototyping** - Experimenting with new ideas
✅ **Research & Development** - Testing different approaches
✅ **Full control** - Need to customize every detail
✅ **Integration challenges** - Services that don't work with OpenFang

---

### Decision Matrix

#### Choose **OpenFang** if:

- ✅ You want **quick deployment** (MVP, production)
- ✅ You need **proactive features** (reminders, briefings)
- ✅ You prefer **configuration over code**
- ✅ You want **built-in tools** (calendar, email, tasks)
- ✅ You need **daemon mode** (24/7 background service)
- ✅ You want **low maintenance**
- ✅ Standard use cases are sufficient

#### Choose **LangGraph** if:

- ✅ You need **custom workflow logic**
- ✅ You want **full control** over agent behavior
- ✅ You're **prototyping** new ideas
- ✅ You need **complex decision trees**
- ✅ You have **Python development skills**
- ✅ OpenFang configuration is not flexible enough
- ✅ You're doing **research & development**

---

### Project Decision

**From TASK.md:**
> **AI Engine:** OpenFang.sh sebagai primary (fallback ke LangGraph jika perlu)

#### Why OpenFang as Primary?

1. **Production-Ready** - All features needed for AI secretary are built-in
2. **Quick MVP** - No coding required, just configuration
3. **Daemon Mode** - Proactive reminders work out-of-the-box
4. **Low Maintenance** - Update config vs maintain code
5. **Built-in Features** - Calendar, email, tasks, multi-channel support

#### When to Use LangGraph?

LangGraph is used as **fallback** or **alternative** when:

1. **Custom Logic Needed** - OpenFang config is not flexible enough
2. **Complex Decision Trees** - Need conditional routing beyond config
3. **Prototyping** - Testing new ideas before implementing in OpenFang
4. **Integration Challenges** - Service doesn't work with OpenFang

---

### Deployment Options

#### Option 1: OpenFang Only (Recommended for MVP)

```yaml
# docker-compose.yml
services:
  openfang:
    image: ghcr.io/rightnow-ai/openfang:latest
    container_name: openfang
    restart: always
    ports:
      - "8090:8090"
    environment:
      - OPENFANG_CONFIG=/etc/openfang/secretary.toml
      - LLM_PROVIDER=${LLM_PROVIDER}
      - LLM_API_KEY=${LLM_API_KEY}
      - LLM_MODEL=${LLM_MODEL}
    volumes:
      - ./openfang/secretary.toml:/etc/openfang/secretary.toml
      - openfang_data:/var/lib/openfang
    networks:
      - secretary-net
```

**Use Case:** Standard AI secretary with proactive features.

---

#### Option 2: LangGraph Only (Custom Implementation)

```yaml
# docker-compose.yml
services:
  langgraph-agent:
    build: ./langgraph
    container_name: langgraph-agent
    restart: always
    ports:
      - "8090:8090"
    environment:
      - LLM_API_KEY=${LLM_API_KEY}
      - LLM_BASE_URL=${LLM_BASE_URL}
      - LLM_MODEL=${LLM_MODEL}
      - QDRANT_URL=http://qdrant:6333
      - CALCOM_API_KEY=${CALCOM_API_KEY}
    volumes:
      - ./langgraph/agent.py:/app/agent.py
    networks:
      - secretary-net
```

**Use Case:** Highly customized workflow that requires full control.

---

#### Option 3: Hybrid (Best of Both Worlds)

```yaml
# docker-compose.yml
services:
  openfang:
    image: ghcr.io/rightnow-ai/openfang:latest
    ports:
      - "8090:8090"
    # For standard operations (reminders, briefings, daily tasks)
  
  langgraph-agent:
    build: ./langgraph
    ports:
      - "8091:8091"
    # For custom workflows (complex analysis, special tasks)
  
  n8n:
    image: n8nio/n8n:latest
    # Routes requests to appropriate agent based on type
```

**Use Case:** 
- OpenFang handles daily operations (reminders, briefings, standard queries)
- LangGraph handles custom workflows (complex analysis, special tasks)
- n8n routes requests based on intent

**Routing Logic:**
```javascript
// n8n Switch Node
if (intent === "standard_query") {
    route_to("http://openfang:8090");
} else if (intent === "complex_analysis") {
    route_to("http://langgraph-agent:8091");
}
```

---

### Analogy

**OpenFang = WordPress**
- Install, configure via dashboard, done
- Many plugins/features built-in
- Production-ready out-of-the-box
- Trade-off: Less flexible for custom logic

**LangGraph = Custom Django/Flask App**
- Build from scratch with code
- Full control over every detail
- Flexible for custom requirements
- Trade-off: More effort and maintenance

---

### Summary

| Criteria | OpenFang | LangGraph |
|----------|----------|-----------|
| **Setup Time** | 30 minutes (config) | 4-8 hours (coding) |
| **Production Ready** | ✅ Immediate | ⚠️ After building features |
| **Proactive Features** | ✅ Built-in | ❌ Need to implement |
| **Maintenance** | Low (config updates) | High (code maintenance) |
| **Flexibility** | Medium (config options) | High (full control) |
| **Best For** | 80% of use cases | 20% custom needs |

**Recommendation:** Start with **OpenFang** for MVP. Add **LangGraph** later if you need custom workflows that OpenFang can't handle.

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

# 4. Restore Qdrant data
docker volume create qdrant_data
docker run --rm \
  -v qdrant_data:/data \
  -v $RESTORE_DIR/qdrant:/backup \
  alpine sh -c "rm -rf /data/* && cp -r /backup/* /data/"

# 5. Restore OpenFang data
docker volume create openfang_data
docker run --rm \
  -v openfang_data:/data \
  -v $RESTORE_DIR/openfang:/backup \
  alpine sh -c "rm -rf /data/* && cp -r /backup/* /data/"

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
for volume in n8n_data qdrant_data openfang_data; do
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
| Qdrant vectors | 10 minutes | Last backup (daily) |
| OpenFang data | 5 minutes | Last backup (daily) |
| Database | 15 minutes | Last backup (daily) |
| Obsidian vault | 5 minutes | Last backup (daily) |
| **Total RTO** | **~40 minutes** | **24 hours** |

**Recommendation:** For production, reduce RPO to 1 hour by increasing backup frequency.
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

```bash
# 0. Verify all services are running
docker compose ps
# All services should show "Up" status

# 1. Inisialisasi Qdrant collections
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
- [ ] Qdrant dashboard accessible at `http://localhost:6333/dashboard`
- [ ] Cal.com accessible at `http://localhost:3000`
- [ ] Telegram bot responds to `/start` command
- [ ] Database migrations completed successfully
- [ ] Health check script passes all tests
- [ ] End-to-end message flow works (Telegram → n8n → OpenFang → Response)

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

### Qdrant Connection Refused

**Symptom:** `Connection refused to http://qdrant:6333`

**Solution:**
```bash
# Verify Qdrant is running
docker ps | grep qdrant

# Check Qdrant logs
docker logs qdrant

# Test connection from host
curl http://localhost:6333/healthz

# Test connection from another container
docker exec n8n curl http://qdrant:6333/healthz
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

### Qdrant Out of Memory

**Symptom:** Qdrant crashes or becomes slow

**Solution:**
```bash
# 1. Check Qdrant memory usage
docker stats qdrant

# 2. Reduce vector dimensions
# Edit embedding model to use smaller dimensions (384 instead of 768)

# 3. Enable quantization in Qdrant config
# 4. Increase Docker memory limit
# 5. Use Qdrant Cloud for production
```

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
