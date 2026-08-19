# Jarvis — Modular Build Plan

## Project Structure

```
jarvis/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app entry
│   │   ├── config.py                # Settings, env vars
│   │   ├── models/
│   │   │   ├── schemas.py           # Pydantic request/response
│   │   │   └── db.py                # Redis connection
│   │   ├── providers/
│   │   │   ├── base.py              # Abstract provider interface
│   │   │   ├── groq_provider.py     # Groq client
│   │   │   ├── openrouter_provider.py
│   │   │   ├── together_provider.py
│   │   │   └── ollama_provider.py
│   │   ├── reliability/
│   │   │   ├── circuit_breaker.py   # Per-provider circuit breaker
│   │   │   ├── retry.py             # Exponential backoff
│   │   │   └── fallback_chain.py    # Orchestrates provider order
│   │   ├── cache/
│   │   │   ├── redis_cache.py       # Redis read/write/TTL
│   │   │   └── cache_key.py         # Key generation logic
│   │   ├── services/
│   │   │   ├── chat.py              # /chat business logic
│   │   │   ├── summary.py           # /summary logic
│   │   │   └── email.py             # Email sending (Resend)
│   │   └── routes/
│   │       ├── chat.py              # POST /chat
│   │       ├── summary.py           # POST /summary
│   │       ├── email.py             # POST /email/send
│   │       ├── conversation.py      # GET /conversation/{id}
│   │       └── health.py            # GET /health
│   ├── tests/
│   │   ├── test_providers.py
│   │   ├── test_circuit_breaker.py
│   │   ├── test_cache.py
│   │   └── test_endpoints.py
│   ├── requirements.txt
│   └── Dockerfile                   # For Render
├── frontend/
│   ├── index.html
│   ├── css/
│   ├── js/
│   │   ├── app.js                   # Main entry
│   │   ├── chat.js                  # Chat UI
│   │   ├── cache.js                 # LocalStorage + IndexedDB
│   │   ├── api.js                   # Backend API calls
│   │   ├── offline.js               # Request queuing
│   │   └── utils.js                 # Formatting, helpers
│   └── assets/
├── .github/workflows/               # CI if needed
├── README.md
├── PLAN.md
├── .env.example
└── .gitignore
```

---

## Phase 1: Backend Foundation ✅ DONE
**Goal**: Working FastAPI app with config and project skeleton

- [x] `config.py` — env-based settings (API keys, Redis URL, provider toggles)
- [ ] `schemas.py` — Pydantic models for ChatRequest, ChatResponse, Conversation, etc.
- [ ] `db.py` — Redis connection manager (lazy, reconnection-safe)
- [x] `main.py` — FastAPI app with CORS, include routers
- [x] `requirements.txt` — all dependencies
- [x] `.env.example` — env var template
- [x] Directory structure created
- [x] Server verified — `/health` returns `{"status": "ok"}`

---

## Phase 2: Model Provider Layer ✅ DONE
**Goal**: Plug-and-play provider abstraction

Fallback chain: **Groq → OpenRouter → Together → Gemini → Cerebras**

- [x] `base.py` — `BaseProvider` ABC with `generate(prompt, context) -> ProviderResponse`
- [x] `groq_provider.py` — Groq SDK (primary, free tier)
- [x] `openrouter_provider.py` — httpx + OpenRouter API (fallback #1)
- [x] `together_provider.py` — httpx + Together API (fallback #2)
- [x] `gemini_provider.py` — httpx + Google Gemini API (fallback #3)
- [x] `cerebras_provider.py` — httpx + Cerebras API (fallback #4)
- [x] Config updated — all model names + API keys in config.py and .env.example
- [ ] Tests: mock each provider, verify interface compliance

---

## Phase 3: Caching Layer ✅ DONE
**Goal**: Redis caching with TTL and semantic keys

- [x] `redis_cache.py` — `cache_get()`, `cache_set()`, `cache_get_stale()`, `cache_delete()`, `cache_health()`
- [x] `cache_key.py` — SHA256 hash of prompt + context, prefixed per endpoint
- [x] Stale-while-revalidate — serves cached response if < 24hr old
- [x] TTL config — chat: 1hr, summary: 6hr (from settings)
- [x] Upstash Redis compatible (standard `redis` client)
- [ ] Tests: mock Redis, verify hit/miss/stale behavior

---

## Phase 4: Reliability Engine ✅ DONE
**Goal**: Fault-tolerant fallback chain

- [x] `circuit_breaker.py` — Track failures per provider; open after 3 failures in 5min window; auto-close after 5min cooldown; `status()` returns healthy/degraded/open
- [x] `retry.py` — Exponential backoff decorator (max 2 retries, base 1s, jitter)
- [x] `fallback_chain.py` — Ordered provider list; skips open circuits; retry + circuit breaker per provider; raises `RuntimeError` if all fail
- [ ] Tests: simulate failures, verify circuit opens, fallback triggers, retries work

---

## Phase 5: API Endpoints ✅ DONE
**Goal**: All routes wired with reliability + caching

- [x] `schemas.py` — `ChatRequest`, `ChatResponse`, `Conversation`, `ConversationMessage`
- [x] `services/chat.py` — cache check → stale check → fallback chain → cache result → save conversation
- [x] `routes/chat.py` — `POST /chat` wired with fallback chain
- [x] `main.py` — providers loaded from env, fallback chain initialized, router included, health endpoint with provider status + Redis check
- [ ] `POST /summary` — Summarize a conversation
- [ ] `POST /email/send` — Send summary via Resend
- [ ] `GET /conversation/{id}` — Retrieve conversation
- [ ] Tests: integration tests with mocked providers + cache

---

## Phase 6: Frontend Foundation ✅ DONE
**Goal**: Static HTML/CSS/JS chat UI

- [x] `index.html` — Clean chat layout
- [x] `chat.js` — Message rendering, input handling, send flow
- [x] `api.js` — Fetch wrapper for all backend endpoints
- [x] `app.js` — Init, event listeners, state management
- [x] `utils.js` — Timestamp formatting, sanitization
- [x] `style.css` — Responsive design (mobile-first, dark theme)
- [ ] Tests: manual visual testing

---

## Phase 7: Frontend Caching & Offline
**Goal**: Offline resilience + fast repeated loads

- `cache.js` — LocalStorage (last 10 messages) + IndexedDB (full history)
- `offline.js` — Queue outbound requests when offline; retry on reconnect
- Status indicator (online/offline/degraded)
- IndexedDB schema: conversations table with timestamps
- Auto-sync when backend becomes reachable again

---

## Phase 8: Integration & Testing
**Goal**: End-to-end verification

- Backend: pytest with coverage
- Frontend: manual E2E + optional Playwright smoke tests
- Test the full fallback chain under simulated outages
- Test offline → online transition
- Load test: verify free-tier rate limits aren't exceeded

---

## Phase 9: Deployment Config
**Goal**: Ready for Render + GitHub Pages

- `Dockerfile` for backend (Render)
- `render.yaml` blueprint
- GitHub Pages workflow for frontend (static deploy)
- `.env.example` with all required vars
- UptimeRobot / cron-job.org keep-alive setup instructions
- README: deployment guide

---

## Phase 10: Polish & Future Enhancements
**Goal**: Nice-to-have features

- Voice conversations (Web Speech API)
- File/image sharing
- Multiple AI personalities (system prompt variations)
- Push notifications
- Searchable conversations
- Analytics dashboard
