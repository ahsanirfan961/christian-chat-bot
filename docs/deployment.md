# Deployment Guide

## 1. Requirements

- Python 3.13+
- `uv` package manager
- OpenRouter API key
- API.Bible API key

## 2. Setup

```bash
uv sync
cp .env.example .env
# fill in API keys
```

## 3. Local Run

```bash
uv run uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000`.

## 4. Environment Variables

- `OPENROUTER_API_KEY`
- `API_BIBLE_KEY`
- `DEFAULT_BIBLE_ID`

## 5. Production Considerations

- Run behind HTTPS reverse proxy
- Set secure cookie flags for production deployment
- Add request timeouts/retries and external API monitoring
- Persist checkpoints on durable storage
- Implement API key secret management via vault or platform secrets
