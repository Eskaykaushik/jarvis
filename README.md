AI Assistant Service
A personal AI assistant with a lightweight static frontend
and an intelligent backend service — built entirely on
free-tier infrastructure, designed for high reliability
through layered caching and multi-provider fallback.
Philosophy
Keep the frontend simple. Keep the assistant intelligent.
The browser handles rendering, caching, and
responsiveness. All AI processing stays in the assistant
service. Every dependency is chosen so the whole
system can run at zero cost while staying resilient to any
single provider going down, rate-limiting, or timing out.
Architecture
Frontend
Hosting: GitHub Pages (static, free, unlimited
bandwidth on public repos)
Cache layers: LocalStorage (fast, small) →
IndexedDB (larger, structured, survives longer)Role: render UI, cache recent conversations, queue
requests when offline, retry on reconnect
Backend — Assistant Service
Hosting: Render free tier, FastAPI
Primary model: Groq (free tier, very low latency)
Fallback models: additional free-tier providers (e.g.
OpenRouter free models, Together.ai free tier, or a
self-hosted Ollama model as a last-resort local
fallback)
Cache: Redis (Upstash free tier — serverless, no idle
server cost)
Both frontend and backend live in a single private repo,
deployed independently.
Reliability Design
Reliability comes from layering — every request has
multiple chances to succeed before the user ever sees
an error.
User Request
│
▼
Frontend Cache (LocalStorage/IndexedDB) ────
hit? return instantly
│ miss
▼Backend Cache (Redis) ──── hit? return,
refresh frontend cache
│ miss
▼
Primary Model (Groq)
│ fail / timeout / rate-limited
▼
Retry with exponential backoff (max 2
retries)
│ still failing
▼
Secondary Model (fallback provider)
│ fail
▼
Tertiary Model (local/self-hosted, if
configured)
│ fail
▼
Stale cached response (if available, marked
as "may be outdated")
│ none available
▼
Graceful error (clear message, retry button,
never a raw stack trace)
Key reliability features
Exponential backoff retries — avoid hammering a
struggling provider; back off before failing over
Circuit breaker per provider — if a model fails
repeatedly in a short window, skip it for N minutes
instead of retrying every request against a dead
endpointMulti-provider fallback chain — never depend on a
single free-tier model; rotate through providers in
priority order
Timeouts on every call — no request hangs
indefinitely; a slow provider fails fast into the fallback
chain
Redis caching with TTL — cuts model calls for
repeated/common queries, which also protects free-
tier rate limits
Stale-while-revalidate — serve a cached response
immediately if available, refresh in the background
Idempotent request handling — safe to retry a
request without duplicating side effects (e.g.
sending an email twice)
Health checks — /health endpoint checks Redis
connectivity and pings each model provider on an
interval, so the fallback chain always reflects current
provider status
Session persistence — conversations survive a
backend restart or redeploy (Render free tier spins
down on inactivity, so this matters)
Cold-start mitigation — a lightweight scheduled ping
(e.g. free UptimeRobot/cron-job.org monitor) keeps
the Render service warm and avoids cold-start
latency on first request
Error recovery — failures degrade gracefully (cached
→ generic helpful message) rather than surfacing
raw errors to the userCaching Strategy
Frontend
Browser → LocalStorage (hot, small) →
IndexedDB (larger, structured)
Read path checks LocalStorage first, then IndexedDB,
before ever hitting the network.
Backend
Request → Redis
│
┌────┴────┐
Hit
Miss
│
Return
│
Call model → Cache result →
Return
Cache keys should incorporate the query and relevant
context so semantically identical requests can reuse
cached responses.
API EndpointsMethodEndpoint
POST/chat
Purpose
Send a message, get
an assistant response
Generate a summary
POST
/summary
(e.g. "send today's
summary")
Send
POST
/email/send
conversation/summary
via email
GET/conversation/{id}
GET/health
Retrieve a stored
conversation
Service, cache, and
provider health status
Staying Free
Component
Frontend
hosting
Free-tier choice
Notes
Free for public
GitHub Pages
repos, generous
bandwidthComponent
Free-tier choice
Notes
Spins down
BackendRender free webwhen idle —
hostingservicemitigate with a
keep-alive ping
Primary
model
Groq
OpenRouter /
FallbackTogether.ai free
model(s)tier, or self-hosted
Ollama
Cache
Upstash Redis free
tier
Free tier, fast
inference
Keeps the chain
alive if Groq
rate-limits
Serverless
pricing, no cost
while idle
Free, also
UptimeUptimeRobot /mitigates
monitorcron-job.orgRender cold
starts
EmailResend free tier /Enough volume
sendingEmailJSfor personal use
Design rule: every new feature should default to a
provider with a genuinely free tier before considering a
paid one, and the fallback chain should always include at
least one provider outside your primary vendor.Future Enhancements
Voice conversations
File sharing
Image sharing
Multiple AI personalities
Multiple users
Push notifications
Mobile application
Searchable conversations
Analytics dashboard
