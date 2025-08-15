import os
from dotenv import load_dotenv, find_dotenv

# Carrega variáveis do arquivo .env que está na raiz
load_dotenv(find_dotenv(".env", raise_error_if_not_found=False), override=False)

def get_credentials() -> dict:
    """Retorna as credenciais do .env."""
    user = os.getenv("FULTec_USER")
    pw = os.getenv("FULTec_PASS")
    cnpj = os.getenv("FULTec_CNPJ")

    if not all([user, pw, cnpj]):
        raise RuntimeError(
            "Credenciais ausentes: defina FULTec_USER, FULTec_PASS e FULTec_CNPJ no .env"
        )

    return {"user": user, "pass": pw, "cnpj": cnpj}
