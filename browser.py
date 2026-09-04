import os
import asyncio
from typing import Tuple
from playwright.async_api import BrowserContext, Page
from playwright_stealth import Stealth

CHROME_PROFILE = os.path.expanduser("~/chrome-prenotami-profile")


async def criar_contexto(p) -> Tuple[BrowserContext, Page]:
    os.makedirs(CHROME_PROFILE, exist_ok=True)

    context = await p.chromium.launch_persistent_context(
        user_data_dir=CHROME_PROFILE,
        headless=False,
        channel="chrome",
        locale="it-IT",
        timezone_id="Europe/Rome",
        viewport={"width": 1440, "height": 900},
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
    )

    await asyncio.sleep(2)
    page = context.pages[0] if context.pages else await context.new_page()
    await Stealth().apply_stealth_async(page)

    return context, page