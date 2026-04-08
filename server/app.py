import sys
import os
import uvicorn

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from api import app
except ImportError:
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    def root():
        return {"status": "ok", "message": "SupportAgentEnv"}

def main():
    """Entry point for OpenEnv validator - required by pyproject.toml [project.scripts]"""
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
