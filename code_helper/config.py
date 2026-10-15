"""Configuration for the Multi-Agent Code Helper.

Loads credentials from .env via python-dotenv.
Separates chat-model and embedding-model configuration.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file with override
load_dotenv(override=True)

# Prevent LiteLLM from timing out fetching cost map from remote GitHub repository
os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"

# Chat model configuration (shared across all agents)
_nim_key = os.getenv("NVIDIA_NIM_API_KEY")
_api_key = os.getenv("NVIDIA_API_KEY")

if not _nim_key or not _nim_key.startswith("nvapi-"):
    if _api_key and _api_key.startswith("nvapi-"):
        _nim_key = _api_key

NVIDIA_NIM_API_KEY = _nim_key

# Sync environment variables for LiteLLM
if NVIDIA_NIM_API_KEY and NVIDIA_NIM_API_KEY.startswith("nvapi-"):
    os.environ["NVIDIA_NIM_API_KEY"] = NVIDIA_NIM_API_KEY
    os.environ["NVIDIA_API_KEY"] = NVIDIA_NIM_API_KEY


NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://api.nvidia.com/v1")
NVIDIA_CHAT_MODEL = os.getenv("NVIDIA_CHAT_MODEL", "meta/llama-3.2-11b-vision-instruct")
NVIDIA_EMBED_MODEL = os.getenv("NVIDIA_EMBED_MODEL", "nvidia/nemotron-3-embed-1b")

# LiteLLM configuration
LITELLM_CHAT_MODEL = f"nvidia_nim/{NVIDIA_CHAT_MODEL}"

# Pinecone configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "code-helper")
PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")

# RAG pipeline configuration
CHUNK_SIZE = 100  # lines per chunk
CHUNK_OVERLAP = 20  # lines of overlap


def validate_config():
    """Validate that required configuration variables are set.

    Returns True if all required variables are present, False otherwise.
    """
    has_nvidia = bool(NVIDIA_NIM_API_KEY and NVIDIA_NIM_API_KEY != "your_nvidia_nim_api_key_here")
    has_pinecone = bool(PINECONE_API_KEY and PINECONE_API_KEY != "your_pinecone_api_key_here")
    if not has_nvidia or not has_pinecone:
        missing = []
        if not has_nvidia:
            missing.append("NVIDIA_NIM_API_KEY")
        if not has_pinecone:
            missing.append("PINECONE_API_KEY")
        print(f"Missing required environment variables: {missing}")
        return False
    return True