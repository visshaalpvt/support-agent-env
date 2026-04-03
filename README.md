# SupportAgentEnv

OpenEnv environment for training AI agents on customer support tasks.

## Tasks
- **Easy**: Ticket classification (5 categories)
- **Medium**: Classification + Priority detection  
- **Hard**: Classification + Priority + Empathetic response

## API Endpoints
- `POST /reset` - Start new episode
- `POST /step` - Submit action, get reward (0.0-1.0)
- `GET /state` - Get current state
- `GET /health` - Health check

## Deployment
```bash
docker build -t support-agent-env .
docker run -p 7860:7860 support-agent-env
```

## Live Demo
https://huggingface.co/spaces/visshaalpvt/support-agent-env
