"""
app.py - FastAPI server for a model-agnostic chatbot on Hugging Face Spaces.

Routes:
  GET  /        -> the chat UI (static/index.html)
  GET  /health  -> 200 OK, for UptimeRobot pings (keeps the Space awake)
  GET  /info    -> active provider/model (shown in the UI header)
  POST /auth    -> checks a PIN from the lock screen (200 / 401), rate-limited
  POST /jobs, GET/DELETE /jobs/{id} -> background generation the UI polls
                   (survives the browser leaving; in-memory, lost on restart)
  POST /chat    -> sends the conversation + system prompt to the active provider,
                   falling back to Pollinations if it fails (see config.py)
                   Requires the X-App-Password header; max 20 requests/min per IP.

To change the provider, model, fallback, or persona, edit config.py /
system_prompt.txt or the Space variables. Never this file or the UI.
"""
import asyncio
import hmac
import secrets
import time
import logging
from typing import List, Literal, Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

import config

log = logging.getLogger("uvicorn.error")

PROVIDERS = ("openrouter", "openrouter_free", "pollinations", "aihorde")

# ---------------------------------------------------------------------------
# Startup checks: refuse to run with a bad configuration.
# ---------------------------------------------------------------------------
if not config.APP_PASSWORD:
    raise RuntimeError(
        "APP_PASSWORD is not set. Add it in Space Settings -> Variables and secrets -> New secret."
    )
if config.PROVIDER not in PROVIDERS:
    raise RuntimeError(f"PROVIDER must be one of {PROVIDERS}, got '{config.PROVIDER}'.")
if config.PROVIDER.startswith("openrouter") and not config.OPENROUTER_API_KEY:
    raise RuntimeError(
        "OPENROUTER_API_KEY is not set. Add it in Space Settings -> Variables and secrets -> New secret, "
        "or set PROVIDER=pollinations."
    )
if config.PROVIDER == "openrouter_free":
    if not config.FREE_MODEL_IDS:
        raise RuntimeError("FREE_MODEL_IDS is empty. Add at least one ':free' model.")
    for _m in config.FREE_MODEL_IDS:
        if not _m.endswith(":free"):
            log.warning("FREE_MODEL_IDS entry '%s' does not end with ':free'; it may be billed.", _m)


def models_for(provider: str) -> list:
    """Models to try, in order, for a provider."""
    if provider == "openrouter":
        return [config.MODEL_ID]
    if provider == "openrouter_free":
        return config.FREE_MODEL_IDS
    if provider == "aihorde":
        return config.AIHORDE_MODEL_IDS
    return [config.POLLINATIONS_MODEL]


def build_request(provider: str, model: str, messages: list, use_penalty: bool = True) -> tuple:
    """Return (url, headers, payload). The same SYSTEM_PROMPT goes to every provider."""
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": config.SYSTEM_PROMPT}] + messages,
        "temperature": config.TEMPERATURE,
        "max_tokens": config.MAX_TOKENS,
    }
    headers = {"Content-Type": "application/json"}
    if provider.startswith("openrouter"):
        headers["Authorization"] = f"Bearer {config.OPENROUTER_API_KEY}"  # from env, never hardcoded
        headers["X-Title"] = config.APP_TITLE
        return config.OPENROUTER_URL, headers, payload
    if provider == "aihorde":
        headers["Authorization"] = f"Bearer {config.AIHORDE_API_KEY}"
        headers["X-Title"] = config.APP_TITLE
        payload["max_tokens"] = config.AIHORDE_MAX_TOKENS
        # presence_penalty is the only anti-repetition knob AI Horde's OpenAI endpoint
        # accepts (frequency/repetition penalties are rejected). Some workers don't
        # support it, so call_model retries without it if no worker can serve it.
        if use_penalty and config.AIHORDE_PRESENCE_PENALTY:
            payload["presence_penalty"] = config.AIHORDE_PRESENCE_PENALTY
        return config.AIHORDE_URL, headers, payload
    # Pollinations: no API key and no Authorization header.
    return config.POLLINATIONS_URL, headers, payload


class ProviderError(Exception):
    def __init__(self, provider: str, status: int, message: str):
        super().__init__(f"{provider} error ({status}): {message}")
        self.status = status


async def call_model(client: httpx.AsyncClient, provider: str, model: str, messages: list) -> dict:
    """Call one model on one provider; return {"reply", "model"} or raise ProviderError."""
    try:
        return await _call_model(client, provider, model, messages, True)
    except ProviderError as e:
        if provider == "aihorde" and config.AIHORDE_PRESENCE_PENALTY and "declares" in str(e):
            log.warning("Retrying %s without presence_penalty: %s", model, e)
            return await _call_model(client, provider, model, messages, False)
        raise


