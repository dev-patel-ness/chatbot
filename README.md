# Generic AI Website Chatbot Platform

A B2B platform that turns any website URL into an AI chatbot: crawl → understand → build a RAG
knowledge base → discover conversational flows → run a multi-intent LangGraph runtime with safety
guardrails → persist & report on conversations — all manageable from an Admin Portal.

See [HLD.md](HLD.md) and [architecture (2).md](architecture%20(2).md) for the full design, and
[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for the staged build plan this repo follows.

---

## Project Structure

```
chatbot/
├── backend/            Python/FastAPI backend (Stages 1-8)
│   ├── ingestion/       Stage 1 — Web crawler + scraper
│   ├── understanding/   Stage 2 — Bedrock page classification/actions/relationships
│   ├── knowledge/       Stage 3 — Chunking, embeddings, pgvector, RAG
│   ├── flows/           Stage 4 — Flow discovery + editable flow CRUD
│   ├── runtime/         Stage 5 — LangGraph multi-intent runtime
│   ├── tools/           Stage 6 — Action/tool execution (mock APIs)
│   ├── safety/          Stage 7 — Input/output safety checks + event log
│   ├── conversations/   Stage 8 — Conversation/message persistence
│   ├── reporting/       Stage 8 — Aggregate metrics, FAQ extraction, summaries
│   ├── websites/        Admin Portal — website onboarding + background ingestion pipeline
│   ├── api/             FastAPI app + routers (public /api/chat + admin-protected routers)
│   ├── mock_api/         Mock action APIs (book-demo, contact, services)
│   ├── docker-compose.yml, Dockerfile
│   └── requirements.txt
├── admin/               React + Vite + TS Admin Portal (website onboarding, flows, knowledge
│                        test tool, conversations, reporting, embed code)
├── widget/              Vanilla-JS embeddable chatbot widget (chatbot.js)
└── index.html           Demo page hosting the widget
```

---

## Prerequisites

- Python 3.12+ (developed on 3.14) with a virtual environment
- Node.js 20+ / npm
- Docker Desktop (for PostgreSQL + pgvector, and optionally the mock API/backend containers)
- AWS credentials with Bedrock access (`aws configure`), region defaults to `us-east-1`
- Bedrock models used by default: `amazon.nova-pro-v1:0` (chat) and `amazon.titan-embed-text-v2:0`
  (embeddings) — override via env vars if your account has different models enabled

---

## Setup

### 1. Backend — Python environment

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium   # only needed for Stage 1 crawling
```

### 2. Infrastructure — PostgreSQL (pgvector) + mock API

```powershell
cd backend
docker compose up -d postgres mock_api
```

### 3. Admin Portal — Node dependencies

```powershell
cd admin
npm install
```

`admin/.env` controls the backend URL the portal talks to:
```
VITE_API_BASE_URL=http://127.0.0.1:8080
```

---

## Running Everything

```powershell
# 1. Postgres + mock API (Docker)
cd backend
docker compose up -d postgres mock_api

# 2. Backend API (host, for fast iteration)
cd backend
.\.venv\Scripts\python.exe -m api.main
# -> http://127.0.0.1:8080

# 3. Admin Portal (host)
cd admin
npm run dev
# -> http://localhost:5173
```

Open **http://localhost:5173**, log in with the admin password (`admin123` by default — set
`ADMIN_PASSWORD` env var before starting `api.main` to change it), then:

1. **Websites** → enter a URL, name, max pages/depth → click **Start Ingestion**. The pipeline runs
   in the background (crawl → understand → embed → discover flows) with live status polling.
2. Open a website's detail page to manage **Flows**, test the **Knowledge** base, browse
   **Conversations**, view **Reporting**, and copy the **Embed** code snippet.

### Fully containerized alternative

```powershell
cd backend
docker compose up -d --build   # builds + runs postgres, mock_api, and backend together
```
When running this way, the admin portal's `.env` should still point at `http://127.0.0.1:8080`
(the backend container publishes that port to the host).

### Embedding the widget on a real site

```html
<script src="http://127.0.0.1:8080/widget/chatbot.js"></script>
<script>
  Chatbot.init({
    websiteId: "your_website_id",
    websiteName: "Your Site",
    apiBaseUrl: "http://127.0.0.1:8080",
  });
</script>
```
The exact snippet (with the right `websiteId`) is available per-website in the Admin Portal's
**Embed** tab.

---

## Individual Stage CLIs (for debugging/offline use)

Each backend stage also has a standalone CLI, useful for testing a single step without the full
Admin Portal pipeline:

```powershell
cd backend
.\.venv\Scripts\python.exe -m ingestion.main --url https://example.com --max-pages 25 --max-depth 2
.\.venv\Scripts\python.exe -m understanding.main --pages-dir ./output/pages
.\.venv\Scripts\python.exe -m knowledge.main ingest --pages-dir ./output/pages --understanding ./output/understanding/understanding.json --website-id example
.\.venv\Scripts\python.exe -m knowledge.main ask --question "..." --website-id example
.\.venv\Scripts\python.exe -m flows.main --region us-east-1 discover --understanding ./output/understanding/understanding.json --website-id example
.\.venv\Scripts\python.exe -m runtime.main --region us-east-1 ask --message "..." --website-id example
.\.venv\Scripts\python.exe -m reporting.main summary --website-id example
```

---

## Key Environment Variables (backend)

| Variable | Default | Purpose |
|---|---|---|
| `AWS_REGION` | `us-east-1` | Bedrock region |
| `BEDROCK_CHAT_MODEL` | `amazon.nova-pro-v1:0` | Chat/classification model |
| `BEDROCK_EMBEDDING_MODEL` | `amazon.titan-embed-text-v2:0` | Embedding model |
| `CHATBOT_DB_DSN` | `postgresql://chatbot:chatbot_dev_password@localhost:5432/chatbot` | Postgres connection |
| `MOCK_API_URL` | `http://127.0.0.1:8000` | Mock actions API base URL |
| `ADMIN_PASSWORD` | `admin123` | Admin Portal login password |

---

## Known Limitations

- Admin auth is intentionally minimal (single shared password, in-memory session token, no
  expiry) — fine for local/hackathon use, not production-ready.
- Real websites may block automated crawling with bot-detection challenges (e.g. Cloudflare/Akamai
  interstitials) — this is expected external behavior, not a platform bug.
- The Docker image's build context is `backend/` only, so the sibling `widget/` folder isn't copied
  into the backend container yet; the `/widget/chatbot.js` static route only works when running the
  backend on the host.
- Mock action APIs (`book_demo`, `contact`, `view_services`) simulate real business backends for
  the MVP — see architecture.md §13 for how to swap in real APIs later.
