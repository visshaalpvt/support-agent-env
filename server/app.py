import sys
import os
import uvicorn

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api import app

def main():
    """Entry point for OpenEnv validator"""
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
