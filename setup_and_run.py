#!/usr/bin/env python3
"""
Setup and Run Script for YouTube Channel Analyzer

This script helps set up the environment and run the analyzer.
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required Python packages."""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Dependencies installed successfully!")
    except subprocess.CalledProcessError:
        print("Failed to install dependencies. Please install manually with: pip install -r requirements.txt")
        return False
    return True

def run_analyzer():
    """Run the YouTube channel analyzer."""
    print("Starting YouTube Channel Analyzer...")
    try:
        subprocess.run([sys.executable, "youtube_analyzer.py"])
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    except Exception as e:
        print(f"Error running analyzer: {e}")

def main():
    """Main setup and run function."""
    print("YouTube Channel Analyzer Setup")
    print("=" * 40)

    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("Error: requirements.txt not found. Please make sure you're in the correct directory.")
        return

    # Install dependencies
    if not install_dependencies():
        return

    # Run the analyzer
    run_analyzer()

if __name__ == "__main__":
    main()