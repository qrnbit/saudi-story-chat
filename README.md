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
- Automatic fallback: if the main provider fails (for `openrouter_free`: if every model in the list fails) (429, server error, timeout, empty reply), the request is retried on Pollinations. Turn off with `FALLBACK_TO_POLLINATIONS=false`.
- Edit the persona in `system_prompt.txt`, or override it with a `SYSTEM_PROMPT` Space variable. The same prompt goes to every provider.
- Required secrets: `APP_PASSWORD` always, and `OPENROUTER_API_KEY` for `openrouter` / `openrouter_free`. The server refuses to start without them.
- `/chat` is password-protected (`X-App-Password` header) and limited to 20 requests per minute per IP (429 when exceeded).
- `/health` returns `OK` for UptimeRobot.

## ⚠️ OpenRouter limits / حدود OpenRouter

- **Free models (`:free`)**: about **50 requests per day** on a free account. Heavy long-story writing can hit this quickly.
- Buying **$10 of credit** (one time) raises the free-model limit to about **1000 requests per day**.
- Paid models (like the default Dolphin Venice model) need credit in your account and are billed per token, very cheaply.
- Check the current limits at https://openrouter.ai/docs/api-reference/limits

بالعربي: الموديلات المجانية في OpenRouter تعطي تقريباً **50 طلب باليوم**، والاستخدام المكثف لكتابة القصص الطويلة قد يحتاج تشحن **10 دولار** عشان يرتفع الحد إلى **1000 طلب يومياً**.

## Pollinations (free fallback)
Set the Space variable `PROVIDER=pollinations` (or rely on the automatic fallback) to send requests to `https://text.pollinations.ai/openai` with no API key. Free, but anonymous use is subject to Pollinations' own fair-use rate limits and model choice. See https://pollinations.ai

Deployment steps in Arabic: see `DEPLOY_AR.md`.
