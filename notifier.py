import os
import sys
import time
import asyncio


class Notifier:
    """Responsável por logs, alertas sonoros e interação com o usuário."""

    # ── Logs ──────────────────────────────────────────────────────────────────

    def log(self, msg: str) -> None:
        print(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def info(self, msg: str) -> None:
        print(msg)

    # ── Alertas sonoros ───────────────────────────────────────────────────────

    def falar(self, msg: str) -> None:
        if sys.platform == "darwin":
            os.system(f'say "{msg}"')
        elif sys.platform == "win32":
            import winsound
            for _ in range(5):
                winsound.Beep(1000, 400)
        else:
            for _ in range(5):
                sys.stdout.write("\a")
                sys.stdout.flush()

    # ── Notificações de estado ────────────────────────────────────────────────

    def sucesso(self) -> None:
        print("\n" + "=" * 55)
        print("!!!  CALENDÁRIO ABERTO — ASSUMA O CONTROLE AGORA!  !!!")
        print("=" * 55 + "\n")
        self.falar("Sucesso! Verifique o navegador agora!")

    def alerta_reverificacao(self) -> None:
        print("\n" + "⚠️  " * 15)
        print("ATENÇÃO: O site pediu uma nova verificação!")
        print("Faça a verificação manualmente no navegador.")
        print("⚠️  " * 15)
        self.falar("Atenção! O site pediu uma nova verificação!")

    def conectado(self) -> None:
        print(">>> FIREFOX CONECTADO COM STEALTH ATIVADO.")
        print(">>> FAÇA LOGIN E NAVEGUE ATÉ A PÁGINA DE SERVIÇOS.\n")

    # ── Interação com o usuário ───────────────────────────────────────────────

    async def aguardar_login(self, segundos: int) -> None:
        """Countdown assíncrono — não bloqueia o event loop."""
        for i in range(segundos, 0, -1):
            print(f"    Robô assume o controle em: {i:02d}s ", end="\r")
            await asyncio.sleep(1)
        print("\n\n>>> MONITORAMENTO ATIVADO!\n")

    def perguntar_reinicio(self) -> bool:
        """Pergunta se o usuário quer reiniciar após re-verificação."""
        self.alerta_reverificacao()
        while True:
            resposta = input(
                "\nApós completar, deseja reiniciar o monitoramento? (s/n): "
            ).strip().lower()
            if resposta in ("s", "n"):
                return resposta == "s"
            print("Digite 's' para sim ou 'n' para não.")