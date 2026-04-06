import sys
import os
import uvicorn

# Add the parent directory to the path so we can import from the root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api import app

def main():
    uvicorn.run("api:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
