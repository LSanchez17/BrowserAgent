"""Async Playwright client wrapper.

Provides a small async-first helper to start Playwright, launch a browser,
and fetch rendered page content.
"""
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Browser


class PlaywrightClient:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def get_page_content(self, url: str, wait_selectors: Optional[List[str]] = None, timeout: int = 30000) -> Dict[str, Any]:
        """Navigate to `url`, wait for network idle and optional selectors,
        and return a dict with `url`, `title`, and `html`.
        """
        page = await self.browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        print(f"\n🌐 Opening: {url}")
        await page.goto(url, timeout=timeout)
        await page.wait_for_load_state("networkidle", timeout=timeout)

        # When the page may contain specific objects of interest, we wait for them
        if wait_selectors:
            for sel in wait_selectors:
                try:
                    await page.wait_for_selector(sel, timeout=timeout)
                except Exception:
                    # ignore selector timeouts and continue
                    pass
    
        title = await page.title()
        html = await page.content()
        await page.close()
        print(f"\n✅ Closing browser, found: {title}")
        return {"url": page.url, "title": title, "html": html}
    # TODO: Can we use this as a tool execution call? Maybe have a playwright tool that has arguments deciding which method to call, hmm
    async def new_page(self):
        """Create and return a new Playwright Page with sane defaults."""
        page = await self.browser.new_page()
        await page.set_viewport_size({"width": 1920, "height": 1080})
        return page

    async def close_page(self, page) -> None:
        try:
            await page.close()
        except Exception:
            pass

    async def page_goto(self, page, url: str, timeout: int = 30000) -> None:
        await page.goto(url, timeout=timeout)
        await page.wait_for_load_state("networkidle", timeout=timeout)

    async def page_get_content(self, page) -> Dict[str, Any]:
        title = await page.title()
        html = await page.content()
        return {"url": page.url, "title": title, "html": html}

    async def page_click(self, page, selector: str, timeout: int = 10000) -> Dict[str, Any]:
        try:
            await page.click(selector, timeout=timeout)
            await page.wait_for_load_state("networkidle", timeout=timeout)
            return {"status": "ok", "action": "click", "selector": selector}
        except Exception as e:
            return {"status": "error", "action": "click", "selector": selector, "error": str(e)}

    async def page_fill(self, page, selector: str, value: str, timeout: int = 10000) -> Dict[str, Any]:
        try:
            await page.fill(selector, value, timeout=timeout)
            return {"status": "ok", "action": "fill", "selector": selector}
        except Exception as e:
            return {"status": "error", "action": "fill", "selector": selector, "error": str(e)}

    async def page_query(self, page, selector: str) -> Dict[str, Any]:
        try:
            handle = await page.query_selector(selector)
            if not handle:
                return {"found": False, "selector": selector}
            text = await handle.inner_text()
            return {"found": True, "selector": selector, "text": text}
        except Exception as e:
            return {"found": False, "selector": selector, "error": str(e)}

    async def page_wait_for_selector(self, page, selector: str, timeout: int = 10000) -> Dict[str, Any]:
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return {"status": "ok", "selector": selector}
        except Exception as e:
            return {"status": "error", "selector": selector, "error": str(e)}
