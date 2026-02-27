# Browser Agent - LLM-Powered Browser Automation

A minimal LLM-powered browser agent that can be used as a CLI tool or deployed as a microservice.

## 🏗️ Structure

```
BrowserAgent/
├── run.py                    # CLI entry point
├── service.py                # FastAPI microservice
├── agents/
│   └── browser_agent.py      # Browser agent core
├── requirements.txt          # Dependencies
├── Dockerfile                # Container image
└── docker-compose.yml        # Multi-container setup
```

## 🎯 What It Does

1. Opens a URL with Playwright
2. Extracts page title and text content
3. Uses local Ollama LLM to analyze and execute tasks
4. Returns structured results

Available as both a CLI tool and a microservice with async webhook support.

---

## 🚀 Microservice Deployment

### Quick Start with Docker Compose

```bash
# Start the service (includes Ollama)
docker-compose up -d

# Check status
curl http://localhost:8000/health

# View logs
docker-compose logs -f browser-agent
```

### Manual Docker Build

```bash
# Build image
docker build -t browser-agent-service .

# Run container
docker run -d -p 8000:8000 \
  -e OLLAMA_URL=http://localhost:11434 \
  browser-agent-service
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run the service
python service.py

# Or with uvicorn
uvicorn service:app --reload --host 0.0.0.0 --port 8000
```

---

## 📡 API Usage

### Endpoint: `POST /browser_agent`

**Synchronous Mode** (immediate response):
```bash
curl -X POST http://localhost:8000/browser_agent \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "task": "Find the main heading and describe the page"
  }'
```

Response:
```json
{
  "result": [
    {
      "url": "https://example.com",
      "title": "Example Domain",
      "task": "Find the main heading and describe the page",
      "result": "The main heading is 'Example Domain'. This is a simple demonstration page...",
      "status": "completed"
    }
  ],
  "status": "completed"
}
```

**Asynchronous Mode** (webhook callback):
```bash
curl -X POST http://localhost:8000/browser_agent \
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

When complete, POSTs to your webhook:
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": [{ ... }]
}
```

### Check Task Status

```bash
curl http://localhost:8000/task/550e8400-e29b-41d4-a716-446655440000
```

### Interactive API Documentation

Visit http://localhost:8000/docs for Swagger UI

---

## 💻 CLI Usage

```bash
# Watch the browser work (not headless)
python run.py --url "https://golfnow.com"

# Run invisibly  
python run.py --url "https://golfnow.com" --headless

# Save results to JSON
python run.py --url "https://example.com" --output results.json
```

## 🔧 Configuration

Environment variables:
- `OLLAMA_URL`: Ollama API endpoint (default: `http://localhost:11434`)
- `MODEL`: LLM model to use (default: `qwen3:8b`)
- `HEADLESS`: Run browser headlessly (default: `True`)
---

## 📋 Example Output

```
🤖 BROWSER AGENT - Describe What You See
======================================================================

🌐 Opening: https://golfnow.com
📄 Page Title: GolfNow - Book Tee Times
📝 Content Preview: GolfNow helps you find and book tee times...

🧠 Asking LLM...

💭 LLM Description:
   This is a golf course booking website. The main sections 
   include a search box to find courses, featured courses,
   and tee time availability. Users can search for courses,
   view prices, and book tee times directly.

======================================================================
📊 RESULTS
======================================================================
URL: https://golfnow.com
Title: GolfNow - Book Tee Times

Description:
This is a golf course booking website...

✅ Done!
```

## Roadmap

- ✅ Open URL and describe (DONE)
- ⬜ Find specific elements
- ⬜ Click links
- ⬜ Fill forms
- ⬜ Extract data
- ⬜ Multi-step navigation
