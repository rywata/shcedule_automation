import os
from playwright.async_api import async_playwright, BrowserContext
from playwright_stealth import Stealth

from config import CFG


async def criar_contexto(p) -> BrowserContext:
    """Inicia o Firefox com perfil persistente e stealth ativado."""
    os.makedirs(CFG.firefox_profile, exist_ok=True)

    context = await p.firefox.launch_persistent_context(
        user_data_dir=CFG.firefox_profile,
        headless=False,
        locale="it-IT",
        timezone_id="Europe/Rome",
        viewport={"width": 1440, "height": 900},
    )

    # Aplica stealth na primeira página (ou cria uma nova)
    page = context.pages[0] if context.pages else await context.new_page()
    await Stealth().apply_stealth_async(page)

    return context