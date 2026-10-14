"""Backend configuration settings.

Loads settings from environment variables with sensible defaults for local development.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Find workspace root .env if present
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = ROOT_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# ADK API server connection
ADK_API_BASE_URL = os.getenv("ADK_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
ADK_APP_NAME = os.getenv("ADK_APP_NAME", "code_helper")
ADK_DEFAULT_USER_ID = os.getenv("ADK_DEFAULT_USER_ID", "default_user")

# Frontend CORS
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", f"{FRONTEND_ORIGIN},http://127.0.0.1:5173").split(",")
    if origin.strip()
]

# Server settings
BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8001"))
REQUEST_TIMEOUT_SECONDS = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "120.0"))

# Validation status
def check_required_env_vars() -> dict[str, bool]:
    """Check configuration status without exposing credentials."""
    return {
        "nvidia_configured": bool(os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NVIDIA_API_KEY")),
        "pinecone_configured": bool(os.getenv("PINECONE_API_KEY")),
    }
