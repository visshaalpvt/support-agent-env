"""
OpenEnv multi-mode deployment entry point.
This file re-exports the FastAPI app from the root api.py.
"""

import sys
import os

# Add parent directory to path so we can import from root
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import the FastAPI app from root api.py
from api import app

# Optionally, import environment for context
from support_env import SupportAgentEnv

def main():
    """Main entry point for OpenEnv deployment."""
    print("[INFO] OpenEnv support-agent-env starting")
    # This is typically called by the OpenEnv orchestrator
    pass

if __name__ == "__main__":
    main()

# For debugging
print("[INFO] OpenEnv server/app.py loaded")
print(f"[INFO] FastAPI app imported from api.py")
