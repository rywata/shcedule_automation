import os
import asyncio
from typing import Tuple
from playwright.async_api import BrowserContext, Page
from playwright_stealth import Stealth

FIREFOX_PROFILE = os.path.expanduser("~/firefox-novo-profile")


async def criar_contexto(p) -> Tuple[BrowserContext, Page]:
    os.makedirs(FIREFOX_PROFILE, exist_ok=True)

    context = await p.firefox.launch_persistent_context(
        user_data_dir=FIREFOX_PROFILE,
        headless=False,
        locale="it-IT",
        timezone_id="Europe/Rome",
        viewport={"width": 1440, "height": 900},
        firefox_user_prefs={
            "toolkit.telemetry.enabled": False,
            "datareporting.healthreport.uploadEnabled": False,
            "browser.startup.page": 0,
            "browser.startup.homepage": "about:blank",
        },
    )

    await asyncio.sleep(2)
    page = context.pages[0] if context.pages else await context.new_page()
    await Stealth().apply_stealth_async(page)

    return context, page