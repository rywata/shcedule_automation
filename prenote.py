import os
import sys
import time
import random
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# ─── CONFIGURAÇÕES ────────────────────────────────────────────────────────────
URL_HOME     = "https://prenotami.esteri.it/"
LOGIN_WAIT   = 60
REFRESH_MIN  = 3.0
REFRESH_MAX  = 6.0
CLICK_JITTER = (0.5, 1.5)

BOTAO_SELECTOR = "button:has-text('Reservar')"
OK_SELECTOR    = "button:has-text('ok')"

# Textos que indicam que o site pediu re-verificação/login
TRIGGERS_REVERIFICACAO = [
    "session expired",
    "sessione scaduta",
    "login",
    "accedi",
    "verifica",
    "captcha",
    "pingid",
    "autenticazione",
]
# ──────────────────────────────────────────────────────────────────────────────


def aguardar_login(segundos: int = LOGIN_WAIT) -> None:
    for i in range(segundos, 0, -1):
        print(f"    Robô assume o controle em: {i:02d}s ", end="\r")
        time.sleep(1)
    print("\n\n>>> MONITORAMENTO ATIVADO!\n")


def notificar_sucesso() -> None:
    print("\n" + "=" * 55)
    print("!!!  CALENDÁRIO ABERTO — ASSUMA O CONTROLE AGORA!  !!!")
    print("=" * 55 + "\n")
    if sys.platform == "darwin":
        os.system('say "Sucesso! Verifique o navegador agora!"')


def perguntar_reinicio() -> bool:
    """Pergunta ao usuário se quer reiniciar após re-verificação. Retorna True para continuar."""
    print("\n" + "⚠️  " * 15)
    print("ATENÇÃO: O site pediu uma nova verificação!")
    print("Faça a verificação manualmente no navegador.")
    print("⚠️  " * 15)
    if sys.platform == "darwin":
        os.system('say "Atenção! O site pediu uma nova verificação!"')

    while True:
        resposta = input("\nApós completar a verificação, deseja reiniciar o monitoramento? (s/n): ").strip().lower()
        if resposta == "s":
            return True
        elif resposta == "n":
            return False
        print("Digite 's' para sim ou 'n' para não.")


def detectar_reverificacao(url: str, conteudo: str) -> bool:
    """Retorna True se o site está pedindo re-verificação."""
    url_lower = url.lower()
    conteudo_lower = conteudo.lower()
    return any(
        trigger in url_lower or trigger in conteudo_lower
        for trigger in TRIGGERS_REVERIFICACAO
    )


async def tentar_reserva(page) -> bool:
    try:
        botao = page.locator(BOTAO_SELECTOR).first
        await botao.wait_for(state="visible", timeout=2000)
        await asyncio.sleep(random.uniform(*CLICK_JITTER))
        await botao.click()
        print(f"[{time.strftime('%H:%M:%S')}] Botão 'Reservar' clicado!")

        await asyncio.sleep(1)
        try:
            ok = page.locator(OK_SELECTOR).first
            await ok.wait_for(state="visible", timeout=2000)
            await asyncio.sleep(random.uniform(*CLICK_JITTER))
            await ok.click()
            print(f"[{time.strftime('%H:%M:%S')}] Sem vagas. Continuando...\n")
            return False
        except Exception:
            pass

        return True

    except Exception:
        return False


async def loop_monitoramento(page) -> str:
    """
    Roda o loop de monitoramento.
    Retorna:
      - 'sucesso'       → vaga encontrada
      - 'reverificacao' → site pediu nova verificação
      - 'encerrado'     → usuário encerrou com Ctrl+C
    """
    tentativas = 0
    espera_erro = 10

    while True:
        try:
            tentativas += 1
            url_atual = page.url
            conteudo  = await page.content()

            # ── Bloqueio Radware ──────────────────────────────────────
            if "Error.cshtml" in url_atual or "perfdrive" in url_atual:
                print(f"[{time.strftime('%H:%M:%S')}] Bloqueio Radware — aguardando 15s...")
                await asyncio.sleep(15)
                await page.goto(URL_HOME)
                continue

            # ── Servidor sobrecarregado (HTTP 500) ────────────────────
            if ("HTTP ERROR 500" in conteudo
                or "não consegue atender" in conteudo
                or "Si è verificato un errore" in conteudo
                or "elaborazione della richiesta" in conteudo
            ):
                print(f"[{time.strftime('%H:%M:%S')}] Servidor 500 — aguardando {espera_erro}s...")
                await asyncio.sleep(espera_erro)
                espera_erro = min(espera_erro + 5, 60)
                await page.goto(URL_HOME)
                continue

            # ── Re-verificação pedida pelo site ───────────────────────
            if detectar_reverificacao(url_atual, conteudo):
                print(f"[{time.strftime('%H:%M:%S')}] Re-verificação detectada na URL: {url_atual}")
                return "reverificacao"

            # ── Tudo normal: tenta reservar ───────────────────────────
            espera_erro = 10
            sucesso = await tentar_reserva(page)
            if sucesso:
                notificar_sucesso()
                return "sucesso"

            espera = random.uniform(REFRESH_MIN, REFRESH_MAX)
            print(f"[{time.strftime('%H:%M:%S')}] Tentativa #{tentativas} — "
                  f"próxima em {espera:.1f}s...", end="\r")
            await asyncio.sleep(espera)
            await page.reload()

        except KeyboardInterrupt:
            return "encerrado"
        except Exception as e:
            print(f"\n[{time.strftime('%H:%M:%S')}] Erro: {e}")
            await asyncio.sleep(5)
            try:
                await page.goto(URL_HOME)
            except Exception:
                pass


async def main():
    # Profile Chrome
    # profile_path = os.path.expanduser("~/chrome-prenotami-profile")

    # Profile Firefox
    FIREFOX_PROFILE = os.path.expanduser("~/firefox-prenotami-profile")
    os.makedirs(FIREFOX_PROFILE, exist_ok=True)

    async with async_playwright() as p:
        # Chrome
        '''context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=False,
            channel="chrome",
            locale="it-IT",
            timezone_id="Europe/Rome",
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/147.0.0.0 Safari/537.36"
            ),
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )'''

        # Firefox
        context = await p.firefox.launch_persistent_context(
            user_data_dir=FIREFOX_PROFILE,
            headless=False,
            locale="it-IT",
            timezone_id="Europe/Rome",
            viewport={"width": 1440, "height": 900},
            args=["--no-sandbox"],
        )

        page = context.pages[0] if context.pages else await context.new_page()
        await Stealth().apply_stealth_async(page)

        print(">>> CHROME CONECTADO COM STEALTH ATIVADO.")
        print(">>> FAÇA LOGIN E NAVEGUE ATÉ A PÁGINA DE SERVIÇOS.\n")

        await page.goto(URL_HOME)
        aguardar_login(LOGIN_WAIT)

        # ── Loop externo: persiste até sucesso ou encerramento manual ──
        while True:
            resultado = await loop_monitoramento(page)

            if resultado == "sucesso":
                print(">>> RESERVA CONCLUÍDA! Encerrando...")
                break

            elif resultado == "reverificacao":
                continuar = perguntar_reinicio()
                if continuar:
                    print("\n>>> Reiniciando monitoramento...\n")
                    aguardar_login(LOGIN_WAIT)
                    continue
                else:
                    print("\n>>> Encerrando por escolha do usuário.")
                    break

            elif resultado == "encerrado":
                print("\n\nEncerrado pelo usuário (Ctrl+C).")
                break

        await context.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nEncerrado pelo usuário.")