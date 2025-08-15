from typing import Optional, Dict, List
import requests
import pandas as pd
from urllib.parse import urlencode

from .config import FULTec_BASE_URL, FULTec_TIMEOUT, DEFAULT_SELECT
from .auth import auth_header, refresh_and_get

_SESSION = requests.Session()


def _headers() -> Dict[str, str]:
    return auth_header()


# --------------------------------------------
# $select mínimo requerido pelo dashboard
# --------------------------------------------
_REQUIRED_FIELDS: List[str] = [
    # datas/horas e valores
    "dhRegistro", "valor", "litragem",
    # campos usados em filtros e gráficos
    "produto",
    "idFuncionario", "nomeFuncionario",
    "idNivel", "nivel",
]


def _ensure_select_fields(select: Optional[str]) -> str:
    """
    Garante que o $select enviado à API contenha os campos mínimos para o dashboard.
    Se 'select' vier None, usa apenas os mínimos.
    """
    if not select:
        return ",".join(_REQUIRED_FIELDS)

    fields = [s.strip() for s in select.split(",") if s.strip()]
    for f in _REQUIRED_FIELDS:
        if f not in fields:
            fields.append(f)
    return ",".join(fields)


# --------------------------------------------
# Montagem do $filter
# --------------------------------------------
def _escape_odata_str(value: str) -> str:
    """Escapa aspas simples para OData (' -> '')."""
    return value.replace("'", "''")


def build_filter(
    start_iso: Optional[str] = None,
    end_iso: Optional[str] = None,
    extra: Optional[str] = None,
    produto: Optional[str] = None,
    colaborador: Optional[str] = None,
    nivel: Optional[str] = None,
) -> Optional[str]:
    """
    Monta a expressão para $filter com datas/horas e filtros opcionais.
    Usa 'contains' para permitir busca parcial.
    """
    parts: List[str] = []

    # Filtros de data/hora
    if start_iso:
        parts.append(f"dhRegistro ge {start_iso}")
    if end_iso:
        parts.append(f"dhRegistro lt {end_iso}")

    # Filtro extra já pronto
    if extra:
        parts.append(extra)

    # Filtros específicos
    if produto and produto.strip():
        v = _escape_odata_str(produto.strip())
        parts.append(f"contains(produto, '{v}')")

    if colaborador and colaborador.strip():
        v = _escape_odata_str(colaborador.strip())
        parts.append(f"contains(nomeFuncionario, '{v}')")

    if nivel and nivel.strip():
        v = _escape_odata_str(nivel.strip())
        parts.append(f"contains(nivel, '{v}')")

    return " and ".join(parts) if parts else None


# --------------------------------------------
# Request com retry de 401 (refresh)
# --------------------------------------------
def _request_with_retry(url: str, timeout: float) -> requests.Response:
    resp = _SESSION.get(url, headers=_headers(), timeout=timeout)
    if resp.status_code == 401:
        resp = _SESSION.get(url, headers=refresh_and_get(), timeout=timeout)
    resp.raise_for_status()
    return resp


# --------------------------------------------
# Fetch principal
# --------------------------------------------
def fetch_abastecimentos(
    select: Optional[str] = DEFAULT_SELECT,
    orderby: str = "dhRegistro asc",
    filter_expr: Optional[str] = None,
    top: Optional[int] = None,
    timeout: float = FULTec_TIMEOUT,
) -> pd.DataFrame:
    endpoint = f"{FULTec_BASE_URL}/abastecimento"
    params: Dict[str, str] = {}

    # SEMPRE garante campos mínimos (inclui 'litragem' e 'valor')
    params["$select"] = _ensure_select_fields(select)

    if orderby:
        params["$orderby"] = orderby
    if filter_expr:
        params["$filter"] = filter_expr
    if top:
        params["$top"] = str(int(top))

    # Permite parênteses e aspas simples na query OData
    safe_chars = " ,:()'"
    url = f"{endpoint}?{urlencode(params, safe=safe_chars)}"

    r = _request_with_retry(url, timeout)
    data = (r.json() or {}).get("abastecimentos", [])
    df = pd.DataFrame(data)

    # Se vazio, cria colunas esperadas para não quebrar o pipeline
    if df.empty:
        for col in [
            "dhRegistro", "valor", "litragem", "produto",
            "idFuncionario", "nomeFuncionario", "idNivel", "nivel",
            "data"
        ]:
            if col not in df.columns:
                df[col] = pd.Series(dtype="object")
        for c in ("valor", "litragem", "valorUnitario", "encerrante"):
            if c not in df.columns:
                df[c] = pd.Series(dtype="float64")
        return df

    # Fallbacks de nomes, caso a API varie
    if "litragem" not in df.columns:
        if "litros" in df.columns:
            df["litragem"] = pd.to_numeric(df["litros"], errors="coerce")
        elif "quantidade" in df.columns:
            df["litragem"] = pd.to_numeric(df["quantidade"], errors="coerce")

    # Normalizações de data/hora
    if "dhRegistro" in df.columns:
        df["dhRegistro"] = pd.to_datetime(df["dhRegistro"], errors="coerce")
        df["dia"] = df["dhRegistro"].dt.date
        df["mes"] = df["dhRegistro"].dt.to_period("M").astype(str)
        df["hora_num"] = df["dhRegistro"].dt.hour

    if "data" in df.columns:
        df["data"] = pd.to_datetime(df["data"], errors="coerce")

    # Garante numéricos
    for c in ("valor", "litragem", "valorUnitario", "encerrante"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            df[c] = pd.Series(dtype="float64")

    return df
