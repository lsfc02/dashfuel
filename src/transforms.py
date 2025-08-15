import pandas as pd


# ----------------- KPIs -----------------
def _num(s):
    return pd.to_numeric(s, errors="coerce")

def kpis(df: pd.DataFrame):
    """
    Volta a retornar TUPLA (abastecimentos, litragem, faturamento, ticket_medio),
    que é o formato esperado por ui.kpi_row(...).
    Resiliente a ausência de colunas.
    """
    total_abast = int(df.shape[0])

    litros = _num(df["litragem"]) if "litragem" in df.columns else pd.Series(dtype="float64")
    valor  = _num(df["valor"])     if "valor"     in df.columns else pd.Series(dtype="float64")

    total_litros = float(litros.sum(skipna=True)) if not litros.empty else 0.0
    total_valor  = float(valor.sum(skipna=True))  if not valor.empty  else 0.0

    ticket_medio = (total_valor / total_abast) if total_abast > 0 else 0.0
    return total_abast, total_litros, total_valor, ticket_medio


# ----------------- Tendência diária -----------------
def por_dia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega Valor e Litragem por dia.
    Usa 'data' se existir; senão, deriva de 'dhRegistro'.
    Retorna colunas: ['dia', 'Valor', 'Litragem']
    """
    if df.empty:
        return pd.DataFrame(columns=["dia", "Valor", "Litragem"])

    work = df.copy()

    if "data" in work.columns:
        work["data"] = pd.to_datetime(work["data"], errors="coerce")
        dia = work["data"].dt.date
    elif "dhRegistro" in work.columns:
        work["dhRegistro"] = pd.to_datetime(work["dhRegistro"], errors="coerce")
        dia = work["dhRegistro"].dt.date
    else:
        return pd.DataFrame(columns=["dia", "Valor", "Litragem"])

    valor_ser  = _num(work["valor"])    if "valor"    in work.columns else pd.Series(dtype="float64")
    litros_ser = _num(work["litragem"]) if "litragem" in work.columns else pd.Series(dtype="float64")

    diario = (
        pd.DataFrame({"dia": dia, "Valor": valor_ser, "Litragem": litros_ser})
        .groupby("dia", as_index=False)
        .sum(numeric_only=True)
    )
    return diario


# ----------------- Colaboradores -----------------
def resumo_por_colaborador(df: pd.DataFrame) -> pd.DataFrame:
    """
    Resumo de faturamento por colaborador.
    Usa 'nomeFuncionario' (ou 'nomeVendedor' como fallback).
    Retorna colunas: ['Colaborador', 'Valor'] ordenado desc.
    """
    if df.empty:
        return pd.DataFrame(columns=["Colaborador", "Valor"])

    work = df.copy()

    if "nomeFuncionario" in work.columns:
        col_nome = "nomeFuncionario"
    elif "nomeVendedor" in work.columns:
        col_nome = "nomeVendedor"
    else:
        return pd.DataFrame(columns=["Colaborador", "Valor"])

    work["_valor_num"] = _num(work["valor"]) if "valor" in work.columns else pd.Series(dtype="float64")

    resumo = (
        work.groupby(col_nome, dropna=False)["_valor_num"]
        .sum()
        .reset_index()
        .rename(columns={col_nome: "Colaborador", "_valor_num": "Valor"})
        .sort_values("Valor", ascending=False)
    )
    return resumo
