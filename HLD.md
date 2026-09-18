# High-Level Design (HLD)
# Generic AI Website Chatbot Platform

**Version:** 1.0  
**Status:** MVP / Hackathon  
**Primary Source Website:** Ness.com  
**Demo Host:** `index.html`

---

# 1. Purpose

This document defines the High-Level Design for a B2B platform that can generate and operate an AI chatbot for a website from its URL.

The platform will:

1. Crawl the target website.
2. Scrape its content and UI structure.
3. Understand the website using AWS Bedrock.
4. Build a searchable website knowledge base using embeddings and pgvector.
5. Automatically discover conversational flows.
6. Store flows as editable configurations.
7. Run conversations using LangGraph.
8. Retrieve website information through RAG.
9. Execute action-oriented flows through mock/exposed APIs.
10. Persist conversations and execution information.
11. Apply input and output safety controls.
12. Expose a chatbot widget that can be embedded into a website.
13. Package the application as a Docker image.

For the MVP, Ness.com is the source website and `index.html` is only a demonstration host for the chatbot.

---

# 2. Goals

## 2.1 Functional Goals

### Website onboarding

A website owner provides:

```text
Website URL
```

The platform then starts website ingestion.

### Website understanding

The system should understand:

- Pages
- URLs
- Navigation
- Menus
- Links
- Buttons
- Forms
- Headings
- Text
- Page relationships
- Potential user actions

### Knowledge-based chatbot

The chatbot should answer questions using information obtained from the target website.

### Automatic flow discovery

The platform should automatically identify possible conversational flows from the website.

### Editable flows

An administrator should be able to:

- View discovered flows
- Edit flow names
- Edit triggers
- Add steps
- Remove steps
- Change step order
- Configure actions
- Publish flows

### Action execution

The chatbot should be able to execute flows through configured APIs.

For the MVP, these APIs are mock APIs.

### Conversation persistence

Conversations and messages should be persisted for later review.

### Conversation reporting

The platform should provide basic conversation-level analytics.

### Safety

The chatbot should not expose internal instructions, confidential information, or unsafe content in response to malicious or abusive requests.

### Deployment

The application should be containerized using Docker.

---

# 3. Non-Goals for MVP

The following are intentionally outside the initial scope:

- Implementing real business backends for customer websites
- Production-grade multi-tenant enterprise IAM
- Kubernetes/EKS
- Complex microservice infrastructure
- Multi-agent architecture
- SMTP integration
- SMS integration
- Calendar integration
- Real payment processing
- Full enterprise analytics
- Automatic discovery of arbitrary private APIs
- Fully autonomous execution of unknown website actions

These can be added later.

---

# 4. High-Level System Context

```text
                         ┌─────────────────────┐
                         │    Website Owner    │
                         └──────────┬──────────┘
                                    │
                              Enter Website URL
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Chatbot Platform   │
                         │                     │
                         │ Crawler             │
                         │ Scraper             │
                         │ AI Understanding    │
                         │ RAG                 │
                         │ Flow Discovery      │
                         │ Flow Engine         │
                         │ Chat Runtime        │
                         │ Analytics            │
                         └──────────┬──────────┘
                                    │
                     ┌──────────────┼──────────────┐
                     ▼              ▼              ▼
                Ness.com       Mock APIs       PostgreSQL
                                                   +
                                                pgvector
                                    │
                                    ▼
                             Chatbot Widget
                                    │
                                    ▼
                               index.html
```

---

# 5. Architecture Style

The MVP uses a **modular backend architecture** rather than deploying many independent microservices.

The major logical modules are:

```text
Backend
│
├── Website Ingestion
│   ├── Crawler
│   └── Scraper
│
├── Website Understanding
│
├── Knowledge/RAG
│
├── Flow Management
│
├── Chat Runtime
│
├── Tool/API Management
│
├── Safety
│
├── Conversation Management
│
└── Analytics
```

