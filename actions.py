import random
import asyncio
from playwright.async_api import Page

from config import CFG
from detector import e_url_oauth
from notifier import Notifier


async def aguardar_oauth(page: Page, notifier: Notifier, timeout: int = 60) -> bool:
    """Aguarda o redirect OAuth completar e retornar ao Prenotami."""
    if not e_url_oauth(page.url):
        return True

    notifier.log("Aguardando autenticação OAuth...")

    async def liberar_oauth(route):
        await route.continue_()

    await page.route("**/pingid**", liberar_oauth)
    await page.route("**/oauth2/**", liberar_oauth)
    await page.route("**/iam.esteri.it/**", liberar_oauth)

    try:
        await page.wait_for_url("*prenotami.esteri.it*", timeout=timeout * 1000)
        notifier.log("Login OAuth concluído!")
        return True
    except Exception:
        notifier.log("Timeout aguardando OAuth — faça o login manualmente.")
        return False


async def clicar(page: Page, selector: str, timeout: int = 2000) -> bool:
    """Clica em um elemento com jitter humano. Retorna True se clicou."""
    try:
        el = page.locator(selector).first
        await el.wait_for(state="visible", timeout=timeout)
        await asyncio.sleep(random.uniform(*CFG.click_jitter))
        await el.click()
        return True
    except Exception:
        return False


async def tentar_reserva(page: Page, notifier: Notifier) -> bool:
    """
    Clica em Reservar e verifica o resultado.
    Retorna True se o calendário abriu (sucesso).
    """
    if not await clicar(page, CFG.botao_selector):
        return False

    notifier.log("Botão 'Reservar' clicado!")
    await asyncio.sleep(1)

    if await clicar(page, CFG.ok_selector):
        notifier.log("Sem vagas. Continuando...\n")
        return False

    return True  # Calendário abriu!


async def simular_mouse(page: Page) -> None:
    """Move o mouse aleatoriamente para simular comportamento humano."""
    await page.mouse.move(
        random.randint(100, 800),
        random.randint(100, 600),
    )
    await asyncio.sleep(random.uniform(0.3, 0.8))