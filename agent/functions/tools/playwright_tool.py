from typing import Any, Dict, Optional
from ..base_tool import BaseTool


class PlaywrightTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="playwright",
            description=(
                "Unified Playwright tool allowing the LLM to specify an `action` "
                "(goto, click, fill, query, get_content, wait_for_selector) "
                "and action-specific arguments."
            ),
        )

    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Playwright action to perform.",
                    "enum": [
                        "goto",
                        "click",
                        "fill",
                        "query",
                        "get_content",
                        "wait_for_selector",
                    ],
                },
                "requires_page": {
                    "type": "boolean",
                    "description": "Whether a Playwright Page object is required.",
                    "default": True,
                },
                "selector": {"type": "string", "description": "CSS selector for element actions."},
                "url": {"type": "string", "description": "URL for navigation actions."},
                "value": {"type": "string", "description": "Value for form fill actions."},
                "timeout": {"type": "integer", "description": "Timeout in ms.", "default": 10000},
            },
            "required": ["action"],
        }

    async def execute(self, page: Optional[Any] = None, action: str = None, selector: Optional[str] = None,
                      url: Optional[str] = None, value: Optional[str] = None, timeout: int = 10000) -> Dict[str, Any]:
        try:
            if action == "goto":
                await page.goto(url, timeout=timeout)
                await page.wait_for_load_state("networkidle", timeout=timeout)
                return {"success": True, "action": "goto", "url": page.url}

            if action == "click":
                await page.click(selector, timeout=timeout)
                await page.wait_for_load_state("networkidle", timeout=timeout)
                title = await page.title()
                return {"success": True, "action": "click", "url": page.url, "title": title}

            if action == "fill":
                await page.fill(selector, value, timeout=timeout)
                return {"success": True, "action": "fill", "selector": selector}

            if action == "query":
                handle = await page.query_selector(selector)
                if not handle:
                    return {"success": True, "found": False, "selector": selector}
                text = await handle.inner_text()
                return {"success": True, "found": True, "selector": selector, "text": text}

            if action == "get_content":
                title = await page.title()
                html = await page.content()
                return {"success": True, "action": "get_content", "url": page.url, "title": title, "html": html}

            if action == "wait_for_selector":
                await page.wait_for_selector(selector, timeout=timeout)
                return {"success": True, "action": "wait_for_selector", "selector": selector}

            return {"success": False, "error": f"Unsupported action: {action}"}

        except Exception as e:
            return {"success": False, "error": str(e)}
