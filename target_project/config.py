"""Configuration module for the target Python project.

Contains global configuration settings, constants, and environment
variable loading logic for the codebase.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project constants
PROJECT_NAME = "Sample Python Project"
VERSION = "1.0.0"

# Application settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
HOST = os.getenv("HOST", "localhost")
PORT = int(os.getenv("PORT", "8080"))

# Feature flags
FEATURE_A = os.getenv("FEATURE_A", "False").lower() == "true"
FEATURE_B = os.getenv("FEATURE_B", "False").lower() == "true"


def get_config():
    """Return a configuration dictionary."""
    return {
        "project_name": PROJECT_NAME,
        "version": VERSION,
        "debug": DEBUG,
        "host": HOST,
        "port": PORT,
        "feature_a": FEATURE_A,
        "feature_b": FEATURE_B,
    }