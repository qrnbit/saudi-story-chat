"""
config.py - Every setting you might want to change lives here.
The UI never needs to change when you edit this file.
Every value can also be overridden from Space Settings -> Variables and secrets.
"""
import os

# ---------------------------------------------------------------------------
# 0) PROVIDER  <-- which backend answers the chat
# ---------------------------------------------------------------------------
#   "openrouter"      -> OpenRouter with MODEL_ID (any model, paid or free)
#   "openrouter_free" -> OpenRouter, trying each model in FREE_MODEL_IDS in order
#                        (":free" models, no credit needed)
#   "pollinations"    -> Pollinations.ai, free, no API key, no Authorization header
PROVIDER = os.environ.get("PROVIDER", "openrouter").strip().lower()

# ---------------------------------------------------------------------------
# 1) MODELS
# ---------------------------------------------------------------------------
# Used ONLY when PROVIDER = "openrouter".
# Default: Dolphin Mistral 24B Venice Edition (uncensored creative model, paid,
# about $0.20 per million tokens, needs credit). Browse: https://openrouter.ai/models
MODEL_ID = os.environ.get("MODEL_ID", "cognitivecomputations/dolphin-mistral-24b-venice-edition")

# Used ONLY when PROVIDER = "openrouter_free". Comma-separated list of ":free"
# models, tried in order: if one fails, the next is tried; if all fail, the
# request falls back to Pollinations (when FALLBACK_TO_POLLINATIONS is on).
# Free list (changes often): https://openrouter.ai/models?max_price=0
# See DEPLOY_AR.md for the list that was available when this was written.
FREE_MODEL_IDS = [
    m.strip()
    for m in os.environ.get(
        "FREE_MODEL_IDS",
        "google/gemma-4-31b-it:free,nousresearch/hermes-3-llama-3.1-405b:free",
    ).split(",")
    if m.strip()
]

# Used ONLY when PROVIDER = "pollinations" (or when falling back to it).
POLLINATIONS_MODEL = os.environ.get("POLLINATIONS_MODEL", "openai")

# ---------------------------------------------------------------------------
# 2) AUTOMATIC FALLBACK
# ---------------------------------------------------------------------------
# If the main provider fails (429 rate limit, server error, timeout, network
# error, or empty reply), retry the same request on Pollinations.
# Set the Space variable FALLBACK_TO_POLLINATIONS=false to turn it off.
FALLBACK_TO_POLLINATIONS = os.environ.get("FALLBACK_TO_POLLINATIONS", "true").strip().lower() in ("1", "true", "yes", "on")

# ---------------------------------------------------------------------------
# 3) GENERATION SETTINGS
# ---------------------------------------------------------------------------
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.95"))  # higher = more creative
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "4096"))     # long stories need more
MAX_HISTORY_MESSAGES = 30   # how many past messages are sent back to the model
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "300"))
RATE_LIMIT = "20/minute"    # max /chat requests per IP
AUTH_RATE_LIMIT = "30/minute"  # max /auth (PIN lock) attempts per IP

# ---------------------------------------------------------------------------
# 4) SYSTEM PROMPT  <-- EDIT THE PERSONA IN system_prompt.txt
# ---------------------------------------------------------------------------
# The persona lives in its own file so you can edit it without touching code.
# You can also paste a whole new prompt into a Space variable named SYSTEM_PROMPT,
# which overrides the file. The same prompt is sent to every provider.
_PROMPT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "system_prompt.txt")


def _load_system_prompt() -> str:
    override = os.environ.get("SYSTEM_PROMPT", "").strip()
    if override:
        return override
    with open(_PROMPT_FILE, encoding="utf-8") as f:
        return f.read().strip()


SYSTEM_PROMPT = _load_system_prompt()

# ---------------------------------------------------------------------------
# 5) SECRETS (set in Space Settings -> Secrets, never hardcode)
# ---------------------------------------------------------------------------
# Required when PROVIDER is "openrouter" or "openrouter_free".
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
# REQUIRED always: every /chat request must send it in the X-App-Password header.
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")

# ---------------------------------------------------------------------------
# 6) ENDPOINTS (no need to change)
# ---------------------------------------------------------------------------
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
POLLINATIONS_URL = "https://text.pollinations.ai/openai"

# AI Horde (free volunteer GPUs, allows adult fiction between adults).
# PROVIDER = "aihorde". Anonymous key 0000000000 works; a free key from
# https://aihorde.net/register gives better queue priority (set AIHORDE_API_KEY).
AIHORDE_URL = "https://oai.aihorde.net/v1/chat/completions"
AIHORDE_API_KEY = os.environ.get("AIHORDE_API_KEY", "").strip() or "0000000000"
AIHORDE_MODEL_IDS = [
    m.strip()
    for m in os.environ.get(
        "AIHORDE_MODEL_IDS",
        "koboldcpp/G4-MeroMero-26B-A4B-it-uncensored-heretic,Nimbz/Gemma-4-Dark-Orthia-31B,koboldcpp/Gemma-4-E4B-it-Ultra-Uncensored-Heretic",
    ).split(",")
    if m.strip()
]
# Anti-repetition (0 = off). Only presence_penalty is accepted by AI Horde.
AIHORDE_PRESENCE_PENALTY = float(os.environ.get("AIHORDE_PRESENCE_PENALTY", "0.4"))
AIHORDE_MAX_TOKENS = int(os.environ.get("AIHORDE_MAX_TOKENS", "1024"))
APP_TITLE = "Saudi Story Chat"
