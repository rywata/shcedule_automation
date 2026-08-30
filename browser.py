import os
import asyncio
from typing import Tuple
from playwright.async_api import BrowserContext, Page
from playwright_stealth import Stealth

from config import CFG

FIREFOX_PROFILE = os.path.expanduser("~/firefox-prenotami-profile")


async def criar_contexto(p) -> Tuple[BrowserContext, Page]:
    os.makedirs(FIREFOX_PROFILE, exist_ok=True)

    context = await p.firefox.launch_persistent_context(
        user_data_dir=FIREFOX_PROFILE,
        headless=False,
        locale="it-IT",
        timezone_id="Europe/Rome",
        viewport={"width": 1440, "height": 900},
        executable_path="/Applications/Firefox.app/Contents/MacOS/firefox",
        firefox_user_prefs={
            "toolkit.telemetry.enabled": False,
            "datareporting.healthreport.uploadEnabled": False,
            "browser.safebrowsing.enabled": False,
            # Abre sempre em branco para o script controlar a navegação
            "browser.startup.page": 0,
            "browser.startup.homepage": "about:blank",
            "general.useragent.override": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:138.0) "
                "Gecko/20100101 Firefox/138.0"
            ),
        },
    )

    await asyncio.sleep(2)

    page = context.pages[0] if context.pages else await context.new_page()
    await Stealth().apply_stealth_async(page)

    return context, page