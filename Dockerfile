FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=America/Sao_Paulo

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates tzdata \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY app /app/app
COPY src /app/src
COPY README.md streamlit.toml /app/

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1


CMD ["streamlit","run","app/pages/01_Visão_Geral.py","--server.port=8501","--server.address=0.0.0.0"]
