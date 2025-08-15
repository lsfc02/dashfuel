import streamlit as st
import plotly.express as px
import pandas as pd


def _fmt_br_number(x: float, casas: int = 2) -> str:
    if x is None:
        x = 0.0
    s = f"{float(x):,.{casas}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_br_currency(x: float) -> str:
    return f"R$ {_fmt_br_number(x, 2)}"


def kpi_row(k):
    """Exibe KPIs (tuple/list ou dict)."""
    if isinstance(k, (tuple, list)):
        total_abast, total_litros, total_valor, ticket_medio = k
    else:
        total_abast = float(k.get("total_abast", 0))
        total_litros = float(k.get("litros", 0))
        total_valor = float(k.get("faturamento", 0))
        ticket_medio = float(k.get("ticket_medio", 0))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Abastecimentos", _fmt_br_number(total_abast, 0))
    c2.metric("Litragem (L)", _fmt_br_number(total_litros, 2))
    c3.metric("Faturamento (R$)", _fmt_br_currency(total_valor))
    c4.metric("Ticket médio (R$)", _fmt_br_currency(ticket_medio))


# ---------- Tendência diária ----------
def _has_trend_cols(df: pd.DataFrame) -> bool:
    return {"dia", "Valor", "Litragem"}.issubset(df.columns)


def plot_series_dia(df: pd.DataFrame):
    if not _has_trend_cols(df):
        st.info("Dados insuficientes para montar a tendência diária.")
        return
    df_long = df.melt(id_vars=["dia"], value_vars=["Valor", "Litragem"],
                      var_name="Métrica", value_name="vl")
    fig = px.line(df_long, x="dia", y="vl", color="Métrica", markers=True,
                  labels={"dia": "Data", "vl": "Valor / Litragem", "Métrica": "Métrica"},
                  hover_data={"vl": ":,.2f"})
    fig.update_layout(hovermode="x unified", legend_title="Métrica",
                      margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)


def plot_tendencia_barras(df: pd.DataFrame):
    if not _has_trend_cols(df):
        st.info("Dados insuficientes para montar a tendência diária.")
        return
    df_long = df.melt(id_vars=["dia"], value_vars=["Valor", "Litragem"],
                      var_name="Métrica", value_name="vl")
    fig = px.bar(df_long, x="dia", y="vl", color="Métrica", barmode="group",
                 labels={"dia": "Data", "vl": "Valor / Litragem", "Métrica": "Métrica"},
                 hover_data={"vl": ":,.2f"})
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), legend_title="Métrica")
    st.plotly_chart(fig, use_container_width=True)


def plot_tendencia_area(df: pd.DataFrame):
    if not _has_trend_cols(df):
        st.info("Dados insuficientes para montar a tendência diária.")
        return
    df_long = df.melt(id_vars=["dia"], value_vars=["Valor", "Litragem"],
                      var_name="Métrica", value_name="vl")
    fig = px.area(df_long, x="dia", y="vl", color="Métrica",
                  labels={"dia": "Data", "vl": "Valor / Litragem", "Métrica": "Métrica"},
                  hover_data={"vl": ":,.2f"})
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), legend_title="Métrica")
    st.plotly_chart(fig, use_container_width=True)


def plot_tendencia_disp(df: pd.DataFrame):
    if not _has_trend_cols(df):
        st.info("Dados insuficientes para montar a dispersão Valor x Litragem.")
        return
    fig = px.scatter(df, x="Litragem", y="Valor", hover_name="dia",
                     labels={"Litragem": "Litragem (L)", "Valor": "Faturamento (R$)"})
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)


def plot_tendencia(df: pd.DataFrame, mode: str):
    if mode == "linha":
        return plot_series_dia(df)
    if mode == "barras":
        return plot_tendencia_barras(df)
    if mode == "area":
        return plot_tendencia_area(df)
    if mode == "dispersao":
        return plot_tendencia_disp(df)
    return plot_tendencia_barras(df)


# ---------- Top colaboradores ----------
def plot_bar_colaboradores(resumo: pd.DataFrame, top_n: int = 10):
    if resumo.empty:
        st.info("Sem dados para exibir colaboradores.")
        return

    df = resumo.copy()
    if "colaborador" in df.columns and "Colaborador" not in df.columns:
        df = df.rename(columns={"colaborador": "Colaborador"})

    df = df.sort_values("Valor", ascending=False).reset_index(drop=True)

    if len(df) > top_n:
        top = df.iloc[:top_n].copy()
        resto = df.iloc[top_n:].copy()
        outros = {"Colaborador": "Outros", "Valor": resto["Valor"].sum()}
        if "Abastecimentos" in df.columns:
            outros["Abastecimentos"] = resto["Abastecimentos"].sum()
        if "Litragem" in df.columns:
            outros["Litragem"] = resto["Litragem"].sum()
        if "%" in df.columns:
            outros["%"] = resto["%"].sum()
        df = pd.concat([top, pd.DataFrame([outros])], ignore_index=True)

    df["Valor_fmt"] = df["Valor"].apply(_fmt_br_currency)

    hover = {"Valor": False, "Valor_fmt": True}
    if "Abastecimentos" in df.columns:
        hover["Abastecimentos"] = True
    if "Litragem" in df.columns:
        hover["Litragem"] = True
    if "%" in df.columns:
        hover["%"] = True

    fig = px.bar(df, x="Valor", y="Colaborador", orientation="h",
                 text="Valor_fmt", hover_data=hover,
                 labels={"Valor": "Valor (R$)", "Colaborador": "Colaborador"})
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_layout(margin=dict(l=10, r=20, t=10, b=10),
                      xaxis_title="Valor (R$)", yaxis_title="Colaborador")
    st.plotly_chart(fig, use_container_width=True)
