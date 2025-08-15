import time
import requests
from .secrets import get_credentials
from .config import FULTec_BASE_URL, FULTec_TIMEOUT

# --- credenciais do .env
_creds = get_credentials()
FULTec_USER = _creds["user"]
FULTec_PASS = _creds["pass"]
FULTec_CNPJ = _creds["cnpj"]

# --- cache do token
_cached_token = None
_cached_until = 0  # epoch seconds

def _try_token():
    url = f"{FULTec_BASE_URL}/token"
    payload = {"username": FULTec_USER, "password": FULTec_PASS, "cnpj": str(FULTec_CNPJ)}

    # tenta json+basic, depois form+basic, depois json sem basic
    for kwargs in (
        dict(json=payload, auth=(FULTec_USER, FULTec_PASS)),
        dict(data=payload, auth=(FULTec_USER, FULTec_PASS)),
        dict(json=payload),
    ):
        r = requests.post(url, timeout=FULTec_TIMEOUT, **kwargs)
        if r.ok:
            data = r.json()
            tok = data.get("token") or data.get("access_token") or data.get("jwt")
            ttl = int(data.get("expires_in", 3000))
            if tok:
                return tok, ttl
    r.raise_for_status()  # se nenhuma tentativa funcionou

def get_token(force: bool = False) -> str:
    global _cached_token, _cached_until
    now = int(time.time())
    if force or not _cached_token or now >= _cached_until:
        tok, ttl = _try_token()
        _cached_token = tok
        _cached_until = now + max(60, ttl - 60)
    return _cached_token

def auth_header() -> dict:
    """Header Authorization atual."""
    return {"Authorization": f"Bearer {get_token()}"}

def refresh_and_get() -> dict:
    """Força renovar o token e devolve header pronto (usado após 401)."""
    _ = get_token(force=True)
    return auth_header()