This keeps the MVP easier to develop, debug, test, and containerize.

---

# 6. Technology Stack

| Layer | Technology |
|---|---|
| Demo frontend | HTML, CSS, JavaScript |
| Chatbot widget | JavaScript |
| Admin UI | React.js |
| Backend | Python |
| API framework | FastAPI |
| Workflow orchestration | LangGraph |
| LLM | AWS Bedrock |
| Embeddings | Amazon Bedrock embedding model |
| Browser crawling | Playwright |
| HTML parsing | BeautifulSoup |
| Relational database | PostgreSQL |
| Vector database capability | pgvector |
| RAG | Custom Python RAG pipeline |
| Action APIs | FastAPI mock APIs |
| Containerization | Docker |
| Local orchestration | Docker Compose |
| Source control | Git / GitHub |
| Cloud | AWS |

---

# 7. Major Components

## 7.1 Website Onboarding Service

### Responsibility

Accept a website URL and create a website ingestion job.

### Input

```json
{
  "url": "https://www.ness.com"
}
```

### Output

```json
{
  "website_id": "ness",
  "status": "crawl_started"
}
```

### Responsibilities

- Validate URL
- Create website record
- Create crawl job
- Start crawler
- Track ingestion status

---

# 8. Web Crawler

## 8.1 Responsibility

The crawler discovers pages belonging to the target website.

The crawler answers:

> "Which pages should I visit?"

### Technology

**Playwright**

### Why Playwright?

The target website may use JavaScript rendering.

Playwright allows the system to:

- Load rendered pages
- Execute JavaScript
- Navigate links
- Inspect DOM
- Detect dynamically rendered elements

### Crawl process

```text
Seed URL
   ↓
Load page using Playwright
   ↓
Extract internal URLs
   ↓
Normalize URLs
   ↓
Check visited set
   ↓
Add new URLs to queue
   ↓
Visit next URL
   ↓
Repeat
```

### Crawl controls

The crawler should maintain:

```text
visited_urls
pending_urls
failed_urls
crawl_depth
crawl_status
```

### URL restrictions

For a website onboarding job:

```text
Allowed domain = ness.com
```

External links should not automatically become crawl targets.

---

# 9. Web Scraper / Content Extractor

## 9.1 Responsibility

The scraper extracts useful information from every crawled page.

The scraper answers:

> "What exists on this page?"

### Extract

```text
Page URL
Page title
Meta information
Headings
Paragraphs
Text
Links
Buttons
Forms
Inputs
Navigation
Menu information
Images/alt text
```

### Example output

```json
{
  "url": "https://www.ness.com/services/example",
  "title": "Example Service",
  "headings": [
    "Example Service",
    "Our Capabilities"
  ],
  "content": "...",
  "links": [
    {
      "text": "Learn More",
      "url": "/services/example/details"
    }
  ],
  "buttons": [
    {
      "text": "Contact Us"
    }
  ],
  "forms": []
}
```

---

# 10. Website Data Processing

The raw scraper output should not directly become the chatbot context.

The processing pipeline is:

```text
Raw Page
   ↓
Clean HTML
   ↓
Remove irrelevant content
   ↓
Normalize text
   ↓
Extract structured elements
   ↓
Classify page
   ↓
Create knowledge chunks
   ↓
Create embeddings
```

The system should retain both:

1. Structured website information
2. Searchable knowledge chunks

This is important because RAG alone is not sufficient for flow discovery.

---

# 11. Website Understanding Service

AWS Bedrock is used to interpret website information.

### Inputs

```text
Page content
Page structure
Navigation
Links
Buttons
Forms
Page metadata
```

### Outputs

```text
Page classification
Website sections
Services
Potential actions
Potential intents
Relationships
Candidate flows
```

Example:

```json
{
  "page_type": "service",
  "service_name": "Salesforce",
  "possible_actions": [
    "learn_more",
    "contact"
  ]
}
```

---

# 12. Knowledge Base / RAG