async def _call_model(client, provider, model, messages, use_penalty) -> dict:
    url, headers, payload = build_request(provider, model, messages, use_penalty)
    try:
        r = await client.post(url, json=payload, headers=headers)
    except httpx.TimeoutException:
        raise ProviderError(f"{provider}/{model}", 504, "timed out")
    except httpx.HTTPError as e:
        raise ProviderError(f"{provider}/{model}", 502, f"network error: {e}")

    try:
        data = r.json()
    except ValueError:
        data = {}
    if r.status_code != 200 or not isinstance(data, dict) or "choices" not in data:
        err = data.get("error", {}) if isinstance(data, dict) else {}
        msg = err.get("message") if isinstance(err, dict) else None
        raise ProviderError(f"{provider}/{model}", r.status_code if r.status_code != 200 else 502, msg or r.text[:300])

    reply = (data["choices"][0].get("message") or {}).get("content") or ""
    if not reply.strip():
        raise ProviderError(f"{provider}/{model}", 502, "empty reply")
    return {"reply": reply, "model": data.get("model", model)}


async def call_provider(client: httpx.AsyncClient, provider: str, messages: list) -> dict:
    """Try each of the provider's models in order (openrouter_free may have several).
    Return the first success; if all fail, raise one ProviderError listing every failure."""
    errors = []
    for model in models_for(provider):
        try:
            return await call_model(client, provider, model, messages)
        except ProviderError as e:
            log.warning("Model failed: %s", e)
            errors.append(str(e))
    raise ProviderError(provider, 502, " ; ".join(errors))


# ---------------------------------------------------------------------------
# Rate limiting (per client IP). Hugging Face sits behind a proxy, so the real
# client IP is the first entry of X-Forwarded-For.
# ---------------------------------------------------------------------------
def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


limiter = Limiter(key_func=client_ip)

app = FastAPI(title=config.APP_TITLE)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # returns 429
app.mount("/static", StaticFiles(directory="static"), name="static")


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


class AuthRequest(BaseModel):
    pin: str


def password_ok(value: Optional[str]) -> bool:
    """Constant-time compare with APP_PASSWORD."""
    return bool(value) and hmac.compare_digest(value.encode(), config.APP_PASSWORD.encode())


@app.get("/")
def index():
    return FileResponse("static/index.html")


@app.api_route("/health", methods=["GET", "HEAD"], response_class=PlainTextResponse)
def health():
    # UptimeRobot pings this every 5 minutes. Cheap: never calls a model.
    return "OK"


@app.get("/info")
def info():
    return {
        "provider": config.PROVIDER,
        "model": ", ".join(models_for(config.PROVIDER)),
        "fallback": config.FALLBACK_TO_POLLINATIONS and config.PROVIDER != "pollinations",
        "pin_length": len(config.APP_PASSWORD),  # number of dots on the lock screen
    }


@app.post("/auth")
@limiter.limit(config.AUTH_RATE_LIMIT)
async def auth(request: Request, req: AuthRequest):
    # Used by the PIN lock screen. The PIN itself is never sent to the browser;
    # each attempt is checked here. (The "enter it 4 times" logic is client-side.)
    if not password_ok(req.pin):
        raise HTTPException(status_code=401, detail="Wrong PIN")
    return {"ok": True}


async def generate(history: list) -> dict:
    """Run one generation (primary provider, then optional Pollinations fallback).
    Returns the result dict or raises HTTPException(502)."""
    async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT_SECONDS) as client:
        try:
            result = await call_provider(client, config.PROVIDER, history)
            return {**result, "provider": config.PROVIDER, "fallback_used": False}
        except ProviderError as primary_error:
            can_fallback = config.FALLBACK_TO_POLLINATIONS and config.PROVIDER != "pollinations"
            if not can_fallback:
                raise HTTPException(status_code=502, detail=str(primary_error))
            log.warning("Primary provider failed (%s); falling back to pollinations.", primary_error)
            try:
                result = await call_provider(client, "pollinations", history)
                return {
                    **result,
                    "provider": "pollinations",
                    "fallback_used": True,
                    "primary_error": str(primary_error),
                }
            except ProviderError as fallback_error:
                raise HTTPException(
                    status_code=502,
                    detail=f"{primary_error} | fallback: {fallback_error}",
                )


