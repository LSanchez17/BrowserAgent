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