## 12.1 Purpose

RAG provides the chatbot with relevant website information without sending the entire website to the LLM.

### Pipeline

```text
Website Content
      ↓
Cleaning
      ↓
Chunking
      ↓
Bedrock Embeddings
      ↓
pgvector
      ↓
Semantic Search
      ↓
Relevant Chunks
      ↓
AWS Bedrock LLM
      ↓
Response
```

---

# 13. Chunking Strategy

Website content should be divided into meaningful chunks.

The system should prefer semantic sections over arbitrary splitting.

Example:

```text
Page
 ├── Overview
 ├── Capabilities
 ├── Benefits
 └── Contact
```

Each section can become one or more chunks.

Every chunk should contain metadata.

```json
{
  "website_id": "ness",
  "url": "...",
  "page_title": "...",
  "section": "Capabilities",
  "content_type": "service",
  "text": "...",
  "embedding": [...]
}
```

Metadata allows filtering and better retrieval.

---

# 14. Vector Storage

PostgreSQL with the pgvector extension is used.

### Why pgvector?

The platform already needs PostgreSQL for:

```text
Users
Websites
Flows
Conversations
Messages
Execution data
```

pgvector allows website embeddings to remain in the same database.

```text
                 PostgreSQL
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
 Relational Data              pgvector
        │                         │
 Users/Flows/             Embeddings/Chunks
 Conversations            Semantic Search
```

---

# 15. Retrieval Architecture

The initial retrieval process:

```text
User Query
    ↓
Query Embedding
    ↓
pgvector similarity search
    ↓
Top-K chunks
    ↓
Metadata filtering
    ↓
Context construction
    ↓
AWS Bedrock
```

Future retrieval improvements can include:

```text
Vector Search
     +
Keyword Search
     +
Metadata Filtering
     ↓
Reranking
     ↓
Final Context
```

---

# 16. Automatic Flow Discovery

The system automatically generates candidate flows using:

```text
Website structure
+
Page classifications
+
Buttons
+
Forms
+
Links
+
Available actions
+
Website content
+
AWS Bedrock
```

Example:

```text
Service Discovery
       ↓
Service Selection
       ↓
Service Details
       ↓
Contact
```

The discovered flow should be stored as structured data.

---

# 17. Flow Model

A flow consists of:

```text
Flow
 ├── Name
 ├── Description
 ├── Trigger
 ├── Steps
 ├── Conditions
 ├── Required inputs
 ├── Actions
 └── Published status
```

Example:

```json
{
  "name": "Contact Sales",
  "trigger": [
    "I want to contact sales",
    "Talk to someone"
  ],
  "steps": [
    {
      "type": "collect_input",
      "field": "name"
    },
    {
      "type": "collect_input",
      "field": "email"
    },
    {
      "type": "collect_input",
      "field": "requirement"
    },
    {
      "type": "api_call",
      "action": "create_contact"
    }
  ]
}
```

---

# 18. Editable Flow Management

The platform should provide an admin interface.

```text
             Flow Discovery
                    ↓
              Candidate Flow
                    ↓
              Admin Dashboard
                    ↓
       ┌────────────┼────────────┐
       ▼            ▼            ▼
     Edit         Add          Delete
       │            │            │
       └────────────┼────────────┘
                    ↓
                 Validate
                    ↓
                 Publish
```

Only published flows should be used by the production chatbot runtime.

---

# 19. Chat Runtime

The chat runtime is orchestrated by LangGraph.

### High-level graph

```text
START
  ↓
Load Conversation State
  ↓
Input Safety
  ↓
Intent Detection
  ↓
Route
 ┌──────────────┬───────────────┐
 ▼              ▼               ▼
RAG          Flow Engine     Direct Response
 │              │
 │              ▼
 │           Tool/API
 │              │
 └───────┬──────┘
         ▼
   AWS Bedrock LLM
         ↓
 Output Safety
         ↓
 Persist Conversation
         ↓
        END
```

