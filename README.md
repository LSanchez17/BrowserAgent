# Browser Agent - LLM-Powered Browser Automation

A lightweight, LLM-powered browser agent now implemented as a FastAPI microservice with optional CLI helpers. The service uses Playwright for browser automation, Ollama as the local LLM backend, and Redis for task state when running asynchronously (webhooks).

## 🏗️ Current Structure

```
BrowserAgent/
├── main.py
├── run.py
├── config.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── agent/
│   ├── __init__.py
│   ├── browser_agent.py
│   ├── html_utils.py
│   ├── llm_client.py
│   ├── playwright_client.py
│   └── TODO.md
├── functions/
│   ├── base_tool.py
│   ├── tool_registry.py
│   └── tools/
│       ├── __init__.py
│       └── click_link_tool.py
├── dependencies/
│   ├── __init__.py
│   └── dependencies.py
├── routes/
│   ├── __init__.py
│   └── tasks_controller.py
├── schemas/
│   ├── __init__.py
│   └── schemas.py
├── services/
│   ├── __init__.py
│   └── task_manager.py
├── aliases/
│   ├── __init__.py
│   └── global_aliases.py
└── README.md
```

## 🎯 What It Does

1. Opens a URL with Playwright and extracts page content
2. Uses Ollama LLM to analyze/execute tasks
3. Returns structured results synchronously or via webhook (async)
4. Persists task state in Redis with a TTL for asynchronous tasks

Key notes: Pydantic v2 is used for schemas; Redis lifecycle is managed via FastAPI lifespan. Application dependencies live under the `dependencies/` package and are injected into routes with `Depends(get_redis)`. Tooling and custom tools are placed under the `functions/` package.

---

## 🚀 Deployment & Local Development

### Quick Start with Docker Compose

```bash
# Start the stack (Redis + Ollama + browser-agent)
docker-compose up -d

# Health check
curl http://localhost:8000/health

# View service logs
docker-compose logs -f browser-agent
```

### Local Development (venv)

```bash
# Create and activate venv
python -m venv venv
source venv/Scripts/activate  # Windows PowerShell: .\venv\Scripts\Activate.ps1

# Install deps
pip install -r requirements.txt
playwright install chromium

# Run the service
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 📡 API Overview

Endpoints:
- `POST /tasks` (async) — schedule a browser task; returns `task_id` immediately if `webhook_url` provided
- `GET /tasks/{task_id}` — poll task status and result
- `DELETE /tasks/{task_id}` — remove a task
- `GET /health` — service health and configuration
- `GET /docs` — OpenAPI docs (Swagger UI)

Example async request:

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "task": "Analyze the page structure",
    "webhook_url": "https://your-service.com/webhook/callback"
  }'
```

Immediate response:

```json
{
  "result": [],
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

When complete the service posts the result to the `webhook_url` you provided.

---

## 🔧 Configuration

Environment variables (config.py reads these):
- `OLLAMA_URL` (default: `http://localhost:11434`)
- `MODEL` (default LLM model)
- `HEADLESS` (browser headless mode)
- `REDIS_URL` (e.g. `redis://redis:6379/0` in docker-compose)

---

## Notes & Development Tips

- On Windows, Playwright subprocesses require special handling — this project uses a thread-pool workaround for compatibility.
