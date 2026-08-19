# Jarvis

A personal AI assistant with a lightweight static frontend and an intelligent backend service — built entirely on free-tier infrastructure, designed for high reliability through layered caching and multi-provider fallback.

---

## Philosophy

> Keep the frontend simple. Keep the assistant intelligent.

The browser handles rendering, caching, and responsiveness. All AI processing stays in the assistant service. Every dependency is chosen so the whole system can run at zero cost while staying resilient to any single provider going down, rate-limiting, or timing out.

---

## Architecture

### Frontend

- **Hosting:** GitHub Pages (static, free, unlimited bandwidth on public repos)
- **Cache layers:** LocalStorage (fast, small) → IndexedDB (larger, structured, survives longer)
- **Role:** Render UI, cache recent conversations, queue requests when offline, retry on reconnect

### Backend — Assistant Service

- **Hosting:** Render free tier, FastAPI
- **Primary model:** Groq (free tier, very low latency)
- **Fallback models:** OpenRouter → Together.ai → Google Gemini → Cerebras
- **Cache:** Redis (Upstash free tier — serverless, no idle server cost)

Both frontend and backend live in a single private repo, deployed independently.

---

## Reliability Design

Reliability comes from layering — every request has multiple chances to succeed before the user ever sees an error.

```
User Request
    │
    ▼
Frontend Cache (LocalStorage/IndexedDB) ──── hit? return instantly
    │ miss
    ▼
Backend Cache (Redis) ──── hit? return, refresh frontend cache
    │ miss
    ▼
Primary Model (Groq)
    │ fail / timeout / rate-limited
    ▼
Retry with exponential backoff (max 2 retries)
    │ still failing
    ▼
Secondary Model (OpenRouter)
    │ fail
    ▼
Tertiary Model (Together.ai)
    │ fail
    ▼
Fallback Model (Gemini / Cerebras)
    │ fail
    ▼
Stale cached response (if available, marked as "may be outdated")
    │ none available
    ▼
Graceful error (clear message, retry button, never a raw stack trace)
```

### Key Reliability Features

- **Exponential backoff retries** — avoid hammering a struggling provider; back off before failing over
- **Circuit breaker per provider** — if a model fails repeatedly in a short window, skip it for N minutes instead of retrying every request against a dead endpoint
- **Multi-provider fallback chain** — never depend on a single free-tier model; rotate through providers in priority order
- **Timeouts on every call** — no request hangs indefinitely; a slow provider fails fast into the fallback chain
- **Redis caching with TTL** — cuts model calls for repeated/common queries, which also protects free-tier rate limits
- **Stale-while-revalidate** — serve a cached response immediately if available, refresh in the background
- **Idempotent request handling** — safe to retry a request without duplicating side effects
- **Health checks** — `/health` endpoint checks Redis connectivity and reports provider status
- **Session persistence** — conversations survive a backend restart or redeploy (Render free tier spins down on inactivity, so this matters)
- **Cold-start mitigation** — a lightweight scheduled ping (UptimeRobot / cron-job.org) keeps the Render service warm
- **Error recovery** — failures degrade gracefully (cached → generic helpful message) rather than surfacing raw errors to the user

---

## Caching Strategy

### Frontend

```
Browser → LocalStorage (hot, small) → IndexedDB (larger, structured)
```

Read path checks LocalStorage first, then IndexedDB, before ever hitting the network.

### Backend

```
Request → Redis
            │
        ┌───┴───┐
       Hit     Miss
        │       │
      Return   Call model → Cache result → Return
```

Cache keys incorporate the query and relevant context so semantically identical requests can reuse cached responses.

---

## API Endpoints

| Method | Endpoint            | Purpose                                       |
| ------ | ------------------- | --------------------------------------------- |
| POST   | `/chat`             | Send a message, get an assistant response     |
| POST   | `/summary`          | Generate a summary (e.g. "send today's summary") |
| POST   | `/email/send`       | Send conversation/summary via email           |
| GET    | `/conversation/{id}`| Retrieve a stored conversation                |
| GET    | `/health`           | Service, cache, and provider health status    |

---

## Staying Free

| Component            | Free-tier choice                          | Notes                                              |
| -------------------- | ----------------------------------------- | -------------------------------------------------- |
| Frontend hosting     | GitHub Pages                              | Free for public repos, generous bandwidth          |
| Backend hosting      | Render free web service                   | Spins down when idle — mitigate with keep-alive ping |
| Primary model        | Groq                                      | Free tier, fast inference                          |
| Fallback model(s)    | OpenRouter / Together.ai / Gemini / Cerebras | Keeps the chain alive if Groq rate-limits      |
| Cache                | Upstash Redis free tier                   | Serverless pricing, no cost while idle             |
| Uptime monitor       | UptimeRobot / cron-job.org                | Free, also mitigates Render cold starts            |
| Email sending        | Resend free tier                          | Enough volume for personal use                     |

> **Design rule:** Every new feature should default to a provider with a genuinely free tier before considering a paid one, and the fallback chain should always include at least one provider outside your primary vendor.

---

## Future Enhancements

- Voice conversations
- File sharing
- Image sharing
- Multiple AI personalities
- Multiple users
- Push notifications
- Mobile application
- Searchable conversations
- Analytics dashboard

---

## Project Structure

```
jarvis/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry
│   │   ├── config.py                # Settings, env vars
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic request/response
│   │   ├── providers/
│   │   │   ├── base.py              # Abstract provider interface
│   │   │   ├── groq_provider.py     # Groq (primary)
│   │   │   ├── openrouter_provider.py
│   │   │   ├── together_provider.py
│   │   │   ├── gemini_provider.py
│   │   │   └── cerebras_provider.py
│   │   ├── reliability/
│   │   │   ├── circuit_breaker.py   # Per-provider circuit breaker
│   │   │   ├── retry.py             # Exponential backoff
│   │   │   └── fallback_chain.py    # Orchestrates provider order
│   │   ├── cache/
│   │   │   ├── redis_cache.py       # Redis read/write/TTL
│   │   │   └── cache_key.py         # Key generation logic
│   │   ├── services/
│   │   │   └── chat.py              # Chat business logic
│   │   └── routes/
│   │       └── chat.py              # POST /chat
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js                   # Main entry
│       ├── chat.js                  # Chat UI
│       ├── api.js                   # Backend API calls
│       └── utils.js                 # Formatting, helpers
├── render.yaml                       # Render blueprint
├── .env.example
├── .gitignore
├── PLAN.md
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- Upstash Redis account (free)
- API keys from at least one provider (Groq recommended)

### Setup

```bash
# Clone
git clone https://github.com/Eskaykaushik/jarvis.git
cd jarvis

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp ../.env.example .env
# Edit .env with your API keys

# Run
uvicorn app.main:app --reload
```

### Frontend

Open `frontend/index.html` in a browser, or serve with any static server.

### Deploy

- **Frontend:** Push to `main` → GitHub Pages auto-deploys
- **Backend:** Connect repo to Render → it reads `render.yaml`
