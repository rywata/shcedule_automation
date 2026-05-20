import os
import sys
import time
import random
import asyncio
from enum import Enum, auto
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page, BrowserContext
from playwright_stealth import Stealth

'''



ARQUIVO DESCONTINUADO



'''


# ──────────────────────────────────────────────────────────────────────────────
# CONFIGURAÇÕES
# ──────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Config:
    url_home:        str   = "https://prenotami.esteri.it/"
    firefox_profile: str   = os.path.expanduser("~/firefox-prenotami-profile")
    login_wait:      int   = 60
    refresh_min:     float = 8.0
    refresh_max:     float = 15.0
    click_jitter:    tuple = (0.5, 1.5)
    espera_erro_ini: int   = 10
    espera_erro_max: int   = 60

    botao_selector:  str   = "button:has-text('Reservar')"
    ok_selector:     str   = "button:has-text('ok')"

    # URLs que fazem parte do fluxo OAuth — não interromper
    urls_oauth: tuple = (
        "iam.esteri.it", "pingid", "oauth2", "signin", "authorize",
    )

    # Gatilhos de re-verificação REAL (após login)
    triggers_reverificacao: tuple = (
        "session expired", "sessione scaduta",
        "captcha", "autenticazione", "verifica",
    )

    # Mensagens de erro de servidor
    erros_servidor: tuple = (
        "HTTP ERROR 500", "HTTP ERROR 404",
        "não consegue atender",
        "Si è verificato un errore",
        "elaborazione della richiesta",
    )

CFG = Config()

# ──────────────────────────────────────────────────────────────────────────────
# ENUMS
# ──────────────────────────────────────────────────────────────────────────────

class Resultado(Enum):
    SUCESSO        = auto()
    REVERIFICACAO  = auto()
    ENCERRADO      = auto()

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")


def falar(msg: str) -> None:
    if sys.platform == "darwin":
        os.system(f'say "{msg}"')


def aguardar_login(segundos: int = CFG.login_wait) -> None:
    for i in range(segundos, 0, -1):
        print(f"    Robô assume o controle em: {i:02d}s ", end="\r")
        time.sleep(1)
    print("\n\n>>> MONITORAMENTO ATIVADO!\n")


def perguntar_reinicio() -> bool:
    print("\n" + "⚠️  " * 15)
    print("ATENÇÃO: O site pediu uma nova verificação!")
    print("Faça a verificação manualmente no navegador.")
    print("⚠️  " * 15)
    falar("Atenção! O site pediu uma nova verificação!")
    while True:
        resposta = input("\nApós completar, deseja reiniciar o monitoramento? (s/n): ").strip().lower()
        if resposta in ("s", "n"):
            return resposta == "s"
        print("Digite 's' para sim ou 'n' para não.")


def notificar_sucesso() -> None:
    print("\n" + "=" * 55)
    print("!!!  CALENDÁRIO ABERTO — ASSUMA O CONTROLE AGORA!  !!!")
    print("=" * 55 + "\n")
    falar("Sucesso! Verifique o navegador agora!")

# ──────────────────────────────────────────────────────────────────────────────
# DETECÇÃO DE ESTADO DA PÁGINA
# ──────────────────────────────────────────────────────────────────────────────

def e_url_oauth(url: str) -> bool:
    return any(token in url.lower() for token in CFG.urls_oauth)


def e_erro_servidor(conteudo: str) -> bool:
    return any(msg in conteudo for msg in CFG.erros_servidor)


def e_reverificacao(url: str, conteudo: str) -> bool:
    if e_url_oauth(url):
        return False
    return any(t in conteudo.lower() for t in CFG.triggers_reverificacao)


def e_bloqueio_radware(url: str) -> bool:
    return "Error.cshtml" in url or "perfdrive" in url

# ──────────────────────────────────────────────────────────────────────────────
# AÇÕES NA PÁGINA
# ──────────────────────────────────────────────────────────────────────────────

async def aguardar_oauth(page: Page, timeout: int = 60) -> bool:
    if not e_url_oauth(page.url):
        return True
    log("Aguardando autenticação OAuth...")
    try:
        await page.wait_for_url("*prenotami.esteri.it*", timeout=timeout * 1000)
        log("Login OAuth concluído!")
        return True
    except Exception:
        log("Timeout aguardando OAuth — faça o login manualmente.")
        return False


