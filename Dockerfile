FROM python:3.9-slim

WORKDIR /app

# Install all dependencies needed by api.py AND inference.py
RUN pip install --no-cache-dir fastapi uvicorn pydantic python-multipart openai httpx

# Copy all essential files
COPY api.py .
COPY safe_grader.py .
COPY graders.py .
COPY schema.py .
COPY support_env.py .
COPY tickets.json .
COPY openenv.yaml .
COPY inference.py .

# Create server directory for compatibility
RUN mkdir -p server
RUN echo "import sys, os; sys.path.append(os.path.dirname(os.path.dirname(__file__))); from api import app" > server/app.py

EXPOSE 7860

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
