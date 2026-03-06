"""
Environment variable loader with .env file support.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

def load_env_file(env_file: str = ".env") -> None:
    """
    Load environment variables from a .env file.
    .env file values take precedence over existing environment variables.
    
    Args:
        env_file: Path to the .env file (default: .env)
    """
    env_path = Path(env_file)
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    # Always override existing environment variables with .env values
                    os.environ[key.strip()] = value

def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> str:
    """
    Get an environment variable with optional default value.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        required: If True, raises ValueError when variable is not found
        
    Returns:
        Environment variable value
        
    Raises:
        ValueError: If required=True and variable is not found
    """
    value = os.getenv(key, default)
    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    return value

# Load .env file on module import
load_env_file() 