---

# 20. LangGraph State

The graph should maintain conversation state such as:

```json
{
  "conversation_id": "...",
  "website_id": "ness",
  "user_message": "...",
  "intent": "...",
  "active_flow": "...",
  "current_step": 2,
  "collected_data": {},
  "retrieved_context": [],
  "tool_result": null,
  "response": "..."
}
```

This allows multi-turn flows.

Example:

```text
User:
I want to contact sales.

AI:
Sure. What is your name?

User:
Rahul.

AI:
What is your email?

User:
...
```

The state persists across turns.

---

# 21. Intent Detection

The runtime determines what the user is trying to do.

Example categories:

```text
INFORMATION
SERVICE_QUERY
FLOW_REQUEST
ACTION_REQUEST
CONTACT
UNKNOWN
ABUSE
```

The router then decides which execution path to use.

---

# 22. RAG Path

Example:

> "What Salesforce services does Ness provide?"

```text
User
 ↓
Safety
 ↓
Intent Detection
 ↓
Information Query
 ↓
Generate Query Embedding
 ↓
pgvector
 ↓
Retrieve relevant Ness chunks
 ↓
AWS Bedrock
 ↓
Output Safety
 ↓
Response
```

The response should be grounded in the retrieved website content.

---

# 23. Flow Path

Example:

> "I want to contact Ness."

```text
User
 ↓
Safety
 ↓
Intent Detection
 ↓
Contact Flow
 ↓
Check current flow step
 ↓
Collect required information
 ↓
Validate
 ↓
Mock API
 ↓
API Result
 ↓
AWS Bedrock
 ↓
Output Safety
 ↓
Response
```

---

# 24. Tool / API Layer

The flow engine can invoke configured actions.

For MVP:

```text
GET  /api/services
GET  /api/services/{id}
POST /api/contact
POST /api/book-demo
```

The APIs are mock implementations.

### Tool execution model

```text
Flow Step
   ↓
Tool Resolver
   ↓
Validate Parameters
   ↓
Call API
   ↓
Receive Result
   ↓
Store Tool Execution
   ↓
Return Result to LangGraph
```

---

# 25. API Safety

Before calling an action API:

```text
Check action
Check required fields
Validate field values
Check authorization/context
Execute only configured action
```

The LLM should not be allowed to invent arbitrary API endpoints.

The flow configuration should define which tools are available.

---

# 26. Safety Architecture

Safety exists at multiple points.

```text
User
 ↓
Input Safety
 ↓
Intent / LangGraph
 ↓
RAG / Flow / Tool
 ↓
AWS Bedrock
 ↓
Output Safety
 ↓
User
```

### Input safety

Detect:

- Prompt injection
- System prompt extraction
- Malicious instructions
- Abuse
- Requests outside the website's intended scope

### Output safety

Check:

- Sensitive information
- Internal instructions
- Unsupported claims
- Unsafe responses
- Accidental tool output exposure

---

# 27. Conversation Persistence

Every conversation should be stored.

### Suggested data

```text
Website
Conversation
Message
FlowExecution
ToolExecution
SafetyEvent
```

### Message

```json
{
  "conversation_id": "...",
  "role": "user",
  "content": "...",
  "timestamp": "..."
}
```

### Flow execution

```json
{
  "conversation_id": "...",
  "flow_id": "...",
  "step": 2,
  "status": "completed"
}
```

---

# 28. Conversation Analytics

The reporting layer reads persisted conversation data.

Initial metrics:

```text
Total conversations
Total messages
Frequently asked questions
Most used flows
Unknown queries
Failed conversations
Abandoned flows
Average conversation length
Safety-triggered conversations
```

Example:

```text
Conversation Report
-------------------------
Total Conversations: 1,250
Total Messages: 7,820

Top Queries:
1. Services
2. Salesforce
3. AI capabilities

Flow Usage:
Service Flow: 430
Contact Flow: 185

Unknown Queries: 76
Safety Events: 18
```

