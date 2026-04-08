import sys
import os
import uvicorn

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Try to import from api.py
try:
    from api import app
except ImportError:
    # Fallback: create a minimal app
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    def root():
        return {"status": "ok", "message": "SupportAgentEnv API"}

def main():
    """Entry point for OpenEnv validator"""
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
