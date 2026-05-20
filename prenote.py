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
REFRESH_MIN  = 8.0
REFRESH_MAX  = 15.0
CLICK_JITTER = (0.5, 1.5)

BOTAO_SELECTOR = "button:has-text('Reservar')"
OK_SELECTOR    = "button:has-text('ok')"

FIREFOX_PROFILE = os.path.expanduser("~/firefox-prenotami-profile")

# ⚠️  Apenas erros APÓS o login — nunca URLs do fluxo OAuth normal
TRIGGERS_REVERIFICACAO = [
    "session expired",
    "sessione scaduta",
    "captcha",
    "autenticazione",
    "verifica",
]

# URLs que fazem parte do fluxo OAuth normal — NÃO interromper
URLS_OAUTH_PERMITIDAS = [
    "iam.esteri.it",
    "pingid",
    "oauth2",
    "signin",
    "authorize",
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


def e_url_oauth(url: str) -> bool:
    """Retorna True se a URL faz parte do fluxo OAuth normal — não deve interromper."""
    url_lower = url.lower()
    return any(permitida in url_lower for permitida in URLS_OAUTH_PERMITIDAS)


def detectar_reverificacao(url: str, conteudo: str) -> bool:
    """Retorna True apenas se o site pediu re-verificação APÓS o login."""
    if e_url_oauth(url):
        return False  # fluxo OAuth normal, não interrompe
    conteudo_lower = conteudo.lower()
    return any(trigger in conteudo_lower for trigger in TRIGGERS_REVERIFICACAO)


def detectar_erro_servidor(conteudo: str) -> bool:
    return any(msg in conteudo for msg in [
        "HTTP ERROR 500",
        "HTTP ERROR 404",
        "não consegue atender",
        "Si è verificato un errore",
        "elaborazione della richiesta",
    ])


async def aguardar_oauth(page, timeout: int = 60) -> bool:
    """Aguarda o redirect OAuth completar e retornar ao prenotami."""
    if not e_url_oauth(page.url):
        return True  # já está no prenotami, não precisa aguardar
    print(f"[{time.strftime('%H:%M:%S')}] Aguardando autenticação OAuth...")
    try:
        await page.wait_for_url("*prenotami.esteri.it*", timeout=timeout * 1000)
        print(f"[{time.strftime('%H:%M:%S')}] Login OAuth concluído!")
        return True
    except Exception:
        print("Timeout aguardando OAuth — faça o login manualmente.")
        return False


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

        return True  # Calendário abriu!

    except Exception:
        return False


async def loop_monitoramento(page) -> str:
    tentativas = 0
    espera_erro = 10

    while True:
        try:
            tentativas += 1
            url_atual = page.url

            # ── Aguarda OAuth se ainda estiver no fluxo de login ──────
            if e_url_oauth(url_atual):
                oauth_ok = await aguardar_oauth(page)
                if not oauth_ok:
                    return "reverificacao"
                continue

            conteudo = await page.content()

            # ── Bloqueio Radware ──────────────────────────────────────
            if "Error.cshtml" in url_atual or "perfdrive" in url_atual:
                print(f"[{time.strftime('%H:%M:%S')}] Bloqueio Radware — aguardando 30s...")
                await asyncio.sleep(30)
                await page.goto(URL_HOME)
                continue

            # ── Erro de servidor ──────────────────────────────────────
            if detectar_erro_servidor(conteudo):
                print(f"[{time.strftime('%H:%M:%S')}] Erro servidor — aguardando {espera_erro}s...")
                await asyncio.sleep(espera_erro)
                espera_erro = min(espera_erro + 5, 60)
                await page.goto(URL_HOME)
                continue

            # ── Re-verificação real (sessão expirada etc.) ────────────
            if detectar_reverificacao(url_atual, conteudo):
                print(f"[{time.strftime('%H:%M:%S')}] Re-verificação detectada!")
                return "reverificacao"

            # ── Tudo normal: tenta reservar ───────────────────────────
            espera_erro = 10
            sucesso = await tentar_reserva(page)
            if sucesso:
                notificar_sucesso()
                return "sucesso"

            # Movimento de mouse para parecer humano
            await page.mouse.move(
                random.randint(100, 800),
                random.randint(100, 600)
            )
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
    os.makedirs(FIREFOX_PROFILE, exist_ok=True)

    async with async_playwright() as p:
        context = await p.firefox.launch_persistent_context(
            user_data_dir=FIREFOX_PROFILE,
            headless=False,
            locale="it-IT",
            timezone_id="Europe/Rome",
            viewport={"width": 1440, "height": 900},
        )

        page = context.pages[0] if context.pages else await context.new_page()
        await Stealth().apply_stealth_async(page)

        print(">>> FIREFOX CONECTADO COM STEALTH ATIVADO.")
        print(">>> FAÇA LOGIN E NAVEGUE ATÉ A PÁGINA DE SERVIÇOS.\n")

        await page.goto(URL_HOME)
        aguardar_login(LOGIN_WAIT)

        # ── Loop externo ──────────────────────────────────────────────
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