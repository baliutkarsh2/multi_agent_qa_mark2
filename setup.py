#!/usr/bin/env python3
"""
Setup script for the LLM-Driven Multi-Agent Android QA project.
This script helps users set up their environment and create the .env file.
"""
import os
import shutil
from pathlib import Path

def main():
    print("LLM-Driven Multi-Agent Android QA Setup")
    print("=" * 50)
    
    # Check if .env already exists
    env_file = Path(".env")
    if env_file.exists():
        print("⚠️  .env file already exists. Skipping creation.")
        return
    
    # Copy env_example.txt to .env
    example_file = Path("env_example.txt")
    if example_file.exists():
        shutil.copy(example_file, env_file)
        print("✅ Created .env file from env_example.txt")
        print("\n📝 Next steps:")
        print("1. Edit .env file and add your OpenAI API key")
        print("2. Run: python init_dirs.py")
        print("3. Run: python -m runners.run_example --goal 'your goal here'")
    else:
        print("❌ env_example.txt not found. Please create it manually.")
        
        # Create a basic .env file
        with open(env_file, 'w') as f:
            f.write("# API Keys and Sensitive Configuration\n")
            f.write("# Copy this file to .env and fill in your actual values\n\n")
            f.write("# OpenAI API Key (required)\n")
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n\n")
            f.write("# Android Device Configuration (optional)\n")
            f.write("ANDROID_EMULATOR_SERIAL=emulator-5554\n\n")
            f.write("# Logging Configuration (optional)\n")
            f.write("LOG_LEVEL=INFO\n\n")
            f.write("# Memory Store Configuration (optional)\n")
            f.write("MEMORY_STORE_PATH=memory_store\n\n")
            f.write("# Screenshot Directory (optional)\n")
            f.write("SCREENSHOT_DIR=logs/screenshots\n")
        
        print("✅ Created basic .env file")
        print("\n📝 Next steps:")
        print("1. Edit .env file and add your OpenAI API key")
        print("2. Run: python init_dirs.py")
        print("3. Run: python -m runners.run_example --goal 'your goal here'")

if __name__ == "__main__":
    main() 