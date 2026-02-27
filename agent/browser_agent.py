"""
Simple browser agent that opens a URL and describes what it sees using Ollama.
"""
import asyncio
import ollama

from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Page, Browser


class BrowserAgent:
    """Simple browser agent that describes web pages."""
    
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
    
    async def ask_llm(self, prompt: str) -> str:
        """Ask LLM a question.
        
        Args:
            prompt: Question for the LLM
            
        Returns:
            LLM response
        """
        print(f"\n🧠 Asking LLM...")
        try:
            response = await self.client.generate(
                model=self.model,
                prompt=prompt,
                stream=False
            )
            answer = response['response'].strip()
            return answer
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return ""
    
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
        await asyncio.sleep(1)
        
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

        description = await self.ask_llm(prompt)
        
        print(f"\n💭 LLM Description:")
        print(f"   {description}")
        
        return {
            'url': self.page.url,
            'title': title,
            'description': description,
            'text_preview': text_preview[:500]
        }
    
    async def execute_task(self, url: str, task: str) -> Dict[str, Any]:
        """Execute a task on a webpage.
        
        Args:
            url: URL to visit
            task: Description of what to do on the page
            
        Returns:
            Dict with task results, URL, title, and execution details
        """
        print(f"\n🌐 Opening: {url}")
        print(f"📋 Task: {task}")
        
        # Navigate to URL
        await self.page.goto(url, timeout=30000)
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)
        
        # Get page info
        title = await self.page.title()
        text = await self.page.evaluate('() => document.body.innerText')
        text_preview = text[:2000] if text else ""
        
        print(f"📄 Page Title: {title}")
        
        # Ask LLM to execute the task
        prompt = f"""You are a browser automation assistant. A user wants you to perform a task on a webpage.

Page Title: {title}
URL: {url}

Page Content:
{text_preview}

User's Task: {task}

Based on the page content above, provide:
1. What you observe on the page that's relevant to the task
2. What actions would be needed to complete this task
3. Any data or results from analyzing the page content

Respond in a clear, structured way."""

        result = await self.ask_llm(prompt)
        
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
