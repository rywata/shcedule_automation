import asyncio
from playwright.async_api import async_playwright

from config import CFG, Resultado
from browser import criar_contexto
from monitor import Monitor
from notifier import Notifier


async def main() -> None:
    notifier = Notifier()

    async with async_playwright() as p:
        context, page = await criar_contexto(p)

        await asyncio.sleep(3)
        await page.goto(CFG.url_home, wait_until="domcontentloaded", timeout=60000)

        notifier.conectado()
        notifier.aguardar_login(CFG.login_wait)

        # ── Loop externo: reinicia após re-verificação ────────────────
        while True:
            monitor   = Monitor(page, notifier)
            resultado = await monitor.rodar()

            if resultado == Resultado.SUCESSO:
                notifier.info(">>> RESERVA CONCLUÍDA!")
                break

            if resultado == Resultado.REVERIFICACAO:
                if notifier.perguntar_reinicio():
                    notifier.info("\n>>> Reiniciando monitoramento...\n")
                    notifier.aguardar_login(CFG.login_wait)
                else:
                    notifier.info("\n>>> Encerrando por escolha do usuário.")
                    break

            if resultado == Resultado.ENCERRADO:
                notifier.info("\nEncerrado pelo usuário.")
                break

        await context.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEncerrado pelo usuário.")