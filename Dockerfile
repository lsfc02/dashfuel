# Usa Python slim pra imagem ficar leve
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=America/Sao_Paulo

# Dependências do sistema (build + tzdata)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates tzdata \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia só requirements primeiro (melhor cache)
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# Copia o código
COPY app /app/app
COPY src /app/src
COPY README.md streamlit.toml /app/

# Se você tiver uma pasta .streamlit com config/secrets, copie assim:
# COPY .streamlit /app/.streamlit

# Exponha a porta padrão do Streamlit
EXPOSE 8501

# Healthcheck simples
HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Comando de execução
CMD ["streamlit", "run", "app/Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
