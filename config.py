import os
from enum import Enum, auto
from dataclasses import dataclass
 
 
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
 
    urls_oauth: tuple = (
        "iam.esteri.it", "pingid", "oauth2", "signin", "authorize",
    )
 
    triggers_reverificacao: tuple = (
        "session expired", "sessione scaduta",
        "captcha", "autenticazione", "verifica",
    )
 
    erros_servidor: tuple = (
        "HTTP ERROR 500", "HTTP ERROR 404",
        "não consegue atender",
        "Si è verificato un errore",
        "elaborazione della richiesta",
    )
 
 
class Resultado(Enum):
    SUCESSO       = auto()
    REVERIFICACAO = auto()
    ENCERRADO     = auto()
 
CFG = Config()