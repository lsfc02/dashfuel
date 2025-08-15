# --- garantir que o pacote "src" seja encontrado ---
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import os
import streamlit as st
import datetime as dt
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from openai import OpenAI
import json

from src.fultec_api import fetch_abastecimentos, build_filter
from src.transforms import kpis, por_dia, resumo_por_colaborador
import src.ui_components as ui

# ==================== CONFIGURAÇÕES ====================
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("⚠️ Chave da OpenAI não encontrada no .env (OPENAI_API_KEY).")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)
st.set_page_config(layout="wide")

# ==================== CHAT TRIGGER ====================
st.markdown("### 💬 Chat IA (aciona funcionalidades do dashboard)")
user_prompt = st.text_input(
    "Digite seu comando",
    ""
)

# Valores padrão
d_ini = dt.date.today().replace(day=1)
d_fim = dt.date.today()
h_ini = dt.time(0, 0)
h_fim = dt.time(23, 59)
acao = "mostrar_tendencia"
parametros = {}
filtros_extras = {}

if user_prompt:
    try:
        system_prompt = f"""
Você é um orquestrador para um dashboard de abastecimentos.
Responda SOMENTE em JSON válido, sem markdown, sem texto extra, sem explicações.
Formato:
{{
  "acao": "<acao>",
  "filtros": {{
    "data_inicial": "YYYY-MM-DD",
    "hora_inicial": "HH:MM",
    "data_final": "YYYY-MM-DD",
    "hora_final": "HH:MM"
  }},
  "filtros_extras": {{
    "produto": "<nome do produto ou vazio>",
    "colaborador": "<nome do funcionário ou vazio>",
    "nivel": "<nível ou vazio>"
  }},
  "parametros": {{
    "top_n": <numero> (opcional),
    "modo": "<linha|barras|area|dispersao>" (opcional)
  }}
}}

Ações possíveis:
- mostrar_tendencia
- mostrar_top_colaboradores
- mostrar_kpis

Se não especificar data/hora, use:
data_inicial = {d_ini}, hora_inicial = "00:00",
data_final = {d_fim}, hora_final = "23:59".
"""
        ai_response = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_output_tokens=400
        )

        raw_text = ai_response.output_text.strip()

        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            st.error("❌ Erro: A IA não retornou JSON válido.")
            st.code(raw_text, language="json")
            st.stop()

        # Aplica filtros de data/hora
        d_ini = dt.datetime.strptime(data["filtros"]["data_inicial"], "%Y-%m-%d").date()
        h_ini = dt.datetime.strptime(data["filtros"]["hora_inicial"], "%H:%M").time()
        d_fim = dt.datetime.strptime(data["filtros"]["data_final"], "%Y-%m-%d").date()
        h_fim = dt.datetime.strptime(data["filtros"]["hora_final"], "%H:%M").time()

        # Extras
        filtros_extras = data.get("filtros_extras", {})
        acao = data.get("acao", acao)
        parametros = data.get("parametros", {})

    except Exception as e:
        st.error(f"Erro ao processar comando da IA: {e}")

# ==================== FILTROS ====================
col1, col2 = st.columns(2)
with col1:
    d_ini = st.date_input("Data inicial", d_ini)
    h_ini = st.time_input("Hora inicial", h_ini)
with col2:
    d_fim = st.date_input("Data final", d_fim)
    h_fim = st.time_input("Hora final", h_fim)

tz = ZoneInfo("America/Sao_Paulo")
dt_ini = dt.datetime.combine(d_ini, h_ini).replace(tzinfo=tz)
dt_fim = dt.datetime.combine(d_fim, h_fim).replace(tzinfo=tz)

start_iso = dt_ini.strftime("%Y-%m-%dT%H:%M:%S")
end_iso   = dt_fim.strftime("%Y-%m-%dT%H:%M:%S")

# Monta filtro da API
filtro = build_filter(
    start_iso=start_iso,
    end_iso=end_iso,
    produto=filtros_extras.get("produto"),
    colaborador=filtros_extras.get("colaborador"),
    nivel=filtros_extras.get("nivel")
)

@st.cache_data(ttl=120, show_spinner=False)
def _load(filter_expr: str):
    return fetch_abastecimentos(filter_expr=filter_expr)

df = _load(filtro)

# ==================== EXECUÇÃO DE AÇÃO ====================
if acao == "mostrar_kpis":
    ui.kpi_row(kpis(df))

elif acao == "mostrar_tendencia":
    ui.kpi_row(kpis(df))
    st.subheader("Tendência diária")
    modo = parametros.get("modo", "linha")
    trend_df = por_dia(df)
    ui.plot_tendencia(trend_df, modo)

elif acao == "mostrar_top_colaboradores":
    ui.kpi_row(kpis(df))
    st.subheader("Top Colaboradores")
    top_n = parametros.get("top_n", 10)
    ui.plot_bar_colaboradores(resumo_por_colaborador(df), top_n=top_n)

# ==================== SEMPRE MOSTRAR TOP COLABORADORES ====================
st.subheader("Top Colaboradores (por Valor)")
top_n = parametros.get("top_n", 10)
ui.plot_bar_colaboradores(resumo_por_colaborador(df), top_n=top_n)

# ==================== EXPORTAR ====================
st.download_button(
    "Baixar CSV do período",
    df.to_csv(index=False).encode("utf-8"),
    "abastecimentos.csv",
    "text/csv"
)
