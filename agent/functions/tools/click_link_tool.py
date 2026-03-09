from typing import Any, Dict
from ..base_tool import BaseTool

# TODO: Maybe fold into a singular playwright_tool.py that just calls methods in the Playwright client, thereby having access to the page object?
class PageClickTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="page_click", 
            description="Tool used to click elements on a webpage using a playwright selector. Useful for navigation and interaction."
        )

    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "requires_page": {
                    "type": "boolean",
                    "description": "Indicates whether the tool requires a Playwright page object to interact with. This will be passed by the agent when executing the tool.",
                    "default": True
                },
                "selector": {
                    "type": "string",
                    "description": "A CSS selector string to identify the element to click on the page. Prefer using unique identifiers like IDs or specific class names to avoid ambiguity. Example: '#submit-button' or '.nav-link'."
                },
            },
            "required": ["selector", "requires_page"]
        }

    async def execute(self, page, selector: str, requires_page: bool) -> Dict[str, Any]:
        """Simulate a click on the page using the provided selector.

        ### Args:
            page: The Playwright page object to interact with.
            selector: A CSS selector string to identify the element to click.

        ### Returns:
            A dictionary with the result of the click action, including any new URL or page title.
        """
        try:
            print(f"\n🔍 Attempting to click element with selector: {selector}")
            await page.click(selector)
            await page.wait_for_load_state('networkidle')
            new_url = page.url
            new_title = await page.title()
            print(f"✅ Click successful. New URL: {new_url}, New Title: {new_title}")
            # TODO: this response should be somewhat standardized, investigate
            return {"success": True, "url": new_url, "title": new_title}
        except Exception as e:
            print(f"❌ Click failed: {e}")
            return {"success": False, "error": str(e)}