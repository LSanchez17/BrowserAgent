# Browser Agent - Simple Start

A minimal LLM-powered browser agent that opens a URL and describes what it sees.

## Structure

```
BrowserAgent/
├── run.py                    # Entry point
├── agents/
│   └── browser_agent.py      # Browser agent 
└── requirements.txt          # Dependencies
```

## What It Does

1. Opens a URL with Playwright
2. Extracts page title and text content
3. Asks local Ollama to describe the page
4. Prints the description

A foundation to build on.

## Usage

```bash
# Watch the browser work (not headless)
python run.py --url "https://golfnow.com"

# Run invisibly  
python run.py --url "https://golfnow.com" --headless

# Save results to JSON
python run.py --url "https://example.com" --output results.json
```

## Example Output

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
