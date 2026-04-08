FROM python:3.9-slim

WORKDIR /app

# Minimal requirements - only what's absolutely necessary
RUN pip install fastapi uvicorn pydantic python-multipart

# Copy only essential files
COPY api.py .
COPY support_env.py .
COPY graders.py .
COPY schema.py .
COPY tickets.json .
COPY openenv.yaml .
COPY templates ./templates

# Create server directory
RUN mkdir -p server
RUN echo "import sys, os; sys.path.append(os.path.dirname(os.path.dirname(__file__))); from api import app" > server/app.py

EXPOSE 7860

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "7860"]
