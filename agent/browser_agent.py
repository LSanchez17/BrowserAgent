"""Simple browser agent that opens a page, cleans HTML, and asks an LLM.

Delegates browser I/O to `PlaywrightClient`, HTML cleaning to
`html_utils.clean_html`, and LLM calls to `LLMClient`.
"""
from typing import Optional, Dict, Any

from .html_utils import clean_html
from .playwright_client import PlaywrightClient
from .llm_client import LLMClient


class BrowserAgent:
    """Simple browser agent that can interact with web pages."""
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        playwright_client: Optional[PlaywrightClient] = None,
    ):
        """Initialize the browser agent.
        
        Args:
            llm_client: Optional LLM client instance. If not provided, a default will be created.
            playwright_client: Optional Playwright client instance. If not provided, a default will be created
        """
        # Clients for LLM and Playwright interactions
        self.llm_client: LLMClient = llm_client if llm_client else LLMClient()
        self.playwright_client: PlaywrightClient = playwright_client if playwright_client else PlaywrightClient(headless=True)
    
    async def __aenter__(self):
        """Start browser."""
        await self.playwright_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close browser."""
        await self.playwright_client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def ask_llm(self, prompt: str, response_schema: Dict[str, Any]) -> Any:
        """Ask LLM a question.
        
        Args:
            prompt: Question for the LLM
            response_schema: Schema to request structured output from the model

        Returns:
            LLM response in structured format if response_schema is provided, otherwise raw text
        """
        try:
            return await self.llm_client.evaluate(prompt=prompt, schema=response_schema)
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return ""
    
    # For debugging and incremental development; avoid full microservice running
    async def debug_run(self, url: str) -> Dict[str, Any]:
        # Create a persistent page for interactive flows
        page = await self.playwright_client.new_page()

        try:
            await self.playwright_client.page_goto(page, url)

            # Initial fetch of page content
            page_info = await self.playwright_client.page_get_content(page)
            title = page_info.get('title')
            html = page_info.get('html')
            page_url = page_info.get('url')

            # Clean HTML preview (remove scripts, styles, common clutter)
            cleaned_html = clean_html(html)
            html_preview = cleaned_html[:8000] if cleaned_html else ""

            print(f"📄 Page Title: {title}")
            debug_task = "Click the hours of operation (or something similar) so we can then extract information"
            # Initial prompt
            base_prompt = f"You are looking at a webpage. Use the provided page content to complete the task.\nPage Title: {title}\nUser Task: {debug_task}\n"
            prompt_suffix = f"Page Content:\n{html_preview}\nAccomplish this task: {debug_task}\n"
            prompt = base_prompt + prompt_suffix

            messages = [
                {
                    "role": "system", 
                    "content": (
                        "You are a helpful autonomous browser assistant. " 
                        "Your main goal is to accomplish the user's request. "
                        "You have a list of tools you can use to interact with the page and extract information. "
                        "Use them wisely to complete the task. You are primarily using playwright"
                    ),
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]

            # Naive, find a more robust pattern
            max_iterations = 5

            for _ in range(max_iterations):
                print(f"\n💬 Looping and Sending messages to LLM: ")
                resp = await self.llm_client.chat(messages=messages)
                tool_calls = getattr(resp.message, 'tool_calls', [])

                if not tool_calls:
                    print(f"\n💬 Final LLM Response:\n{resp}")

                    await self.playwright_client.close_page(page)

                    # We want to adapt this to match the original expected return as well
                    return {
                        "response": resp,
                        "messages": messages,
                    }
                
                for call in tool_calls:
                    tool_name, tool_response = await self.llm_client.execute_tool_call(call, page)

                    # Append the tool response to the messages for the next LLM turn
                    messages.append({"role": "tool", "name": tool_name, "content": str(tool_response)})

            await self.playwright_client.close_page(page)

            return {
                "error": f"Max iterations ({max_iterations}) reached before completion",
                "messages": messages,
                "initial_url": url,
                "url": page_url,
                "title": title,
                "description": debug_task,
            }
        finally:
            await self.playwright_client.close_page(page)
    
    async def execute_task(self, url: str, task: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task on a webpage.
        
        Args:
            url: URL to visit
            task: Description of what to do on the page
            response_schema: Schema to request structured output from the model
        Returns:
            Dict with task results, URL, title, and execution details
        """
        # Grab the page content through playwright
        page_info = await self.playwright_client.get_page_content(url)
        title = page_info.get('title')
        html = page_info.get('html')
        page_url = page_info.get('url')

        # Clean HTML preview (remove scripts, styles, common clutter)
        cleaned_html = clean_html(html)
        html_preview = cleaned_html[:8000] if cleaned_html else ""
        
        print(f"📄 Page Title: {title}")
        
        prompt = f"""You are a browser automation assistant. A user wants you to perform a task on a webpage.
                    Page Title: {title}
                    URL: {url}
                    Page Content:
                    {html_preview}
                    User's Task: {task}
                    Use the page content to complete the task."""

        result = await self.ask_llm(prompt, response_schema=response_schema)
        
        return {
            'initial_url': url,
            'url': page_url,
            'title': title,
            'task': task,
            'result': result,
            'html_preview': html_preview[:500],
            'status': 'completed'
        }
