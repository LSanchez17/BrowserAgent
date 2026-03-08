"""
Simple browser agent that opens a URL and interacts with it using a combination of Ollama and Playwright.
"""
import asyncio
import ollama
import json

from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser


class BrowserAgent:
    """Simple browser agent that can interact with web pages."""
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "qwen3:8b",
        headless: bool = True
    ):
        """Initialize the browser agent.
        
        Args:
            ollama_url: URL of Ollama API
            model: Model name to use
            headless: Whether to run browser in headless mode
        """
        self.ollama_url = ollama_url
        self.model = model
        self.headless = headless
        self.client = ollama.AsyncClient(host=ollama_url)
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def __aenter__(self):
        """Start browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        await self.page.set_viewport_size({"width": 1920, "height": 1080})
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close browser."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
    
    async def ask_llm(self, prompt: str, response_schema: Dict[str, Any]) -> Any:
        """Ask LLM a question.
        
        Args:
            prompt: Question for the LLM
            response_schema: Optional schema to request structured output from the model

        Returns:
            LLM response in structured format if response_schema is provided, otherwise raw text
        """
        print(f"\n🧠 Asking LLM...")
        try:
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=False,
                format=response_schema,
            )
            answer = response.get('response')

            return json.loads(answer)
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return ""
    
    # This runs only during the manual run.py. Used for quick testing and debugging of the agent's capabilities.
    async def describe_page(self, url: str) -> Dict[str, Any]:
        """Open a URL and describe what's on the page.
        
        Args:
            url: URL to visit
            
        Returns:
            Dict with URL, title, description, and text preview
        """
        print(f"\n🌐 Opening: {url}")
        
        # Navigate to URL
        await self.page.goto(url, timeout=30000)
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(5)
        
        # Get page info
        title = await self.page.title()
        text = await self.page.evaluate('() => document.body.innerText')
        text_preview = text[:2000] if text else ""
        
        print(f"📄 Page Title: {title}")
        print(f"📝 Content Preview: {text_preview[:200]}...")
        
        # Ask LLM to describe what it sees
        prompt = f"""You are looking at a webpage. Describe what you see in a clear, concise way.

            Page Title: {title}

            Page Content:
            {text_preview}

            Describe this page in 2-3 sentences. Focus on:
            1. What type of website/page is this?
            2. What are the main elements or sections?
            3. What actions can a user take here?
        """
        debug_schema = {
            "type": "object",
            "properties": {
                "description": {"type": "string"}
            },
            "required": ["description"]
        }
        
        description = await self.ask_llm(prompt, response_schema=debug_schema)
        
        print(f"\n💭 LLM Description:")
        print(f"   {description}")
        
        return {
            'url': self.page.url,
            'title': title,
            'description': description,
            'text_preview': text_preview[:500]
        }
    
    async def execute_task(self, url: str, task: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task on a webpage.
        
        Args:
            url: URL to visit
            task: Description of what to do on the page
            
        Returns:
            Dict with task results, URL, title, and execution details
        """
        print(f"\n🌐 Opening: {url}")
        # Get page info - Mainly for debugging purposes
        
        # Navigate to URL
        await self.page.goto(url, timeout=30000)
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(3)
        
        # Get page info-Mainly for debugging purposes
        title = await self.page.title()
        text = await self.page.evaluate('() => document.body.innerText')
        text_preview = text[:2000] if text else ""
        
        print(f"📄 Page Title: {title}")
        
        # Simple prompt to task the LLM to accomplish a task. Response schema is passed to ensure structured output that can be easily parsed and used by other systems.
        prompt = f"""You are a browser automation assistant. A user wants you to perform a task on a webpage.
                    Page Title: {title}
                    URL: {url}
                    Page Content:
                    {text_preview}
                    User's Task: {task}
                    Use the page content to complete the task."""

        result = await self.ask_llm(prompt, response_schema=response_schema)
        
        print(f"\n💭 Task Result:")
        print(f"   {result}")
        
        return {
            'url': self.page.url,
            'title': title,
            'task': task,
            'result': result,
            'text_preview': text_preview[:500],
            'status': 'completed'
        }
