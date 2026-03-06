"""Central configuration accessible across all modules."""
from __future__ import annotations
import os
from .env_loader import get_env_var, load_env_file

# Load environment variables from .env file
load_env_file()

# API Keys and sensitive configuration
try:
    OPENAI_API_KEY: str = get_env_var("OPENAI_API_KEY", required=True)
except ValueError as e:
    print("❌ Configuration Error:")
    print("   The OPENAI_API_KEY environment variable is not set.")
    print("   Please follow these steps:")
    print("   1. Run: python setup.py")
    print("   2. Edit the .env file and add your OpenAI API key")
    print("   3. Make sure the .env file exists in the project root")
    print(f"   Error: {e}")
    raise

# Android configuration
ANDROID_EMULATOR_SERIAL: str = get_env_var("ANDROID_EMULATOR_SERIAL", "emulator-5554")

# Logging configuration
LOG_LEVEL: str = get_env_var("LOG_LEVEL", "INFO")

# Memory store configuration
MEMORY_STORE_PATH: str = get_env_var("MEMORY_STORE_PATH", "memory_store")

# Screenshot directory
SCREENSHOT_DIR: str = get_env_var("SCREENSHOT_DIR", "logs/screenshots") 