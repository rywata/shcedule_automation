import random
import asyncio
from typing import Optional
from playwright.async_api import Page

from config import CFG, Resultado
from detector import e_url_oauth, e_bloqueio_radware, e_erro_servidor, e_reverificacao
from actions import aguardar_oauth, tentar_reserva, simular_mouse
from notifier import Notifier


class Monitor:
    """
    Gerencia o loop de monitoramento de vagas.
    Mantém estado interno de tentativas e tempo de espera por erro.
    """

    def __init__(self, page: Page, notifier: Notifier) -> None:
        self.page        = page
        self.notifier    = notifier
        self.tentativas  = 0
        self.espera_erro = CFG.espera_erro_ini

    async def rodar(self) -> Resultado:
        """
        Executa o loop de monitoramento até encontrar uma vaga
        ou detectar re-verificação. KeyboardInterrupt é tratado no main.
        """
        while True:
            try:
                resultado = await self._ciclo()
                if resultado is not None:
                    return resultado

            except Exception as e:
                self.notifier.log(f"Erro inesperado: {e}")
                await asyncio.sleep(5)
                await self._voltar_home()

    async def _ciclo(self) -> Optional[Resultado]:
        """
        Executa um ciclo de verificação.
        Retorna um Resultado se o loop deve encerrar, ou None para continuar.
        """
        self.tentativas += 1
        url = self.page.url

        # ── Fluxo OAuth em andamento ──────────────────────────────────
        if e_url_oauth(url):
            ok = await aguardar_oauth(self.page, self.notifier)
            return Resultado.REVERIFICACAO if not ok else None

        conteudo = await self.page.content()

        # ── Bloqueio Radware ──────────────────────────────────────────
        if e_bloqueio_radware(url):
            self.notifier.log("Bloqueio Radware — aguardando 30s...")
            await asyncio.sleep(30)
            await self._voltar_home()
            return None

        # ── Erro de servidor ──────────────────────────────────────────
        if e_erro_servidor(conteudo):
            self.notifier.log(f"Erro no servidor — aguardando {self.espera_erro}s...")
            await asyncio.sleep(self.espera_erro)
            self.espera_erro = min(self.espera_erro + 5, CFG.espera_erro_max)
            await self._voltar_home()
            return None

        # ── Re-verificação real (sessão expirada) ─────────────────────
        if e_reverificacao(url, conteudo):
            self.notifier.log("Re-verificação detectada!")
            return Resultado.REVERIFICACAO

        # ── Tudo normal: tenta reservar ───────────────────────────────
        self.espera_erro = CFG.espera_erro_ini

        if await tentar_reserva(self.page, self.notifier):
            self.notifier.sucesso()
            return Resultado.SUCESSO

        await simular_mouse(self.page)
        espera = random.uniform(CFG.refresh_min, CFG.refresh_max)
        self.notifier.log(f"Tentativa #{self.tentativas} — próxima em {espera:.1f}s...")
        await asyncio.sleep(espera)
        await self.page.reload()
        return None

    async def _voltar_home(self) -> None:
        try:
            await self.page.goto(CFG.url_home)
        except Exception:
            pass