---

# 29. Database Design

## 29.1 Main Tables

### websites

```text
id
name
url
status
created_at
updated_at
```

### crawl_jobs

```text
id
website_id
status
started_at
completed_at
pages_found
pages_processed
error
```

### pages

```text
id
website_id
url
title
page_type
content
metadata
created_at
```

### chunks

```text
id
website_id
page_id
content
section
content_type
embedding
metadata
created_at
```

### flows

```text
id
website_id
name
description
status
version
created_at
updated_at
```

### flow_steps

```text
id
flow_id
step_order
step_type
configuration
created_at
```

### conversations

```text
id
website_id
user_id
status
started_at
ended_at
```

### messages

```text
id
conversation_id
role
content
created_at
```

### flow_executions

```text
id
conversation_id
flow_id
current_step
status
started_at
completed_at
```

### tool_executions

```text
id
conversation_id
flow_execution_id
tool_name
request
response
status
created_at
```

### safety_events

```text
id
conversation_id
message_id
event_type
action_taken
created_at
```

---

# 30. Logical Database Relationship

```text
Website
  │
  ├────────────── Pages
  │                  │
  │                  └──── Chunks ──── Embeddings
  │
  ├────────────── Flows
  │                  │
  │                  └──── Flow Steps
  │
  └────────────── Conversations
                     │
                     ├──── Messages
                     ├──── Flow Executions
                     │          │
                     │          └──── Tool Executions
                     │
                     └──── Safety Events
```

---

# 31. Backend API Design

## Website APIs

```text
POST /api/websites
GET  /api/websites/{website_id}
POST /api/websites/{website_id}/crawl
GET  /api/websites/{website_id}/crawl/status
```

## Flow APIs

```text
GET    /api/websites/{website_id}/flows
GET    /api/flows/{flow_id}
POST   /api/websites/{website_id}/flows
PUT    /api/flows/{flow_id}
DELETE /api/flows/{flow_id}
POST   /api/flows/{flow_id}/publish
```

## Chat APIs

```text
POST /api/chat
GET  /api/conversations/{conversation_id}
GET  /api/conversations/{conversation_id}/messages
```

## Analytics APIs

```text
GET /api/websites/{website_id}/analytics
GET /api/websites/{website_id}/conversations
```

## Mock action APIs

```text
GET  /api/services
GET  /api/services/{service_id}
POST /api/contact
POST /api/book-demo
```

---

# 32. Chatbot Widget Architecture

The chatbot widget is independent of the demo host page.

```text
index.html
     │
     ▼
Chatbot JavaScript
     │
     ▼
POST /api/chat
     │
     ▼
FastAPI
     │
     ▼
LangGraph
```

Eventually a customer could integrate it with:

```html
<script src="https://platform.example.com/chatbot.js"></script>
```

and initialize it using a website identifier.

---

# 33. Admin UI

The admin interface should eventually contain:

```text
Dashboard
│
├── Websites
│
├── Crawl Status
│
├── Knowledge Base
│
├── Discovered Flows
│
├── Flow Editor
│
├── Published Flows
│
├── Conversations
│
└── Analytics
```

### Flow Editor

The administrator should be able to visually inspect:

```text
Flow: Contact Sales

[Trigger]
    ↓
[Collect Name]
    ↓
[Collect Email]
    ↓
[Collect Requirement]
    ↓
[Call Contact API]
    ↓
[Confirmation]
```

---

# 34. Website Ingestion Sequence

```text
Website Owner
     │
     │ Submit URL
     ▼
FastAPI
     │
     │ Create Website
     ▼
Crawl Job
     │
     ▼
Playwright Crawler
     │
     │ Discover URLs
     ▼
Scraper
     │
     │ Extract content/UI
     ▼
Website Data
     │
     ├───────────────┐
     ▼               ▼
RAG Pipeline    Bedrock Analysis
     │               │
     ▼               ▼
Embeddings       Flow Candidates
     │               │
     ▼               ▼
pgvector          Flow Store
```