def check_chat(req: ChatRequest, x_app_password: Optional[str]) -> list:
    # Password is checked on the server for every request (constant-time compare).
    if not password_ok(x_app_password):
        raise HTTPException(status_code=401, detail="Wrong password")
    if not req.messages:
        raise HTTPException(status_code=400, detail="No messages")
    return [m.model_dump() for m in req.messages[-config.MAX_HISTORY_MESSAGES:]]


@app.post("/chat")
@limiter.limit(config.RATE_LIMIT)
async def chat(
    request: Request,  # required by slowapi
    req: ChatRequest,
    x_app_password: Optional[str] = Header(default=None),
):
    """Synchronous chat (waits for the reply). The UI uses /jobs instead."""
    return await generate(check_chat(req, x_app_password))


# ---------------------------------------------------------------------------
# Background jobs: generation runs on the server, independent of the browser
# connection, so leaving Safari (switching apps / locking the phone) doesn't
# kill it. The UI starts a job, keeps the job_id in localStorage, and polls.
# Jobs live in memory only: they are lost on restart/redeploy (acceptable).
# ---------------------------------------------------------------------------
JOBS: dict = {}


def _prune_jobs() -> None:
    now = time.time()
    for jid in [j for j, v in JOBS.items() if now - v["created"] > config.JOB_TTL_SECONDS]:
        task = JOBS.pop(jid).get("task")
        if task and not task.done():
            task.cancel()
    # Cap: drop the oldest finished jobs first, then the oldest of any kind.
    while len(JOBS) >= config.MAX_JOBS:
        done = [j for j, v in JOBS.items() if v["status"] != "pending"]
        victim = min(done or JOBS, key=lambda j: JOBS[j]["created"])
        task = JOBS.pop(victim).get("task")
        if task and not task.done():
            task.cancel()


async def _run_job(job_id: str, history: list) -> None:
    job = JOBS.get(job_id)
    try:
        result = await generate(history)
        if job is not None:
            job.update(status="done", finished=time.time(), **result)
    except asyncio.CancelledError:
        if job is not None:
            job.update(status="error", error="cancelled", finished=time.time())
        raise
    except HTTPException as e:
        if job is not None:
            job.update(status="error", error=str(e.detail), finished=time.time())
    except Exception as e:  # never leave a job stuck in "pending"
        log.exception("Job %s crashed", job_id)
        if job is not None:
            job.update(status="error", error=f"internal error: {e}", finished=time.time())


def _public(job_id: str, job: dict) -> dict:
    out = {"job_id": job_id, "status": job["status"], "created": job["created"]}
    for k in ("reply", "model", "provider", "fallback_used", "primary_error", "error", "finished"):
        if k in job:
            out[k] = job[k]
    return out


def _get_job(job_id: str, x_app_password: Optional[str]) -> dict:
    if not password_ok(x_app_password):
        raise HTTPException(status_code=401, detail="Wrong password")
    job = JOBS.get(job_id)
    if job is None or time.time() - job["created"] > config.JOB_TTL_SECONDS:
        raise HTTPException(status_code=404, detail="Job not found (expired or server restarted)")
    return job


@app.post("/jobs")
@limiter.limit(config.RATE_LIMIT)
async def start_job(
    request: Request,
    req: ChatRequest,
    x_app_password: Optional[str] = Header(default=None),
):
    history = check_chat(req, x_app_password)
    _prune_jobs()
    job_id = secrets.token_urlsafe(12)
    JOBS[job_id] = {"status": "pending", "created": time.time()}
    # Keep a reference to the task so it isn't garbage-collected mid-run.
    JOBS[job_id]["task"] = asyncio.create_task(_run_job(job_id, history))
    return _public(job_id, JOBS[job_id])


@app.get("/jobs/{job_id}")
@limiter.limit(config.JOB_POLL_RATE_LIMIT)
async def get_job(request: Request, job_id: str, x_app_password: Optional[str] = Header(default=None)):
    return _public(job_id, _get_job(job_id, x_app_password))


@app.delete("/jobs/{job_id}")
@limiter.limit(config.JOB_POLL_RATE_LIMIT)
async def cancel_job(request: Request, job_id: str, x_app_password: Optional[str] = Header(default=None)):
    job = _get_job(job_id, x_app_password)
    task = job.get("task")
    if task and not task.done():
        task.cancel()
    JOBS.pop(job_id, None)
    return {"job_id": job_id, "status": "cancelled"}
