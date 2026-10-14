"""Configuration for the Multi-Agent Code Helper.

Loads credentials from .env via python-dotenv.
Separates chat-model and embedding-model configuration.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Chat model configuration (shared across all agents)
NVIDIA_NIM_API_KEY = os.getenv("NVIDIA_NIM_API_KEY")
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
    required_vars = [
        "NVIDIA_NIM_API_KEY",
        "PINECONE_API_KEY",
    ]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"Missing required environment variables: {missing}")
        return False
    return True