async def clicar(page: Page, selector: str, timeout: int = 2000) -> bool:
    """Tenta clicar em um elemento com jitter humano. Retorna True se clicou."""
    try:
        el = page.locator(selector).first
        await el.wait_for(state="visible", timeout=timeout)
        await asyncio.sleep(random.uniform(*CFG.click_jitter))
        await el.click()
        return True
    except Exception:
        return False


async def tentar_reserva(page: Page) -> bool:
    """Clica em Reservar e verifica se abriu o calendário. Retorna True no sucesso."""
    if not await clicar(page, CFG.botao_selector):
        return False

    log("Botão 'Reservar' clicado!")
    await asyncio.sleep(1)

    # Popup de sem vagas
    if await clicar(page, CFG.ok_selector):
        log("Sem vagas. Continuando...\n")
        return False

    return True  # Calendário abriu!


async def simular_mouse(page: Page) -> None:
    await page.mouse.move(random.randint(100, 800), random.randint(100, 600))
    await asyncio.sleep(random.uniform(0.3, 0.8))

# ──────────────────────────────────────────────────────────────────────────────
# LOOP DE MONITORAMENTO
# ──────────────────────────────────────────────────────────────────────────────

async def loop_monitoramento(page: Page) -> Resultado:
    tentativas  = 0
    espera_erro = CFG.espera_erro_ini

    while True:
        try:
            tentativas += 1
            url = page.url

            if e_url_oauth(url):
                if not await aguardar_oauth(page):
                    return Resultado.REVERIFICACAO
                continue

            conteudo = await page.content()

            if e_bloqueio_radware(url):
                log("Bloqueio Radware — aguardando 30s...")
                await asyncio.sleep(30)
                await page.goto(CFG.url_home)
                continue

            if e_erro_servidor(conteudo):
                log(f"Erro no servidor — aguardando {espera_erro}s...")
                await asyncio.sleep(espera_erro)
                espera_erro = min(espera_erro + 5, CFG.espera_erro_max)
                await page.goto(CFG.url_home)
                continue

            if e_reverificacao(url, conteudo):
                log(f"Re-verificação detectada!")
                return Resultado.REVERIFICACAO

            espera_erro = CFG.espera_erro_ini

            if await tentar_reserva(page):
                notificar_sucesso()
                return Resultado.SUCESSO

            await simular_mouse(page)
            espera = random.uniform(CFG.refresh_min, CFG.refresh_max)
            log(f"Tentativa #{tentativas} — próxima em {espera:.1f}s...")
            await asyncio.sleep(espera)
            await page.reload()

        except KeyboardInterrupt:
            return Resultado.ENCERRADO
        except Exception as e:
            log(f"Erro inesperado: {e}")
            await asyncio.sleep(5)
            try:
                await page.goto(CFG.url_home)
            except Exception:
                pass

# ──────────────────────────────────────────────────────────────────────────────
# INICIALIZAÇÃO DO BROWSER
# ──────────────────────────────────────────────────────────────────────────────

async def criar_contexto(p) -> BrowserContext:
    os.makedirs(CFG.firefox_profile, exist_ok=True)
    return await p.firefox.launch_persistent_context(
        user_data_dir=CFG.firefox_profile,
        headless=False,
        locale="it-IT",
        timezone_id="Europe/Rome",
        viewport={"width": 1440, "height": 900},
    )

# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

async def main() -> None:
    async with async_playwright() as p:
        context = await criar_contexto(p)
        page    = context.pages[0] if context.pages else await context.new_page()

        await Stealth().apply_stealth_async(page)
        await page.goto(CFG.url_home)

        print(">>> FIREFOX CONECTADO COM STEALTH ATIVADO.")
        print(">>> FAÇA LOGIN E NAVEGUE ATÉ A PÁGINA DE SERVIÇOS.\n")
        aguardar_login()

        while True:
            resultado = await loop_monitoramento(page)

            if resultado == Resultado.SUCESSO:
                print(">>> RESERVA CONCLUÍDA!")
                break

            if resultado == Resultado.REVERIFICACAO:
                if perguntar_reinicio():
                    print("\n>>> Reiniciando monitoramento...\n")
                    aguardar_login()
                else:
                    print("\n>>> Encerrando por escolha do usuário.")
                    break

            if resultado == Resultado.ENCERRADO:
                print("\nEncerrado pelo usuário.")
                break

        await context.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nEncerrado pelo usuário.")