---

# 35. Chat Request Sequence

Example:

> "What Salesforce services does Ness provide?"

```text
User
 │
 ▼
Chatbot Widget
 │
 ▼
POST /api/chat
 │
 ▼
FastAPI
 │
 ▼
LangGraph
 │
 ▼
Input Safety
 │
 ▼
Intent Detection
 │
 ▼
RAG Node
 │
 ▼
Create Query Embedding
 │
 ▼
pgvector Search
 │
 ▼
Relevant Chunks
 │
 ▼
AWS Bedrock
 │
 ▼
Output Safety
 │
 ▼
Persist Message
 │
 ▼
FastAPI Response
 │
 ▼
Chatbot Widget
```

---

# 36. Action Flow Sequence

Example:

> "I want to contact sales."

```text
User
 │
 ▼
Chatbot Widget
 │
 ▼
FastAPI
 │
 ▼
LangGraph
 │
 ▼
Safety
 │
 ▼
Intent Detection
 │
 ▼
Contact Flow
 │
 ▼
Collect Name
 │
 ▼
Collect Email
 │
 ▼
Collect Requirement
 │
 ▼
Validate
 │
 ▼
Mock Contact API
 │
 ▼
API Result
 │
 ▼
AWS Bedrock
 │
 ▼
Output Safety
 │
 ▼
Persist Conversation
 │
 ▼
Response
```

---

# 37. Multi-Turn Conversation

Conversation state should be maintained by `conversation_id`.

Example:

```text
Conversation ID = abc123

Turn 1:
User: I want to contact sales.

State:
active_flow = contact_sales
current_step = collect_name

Turn 2:
User: Rahul

State:
name = Rahul
current_step = collect_email

Turn 3:
User: rahul@example.com

State:
name = Rahul
email = rahul@example.com
current_step = collect_requirement
```

The flow should continue from the current state rather than restarting.

---

# 38. Failure Handling

## Crawler failure

```text
Page fails
   ↓
Log failure
   ↓
Continue with remaining pages
```

The overall crawl should not necessarily fail because one page failed.

## LLM failure

```text
Bedrock request fails
   ↓
Retry according to configured policy
   ↓
If still failing:
Return safe fallback
```

## Vector search failure

```text
Vector search fails
   ↓
Attempt fallback retrieval
   ↓
If unavailable:
Return controlled response
```

## Tool/API failure

```text
API call
   ↓
Failure
   ↓
Record error
   ↓
LLM generates user-friendly response
```

---

# 39. Observability

The MVP should log:

```text
HTTP requests
Crawler status
Scraping errors
LLM calls
LLM latency
RAG retrieval count
Flow execution
Tool calls
Safety events
Database errors
```

Each chat request should have a correlation identifier.

Example:

```text
request_id = req_12345
conversation_id = conv_456
```

This makes debugging easier.

---

# 40. Security

## Secrets

Do not hardcode:

```text
AWS credentials
Database passwords
API keys
LLM credentials
```

Use environment variables/secrets management.

## Database

Use parameterized queries/ORM access.

## API

Validate request payloads.

## Tool execution

Only execute tools defined in the published flow configuration.

## Website isolation

Every website's data must be associated with a `website_id`.

A chatbot for website A must not retrieve knowledge belonging to website B.

---

# 41. Multi-Tenant Design

Although the MVP uses Ness.com, the database should be designed for multiple websites.

```text
Website A
   ├── Pages
   ├── Chunks
   ├── Flows
   └── Conversations

Website B
   ├── Pages
   ├── Chunks
   ├── Flows
   └── Conversations
```

Every relevant entity should include a relationship to `website_id`.

This is critical for the long-term B2B platform.

---

# 42. Docker Design

The MVP should be containerized.

