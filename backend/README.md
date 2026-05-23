# AI Backend Playground

FastAPI backend for AI workflows, structured analysis, chat, and safe tool execution.

## Requirements

- Python 3.11+
- OpenAI-compatible API key for `/analyze`, `/form-assistant`, and `/chat`

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set `OPENAI_API_KEY`. If you use an OpenAI-compatible provider, also set `OPENAI_BASE_URL`.

The service also accepts the existing frontend variable names as fallbacks:

- `AI_API_KEY`
- `BASE_URL`

## Run

```bash
uvicorn app.main:app --reload
```

Open API docs at:

```txt
http://localhost:8000/docs
```

Health check:

```bash
curl http://localhost:8000/health
```

## Endpoints

- `GET /health`
- `POST /analyze`
- `POST /form-assistant`
- `POST /chat`
- `POST /tools/execute`

## Test

```bash
pytest tests
```
