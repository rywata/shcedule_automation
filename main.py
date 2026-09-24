import asyncio
from playwright.async_api import async_playwright

from config import CFG, Resultado
from browser import criar_contexto
from monitor import Monitor
from notifier import Notifier

def menu_pos_parada(motivo: str) -> str:
    """
    Exibe menu após qualquer parada.
    Retorna: 'retomar', 'encerrar'
    """
    print(f"\n{'─' * 45}")
    print(f"  Automação pausada — {motivo}")
    print(f"{'─' * 45}")
    print("  [1] Retomar monitoramento")
    print("  [2] Encerrar e fechar navegador")
    print(f"{'─' * 45}")
    while True:
        escolha = input("  Escolha (1 ou 2): ").strip()
        if escolha == "1":
            return "retomar"
        if escolha == "2":
            return "encerrar"
        print(" Digite 1 ou 2.")


async def main() -> None:
    notifier = Notifier()

    async with async_playwright() as p:
        context, page = await criar_contexto(p)

        await asyncio.sleep(3)
        await page.goto(CFG.url_home, wait_until="domcontentloaded", timeout=60000)

        notifier.conectado()
        await notifier.aguardar_login(CFG.login_wait)

        # ── Loop externo: reinicia após re-verificação ────────────────
        while True:
            monitor   = Monitor(page, notifier)
            resultado = await monitor.rodar()

            if resultado == Resultado.SUCESSO:
                notifier.info(">>> RESERVA CONCLUÍDA!")
                acao = menu_pos_parada("reserva concluída")

            elif resultado == Resultado.REVERIFICACAO:
                notifier.perguntar_reinicio() 
                acao = menu_pos_parada("re-verificação necessária")

            elif resultado == Resultado.ENCERRADO:
                acao = menu_pos_parada("encerrado pelo usuário")

            else:
                break

            if acao == "retomar":
                notifier.info("\n>>> Retomando monitoramento...\n")
                await notifier.aguardar_login(CFG.login_wait)
            else:
                notifier.info("\n>>> Encerrando...")
                break

        try:
            await context.close()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEncerrado pelo usuário.")