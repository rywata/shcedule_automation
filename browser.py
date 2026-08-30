import os
from typing import Tuple
from playwright.async_api import BrowserContext, Page
from playwright_stealth import Stealth

from config import CFG


async def criar_contexto(p) -> Tuple[BrowserContext, Page]:
    """
    Inicia o Firefox com perfil persistente e stealth ativado.
    Retorna o contexto E a página já com stealth aplicado.
    """
    os.makedirs(CFG.firefox_profile, exist_ok=True)

    context = await p.firefox.launch_persistent_context(
        user_data_dir=CFG.firefox_profile,
        headless=False,
        locale="it-IT",
        timezone_id="Europe/Rome",
        viewport={"width": 1440, "height": 900},
    )

    page = context.pages[0] if context.pages else await context.new_page()
    await Stealth().apply_stealth_async(page)

    return context, page