```text
                 Docker Compose
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
   ┌──────────────┐       ┌──────────────┐
   │  Application │       │ PostgreSQL   │
   │  FastAPI     │──────▶│ + pgvector   │
   │              │       │              │
   │ LangGraph    │       │ Data         │
   │ RAG          │       │ Embeddings   │
   │ Crawler      │       └──────────────┘
   │ Scraper      │
   └──────┬───────┘
          │
          ▼
     AWS Bedrock
```

The final application image should contain the application dependencies and code.

Playwright browser dependencies must also be included in the application image.

---

# 43. Docker Runtime Configuration

Environment variables should include values such as:

```text
DATABASE_URL
AWS_REGION
BEDROCK_MODEL_ID
BEDROCK_EMBEDDING_MODEL_ID
LOG_LEVEL
```

Secrets should be supplied at runtime.

The Docker image should not contain credentials.

---

# 44. Deployment Direction

Initial direction:

```text
Developer
   ↓
GitHub
   ↓
Docker Build
   ↓
Docker Image
   ↓
Container Registry
   ↓
AWS Compute
```

AWS Bedrock remains an external managed service accessed by the application.

The MVP does not require EKS.

---

# 45. Scalability Considerations

The MVP is modular enough to scale later.

Potential future separation:

```text
API Service
Crawler Worker
Scraper Worker
AI/Flow Service
RAG Service
Analytics Service
```

For the MVP, these can remain within one backend application.

If crawl jobs become long-running, a background worker/queue can be introduced later.

---

# 46. Why Crawler and Scraper Are Separate

The distinction is intentional.

```text
Crawler
    =
Discover pages

Scraper
    =
Extract information from pages
```

Example:

```text
Crawler:
"What URLs are available?"

Scraper:
"What is on this URL?"

Website Understanding:
"What does this information mean?"

Flow Discovery:
"What user journey can be created?"
```

This separation makes the system easier to evolve.

---

# 47. Why RAG and Flow Store Are Separate

RAG answers:

> "What information is present on the website?"

Flows answer:

> "What should the chatbot do when a user follows a particular process?"

Therefore:

```text
Website Content
      ↓
RAG
      ↓
Knowledge Retrieval
```

while:

```text
Website Structure + Actions
      ↓
Flow Discovery
      ↓
Flow Store
      ↓
Flow Engine
```

Both are used by the chatbot runtime.

---

# 48. Why LangGraph Is Used

LangGraph is used for runtime orchestration.

It provides a structured mechanism for:

- Conversation state
- Conditional routing
- Multi-step flows
- Tool/API calls
- Branching
- Loops
- Error handling
- Human-in-the-loop capabilities later

It should not be responsible for crawling or database storage.

---

# 49. Why AWS Bedrock Is Used

AWS Bedrock is the managed AI/LLM layer.

It can be used for:

```text
Website understanding
Flow discovery
Intent detection
Response generation
Reasoning/tool selection
Embeddings
```

This keeps model hosting outside the application and fits the AWS-based deployment direction.

---

# 50. End-to-End Data Flow

## Phase 1 — Website Onboarding

```text
Website URL
   ↓
Crawler
   ↓
Scraper
   ↓
Structured Website Data
```

## Phase 2 — Knowledge Generation

```text
Structured Content
   ↓
Clean + Chunk
   ↓
Bedrock Embeddings
   ↓
pgvector
```

## Phase 3 — Flow Generation

```text
Website Structure
   +
Content
   +
UI Elements
   ↓
AWS Bedrock
   ↓
Candidate Flows
   ↓
PostgreSQL
```

## Phase 4 — Human Review

```text
Candidate Flows
   ↓
Admin UI
   ↓
Edit
   ↓
Publish
```

## Phase 5 — Chat

```text
User
   ↓
Chatbot Widget
   ↓
FastAPI
   ↓
LangGraph
   ↓
Safety
   ↓
RAG / Flow
   ↓
Bedrock / Tool API
   ↓
Safety
   ↓
Response
   ↓
Persist
```

