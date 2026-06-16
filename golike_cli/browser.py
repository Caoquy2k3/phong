from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page


@asynccontextmanager
async def launch_browser(headless: bool = True, slow_mo_ms: int = 0, user_agent: Optional[str] = None,
                         viewport_width: int = 1280, viewport_height: int = 800, timeout_ms: int = 30000,
                         storage_state: Optional[Path] = None) -> AsyncIterator[tuple[Browser, BrowserContext, Page]]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, slow_mo=slow_mo_ms)
        context_kwargs = {
            "viewport": {"width": viewport_width, "height": viewport_height},
        }
        if user_agent:
            context_kwargs["user_agent"] = user_agent
        if storage_state and Path(storage_state).exists():
            context_kwargs["storage_state"] = str(storage_state)
        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()
        page.set_default_timeout(timeout_ms)
        try:
            yield browser, context, page
        finally:
            await context.close()
            await browser.close()
