#!/usr/bin/env python3
"""
Initialize necessary directories for the LLM-Driven Multi-Agent Android QA project.
This script creates directories that are excluded from version control.
"""
from pathlib import Path

def init_directories():
    """Create necessary directories for the project."""
    directories = [
        "logs/screenshots",
        "memory_store"
    ]
    
    print("📁 Initializing project directories...")
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")
    
    print("\n🎉 All directories initialized successfully!")

if __name__ == "__main__":
    init_directories() 