---

# 51. MVP Development Phases

## Phase 1 — Project Foundation

- Create repository
- Create FastAPI application
- Configure PostgreSQL
- Configure pgvector
- Configure Docker
- Configure environment variables

## Phase 2 — Crawler + Scraper

- Implement Playwright crawler
- Implement URL discovery
- Implement duplicate handling
- Implement BeautifulSoup extraction
- Store pages

## Phase 3 — RAG

- Clean content
- Chunk content
- Generate Bedrock embeddings
- Store embeddings in pgvector
- Implement retrieval
- Test Ness questions

## Phase 4 — Website Understanding

- Classify pages
- Extract services/categories
- Analyze navigation/UI structure
- Generate candidate flows with Bedrock

## Phase 5 — Flow System

- Store flows
- Store flow steps
- Implement editing APIs
- Add publish/version status

## Phase 6 — LangGraph Chat Runtime

- Conversation state
- Safety node
- Intent node
- RAG node
- Flow node
- Tool node
- Response node

## Phase 7 — Mock APIs

- Services API
- Contact API
- Book-demo API
- Tool execution tracking

## Phase 8 — Chatbot Widget

- Build chat UI
- Connect to `/api/chat`
- Add conversation state
- Embed in `index.html`

## Phase 9 — Reporting

- Persist conversations
- Build basic analytics endpoints
- Add conversation review

## Phase 10 — Docker

- Build Docker image
- Run with Docker Compose
- Test complete application locally
- Prepare AWS deployment

---

# 52. Final MVP Architecture

```text
                         NESS.COM
                            │
                            ▼
                  ┌──────────────────┐
                  │   WEB CRAWLER    │
                  │    Playwright    │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │   WEB SCRAPER    │
                  │ BeautifulSoup +  │
                  │    Playwright    │
                  └────────┬─────────┘
                           │
                           ▼
                ┌────────────────────────┐
                │ Website Understanding  │
                │      AWS Bedrock       │
                └───────────┬────────────┘
                            │
               ┌────────────┴────────────┐
               ▼                         ▼
       ┌────────────────┐       ┌────────────────┐
       │ RAG Pipeline   │       │ Flow Discovery │
       │                │       │                │
       │ Chunking       │       │ Bedrock LLM    │
       │ Embeddings     │       │                │
       │ pgvector       │       │ Flow Store     │
       └───────┬────────┘       └───────┬────────┘
               │                        │
               └───────────┬────────────┘
                           ▼
                     ┌─────────────┐
                     │   FastAPI   │
                     └──────┬──────┘
                            ▼
                     ┌─────────────┐
                     │  LangGraph  │
                     └──────┬──────┘
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
           RAG            Flow          Tool/API
           Node           Node            Node
             │              │              │
             │              │         Mock APIs
             └──────────────┼──────────────┘
                            ▼
                     AWS Bedrock LLM
                            │
                            ▼
                     Output Safety
                            │
                            ▼
                   Conversation Store
                            │
                            ▼
                    Chatbot Widget
                            │
                            ▼
                       index.html
```

---

# 53. Architectural Principles

The system follows these principles:

```text
Website
    = Source of knowledge and website structure

Crawler
    = Page discovery

Scraper
    = Page/UI extraction

Website Understanding
    = Interpretation of website data

RAG
    = Knowledge retrieval

Flow Store
    = Business/conversation process definition

LangGraph
    = Runtime workflow orchestration

AWS Bedrock
    = AI/LLM capability

PostgreSQL
    = Persistent application state

pgvector
    = Semantic vector retrieval

Mock APIs
    = MVP action execution

Chatbot Widget
    = Website integration interface

Docker
    = Application packaging
```

The core design goal is to keep **knowledge, flows, orchestration, actions, and presentation separated** so the Ness.com prototype can later evolve into a platform that supports multiple customer websites without redesigning the entire system.
