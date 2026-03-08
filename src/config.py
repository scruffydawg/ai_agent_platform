import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Define project root explicitly to enforce absolute pathing
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Define standard directories
DEFAULT_STORAGE_ROOT = Path(os.environ.get("GUIDE_STORAGE_ROOT", str(Path.home() / "guide_storage")))
MEMORY_DIR = DEFAULT_STORAGE_ROOT / "data" / "memory"

# Ensure data directories exist
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# --- SECURITY & HARDENING (Phase 1) ---
ALLOWED_SENDERS = os.getenv("ALLOWED_SENDERS", "dave,scruffydawg").split(",")
WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN", "a7f3k9xm2p1q8r4n")
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "")

# --- TAILSCALE-FIRST NETWORKING PROTOCOL ---
# Identify Tailnet nodes for standardized routing
TAILNET_NODES = {
    "tai_mae": "taimae.tail692253.ts.net",
    "sienna": "sienna.tail692253.ts.net",
    "dash": "dash.tail692253.ts.net",
    "pi": "raspberrypi.tail692253.ts.net"
}

# Search & Localization
SEARCH_DEFAULT_REGION = "us-CO"
SEARCH_DEFAULT_LANGUAGE = "en-US"

# Source Reputation Tiers
SOURCE_TIERS = {
    "tier_1_local": ["denverpost.com", "cpr.org", "coloradosun.com", "9news.com", "denver7.com"],
    "tier_2_national": ["nytimes.com", "reuters.com", "apnews.com", "wsj.com", "bloomberg.com", "bbc.com"],
    "tier_3_academic": [".gov", ".edu"]
}

def resolve_target(node_key: str, default: str) -> str:
    """Helper to prioritize Tailnet DNS over local ethernet."""
    ts_dns = TAILNET_NODES.get(node_key)
    # In a production build, we would add a connectivity check here
    return ts_dns if ts_dns else default

# --- External Services (Tailscale Priority) ---
POSTGRES_URL = os.getenv("POSTGRES_URL", f"postgresql+asyncpg://user:pass@{resolve_target('dash', 'localhost')}:5432/agent_db")
QDRANT_URL = os.getenv("QDRANT_URL", f"http://localhost:6333")
SEARXNG_URL = os.getenv("SEARXNG_URL", f"http://localhost:8080/search")

# --- LLM & Memory Settings (Tai Mae Optimized) ---
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen3.5:27b") # Optimized for 24GB VRAM (RTX 3090)
LLM_ENGINE = os.getenv("LLM_ENGINE", "ollama")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
MEMORY_SOFT_LIMIT = 50000  # Optimized for Qwen 262K context window
