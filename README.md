---
title: Saudi Story Chat
emoji: 📖
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Saudi Story Chat

Model-agnostic chat UI (FastAPI) that talks to OpenRouter, with a Saudi-dialect creative-writing persona.

- `PROVIDER` (Space variable or `config.py`):
  - `openrouter` (default): OpenRouter with `MODEL_ID` (paid or free).
  - `openrouter_free`: OpenRouter, trying each `:free` model in `FREE_MODEL_IDS` (comma-separated) in order; no credit needed.
  - `pollinations`: Pollinations.ai, free, no API key.
  - `aihorde` (current live setup): AI Horde volunteer GPUs, free, no card. Models in `AIHORDE_MODEL_IDS` (comma list, tried in order), optional free `AIHORDE_API_KEY` for faster queue, `AIHORDE_PRESENCE_PENALTY` (default 0.4, anti-repetition; the only penalty AI Horde accepts, auto-dropped if no worker supports it). Replies take ~30-120 s.
- Automatic fallback: if the main provider fails (for `openrouter_free`: if every model in the list fails) (429, server error, timeout, empty reply), the request is retried on Pollinations. Turn off with `FALLBACK_TO_POLLINATIONS=false`.
- Edit the persona in `system_prompt.txt`, or override it with a `SYSTEM_PROMPT` Space variable. The same prompt goes to every provider.
- Required secrets: `APP_PASSWORD` always, and `OPENROUTER_API_KEY` for `openrouter` / `openrouter_free`. The server refuses to start without them.
- `/chat` is password-protected (`X-App-Password` header) and limited to 20 requests per minute per IP (429 when exceeded).
- `/health` returns `OK` for UptimeRobot.
- `POST /auth` checks a PIN from the lock screen (200/401, 30/min per IP). The UI is an iPhone-style PIN lock: the PIN (= `APP_PASSWORD`) is never in the page; each attempt is verified by `/auth`. By the owner's request, the correct PIN must be entered 4 times (the first 3 correct entries show "wrong"; wrong PINs don't count). The count is in sessionStorage; the session locks again when Safari's tab/session ends or on a 401.
- Background jobs: the UI calls `POST /jobs` (password + 20/min), gets a `job_id` immediately, and polls `GET /jobs/{id}` every ~3 s (`DELETE` cancels). Generation runs as a server-side asyncio task independent of the browser, so leaving Safari mid-story doesn't lose it; the pending job is kept in localStorage and resumed on return. Jobs are in memory (expire after 1 h, max 200) and are lost on restart/redeploy. `POST /chat` (synchronous) still works.
- The UI is mobile-first for iPhone Safari (safe areas, keyboard-aware layout, add-to-home-screen icon) and keeps chat history in localStorage.
- Hosting: Render free web service (Docker), auto-deploys from GitHub `main`. Settings: Render dashboard -> service -> Environment.

## ⚠️ OpenRouter limits / حدود OpenRouter

- **Free models (`:free`)**: about **50 requests per day** on a free account. Heavy long-story writing can hit this quickly.
- Buying **$10 of credit** (one time) raises the free-model limit to about **1000 requests per day**.
- Paid models (like the default Dolphin Venice model) need credit in your account and are billed per token, very cheaply.
- Check the current limits at https://openrouter.ai/docs/api-reference/limits

بالعربي: الموديلات المجانية في OpenRouter تعطي تقريباً **50 طلب باليوم**، والاستخدام المكثف لكتابة القصص الطويلة قد يحتاج تشحن **10 دولار** عشان يرتفع الحد إلى **1000 طلب يومياً**.

## Pollinations (free fallback)
Set the Space variable `PROVIDER=pollinations` (or rely on the automatic fallback) to send requests to `https://text.pollinations.ai/openai` with no API key. Free, but anonymous use is subject to Pollinations' own fair-use rate limits and model choice. See https://pollinations.ai

Deployment steps in Arabic: see `DEPLOY_AR.md`.
