---
title: SupportAgentEnv
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_file: api.py
---

# SupportAgentEnv

OpenEnv environment for training AI agents on customer support tasks.

## Overview

SupportAgentEnv is a customer support automation training environment where AI agents learn to:
- Classify customer tickets into 5 categories
- Detect priority levels (low, medium, high, urgent)
- Write empathetic, helpful responses

## Tasks

| Difficulty | What Agent Must Do | Grading Weight |
|------------|-------------------|----------------|
| **Easy** | Classify ticket category | Category (100%) |
| **Medium** | Classify + Detect priority | Category (50%) + Priority (50%) |
| **Hard** | Classify + Priority + Write response | Category (30%) + Priority (30%) + Response (40%) |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/reset` | POST | Start new episode |
| `/step` | POST | Submit action, get reward |
| `/state` | GET | Get current state |
| `/docs` | GET | Swagger API documentation |

## Live Demo

Visit the root URL for the interactive dashboard: https://visshaalpvt-support-agent-env.hf.space

## Deployment

### Local Deployment
```bash
docker build -t support-agent-env .
docker run -p 7860:7860 support-agent-env
```

### Hugging Face Spaces
This Space is automatically deployed from GitHub. Push to the main branch to trigger a new build.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `API_BASE_URL` | LLM API endpoint (provided by judges) |
| `HF_TOKEN` | Hugging Face token (provided by judges) |
| `MODEL_NAME` | Model name for inference |
| `SPACE_URL` | This Space URL |

## Testing

Run the baseline inference script:
```bash
pip install -r requirements.txt
python inference.py
```

## License

MIT
