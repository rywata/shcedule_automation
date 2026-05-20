
from config import CFG
 
 
def e_url_oauth(url: str) -> bool:
    """Retorna True se a URL faz parte do fluxo OAuth normal."""
    return any(token in url.lower() for token in CFG.urls_oauth)
 
 
def e_bloqueio_radware(url: str) -> bool:
    """Retorna True se o Radware bloqueou a requisição."""
    return "Error.cshtml" in url or "perfdrive" in url
 
 
def e_erro_servidor(conteudo: str) -> bool:
    """Retorna True se o servidor retornou um erro conhecido (500, 404, etc)."""
    return any(msg in conteudo for msg in CFG.erros_servidor)
 
 
def e_reverificacao(url: str, conteudo: str) -> bool:
    """
    Retorna True se o site pediu re-verificação real (sessão expirada, captcha).
    Ignora URLs do fluxo OAuth para evitar falsos positivos.
    """
    if e_url_oauth(url):
        return False
    return any(t in conteudo.lower() for t in CFG.triggers_reverificacao)